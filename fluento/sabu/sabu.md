# Sabu — AI Sales Call Analysis

Sabu listens to every sales call so your managers don't have to.

---

## The Problem

Sales teams make hundreds of calls a day. Managers can realistically listen to 5–10. Everything else goes unreviewed — bad habits compound, good calls go unnoticed, and coaching is reactive at best.

---

## What Sabu Does

Sabu automatically analyses every recorded sales call against a set of criteria you define. For each call it produces:

- A full transcript with speaker labels (agent vs customer)
- A score or answer for each criterion — e.g. "Did the agent introduce themselves? 4/5", "Was a meeting booked? No"
- A one-line justification for every score, grounded in what was actually said

Results are available in a dashboard — filterable by agent, date, disposition, and score — so managers can spot patterns, identify outliers, and coach with evidence.

---

## Who It's For

- **Sales managers** who want visibility across their full team, not just the calls they happen to listen to
- **QA / training teams** who need consistent, objective scoring at scale
- **Revenue leaders** who want to understand what separates converted calls from lost ones

---

## How It Works

```
Telephony system          Sabu
(e.g. Tubelight)
                          1. Ingest
    CDR + recordings ────▶ Pull call records for the day
                           Filter by team / campaign / talk time
                           Store in database

                          2. Analyse (AI pipeline)
                           Transcribe audio → Hindi/English text  (Sarvam AI)
                           Split into agent / customer turns       (Gemini)
                           Score each rubric                       (Gemini)

                          3. Dashboard
                           View scores, transcripts, trends
                           Filter and drill into any call
```

### Rubrics — define your own criteria

A rubric is a question + an output format. Examples:

| Rubric | Output | Example prompt |
|---|---|---|
| Opening quality | Score 1–5 | "Did the agent introduce themselves by name and company?" |
| Meeting booked | Yes / No | "Was a demo or physical meeting explicitly confirmed?" |
| Objection handled | Enum | "How well did the agent handle the customer's main objection? (Well / Partially / Poorly)" |
| Key insight | Free text | "What was the customer's primary concern in this call?" |

You define the rubrics. The AI answers them for every call.

---

## Conversion Tracking

Every project has configurable **success stages** and **failure stages** — drawn from the disposition values your telephony system records (e.g. "Deal Created" = success, "Explicit Disinterest" = failure).

Conversion rate = success-stage calls / total calls, always calculated on whatever filter is active in the dashboard.

---

## Current Telephony Integration

**Tubelight** (hellotubelight.com) — supported out of the box.

The ingest layer is designed to be provider-agnostic. Adding a new telephony system (Exotel, Knowlarity, Aircall, etc.) requires implementing one module that maps the provider's CDR to Sabu's call schema. See `tech-spec.md` for details.

---

## Languages Supported

Optimised for **Hindi and Hindi-English code-switched** sales calls (common in India). The transcription model (Sarvam saarika:v2.5) is purpose-built for Indian languages and accents.

Rubric scoring works in any language the underlying LLM supports.

---

## Cost

~$0.004 per call (avg 53s call, 2 rubrics). Transcription is ~83% of the cost; adding more rubrics is nearly free.

| Volume | Daily | Monthly |
|---|---|---|
| 100 calls/day | $0.43 | $13 |
| 700 calls/day | $3.00 | $91 |
| 5,000 calls/day | $21 | $640 |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Tailwind CSS, Firebase Hosting |
| Auth | Firebase Google Auth |
| Backend | Python, FastAPI |
| Database | MongoDB |
| Transcription | Sarvam AI (saarika:v2.5) |
| Diarization + Scoring | Google Gemini 2.5 Flash |
| Audio processing | ffmpeg |

---

## Docs

- [`tech-spec.md`](./tech-spec.md) — components, how to run, how to add a new telephony system
- [`features/Dashboard for analytics.md`](./features/Dashboard%20for%20analytics.md) — dashboard feature spec
- [[Job orchestration framework]]
