# debug-user-issue — support troubleshooting & setup health

For the **support** use case: a specific child/school reports a problem, or someone asks "is school X set up well?". Start from the **symptom**, map it to the **requirement or mechanism**, then confirm with data.

## Triage tree (symptom → where to look)

| Symptom | Likely cause | Where to check |
|---|---|---|
| Lab won't start / no lab code | Teacher tablet offline when starting | Teacher must be online to get the 6-digit code (see glossary lab flow) |
| Child can't enter / wrong code | Expired or mistyped 6-digit code | Re-issue from teacher tablet |
| Child can't hear / Curie can't hear child | Audio: no external mic/headphones, wrong default device, noise | `fluento_setup_assistant` audio + mic fields (below) |
| Poor/broken conversation, drops | Network below 40 Mbps, jitter, packet loss | `fluento_setup_assistant` network fields |
| "No LLM Activities … exhausted quota" | Quota exhausted (hard stop, non-recoverable) | `analyze-session.md` error list + student quota-usage portal page |
| Idle / "forcefully stopped as user idle" | Idle triggers (5s silence threshold can be aggressive) | `analyze-session.md` error list |
| Mass dropout on a date | Backend incident (e.g. chunk-URL failure Jun 29) | `find-lab.md` / `analyze-session.md` |
| Session ran too long / cost overrun | Cue governor didn't cut off | `session-analyser.md` (Governor & Quota) |
| Empty session, nobody joined | Client never joined WebRTC | `session-analyser.md` (Client-join) + Cerebrium Logs |

## Setup / hardware health — `active_teach_fe.fluento_setup_assistant`

This table logs a **pre-lab diagnostic** run on each device: it directly measures the lab requirements. Use it for "is lab setup done well for school X?" and for audio/network/camera/system complaints.

**Scores are categorical: `pass` / `warn` / `fail` (or NULL when a check didn't run / partial).**
- `properties_overall_score` (+ `_value`) — rolled-up verdict. Also `properties_network_score`, `properties_audio_score`, `properties_camera_score`, `properties_system_score`.

**Useful raw fields by category:**
- **Network (≥40 Mbps rule):** `properties_network_download_mbps`, `properties_network_latency_ms`, `properties_network_jitter_ms`, `properties_network_packet_loss_pct`, `properties_network_stun_reachable`, `properties_network_issues`.
- **Audio (headset + boom mic):** `properties_mic_has_external_mic`, `properties_mic_is_headphone_default`, `properties_mic_noise_floor_db`, `properties_mic_speaker_confirmed`, `properties_mic_signal_detected`, `properties_mic_voice_detected`, `properties_audio_issues`. Audio is the **most common cause of a `fail` overall** even when network passes.
- **Camera (optional 1080p):** `properties_camera_has_camera`, `properties_camera_resolution`, `properties_camera_face_detected`, `properties_camera_framerate`.
- **System (Chrome rule):** `properties_is_chrome_default_browser`, `properties_webrtc_support`, `properties_cpu_*`, `properties_ram_*`, `properties_disk_*`, `properties_operating_system`.
- **Identity / location:** `properties_school_id`, `properties_device_id`, `ip`, `properties_hostname`, `properties_mac_addresses`, `properties_machine_id`.

### Setup health for a school (verified query)
Saved as `fluento_setup_health_by_school`. Pattern:
```sql
SELECT
    properties_overall_score AS overall,
    count() AS checks,
    round(avg(properties_network_download_mbps),1) AS avg_mbps,
    uniqExact(properties_device_id) AS devices,
    uniqExact(ip) AS distinct_ips
FROM active_teach_fe.fluento_setup_assistant
WHERE properties_school_id = '<school_id>'
  AND date >= today() - 30
GROUP BY properties_overall_score
ORDER BY checks DESC
```
Read it as: mostly `pass` + healthy avg Mbps = good setup. A cluster of `fail`/`warn` → drill into the sub-scores to see whether it's audio, network, or system. (Verified example: school 60 = mostly `pass`, ~76 Mbps, 11 devices / 3 IPs → healthy.)

### Gotchas
- **ClickHouse v20.12:** `GROUP BY` must list real column names — not positions, not aliases. (`GROUP BY properties_overall_score`, not `GROUP BY 1` or `GROUP BY overall`.)
- NULL overall score = the check was partial or didn't finish; don't count it as a failure.
- One device can log several checks; use `uniqExact(properties_device_id)` for device counts.

## Escalation
A support investigation often escalates to a **developer deep-dive** — the same session/portal path in `session-analyser.md` (transcript, logs, cues, events). Hand off with the `run_id` / `school_id` you already resolved.
