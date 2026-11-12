"""about.py — about the program  (/?page=about).  Port of app/about/page.tsx."""
from __future__ import annotations

from typing import Any

from dash import html

import constants as C
import page_constants as P
from utils import theme
from utils.components import rich
from utils.routing import external_link, link

PAGE = C.PAGE_ABOUT
PROTECTED = False


def _cell(label: str, body: str, accent: bool = False) -> html.Div:
    return html.Div(
        [
            html.P(
                label,
                className="text-[10px] font-bold uppercase tracking-widest " + ("text-brand-blue" if accent else "text-brand-mid"),
            ),
            html.P(body, className="mt-2 text-sm leading-relaxed text-gray-700"),
        ],
        className="p-5 " + ("bg-brand-tint/30" if accent else "bg-white"),
    )


def layout(params: dict[str, str]) -> Any:
    measure, gap, action = P.ABOUT_COL_LABELS
    return html.Div(
        [
            # Hero
            html.P(P.ABOUT_EYEBROW, className="text-xs font-semibold uppercase tracking-widest text-brand-mid"),
            html.H1(P.ABOUT_TITLE, className="mt-3 max-w-3xl text-4xl font-bold leading-tight text-brand-blue"),
            html.P(P.ABOUT_INTRO, className="mt-5 max-w-3xl text-lg leading-relaxed text-gray-700"),
            # Approach
            html.Section(
                [
                    html.H2(P.ABOUT_APPROACH_TITLE, className="text-2xl font-bold text-brand-blue"),
                    html.P(rich(P.ABOUT_APPROACH_BODY), className="mt-3 max-w-3xl text-base leading-relaxed text-gray-700"),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span(
                                        str(i + 1),
                                        className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-blue text-sm font-bold text-white",
                                    ),
                                    html.H3(p["t"], className="mt-3 text-base font-bold text-brand-navy"),
                                    html.P(p["d"], className="mt-2 text-sm leading-relaxed text-gray-700"),
                                ],
                                className="rounded-xl border border-brand-line p-5",
                            )
                            for i, p in enumerate(P.ABOUT_PILLARS)
                        ],
                        className="mt-6 grid grid-cols-1 gap-5 md:grid-cols-3",
                    ),
                ],
                className="mt-14",
            ),
            # What this site demonstrates
            html.Section(
                [
                    html.H2(P.ABOUT_DEMO_TITLE, className="text-2xl font-bold text-brand-blue"),
                    html.P(rich(P.ABOUT_DEMO_BODY), className="mt-3 max-w-3xl text-base leading-relaxed text-gray-700"),
                ],
                className="mt-14 rounded-2xl bg-brand-tint/40 p-7",
            ),
            # Eight issues
            html.Section(
                [
                    html.H2(P.ABOUT_ISSUES_TITLE, className="text-2xl font-bold text-brand-blue"),
                    html.P(P.ABOUT_ISSUES_INTRO, className="mt-2 text-sm text-gray-600"),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Span(
                                                str(it["n"]),
                                                className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-blue text-sm font-bold text-white",
                                            ),
                                            html.H3(it["issue"], className="text-base font-bold text-brand-navy"),
                                        ],
                                        className="flex items-center gap-3 border-b border-brand-line bg-brand-tint/50 px-5 py-3",
                                    ),
                                    html.Div(
                                        [
                                            _cell(measure, it["measure"]),
                                            _cell(gap, it["gap"]),
                                            _cell(action, it["action"], accent=True),
                                        ],
                                        className="grid grid-cols-1 gap-px bg-brand-line sm:grid-cols-3",
                                    ),
                                ],
                                className="overflow-hidden rounded-xl border border-brand-line",
                            )
                            for it in P.ABOUT_ISSUES
                        ],
                        className="mt-6 space-y-5",
                    ),
                ],
                className="mt-14",
            ),
            # Knowledge session
            html.Section(
                [
                    html.P(P.ABOUT_KNOWLEDGE_EYEBROW, className="text-xs font-semibold uppercase tracking-widest text-brand-mid"),
                    html.H2(P.ABOUT_KNOWLEDGE_TITLE, className="mt-2 text-2xl font-bold text-brand-blue"),
                    html.P(rich(P.ABOUT_KNOWLEDGE_P1), className="mt-3 max-w-3xl text-base leading-relaxed text-gray-700"),
                    html.P(rich(P.ABOUT_KNOWLEDGE_P2), className="mt-3 max-w-3xl text-base leading-relaxed text-gray-700"),
                    html.Div(
                        [
                            link(P.ABOUT_CTA_MAP, C.PAGE_MAP, "rounded bg-brand-blue px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-navy"),
                            external_link(P.ABOUT_CTA_SITE, P.PIM_PAM_NET_URL, theme.BTN_OUTLINE),
                        ],
                        className="mt-6 flex flex-wrap gap-3",
                    ),
                ],
                className="mt-14 rounded-2xl border border-brand-line bg-white p-7",
            ),
        ],
        className="mx-auto max-w-5xl px-6 py-12",
    )
