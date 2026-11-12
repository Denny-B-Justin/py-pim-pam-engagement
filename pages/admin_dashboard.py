"""
admin_dashboard.py — portfolio & results overview  (/?page=admin-dashboard).
Port of app/admin/dashboard/page.tsx. Read-only; always reads fresh data.
"""
from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any

from dash import html

import constants as C
import page_constants as P
from services import db
from services import repository as repo
from services import validation as V
from utils import components as ui
from utils import theme
from utils.routing import link

log = logging.getLogger(__name__)

PAGE = C.PAGE_ADMIN_DASHBOARD
PROTECTED = True

_TOOL_BAR_COLOR = "#3675b7"
_COMPLETENESS_BAR_COLOR = "#374291"


def _has(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _days_since(value: Any) -> float:
    """Fractional days since a date; no date counts as 'infinitely long ago' (→ stale)."""
    day = repo.parse_day(value)
    if day is None:
        return math.inf
    then = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - then).total_seconds() / 86400


def _is_stale(value: Any) -> bool:
    return _days_since(value) > C.STALE_DAYS


# ── small building blocks (Kpi / Section / Bar / GapList in the original) ───
def _kpi(label: str, value: int, sub: str | None = None, tone: str | None = None) -> html.Div:
    return html.Div(
        [
            html.Div(str(value), className="text-2xl font-bold " + ("text-amber-600" if tone == "warn" else "text-brand-blue")),
            html.Div(label, className="mt-0.5 text-[11px] font-semibold uppercase tracking-wider text-gray-500"),
            html.Div(sub, className="text-xs text-gray-400") if sub else None,
        ],
        className="rounded-xl border border-brand-line bg-white p-4",
    )


def _section(title: str, children: Any) -> html.Section:
    return html.Section(
        [
            html.H2(title, className="text-sm font-bold uppercase tracking-wider text-brand-blue"),
            html.Div(children, className="mt-4"),
        ],
        className="mt-8 rounded-xl border border-brand-line bg-white p-5",
    )


def _pct(n: int, total: int) -> int:
    """Math.round((n / total) * 100) — JavaScript rounds halves up, Python's round() does not."""
    return math.floor(n / total * 100 + 0.5) if total else 0


def _bar(label: str, n: int, total: int, color: str) -> html.Div:
    w = _pct(n, total)
    return html.Div(
        [
            html.Div(
                [
                    html.Span(label, className="text-gray-700"),
                    html.Span([f"{n}/{total} ", html.Span(f"· {w}%", className="text-gray-400")], className="text-gray-500"),
                ],
                className="flex items-baseline justify-between text-sm",
            ),
            html.Div(
                html.Div(className="h-full rounded-full", style={"width": f"{w}%", "background": color}),
                className="mt-1 h-2.5 w-full overflow-hidden rounded-full bg-gray-100",
            ),
        ]
    )


def _gap_list(title: str, countries: list[dict[str, Any]], show_date: bool = False) -> html.Div:
    head = html.H3([title, " ", html.Span(f"({len(countries)})", className="text-gray-400")], className="text-xs font-bold uppercase tracking-wider text-gray-500")
    if not countries:
        return html.Div([head, html.P("All complete ✓", className="mt-2 text-sm italic text-brand-mid")])
    items = []
    for c in countries:
        line: list[Any] = [link(c.get("name"), C.PAGE_ADMIN_COUNTRY, "text-brand-blue hover:underline", iso=c["iso3"])]
        if show_date:
            d = _days_since(c.get("last_updated"))
            line.append(html.Span("never" if math.isinf(d) else f"{math.floor(d + 0.5)}d", className="ml-2 text-xs text-gray-400"))
        items.append(html.Li(line))
    return html.Div([head, html.Ul(items, className="mt-2 max-h-72 space-y-1 overflow-y-auto pr-1 text-sm")])


# ── layout ──────────────────────────────────────────────────────────────────
def _load() -> repo.DashboardData | None:
    if not repo.db_available():
        return None
    try:
        return repo.fetch_dashboard_data()
    except db.DatabaseError:
        log.exception("Could not load the dashboard data")
        return None


def layout(params: dict[str, str]) -> Any:
    data = _load()
    countries = data.countries if data else []
    contacts = data.contacts if data else []
    total = len(countries)

    header = html.Div(
        [
            html.Div(
                [
                    ui.eyebrow(P.DASH_EYEBROW),
                    html.H1(P.DASH_TITLE, className="mt-1 text-3xl font-bold text-brand-blue"),
                    html.P(f"{total} countries · live from the engagement database.", className="mt-1 text-sm text-gray-600"),
                ]
            ),
            html.Div(
                [
                    link("Results tracker →", C.PAGE_ADMIN_REVIEW, "text-brand-blue hover:text-brand-navy"),
                    link("Admin →", C.PAGE_ADMIN, "text-brand-blue hover:text-brand-navy"),
                    link("Map →", C.PAGE_MAP, "text-brand-blue hover:text-brand-navy"),
                ],
                className="flex flex-wrap gap-3 text-sm",
            ),
        ],
        className="flex flex-wrap items-end justify-between gap-3 border-b border-brand-line pb-4",
    )

    if total == 0:
        body: list[Any] = [html.P(P.DASH_NO_DATA, className="mt-8 text-sm text-amber-800")]
        return html.Div([header, *body], className="mx-auto max-w-6xl px-6 py-10")

    # Focal points (role "Focal point (TTL)") grouped by country
    focal_by_iso: dict[str, list[dict[str, Any]]] = {}
    for p in contacts:
        if p.get("role") == C.FOCAL_ROLE:
            focal_by_iso.setdefault(p["iso3"], []).append(p)

    def focal_email_ok(iso: str) -> bool:
        return any(V.has_valid_email(p.get("email")) for p in focal_by_iso.get(iso, []))

    stale_count = sum(1 for c in countries if _is_stale(c.get("last_updated")))
    has_focal = sum(1 for c in countries if c["iso3"] in focal_by_iso)
    focal_email_complete = sum(1 for c in countries if focal_email_ok(c["iso3"]))
    with_brief = sum(1 for c in countries if any(_has(c.get(f.key)) for f in C.BRIEF_FIELDS))
    wb_total = len(contacts)
    wb_with_email = sum(1 for p in contacts if V.has_valid_email(p.get("email")))

    by_status = [(s, sum(1 for c in countries if c.get("status") == s)) for s in C.ENGAGEMENT_STATUSES]
    tool_coverage = [(t.label, sum(1 for c in countries if ui.is_true(c.get(t.key)))) for t in C.TOOL_FIELDS]
    has_counterpart = sum(1 for c in countries if c["iso3"] in data.counterpart_isos)

    completeness = [
        ("Focal point assigned", has_focal),
        ("Focal-point e-mail on file", focal_email_complete),
        ("PIM counterpart assigned", has_counterpart),
        ("Summary written", sum(1 for c in countries if _has(c.get("summary")))),
        ("Engagement brief started", with_brief),
        ("Regional engagements noted", sum(1 for c in countries if _has(c.get("regional_engagements")))),
        (f"Updated in last {C.STALE_DAYS} days", total - stale_count),
    ]

    regions = sorted({c.get("region") for c in countries}, key=lambda r: str(r))

    no_focal = [c for c in countries if c["iso3"] not in focal_by_iso]
    focal_no_email = [c for c in countries if c["iso3"] in focal_by_iso and not focal_email_ok(c["iso3"])]
    stale_list = sorted((c for c in countries if _is_stale(c.get("last_updated"))), key=lambda c: _days_since(c.get("last_updated")), reverse=True)

    kpis = html.Div(
        [
            _kpi("Countries", total),
            _kpi("With a focal point", has_focal, f"{_pct(has_focal, total)}%"),
            _kpi("Focal-point e-mail", focal_email_complete, f"{_pct(focal_email_complete, total)}%", "warn" if focal_email_complete < total else "ok"),
            _kpi("Engagement brief", with_brief, f"{_pct(with_brief, total)}%"),
            _kpi(f"Stale (>{C.STALE_DAYS}d)", stale_count, None, "warn" if stale_count > 0 else "ok"),
        ],
        className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5",
    )

    maturity = _section(
        "Engagement maturity",
        [
            html.Div(
                [
                    html.Div(title=f"{s}: {n}", style={"width": f"{n / total * 100}%", "background": theme.status_color(s)})
                    for s, n in by_status
                    if n
                ],
                className="flex h-7 w-full overflow-hidden rounded-lg border border-brand-line",
            ),
            html.Div(
                [
                    html.Span(
                        [
                            html.Span(className="h-3 w-3 rounded-sm", style={"background": theme.status_color(s)}),
                            html.Span(s, className="font-medium text-gray-700"),
                            html.Span(str(n), className="text-gray-400"),
                        ],
                        className="inline-flex items-center gap-1.5",
                    )
                    for s, n in by_status
                ],
                className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-sm",
            ),
        ],
    )

    two_up = html.Div(
        [
            _section("Tools applied (countries)", html.Div([_bar(label, n, total, _TOOL_BAR_COLOR) for label, n in tool_coverage], className="space-y-2.5")),
            _section(
                "Data completeness",
                [
                    html.Div([_bar(label, n, total, _COMPLETENESS_BAR_COLOR) for label, n in completeness], className="space-y-2.5"),
                    html.P(["WB e-mail registry: ", html.B(str(wb_with_email)), f"/{wb_total} contacts have an e-mail."], className="mt-3 text-xs text-gray-500"),
                ],
            ),
        ],
        className="mt-8 grid gap-8 lg:grid-cols-2",
    )

    matrix_rows = []
    for rg in regions:
        in_region = [c for c in countries if c.get("region") == rg]
        cells = []
        for s in C.ENGAGEMENT_STATUSES:
            n = sum(1 for c in in_region if c.get("status") == s)
            cells.append(html.Td(str(n) if n else html.Span("·", className="text-gray-300"), className="px-3 py-2 text-center text-gray-700"))
        matrix_rows.append(
            html.Tr(
                [html.Td(rg, className="py-2 pr-4 font-medium text-brand-navy"), *cells, html.Td(str(len(in_region)), className="px-3 py-2 text-center font-semibold text-gray-800")]
            )
        )
    by_region = _section(
        "By region",
        html.Div(
            html.Table(
                [
                    html.Thead(
                        html.Tr(
                            [
                                html.Th("Region", className="py-2 pr-4"),
                                *[html.Th(s, className="px-3 py-2 text-center") for s in C.ENGAGEMENT_STATUSES],
                                html.Th("Total", className="px-3 py-2 text-center"),
                            ],
                            className="border-b border-brand-line text-left text-xs font-semibold uppercase tracking-wider text-brand-mid",
                        )
                    ),
                    html.Tbody(matrix_rows, className="divide-y divide-gray-100"),
                ],
                className="min-w-full text-sm",
            ),
            className="overflow-x-auto",
        ),
    )

    gaps = _section(
        "Gaps to fill",
        html.Div(
            [
                _gap_list("No focal point", no_focal),
                _gap_list("Focal point, no e-mail", focal_no_email),
                _gap_list(f"Stale (>{C.STALE_DAYS} days)", stale_list, show_date=True),
            ],
            className="grid gap-6 md:grid-cols-3",
        ),
    )

    return html.Div([header, kpis, maturity, two_up, by_region, gaps], className="mx-auto max-w-6xl px-6 py-10")
