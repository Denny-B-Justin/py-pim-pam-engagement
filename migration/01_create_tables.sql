-- ============================================================================
-- 01_create_tables.sql  -  Unity Catalog tables for the PIM-PAM engagement Dash app
--
-- Run this once in a Databricks SQL editor (or notebook) with a principal that may
-- CREATE TABLE in prd_mega.sgpbp163. The service principal the app uses afterwards needs only
-- USE CATALOG, USE SCHEMA, SELECT and MODIFY on these tables (grants at the end of this file).
--
-- Generated from constants.py (COUNTRY_COLUMNS / CHILD_TABLE_COLUMNS). If you change the
-- catalog / schema there (or via DATABRICKS_CATALOG / DATABRICKS_SCHEMA), change it here too.
--
-- Design notes
--   * STRING ids (UUID for new rows, the old numeric id as text for migrated rows) instead of
--     IDENTITY columns: identity columns disable concurrent writes on a Delta table.
--   * Deletion vectors are enabled so concurrent UPDATE / DELETE on different rows of the same
--     table do not conflict (two staff members editing at the same time).
--   * PRIMARY KEY constraints are informational in Unity Catalog (not enforced) - the app
--     enforces uniqueness itself (INSERT ... WHERE NOT EXISTS).
--   * Timestamps are written by the app in UTC.
-- ============================================================================

-- One row per country engagement (replaces Supabase public.countries). Source of truth for the map, country pages and admin editor.
CREATE TABLE IF NOT EXISTS `prd_mega`.`sgpbp163`.`pimpam_countries` (
  `iso3` STRING NOT NULL COMMENT 'ISO 3166-1 alpha-3 code, upper case (primary key of the countries table)',
  `name` STRING,
  `region` STRING,
  `cmu` STRING,
  `gov_pm` STRING,
  `ttl` STRING,
  `status` STRING COMMENT 'Engagement status: Inception | Awareness | Application | Adoption',
  `focus_note` STRING,
  `maturity_rating` STRING,
  `last_updated` DATE COMMENT 'Date of the last substantive update (drives the 180-day stale flag)',
  `created_at` TIMESTAMP,
  `updated_at` TIMESTAMP COMMENT 'Last save from the country editor - used for optimistic concurrency (do not hand-edit)',
  `summary` STRING,
  `status_note` STRING,
  `counterpart` STRING,
  `language` STRING,
  `epim_cba_count` INT,
  `comment` STRING,
  `wbg_team` STRING,
  `contacts` STRING,
  `wbg_email_primary` STRING,
  `wbg_email_secondary` STRING,
  `counterpart_email_primary` STRING,
  `counterpart_email_secondary` STRING,
  `regional_engagements` STRING,
  `key_pim_issues` STRING,
  `key_asa_ta` STRING,
  `key_operational_engagements` STRING,
  `success_2026` STRING,
  `success_2027` STRING,
  `resourcing_context` STRING,
  `tool_gpb_cba` BOOLEAN,
  `tool_gpb_ccs` BOOLEAN,
  `tool_gpb_pia` BOOLEAN,
  `tool_gpb_ldt` BOOLEAN,
  `tool_pimpam_ai_demo` BOOLEAN,
  `assessments_note` STRING,
  `operations_note` STRING,
  `epim_cba_note` STRING,
  `activity_note` STRING,
  `reference_notes` STRING COMMENT 'Free-text references (not called `references`: reserved word)',
  `reviewed_at` TIMESTAMP COMMENT 'When the record was last verified in the data-review tracker (NULL = not reviewed)',
  CONSTRAINT `pimpam_countries_pk` PRIMARY KEY (`iso3`)
)
USING DELTA
COMMENT 'One row per country engagement (replaces Supabase public.countries). Source of truth for the map, country pages and admin editor.'
TBLPROPERTIES (
  'delta.enableDeletionVectors' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);

-- World Bank focal points / managers / staff - one row per person per country (Supabase country_contacts).
CREATE TABLE IF NOT EXISTS `prd_mega`.`sgpbp163`.`pimpam_country_contacts` (
  `id` STRING NOT NULL COMMENT 'STRING key: a UUID for rows created by the app; the old numeric id (as text) for migrated rows',
  `iso3` STRING COMMENT 'Country this row belongs to (logical FK to pimpam_countries.iso3)',
  `role` STRING,
  `name` STRING,
  `email` STRING,
  `organization` STRING,
  `notes` STRING,
  `created_at` TIMESTAMP,
  CONSTRAINT `pimpam_country_contacts_pk` PRIMARY KEY (`id`)
)
USING DELTA
COMMENT 'World Bank focal points / managers / staff - one row per person per country (Supabase country_contacts).'
TBLPROPERTIES (
  'delta.enableDeletionVectors' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);

-- Government / client PIM counterparts - also the e-mail update list (Supabase pim_counterparts).
CREATE TABLE IF NOT EXISTS `prd_mega`.`sgpbp163`.`pimpam_counterparts` (
  `id` STRING NOT NULL COMMENT 'STRING key: a UUID for rows created by the app; the old numeric id (as text) for migrated rows',
  `iso3` STRING COMMENT 'Country this row belongs to (logical FK to pimpam_countries.iso3)',
  `level` STRING,
  `jurisdiction` STRING,
  `name` STRING,
  `title` STRING,
  `email` STRING,
  `organization` STRING,
  `notes` STRING,
  `created_at` TIMESTAMP,
  CONSTRAINT `pimpam_counterparts_pk` PRIMARY KEY (`id`)
)
USING DELTA
COMMENT 'Government / client PIM counterparts - also the e-mail update list (Supabase pim_counterparts).'
TBLPROPERTIES (
  'delta.enableDeletionVectors' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);

-- PEFA / PIMA / CCIA / InfraGov / GTMI assessments per country (Supabase assessments).
CREATE TABLE IF NOT EXISTS `prd_mega`.`sgpbp163`.`pimpam_assessments` (
  `id` STRING NOT NULL COMMENT 'STRING key: a UUID for rows created by the app; the old numeric id (as text) for migrated rows',
  `iso3` STRING COMMENT 'Country this row belongs to (logical FK to pimpam_countries.iso3)',
  `type` STRING,
  `year` INT,
  `score` DOUBLE,
  `link` STRING,
  `notes` STRING,
  `created_at` TIMESTAMP,
  CONSTRAINT `pimpam_assessments_pk` PRIMARY KEY (`id`)
)
USING DELTA
COMMENT 'PEFA / PIMA / CCIA / InfraGov / GTMI assessments per country (Supabase assessments).'
TBLPROPERTIES (
  'delta.enableDeletionVectors' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);

-- Operations & pipeline per country (Supabase projects).
CREATE TABLE IF NOT EXISTS `prd_mega`.`sgpbp163`.`pimpam_projects` (
  `id` STRING NOT NULL COMMENT 'STRING key: a UUID for rows created by the app; the old numeric id (as text) for migrated rows',
  `iso3` STRING COMMENT 'Country this row belongs to (logical FK to pimpam_countries.iso3)',
  `code` STRING,
  `name` STRING,
  `funder` STRING,
  `year` INT,
  `ida_commitment_musd` DOUBLE,
  `status` STRING,
  `link` STRING,
  `notes` STRING,
  `created_at` TIMESTAMP,
  CONSTRAINT `pimpam_projects_pk` PRIMARY KEY (`id`)
)
USING DELTA
COMMENT 'Operations & pipeline per country (Supabase projects).'
TBLPROPERTIES (
  'delta.enableDeletionVectors' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);

-- Recent activity: missions, BBLs, trainings (Supabase events).
CREATE TABLE IF NOT EXISTS `prd_mega`.`sgpbp163`.`pimpam_events` (
  `id` STRING NOT NULL COMMENT 'STRING key: a UUID for rows created by the app; the old numeric id (as text) for migrated rows',
  `iso3` STRING COMMENT 'Country this row belongs to (logical FK to pimpam_countries.iso3)',
  `date` DATE,
  `type` STRING,
  `location` STRING,
  `notes` STRING,
  `link` STRING,
  `created_at` TIMESTAMP,
  CONSTRAINT `pimpam_events_pk` PRIMARY KEY (`id`)
)
USING DELTA
COMMENT 'Recent activity: missions, BBLs, trainings (Supabase events).'
TBLPROPERTIES (
  'delta.enableDeletionVectors' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);

-- Undo log: snapshot (JSON text) of every deleted child record, restorable from the country editor (Supabase deleted_records).
CREATE TABLE IF NOT EXISTS `prd_mega`.`sgpbp163`.`pimpam_deleted_records` (
  `id` STRING NOT NULL COMMENT 'STRING key: a UUID for rows created by the app; the old numeric id (as text) for migrated rows',
  `table_name` STRING COMMENT 'Unity Catalog name of the table the row was deleted from (e.g. pimpam_events)',
  `iso3` STRING COMMENT 'Country this row belongs to (logical FK to pimpam_countries.iso3)',
  `payload` STRING COMMENT 'JSON text of the deleted row (Supabase: jsonb)',
  `deleted_at` TIMESTAMP,
  CONSTRAINT `pimpam_deleted_records_pk` PRIMARY KEY (`id`)
)
USING DELTA
COMMENT 'Undo log: snapshot (JSON text) of every deleted child record, restorable from the country editor (Supabase deleted_records).'
TBLPROPERTIES (
  'delta.enableDeletionVectors' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);

-- LEGACY archive of the retired ePIM-CBA projects table. Not read by the app.
CREATE TABLE IF NOT EXISTS `prd_mega`.`sgpbp163`.`pimpam_epim_cba_projects` (
  `id` STRING NOT NULL COMMENT 'STRING key: a UUID for rows created by the app; the old numeric id (as text) for migrated rows',
  `iso3` STRING COMMENT 'Country this row belongs to (logical FK to pimpam_countries.iso3)',
  `sector` STRING,
  `status` STRING,
  `year` INT,
  `notes` STRING,
  `created_at` TIMESTAMP,
  CONSTRAINT `pimpam_epim_cba_projects_pk` PRIMARY KEY (`id`)
)
USING DELTA
COMMENT 'LEGACY archive of the retired ePIM-CBA projects table. Not read by the app.'
TBLPROPERTIES (
  'delta.enableDeletionVectors' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);

-- Optional: enforce the four engagement statuses at write time. Uncomment after the data is
-- loaded and checked - a CHECK constraint rejects any write that violates it.
-- ALTER TABLE `prd_mega`.`sgpbp163`.`pimpam_countries` ADD CONSTRAINT `pimpam_status_valid`
--   CHECK (`status` IN ('Inception', 'Awareness', 'Application', 'Adoption'));

-- Grants for the app's service principal (replace <client-id> with the principal's application ID):
-- GRANT USE CATALOG ON CATALOG `prd_mega` TO `<client-id>`;
-- GRANT USE SCHEMA  ON SCHEMA  `prd_mega`.`sgpbp163` TO `<client-id>`;
-- GRANT SELECT, MODIFY ON SCHEMA `prd_mega`.`sgpbp163` TO `<client-id>`;
