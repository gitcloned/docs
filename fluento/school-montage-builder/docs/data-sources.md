# Where the data comes from

The montage builder pulls from two places: ClickHouse for the session metadata, and the session analyser portal for the actual video recordings. They serve different purposes and are accessed differently.

---

## ClickHouse — for session and student metadata

ClickHouse is where all the structured event data lives. When we run Stage 1 discovery, this is where we ask questions like: how many sessions ran for school 60 in June? Which labs were they doing? How many unique students showed up?

The tables we care about most:

- `fluento.student_lab_session_init` — fires when the Pipecat bot starts for a student. This is the best proxy for "a student actually started a lab session." One row per student per session. Has `school_id`, `lab_id`, `run_id`, `sa_id` (student ID), and a timestamp.
- `fluento.student_lab_completed` — fires when a student finishes all activities in a lab. This is the source of truth for completion — don't use `student_lab_exited` for this, it contradicts.
- `fluento.student_lab_activity_status` — one row per activity lifecycle event for a student. Has an `isllm` flag so you can tell whether an activity was a real voice conversation with Ms Curie or a non-LLM activity like an MCQ. Useful for figuring out which activities to skip.
- `fluento.teacher_lab_session_end` — teacher-side summary per lab session. Has the totals: students entered, completed, errored, not started, and the overall session duration. A good quick overview when you want to understand how a lab went without querying per-student tables.

A few things to keep in mind when writing queries here:
- ClickHouse here is an old version (v20.12). `GROUP BY` has to use real column names — no positions, no aliases.
- Use `toString(properties_lab_id)` in WHERE clauses or you'll get type mismatches.
- `teacher_lab_session_end` has two rows per session (one for the attempt, one for success). Filter on `properties_status = 'success'` to get the right one.
- `student_lab_opened` fires on page navigation, not on actual lab entry. Don't use it as an entry count.

---

## Session analyser portal — for video recordings

The actual video files live in the session analyser, at `http://10.0.53.3:5179`. This is an internally hosted portal and it's where you go for anything about a specific session: the full conversation transcript, the media recordings, the Cerebrium backend logs.

For the montage builder, the relevant part is the **Media tab** on a single-session page. Each session page lives at:

```
http://10.0.53.3:5179/session/prod/<run_id>
```

Where `run_id` is in the format `cloud-cerebrium-<hash>`. You get this from ClickHouse — it's the `run_id` on `student_lab_session_init`.

The Media tab has sub-tabs for Audio, Video, and Before and After. The video recordings are what we want — they're the webcam footage of the child during the session. They're available as MP4 and HLS.

The **Before and After** tab is also worth knowing about. "Before" is a recording captured during week 1 of the program, "After" is from week 4. These are essentially the program's own progress snapshots — a child at the start of their journey and the same child a month later. These could be powerful material for certain sections of the montage.

---

## How the download works in practice

For Stage 2, the flow is:

1. Use the `run_id` values from ClickHouse to build session URLs.
2. Hit the session analyser API to get the video URLs for each run.
3. ==Download the MP4s locally into `stage-2-material/clips/`.==
4. Run per-clip analysis on each downloaded file.

The session analyser is only accessible from the internal network (10.0.53.3), so the tool needs to run from a machine that can reach it — typically a laptop connected to the office network or VPN.

---

## What we don't have (yet)

There's no direct flag in ClickHouse for "this session has a usable video recording." The presence and quality of a recording only becomes clear once you actually look at the Media tab on the portal, or download the file. That's why Stage 2 has to do a download-and-check pass rather than just filtering in the query layer.

Similarly, there's no before/after-video-generated event in ClickHouse — you have to check the portal to know if the Before and After clips exist for a given session. If we want to use those clips in the montage, the tool will need to check the Media tab for each session individually.
