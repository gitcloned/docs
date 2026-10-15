# glossary — Fluento domain model & nomenclature

Read this whenever a term or ID in a request is unclear.

## Program structure

- **Fluento** — LEAD School's spoken-English conversational program for children, mostly delivered in school **labs**.
- **Level** — the program runs from **Level B to Level H**. A school can run different levels for different grades (commonly Level B for Class 1, Level C for Class 2, etc. — mapping varies by school).
- **Book** — each level has a book. A book = **8 units**, each unit = **4 chapters**.
- **Chapter** — the unit of teaching. Often called a **"week"** in casual requests ("which week is school 60 on?" ≈ which chapter).
- **3-day cycle per chapter:**
  - **Day 1** — teacher teaches the chapter in class.
  - **Day 2** — **the lab**: children learn with **Ms Curie**, the AI voice tutor. *This is what Bugzy is almost always about.*
  - **Day 3** — teacher asks children to present what they learnt.

## The lab

- **Ms Curie** — the AI voice tutor children talk to during the Day-2 lab.
- **Lab** = an ordered set of **activities**. A lab is **complete** only when all activities are done; on completion the child gets a **report**.
- **Activity types:**
  - **LLM-based** — real voice-to-voice conversation: **STT → LLM → TTS**. Driven by a **`flow_id`** (the LLM prompt/flow definition). These consume **quota** (see session-analyser reference).
  - **Non-LLM** — interactive fun activities that don't need an LLM (e.g. MCQ).
- **Assessment** — one or more activities in a lab are marked for assessment. After completion the backend scores the child's conversation against a **learning outcome** and its **rubric**.
- **Before/After video** — **Before** = a video captured in an activity in **week 1** (chapter 1); **After** = captured in an activity in **week 4** (chapter 4). Both surface in the session-analyser **Media → Before and After** tab.

## How a lab runs (physical flow)

1. Teacher, on her **teacher tablet**, opens the day plan → taps the CTA to **start the lab**.
2. If online, she gets a **6-digit lab code**.
3. Children sit at computers. Seating depends on infra: 1 child/machine, or 2 children/machine, or 1/machine with others waiting — depends on how many machines the school has.
4. Each child opens **`https://fluentolab.mscurie.ai`** → enters the **lab code** → selects their **name** → selects the **week/chapter** the teacher wants → starts.

## Requirements for a lab to work well

- **Internet ≥ 40 Mbps**
- **Chrome** browser
- **External headphones with boom mic**, noise-reducing
- **Webcam** — optional but important; ideally **1080p**

(These map directly onto the `fluento_setup_assistant` diagnostic scores — see `debug-user-issue.md`.)

## ID nomenclature

| ID | Meaning |
|---|---|
| **school_id** | Identifies a school |
| **lab_id** | System id of a lab |
| **activity_id** | System id of an activity |
| **flow_id** | LLM flow id — defines the prompt for an LLM-based activity |
| **run_id** | Browser-generated id for **one child's run** (typically one lab, many activities). In the analyser this appears as `cloud-cerebrium-<hash>`. **Per-student, per-session — NOT shared across students.** |
| **session_id** | Browser-generated id for **one activity session** for a child |
| **student_id** (a.k.a. `sa_id` in some tables) | Uniquely identifies a student |

## Data sources at a glance

- **ClickHouse** (via `lead-analyst`) — event tables under `fluento.*` (lab lifecycle/errors) and `active_teach_fe.fluento_setup_assistant` (pre-lab device/network diagnostics). Also `teacherapp_android.*` and Postgres operational data exist but are usually not Fluento-lab questions.
- **Session Analyser portal** (`http://10.0.53.3:5179`) — internally hosted; deep per-session view. See `session-analyser.md`.

## Tables Bugzy should know (fluento.* + setup)

Always `load_index` first — but these are the ones that matter, grouped by what they answer. `run_id` is per-student-per-session throughout; use `toString(properties_lab_id)` in WHERE; ClickHouse is v20.12 (GROUP BY real columns only).

**Per-activity (finest grain) — often the right table, and highest volume:**
- `fluento.student_lab_activity_status` — one row per activity lifecycle event: `properties_status` = `loaded → ready → connected → ended`, with **`properties_isllm`** (1 = LLM voice activity, 0 = non-LLM e.g. MCQ). Has `activity_id`, `session_id`, `run_id`, `lab_id`, `sa_id`, `school_id`. Use for: LLM-vs-non-LLM splits, per-activity completion, and `connected` as an "activity actually started for the child" signal.

**Lab lifecycle (per student per lab):**
- `student_lab_session_init` — **bot session started** (best proxy for lab entry). No client-join column.
- `student_lab_opened` — page navigation only; NOT a reliable entry count.
- `student_lab_completed` — **source of truth for completion**.
- `student_lab_exited` — exit events; do NOT use for completion (contradicts completed).
- `student_lab_error` — error events. Coded in `properties_code` (SPP-xxxx buckets + FL-codes); `isrecoverable`, `details_data_fatal`. **Exclude `SPP-4003` (normal silence) from error metrics.** See `error-codes.md`.
- `student_session_exited`, `student_session_expired` — session teardown / quota-expiry signals (low volume).
- `student_code_submitted` — child entered the 6-digit lab code.

**Navigation / selection (funnel before the lab):**
- `student_labs_page_viewed`, `student_unit_map_viewed`, `student_unit_selected`, `student_profile_selected`, `student_profiles_exited` — the pick-name / pick-week funnel. Useful for "kids reached the page but didn't start."

**Teacher side:**
- `teacher_lab_session_start` / `teacher_lab_session_end` — teacher-side lab aggregates (`students_total/completed/errored/not_started`, `session_duration_seconds`). `session_duration_seconds` is the ONLY duration in ClickHouse — it's whole-lab teacher-side, NOT the per-activity WebRTC duration (that's portal-only).
- `teacher_class_report_*`, `teacher_student_report_*`, `teacher_reports_opened`, `teacher_student_filter_applied` — teacher report viewing.

**Setup / device (separate DB):**
- `active_teach_fe.fluento_setup_assistant` — pre-lab device/network/audio/camera diagnostic + `ip`/`hostname`/`mac`. See `debug-user-issue.md`.

> The `fluento` database has ~23 tables total; the ones above are the load-bearing set. If a question needs something not listed, `describe_table` + `get_context` before querying — don't assume a column exists (e.g. there is **no** before/after-video-generated event in ClickHouse; that's portal-only).
