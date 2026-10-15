# Data

## Data sources

| Source name | Type | When available |
|---|---|---|
| `clickhouse` | ClickHouse | `CLICKHOUSE_HOST` env var is set |
| `postgres` | PostgreSQL | `POSTGRES_HOST` env var is set |
| `sheets` | CSV via DuckDB | Always — no config needed |

## ClickHouse

Described in `knowledge/sources/clickhouse.yml`.

**Databases:**
- `teacherapp_android` — TeacherApp Android event tables. One row per user action. Most important table: `device_vitals` (~8M+ rows, fired periodically with full device state).
- `analytics` — S3-backed tables. May fail with AWS credential errors if keys expire.

**Key table pattern:** event tables have one row per event; `device_vitals` is different — it's a periodic snapshot of the full device state (storage, battery, app version, etc.).

## Google Sheets (CSV source)

Manifested in `knowledge/sources/sheets.yml`. CSVs live in `data/sheets/`. Refreshed via `scripts/refresh_sheets.py`.

| Table | Description | Size |
|---|---|---|
| `dispatches` | School hardware dispatch orders — warehouse, zone, asset, TAT data. Apr–Nov 2025. | ~66k rows |
| `propel_schools` | Propel school master list — deal ID, school name, state, product, status, size, agreement type | — |

CSVs are registered as DuckDB in-memory views on first query. Use `source="sheets"` when calling `run_query`.

## Knowledge base

File-based, lives in `knowledge/`. Grows over time via `save_query` and `add_table_note` tools.

| Folder | Format | Contents |
|---|---|---|
| `knowledge/sources/` | YAML | Source configs (connection details, notes) |
| `knowledge/tables/` | MD with YAML frontmatter | Table descriptions, column gotchas, tags |
| `knowledge/queries/` | YAML | Saved SQL queries (name, sql, description, source, tags) |
| `knowledge/rca_patterns/` | MD | Root cause analysis patterns for known issue types |

## Saved queries (as of last sync)

| Query slug | Source | Description |
|---|---|---|
| `storage_corruption_by_version` | clickhouse | — |
| `sd_card_health_per_school` | clickhouse | — |
| `stuck_non_5x_no_login_ay10_schools` | clickhouse | — |
| `upgrade_funnel_by_version_group` | clickhouse | — |
| `device_upgrade_event_timeline` | clickhouse | — |
| `ay10_upgrade_funnel` | clickhouse | — |
| `fluento_lab_completion_by_day` | clickhouse | — |
| `fluento_incomplete_students_with_reason` | clickhouse | — |
| `fluento_active_students_at_time` | clickhouse | — |
| `fluento_error_frequency_summary` | clickhouse | — |
| `sd_card_new_vs_old_corruption` | clickhouse | — |
| `sd_card_new_corruption_by_brand` | clickhouse | — |
| `sd_card_school_corruption_detail` | clickhouse | — |
| `fluento_setup_health_by_school` | clickhouse | — |
| `propel_school_ids` | sheets | — |
| `lab_completion_by_run_id` | clickhouse | — |

[← Back to index](lead-anlayst.md)
