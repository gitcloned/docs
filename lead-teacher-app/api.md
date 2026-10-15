# lead-teacher-app — API

Endpoint contracts, auth, query params.

---

## Environments

| Name | Base URL |
|---|---|
| Production | `https://nucleus.leadschool.in/api/` |
| Feature Test | `https://ft-nucleus.leadschool.in/api/` |
| Staging | `https://stag1-nucleus.leadschool.in/api/` (currently 503) |

Use `ft-nucleus` for dev/testing. Use `nucleus` for prod validation.

---

## Auth

All requests inject these headers automatically:

| Header | Value |
|---|---|
| `Authorization` | JWT bearer token (`su[0].user_token` from login response) |
| `schoolid` | School identifier |
| `schooluserid` | Teacher's user ID (`su[0].schooluserid` from login response) |
| `academicyearid` | Current academic year |
| `devicetoken` | Device registration token (`token` field from login response) |
| `devicemodel` | **Hardcoded whitelisted value** — do NOT pass actual device model (see note below) |
| `deviceid` | Device identifier |
| `wifimacuid` | WiFi MAC address |
| `apptype` | `android` |
| `app-version-number` | Current app version (e.g. `780`) |
| `source` | `teacherapp` |

No per-call auth setup needed — headers are injected at the HTTP client layer.

**Device whitelist gate:** The backend checks `devicemodel` against a DB whitelist (`tas_device_whitelist`). Unrecognized models return `"This device is not supported by LEAD School"`. The check is a plain string match — the backend does not verify the device is actually that model.

**Important for testing on any Android device:** Always hardcode `devicemodel` to a whitelisted value. The actual device's model string will be rejected unless it has been added to the DB whitelist.

| Environment | `devicemodel` value to use |
|---|---|
| Production (`nucleus`) | `Lenovo TB-7304F` |
| Feature Test (`ft-nucleus`) | `Lenovo TB-X304L` |

Set this per-environment in the HTTP client config, not at call sites.

---

## Endpoints

| Purpose | Method + Path |
|---|---|
| Login | `POST teacherApp/authenticate/login` |
| App config (incl. S3 credentials) | `GET teacherApp/v14/config` |
| Check / download Realm DB | `GET teacherApp/v14/realmImage` |
| Resource metadata | `GET teacherapp/v13/resource/{id}` |
| Content download by class-subject | `POST teacherApp/v13/internetaware/content/download/classSubject` |
| Content download incremental (USM) | `POST teacherApp/v13/internetaware/content/download/usm/incremental` |
| Actual resource files | CDN via HTTP GET, or S3 via AWS SDK |

---

## Response schemas

### Login (`POST teacherApp/authenticate/login`)
Key fields used by the app:
- `su[0].user_token` → `Authorization` header (JWT)
- `su[0].schooluserid` → `schooluserid` header
- `token` → `devicetoken` header
- `su[0].schoolid`, `su[0].academicyearid` → respective headers

### realmImage (`GET teacherApp/v14/realmImage`)
Returns location of the Realm DB zip in S3:

| Field | Notes |
|---|---|
| `bucketName` | S3 bucket name (e.g. `ta-realm`) |
| `directory` | Path within bucket (e.g. `production/14527/S8/`) |
| `fileName` | Zip file name (e.g. `S8_AY_10_14527.zip`) |
| `size` | File size in bytes |
| `checksumHash` | MD5 hash — use to skip download if local copy matches |
| `force` | Boolean — if true, re-download even if hash matches |

S3 bucket is private — direct URL returns 403. App downloads using `AmazonS3Client` with IAM credentials obtained from the config API (see S3 download flow below).

### Config (`GET teacherApp/v14/config`)
Returns app-wide configuration. Key fields for S3:

| Field | Notes |
|---|---|
| `s3Key` | AES-encrypted AWS access key ID |
| `s3Secret` | AES-encrypted AWS secret access key |

Credentials are decrypted with `CryptoService` and stored in SharedPrefs. Must be fetched before any S3 download.

### Resource metadata (`GET teacherapp/v13/resource/{id}`)
Returns metadata for a single resource (file type, CDN/S3 URL, version).

---

## Notes

- **Call sequence for S3:** `login → config → realmImage → S3 download`. Config must run first to populate credentials.
- **S3 download — no signed URLs.** Uses `AmazonS3Client` (AWS Android SDK) with static IAM credentials from the config API. Region: `ap-south-1` (Mumbai). The existing app has a native `.so` fallback for credentials, but that binary is not available in the new app — config API is the only source.
- **Realm DB first.** The app calls `realmImage` on sync to get the latest content manifest — units, day plans, resource lists. Everything else is derived from that.
- **CDN vs S3.** Resource files come from CDN (HTTP GET) or S3 (AWS SDK) depending on the resource. The download layer handles both.
- **Incremental downloads.** The USM incremental endpoint avoids re-downloading unchanged content — use this for background sync. The classSubject endpoint is for on-demand or first-time pulls.
- **Content download on first sync returns empty.** `classSubject` and `usm/incremental` return empty resource arrays until the Realm zip is downloaded and parsed. The Realm zip is the source of truth for the initial content list.
- These APIs are shared with the existing teacher app — no backend changes needed.

[← Back to index](lead-teacher-app.md)
