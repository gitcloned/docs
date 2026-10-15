# How it works

## Starting a project

Everything begins with the CLI. You run something like:

```bash
montage start \
  --school 60 \
  --from 2025-06-01 \
  --to 2025-06-30 \
  --skip-activities 12,15 \
  --structure-hint structure.yaml
```

At minimum, you give it a school ID and a date range. Everything else is optional — you can skip specific activity IDs if you know they produce footage that won't work (a particular MCQ activity, say, where children aren't talking), and you can pass a structure hint YAML if you already have a sense of what sections you want the video to have.

When you run this, two things happen: it creates a project folder (named something like `school-60_jun-2025/`), and it starts a local web server that you open in your browser. From that point on, you work in the browser. The terminal just stays alive in the background.

## The project folder

The project folder is the source of truth for everything. It holds all the downloaded footage, all the analysis, the structure, the edit — everything. If you ever need to pick up where you left off, or hand the project to someone else, the folder has it all.

Inside, the structure looks like this:

```
school-60_jun-2025/
  config.yaml          ← the inputs you gave the CLI (school, dates, hints)
  stage-1-discovery/   ← session and student stats pulled from the data
  stage-2-material/    ← downloaded clips and per-clip analysis
  stage-3-structure/   ← the suggested (and confirmed) montage structure
  stage-4-edit/        ← the final edit: clip selections, trim points, output
```

Each stage writes its output into its own sub-folder. The next stage reads from that folder. This means the stages are independent — if you want to re-run stage 3 with a different structure hint, you just change the hint and re-run stage 3. You don't re-download all the footage. You don't re-run the analysis. You just pick up from where stage 2 left off.

This repeatability is intentional. Montage editing involves a lot of back-and-forth — you'll realise the structure needs adjusting, or you'll want to swap one clip for another. The folder-per-stage design means you can iterate freely without starting over.

## The four stages

### Stage 1 — Discovery

The first thing the tool does is figure out what material exists. It queries the session data for the school and date range you gave it: how many sessions ran, how many students participated, which labs they were doing, which activities. This is purely a data-gathering step — nothing is downloaded yet.

At the end of this stage, you have a clear picture of the raw pool. You can see if the date range gave you enough sessions, if certain labs dominated, if some days had very low participation. You can also adjust the filter here — exclude certain labs, narrow the date range — before moving on.

Stage 1 output: `stage-1-discovery/sessions.json` and a summary that the UI renders.

### Stage 2 — Material analysis

This is the heavy stage. The tool downloads the actual video recordings from the session analyser, one by one, into `stage-2-material/clips/`. As it downloads, it runs analysis on each clip:

- How long is the video, and how long is the usable audio?
- How many conversation turns were there, and how many words did the child actually speak?
- Is the child visible in the frame? Is their face visible? Is it just face, or upper body too?
- Roughly what percentage of the clip is the child clearly on screen?
- Is the child a boy or a girl? (useful for editorial balance across the montage)
- Are there any moments of noticeable emotion — laughter, surprise, excitement?

Clips that are clearly unusable get filtered out automatically: too short, no audio, child never appears on screen, conversation was empty. The rest get annotated with all the metadata above and saved into `stage-2-material/clips.json`.

This stage takes the longest. It can run overnight if there are a lot of sessions.

### Stage 3 — Structure suggestion

With the analysed material in hand, the tool now suggests a montage structure. If you passed a `--structure-hint` YAML at the start, it uses that as the shape. If not, it uses an LLM to look at what material exists and propose something sensible based on what the lab content was and what moments are available.

The structure is a set of named sections — Introduction, Learning, Engagement, Closing, or whatever the hint defines — each mapped to a set of candidate clips from the pool, with a reasoning note for why each clip was assigned there.

This gets saved to `stage-3-structure/structure.yaml`. You can edit this file directly, or use the UI to swap clips around, before moving to the final stage.

### Stage 4 — Edit and preview

The final stage is where you make the edit feel right. The UI shows you the structure with the assigned clips, and you can:

- Swap a clip for a different one from the same pool
- Trim the in and out points of a clip
- Reorder clips within a section
- Add or remove transition text between sections

You can also run a preview — the tool stitches the current edit together into a rough cut so you can watch it end to end before committing to a full render. Once you're happy, you kick off the final render and it produces the finished MP4.
