# Agent — Overview

Architecture, session lifecycle, and request/response flow.

---

## What it is

A TypeScript AI tutor that runs a Gemini-powered teaching session for one student × concept pair. It is structured as a stateless engine driven by a compiled plan, not an open-ended LLM conversation.

```
prodigy/agent/
├── src/
│   ├── agent.ts          # newAgent() — public interface
│   ├── engine.ts         # TurnEngine — Gemini agentic loop
│   ├── context.ts        # buildContext() — loads session data from LP
│   ├── session-manager.ts# SessionManager — in-memory session store
│   ├── skills.ts         # SkillLoader — loads SKILL.md files
│   ├── transport.ts      # Transport interface
│   ├── plan-builder.ts   # Compiles probingTree → PlanStep[]
│   ├── api.ts            # HTTP clients for CMS + LP
│   ├── types.ts          # Domain types
│   ├── tools/            # Tool implementations
│   └── transports/       # Transport implementations
├── skills/               # One folder per concept state
│   └── probing/SKILL.md
├── prompts/base.md       # Base system prompt
└── scripts/cli.mjs       # CLI entry point
```

---

## High-level architecture

```
CLI (cli.mjs)
      │
      ▼
SessionManager ──────────────────────────────────────┐
  create(studentId, conceptId)                        │
    → LP: find/create Journey + JourneyNode           │
    → buildContext() → Concept, Session, Plan         │
  join(sessionId, transport)                          │
    → wires Transport events to agent                 │
  end(sessionId)                                      │
    → persists history to LP                          │
      │                                               │
      ▼                                               ▼
  Agent (newAgent)                            Transport
    initiate()  ←── 'connected' event         StdinTransport
    send(text)  ←── 'message' event           WebSocket (future)
      │
      ▼
  TurnEngine.run(skill, ctx)
    → Gemini API (system prompt + history + tools)
    → tool calls handled locally
    → yields TurnEvent stream
```

---

## Session lifecycle

```
SessionManager.create()
      │
      ├─ LP: find or create Journey (studentId)
      ├─ LP: find or create JourneyNode (journeyId + conceptId)
      └─ buildContext()
           ├─ CMS: fetch Concept
           ├─ LP: fetch JourneyNode
           ├─ LP: find 'started' session or create new ('initialised')
           ├─ LP: fetch Memories
           └─ compile Plan fresh from probingTree
                 ↓
      SessionManager.join(transport)
           ├─ transport 'connected' → agent.initiate()
           │     └─ TurnEngine runs → agent speaks first
           │           └─ first text yielded → PATCH session: 'started'
           ├─ transport 'message' → agent.send(text)
           │     └─ TurnEngine runs → agent responds
           └─ transport 'disconnected' → SessionManager.end()
                 └─ if started: PATCH session history + 'completed'
                    if initialised: discard (never persisted)
```

**Status values:**

| Status | Meaning |
|---|---|
| `initialised` | Session record created; agent has not spoken yet |
| `started` | Agent produced first text response |
| `completed` | Student exited; history saved to LP |

Only `started` sessions are resumed on re-run. `initialised` sessions are silently dropped.

---

## Turn flow

Each time the student sends a message:

```
student types "1"
      │
      ▼
StdinTransport
  readline fires → messageHandlers called with "1"
      │
      ▼
SessionManager handler
  agent.send("1") → appendAndRun('student', '1')
      │
      ├─ history.push({ role: 'student', content: '1' })
      └─ turn() called
            │
            ▼
      TurnEngine.run(skill, ctx)
        1. map ctx.session.history → Gemini Content[]
        2. chatHistory = all but last; lastMessage = last entry
        3. ai.chats.create({ history: chatHistory, systemInstruction, tools })
        4. chat.sendMessage({ message: lastMessage })
        5. while functionCalls present:
             → execute tool locally
             → chat.sendMessage({ message: toolResults })
        6. yield TurnEvents (text, tool_call, tool_result, error)
            │
            ▼
      SessionManager handler
        for each event → transport.send(event)
            │
            ▼
      StdinTransport.send()
        text       → print "Tutor: ..."
        tool_call  → print "  → [toolName]"
        error      → print "[Error] ..."
            │
            ▼
      turn() completes
        agentText saved to history
        prompt() called → readline waits for next input
```

---

## History format

History lives in `ctx.session.history` (in-memory during session, flushed to LP on end).

```
[
  { role: 'student', content: 'Begin the session.' },  ← synthetic seed (Gemini requires first msg to be user)
  { role: 'agent',   content: 'Hi! Solve this...' },
  { role: 'student', content: '1' },
  { role: 'agent',   content: 'Correct! Now...' },
  ...
]
```

Gemini receives: `chatHistory = history[0..-2]`, `lastMessage = history[-1].content`.

---

[← Back to index](../prodigy.md)
