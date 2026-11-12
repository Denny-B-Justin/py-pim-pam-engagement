"""
repository.py — every read and write against the Unity Catalog tables.

This is the Python replacement for the Supabase calls scattered through the
original Next.js pages and API routes. Reads return plain dicts / lists; writes
raise `ServiceError` (see validation.py) with a short code or a user-ready message.

Notes
-----
* Child-table ids are STRING (uuid4 for new rows; the old numeric id for migrated
  rows) — Delta identity columns would disable concurrent writes on the table.
* `created_at` / `updated_at` / `deleted_at` are supplied by the app (UTC).
* Delta primary / foreign keys are informational only, so uniqueness is enforced
  here (create_country) and cascade deletes are not needed (the app never
  deletes a country).
"""
from __future__ import annotations

import json
import logging
import re
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Callable, Mapping

import constants as C
import page_constants as P
from services import db
from services.cache import cache
from services.fallback_data import FALLBACK_COUNTRIES
from services.validation import (
    ERR_EXISTS,
    ERR_INVALID,
    ERR_NO_DB,
    ServiceError,
    can_sync_email_for_name,
    has_valid_email,
    same_contact_name,
)

log = logging.getLogger(__name__)

# Runs independent queries side by side; each borrows a session from db's shared pool.
_POOL_SIZE = 6
_POOL = ThreadPoolExecutor(max_workers=_POOL_SIZE, thread_name_prefix="pp-db")

# Stable insertion order for child rows (ids are strings, so ORDER BY id alone is not enough).
_ID_ORDER = "`created_at` ASC NULLS LAST, LENGTH(`id`) ASC, `id` ASC"


# ── helpers ─────────────────────────────────────────────────────────────────
def db_available() -> bool:
    return db.is_configured()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


def to_iso(value: Any) -> str | None:
    """date / datetime → ISO string; str passes through; blank → None."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def parse_ts(value: Any) -> datetime | None:
    """Tolerant timestamp parser (ISO 8601 and Postgres-style '2026-06-10 12:00:00+00')."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip().replace("Z", "+00:00")
    if re.search(r"[+-]\d\d$", text):
        text += ":00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def parse_day(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        return None


def warm_up() -> None:
    """Fill the country-list cache, then open enough sessions for one fully parallel page load."""
    fetch_countries()
    db.warm_up(_POOL_SIZE - 1)


def _parallel(*calls: Callable[[], Any]) -> list[Any]:
    """Run independent queries concurrently (the original used Promise.all). Errors propagate."""
    futures = [_POOL.submit(c) for c in calls]
    return [f.result() for f in futures]


def _expr(table: str, col: str, marker: str) -> str:
    """SQL expression for a bound value; INT columns are cast so BIGINT params fit."""
    types = C.COUNTRY_COLUMNS if table == C.TBL_COUNTRIES else C.CHILD_TABLE_COLUMNS[table]
    return f"CAST({marker} AS INT)" if types.get(col) == "INT" else marker


def _guard_write(fn):
    """Decorator: turn database failures into ServiceError for the UI."""

    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except db.DatabaseNotConfigured as exc:
            raise ServiceError(ERR_NO_DB, str(exc)) from exc
        except db.DatabaseError as exc:
            raise ServiceError(str(exc)) from exc

    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper


# ═════════════════════════════════════════════════════════════════════════════
# READS
# ═════════════════════════════════════════════════════════════════════════════
@dataclass
class CountryList:
    countries: list[dict[str, Any]]
    source: str  # "db" | "static"


FALLBACK_CACHE_SECONDS = 60
_countries_lock = threading.Lock()  # one load at a time; concurrent callers reuse its result


def _static_list() -> CountryList:
    return CountryList([dict(c) for c in FALLBACK_COUNTRIES], "static")


def fetch_countries() -> CountryList:
    """
    The public country list (map, landing page, country index).

    Cached for CACHE_TTL_SECONDS (the original's ISR window). Falls back to the
    bundled snapshot when the database is unreachable or empty — a fallback is
    cached only for FALLBACK_CACHE_SECONDS, so a failing query (which can take
    30 s+) is not repeated on every page view, yet the site soon recovers.
    """
    cached = cache.get("countries")
    if cached is not None:
        return cached
    if not db.is_configured():
        return _static_list()
    with _countries_lock:
        cached = cache.get("countries")
        return cached if cached is not None else _load_countries()


def _load_countries() -> CountryList:
    try:
        rows = db.query(
            f"SELECT `iso3`, `name`, `region`, `status`, `focus_note`, `ttl` FROM {db.fq(C.TBL_COUNTRIES)} "
            "ORDER BY `region` ASC, `name` ASC"
        )
    except db.DatabaseError:
        rows = []
    rows = _valid_country_rows(rows)
    if not rows:
        fallback = _static_list()
        cache.put("countries", fallback, FALLBACK_CACHE_SECONDS)
        return fallback
    result = CountryList(
        [
            {
                "iso3": r["iso3"],
                "name": r["name"],
                "region": r["region"],
                "status": r["status"],
                "focus": r.get("focus_note") or "",
                "contact": r.get("ttl") or "—",
            }
            for r in rows
        ],
        "db",
    )
    cache.put("countries", result)
    return result


def _valid_country_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Drop malformed country rows (e.g. fragments of a badly parsed CSV import: no
    3-letter iso3, no name) so one bad row cannot break a page, and default a
    missing region / status to "" so sorting and grouping still work.
    """
    valid = [r for r in rows if re.fullmatch(r"[A-Z]{3}", r.get("iso3") or "") and r.get("name")]
    if len(valid) < len(rows):
        log.warning("Skipped %d malformed row(s) in %s", len(rows) - len(valid), C.TBL_COUNTRIES)
    for r in valid:
        r["region"] = r.get("region") or ""
        r["status"] = r.get("status") or ""
    return valid


def fetch_admin_rows() -> list[dict[str, Any]]:
    """Fresh country rows for the /admin list (iso3, name, region, status, focus_note, ttl)."""
    return _valid_country_rows(
        db.query(
            f"SELECT `iso3`, `name`, `region`, `status`, `focus_note`, `ttl` FROM {db.fq(C.TBL_COUNTRIES)} "
            "ORDER BY `region` ASC, `name` ASC"
        )
    )


def fetch_countries_full() -> list[dict[str, Any]]:
    """Every column of every country (review tracker, dashboard, exports)."""
    return _valid_country_rows(db.query(f"SELECT * FROM {db.fq(C.TBL_COUNTRIES)} ORDER BY `region` ASC, `name` ASC"))


def fetch_wb_contacts() -> list[dict[str, Any]]:
    """All World Bank contacts (id, iso3, role, name, email, organization), insertion order."""
    return db.query(
        f"SELECT `id`, `iso3`, `role`, `name`, `email`, `organization` FROM {db.fq(C.TBL_CONTACTS)} ORDER BY {_ID_ORDER}"
    )


def fetch_counterpart_isos() -> set[str]:
    rows = db.query(f"SELECT DISTINCT `iso3` FROM {db.fq(C.TBL_COUNTERPARTS)}")
    return {r["iso3"] for r in rows}


def fetch_country_row(iso3: str) -> dict[str, Any] | None:
    return db.query_one(f"SELECT * FROM {db.fq(C.TBL_COUNTRIES)} WHERE `iso3` = :iso3", {"iso3": iso3})


@dataclass
class CountryBundle:
    country: dict[str, Any] | None
    assessments: list[dict[str, Any]] = field(default_factory=list)
    projects: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    contacts: list[dict[str, Any]] = field(default_factory=list)
    counterparts: list[dict[str, Any]] = field(default_factory=list)


def _child_rows(table: str, iso3: str, order: str) -> list[dict[str, Any]]:
    return db.query(f"SELECT * FROM {db.fq(table)} WHERE `iso3` = :iso3 ORDER BY {order}", {"iso3": iso3})


def fetch_country_bundle(iso3: str) -> CountryBundle:
    """
    Everything the public country page needs, read fresh (it renders staff-only
    content, so it is never cached). Ordering matches the original queries
    (Postgres sorts NULLs first on DESC, hence NULLS FIRST).
    """
    country, assessments, projects, events, contacts, counterparts = _parallel(
        lambda: fetch_country_row(iso3),
        lambda: _child_rows(C.TBL_ASSESSMENTS, iso3, f"`year` DESC NULLS FIRST, {_ID_ORDER}"),
        lambda: _child_rows(C.TBL_PROJECTS, iso3, f"`year` DESC NULLS FIRST, {_ID_ORDER}"),
        lambda: _child_rows(C.TBL_EVENTS, iso3, f"`date` DESC NULLS FIRST, {_ID_ORDER}"),
        lambda: _child_rows(C.TBL_CONTACTS, iso3, _ID_ORDER),
        lambda: _child_rows(C.TBL_COUNTERPARTS, iso3, _ID_ORDER),
    )
    return CountryBundle(country, assessments, projects, events, contacts, counterparts)


@dataclass
class EditorBundle:
    country: dict[str, Any] | None
    children: dict[str, list[dict[str, Any]]]
    deleted: list[dict[str, Any]]


def fetch_editor_bundle(iso3: str) -> EditorBundle:
    """Country row + the five child tables + recently deleted records, for /admin-country."""
    calls: list[Callable[[], Any]] = [lambda: fetch_country_row(iso3)]
    for t in C.CHILD_TABLES:
        calls.append(lambda t=t: _child_rows(t.table, iso3, _ID_ORDER))
    calls.append(lambda: fetch_deleted(iso3))
    results = _parallel(*calls)
    children = {t.table: results[1 + i] for i, t in enumerate(C.CHILD_TABLES)}
    return EditorBundle(results[0], children, results[-1])


def fetch_deleted(iso3: str) -> list[dict[str, Any]]:
    return db.query(
        f"SELECT * FROM {db.fq(C.TBL_DELETED)} WHERE `iso3` = :iso3 ORDER BY `deleted_at` DESC LIMIT {int(C.DELETED_RECORDS_LIMIT)}",
        {"iso3": iso3},
    )


@dataclass
class DashboardData:
    countries: list[dict[str, Any]]
    contacts: list[dict[str, Any]]
    counterpart_isos: set[str]


def fetch_dashboard_data() -> DashboardData:
    countries, contacts, isos = _parallel(fetch_countries_full, fetch_wb_contacts, fetch_counterpart_isos)
    return DashboardData(countries, contacts, isos)


# ═════════════════════════════════════════════════════════════════════════════
# WRITES — countries
# ═════════════════════════════════════════════════════════════════════════════
@_guard_write
def update_country_basic(iso3: str, name: str, region: str, status: str, focus_note: str) -> None:
    """
    /admin quick edit: name, region, status, focus. Deliberately does NOT stamp
    `last_updated` (that would defeat the stale-data flag) and leaves the legacy
    `ttl` column alone.
    """
    db.execute(
        f"UPDATE {db.fq(C.TBL_COUNTRIES)} SET `name` = :name, `region` = :region, `status` = :status, "
        "`focus_note` = :focus WHERE `iso3` = :iso3",
        {"name": name, "region": region, "status": status, "focus": focus_note, "iso3": iso3},
    )
    cache.clear()


@_guard_write
def create_country(iso3: str, name: str, region: str, status: str, ttl: str, focus_note: str) -> None:
    """Insert a country (and a Focal point contact when `ttl` is given). Raises ERR_EXISTS on a duplicate."""
    now = now_utc()
    values = {
        "iso3": iso3,
        "name": name,
        "region": region,
        "status": status,
        "ttl": ttl or None,
        "focus_note": focus_note or None,
        "last_updated": now.date(),
        "created_at": now,
        "updated_at": now,
    }
    cols = list(values)
    sql = (
        f"INSERT INTO {db.fq(C.TBL_COUNTRIES)} ({', '.join(db.column(C.TBL_COUNTRIES, c) for c in cols)}) "
        f"SELECT {', '.join(_expr(C.TBL_COUNTRIES, c, ':v_' + c) for c in cols)} "
        f"WHERE NOT EXISTS (SELECT 1 FROM {db.fq(C.TBL_COUNTRIES)} WHERE `iso3` = :v_iso3)"
    )
    affected = db.execute(sql, {f"v_{c}": v for c, v in values.items()})
    if affected == 0:
        raise ServiceError(ERR_EXISTS)
    if ttl:
        _insert_row(C.TBL_CONTACTS, {"id": new_id(), "iso3": iso3, "role": C.FOCAL_ROLE, "name": ttl, "created_at": now})
    cache.clear()


@_guard_write
def update_country_full(iso3: str, update: Mapping[str, Any], baseline: str | None) -> None:
    """
    Save the full-record editor.

    Optimistic concurrency: `baseline` is the `updated_at` the form was rendered
    with. The UPDATE only applies while the row still carries that value, so two
    staff members can't silently overwrite each other.
    """
    values = dict(update)
    if values.get("last_updated") is None:
        values["last_updated"] = now_utc().date()  # default to today, like the original
    stamp = now_utc()
    values["updated_at"] = stamp

    sets = [f"{db.column(C.TBL_COUNTRIES, k)} = {_expr(C.TBL_COUNTRIES, k, ':v_' + k)}" for k in values]
    params: dict[str, Any] = {f"v_{k}": v for k, v in values.items()}
    params["iso3"] = iso3
    where = "`iso3` = :iso3"
    base_ts = parse_ts(baseline)
    if baseline and base_ts is not None:
        where += " AND (`updated_at` IS NULL OR `updated_at` = :baseline)"
        params["baseline"] = base_ts

    affected = db.execute(f"UPDATE {db.fq(C.TBL_COUNTRIES)} SET {', '.join(sets)} WHERE {where}", params)
    if affected == 0:
        if fetch_country_row(iso3) is None:
            raise ServiceError("Country not found.")
        raise ServiceError(P.EDITOR_STALE_MESSAGE)
    cache.clear()


@_guard_write
def set_reviewed(iso3: str, verified: bool) -> None:
    """Set (verified) or clear `reviewed_at` for the data-review tracker."""
    db.execute(
        f"UPDATE {db.fq(C.TBL_COUNTRIES)} SET `reviewed_at` = :ts WHERE `iso3` = :iso3",
        {"ts": now_utc() if verified else None, "iso3": iso3},
    )


# ═════════════════════════════════════════════════════════════════════════════
# WRITES — child records
# ═════════════════════════════════════════════════════════════════════════════
def _insert_row(table: str, values: Mapping[str, Any]) -> None:
    cols = list(values)
    db.execute(
        f"INSERT INTO {db.fq(table)} ({', '.join(db.column(table, c) for c in cols)}) "
        f"VALUES ({', '.join(_expr(table, c, ':v_' + c) for c in cols)})",
        {f"v_{c}": values[c] for c in cols},
    )


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _from_payload(table: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    """Convert a snapshotted JSON payload back into typed column values (whitelisted, minus id)."""
    out: dict[str, Any] = {}
    for col, typ in C.CHILD_TABLE_COLUMNS[table].items():
        if col == "id" or col not in payload:
            continue
        v = payload[col]
        if v is None or v == "":
            out[col] = None
        elif typ == "DATE":
            out[col] = parse_day(v)
        elif typ == "TIMESTAMP":
            out[col] = parse_ts(v)
        elif typ == "INT":
            out[col] = int(float(v))
        elif typ == "DOUBLE":
            out[col] = float(v)
        else:
            out[col] = str(v)
    return out


@_guard_write
def child_add(table: str, iso3: str, rec: Mapping[str, Any]) -> dict[str, Any]:
    """Insert a child record; returns the stored row."""
    _check_child_table(table)
    row = {"id": new_id(), "iso3": iso3, **rec, "created_at": now_utc()}
    _insert_row(table, row)
    if table == C.TBL_CONTACTS:
        _sync_contact_email(row)
    cache.clear()
    return row


@_guard_write
def child_update(table: str, iso3: str, record_id: str, rec: Mapping[str, Any]) -> None:
    """Partial update: only the keys in `rec` are written."""
    _check_child_table(table)
    if not record_id:
        raise ServiceError(ERR_INVALID)
    if rec:
        sets = [f"{db.column(table, k)} = {_expr(table, k, ':v_' + k)}" for k in rec]
        params: dict[str, Any] = {f"v_{k}": v for k, v in rec.items()}
        params.update({"rid": record_id, "iso3": iso3})
        db.execute(f"UPDATE {db.fq(table)} SET {', '.join(sets)} WHERE `id` = :rid AND `iso3` = :iso3", params)
    if table == C.TBL_CONTACTS:
        saved = db.query_one(
            f"SELECT * FROM {db.fq(table)} WHERE `id` = :rid AND `iso3` = :iso3", {"rid": record_id, "iso3": iso3}
        )
        if saved:
            _sync_contact_email(saved)
    cache.clear()


@_guard_write
def child_delete(table: str, iso3: str, record_id: str) -> None:
    """Snapshot the row into deleted_records (so it can be restored), then delete it."""
    _check_child_table(table)
    if not record_id:
        raise ServiceError("Nothing to delete (missing record id).")
    row = db.query_one(
        f"SELECT * FROM {db.fq(table)} WHERE `id` = :rid AND `iso3` = :iso3", {"rid": record_id, "iso3": iso3}
    )
    log_id: str | None = None
    if row:
        log_id = new_id()
        _insert_row(
            C.TBL_DELETED,
            {
                "id": log_id,
                "table_name": table,
                "iso3": iso3,
                "payload": json.dumps(row, default=_json_default),
                "deleted_at": now_utc(),
            },
        )
    try:
        db.execute(f"DELETE FROM {db.fq(table)} WHERE `id` = :rid AND `iso3` = :iso3", {"rid": record_id, "iso3": iso3})
    except db.DatabaseError:
        if log_id:  # don't leave an orphaned undo entry behind
            try:
                db.execute(f"DELETE FROM {db.fq(C.TBL_DELETED)} WHERE `id` = :id", {"id": log_id})
            except db.DatabaseError:
                pass
        raise
    cache.clear()


@_guard_write
def child_restore(table: str, iso3: str, restore_id: str) -> None:
    """Undo a delete: re-insert the snapshotted payload (with a fresh id), then drop the log entry."""
    _check_child_table(table)
    if not restore_id:
        raise ServiceError("Nothing to restore.")
    log = db.query_one(f"SELECT * FROM {db.fq(C.TBL_DELETED)} WHERE `id` = :id", {"id": restore_id})
    if not log or log.get("table_name") != table or log.get("iso3") != iso3:
        raise ServiceError("Could not find the deleted record to restore.")
    try:
        payload = json.loads(log["payload"]) if isinstance(log.get("payload"), str) else dict(log.get("payload") or {})
    except (ValueError, TypeError) as exc:
        raise ServiceError("The deleted record's snapshot is unreadable.") from exc
    values = _from_payload(table, payload)
    values["id"] = new_id()
    values["iso3"] = iso3
    values.setdefault("created_at", now_utc())
    _insert_row(table, values)
    db.execute(f"DELETE FROM {db.fq(C.TBL_DELETED)} WHERE `id` = :id", {"id": restore_id})
    cache.clear()


def _check_child_table(table: str) -> None:
    if table not in C.CHILD_TABLE_BY_NAME:
        raise ServiceError(ERR_INVALID)


def _sync_contact_email(saved: Mapping[str, Any]) -> None:
    """
    A World Bank person has ONE e-mail across every country they appear in. When a
    contact with an e-mail is saved, copy that e-mail to every other row with the
    same name (case/space-insensitive). Only non-empty e-mails propagate, and
    placeholder / very short names are never synced.
    """
    email, name = saved.get("email"), saved.get("name")
    if not (has_valid_email(email) and name and can_sync_email_for_name(name)):
        return
    key = str(name).strip().lower()
    same = db.query(
        f"SELECT `id`, `name`, `email`, `iso3` FROM {db.fq(C.TBL_CONTACTS)} WHERE LOWER(TRIM(`name`)) = :key",
        {"key": key},
    )
    ids = [
        r["id"]
        for r in same
        if r["id"] != saved.get("id") and same_contact_name(r.get("name"), name) and r.get("email") != email
    ]
    if not ids:
        return
    marks = ", ".join(f":id{i}" for i in range(len(ids)))
    params: dict[str, Any] = {f"id{i}": v for i, v in enumerate(ids)}
    params["email"] = email
    db.execute(f"UPDATE {db.fq(C.TBL_CONTACTS)} SET `email` = :email WHERE `id` IN ({marks})", params)
