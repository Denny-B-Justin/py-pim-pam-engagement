"""home.py — landing page  (/?page=home).  Port of app/page.tsx."""
from __future__ import annotations

from typing import Any

from dash import html

import constants as C
import page_constants as P
from services import repository as repo
from utils import theme
from utils.routing import link

PAGE = C.PAGE_HOME
PROTECTED = False


def layout(params: dict[str, str]) -> Any:
    countries = repo.fetch_countries().countries
    counts: dict[str, int] = {}
    for c in countries:
        counts[c["status"]] = counts.get(c["status"], 0) + 1

    hero = html.Section(
        [
            html.Div(
                [
                    html.P(P.HOME_EYEBROW, className="text-xs font-semibold uppercase tracking-widest text-brand-mid"),
                    html.H1(P.HOME_TITLE, className="mt-3 text-4xl font-bold leading-tight text-brand-blue"),
                    html.P(P.HOME_INTRO, className="mt-4 text-base leading-relaxed text-gray-700"),
                    html.Div(
                        [
                            link(
                                P.HOME_CTA_PRIMARY,
                                C.PAGE_MAP,
                                "rounded bg-brand-blue px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-navy",
                            ),
                            link(P.HOME_CTA_SECONDARY, C.PAGE_LOGIN, theme.BTN_OUTLINE),
                        ],
                        className="mt-6 flex flex-wrap items-center gap-3",
                    ),
                ]
            ),
            html.Div(
                [
                    html.P(P.HOME_GLANCE_LABEL, className="text-xs font-semibold uppercase tracking-wider text-gray-500"),
                    html.P(f"{len(countries)} countries", className="mt-1 text-2xl font-bold text-brand-blue"),
                    html.Ul(
                        [
                            html.Li(
                                [
                                    html.Span(
                                        [
                                            html.Span(className=f"inline-block h-3 w-5 rounded-sm {theme.STATUS_SWATCH_CLASSES[s]}"),
                                            html.Span(s, className="text-gray-700"),
                                        ],
                                        className="flex items-center gap-2",
                                    ),
                                    html.Span(str(counts.get(s, 0)), className="font-semibold text-brand-blue"),
                                ],
                                className="flex items-center justify-between text-sm",
                            )
                            for s in C.ENGAGEMENT_STATUSES
                        ],
                        className="mt-4 space-y-2",
                    ),
                    html.P(P.HOME_GLANCE_NOTE, className="mt-4 text-xs italic text-gray-500"),
                ],
                className="rounded-2xl border border-gray-200 bg-gray-50 p-6",
            ),
        ],
        className="grid grid-cols-1 gap-10 md:grid-cols-2 md:items-center",
    )

    cards = html.Section(
        [
            html.Div(
                [
                    html.H3(card["title"], className="text-sm font-bold uppercase tracking-wider text-brand-mid"),
                    html.P(card["body"], className="mt-2 text-sm text-gray-700"),
                    link(
                        f"{card['cta']} →",
                        card["page"],
                        "mt-3 inline-block text-sm font-semibold text-brand-blue hover:text-brand-navy",
                    ),
                ],
                className="rounded-xl border border-gray-200 p-5 hover:border-brand-blue",
            )
            for card in P.HOME_CARDS
        ],
        className="mt-16 grid grid-cols-1 gap-6 md:grid-cols-3",
    )

    return html.Div([hero, cards], className="mx-auto max-w-6xl px-6 py-12")
