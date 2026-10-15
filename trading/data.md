# trading — Data Model

Entities, fields, storage decisions.

## Signals (SQLite — `strategy-analysis/signals.db`)

Primary store for all analyst output.

| Field | Type | Notes |
|-------|------|-------|
| id | INTEGER | auto PK |
| strategy | TEXT | e.g. `pivot_trend` |
| date | TEXT | YYYY-MM-DD |
| symbol | TEXT | e.g. `NSE:CDSL` |
| action | TEXT | `BUY` / `SELL` / `NOTHING` |
| entry | REAL | null for NOTHING |
| sl | REAL | stop loss, null for NOTHING |
| tp | REAL | take profit, null for NOTHING |
| rr | REAL | risk:reward ratio, null for NOTHING |
| reason | TEXT | one paragraph max |
| confidence | TEXT | `HIGH` / `MEDIUM` / `LOW` |
| run_at | TEXT | ISO 8601 datetime |

Unique constraint: `(strategy, date, symbol)` — one signal per strategy per stock per day. Re-running overwrites.

## Strategy folder (filesystem)

```
strategies/<name>/
  strategy.md       — strategy rules (human-authored)
  config.yaml       — tunable parameters
  meta.yaml         — instruments + Kite tokens
  positions.json    — open positions { "open_positions": {} }
  tradebook.csv     — trade log (append-only)
```

## Analysis output (filesystem — not versioned)

```
strategy-analysis/<strategy>/<YYYY-MM-DD>/<SYMBOL>/
  signal.json       — canonical signal (written by emit.py)
  analysis.md       — analyst reasoning
  candles.json      — raw candle data (optional)
  chart.png         — price chart (optional)
```

## tradebook.csv fields

| Field | Notes |
|-------|-------|
| date | ISO datetime |
| symbol | NSE symbol |
| direction | BUY / SELL |
| entry | entry price |
| sl | stop loss |
| tp | take profit |
| exit_price | actual exit |
| pnl | profit/loss in INR |
| rr_achieved | actual R:R |
| reason | exit reason |
| status | WIN / LOSS / STOPPED |

[← Back to index](trading.md)
