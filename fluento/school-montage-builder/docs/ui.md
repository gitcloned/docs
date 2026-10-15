# How the UI works

When you run the CLI, it prints a localhost URL and you open it in your browser. From that point on, the terminal just stays alive quietly in the background — everything happens in the browser.

The UI is deliberately simple. It shows you one stage at a time. You're not looking at a timeline editor and a download progress bar at the same time. You finish what you need to do in a stage, then move forward.

Completed stages are visible at the top as a navigation trail — you can click back to review them, but you can't accidentally edit something mid-pipeline. The active stage is where your attention is.

---

## Stage 1 — Discovery

The first screen is a summary of what the tool found. Before any footage is downloaded, before any analysis runs, you just see the shape of your material:

- How many sessions ran in the date range you gave it
- How many unique students appeared across those sessions
- Which labs they were doing, and how many sessions per lab
- A breakdown by day — so you can see if participation was spread out or concentrated

This is a sanity check. If you asked for June and you're seeing 3 sessions when you expected 30, something is off with the filter. You can adjust the school ID, date range, or lab exclusions here and re-run the discovery without touching anything else.

When the numbers look right, you click through to Stage 2.

---

## Stage 2 — Material analysis

This stage has two phases that happen while you watch.

First, downloads. The tool starts pulling video clips from the session analyser and you see them appear one by one — a small thumbnail, the student's session ID, the lab it came from, and a status indicator (downloading, analysing, done, or skipped). Clips that get filtered out automatically (too short, empty conversation, child never on screen) are shown as skipped with a reason so you understand what was excluded and why.

Second, analysis. As each clip finishes downloading, the analysis results fill in alongside it:

- Video duration and audio duration
- Conversation turns and words spoken by the child
- Visibility: face visible, upper body visible, percentage of clip where the child is clearly on screen
- A gender indicator (just for editorial balance — M/F/unclear)
- Emotion flags if any moments stood out

By the time all clips are done, you have a filterable, sortable table of everything usable. You can browse it, click a clip to watch it, and manually mark something as excluded if you don't want it in the pool even though the tool kept it. You can also manually include something the tool skipped, if you think it's worth it.

When you're happy with the pool, you move to Stage 3.

---

## Stage 3 — Structure

This screen shows you the proposed montage structure — a set of named sections with clips assigned to each one.

If you passed a structure hint YAML at the start, the sections come from that. If not, the tool used an LLM to propose something based on the material and the lab content. Either way, you see something like:

```
Introduction (2 clips suggested)
  → [clip from session X] — child greeting Ms Curie, face clearly visible, warm moment
  → [clip from session Y] — Ms Curie welcoming, good audio

Learning (4 clips suggested)
  → ...

Engagement (3 clips suggested)
  → ...

Closing (2 clips suggested)
  → ...
```

Each clip has a short note explaining why it was assigned there. You can swap a clip for a different one from the pool, remove a clip from a section, or move a clip to a different section. If you want to add a section that wasn't suggested, you can do that too.

When the structure feels right, move to Stage 4.

---

## Stage 4 — Edit and preview

This is the final stage before render. You see the full edit laid out: sections in order, clips within each section in order, with trim controls on each clip (set the in-point and out-point so only the right moment plays).

You can also:
- Add transition text between sections — a short line that appears on screen between the Introduction and the Learning section, for example
- Reorder clips by dragging
- Set the background music track (or leave it as the default)
- Choose which 3–6 students to feature consistently across sections (the tool will highlight if a student appears across multiple clips so you can pick who to lean on)

The **Preview** button stitches the current edit into a rough cut — low-res, fast — and plays it back right there in the browser. This is so you can watch the whole thing end to end and feel whether the pacing works before committing to a full render.

When it feels right, you hit **Render**. The tool produces the finished MP4 and saves it into `stage-4-edit/output/`.
