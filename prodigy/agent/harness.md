# Agent — Harness

TurnEngine, SessionManager, AgentContext, and the agent loop.

---

## AgentContext

Loaded once at session start via `buildContext()`. Passed to every tool and skill.

| Field | Type | Source |
|---|---|---|
| `session` | `Session` | LP — resumed or newly created |
| `concept` | `Concept` | CMS — fetched by conceptId |
| `journeyNode` | `JourneyNode` | LP — fetched by journeyNodeId |
| `memories` | `Memory[]` | LP — loaded by studentId + conceptId |
| `plan` | `PlanStep[]` | Compiled fresh — never persisted directly (saved to planHistory) |
| `modelPrompt` | `string` | Extra prompt fragment from markdown plan model declarations |
| `practice` | `PracticeExercise \| undefined` | Loaded when state is `mastering` and questions exist |

`concept`, `journeyNode`, `plan`, and `practice` are swapped in-memory when a prereq redirect fires mid-session. The swap is transparent to the LLM — it takes effect on the next turn via `skills.get(ctx.journeyNode.state)`.

**Plan built by state:**
- `not_assessed` → `probe.md` (markdown) if present, else compiled from `concept.probingTree`
- `learning` → `teach.md` (markdown) if present, else compiled from `concept.lessonPlan`
- `mastering` → `mastery.md` (markdown) if present, else flat mastery question plan
- `clarity` → same as `mastering` (checkpoint — loads mastery plan; transitions in-session)

**Practice questions loaded by priority:**
1. `cms/content/{conceptId}/questions.json` — filesystem JSON (preferred)
2. `/concepts/{conceptId}/mastery-questions` — CMS DB (fallback)

---

## TurnEngine

`src/engine.ts` — stateless Gemini loop. Called once per agent turn.

```
TurnEngine.run(skill, ctx)
      │
      ├─ build toolDefs from skill.tools (filtered from registry)
      ├─ map ctx.session.history → Gemini Content[]
      │     chatHistory = all but last entry
      │     lastMessage  = last entry text
      │
      ├─ ai.chats.create({
      │     model:  'gemini-2.5-flash',
      │     history: chatHistory,
      │     config: {
      │       systemInstruction: basePrompt + skill.prompt(ctx),
      │       tools: [{ functionDeclarations: toolDefs }]
      │     }
      │   })
      │
      └─ agentic loop:
           response = chat.sendMessage({ message: lastMessage })
           while true:
             yield text if present
             if no functionCalls → break
             for each call:
               yield tool_call
               result = tool.run(args, ctx)
               yield tool_result
               if result.action → yield action
             response = chat.sendMessage({ message: toolResults })
```

**Key constraints:**
- Gemini history must start with a `user` role entry — synthetic `'Begin the session.'` seeded on first turn
- Engine is fully stateless — creates a fresh chat object on every call using full history replay
- `systemInstruction` is a separate field, not a history entry
- `systemInstruction` is fixed for the duration of a turn's agentic loop — ctx swaps mid-turn take effect on the next call to `TurnEngine.run()`

---

## SessionManager

`src/session-manager.ts` — in-memory session store. Holds one entry per active session.

```ts
Map<sessionId, { agent: Agent; resumed: boolean }>
```

**Methods:**

| Method                         | What it does                                                                    |
| ------------------------------ | ------------------------------------------------------------------------------- |
| `create(studentId, conceptId)` | LP: find/create Journey → JourneyNode → buildContext → newAgent                 |
| `join(sessionId, transport)`   | Wires transport events to agent. Agent speaks first on 'connected'.             |
| `end(sessionId)`               | If started: PATCH session to LP (history + status: completed). Remove from map. |
| `getAgent(sessionId)`          | Return agent for a session (used by CLI to read ctx)                            |
| `isActive(sessionId)`          | Check if session is still in map                                                |
|                                |                                                                                 |

**Resume logic** (`buildContext`):
- Queries LP for sessions with `status: started` for this student × concept
- If found: reuses that session record (history loaded from LP)
- If not: creates a new session with `status: initialised`

**Per-turn session persist (fire-and-forget):**
After each `initiate()` and `send()` turn, `SessionManager` calls `persistSession(ctx)` without awaiting the result. This writes `history`, `planHistory`, and `teachingPlan` to LP after every turn. Ruled out: awaiting the persist — adds latency per turn.

---

## Agent

`src/agent.ts` — thin wrapper exposing `initiate()` and `send()`.

```
newAgent(studentId, conceptId, journeyNodeId)
  → buildContext()
  → returns { ctx, initiate(), send() }

initiate()
  → seed history with 'Begin the session.' if empty
  → turn()

send(content)
  → history.push({ role: 'student', content })
  → turn()

turn()  [async generator]
  → skill = skills.get(ctx.journeyNode.state)   ← re-evaluated each turn
  → for each event from engine.run(skill, ctx):
       if text: accumulate agentText
                on first text: PATCH session status → 'started' (once only)
       yield event
  → history.push({ role: 'agent', content: agentText })
```

Skill is re-evaluated at the top of every turn — `ctx.journeyNode.state` reflects any swaps from the previous turn's redirect.

---

## Plan — PlanStep

In-memory plan compiled from concept data. Not persisted to DB.

| Field | Type | Notes |
|---|---|---|
| `id` | number | Sequential, 1-based |
| `content` | `Record<string, unknown>` | Shape varies by type (see below) |
| `status` | enum | `pending \| in_progress \| done` |
| `outcome` | enum | `pass \| fail \| not_sure` — set when done |
| `type` | enum | `probe \| teach \| inline \| practice \| resource \| store_memory \| advance_state` |
| `ifCorrect` | `number \| null` | Next step id on pass or not_sure |
| `ifWrong` | `number \| null` | Next step id on fail |

**Content shapes by type:**

| Type | Content fields |
|---|---|
| `probe` | `{ question, idealAnswer }` |
| `teach` | `{ conceptId, conceptTitle, reason? }` |
| `inline` | `{ explanation }` |
| `practice` | `{ lessonType, question, questionId, learningIndicator }` |
| `resource` | `{ lessonType, instruction?, resources: [{ id, title, youtubeUrl, url }] }` |
| `store_memory` | `{ instruction }` |
| `advance_state` | `{ instruction, targetState }` |

---

## Markdown plan builder (v2)

`src/learning/plan-builder-v2.ts` — content-first plan authoring. Markdown files in `cms/content/{conceptId}/` take precedence over DB-compiled plans.

**File detection order:**

| File | Checked for state |
|---|---|
| `probe.md` | `not_assessed` |
| `teach.md` | `learning` |
| `mastery.md` | `mastering`, `clarity` |
| `questions.json` | loaded into `PracticeExercise` when state is `mastering` |

**Markdown plan format:**

```markdown
# Plan title
# Models: function-graph     ← optional — adds model prompt fragment

## 1 (Step name)
Step instruction text here.
redirect: other-concept-id   ← prereq redirect
mode: teach
reason: Why we're going there
then: 3                      ← resume at step 3 after redirect

## 2 (Another step)
store_memory: true           ← creates store_memory step
```

Each `##` heading is one step. `(name)` in parens is the step name. Key-value lines (`redirect:`, `mode:`, `state:`, `practice:`, `then:`) define step behaviour. Prose lines become `content.instruction`.

**`questions.json` format:**
```json
[
  {
    "id": "q1", "order": 1, "type": "open",
    "difficulty": "hard", "score": 3,
    "stem": "Question text shown to student",
    "idealAnswer": "Expected answer for agent reference",
    "stepsToSolve": ["Step 1", "Step 2"],
    "hints": ["Hint 1"],
    "writingHint": "How to write steps on canvas"
  }
]
```

---

## transitionState

`src/tools/state.ts` — advances `journeyNode.state` at plan end. Called by `update_step` when a plan exhausts or a redirect step completes.

```
transitionState(ctx)
  → whatIsNext(currentNode.state, supportedPhases)
  → patch journeyNode + session in LP
  → switch on result.typeOfMove:
       advance-state:
         if isTransitionState(newState) → rebuild ctx.plan, ctx.practice in-session → return true
         else (checkpoint) → return false  (session ends)
       go-to-origin → returnToOrigin()
       go-to-next-concept → return false
```

**In-session state transitions** — when `clarity → mastering`, the plan is rebuilt within the same session without requiring a new connection. `ctx.practice` is also populated at this point from `questions.json` or DB.

---

## Plan compilation (legacy — DB-compiled)

`src/learning/plan-builder.ts` builds plans from DB data when no markdown file exists:

### Probing plan (`not_assessed`)

Compiles `Concept.probingTree` into a flat step array with navigation pointers.

```
entryQuestion (step 1)
  ifCorrect → store_memory    (student already knows it)
  ifWrong   → nodes[0] (step 2)   (diagnose gap)

nodes[0] (step 2)
  ifCorrect → nodes[0].ifCorrect branch
  ifWrong   → nodes[0].ifWrong branch

... (recursive)

all terminal branches → store_memory → advance_state
```

- `entryQuestion` is a Perseus widget — extracted to `{ question, idealAnswer, perseusContent }`
- `teach` nodes compile to a `teach` step; `update_step` handles the redirect internally
- `inline` nodes show an explanation inline then continue
- All `null` branch pointers are wired to `store_memory` at compilation time

### Teaching plan (`learning`)

Compiles `Concept.lessonPlan` into resource + practice step pairs.

```
sort lessonPlan: ido → wedo → youdo

for each lesson step:
  1. resource step (if resources attached) OR teach step (instruction only)
  2. practice step (from assessmentQuestion → learningIndicator → masteryQuestion fallback)

end: advance_state → clarity
```

---

[← Back to index](../prodigy.md)
