# API — Sabu

Base URL: `http://localhost:14100` (dev).

**Auth — two token types:**
- Firebase users: `Authorization: Bearer <firebase-id-token>` — used for admin/UI endpoints
- Runners: `Authorization: Bearer <runner_id>:<secret>` — used for runner-to-server calls

Returns `401` if missing or invalid, `403` if the caller lacks the required role.

**RBAC roles (Firebase users):**

| Role | Scope | Privileges |
|---|---|---|
| `super-admin` | global | Set via `SUPER_ADMIN_EMAIL` env var — full access everywhere, implicit project-admin on all projects |
| `site-admin` | global | Can create projects; access to projects goes through `project_roles` |
| `project-admin` | per project | Full project control — edit settings, view calls + recordings, delete project |
| `project-user` | per project | Read-only — view calls, listen to recordings (no download) |

Role enforcement per endpoint is noted in the tables below.

---

## Projects

| Method | Path | Auth | Required role | Description |
|---|---|---|---|---|
| `GET` | `/api/projects` | Firebase | any | List accessible projects (filtered by project_roles) |
| `POST` | `/api/projects` | Firebase | site-admin+ | Create a project; creator auto-added as project-admin |
| `GET` | `/api/projects/{project_id}` | Firebase | project-user+ | Get a project by ID |
| `PUT` | `/api/projects/{project_id}` | Firebase | project-admin | Update a project (partial — only supplied fields change) |
| `DELETE` | `/api/projects/{project_id}` | Firebase | project-admin | Delete a project |
| `PUT` | `/api/projects/{project_id}/schedule` | Firebase | project-admin | Save runner schedule config + assigned runners |
| `PATCH` | `/api/projects/{project_id}/report-config` | Firebase | project-admin | Save daily report settings (recipients, rubrics, send time) |
| `GET` | `/api/projects/{project_id}/runner-jobs` | Firebase | project-user+ | Job history for a project |
| `GET` | `/api/projects/{project_id}/jobs/stream` | Firebase | project-user+ | SSE — live job updates via MongoDB change stream |

### POST /api/projects — body

```json
{
  "name": "string",
  "description": "string",
  "rubrics": [
    {
      "id": "string",
      "name": "string",
      "prompt": "string",
      "output_type": "range | boolean | freetext | enum",
      "range": {"min": 1, "max": 5},
      "options": ["option1", "option2"]
    }
  ],
  "ingestion_configs": [
    {
      "id": "uuid",
      "name": "string",
      "filters": {},
      "enabled": true
    }
  ],
  "success_stages": ["Deal Created"],
  "failure_stages": ["Explicit Disinterest"],
  "pipeline_stages": [
    {"id": "string", "name": "string", "type": "success|failure|neutral", "color": "string", "items": ["tag1"]}
  ]
}
```

Returns: `201` with the created project object (id as string, includes `created_at`, `updated_at`).

### PUT /api/projects/{project_id}/schedule — body

```json
{
  "runner_schedule": {
    "ingest": {"days": ["mon","fri"], "hours": [9, 18], "timezone": "Asia/Calcutta"},
    "analyse": {"poll_interval_minutes": 10}
  },
  "assigned_runner_ids": ["runner-abc"]
}
```

Returns: `{"ok": true}` or `404` if project not found.

### PATCH /api/projects/{project_id}/report-config — body

```json
{
  "enabled": true,
  "recipients": ["manager@example.com"],
  "send_time": "08:00",
  "rubric_ids": ["rubric-uuid-1", "rubric-uuid-2"],
  "meaningful_min_seconds": 45,
  "sample_calls_per_agent": 3
}
```

Returns: `{"ok": true}` or `404` if project not found.

### GET /api/projects/{project_id}/runner-jobs — query params

| Param | Type | Default | Notes |
|---|---|---|---|
| `limit` | int | 50 | max records to return |

Returns list of job objects sorted by `created_at` desc. See runner-jobs shape below.

### GET /api/projects/{project_id}/jobs/stream

SSE stream. Requires MongoDB replica set for change streams (falls back to heartbeat ping every 30s on standalone).

Event shape:
```json
{
  "job_id": "...",
  "type": "analyse",
  "status": "done",
  "session_id": "...",
  "claimed_by": "runner-abc",
  "finished_at": "2026-08-05T10:32:00"
}
```

---

## Calls

| Method | Path | Auth | Required role | Description |
|---|---|---|---|---|
| `GET` | `/api/projects/{project_id}/calls` | Firebase | project-user+ | List calls for a project (paginated) |
| `GET` | `/api/calls/{session_id}` | Firebase | project-user+ | Get full call detail (transcript + rubric scores) |

### GET /api/projects/{project_id}/calls — query params

| Param | Type | Default | Notes |
|---|---|---|---|
| `page` | int | 1 | ≥1 |
| `page_size` | int | 20 | 1–100 |
| `agent` | str | — | regex search on `agent_name` (case-insensitive) |
| `status` | str | — | `pending` \| `processing` \| `done` \| `failed` \| `skipped` |
| `date_from` | str | — | ISO date or datetime; filters `start_time ≥` |
| `date_to` | str | — | ISO date or datetime; bare date (10 chars) treated as end-of-day 23:59:59 |
| `team_name` | str | — | CSV of team names, case-insensitive (e.g. `"Sales,Support"`) |
| `campaign` | str | — | CSV of campaign names, case-insensitive |

`skipped` calls (talk time below project threshold) are excluded from the default result set. Pass `status=skipped` to see them explicitly.

Returns:
```json
{
  "items": [{ "session_id", "project_id", "agent_name", "team_name", "campaign",
              "start_time", "talk_time_seconds", "final_tag", "status" }],
  "total": 142,
  "page": 1,
  "page_size": 20
}
```

### GET /api/calls/{session_id}

Returns the full call document including `transcript` (list of `{speaker, text, start_sec, end_sec}`) and `analysis` (dict of rubric results).

---

## Dashboard

| Method | Path | Auth | Required role | Description |
|---|---|---|---|---|
| `GET` | `/api/projects/{project_id}/dashboard` | Firebase | project-user+ | Widget data for the dashboard |
| `GET` | `/api/projects/{project_id}/agents` | Firebase | project-user+ | Distinct agent names (for filter dropdown) |
| `GET` | `/api/projects/{project_id}/dispositions` | Firebase | project-user+ | Distinct final_tag values (for project settings) |
| `PUT` | `/api/projects/{project_id}/dashboard/yaml` | Firebase | project-admin | Save custom dashboard YAML config |

### GET /api/projects/{project_id}/dashboard — query params

| Param | Type | Default | Notes |
|---|---|---|---|
| `date_from` | str | 30 days ago | ISO date or datetime |
| `date_to` | str | now | ISO date or datetime; bare date treated as 23:59:59 end-of-day |
| `agent` | str | — | exact match on `agent_name` |
| `status` | str | — | filter by call status |
| `rubric_id` | str | — | filter by rubric answer |
| `rubric_value` | str | — | value for the rubric filter (coerced to bool/int/float/str) |
| `team_name` | str | — | CSV of team names, case-insensitive |
| `campaign` | str | — | CSV of campaign names, case-insensitive |

`skipped` calls are always excluded from dashboard counts and rubric aggregations regardless of other filters.

Returns:
```json
{
  "project_id": "...",
  "date_from": "2026-07-06",
  "date_to": "2026-08-05",
  "summary": {
    "total_calls": 142,
    "unique_agents": 8,
    "avg_talk_time_seconds": 183,
    "conversion_rate": 0.12,
    "succeeded_count": 17,
    "failed_count": 55,
    "in_progress_count": 70
  },
  "widgets": [...]
}
```

Widget data shape depends on widget type (`metric`, `funnel`, `rubric`).

### PUT /api/projects/{project_id}/dashboard/yaml — body

```json
{ "yaml": "<YAML string>" }
```

Validates YAML before saving. Returns `{"ok": true}` or `400` with parse error detail.

---

## Runners

Any authenticated user can provision a runner. Runners authenticate with `runner_id:secret` bearer token.

| Method | Path | Auth | Required role | Description |
|---|---|---|---|---|
| `POST` | `/api/runners/provision` | Firebase | any | Generate a one-time registration token (with visibility setting) |
| `POST` | `/api/runners/register` | None | — | Runner exchanges provision token for permanent secret |
| `GET` | `/api/runners` | Firebase | any | List active runners (filtered by visibility) |
| `PUT` | `/api/runners/{runner_id}/visibility` | Firebase | creator or super-admin | Change runner visibility setting |
| `PUT` | `/api/runners/{runner_id}/heartbeat` | Runner | — | Update `last_heartbeat_at` (online ping) |
| `GET` | `/api/runners/{runner_id}/projects` | Runner | — | Fetch projects assigned to this runner (schedule + configs) |
| `DELETE` | `/api/runners/{runner_id}` | Firebase | site-admin+ | Remove a runner |

### POST /api/runners/provision — body

```json
{ "visibility": "all" }
```

`visibility` options: `"all"` (default) \| `"me"` (only provisioner can see) \| `"project"` (users with access to assigned projects).

Returns: `201`
```json
{ "runner_id": "abc123...", "provision_token": "..." }
```

### POST /api/runners/register — body

```json
{
  "provision_token": "...",
  "name": "office-server",
  "machine_name": "hostname",
  "machine_id": "A1B2C3D4-...",
  "os": "Darwin 24.5.0 (arm64)",
  "python_version": "3.11.9",
  "runner_version": "0.1.0",
  "config_path": "/Users/alice/.sabu/config.json",
  "log_path": "/Users/alice/.sabu/logs"
}
```

All fields except `provision_token`, `name`, and `machine_name` are optional. Sent automatically by `python runner/runner.py init`.

Returns: `201`
```json
{ "runner_id": "abc123...", "secret": "..." }
```

Returns `404` if provision token is invalid or already used.

### GET /api/runners

Returns runners visible to the caller based on `visibility` field:
- `"all"` — visible to everyone
- `"me"` — only the creator (+ super-admin)
- `"project"` — users who have access to at least one of the runner's `assigned_project_ids`
- Creator always sees their own runners regardless of visibility setting

```json
[{
  "id": "abc123...",
  "name": "office-server",
  "machine_name": "hostname",
  "assigned_project_ids": ["proj-id-1"],
  "last_heartbeat_at": "2026-08-05T10:30:00",
  "online": true,
  "created_at": "2026-08-01T09:00:00",
  "machine_id": "A1B2C3D4-...",
  "os": "Darwin 24.5.0 (arm64)",
  "python_version": "3.11.9",
  "runner_version": "0.1.0",
  "config_path": "/Users/alice/.sabu/config.json",
  "log_path": "/Users/alice/.sabu/logs",
  "visibility": "all",
  "created_by": "user@example.com"
}]
```

`online` is `true` if `last_heartbeat_at` within the last 2 minutes.

### PUT /api/runners/{runner_id}/visibility — body

```json
{ "visibility": "all" }
```

Only the runner's creator or a super-admin can call this. Returns updated runner object.

---

## Runner Jobs

Runner-facing endpoints for atomic job claiming. Auth: `runner_id:secret` bearer.

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/runner-jobs/claim` | Runner | Upsert + atomic claim a job by hash |
| `PUT` | `/api/runner-jobs/{job_id}/done` | Runner | Mark job complete |
| `PUT` | `/api/runner-jobs/{job_id}/failed` | Runner | Mark job failed with error message |

### POST /api/runner-jobs/claim — body

```json
{
  "job_hash": "sha256hex...",
  "type": "ingest",
  "project_id": "...",
  "config_id": "uuid",
  "date": "2026-08-05",
  "session_id": null
}
```

- Creates the job record if it doesn't exist (upsert by `job_hash`)
- Claims it atomically — second caller for the same hash gets `409`
- Reclaims `failed` or expired-`processing` (lock > 10 min) jobs

Returns `200` with the job object, or `409` if already claimed.

Job object shape:
```json
{
  "id": "...",
  "job_hash": "...",
  "type": "ingest",
  "project_id": "...",
  "config_id": "uuid",
  "date": "2026-08-05",
  "session_id": null,
  "status": "processing",
  "claimed_by": "runner-abc",
  "started_at": "2026-08-05T10:00:00",
  "finished_at": null,
  "error": null,
  "created_at": "2026-08-05T10:00:00"
}
```

### PUT /api/runner-jobs/{job_id}/done

Returns `{"ok": true}` or `404` if job not found / not owned by this runner.

### PUT /api/runner-jobs/{job_id}/failed — body

```json
{ "error": "transcription failed: network timeout" }
```

Returns `{"ok": true}` or `404` if job not found / not owned by this runner.

---

## Users

User management. Only site-admins+ can list/create/update/delete users.

| Method | Path | Auth | Required role | Description |
|---|---|---|---|---|
| `GET` | `/api/users` | Firebase | site-admin+ | List all users |
| `POST` | `/api/users` | Firebase | site-admin+ | Create a user (optionally creates Firebase password account) |
| `GET` | `/api/users/me` | Firebase | any | Get caller's own profile + roles |
| `GET` | `/api/users/resolve-phone` | **None** | — | Resolve phone number → email (for phone login) |
| `PUT` | `/api/users/{email}` | Firebase | site-admin+ (or super-admin for global_role) | Update a user |
| `DELETE` | `/api/users/{email}` | Firebase | site-admin+ | Delete a user |

### POST /api/users — body

```json
{
  "email": "user@example.com",
  "first_name": "Alice",
  "phone": "+911234567890",
  "password": "optional — creates Firebase email/password account",
  "global_role": "site-admin",
  "project_roles": {
    "project-id-1": "project-admin",
    "project-id-2": "project-user"
  }
}
```

- `global_role` can only be set to `"site-admin"` by a super-admin
- `project_roles` values: `"project-admin"` \| `"project-user"`
- Returns `201` with the created user object

### GET /api/users/me

No auth token required for the resolve-phone endpoint. Returns:
```json
{
  "email": "user@example.com",
  "first_name": "Alice",
  "global_role": "site-admin",
  "project_roles": {"project-id-1": "project-admin"}
}
```

### GET /api/users/resolve-phone

Public — no auth required. Used on the login page to convert a phone number to email before Firebase sign-in.

Query param: `phone` (string, e.g. `+911234567890` or bare 10-digit).

Returns:
```json
{ "email": "user@example.com" }
```

Returns `404` if no account found for that phone number.

Phone normalization: `+91XXXXXXXXXX`, `91XXXXXXXXXX` (12 digits), 10-digit bare, and `0XXXXXXXXXX` (0-prefix) all map to `+91XXXXXXXXXX`.

---

## Error responses

| Code | When |
|---|---|
| `400` | Invalid project ID (not a valid ObjectId), invalid YAML, invalid visibility value |
| `401` | Missing or invalid token (Firebase or runner) |
| `403` | Insufficient role — caller lacks required project or global role; runner ID mismatch |
| `404` | Project, call, runner, job, or user not found; invalid provision token; phone not found |
| `409` | Job already claimed or completed (race condition on claim) |

[← Back to index](sales-booster.md)
