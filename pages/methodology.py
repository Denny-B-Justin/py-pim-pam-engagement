"""methodology.py — approach, progression model, FMUP results  (/?page=methodology).  Port of app/methodology/page.tsx."""
from __future__ import annotations

from typing import Any, Sequence

from dash import html

import constants as C
import page_constants as P
from utils import theme
from utils.components import rich
from utils.routing import link

PAGE = C.PAGE_METHODOLOGY
PROTECTED = False


def _results_table(rows: Sequence[dict[str, Any]]) -> html.Div:
    head = html.Thead(
        html.Tr(
            [html.Th("Indicator", className="border-b border-brand-line px-4 py-2 text-left text-xs font-bold uppercase tracking-wider text-brand-blue")]
            + [
                html.Th(
                    col,
                    className="w-20 border-b border-l border-brand-line px-3 py-2 text-center text-xs font-bold uppercase tracking-wider text-brand-blue",
                )
                for col in P.METHOD_FMUP_COLS
            ],
            className="bg-brand-tint",
        )
    )
    body_rows = []
    for r in rows:
        is_output = r.get("kind") == "output"
        label: list[Any] = []
        if is_output:
            label.append(
                html.Span(
                    "Output",
                    className="mr-2 rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-gray-500",
                )
            )
        label.append(r["label"].removeprefix("Output — ") if is_output else r["label"])
        last = len(r["vals"]) - 1
        body_rows.append(
            html.Tr(
                [html.Td(label, className="border-b border-brand-line px-4 py-3 leading-relaxed text-gray-700")]
                + [
                    html.Td(
                        str(v),
                        className="border-b border-l border-brand-line px-3 py-3 text-center tabular-nums "
                        + ("font-bold text-brand-blue" if i == last else "text-gray-700"),
                    )
                    for i, v in enumerate(r["vals"])
                ],
                className="align-top",
            )
        )
    return html.Div(
        html.Table([head, html.Tbody(body_rows)], className="min-w-[640px] w-full border-collapse text-sm"),
        className="overflow-x-auto rounded-b-lg border border-t-0 border-brand-line",
    )


def layout(params: dict[str, str]) -> Any:
    narrative = html.Div(
        [
            html.Section(
                [html.H2(s["h"], className="text-2xl font-bold text-brand-blue")]
                + [html.P(para, className="mt-3 max-w-3xl text-base leading-relaxed text-gray-700") for para in s["p"]]
            )
            for s in P.METHOD_SECTIONS
        ],
        className="mt-12 space-y-10",
    )

    progression = html.Section(
        [
            html.H2(P.METHOD_PROGRESSION_TITLE, className="text-2xl font-bold text-brand-blue"),
            html.P(rich(P.METHOD_PROGRESSION_INTRO), className="mt-3 max-w-3xl text-base leading-relaxed text-gray-700"),
            html.Div(
                html.Table(
                    [
                        html.Thead(
                            html.Tr(
                                [html.Th(className="w-32 border-b border-brand-line bg-brand-tint px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-brand-blue")]
                                + [
                                    html.Th(
                                        name,
                                        className="border-b border-l border-brand-line px-4 py-3 text-left text-sm font-bold",
                                        style={"background": bg, "color": fg},
                                    )
                                    for name, bg, fg in P.METHOD_STAGES
                                ]
                            )
                        ),
                        html.Tbody(
                            [
                                html.Tr(
                                    [html.Th(r["row"], className="border-b border-brand-line bg-brand-tint/50 px-4 py-3 text-left text-sm font-bold text-brand-navy")]
                                    + [
                                        html.Td(rich(cell), className="border-b border-l border-brand-line px-4 py-3 leading-relaxed text-gray-700")
                                        for cell in r["cells"]
                                    ],
                                    className="align-top",
                                )
                                for r in P.METHOD_PROGRESSION
                            ]
                        ),
                    ],
                    className="min-w-[720px] w-full border-collapse text-sm",
                ),
                className="mt-6 overflow-x-auto rounded-xl border border-brand-line",
            ),
        ],
        className="mt-16",
    )

    fmup = html.Section(
        [
            html.H2(P.METHOD_FMUP_TITLE, className="text-2xl font-bold text-brand-blue"),
            html.P(P.METHOD_FMUP_INTRO, className="mt-3 max-w-3xl text-base leading-relaxed text-gray-700"),
            html.H3(P.METHOD_MODULE1_TITLE, className="mt-8 rounded-t-lg bg-brand-blue px-4 py-2.5 text-sm font-bold text-white"),
            _results_table(P.METHOD_OUTCOME_ROWS),
            html.H3(P.METHOD_COMPONENT_TITLE, className="mt-10 rounded-t-lg bg-brand-blue px-4 py-2.5 text-sm font-bold text-white"),
            _results_table(P.METHOD_COMPONENT_ROWS),
        ],
        className="mt-16",
    )

    return html.Div(
        [
            html.P(P.METHOD_EYEBROW, className="text-xs font-semibold uppercase tracking-widest text-brand-mid"),
            html.H1(P.METHOD_TITLE, className="mt-3 max-w-3xl text-4xl font-bold leading-tight text-brand-blue"),
            html.P(P.METHOD_INTRO, className="mt-5 max-w-3xl text-lg leading-relaxed text-gray-700"),
            narrative,
            progression,
            fmup,
            html.Div(
                [
                    link(P.METHOD_CTA_MAP, C.PAGE_MAP, "rounded bg-brand-blue px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-navy"),
                    link(P.METHOD_CTA_ABOUT, C.PAGE_ABOUT, theme.BTN_OUTLINE),
                ],
                className="mt-14 flex flex-wrap gap-3",
            ),
        ],
        className="mx-auto max-w-5xl px-6 py-12",
    )
