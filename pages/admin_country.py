"""
admin_country.py — full-record country editor  (/?page=admin-country&iso=SRB).
Port of app/admin/country/[iso]/page.tsx, UnsavedGuard / ConfirmDeletes and the API routes
api/admin/country-update and api/admin/child.

How the original <form> posts map onto Dash:
  * "Save changes"  → one callback reads every field (pattern ids `ed-f`) and writes the country row.
  * per-record Save / Add / ✕ / Restore → one callback each, keyed by (table, record id).
  * Every write publishes a result record into the single `ed-res` store; one refresh callback
    shows the banner and re-renders whatever changed (the form after a full save, the records
    after a record action). A full save also re-reads `updated_at`, the optimistic-concurrency
    baseline.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from dash import ALL, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate

import constants as C
import page_constants as P
from services import db
from services import repository as repo
from services import validation as V
from utils import forms, results, theme
from utils import components as ui
from utils.layout import error_panel
from utils.routing import external_link, link, page_search, page_url

log = logging.getLogger(__name__)

PAGE = C.PAGE_ADMIN_COUNTRY
PROTECTED = True

_SAVE_BTN = "rounded bg-brand-blue px-6 py-2.5 text-sm font-semibold text-white hover:bg-brand-navy"
_REC_BTN = "rounded bg-brand-blue px-4 py-1.5 text-sm font-semibold text-white hover:bg-brand-navy"
_WIDE_INPUT = theme.INPUT_WIDE_CLS
_REC_INPUT = "w-full " + theme.INPUT_CLS
_MARK = {"data-pp-save": "1"}  # admin.js: any save clears the unsaved-changes guard


# ── ids ─────────────────────────────────────────────────────────────────────
def _fid(key: str) -> dict[str, str]:
    return {"type": "ed-f", "key": key}


def _rf(tbl: str, rid: str, key: str) -> dict[str, str]:
    return {"type": "ed-rf", "tbl": tbl, "rid": rid, "key": key}


def _af(tbl: str, key: str) -> dict[str, str]:
    return {"type": "ed-af", "tbl": tbl, "key": key}


# ── view: header ────────────────────────────────────────────────────────────
def _header_children(row: dict[str, Any]) -> list[Any]:
    iso = row["iso3"]
    return [
        html.Div(
            [
                link(P.EDITOR_BACK_LABEL, C.PAGE_ADMIN_REVIEW, "text-sm text-brand-blue hover:text-brand-navy"),
                html.H1(
                    [row.get("name"), " ", html.Span(iso, className="text-base font-normal text-gray-400")],
                    className="mt-2 text-3xl font-bold text-brand-blue",
                ),
                html.P(f"{row.get('region')} · {row.get('status')}", className="mt-1 text-sm text-gray-600"),
            ]
        ),
        html.Div(
            [
                external_link(P.EDITOR_PUBLIC_LABEL, page_url(C.PAGE_COUNTRY_DETAIL, iso=iso), "text-brand-blue hover:text-brand-navy"),
                ui.sign_out_button(),
            ],
            className="flex items-center gap-4 text-sm",
        ),
    ]


# ── view: the main form ─────────────────────────────────────────────────────
def _text_value(f: C.CountryField, val: Any) -> Any:
    if val is None:
        return ""
    if f.type == "date":
        return str(val)[:10]
    return ui.cell(val)


def _control(f: C.CountryField, val: Any) -> Any:
    fid = _fid(f.key)
    if f.type == "boolean":
        return html.Span(forms.checkbox(fid, ui.is_true(val), "Applied", class_name="pp-checkbox-lg"), className="mt-0.5 inline-flex items-center gap-2")
    if f.type == "textarea":
        return forms.textarea(fid, _text_value(f, val), rows=3, class_name=_WIDE_INPUT)
    if f.type == "select":
        return forms.select(fid, C.ENGAGEMENT_STATUSES, val or "Inception", class_name="w-full pp-select-lg")
    return forms.text_input(
        fid, _text_value(f, val), {"number": "number", "date": "date", "email": "email"}.get(f.type, "text"), class_name=_WIDE_INPUT
    )


def _field(f: C.CountryField, row: dict[str, Any]) -> Any:
    wide = f.type == "textarea"
    cls = "flex flex-col gap-1" + (" sm:col-span-2" if wide else "")
    label = html.Span(f.label, className="text-[11px] font-semibold uppercase tracking-wider text-gray-500")
    # A <label> may only wrap one control — the checkbox and the drop-down bring their own.
    tag = html.Label if f.type in ("text", "textarea", "date", "number", "email") else html.Div
    return tag([label, _control(f, row.get(f.key))], className=cls)


def _form_children(row: dict[str, Any]) -> list[Any]:
    out: list[Any] = [
        # Top save bar — one clear button so every field can be saved without scrolling to the bottom
        html.Div(
            [
                html.Button("Save changes", id="ed-save-top", n_clicks=0, className=_SAVE_BTN, **_MARK),
                html.Span(
                    ["Saves ", html.B("every field"), " in this form at once. (Records below save with their own buttons.)"],
                    className="text-xs text-gray-500",
                ),
            ],
            className="sticky top-0 z-10 -mx-2 flex items-center gap-3 rounded-lg border border-brand-line bg-white/95 px-4 py-3 shadow-sm backdrop-blur",
        )
    ]
    for group in C.FIELD_GROUPS:
        fields = [f for f in C.COUNTRY_FIELDS if f.group == group]
        if not fields:
            continue
        out.append(
            html.Section(
                [
                    html.H2(group, className="text-xs font-bold uppercase tracking-widest text-brand-mid"),
                    html.Div([_field(f, row) for f in fields], className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2"),
                ]
            )
        )
    out.append(
        html.Div(
            [
                html.Button("Save changes", id="ed-save-bottom", n_clicks=0, className=_SAVE_BTN, **_MARK),
                link("Cancel", C.PAGE_ADMIN_REVIEW, "text-sm text-gray-600 hover:text-gray-800"),
                html.Span("Saves every field above at once.", className="text-xs text-gray-400"),
            ],
            className="flex items-center gap-3 border-t border-brand-line pt-5",
        )
    )
    return out


# ── view: records ───────────────────────────────────────────────────────────
def _record_field(f: C.ChildField, field_id: dict[str, str], value: Any = None) -> html.Div:
    wide = f.key in ("notes", "name")
    label = html.Span(f"{f.label}{' *' if f.required else ''}", className="text-[10px] font-semibold uppercase tracking-wider text-gray-500")
    if f.type == "select":
        cur = "" if value is None else str(value)
        opts = list(f.options)
        if cur and cur not in opts:  # keep a pre-existing value that isn't in the predefined list
            opts = [cur, *opts]
        control = forms.select(field_id, opts, cur, class_name="w-full", allow_empty=True)
    else:
        text = "" if value is None else (str(value)[:10] if f.type == "date" else ui.cell(value))
        kwargs: dict[str, Any] = {}
        if f.placeholder:
            kwargs["placeholder"] = f.placeholder
        control = forms.text_input(
            field_id, text, {"number": "number", "date": "date", "url": "url", "email": "email"}.get(f.type, "text"), class_name=_REC_INPUT, **kwargs
        )
    cls = "flex flex-col gap-1 " + ("min-w-[12rem] flex-1" if wide else "w-32")
    # <div>, not <label>: the drop-down and the number / date inputs bring their own focus handling.
    return html.Div([label, control], className=cls)


def _record_row(cfg: C.ChildTable, row: dict[str, Any]) -> html.Div:
    rid = str(row["id"])
    return html.Div(
        [
            *[_record_field(f, _rf(cfg.table, rid, f.key), row.get(f.key)) for f in cfg.fields],
            html.Button("Save", id={"type": "ed-rsave", "tbl": cfg.table, "rid": rid}, n_clicks=0, className=_REC_BTN, **_MARK),
            dcc.ConfirmDialogProvider(
                html.Button(
                    "✕",
                    n_clicks=0,
                    title="Delete",
                    className="rounded px-2 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50",
                    **_MARK,
                ),
                id={"type": "ed-rdel", "tbl": cfg.table, "rid": rid},
                message=P.EDITOR_DELETE_CONFIRM,
            ),
        ],
        className="flex flex-wrap items-end gap-2 rounded-lg border border-brand-line bg-white p-3",
    )


def _add_row(cfg: C.ChildTable) -> html.Div:
    required = [f.label for f in cfg.fields if f.required]
    children: list[Any] = [_record_field(f, _af(cfg.table, f.key)) for f in cfg.fields]
    children.append(html.Button("Add", id={"type": "ed-aadd", "tbl": cfg.table}, n_clicks=0, className=_REC_BTN, **_MARK))
    if required:
        children.append(html.Span(f"{' & '.join(required)} required", className="self-center text-[11px] text-gray-400"))
    return html.Div(children, className="flex flex-wrap items-end gap-2 rounded-lg border border-dashed border-brand-line bg-brand-tint/20 p-3")


def _child_section(cfg: C.ChildTable, rows: list[dict[str, Any]], just_saved: bool) -> html.Section:
    head: list[Any] = [html.H3(cfg.label, className="text-sm font-bold uppercase tracking-widest text-brand-mid")]
    if just_saved:
        head.append(html.Span("✓ Saved", className="rounded-full bg-brand-green/10 px-2 py-0.5 text-xs font-semibold text-brand-green"))
    if cfg.hint:
        head.append(html.Span(cfg.hint, className="text-xs text-gray-400"))
    head.append(html.Span(f"{len(rows)} record{'' if len(rows) == 1 else 's'}", className="ml-auto text-xs text-gray-400"))
    return html.Section(
        [
            html.Div(head, className="flex flex-wrap items-baseline gap-2"),
            html.Div([*[_record_row(cfg, r) for r in rows], _add_row(cfg)], className="mt-3 space-y-2"),
        ],
        id=f"records-{cfg.table}",
        className="scroll-mt-20",
    )


def _payload(d: dict[str, Any]) -> dict[str, Any]:
    raw = d.get("payload")
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else {}
    except ValueError:
        parsed = {}
    return parsed if isinstance(parsed, dict) else {}


def _deleted_section(rows: list[dict[str, Any]]) -> html.Div:
    def label_of(table: str) -> str:
        cfg = C.CHILD_TABLE_BY_NAME.get(table)
        return cfg.label if cfg else table

    def summarize(p: dict[str, Any]) -> str:
        parts = [str(p[k]) for k in ("name", "type", "code", "date", "location") if p.get(k)]
        return " · ".join(parts[:2]) or "(record)"

    items = []
    for d in rows:
        items.append(
            html.Li(
                [
                    html.Span(
                        [
                            html.Span(label_of(d.get("table_name")), className="text-[10px] font-bold uppercase tracking-wider text-gray-400"),
                            " ",
                            html.Span(summarize(_payload(d)), className="font-medium text-brand-navy"),
                        ],
                        className="text-gray-700",
                    ),
                    html.Button(
                        "Restore",
                        id={"type": "ed-restore", "tbl": d.get("table_name"), "did": str(d["id"])},
                        n_clicks=0,
                        className="rounded border border-brand-blue px-3 py-1 text-xs font-semibold text-brand-blue hover:bg-brand-tint",
                        **_MARK,
                    ),
                ],
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-brand-line bg-gray-50 px-3 py-2 text-sm",
            )
        )
    return html.Div(
        [
            html.H3(P.EDITOR_DELETED_TITLE, className="text-sm font-bold uppercase tracking-widest text-brand-mid"),
            html.P(P.EDITOR_DELETED_NOTE, className="mt-1 text-xs text-gray-500"),
            html.Ul(items, className="mt-3 space-y-2"),
        ],
        className="mt-12 border-t border-brand-line pt-6",
    )


def _records_children(bundle: repo.EditorBundle, saved_table: str | None = None) -> list[Any]:
    out: list[Any] = [
        html.Div(
            [_child_section(cfg, bundle.children.get(cfg.table, []), saved_table == cfg.table) for cfg in C.CHILD_TABLES],
            className="mt-6 space-y-10",
        )
    ]
    if bundle.deleted:
        out.append(_deleted_section(bundle.deleted))
    return out


# ── layout ──────────────────────────────────────────────────────────────────
def layout(params: dict[str, str]) -> Any:
    from pages import not_found

    iso = V.normalise_iso3(params.get("iso"))
    if not V.is_valid_iso3(iso):
        return not_found.layout(params)

    def back_link() -> Any:
        return link(P.EDITOR_BACK_LABEL, C.PAGE_ADMIN_REVIEW, "mt-4 inline-block text-sm text-brand-blue")

    if not repo.db_available():
        return html.Div([html.P(P.EDITOR_NO_DB, className="text-sm text-amber-800"), back_link()], className="mx-auto max-w-3xl px-6 py-12")
    try:
        bundle = repo.fetch_editor_bundle(iso)
    except db.DatabaseError as exc:
        log.exception("Could not load %s", iso)
        return html.Div([error_panel(f"Could not load this record: {exc}"), back_link()])
    row = bundle.country
    if not row:
        return not_found.layout(params)

    return html.Div(
        [
            dcc.Store(id="ed-iso", data=iso),
            dcc.Store(id="ed-baseline", data=repo.to_iso(row.get("updated_at")) or ""),
            dcc.Store(id="ed-res"),
            dcc.Store(id="ed-last"),  # `t` of the last result already handled (no initial data: a Store restores its own)
            dcc.Store(id="ed-fx"),
            html.Div(
                _header_children(row),
                id="ed-header",
                className="flex flex-wrap items-end justify-between gap-3 border-b border-brand-line pb-4",
            ),
            html.Div(id="ed-banner"),
            html.Div(_form_children(row), id="country-form", className="mt-6 space-y-8"),
            html.Div(
                [
                    html.H2("Records", className="text-2xl font-bold text-brand-blue"),
                    html.P(P.EDITOR_RECORDS_INTRO.format(name=row.get("name")), className="mt-1 text-sm text-gray-600"),
                    html.P(P.EDITOR_RECORDS_WARNING, className="mt-1 text-xs text-amber-700"),
                    html.Div(_records_children(bundle), id="ed-records"),
                ],
                className="mt-12 border-t border-brand-line pt-8",
            ),
        ],
        className="mx-auto max-w-4xl px-6 py-10",
    )


# ── controller ──────────────────────────────────────────────────────────────
def _login_redirect(iso: str) -> str:
    return page_search(C.PAGE_LOGIN, next=page_search(C.PAGE_ADMIN_COUNTRY, iso=iso))


def _valid_iso(iso: Any) -> str:
    iso = V.normalise_iso3(iso)
    if not V.is_valid_iso3(iso):
        raise V.ServiceError(V.ERR_INVALID)
    return iso


@results.guarded
def _do_fields_save(iso: Any, fields: dict[str, Any], baseline: Any) -> dict[str, Any]:
    iso = _valid_iso(iso)
    repo.update_country_full(iso, V.clean_country_update(fields), V.as_text(baseline) or None)
    return results.ok("saved", kind="fields", iso=iso)


@results.guarded
def _do_record_save(iso: Any, tbl: str, rid: str, fields: dict[str, Any]) -> dict[str, Any]:
    iso = _valid_iso(iso)
    cfg = C.CHILD_TABLE_BY_NAME.get(tbl)
    if cfg is None:
        raise V.ServiceError(V.ERR_INVALID)
    repo.child_update(tbl, iso, rid, V.build_child_record(cfg, fields, "update"))
    return results.ok("saved", kind="record", tbl=tbl, iso=iso)


@results.guarded
def _do_record_add(iso: Any, tbl: str, fields: dict[str, Any]) -> dict[str, Any]:
    iso = _valid_iso(iso)
    cfg = C.CHILD_TABLE_BY_NAME.get(tbl)
    if cfg is None:
        raise V.ServiceError(V.ERR_INVALID)
    repo.child_add(tbl, iso, V.build_child_record(cfg, fields, "add"))
    return results.ok("saved", kind="record", tbl=tbl, iso=iso)


@results.guarded
def _do_record_delete(iso: Any, tbl: str, rid: str) -> dict[str, Any]:
    repo.child_delete(tbl, _valid_iso(iso), rid)
    return results.ok("saved", kind="record", tbl=tbl, iso=V.normalise_iso3(iso))


@results.guarded
def _do_record_restore(iso: Any, tbl: str, did: str) -> dict[str, Any]:
    repo.child_restore(tbl, _valid_iso(iso), did)
    return results.ok("saved", kind="record", tbl=tbl, iso=V.normalise_iso3(iso))


def _failed(res: dict[str, Any], kind: str) -> dict[str, Any]:
    res.setdefault("kind", kind)
    return res


def _collect(values: list[Any], ids: list[dict[str, Any]], **match: str) -> dict[str, Any]:
    """The values of the fields whose pattern id carries every `match` pair, keyed by field key."""
    return {i["key"]: v for v, i in zip(values, ids) if all(i.get(k) == want for k, want in match.items())}


def register_callbacks(app) -> None:
    # "Save changes" (top or bottom button)
    @app.callback(
        Output("ed-res", "data", allow_duplicate=True),
        Input("ed-save-top", "n_clicks"),
        Input("ed-save-bottom", "n_clicks"),
        State({"type": "ed-f", "key": ALL}, "value"),
        State({"type": "ed-f", "key": ALL}, "id"),
        State("ed-iso", "data"),
        State("ed-baseline", "data"),
        prevent_initial_call=True,
    )
    def _save_fields(top, bottom, values, ids, iso, baseline):
        if not (top or bottom):
            raise PreventUpdate
        return _failed(_do_fields_save(iso, _collect(values, ids), baseline), "fields")

    # A record's own "Save"
    @app.callback(
        Output("ed-res", "data", allow_duplicate=True),
        Input({"type": "ed-rsave", "tbl": ALL, "rid": ALL}, "n_clicks"),
        State({"type": "ed-rf", "tbl": ALL, "rid": ALL, "key": ALL}, "value"),
        State({"type": "ed-rf", "tbl": ALL, "rid": ALL, "key": ALL}, "id"),
        State("ed-iso", "data"),
        prevent_initial_call=True,
    )
    def _save_record(_clicks, values, ids, iso):
        trig = ctx.triggered_id
        if not trig or not ctx.triggered[0]["value"]:
            raise PreventUpdate
        fields = _collect(values, ids, tbl=trig["tbl"], rid=trig["rid"])
        return _failed(_do_record_save(iso, trig["tbl"], trig["rid"], fields), "record")

    # The dashed "Add" row
    @app.callback(
        Output("ed-res", "data", allow_duplicate=True),
        Input({"type": "ed-aadd", "tbl": ALL}, "n_clicks"),
        State({"type": "ed-af", "tbl": ALL, "key": ALL}, "value"),
        State({"type": "ed-af", "tbl": ALL, "key": ALL}, "id"),
        State("ed-iso", "data"),
        prevent_initial_call=True,
    )
    def _add_record(_clicks, values, ids, iso):
        trig = ctx.triggered_id
        if not trig or not ctx.triggered[0]["value"]:
            raise PreventUpdate
        return _failed(_do_record_add(iso, trig["tbl"], _collect(values, ids, tbl=trig["tbl"])), "record")

    # ✕ (after the confirmation dialog)
    @app.callback(
        Output("ed-res", "data", allow_duplicate=True),
        Input({"type": "ed-rdel", "tbl": ALL, "rid": ALL}, "submit_n_clicks"),
        State("ed-iso", "data"),
        prevent_initial_call=True,
    )
    def _delete_record(_clicks, iso):
        trig = ctx.triggered_id
        if not trig or not ctx.triggered[0]["value"]:
            raise PreventUpdate
        return _failed(_do_record_delete(iso, trig["tbl"], trig["rid"]), "record")

    # "Restore" in Recently deleted
    @app.callback(
        Output("ed-res", "data", allow_duplicate=True),
        Input({"type": "ed-restore", "tbl": ALL, "did": ALL}, "n_clicks"),
        State("ed-iso", "data"),
        prevent_initial_call=True,
    )
    def _restore_record(_clicks, iso):
        trig = ctx.triggered_id
        if not trig or not ctx.triggered[0]["value"]:
            raise PreventUpdate
        return _failed(_do_record_restore(iso, trig["tbl"], trig["did"]), "record")

    # Banner + re-render whatever changed
    @app.callback(
        Output("ed-banner", "children"),
        Output("ed-header", "children"),
        Output("country-form", "children"),
        Output("ed-baseline", "data"),
        Output("ed-records", "children"),
        Output("pp-url", "search", allow_duplicate=True),
        Output("ed-last", "data"),
        Input("ed-res", "data"),
        State("ed-iso", "data"),
        State("ed-last", "data"),
        prevent_initial_call=True,
    )
    def _refresh(res, iso, last_handled):
        # a dcc.Store restores its old data when the page is re-mounted — handle each result once
        if not res or res.get("t", 0) <= (last_handled or 0):
            raise PreventUpdate
        stamp = res["t"]
        keep = (no_update,) * 4
        if res.get("auth"):
            return (no_update,) * 5 + (_login_redirect(V.normalise_iso3(iso)), stamp)
        if not res.get("ok"):
            return (results.banner_from(res, P.EDITOR_ERRORS),) + keep + (no_update, stamp)
        ok_banner = ui.banner("ok", P.EDITOR_SAVED_MESSAGE)
        try:
            bundle = repo.fetch_editor_bundle(V.normalise_iso3(iso))
        except db.DatabaseError as exc:
            return (ui.banner("warn", [html.B("Database read error:"), f" {exc}."]),) + keep + (no_update, stamp)
        row = bundle.country
        if not row:
            return (ui.banner("err", P.EDITOR_NOT_FOUND),) + keep + (no_update, stamp)
        if res.get("kind") == "fields":
            return (
                ok_banner,
                _header_children(row),
                _form_children(row),
                repo.to_iso(row.get("updated_at")) or "",
                no_update,
                no_update,
                stamp,
            )
        return ok_banner, no_update, no_update, no_update, _records_children(bundle, res.get("tbl")), no_update, stamp

    # Bring the banner into view after a full save / an error, and re-arm the unsaved-changes guard
    # when a full save was refused (the typed values are still on screen, unsaved).
    app.clientside_callback(
        """
        function (res) {
          if (!res) { return window.dash_clientside.no_update; }
          if (!res.ok && res.kind === 'fields' && window.ppAdmin) { window.ppAdmin.markDirty(); }
          if (!res.ok || res.kind === 'fields') { window.scrollTo({ top: 0, behavior: 'smooth' }); }
          return Date.now();
        }
        """,
        Output("ed-fx", "data"),
        Input("ed-res", "data"),
        prevent_initial_call=True,
    )
