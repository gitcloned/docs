# doc-sync — Data Model

*Thin coverage — doc-sync is file-based. All state lives in plain markdown files; no database.*

## Key files

| File | Location | Role |
|---|---|---|
| `document.md` | repo root (per project) | Config: docs_folder, sync_branches, categories, rules, index snapshot |
| `<repo-name>.md` | docs_folder | TOC / entry point for the project |
| `<category>.md` | docs_folder | One file per category (system, data, api, decisions, issues, ops) |

## State in document.md

`document.md` stores two sections under `## Documentation Index`:

- **Structure** — snapshot of every file in docs_folder (filename, line count, last modified). Used to compute the diff on next sync.
- **Semantic Map** — maps each category to the actual file(s) covering it. Updated each sync.

The line-count snapshot is the diff mechanism — not git-based.

## No shared state between sessions

Each sync reads `document.md` fresh. Nothing is carried in memory between sessions — the stored index is the only persistent state.

[← Back to index](doc-sync.md)
