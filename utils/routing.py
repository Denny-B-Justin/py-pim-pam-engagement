"""
routing.py — "/?page=<name>" URL helpers.

Every page of the site is served from the app root with a `page` query
parameter (e.g. `/?page=home`, `/?page=map`, `/?page=country-detail&iso=SRB`).
Links are always built through `page_url()` so they keep working when the app
is mounted under a path prefix (Posit Connect serves it at /content/<guid>/).
"""
from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlencode

import dash
from dash import dcc, html

import constants as C


def page_url(page: str, **params: Any) -> str:
    """Return the app-relative URL for a page, e.g. '/?page=country-detail&iso=SRB'."""
    query = {C.PAGE_QUERY_PARAM: page}
    query.update({k: v for k, v in params.items() if v not in (None, "")})
    return f"{dash.get_relative_path('/')}?{urlencode(query)}"


def page_search(page: str, **params: Any) -> str:
    """Return just the '?page=…' query string (what dcc.Location.search expects)."""
    query = {C.PAGE_QUERY_PARAM: page}
    query.update({k: v for k, v in params.items() if v not in (None, "")})
    return "?" + urlencode(query)


def parse_search(search: str | None) -> dict[str, str]:
    """Parse a '?a=1&b=2' string into {'a': '1', 'b': '2'} (first value wins)."""
    if not search:
        return {}
    parsed = parse_qs(search.lstrip("?"), keep_blank_values=False)
    return {k: v[0] for k, v in parsed.items() if v}


def link(children: Any, page: str, class_name: str = "", title: str | None = None, **params: Any) -> dcc.Link:
    """In-app link (client-side navigation, no full page reload)."""
    return dcc.Link(children, href=page_url(page, **params), className=class_name, refresh=False, title=title)


def external_link(children: Any, href: str, class_name: str = "", new_tab: bool = True, **kwargs: Any) -> html.A:
    extra = {"target": "_blank", "rel": "noreferrer"} if new_tab else {}
    return html.A(children, href=href, className=class_name, **extra, **kwargs)


def safe_next_search(next_value: str | None) -> str:
    """
    Validate the `next` parameter used after login so it can only ever point at
    one of our own pages. Returns a '?page=…' query string.
    """
    from pages import PAGES  # local import: pages import this module

    fallback = "?" + C.POST_LOGIN_QUERY
    if not next_value:
        return fallback
    parsed = parse_search(next_value)
    page = parsed.get(C.PAGE_QUERY_PARAM)
    if page not in PAGES or page == C.PAGE_LOGIN:
        return fallback
    iso = parsed.get("iso")
    if iso and not (iso.isalpha() and len(iso) == 3):
        return fallback
    return page_search(page, iso=iso)
