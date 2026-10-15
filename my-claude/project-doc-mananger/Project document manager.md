# Project Document Manager (doc-sync)

## Problem

As a developer works across projects and Claude sessions, three core problems emerge:

- **Context loss** — when a terminal session dies, all accumulated context is gone
- **Documentation rot** — docs become stale and are not maintained as the project evolves ([Context Rot, arxiv 2606.09090](https://arxiv.org/abs/2606.09090))
- **No shared context** — collaborating across developers is hard; there is no structured shared understanding of a project

## Solution

A skill built to the **Agent Skills open standard** (agentskills.io) that maintains structured project documentation — triggered manually in the live session, governed by per-repo rules.

By targeting Agent Skills, the skill is installable by any developer regardless of which AI coding tool they use: Claude Code, OpenAI Codex, GitHub Copilot, Cursor, Gemini CLI, and 35+ others.

### Core ideas

- **Central docs folder** (e.g. `~/Documents/Projects/`) — one place for documentation across all projects
- **`document.md` per repo** — a config file the developer writes once, defining what to document and how. The AI reads this at every sync.
- **`/doc-sync` in the live session** — run at the end of a coding session; the AI has full context of decisions made, problems solved, architecture choices
- **Optional docs GitHub repo** — push the central docs to a remote repo for team sharing

## How it works

### Developer install (once per machine)

```bash
git clone <repo> ~/Documents/Code/doc-sync
bash ~/Documents/Code/doc-sync/install-global.sh
```

This copies the skill to wherever each installed harness looks for skills:
- Claude Code → `~/.claude/skills/doc-sync/`
- Codex → `~/.codex/skills/doc-sync/`
- Gemini → `~/.gemini/skills/doc-sync/`

After this, `/doc-sync` is available as a slash command in any session.

### Per-repo init (once per project)

```
/doc-sync install
  → asks: path for central docs folder (default: ~/Documents/Projects/)
  → asks: GitHub repo to sync docs to (optional)
  → writes document.md to current repo root
```

### document.md (per repo)

Created at install, editable by the developer. Controls what the AI documents and how.

```markdown
# Document Config

docs_folder: ~/Documents/Projects/
docs_repo: git@github.com:org/docs.git   # optional

## Documentation Rules

- Always document architectural decisions with rationale
- Keep a running data model section with field descriptions
- Log API contract changes
- Note any third-party service dependencies and why chosen
- Do not document internal implementation details, only interfaces and decisions
```

### Sync (manual, in the live session)

```
/doc-sync       — update docs based on what changed in this session
/doc-sync full  — regenerate full project doc from scratch
```

The AI runs in the same session where work happened — it has context of decisions made, not just git log. This is the key advantage over tools like claude-mem that replay session history.

## Technical feasibility

- **Agent Skills standard** — skill folder + SKILL.md, installable on 40+ tools
- **document.md** — plain markdown config, per-repo, developer-controlled, commit to repo to share rules with team
- **No git hook for AI invocation** — headless AI sessions lack session context; sync is always manual in the live session
- **Docs GitHub repo sync** — standard `git add/commit/push` via `sync-remote.sh` after writing the doc

## Source layout

```
doc-sync/
├── SKILL.md                         ← Agent Skills manifest + sync instructions
├── install-global.sh                ← global install (copies skill to harness dirs)
├── scripts/
│   ├── install.sh                   ← per-repo install (writes document.md)
│   ├── post-push.sh                 ← git hook stub (reminder only, no AI invocation)
│   └── sync-remote.sh               ← pushes doc to optional shared GitHub repo
├── references/
│   └── document-md-format.md        ← format spec for document.md
├── assets/
│   └── document.md.template         ← default template
└── tests/                           ← bats tests (40 passing)
```

## Distribution: Agent Skills standard

Agent Skills is an open standard originally created by Anthropic (December 2025), now cross-industry — supported by 40+ products including Claude, Codex, Copilot, Cursor, Gemini CLI, VS Code, and JetBrains.

### What "compatible" means — actionable checklist

**1. File structure**
```
doc-sync/
├── SKILL.md          ← required
├── scripts/
├── references/
└── assets/
```

**2. SKILL.md required fields**
```yaml
name: doc-sync          # matches folder name exactly
description: >          # max 1,024 chars, says what it does AND when to activate
  ...
```

**3. Body rules**
- Plain English instructions, under 5,000 tokens
- No harness-specific tool names (say "run a shell command", not "use Bash tool")
- No angle brackets in frontmatter

**4. Scripts must be harness-agnostic**
- Plain shell — no Claude SDK calls
- Works identically whether invoked from Claude, Codex, or Gemini

**5. Publish**
- Submit PR to agentskills.io registry
- Installable via `/skill install doc-sync` in any compatible tool
