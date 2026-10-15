# Module — Sync Orchestrator

The top-level coordinator. Wires all other modules in sequence, responds to triggers, and ensures the device always has the right content ready.

---

## Function

- Listen for triggers (scheduled, user actions, system events)
- On trigger: run the full sync pipeline across all modules in order
- Handle partial failures gracefully — a failed policy fetch doesn't stop a content sync
- Prevent concurrent syncs (one at a time)
- Report sync state to observers (for UI status indicator)

**Interface:**
```
trigger(reason: SyncReason)
  → starts a sync if none is running; queues if one is in progress

observeState(): Flow<SyncState>
  → IDLE | SYNCING(step, progress) | ERROR(reason) | COMPLETED
```

---

## Non-functional requirements

- **Single instance:** only one sync runs at a time. WorkManager guarantees this with `ExistingWorkPolicy.KEEP`.
- **Survives restarts:** implemented as a WorkManager Worker. If the device reboots mid-sync, WorkManager re-enqueues on boot.
- **Partial failure tolerance:** if Policy Manager fails (offline), continue with cached policy. If Content Manifest fails, continue with existing Realm. Never abort the whole sync because one step failed.
- **Offline-safe:** a sync with no internet is valid — it re-evaluates priorities on existing data and queues downloads for when connectivity returns.
- **No duplicate triggers:** multiple triggers in quick succession (e.g., teacher select then immediate foreground event) result in one sync, not many.

---

## Trigger types

| Trigger | When fired |
|---|---|
| `TEACHER_SELECTED` | User picks a teacher on Teacher Picker screen |
| `CLASS_SETUP_SAVED` | Teacher saves class/division/subject assignments |
| `APP_FOREGROUND` | App comes to foreground (debounced — max once per N minutes) |
| `PERIODIC` | Timer, WiFi-only, interval from policy (default: every few hours) |
| `CONNECTIVITY_RESTORED` | Device reconnects to WiFi after being offline |
| `STORAGE_EVENT` | Storage Manager emits SD_CARD_UNAVAILABLE or SD_CARD_RECOVERED |

---

## Algorithm

```
sync(reason: SyncReason):
  1. Acquire sync lock → if already running, return

  2. Emit SyncState.SYNCING(step = "policy")
     Policy Manager.syncPolicy()
     → on failure: log, continue with cached policy

  3. Emit SyncState.SYNCING(step = "manifest")
     Content Manifest.syncManifest()
     → on failure: log, continue with existing Realm DB

  4. Storage Manager.checkHealth()
     → if SD_CARD_UNAVAILABLE emitted: Realm DB still intact, continue

  5. Emit SyncState.SYNCING(step = "priority")
     teachers = Teacher Context.getAllTeachers()
     assignments = Teacher Context.getAllAssignments()
     policy = Policy Manager.getPolicy()
     result = Priority Engine.compute(teachers, assignments, policy)

  6. Storage Manager.evict(result.evictionList)

  7. Download Queue.enqueue(result.downloadList)

  8. Emit SyncState.COMPLETED
  9. Release sync lock
```

---

## Offline behaviour

Steps 2 and 3 make network calls — both fail gracefully when offline:
- Policy Manager returns cached policy (or default)
- Content Manifest skips download, uses existing Realm DB

Steps 4–7 are all local — they run normally regardless of connectivity.

Download Queue receives the prioritised list but cannot execute downloads. It holds the queue in Room and begins downloading as soon as WorkManager's network constraint is satisfied (WiFi available).

**Result:** a sync with no internet still recomputes priorities, evicts stale content, and queues the correct items for when connectivity returns.

---

## Room DB

This module does not read or write Room DB directly. It coordinates modules that do.

---

## Realm DB

None directly. Content Manifest manages the Realm DB; this module calls Content Manifest.

---

## Dependencies

- Calls: Policy Manager, Content Manifest, Teacher Context, Priority Engine, Storage Manager, Download Queue
- Listens to: Storage Manager events (StorageEvent flow)
- Triggered by: Teacher Picker screen, Class Setup screen, WorkManager (periodic + network), App lifecycle
- Read by: UI screens (observeState for status indicator)

[← Back to index](modules.md)
