# session-analyser — the portal (http://10.0.53.3:5179)

Internally hosted per-session inspection portal. Use this for any question about **one** session/school/flow, and for anything a pasted analyser link references. It is the source of truth for **quota/timer, cues, transcript, media, Cerebrium logs, and assessment** of an individual run — things that are hard or impossible to see in ClickHouse.

> **Reading the portal:** if a connector/tool that can fetch the analyser page is available, use it to open the run and read the actual field values (Session Timer, Quota, tab contents), then answer with the numbers. If no such tool is available, guide the user to the exact fields to read instead. The diagnostic logic below is the same either way.

## URL patterns

Extract IDs from whatever the user pastes and reason from them.

| URL | What it shows |
|---|---|
| `…/session-analytics?env=prod&school_id=60` | All sessions for a school |
| `…/session-analytics?env=prod&school_id=60&flow_id=<flow_id>` | Sessions for a school + LLM flow |
| `…/session-analytics?env=prod&school_id=60&flow_id=<flow_id>&lab_id=1` | Narrowed to a lab |
| `…/session/prod/<run_id>` | **One run** — `run_id` = `cloud-cerebrium-<hash>`. The main deep-dive page. |
| `…/quota-usage/prod/<school_id>/students/<student_id>` | A student's quota usage |

`env=prod` is the usual environment.

## Anatomy of a single-session page (`/session/prod/<run_id>`)

**Session Timer**
- `WebRTC Duration` — actual session length (ms + s). The real "how long did this run" number.
- `Soft Cue Fired` — timestamp, or `—` if never fired.
- `Hard Cue Fired` — timestamp, or `—` if never fired.

**Quota**
- `Allocated Soft Limit` (e.g. 5 min) — crossing it fires the **Soft Cue**.
- `Allocated Hard Limit` (e.g. 7 min) — crossing it fires the **Hard Cue**.
- `Student Remaining at Start` — the child's remaining quota balance when the run began (quota is a consumable balance; overrunning burns quota = cost).
- `Actual vs Allocated` — WebRTC duration as % of the hard limit.
- `Action` — e.g. `full_flow` (ran the complete activity flow).

**Tabs:** `Metrics` · `Conversation` · `Assessment` · `Media` · `Logs` · `Session Events`
- **Conversation** — total messages / turns / user words / assistant words, and the full transcript. Turns are tagged **USER**, **ASSISTANT** (Curie, with `<stage>`/`<speaker>` markup, may be multilingual), and **SYSTEM** (injected instructions). "Play Audio" may say *No recording available*.
- **Media** — sub-tabs **Audio (n)**, **Video (n)**, **Before and After** (MP4 + HLS; before = week-1 capture, after = week-4 capture).
- **Logs** — Cerebrium backend logs for the run.
- **Assessment** — rubric-based scoring output (✓ when present).
- **Session Events** — raw event stream.

## The cue governor — how the session timer actually works

The governor is a **step in the Pipecat pipeline**. It does **not** kill the WebRTC call. On crossing a limit it **injects a system prompt** telling Ms Curie to wrap up:
- **Soft Cue** (soft limit) → gentle "start wrapping up" signal.
- **Hard Cue** (hard limit) → injects a SYSTEM message like *"the student's session time has ended — give a warm, encouraging closing"*, and Curie delivers a closing turn. The call then ends **gracefully**, so a small tail past the hard limit (the wrap-up) is **normal and healthy**.

**Healthy example:** WebRTC 525s, Hard Cue Fired at 420s (=7-min hard limit) → cue fired on time, ~105s graceful wrap-up. Fine.

### Diagnosing "it didn't cut off / cost overrun" (e.g. "10-min warning nahi hua, ₹20 lag gaya")
Compare **WebRTC Duration** vs **Hard Cue Fired** vs **Allocated Hard Limit**:
- Duration ≫ hard limit **and** `Hard Cue Fired = —` → **(i) the cue never fired** (governor step didn't trigger). Backend/governor bug.
- Duration ≫ hard limit **but** Hard Cue Fired *is* set → **(ii) the cue fired but the wrap-up didn't end the session** (Curie kept going / client never disconnected).
- These are different bugs — always distinguish which one, and quote the three numbers you compared. Cross-check the **Logs** and **Session Events** tabs for the governor step.

## "Client / student never joined" (empty / wasted session)
Symptom: the backend bot ran (quota reserved, cost incurred) but no child ever connected.
- **Signal:** the **Conversation** tab has **only SYSTEM messages and no USER turns** (and typically near-zero user words / very short or oddly-shaped WebRTC duration).
- **Confirm** in the **Logs** tab (Cerebrium logs) — they show whether the client peer ever joined the WebRTC session.
- For "too many such sessions lately", this becomes a cross-session question → hand to `lead-analyst`. **Note:** `fluento.student_lab_session_init` fires when the **bot** starts (backend up) but does **not** record whether the **client** joined — there is no join-status column there. So a no-join can't be counted from `session_init` alone; the reliable signals are the portal transcript (SYSTEM-only, no USER turns) and Cerebrium **Logs**. In ClickHouse, `fluento.student_lab_activity_status` reaching `connected` (esp. for `isllm=1`) indicates the activity actually started for the child — useful as a cross-session proxy, though ⚠ verify against a known no-join case first. If counting across sessions, ⚠ verify which table/field actually records user-turn presence before trusting a number.

## Before/After video present or missing
- Check **Media → Before and After**. "Before" should exist once week-1 is done, "after" once week-4 is done.
- "Any sessions today where before & after video was generated?" is a cross-session question → `lead-analyst` (⚠ investigate which table/flag records the generated media before answering; the portal is the per-session confirmation).

## "Attending from home" — ⚠ investigate
Labs are meant to be in-school, so home attendance is an anomaly worth flagging, but there is **no single confirmed field**. Approach with `lead-analyst` on `active_teach_fe.fluento_setup_assistant`, which carries `ip`, `hostname`, `mac_addresses`, `machine_id`:
- A school normally shows a **small set of shared IPs** across many devices (e.g. school 60: ~11 devices / 3 IPs). A run from an **IP/hostname outside that baseline**, or an unusual one-device-one-IP pattern, is the signal.
- Form the school's normal baseline first, then look for outliers. **Verify against real rows** and state confidence — do not assert "from home" from a single field alone.
