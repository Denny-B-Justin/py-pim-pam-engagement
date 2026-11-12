"""
constants.py — system-level constants for the PIM-PAM engagement Dash app.

Everything the *system* needs in order to run lives here: Databricks connection
settings, the Unity Catalog catalog / schema / table names, column definitions,
session + cache settings, validation limits and the list of page names.

Page *content* (headings, copy, nav labels, release notes, …) lives in
`page_constants.py` instead.

Secrets (client id / secret, passwords) are NEVER hard-coded here. They are read
from environment variables — a local `.env` file during development (copy
`.env.sample`) or the Variables pane of the content settings on Posit Connect.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"

# Loads ./.env for local development. On Posit Connect there is no .env file and
# the variables come from the content's Vars pane, so this is simply a no-op.
load_dotenv(BASE_DIR / ".env", override=False)


def _env(name: str, default: str = "") -> str:
    """Read an environment variable, stripping whitespace and wrapping quotes."""
    return os.getenv(name, default).strip().strip("'\"")


def _env_bool(name: str, default: bool = False) -> bool:
    raw = _env(name, "true" if default else "false").lower()
    return raw in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(_env(name, str(default)))
    except ValueError:
        return default


# ─────────────────────────────────────────────────────────────────────────────
# 1. Azure Databricks connection (OAuth machine-to-machine / service principal)
# ─────────────────────────────────────────────────────────────────────────────
# Values come from the environment (see .env.sample).
#   DATABRICKS_SERVER_HOSTNAME  e.g. adb-1234567890123456.7.azuredatabricks.net  (no https://)
#   DATABRICKS_HTTP_PATH        e.g. /sql/1.0/warehouses/abcdef1234567890         (SQL warehouse)
#   DATABRICKS_CLIENT_ID        service-principal application (client) ID
#   DATABRICKS_CLIENT_SECRET    service-principal OAuth secret
#   DATABRICKS_AZURE_TENANT_ID  OPTIONAL — only if the principal is a Microsoft Entra ID
#                               (Azure AD) service principal rather than a Databricks-managed one.
DATABRICKS_SERVER_HOSTNAME = (
    _env("DATABRICKS_SERVER_HOSTNAME").replace("https://", "").replace("http://", "").rstrip("/")
)
DATABRICKS_HTTP_PATH = _env("DATABRICKS_HTTP_PATH")
DATABRICKS_CLIENT_ID = _env("DATABRICKS_CLIENT_ID")
DATABRICKS_CLIENT_SECRET = _env("DATABRICKS_CLIENT_SECRET")
DATABRICKS_AZURE_TENANT_ID = _env("DATABRICKS_AZURE_TENANT_ID")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Unity Catalog location  (catalog.schema.table)
# ─────────────────────────────────────────────────────────────────────────────
CATALOG = _env("DATABRICKS_CATALOG", "prd_mega")
SCHEMA = _env("DATABRICKS_SCHEMA", "sgpbpi163")

# Ideal Unity Catalog table names. Create the tables with these exact names
# (migration/01_create_tables.sql does it for you) and load the Supabase CSV
# exports into them (see migration/MIGRATION.md).
TABLE_PREFIX = "pimpam_ai_engagement_prod_"

TBL_COUNTRIES = f"{TABLE_PREFIX}countries"            # one row per country engagement
TBL_CONTACTS = f"{TABLE_PREFIX}country_contacts"      # World Bank focal points / staff
TBL_COUNTERPARTS = f"{TABLE_PREFIX}pim_counterparts"  # government / client counterparts
TBL_ASSESSMENTS = f"{TABLE_PREFIX}assessments"        # PEFA / PIMA / CCIA / InfraGov / GTMI
TBL_PROJECTS = f"{TABLE_PREFIX}projects"              # operations & pipeline
TBL_EVENTS = f"{TABLE_PREFIX}events"                  # missions, BBLs, training, …
TBL_DELETED = f"{TABLE_PREFIX}deleted_records"        # undo log for deleted child records
TBL_EPIM_CBA = f"{TABLE_PREFIX}epim_cba_projects"     # LEGACY — not read by the app (archive only)

# Table the app actually uses at run time (TBL_EPIM_CBA is deliberately excluded).
APP_TABLES = (
    TBL_COUNTRIES,
    TBL_CONTACTS,
    TBL_COUNTERPARTS,
    TBL_ASSESSMENTS,
    TBL_PROJECTS,
    TBL_EVENTS,
    TBL_DELETED,
)

# Source (Supabase / Postgres) table  →  target (Unity Catalog) table.
SUPABASE_TO_UC_TABLES = {
    "countries": TBL_COUNTRIES,
    "country_contacts": TBL_CONTACTS,
    "pim_counterparts": TBL_COUNTERPARTS,
    "assessments": TBL_ASSESSMENTS,
    "projects": TBL_PROJECTS,
    "events": TBL_EVENTS,
    "deleted_records": TBL_DELETED,
    "epim_cba_projects": TBL_EPIM_CBA,  # optional / legacy
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. Column definitions (used by the repository layer and the migration loader)
# ─────────────────────────────────────────────────────────────────────────────
# NOTE: the child tables use a STRING `id` (a UUID for new rows; the old numeric
# id for migrated rows). This avoids Delta identity columns, which disable
# concurrent writes on a table.
COUNTRY_COLUMNS = {
    "iso3": "STRING", "name": "STRING", "region": "STRING", "cmu": "STRING",
    "gov_pm": "STRING", "ttl": "STRING", "status": "STRING", "focus_note": "STRING",
    "maturity_rating": "STRING", "last_updated": "DATE", "created_at": "TIMESTAMP",
    "updated_at": "TIMESTAMP", "summary": "STRING", "status_note": "STRING",
    "counterpart": "STRING", "language": "STRING", "epim_cba_count": "INT",
    "comment": "STRING", "wbg_team": "STRING", "contacts": "STRING",
    "wbg_email_primary": "STRING", "wbg_email_secondary": "STRING",
    "counterpart_email_primary": "STRING", "counterpart_email_secondary": "STRING",
    "regional_engagements": "STRING", "key_pim_issues": "STRING", "key_asa_ta": "STRING",
    "key_operational_engagements": "STRING", "success_2026": "STRING",
    "success_2027": "STRING", "resourcing_context": "STRING",
    "tool_gpb_cba": "BOOLEAN", "tool_gpb_ccs": "BOOLEAN", "tool_gpb_pia": "BOOLEAN",
    "tool_gpb_ldt": "BOOLEAN", "tool_pimpam_ai_demo": "BOOLEAN",
    "assessments_note": "STRING", "operations_note": "STRING", "epim_cba_note": "STRING",
    "activity_note": "STRING", "reference_notes": "STRING", "reviewed_at": "TIMESTAMP",
}

CHILD_TABLE_COLUMNS = {
    TBL_CONTACTS: {
        "id": "STRING", "iso3": "STRING", "role": "STRING", "name": "STRING",
        "email": "STRING", "organization": "STRING", "notes": "STRING", "created_at": "TIMESTAMP",
    },
    TBL_COUNTERPARTS: {
        "id": "STRING", "iso3": "STRING", "level": "STRING", "jurisdiction": "STRING",
        "name": "STRING", "title": "STRING", "email": "STRING", "organization": "STRING",
        "notes": "STRING", "created_at": "TIMESTAMP",
    },
    TBL_ASSESSMENTS: {
        "id": "STRING", "iso3": "STRING", "type": "STRING", "year": "INT", "score": "DOUBLE",
        "link": "STRING", "notes": "STRING", "created_at": "TIMESTAMP",
    },
    TBL_PROJECTS: {
        "id": "STRING", "iso3": "STRING", "code": "STRING", "name": "STRING", "funder": "STRING",
        "year": "INT", "ida_commitment_musd": "DOUBLE", "status": "STRING", "link": "STRING",
        "notes": "STRING", "created_at": "TIMESTAMP",
    },
    TBL_EVENTS: {
        "id": "STRING", "iso3": "STRING", "date": "DATE", "type": "STRING", "location": "STRING",
        "notes": "STRING", "link": "STRING", "created_at": "TIMESTAMP",
    },
    TBL_DELETED: {
        "id": "STRING", "table_name": "STRING", "iso3": "STRING", "payload": "STRING",
        "deleted_at": "TIMESTAMP",
    },
    TBL_EPIM_CBA: {
        "id": "STRING", "iso3": "STRING", "sector": "STRING", "status": "STRING", "year": "INT",
        "notes": "STRING", "created_at": "TIMESTAMP",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. Domain constants
# ─────────────────────────────────────────────────────────────────────────────
ENGAGEMENT_STATUSES = ("Inception", "Awareness", "Application", "Adoption")
STATUS_ORDER = {s: i for i, s in enumerate(ENGAGEMENT_STATUSES)}

FOCAL_ROLE = "Focal point (TTL)"
WB_ROLES = (FOCAL_ROLE, "Practice Manager (PM-Gov)", "WBG team", "Other contact")
ROLE_ORDER = {role: i for i, role in enumerate(WB_ROLES)}

STALE_DAYS = 180                 # a record not updated for this long is flagged "stale"
DELETED_RECORDS_LIMIT = 20       # "Recently deleted" entries shown per country
YEAR_MIN, YEAR_MAX = 1990, 2100  # accepted range for `year` fields

# E-mail auto-sync: a World Bank staff member's e-mail is propagated to every row
# with the same name — but never for placeholder / very short names.
SYNC_SENTINELS = frozenset({"tbd", "tba", "n/a", "na", "none", "-", "—", "?", "x"})
MIN_SYNC_NAME_LEN = 4


# ── Editable country fields (single source of truth for the admin form,
#    the update handler's whitelist and the Word brief) ──────────────────────
@dataclass(frozen=True)
class CountryField:
    key: str
    label: str
    type: str          # text | textarea | select | date | number | email | boolean
    group: str
    word_limit: int | None = None


GROUP_IDENTITY = "Identity"
GROUP_ENGAGEMENT = "Engagement"
GROUP_BRIEF = "Engagement brief (max 300 words)"
GROUP_TOOLS = "Tools applied"
GROUP_NARRATIVES = "Section narratives (max 300 words)"
GROUP_REFERENCES = "References"

FIELD_GROUPS = (GROUP_IDENTITY, GROUP_ENGAGEMENT, GROUP_BRIEF, GROUP_TOOLS, GROUP_NARRATIVES, GROUP_REFERENCES)

COUNTRY_FIELDS: tuple[CountryField, ...] = (
    # Identity
    CountryField("name", "Country name", "text", GROUP_IDENTITY),
    CountryField("region", "Region", "text", GROUP_IDENTITY),
    CountryField("status", "Engagement status", "select", GROUP_IDENTITY),
    # Engagement
    CountryField("focus_note", "Focus", "textarea", GROUP_ENGAGEMENT),
    CountryField("summary", "Summary", "textarea", GROUP_ENGAGEMENT),
    CountryField("status_note", "Status note (e.g. last e-mail)", "text", GROUP_ENGAGEMENT),
    CountryField("language", "Language", "text", GROUP_ENGAGEMENT),
    CountryField("regional_engagements", "Regional Management/Staff Unit Engagements", "textarea", GROUP_ENGAGEMENT, 250),
    CountryField("last_updated", "Last updated", "date", GROUP_ENGAGEMENT),
    CountryField("comment", "Comment", "textarea", GROUP_ENGAGEMENT),
    # Engagement brief (free-text strategic narrative, shown on the public country page)
    CountryField("key_pim_issues", "Key Country PIM Issues", "textarea", GROUP_BRIEF, 300),
    CountryField("key_asa_ta", "Key ASA-TA Engagements (Recent/Ongoing)", "textarea", GROUP_BRIEF, 300),
    CountryField("key_operational_engagements", "Key Operational Engagements (existing or expected operations)", "textarea", GROUP_BRIEF, 300),
    CountryField("success_2026", "What does success in 2026 mean?", "textarea", GROUP_BRIEF, 300),
    CountryField("success_2027", "What does success in 2027 mean?", "textarea", GROUP_BRIEF, 300),
    CountryField("resourcing_context", "Resourcing Context", "textarea", GROUP_BRIEF, 300),
    # Tools applied (checklist)
    CountryField("tool_gpb_cba", "GPB CBA", "boolean", GROUP_TOOLS),
    CountryField("tool_gpb_ccs", "GPB CCS", "boolean", GROUP_TOOLS),
    CountryField("tool_gpb_pia", "GPB PIA", "boolean", GROUP_TOOLS),
    CountryField("tool_gpb_ldt", "GPB LDT", "boolean", GROUP_TOOLS),
    CountryField("tool_pimpam_ai_demo", "pim-pam.ai Demo", "boolean", GROUP_TOOLS),
    # Section narratives
    CountryField("assessments_note", "Assessments — narrative", "textarea", GROUP_NARRATIVES, 300),
    CountryField("operations_note", "Operations & pipeline — narrative", "textarea", GROUP_NARRATIVES, 300),
    CountryField("activity_note", "Recent activity — narrative", "textarea", GROUP_NARRATIVES, 300),
    # References (staff-only, shown last). Column is `reference_notes` because
    # `references` is a reserved SQL keyword.
    CountryField("reference_notes", "References", "textarea", GROUP_REFERENCES),
)

COUNTRY_FIELD_KEYS = tuple(f.key for f in COUNTRY_FIELDS)
BRIEF_FIELDS = tuple(f for f in COUNTRY_FIELDS if f.group == GROUP_BRIEF)
TOOL_FIELDS = tuple(f for f in COUNTRY_FIELDS if f.group == GROUP_TOOLS)


# ── Child record tables shown in the "Records" section of the country editor ─
@dataclass(frozen=True)
class ChildField:
    key: str
    label: str
    type: str  # text | number | date | url | email | select
    required: bool = False
    placeholder: str | None = None
    options: tuple[str, ...] = ()


@dataclass(frozen=True)
class ChildTable:
    table: str                 # Unity Catalog table name
    label: str
    fields: tuple[ChildField, ...]
    hint: str | None = None


CHILD_TABLES: tuple[ChildTable, ...] = (
    ChildTable(
        table=TBL_CONTACTS,
        label="World Bank Managers & Staff",
        hint="Bank-side focal points, PM, and team — one row per person. Saving an e-mail syncs it to the same name in every country.",
        fields=(
            ChildField("role", "Role", "select", options=WB_ROLES),
            ChildField("name", "Name", "text", required=True),
            ChildField("email", "Email", "email"),
            ChildField("organization", "Organization / unit", "text"),
            ChildField("notes", "Notes", "text"),
        ),
    ),
    ChildTable(
        table=TBL_COUNTERPARTS,
        label="PIM Counterparts",
        hint="Government / client counterparts — also the e-mail update list",
        fields=(
            ChildField("level", "Level", "select", options=("National", "Sub-national")),
            ChildField("jurisdiction", "Jurisdiction (if sub-national)", "text", placeholder="e.g. Ceará"),
            ChildField("name", "Name", "text", required=True),
            ChildField("title", "Title / role", "text", placeholder="Director, PIM Unit"),
            ChildField("email", "Email", "email"),
            ChildField("organization", "Organization", "text", placeholder="Ministry of Finance"),
            ChildField("notes", "Notes", "text"),
        ),
    ),
    ChildTable(
        table=TBL_ASSESSMENTS,
        label="Assessments",
        hint="PEFA / PIMA / CCIA / InfraGov / GTMI",
        fields=(
            ChildField("type", "Type", "text", required=True, placeholder="PEFA"),
            ChildField("year", "Year", "number", placeholder="2025"),
            ChildField("score", "Score", "number"),
            ChildField("link", "Link", "url"),
            ChildField("notes", "Notes", "text"),
        ),
    ),
    ChildTable(
        table=TBL_PROJECTS,
        label="Operations & pipeline",
        fields=(
            ChildField("code", "P-code", "text", placeholder="P175655"),
            ChildField("name", "Name", "text", required=True),
            ChildField("funder", "Funder", "text", placeholder="WB / UK-FCDO / SECO …"),
            ChildField("year", "Year", "number"),
            ChildField("ida_commitment_musd", "Commitment (US$ M)", "number"),
            ChildField("status", "Status", "text", placeholder="Active / Pipeline / Closed"),
            ChildField("link", "Link", "url"),
            ChildField("notes", "Notes", "text"),
        ),
    ),
    ChildTable(
        table=TBL_EVENTS,
        label="Recent activity",
        fields=(
            ChildField("date", "Date", "date"),
            ChildField("type", "Type", "text", placeholder="Mission / BBL / training …"),
            ChildField("location", "Location", "text"),
            ChildField("notes", "Notes", "text"),
            ChildField("link", "Link", "url"),
        ),
    ),
)
CHILD_TABLE_NAMES = tuple(t.table for t in CHILD_TABLES)
CHILD_TABLE_BY_NAME = {t.table: t for t in CHILD_TABLES}

# ─────────────────────────────────────────────────────────────────────────────
# 5. Authentication & session (shared-password gate — no per-user identity)
# ─────────────────────────────────────────────────────────────────────────────
APP_PASSWORD = _env("APP_PASSWORD")
APP_COOKIE_SECRET = _env("APP_COOKIE_SECRET")      # signs the session cookie (>= 32 chars)
SESSION_COOKIE_NAME = "pp_session"
SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7        # 7 days
SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", False)  # set true behind HTTPS

# ─────────────────────────────────────────────────────────────────────────────
# 6. Caching, site & runtime
# ─────────────────────────────────────────────────────────────────────────────
# Public pages (/, map, country index) read through a short TTL cache — the same
# 5-minute window the original Next.js site used (ISR `revalidate = 300`).
# Admin pages and the country detail page always read fresh data.
CACHE_TTL_SECONDS = _env_int("CACHE_TTL_SECONDS", 300)

SITE_URL = _env("SITE_URL").rstrip("/")   # optional; used for link-preview (OpenGraph) tags
DEBUG = _env_bool("DEBUG", False)
HOST = _env("HOST", "0.0.0.0")
PORT = _env_int("PORT", 8050)
LOG_LEVEL = _env("LOG_LEVEL", "INFO").upper()

# ─────────────────────────────────────────────────────────────────────────────
# 7. Routing — every page is served from "/?page=<name>"
# ─────────────────────────────────────────────────────────────────────────────
PAGE_QUERY_PARAM = "page"
DEFAULT_PAGE = "home"

PAGE_HOME = "home"
PAGE_ABOUT = "about"
PAGE_METHODOLOGY = "methodology"
PAGE_MAP = "map"
PAGE_COUNTRY = "country"                  # country directory      (was /country)
PAGE_COUNTRY_DETAIL = "country-detail"    # one country, ?iso=SRB  (was /country/SRB)
PAGE_LOGIN = "login"
PAGE_RELEASE_NOTES = "release-notes"
PAGE_ADMIN = "admin"
PAGE_ADMIN_REVIEW = "admin-review"
PAGE_ADMIN_COUNTRY = "admin-country"      # country editor, ?iso=SRB (was /admin/country/SRB)
PAGE_ADMIN_DASHBOARD = "admin-dashboard"
PAGE_NOT_FOUND = "not-found"

# Where a successful login lands when no ?next= was supplied.
POST_LOGIN_QUERY = f"{PAGE_QUERY_PARAM}={PAGE_COUNTRY}"

# ─────────────────────────────────────────────────────────────────────────────
# 8. Export file names
# ─────────────────────────────────────────────────────────────────────────────
XLSX_FOCAL_POINTS_FILENAME = "WB_Focal_Points.xlsx"
XLSX_REGISTRY_FILENAME = "WB_Managers_and_Staff_registry.xlsx"
CSV_REVIEW_FILENAME = "pim-pam-engagement-review.csv"
DOCX_CREATOR = "PIM-PAM engagement"
