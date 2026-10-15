# What the MVP is

The goal for the MVP is simple: produce one real, watchable montage for one school, end to end, without too much manual work. It doesn't have to be perfect. It has to be good enough that someone watches it and feels something.

Here's what that means in terms of what we build and what we skip for now.

---

## What's in the MVP

**The CLI and project folder structure.** You run one command, it creates the folder, it starts the server. The config lives in `config.yaml` so the project is reproducible and shareable.

**Stage 1 — Discovery.** Pull session and student counts from ClickHouse for the given school and date range. Show them in the UI. Let the user adjust the filter before proceeding. This is mostly a query and a display.

**Stage 2 — Material download and basic analysis.** Download the actual video clips from the session analyser. Run per-clip analysis covering: video and audio duration, conversation turns and words spoken, whether the child's face is visible, and rough percentage of time they're on screen. Filter out anything clearly unusable. The emotion detection and gender detection can be simple or even manual at this stage — the important thing is the pipeline works and the good clips make it through.

**Stage 3 — Structure with a hint.** Accept a structure hint YAML and use it to assign clips to sections. The LLM-suggested structure (no hint) can come later — for the MVP, we assume the person running the tool knows roughly what sections they want and provides the YAML. The UI shows the assignment and lets you swap clips around.

**Stage 4 — Edit and render.** Trim controls, section ordering, transition text, background music track. A preview that plays the rough cut in the browser. A final render that produces an MP4.

---

## What we're deliberately skipping for now

**Fully automatic structure suggestion (no hint).** The LLM-driven structure where it looks at the material and proposes the sections entirely on its own — that's a nice feature but not needed to produce the first montage. The YAML hint is good enough.

**Emotion detection.** Identifying moments of laughter, surprise, or peak engagement from video frames is genuinely hard to do well. For the MVP, emotional moments can be flagged manually by the user in Stage 2 — they browse the clips and tag the good ones. Automated emotion detection is a post-MVP improvement.

**Student continuity across sections.** The idea of picking 3–6 children and making sure the same faces appear across Introduction, Learning, and Closing — this matters a lot for the final quality of the montage, but the logic to enforce it automatically is complex. For the MVP, the editor does this by eye in Stage 4. We can make the UI highlight when the same student appears in multiple assigned clips to make it easier.

**Multiple music track options and audio mixing.** For now, just one background music track, applied at a fixed volume. Proper audio ducking and mixing can wait.

**Cloud render / sharing.** The output is a local MP4. Uploading to a shared drive or school portal is out of scope for now.

---

## What "done" looks like for the MVP

You run the CLI for school 60, give it a June date range, wait for the downloads and analysis, pick a structure, make a few manual edits, hit preview, tweak trim points, and render. The output is a 3–5 minute MP4 that a school coordinator could watch and feel proud of, with background music, transition text between sections, and a handful of real children's real moments from their sessions with Ms Curie.

That's the bar.
