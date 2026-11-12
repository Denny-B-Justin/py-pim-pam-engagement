"""
admin_review.py — data review tracker  (/?page=admin-review).  Port of app/admin/review/page.tsx,
ReviewTable.tsx and api/admin/review-toggle.

The original did all filtering / sorting in the browser. Here the rows live in a store and one
callback renders the table from (rows + search + filters + sort), so the behaviour — gap flags,
sort rules, CSV columns — is identical.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from dash import ALL, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate

import constants as C
import page_constants as P
from services import auth, db
from services import repository as repo
from services.fallback_data import FALLBACK_COUNTRIES
from services.validation import ServiceError
from utils import forms, results, theme
from utils import components as ui
from utils.routing import link, page_search

log = logging.getLogger(__name__)

PAGE = C.PAGE_ADMIN_REVIEW
PROTECTED = True

SORT_KEYS = ("iso3", "name", "region", "status", "last_updated")
OPT_IDS = ("issues", "unreviewed", "nosummary", "noemail")


# ── data shaping ────────────────────────────────────────────────────────────
def _review_rows(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for r in raw:
        emails = [
            e
            for e in (
                r.get("wbg_email_primary"),
                r.get("wbg_email_secondary"),
                r.get("counterpart_email_primary"),
                r.get("counterpart_email_secondary"),
            )
            if isinstance(e, str) and "@" in e
        ]
        out.append(
            {
                "iso3": r["iso3"],
                "name": r.get("name"),
                "region": r.get("region"),
                "status": r.get("status"),
                "focus_note": r.get("focus_note"),
                "ttl": r.get("ttl"),
                "last_updated": repo.to_iso(r.get("last_updated")),
                "reviewed_at": repo.to_iso(r.get("reviewed_at")),
                "summary": r.get("summary"),
                "counterpart": r.get("counterpart"),
                "emails": emails,
            }
        )
    return out


def _load() -> tuple[list[dict[str, Any]], str | None, bool]:
    """(rows, db_error, using_fallback)"""
    rows: list[dict[str, Any]] = []
    db_error: str | None = None
    if repo.db_available():
        try:
            rows = _review_rows(repo.fetch_countries_full())
        except db.DatabaseError as exc:
            db_error = str(exc)
    using_fallback = not rows and not db_error
    if using_fallback:
        rows = [
            {
                "iso3": c["iso3"], "name": c["name"], "region": c["region"], "status": c["status"],
                "focus_note": c["focus"], "ttl": c["contact"], "last_updated": None, "reviewed_at": None,
                "summary": None, "counterpart": None, "emails": [],
            }
            for c in FALLBACK_COUNTRIES
        ]
    return rows, db_error, using_fallback


def _days_since(day: str | None) -> int | None:
    parsed = repo.parse_day(day)
    if parsed is None:
        return None
    then = datetime(parsed.year, parsed.month, parsed.day, tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - then).days


def _flags(r: dict[str, Any]) -> dict[str, bool]:
    d = _days_since(r.get("last_updated"))
    return {
        "noFocus": ui.is_blank(r.get("focus_note")),
        "noContact": ui.is_blank(r.get("ttl")),
        "noDate": not r.get("last_updated"),
        "stale": d is not None and d > C.STALE_DAYS,
    }


def _has_issue(f: dict[str, bool]) -> bool:
    return any(f.values())


def _no_summary(r: dict[str, Any]) -> bool:
    return ui.is_blank(r.get("summary"))


def _no_email(r: dict[str, Any]) -> bool:
    return not r.get("emails")


def _no_counterpart(r: dict[str, Any]) -> bool:
    return ui.is_blank(r.get("counterpart"))


def _view(rows: list[dict[str, Any]], query: str, opts: list[str], sort_key: str, sort_dir: int) -> list[dict[str, Any]]:
    q = (query or "").strip().lower()
    only_issues, only_unrev, only_nosum, only_noemail = (o in opts for o in OPT_IDS)

    def keep(r: dict[str, Any]) -> bool:
        if only_issues and not _has_issue(_flags(r)):
            return False
        if only_unrev and r.get("reviewed_at"):
            return False
        if only_nosum and not _no_summary(r):
            return False
        if only_noemail and not _no_email(r):
            return False
        if not q:
            return True
        hay = f"{r.get('name') or ''} {r['iso3']} {r.get('region') or ''} {r.get('status') or ''} {r.get('ttl') or ''} {r.get('focus_note') or ''}".lower()
        return q in hay

    def key(r: dict[str, Any]):
        if sort_key == "status":
            return C.STATUS_ORDER.get(r.get("status"), 99)
        if sort_key == "last_updated":
            d = repo.parse_day(r.get("last_updated"))
            return d.toordinal() if d else 0
        return str(r.get(sort_key) or "").lower()

    return sorted((r for r in rows if keep(r)), key=key, reverse=sort_dir == -1)


# ── view ────────────────────────────────────────────────────────────────────
def _stats_view(rows: list[dict[str, Any]]) -> list[Any]:
    by_status: dict[str, int] = {}
    n_focus = n_contact = n_date = n_stale = with_issue = reviewed = summary = email = counterpart = 0
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        f = _flags(r)
        n_focus += f["noFocus"]
        n_contact += f["noContact"]
        n_date += f["noDate"]
        n_stale += f["stale"]
        with_issue += _has_issue(f)
        reviewed += bool(r.get("reviewed_at"))
        summary += not _no_summary(r)
        email += not _no_email(r)
        counterpart += not _no_counterpart(r)

    total = len(rows)
    grid = html.Div(
        [ui.stat("Countries", total)]
        + [ui.stat(s, by_status.get(s, 0), dot=theme.status_color(s)) for s in C.ENGAGEMENT_STATUSES]
        + [ui.stat("With data gaps", with_issue, warn=with_issue > 0), ui.stat(f"Reviewed / {total}", reviewed)],
        className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6",
    )
    out: list[Any] = [grid]
    if with_issue > 0:
        parts: list[Any] = ["Gaps detected: "]
        if n_focus:
            parts += [ui.badge(f"{n_focus} missing focus note"), " "]
        if n_contact:
            parts += [ui.badge(f"{n_contact} missing focal point"), " "]
        if n_date:
            parts += [ui.badge(f"{n_date} no update date"), " "]
        if n_stale:
            parts += [ui.badge(f"{n_stale} not updated in {C.STALE_DAYS}+ days")]
        out.append(html.P(parts, className="mt-3 text-xs text-gray-600"))
    out.append(
        html.P(
            [
                "Expanded-field completeness: ",
                ui.soft_badge(f"{summary}/{total} have a summary"), " ",
                ui.soft_badge(f"{email}/{total} have an e-mail"), " ",
                ui.soft_badge(f"{counterpart}/{total} have a counterpart"),
            ],
            className="mt-2 text-xs text-gray-600",
        )
    )
    return out


def _th(label: str, key: str | None, sort_key: str, sort_dir: int) -> html.Th:
    cls = "border-b border-brand-line px-3 py-2 text-left text-xs font-bold uppercase tracking-wider text-brand-blue"
    if key is None:
        return html.Th(label, className=cls)
    arrow = html.Span("▲" if sort_dir == 1 else "▼", className="ml-1") if sort_key == key else None
    return html.Th(
        [label, arrow],
        id={"type": "rv-sort", "key": key},
        n_clicks=0,
        className=cls + " cursor-pointer select-none hover:text-brand-navy",
    )


def _table(rows: list[dict[str, Any]], sort_key: str, sort_dir: int) -> html.Table:
    head = html.Thead(
        html.Tr(
            [
                _th("ISO", "iso3", sort_key, sort_dir),
                _th("Country", "name", sort_key, sort_dir),
                _th("Region", "region", sort_key, sort_dir),
                _th("Status", "status", sort_key, sort_dir),
                _th("Focal point", None, sort_key, sort_dir),
                _th("Focus note", None, sort_key, sort_dir),
                _th("Updated", "last_updated", sort_key, sort_dir),
                _th("Gaps", None, sort_key, sort_dir),
                _th("Review", None, sort_key, sort_dir),
            ]
        ),
        className="bg-brand-tint",
    )
    body: list[Any] = []
    for r in rows:
        f = _flags(r)
        flags: list[Any] = []
        if f["noFocus"]:
            flags.append(ui.flag("focus"))
        if f["noContact"]:
            flags.append(ui.flag("focal pt"))
        if f["noDate"]:
            flags.append(ui.flag("date"))
        if f["stale"]:
            flags.append(ui.flag("stale"))
        if _no_summary(r):
            flags.append(ui.soft_flag("summary"))
        if _no_email(r):
            flags.append(ui.soft_flag("e-mail"))
        if _no_counterpart(r):
            flags.append(ui.soft_flag("counterpart"))

        reviewed = r.get("reviewed_at")
        day = (reviewed or "")[:10]
        toggle = html.Button(
            f"✓ {day}" if reviewed else "Mark verified",
            id={"type": "rv-toggle", "iso": r["iso3"]},
            n_clicks=0,
            title=f"Reviewed {day} — click to clear" if reviewed else None,
            className=(
                "rounded-full bg-brand-green/15 px-2 py-0.5 text-xs font-semibold text-brand-green hover:bg-brand-green/25"
                if reviewed
                else "rounded-full border border-gray-300 px-2 py-0.5 text-xs font-medium text-gray-600 hover:border-brand-blue hover:text-brand-blue"
            ),
        )
        body.append(
            html.Tr(
                [
                    html.Td(r["iso3"], className="px-3 py-2 font-mono text-xs font-bold text-brand-blue"),
                    html.Td(
                        link(r.get("name"), C.PAGE_ADMIN_COUNTRY, "hover:text-brand-blue hover:underline", iso=r["iso3"]),
                        className="whitespace-nowrap px-3 py-2 font-semibold text-brand-navy",
                    ),
                    html.Td(r.get("region"), className="whitespace-nowrap px-3 py-2 text-xs text-gray-500"),
                    html.Td(ui.status_pill(r.get("status")), className="whitespace-nowrap px-3 py-2"),
                    html.Td("—" if f["noContact"] else r.get("ttl"), className="px-3 py-2 " + ("text-amber-700" if f["noContact"] else "text-gray-700")),
                    html.Td("—" if f["noFocus"] else r.get("focus_note"), className="max-w-md px-3 py-2 " + ("text-amber-700" if f["noFocus"] else "text-gray-700")),
                    html.Td(
                        r.get("last_updated") or "—",
                        className="whitespace-nowrap px-3 py-2 text-xs " + ("text-amber-700" if f["noDate"] or f["stale"] else "text-gray-500"),
                    ),
                    html.Td(html.Div(flags, className="flex flex-wrap gap-1"), className="px-3 py-2"),
                    html.Td(toggle, className="whitespace-nowrap px-3 py-2"),
                ],
                className="bg-amber-50/40" if _has_issue(f) else None,
            )
        )
    if not rows:
        body.append(
            html.Tr(html.Td("No countries match the current filter.", colSpan=9, className="px-3 py-6 text-center text-sm text-gray-500"))
        )
    return html.Table([head, html.Tbody(body, className="divide-y divide-gray-100 bg-white")], className="min-w-[900px] w-full border-collapse text-sm")


def layout(params: dict[str, str]) -> Any:
    rows, db_error, using_fallback = _load()

    banners: list[Any] = []
    if db_error:
        banners.append(ui.banner("warn", [html.B("Database read error:"), f" {db_error}."]))
    if using_fallback:
        banners.append(ui.banner("warn", [html.B("Showing the static snapshot"), " — the database returned no rows."]))

    return html.Div(
        [
            dcc.Store(id="rv-rows", data=rows),
            dcc.Store(id="rv-sortstate", data={"key": "region", "dir": 1}),
            dcc.Download(id="rv-dl"),
            html.Div(
                [
                    html.Div(
                        [
                            html.P(P.REVIEW_EYEBROW, className="text-xs font-semibold uppercase tracking-widest text-brand-mid"),
                            html.H1(P.REVIEW_TITLE, className="mt-1 text-3xl font-bold text-brand-blue"),
                            html.P(
                                [P.REVIEW_INTRO_PRE, html.Strong(P.REVIEW_INTRO_BOLD), P.REVIEW_INTRO_POST],
                                className="mt-2 max-w-2xl text-sm text-gray-600",
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            link("Dashboard →", C.PAGE_ADMIN_DASHBOARD, "text-brand-blue hover:text-brand-navy"),
                            link("Edit data →", C.PAGE_ADMIN, "text-brand-blue hover:text-brand-navy"),
                            ui.sign_out_button(),
                        ],
                        className="flex items-center gap-4 text-sm",
                    ),
                ],
                className="flex flex-wrap items-end justify-between gap-3 border-b border-brand-line pb-4",
            ),
            html.Div(banners, id="rv-banner"),
            html.Div(
                [
                    html.Div(_stats_view(rows), id="rv-stats"),
                    html.Div(
                        [
                            forms.text_input(
                                "rv-q", "", "search", theme.SEARCH_CLS,
                                label="Search the dataset", placeholder=P.REVIEW_SEARCH_PLACEHOLDER,
                            ),
                            forms.checkbox({"type": "rv-opt", "opt": "issues"}, False, "Only rows with gaps"),
                            forms.checkbox({"type": "rv-opt", "opt": "unreviewed"}, False, "Only unreviewed"),
                            forms.checkbox({"type": "rv-opt", "opt": "nosummary"}, False, "Missing summary"),
                            forms.checkbox({"type": "rv-opt", "opt": "noemail"}, False, "No e-mail"),
                            html.Span(f"{len(rows)} shown", id="rv-count", className="text-xs text-gray-500"),
                            html.Button(
                                "Export CSV",
                                id="rv-export",
                                n_clicks=0,
                                className="ml-auto rounded border border-brand-blue px-3 py-1.5 text-sm font-semibold text-brand-blue hover:bg-brand-blue/5",
                            ),
                        ],
                        className="mt-5 flex flex-wrap items-center gap-3",
                    ),
                    html.Div(
                        _table(_view(rows, "", [], "region", 1), "region", 1),
                        id="rv-table",
                        className="mt-4 overflow-x-auto rounded-lg border border-brand-line",
                    ),
                ],
                className="mt-6",
            ),
        ],
        className="mx-auto max-w-7xl px-6 py-10",
    )


# ── controller ──────────────────────────────────────────────────────────────
def _opts_from(values: list[Any]) -> list[str]:
    """Collapse the four single-box checklists into the list of ticked option names."""
    chosen: list[str] = []
    for name, value in zip(OPT_IDS, values):
        if value and "true" in value:
            chosen.append(name)
    return chosen


def _csv(view: list[dict[str, Any]]) -> str:
    cols = ["iso3", "name", "region", "status", "ttl", "focus_note", "last_updated", "data_gaps", "has_summary", "counterpart", "emails", "reviewed_at"]

    def esc(v: Any) -> str:
        return '"' + ("" if v is None else str(v)).replace('"', '""') + '"'

    lines = [",".join(cols)]
    for r in view:
        f = _flags(r)
        gaps = "; ".join(
            label for label, on in (("no-focus-note", f["noFocus"]), ("no-focal-point", f["noContact"]), ("no-date", f["noDate"]), ("stale", f["stale"])) if on
        )
        cells = [
            r["iso3"], r.get("name"), r.get("region"), r.get("status"), r.get("ttl"), r.get("focus_note"),
            r.get("last_updated"), gaps, "no" if _no_summary(r) else "yes", r.get("counterpart") or "",
            "; ".join(r.get("emails") or []), r.get("reviewed_at") or "",
        ]
        lines.append(",".join(esc(c) for c in cells))
    return "\n".join(lines)


def register_callbacks(app) -> None:
    # sort headers → sort state
    @app.callback(
        Output("rv-sortstate", "data"),
        Input({"type": "rv-sort", "key": ALL}, "n_clicks"),
        State("rv-sortstate", "data"),
        prevent_initial_call=True,
    )
    def _toggle_sort(_clicks, current):
        if not ctx.triggered_id or not ctx.triggered[0]["value"]:
            raise PreventUpdate
        key = ctx.triggered_id["key"]
        if key not in SORT_KEYS:
            raise PreventUpdate
        if key == current["key"]:
            return {"key": key, "dir": -current["dir"]}
        return {"key": key, "dir": 1}

    # rows + search + filters + sort → table
    @app.callback(
        Output("rv-table", "children"),
        Output("rv-count", "children"),
        Input("rv-rows", "data"),
        Input("rv-q", "value"),
        Input({"type": "rv-opt", "opt": ALL}, "value"),
        Input("rv-sortstate", "data"),
    )
    def _render(rows, query, opt_values, sort):
        view = _view(rows or [], query or "", _opts_from(opt_values or []), sort["key"], sort["dir"])
        return _table(view, sort["key"], sort["dir"]), f"{len(view)} shown"

    # rows → summary stats
    @app.callback(Output("rv-stats", "children"), Input("rv-rows", "data"), prevent_initial_call=True)
    def _render_stats(rows):
        return _stats_view(rows or [])

    # "Mark verified" / clear
    @app.callback(
        Output("rv-rows", "data"),
        Output("rv-banner", "children"),
        Output("pp-url", "search", allow_duplicate=True),
        Input({"type": "rv-toggle", "iso": ALL}, "n_clicks"),
        State("rv-rows", "data"),
        prevent_initial_call=True,
    )
    def _toggle_review(_clicks, rows):
        if not ctx.triggered_id or not ctx.triggered[0]["value"]:
            raise PreventUpdate
        if not auth.is_authenticated():
            return no_update, no_update, page_search(C.PAGE_LOGIN, next=page_search(C.PAGE_ADMIN_REVIEW))
        iso = ctx.triggered_id["iso"]
        current = next((r for r in rows or [] if r["iso3"] == iso), None)
        if current is None:
            raise PreventUpdate
        try:
            repo.set_reviewed(iso, not current.get("reviewed_at"))
            fresh, db_error, _ = _load()
        except ServiceError as exc:
            return no_update, ui.banner("err", results.error_text(exc.code)), no_update
        if db_error:
            return no_update, ui.banner("warn", [html.B("Database read error:"), f" {db_error}."]), no_update
        return fresh, [], no_update

    # Export CSV (respects the current search / filters / sort)
    @app.callback(
        Output("rv-dl", "data"),
        Input("rv-export", "n_clicks"),
        State("rv-rows", "data"),
        State("rv-q", "value"),
        State({"type": "rv-opt", "opt": ALL}, "value"),
        State("rv-sortstate", "data"),
        prevent_initial_call=True,
    )
    def _export(n, rows, query, opt_values, sort):
        if not n:
            raise PreventUpdate
        if not auth.is_authenticated():
            raise PreventUpdate
        view = _view(rows or [], query or "", _opts_from(opt_values or []), sort["key"], sort["dir"])
        return dcc.send_string(_csv(view), C.CSV_REVIEW_FILENAME)
