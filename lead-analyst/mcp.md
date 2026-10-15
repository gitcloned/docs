# MCP

## Server

- **Name:** `lead-analyst`
- **Framework:** FastMCP (`mcp[cli]`)
- **Transport:** stdio (Claude Desktop connects via subprocess)
- **Entry point:** `server.py` → `main()` → `mcp.run()`

## Tools

| Tool | Parameters | Description |
|---|---|---|
| `load_index` | — | Returns one-liner index of all known tables, queries, and RCA patterns. Call at start of every investigation. |
| `get_context` | `name: str` | Full detail for a table, saved query, or RCA pattern. Includes gotchas, column notes, example SQL. |
| `run_query` | `sql: str`, `source: str = "clickhouse"`, `limit: int = 200` | Execute SQL. Returns formatted text table. |
| `list_sources` | — | List all configured data sources with descriptions. |
| `list_tables` | `source: str = "clickhouse"`, `database: str = ""` | List tables in a source, optionally filtered by database. |
| `describe_table` | `table: str`, `source: str = "clickhouse"` | Get schema (columns + types) for a table from the live source. |
| `save_query` | `name: str`, `sql: str`, `description: str`, `source: str`, `tags: list[str]` | Persist a useful SQL query to `knowledge/queries/`. |
| `add_table_note` | `table: str`, `note: str` | Append a gotcha or observation to a table's knowledge file. |

## Recommended call sequence

```
load_index()
  → get_context("table_name")
    → run_query("SELECT ...", source="clickhouse")
      → save_query("slug", sql, description)   # if query is worth keeping
      → add_table_note("table", "gotcha")      # if something tricky was found
```

## Claude Desktop config

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "lead-analyst": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/lead-anlayst", "lead-analyst"],
      "env": {
        "CLICKHOUSE_HOST": "...",
        "CLICKHOUSE_USER": "...",
        "CLICKHOUSE_PASSWORD": "..."
      }
    }
  }
}
```

The installer writes this automatically. Manual config is only needed for dev setups.

## Adding a new data source

1. Create `tools/sources/<name>.py` — implement `DataSource` base class (`query`, `list_tables`, `describe_table`)
2. Add to registry in `tools/query.py` — check env var, instantiate, add to `_SOURCES`
3. Add `knowledge/sources/<name>.yml` — document the source for Claude

[← Back to index](lead-anlayst.md)
