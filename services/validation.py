"""
validation.py — server-side validation and normalisation.

Ports `lib/validation.ts` and the parsing rules of the original API routes
(`/api/admin/child`, `/country-update`, `/create`, `/update`). Nothing here talks
to the database, so every rule can be exercised in isolation.

Every function returns data or raises `ServiceError`; page callbacks turn the
error into a banner (see `ADMIN_ERRORS` / `EDITOR_ERRORS` in page_constants.py).
"""
from __future__ import annotations

import math
import re
from datetime import date, datetime
from typing import Any, Mapping

import constants as C

# ── errors ──────────────────────────────────────────────────────────────────
ERR_INVALID = "invalid"
ERR_BAD_ISO = "badiso"
ERR_EXISTS = "exists"
ERR_NO_DB = "nodb"


class ServiceError(Exception):
    """A user-presentable failure. `code` is a short key or a full message."""

    def __init__(self, code: str, message: str | None = None) -> None:
        super().__init__(message or code)
        self.code = code
        self.message = message or code


# ── primitives ──────────────────────────────────────────────────────────────
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)
_ISO3_RE = re.compile(r"^[A-Z]{3}$")
# JavaScript's Number("…") grammar for decimal literals — Python's float() is looser
# (it accepts "nan", "inf", "1_000"), which the original never did.
_NUMBER_RE = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")


def as_text(value: Any) -> str:
    """Coerce a callback value to text (None → '')."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):  # e.g. a dcc.Checklist value
        return ",".join(str(v) for v in value)
    return str(value)


def normalise_iso3(raw: Any) -> str:
    return as_text(raw).strip().upper()


def is_valid_iso3(iso3: str) -> bool:
    return bool(_ISO3_RE.match(iso3))


def parse_number(raw: str) -> float | None:
    """JS-style Number(): a finite float, or None when `raw` is not a number."""
    text = raw.strip()
    if not _NUMBER_RE.match(text):
        return None
    value = float(text)
    return value if math.isfinite(value) else None


def parse_date(raw: str) -> date | None:
    try:
        return datetime.strptime(raw.strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def count_words(text: str) -> int:
    return len(text.split())


def is_checked(value: Any) -> bool:
    """A dcc.Checklist value (['true'] / []) → bool."""
    if isinstance(value, (list, tuple)):
        return "true" in [str(v).lower() for v in value]
    return str(value).lower() in {"true", "1", "yes", "on"}


# ── child-record fields (lib/validation.ts · fieldError) ────────────────────
def field_error(f: C.ChildField, raw: str) -> str | None:
    """Human-readable error if `raw` is invalid for the field, else None. Empty is always fine."""
    if raw == "":
        return None
    if f.type == "number":
        n = parse_number(raw)
        if n is None:
            return f"“{f.label}” must be a number."
        if n < 0:
            return f"“{f.label}” can’t be negative."
        if f.key == "year":
            if not (C.YEAR_MIN <= n <= C.YEAR_MAX):
                return f"“{f.label}” must be a year between {C.YEAR_MIN} and {C.YEAR_MAX}."
            if n != int(n):
                return f"“{f.label}” must be a whole year."
    elif f.type == "url" and not _URL_RE.match(raw):
        return f"“{f.label}” must start with http:// or https://"
    elif f.type == "email" and not _EMAIL_RE.match(raw):
        return f"“{f.label}” is not a valid e-mail address."
    elif f.type == "date" and parse_date(raw) is None:
        return f"“{f.label}” must be a valid date (YYYY-MM-DD)."
    return None


def can_sync_email_for_name(name: str | None) -> bool:
    """True when a contact name is real enough to safely broadcast an e-mail by name."""
    t = (name or "").strip().lower()
    return len(t) >= C.MIN_SYNC_NAME_LEN and t not in C.SYNC_SENTINELS


def same_contact_name(a: str | None, b: str | None) -> bool:
    return (a or "").strip().lower() == (b or "").strip().lower()


def has_valid_email(value: Any) -> bool:
    return isinstance(value, str) and "@" in value


def build_child_record(cfg: C.ChildTable, values: Mapping[str, Any], action: str) -> dict[str, Any]:
    """
    Whitelist, validate and convert the submitted fields of a child record.

    * action == "add"    — every configured field is read.
    * action == "update" — only fields present in `values` are touched, so a
      partial edit (e.g. just the e-mail on the /admin list) never blanks the rest.
    """
    rec: dict[str, Any] = {}
    for f in cfg.fields:
        if action == "update" and f.key not in values:
            continue
        raw = as_text(values.get(f.key)).strip()
        err = field_error(f, raw)
        if err:
            raise ServiceError(err)
        if raw == "":
            rec[f.key] = None
        elif f.type == "number":
            n = parse_number(raw)
            rec[f.key] = int(n) if (f.key == "year" and n is not None) else n
        elif f.type == "date":
            rec[f.key] = parse_date(raw)
        else:
            rec[f.key] = raw
    for f in cfg.fields:
        if not f.required:
            continue
        if action == "update" and f.key not in values:
            continue
        if not rec.get(f.key):
            raise ServiceError(ERR_INVALID)
    return rec


# ── country: quick edit / create ────────────────────────────────────────────
def clean_country_basics(values: Mapping[str, Any], *, require_valid_iso3: bool) -> dict[str, Any]:
    """Validate the fields shared by the /admin quick-edit row and the add form."""
    iso3 = normalise_iso3(values.get("iso3"))
    name = as_text(values.get("name")).strip()
    region = as_text(values.get("region")).strip()
    status = as_text(values.get("status")).strip()
    if require_valid_iso3 and not is_valid_iso3(iso3):
        raise ServiceError(ERR_BAD_ISO)
    if not iso3 or not name or not region or status not in C.ENGAGEMENT_STATUSES:
        raise ServiceError(ERR_INVALID)
    return {
        "iso3": iso3,
        "name": name,
        "region": region,
        "status": status,
        "ttl": as_text(values.get("ttl")).strip(),
        "focus_note": as_text(values.get("focus_note")),
    }


# ── country: full-record editor (api/admin/country-update) ──────────────────
def clean_country_update(values: Mapping[str, Any]) -> dict[str, Any]:
    """
    Build the UPDATE payload from the submitted editor fields.

    Only keys present in `values` are written; booleans arrive as dcc.Checklist
    values; text is trimmed ('' → NULL); word limits are enforced.
    """
    update: dict[str, Any] = {}
    for f in C.COUNTRY_FIELDS:
        if f.key not in values:
            continue
        raw = values[f.key]
        if f.key == "status":
            status = as_text(raw)
            if status not in C.ENGAGEMENT_STATUSES:
                raise ServiceError(ERR_INVALID)
            update["status"] = status
        elif f.type == "boolean":
            update[f.key] = is_checked(raw)
        elif f.type == "number":
            n = parse_number(as_text(raw))
            update[f.key] = n
        elif f.type == "date":
            text = as_text(raw).strip()
            if text == "":
                update[f.key] = None
            else:
                d = parse_date(text)
                if d is None:
                    raise ServiceError(f"“{f.label}” must be a valid date (YYYY-MM-DD).")
                update[f.key] = d
        else:
            text = as_text(raw).strip()
            if f.word_limit and text:
                words = count_words(text)
                if words > f.word_limit:
                    raise ServiceError(
                        f"“{f.label}” is {words} words — the limit is {f.word_limit}. Please shorten it."
                    )
            update[f.key] = text or None
    # name / region must never be blanked
    if "name" in update and update["name"] is None:
        raise ServiceError(ERR_INVALID)
    if "region" in update and update["region"] is None:
        raise ServiceError(ERR_INVALID)
    return update
