"""
page_constants.py — content and presentation constants for the pages.

Everything a page *says* lives here (headings, paragraphs, nav labels, release
notes, banner messages, map settings …) so copy can be edited without touching
page code. System constants (database, tables, session, routing) live in
`constants.py`.
"""
from __future__ import annotations

import constants as C

# ─────────────────────────────────────────────────────────────────────────────
# Site-wide
# ─────────────────────────────────────────────────────────────────────────────
SITE_TITLE = "WBG Global PIIAG / PIM-PAM"
SITE_NAME = "PIM-PAM Country Engagement"
SITE_DESC = "Country engagement status across the World Bank Group's Global PIIAG / PIM-PAM program."
OG_IMAGE_FILE = "og-image.png"

HEADER_BRAND_TITLE = "Global PIIAG"
HEADER_BRAND_SUBTITLE = "PIM-PAM Engagement"
LOGO_FILE = "pim-pam-logo.png"
LOGO_ALT = "pim-pam.net"
LOGO_WIDTH, LOGO_HEIGHT = 219, 94

# Per-page browser tab titles (suffix matches the original site).
_SUFFIX = f" · {SITE_TITLE}"
PAGE_TITLES = {
    C.PAGE_HOME: SITE_TITLE,
    C.PAGE_ABOUT: "About" + _SUFFIX,
    C.PAGE_METHODOLOGY: "Methodology" + _SUFFIX,
    C.PAGE_MAP: SITE_TITLE,
    C.PAGE_COUNTRY: "Countries" + _SUFFIX,
    C.PAGE_COUNTRY_DETAIL: SITE_TITLE,
    C.PAGE_LOGIN: SITE_TITLE,
    C.PAGE_RELEASE_NOTES: "Release Notes" + _SUFFIX,
    C.PAGE_ADMIN: SITE_TITLE,
    C.PAGE_ADMIN_REVIEW: SITE_TITLE,
    C.PAGE_ADMIN_COUNTRY: SITE_TITLE,
    C.PAGE_ADMIN_DASHBOARD: SITE_TITLE,
    C.PAGE_NOT_FOUND: SITE_TITLE,
}

# (label, page, extra css classes) — order matters. `None` page = external.
NAV_LINKS = (
    ("About", C.PAGE_ABOUT),
    ("Methodology", C.PAGE_METHODOLOGY),
    ("Map", C.PAGE_MAP),
    ("Countries", C.PAGE_COUNTRY),
    ("Dashboard", C.PAGE_ADMIN_DASHBOARD),
    ("Release notes", C.PAGE_RELEASE_NOTES),   # hidden below the `lg` breakpoint on desktop
    ("Admin", C.PAGE_ADMIN),
)
NAV_CTA_LABEL = "Staff sign-in"

FOOTER_LEFT = "Maintained in the PIM-PAM engagement database · part of pim-pam.net."
FOOTER_RIGHT = "© World Bank Group · Global PIIAG / PIM-PAM"

PIM_PAM_NET_URL = "https://pim-pam.net"
PIM_PAM_AI_URL = "https://pim-pam.ai"

# Shared labels
LABEL_SIGN_OUT = "Sign out"
LABEL_NOT_RECORDED = "Not recorded yet"
DB_NOT_CONNECTED_ADMIN = (
    "the database is not connected (check the Databricks environment variables "
    "on Posit Connect or in your .env file)."
)

# ─────────────────────────────────────────────────────────────────────────────
# Home
# ─────────────────────────────────────────────────────────────────────────────
HOME_EYEBROW = "Global PIIAG / PIM-PAM Program"
HOME_TITLE = "PIM-PAM for Prosperity Development Impacts"
HOME_INTRO = (
    "An interactive view of country engagement under our Public Infrastructure Investment and "
    "Asset Governance (PIIAG) program — color-coded from initial engagement (Inception) through "
    "Adoption. Click any country on the map to see the level of engagement; staff can sign in for "
    "deeper detail on assessments, pipeline, and focal points."
)
HOME_CTA_PRIMARY = "Explore the map →"
HOME_CTA_SECONDARY = "Staff sign-in"
HOME_GLANCE_LABEL = "Engagement at a glance"
HOME_GLANCE_NOTE = "Live from the PIM-PAM engagement database."
HOME_CARDS = (
    {
        "title": "Public map",
        "body": "World-wide view of engagement levels across regions. No sign-in required.",
        "page": C.PAGE_MAP,
        "cta": "Open map",
    },
    {
        "title": "InfraGov 2.0 Diagnosis, pim-pam.net Digital Demonstrations",
        "body": (
            "Per-country InfraGov 2.0 and PEFA / PIMA / CCIA diagnostics — focal points and "
            "pipeline — alongside pim-pam.net digital tool demonstrations."
        ),
        "page": C.PAGE_LOGIN,
        "cta": "Staff sign-in",
    },
    {
        "title": "Methodology",
        "body": (
            "Our approach, the Awareness → Application → Adoption engagement model, and the FMUP "
            "results framework."
        ),
        "page": C.PAGE_METHODOLOGY,
        "cta": "Learn more",
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# Login
# ─────────────────────────────────────────────────────────────────────────────
LOGIN_TITLE = "Staff sign-in"
LOGIN_INTRO = (
    "Enter the shared password to view per-country detail. Ask your team lead if you don't have it."
)
LOGIN_PASSWORD_LABEL = "Password"
LOGIN_BUTTON = "Sign in"
LOGIN_ERROR = "Incorrect password. Try again."
LOGIN_NOT_CONFIGURED = "Server is not configured (missing APP_PASSWORD or APP_COOKIE_SECRET)."
LOGIN_FOOTNOTE = (
    "The password is a soft gate, not a security boundary. Don't put truly sensitive data here."
)

# ─────────────────────────────────────────────────────────────────────────────
# Country directory + country detail
# ─────────────────────────────────────────────────────────────────────────────
COUNTRY_INDEX_EYEBROW = "Country detail"
COUNTRY_INDEX_TITLE = "Countries"
COUNTRY_INDEX_INTRO = "Select a country to view its engagement detail. {n} countries across {r} regions."

DETAIL_BACK_LABEL = "← Back to map"
DETAIL_DOWNLOAD_BRIEF = "Download Word brief"
DETAIL_MATURITY_LABEL = "Maturity"
DETAIL_EDIT_LABEL = "Edit this country"
DETAIL_RESTRICTED_TITLE = "Staff detail is restricted"
DETAIL_RESTRICTED_BODY = (
    "Sign in to see contacts & mailing lists, operational records (assessments, operations, "
    "tools applied, events), and the latest internal updates."
)
DETAIL_RESTRICTED_CTA = "Staff sign-in for full detail →"
DETAIL_STAFF_DIVIDER = "Staff detail"
DETAIL_NO_DB = (
    "Database not connected. Set the DATABRICKS_* environment variables (see .env.sample) to "
    "populate this page from your Unity Catalog tables. The page falls back to the static "
    "engagement snapshot for now."
)
DETAIL_EMPTY_ASSESSMENTS = "No PEFA / PIMA / CCIA / InfraGov / GTMI records yet for this country."
DETAIL_EMPTY_OPERATIONS = "No World Bank operations recorded for this country yet."
DETAIL_EMPTY_EVENTS = "No events recorded yet."
DETAIL_PEOPLE_NONE = "None recorded yet."

# ─────────────────────────────────────────────────────────────────────────────
# Admin — country list
# ─────────────────────────────────────────────────────────────────────────────
ADMIN_EYEBROW = "Admin"
ADMIN_TITLE = "Country engagement"
ADMIN_INTRO = (
    "The Databricks Unity Catalog database is the source of truth. Changes here appear on the map "
    "and country pages immediately — no redeploy needed."
)
ADMIN_ERRORS = {
    "invalid": "Could not save: a required field was missing or the status was invalid.",
    "nodb": "Could not save: " + DB_NOT_CONNECTED_ADMIN,
    "exists": "Could not add: a country with that ISO3 code already exists. Use the table below to edit it.",
    "badiso": "Could not add: ISO3 must be a 3-letter country code (e.g. SRB).",
}
ADMIN_FALLBACK_BANNER = (
    "the database returned no rows. Saving and adding require a working Databricks connection "
    "(create and load the tables first — see migration/MIGRATION.md)."
)
ADMIN_EXCEL_TITLE = "Excel downloads"
ADMIN_EXCEL_INTRO = "Generate spreadsheet (.xlsx) extracts from the live database."
ADMIN_EXPORT_FOCAL = ("World Bank focal points", "Country · name · e-mail · last record update")
ADMIN_EXPORT_REGISTRY = ("WB managers & staff — master registry", "All roles · e-mail completeness flagged")
ADMIN_ADD_TITLE = "Add new country engagement"
ADMIN_ADD_INTRO = "Creates a new country record in the database."
ADMIN_UPDATE_TITLE = "Update existing country engagement"
ADMIN_UPDATE_INTRO = (
    "{n} countries. Each row saves on its own. Focal points are managed as structured contacts — "
    "use Edit to change them on the country’s detail page."
)
ADMIN_SEARCH_PLACEHOLDER = "Filter by country, ISO, or region…"

# ─────────────────────────────────────────────────────────────────────────────
# Admin — data review
# ─────────────────────────────────────────────────────────────────────────────
REVIEW_EYEBROW = "Data review"
REVIEW_TITLE = "Country Engagement and Results Tracker"
REVIEW_INTRO_PRE = "A read-only QA view of the live source-of-truth data. Sort, filter, scan for gaps, and export. "
REVIEW_INTRO_BOLD = "Click a country"
REVIEW_INTRO_POST = " to open its full record and edit every field."
REVIEW_SEARCH_PLACEHOLDER = "Search country, ISO, region, focal point…"

# ─────────────────────────────────────────────────────────────────────────────
# Admin — country editor
# ─────────────────────────────────────────────────────────────────────────────
EDITOR_BACK_LABEL = "← Back to review"
EDITOR_PUBLIC_LABEL = "Public page ↗"
EDITOR_NO_DB = "Database not connected — cannot load this record."
EDITOR_SAVED_MESSAGE = "Saved successfully."
EDITOR_NOT_FOUND = "Could not save: this country no longer exists."
EDITOR_ERRORS = {
    "invalid": "Could not save: country name, region, and a valid status are required.",
}
EDITOR_STALE_MESSAGE = (
    "This country was changed by someone else since you opened it. Reload the page and re-apply your edit."
)
EDITOR_SAVE_BAR_NOTE = "Saves every field in this form at once. (Records below save with their own buttons.)"
EDITOR_RECORDS_INTRO = (
    "Contacts, counterparts, assessments, operations, and events for {name}. These appear on the "
    "public country page. (Tools applied are set in the form above.)"
)
EDITOR_RECORDS_WARNING = (
    "Each record below saves with its own Save/Add button — the “Save changes” button above does "
    "not save these rows."
)
EDITOR_DELETE_CONFIRM = "Delete this record? This can’t be undone."
EDITOR_DELETED_TITLE = "Recently deleted"
EDITOR_DELETED_NOTE = "Deleted records can be restored here."

# ─────────────────────────────────────────────────────────────────────────────
# Admin — dashboard
# ─────────────────────────────────────────────────────────────────────────────
DASH_EYEBROW = "Dashboard"
DASH_TITLE = "Portfolio & results overview"
DASH_NO_DATA = "No country data available (database not connected)."

# ─────────────────────────────────────────────────────────────────────────────
# Map
# ─────────────────────────────────────────────────────────────────────────────
MAP_ARIA_LABEL = "Interactive map of country engagement levels"
MAP_LOADING = "Loading map…"
MAP_CONFIG = {
    "center": [22, 25],
    "zoom": 3,
    "minZoom": 2,
    "maxZoom": 7,
    # Keyless light-gray Esri basemap (note the {z}/{y}/{x} tile order).
    "tileUrl": "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
    "tileAttribution": (
        'Tiles &copy; <a href="https://www.esri.com/">Esri</a> &mdash; Esri, HERE, Garmin, '
        "&copy; OpenStreetMap contributors"
    ),
    "tileMaxZoom": 16,
    "geojsonFile": "countries.geojson",
    # CDN copies tried in order if the bundled file can't be loaded (same as the original site)
    "geojsonFallbackUrls": [
        "https://cdn.jsdelivr.net/gh/nvkelso/natural-earth-vector@master/geojson/ne_110m_admin_0_countries.geojson",
        "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson",
    ],
    "mapBackground": "#eef4f9",
    # Labels that need the small font / are hidden until zoomed in
    "smallLabelIso": ["XKX", "MNE", "MKD", "ALB", "BIH", "SRB", "ARM", "AZE", "GEO", "HRV", "MDA", "LUX", "RWA", "IRL", "LTU"],
    "clusterIso": ["XKX", "MNE", "MKD", "ALB", "BIH", "SRB", "HRV", "ARM", "AZE", "GEO", "MDA"],
    "clusterLabelMinZoom": 5,
    "clusterHintLatLng": [43.4, 20.2],
    "clusterHintHtml": "<span>Western Balkans &amp; Caucasus<br><small>zoom in for country names</small></span>",
    # Manual label anchors (geometry bounds-centre is awkward for these)
    "labelOverride": {
        "FRA": [46.6, 2.2], "USA": [39.5, -98.5], "RUS": [62.0, 95.0], "NOR": [62.0, 10.0],
        "NLD": [52.2, 5.3], "GRC": [39.0, 22.0], "BRA": [-10.3, -52.0], "ZAF": [-29.0, 25.0],
        "CAN": [56.0, -96.0], "IDN": [-2.5, 118.0], "PRT": [39.5, -8.0], "DNK": [56.0, 10.0],
        "CHL": [-35.0, -71.0], "HRV": [45.2, 16.0], "NZL": [-42.0, 173.0],
        "IRL": [53.3, -8.1], "LTU": [55.3, 23.9], "POL": [52.0, 19.5],
    },
    "popupLinkLabel": "View full detail →",
}

# ─────────────────────────────────────────────────────────────────────────────
# About
# ─────────────────────────────────────────────────────────────────────────────
ABOUT_EYEBROW = "About the program"
ABOUT_TITLE = "Closing the gap between diagnosis and delivery in public investment."
ABOUT_INTRO = (
    "Public investment and asset management are central to a country's ability to turn fiscal "
    "resources into tangible development outcomes. Yet across contexts, a persistent gap separates "
    "diagnostic insight from implementation — producing inefficiencies, underperforming assets, "
    "and lost value in public spending."
)
ABOUT_APPROACH_TITLE = "Our approach"
# Segments: plain strings or ("b", "bold text")
ABOUT_APPROACH_BODY = (
    "The World Bank's PIM-PAM program delivers a more impactful set of cross-country support to "
    "strengthen the policy and practice that drive development outcomes. It works across the "
    "tangible ",
    ("b", "people, process, and technology"),
    " dimensions of PIM-PAM, guided by three principles:",
)
ABOUT_PILLARS = (
    {
        "t": "Demand & ownership",
        "d": "Cultivate real demand and leadership for better PIM-PAM outcomes — even where politics often weighs against professionalism.",
    },
    {
        "t": "Digitalization & AI",
        "d": "Leverage digital tools and AI in smart, targeted ways to support and amplify genuine pockets of demand.",
    },
    {
        "t": "Sustained skills",
        "d": "Build lasting capacity across Ministries of Finance and PIM-PAM lead units, MDAs, sub-national governments, and SOEs.",
    },
)
ABOUT_DEMO_TITLE = "What this site demonstrates"
ABOUT_DEMO_BODY = (
    "This engagement site shows how the ",
    ("b", "InfraGov 2.0"),
    " modular assessment framework and the ",
    ("b", "pim-pam.net"),
    " digital tools and learning resources are being leveraged to achieve greater impact — "
    "addressing eight key PIM-PAM issues found across many client countries.",
)
ABOUT_ISSUES_TITLE = "Eight key PIM-PAM issues"
ABOUT_ISSUES_INTRO = "For each issue: what we measure, the gap we typically find, and the action we take."
ABOUT_ISSUES = (
    {
        "n": 1, "issue": "Awareness",
        "measure": "Diagnostics — PIMA, PEFA, PFRs, and the new InfraGov 2.0 assessments — give a rapid read on where things can be improved.",
        "gap": "These reports are a first step, but too often simply regurgitate the issues raised in earlier rounds.",
        "action": "Distinguish genuinely new issues from repeats. Rank policy and practice measures against expected outcomes for the next three budget years, with KPIs for the existing PIM pipeline and portfolio.",
    },
    {
        "n": 2, "issue": "Political demand",
        "measure": "Boost professional leadership demand in the face of political inertia and vested interests.",
        "gap": "Engagement languishes at the level of workshops and proceduralism, with no senior commitment to reform actions or measurable outcomes (e.g. the number and value of public investment flows affected).",
        "action": "Validate demand at senior levels and communicate it to the technical level, together with clear outcome measures.",
    },
    {
        "n": 3, "issue": "Limited PIM impact (materiality & proportionality)",
        "measure": "Quantify the functional impact of PIM policy and practice.",
        "gap": "No clear baseline for the “denominator” — total capital budgets and investments over the past three years, and project identifiers.",
        "action": "Measure the denominator against policy guidance: which projects should be subject to PIM, and how many actually are.",
    },
    {
        "n": 4, "issue": "Prioritizing PIM policy gaps",
        "measure": "Pinpoint which specific parts of the policy framework need changing or updating to address the issues.",
        "gap": "No clear inventory of the current policy profile, with many drafts still in progress.",
        "action": "Use pim-pam.ai for systematic review — benchmarking the de jure context against the status that available drafts would create if promulgated.",
    },
    {
        "n": 5, "issue": "Prioritizing practice gaps at the MoF / PIM-unit level",
        "measure": "Strengthen the pipeline and portfolio oversight data the Ministry of Finance currently provides.",
        "gap": "Proponents bypass the PIM process; capacity for project review is weak.",
        "action": "Alongside metrics, introduce AI-supported readiness assessments and practical digital tools that strengthen the support-and-challenge function.",
    },
    {
        "n": 6, "issue": "Prioritizing practice gaps at the proponent level (national, SNG, SOE)",
        "measure": "Strengthen pipeline and portfolio oversight data by sector.",
        "gap": "Proponents bypass the PIM process; capacity for project preparation is weak.",
        "action": "Alongside metrics, introduce end-user-centric digital and AI tools to support project preparation and strengthen the support-and-challenge function.",
    },
    {
        "n": 7, "issue": "Climate change addressed only in the abstract",
        "measure": "Sharpen the functional assessment of climate against policies and practices.",
        "gap": "Foundational PIM processes are lacking, with little real understanding of the climate adaptation or mitigation function and limited access to fit-for-purpose data.",
        "action": "Alongside metrics, introduce geospatial, end-user-centric digital and AI tools to support project preparation and strengthen the support-and-challenge function.",
    },
    {
        "n": 8, "issue": "PIM–PFM coherence",
        "measure": "The extent to which PIM reform design reflects the broader PFM system context.",
        "gap": "PIM reforms are frequently designed in isolation from the wider PFM environment, producing technically sound outputs but ineffective results given the lack of complementary upstream or downstream reforms or institutional capacity.",
        "action": "Before designing PIM interventions, identify binding PFM constraints and sequence reforms accordingly. Ensure PIM reforms speak to the broader PFM reform framework, and avoid technically correct reforms that outrun the institutional capacity to implement them.",
    },
)
ABOUT_KNOWLEDGE_EYEBROW = "Knowledge session"
ABOUT_KNOWLEDGE_TITLE = "Taking these approaches forward, together"
ABOUT_KNOWLEDGE_P1 = (
    "Against this backdrop, the ",
    ("b", "Financial Management Umbrella Program (FMUP)"),
    ", in collaboration with the ",
    ("b", "Government of Austria"),
    ", is convening a knowledge session to explore how this implementation gap can be closed "
    "through more practical, scalable approaches. The session focuses on the InfraGov 2.0 "
    "framework and associated tools — helping governments and practitioners strengthen "
    "decision-making, improve asset management, and raise the effectiveness of public "
    "investment systems.",
)
ABOUT_KNOWLEDGE_P2 = (
    "It brings together development partners and practitioners for an interactive discussion on "
    "applying these approaches across country contexts — with a focus on relevance, alignment "
    "with partner priorities, and opportunities to support uptake and scaling — and on "
    "identifying next steps for collaboration."
)
ABOUT_CTA_MAP = "Explore the engagement map →"
ABOUT_CTA_SITE = "Visit pim-pam.net"
ABOUT_COL_LABELS = ("Measure", "Gap", "Action")

# ─────────────────────────────────────────────────────────────────────────────
# Methodology
# ─────────────────────────────────────────────────────────────────────────────
METHOD_EYEBROW = "Methodology"
METHOD_TITLE = "Global PIM-PAM: Prosperity Through Better Investment"
METHOD_INTRO = (
    "PIM-PAM helps countries get more from every public dollar invested — strengthening the "
    "policies and practices behind public investment and asset management, powered by "
    "digitalization, AI, and stronger domestic skills. We work with “beacon” countries already "
    "demonstrating tangible innovations, and with those pushing to reach the frontier."
)
METHOD_SECTIONS = (
    {
        "h": "From memos to demos",
        "p": [
            "Reports, diagnostics, and assessments have long defined how this work gets done. PIM-PAM shifts the emphasis to functional online tools and learning-by-doing — so counterparts experience what good looks like, rather than just reading about it. This is how we break the bottlenecks that have stalled PIM-PAM reform for years.",
        ],
    },
    {
        "h": "Built for a changing World Bank",
        "p": [
            "The WBG's operating model is changing. Traditional, contractor-heavy country technical assistance is no longer sustainable — just as demand grows across sub-national governments and state-owned enterprises through deeper IFC collaboration. PIM-PAM meets this moment with scalable global solutions, building on the cross-country results chain already established by the Financial Management Umbrella Program (FMUP).",
        ],
    },
    {
        "h": "pim-pam.net: prototype, then adopt",
        "p": [
            "PIM-PAM IT projects are notorious for delays and disappointment, and AI raises the stakes further. Open-source prototypes and model resources let counterparts see success in digitalization and AI firsthand — cutting the time, cost, and risk of building real systems. Bank-executed activities can't implement government systems directly, but prototypes and learning-by-doing pave a faster, surer path to recipient-led adoption.",
        ],
    },
    {
        "h": "Adoption is the goal",
        "p": [
            "Success means more than a pilot. Adoption means counterparts have built digital PIM-PAM tools into their standard budget processes — annual and medium-term. Our engagement tracker follows each partnership from inception to awareness, application, and adoption, focusing effort where demonstrations are most likely to succeed. The aim: a critical mass of countries with real improvements, enabling faster replication and lasting impact.",
        ],
    },
    {
        "h": "Results depend on the wider system",
        "p": [
            "Better PIM-PAM can only do so much alone. What sits upstream and downstream matters — fiscal space, capital markets, and financing instruments determine whether investment can be mobilized; recurrent funding and institutional capacity determine whether infrastructure actually delivers services. Even a fiscal crisis can spur better portfolio management by forcing a long-overdue data rationalization.",
        ],
    },
    {
        "h": "Global and regional knowledge hubs",
        "p": [
            "Peer learning drives the agenda forward. In ECA, the Vienna Development Knowledge Center (VDKC) anchors knowledge exchange — deepening collaboration with EU-27 members, Switzerland, and the UK on PIM-PAM, applied AI, and end-user-centric public sector skills.",
        ],
    },
)
METHOD_PROGRESSION_TITLE = "The PIM-PAM country engagement progressions model"
METHOD_PROGRESSION_INTRO = (
    ("Each partnership progresses from ", ("b", "Inception"),
     " through three active stages — Awareness, Application, and Adoption — the same scale used "
     "to colour-code the ", ("link_page", "engagement map", C.PAGE_MAP),
     ". For each stage we set out the objective, the instruments we use, and the outcomes we expect.")
)
# (stage, background, foreground)
METHOD_STAGES = (
    ("Awareness", "#F6B26B", "#5a4500"),
    ("Application", "#3D85C6", "#ffffff"),
    ("Adoption", "#1F4E79", "#ffffff"),
)
# Each cell is a list of segments: plain strings or ("a", text, url)
METHOD_PROGRESSION = (
    {
        "row": "Objective",
        "cells": (
            ["Colleagues and counterparts appreciate the value of global solutions."],
            [("a", "pim-pam.net", PIM_PAM_NET_URL), " and ", ("a", "pim-pam.ai", PIM_PAM_AI_URL),
             " tools are applied to a specific country context."],
            ["Decision-support is mainstreamed as part of policies and practices, including digitalization and AI."],
        ),
    },
    {
        "row": "Instruments",
        "cells": (
            ["Regional units outreach and demonstrations."],
            ["ASA such as Public Finance Reviews (PFR), InfraGov 2.0, learning-by-doing, pim-pam.ai Country Policy Profiles, GPB CBA-CCS-LDT-PIA demos & sandboxes, and prototype applications."],
            ["Implementation of solutions as part of annual and medium-term decision-making (e.g. Georgia ePIM-CBA)."],
        ),
    },
    {
        "row": "Outcomes",
        "cells": (
            ["Options for application in ASA (e.g. PFRs) or future DPO / PfoR / IPF operations, and Partnerships / TF fundraising."],
            ["Decision-support insights for counterparts, Knowledge Exchange and Peer Learning offerings, and policy-practice reform prioritization and sequencing (including KPIs and data investments)."],
            ["Mainstreaming into policies and practices, including public-sector staffing, skills, and digitalization."],
        ),
    },
)
METHOD_FMUP_TITLE = "FMUP results framework for PIM-PAM"
METHOD_FMUP_INTRO = (
    "PIM-PAM contributes to the cross-country results chain of the Financial Management Umbrella "
    "Program (FMUP). Targets below are illustrative of the shared monitoring framework."
)
METHOD_FMUP_COLS = ("Baseline", "FY23", "FY24", "FY25", "FY26", "End Target")
METHOD_MODULE1_TITLE = (
    "Module 1 Outcome — Improved strategic allocation and value-for-money of public resources "
    "deployed to achieve policy objectives that benefit citizens of target countries"
)
METHOD_OUTCOME_ROWS = (
    {"label": "Outcome Indicator 1.1 — Number of governments that demonstrate strengthened institutional capacity to manage public budgeting more efficiently", "vals": [0, 0, 7, 14, 0, 30]},
    {"label": "Outcome Indicator 1.2 — Number of governments that demonstrate strengthened public investment or public asset management practices", "vals": [0, 0, 4, 8, 0, 10]},
)
METHOD_COMPONENT_TITLE = "Component 1.2 — Public Investment Management and Governance of Infrastructure"
METHOD_COMPONENT_ROWS = (
    {"label": "Indicator 1.2.1 — Number of countries with new or revised InfraGov, PIM, or PAM laws, regulations, procedures, practices, or systems", "vals": [0, 0, 4, 8, 1, 10], "kind": "indicator"},
    {"label": "Output — Number of knowledge or analytical products created, revised, or implemented to inform InfraGov, PIM, or PAM reforms", "vals": [0, 0, 7, 2, 0, 10], "kind": "output"},
    {"label": "Output — Number of governments that receive technical assistance to strengthen InfraGov, PIM, or PAM laws, regulations, procedures, practices, or systems", "vals": [0, 0, 2, 4, 0, 10], "kind": "output"},
)
METHOD_CTA_MAP = "Explore the engagement map →"
METHOD_CTA_ABOUT = "About the program"

# ─────────────────────────────────────────────────────────────────────────────
# Release notes (newest first)
# ─────────────────────────────────────────────────────────────────────────────
RELEASE_EYEBROW = "Release notes"
RELEASE_TITLE = "What's new"
RELEASE_INTRO_PRE = (
    "Updates to the PIM-PAM country engagement site, newest first. Methodology and the wider "
    "toolset are documented at "
)
RELEASE_NOTES = (
    {
        "version": "v1.7.0", "category": "Feature", "date": "June 2026",
        "title": "Portfolio dashboard, exports & country briefs",
        "items": (
            "New staff Portfolio & Results dashboard: engagement maturity across the portfolio, tools-applied coverage, data completeness, and a “gaps to fill” view — all at a glance.",
            "Download a formatted Word brief for any country, plus Excel exports of World Bank focal points and the full managers & staff registry.",
            "Country profiles now include a “Regional Management/Staff Unit Engagements” note (replacing the old ePIM-CBA count), shown alongside the engagement brief.",
            "Contacts: a World Bank team member’s e-mail now stays consistent across every country they support, and the staff registry is complete with e-mails on file.",
            "Reliability: save confirmations, recoverable deletes with one-click restore, input validation, and always-fresh data so edits save cleanly and nothing is lost.",
        ),
    },
    {
        "version": "v1.6.0", "category": "Feature", "date": "June 2026",
        "title": "Golden dataset: full country records, review tools & directory",
        "items": (
            "Each country record now carries the full engagement profile — summary, counterpart, language, WBG team, status notes, and contact e-mail fields for mailing lists — with the legacy tracking sheet retired in favour of the live database.",
            "New data-review dashboard for the team: completeness flags, per-country verification tracking, filters, and CSV export.",
            "Per-country admin editor covering every field, plus assessments, operations, ePIM-CBA projects, and events with inline editing.",
            "New Countries directory listing all engagements by region.",
            "Under the hood: security headers, a branded link-preview card, faster cached pages and map data.",
        ),
    },
    {
        "version": "v1.5.0", "category": "Feature", "date": "June 2026",
        "title": "Methodology page",
        "items": (
            "Added a Methodology page: the program narrative (“from memos to demos”), the Awareness → Application → Adoption engagement progressions model, and the FMUP results framework.",
            "The landing “Methodology” card and the main navigation now link to it.",
        ),
    },
    {
        "version": "v1.4.0", "category": "Improvement", "date": "June 2026",
        "title": "Eighth key issue and site improvements",
        "items": (
            "Added an eighth key PIM-PAM issue — PIM–PFM coherence — to the About page.",
            "Faster public pages (now cached) and a lighter, self-hosted map.",
            "Admin editor: search/filter, region grouping with jump links, and scroll-back to the row you just saved.",
            "Added a mobile navigation menu so every section is reachable on phones.",
        ),
    },
    {
        "version": "v1.3.0", "category": "Feature", "date": "June 2026",
        "title": "About & Release Notes",
        "items": (
            "Added an About page setting out the PIM-PAM program’s rationale, its people–process–technology approach, and the key PIM-PAM issues it addresses.",
            "Added this Release Notes page so partners can follow how the site evolves.",
        ),
    },
    {
        "version": "v1.2.0", "category": "Feature", "date": "June 2026",
        "title": "Live database & in-browser editing",
        "items": (
            "The Supabase database is now the single source of truth — the map, landing page, and country pages read from it live, so updates appear instantly without a redeploy.",
            "New password-gated Admin area to update existing country engagements (status, focal point, focus note) directly online.",
            "Admin can also add new country engagements to the database from the browser.",
        ),
    },
    {
        "version": "v1.1.0", "category": "Improvement", "date": "June 2026",
        "title": "PIM-PAM branding",
        "items": (
            "Applied the pim-pam.net brand across the site: logo, Fira Sans headings, Inter body text, and the official colour palette.",
        ),
    },
    {
        "version": "v1.0.0", "category": "Release", "date": "June 2026",
        "title": "Initial launch",
        "items": (
            "Public landing page and an interactive engagement map covering 43 countries.",
            "Countries are colour-coded across the engagement scale: Inception → Awareness → Application → Adoption.",
            "Password-gated per-country detail pages showing engagement status, focus, and focal points.",
            "Backed by a Supabase database, with a static fallback so the site always renders.",
        ),
    },
)
# Tailwind classes for the category tag
RELEASE_TAG_CLASSES = {
    "Release": "bg-brand-blue text-white",
    "Feature": "bg-brand-green/15 text-brand-green",
    "Improvement": "bg-brand-mid/15 text-brand-mid",
}

# ─────────────────────────────────────────────────────────────────────────────
# 404
# ─────────────────────────────────────────────────────────────────────────────
NOT_FOUND_TITLE = "Page not found"
NOT_FOUND_BODY = "We couldn't find the page you were looking for."
NOT_FOUND_CTA = "← Back to home"
