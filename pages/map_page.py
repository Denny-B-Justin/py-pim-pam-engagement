"""
map_page.py — public engagement map  (/?page=map).  Port of app/map/page.tsx + MapClient.tsx.

The page only supplies the container and a JSON payload; the Leaflet logic lives in
assets/map.js and is started by a clientside callback.
"""
from __future__ import annotations

from typing import Any

import dash
from dash import Input, Output, dcc, html

import constants as C
import page_constants as P
from services import repository as repo
from utils import theme
from utils.routing import page_url

PAGE = C.PAGE_MAP
PROTECTED = False

DARK_FILL = ("Application", "Adoption")


def layout(params: dict[str, str]) -> Any:
    countries = repo.fetch_countries().countries
    payload = {
        "countries": countries,
        "colors": theme.STATUS_COLORS,
        "darkFill": list(DARK_FILL),
        "config": P.MAP_CONFIG,
        "geojsonUrl": dash.get_asset_url(P.MAP_CONFIG["geojsonFile"]),
        "detailHref": page_url(C.PAGE_COUNTRY_DETAIL, iso="__ISO__"),
    }
    return html.Div(
        [
            dcc.Store(id="pp-map-data", data=payload),
            dcc.Store(id="pp-map-ready"),
            html.Div(
                [
                    html.Div(id="pp-map", className="h-full w-full", style={"background": P.MAP_CONFIG["mapBackground"]}),
                    html.Div(
                        html.Span(
                            P.MAP_LOADING,
                            className="rounded-full bg-white/90 px-4 py-2 text-sm font-medium text-brand-blue shadow",
                        ),
                        id="pp-map-loading",
                        className="pointer-events-none absolute inset-0 flex items-center justify-center",
                    ),
                ],
                className="relative h-full w-full",
                role="region",
                **{"aria-label": P.MAP_ARIA_LABEL},
            ),
        ],
        # `isolate` keeps Leaflet's high z-index panes underneath the header's mobile menu
        className="relative isolate",
        style={"height": "calc(100vh - 130px)"},
    )


def register_callbacks(app) -> None:
    app.clientside_callback(
        """
        function (payload) {
            if (window.ppMap) { window.ppMap.render(payload); }
            return window.dash_clientside.no_update;
        }
        """,
        Output("pp-map-ready", "data"),
        Input("pp-map-data", "data"),
    )
