# System

## Architecture

```
Claude Desktop
     |
     | MCP (stdio)
     v
  server.py  (FastMCP)
     |
     +-- tools/query.py       — routes SQL to the right data source
     |       |
     |       +-- sources/clickhouse.py   — ClickHouse adapter
     |       +-- sources/postgres.py     — PostgreSQL adapter
     |       +-- sources/csv.py          — Google Sheets / CSV via DuckDB
     |
     +-- tools/knowledge.py   — knowledge base reads/writes
             |
             +-- knowledge/sources/      — YAML: source configs
             +-- knowledge/tables/       — MD: table descriptions + gotchas
             +-- knowledge/queries/      — YAML: saved SQL queries
             +-- knowledge/rca_patterns/ — MD: root cause analysis patterns
```

## Components

| Component | File | Role |
|---|---|---|
| MCP Server | `server.py` | Exposes all tools to Claude via FastMCP |
| Query router | `tools/query.py` | Lazy-initialises sources, routes `run_query`/`describe_table`/`list_tables` |
| Knowledge base | `tools/knowledge.py` | `load_index`, `get_context`, `save_query`, `add_table_note` |
| ClickHouse adapter | `tools/sources/clickhouse.py` | Connects via `clickhouse-connect` |
| Postgres adapter | `tools/sources/postgres.py` | Connects via `psycopg2` |
| CSV/Sheets adapter | `tools/sources/csv.py` | Reads CSVs via DuckDB in-memory, manifested in `knowledge/sources/sheets.yml` |
| Installer (macOS) | `installer/install.command` | Shell script — installs Python env, writes Claude Desktop config |
| Installer (Windows) | `installer/install.ps1` | PowerShell equivalent |
| Build script | `build.sh` | Produces `dist/lead-analyst-mac.zip` and `dist/lead-analyst-windows.zip` |

## Tech stack

| Layer | Technology |
|---|---|
| MCP framework | `mcp[cli]` (FastMCP) |
| Package manager | `uv` + `hatchling` |
| ClickHouse client | `clickhouse-connect` |
| Postgres client | `psycopg2-binary` |
| CSV querying | `duckdb` |
| Data processing | `pandas`, `numpy` |
| Config | `python-dotenv`, `pyyaml` |
| Runtime | Python 3.10+ |

## Key design decisions

- Sources are lazy-initialised — missing env vars don't crash startup
- `sheets` CSV source is always registered (no env var required)
- CSV files are registered as DuckDB views on first query, not at import
- Knowledge base is file-based YAML/MD — no database needed, easy to edit and commit
- Query results are capped at 200 rows by default; column widths capped at 60 chars for readability

[← Back to index](lead-anlayst.md)
