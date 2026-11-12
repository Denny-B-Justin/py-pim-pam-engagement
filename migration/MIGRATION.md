# Moving the data: Supabase → Unity Catalog (`prd_mega.sgpbp163`)

This guide takes the data from the old Next.js app's Supabase project into the Azure Databricks
Unity Catalog tables that the Dash app reads and writes. The data set is small (about 40 countries
and a few hundred child records), so a CSV / Excel export plus the loader script in this folder is
all that is needed.

> **Schema name.** The request text said `prd_mega.sgpbp163`; the generic instructions said
> `prd_mega.sgpbpi163`. The app defaults to **`sgpbp163`**. If yours is the other one, set
> `DATABRICKS_SCHEMA=sgpbpi163` in `.env` / the Connect Vars pane **and** change the schema in
> `01_create_tables.sql` (or run it with the right schema selected). Nothing else needs to change.

## 1. Is any of this NoSQL?

**No.** Supabase is hosted PostgreSQL (accessed through its REST layer), so every table is already
relational and maps one-to-one onto a Unity Catalog (Delta) table. The one NoSQL-flavoured thing is a
single column:

| Where | Supabase type | Unity Catalog type | What changes |
|---|---|---|---|
| `deleted_records.payload` | `jsonb` | `STRING` (holds JSON text) | The app writes it with `json.dumps` and reads it with `json.loads`. The loader checks that every payload parses as JSON. |

That column is a snapshot of a deleted row, used only by the "Recently deleted → Restore" feature, so
it is deliberately kept as an opaque JSON string rather than being split into columns.
(If you would rather store it as Databricks' `VARIANT` type, change the column type in the DDL and
use `parse_json(:payload)` when inserting / `to_json(payload)` when reading in
`services/repository.py`. It is a two-line change but not needed.)

The Google Sheet mentioned in the old repo (`1F7mMr238p1ZVR0VL2Rhk9zVXonqnzvI0K3IwOpF8tco`) was a
**retired, one-time backfill source**. Nothing reads it any more — do **not** migrate it.

> If you ever do meet a real document store (MongoDB, Firestore, Cosmos DB…), the recipe is:
> one collection → one table; scalar fields → typed columns; nested objects → flattened columns
> (`address.city` → `address_city`); arrays of objects → a child table with a foreign key to the
> parent; genuinely free-form blobs → a `STRING` (JSON) or `VARIANT` column.

## 2. Table names (what to call them in Unity Catalog)

All tables live in `prd_mega.sgpbp163` and carry the `pimpam_` prefix so they cannot collide with
anything else in the schema. The names are defined once, in `constants.py`
(`TBL_*` and `SUPABASE_TO_UC_TABLES`); the DDL is generated from the same definitions.

| Supabase table (old) | Unity Catalog table (new) | Key | Rows contain |
|---|---|---|---|
| `countries` | `pimpam_countries` | `iso3` | one row per country engagement (≈ 40) |
| `country_contacts` | `pimpam_country_contacts` | `id` | World Bank focal points / managers / staff |
| `pim_counterparts` | `pimpam_counterparts` | `id` | government / client counterparts (note: *not* `pimpam_pim_counterparts`) |
| `assessments` | `pimpam_assessments` | `id` | PEFA / PIMA / CCIA / InfraGov / GTMI results |
| `projects` | `pimpam_projects` | `id` | operations & pipeline |
| `events` | `pimpam_events` | `id` | missions, BBLs, trainings |
| `deleted_records` | `pimpam_deleted_records` | `id` | undo log (JSON text) |
| `epim_cba_projects` | `pimpam_epim_cba_projects` | `id` | **legacy archive only** — the app no longer reads it; migrate if you want to keep the history |

Column names are **identical** to Supabase's (including `reference_notes`, never `references`, which
is a reserved word). Only the table names and the types below differ.

## 3. Step by step

1. **Create the service principal** (once, by a workspace admin). In the Azure Databricks workspace:
   *Settings → Identity and access → Service principals → Add*, open it, *Secrets → Generate secret*.
   Keep the **Client ID** (application ID) and the **secret** — they go into `.env` locally and into
   the Vars pane on Posit Connect, never into source code. (If your organisation uses an Azure Entra ID
   application instead, also set `DATABRICKS_AZURE_TENANT_ID`.) Give the principal *Can use* on the SQL
   warehouse.
2. **Create the tables.** Open a SQL editor on the warehouse and run
   [`01_create_tables.sql`](01_create_tables.sql). It is idempotent (`CREATE TABLE IF NOT EXISTS`).
   Afterwards run the `GRANT` statements at the bottom (uncomment them and put in the client ID) so
   the service principal can `SELECT` and `MODIFY` the tables.
3. **Export from Supabase** — ask the app owner, or do it yourself in the Supabase dashboard
   (*Table Editor → pick a table → Export → CSV*), once per table in the table above. Name each file
   after the Supabase table (`countries.csv`, `country_contacts.csv`, …) and put them in one folder,
   e.g. `./export/`. An Excel workbook with one sheet per table works too (`--xlsx`).
   The export must contain the header row. Do not edit the files by hand.
4. **Check the export without touching Databricks:**
   ```bash
   python migration/load_csv_to_uc.py --dir ./export --dry-run
   ```
   Fix anything it reports (it names the file, row and column). Warnings about columns that are
   "NULL" mean the Supabase project never ran that optional migration — that is fine.
5. **Load it** (with the Databricks variables set in `.env`):
   ```bash
   python migration/load_csv_to_uc.py --dir ./export
   ```
   The script validates everything first and writes nothing if any value is bad, refuses to load into
   a table that already has rows (use `--truncate` to replace the contents), inserts in batches with
   bound parameters, and compares row counts at the end.
6. **Verify** with the queries in section 6, then start the app and open
   `/?page=admin-dashboard` — the totals should match what you saw on the old site.
7. **Cut over.** Deploy to Posit Connect (see the README), and keep the Supabase project read-only
   for a while as a fallback.

## 4. Type mapping

| PostgreSQL (Supabase) | Unity Catalog | Notes |
|---|---|---|
| `text` / `varchar` | `STRING` | empty strings in the export become `NULL` |
| `bigserial` / `bigint` id | `STRING` | old numbers are kept as text (`"12"`); rows created by the app get a UUID. No `IDENTITY` columns: they disable concurrent writes on a Delta table. |
| `integer` | `INT` | `year`, `epim_cba_count` |
| `numeric` / `double precision` | `DOUBLE` | `score`, `ida_commitment_musd` |
| `boolean` (`t` / `f` in CSV) | `BOOLEAN` | the five `tool_*` columns |
| `date` | `DATE` | `last_updated`, `events.date` |
| `timestamptz` | `TIMESTAMP` | stored in UTC; the app writes UTC |
| `jsonb` | `STRING` | see section 1 |

## 5. What does *not* carry over

* **Foreign keys / `ON DELETE CASCADE`** — Unity Catalog keys are informational. The app never deletes
  a country, and it deletes child rows itself, so nothing relies on cascades.
* **Row-level security** — access is now controlled by Unity Catalog grants and by the app's staff
  password. The service principal is the only identity that touches the tables.
* **Indexes** — Delta tables have none; at this size a full scan is instant.
* **The "missing columns" SQL banner** of the old admin page — the DDL creates every column up front.

## 6. Verification queries

```sql
-- row counts (compare with the Supabase table editor)
SELECT 'countries' AS t, COUNT(*) AS n FROM prd_mega.sgpbp163.pimpam_countries
UNION ALL SELECT 'country_contacts', COUNT(*) FROM prd_mega.sgpbp163.pimpam_country_contacts
UNION ALL SELECT 'counterparts',     COUNT(*) FROM prd_mega.sgpbp163.pimpam_counterparts
UNION ALL SELECT 'assessments',      COUNT(*) FROM prd_mega.sgpbp163.pimpam_assessments
UNION ALL SELECT 'projects',         COUNT(*) FROM prd_mega.sgpbp163.pimpam_projects
UNION ALL SELECT 'events',           COUNT(*) FROM prd_mega.sgpbp163.pimpam_events
UNION ALL SELECT 'deleted_records',  COUNT(*) FROM prd_mega.sgpbp163.pimpam_deleted_records;

-- the four engagement statuses (anything else will not colour correctly on the map)
SELECT status, COUNT(*) FROM prd_mega.sgpbp163.pimpam_countries GROUP BY status ORDER BY 2 DESC;

-- child rows whose country does not exist (should return 0 rows)
SELECT 'country_contacts' AS t, c.iso3 FROM prd_mega.sgpbp163.pimpam_country_contacts c
  LEFT ANTI JOIN prd_mega.sgpbp163.pimpam_countries k ON k.iso3 = c.iso3
UNION ALL SELECT 'events', e.iso3 FROM prd_mega.sgpbp163.pimpam_events e
  LEFT ANTI JOIN prd_mega.sgpbp163.pimpam_countries k ON k.iso3 = e.iso3;

-- undo log: only Unity Catalog table names, and every payload is JSON (both should be clean)
SELECT table_name, COUNT(*) FROM prd_mega.sgpbp163.pimpam_deleted_records GROUP BY table_name;
SELECT id FROM prd_mega.sgpbp163.pimpam_deleted_records WHERE get_json_object(payload, '$.iso3') IS NULL;
```

## 7. Doing it without the script (optional)

You can also upload each CSV through *Catalog → Create → Table* into a scratch table and then
`INSERT INTO … SELECT` with explicit `CAST`s. Two things the script does for you that you would then have
to do by hand: turn the numeric `id` columns into text, and rewrite `deleted_records.table_name` from the
Supabase name to the Unity Catalog name (`events` → `pimpam_events`, `pim_counterparts` →
`pimpam_counterparts`, …) — otherwise "Restore" in the country editor will not find the table.

## 8. Re-running / rolling back

* The loader is safe to re-run: without `--truncate` it refuses to touch a table that has rows.
* To start over: `python migration/load_csv_to_uc.py --dir ./export --truncate` (asks for confirmation;
  `--yes` skips the prompt in scripts). Delta keeps history, so a mistaken load can also be undone with
  `RESTORE TABLE … TO VERSION AS OF n`.
