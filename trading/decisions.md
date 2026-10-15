# trading — Decisions

Choices made and why, alternatives ruled out.

## Architecture

- **Skills over agents for analyst** — analyst runs as a `/analyst` skill in the current jarvis session, not a sub-agent. Reason: Kite MCP auth is session-bound — sub-agents spawn fresh sessions and lose the auth token.

- **Two Kite MCP servers** — `mcp.kite.trade` for market data, local `kite-mcp-server` for order placement. Reason: hosted server has full market data access (uses Zerodha's own API key) but excludes order tools for safety; local server has order tools but requires your own Kite Connect subscription for market data.

- **Markdown for strategy rules** — strategy logic lives in `strategy.md`, read by the analyst at runtime. Reason: human-readable, easy to edit, no code changes needed to adjust strategy behaviour.

- **Protocol + shared emitter pattern** — all strategies call `analyst/emit.py` to output signals. Reason: enforces consistent schema across strategies at a single gate; analysis is flexible, output is standardised.

- **SQLite for signals** — `strategy-analysis/signals.db`. Reason: zero-infra, queryable, portable. Overkill would be Postgres for this scale.

- **strategy-analysis/ not versioned** — added to `.gitignore`. Reason: generated output, regenerated each run; storing it in git adds noise with no benefit.

## Market data

- **Historical data not available on personal Kite Connect key** — confirmed via testing. Personal API key on basic plan lacks historical data subscription. Workaround: use `mcp.kite.trade` for all market data in interactive sessions.

- **Browser login required once per session** — Kite Connect OAuth always requires browser consent. No headless workaround found without automating the browser (Playwright) or subscribing to a higher API tier. Accepted as a manual morning step.

## Kite MCP server

- **Local kite-mcp-server over hosted for orders** — hosted `mcp.kite.trade` explicitly excludes `place_order`, `modify_order`, `cancel_order`. Local binary built from `github.com/zerodha/kite-mcp-server` adds these back.

- **HTTP mode over stdio** — local server runs in HTTP mode on port 8080, connected via `mcp-remote`. Reason: stdio mode has a session ID bug (uses literal `"stdio"` string instead of UUID) that breaks the login flow.

[← Back to index](trading.md)
