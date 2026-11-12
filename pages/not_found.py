"""not_found.py — unknown ?page= value."""
from __future__ import annotations

from typing import Any

from dash import html

import constants as C
import page_constants as P
from utils.routing import link

PAGE = C.PAGE_NOT_FOUND
PROTECTED = False


def layout(params: dict[str, str]) -> Any:
    return html.Div(
        [
            html.H1(P.NOT_FOUND_TITLE, className="text-3xl font-bold text-brand-blue"),
            html.P(P.NOT_FOUND_BODY, className="mt-3 text-gray-600"),
            link(P.NOT_FOUND_CTA, C.PAGE_HOME, "mt-6 inline-block text-sm font-semibold text-brand-blue hover:text-brand-navy"),
        ],
        className="mx-auto max-w-3xl px-6 py-20",
    )
