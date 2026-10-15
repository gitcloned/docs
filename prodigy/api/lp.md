# API — Learning Progression Service

Endpoint contracts for the LP service (port 3002).

No auth. All endpoints return JSON.

---

## Journeys

### `GET /students/:studentId/journeys`
All learning journeys for a student.

**Returns:** `LearningJourney[]`

---

### `POST /students/:studentId/journeys`
Create a new learning journey for a student.

**Body:**
| Field | Type | Notes |
|---|---|---|
| `objective` | string | e.g. "Learn mathematics" |

**Returns:** `LearningJourney`

---

### `GET /journeys/:id/nodes`
All journey nodes for a given journey.

**Returns:** `LearningJourneyNode[]`

---

## Journey Nodes

### `GET /journey-nodes`
Query journey nodes.

**Query params:**
| Param | Notes |
|---|---|
| `journeyId` | Filter by journey |
| `conceptId` | Filter by concept |

**Returns:** `LearningJourneyNode[]`

---

### `GET /journey-nodes/:id`
Single journey node by id.

**Returns:** `LearningJourneyNode`

---

### `POST /journey-nodes`
Create a new journey node.

**Body:**
| Field | Type | Notes |
|---|---|---|
| `journeyId` | string | |
| `conceptId` | string | KA slug |
| `order` | number | Position in journey |
| `state` | ConceptState | Initial: `not_assessed` |
| `masteryLevel` | enum \| null | `lots \| mots \| hots \| null` |

**Returns:** `LearningJourneyNode`

Unique index: `{ journeyId, conceptId }` — no duplicate nodes per journey.

---

### `PATCH /journey-nodes/:id`
Update a journey node (state transition).

**Body:** partial — any fields to update (e.g. `{ state: 'learning' }`)

**Returns:** `LearningJourneyNode`

---

## Sessions

### `GET /students/:studentId/sessions`
Sessions for a student.

**Query params:**
| Param | Notes |
|---|---|
| `conceptId` | Filter by concept |
| `status` | `initialised \| started \| completed` |

**Returns:** `Session[]`

---

### `POST /sessions`
Create a new session.

**Body:**
| Field | Type | Notes |
|---|---|---|
| `studentId` | string | |
| `conceptId` | string | |
| `journeyNodeId` | string | |
| `status` | string | `initialised` on creation |
| `conceptStateAtStart` | ConceptState | |
| `conceptStateAtEnd` | ConceptState \| null | null on creation |
| `teachingPlan` | object | `{ content: '', createdAt, updatedAt }` |
| `history` | array | `[]` on creation |
| `memory` | array | `[]` on creation |
| `createdAt` | date | |
| `endedAt` | date \| null | null on creation |

**Returns:** `Session`

---

### `PATCH /sessions/:id`
Update a session (status transition, history flush, state end).

**Body:** partial — common patterns:
```
{ status: 'started' }                               ← agent first response
{ conceptStateAtEnd: 'learning' }                   ← after advance_state tool
{ status: 'completed', history: [...], endedAt }    ← on session end
```

**Returns:** `Session`

---

### `POST /sessions/:id/messages`
Append a message to session history.

**Body:**
| Field | Type | Notes |
|---|---|---|
| `role` | string | `student \| agent` |
| `content` | string | Message text |

**Returns:** updated `Session`

---

## Memories

### `GET /students/:studentId/memories`
All memories for a student.

**Query params:**
| Param | Notes |
|---|---|
| `conceptId` | Filter by concept |

**Returns:** `Memory[]`

---

### `POST /students/:studentId/memories`
Create a new memory observation.

**Body:**
| Field | Type | Notes |
|---|---|---|
| `context` | object | `{ conceptId?: string, strandId?: string }` |
| `type` | string | `factual \| reflected` |
| `content` | string | The observation text |

**Returns:** `Memory`

---

[← Back to index](../prodigy.md)
