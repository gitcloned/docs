# Data Model — Sabu

MongoDB database: `sales_booster`. Five collections.

---

## Collection: `projects`

One document per project (workspace).

| Field | Type | Notes |
|---|---|---|
| `_id` | ObjectId | auto-generated |
| `name` | str | |
| `description` | str | |
| `rubrics` | list[Rubric] | see below |
| `ingestion_configs` | list[IngestionConfig] | see below |
| `success_stages` | list[str] | disposition values that count as success |
| `failure_stages` | list[str] | disposition values that count as failure |
| `pipeline_stages` | list[dict] \| null | funnel stage definitions for dashboard |
| `dashboard_yaml` | str \| null | custom widget layout; auto-generated if absent |
| `runner_schedule` | RunnerSchedule \| null | when to poll for ingest + analyse jobs |
| `assigned_runner_ids` | list[str] | runner IDs responsible for this project |
| `created_by` | str \| null | email of user who created the project |
| `created_at` | datetime | UTC |
| `updated_at` | datetime | UTC |

### Rubric (embedded in project.rubrics)

| Field | Type | Notes |
|---|---|---|
| `id` | str | stable identifier for this rubric |
| `name` | str | display name |
| `prompt` | str | question sent to the AI |
| `output_type` | str | `range` \| `boolean` \| `freetext` \| `enum` |
| `range` | dict \| null | `{"min": int, "max": int}` — only for `range` type |
| `options` | list[str] \| null | only for `enum` type |

### IngestionConfig (embedded in project.ingestion_configs)

| Field | Type | Notes |
|---|---|---|
| `id` | str | UUID, passed as `--config-id` to ingest worker |
| `name` | str | display name |
| `source` | str | telephony provider — `"tubelight"` (default); drives `IngestSource` factory |
| `filters` | dict | e.g. `{"team_name": "Sales,Support", "campaign": "Q3", "min_talk_seconds": 30, "agent_names": []}` |
| `enabled` | bool | default true |
| `last_run_at` | datetime \| null | set by ingest worker after each run |

Filter semantics:
- `team_name` and `campaign` accept comma-separated values — matched case-insensitively (e.g. `"Sales,Support"`)
- `min_talk_seconds` is **enforced at analysis time**, not at ingest — short calls are stored with `status: "skipped"` instead of being excluded at ingest
- `agent_names` is a list of exact agent name strings

### PipelineStage (embedded in project.pipeline_stages)

| Field | Type | Notes |
|---|---|---|
| `id` | str | |
| `name` | str | |
| `type` | str | `success` \| `failure` \| `neutral` |
| `color` | str | theme color hint |
| `items` | list[str] | disposition values (`final_tag`) that belong to this stage |

### RunnerSchedule (embedded in project.runner_schedule)

| Field | Type | Notes |
|---|---|---|
| `ingest.days` | list[str] | e.g. `["mon","tue","wed","thu","fri"]` |
| `ingest.hours` | list[int] | hours of day to run (24h), e.g. `[9, 18]` |
| `ingest.timezone` | str | IANA timezone, e.g. `"Asia/Calcutta"` |
| `analyse.poll_interval_minutes` | int | how often to check for pending analysis — `5\|10\|30\|60` |

---

## Collection: `calls`

One document per call recording.

| Field | Type | Notes |
|---|---|---|
| `_id` | str | session ID from telephony provider |
| `project_id` | str | string form of project ObjectId |
| `agent_name` | str | |
| `team_name` | str | |
| `campaign` | str | |
| `customer_number` | str | |
| `start_time` | datetime | |
| `end_time` | datetime | |
| `talk_time_seconds` | int | |
| `final_tag` | str | disposition/outcome label from telephony |
| `comment` | str | |
| `disconnected_by` | str | |
| `recording_url` | str | URL the analyse worker downloads from |
| `transcript` | list[TranscriptSegment] | empty at ingest; populated after analyse |
| `analysis` | dict[rubric_id → RubricResult] | empty at ingest; populated after analyse |
| `status` | str | `pending` \| `processing` \| `done` \| `failed` \| `skipped` |
| `error` | str \| null | set on failure |
| `created_at` | datetime | |
| `analysed_at` | datetime \| null | set when analyse worker finishes |

### TranscriptSegment (embedded in call.transcript)

| Field | Type | Notes |
|---|---|---|
| `speaker` | str | `AGENT` or `CUSTOMER` |
| `text` | str | |
| `start_sec` | float | |
| `end_sec` | float | |

### RubricResult (embedded in call.analysis, keyed by rubric id)

| Field | Type | Notes |
|---|---|---|
| `value` | any | type matches rubric `output_type` |
| `justification` | str | one-line reason from the AI grounded in transcript |

---

## Collection: `runners`

One document per registered runner machine.

| Field | Type | Notes |
|---|---|---|
| `_id` | str | `secrets.token_hex(12)` — plain string, not ObjectId |
| `name` | str | user-given name, e.g. `"office-server"` |
| `machine_name` | str | hostname |
| `machine_id` | str \| null | OS-level UUID — `ioreg` on macOS, `/etc/machine-id` on Linux, random UUID fallback; cached to `~/.sabu/machine_id` |
| `os` | str \| null | platform string, e.g. `"Darwin 24.5.0 (arm64)"` |
| `python_version` | str \| null | e.g. `"3.11.9"` |
| `runner_version` | str \| null | e.g. `"0.1.0"` |
| `config_path` | str \| null | path to `~/.sabu/config.json` on the runner machine |
| `log_path` | str \| null | path to `~/.sabu/logs/` on the runner machine |
| `secret` | str | plaintext secret; runner passes as `runner_id:secret` bearer token |
| `provision_token` | str | one-time registration token; cleared to `""` after use |
| `status` | str | `"provisioned"` → `"active"` |
| `assigned_project_ids` | list[str] | populated by admin; projects this runner serves |
| `visibility` | str | `"all"` \| `"me"` \| `"project"` — controls who can see this runner |
| `created_by` | str \| null | email of user who provisioned this runner |
| `last_heartbeat_at` | datetime \| null | UTC; updated on every heartbeat ping |
| `created_at` | datetime | UTC |

- **Online threshold:** `last_heartbeat_at` within last 2 minutes → runner is online
- **Visibility rules:** `"all"` — visible to all users; `"me"` — only creator (+ super-admin); `"project"` — users with access to any assigned project. Creator always sees their own runner regardless of visibility.
- **Migration:** on startup, existing runners without `visibility` are set to `"all"`; `created_by` set to `SUPER_ADMIN_EMAIL` if missing.

---

## Collection: `runner_jobs`

One document per job attempt. Unified collection for both ingest and analyse jobs.

| Field | Type | Notes |
|---|---|---|
| `_id` | str | `secrets.token_hex(12)` — plain string |
| `job_hash` | str | **unique index** — SHA-256 dedup key (see below) |
| `type` | str | `"ingest"` \| `"analyse"` |
| `project_id` | str | |
| `config_id` | str \| null | ingest only — ingestion config UUID |
| `date` | str \| null | ingest only — `"YYYY-MM-DD"` |
| `session_id` | str \| null | analyse only — call session_id |
| `status` | str | `"pending"` \| `"processing"` \| `"done"` \| `"failed"` |
| `claimed_by` | str \| null | runner `_id` that owns the job |
| `locked_until` | datetime \| null | crash-recovery TTL — job reclaims after 10 min if runner dies |
| `started_at` | datetime \| null | set on claim |
| `finished_at` | datetime \| null | set on done/failed |
| `error` | str \| null | truncated to 500 chars on failure |
| `created_at` | datetime | UTC |

### job_hash computation

- **Ingest:** `sha256(project_id + ":" + config_id + ":" + date)`
- **Analyse:** `sha256(project_id + ":" + session_id)`

Prevents duplicate jobs — two runners racing to claim the same work will only create one record.

### Indexes on runner_jobs

| Index | Type | Purpose |
|---|---|---|
| `{job_hash: 1}` | unique | enforce dedup at DB level |
| `{project_id: 1, status: 1, locked_until: 1}` | composite | claim queries |
| `{project_id: 1, type: 1, date: 1}` | composite | history listing |

---

## Collection: `users`

One document per user. `_id` is the user's email address.

| Field | Type | Notes |
|---|---|---|
| `_id` | str | email address |
| `first_name` | str | |
| `phone` | str \| null | normalized to `+91XXXXXXXXXX`; used for phone login lookup |
| `global_role` | str \| null | `"super-admin"` (env only) \| `"site-admin"` \| null |
| `project_roles` | dict | `{project_id: "project-admin" \| "project-user"}` |
| `created_by` | str \| null | email of site-admin who created this account |
| `created_at` | datetime \| null | UTC |
| `disabled` | bool | if true, user is blocked from access |

Notes:
- `super-admin` is not stored in the DB — it is determined solely by the `SUPER_ADMIN_EMAIL` environment variable
- Site-admins have `global_role: "site-admin"` but their project access is still controlled by `project_roles`
- Site-admins cannot promote users to `super-admin` — only the env var controls that
- `phone` is normalized at write time; lookup supports `+91XXXXXXXXXX`, `91XXXXXXXXXX`, 10-digit, and `0XXXXXXXXXX` formats

---

## Storage Notes

- Recordings are cached to disk at `recordings/YYYY-MM/<session-id>.mp3`
- Storage is abstracted via `workers/shared/storage.py` (`RecordingStorage` ABC) — S3 backend can be swapped in by setting `RECORDING_STORAGE=s3`
- Ingest is idempotent: uses `$setOnInsert` so re-runs don't overwrite existing records
- `runner_jobs` indexes are created automatically at server startup via `ensure_indexes()`

[← Back to index](sales-booster.md)
