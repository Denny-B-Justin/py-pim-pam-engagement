"""release_notes.py — changelog  (/?page=release-notes).  Port of app/release-notes/page.tsx."""
from __future__ import annotations

from typing import Any

from dash import html

import constants as C
import page_constants as P
from utils.routing import external_link

PAGE = C.PAGE_RELEASE_NOTES
PROTECTED = False


def layout(params: dict[str, str]) -> Any:
    articles = [
        html.Article(
            [
                # timeline dot
                html.Span(className="absolute -left-[1.7rem] top-1.5 h-3 w-3 rounded-full border-2 border-white bg-brand-blue"),
                html.Div(
                    [
                        html.Span(n["version"], className="rounded bg-brand-tint px-2 py-0.5 text-xs font-bold text-brand-blue"),
                        html.Span(
                            n["category"],
                            className=f"rounded-full px-2 py-0.5 text-[11px] font-semibold {P.RELEASE_TAG_CLASSES[n['category']]}",
                        ),
                        html.Span(n["date"], className="text-xs text-gray-500"),
                    ],
                    className="flex flex-wrap items-center gap-2",
                ),
                html.H2(n["title"], className="mt-2 text-xl font-bold text-brand-navy"),
                html.Ul(
                    [
                        html.Li(
                            [
                                html.Span(className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-mid"),
                                html.Span(item),
                            ],
                            className="flex gap-2 text-sm leading-relaxed text-gray-700",
                        )
                        for item in n["items"]
                    ],
                    className="mt-3 space-y-2",
                ),
            ],
            className="relative",
        )
        for n in P.RELEASE_NOTES
    ]
    return html.Div(
        [
            html.P(P.RELEASE_EYEBROW, className="text-xs font-semibold uppercase tracking-widest text-brand-mid"),
            html.H1(P.RELEASE_TITLE, className="mt-3 text-4xl font-bold leading-tight text-brand-blue"),
            html.P(
                [
                    P.RELEASE_INTRO_PRE,
                    external_link("wkpgf-pimpam-digital-tools", P.PIM_PAM_NET_URL, "font-semibold text-brand-blue underline"),
                    ".",
                ],
                className="mt-4 max-w-2xl text-base leading-relaxed text-gray-700",
            ),
            html.Div(articles, className="mt-10 space-y-8 border-l-2 border-brand-line pl-6"),
        ],
        className="mx-auto max-w-3xl px-6 py-12",
    )
