# doc-sync — System

See [Project document manager.md](Project%20document%20manager.md) for the full design doc — problem, solution, source layout, and Agent Skills compliance.

## What it does

- Maintains structured project documentation across Claude sessions
- Triggered manually at end of a coding session (`/doc-sync`)
- AI has live session context — knows decisions made, not just git log
- Optional sync to a shared GitHub docs repo for team use

## Core constraint

Sync must be manual in the live session. Headless AI sessions (e.g. git hooks) lack the session context that makes this useful.

## Components

| Component | Path | Role |
|---|---|---|
| SKILL.md | `doc-sync/SKILL.md` | Agent Skills manifest + full sync instructions |
| install-global.sh | `doc-sync/install-global.sh` | Copies skill to each harness's skills dir |
| install.sh | `scripts/install.sh` | Per-repo setup — writes `document.md`, stubs, post-push hook |
| compute-stats.sh | `scripts/compute-stats.sh` | Diffs docs folder against stored snapshot |
| sync-remote.sh | `scripts/sync-remote.sh` | Pushes docs to optional GitHub remote |
| document.md | repo root (per project) | Per-repo config: rules, exclusions, index snapshot |

## Source layout

```
doc-sync/
├── SKILL.md
├── install-global.sh
├── scripts/
│   ├── install.sh
│   ├── compute-stats.sh
│   └── sync-remote.sh
├── references/
│   └── document-md-format.md
└── assets/
    └── document.md.template
```

## Distribution

Built to the **Agent Skills open standard** — installable on 40+ tools including Claude Code, Codex, Gemini CLI, Cursor, Copilot, VS Code, JetBrains.

[← Back to index](doc-sync.md)
