"""
admin_home.py — country list editor  (/?page=admin).  Port of app/admin/page.tsx and the API routes
admin/update, admin/create, admin/child (inline contact add / e-mail edit) and admin/export/*.

Each row is an independent set of pattern-matching components (keyed by ISO3). A row's Save /
contact callbacks write to Unity Catalog and publish a result record into the row's `adm-res`
store; one refresh callback shows the banner and re-renders the list when contacts changed.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from dash import ALL, MATCH, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate

import constants as C
import page_constants as P
from services import auth, db, exports
from services import repository as repo
from services import validation as V
from services.fallback_data import FALLBACK_COUNTRIES
from utils import forms, results, theme
from utils.components import banner, sign_out_button
from utils.routing import link, page_search

log = logging.getLogger(__name__)

PAGE = C.PAGE_ADMIN
PROTECTED = True

_ROW_BASE = "scroll-mt-20 rounded-lg border p-3 "
_ROW_NORMAL = _ROW_BASE + "border-brand-line bg-white"
_ROW_SAVED = _ROW_BASE + "border-brand-green/50 bg-brand-green/5"
_CONTACTS_CFG = C.CHILD_TABLE_BY_NAME[C.TBL_CONTACTS]


def _slug(region: str) -> str:
    return "region-" + re.sub(r"[^a-z0-9]+", "-", region, flags=re.IGNORECASE).lower()


# ── pattern-matching ids ────────────────────────────────────────────────────
def _rid(kind: str, iso: str) -> dict[str, str]:
    return {"type": f"adm-{kind}", "iso": iso}


def _cid(kind: str, iso: str, cid: str) -> dict[str, str]:
    return {"type": f"adm-{kind}", "iso": iso, "cid": cid}


# ── view ────────────────────────────────────────────────────────────────────
def _contact_chip(iso: str, p: dict[str, Any]) -> html.Div:
    has_email = V.has_valid_email(p.get("email"))
    return html.Div(
        [
            html.Span(p.get("name"), className="font-medium text-brand-navy"),
            forms.text_input(
                _cid("cemail", iso, p["id"]),
                p.get("email"),
                "email",
                class_name=(
                    "w-36 rounded border px-1 py-0.5 text-xs focus:border-brand-blue focus:outline-none focus:ring-1 focus:ring-brand-blue "
                    + ("border-gray-200" if has_email else "border-red-300 placeholder:text-red-400")
                ),
                placeholder="add e-mail",
                label=f"E-mail for {p.get('name')}",
            ),
            html.Button(
                "Save",
                id=_cid("csave", iso, p["id"]),
                n_clicks=0,
                className="rounded px-1.5 py-0.5 text-xs font-semibold text-brand-blue hover:bg-brand-tint",
            ),
        ],
        className="inline-flex items-center gap-1 rounded-full border bg-white py-0.5 pl-2 pr-1 text-xs "
        + ("border-brand-line" if has_email else "border-red-400 bg-red-50"),
        title=p.get("role") or None,
    )


def _country_row(r: dict[str, Any], contacts: list[dict[str, Any]], highlight: str | None) -> html.Div:
    iso = r["iso3"]
    contact_block = (
        [html.Span("No WB contacts yet", className="text-xs italic text-gray-400")]
        if not contacts
        else [_contact_chip(iso, p) for p in contacts]
    )
    return html.Div(
        [
            dcc.Store(id=_rid("res", iso)),
            # Row 1 — country fields
            html.Div(
                [
                    html.Span(iso, className="rounded bg-brand-tint px-2 py-1 text-xs font-bold text-brand-blue"),
                    forms.field(
                        "Name",
                        forms.text_input(_rid("name", iso), r.get("name"), class_name=f"{theme.INPUT_CLS} w-full"),
                        "min-w-[9rem] flex-1",
                    ),
                    forms.field(
                        "Region",
                        forms.text_input(_rid("region", iso), r.get("region"), class_name=f"{theme.INPUT_CLS} w-full"),
                        "w-28",
                    ),
                    forms.field(
                        "Status",
                        forms.select(_rid("status", iso), C.ENGAGEMENT_STATUSES, r.get("status"), class_name="w-full"),
                        "w-36",
                    ),
                    forms.field(
                        "Focus note",
                        forms.text_input(_rid("focus", iso), r.get("focus_note"), class_name=f"{theme.INPUT_CLS} w-full"),
                        "min-w-[12rem] flex-[2]",
                    ),
                    html.Button(
                        "Save",
                        id=_rid("save", iso),
                        n_clicks=0,
                        className="rounded bg-brand-blue px-4 py-1.5 text-sm font-semibold text-white hover:bg-brand-navy",
                    ),
                ],
                className="flex flex-wrap items-end gap-2",
            ),
            # Row 2 — World Bank focal points & team registry (read + inline edit + inline add)
            html.Div(
                [
                    html.Span("WB team", className="text-[10px] font-bold uppercase tracking-wider text-brand-mid"),
                    html.Div(contact_block, className="flex flex-1 flex-wrap items-center gap-1.5"),
                    html.Div(
                        [
                            forms.text_input(
                                _rid("qname", iso), "", class_name=f"{theme.INPUT_CLS} w-28", placeholder="Add name",
                                label=f"Add WB contact name for {r.get('name')}",
                            ),
                            forms.text_input(
                                _rid("qemail", iso), "", "email", class_name=f"{theme.INPUT_CLS} w-40", placeholder="e-mail",
                                label=f"Add WB contact e-mail for {r.get('name')}",
                            ),
                            forms.select(_rid("qrole", iso), C.WB_ROLES, C.FOCAL_ROLE, class_name="w-36"),
                            html.Button(
                                "+ Add",
                                id=_rid("qadd", iso),
                                n_clicks=0,
                                className="rounded border border-brand-blue px-3 py-1.5 text-xs font-semibold text-brand-blue hover:bg-brand-tint",
                            ),
                        ],
                        className="flex flex-wrap items-end gap-1.5",
                    ),
                    link("Manage →", C.PAGE_ADMIN_COUNTRY, "shrink-0 text-xs font-semibold text-brand-blue hover:underline", iso=iso),
                ],
                className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-2 border-t border-brand-line/60 pt-2",
            ),
        ],
        id=_rid("row", iso),
        className=_ROW_SAVED if highlight == iso else _ROW_NORMAL,
        **{"data-country": f"{r.get('name')} {iso} {r.get('region')}".lower()},
    )


def _list(rows: list[dict[str, Any]], contacts: list[dict[str, Any]], highlight: str | None = None) -> list[Any]:
    by_iso: dict[str, list[dict[str, Any]]] = {}
    for c in contacts:
        by_iso.setdefault(c["iso3"], []).append(c)
    by_region: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        by_region.setdefault(r["region"], []).append(r)
    return [
        html.Div(
            [
                html.H3(region, className="mb-2 text-xs font-bold uppercase tracking-widest text-brand-mid"),
                html.Div([_country_row(r, by_iso.get(r["iso3"], []), highlight) for r in items], className="space-y-2"),
            ],
            id=_slug(region),
            className="scroll-mt-20",
            **{"data-region-group": "1"},
        )
        for region, items in by_region.items()
    ]


def _stats(contacts: list[dict[str, Any]]) -> Any:
    total = len(contacts)
    if not total:
        return None
    with_email = sum(1 for p in contacts if V.has_valid_email(p.get("email")))
    missing = total - with_email
    parts: list[Any] = ["WB registry: ", html.B(str(with_email)), f"/{total} with e-mail"]
    if missing:
        parts.append(html.Span(f"· {missing} missing", className="ml-1 font-semibold text-red-600"))
    return parts


def _download_card(button_id: str, title: str, subtitle: str) -> html.Button:
    return html.Button(
        [
            html.Span("⬇", className="leading-5", **{"aria-hidden": "true"}),
            html.Span([title, html.Span(subtitle, className="mt-0.5 block text-[11px] font-normal text-gray-500")], className="text-left"),
        ],
        id=button_id,
        n_clicks=0,
        className="inline-flex items-start gap-2 rounded-lg border border-brand-blue bg-white px-4 py-3 text-sm font-semibold text-brand-blue hover:bg-brand-tint",
    )


def _load() -> tuple[list[dict[str, Any]], list[dict[str, Any]], str | None, bool]:
    """(rows, contacts, db_error, using_fallback)"""
    rows: list[dict[str, Any]] = []
    contacts: list[dict[str, Any]] = []
    db_error: str | None = None
    if repo.db_available():
        try:
            rows = repo.fetch_admin_rows()
            contacts = repo.fetch_wb_contacts()
        except db.DatabaseError as exc:
            db_error = str(exc)
    using_fallback = not rows
    if using_fallback and not db_error:
        rows = [
            {"iso3": c["iso3"], "name": c["name"], "region": c["region"], "status": c["status"], "focus_note": c["focus"], "ttl": c["contact"]}
            for c in FALLBACK_COUNTRIES
        ]
    return rows, contacts, db_error, using_fallback


def layout(params: dict[str, str]) -> Any:
    rows, contacts, db_error, using_fallback = _load()
    regions = list(dict.fromkeys(r["region"] for r in rows))

    initial_banners: list[Any] = []
    if db_error:
        initial_banners.append(banner("warn", [html.B("Database read error:"), f" {db_error}."]))
    if using_fallback and not db_error:
        initial_banners.append(banner("warn", [html.B("Showing the static snapshot"), " — ", P.ADMIN_FALLBACK_BANNER]))

    return html.Div(
        [
            dcc.Download(id="adm-dl"),
            dcc.Store(id="adm-last"),  # `t` of the last row result already shown (no initial data: a Store restores its own)
            html.Div(
                [
                    html.Div(
                        [
                            html.P(P.ADMIN_EYEBROW, className="text-xs font-semibold uppercase tracking-widest text-brand-mid"),
                            html.H1(P.ADMIN_TITLE, className="mt-1 text-3xl font-bold text-brand-blue"),
                            html.P(P.ADMIN_INTRO, className="mt-2 text-sm text-gray-600"),
                        ]
                    ),
                    html.Div(
                        [
                            link("Dashboard →", C.PAGE_ADMIN_DASHBOARD, "text-brand-blue hover:text-brand-navy"),
                            link("Review data →", C.PAGE_ADMIN_REVIEW, "text-brand-blue hover:text-brand-navy"),
                            link("View map →", C.PAGE_MAP, "text-brand-blue hover:text-brand-navy"),
                            sign_out_button(),
                        ],
                        className="flex items-center gap-4 text-sm",
                    ),
                ],
                className="flex flex-wrap items-end justify-between gap-3 border-b border-brand-line pb-4",
            ),
            html.Div(initial_banners, id="admin-banner"),
            # Excel downloads + WB registry completeness
            html.Section(
                [
                    html.Div(
                        [
                            html.H2(P.ADMIN_EXCEL_TITLE, className="text-sm font-bold uppercase tracking-wider text-brand-blue"),
                            html.Span(_stats(contacts), id="admin-stats", className="text-xs text-gray-600"),
                        ],
                        className="flex flex-wrap items-baseline justify-between gap-2",
                    ),
                    html.P(P.ADMIN_EXCEL_INTRO, className="mt-1 text-xs text-gray-600"),
                    html.Div(
                        [
                            _download_card("adm-dl-focal", *P.ADMIN_EXPORT_FOCAL),
                            _download_card("adm-dl-registry", *P.ADMIN_EXPORT_REGISTRY),
                        ],
                        className="mt-4 flex flex-wrap gap-3",
                    ),
                ],
                className="mt-8 rounded-xl border border-brand-line bg-white p-5",
            ),
            # Add new country engagement
            html.Section(
                [
                    html.H2(P.ADMIN_ADD_TITLE, className="text-sm font-bold uppercase tracking-wider text-brand-blue"),
                    html.P(P.ADMIN_ADD_INTRO, className="mt-1 text-xs text-gray-600"),
                    html.Div(
                        [
                            forms.field("ISO3 code *", forms.text_input("adm-add-iso3", "", placeholder="SRB", maxLength=3, class_name=f"{theme.INPUT_CLS} uppercase")),
                            forms.field("Country name *", forms.text_input("adm-add-name", "", placeholder="Serbia")),
                            forms.field("Region *", forms.text_input("adm-add-region", "", placeholder="ECA-West")),
                            forms.field("Engagement status *", forms.select("adm-add-status", C.ENGAGEMENT_STATUSES, "Inception")),
                            forms.field("Focal point (TTL)", forms.text_input("adm-add-ttl", "", placeholder="Name / lead")),
                            forms.field("Focus note", forms.text_input("adm-add-focus", "", placeholder="Short summary of engagement")),
                            html.Div(
                                html.Button(
                                    "Add country",
                                    id="adm-add-btn",
                                    n_clicks=0,
                                    className="rounded bg-brand-blue px-5 py-2 text-sm font-semibold text-white hover:bg-brand-navy",
                                ),
                                className="flex items-end sm:col-span-2 lg:col-span-3",
                            ),
                        ],
                        className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3",
                    ),
                ],
                className="mt-8 rounded-xl border border-brand-line bg-brand-tint/30 p-5",
            ),
            # Update existing country engagement
            html.Section(
                [
                    html.H2(P.ADMIN_UPDATE_TITLE, className="text-sm font-bold uppercase tracking-wider text-brand-blue"),
                    html.P(
                        P.ADMIN_UPDATE_INTRO.format(n=len(rows)),
                        id="admin-count",
                        className="mt-1 text-xs text-gray-600",
                    ),
                    html.Div(
                        [
                            forms.text_input(
                                "adm-search",
                                "",
                                "search",
                                theme.SEARCH_CLS,
                                label="Filter countries",
                                placeholder=P.ADMIN_SEARCH_PLACEHOLDER,
                            ),
                            html.Div(
                                [
                                    html.A(
                                        rg,
                                        href=f"#{_slug(rg)}",
                                        className="rounded-full border border-brand-line px-2.5 py-1 text-xs font-medium text-brand-blue hover:bg-brand-tint/50",
                                    )
                                    for rg in regions
                                ],
                                className="flex flex-wrap gap-1.5",
                            ),
                        ],
                        className="mt-4 flex flex-col gap-3",
                    ),
                    html.Div(_list(rows, contacts), id="admin-list", className="mt-5 space-y-8"),
                ],
                className="mt-10",
            ),
        ],
        className="mx-auto max-w-6xl px-6 py-10",
    )


# ── controller ──────────────────────────────────────────────────────────────
def _saved_banner(result: dict[str, Any]) -> html.Div:
    if result.get("ok") and result.get("iso"):
        verb = "Added" if result.get("kind") == "added" else "Saved"
        return banner("ok", [f"{verb} ", html.B(result["iso"]), " successfully."])
    return results.banner_from(result)


def _login_redirect() -> str:
    return page_search(C.PAGE_LOGIN, next=page_search(C.PAGE_ADMIN))


@results.guarded
def _do_row_save(iso: str, name: Any, region: Any, status: Any, focus: Any) -> dict[str, Any]:
    clean = V.clean_country_basics(
        {"iso3": iso, "name": name, "region": region, "status": status, "focus_note": focus}, require_valid_iso3=False
    )
    repo.update_country_basic(iso, clean["name"], clean["region"], clean["status"], clean["focus_note"])
    return results.ok("saved", refresh=False, iso=iso, kind="saved")


@results.guarded
def _do_contact_save(iso: str, contact_id: str, email: Any) -> dict[str, Any]:
    rec = V.build_child_record(_CONTACTS_CFG, {"email": email}, "update")
    repo.child_update(C.TBL_CONTACTS, iso, contact_id, rec)
    return results.ok("saved", iso=iso, kind="saved")


@results.guarded
def _do_contact_add(iso: str, name: Any, email: Any, role: Any) -> dict[str, Any]:
    rec = V.build_child_record(_CONTACTS_CFG, {"name": name, "email": email, "role": role}, "add")
    repo.child_add(C.TBL_CONTACTS, iso, rec)
    return results.ok("saved", iso=iso, kind="saved")


def register_callbacks(app) -> None:
    # Row 1: save name / region / status / focus
    @app.callback(
        Output(_rid("res", MATCH), "data", allow_duplicate=True),
        Output(_rid("row", MATCH), "className", allow_duplicate=True),
        Input(_rid("save", MATCH), "n_clicks"),
        State(_rid("name", MATCH), "value"),
        State(_rid("region", MATCH), "value"),
        State(_rid("status", MATCH), "value"),
        State(_rid("focus", MATCH), "value"),
        prevent_initial_call=True,
    )
    def _row_save(n, name, region, status, focus):
        if not n:
            raise PreventUpdate
        iso = ctx.triggered_id["iso"]
        res = _do_row_save(iso, name, region, status, focus)
        return res, (_ROW_SAVED if res.get("ok") else _ROW_NORMAL)

    # Row 2: edit an existing contact's e-mail in place
    @app.callback(
        Output(_rid("res", MATCH), "data", allow_duplicate=True),
        Input({"type": "adm-csave", "iso": MATCH, "cid": ALL}, "n_clicks"),
        State({"type": "adm-cemail", "iso": MATCH, "cid": ALL}, "value"),
        State({"type": "adm-cemail", "iso": MATCH, "cid": ALL}, "id"),
        prevent_initial_call=True,
    )
    def _contact_save(clicks, emails, ids):
        trig = ctx.triggered_id
        if not trig or not ctx.triggered[0]["value"]:
            raise PreventUpdate
        email = next((v for v, i in zip(emails, ids) if i["cid"] == trig["cid"]), "")
        return _do_contact_save(trig["iso"], trig["cid"], email)

    # Row 2: quick-add a WB contact
    @app.callback(
        Output(_rid("res", MATCH), "data", allow_duplicate=True),
        Input(_rid("qadd", MATCH), "n_clicks"),
        State(_rid("qname", MATCH), "value"),
        State(_rid("qemail", MATCH), "value"),
        State(_rid("qrole", MATCH), "value"),
        prevent_initial_call=True,
    )
    def _contact_add(n, name, email, role):
        if not n:
            raise PreventUpdate
        return _do_contact_add(ctx.triggered_id["iso"], name, email, role)

    # Show the banner for whichever row just finished; re-render the list when contacts changed
    @app.callback(
        Output("admin-banner", "children", allow_duplicate=True),
        Output("admin-list", "children", allow_duplicate=True),
        Output("admin-stats", "children", allow_duplicate=True),
        Output("pp-url", "search", allow_duplicate=True),
        Output("adm-last", "data"),
        Input(_rid("res", ALL), "data"),
        State("adm-last", "data"),
        prevent_initial_call=True,
    )
    def _refresh(all_results, last_handled):
        # Re-rendering the list re-mounts every row store, and a dcc.Store restores its old data —
        # so act only on the NEWEST result, and only once.
        fresh = [r for r in all_results or [] if isinstance(r, dict) and r.get("t")]
        if not fresh:  # freshly rendered (empty) stores
            raise PreventUpdate
        value = max(fresh, key=lambda r: r["t"])
        if value["t"] <= (last_handled or 0):
            raise PreventUpdate
        stamp = value["t"]
        if value.get("auth"):
            return no_update, no_update, no_update, _login_redirect(), stamp
        if not value.get("refresh"):
            return _saved_banner(value), no_update, no_update, no_update, stamp
        rows, contacts, db_error, _ = _load()
        if db_error:
            return banner("warn", [html.B("Database read error:"), f" {db_error}."]), no_update, no_update, no_update, stamp
        return _saved_banner(value), _list(rows, contacts, value.get("iso")), _stats(contacts), no_update, stamp

    # Add a new country
    @app.callback(
        Output("admin-banner", "children", allow_duplicate=True),
        Output("admin-list", "children", allow_duplicate=True),
        Output("admin-stats", "children", allow_duplicate=True),
        Output("admin-count", "children", allow_duplicate=True),
        Output("pp-url", "search", allow_duplicate=True),
        Output("adm-add-iso3", "value"),
        Output("adm-add-name", "value"),
        Output("adm-add-region", "value"),
        Output("adm-add-ttl", "value"),
        Output("adm-add-focus", "value"),
        Input("adm-add-btn", "n_clicks"),
        State("adm-add-iso3", "value"),
        State("adm-add-name", "value"),
        State("adm-add-region", "value"),
        State("adm-add-status", "value"),
        State("adm-add-ttl", "value"),
        State("adm-add-focus", "value"),
        prevent_initial_call=True,
    )
    def _add_country(n, iso3, name, region, status, ttl, focus):
        if not n:
            raise PreventUpdate
        keep = (no_update,) * 5  # leave the form as typed when something is wrong
        if not auth.is_authenticated():
            return no_update, no_update, no_update, no_update, _login_redirect(), *keep
        try:
            clean = V.clean_country_basics(
                {"iso3": iso3, "name": name, "region": region, "status": status, "ttl": ttl, "focus_note": focus},
                require_valid_iso3=True,
            )
            repo.create_country(clean["iso3"], clean["name"], clean["region"], clean["status"], clean["ttl"], clean["focus_note"])
        except V.ServiceError as exc:
            return results.banner_from(results.fail(exc.message, code=exc.code)), no_update, no_update, no_update, no_update, *keep
        rows, contacts, db_error, _ = _load()
        return (
            banner("ok", ["Added ", html.B(clean["iso3"]), " successfully."]),
            _list(rows, contacts, clean["iso3"]),
            _stats(contacts),
            P.ADMIN_UPDATE_INTRO.format(n=len(rows)),
            no_update,
            "", "", "", "", "",
        )

    # Excel downloads
    @app.callback(
        Output("adm-dl", "data", allow_duplicate=True),
        Output("admin-banner", "children", allow_duplicate=True),
        Input("adm-dl-focal", "n_clicks"),
        prevent_initial_call=True,
    )
    def _dl_focal(n):
        return _export(n, exports.focal_points_xlsx, C.XLSX_FOCAL_POINTS_FILENAME)

    @app.callback(
        Output("adm-dl", "data", allow_duplicate=True),
        Output("admin-banner", "children", allow_duplicate=True),
        Input("adm-dl-registry", "n_clicks"),
        prevent_initial_call=True,
    )
    def _dl_registry(n):
        return _export(n, exports.registry_xlsx, C.XLSX_REGISTRY_FILENAME)

    # Client-side filter (shows / hides the already-rendered rows and empty region groups)
    app.clientside_callback(
        """
        function (value) {
            if (window.ppAdmin) { window.ppAdmin.setFilter(value); }
            return window.dash_clientside.no_update;
        }
        """,
        Output("adm-search", "className"),
        Input("adm-search", "value"),
    )


def _export(n_clicks, builder, filename):
    if not n_clicks:
        raise PreventUpdate
    if not auth.is_authenticated():
        return no_update, banner("err", "Please sign in again.")
    if not repo.db_available():
        return no_update, banner("err", "Database not connected.")
    try:
        data = builder()
    except db.DatabaseError as exc:
        return no_update, banner("err", f"Could not build the export: {exc}")
    return dcc.send_bytes(data, filename), no_update
