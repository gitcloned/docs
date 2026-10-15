# Module — Priority Engine

Pure computation. No I/O, no network, no file system. Takes teacher context + content manifest + policy and returns a ranked list of what to download and what to evict.

---

## Function

- For every resource across all logged-in teachers' upcoming day plans: compute a priority score
- Return a download list ordered highest score first
- Return an eviction list: resources currently on device that score zero (teacher no longer teaches that subject, or day plan is too far away)

**Interface:**
```
compute(
  teachers: List<TeacherAccount>,
  assignments: Map<TeacherAccount, List<TeacherClassAssignment>>,
  policy: DownloadPolicy
): PriorityResult

PriorityResult {
  downloadList: List<RankedResource>   // ordered, highest priority first
  evictionList: List<String>           // resourceIds to remove from device
}

RankedResource {
  resourceId: String
  score: Float
  targetTier: StorageTier              // INTERNAL or SD_CARD
}
```

---

## Non-functional requirements

- **Pure function:** same inputs always produce same output. No side effects.
- **Fast:** runs in-memory on the full resource set. Must complete in under 2 seconds on a low-end device.
- **Swappable:** abstracted behind an interface — V1 is rule-based. V2+ can be ML-based without changing callers.
- **Multi-teacher fair:** a resource needed by two teachers gets the higher of the two scores, not summed. One teacher's priorities don't crowd out another's.
- **Deduplication:** if Teacher A and Teacher B both need the same resource, it appears once in the download list.

---

## Algorithm (V1 — rule-based)

```
compute():
  1. For each teacher:
     a. Get their TeacherClassAssignment rows
     b. For each assignment (classId, division, subjectId):
        - Find matching units in Realm (via Content Manifest)
        - For each unit, get all day plans ordered by scheduledDate
        - For each day plan, get all resources

  2. Score each resource:
     score = baseDayScore × unitFactor × resourceTypeFactor

     baseDayScore = policy.internalStorageCap / (daysUntilDayPlan + 1)
       — resources for today score highest; score decays as days increase

     unitFactor:
       — active unit (currently being taught): 2.0
       — next unit: 1.0
       — future units: 0.5

     resourceTypeFactor:
       — slide: 1.0
       — video: 0.8  (large, lower priority to avoid filling storage)
       — worksheet: 1.0

  3. Across all teachers: for shared resources, take max(scoreTeacherA, scoreTeacherB)

  4. Determine target storage tier:
     — score above threshold (policy.hotTierDays) → INTERNAL
     — score below threshold → SD_CARD

  5. Build downloadList:
     — all resources with score > 0, sorted descending by score
     — exclude already-downloaded resources where version matches (read from ResourceStatus)

  6. Build evictionList:
     — all ResourceStatus rows where status = DOWNLOADED
     — AND resourceId not in any teacher's assignment scope
     — OR score = 0 (day plan is beyond policy horizon)

  7. Update ResourceStatus.priorityScore for all scored resources (write to Room)

  8. Return PriorityResult { downloadList, evictionList }
```

---

## Realm DB objects read

| Object | Fields used |
|---|---|
| Unit | id, subjectId, isActive, sequence |
| DayPlan | id, unitId, scheduledDate |
| Resource | id, dayPlanId, type, version, cdnUrl, s3Key, isS3 |

Read via Content Manifest query interface — this module does not open Realm directly.

---

## Room DB

### `ResourceStatus` (existing table — read and written)

| Field | Operation | Notes |
|---|---|---|
| resourceId | read | Identify the resource |
| teacherId | read | Which teacher's need this is |
| status | read | Skip already-downloaded resources with matching version |
| version | read | Compare with Realm Resource.version to detect staleness |
| priorityScore | **write** | Updated after each compute() call |

No new Room tables needed.

---

## Dependencies

- Reads from: Content Manifest (Realm queries via interface)
- Reads from: Teacher Context (assignments)
- Reads from: Policy Manager (scoring weights, tier thresholds, horizon days)
- Reads from: `ResourceStatus` Room table (current download state + version)
- Writes to: `ResourceStatus.priorityScore`
- Called by: Sync Orchestrator
- Results consumed by: Download Queue (downloadList), Storage Manager (evictionList)

[← Back to index](modules.md)
