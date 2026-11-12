"""
auth.py — the shared-password gate.

Same model as the original site: one shared staff password, no per-user identity.
The original stored an HMAC-signed `pp_session` cookie; here Flask's signed,
HttpOnly session cookie plays that role (signed with APP_COOKIE_SECRET, valid for
7 days). The cookie is set from a Dash callback, so no custom Flask route is needed.

Every callback that reads staff data or writes to the database MUST call
`is_authenticated()` itself — hiding a page in the UI is not enough.
"""
from __future__ import annotations

import hmac
import time

from flask import has_request_context, session

import constants as C

_SESSION_KEY = "pp_ok"
_ISSUED_KEY = "pp_iat"

LOGIN_OK = "ok"
LOGIN_BAD_PASSWORD = "bad"
LOGIN_NOT_CONFIGURED = "unconfigured"


def is_configured() -> bool:
    """Both the shared password and the cookie-signing secret must be set."""
    return bool(C.APP_PASSWORD and C.APP_COOKIE_SECRET)


def safe_equal(a: str, b: str) -> bool:
    """Constant-time string comparison (does not leak how much of the password matched)."""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def login(password: str | None) -> str:
    """Validate the shared password and start a session. Returns one of the LOGIN_* codes."""
    if not is_configured():
        return LOGIN_NOT_CONFIGURED
    if not safe_equal(password or "", C.APP_PASSWORD):
        return LOGIN_BAD_PASSWORD
    session.clear()
    session[_SESSION_KEY] = True
    session[_ISSUED_KEY] = int(time.time())
    session.permanent = True  # honours PERMANENT_SESSION_LIFETIME (7 days)
    return LOGIN_OK


def logout() -> None:
    if has_request_context():
        session.clear()


def is_authenticated() -> bool:
    """True when the current request carries a valid staff session."""
    if not has_request_context() or not is_configured():
        return False
    if session.get(_SESSION_KEY) is not True:
        return False
    issued = session.get(_ISSUED_KEY)
    if not isinstance(issued, int):
        return False
    return (time.time() - issued) < C.SESSION_MAX_AGE_SECONDS
