"""
login.py — staff sign-in  (/?page=login[&next=<?page=…>]).  Port of app/login/page.tsx
and app/api/login/route.ts.

The shared-password check runs in a Dash callback; on success the Flask session
cookie is set (see services/auth.py) and the browser is sent to the validated
`next` page. No custom Flask route is needed.
"""
from __future__ import annotations

from typing import Any

from dash import Input, Output, State, dcc, html, no_update
from dash.exceptions import PreventUpdate

import constants as C
import page_constants as P
from services import auth
from utils.routing import safe_next_search

PAGE = C.PAGE_LOGIN
PROTECTED = False

_INPUT_CLS = (
    "mt-2 w-full rounded border border-gray-300 px-3 py-2 text-sm shadow-sm "
    "focus:border-brand-blue focus:outline-none focus:ring-1 focus:ring-brand-blue"
)


def layout(params: dict[str, str]) -> Any:
    return html.Div(
        [
            html.Div(
                [
                    html.H1(P.LOGIN_TITLE, className="text-2xl font-bold text-brand-blue"),
                    html.P(P.LOGIN_INTRO, className="mt-2 text-sm text-gray-600"),
                ]
            ),
            html.Div(
                [
                    html.Label(P.LOGIN_PASSWORD_LABEL, htmlFor="login-password", className="block text-xs font-semibold uppercase tracking-wider text-gray-600"),
                    dcc.Input(
                        id="login-password",
                        type="password",
                        value="",
                        name="password",
                        required=True,
                        autoFocus=True,
                        autoComplete="current-password",
                        debounce=False,
                        n_submit=0,
                        className=_INPUT_CLS,
                    ),
                    dcc.Store(id="login-next", data=params.get("next") or ""),
                    html.P(id="login-msg", className="mt-3 text-xs text-red-600"),
                    html.Button(
                        P.LOGIN_BUTTON,
                        id="login-submit",
                        n_clicks=0,
                        className="mt-4 w-full rounded bg-brand-blue px-4 py-2 text-sm font-semibold text-white hover:bg-brand-navy",
                    ),
                ],
                className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm",
            ),
            html.P(P.LOGIN_FOOTNOTE, className="text-center text-xs text-gray-500"),
        ],
        className="mx-auto flex max-w-md flex-col gap-6 px-6 py-16",
    )


def register_callbacks(app) -> None:
    @app.callback(
        Output("pp-url", "search", allow_duplicate=True),
        Output("login-msg", "children"),
        Input("login-submit", "n_clicks"),
        Input("login-password", "n_submit"),
        State("login-password", "value"),
        State("login-next", "data"),
        prevent_initial_call=True,
    )
    def _sign_in(n_clicks, n_submit, password, next_value):
        if not (n_clicks or n_submit) or not password:
            raise PreventUpdate
        result = auth.login(password)
        if result == auth.LOGIN_OK:
            return safe_next_search(next_value), ""
        if result == auth.LOGIN_NOT_CONFIGURED:
            return no_update, P.LOGIN_NOT_CONFIGURED
        return no_update, P.LOGIN_ERROR
