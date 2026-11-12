"""
pages — one module per page of the site.

Every module exposes:
    PAGE        the value of the `?page=` query parameter that selects it
    PROTECTED   True when a staff session is required
    layout(params) -> Dash component tree (params = the parsed query string)
    register_callbacks(app)   optional — the page's own callbacks
"""
from __future__ import annotations

from types import ModuleType

from pages import (
    about,
    admin_country,
    admin_dashboard,
    admin_home,
    admin_review,
    country_detail,
    country_index,
    home,
    login,
    map_page,
    methodology,
    not_found,
    release_notes,
)

_MODULES: tuple[ModuleType, ...] = (
    home,
    about,
    methodology,
    map_page,
    country_index,
    country_detail,
    login,
    release_notes,
    admin_home,
    admin_review,
    admin_country,
    admin_dashboard,
    not_found,
)

# ?page=<name>  →  page module
PAGES: dict[str, ModuleType] = {m.PAGE: m for m in _MODULES}


def register_callbacks(app) -> None:
    """Register every page's own callbacks (called once from app.py)."""
    for module in _MODULES:
        register = getattr(module, "register_callbacks", None)
        if register is not None:
            register(app)
