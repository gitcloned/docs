# doc-sync — Operations

## Developer install (once per machine)

```bash
git clone <repo> ~/Documents/Code/doc-sync
bash ~/Documents/Code/doc-sync/install-global.sh
```

Copies the skill to each installed harness:
- Claude Code → `~/.claude/skills/doc-sync/`
- Codex → `~/.codex/skills/doc-sync/`
- Gemini → `~/.gemini/skills/doc-sync/`

After this, `/doc-sync` is available as a slash command in any session.

## Per-repo init (once per project)

```
/doc-sync install
```

Prompts for:
- Path to central docs folder (e.g. `~/Documents/Projects/my-app/`)
- Categories to document (system, data, api, decisions, issues, ops)
- Optional GitHub repo URL to sync docs to

Writes `document.md` to the repo root and stub category files to the docs folder. Git is optional — post-push hook is skipped if not a git repo.

## Running a sync

```
/doc-sync       — update docs based on what changed in this session
```

Run at the end of a coding session while the AI still has context of decisions made.

## Optional remote docs sync

- Set `docs_repo` in `document.md` to a GitHub remote URL
- After each sync, `sync-remote.sh` runs `git add/commit/push` for each updated file

## Environment

- No environment variables required
- All config lives in `document.md` at the repo root
- Docs folder path is set once at install and stored in `document.md`

[← Back to index](doc-sync.md)
