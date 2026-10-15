# Module — Storage Manager

Places downloaded files on the correct storage tier, tracks where every file lives, detects SD card health issues, and evicts files when storage limits are reached.

---

## Function

- Accept a downloaded file and place it in internal storage or SD card (as instructed)
- Track the local path of every resource
- Check SD card health proactively — do not wait for a failed read to discover corruption
- Emit events when storage state changes (SD card lost, storage full)
- Evict files given a list of resource IDs to remove

**Interface:**
```
store(tempFile: File, resourceId: String, tier: StorageTier): String
  → moves file to correct location, returns absolute local path

getPath(resourceId: String): String?
  → returns local path, or null if not on device

evict(resourceIds: List<String>)
  → deletes files, updates ResourceStatus to NOT_DOWNLOADED

checkHealth(): StorageHealth
  → checks SD card mount + reads N sample files

availableSpace(tier: StorageTier): Long
  → available bytes on internal or SD card

observeEvents(): Flow<StorageEvent>
  → SD_CARD_UNAVAILABLE | STORAGE_FULL | SD_CARD_RECOVERED
```

---

## Non-functional requirements

- **Proactive health checks:** run on every app foreground and after each sync. Not reactive to read failures.
- **Event-driven:** storage state changes emit events that Sync Orchestrator listens to — enabling re-sync without a timer.
- **Atomic placement:** write to temp path first, then move. A failed placement never leaves a half-written file at the real path.
- **SD card is lossy by design:** SD card files are treated as evictable at any time. If card is removed, content is re-downloaded when card returns (or from internal if within hot tier).
- **Never evict internal without explicit instruction:** internal storage files are only removed when explicitly passed to evict() by Sync Orchestrator (with the eviction list from Priority Engine).

---

## Storage tiers

| Tier | Location | Used for | Eviction |
|---|---|---|---|
| INTERNAL | `context.filesDir` | Next 2-3 days of day plans | Only when Priority Engine says so |
| SD_CARD | First external storage path | Rest of curriculum | Treated as lossy; re-downloadable |

---

## Algorithm

### store()
```
store(tempFile, resourceId, tier):
  1. Determine destination path:
     - INTERNAL: context.filesDir / "resources" / resourceId
     - SD_CARD: sdCardPath / "lead_teacher" / "resources" / resourceId
  2. Check available space on target tier
  3. If insufficient space → emit STORAGE_FULL event, return error
  4. Move tempFile to destination (atomic rename where possible)
  5. Update ResourceStatus.localPath, ResourceStatus.storageTier
  6. Return destination path
```

### checkHealth()
```
checkHealth():
  1. Check SD card is mounted (Environment.getExternalStorageState)
  2. If not mounted → emit SD_CARD_UNAVAILABLE, update all SD_CARD ResourceStatus rows to NOT_DOWNLOADED
  3. If mounted: pick N random ResourceStatus rows where storageTier = SD_CARD AND status = DOWNLOADED
  4. Attempt to read first byte of each file
  5. If any read fails → treat as corrupted, emit SD_CARD_UNAVAILABLE
  6. If all pass → emit SD_CARD_RECOVERED (if previous state was unavailable)
```

### evict()
```
evict(resourceIds):
  1. For each resourceId:
     - Load ResourceStatus.localPath
     - Delete file at localPath
     - Update ResourceStatus: status = NOT_DOWNLOADED, localPath = null
  2. Log bytes freed
```

---

## Room DB

### `ResourceStatus` (existing table — read and written by this module)

| Field | Operation | Notes |
|---|---|---|
| resourceId | read | Look up which file to serve/evict |
| status | read + **write** | Set to NOT_DOWNLOADED on eviction |
| storageTier | read + **write** | INTERNAL or SD_CARD |
| localPath | read + **write** | Where the file lives; nulled on eviction |

No new Room tables needed.

---

## Realm DB

None. This module has no dependency on Realm.

---

## Storage events

| Event | When emitted | Effect |
|---|---|---|
| `SD_CARD_UNAVAILABLE` | SD card missing or unreadable | Sync Orchestrator re-syncs; Priority Engine sees all SD content as missing |
| `STORAGE_FULL` | No space left on a tier | Download Queue pauses; Sync Orchestrator may trigger eviction pass |
| `SD_CARD_RECOVERED` | Card reappears after unavailable | Sync Orchestrator re-syncs to refill SD card |

---

## Dependencies

- Reads from: `ResourceStatus` Room table
- Writes to: `ResourceStatus` Room table
- Emits events to: Sync Orchestrator
- Called by: Download Queue (store), Sync Orchestrator (evict, checkHealth)

[← Back to index](modules.md)
