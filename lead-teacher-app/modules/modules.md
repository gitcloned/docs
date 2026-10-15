# lead-teacher-app — Modules

Seven functional modules. Each has one job. They communicate through defined interfaces and know nothing about each other's internals.

---

## The seven modules

| Module | One-line job |
|---|---|
| [Policy Manager](module-policy-manager.md) | Fetch and serve the download policy file |
| [Content Manifest](module-content-manifest.md) | Download and maintain the Realm DB (content catalogue) |
| [Teacher Context](module-teacher-context.md) | Know who is on the device and what each teacher teaches |
| [Priority Engine](module-priority-engine.md) | Compute what to download next and what to evict |
| [Download Queue](module-download-queue.md) | Execute downloads, manage the queue, handle retries |
| [Storage Manager](module-storage-manager.md) | Place files, track locations, detect SD card issues, evict |
| [Sync Orchestrator](module-sync-orchestrator.md) | Wire all modules in sequence; respond to triggers |

---

## Dependency map

```
Sync Orchestrator
    ├── Policy Manager       (fetch latest policy)
    ├── Content Manifest     (fetch latest Realm DB)
    ├── Teacher Context      (who needs what)
    ├── Priority Engine      (compute download + eviction lists)
    │       ├── reads: Content Manifest (Realm)
    │       ├── reads: Teacher Context (Room)
    │       └── reads: Policy Manager (rules)
    ├── Storage Manager      (evict low-priority files)
    │       └── emits events → Sync Orchestrator
    └── Download Queue       (execute downloads)
            └── calls: Storage Manager (place downloaded files)
```

**Rules:**
- Only Sync Orchestrator knows the full picture — it calls everyone
- Priority Engine is the only module that reads from three others
- Download Queue and Storage Manager call each other; no one else does
- Teacher Context and Policy Manager are leaf nodes — they depend on nothing

---

## What each module exposes

| Module | Inputs | Outputs |
|---|---|---|
| Policy Manager | — | `DownloadPolicy` |
| Content Manifest | — | Realm DB (queryable) |
| Teacher Context | — | Teacher + assignment list |
| Priority Engine | Policy + Manifest + Teacher Context | Download list + Eviction list |
| Download Queue | Ranked download list | Progress events, ResourceStatus updates |
| Storage Manager | Files to store / resource IDs to evict | File paths, health events |
| Sync Orchestrator | Trigger reason | Sync state events |

---

## Design gaps found (from scenario simulation)

| Gap | Fix location |
|---|---|
| No policy on first run (server unreachable) | Policy Manager — hardcoded default |
| Priority Engine only returned download list | Priority Engine — now also returns eviction list |
| SD card corruption detected only on failed read | Storage Manager — proactive health check |
| Sync Orchestrator only had scheduled/manual triggers | Sync Orchestrator — also listens to Storage Manager events |
| Download Queue was append-only | Download Queue — supports cancellation |

---

## DB overview

Each module's full DB requirements are in its own page. Summary:

| Module            | Realm reads               | Room tables                                                |
| ----------------- | ------------------------- | ---------------------------------------------------------- |
| Policy Manager    | —                         | `DownloadPolicy` (new)                                     |
| Content Manifest  | manages all Realm objects | `ContentSyncState` (new)                                   |
| Teacher Context   | —                         | `TeacherAccount`, `TeacherClassAssignment` (existing)      |
| Priority Engine   | Unit, DayPlan, Resource   | `ResourceStatus` (read + write priorityScore)              |
| Download Queue    | —                         | `DownloadQueueItem` (new), `ResourceStatus` (write status) |
| Storage Manager   | —                         | `ResourceStatus` (read/write localPath, storageTier)       |
| Sync Orchestrator | —                         | —                                                          |

[← Back to index](lead-teacher-app.md)
