"""country_index.py — country directory  (/?page=country).  Port of app/country/page.tsx."""
from __future__ import annotations

import unicodedata
from typing import Any

from dash import html

import constants as C
import page_constants as P
from services import repository as repo
from utils import theme
from utils.routing import link

PAGE = C.PAGE_COUNTRY
PROTECTED = False


def _sort_key(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in folded if not unicodedata.combining(ch)).casefold()


def layout(params: dict[str, str]) -> Any:
    countries = repo.fetch_countries().countries

    # group by region — regions alphabetical, countries alphabetical (localeCompare-style)
    by_region: dict[str, list[dict[str, Any]]] = {}
    for c in sorted(countries, key=lambda c: _sort_key(c["name"])):
        by_region.setdefault(c["region"], []).append(c)
    regions = sorted(by_region)

    counts: dict[str, int] = {}
    for c in countries:
        counts[c["status"]] = counts.get(c["status"], 0) + 1

    legend = html.Div(
        [
            html.Span(
                [
                    html.Span(className="inline-block h-3 w-4 rounded-sm", style={"background": theme.status_color(s)}),
                    f"{s} ",
                    html.Span(str(counts.get(s, 0)), className="font-semibold text-brand-blue"),
                ],
                className="flex items-center gap-1.5",
            )
            for s in C.ENGAGEMENT_STATUSES
        ],
        className="mt-4 flex flex-wrap gap-4 text-xs text-gray-600",
    )

    sections = [
        html.Section(
            [
                html.H2(region, className="text-xs font-bold uppercase tracking-widest text-brand-mid"),
                html.Div(
                    [
                        link(
                            [
                                html.Span(
                                    [
                                        html.Span(
                                            className="inline-block h-2.5 w-2.5 shrink-0 rounded-full",
                                            style={"background": theme.status_color(c["status"])},
                                            title=c["status"],
                                        ),
                                        c["name"],
                                        html.Span(c["iso3"], className="text-xs font-normal text-gray-400"),
                                    ],
                                    className="flex items-center gap-2 font-semibold text-brand-navy",
                                ),
                                html.Span(c["status"], className="shrink-0 text-xs text-gray-500"),
                            ],
                            C.PAGE_COUNTRY_DETAIL,
                            "flex items-center justify-between gap-2 rounded-lg border border-brand-line bg-white px-4 py-3 hover:border-brand-blue hover:shadow-sm",
                            iso=c["iso3"],
                        )
                        for c in by_region[region]
                    ],
                    className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3",
                ),
            ]
        )
        for region in regions
    ]

    return html.Div(
        [
            html.P(P.COUNTRY_INDEX_EYEBROW, className="text-xs font-semibold uppercase tracking-widest text-brand-mid"),
            html.H1(P.COUNTRY_INDEX_TITLE, className="mt-1 text-3xl font-bold text-brand-blue"),
            html.P(
                P.COUNTRY_INDEX_INTRO.format(n=len(countries), r=len(regions)),
                className="mt-2 max-w-2xl text-sm text-gray-600",
            ),
            legend,
            html.Div(sections, className="mt-8 space-y-8"),
        ],
        className="mx-auto max-w-5xl px-6 py-10",
    )
