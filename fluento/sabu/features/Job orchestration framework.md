# Job Orchestration Framework

Like GitHub/Jenkins runners — install a sabu runner on any machine, map it to a project, and it picks up and executes jobs automatically.

---

## Original notes

> Like github runner, or jenkins runner - we also should be able to create sabu runners, which installs on any machine.
> Runner when installed: create system folder ~/.sabu/config, ~/.sabu/logs, ping to mark if live, register to cron.
> On UI, every project can be mapped to a list of available runners.
> Only a single runner should pick a task — consistency via database. Polls for tasks, pushes status back centrally.

---

## Decisions

| Concern | Decision | Rationale |
|---|---|---|
| Worker code distribution | Run directly from the cloned repo (`python runner/runner.py`) | Workers live alongside the runner; no separate package needed for a closed deployment |
| Python deps | Repo venv at `workers/.venv/` | Shared with workers; no separate venv needed |
| Distribution channel | Clone repo + activate venv + run `python runner/runner.py init` | `sabu-runner` PyPI package considered but deferred — not needed while teams use the same repo |
| Task claiming | MongoDB two-step upsert + `findOneAndUpdate` with `locked_until` TTL | Atomic, no race conditions; dedup via `job_hash` unique index |
| Live status | Server-Sent Events (SSE) via MongoDB change streams | No second data store needed (ruled out Firestore) |
| Runner auth | `runner_id:secret` plaintext bearer token | Simple; bcrypt hashing deferred to v2 |
| Runner identity | Plain string `_id` (not ObjectId) | Simplifies auth token format (`runner_id:secret` split on `:`) |
| Heartbeat threshold | 2 minutes without ping = offline | Balances responsiveness vs noise |
| Runner registration | Admin provisions via UI → one-time token → runner calls `/register` | Keeps secret off the wire at provision time |

---

## Architecture

### Runner lifecycle

```
cd /path/to/sales-booster/workers
source .venv/bin/activate
python runner/runner.py init --server <url> --token <token> --name <name>
  └─▶ collects: machine_id, OS, python_version, runner_version, config_path, log_path
  └─▶ POST /api/runners/register  (exchange provision token, send machine metadata)
      creates ~/.sabu/config.json  (server URL, runner_id, secret)
      creates ~/.sabu/machine_id   (cached OS UUID)

python runner/runner.py start
  └─▶ polling loop (every 30s):
        PUT /api/runners/:id/heartbeat
        GET /api/runners/:id/projects  (schedule + ingestion_configs)
        for each project:
          Priority 1 — Ingest (if schedule matches today/hour):
            compute job_hash(project_id + config_id + today)
            POST /api/runner-jobs/claim  →  if 200, run ingest worker
          Priority 2 — Analyse (if poll_interval_minutes elapsed):
            compute job_hash(project_id + session_id) per pending call
            POST /api/runner-jobs/claim  →  if 200, run analyse worker
```

### Task claiming (mutual exclusion)

Two-step atomic claim on `runner_jobs` collection:

```python
# Step 1: upsert — create the record if it doesn't exist
await col.update_one(
    {"job_hash": job_hash},
    {"$setOnInsert": {"_id": job_id, ..., "status": "pending", "created_at": now}},
    upsert=True,
)

# Step 2: atomic claim — only one runner wins
job = await col.find_one_and_update(
    {
        "job_hash": job_hash,
        "$or": [
            {"status": "pending"},
            {"status": "failed"},
            {"status": "processing", "locked_until": {"$lt": now}},  # crashed runner
        ],
    },
    {"$set": {
        "status": "processing",
        "claimed_by": runner_id,
        "locked_until": now + timedelta(minutes=10),
        "started_at": now,
    }},
    return_document=True,
)
# job is None → another runner claimed it first → skip (409 from API)
```

- `job_hash` unique index prevents duplicate job records at DB level
- `locked_until` TTL — if a runner crashes, the job auto-reclaims after 10 min
- `claimed_by` — runner identity stored for observability

### Live status via SSE

```
Runner  →  PUT /api/runner-jobs/:id/done or /failed   (MongoDB write)
Backend →  GET /api/projects/:id/jobs/stream           (SSE endpoint)
            watches MongoDB change stream on runner_jobs
            pushes events to connected frontend clients
Frontend → EventSource('/api/projects/:id/jobs/stream')
            updates jobs panel in real time
```

Requires MongoDB replica set for change streams. Falls back to 30-second heartbeat ping on standalone MongoDB.

### Multi-runner consistency

- A project maps to 1+ runners (via `assigned_runner_ids`)
- All runners poll the same `runner_jobs` collection
- Only one claims each job (atomic two-step claim + unique `job_hash` index)
- Runners are stateless — any runner assigned to a project can execute any job for it

---

## Job types

| Type | job_hash input | When to create |
|---|---|---|
| `ingest` | `sha256(project_id:config_id:date)` | When schedule says today is a run day and the hour matches |
| `analyse` | `sha256(project_id:session_id)` | When a call has `status=pending` and hasn't been analysed |

---

## Ingest behaviour & limits

- **Fetches the full day** — every ingest run pulls all CDR rows from Tubelight for that date (~1800–2500 rows)
- **No delta tracking** — does not check what was last run; deduplication is by `session_id` at insert time
- **Re-running the same date is safe** — second run inserts 0, skips all (idempotent)
- **No hard cap on ingestion** — bounded only by your filters (team_name, agent_names, min_talk_seconds); loose filters can pull 500+ calls in one shot
- **Cost control strategy** — use `agent_names` or `team_name` in the ingestion config to bound the call set per run
- **No automatic backfill** — if runner was offline for 3 days, those days are missed; run manually: `python ingest/ingest.py --project-id <id> --config-id <cfg> --date YYYY-MM-DD`

## Analysis behaviour & limits

- **Poll-driven** — runner checks for pending calls every N minutes (configured via `poll_interval_minutes`)
- **20 calls per cycle** — hardcoded cap: `get_pending_calls(limit=20)` — large backlogs drain over multiple cycles
- **One claim per call** — two runners can't analyse the same call; atomic claim via `job_hash` unique index
- **Backlog drains automatically** — runner keeps cycling until all pending calls are done

---

## Runner registration flow

```
Admin UI  →  POST /api/runners/provision   (Firebase auth)
             ← {runner_id, provision_token}

Admin gives token to operator → runs:
  python runner/runner.py init --server <url> --token <provision_token> --name <name>
  → POST /api/runners/register  (includes machine metadata: machine_id, OS, python_version, etc.)
  ← {runner_id, secret}   (provision_token cleared in DB)
  → saves to ~/.sabu/config.json
```

[← Back to index](../sales-booster.md)
