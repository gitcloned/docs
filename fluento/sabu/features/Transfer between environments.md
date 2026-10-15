# Transfer between environments

Copy call records and analysis results from one environment to another — idempotent, safe to re-run.

---

## When to use

- Local runner has analysed calls that production hasn't ingested yet
- Production was down and local has the analysis results
- Backfilling a new environment from an existing one
- Spot-checking production data against local truth

---

## CLI

```
python runner/runner.py transfer \
  --src-env local \
  --dst-env production \
  --days 3
```

| Flag | Default | Description |
|---|---|---|
| `--src-env` | `local` | Source environment name (maps to `envs.<name>` in `~/.sabu/config.json`) |
| `--dst-env` | `production` | Destination environment name |
| `--days` | `2` | How many days back to transfer (today + N-1 days) |
| `--dst-project-id` | none | Skip name-based lookup; use this project ID on destination directly |

---

## How it works

Two passes per project per date:

```
For each project × date:

  Pass 1 — CDR sync (idempotent insert)
    src.GET /api/runner/projects/{id}/calls?date=YYYY-MM-DD
    dst.POST /api/runner/projects/{id}/calls         (bulk upsert, $setOnInsert)
    → new calls land as status=pending
    → existing session_ids are silently skipped

  Pass 2 — Analysis sync (never overwrites)
    Filter Pass 1 results: status=done AND analysis not empty
    dst.POST /api/runner/projects/{id}/calls/sync-analysis
    → only updates calls still at status=pending or failed on dst
    → calls already analysed on dst are left untouched
    Fallback: if sync-analysis returns 404, falls back to
              PUT /api/runner/calls/{id}/result  per call
```

---

## Project matching

The source runner must be assigned to the project (`assigned_runner_ids`).

The destination project is looked up by **name** by default:
```
GET /api/runner/projects/search?name=<exact-name>
```

If names differ between environments, pass `--dst-project-id <id>` to skip the lookup.

---

## Idempotency

| What | Guarantee |
|---|---|
| CDR records (session_ids) | `$setOnInsert` — duplicate inserts are safe; second run inserts 0 |
| Analysis results | Only written if destination call is `pending` or `failed` — never overwrites a completed analysis |
| Running transfer twice | Produces same result as running once |

---

## What transfers

- Call metadata: `session_id`, `agent_name`, `team_name`, `campaign`, `start_time`, `end_time`, `talk_time_seconds`, `final_tag`, `comment`, `customer_number`, `recording_url`, etc.
- Analysis fields (Pass 2): `transcript`, `analysis`, `rubrics_hash`, `analysed_at`

## What does NOT transfer

- Calls with `status != done` or empty `analysis` — CDR record lands but analysis is skipped; destination runner picks them up and analyses locally
- Calls already marked `done` on destination — left as-is

---

## Example output

```
Transferring 3 day(s): 2026-08-21, 2026-08-20, 2026-08-19
  local  →  production (https://api.example.com)
────────────────────────────────────────────────────────

  Fluento  (src:6a6a0f41… → dst:6a6a0f41…)
    2026-08-21  CDR: 82 fetched → 3 new, 79 already existed
    2026-08-21  analysis: 79 done → 0 synced, 79 skipped (already done on dst)
    2026-08-20  CDR: 94 fetched → 0 new, 94 already existed
    2026-08-20  analysis: 89 done → 0 synced, 89 skipped
────────────────────────────────────────────────────────

Done. 3 calls transferred to production.
Queued as pending — the production runner will analyse them.
```

---

## Auth requirements

- **Source runner** must be registered (`runner_id:secret`) and assigned to the project
- **Destination runner** only needs to be registered — no project assignment required for the transfer endpoints

[← Back to index](../sales-booster.md)
