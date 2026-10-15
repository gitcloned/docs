# Module — Policy Manager

Fetches the download policy file from the server, stores it locally, and serves it to any module that needs rules about how to download.

---

## Function

- On sync: call server to check if a newer policy exists
- If newer: download and store locally
- Always: serve the current local policy to callers
- If never fetched and server unreachable: serve the hardcoded default policy

**Interface:**
```
syncPolicy()                  → fetch from server if outdated, store locally
getPolicy(): DownloadPolicy   → return current local policy (never null)
```

---

## Non-functional requirements

- **Offline-safe:** never blocks callers. If offline, getPolicy() returns last-fetched policy.
- **Default policy:** hardcoded defaults ship with the app. First run with no internet still works.
- **Fast reads:** getPolicy() reads from memory cache, not DB. DB is only hit on app start or after a sync.
- **Atomic writes:** write new policy to a temp location, swap on success. A failed download never corrupts the current policy.

---

## Algorithm

```
syncPolicy():
  1. GET teacherApp/v14/config → read policyVersion from response
  2. Compare with stored DownloadPolicy.version
  3. If same → return (no update needed)
  4. If different → GET policy file URL from config response
  5. Download policy JSON
  6. Write to temp → validate → swap to active
  7. Update DownloadPolicy table
  8. Refresh in-memory cache
```

If any step fails → keep existing policy, log failure, continue.

---

## What the policy file contains

| Field | What it controls |
|---|---|
| `internalStorageCap` | Max bytes to use in internal storage |
| `sdCardStorageCap` | Max bytes to use on SD card |
| `hotTierDays` | Resources within N days go to internal storage |
| `downloadOnWifiOnly` | Enforce WiFi constraint |
| `retryLimit` | Max download retries per resource |
| `syncIntervalHours` | Periodic sync frequency |
| `sdCardFallbackPolicy` | What to do when SD card is unavailable |
| `defaultPriorityWeights` | Weights for the priority scoring formula |

---

## Room DB

### `DownloadPolicy` (new table)

| Field | Type | Notes |
|---|---|---|
| id | Int | Always 1 — single row |
| version | String | Version tag from server |
| policyJson | String | Full JSON blob |
| fetchedAt | Long | Unix timestamp of last successful fetch |
| isDefault | Boolean | True if this is the hardcoded fallback, not from server |

---

## Realm DB

None. This module has no dependency on Realm.

---

## Dependencies

- Reads from: `GET teacherApp/v14/config` (policy version + URL)
- Writes to: `DownloadPolicy` Room table
- Called by: Sync Orchestrator
- Read by: Priority Engine, Download Queue, Sync Orchestrator

[← Back to index](modules.md)
