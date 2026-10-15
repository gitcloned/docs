# prodigy

| | |
|---|---|
| [System](system.md) | Architecture, component structure, tech stack |
| [Data Model](data.md) | Entities, fields, storage decisions |
| [Decisions](decisions.md) | Choices made and why, alternatives ruled out |

## Agent

| | |
|---|---|
| [Overview](agent/overview.md) | Architecture, session lifecycle, turn flow |
| [Harness](agent/harness.md) | TurnEngine, SessionManager, AgentContext, plan compilation |
| [Skills](agent/skills.md) | Skill system, SKILL.md format, state → skill mapping |
| [Tools](agent/tools.md) | All callable tools: plan, state, memory |
| [Transport](agent/transport.md) | Transport interface, TurnEvent types, StdinTransport |

## API

| | |
|---|---|
| [LP Service](api/lp.md) | Learning Progression endpoints (port 3002) |
| [CMS Backend](api/cms.md) | CMS content endpoints (port 3001) |

*Maintained by doc-sync. Run `/doc-sync` to update.*
