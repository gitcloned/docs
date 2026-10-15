
| | |
|---|---|
| [System](system.md) | Architecture, component structure, tech stack |
| [Data Model](data.md) | Entities, fields, storage decisions |
| [API](api.md) | Endpoint contracts, auth, query params |
| [Decisions](decisions.md) | Choices made and why, alternatives ruled out |

A smart offline resource manager for teachers in low-connectivity schools.

This is a fork from current teacher android app. Local folder location to study more:
 - Android app: /Users/ashishjain/Documents/Code/teacherapp-frontend
 - Android app backend: /Users/ashishjain/Documents/Code/teacherapp-backend

---

## What this app does

Teachers walk into class expecting their slides, videos and worksheets to just work — no internet needed, no waiting. This app makes that happen by quietly managing what gets downloaded, what stays on the device, and what gets refreshed, all without the teacher having to think about it.

It's not a teaching app itself. It's the layer underneath — making sure the right content is always ready.

---

## The problem it solves

The existing teacher app downloads content as part of a one-click sync. That works, but it's a blunt instrument. This app is about being smarter:

- **Offline first, always.** Schools often have poor or no internet. Content must be ready before the teacher needs it, not when she asks for it.
- **SD cards are unreliable.** They corrupt silently. Losing everything on the card before an important class is a real scenario.
- **Devices are shared.** Multiple teachers use the same tablet across shifts. Each has different classes and subjects. The app needs to serve all of them without one teacher's content crowding out another's.
- **Storage is limited.** Internal storage is small but reliable. SD card is large but fragile. The app has to be smart about what goes where.
- **Internet is slow and patchy.** Downloads need to work on 2G, resume after drops, and not waste bandwidth re-downloading things that haven't changed.

---

## What "smart" means here

The app builds a picture of what each teacher is likely to need — based on their class/division assignments and the day plans coming up — and uses that to decide:

1. What to proactively download
2. Where to store it (internal vs SD card, based on how likely it is to be needed soon)
3. When to refresh it (when a newer version is available on the server)
4. What to clean up (old content that's no longer relevant)

This isn't just a download manager. It's a priority engine sitting on top of one.

---

## Key challenges

**Two-tier storage**
Internal storage = small, reliable. SD card = large, can corrupt. The app keeps the highest-priority content (next few days of teaching, most-used resources) in internal storage as a safety net. Everything else lives on SD card.

**Multi-teacher on one device**
Each teacher has a login. Each teaches different classes and divisions. The resource set for the device is the union of all teachers' needs, but priorities are per-teacher. Teacher A's content shouldn't be evicted just because Teacher B's content arrived.

**Probability of use**
Not all resources are equally likely to be needed. A resource for tomorrow's day plan is much more important than one for a unit three months away. The priority model should account for:
- How soon the day plan falls
- Whether the teacher has taught this unit before (usage history)
- Whether it's currently the active unit

**Version management**
Resources on the server get updated. The app needs to detect when a local file is stale and replace it silently in the background — without disrupting a teacher mid-class.

**On-demand downloads**
Teachers can also explicitly request content — a single resource, everything for today's class, or a whole unit. On-demand requests jump the queue and should feel fast even on a slow connection.

---

## What we know about the backend

The app reuses the existing teacher app backend. Key APIs already understood:

| What | Endpoint |
|---|---|
| Check / download realm DB | `GET teacherApp/v14/realmImage` |
| Resource metadata | `GET teacherapp/v13/resource/{id}` |
| Content download (class-subject) | `POST teacherApp/v13/internetaware/content/download/classSubject` |
| Content download (incremental / USM) | `POST teacherApp/v13/internetaware/content/download/usm/incremental` |
| Actual resource files | CDN (HTTP GET) or S3 (AWS SDK) |

Auth is header-based: `Authorization` (JWT), `schoolid`, `schooluserid`, `academicyearid`, `devicetoken` — all injected per request automatically.

The realm DB is the source of truth for what content exists — units, day plans, resource lists. The app downloads realm first, then uses it to build the download plan.

---

## Questions and their response

- Where does the class/division assignment per teacher come from — a new local table the teacher sets up manually, or pulled from an API?
	- Yes, a new local table. Which gets modified as teacher marks or unmarks the class, division and subject he/she will teach
- What's the internal storage budget — a fixed cap (e.g. 2 GB) or dynamic based on available space?
	- Yes dynamic. We can have an upper cap till like 2-4 GB. Not sure of number right now. But upper cap would help as that also saves the amount of movement we want to do across storages.
- Is "probability of use" rule-based (next 2 weeks = high priority) or learned from usage patterns over time?
	- This should be an abstraction as we would continue to evolve. In start it could be a code based algo, later we can have a ML based algo.
- Does each teacher log in separately, or does the app support a shared-device mode with quick teacher switching?
	- We should have it like gmail. A teacher can login, but another teacher can also add her account by logging in
- What language we should use to build android app? 
	- Kotlin + Jetpack Compose
- 

---

