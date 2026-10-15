# lead-teacher-app — System

Architecture, component structure, tech stack.

---

## Tech stack

| Layer | Technology |
|---|---|
| Language | Kotlin |
| UI | Jetpack Compose |
| Background sync | WorkManager |
| Content manifest | Realm DB (server-synced) |
| Device state | Room DB |
| Dependency injection | Koin (matches existing app) |
| File storage | Android File API (internal + SD card) |
| Resource delivery | CDN (HTTP) or S3 (AWS SDK) |

---

## Screen flow

```
App open
  ├── No teacher → Login
  └── Teacher(s) exist → Teacher Picker

Teacher selected
  ├── No classes set up → Class/Division/Subject Setup
  └── Classes set up → Home

Home → Subject Picker → Chapter List → Day Plan List → Resource List
```

Eight screens total. Smart download runs in background throughout — not tied to any screen.

---

## Components

### Screens
| Screen | Purpose |
|---|---|
| Login | Credential entry; calls auth API |
| Teacher Picker | Netflix-style card list of logged-in teachers; "Add account" action |
| Class/Division/Subject Setup | Teacher marks which classes she teaches; saves to Room |
| Home | Shows teacher's class+division cards; entry point after setup |
| Subject Picker | Subjects for selected class+division; shows download readiness |
| Chapter List | Units for selected subject; "continue" badge on current chapter |
| Day Plan List | Day plans within chapter; today's plan highlighted |
| Resource List | Resources for a day plan; per-resource download status + on-demand trigger |

### Background worker
- **Trigger:** teacher selected, class setup saved, app foreground, periodic schedule
- **Steps:**
  1. Fetch policy file from server (if updated); store locally
  2. Pull Realm DB (`GET teacherApp/v14/realmImage`)
  3. Build priority list from upcoming day plans across all logged-in teachers
  4. Apply policy file — storage caps, tier thresholds, download constraints
  5. Download missing / stale resources in priority order
  6. Evict lowest-priority files when storage cap is reached

### Policy file
- Fetched from server; stored on device; read at download time
- Controls: storage budget, tier thresholds, per-environment overrides, connectivity constraints
- Server can update it without an app release — takes effect on next worker run
- Stale local policy is still functional; no hard dependency on freshness

### Priority engine
- Abstracted behind an interface — algorithm is swappable
- V1: rule-based (days until day plan, active unit vs future unit)
- V2+: ML-based (planned, not built yet)

---

## Data flow

```
Server (Realm DB + CDN/S3)
    ↓  WorkManager sync
Realm DB (content manifest)  +  Room DB (device state, assignments, status)
    ↓
Priority engine → download queue → file system (internal / SD card)
    ↓
UI reads Room DB for status; Realm DB for content structure
```

---

## Module boundaries

- **Login** — auth only; emits teacher credentials; no knowledge of content
- **Smart worker** — reads Room + Realm; writes files + ResourceStatus; no UI
- **UI screens** — read-only consumers of Room DB and Realm DB; trigger on-demand downloads via worker API
- **Priority engine** — pure function: takes teacher assignments + day plan dates → returns ranked resource list

[← Back to index](lead-teacher-app.md)
