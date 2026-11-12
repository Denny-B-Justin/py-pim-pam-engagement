"""
layout.py — the application shell (header, main, footer) and HTML template.

Ported from the original `app/layout.tsx`. The shell is rendered once; the
`#page-content` element is swapped by the router callback in app.py.
"""
from __future__ import annotations

from typing import Any

import dash
from dash import dcc, html

import constants as C
import page_constants as P
from utils.routing import link


def build_index_string() -> str:
    """HTML document template (title, description, OpenGraph / Twitter tags, favicon)."""
    og = ""
    if C.SITE_URL:
        image = f"{C.SITE_URL}/assets/{P.OG_IMAGE_FILE}"
        og = f"""
        <meta property="og:title" content="{P.SITE_TITLE}">
        <meta property="og:description" content="{P.SITE_DESC}">
        <meta property="og:url" content="{C.SITE_URL}">
        <meta property="og:site_name" content="{P.SITE_NAME}">
        <meta property="og:type" content="website">
        <meta property="og:image" content="{image}">
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" content="{P.SITE_TITLE}">
        <meta name="twitter:description" content="{P.SITE_DESC}">
        <meta name="twitter:image" content="{image}">"""
    return f"""<!DOCTYPE html>
<html lang="en">
    <head>
        {{%metas%}}
        <title>{{%title%}}</title>
        <meta name="description" content="{P.SITE_DESC}">{og}
        <link rel="icon" type="image/svg+xml" href="assets/icon.svg">
        {{%css%}}
    </head>
    <body class="font-sans antialiased text-ink">
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>"""


# ── header ──────────────────────────────────────────────────────────────────
def _brand() -> Any:
    return link(
        [
            html.Img(
                src=dash.get_asset_url(P.LOGO_FILE),
                alt=P.LOGO_ALT,
                width=P.LOGO_WIDTH,
                height=P.LOGO_HEIGHT,
                className="h-8 w-auto sm:h-9",
            ),
            html.Span(className="hidden h-8 w-px bg-brand-line sm:block"),
            html.Span(
                [
                    html.Span(P.HEADER_BRAND_TITLE, className="font-heading text-sm font-bold tracking-tight text-brand-blue"),
                    html.Span(P.HEADER_BRAND_SUBTITLE, className="text-[11px] uppercase tracking-wider text-brand-mid"),
                ],
                className="hidden flex-col leading-tight sm:flex",
            ),
        ],
        C.PAGE_HOME,
        "flex items-center gap-3 hover:opacity-80",
    )


def _desktop_nav() -> html.Nav:
    items: list[Any] = []
    for label, page in P.NAV_LINKS:
        # "Release notes" is hidden below the `lg` breakpoint on desktop (as in the original)
        cls = "hidden hover:text-brand-navy lg:inline" if page == C.PAGE_RELEASE_NOTES else "hover:text-brand-navy"
        items.append(link(label, page, cls))
    items.append(link(P.NAV_CTA_LABEL, C.PAGE_LOGIN, "rounded bg-brand-blue px-3 py-1.5 text-white hover:bg-brand-navy"))
    return html.Nav(items, className="hidden items-center gap-5 text-sm font-medium text-brand-blue sm:flex")


def _mobile_nav() -> html.Details:
    """No-JS disclosure menu so every link is reachable on phones."""
    links = [link(label, page, "block px-4 py-2 hover:bg-brand-tint/50") for label, page in P.NAV_LINKS]
    links.append(link(P.NAV_CTA_LABEL, C.PAGE_LOGIN, "block px-4 py-2 hover:bg-brand-tint/50"))
    return html.Details(
        [
            html.Summary(
                html.Img(src=dash.get_asset_url("menu.svg"), alt="", width=24, height=24),
                className="flex cursor-pointer list-none items-center rounded p-1.5 text-brand-blue [&::-webkit-details-marker]:hidden",
                **{"aria-label": "Open menu"},
            ),
            html.Div(
                links,
                className="absolute right-0 z-20 mt-2 w-48 overflow-hidden rounded-lg border border-brand-line bg-white py-1 text-sm font-medium text-brand-blue shadow-lg",
            ),
        ],
        className="pp-mobile-menu relative sm:hidden",
    )


def header() -> html.Header:
    return html.Header(
        html.Div(
            [_brand(), _desktop_nav(), _mobile_nav()],
            className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-3",
        ),
        className="border-b border-brand-line bg-white",
    )


def footer() -> html.Footer:
    return html.Footer(
        html.Div(
            [html.Span(P.FOOTER_LEFT), html.Span(P.FOOTER_RIGHT)],
            className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-6 py-4 text-xs text-brand-mid",
        ),
        className="mt-12 border-t border-brand-line bg-brand-tint/40",
    )


def shell() -> html.Div:
    """The whole application layout."""
    return html.Div(
        [
            dcc.Location(id="pp-url", refresh=False),
            dcc.Store(id="pp-title"),
            header(),
            # Only the router's own swap of #page-content shows the spinner — callbacks that update
            # something *inside* a page (a save message, a table) must not blank the whole page.
            dcc.Loading(
                html.Main(id="page-content"),
                type="circle",
                color="#374291",
                delay_show=400,
                target_components={"page-content": "children"},
                parent_className="pp-loading",
            ),
            footer(),
        ]
    )


def error_panel(message: str) -> html.Div:
    return html.Div(
        html.Div(message, className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900"),
        className="mx-auto max-w-3xl px-6 py-12",
    )
