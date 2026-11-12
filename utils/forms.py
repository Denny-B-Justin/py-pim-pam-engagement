"""
forms.py — form-control builders.

Dash has no <input type=checkbox> / native <select> that report their value to
callbacks, so these helpers wrap the `dcc` equivalents and style them (through
assets/style.css) to look like the original native controls.
"""
from __future__ import annotations

from typing import Any, Iterable

from dash import dcc, html

from utils import theme


def labelled(text: str, control: Any) -> html.Label:
    """
    Give a control an accessible name. `dcc.Input` has no `aria-label` prop, so the name is a
    visually hidden <label> wrapped around it (`display: contents` keeps the layout unchanged).
    """
    return html.Label([html.Span(text, className="sr-only"), control], className="contents")


def text_input(
    id_: Any,
    value: Any = None,
    type_: str = "text",
    class_name: str = theme.INPUT_CLS,
    label: str | None = None,
    **kwargs: Any,
) -> Any:
    """
    Single-line input. type_ may be text | email | url | number | date | password | search.
    `label` is the accessible name (the original's aria-label).
    """
    if type_ == "number":
        kwargs.setdefault("step", "any")
        kwargs.setdefault("min", 0)
    control = dcc.Input(
        id=id_,
        type=type_,
        value="" if value is None else value,
        className=class_name,
        debounce=False,
        **kwargs,
    )
    return labelled(label, control) if label else control


def textarea(id_: Any, value: Any = None, rows: int = 3, class_name: str = theme.INPUT_WIDE_CLS, **kwargs: Any) -> dcc.Textarea:
    return dcc.Textarea(id=id_, value="" if value is None else value, rows=rows, className=class_name, **kwargs)


def select(
    id_: Any,
    options: Iterable[str],
    value: str | None = None,
    class_name: str = "",
    clearable: bool = False,
    placeholder: str = "",
    allow_empty: bool = False,
) -> dcc.Dropdown:
    """
    Drop-down styled like a native <select> (see `.pp-select` in style.css).

    allow_empty adds the "—" entry (value "") that the original record forms offered, so a
    role / level can be left blank.
    """
    opts = list(options)
    items = [{"label": o, "value": o} for o in opts]
    if allow_empty:
        items.insert(0, {"label": "—", "value": ""})
        current: str | None = value if value in opts else ""
    else:
        current = value if value in opts else None
    return dcc.Dropdown(
        id=id_,
        options=items,
        value=current,
        clearable=clearable,
        searchable=False,
        placeholder=placeholder,
        className=f"pp-select {class_name}".strip(),
    )


def checkbox(id_: Any, checked: bool, label: str = "", class_name: str = "") -> dcc.Checklist:
    """A single checkbox. The callback value is ['true'] when ticked and [] when not."""
    return dcc.Checklist(
        id=id_,
        options=[{"label": f" {label}" if label else "", "value": "true"}],
        value=["true"] if checked else [],
        className=f"pp-checkbox {class_name}".strip(),
        inputClassName="pp-checkbox-input",
        labelClassName="pp-checkbox-label",
    )


def field(label: str, child: Any, class_name: str = "", label_class: str | None = None) -> html.Label:
    """Label + control stacked vertically (the original `Field` helper)."""
    label_class = label_class or "text-[10px] font-semibold uppercase tracking-wider text-gray-500"
    return html.Label([html.Span(label, className=label_class), child], className=f"flex flex-col gap-1 {class_name}".strip())
