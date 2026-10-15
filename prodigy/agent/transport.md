# Agent — Transport

Transport interface, event types, log channel, and StdinTransport implementation.

---

## Transport interface

`src/transport.ts` — abstracts I/O. The agent and session manager never know which transport is active.

```ts
interface Transport {
  handle(event: TurnEvent): void              // system → transport: conversation events
  onLog(entry: LogEntry): void                // system → transport: operational logs (filterable)
  on(event: 'message',      handler: (text) => void)   // user → agent
  on(event: 'connected',    handler: () => void)        // session started
  on(event: 'disconnected', handler: () => void)        // session ended
}
```

**Two output channels:**

| Method | What goes through it | Filterable? |
|---|---|---|
| `handle(event)` | TurnEvents — text, tool calls, errors, action signals | No — always shown |
| `onLog(entry)` | Operational logs — connect, disconnect, state changes, debug | Yes — by log level |

**Input events (registered via `on()`):**

| Event | Direction | Who fires it |
|---|---|---|
| `on('message')` | user → agent | Transport fires when user sends input |
| `on('connected')` | — | Transport fires when ready; agent initiates first |
| `on('disconnected')` | — | Transport fires on exit; SessionManager persists + cleans up |

`SessionManager.join()` wires `ctx.log = entry => transport.onLog(entry)` — so any code that calls `ctx.log(...)` routes through the active transport's log channel.

---

## LogEntry

```ts
type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  level:   LogLevel;
  message: string;
}
```

Defined in `src/types.ts` (not transport-specific — usable anywhere in the agent).

---

## TurnEvent types

Emitted by `TurnEngine`, forwarded to transport via `SessionManager.join()`:

| Type | Fields | Display |
|---|---|---|
| `text` | `content: string` | Agent's spoken response |
| `tool_call` | `name: string, args: unknown` | Tool the agent invoked |
| `tool_result` | `name: string, result: unknown` | Tool's return value |
| `action` | `action: unknown` | Signal from a tool for the transport to act on |
| `error` | `message: string` | Any unhandled error in the turn |

Transports are free to ignore or format any event type. StdinTransport suppresses `tool_result`.

**`action` events** are yielded by the engine immediately after the `tool_result` event when a tool result contains an `action` field. The engine emits it; the transport decides whether to act.

| Action type | Source | Effect |
|---|---|---|
| `send-ok` | `update_step` prereq redirect | Canvas auto-sends "Ok" to start the prereq turn immediately |
| `parallel-start` | Output parser (LLM writes `parallel:start`) | Canvas begins parallel block — renders next blocks simultaneously |
| `parallel-end` | Output parser | Canvas ends parallel block |
| `open-camera` | Output parser (LLM writes `camera: open`) | Canvas opens student camera UI |

**`send-ok` detail:** When a prereq redirect fires mid-session, the engine breaks the LLM loop (no further text generated), emits `send-ok`, and stops. The transport auto-sends "Ok" to trigger a fresh agent turn with the prereq plan loaded. The student sees no gap.

---

## StdinTransport

`src/transports/stdin.ts` — readline-based terminal transport.

### Constructor options

```ts
interface StdinTransportOptions {
  studentName?:   string;         // label for the input prompt (default: 'You')
  logLevel?:      LogLevel | 'none';  // minimum log level to print (default: 'debug')
  hideToolCalls?: boolean;        // suppress tool_call events (default: false)
}
```

### Start flow

```
start()
  │
  ├─ readline.createInterface(stdin, stdout)
  │
  ├─ define prompt() function
  │     readline.question(`\n${studentName}: `, async (input) => {
  │       if /exit → fire disconnected, close
  │       await all messageHandlers(text)     ← blocks until agent responds
  │       if pendingAutoSend:
  │         pendingAutoSend = false
  │         print "[Action] Sending auto ok"
  │         await all messageHandlers('Ok')   ← auto-advance for redirect turns
  │       prompt()                            ← ask for next input
  │     })
  │
  ├─ on('close') → fire disconnectedHandlers
  │
  └─ Promise.all(connectedHandlers)           ← agent speaks first
         .catch(err → print [Error])
         .finally(→ prompt())                ← then open input
```

**Key design:** `await h(text)` blocks re-prompting until the agent fully responds. This prevents the input prompt appearing mid-response.

**Auto-send on redirect:** When a turn emits `{ type: 'action', action: { type: 'send-ok' } }`, `handle()` sets `pendingAutoSend = true`. After the turn completes, stdin fires "Ok" automatically so the next turn starts immediately with the new prereq plan loaded. No user input required.

### handle() — output formatting

```
event.type == 'text'                         →  "\nTutor: {content}\n"   (stdout)
event.type == 'tool_call' (not hidden)       →  "  → [{name}] {args}\n"  (stdout)
event.type == 'action'                       →  sets pendingAutoSend = true (no output)
event.type == 'error'                        →  "\n[Error] {message}\n"   (stdout)
tool_result                                  →  (suppressed)
```

### onLog() — log output

Writes to **stderr**. Filtered by `logLevel` — entries below the threshold are dropped silently.

```
[DEBUG] message    → gray   (level: debug)
[INFO]  message    → cyan   (level: info)
[WARN]  message    → yellow (level: warn)
[ERROR] message    → red    (level: error)
```

ANSI colour codes inline — no extra dependency needed.

`[Error]` from `handle()` (TurnEvent) is always shown regardless of `logLevel` — it goes through a different channel.

---

## CLI flags (scripts/cli.mjs)

| Flag | Values | Default | Effect |
|---|---|---|---|
| `--log-level` | `debug\|info\|warn\|error\|none` | `debug` | Minimum log level shown in stderr |
| `--hide-tool-calls` | (flag, no value) | false | Suppress `tool_call` events from stdout |
| `--student` | string | `test-student-1` | Student ID for the session |

`--log-level none` silences all operational logs. Errors from `handle()` (TurnEvents) are unaffected.

---

---

## WebSocketTransport

`src/transports/ws.ts` — serves both the WebSocket and an optional HTML test page on the same port.

### Constructor options

```ts
interface WebSocketTransportOptions {
  port?:      number;           // default 32004
  logLevel?:  LogLevel | 'none';
  medium?:    BaseMedium;       // CanvasMedium (wires output/input modalities)
  serveHtml?: string;           // path to HTML file served at GET /
}
```

### Protocol

**Client → server:** `{ type: 'message', text?, audio?, images?, activity? }`

**Server → client:** JSON-serialised `TurnEvent` (text_chunk, tool_call, tool_result, action, error, etc.)

One WebSocket client at a time — second connection is rejected with code 1008.

### Output modalities (CanvasMedium)

The LLM outputs structured text. `OutputParser` scans for key lines and routes to the registered modality:

```
speak: Text to say aloud          → TTS audio (Inworld)
write: Text to animate on canvas  → write block
model: function-graph             → interactive 2D graph
/equation: y = 2x + 1
/action: plot
model3d: cuboid-volume-01         → 3D unit-cube model
/action: build-base
annotate: Short note              → highlight on canvas text
/mark: underline
/target: exact text to mark
camera: open                      → open student camera
parallel:start … parallel:end    → render blocks simultaneously
question: Q01                     → question frame on canvas
question: end                     → close question frame
```

### Input modalities (CanvasMedium)

| Modality | What it receives | Processing |
|---|---|---|
| `text` | Typed student message | Identity — passed as-is |
| `audio` | Base64 audio blob | Groq Whisper STT → transcript |
| `image` | JPEG blob | Stored in `image-store`, `[image]` placeholder injected into history |

### CLI flags

| Flag | Values | Default | Effect |
|---|---|---|---|
| `--medium` | `stdin\|canvas` | `stdin` | Transport type |
| `--port` | number | `32004` | WebSocket port |
| `--tts` | `inworld\|test\|none` | env var | TTS provider override |
| `--state` | ConceptState | — | Force a specific node state (skips buildContext state lookup) |
| `--log-level` | `debug\|info\|warn\|error\|none` | `debug` | Minimum log level |
| `--student` | string | `test-student-1` | Student ID |
| `--hide-tool-calls` | flag | false | Suppress tool_call events |

---

[← Back to index](../prodigy.md)
