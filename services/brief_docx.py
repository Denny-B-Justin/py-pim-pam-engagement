"""
brief_docx.py — the filled Word (.docx) country brief.

Port of `lib/countryDocx.ts`. It mirrors the on-page profile and respects the same
two tiers: the staff-only sections are included only when `authed` is True.
Sizes, colours, column widths and wording are carried over unchanged
(US Letter, 1" margins, Arial 10.5 pt).
"""
from __future__ import annotations

import re
from datetime import date, datetime
from io import BytesIO
from typing import Any, Sequence

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Twips

import constants as C

NAVY = "374291"
MID = "3675B7"
LINE = "C9D3EA"
TINTHDR = "DEE5F5"
GRAY = "8A94A6"
TEXT = "33373F"
CONTENT = 9360  # US Letter, 1" margins, in twips


# ── tiny helpers ────────────────────────────────────────────────────────────
def txt(value: Any) -> str:
    """Display text for a record value (None → '', 3.0 → '3', dates → ISO)."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, (datetime, date)):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
    return str(value).strip()


def has(value: Any) -> bool:
    return txt(value) != ""


def _rgb(hex6: str) -> RGBColor:
    return RGBColor.from_string(hex6)


def _run(par, text: str, *, size: float | None = None, bold: bool = False, italic: bool = False, color: str | None = None):
    r = par.add_run(text)
    if size is not None:
        r.font.size = Pt(size)
    r.font.bold = bold or None
    r.font.italic = italic or None
    if color:
        r.font.color.rgb = _rgb(color)
    return r


def _spacing(par, before: int = 0, after: int = 0) -> None:
    pf = par.paragraph_format
    pf.space_before = Twips(before)
    pf.space_after = Twips(after)


def _bottom_border(par, size: int, color: str, space: int) -> None:
    ppr = par._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(size))
    bottom.set(qn("w:space"), str(space))
    bottom.set(qn("w:color"), color)
    borders.append(bottom)
    ppr.append(borders)


def _shade_run(run, fill: str) -> None:
    rpr = run._r.get_or_add_rPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    rpr.append(shd)


def _shade_cell(cell, fill: str) -> None:
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcpr.append(shd)


def _set_font(style, size_pt: float, bold: bool | None, color: str) -> None:
    style.font.name = "Arial"
    style.font.size = Pt(size_pt)
    style.font.bold = bold
    style.font.color.rgb = _rgb(color)
    rpr = style.element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.insert(0, fonts)
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if fonts.get(qn(attr)) is not None:
            del fonts.attrib[qn(attr)]
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        fonts.set(qn(attr), "Arial")


# ── document building blocks ────────────────────────────────────────────────
class _Brief:
    def __init__(self, name: str) -> None:
        self.name = name
        self.doc = Document()
        self._setup()

    def _setup(self) -> None:
        d = self.doc
        sec = d.sections[0]
        sec.page_width, sec.page_height = Twips(12240), Twips(15840)
        sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Twips(1440)

        normal = d.styles["Normal"]
        _set_font(normal, 10.5, None, TEXT)
        normal.paragraph_format.space_before = Twips(0)
        normal.paragraph_format.space_after = Twips(0)
        normal.paragraph_format.line_spacing = 1.0

        h1 = d.styles["Heading 1"]
        _set_font(h1, 15, True, NAVY)
        h1.paragraph_format.space_before = Twips(240)
        h1.paragraph_format.space_after = Twips(120)
        h1.paragraph_format.line_spacing = 1.0

        h2 = d.styles["Heading 2"]
        _set_font(h2, 11, True, NAVY)
        h2.paragraph_format.space_before = Twips(200)
        h2.paragraph_format.space_after = Twips(60)
        h2.paragraph_format.line_spacing = 1.0
        ppr = h2.element.get_or_add_pPr()
        borders = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        for k, v in (("w:val", "single"), ("w:sz", "6"), ("w:space", "4"), ("w:color", LINE)):
            bottom.set(qn(k), v)
        borders.append(bottom)
        ppr.append(borders)

        props = d.core_properties
        props.author = C.DOCX_CREATOR
        props.last_modified_by = C.DOCX_CREATOR
        props.title = f"{self.name} — PIM-PAM Country Engagement Brief"
        props.comments = ""

        # footer: "<name> — PIM-PAM Country Engagement Brief      Page <n>"
        footer = sec.footer
        footer.is_linked_to_previous = False
        par = footer.paragraphs[0]
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _run(par, f"{self.name} — PIM-PAM Country Engagement Brief      Page ", size=7.5, color=GRAY)
        # PAGE field as a complex field; every run carries the size so the number matches the text
        for kind, text in (("begin", None), ("instr", " PAGE "), ("separate", None), ("text", "1"), ("end", None)):
            run = _run(par, "", size=7.5, color=GRAY)
            if kind == "instr":
                el = OxmlElement("w:instrText")
                el.set(qn("xml:space"), "preserve")
                el.text = text
                run._r.append(el)
            elif kind == "text":
                run.text = text
            else:
                el = OxmlElement("w:fldChar")
                el.set(qn("w:fldCharType"), kind)
                run._r.append(el)

    # paragraphs -------------------------------------------------------------
    def para(self, text: str = "", *, size: float = 10.5, bold: bool = False, italic: bool = False,
             color: str = TEXT, before: int = 0, after: int = 0):
        p = self.doc.add_paragraph()
        _spacing(p, before, after)
        if text:
            _run(p, text, size=size, bold=bold, italic=italic, color=color)
        return p

    def heading(self, label: str) -> None:
        self.doc.add_paragraph(label, style="Heading 2")

    def heading1(self, label: str) -> None:
        self.doc.add_paragraph(label, style="Heading 1")

    def not_set(self) -> None:
        self.para("Not recorded yet", italic=True, color=GRAY, after=120)

    def prose(self, label: str, value: Any) -> None:
        """Always rendered: a placeholder shows when empty, so the brief doubles as a completeness check."""
        self.heading(label)
        if has(value):
            self.para(txt(value), size=10.5, after=120)
        else:
            self.not_set()

    def narrative(self, value: Any) -> None:
        if has(value):
            self.para(txt(value), size=10, after=100)
        else:
            self.not_set()

    def empty_hint(self, text: str) -> None:
        self.para(text, size=9, italic=True, color=GRAY, after=120)

    def spacer(self) -> None:
        self.para("", after=120)

    # table ------------------------------------------------------------------
    def table(self, headers: Sequence[str], widths: Sequence[int], rows: Sequence[Sequence[str]]) -> None:
        tbl = self.doc.add_table(rows=1 + len(rows), cols=len(headers))
        tbl.autofit = False
        tblpr = tbl._tbl.tblPr

        layout = OxmlElement("w:tblLayout")
        layout.set(qn("w:type"), "fixed")
        tblpr.append(layout)
        tblw = tblpr.find(qn("w:tblW"))
        if tblw is None:
            tblw = OxmlElement("w:tblW")
            tblpr.append(tblw)
        tblw.set(qn("w:w"), str(CONTENT))
        tblw.set(qn("w:type"), "dxa")

        borders = OxmlElement("w:tblBorders")
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            el = OxmlElement(f"w:{edge}")
            for k, v in (("w:val", "single"), ("w:sz", "4"), ("w:space", "0"), ("w:color", LINE)):
                el.set(qn(k), v)
            borders.append(el)
        tblpr.append(borders)

        margins = OxmlElement("w:tblCellMar")
        for edge, val in (("top", 80), ("left", 120), ("bottom", 80), ("right", 120)):
            el = OxmlElement(f"w:{edge}")
            el.set(qn("w:w"), str(val))
            el.set(qn("w:type"), "dxa")
            margins.append(el)
        tblpr.append(margins)

        for i, w in enumerate(widths):
            tbl.columns[i].width = Twips(w)

        def fill(cell, text: str, i: int, *, header: bool) -> None:
            cell.width = Twips(widths[i])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER if header else WD_CELL_VERTICAL_ALIGNMENT.TOP
            par = cell.paragraphs[0]
            _spacing(par, 0, 0)
            if header:
                _shade_cell(cell, TINTHDR)
                _run(par, text, size=8, bold=True, color=NAVY)
            else:
                _run(par, text or "", size=8.5, color=TEXT)

        for i, h in enumerate(headers):
            fill(tbl.rows[0].cells[i], h, i, header=True)
        trpr = tbl.rows[0]._tr.get_or_add_trPr()
        trpr.append(OxmlElement("w:tblHeader"))
        for r_idx, row in enumerate(rows, start=1):
            for i, text in enumerate(row):
                fill(tbl.rows[r_idx].cells[i], text, i, header=False)


def _safe_filename(name: str, iso3: str) -> str:
    safe = re.sub(r"[^a-z0-9]+", "_", name or iso3, flags=re.IGNORECASE).strip("_")
    return f"PIM-PAM_{safe}_brief.docx"


def brief_filename(country: dict[str, Any], iso3: str) -> str:
    return _safe_filename(str(country.get("name") or iso3), iso3)


def build_country_brief(
    country: dict[str, Any],
    contacts: Sequence[dict[str, Any]],
    counterparts: Sequence[dict[str, Any]],
    assessments: Sequence[dict[str, Any]],
    projects: Sequence[dict[str, Any]],
    events: Sequence[dict[str, Any]],
    authed: bool,
) -> bytes:
    c = country or {}
    name = txt(c.get("name")) or "Country"
    region = txt(c.get("region"))
    status = txt(c.get("status")) or "—"
    b = _Brief(name)

    # ── title block ──
    b.para(name, size=20, bold=True, color=NAVY, after=40)
    b.para("PIM-PAM Country Engagement Brief", size=12, color=MID, after=40)
    sub = b.para(
        "   ·   ".join(
            x for x in (region, f"Maturity: {status}", f"Last updated {txt(c.get('last_updated'))}" if has(c.get("last_updated")) else "") if x
        ),
        size=9,
        italic=True,
        color=GRAY,
        after=160,
    )
    _bottom_border(sub, 12, NAVY, 6)

    # ── public tier ──
    b.prose("Focus", c.get("focus_note"))
    b.prose("Summary", c.get("summary"))
    b.heading1("Engagement brief")
    for f in C.BRIEF_FIELDS:
        b.prose(f.label, c.get(f.key))
    b.prose("Regional Management/Staff Unit Engagements", c.get("regional_engagements"))

    b.heading("Profile details")
    b.para(
        "    ·    ".join(
            (
                f"Language: {txt(c.get('language')) if has(c.get('language')) else '—'}",
                f"Last updated: {txt(c.get('last_updated')) if has(c.get('last_updated')) else '—'}",
            )
        ),
        size=9.5,
        after=120,
    )

    # ── staff tier ──
    if authed:
        tag = b.para("", before=240, after=120)
        _bottom_border(tag, 6, LINE, 4)
        _shade_run(_run(tag, "  STAFF DETAIL  ", size=7, bold=True, color="FFFFFF"), MID)

        b.prose("Latest status", c.get("status_note"))

        b.heading("World Bank Managers & Staff")
        if contacts:
            b.table(
                ["Role", "Name", "Email", "Organization", "Notes"],
                [1700, 2160, 2300, 1900, 1300],
                [[txt(p.get("role")), txt(p.get("name")), txt(p.get("email")), txt(p.get("organization")), txt(p.get("notes"))] for p in contacts],
            )
        else:
            b.empty_hint("No World Bank staff recorded yet.")
        b.spacer()

        b.heading("PIM Counterparts")
        if counterparts:
            b.table(
                ["Level", "Jurisdiction", "Name", "Title", "Email", "Organization"],
                [1180, 1480, 1900, 1600, 2100, 1100],
                [
                    [txt(p.get("level")), txt(p.get("jurisdiction")), txt(p.get("name")), txt(p.get("title")), txt(p.get("email")), txt(p.get("organization"))]
                    for p in counterparts
                ],
            )
        else:
            b.empty_hint("No counterparts recorded yet.")
        b.spacer()

        b.prose("Comment", c.get("comment"))

        b.heading("Tools applied")
        for f in C.TOOL_FIELDS:
            applied = c.get(f.key) is True or c.get(f.key) == 1
            p = b.para("", after=20)
            _run(p, "☑  " if applied else "☐  ", size=11, color=NAVY if applied else GRAY)
            _run(p, f.label, size=10.5, bold=applied, color=NAVY if applied else TEXT)
            _run(p, "  — applied" if applied else "  — not yet", size=8.5, italic=True, color=GRAY)
        b.spacer()

        b.heading("Assessments")
        b.narrative(c.get("assessments_note"))
        if assessments:
            b.table(
                ["Type", "Year", "Score", "Link", "Notes"],
                [1900, 1100, 1100, 2660, 2600],
                [[txt(r.get("type")), txt(r.get("year")), txt(r.get("score")), txt(r.get("link")), txt(r.get("notes"))] for r in assessments],
            )
        else:
            b.empty_hint("No assessment records yet.")
        b.spacer()

        b.heading("Operations & Pipeline")
        b.narrative(c.get("operations_note"))
        if projects:
            b.table(
                ["P-code", "Name", "Funder", "Year", "US$ M", "Status"],
                [1300, 2660, 1600, 800, 1100, 1900],
                [
                    [txt(r.get("code")), txt(r.get("name")), txt(r.get("funder")), txt(r.get("year")), txt(r.get("ida_commitment_musd")), txt(r.get("status"))]
                    for r in projects
                ],
            )
        else:
            b.empty_hint("No operations records yet.")
        b.spacer()

        b.heading("Recent activity")
        b.narrative(c.get("activity_note"))
        if events:
            b.table(
                ["Date", "Type", "Location", "Notes"],
                [1500, 2100, 2100, 3660],
                [[txt(r.get("date")), txt(r.get("type")), txt(r.get("location")), txt(r.get("notes"))] for r in events],
            )
        else:
            b.empty_hint("No activity records yet.")
        b.spacer()

        b.prose("References", c.get("reference_notes"))

    out = BytesIO()
    b.doc.save(out)
    return out.getvalue()
