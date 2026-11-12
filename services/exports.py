"""
exports.py — Excel (.xlsx) extracts for the /admin "Excel downloads" section.

Ports `app/api/admin/export/focal-points` and `.../wb-registry`. Both build the
workbook in memory and return the raw bytes; the page hands them to a
`dcc.Download`. Callers must have checked `auth.is_authenticated()` first.
"""
from __future__ import annotations

import unicodedata
from datetime import datetime
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

import constants as C
from services import repository as repo

_HEADER_FILL = PatternFill("solid", fgColor="374291")
_HEADER_FONT = Font(bold=True, color="FFFFFF")
_THIN = Side(style="thin", color="C9D3EA")
_BORDER = Border(top=_THIN, bottom=_THIN, left=_THIN, right=_THIN)
_WARN_FILL = PatternFill("solid", fgColor="FCE4E2")
_WARN_FONT = Font(bold=True, color="C0392B")


def _sort_key(text: str) -> str:
    """Accent- and case-insensitive ordering, like JavaScript's String.localeCompare."""
    folded = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in folded if not unicodedata.combining(ch)).casefold()


def _country_map() -> dict[str, dict[str, Any]]:
    return {c["iso3"]: c for c in repo.fetch_countries_full()}


def _stamp(value: Any) -> str:
    return repo.to_iso(value) or ""


def _build(sheet_title: str, columns: list[tuple[str, int]], rows: list[list[Any]], warn_col: int | None = None) -> bytes:
    wb = Workbook()
    wb.properties.creator = C.DOCX_CREATOR
    wb.properties.created = datetime(1970, 1, 1)  # deterministic — no volatile timestamp embedded
    ws = wb.active
    ws.title = sheet_title
    ws.freeze_panes = "A2"

    for idx, (header, width) in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=idx, value=header)
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = Alignment(vertical="center")
        ws.column_dimensions[cell.column_letter].width = width
    ws.row_dimensions[1].height = 20

    for r_idx, values in enumerate(rows, start=2):
        for c_idx, value in enumerate(values, start=1):
            ws.cell(row=r_idx, column=c_idx, value=value)
        if warn_col is not None and values[warn_col - 1] == "No":
            flagged = ws.cell(row=r_idx, column=warn_col)
            flagged.font = _WARN_FONT
            flagged.fill = _WARN_FILL

    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=len(columns)):
        for cell in row:
            cell.border = _BORDER
    last_col = ws.cell(row=1, column=len(columns)).column_letter
    ws.auto_filter.ref = f"A1:{last_col}1"

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def focal_points_xlsx() -> bytes:
    """Every World Bank focal point: country · name · e-mail · country record last updated."""
    countries = _country_map()
    contacts = [c for c in repo.fetch_wb_contacts() if c.get("role") == C.FOCAL_ROLE]
    items = []
    for p in contacts:
        country = countries.get(p["iso3"])
        items.append(
            (
                (country or {}).get("name") or p["iso3"],
                p.get("name") or "",
                p.get("email") or "",
                _stamp((country or {}).get("last_updated")),
            )
        )
    items.sort(key=lambda r: (_sort_key(r[0]), _sort_key(r[1])))
    return _build(
        "WB Focal Points",
        [("Country", 28), ("Focal point (name)", 30), ("E-mail", 34), ("Country record last updated", 26)],
        [list(r) for r in items],
    )


def registry_xlsx() -> bytes:
    """Master registry: all roles, with an e-mail-completeness flag (missing e-mails highlighted)."""
    countries = _country_map()
    items = []
    for p in repo.fetch_wb_contacts():
        country = countries.get(p["iso3"])
        has_email = bool(p.get("email")) and "@" in str(p["email"])
        items.append(
            {
                "country": (country or {}).get("name") or p["iso3"],
                "role": p.get("role") or "",
                "name": p.get("name") or "",
                "email": p.get("email") or "",
                "complete": "Yes" if has_email else "No",
                "last": _stamp((country or {}).get("last_updated")),
                "order": C.ROLE_ORDER.get(p.get("role") or "", 9),
            }
        )
    items.sort(key=lambda r: (_sort_key(r["country"]), r["order"], _sort_key(r["name"])))
    return _build(
        "WB Registry",
        [
            ("Country", 26),
            ("Role", 24),
            ("Name", 28),
            ("E-mail", 34),
            ("E-mail complete?", 16),
            ("Country record last updated", 26),
        ],
        [[r["country"], r["role"], r["name"], r["email"], r["complete"], r["last"]] for r in items],
        warn_col=5,
    )
