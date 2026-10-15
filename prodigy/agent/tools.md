# Agent — Tools

All callable tools the agent can invoke during a session.

---

## Tool registry

`src/tools/index.ts` — `ToolRegistry` holds all tools. Each skill declares which subset it may use via `tools:` frontmatter. The engine only exposes those tools to Gemini for that turn.

---

## Plan tools

### `read_plan`

Read the full compiled plan for this session.

- **Args:** none
- **Returns:** `{ plan: string }` — all steps formatted as `[status] id. (type) content → pass:N → fail:N`
- **When to call:** At session start to understand the teaching plan.

---

### `get_next_step`

Get the current `in_progress` step (or next `pending` if none in progress).

- **Args:** none
- **Returns:** `{ step: { id, type, content } }` or `{ done: true, message }`
- **When to call:** At the start of each turn to know what to do next.

```
if done: true → all steps complete, close the session
```

**Content shape by type:**

| Type | Fields in `content` |
|---|---|
| `probe` | `question`, `idealAnswer` |
| `teach` | `conceptId`, `conceptTitle`, `reason` (optional — why this prereq) |
| `inline` | `explanation` |
| `practice` | `lessonType` (ido/wedo/youdo), `question`, `questionId`, `learningIndicator` |
| `resource` | `lessonType`, `instruction`, `resources[]` (id, title, youtubeUrl, url) |
| `store_memory` | `instruction` |
| `advance_state` | `instruction`, `targetState` |

---

### `update_step`

Mark the current step done and advance the plan. Handles state transitions, prereq redirects, and resource delivery internally — you never call advance_state or redirect_to_prereq separately.

- **Args:** `{ id: number, outcome: 'pass' | 'fail' | 'done' | 'not_sure' }`
  - `done` — for non-interactive steps (`store_memory`, `advance_state`, `resource`)
  - `pass` / `fail` — after student answers a question
  - `not_sure` — treated the same as `pass` for navigation
- **Returns (normal):** `{ ok, nextStep }` or `{ ok, allDone: true }`
- **Returns (prereq redirect):** `{ ok: true, action: { type: 'send-ok' }, message }` — ctx swapped internally; end your turn, next turn loads the prereq plan
- **Returns (state advance):** `{ ok, state, concept, nextStep, message }` — when an `advance_state` step completes, next concept plan is loaded

**Navigation:**
```
outcome == 'fail'                → follow step.ifWrong
outcome == 'pass' | 'not_sure'  → follow step.ifCorrect
outcome == 'done'               → follow step.ifCorrect
```

**Internal side-effects (transparent to agent):**

| Step type | What update_step does internally |
|---|---|
| `advance_state` | Calls `transitionState()` — PATCHes journey node state, may swap ctx to origin concept |
| `teach` (with conceptId) | Calls `redirectToPrereq()` — creates prereq node, swaps ctx, appends planHistory |

`nextStep` has the same shape as `get_next_step` returns. The agent follows that instruction next.

---

---

## Practice tool

### `get_next_question`

Drive a practice exercise question by question. Used only in the mastering skill when `ctx.practice` is loaded.

- **Args:** `{ outcome?: 'pass' | 'fail' | 'not_sure' }` — omit on first call or when rereading; pass outcome only when the full question attempt is finished
- **Returns (question):** `{ done: false, index, total, question: { id, stem, idealAnswer, type, difficulty, score, stepsToSolve[], hints[], writingHint } }`
- **Returns (done):** `{ done: true, message, summary: { total, passed, failed } }`

**Question loop:**
```
get_next_question()                      ← first call, no outcome
  → present stem to student
  → student attempts, agent helps via stepsToSolve / hints
  → when finished: get_next_question({ outcome: 'pass' })
  → repeat until done: true
  → update_step(id, 'pass'|'fail')
```

`stepsToSolve` — ordered teaching steps for this question. Agent follows these only; does not invent steps.
`hints` — release one at a time, only when student is stuck after a genuine attempt.
`writingHint` — how to write working on the canvas (e.g. "keep equation on left, annotate terms").

---

## State tool

*`advance_state` is now handled internally by `update_step` — it is no longer a standalone agent tool.*

---

## Memory tool

### `store_memory`

Persist an observation about the student for future sessions.

- **Args:** `{ type: 'factual' | 'reflected', content: string }`
- **Returns:** `{ ok: true }`
- **Side effects:** `POST /students/:studentId/memories`

| Type | When to use |
|---|---|
| `factual` | What the student knows — "understands substitution into two-variable equations" |
| `reflected` | Consistent struggle — "confuses which value is x and which is y in ordered pairs" |

Memories are loaded at the start of every subsequent session for the same concept.

---

## Tool call flow (Gemini)

```
Gemini decides to call get_next_step
      │
      ▼
TurnEngine intercepts functionCalls from response
      │
      ├─ yields { type: 'tool_call', name: 'get_next_step', args: {} }
      ├─ tool.run({}, ctx) → { step: { id: 1, type: 'probe', content: {...} } }
      ├─ yields { type: 'tool_result', name: 'get_next_step', result: {...} }
      │    if result contains .action → also yields { type: 'action', action }
      └─ sends result back to Gemini → next response
```

Unknown tool name → `{ error: 'unknown tool: <name>' }` returned to Gemini.

---

[← Back to index](../prodigy.md)
