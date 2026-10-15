# Module — Content Manifest

Downloads and maintains the Realm DB from the server. This is the catalogue — every unit, day plan, and resource that exists for a school. Other modules query it to understand what content is available.

---

## Function

- On sync: check if server has a newer Realm DB using checksumHash
- If newer: download the zip from S3, unzip, import into Realm
- Always: expose query methods so other modules can read content structure
- If offline: serve the existing local Realm DB

**Interface:**
```
syncManifest()                              → download and import if newer version exists
getUnitsForSubject(subjectId): List<Unit>   → all chapters for a subject
getDayPlansForUnit(unitId): List<DayPlan>   → all day plans in a chapter, ordered by date
getResourcesForDayPlan(dayPlanId): List<Resource> → all files for a day plan
getUpcomingDayPlans(subjectId, fromDate, days): List<DayPlan> → day plans in next N days
```

---

## Non-functional requirements

- **Offline-safe:** if no internet, use existing Realm DB. Never blocks if Realm exists.
- **Atomic import:** download to temp file → verify checksum → swap. Partial downloads never corrupt the live DB.
- **Checksum skip:** if local checksumHash matches server response, skip the download entirely — even if file is old.
- **Large file handling:** the Realm zip can be several MB (observed: 7.7 MB for school 14527). Download must stream, not load into memory.
- **Unzip into two files:** the zip contains two Realm files — content DB and resource DB. Both extracted to internal storage.

---

## Algorithm

```
syncManifest():
  1. GET teacherApp/v14/realmImage
     → { bucketName, directory, fileName, size, checksumHash, force }
  2. Compare checksumHash with ContentSyncState.checksumHash
  3. If same AND force == false → return (no update needed)
  4. Download zip from S3:
       AmazonS3Client(credentials from Policy Manager or config API)
       .getObject(bucketName, directory + "/" + fileName)
       → stream to temp file
  5. Verify: MD5(tempFile) == checksumHash → abort if mismatch
  6. Unzip temp file:
       → content Realm DB file (e.g. content.realm)
       → resource Realm DB file (e.g. resource.realm)
  7. Close existing Realm instances
  8. Move unzipped files to active Realm paths (atomic swap)
  9. Reinitialise Realm
  10. Update ContentSyncState: fileName, checksumHash, syncedAt
```

If step 4–9 fails → keep existing Realm, mark sync as failed, retry on next trigger.

---

## Realm DB objects (managed by this module)

This module owns the Realm DB. All other modules query it through this module's interface.

### Unit (Chapter)
| Field | Type | Notes |
|---|---|---|
| id | String | Unique identifier |
| subjectId | String | Links to a subject |
| name | String | Display name |
| sequence | Int | Order within the subject |
| isActive | Boolean | Whether this is the current teaching unit |

### DayPlan
| Field | Type | Notes |
|---|---|---|
| id | String | Unique identifier |
| unitId | String | Parent unit |
| scheduledDate | Date | When this day plan is taught |
| title | String | Display name |
| sequence | Int | Order within the unit |

### Resource
| Field | Type | Notes |
|---|---|---|
| id | String | Unique identifier |
| dayPlanId | String | Parent day plan |
| type | String | `slide`, `video`, `worksheet` |
| version | String | Server version — used to detect staleness |
| cdnUrl | String | Direct CDN download URL (if CDN-hosted) |
| s3Key | String | S3 object key (if S3-hosted) |
| isS3 | Boolean | True = use S3, False = use CDN URL |

---

## Room DB

### `ContentSyncState` (new table)

| Field | Type | Notes |
|---|---|---|
| id | Int | Always 1 — single row |
| fileName | String | Last downloaded zip file name |
| checksumHash | String | MD5 of last downloaded zip |
| syncedAt | Long | Unix timestamp of last successful import |
| fileSizeBytes | Long | Expected size from server (for progress) |

---

## Dependencies

- Reads from: `GET teacherApp/v14/realmImage` (metadata), S3 (zip file)
- Reads from: Policy Manager (S3 credentials — or falls back to config API directly)
- Writes to: Realm DB (content manifest), `ContentSyncState` Room table
- Called by: Sync Orchestrator
- Read by: Priority Engine (via query interface)

[← Back to index](modules.md)
