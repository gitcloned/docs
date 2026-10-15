# prodigy — Data Model

Entities, fields, and storage decisions. Database: MongoDB.

---

## Entities

### `Board`
Curriculum authority (e.g. CBSE, ICSE, IB, State Boards).

| Field | Type | Notes |
|---|---|---|
| `name` | string | e.g. "CBSE" |
| `description` | string | |

---

### `Class`
Grade/year level.

| Field | Type | Notes |
|---|---|---|
| `name` | string | e.g. "Grade 9", "Class 10" |
| `code` | string | e.g. "G9", "C10" |

---

### `Strand`
A course or major subject area. Top of the 4-level content hierarchy.

| Field | Type | Notes |
|---|---|---|
| `title` | string | e.g. "Algebra 1", "Number Sense" |
| `subject` | string | e.g. "Mathematics", "Science" |
| `weight` | number | Relative importance within subject |
| `kaSlug` | string | KA course slug — present on KA-imported strands |
| `source` | string | e.g. "khan-academy", "internal" |

---

### `Unit`
Second level of the hierarchy. Groups related topics within a strand.

| Field | Type | Notes |
|---|---|---|
| `title` | string | e.g. "Linear equations & graphs" |
| `description` | string | |
| `strand` | ref | `StrandRef` |
| `order` | number | Position within strand |
| `prerequisites` | array | `[UnitRef]` — units that should be completed first |
| `kaSlug` | string | KA unit slug |
| `source` | string | |

---

### `Topic`
Third level. A focused learning module within a unit — groups 2–6 concepts taught together.

| Field | Type | Notes |
|---|---|---|
| `title` | string | e.g. "Two-variable linear equations intro" |
| `description` | string | |
| `unit` | ref | `UnitRef` |
| `order` | number | Position within unit |
| `probingTree` | object | Optional. Topic-level `ProbingTree` — broader probe across all concepts in this topic |
| `practiceTests` | array | `[ResourceRef]` — exercise resources (practice-test type) for this topic |
| `kaSlug` | string | KA lesson slug |
| `source` | string | |

---

### `Exam`
Examination or test a question has appeared in.

| Field | Type | Notes |
|---|---|---|
| `name` | string | e.g. "CBSE Board", "JEE Mains" |
| `year` | number | |

---

### `Resource`
Teaching or practice material. Type determines which fields apply.

| Field | Type | Notes |
|---|---|---|
| `title` | string | |
| `type` | enum | `teaching-video` \| `practice-test` \| `article` \| `simulation` \| `other` |
| `source` | string | e.g. "khan-academy", "internal" |
| `description` | string | |
| `url` | string | Canonical URL (KA page or direct) |
| `kaSlug` | string | KA content slug — present on KA-imported resources |

**Type: `teaching-video`**

| Field | Type | Notes |
|---|---|---|
| `youtubeId` | string | e.g. `_LDR1_Prveo` — extracted from KA CDN download URLs |
| `youtubeUrl` | string | `https://www.youtube.com/watch?v=<youtubeId>` |
| `duration` | number | Seconds |
| `thumbnail` | string | Thumbnail image URL |
| `cfuMarkers` | array | `[{ timestamp: number, label: string, question: QuestionRef\|null }]` — populated from KA "key moments" (chapter timestamps) |

**Type: `practice-test`**

| Field | Type | Notes |
|---|---|---|
| `questions` | array | `[QuestionRef]` — ordered list |

**Type: `article`**

| Field | Type | Notes |
|---|---|---|
| `url` | string | Link to KA article or internal content |

**Type: `simulation`**

| Field | Type | Notes |
|---|---|---|
| `url` | string | |

---

### `Question`
Top-level entity. Referenced by concepts, lesson steps, misconceptions, and resources.

Two sources: **DB questions** (KA-imported or Prodigy-authored) and **`questions.json`** (filesystem, per concept — preferred for mastery practice).

**DB Question fields:**

| Field | Type | Notes |
|---|---|---|
| `type` | enum | `mcq` \| `fib` \| `subjective` \| `perseus` |
| `difficultyLevel` | enum | `lots` \| `mots` \| `hots` (Lower / Middle / Higher Order Thinking Skills) |
| `appearedInExams` | array | `[{ exam: ExamRef, link: string }]` |
| `relatedQuestions` | array | `[QuestionRef]` |

**`questions.json` — mastery practice format** (`cms/content/{conceptId}/questions.json`):

| Field | Type | Notes |
|---|---|---|
| `id` | string | Unique within the concept |
| `order` | number | Display/ask order |
| `type` | string | `open` \| `multi-part` |
| `difficulty` | string | `easy` \| `medium` \| `hard` |
| `score` | number | Max score for this question |
| `stem` | string | Question text shown to student |
| `idealAnswer` | string \| null | Agent reference only — never revealed before attempt |
| `stepsToSolve` | string[] | Ordered teaching steps — agent follows these only |
| `hints` | string[] | Released one at a time when student is stuck |
| `writingHint` | string \| null | How to write working on canvas |

Agent receives the full question object from `get_next_question` — `stepsToSolve` and `hints` guide the teaching; `idealAnswer` is for evaluation only.

**When `type` is `mcq`, `fib`, or `subjective`** (Prodigy-authored):

| Field | Type | Notes |
|---|---|---|
| `stem` | string | Question text |
| `idealAnswer` | string | |
| `steps` | array | `[SolutionStep]` — embedded |
| `teachingTree` | object | Optional. `HintStep` tree to help a stuck student — stays within this concept |

**When `type` is `perseus`** (KA-imported or Perseus-authored):

| Field | Type | Notes |
|---|---|---|
| `perseusContent` | object | Raw Perseus JSON — see below |
| `teachingTree` | object | Optional. `HintStep` tree to help a stuck student — stays within this concept |

**`perseusContent` structure:**
```
{
  content: string    // Markdown + LaTeX stem with [[☃ widget-name]] placeholders
  widgets: {         // keyed by widget name
    "<name>": {
      type: string   // one of 33 Perseus widget types (see below)
      options: object
    }
  }
  hints: array       // hint steps, each with content + widgets
}
```

**Perseus widget types (33 total):** `radio`, `numeric-input`, `expression`, `interactive-graphs`, `grapher`, `number-line`, `matrix`, `fill-in-the-blank`, `free-response`, `categorizer`, `sorter`, `matcher`, `orderer`, `plotter`, `label-image`, `measurer`, `table`, `dropdown`, `phet-simulation`, `cs-program`, `python-program`, `iframe`, `image`, `video`, `explanation`, `definition`, `group`, `graded-group`, `graded-group-set`, `interaction`, `input-number`, `blank`, `deprecated-standin`

Perseus is Khan Academy's open-source exercise renderer ([github.com/Khan/perseus](https://github.com/Khan/perseus)). A question is a content string with embedded widget placeholders — the renderer handles display and interaction.

**Embedded: `SolutionStep`** (native questions only)

| Field | Type | Notes |
|---|---|---|
| `description` | string | What this step does |
| `hint` | object | `{ whatToShow: string, whatToSpeak: string }` |

---

### `HintStep` — Two tree types

**Probing tree** (`Concept.probingTree`) — cross-concept diagnostic. Navigates backward through prerequisites to find a student's knowledge floor. Used when state is `not_assessed`.

**Teaching tree** (`Question.teachingTree`) — per-question teaching aid. Helps a student who is stuck on a specific question. Stays within the concept. Used during `learning` or mastery phases.

Both use the same `HintStep` node structure.

### `HintStep` — node structure (embedded in both tree types)

Recursive diagnostic conversation tree. Each node probes the student's understanding, branches on correct/wrong, and routes to content or deeper probing.

**Root-level `hints[]` on a Question:**

| Field | Type | Notes |
|---|---|---|
| `probe` | string | Question to ask the student |
| `idealAnswer` | string | Expected correct answer (for matching) |
| `ifCorrect` | HintAction | What to do if student answers correctly |
| `ifWrong` | HintAction | What to do if student answers incorrectly |

**`HintAction` — union type:**

| `type` | Fields | Meaning |
|---|---|---|
| `steps` | `steps: [HintStep]` | Recursive — go deeper with more probing steps |
| `inline` | `content: string`, `thenAsk?: HintStep` | Show inline explanation, optionally ask a follow-up |
| `teach` | `conceptId`, `title`, `thenAsk?: HintStep` | Teach a concept — agent runs its `lessonPlan`. Used in probing tree when child needs remediation. |
| `resource` | `resourceId`, `title`, `url`, `youtubeUrl` | Point directly to a specific resource (used sparingly — prefer `teach`) |
| `concept` | `conceptId`, `title` | Run the probing tree for a prerequisite concept (assess, not teach) |
| `question` | — | Return to the original question — student is ready to answer |

**Flow:**
```
Question.hints[]
  └─ HintStep (probe + idealAnswer)
       ├─ ifCorrect → HintAction
       │    ├─ steps → [HintStep, ...]   (recurse deeper)
       │    ├─ question                  (back to original — ready)
       │    └─ resource / concept        (send to content)
       └─ ifWrong → HintAction
            ├─ inline → content + thenAsk → HintStep
            ├─ steps → [HintStep, ...]
            └─ resource / concept
```

**Design:** Tree depth reflects prerequisite depth — a student who can't solve `x + 10 = -15` gets probed about substitution; if that also fails, gets routed to a foundational video. `ifCorrect: { type: "question" }` terminates the hint session and returns the student to the original question.

---

### `Concept`
The atomic content unit — fourth and leaf level of the hierarchy. Each concept is typically one teaching video or article, with its own lesson plan, questions, and probing tree.

| Field | Type | Notes |
|---|---|---|
| `title` | string | |
| `topic` | ref | `TopicRef` — parent topic |
| `order` | number | Position within topic |
| `conceptWeightage` | number | |
| `classApplicableTo` | array | `[ClassRef]` |
| `boards` | array | `[BoardRef]` — boards where this concept is taught |
| `prerequisites` | array | `[ConceptRef]` — concepts within the same topic that precede this one |
| `nextConcepts` | array | `[ConceptRef]` |
| `misconceptions` | array | `[{ text: string, prereqConcept: ConceptRef\|null, questions: [QuestionRef] }]` — embedded |
| `lessonPlan` | array | `[LessonStep]` — typically 1 IDo step with the teaching video/article resource |
| `probingTree` | object | Optional. `ProbingTree` — diagnostic tree for this concept. Manually authored. |
| `masteryQuestions` | array | `[QuestionRef]` — ordered lots → mots → hots |
| `examQuestions` | array | `[QuestionRef]` — questions that appeared in real exams |

**`ProbingTree` structure:**
```
{
  entryQuestion: QuestionRef     // first question asked to probe this concept
  nodes: [ProbingNode]           // embedded diagnostic tree
}
```
Each `ProbingNode` is a `HintStep` (see below) — `probe + idealAnswer + ifCorrect/ifWrong`. `ifWrong` routes to prerequisite concepts via `{ type: "concept" }` actions. Output of traversal: which concept is the student's knowledge floor.

**Embedded: `LessonStep`**

| Field | Type | Notes |
|---|---|---|
| `type` | enum | `ido` \| `wedo` \| `youdo` (extensible) |
| `instruction` | string | What the teacher does in this step |
| `resources` | array | `[ResourceRef]` — stored as kaSlug strings, not ObjectId. Mongoose populated via `foreignField: 'id'` |
| `learningIndicator` | object | `{ text: string, assessmentQuestion: QuestionRef }` |

---

### `LearningJourney`
A student's ordered path through concepts toward an objective. Concepts form a graph, but a journey flattens them to a linear sequence.

| Field | Type | Notes |
|---|---|---|
| `studentId` | ref | |
| `objective` | string | Why this journey was created — e.g. "CBSE Grade 9 Algebra", "JEE Mains prep" |
| `createdAt` | date | |

---

### `LearningJourneyNode`
One concept in a journey. Merges concept-level progress state — the single source of truth for a student's standing on a concept within a journey.

| Field | Type | Notes |
|---|---|---|
| `journeyId` | ref | |
| `conceptId` | ref | |
| `order` | number | Linear position in the journey |
| `state` | enum | `not_assessed \| learning \| learn-pre-req-before \| clarity \| mastered \| exam_ready` |
| `masteryLevel` | enum | `lots \| mots \| hots \| null` — highest level reached |
| `probingPath` | array | Nodes visited in probing tree — to resume mid-session |
| `goTo` | ref | `ConceptRef \| null` — next concept to visit after this node is done. Set on creation from `concept.nextConcepts[0]`; overridden to the originating concept for prereq-redirect nodes |
| `cameFrom` | ref | `ConceptRef \| null` — concept that redirected here (set only on prereq-redirect nodes) |
| `preReqToLearn` | ref | `ConceptRef \| null` — prereq concept blocking this node (set when state is `learn-pre-req-before`) |
| `lastActivity` | date | |
| `completedAt` | date | Set when state reaches `exam_ready` |

**State progression (sequential, starting point varies per student):**
```
not_assessed → learning → clarity → mastered → exam_ready
                  ↓
          learn-pre-req-before   (detour: teach a prereq before continuing)
```

| State | Meaning | Agent skill invoked |
|---|---|---|
| `not_assessed` | Child has not studied this topic or its descendants | Concept probing skill |
| `learning` | Gap identified, teaching in progress | Teaching skill |
| `learn-pre-req-before` | A prereq gap was found mid-teaching — paused until prereq is done | (prereq redirect — navigates to prereq node) |
| `clarity` | Child can answer LOTS questions | Mastery practice skill (lots → mots) |
| `mastered` | Child clears MOTS/HOTS questions | Mastery practice skill (hots → exam) |
| `exam_ready` | Child clears exam-level questions | Exam simulation |

**Navigation fields — how the agent finds the next concept:**
```
Node created for concept A
  goTo = concept.nextConcepts[0]        ← linear next
  cameFrom = null
  preReqToLearn = null

Probing finds gap in prereq B → redirect
  Node A: state = learn-pre-req-before, preReqToLearn = B
  Node B (new): goTo = A, cameFrom = A   ← returns to A when done
```

---

### `Session`
One teaching session — a child working on one concept. Created fresh for `not_assessed`; resumed from last session for all other states.

| Field | Type | Notes |
|---|---|---|
| `studentId` | ref | |
| `conceptId` | ref | |
| `journeyNodeId` | ref | `LearningJourneyNode` — the node being worked on |
| `status` | enum | `initialised \| started \| completed` |
| `conceptStateAtStart` | enum | State when session began |
| `conceptStateAtEnd` | enum | State when session ended — null until advance_state tool runs |
| `teachingPlan` | object | `TeachingPlan` — embedded |
| `planHistory` | array | `PlanHistoryEntry[]` — plan for each concept visited this session |
| `history` | array | `Message[]` — conversation turns |
| `memory` | array | `[MemoryRef]` — memory loaded for this session |
| `questionProgress` | array | `[{ questionId, outcome }]` — mastery practice results; persisted after each question |
| `createdAt` | date | |
| `endedAt` | date | null until session ends |

**Status lifecycle:** `initialised` (created, agent not yet spoken) → `started` (agent produced first response) → `completed` (student exited, history saved). Only `started` sessions are resumed. `initialised` sessions are never persisted on exit.

---

### `TeachingPlan`
Free-text plan authored by the teaching agent at session start. LLM writes and updates it in plain text as the session progresses.

| Field | Type | Notes |
|---|---|---|
| `content` | string | Free text — what the agent plans to do and why |
| `createdAt` | date | |
| `updatedAt` | date | |

No structured branching — the LLM reasons over this text each turn and rewrites as needed. Structure can be added later if navigation becomes hard to manage in text.

---

### `PlanHistoryEntry`
Appended to `Session.planHistory` each time the agent switches to a new concept (prereq redirect or return to origin).

| Field | Type | Notes |
|---|---|---|
| `conceptId` | string | |
| `conceptTitle` | string | |
| `plan` | array | `PlanStep[]` — compiled plan for that concept at the time of redirect |
| `startedAt` | date | When the agent switched to this concept |

---

### `Memory`
A persisted observation about a student, scoped to a concept or strand. Survives across sessions.

| Field | Type | Notes |
|---|---|---|
| `studentId` | ref | |
| `context` | object | `{ conceptId?: ref, strandId?: ref }` — what this memory is about |
| `type` | enum | `factual \| reflected` — factual: what child knows; reflected: what child struggles with |
| `content` | string | The observation text |
| `lastAccessedAt` | date | |
| `createdAt` | date | |

---

## Relationships

```
Strand ─────────────────────────── top of content hierarchy
Unit ───────────────────────────── Unit.strand → Strand
Topic ──────────────────────────── Topic.unit → Unit
Concept ────────────────────────── Concept.topic → Topic
Board ──────────────────────────── attribute on Concept.boards[]
Class ──────────────────────────── attribute on Concept.classApplicableTo[]
Exam ───────────────────────────── Question.appearedInExams[].exam
Resource ───────────────────────── LessonStep.resources[]
                                   Topic.practiceTests[]
Question ───────────────────────── Concept.probingTree.entryQuestion
                                   Concept.masteryQuestions[]
                                   Concept.examQuestions[]
                                   LessonStep.learningIndicator.assessmentQuestion
                                   Concept.misconceptions[].questions[]
                                   Resource (practice-test).questions[]
                                   Resource (teaching-video).cfuMarkers[].question
                                   Question.relatedQuestions[]
Concept → Concept ──────────────── prerequisites[], nextConcepts[]
                                   Concept.misconceptions[].prereqConcept
                                   ProbingTree HintAction { type: "teach" | "concept" }
Student × Journey ──────────────── LearningJourney
Student × Concept × Journey ─────── LearningJourneyNode (carries state + masteryLevel)
Session ────────────────────────── LearningJourneyNode (journeyNodeId)
Memory ─────────────────────────── Student, scoped to context.conceptId or strandId
```

---

## Storage Notes

- MongoDB — document-oriented, good fit for nested lesson steps and misconceptions
- 4-level content hierarchy: `strands` → `units` → `topics` → `concepts` — each a separate collection
- `LessonStep` and `SolutionStep` are embedded (not separate collections)
- All cross-entity references use MongoDB ObjectId refs
- `Question` is a top-level collection — shared across concepts, lesson steps, and resources
- `LearningJourneyNode` is a separate collection (not embedded in journey) — enables querying a student's progress across all concepts without loading the full journey
- `TeachingPlan` is embedded in `Session` — it's session-scoped, not reused
- `Memory` is a top-level collection — queried by studentId + context at session start
- `Topic.practiceTests` holds exercise `ResourceRef`s — individual Question docs linked via a separate question import step

---

## ERP collections (v1)

People, classrooms, and access codes. Separate namespace from CMS/LP — prefixed `erp_`.

### `erp_students`

One doc per child. Stable ID — never changes even when access code is reset or the student joins a new class.

| Field | Type | Notes |
|---|---|---|
| `id` | string | Stable student ID — used by LP to key progress |
| `name` | string | Display name |
| `age` | number | |
| `grade` | string | e.g. "Grade 7", "Not in school yet" |
| `hashedCode` | string | bcrypt hash of the 6-char access code |
| `createdByUserId` | string | Adult who created the profile |
| `createdAt` | date | |

### `erp_users`

Adults (parents and/or teachers). One doc per Google account.

| Field | Type | Notes |
|---|---|---|
| `id` | string | |
| `firebaseUid` | string | Unique — from Firebase ID token |
| `name` | string | From Google profile |
| `email` | string | From Google profile |
| `roles` | string[] | `["parent"]`, `["teacher"]`, or `["parent","teacher"]` |
| `createdAt` | date | |

### `erp_classrooms`

A teaching group owned by one teacher.

| Field | Type | Notes |
|---|---|---|
| `id` | string | |
| `name` | string | e.g. "Grade 7 Maths" |
| `ownerUserId` | string | Teacher who created it |
| `subject` | string | |
| `grade` | string | |
| `classCode` | string | 6-char code students use to join (hashed for lookup) |
| `status` | string | `active` / `archived` |
| `createdAt` | date | |

### `erp_enrollments`

One doc per student × classroom pair. Open join — no pending state in v1.

| Field | Type | Notes |
|---|---|---|
| `classroomId` | string | |
| `studentId` | string | Matches `erp_students.id` and LP's student key |
| `joinedAt` | date | |

### Access code format

- 6 characters, uppercase, no vowels, no `0` or `1` — e.g. `K7M9R2`
- Generated with `crypto.randomBytes` — checked for uniqueness per collection
- Stored as bcrypt hash — never raw
- Student codes and class codes use separate collections — no namespace collision

[← Back to index](prodigy.md)
