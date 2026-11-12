# PIM-PAM engagement site — Python Dash edition

World Bank PIM-PAM country-engagement site, ported from the original Next.js / Supabase / Vercel
app to **Python 3.11.9 + Dash 3**, with data in **Azure Databricks Unity Catalog** and hosting on
**Posit Connect**.

Every page is served from the app root with a query string:

| URL | Page | Access |
|---|---|---|
| `/?page=home` (also `/`) | Home | public |
| `/?page=map` | Interactive engagement map | public |
| `/?page=country` | Country directory | public |
| `/?page=country-detail&iso=SRB` | One country (staff signed in see the restricted sections) | public / staff |
| `/?page=about`, `/?page=methodology`, `/?page=release-notes` | Content pages | public |
| `/?page=login` | Staff sign-in (shared password) | public |
| `/?page=admin` | Country list + add country, contacts | staff |
| `/?page=admin-country&iso=SRB` | Country editor (fields, contacts, assessments, projects, events, undo) | staff |
| `/?page=admin-review` | Data-review tracker (verify, filters, CSV export) | staff |
| `/?page=admin-dashboard` | Portfolio & completeness dashboard | staff |

An unknown `?page=` shows a "not found" page; a staff page opened without a session redirects to
`/?page=login&next=…` and returns there after sign-in.

## Quick start (local)

```bash
python3.11 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.sample .env                                         # then fill it in
python app.py                                               # http://localhost:8050/?page=home
```

Without the Databricks variables the public pages still work from a bundled read-only snapshot of
the country list; the staff pages (editing, review, dashboard) need the database.

## Configuration

All settings are environment variables — see [`.env.sample`](.env.sample) for the full, commented
list. They are read in one place, `constants.py`, together with the catalog / schema / table names
(`prd_mega` · `sgpbpi163` · `pimpam_*`). **No secret is stored in the code.** Locally they come from
`.env` (git-ignored); on Posit Connect from the content's **Vars** pane.

| Variable | Purpose |
|---|---|
| `DATABRICKS_SERVER_HOSTNAME`, `DATABRICKS_HTTP_PATH` | SQL warehouse connection details |
| `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET` | service principal (OAuth machine-to-machine) |
| `DATABRICKS_AZURE_TENANT_ID` | only for an Azure Entra ID application secret |
| `DATABRICKS_CATALOG`, `DATABRICKS_SCHEMA` | default `prd_mega` / `sgpbpi163` |
| `APP_PASSWORD` | shared staff password |
| `APP_COOKIE_SECRET` | signs the session cookie (≥ 32 random characters) |
| `SESSION_COOKIE_SECURE` | `true` when served over HTTPS (Connect) |
| `CACHE_TTL_SECONDS`, `SITE_URL`, `HOST`, `PORT`, `DEBUG`, `LOG_LEVEL` | optional |

## Data

Run [`migration/01_create_tables.sql`](migration/01_create_tables.sql) once, then load the Supabase
export with [`migration/load_csv_to_uc.py`](migration/load_csv_to_uc.py). The full guide — table
names, export steps, type mapping, the NoSQL question, verification queries and grants — is in
[`migration/MIGRATION.md`](migration/MIGRATION.md).

## Deploying to Posit Connect

```bash
pip install rsconnect-python
rsconnect add --server https://<your-connect-server> --api-key <your-api-key> --name connect

# only needed if you change the code or requirements.txt (manifest.json is already included)
rsconnect write-manifest dash --entrypoint app:app --overwrite \
    -x "design/**" -x "migration/**" -x "**/*.pyc" -x "**/__pycache__" -x ".env" .

rsconnect deploy dash --name connect --entrypoint app:app \
    -x "design/**" -x "migration/**" -x "**/*.pyc" -x "**/__pycache__" -x ".env" .
```

Then, on the content's settings page in Connect:

1. **Vars** — add every variable from `.env.sample` (mark the client secret, `APP_PASSWORD` and
   `APP_COOKIE_SECRET` as secrets). Set `SESSION_COOKIE_SECURE=true`.
2. **Access** — choose who may open the site. The public pages are meant to be visible to everyone who
   can reach the content; the staff pages are protected by the app's own password on top of that.
3. **Python** — the manifest pins 3.11.9 (the server must have a matching 3.11 installation).

Notes for Connect:

* Do **not** pass `url_base_pathname` to `dash.Dash(...)` — Connect sets the base path itself. All links
  are built with `dash.get_relative_path`, and routing uses only the `?page=` query string, so the app
  works the same under `/content/<guid>/` and under a vanity URL.
* The app stores no data on local disk. The read-only pages keep a small in-memory cache
  (`CACHE_TTL_SECONDS`, default 5 minutes) **per worker process**; after a staff edit the worker that
  handled it refreshes immediately and any other worker catches up when its cache expires.

## Project layout

```
app.py                  entry point + ?page= router (Dash app object `app`, WSGI `server`)
constants.py            system constants: Databricks settings, catalog/schema/table names, column
                        definitions, field metadata, session & cache settings, page names
page_constants.py       page content: headings, copy, navigation labels, release notes
.env.sample             every environment variable, no secrets
requirements.txt        pinned dependencies
.python-version         3.11.9
manifest.json           Posit Connect manifest (rsconnect-python)

pages/                  one module per page: home, about, methodology, release_notes, not_found,
                        country_index, country_detail, login, map_page,
                        admin_home, admin_country, admin_review, admin_dashboard
utils/                  design layer: theme (brand colours), layout (header/footer/shell),
                        components (cards, badges, sections), forms, routing, results (admin results)
services/               db (Databricks SQL), repository (queries + writes), auth, cache, validation,
                        exports (CSV/XLSX), brief_docx (Word brief), fallback_data (offline snapshot)

assets/                 served by Dash: style.css, 00-tailwind.css, logo + icons, fonts, Leaflet,
                        map.js / admin.js / site.js, country boundaries, Word template
design/                 optional Tailwind build setup (see below)
migration/              DDL, loader script and the migration guide
```

## Design

The visual design is a faithful port of the original site: the same Tailwind utility classes, brand
palette, Inter (body) / Fira Sans (headings) type, spacing, cards, badges, tables and map. Fonts and
Leaflet are self-hosted in `assets/`, so the only external request is the map's Esri base-map tiles.

* `assets/00-tailwind.css` — compiled Tailwind utilities (loaded first, hence the `00-`).
* `assets/style.css` — hand-written: font faces, map labels, and skins for the Dash dropdown and
  checkbox components so they match the original form controls.

If you add Tailwind classes to a Python file, rebuild the stylesheet (needs Node.js, one time):

```bash
cd design && npm install && npm run build      # npm run watch while developing
```

## Security notes

* Secrets only from the environment; nothing sensitive is committed (`.env` is git-ignored).
* Staff sign-in: shared password compared in constant time; HttpOnly, SameSite=Lax, signed session
  cookie (7 days, named per Connect content so apps on the same host do not collide).
* Every write goes through a callback that re-checks the session; SQL identifiers come from a
  whitelist in `constants.py` and every value is a bound parameter.
* Edits use optimistic concurrency: saving a country that someone else changed meanwhile is rejected
  with a "reload" message instead of overwriting their work.
* Like the original, the sign-in form has no rate limiting; keep the Connect access list restricted
  if the content is reachable from the internet.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Staff pages say the database is not configured | one of the four `DATABRICKS_*` connection variables is missing |
| "Could not connect to Databricks" | warehouse stopped / wrong HTTP path / principal lacks *Can use* on the warehouse |
| `PERMISSION_DENIED` / table not found | tables not created in the schema in use, or missing `SELECT, MODIFY` grants (see `01_create_tables.sql`) |
| Sign-in always fails | `APP_PASSWORD` or `APP_COOKIE_SECRET` not set (a warning is logged at start-up) |
| Sign-in works but you are bounced back | `SESSION_COOKIE_SECURE=true` while opening the app over plain HTTP |
| Styling looks unstyled after adding classes | rebuild `assets/00-tailwind.css` (see Design) |
