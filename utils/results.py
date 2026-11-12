"""
results.py — the little "result record" the admin write callbacks publish.

Every admin write (save a row, add a contact, delete a record …) happens in its own
callback, which stores one of these dicts in a per-row `dcc.Store`. A single refresh
callback per page listens to all those stores, shows the success / error banner and
re-renders whatever changed. `t` (microseconds, so it stays a safe JavaScript integer) is a
nonce so that two identical consecutive results still count as a change — and orders them: a
`dcc.Store` keeps its data when it is re-mounted, so a page that re-renders may see an OLD
result again; the refresh callbacks ignore any result that is not newer than the last one handled.
"""
from __future__ import annotations

import time
from typing import Any, Mapping

from dash import html

import page_constants as P
from services import auth
from services.validation import ServiceError
from utils.components import banner


def _stamp() -> int:
    return time.time_ns() // 1000


def ok(message: Any, refresh: bool = True, **extra: Any) -> dict[str, Any]:
    return {"ok": True, "msg": message, "refresh": refresh, "t": _stamp(), **extra}


def fail(message: str, **extra: Any) -> dict[str, Any]:
    return {"ok": False, "msg": message, "refresh": False, "t": _stamp(), **extra}


def needs_login() -> dict[str, Any]:
    """The session expired (or never existed) — the refresh callback sends the user to the sign-in page."""
    return {"ok": False, "auth": True, "msg": "Please sign in again.", "refresh": False, "t": _stamp()}


def guarded(fn):
    """
    Decorator for write callbacks: refuses without a valid staff session and turns
    ServiceError into a failed result, so callbacks never raise into the browser.
    """

    def wrapper(*args, **kwargs):
        if not auth.is_authenticated():
            return needs_login()
        try:
            return fn(*args, **kwargs)
        except ServiceError as exc:
            return fail(exc.message, code=exc.code)

    wrapper.__name__ = fn.__name__
    return wrapper


def error_text(code_or_message: str, mapping: Mapping[str, str] | None = None) -> str:
    """Map a short error code to its banner text; anything else is shown as 'Could not save: …'."""
    table = mapping if mapping is not None else P.ADMIN_ERRORS
    return table.get(code_or_message, f"Could not save: {code_or_message}")


def banner_from(result: Mapping[str, Any], mapping: Mapping[str, str] | None = None) -> html.Div:
    """Banner for a result record (ok → green, failure → red)."""
    if result.get("ok"):
        return banner("ok", result.get("msg"))
    code = result.get("code") or result.get("msg") or ""
    return banner("err", error_text(str(code), mapping))
