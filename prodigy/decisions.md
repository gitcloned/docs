# prodigy — Decisions

Key design choices and why. Alternatives ruled out noted inline.

---

## Content Model

**`Question` is a top-level collection, not embedded in Concept.**
Questions are shared — they appear in concept question banks, lesson step indicators, misconception checks, and resource CFU markers. Embedding would force duplication.

**`Board` is an attribute array on `Concept`, not a separate mapping table.**
Simpler to query and author. A concept lists which boards it applies to (`boards: [BoardRef]`).
Ruled out: `CurriculumMap` entity (Board + Class → ordered [ConceptRef]) — correct model for curriculum sequencing but over-engineered for current scope.

**`LessonPlan` is a flat ordered sequence of `LessonStep`, not grouped by type.**
Each step carries its own `type` (ido/wedo/youdo). Flat sequence preserves teaching order exactly as authored. Ruled out: nested structure with separate ido/wedo/youdo arrays — loses interleaving order.

**`Resource` is a top-level collection.**
Same resource (e.g. a video) can appear in multiple lesson plans across concepts. Top-level avoids duplication. Type-specific fields (`cfuMarkers`, `questions`) use discriminated structure on a single collection.

**Difficulty levels are `lots` / `mots` / `hots`** (Lower / Middle / Higher Order Thinking Skills).
Maps to Bloom's taxonomy tiers. Standard in Indian edtech curriculum. Ruled out: numeric 1–5 scale — less meaningful to content authors.

---

## Tech Stack

**Monorepo with pnpm workspaces — 4 packages: `types`, `backend`, `frontend`, `mcp`.**
Shared TypeScript interfaces across all packages prevent schema drift. Single `pnpm dev` to run everything. Ruled out: separate repos — type duplication; single Express process — mixes concerns.

**Frontend: React + Vite (not Next.js).**
No SSR needed for a CMS. Vite is faster for local dev. User preference.

**Backend: Node.js + Express + TypeScript.**
Consistent language with frontend. Mongoose for MongoDB ODM.

**MCP server: TypeScript, stdio transport, calls backend API.**
MCP never talks to MongoDB directly — all business logic and validation stays in the backend. MCP is a thin API client.

**Database: MongoDB (local instance).**
Document model fits nested content (lesson steps, misconceptions, question steps). Already running locally.

**Deployment: local-first.**
Docker Compose or cloud deployment is a future concern.

---

## Structure

**Repo lives at `prodigy/cms/`** — not repo root, keeps the door open for other subprojects.

---

## Content Sourcing — Khan Academy

**Use KA content as the initial resource layer, linked by URL — not copied into DB.**
Videos and exercises are stored as `Resource` docs pointing to KA/YouTube URLs. KA's content is free (CC BY-NC-SA). Ruled out: scraping and storing content locally — ToS risk, storage overhead, and KA's content changes.

**Playwright once for cookies, then plain HTTP for all subsequent requests.**
KA's site requires a JS bot-challenge that only a real browser can pass. One Playwright session captures cookies + the GraphQL request signature. All 600+ items are then fetched concurrently via plain `https.get` using those cookies. Ruled out: Playwright per page — too slow (~5s each); scraping HTML — too fragile.

**Unit-order progression as prerequisite chain for imported content.**
KA doesn't expose a prerequisite graph via API. Unit sequence (Unit 1 → Unit 2 → …) is used as a proxy. Each imported concept's `prerequisites[]` points to the previous unit's concept. Ruled out: inferring prereqs via LLM — adds complexity, can be done later as an enrichment step.

**KA exercise answers are not imported — stems only.**
KA's `getAssessmentItemByProblemNumber` endpoint returns question stems in LaTeX and widget types (MCQ, numeric input) but withholds correct answers intentionally. Stems are available for import; answers must be authored manually or solved by LLM.

---

## Question Format — Perseus

**`Question.type` includes `"perseus"` as a first-class type alongside `mcq`, `fib`, `subjective`.**
Perseus is Khan Academy's open-source exercise format ([github.com/Khan/perseus](https://github.com/Khan/perseus)). A question is a JSON blob: a Markdown+LaTeX content string with `[[☃ widget-name]]` placeholders, plus a `widgets` map that defines 1–N interactive components. The renderer handles display — no pre-defined type needed.

Ruled out: mapping Perseus widgets to `mcq`/`fib`/`subjective` — too restrictive. Perseus has 33 widget types including graphing (`interactive-graphs`), algebraic expression input (`expression`), drag-and-drop (`categorizer`, `sorter`), PhET simulations, and more. A fixed enum cannot represent this.

**Native (Prodigy-authored) questions keep their structured fields** (`stem`, `idealAnswer`, `steps`). Perseus questions store the raw `perseusContent` blob. The `type` field tells the renderer which path to take.

---

## Adaptive Hint Trees

**Two distinct tree types, same `HintStep` node structure.**
- `Concept.probingTree` — cross-concept diagnostic. Navigates backward through prerequisites to find where a student's understanding holds firm (the knowledge floor). Used in `not_assessed` state.
- `Question.teachingTree` — per-question teaching aid. Helps a stuck student on a specific question. Stays within the concept. Used in `learning` and mastery states.
Ruled out: one unified tree — probing and teaching have different traversal goals and scope.

**`HintAction` types: `steps` (recurse), `resource` (KA video/article), `concept` (prereq redirect), `inline` (explanation), `question` (return to original).**
`inline` avoids a full resource redirect for simple arithmetic corrections — show the working inline, then ask again. `question` terminates the hint session when the student is ready. `concept` in probing tree triggers cross-concept navigation. Ruled out: single `content` field per branch — too rigid, can't recurse or route contextually.

**`idealAnswer` on every `HintStep` probe — evaluated by LLM at runtime, not exact string match.**
The tutor AI grades the student's response against `idealAnswer` to decide the branch. Free-text responses need semantic matching, not equality. LLM also generates probe language at runtime from context — only `idealAnswer + ifCorrect/ifWrong` need to be stored. Ruled out: multiple choice inside hints — telegraphs the answer; pre-authoring all probe text — too much authoring burden.

**Probing tree is stored per concept, generated once, reused across sessions.**
Storing it makes it editable and auditable. Ruled out: generate fresh each session — burns tokens and loses refinements.

---

## Student Concept State

**`LearningJourneyNode` merges `StudentConceptState` — one entity tracks both journey position and concept progress.**
A node already has journeyId, conceptId, and order. Adding state fields (state, masteryLevel, probingPath) to the node makes it the single source of truth. Ruled out: separate `StudentConceptState` collection — duplicate entity with the same key (student × concept), adds a join for no benefit.

**State per journey node, not per student × concept globally.**
The same concept can appear in multiple journeys (e.g. "CBSE prep" and "JEE prep") with different state per journey. State is contextual to the journey objective. Ruled out: global state per student × concept — a student may have different mastery in different learning contexts.

**Three question roles per concept: `probingTree`, `masteryQuestions[]`, `examQuestions[]`.**
Previously a flat `questions[]` bank — no way to know which question serves which purpose. Mastery questions are ordered lots → mots → hots. Exam questions are a subset of mastery questions where `appearedInExams` is non-empty. Ruled out: separate collections — questions are already top-level, role is contextual.

**`Concept.misconceptions[].prereqConcept` links a misconception to the prerequisite concept it traces back to.**
The probing tree uses this to route `ifWrong` to the right prereq concept, not just to a generic question. Ruled out: storing the prereq only on the HintStep node — loses the structural relationship for querying.

**`TeachingPlan.content` is free text — no structured branching.**
The agent writes and rewrites a plain-text plan each turn. Branching lives in the LLM's reasoning, not in the data structure. Ruled out: DAG with conditional edges, flat list with onSuccess/onFailure pointers — over-engineered for current stage; adds schema complexity without proven need. Can be structured later if navigation becomes hard to manage in text.

**`Memory.type: factual | reflected` — two distinct observation types.**
Factual: what the child knows. Reflected: what the child consistently struggles with. Different types are loaded and weighted differently by the agent. Ruled out: single `notes` string — loses the distinction between capability and difficulty pattern.

---

## Agent — LLM

**Gemini Flash (`@google/genai` 2.x) over Anthropic.**
`@google/genai` 2.x sends tool responses as `role: 'user'` (correct). The older `@google/generative-ai` 0.x SDK sent `role: 'function'` which Gemini Flash rejects with a 400. Ruled out: Anthropic — switched to meet product requirement.

**TurnEngine is stateless — new chat object created on every turn.**
Full conversation history is replayed to Gemini on every call via `ai.chats.create({ history })`. No persistent chat object held between turns. Ruled out: stateful chat — complicates session resume and makes the engine harder to reason about.

**Gemini history must start with a `user` role entry.**
If the agent speaks first (initiate), there is no prior student message. A synthetic `{ role: 'student', content: 'Begin the session.' }` is seeded into history before the first turn. Ruled out: sending empty history — Gemini rejects it.

**`systemInstruction` is separate from history.**
Gemini has a dedicated `config.systemInstruction` field — not a `system` role message in history. This means it is not subject to the history ordering constraint.

**Within-turn `systemInstruction` is fixed — ctx swaps take effect on next turn.**
Gemini's `systemInstruction` is set at `ai.chats.create()` time and cannot change during the agentic tool-call loop. If a prereq redirect fires mid-turn and swaps `ctx`, the new skill prompt is not loaded until the next call to `TurnEngine.run()`. The LLM is told to end its turn; the transport auto-advances to trigger the next turn with the new skill. Ruled out: changing systemInstruction mid-turn — not possible with the SDK; ruled out: expecting LLM to load the new plan itself from the redirect return value — LLM ignores structured signals, only reads prose.

---

## Agent — Session Lifecycle

**Session status: `initialised → started → completed` — not `in_progress`.**
A session is created (`initialised`) before the agent runs. If the agent crashes or the user exits immediately, the session is never meaningfully started. Only sessions where the agent produced at least one text response are marked `started`. Only `started` sessions are resumed on re-run. `initialised` sessions are silently dropped on exit. Ruled out: `in_progress` as the creation status — creates zombie sessions on crash.

**Session persisted fire-and-forget after every turn.**
`SessionManager` calls `persistSession(ctx)` after each `initiate()` and `send()` without awaiting the result. This writes `history`, `planHistory`, and `teachingPlan` to LP after every turn, giving crash recovery without adding turn latency. Ruled out: awaiting persist — adds latency; ruled out: writing only on clean exit — history lost if session crashes mid-session.

**Plan compiled fresh each session — not persisted to DB.**
`concept.probingTree` / `concept.lessonPlan` is compiled into a `PlanStep[]` at session start. The compiled plan lives in memory for the session duration. Ruled out: storing compiled plan in DB — adds schema complexity; source data is already persisted.

**`Session.planHistory` tracks which concepts and plans have been visited.**
When a prereq redirect fires, the prereq concept's plan is appended to `planHistory` as a `PlanHistoryEntry { conceptId, conceptTitle, plan, startedAt }`. The same happens when returning to the origin concept. This gives a full audit trail of what was taught across concept hops without storing the plan in the journey node. Ruled out: storing plan in journey node — plan is session-scoped, not node-scoped; one node may be visited in multiple sessions with different plans.

---

## Agent — Architecture

**Transport abstraction — `Transport` interface with `StdinTransport` first.**
All I/O goes through a `Transport` interface. A WebSocket transport can be added without touching agent or session manager code. Ruled out: hardcoding stdin/stdout in agent — couples I/O to business logic.

**Two output channels on Transport: `handle()` and `onLog()`.**
`handle(event: TurnEvent)` carries conversation events (text, tool calls, errors) — always shown, no filtering. `onLog(entry: LogEntry)` carries operational logs (connect, disconnect, state transitions, debug) — filtered by log level per transport. Ruled out: single channel — can't suppress debug noise without also suppressing agent errors; ruled out: `console.log` directly in agent code — bypasses transport abstraction entirely.

**`action` TurnEvent — transport-level signal, not session-manager concern.**
When `update_step` fires a prereq redirect, it returns `action: { type: 'send-ok' }`. The engine yields a `{ type: 'action', action }` event. The transport decides what to do — `StdinTransport` auto-sends "Ok" after the turn to advance. Session-manager does not see or handle action signals. Ruled out: session-manager handling auto-advance — transport is the right boundary for I/O behavior decisions; ruled out: returning nextStep from redirect — LLM is within-turn and can't load a new system prompt.

**`ctx.log` is dependency-injected by `SessionManager.join()`.**
`AgentContext` has a `log: (entry: LogEntry) => void` field, defaulting to a no-op in `buildContext`. `join()` wires it to `entry => transport.onLog(entry)`. Any agent code (engine, tools, skills) calls `ctx.log(...)` without knowing the transport. Ruled out: passing transport directly to agent — creates a hard dependency; ruled out: a global logger — breaks transport isolation for multi-session servers.

**Transport method names: `handle` (not `send`), `onLog` (not `log`).**
`send` implied a one-way push. `handle` matches the event-handler mental model — the transport decides what to do with the event. `onLog` mirrors `on('message')` naming style (observer pattern). Ruled out: keeping `send` — misleading when a transport might queue, buffer, or drop events.

**ANSI colour codes for log levels — no library.**
`\x1b[90m` (gray/debug), `\x1b[36m` (cyan/info), `\x1b[33m` (yellow/warn), `\x1b[31m` (red/error). Direct escape codes, no chalk/kleur dependency. Ruled out: chalk — adds a dependency for three lines of code.

**Gemini SDK: check `response.functionCalls` before accessing `response.text`.**
Accessing `.text` when function calls are present triggers a noisy SDK warning. Engine now checks `const calls = response.functionCalls` first; `.text` is only accessed when `calls` is empty. Ruled out: suppressing the warning — symptom fix, not root cause.

**SessionManager holds sessions in-memory — not DB-backed.**
Active sessions live in a `Map<sessionId, { agent }>`. DB is only read at create and written at end. Ruled out: querying LP on every turn — adds latency; session state during a turn is transient.

**`prompt()` called via `.finally()` after connected handlers complete.**
`StdinTransport.start()` fires connected handlers and waits for them (agent initiates first), then calls `prompt()` to open input. `.finally()` ensures `prompt()` is always called even if initiation errors. Ruled out: calling `prompt()` before connected handlers — input prompt appears before agent speaks; calling `prompt()` only in `.then()` — errors silently suppress the input prompt.

---

## Agent — Journey Navigation

**`LearningJourneyNode.goTo` set on creation from `concept.nextConcepts[0]`.**
Every node knows its linear next destination before any session begins. When the agent finishes a concept, it reads `goTo` rather than querying the concept graph. Ruled out: looking up `nextConcepts` at completion time — requires an extra CMS fetch; ruled out: leaving `goTo` null until needed — loses the connection if the concept graph changes later.

**Prereq redirect creates a new node with `goTo` pointing back to the originating concept.**
When the probing tree identifies a prerequisite gap (`{ type: "teach", conceptId: X }`), a node for X is created with `goTo = originatingConcept`. After X is done, the agent follows `goTo` to return. The originating node's state is set to `learn-pre-req-before` and `preReqToLearn = X` while waiting. Ruled out: storing return pointers only in session history — lost on crash/resume; ruled out: a single global `goTo` field on the journey — multiple concurrent prereq detours not possible.

**Prereq node starts in `learning` state — not `not_assessed`.**
When the probing tree says `{ type: "teach", conceptId: X }`, it has already diagnosed that the student needs to learn X. Creating the prereq node in `not_assessed` would re-run the probing tree for X unnecessarily. Starting in `learning` skips re-assessment and goes straight to the lesson plan. Ruled out: `not_assessed` — double-probing a concept already diagnosed as a gap.

**Probing tree already encodes which prereq to redirect to — no new data on `Concept`.**
`HintAction { type: "teach", conceptId }` in the probing tree already names the target concept. The agent reads `conceptId` from the tree node and creates/finds the prereq journey node. No new `prereqConceptId` field needed on `Concept`. Ruled out: storing prereq redirect targets separately — duplicates information already in the probing tree.

**`lessonPlan.resources` stored as String (kaSlug) refs, not ObjectId.**
KA import stores resource IDs as kaSlug strings (e.g. `"intro-to-two-variable-linear-equations"`). Mongoose populate with ObjectId refs silently drops mismatches. Changed Mongoose schema to `[{ type: String, ref: 'Resource' }]` with `.populate({ path: 'lessonPlan.resources', foreignField: 'id' })`. No re-import needed — data was correct, schema was wrong. Ruled out: re-importing with ObjectId refs — unnecessary churn; ruled out: keeping ObjectId — Mongoose silently drops strings, resources never populate.

**`returnToOrigin` always patches state — never leaves node in `learn-pre-req-before`.**
Original code only cleared `preReqToLearn`; it left `journeyNode.state` unchanged. If `resumeStep` is in the origin session's planHistory, state is set to `assessing` (probe in progress — plan's redirect steps decide final state). Otherwise `learning`. Ruled out: leaving state as `learn-pre-req-before` — no valid plan exists for that state; ruled out: always setting `learning` — if returning mid-probe, `assessing` is the correct state.

---

## Agent — Medium Architecture

**Output modalities over plain text protocol — structured output, not conversation.**
LLM writes keyword lines (`speak:`, `write:`, `model:`, `camera:`) in its text response. `OutputParser` scans line-by-line and routes to the registered modality. Ruled out: tool calls for each output action — too many round trips, breaks the streaming experience; ruled out: JSON output — harder to prompt, breaks natural language flow.

**`camera: open` as an output modality, not a tool.**
Camera open is a presentation command (output direction), not a side-effecting action that needs a result. Fits the existing output modality pattern — LLM writes `camera: open` inline, parser emits `open-camera` action, canvas opens camera. Ruled out: a `request_camera` tool — unnecessary tool call round-trip for a pure presentation signal.

**`send-ok` action breaks the LLM loop on prereq redirect.**
When `update_step` fires a prereq redirect, the tool result already contains the next step — the LLM has everything it needs. Feeding the result back to the LLM would generate redundant text. Engine detects `send-ok` in the result, emits the action, and breaks the loop. Transport auto-sends "Ok" to trigger the next turn. Ruled out: letting the LLM generate a response — duplicates content; ruled out: a new session — session continuity is needed for plan history.

---

## Agent — Mastery Phase

**Markdown plans (`mastery.md`, `teach.md`, `probe.md`) take precedence over DB-compiled plans.**
Content authors write plans as markdown files in `cms/content/{conceptId}/`. Agent checks for these files at session start and uses them if present. DB-compiled plans remain the fallback. Ruled out: DB-only plans — too rigid for per-concept teaching variation; ruled out: markdown-only — some concepts have no authored plan yet.

**`questions.json` filesystem file preferred over DB `masteryQuestions`.**
DB `masteryQuestions` is empty for most concepts; authoring questions as JSON in the content folder is faster and easier to iterate. Agent checks `cms/content/{conceptId}/questions.json` first, falls back to CMS API. Ruled out: DB-only — cumbersome to author, no tooling yet; ruled out: embedding questions in `mastery.md` — unstructured, `get_next_question` can't consume them.

**Checkpoint state (`clarity`) transitions to mastering in-session — no new session required.**
When `update_step` reaches a checkpoint (e.g. `clarity`), `transitionState` is called. If the next state is a transition state (`mastering`), the plan is rebuilt and `ctx.practice` is loaded within the same session. The student continues without a break. Ruled out: always ending session at checkpoint — forces an unnecessary reconnect and breaks the teaching flow.

---

## ERP — V1 Scope

**No mobile verification in v1.** Adults complete onboarding without a phone check. Saves Firebase phone auth complexity for now; can be added later with no data model change.

**Open classroom join — no approval step.** All classrooms default to `open`. Student submits class code → enrolled immediately. Saves the pending-state UI and teacher approval flow for v1. Default will be reconsidered before wider rollout.

**No Firebase custom tokens for student login in v1.** `POST /auth/student` returns `{ studentId, name }` directly — no Firebase exchange. Canvas stores `studentId` in memory (or localStorage on "remember me"). Firebase custom token flow is a later iteration.

**bcrypt for access codes, not HMAC.** Full spec calls for keyed HMAC + out-of-DB key. bcrypt is simpler, no key management, and good enough for v1. Migrate to HMAC when operating at scale.

**ERP runs as a separate Express service at port 32005.** Same MongoDB deployment as CMS/LP but separate collection namespace (`erp_` prefix). Ruled out: adding ERP routes to CMS backend — keeps concerns separate; ruled out: a shared user collection with CMS — CMS has no user concept today.

---

## ERP — Multi-session WebSocket

**`MultiSessionServer` added to `agent/src/transports/ws.ts` — not a new file.** Keeps `cli.mjs` working unchanged (it uses `WebSocketTransport` directly). The new class is a second export from the same module. Ruled out: new file — unnecessary; ruled out: modifying `WebSocketTransport` — it's 1:1 by design and cli.mjs depends on it.

**Session created over HTTP before WebSocket connects.** `POST /sessions` runs `SessionManager.create()` and returns a `sessionId`. The WS then connects with `?sessionId=xxx` and calls `SessionManager.join()`. Ruled out: first-message handshake (send studentId on connect) — HTTP gives a proper response code and error message; ruled out: studentId in WS URL — exposes identity in server logs and proxies.

**Each WS connection gets its own `PerConnectionTransport`.** `SessionManager.join()` accepts a `Transport` — passing a per-connection object means sessions are fully isolated. No shared state between connections. Ruled out: one transport object shared across connections — impossible, `handle()` would broadcast to all sockets.

[← Back to index](prodigy.md)
