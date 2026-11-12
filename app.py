"""
app.py — entry point of the PIM-PAM engagement site (Dash, for Posit Connect).

    local :  python app.py            (reads ./.env)
    Connect: manifest.json  →  entrypoint "app:app"

Every page is served from the app root with a query string:
    /?page=home   /?page=map   /?page=country-detail&iso=SRB   /?page=admin-review …
A single router callback turns `?page=` into the page's layout; protected (staff) pages
send visitors without a valid session to /?page=login&next=<the page they asked for>.
"""
from __future__ import annotations

import logging
import os
import threading
from datetime import timedelta
from typing import Any

import dash
from dash import Input, Output, no_update
from dash.exceptions import PreventUpdate

import constants as C
import page_constants as P
import pages
from services import auth
from services import repository as repo
from utils import layout
from utils.routing import page_search, parse_search

logging.basicConfig(level=getattr(logging, C.LOG_LEVEL, logging.INFO), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("pimpam")

app = dash.Dash(
    __name__,
    use_pages=False,  # a `pages/` folder exists, but routing is the single ?page= router below
    suppress_callback_exceptions=True,  # page layouts are rendered by the router
    title=P.SITE_TITLE,
    update_title=None,
    assets_folder=str(C.ASSETS_DIR),
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.index_string = layout.build_index_string()
server = app.server  # what gunicorn / Posit Connect serve


# ── session cookie (staff sign-in) ──────────────────────────────────────────
def _configure_session() -> None:
    server.secret_key = C.APP_COOKIE_SECRET or os.urandom(32)  # sign-in is disabled without a real secret
    # Every Posit Connect item is served from the same host, so give this app's cookie its own name.
    guid = os.getenv("CONNECT_CONTENT_GUID", "")[:8]
    server.config.update(
        SESSION_COOKIE_NAME=f"{C.SESSION_COOKIE_NAME}_{guid}" if guid else C.SESSION_COOKIE_NAME,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=C.SESSION_COOKIE_SECURE,
        PERMANENT_SESSION_LIFETIME=timedelta(seconds=C.SESSION_MAX_AGE_SECONDS),
    )
    if not auth.is_configured():
        log.warning("APP_PASSWORD / APP_COOKIE_SECRET are not set — staff sign-in is disabled.")


_configure_session()
app.layout = layout.shell
pages.register_callbacks(app)

# Warm the country-list cache in the background so the first visitor does not wait for the warehouse.
threading.Thread(target=repo.fetch_countries, name="pp-warmup", daemon=True).start()


# ── router ──────────────────────────────────────────────────────────────────
@app.callback(
    Output("page-content", "children"),
    Output("pp-title", "data"),
    Output("pp-url", "search"),
    Input("pp-url", "search"),
)
def route(search: str | None) -> tuple[Any, Any, Any]:
    params = parse_search(search)
    name = params.get(C.PAGE_QUERY_PARAM) or C.DEFAULT_PAGE
    module = pages.PAGES.get(name)
    if module is None:
        name, module = C.PAGE_NOT_FOUND, pages.PAGES[C.PAGE_NOT_FOUND]
    if module.PROTECTED and not auth.is_authenticated():
        # Show the sign-in page right here AND put its address in the bar. (A callback is not
        # re-triggered by its own output, so merely changing the URL would leave the page blank.)
        wanted = page_search(name, iso=params.get("iso"))
        login_page = pages.PAGES[C.PAGE_LOGIN]
        content = login_page.layout({C.PAGE_QUERY_PARAM: C.PAGE_LOGIN, "next": wanted})
        return content, P.PAGE_TITLES.get(C.PAGE_LOGIN, P.SITE_TITLE), page_search(C.PAGE_LOGIN, next=wanted)
    try:
        content = module.layout(params)
    except Exception:  # a page must never leave the visitor with a blank screen
        log.exception("Page %s failed to render", name)
        content = layout.error_panel("Sorry — this page could not be displayed. Please try again.")
    return content, P.PAGE_TITLES.get(name, P.SITE_TITLE), no_update


# browser-tab title
app.clientside_callback(
    """
    function (title) {
      if (title) { document.title = title; }
      return false;
    }
    """,
    Output("pp-title", "clear_data"),
    Input("pp-title", "data"),
)


# "Sign out" button (present on the staff pages)
@app.callback(
    Output("pp-url", "search", allow_duplicate=True),
    Input("pp-signout", "n_clicks"),
    prevent_initial_call=True,
)
def sign_out(n_clicks: int | None) -> str:
    if not n_clicks:
        raise PreventUpdate
    auth.logout()
    return page_search(C.PAGE_HOME)


if __name__ == "__main__":
    app.run(host=C.HOST, port=C.PORT, debug=C.DEBUG)
