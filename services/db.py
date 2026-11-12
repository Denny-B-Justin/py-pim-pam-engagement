"""
db.py — thin Azure Databricks SQL layer (Unity Catalog).

* Authenticates with OAuth machine-to-machine (service-principal client id +
  secret). If DATABRICKS_AZURE_TENANT_ID is set, the principal is treated as a
  Microsoft Entra ID service principal instead of a Databricks-managed one.
* One connection per worker thread, created lazily and re-created if the
  session has gone away.
* Every statement uses *named parameters* (`:name`) — values are never
  interpolated into SQL text. Identifiers (catalog / schema / table / column)
  come only from constants.py and are validated before use.
"""
from __future__ import annotations

import logging
import random
import re
import threading
import time
from decimal import Decimal
from typing import Any, Mapping

import constants as C

log = logging.getLogger(__name__)

_IDENT = re.compile(r"^[A-Za-z0-9_\-]+$")
_ALLOWED_TABLES = frozenset(C.APP_TABLES) | frozenset(C.CHILD_TABLE_COLUMNS)


class DatabaseNotConfigured(RuntimeError):
    """Raised when the Databricks connection variables are missing."""


class DatabaseError(RuntimeError):
    """Raised when a statement could not be executed."""


# ── configuration / naming ──────────────────────────────────────────────────
def is_configured() -> bool:
    return all(
        (C.DATABRICKS_SERVER_HOSTNAME, C.DATABRICKS_HTTP_PATH, C.DATABRICKS_CLIENT_ID, C.DATABRICKS_CLIENT_SECRET)
    )


def fq(table: str) -> str:
    """Fully qualified, back-tick quoted table name: `catalog`.`schema`.`table`."""
    if table not in _ALLOWED_TABLES:
        raise ValueError(f"Unknown table: {table!r}")
    for part in (C.CATALOG, C.SCHEMA, table):
        if not _IDENT.match(part):
            raise ValueError(f"Illegal identifier: {part!r}")
    return f"`{C.CATALOG}`.`{C.SCHEMA}`.`{table}`"


def column(table: str, name: str) -> str:
    """Return `name` if it is a known column of `table` (identifier-injection guard)."""
    known = C.COUNTRY_COLUMNS if table == C.TBL_COUNTRIES else C.CHILD_TABLE_COLUMNS.get(table, {})
    if name not in known:
        raise ValueError(f"Unknown column {name!r} for table {table!r}")
    return f"`{name}`"


# ── connection handling ─────────────────────────────────────────────────────
_local = threading.local()


def _credentials_provider():
    """Header-factory provider for databricks-sql-connector (OAuth M2M)."""
    from databricks.sdk.core import Config, azure_service_principal, oauth_service_principal

    host = f"https://{C.DATABRICKS_SERVER_HOSTNAME}"
    if C.DATABRICKS_AZURE_TENANT_ID:
        cfg = Config(
            host=host,
            azure_client_id=C.DATABRICKS_CLIENT_ID,
            azure_client_secret=C.DATABRICKS_CLIENT_SECRET,
            azure_tenant_id=C.DATABRICKS_AZURE_TENANT_ID,
        )
        return azure_service_principal(cfg)
    cfg = Config(host=host, client_id=C.DATABRICKS_CLIENT_ID, client_secret=C.DATABRICKS_CLIENT_SECRET)
    return oauth_service_principal(cfg)


def _connect():
    from databricks import sql

    return sql.connect(
        server_hostname=C.DATABRICKS_SERVER_HOSTNAME,
        http_path=C.DATABRICKS_HTTP_PATH,
        credentials_provider=_credentials_provider,
        _user_agent_entry="pim-pam-engagement-dash",
    )


def _drop_connection() -> None:
    conn = getattr(_local, "conn", None)
    _local.conn = None
    if conn is not None:
        try:
            conn.close()
        except Exception:  # noqa: BLE001 — closing a dead session may itself fail
            pass


def _cursor():
    if not is_configured():
        raise DatabaseNotConfigured(
            "Databricks is not configured (set DATABRICKS_SERVER_HOSTNAME, DATABRICKS_HTTP_PATH, "
            "DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET)."
        )
    for attempt in (1, 2):
        try:
            if getattr(_local, "conn", None) is None:
                _local.conn = _connect()
            return _local.conn.cursor()
        except Exception as exc:  # noqa: BLE001
            _drop_connection()
            if attempt == 2:
                log.exception("Could not open a Databricks session")
                raise DatabaseError(f"Could not connect to Databricks: {exc}") from exc
    raise DatabaseError("Could not connect to Databricks.")  # pragma: no cover


# ── value normalisation ─────────────────────────────────────────────────────
def _py(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    return value


def _rows(cur) -> list[dict[str, Any]]:
    cols = [d[0] for d in cur.description]
    return [{c: _py(v) for c, v in zip(cols, row)} for row in cur.fetchall()]


# ── public API ──────────────────────────────────────────────────────────────
def query(sql_text: str, params: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """Run a SELECT and return a list of dicts. Retries once when the session has gone away."""
    last: Exception | None = None
    for attempt in (1, 2):
        cur = _cursor()
        try:
            cur.execute(sql_text, dict(params) if params else None)
            return _rows(cur)
        except DatabaseNotConfigured:
            raise
        except Exception as exc:  # noqa: BLE001
            last = exc
            dead = _looks_like_dead_session(exc)
            if dead:
                _drop_connection()
            if attempt == 1 and dead:
                continue
            break
        finally:
            try:
                cur.close()
            except Exception:  # noqa: BLE001
                pass
    log.error("Query failed: %s", last)
    raise DatabaseError(_clean_message(last)) from last


def query_one(sql_text: str, params: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
    rows = query(sql_text, params)
    return rows[0] if rows else None


def execute(sql_text: str, params: Mapping[str, Any] | None = None) -> int:
    """
    Run an INSERT / UPDATE / DELETE and return the number of affected rows
    (-1 if the engine did not report it).

    Delta Lake aborts a statement that collides with a concurrent write
    (`DELTA_CONCURRENT_*`). Nothing was committed in that case, so the statement is
    retried a few times. Any other failure is raised straight away — a write is
    never retried blindly, because it might already have been applied.
    """
    last: Exception | None = None
    for attempt in range(_CONFLICT_RETRIES + 1):
        cur = _cursor()
        try:
            cur.execute(sql_text, dict(params) if params else None)
            affected = -1
            if cur.description:
                names = [d[0] for d in cur.description]
                row = cur.fetchone()
                if row is not None and "num_affected_rows" in names:
                    affected = int(row[names.index("num_affected_rows")])
            return affected
        except DatabaseNotConfigured:
            raise
        except Exception as exc:  # noqa: BLE001
            last = exc
            if _is_write_conflict(exc) and attempt < _CONFLICT_RETRIES:
                log.warning("Concurrent write conflict, retrying (%s/%s)", attempt + 1, _CONFLICT_RETRIES)
                time.sleep(0.15 * (attempt + 1) + random.random() * 0.1)
                continue
            if _looks_like_dead_session(exc):
                _drop_connection()
            break
        finally:
            try:
                cur.close()
            except Exception:  # noqa: BLE001
                pass
    log.error("Statement failed: %s", last)
    raise DatabaseError(_clean_message(last)) from last


_CONFLICT_RETRIES = 3
_CONFLICT_MARKERS = ("delta_concurrent", "concurrentappend", "concurrentdelete", "concurrentmodification", "concurrentwrite", "metadata_changed")


def _is_write_conflict(exc: Exception) -> bool:
    text = f"{type(exc).__name__} {exc}".lower()
    return any(marker in text for marker in _CONFLICT_MARKERS)


def _looks_like_dead_session(exc: Exception) -> bool:
    text = f"{type(exc).__name__} {exc}".lower()
    return any(
        marker in text
        for marker in ("session", "closed", "connection", "timed out", "timeout", "invalidhandle", "requesterror", "interfaceerror")
    )


def _clean_message(exc: Exception | None) -> str:
    """A short, user-presentable error (no stack traces, no secrets)."""
    text = str(exc or "Unknown database error").strip().splitlines()[0] if exc else "Unknown database error"
    return text[:300]


def ping() -> bool:
    """True when the warehouse answers a trivial query (used by the README / health checks)."""
    try:
        query("SELECT 1 AS ok")
        return True
    except Exception:  # noqa: BLE001
        return False
