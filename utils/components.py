"""
components.py — reusable display components.

Each helper is a direct port of a small React helper from the original site
(`Prose`, `Narrative`, `Section`, `PeopleSection`, `ToolChecklist`, `Table`, …),
using the same Tailwind class strings so the rendered design is identical.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable, Sequence

from dash import html

import constants as C
import page_constants as P
from utils import theme
from utils.routing import external_link, link


# ── generic ─────────────────────────────────────────────────────────────────
def is_blank(value: Any) -> bool:
    return value is None or str(value).strip() in ("", "—")


def is_true(value: Any) -> bool:
    """Booleans come back as True/False from Databricks (1/0 from other engines)."""
    return value is True or value == 1 or str(value).lower() == "true"


def eyebrow(text: str, class_name: str = "") -> html.P:
    return html.P(text, className=f"text-xs font-semibold uppercase tracking-widest text-brand-mid {class_name}".strip())


def rich(segments: Any) -> list[Any]:
    """
    Turn a tuple of segments into Dash children. A segment is a plain string,
    ("b", text) for bold, ("a", text, url) for an external link or
    ("link_page", text, page) for an in-app link.
    """
    if isinstance(segments, str):
        return [segments]
    out: list[Any] = []
    for seg in segments:
        if isinstance(seg, str):
            out.append(seg)
        elif seg[0] == "b":
            out.append(html.Strong(seg[1]))
        elif seg[0] == "a":
            out.append(external_link(seg[1], seg[2], "text-brand-blue underline"))
        elif seg[0] == "link_page":
            out.append(link(seg[1], seg[2], "text-brand-blue underline"))
    return out


def banner(tone: str, children: Any, class_name: str = "") -> html.Div:
    return html.Div(children, className=f"mt-4 rounded-lg border px-4 py-3 text-sm {theme.BANNER_TONES[tone]} {class_name}".strip())


def sign_out_button() -> html.Button:
    return html.Button(P.LABEL_SIGN_OUT, id="pp-signout", n_clicks=0, className=theme.BTN_SIGN_OUT)


def status_pill(status: str | None, class_name: str = "rounded-full px-2 py-0.5 text-xs font-semibold") -> html.Span:
    return html.Span(
        status,
        className=class_name,
        style={"background": theme.status_color(status, "#ddd"), "color": theme.status_text_color(status)},
    )


def status_dot(status: str | None, class_name: str = "inline-block h-2.5 w-2.5 shrink-0 rounded-full") -> html.Span:
    return html.Span(className=class_name, style={"background": theme.status_color(status)}, title=status)


# ── country detail page helpers ─────────────────────────────────────────────
def not_set() -> html.Span:
    return html.Span(P.LABEL_NOT_RECORDED, className="italic text-gray-400")


def prose(label: str, value: Any) -> html.Section:
    """A labelled prose field, always rendered (placeholder when empty)."""
    return html.Section(
        [
            html.H2(label, className="text-xs font-bold uppercase tracking-widest text-brand-mid"),
            html.P(
                str(value) if not is_blank(value) else not_set(),
                className="mt-2 whitespace-pre-line text-base leading-relaxed text-gray-700",
            ),
        ],
        className="mt-6",
    )


def narrative(text: Any) -> html.P:
    return html.P(
        str(text) if not is_blank(text) else not_set(),
        className="mb-3 whitespace-pre-line text-sm leading-relaxed text-gray-700",
    )


def section(title: str, children: Any, section_id: str | None = None, class_name: str = "mt-10") -> html.Section:
    extra = {"id": section_id} if section_id else {}
    return html.Section(
        [
            html.H2(title, className="text-xs font-bold uppercase tracking-widest text-brand-mid"),
            html.Div(children, className="mt-3"),
        ],
        className=class_name,
        **extra,
    )


def empty_hint(hint: str) -> html.P:
    return html.P(hint, className="text-sm italic text-gray-500")


def detail(label: str, value: Any) -> html.Div:
    empty = value is None or value == "" or value == "—"
    return html.Div(
        [
            html.Dt(label, className="text-[10px] font-semibold uppercase tracking-wider text-gray-400"),
            html.Dd(
                html.Span("—", className="text-gray-400") if empty else str(value),
                className="mt-0.5 text-gray-700",
            ),
        ]
    )


def tool_checklist(row: dict[str, Any]) -> html.Ul:
    items = []
    for f in C.TOOL_FIELDS:
        applied = is_true(row.get(f.key))
        items.append(
            html.Li(
                [
                    html.Span(
                        "✓" if applied else "",
                        className=(
                            "flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-bold "
                            + ("bg-brand-blue text-white" if applied else "border border-gray-300 text-gray-300")
                        ),
                        **{"aria-hidden": "true"},
                    ),
                    html.Span(f.label, className="font-semibold text-brand-navy" if applied else "text-gray-500"),
                    html.Span("Applied" if applied else "Not yet", className="ml-auto text-[11px] uppercase tracking-wider text-gray-400"),
                ],
                className="flex items-center gap-2.5 rounded-lg border border-brand-line px-3 py-2 text-sm",
            )
        )
    return html.Ul(items, className="grid grid-cols-1 gap-2 sm:grid-cols-2")


def people_section(title: str, people: Sequence[dict[str, Any]], email_all_label: str = "Email all →") -> html.Section:
    emails = [p["email"] for p in people if p.get("email") and "@" in str(p["email"])]
    heading_children: list[Any] = [html.H2(title, className="text-xs font-bold uppercase tracking-widest text-brand-mid")]
    if emails:
        heading_children.append(
            html.A(email_all_label, href="mailto:" + ",".join(emails), className="text-xs font-semibold text-brand-blue hover:text-brand-navy")
        )
    body: Any
    if not people:
        body = html.P(P.DETAIL_PEOPLE_NONE, className="mt-2 text-sm italic text-gray-400")
    else:
        lis = []
        for p in people:
            line: list[Any] = [html.Span(p.get("name"), className="font-semibold text-brand-navy")]
            if p.get("level") or p.get("jurisdiction"):
                tag = f"{p.get('level') or 'Sub-national'} · {p['jurisdiction']}" if p.get("jurisdiction") else p.get("level")
                line.append(html.Span(tag, className="ml-2 rounded bg-brand-tint px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-brand-blue"))
            if p.get("role") or p.get("title"):
                line.append(html.Span(p.get("role") or p.get("title"), className="ml-2 text-xs text-gray-500"))
            if p.get("organization"):
                line.append(html.Span(f"· {p['organization']}", className="ml-2 text-xs text-gray-400"))
            li_children: list[Any] = [html.Span(line, className="text-gray-800")]
            if p.get("email") and "@" in str(p["email"]):
                li_children.append(html.A(p["email"], href=f"mailto:{p['email']}", className="mt-0.5 block text-xs text-brand-blue hover:underline"))
            lis.append(html.Li(li_children, className="px-4 py-2.5 text-sm"))
        body = html.Ul(lis, className="mt-3 divide-y divide-gray-100 rounded-lg border border-brand-line")
    return html.Section(
        [html.Div(heading_children, className="flex flex-wrap items-baseline gap-3"), body],
        className="mt-8",
    )


def simple_table(cols: Sequence[str], rows: Iterable[Sequence[Any]]) -> html.Div:
    """The plain grey data table used for assessments / operations / events."""
    return html.Div(
        html.Table(
            [
                html.Thead(
                    html.Tr([html.Th(c, className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-gray-600") for c in cols]),
                    className="bg-gray-50",
                ),
                html.Tbody(
                    [html.Tr([html.Td(cell, className="px-3 py-2 align-top text-gray-800") for cell in r]) for r in rows],
                    className="divide-y divide-gray-100 bg-white",
                ),
            ],
            className="min-w-full divide-y divide-gray-200 text-sm",
        ),
        className="overflow-x-auto rounded-lg border border-gray-200",
    )


def cell(value: Any) -> str:
    """
    Raw table-cell text, mirroring how the original printed record values:
    None → empty, 3.0 → "3" (JavaScript prints whole numbers without a decimal point),
    dates → ISO text.
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


# ── review / dashboard helpers ──────────────────────────────────────────────
def stat(label: str, value: Any, dot: str | None = None, warn: bool = False) -> html.Div:
    label_children: list[Any] = []
    if dot:
        label_children.append(html.Span(className="inline-block h-2.5 w-2.5 rounded-sm", style={"background": dot}))
    label_children.append(label)
    return html.Div(
        [
            html.Div(label_children, className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-gray-500"),
            html.Div(str(value), className="mt-1 text-2xl font-bold " + ("text-amber-700" if warn else "text-brand-blue")),
        ],
        className="rounded-lg border p-3 " + ("border-amber-300 bg-amber-50" if warn else "border-brand-line bg-white"),
    )


def badge(children: Any) -> html.Span:
    return html.Span(children, className="mr-1 inline-block rounded bg-amber-100 px-1.5 py-0.5 text-[11px] font-medium text-amber-800")


def soft_badge(children: Any) -> html.Span:
    return html.Span(children, className="mr-1 inline-block rounded bg-brand-tint px-1.5 py-0.5 text-[11px] font-medium text-brand-blue")


def flag(children: Any) -> html.Span:
    return html.Span(children, className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-800")


def soft_flag(children: Any) -> html.Span:
    return html.Span(children, className="rounded bg-brand-tint px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-brand-blue")
