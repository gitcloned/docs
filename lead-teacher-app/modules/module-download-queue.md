# Module — Download Queue

Takes the priority-ranked download list and executes actual downloads. Manages the queue, tracks progress, handles retries, and supports cancellation when priorities shift.

---

## Function

- Accept a ranked list of resources from Priority Engine
- Diff against existing queue — add new items, reorder, cancel items no longer needed
- Download each resource in order, using CDN (HTTP GET) or S3 (AWS SDK) depending on the resource
- Report progress to observers
- On success: hand file to Storage Manager, update ResourceStatus
- On failure: retry up to the policy limit, then mark FAILED

**Interface:**
```
enqueue(downloadList: List<RankedResource>)
  → diffs against current queue, cancels removed items, adds/reorders new ones

cancel(resourceId: String)
  → stops in-progress download, removes from queue

getStatus(resourceId: String): DownloadStatus
  → NOT_DOWNLOADED | QUEUED | DOWNLOADING(progress%) | DOWNLOADED | FAILED

observeQueue(): Flow<List<DownloadQueueItem>>
  → live updates for UI (Resource List screen)

observeActiveDownload(): Flow<ActiveDownload?>
  → current file being downloaded + progress
```

---

## Non-functional requirements

- **Persists across restarts:** queue is in Room. If app is killed mid-download, queue resumes on next sync trigger.
- **Cancellation:** when teacher changes allocation and Priority Engine removes items, in-progress downloads for those resources stop within one retry cycle.
- **Network constraint:** only downloads on WiFi (enforced by WorkManager constraint, backed by policy).
- **Sequential by default:** downloads one file at a time to avoid saturating the connection on 2G/3G. Parallel can be enabled via policy.
- **No partial resume:** failed/interrupted downloads restart from byte 0. File sizes are small enough that resumable downloads are not worth the complexity.
- **Retry backoff:** exponential backoff between retries. Max retries from policy (default: 3).

---

## Algorithm

```
enqueue(newList):
  1. Load current DownloadQueueItem rows from Room
  2. For each item in current queue NOT in newList:
     - If status = DOWNLOADING: cancel the active download call
     - Delete DownloadQueueItem row
     - Leave ResourceStatus as-is (NOT_DOWNLOADED — it was never completed)
  3. For each item in newList:
     - If already in queue: update priorityScore, reorder
     - If not in queue AND ResourceStatus != DOWNLOADED: insert DownloadQueueItem
  4. Sort queue by priorityScore descending
  5. Start processing if not already running

processQueue() [runs continuously while items exist]:
  1. Take top item from queue (status = QUEUED)
  2. Mark DownloadQueueItem.status = DOWNLOADING, ResourceStatus.status = DOWNLOADING
  3. Download:
     - If Resource.isS3:
         AmazonS3Client.getObject(bucketName, s3Key) → stream to temp file
     - Else:
         HTTP GET cdnUrl → stream to temp file
  4. On success:
     - Call Storage Manager.store(tempFile, resourceId, targetTier)
     - Storage Manager returns localPath
     - Update ResourceStatus: status=DOWNLOADED, localPath, version, storageTier
     - Delete DownloadQueueItem row
     - Process next item
  5. On failure:
     - Increment DownloadQueueItem.retryCount
     - If retryCount < policy.retryLimit: requeue with backoff delay
     - If retryCount >= policy.retryLimit: mark ResourceStatus.status = FAILED, delete queue item
```

---

## Room DB

### `DownloadQueueItem` (new table)

Persists the active queue so it survives app restarts.

| Field | Type | Notes |
|---|---|---|
| resourceId | String | FK — matches Realm Resource.id |
| priorityScore | Float | From Priority Engine — used for ordering |
| status | Enum | `QUEUED`, `DOWNLOADING` |
| retryCount | Int | Increments on each failure |
| targetTier | Enum | `INTERNAL`, `SD_CARD` — from Priority Engine |
| enqueuedAt | Long | Unix timestamp |

### `ResourceStatus` (existing table — written by this module)

| Field | Operation | Notes |
|---|---|---|
| status | **write** | QUEUED → DOWNLOADING → DOWNLOADED / FAILED |
| localPath | **write** | Set on successful download (from Storage Manager) |
| version | **write** | Set to Realm Resource.version at time of download |
| storageTier | **write** | INTERNAL or SD_CARD |

---

## Realm DB

None. This module does not read Realm directly. Resource URLs and metadata come from the `RankedResource` objects passed in by Priority Engine (which sourced them from Content Manifest).

---

## Dependencies

- Reads from: `DownloadQueueItem`, `ResourceStatus` Room tables
- Writes to: `DownloadQueueItem`, `ResourceStatus` Room tables
- Calls: Storage Manager (to place downloaded files)
- Uses: S3 credentials from Policy Manager (or Config API); CDN HTTP directly
- Called by: Sync Orchestrator (enqueue), UI screens (cancel, observe)

[← Back to index](modules.md)
