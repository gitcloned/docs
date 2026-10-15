# System — Sabu

Sabu is an AI-powered sales call analysis platform: ingest recordings → transcribe → diarize → score → dashboard.

Full technical reference: **[`tech-spec.md`](./tech-spec.md)**

---

## Components

```
Frontend (React/Vite)
  └─▶ Backend (FastAPI) ──▶ MongoDB (sales_booster db)
                                ├─ projects  (config, rubrics, ingestion configs)
                                ├─ calls     (CDR + transcript + rubric scores)
                                ├─ runners   (registered runner machines)
                                ├─ runner_jobs (ingest + analyse job queue)
                                └─ users     (RBAC — roles, phone numbers)
                                     ▲
                Ingest Worker ───────┘  (pulls CDR from telephony provider)
                Analyse Worker ──────┘  (transcribe → diarize → score)
                                     ▲
                Telephony system ────┘  (e.g. Tubelight)
```

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Tailwind CSS, Firebase Hosting |
| Auth | Firebase Auth — Google OAuth + email/password (for phone login) |
| Backend | Python 3.11, FastAPI |
| Database | MongoDB (`sales_booster` db, 5 collections) |
| Transcription | Sarvam AI saarika:v2.5 (chunked, ≤25s per call) |
| Diarization + Scoring | Gemini 3.5 Flash (model ID: `gemini-3.5-flash`) |
| Audio processing | ffmpeg (splits audio into chunks) |

## Auth & Login

Two login methods on the login page:
- **Google** — Firebase Google OAuth; email from Google identity used as user key
- **Phone + password** — frontend calls `GET /api/users/resolve-phone?phone=...` (no auth) to get the email, then calls Firebase `signInWithEmailAndPassword`. Backend creates the Firebase email/password account when a user is created with a `password` set.

## RBAC

Roles checked on every Firebase-authenticated endpoint:

| Role            | How granted                                     | Implicit project-admin? |
| --------------- | ----------------------------------------------- | ----------------------- |
| `super-admin`   | `SUPER_ADMIN_EMAIL` env var                     | Yes — all projects      |
| `site-admin`    | `global_role: "site-admin"` in users collection | No — uses project_roles |
| `project-admin` | `project_roles[project_id]: "project-admin"`    | —                       |
| `project-user`  | `project_roles[project_id]: "project-user"`     | —                       |

Key rule: **site-admin is NOT an implicit project-admin** — the only extra privilege is being able to create projects. All other access is controlled by `project_roles`.

When a site-admin creates a project, they are automatically added as `project-admin` for that project.

RBAC is implemented in `backend/rbac.py` via FastAPI dependencies (`require_site_admin`, `require_project_admin`, `require_project_access`, `get_project_role`, `get_accessible_project_ids`).

## Call Status Lifecycle

```
pending → processing → done
                    └─▶ failed
```

- `pending` — ingested, waiting for analyse worker
- `processing` — picked up by analyse worker (in-flight)
- `done` — transcript + scores written
- `failed` — error during pipeline (error message stored on call)

## Worker Design

All workers are CLI scripts or Lambda functions, not long-running services.
- **Ingest Worker** — delegates to an `IngestSource` (see below). Idempotent — safe to re-run.
- **Analyse Worker** — provider-agnostic. Picks up all `pending` calls for a project and runs the AI pipeline.
- **Report Worker** — generates and emails a daily HTML report per project. Runs as an AWS Lambda (triggered by EventBridge at 8:00 IST). Uses runner auth (not Firebase) to fetch data via REST API. See [features/Scheduled report.md](./features/Scheduled report.md).

See `tech-spec.md → How to Run` for exact commands.

## Ingest Source Abstraction

Telephony providers are pluggable via an abstract factory:

```
workers/sources/
  base.py               ← IngestSource ABC (fetch_cdr, get_recording_url)
  factory.py            ← get_source(source_type) → IngestSource
  ADDING_A_SOURCE.md    ← guide for new providers
  tubelight/
    client.py           ← Tubelight API calls
    source.py           ← TubeLightSource(IngestSource)
```

Each ingestion config stores a `source` field (e.g. `"tubelight"`). The factory returns the right implementation at runtime.

**Audio handling per source:**
- **Permanent CDN URLs** (Tubelight): `get_recording_url` returns the CDN URL as-is — no upload needed. Workers and frontend stream directly.
- **Expiring/local files** (future sources): source downloads and uploads to S3, returns S3 URL — stored permanently in MongoDB.

To add a new source: follow `workers/sources/ADDING_A_SOURCE.md`.

## Deployment

| Layer | Platform | Notes |
|---|---|---|
| Frontend | Firebase Hosting | `firebase deploy` |
| Backend | AWS ECS | Docker container, env vars from Secrets Manager |
| Database | MongoDB Atlas (or AWS DocumentDB) | Connection via `MONGO_URI` |

**Backend deploy — Jenkins job:** `build-prod-sabu`
- Jenkins: `https://jenkins-v2.leadschool.in/job/build-prod-sabu/`
- Builds the Docker image from `backend/Dockerfile`, pushes to ECR, updates ECS task definition

**Production logs (Grafana/Loki):** `http://10.0.60.218:3000/explore`
- Loki query: `{task="prod-sabu"}` — streams all ECS container logs
- Task label set by ECS task definition; logs are indexed by Loki agent on the host

**Key env vars for ECS:**

| Var | Description |
|---|---|
| `MONGO_URI` | Atlas connection string |
| `FIREBASE_CREDENTIALS_JSON` | Full service-account JSON (single line, from Secrets Manager) |
| `CORS_ORIGINS` | Comma-separated allowed origins (Firebase Hosting URL + localhost) |
| `SUPER_ADMIN_EMAIL` | Email with permanent super-admin access (no DB record needed) |
| `ALLOWED_DOMAINS` | Optional — restrict Firebase sign-in to specific domains |

**MongoDB seed for production:**
```bash
# Dump local DB
bash scripts/mongo-dump.sh
# Restore in production
mongorestore --uri="<PROD_URI>" --drop --gzip --archive=dumps/sales_booster_<date>.tar.gz
```

[← Back to index](sales-booster.md)
