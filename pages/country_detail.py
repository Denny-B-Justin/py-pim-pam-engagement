"""
country_detail.py — one country  (/?page=country-detail&iso=SRB).  Port of app/country/[iso]/page.tsx
and app/api/country/[iso]/brief/route.ts.

A public page with a restricted tier: anyone sees the highlights; signed-in staff also see contacts,
operational records and internal updates. Rendered per request (never cached) because the content
depends on the session.
"""
from __future__ import annotations

import logging
from typing import Any

from dash import Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate

import constants as C
import page_constants as P
from services import auth, brief_docx, db
from services import repository as repo
from services.fallback_data import FALLBACK_COUNTRIES
from services.validation import is_valid_iso3, normalise_iso3
from utils import components as ui
from utils.routing import link, page_search

log = logging.getLogger(__name__)

PAGE = C.PAGE_COUNTRY_DETAIL
PROTECTED = False


def _safe_url(url: Any) -> str | None:
    """Only http(s) links are rendered as links (migrated data may hold anything)."""
    text = str(url or "").strip()
    return text if text.lower().startswith(("http://", "https://")) else None


def _link_cell(url: Any) -> Any:
    safe = _safe_url(url)
    return html.A("View", href=safe, className="text-brand-blue underline", target="_blank", rel="noreferrer") if safe else "—"


def _dash(value: Any) -> Any:
    """`value ?? "—"` — only None falls back (0 and '' are shown as they are)."""
    return "—" if value is None else ui.cell(value)


def _load(iso: str) -> tuple[repo.CountryBundle | None, dict[str, Any] | None]:
    bundle: repo.CountryBundle | None = None
    if repo.db_available():
        try:
            bundle = repo.fetch_country_bundle(iso)
        except db.DatabaseError:
            log.exception("Could not load country %s", iso)
    fallback = next((c for c in FALLBACK_COUNTRIES if c["iso3"] == iso), None)
    return bundle, fallback


def layout(params: dict[str, str]) -> Any:
    from pages import not_found  # local import keeps the registry free of cycles

    iso = normalise_iso3(params.get("iso"))
    if not is_valid_iso3(iso):
        return not_found.layout(params)

    authed = auth.is_authenticated()
    bundle, fallback = _load(iso)
    db_country = bundle.country if bundle else None
    country: dict[str, Any] | None = db_country or fallback
    if not country:
        return not_found.layout(params)
    b = bundle or repo.CountryBundle(country=None)
    fb = fallback or {}

    status = country.get("status") or fb.get("status") or "Awareness"
    focus = country.get("focus_note") or fb.get("focus")

    header_right: list[Any] = [
        html.Div(
            [
                html.P(P.DETAIL_MATURITY_LABEL, className="text-[10px] font-semibold uppercase tracking-wider text-gray-400"),
                ui.status_pill(status, "mt-1 inline-block rounded-full px-3 py-1 text-xs font-semibold text-white"),
            ],
            className="text-right",
        )
    ]
    if authed:
        header_right.append(
            html.Div(
                [
                    link(
                        P.DETAIL_EDIT_LABEL,
                        C.PAGE_ADMIN_COUNTRY,
                        "rounded border border-brand-blue px-3 py-1 text-xs font-semibold text-brand-blue hover:bg-brand-tint",
                        iso=iso,
                    ),
                    ui.sign_out_button(),
                ],
                className="flex items-center gap-2",
            )
        )

    children: list[Any] = [
        dcc.Store(id="detail-iso", data=iso),
        dcc.Download(id="detail-download"),
        html.Div(
            [
                link(P.DETAIL_BACK_LABEL, C.PAGE_MAP, "text-sm text-brand-blue hover:text-brand-navy"),
                html.Button(
                    [html.Span("⬇", **{"aria-hidden": "true"}), " ", P.DETAIL_DOWNLOAD_BRIEF],
                    id="detail-brief",
                    n_clicks=0,
                    className="inline-flex items-center gap-1.5 rounded border border-brand-blue px-3 py-1.5 text-xs font-semibold text-brand-blue hover:bg-brand-tint",
                ),
            ],
            className="flex items-center justify-between gap-3",
        ),
        html.Header(
            [
                html.Div(
                    [
                        html.P(country.get("region") or fb.get("region"), className="text-xs font-semibold uppercase tracking-widest text-gray-500"),
                        html.H1(country.get("name") or fb.get("name"), className="mt-1 text-3xl font-bold text-brand-blue"),
                    ]
                ),
                html.Div(header_right, className="flex items-start gap-3"),
            ],
            className="mt-3 flex flex-wrap items-end justify-between gap-4 border-b border-gray-200 pb-5",
        ),
        # Public fields — always shown, with a placeholder when empty
        ui.prose("Focus", focus),
        ui.prose("Summary", country.get("summary")),
    ]
    for f in C.BRIEF_FIELDS:
        children.append(ui.prose(f.label, country.get(f.key)))
    children.append(ui.prose("Regional Management/Staff Unit Engagements", country.get("regional_engagements")))
    children.append(
        html.Dl(
            [
                ui.detail("Language", country.get("language")),
                ui.detail("Last updated", repo.to_iso(country.get("last_updated"))),
            ],
            className="mt-6 grid grid-cols-1 gap-x-8 gap-y-3 border-t border-gray-100 pt-5 text-sm sm:grid-cols-2 lg:grid-cols-3",
        )
    )

    # ── restricted tier ──
    if not authed:
        children.append(
            html.Div(
                [
                    html.P(P.DETAIL_RESTRICTED_TITLE, className="text-sm font-semibold text-brand-blue"),
                    html.P(P.DETAIL_RESTRICTED_BODY, className="mx-auto mt-1 max-w-md text-sm text-gray-600"),
                    link(
                        P.DETAIL_RESTRICTED_CTA,
                        C.PAGE_LOGIN,
                        "mt-4 inline-block rounded bg-brand-blue px-5 py-2 text-sm font-semibold text-white hover:bg-brand-navy",
                        next=page_search(C.PAGE_COUNTRY_DETAIL, iso=iso),
                    ),
                ],
                className="mt-10 rounded-xl border border-brand-line bg-brand-tint/30 px-5 py-6 text-center",
            )
        )
    else:
        children += [
            html.Div(
                [
                    html.Span(P.DETAIL_STAFF_DIVIDER, className="text-[10px] font-bold uppercase tracking-widest text-gray-400"),
                    html.Span(className="h-px flex-1 bg-brand-line"),
                ],
                className="mt-10 flex items-center gap-3",
            ),
            ui.prose("Latest status", country.get("status_note")),
            ui.people_section("World Bank Managers & Staff", b.contacts),
            ui.people_section("PIM Counterparts", b.counterparts, "Email update list →"),
            ui.prose("Comment", country.get("comment")),
            # Each section shows its narrative (or a placeholder) above any structured records.
            ui.section(
                "Assessments",
                [
                    ui.narrative(country.get("assessments_note")),
                    ui.simple_table(
                        ["Type", "Year", "Score", "Notes", "Link"],
                        [
                            [ui.cell(r.get("type")), ui.cell(r.get("year")), _dash(r.get("score")), _dash(r.get("notes")), _link_cell(r.get("link"))]
                            for r in b.assessments
                        ],
                    )
                    if b.assessments
                    else ui.empty_hint(P.DETAIL_EMPTY_ASSESSMENTS),
                ],
            ),
            ui.section(
                "Operations & Pipeline",
                [
                    ui.narrative(country.get("operations_note")),
                    ui.simple_table(
                        ["P-code", "Name", "Funder", "Year", "Commitment (US$ M)", "Status"],
                        [
                            [
                                ui.cell(r.get("code")),
                                ui.cell(r.get("name")),
                                ui.cell(r.get("funder")),
                                ui.cell(r.get("year")),
                                _dash(r.get("ida_commitment_musd")),
                                ui.cell(r.get("status")),
                            ]
                            for r in b.projects
                        ],
                    )
                    if b.projects
                    else ui.empty_hint(P.DETAIL_EMPTY_OPERATIONS),
                ],
            ),
            ui.section("Tools applied", ui.tool_checklist(country)),
            ui.section(
                "Recent activity",
                [
                    ui.narrative(country.get("activity_note")),
                    ui.simple_table(
                        ["Date", "Type", "Location", "Notes"],
                        [[ui.cell(r.get("date")), ui.cell(r.get("type")), ui.cell(r.get("location")), ui.cell(r.get("notes"))] for r in b.events],
                    )
                    if b.events
                    else ui.empty_hint(P.DETAIL_EMPTY_EVENTS),
                ],
            ),
            # References — shown last, staff-only
            ui.prose("References", country.get("reference_notes")),
        ]
        if not repo.db_available():
            children.append(
                html.Div(
                    [html.B("Database not connected. "), P.DETAIL_NO_DB],
                    className="mt-10 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900",
                )
            )

    return html.Div(children, className="mx-auto max-w-5xl px-6 py-10")


def register_callbacks(app) -> None:
    @app.callback(
        Output("detail-download", "data"),
        Input("detail-brief", "n_clicks"),
        State("detail-iso", "data"),
        prevent_initial_call=True,
    )
    def _download_brief(n_clicks, iso):
        """Build the Word brief. Staff-only sections are included only for a signed-in session."""
        if not n_clicks:
            raise PreventUpdate
        iso = normalise_iso3(iso)
        if not is_valid_iso3(iso):
            raise PreventUpdate
        authed = auth.is_authenticated()
        bundle, fallback = _load(iso)
        country = (bundle.country if bundle else None) or fallback
        if not country:
            raise PreventUpdate
        b = bundle or repo.CountryBundle(country=None)
        data = brief_docx.build_country_brief(country, b.contacts, b.counterparts, b.assessments, b.projects, b.events, authed)
        return dcc.send_bytes(data, brief_docx.brief_filename(country, iso))
