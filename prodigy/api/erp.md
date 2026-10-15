# prodigy — API: ERP (v1)

Student auth, adult auth, student profiles, classrooms, enrollment, and session creation.

Base URL: `http://localhost:32005` (dev). All routes return JSON.

---

## Auth

### Student login
`POST /auth/student`  — public, rate-limited (5 attempts / 60 s per IP)

Request:
```json
{ "code": "K7M9R2" }
```
Response `200`:
```json
{ "studentId": "abc123", "name": "Aarav" }
```
Response `401`: `{ "error": "That code didn't work. Check it and try again." }`
Response `429`: `{ "error": "Too many attempts. Wait a moment and try again." }`

No Firebase token in v1 — `studentId` is returned directly and stored in canvas memory or localStorage ("remember me").

---

### Adult login (Google)
`POST /auth/google`  — public

Request: `Authorization: Bearer <Firebase ID token>`
Response `200`:
```json
{ "userId": "xyz", "name": "Ms Meera", "email": "meera@example.com", "roles": ["teacher"] }
```
- Verifies token with Firebase Admin SDK
- Creates ERP user doc on first sign-in; loads existing on return
- `roles` starts empty — adult sets role during onboarding via `PATCH /me`

---

## Profile

### Get my profile
`GET /me`  — requires `studentId` query param (student) or `Authorization` header (adult)

Response (student):
```json
{ "type": "student", "studentId": "abc123", "name": "Aarav", "grade": "Grade 7" }
```
Response (adult):
```json
{ "type": "user", "userId": "xyz", "name": "Ms Meera", "roles": ["teacher"] }
```

### Update my profile
`PATCH /me`  — adult only, Authorization header required

Body: any subset of `{ name, roles }`. Cannot self-assign roles not yet onboarded.

---

## Students

### Create a student
`POST /students`  — adult only

Request:
```json
{ "name": "Aarav", "age": 12, "grade": "Grade 7", "subject": "Maths" }
```
Response `201`:
```json
{ "studentId": "abc123", "name": "Aarav", "code": "K7M9R2" }
```
- Access code returned once — copy or print it; not stored in plaintext
- `createdByUserId` set to the calling adult

### List my students
`GET /students`  — adult only
Returns students the current adult created or is linked to.

### Reset access code
`POST /students/:id/reset-code`  — adult only, must be linked to the student

Response `200`:
```json
{ "code": "R4T6WX" }
```
- Old code invalidated immediately
- Student profile and progress unchanged

---

## Classrooms

### Create a classroom
`POST /classrooms`  — teacher only

Request:
```json
{ "name": "Grade 7 Maths", "subject": "Mathematics", "grade": "Grade 7" }
```
Response `201`:
```json
{ "classroomId": "cls1", "name": "Grade 7 Maths", "classCode": "B3MN8P" }
```

### List classrooms
`GET /classrooms`  — authenticated
- Teacher: returns classes they own
- Student: returns classes they're enrolled in

### Join a class
`POST /classrooms/join`  — student only

Request:
```json
{ "studentId": "abc123", "classCode": "B3MN8P" }
```
Response `200`:
```json
{ "status": "joined", "classroomId": "cls1", "name": "Grade 7 Maths" }
```
- Open join — no approval step in v1
- Idempotent: joining twice returns `{ "status": "already_joined" }`
- Wrong code: `404 { "error": "We couldn't find that class. Check the code with your teacher." }`

### Class roster
`GET /classrooms/:id/students`  — teacher only (owner of the class)

Returns array of `{ studentId, name, grade, joinedAt }`.

---

## Learning sessions

### Create a learning session
`POST /sessions`  — student only

Request:
```json
{ "studentId": "abc123", "conceptId": "graphing-linear-equations-1" }
```
Response `201`:
```json
{
  "sessionId": "sess_xyz",
  "resumed": false,
  "concept": { "id": "graphing-linear-equations-1", "title": "Graphing linear equations" },
  "state": "not_assessed"
}
```
- Calls `SessionManager.create(studentId, conceptId)` on the agent process
- Returns a `sessionId` the canvas uses to open a WebSocket: `wss://host:32003?sessionId=sess_xyz`
- `resumed: true` if an in-progress session was resumed

---

## Error codes

| Code | Meaning |
|---|---|
| 400 | Bad request — missing or invalid body |
| 401 | Missing or invalid credentials |
| 403 | Authenticated but not authorised for this resource |
| 404 | Resource not found |
| 409 | Conflict (e.g. duplicate enrollment) |
| 429 | Rate limit exceeded |

[← Back to index](../prodigy.md)
