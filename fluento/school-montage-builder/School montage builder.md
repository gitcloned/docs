# School Montage Builder

When a school has been running Fluento for a while, something quietly accumulates: hundreds of small moments, captured on webcam, of children talking with Ms Curie. A child nervously saying hello. A child laughing when they get something right. A child promising they'll practice at home. Most of that footage just sits there, unedited, in session storage.

This tool turns it into something worth showing.

The school montage builder takes all the session recordings from a school's Fluento labs — raw, unedited, real — and assembles them into a single structured video. Something a principal could play at a parent evening. Something that actually communicates what these children have been doing and how much they've grown.

The structure of the video follows a natural arc: children greeting Ms Curie, children doing the learning activity, moments of real engagement and emotion, and then the closing — children wrapping up, making promises, getting their report. Threaded through it all are a handful of the same children appearing again and again, so whoever's watching starts to feel like they know them.

## How to use it

You run it from the terminal. You give it a school, a date range, and optionally some hints about which labs to focus on or avoid. It creates a project folder, starts a local web server, and walks you through the rest in your browser — stage by stage.

## Documentation

- [How it works](docs/how-it-works.md) — the CLI, the stage pipeline, how project folders are structured, and why things are built to be repeatable
- [How the UI works](docs/ui.md) — what the web server shows you at each stage and what you're actually doing there
- [What the MVP is](docs/mvp.md) — what we're building first and what comes later
- [Where the data comes from](docs/data-sources.md) — how we pull session metadata and download the actual video recordings
