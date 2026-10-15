# How It Works

## Request flow

```
User asks Claude a question
     |
     v
Claude calls load_index        — gets one-liner per table/query/RCA pattern
     |
     v
Claude calls get_context(name) — gets full table description, gotchas, example queries
     |
     v
Claude calls run_query(sql, source) — executes SQL against the chosen source
     |
     v
Result formatted as text table (max 200 rows, columns capped at 60 chars)
     |
     v
Claude interprets and answers
```

## Data source selection

- Source is passed as a parameter to `run_query`, `list_tables`, `describe_table`
- Default source: `clickhouse`
- Sources are lazy-initialised on first use — only configured sources appear
- `sheets` source is always available regardless of env vars

## CSV / Google Sheets source

```
sheets.yml manifest
     |
     v
CSVSource._register_tables()   — reads manifest, finds CSV files in data/sheets/
     |
     v
DuckDB in-memory view          — CREATE VIEW <name> AS SELECT * FROM read_csv(...)
     |
     v
DuckDB SQL query               — standard SQL, auto-LIMIT injected if missing
     |
     v
Returns list of dicts          — converted from pandas DataFrame
```

Sheets are static snapshots. To refresh: `python scripts/refresh_sheets.py`

## Knowledge base workflow

Claude is expected to follow this pattern at the start of every investigation:

1. `load_index()` — compact one-liner per known table, query, RCA pattern
2. `get_context(name)` — full detail for any table or pattern that looks relevant
3. `run_query(sql)` — execute the actual query
4. `save_query(name, sql, ...)` — persist useful queries for reuse
5. `add_table_note(table, note)` — record gotchas and observations

The knowledge base grows over time as Claude saves queries and notes. It lives in `knowledge/` and is committed to the repo.

## Query result formatting

- Results are printed as a fixed-width text table
- Column widths are computed from actual data, capped at 60 chars
- Row count shown at the top
- Limit defaults to 200; can be overridden per call

## Installer flow (macOS)

```
install.command runs
     |
     +-- Checks for uv (installs if missing via curl)
     +-- Copies repo files to ~/lead-analyst
     +-- Runs uv sync to install dependencies
     +-- Asks user for ClickHouse username + password (osascript dialog)
     +-- Writes .env file
     +-- Writes ~/Library/Application Support/Claude/claude_desktop_config.json
     +-- (Optional) Configures Teacher App integration
```

Windows installer (`install.ps1`) follows the same steps using PowerShell equivalents.

[← Back to index](lead-anlayst.md)
