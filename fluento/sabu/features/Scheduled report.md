# Scheduled Report

A daily email report, sent per-project to configured recipients, summarising the previous day's call activity and quality metrics.

---

## Purpose

- Give managers a zero-effort daily snapshot without logging in
- Highlight funnel performance across periods (day / week / month)
- Surface rubric quality scores per agent and pipeline stage
- Link directly to representative call recordings for coaching

---

## Architecture / flow

```
Runner auth (runner_id:secret)
  └─▶ GET /api/runners/{runner_id}/projects   ← project config + rubrics + pipeline_stages
  └─▶ GET /api/runner/projects/{id}/calls?date=YYYY-MM-DD  ← calls with analysis (per day)

workers/report/
  generate.py   ← fetch data → build report dict
  render.py     ← report dict → HTML string
  mailer.py     ← HTML + recipients → Gmail SMTP send
  cli.py        ← local CLI for testing
  handler.py    ← AWS Lambda entry point (scheduled via EventBridge)
```

No direct MongoDB access — all data fetched via REST API using runner auth (same as `runner.py start`).

---

## Report config (per project)

Stored under `report_config` on each project document.

| Field | Type | Default | Notes |
|---|---|---|---|
| `enabled` | bool | `false` | Whether to send this project's report |
| `recipients` | string[] | `[]` | Email addresses to send to |
| `send_time` | string | `"08:00"` | HH:MM IST — time to deliver the report |
| `rubric_ids` | string[] | `[]` | Which rubrics to include in grid (empty = all) |
| `meaningful_min_seconds` | int | `45` | Min talk time for a call to count as meaningful |
| `sample_calls_per_agent` | int | `3` | Max sample calls per agent in the calls table |

---

## Date windows

| Period | Range | When included |
|---|---|---|
| Yesterday | single day | always |
| This Week | Monday → yesterday | skipped if today is Monday |
| This Month | 1st → yesterday | skipped if today is in the first Mon–Sun week of the month |

---

## Report sections

### 1 — Funnel summary (all periods)
One compact table with a row per period (Yesterday / This Week / This Month):

| Period | Total calls | Meaningful | Converted | Conv% |
|---|---|---|---|---|

- **Meaningful** = calls ≥ `meaningful_min_seconds`
- **Converted** = calls whose `final_tag` maps to a pipeline stage with `type: success`

### 2 — Agent funnel (yesterday only)
Same columns as above, one row per agent.

### 3 — Rubric grid (yesterday, meaningful calls only)
Grid: agents as dark header rows, rubrics as sub-rows, pipeline stage groups as columns.

- Boolean rubrics → percentage
- Range rubrics → average score
- Columns: one per pipeline stage (Success / Failure / In Progress / etc.) + overall

### 4 — Sample calls (yesterday, meaningful only)
Table: Agent | Stage | Duration | Link

- Up to `sample_calls_per_agent` per agent
- Prioritises stage diversity: picks one success, one failure, one neutral/in-progress before repeating
- Links back to `https://sales-booster-8da8d.web.app/calls/{session_id}`

---

## Frontend — Daily Report settings tab

Project settings → **Daily Report** tab (edit mode only, rendered by `ReportConfig.tsx`):

- Enable/disable toggle
- Send time (HH:MM)
- Recipient list — add/remove email addresses
- Rubric checkboxes — select which rubrics appear in the grid
- Meaningful call threshold (seconds)
- Sample calls per agent (count)

Saved via `PATCH /api/projects/{project_id}/report-config` (project-admin only).

---

## CLI usage (testing)

```bash
# Preview HTML — writes /tmp/report_preview.html, opens browser, does NOT send
PYTHONPATH=. python workers/report/cli.py \
  --project-id <id> --as-of-date 2026-08-27 --dry-run --open

# Send to project's configured recipients
PYTHONPATH=. python workers/report/cli.py \
  --project-id <id> --env production

# Override recipients
PYTHONPATH=. python workers/report/cli.py \
  --project-id <id> --env production --to you@gmail.com
```

Loads runner config from `~/.sabu/config.json` (same as `runner.py start --env production`).

---

## Lambda / cron delivery

`workers/report/handler.py` is the AWS Lambda entry point.

- Triggered daily via EventBridge cron (8:00 IST = 2:30 UTC)
- Iterates all projects where `report_config.enabled = true`
- Skips projects with no recipients
- Event override: `{"project_id": "...", "as_of_date": "YYYY-MM-DD"}` for single-project or backdated sends

Env vars required on Lambda:
| Var | Description |
|---|---|
| `SABU_ENV` | Config env name (e.g. `production`) |
| `GMAIL_USER` | Sender Gmail address |
| `GMAIL_APP_PASSWORD` | 16-char App Password from Google Account → Security |

---

## Gmail sending

Uses `smtplib` with `smtp.gmail.com:587` + STARTTLS — no OAuth.
Requires a Gmail App Password (not the account password) with 2FA enabled on the sender account.

---

## Decisions

| Concern | Decision |
|---|---|
| Auth | Runner auth (`runner_id:secret`) — no Firebase, same as runner.py |
| Data source | REST API, not direct MongoDB — decoupled from DB schema |
| Date logic | First week = Mon–Sun containing the 1st; If today is in that window, skip month period |
| Delivery | Gmail SMTP + App Password — simple, no OAuth setup needed |
| Call links | `sales-booster-8da8d.web.app/calls/{session_id}` — portal direct link |
| Lambda vs cron | Lambda + EventBridge — serverless, no always-on process needed |
| Rubric selection | Optional in settings — empty list means include all project rubrics |

[← Back to index](../sales-booster.md)
