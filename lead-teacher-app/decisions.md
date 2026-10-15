# lead-teacher-app — Decisions

Choices made and why, alternatives ruled out.

---

## Language and UI framework

**Kotlin + Jetpack Compose** — chosen over React Native / Flutter.

- App is Android-only (forked from existing Android app) — no cross-platform benefit
- Deep Android system access needed: SD card, WorkManager, StorageManager, DownloadManager
- React Native / Flutter add an abstraction layer that leaks on file I/O–heavy operations
- Starting fresh — use the modern UI toolkit, not XML layouts

## Background sync

**WorkManager** — chosen over foreground service or manual scheduling.

- Survives app kills and device reboots
- Handles constraints (WiFi-only, battery-not-low) natively
- Well-suited for periodic + triggered sync without holding a foreground notification permanently

## Multi-teacher model

**Gmail-style account switching** — chosen over single-login or "shared device" mode.

- Each teacher logs in once; accounts persist on the device
- Switching teachers requires no password (like Netflix profile switch)
- Resource priorities are computed per-teacher; union of all teachers' needs is what the device downloads

## Class/division/subject assignment

**Local table, teacher-managed** — chosen over pulling from an API.

- No API exists for this today
- Teachers self-declare which classes they teach; they can add/remove at any time
- Stored in Room DB (`TeacherClassAssignment`)

## Storage budget

**Dynamic cap, upper limit ~2–4 GB for internal storage** — chosen over fixed cap.

- Dynamic avoids wasting space on devices with more room
- Upper cap limits churn (too much movement between storage tiers is wasteful)
- Exact number TBD — will be tuned during testing

## Priority model

**Rule-based abstraction (code algo first, ML later)** — chosen over ML from the start.

- Rule-based is explainable and debuggable — important for a first build
- Abstracted behind an interface so the algorithm can be swapped without changing the rest of the system
- Near-term day plans get higher priority; active unit > future units

## Backend

**Reuse existing teacher app APIs** — no new backend work for this app.

- All content APIs already exist and are tested in production
- Auth model (header-based JWT) is the same
- Realm DB as content manifest is already the source of truth

## Testing environment

**Use `ft-nucleus` for dev testing, `nucleus` for prod validation.**

- `ft-nucleus.leadschool.in` — feature test env; safe for active API testing
- `nucleus.leadschool.in` — production; use for final validation only
- Staging (`stag1-nucleus`) is currently 503 — avoid
- Working prod test account: school `14527` ("Board ACE Product"), mobile `3000014527`

## Download policy

**Server-provisioned policy file, device-local, dynamically updatable** — chosen over hardcoded download rules.

- All resource download behaviour (what to download, when, how much, which tier) is governed by a policy file
- Policy file is fetched from the server and stored on the device — server can push a new policy at any time
- Enables different policies per environment (prod vs ft), user context (school type, connectivity profile), or rollout ring
- App reads the local policy file at download time; stale policy is still functional — new policy takes effect on next sync
- Policy file is the single place to tune download strategy without an app release

## S3 credential delivery

**Static IAM credentials via config API** — not signed URLs, not Cognito Identity Pool.

- `GET teacherApp/v14/config` returns AES-encrypted `s3Key` and `s3Secret`
- App decrypts and stores them in SharedPrefs; `AmazonS3Client` is built from these
- Existing app has a native `.so` fallback (`libapi-keys.so`) with credentials baked in — but that binary is not available in the new app
- New app must always call config before any S3 download; no fallback exists

## Device model whitelist

**`devicemodel` header must match an entry in `tas_device_whitelist` DB table** — not a client-side check.

- Backend middleware `validateCacheTASRequestDeviceModel` enforces this; returns `"This device is not supported"` on mismatch
- Known working models: `Lenovo TB-7304F` (prod), `Lenovo TB-X304L` (ft)
- New device models must be added to the whitelist DB before they can call any content APIs

[← Back to index](lead-teacher-app.md)
