# Setup

## For users — Installing

### What you need

- **Claude Desktop** — download from claude.ai/download
- Your **ClickHouse username and password** — ask your team lead

### macOS

1. Extract the `.zip` file
2. Open the `lead-analyst-mac` folder
3. Double-click `install.command`
   - macOS security warning: right-click → **Open** → **Open**
4. Enter your ClickHouse username and password when prompted
5. Wait ~1 minute to complete
6. Quit and reopen Claude Desktop
7. Look for the hammer icon in the chat bar — done

### Windows

1. Right-click the `.zip` → **Extract All**
2. Open the `lead-analyst-windows` folder
3. Double-click `install.bat`
   - Windows Defender warning: **More info** → **Run anyway**
4. Enter credentials when prompted
5. Wait ~1 minute
6. Quit and reopen Claude Desktop
7. Look for the hammer icon — done

### First test

In Claude Desktop, type:
```
Load the index and tell me what tables and patterns you know about.
```
Claude should list available tables and RCA patterns. If it does, everything is working.

### Troubleshooting

| Problem | Fix |
|---|---|
| Hammer icon not showing | Quit Claude Desktop completely and reopen |
| Wrong credentials | Re-run the installer with correct username/password |
| macOS installer won't open | Right-click → Open → Open |
| Windows installer blocked | More info → Run anyway |

---

## For admins — Releasing

### What you need

- Repo access (Bitbucket)
- The ClickHouse host address

### Release steps

1. Pull latest: `git pull`
2. Build: `./build.sh <CLICKHOUSE_HOST>`
   - Example: `./build.sh clickhouse.lead.school`
3. Two files are produced in `dist/`:

| File | Send to |
|---|---|
| `lead-analyst-mac.zip` | macOS users |
| `lead-analyst-windows.zip` | Windows users |

4. Share the zip. Users run the installer.

> Updates overwrite the previous install. No migration needed.

---

## For developers — Local setup

1. Clone the repo
2. Install dependencies: `uv sync`
3. Create `.env` in the repo root:
   ```
   CLICKHOUSE_HOST=...
   CLICKHOUSE_USER=...
   CLICKHOUSE_PASSWORD=...
   # Optional:
   POSTGRES_HOST=...
   POSTGRES_USER=...
   POSTGRES_PASSWORD=...
   POSTGRES_DB=...
   ```
4. Run the server: `uv run lead-analyst`

To add to Claude Desktop manually, add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):
```json
{
  "mcpServers": {
    "lead-analyst": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/lead-anlayst", "lead-analyst"]
    }
  }
}
```

[← Back to index](lead-anlayst.md)
