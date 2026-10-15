# prodigy — System

Architecture, components, and tech stack.

---

## Overview

Prodigy has four sub-systems in the monorepo:

```
prodigy/
├── cms/      # Content management + LP service (Express + MongoDB)
├── agent/    # AI teaching harness (TypeScript + Gemini)
├── canvas/   # Student interactive canvas (React + tldraw)
└── erp/      # People, students, classrooms, access codes (planned — cms/packages/erp)
```

```
Student (iPad/browser)
        │
        ▼
┌───────────────────────┐
│  canvas/  (port 32000)│
│  React + tldraw       │
│  WebSocket client     │
└──┬─────────┬──────────┘
   │ HTTP    │ wss://
   ▼         ▼
┌──────────┐  ┌─────────────────────────────────────────────┐
│  ERP     │  │  agent/  (port 32003)                        │
│ (32005)  │  │  MultiSessionServer — many students at once  │
│ students │  │  HTTP: POST /sessions → sessionId            │
│ classes  │  │  WS:   ?sessionId=xxx → agent session        │
│ auth     │  │  TurnEngine (Gemini Flash) per connection     │
└──────────┘  └────────┬──────────────────────┬─────────────┘
                       │ HTTP                  │ HTTP
                       ▼                       ▼
              ┌─────────────────┐   ┌──────────────────────┐
              │  CMS (32001)    │   │  LP service (32002)   │
              │  Concepts,      │   │  Journeys, sessions,  │
              │  resources,     │   │  memory               │
              │  questions      │   └──────────────────────┘
              └─────────────────┘
```

- **Canvas** — React + tldraw student UI. Connects over WebSocket to agent. Input: text, voice (Whisper STT), photos. Output: write, speak (Inworld TTS), annotate, interactive models, graphs. Port 32000.
- **Agent / MultiSessionServer** — TypeScript AI tutor harness. One persistent process, many concurrent student sessions. HTTP `POST /sessions` creates a session; WS `?sessionId=xxx` joins it. Each connection gets its own `PerConnectionTransport` and agent session. Port 32003.
- **ERP** — People service. Student profiles, access codes, classrooms, enrollment, parent/teacher accounts. Express + Mongoose. Port 32005 (planned).
- **CMS backend** — Node.js + Express, Mongoose. REST API for content (concepts, questions, resources). Port 32001.
- **LP service** — Learning Progression. Express + Mongoose. Tracks journeys, nodes, sessions, memory. Port 32002 (also serves admin HTML).
- **Database** — MongoDB (local). One instance shared across CMS, LP, and ERP collections.

### cli.mjs vs server.mjs

Two ways to run the agent — both use the same `SessionManager` and agent code:

| | `cli.mjs` | `server.mjs` |
|---|---|---|
| Students | One per process | Many concurrent |
| Session start | CLI args `--student --concept` | HTTP `POST /sessions` |
| Transport | `StdinTransport` or `WebSocketTransport` (1:1) | `PerConnectionTransport` per WS connection |
| Use case | Local dev / testing | Deployed backend |

---

## Monorepo structure

```
prodigy/
├── cms/
│   ├── content/                 # Markdown plan files (probe.md, teach.md, mastery.md, questions.json)
│   ├── packages/
│   │   ├── types/               # Shared TypeScript interfaces
│   │   ├── backend/             # CMS REST API          (port 32001)
│   │   ├── admin/               # React + Vite admin UI (port 32003)
│   │   ├── learning-progression/# LP REST API           (port 32002)
│   │   ├── resources/           # Interactive model assets + server (port 32003)
│   │   └── mcp/                 # MCP server (stdio)
│   └── pnpm-workspace.yaml
├── agent/
│   ├── src/
│   │   ├── medium/              # CanvasMedium + modalities (output + input)
│   │   ├── learning/            # Plan builders, state machine, practice exercise
│   │   ├── tools/               # Tool implementations
│   │   └── transports/          # StdinTransport, WebSocketTransport
│   ├── skills/                  # Skill prompt files (SKILL.md per state)
│   ├── prompts/base.md          # Base system prompt
│   └── scripts/cli.mjs          # CLI entry point
└── canvas/
    ├── src/                     # React + tldraw canvas app
    └── tests/                   # Unit tests
```

Start CMS: `pnpm dev` from `cms/`. Start agent server: `node scripts/server.mjs` from `agent/`. Start canvas: `pnpm dev` from `canvas/`. CLI (dev/test): `node scripts/cli.mjs --concept <slug> --medium canvas --student <id>` from `agent/`.

---

## Scripts

### `scripts/ka-import/` — Khan Academy content importer

3-step pipeline. Pulls a KA topic into MongoDB as the 4-level hierarchy + Questions.

```
Step 1  get-session.mjs                              → ka-session.json
        (Playwright, once — passes bot detection)

Step 2  extract-content-from-ka.mjs <topic-url>     → <topic>-import.json
        (plain HTTPS — enriches videos, fetches exercise question pools)

Step 3  import.mjs <topic>-import.json              → MongoDB
        (idempotent upsert, safe to re-run)
```

- **`get-session.mjs`** — opens a real browser once; captures session cookies, the `ContentRouteLessonAndContentData` GraphQL signature (pcv + hash), and the exact `getAssessmentItemByProblemNumber` query body. Saves to `ka-session.json`. Re-run only when cookies expire (~session).
- **`extract-content-from-ka.mjs <url>`** — takes a KA topic URL; fetches all teaching items (videos, articles) and exercise items; for exercises iterates `problemNumber` via the captured GraphQL query until a SHA repeats (pool fully discovered); outputs a single JSON with strand/unit/topic hierarchy + Perseus question blobs. Flags: `--out`, `--no-questions`, `--subject`, `--strand-title`, `--concurrency`, `--delay-min`, `--delay-max`.
- **`import.mjs <json>`** — upserts Strand → Unit → Topic → Concept → Resource → Question. Unique key: `{ source, kaSlug }`. Safe to re-run. Flags: `--dry-run`, `--skip-questions`, `--only-questions`. Accepts both single-topic and full-course JSON shapes.
- **`question-import.mjs`** *(optional enrichment)* — for practice-test Resources in DB that have no questions yet; fetches question pools from KA. Flags: `--all` (re-fetch even populated exercises).
- **`reconstruct.mjs`** *(one-time migration)* — rebuilt full-course `ka-algebra-import.json` from old MongoDB schema.

Output per topic: Strand (1), Unit (1), Topic (1), Concepts (N), Resources (teaching + practice), Questions (Perseus format, SHA-deduplicated from KA's exercise pool).

Current DB state: strands (1), units (17), topics (94), concepts (402), resources (585), questions (75).

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + Vite | No SSR needed for CMS; Vite is faster locally |
| Backend | Node.js + Express | Same language as frontend |
| Shared types | pnpm workspaces + `packages/types` | Prevents schema drift across packages |
| MCP | `@modelcontextprotocol/sdk`, stdio | Calls backend API — no direct DB access |
| Database | MongoDB | Nested lesson plans and misconceptions fit documents naturally |
| Content import | Playwright (session) + HTTP (fetch) | Bot detection requires one real browser; subsequent fetches are plain HTTP |
| LLM | Gemini Flash (`@google/genai` 2.x) | Function calling via `functionDeclarations`; `systemInstruction` separate from history |
| Agent transport | `Transport` interface + `StdinTransport` / `WebSocketTransport` | Decouples I/O from agent logic; same interface, two transports |
| Canvas UI | React + tldraw | Interactive drawing canvas with shape primitives; chosen for annotation + geometry |
| STT | Groq Whisper | Fast, cheap transcription for voice input |
| TTS | Inworld | Low-latency streaming audio for agent speech |
| Interactive models | JSON manifest + Three.js renderer | 3D models (cuboid) and 2D function graphs served as static assets |

---

## Medium architecture

`agent/src/medium/` — abstracts what the LLM can output and what the student can input. One medium per transport connection.

```
BaseMedium
  outputModalities: OutputModalityRegistry   ← speak, write, draw, model, model3d, annotate, question, camera, …
  inputModalities:  InputModalityRegistry    ← text, audio, image
```

**Output pipeline:**
```
LLM text_chunk stream
  → OutputParser (scans for key: lines)
  → active OutputModality.handle(chunk) / .end(attrs)
  → TurnEvent (speech, write, model, action, …)
  → Transport → Canvas
```

LLM writes structured output using keyword lines:
```
speak: Here is your question.
write: 3x + 5y = 100
model: function-graph
/equation: y = 2*x - 3
/action: plot
camera: open
```

**Input pipeline:**
```
Student input (text / audio / image)
  → InputModality.process()
  → LLM history entry
```

**Modalities registered in `CanvasMedium`:**

| Key | Type | Effect |
|---|---|---|
| `speak:` | output | TTS audio via Inworld |
| `write:` | output | Animated text on canvas |
| `draw:` | output | SVG diagram |
| `model:` | output | Interactive 2D graph (function-graph) |
| `model3d:` | output | 3D unit-cube model |
| `annotate:` | output | Underline/circle existing canvas text |
| `question:` | output | Question frame on canvas |
| `camera:` | output | Opens student camera (`camera: open`) |
| `ask:` | output | Pause and wait for student response |
| `play:` | output | Play a model animation routine |

[← Back to index](prodigy.md)
