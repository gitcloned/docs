# Agent — Skills

Skill system, SKILL.md format, and available skills.

---

## What a skill is

A skill is a prompt mode + tool allowlist for one concept state. The active skill is chosen by `LearningJourneyNode.state` at the start of each turn.

One skill active per turn. Skills do not overlap.

---

## SkillLoader

`src/skills.ts` — scans `skills/` directory at startup.

```
skills/
  probing/SKILL.md      → state: not_assessed
  teaching/SKILL.md     → state: learning      (not yet created)
  mastery/SKILL.md      → state: clarity        (not yet created)
  ...
```

Each subfolder must contain a `SKILL.md` with YAML frontmatter.

---

## SKILL.md format

```markdown
---
name:  Concept Probing
state: not_assessed
tools: get_next_step, update_step, store_memory, advance_state, read_plan
---

You are a warm, patient tutor working with {{concept.title}}.

## Your plan
{{plan}}

## Student memory
{{memories}}

## Probing tree (reference only)
{{probingTree}}
```

**Frontmatter fields:**

| Field | Type | Notes |
|---|---|---|
| `name` | string | Human-readable name |
| `state` | ConceptState | The concept state this skill handles |
| `tools` | comma-separated | Which tools the agent may call this turn |

**Template variables:**

| Variable | Replaced with |
|---|---|
| `{{concept.title}}` | Concept title string |
| `{{plan}}` | Formatted plan steps (`[status] id. content`) |
| `{{memories}}` | Bulleted memory list, or "None yet." |
| `{{probingTree}}` | Full `probingTree` JSON (reference for agent) |

---

## Skill → state mapping

| Concept state | Skill folder | Status |
|---|---|---|
| `not_assessed` | `probing/` | Implemented |
| `assessing` | `probing/` | Same skill as not_assessed |
| `learning` | `learning/` | Implemented |
| `mastering` | `mastering/` | Implemented |
| `clarity` | `mastering/` | Same skill — in-session transition to mastering |
| `mastered` | — | Not yet created |
| `exam_ready` | — | Not yet created |

Missing skills throw at runtime: `No skill registered for state: <state>`.

---

## Probing skill — what it does

File: `skills/probing/SKILL.md`

The probing skill follows the compiled plan step by step:

```
Turn start:
  get_next_step → read current in_progress step

  if step.type == 'probe':
    present the question to student
    student answers
    update_step(id, outcome)  → agent gets next step

  if step.type == 'teach':
    tell student to review conceptTitle first
    update_step(id, 'pass')

  if step.type == 'store_memory':
    store_memory(type, content)
    update_step(id, 'pass')

  if step.type == 'advance_state':
    advance_state(state: 'learning', summary)
    update_step(id, 'pass')

  if done == true:
    close out the session
```

The agent follows the plan strictly — it does not navigate the plan itself. The `update_step` tool returns the next step.

---

## Learning skill — what it does

File: `skills/learning/SKILL.md` — state: `learning`

Tools: `get_next_step`, `update_step`, `store_memory`

Follows the teaching plan step by step. For each step: present resource or practice question, wait for student response, call `update_step` with outcome. Higher bar than probing — requires the student to show working.

---

## Mastering skill — what it does

File: `skills/mastering/SKILL.md` — state: `mastering`

Tools: `get_next_step`, `update_step`, `store_memory`, `get_next_question`

Challenges the student to apply the concept under pressure — harder problems, less scaffolding.

**Step types handled:**

| Type | Behaviour |
|---|---|
| `probe` | Ask mastery question. No hints upfront. Intervene only if completely stuck. |
| `practice` | Run `get_next_question` loop. One question per message. Follow `stepsToSolve` and `hints` from the question. |
| `store_memory` | Call `store_memory` with observed strengths/gaps. Then `update_step(id, 'done')`. |

**Practice loop:**
```
get_next_question()
  → present stem → student attempts
  → get_next_question({ outcome })  ← records + advances
  → repeat until done: true
  → update_step(id, 'pass'|'fail')
```

Rules: socratic only — release one hint at a time; mark `not_sure` and move on if still stuck; never reveal `idealAnswer` before attempt.

---

[← Back to index](../prodigy.md)
