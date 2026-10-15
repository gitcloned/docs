# Classes and learning journeys

## Objective

Let a child choose a topic from their class and continue from their saved progress. Use the same learning flow for parent-created and teacher-created classes.

## Principles

- One learning journey per student per subject, shared across classes.
- Joining a class adds topics; it never resets existing progress.
- Topic grades are recommendations, not access restrictions.
- Concept progress decides what to study. A matching session supplies the conversation and unfinished teaching steps.
- CMS owns curriculum, ERP owns classes and enrollment, and Learning Progression (LP) owns journeys and progress.

## Relationships between entities

```text
CMS: Subject → Strand → Unit → Topic → Concept
ERP: Class → selected subjects and topics
     Class ↔ Students (enrollments)
LP:  Student → Journey per subject → Assigned topics → Concept nodes
     Concept node → Sessions
```

A student can join multiple classes. Their progress in a concept is reused across those classes.

A parent-created class is a private class with one child. It uses the same backend model, but has no class-management interface or invitation code.

## Backend changes

### DB models

**CMS**
- Give subjects stable IDs; link strands to them.
- Add `recommendedGrades: number[]` to topics. Retain the existing topic/concept order.
  - Backfill existing CMS records too.

**ERP**
- Class: retain its owner (`ownerUserId` today), grade and name; add `kind: teacher | personal`.
- Store selected topics as class assignments: `classId`, `subjectId`, `topicId`. Each assignment is unique within a class.
- Reuse the existing enrollment model. A personal class has exactly one child.

**LP**
- `learning_journeys`: add `subjectId`; unique on `(studentId, subjectId)`.
- Add `learning_journey_topics`: `id`, `journeyId`, `topicId`, `sourceClassIds`, `assignedAt`
- Unique on `(journeyId, topicId)`. Merge assignment sources when classes overlap.
- Concept nodes: add `topicId`; retain uniqueness on `(journeyId, conceptId)` and the existing state/prerequisite fields.
  - Set `topicId` from CMS when creating a node, including prerequisite nodes. Backfill existing nodes; do not change their progress.
- Sessions: keep the existing statuses. Save unfinished sessions as `started` on disconnect; mark them `completed` only when the phase finishes.

### New APIs

**CMS — `GET /curriculum?grade=7`**
Read subjects, strands, units, topics and concepts. Mark topics recommended for the grade. Keep other topics available for selection.

**ERP — `GET /students/:id/classes/:classId/topics`**
Check that the student belongs to the class. Read its selected subjects/topics and add their names and hierarchy from CMS. Return what this class offers, not the child's progress.

**ERP — `PUT /classrooms/:id/topics`**
Check the class owner and validate the selected topics against CMS. Save the selections, then sync assignments to LP for every enrolled child. If sync fails, retain the selections and allow retry.

**LP — `PUT /students/:id/class-assignments/:classId`**
Called by ERP after enrollment or a change to class topics. For each selected subject, create or reuse the child's journey. Add its topics and record this class as a source. Remove only this class's source from topics no longer selected. Never delete progress or duplicate an existing assignment. Topics with no remaining class source are retained as history but hidden from the assigned-topic list.

**LP — `GET /students/:id/home`**
Read the child's journeys and assigned topics. Use CMS to group them by subject and show their names. Compare concept progress with each topic's full concept list to mark completion. Find the most recently active unfinished topic, follow its prerequisite/next-step rules, and include one optional `continueWith` result. Return `null` if there is no previous unfinished learning to continue; a new child simply sees topics to choose.

**LP — `GET /students/:id/topics/:topicId/next`**
Check that the topic is assigned to the child. Read its concepts and progress, then:
1. If every concept has finished its supported phases, return `completed`.
2. If the topic has no progress, choose its last concept by CMS order, with default `not_assessed` state.
3. Otherwise, continue the most recently active unfinished path in that topic. Follow prerequisite links even when they lead outside the topic; use existing progression rules at phase boundaries.
4. If there is no unfinished path but concepts remain unassessed, choose the last remaining unassessed concept by CMS order.
5. Look for a matching unfinished session for the chosen journey node and phase. Return its ID if found; otherwise return `null` for the session ID.

The topic route and Home's `continueWith` use the same decision logic and result:

```json
{
  "status": "continue",
  "topicId": "...",
  "conceptId": "...",
  "state": "learning",
  "resumeSessionId": null
}
```

Missing concept nodes mean not assessed. Empty topics are unavailable, not complete. Use node activity and saved session history to identify the last learning path; session `createdAt` alone is not enough. Keep the selected topic as the origin when following prerequisite links.

GET requests only read and suggest; they do not create nodes or advance states. Apply student/owner access checks. Assignment sync is a service operation.

**No separate `/continue` route is needed.** Home already returns that information. Both Home's Continue button and topic selection use the existing agent session-start flow below.

### Existing flows: what changes

**Creating a teacher class and enrolling a child**
Today ERP creates a class and enrollment without assigning learning topics. Add subject/topic selection to class setup, suggested by grade. After any enrollment—new student, existing profile or invitation code—ERP calls LP's assignment sync. Reuse existing subject journeys and progress.

**Parent adding a child**
Today this creates only a student profile. Also create a private one-child class, save the selected subjects/topics, enroll the child, and sync LP assignments. Use grade-based defaults that the parent can change. Return the usual student access code. Do not show class-management controls. A retry must reuse the child and personal class already created.

**Starting or resuming from Home**
Today the browser remembers the last lesson locally and sends `studentId` and `conceptId` to the agent. Replace that local choice with Home's `continueWith`, or the selected topic's `/next` result.

Keep the existing handshake:
1. UI calls agent `POST /sessions` with `studentId`, `conceptId`, and the selected `topicId`. It may include the suggested `resumeSessionId`.
2. Agent verifies access and rechecks the topic/progress decision. Client-supplied state or session IDs are hints, not instructions to overwrite progress.
3. Agent creates or resumes the correct session and returns `sessionId`, `resumed`, concept/state and `wsUrl`.
4. UI opens `/sessions/:sessionId` and connects to that WebSocket, as it does today.

**Choosing the journey and concept node**
Today the agent uses `journeys[0]`. Instead, find the journey for the selected topic's subject. Create concept nodes only when needed, setting their actual CMS `topicId`. Reuse nodes already present; do not reset their state.

**Resuming teaching**
Today the agent checks concept state, then selects the latest `started` session for that student/concept. Keep this flow, but also check the journey node and phase so an older assessment cannot override later progress. Reuse saved conversation, teaching-step and practice progress. Preserve the existing return-from-prerequisite flow and its saved resume step. Use the same selection rules in LP and the agent.

**Disconnecting**
Today `SessionManager.end()` marks a session completed on disconnect. Change it to save the unfinished session as `started` and remove only the live connection. Actual phase completion still marks it `completed`. Returning through `POST /sessions` can then restore it, even after an agent restart. The existing session-lookup GET only handles sessions loaded in the running agent; it is not the saved-session resume entry point.

**Existing data**
Backfill subjects and topic grades in CMS. Split existing student journeys by subject, merge duplicates without losing progress, and preserve node/session references. Backfill topic assignments and personal classes for existing parent-created children. Keep enrollment and sync retry-safe. Do not blindly reopen historical completed sessions: check their node state and saved progress first.

## Frontend changes

- Teacher setup: grade → subject selection → recommended topics, with other topics available.
- Parent setup: child details → subjects/topics, with grade-based defaults. No class-management screen.
- Child Home: subject tabs, topics grouped under strands/units, completion labels and one Continue action.
- Selecting an incomplete topic calls LP's topic-next route, then starts/resumes through the agent. Keep the session ID in the URL.
- Completed topics show completion; never silently reset them. Revision can be added separately.
- Replace the browser's local “last lesson” decision with `continueWith` from LP Home.
