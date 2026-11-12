"""
theme.py — design tokens shared by every page.

The visual design is carried over 1:1 from the original Next.js / Tailwind site:
  * brand palette (see design/tailwind.config.js — identical hex values)
  * the four-step engagement scale used by the map, pills and charts
  * the reusable Tailwind class strings for form controls

Components use Tailwind utility classes (compiled into assets/00-tailwind.css);
anything Tailwind can't express lives in assets/style.css.
"""
from __future__ import annotations

# ── PIM-PAM brand palette (per branding guidelines) ─────────────────────────
BRAND = {
    "blue": "#374291",    # Dark blue — headings, links, buttons
    "mid": "#3675b7",     # Mid blue — secondary headings, accents
    "navy": "#021420",    # Azure — darkest text, button hover
    "light": "#64cbd6",   # Light blue
    "purple": "#4345aa",
    "orange": "#f26b23",
    "green": "#37b37f",
    "line": "#c9d3ea",    # borders
    "tint": "#dee5f5",    # table header / light fill
}
INK = "#1f2d3d"

# ── Engagement scale (data encoding — kept stable across map, pills, charts) ─
STATUS_COLORS = {
    "Inception": "#FCE5A2",
    "Awareness": "#F6B26B",
    "Application": "#3D85C6",
    "Adoption": "#1F4E79",
}
STATUS_FALLBACK_COLOR = "#ccc"
INCEPTION_TEXT = "#5a4500"   # dark text used on the pale Inception colour

# Tailwind background classes for the scale swatches (home page)
STATUS_SWATCH_CLASSES = {
    "Inception": "bg-scale-inception",
    "Awareness": "bg-scale-awareness",
    "Application": "bg-scale-application",
    "Adoption": "bg-scale-adoption",
}


def status_color(status: str | None, fallback: str = STATUS_FALLBACK_COLOR) -> str:
    return STATUS_COLORS.get(status or "", fallback)


def status_text_color(status: str | None) -> str:
    return INCEPTION_TEXT if status == "Inception" else "white"


# ── Form control classes (identical to the original `inputCls` strings) ─────
FOCUS = "focus:border-brand-blue focus:outline-none focus:ring-1 focus:ring-brand-blue"
INPUT_CLS = f"rounded border border-gray-300 px-2 py-1.5 text-sm {FOCUS}"
INPUT_WIDE_CLS = f"w-full rounded border border-gray-300 px-3 py-2 text-sm {FOCUS}"
SEARCH_CLS = f"w-full max-w-sm rounded border border-gray-300 px-3 py-2 text-sm {FOCUS}"

# ── Buttons ─────────────────────────────────────────────────────────────────
BTN_PRIMARY = "rounded bg-brand-blue px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-navy"
BTN_OUTLINE = "rounded border border-brand-blue px-5 py-2.5 text-sm font-semibold text-brand-blue hover:bg-brand-blue/5"
BTN_SIGN_OUT = "rounded border border-gray-300 px-3 py-1 text-xs text-gray-600 hover:bg-gray-50"

# ── Banner tones ────────────────────────────────────────────────────────────
BANNER_TONES = {
    "ok": "border-brand-green/40 bg-brand-green/10 text-brand-green",
    "err": "border-red-300 bg-red-50 text-red-700",
    "warn": "border-amber-300 bg-amber-50 text-amber-900",
    "info": "border-brand-line bg-brand-tint/40 text-gray-700",
}
