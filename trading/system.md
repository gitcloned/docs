# trading — System

Architecture, components, tech stack.

## Components

- **Analyst** — runs strategies, fetches market data, emits BUY/SELL/NOTHING signals
- **Strategist** — defines strategy rules in `strategy.md` (human-authored)
- **Trader** — acts on analyst signals (manual for now — no auto order placement)
- **BookKeeper** — records all signals and trades to SQLite + CSV

## How it runs

```
User → /analyst (jarvis session)
  → reads strategies/ folder
  → fetches live data via Kite MCP
  → runs strategy analysis per strategy.md rules
  → writes analysis to strategy-analysis/<strategy>/<date>/<symbol>/
  → calls analyst/emit.py → signal.json + signals.db
  → prints summary
```

## Tech stack

| Layer | Tool |
|-------|------|
| AI interface | Claude Code (jarvis) |
| Market data | Kite MCP — `mcp.kite.trade` |
| Order placement | Local kite-mcp-server — `localhost:8080` |
| Signal storage | SQLite — `strategy-analysis/signals.db` |
| Strategy logic | Markdown — `strategies/<name>/strategy.md` |
| Analyst skill | `.claude/skills/analyst/SKILL.md` |

## Key folders

```
strategies/
  <name>/
    strategy.md      — rules, read by analyst at runtime
    config.yaml      — tunable parameters
    meta.yaml        — instruments to trade
    positions.json   — open positions
    tradebook.csv    — trade log

analyst/
  protocol.md        — signal schema contract
  emit.py            — validates + writes DB + signal.json

strategy-analysis/   — generated, not versioned
  signals.db
  <strategy>/<date>/<symbol>/
    analysis.md
    signal.json
```

## MCP setup

Two servers in `.mcp.json`:
- `kite` → `mcp.kite.trade` — market data (historical, LTP, quotes)
- `kite-orders` → `localhost:8080` — order placement (start via `./start_kite.sh`)

Both require browser login once per session.

[← Back to index](trading.md)
