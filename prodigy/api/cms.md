# API — CMS Backend

Endpoint contracts for the CMS backend (port 3001).

*Not yet fully documented. Key endpoints used by the agent listed below.*

---

## Concepts

### `GET /concepts/:id`
Fetch a concept by its KA slug or MongoDB id.

**Returns:** `Concept` — includes `title`, `probingTree`, `lessonPlan`, `masteryQuestions`, `examQuestions`

---

*Additional CMS endpoints (boards, strands, units, topics, questions, resources) to be documented.*

---

[← Back to index](../prodigy.md)
