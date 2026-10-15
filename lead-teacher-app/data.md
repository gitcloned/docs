# lead-teacher-app — Data Model

Entities, fields, storage decisions.

---

## Storage layers

Two separate databases + file storage:

| Layer | Technology | Purpose |
|---|---|---|
| Content manifest | Realm DB | Units, day plans, resources — synced from server |
| Device state | Room DB | Teacher accounts, class assignments, download status |
| Resource files | File system | Actual slides, videos, worksheets |

---

## Realm DB (server-synced content)

Downloaded from `GET teacherApp/v14/realmImage`. Read-only from the app's perspective — the server owns it.

Key objects:
- **Unit (Chapter)** — a teaching unit for a subject; has many day plans
- **DayPlan** — one day's lesson within a unit; has many resources; includes scheduled date
- **Resource** — a single file (slide, video, worksheet); has id, type, version, CDN/S3 URL

---

## Room DB (local device state)

Owned by the app. Persists across app restarts.

### TeacherAccount
| Field | Type | Notes |
|---|---|---|
| id | String | `schooluserid` from auth |
| name | String | Display name |
| jwt | String | Auth token |
| schoolId | String | |
| academicYearId | String | |
| deviceToken | String | |
| isActive | Boolean | Which teacher is currently selected |

### TeacherClassAssignment
Teacher's self-declared teaching assignments. Set in the Class/Division/Subject setup screen.

| Field | Type | Notes |
|---|---|---|
| teacherId | String | FK → TeacherAccount |
| classId | String | |
| division | String | |
| subjectId | String | |

### ResourceStatus
Tracks download state per resource per teacher.

| Field | Type | Notes |
|---|---|---|
| resourceId | String | From Realm |
| teacherId | String | FK → TeacherAccount |
| status | Enum | `NOT_DOWNLOADED`, `QUEUED`, `DOWNLOADING`, `DOWNLOADED` |
| storageTier | Enum | `INTERNAL`, `SD_CARD` |
| localPath | String | Absolute path to downloaded file |
| version | String | Server version at time of download |
| priorityScore | Float | Computed by priority engine; drives queue order |

---

## File storage

| Tier | Location | Used for |
|---|---|---|
| Internal | Android internal storage | High-priority content — next 2-3 days of day plans |
| SD card | External SD | Lower-priority content — rest of the curriculum |

- Internal storage cap: dynamic, upper limit ~2–4 GB (exact value TBD)
- Eviction: lowest `priorityScore` files removed first when storage is full
- SD card files are not evicted unless explicitly cleaned — but app treats them as lossy (can re-download if card corrupts)

[← Back to index](lead-teacher-app.md)
