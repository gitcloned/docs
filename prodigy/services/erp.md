# ERP service

Manages people and classes. Firebase handles adult identity; ERP holds student profiles, access codes, classrooms, and enrollment.

Implementation details complement [the login journey](../user-journeys/login.md).

---

## Objective

- Students sign in with a short access code — no Google account needed.
- Parents and teachers sign in with Google.
- A student has one profile that follows them across every class they join.
- A teacher creates a classroom and shares a class code. Students join with that code.
- When a student picks a concept to learn, the backend creates an agent session and returns a session identifier (`sessionId`) and WebSocket URL. The canvas connects to the tutor using that ticket.

---

## Technology

TypeScript, Express, MongoDB, Mongoose — matching the existing backend. Separate service, own collections, shares the MongoDB deployment. Firebase Admin SDK on the server to verify Google ID tokens.

Port: `32006` (ERP). Agent HTTP + WebSocket: `32004`. Resources remain on `32003`; canvas preview remains on `32005`. All ports are configurable.

---

## Data model

Collections live in the same MongoDB instance as CMS and LP. No prefix needed — names are unambiguous.

### `students`

One doc per child. The `id` is stable and used by LP to key all learning progress.

| Field | Type | Notes |
|---|---|---|
| `id` | string | Stable ID — never changes |
| `name` | string | |
| `age` | number | |
| `grade` | string | e.g. `"Grade 7"`, `"Not in school yet"` |
| `hashedCode` | string | HMAC-SHA256 of the normalized 6-character access code; unique index |
| `createdByUserId` | string | Adult who created the profile |
| `createdAt` | date | |

### `users`

One doc per adult Google account. A user can be a parent, a teacher, or both.

| Field | Type | Notes |
|---|---|---|
| `id` | string | |
| `firebaseUid` | string | Unique — from verified Firebase token |
| `name` | string | From Google profile |
| `email` | string | From Google profile |
| `roles` | string[] | `["parent"]`, `["teacher"]`, or `["parent","teacher"]` |
| `createdAt` | date | |

### `classrooms`

A teaching group owned by one teacher.

| Field | Type | Notes |
|---|---|---|
| `id` | string | |
| `name` | string | e.g. `"Grade 7 Maths"` |
| `createdByUserId` | string | Ref → `users.id` |
| `subject` | string | |
| `grade` | string | |
| `hashedClassCode` | string | HMAC-SHA256 of the normalized 6-character class code; unique index |
| `status` | string | `active` / `archived` |
| `createdAt` | date | |

### `enrollments`

One doc per student × classroom pair.

| Field | Type | Notes |
|---|---|---|
| `classroomId` | string | Ref → `classrooms.id` |
| `studentId` | string | Ref → `students.id` — same key used by LP |
| `joinedAt` | date | |

Unique index on `(classroomId, studentId)` — joining twice is idempotent.

### Access codes

- 6 characters, uppercase, no vowels, no `0` or `1` — e.g. `K7M9R2`
- Generate each character with `crypto.randomInt(alphabet.length)` from `BCDFGHJKLMNPQRSTVWXYZ23456789`.
- Normalize with `code.trim().toUpperCase()`; reject anything outside this alphabet or not exactly 6 characters.
- Store `createHmac('sha256', ACCESS_CODE_SECRET).update(normalizedCode).digest('hex')`; never store the raw code. Use this deterministic hash for indexed lookup; no bcrypt needed.
- Enforce unique indexes on `students.hashedCode` and `classrooms.hashedClassCode`. On duplicate-key insertion, generate another code and retry.
- Keep `ACCESS_CODE_SECRET` stable and server-only. Changing it invalidates existing codes.
- Return the raw code only on creation/reset. Adults can copy or print it; forgotten codes must be reset.
- Student codes and class codes are separate collections — no namespace collision

---

## REST API

Base URL: `http://localhost:32006`

### Auth

**`POST /auth/student`** — public

Student sends their access code. Gets back their identity.

```
POST /auth/student
{ "code": "K7M9R2" }

200 → { "studentId": "s_abc", "name": "Aarav" }
401 → { "error": "That code didn't work. Check it and try again." }
```

---

**`POST /auth/google`** — public

Adult sends a Firebase ID token. ERP verifies it and creates or loads their account.

```
POST /auth/google
Authorization: Bearer <Firebase ID token>

200 → { "userId": "u_xyz", "name": "Ms Meera", "email": "meera@school.in", "roles": ["teacher"] }
```

On first sign-in, `roles` is empty — adult sets it during onboarding via `PATCH /me`.

---

### Profile

**`GET /me`**

Student: pass `studentId` as query param. Adult: pass `Authorization` header.

```
GET /me?studentId=s_abc
200 → { "type": "student", "studentId": "s_abc", "name": "Aarav", "grade": "Grade 7" }

GET /me  (with Authorization header)
200 → { "type": "user", "userId": "u_xyz", "name": "Ms Meera", "roles": ["teacher"] }
```

---

**`PATCH /me`** — adult only

Update name or roles. Adults may choose parent, teacher, or both during onboarding and change that choice later. These are product roles, not administrator privileges.

---

### Students

**`POST /students`** — adult only

Create a student profile. Returns the access code once — copy or print it.

```
POST /students
{ "userId": "u_xyz", "name": "Aarav", "age": 12, "grade": "Grade 7" }

201 → { "studentId": "s_abc", "name": "Aarav", "code": "K7M9R2" }
```

---

**`GET /students`** — adult only

List students the current adult created.

---

**`POST /students/:id/reset-code`** — adult flow

Generates a new code, invalidates the old one. Profile and progress unchanged.

```
POST /students/s_abc/reset-code

200 → { "code": "R4T6WX" }
```

---

### Classrooms

**`POST /classrooms`** — teacher only

```
POST /classrooms
{ "userId": "u_xyz", "name": "Grade 7 Maths", "subject": "Mathematics", "grade": "Grade 7" }

201 → { "classroomId": "cls_1", "name": "Grade 7 Maths", "classCode": "B3MN8P" }
```

---

**`GET /classrooms`** — authenticated

Teacher: returns classes they own. Student: returns classes they're enrolled in.

---

**`POST /classrooms/join`** — student

Student submits a class code. Enrolled immediately — no approval step.

```
POST /classrooms/join
{ "studentId": "s_abc", "classCode": "B3MN8P" }

200 → { "status": "joined", "classroomId": "cls_1", "name": "Grade 7 Maths" }
200 → { "status": "already_joined" }   ← idempotent
404 → { "error": "We couldn't find that class. Check the code with your teacher." }
```

---

**`GET /classrooms/:id/students`** — teacher only (owner)

Returns `[{ studentId, name, grade, joinedAt }]`.

---

### Sessions (agent service, not ERP)

**`POST /sessions`** — student

Creates an agent session for the student and concept. Returns a `sessionId` the canvas uses to open the WebSocket.

```
POST /sessions
{ "studentId": "s_abc", "conceptId": "graphing-linear-equations-1" }

201 → {
  "sessionId": "sess_xyz",
  "resumed": false,
  "wsUrl": "wss://agent-host?sessionId=sess_xyz",
  "concept": { "id": "graphing-linear-equations-1", "title": "Graphing linear equations" },
  "state": "not_assessed"
}
```

Canvas opens the returned `wsUrl`. Locally it can be `ws://localhost:32004?sessionId=sess_xyz`; behind a tunnel use its public WSS URL. Configure `PUBLIC_AGENT_URL` on the agent to construct it.

---

## Key flows

### Student signs in and starts learning

```
Student enters code "K7M9R2"
  → POST /auth/student { code }
  ← { studentId: "s_abc", name: "Aarav" }

Student sees home screen, picks "Grade 7 Maths" class → concept "Graphing linear equations"
  → POST /sessions { studentId: "s_abc", conceptId: "graphing-linear-equations-1" }
  ← { sessionId: "sess_xyz", concept: { title: "Graphing linear equations" }, state: "not_assessed" }

Canvas opens WebSocket
  → wss://agent-host?sessionId=sess_xyz
  ← tutor sends first message
```

---

### Teacher sets up a class and adds students

```
Teacher signs in with Google
  → POST /auth/google  (Authorization: Bearer <token>)
  ← { userId: "u_xyz", name: "Ms Meera", roles: [] }

Teacher sets role
  → PATCH /me  { userId: "u_xyz", roles: ["teacher"] }

Teacher creates a class
  → POST /classrooms { name: "Grade 7 Maths", subject: "Mathematics", grade: "Grade 7" }
  ← { classroomId: "cls_1", classCode: "B3MN8P" }

Teacher shares "B3MN8P" with students

Teacher adds a new student (no Prodigy account yet; repeat for additional students)
  → POST /students { name: "Aarav", age: 12, grade: "Grade 7" }
  ← { studentId: "s_abc", code: "K7M9R2" }   ← hand this slip to Aarav
  → POST /classrooms/cls_1/students { "studentId": "s_abc" }
  ← { status: "enrolled" }
```

---

### Student joins a class

```
Student is already signed in (studentId known)

Student enters class code "B3MN8P"
  → POST /classrooms/join { studentId: "s_abc", classCode: "B3MN8P" }
  ← { status: "joined", classroomId: "cls_1", name: "Grade 7 Maths" }

Class now appears in student's home screen
  → GET /classrooms?studentId=s_abc
  ← [{ classroomId: "cls_1", name: "Grade 7 Maths" }]
```

---

## WebSocket — how sessionId ties in

The agent server (`port 32004`, entry point `agent/server.mjs`) runs HTTP and WebSocket on the same port.

```
HTTP  POST /sessions  →  SessionManager.create(studentId, conceptId)  →  { sessionId }
WS    ?sessionId=xxx  →  SessionManager.join(sessionId, transport)     →  tutor starts
```

Each WebSocket connection gets its own `PerConnectionTransport`. Each transport routes only its joined session. This is routing isolation, not an authorization guarantee in this MVP. `cli.mjs` still works unchanged via its own `SessionManager` instance.

---

## Error codes

| Code | Meaning |
|---|---|
| 400 | Bad request — missing or invalid body |
| 401 | Missing or invalid credentials |
| 403 | Authenticated but not authorised |
| 404 | Resource not found |
| 409 | Conflict |
| 429 | Rate limit exceeded |


## MVP decisions and frontend contract

Per-request authorization, login attempt controls, institutes, phone verification, photo upload, parent linking, and fine-grained sharing are deferred. Firebase still verifies adult identity at Google sign-in. Student login verifies the access code once. The UI keeps the returned identity and sends `studentId` or `userId` for subsequent requests. Do not build middleware or a permissions matrix as part of this version.

- A user's `roles` can include parent and teacher.
- A classroom's `createdByUserId` is also its owner; no separate owner field.
- Student identities are stable across classes. Enrollment is many-to-many.
- Student access codes identify children; class codes only identify a class to join. Never show a roster as a login shortcut.
- `POST /students` accepts `{userId, name, age?, grade}`; `createdByUserId` comes from `userId` in this MVP. Subject belongs to a classroom, not a student profile.
- `GET /students?userId=…` lists profiles the adult created.
- `PATCH /me` accepts `{userId, name?, roles?}`.
- `POST /classrooms` accepts `{userId, name, subject, grade}`; persist `userId` as `createdByUserId`.
- `GET /classrooms?userId=…` lists owned classes. `GET /classrooms?studentId=…` lists enrolled classes. Return arrays of `{id,name,subject,grade,createdByUserId,status}`.
- `GET /classrooms/:id/students` returns `[{studentId,name,grade,joinedAt}]`.
- Add `POST /classrooms/:id/students` with `{studentId}` to enroll a newly created student from teacher setup; make it idempotent. Reuse a profile; do not create another profile just to add a class.
- Student `POST /classrooms/join` remains `{studentId,classCode}`. Return `{status,classroomId,name}` for both joined and already_joined; reject archived classes.
- Add `POST /classrooms/:id/reset-code` returning `{code}`. It invalidates the old invitation without changing existing enrollment.
- Resetting a student's code must retain the student ID, enrollments, and LP history.
- Every student response includes `studentId`, `name`, `grade`; every adult response includes `userId`, `name`, `email`, `roles`. Return these consistently from sign-in, profile creation, and `/me`.
- The frontend may remember the most recently opened concept on the device and label it **Continue learning**; the agent still decides whether to resume when `/sessions` is called.
- First-time adults choose their role, then create their first child or classroom. Returning adults go directly to their dashboard. A parent may open a child's learning space without requiring another code entry.
- No class is required for personal learning. An empty student home offers **Explore lessons** and **Join a class**.
- Do not show fabricated scores or progress. Only display progress when LP supplies it.

### Lesson catalog

Add `GET /concepts` to ERP, returning `[{id,title,description?}]`, using CMS as the source. For this first version all students and classes use the same available catalog; subject/grade filtering and teacher-assigned concepts can follow. Only include concepts the agent can load. Personal learning and classroom learning both use this endpoint. Never copy lesson content into ERP collections.

### Agent server contract

`agent/server.mjs` owns a single `SessionManager` instance and handles both REST session creation and WebSocket joining. The UI calls the agent's `POST /sessions` directly with `{studentId,conceptId,classroomId?}`; classroomId is context, not a new student identity. Return `{sessionId,resumed,concept:{id,title},state,wsUrl}`. ERP does not create its own SessionManager.

Repeated starts should reuse an existing active student/concept session rather than duplicate it. A reconnect or page refresh must rejoin/resume the session; define replacement behavior for an older socket instead of running two tutor turns. If the process restarted, rebuild from LP history or return a clear recoverable error so the UI can create/resume again.

### Frontend configuration

The journey UI lives in the existing canvas app at `/home`. The canvas remains at `/`, with `/canvas` also supported. The UI starts a lesson through the agent, then mounts the canvas with the returned socket address. The back action returns to the student's learning space.

- `VITE_ERP_API_URL`: local default `http://<current-host>:32006`; set a public HTTPS URL for hosting.
- `VITE_AGENT_API_URL`: local default `http://<current-host>:32004`; set the public HTTPS agent/tunnel URL for hosting.
- `VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_AUTH_DOMAIN`, `VITE_FIREBASE_PROJECT_ID`, `VITE_FIREBASE_APP_ID`: Firebase web configuration for adult Google sign-in.
- Configure CORS on ERP and agent for the frontend origin, JSON requests, and the Authorization header. Handle OPTIONS requests.
- A separate, clearly labelled `/home?preview=1` mode lets developers exercise the UI without ERP. Its sample identities and classroom changes stay on the device and must never be submitted to production APIs.

### Acceptance checks

1. An adult signs in, chooses parent/teacher/both, and returns without repeated onboarding.
2. A parent creates a child, copies/prints the code, and opens the child's learning space.
3. A teacher creates a class, copies its code, adds students, and enrolls them in that class.
4. A student signs in with their code, joins two classes, and retains one student ID and LP history.
5. Joining the same class twice creates no duplicate enrollment.
6. An invalid code gives a clear retry/help path. No-code students can return to adult setup.
7. Code reset invalidates the old code while preserving enrollment/progress.
8. Starting a concept returns a working socket URL; leaving the canvas returns to the same learning space.
9. API errors keep entered form values and offer retry; no silent fallback to demo data.
10. Student identity is remembered only when requested; switching student clears it. Class invitations survive the sign-in flow.
