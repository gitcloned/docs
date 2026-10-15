## What is this

Sabu is an AI-powered sales call analysis platform. It ingests call recordings from telephony systems, transcribes and diarizes them, scores each call against configurable rubrics, and presents results in a dashboard.

The system is designed to work with any telephony/CPaaS provider — not just Tubelight.

---

## Components

```
┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│    Backend      │
│  (React / Vite) │     │   (FastAPI)     │
└─────────────────┘     └────────┬────────┘
                                 │
                         ┌───────▼────────┐
                         │    MongoDB     │
                         └───────┬────────┘
                        ┌────────┴────────┐
               ┌─────────▼──────┐  ┌──────▼──────────┐
               │ Ingest Worker  │  │ Analyse Worker  │
               │ (per system)   │  │ (AI pipeline)   │
               └────────────────┘  └─────────────────┘
                        ▲
               ┌────────┴────────┐
               │  Telephony      │
               │  (e.g. Tubelight│
               └─────────────────┘
```

### Frontend
React + Vite app. Firebase Google Auth for login. Talks only to the Backend API.
Hosted on Firebase Hosting.

### Backend
FastAPI service. Verifies Firebase ID tokens on every request. Reads/writes MongoDB.
Exposes REST endpoints for projects and calls — used only by the Frontend.

### MongoDB
Single database (`sales_booster`). Two collections:
- **`projects`** — project config: name, rubrics, ingestion configs, conversion stage settings
- **`calls`** — one document per call: CDR metadata + transcript + rubric scores + status

### Ingest Worker
A CLI script that pulls call records from a telephony system and writes them to MongoDB.
One worker implementation per telephony provider (e.g. `tubelight.py`).
Idempotent — safe to re-run, skips calls already in the database.

### Analyse Worker
A CLI script that picks up `pending` calls and runs the AI pipeline:
1. Check `talk_time_seconds` against `min_talk_seconds` (min across all enabled ingestion configs) — mark `skipped` and stop if below threshold
2. Download recording (or load from disk cache)
3. Transcribe with Sarvam saarika:v2.5 (chunked, ≤25s per API call)
4. Diarize with Gemini 2.5 Flash (LLM splits transcript into AGENT / CUSTOMER turns)
5. Score each project rubric with Gemini 2.5 Flash
6. Write transcript + scores back to MongoDB, mark call as `done`

---

## How to Run

### Prerequisites
- Python 3.11, Node.js 18+, pnpm
- MongoDB running locally (`mongod`)
- ffmpeg installed (used by analyse worker for audio chunking)
- API keys: Sarvam, Gemini (see `workers/.env`)
- Firebase service account key (see `backend/.env`)

### Backend
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 14100
```
Env: `backend/.env` — `MONGO_URI`, `FIREBASE_CREDENTIALS_PATH`, `CORS_ORIGINS`, `PORT`

### Frontend
```bash
cd frontend
pnpm dev          # dev server on port 14101
pnpm build        # production build
```
Env: `frontend/.env` — Firebase config keys, `VITE_API_BASE_URL`

### Ingest Worker
```bash
cd <repo-root>
source workers/.venv/bin/activate
python3 -m workers.ingest.ingest \
  --project-id <mongo-project-id> \
  --config-id  <ingestion-config-uuid> \
  --date       YYYY-MM-DD
```
- `--project-id` — MongoDB `_id` of the project
- `--config-id` — UUID of the ingestion config within that project (sets the filter)
- `--date` — which day's CDR to fetch

Run this on a cron or manually per day per config.

### Analyse Worker
```bash
cd <repo-root>
source workers/.venv/bin/activate
python3 -m workers.analyse.analyse \
  --project-id <mongo-project-id> \
  --limit 100
```
- `--limit` — max calls to process in one run (default 50)
- Picks up all `status=pending` calls for the project

Run after ingestion. Re-running is safe — already-done calls are skipped.

---

## Call Status Lifecycle

```
pending → processing → done
                    └→ failed
pending → skipped (talk time below threshold — not scored)
```
- `pending` — ingested, not yet analysed
- `processing` — analyse worker has picked it up (in-flight)
- `done` — transcript + rubric scores written
- `failed` — error during transcription or scoring (error message stored)
- `skipped` — talk time below the project's `min_talk_seconds` threshold; never scored; excluded from dashboard counts and calls list by default

`skipped` vs previous behaviour: calls below the talk-time threshold were previously filtered out at ingest (never stored). Now they are stored but marked `skipped` by the analyse worker — visible via `status=skipped` filter if needed.

If a call is stuck in `processing` (e.g. worker crashed), reset it to `pending` to retry:
```bash
db.calls.updateOne({_id: "<session-id>"}, {$set: {status: "pending"}})
```

---

## Recording Storage

Recordings are downloaded from the telephony provider and cached locally to avoid re-downloading on retries.

Storage is abstracted (`workers/shared/storage.py`). Current implementation: disk.
Files are organised as: `recordings/YYYY-MM/<session-id>.mp3`

To add S3 storage: implement the `RecordingStorage` ABC and set `RECORDING_STORAGE=s3` in `workers/.env`.

---

## Adding a New Telephony System

The ingest worker is the only part that is provider-specific. Everything else (analyse, backend, frontend) is system-agnostic.

To add a new provider (e.g. Exotel, Knowlarity, Aircall):

**1. Create `workers/ingest/<provider>.py`**

Implement two things:
- Auth / session management for the provider's API
- A function that fetches CDR (call detail records) for a given date and returns a list of dicts

**2. Map provider fields to the Call schema**

Every call document written to MongoDB must have these fields:

```python
{
    "_id":               str,        # unique call/session ID from the provider
    "project_id":        str,        # MongoDB project _id (string)
    "agent_name":        str,
    "team_name":         str,
    "campaign":          str,
    "customer_number":   str,
    "start_time":        datetime,
    "end_time":          datetime,
    "talk_time_seconds": int,
    "final_tag":         str,        # disposition / outcome label
    "comment":           str,
    "disconnected_by":   str,
    "recording_url":     str,        # URL the analyse worker downloads from
    "transcript":        [],         # empty at ingest time
    "analysis":          {},         # empty at ingest time
    "status":            "pending",
    "error":             None,
    "created_at":        datetime,
}
```

**3. Write to MongoDB (idempotent)**

Use `update_one` with `upsert=True` and `$setOnInsert` so re-runs don't overwrite existing records:

```python
calls_col.update_one(
    {"_id": call["_id"]},
    {"$setOnInsert": call},
    upsert=True,
)
```

**4. Add provider credentials to `workers/.env`**

Add whatever API keys, tenant IDs, or tokens the provider needs.

**5. Wire up in `ingest.py`**

The main `ingest.py` CLI reads the project's ingestion config (filters like team name, campaign) and calls the provider module. Add a branch for the new provider name. Note: `min_talk_seconds` is no longer applied at ingest — it's applied by the analyse worker.

That's it. The analyse worker, backend, and frontend don't change at all.

---

## Project Config — Key Concepts

### Rubrics
Defined per project. Each rubric has:
- **name** and **prompt** — sent to the AI
- **output_type** — `range` (1–5), `boolean`, `enum`, `freetext`
- **range / options** — constraints for range and enum types

The AI is given the full transcript + call metadata and asked to answer the rubric prompt in the specified output format.

### Ingestion Configs
Multiple configs per project. Each config defines a filter and is identified by a UUID. Pass the UUID as `--config-id` when running the ingest worker. This lets one project ingest from multiple teams or campaigns independently.

Filter fields:
- `team_name` — comma-separated team names, matched case-insensitively at ingest; also used as a dashboard/calls filter when a config is selected in the UI
- `campaign` — comma-separated campaign names, same behaviour
- `agent_names` — list of exact agent name strings
- `min_talk_seconds` — enforced at **analysis time** (not ingest) — short calls land in DB as `skipped`

The dashboard and calls list UI have a "Config" dropdown. Selecting a config injects that config's `team_name` and `campaign` as API filters (does **not** apply `min_talk_seconds`).

### Conversion Stages
Defined in project settings. A list of disposition values (from the telephony system's final tag) that count as **success** (e.g. "Deal Created", "Meeting Confirmation Pending") and a list that count as **failure** (e.g. "Explicit Disinterest", "Has Quit"). Conversion rate = success calls / total calls.

---

## AI Pipeline — Cost Reference

Per call (avg 53s Hindi sales call, 2 rubrics):

| Step | Provider | Cost |
|---|---|---|
| Transcription | Sarvam saarika:v2.5 | ~$0.0035 |
| Diarization | Gemini 2.5 Flash | ~$0.0005 |
| Scoring (per rubric) | Gemini 2.5 Flash | ~$0.0001 |
| **Total** | | **~$0.004** |

Adding more rubrics is nearly free (Gemini token cost is minimal). STT dominates at ~83% of cost.
