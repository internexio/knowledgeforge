# KF-VSCode Implementation Plan
**Status:** Ready to build  
**Date:** 2026-04-19  
**Depends on:** `plans/kf-vscode-platform.md` (high-level), `platform-bindings/vscode.yaml`

---

## Dependency Graph (explicit)

Build order derived from hard dependencies. Parallel clusters can run simultaneously.

```
Phase 0 (DONE): local.dev-keys installed → dev-api-keys AuthProvider live

Phase 1 — Parallel, no blockers:
  A: platform-bindings/vscode.yaml          (written — see this repo)
  B: extension package.json + tsconfig.json (new repo scaffold)
  C: copy agent-anthropic.ts + jsonc-edit.ts into KF-VSCode src/

Phase 2 — After Phase 1A:
  D: kf-compile --target vscode             (emits src/resources/kf-modes/*.md)

Phase 3 — After Phase 1B + 2D (parallel):
  E: mode-router.ts                         (reads kf-mode-registry.json)
  F: key-resolution.ts                      (calls vscode.authentication.getSession)
  G: stream-batcher.ts                      (written to AgentEvents interface only)

Phase 4 — After Phase 3:
  H: KFSession.ts                           (assembles E + F + G + agent-anthropic)

Phase 5 — After Phase 4 (parallel):
  I: KFPanel.ts (webview)
  J: sse-server.ts (optional browser variant)

Phase 6:
  K: tsc --noEmit clean pass + vsce package
```

Critical path: `vscode.yaml → kf-compile → mode resources → KFSession → KFPanel`

---

## Handoff Contracts (exact interfaces)

### Handoff 1: AllOfUs AuthProvider → KFSession

```typescript
// In KFSession (lazy init, NOT in activate()):
const session = await vscode.authentication.getSession(
  'dev-api-keys',          // provider ID registered by local.dev-keys
  ['anthropic'],           // scope = key name in Keychain
  { createIfNone: false }
);
if (!session) {
  vscode.window.showErrorMessage(
    'KF: Anthropic key not found. Run "Dev Keys: Open Setup Panel" to add it.'
  );
  return;
}
const apiKey: string = session.accessToken;
```

**Watch for:** `extensionDependencies` in `package.json` uses the extension package ID (`local.dev-keys`), NOT the auth provider ID (`dev-api-keys`). These are different strings. Confusing them gives a "provider not found" at runtime with no useful message.

**Must also subscribe to:**
```typescript
vscode.authentication.onDidChangeSessions((e) => {
  if (e.provider.id === 'dev-api-keys') {
    kfSession.invalidateKey(); // forces re-fetch on next send()
  }
});
```
Without this, user updates key in AllOfUs → KF still uses stale key → silent 401.

---

### Handoff 2: AnthropicAgent events → stream batcher → webview

```typescript
// stream-batcher.ts — 100ms batch window
class StreamBatcher {
  private buffer = '';
  private timer: NodeJS.Timeout | null = null;
  constructor(private readonly flush: (delta: string, accumulated: string) => void) {}

  push(delta: string, accumulated: string) {
    this.buffer += delta;
    if (!this.timer) {
      this.timer = setTimeout(() => {
        this.flush(this.buffer, accumulated);
        this.buffer = '';
        this.timer = null;
      }, 100);
    }
  }
}

// Wire in KFSession:
const batcher = new StreamBatcher((delta, accumulated) => {
  panel.webview.postMessage({ type: 'stream:batch', delta, accumulated });
  // SSE broadcast if browser client connected:
  sseServer?.broadcast('stream:batch', { delta, accumulated });
});

agent.on('stream:delta', (delta, accumulated) => batcher.push(delta, accumulated));
```

**Critical:** Forward `accumulated` (not reconstructed from deltas). If a batch is dropped or delayed, webview resets to last `accumulated` — no desync.

---

### Handoff 3: KFSession state → webview on panel reopen

```typescript
// KFPanel.ts — singleton pattern (from setup-panel.ts)
static show(session: KFSession, extensionUri: vscode.Uri) {
  if (KFPanel.current) {
    KFPanel.current.panel.reveal();
    KFPanel.current.pushSessionState(); // restore state on reveal
    return;
  }
  // create new panel...
}

pushSessionState() {
  this.panel.webview.postMessage({
    type: 'session:state',
    chainHistory: this.session.getChainHistory(),
    currentMode: this.session.getCurrentMode(),
    isRunning: this.session.isRunning(),
  });
}

// Webview always sends 'ready' on load → host responds with 'session:state'
panel.webview.onDidReceiveMessage((msg) => {
  if (msg.type === 'ready') this.pushSessionState();
  // ...
});
```

---

### Handoff 4: Finding interface (AllOfUs → KF adversarial panel)

Copy this type into KF-VSCode, extending `layer` for KF-specific findings:

```typescript
// src/types/finding.ts
export interface Finding {
  id: string;
  layer: 'os' | 'vscode' | 'extensions' | 'project'  // AllOfUs original
        | 'kf-critic' | 'kf-expert' | 'kf-chain';     // KF extensions
  status: 'pass' | 'warn' | 'fail' | 'manual';
  severity: 'high' | 'medium' | 'low' | 'info';
  message: string;
  evidence?: string;
  recommendation?: string;
}
```

---

## Extension Architecture

### File Structure

```
kf-vscode/
├── package.json                    # Extension manifest
├── tsconfig.json
├── src/
│   ├── extension.ts                # activate() / deactivate()
│   ├── KFSession.ts                # Singleton chain state owner
│   ├── KFPanel.ts                  # Webview panel (adapted setup-panel.ts)
│   ├── mode-router.ts              # Maps intent → KF mode system prompt
│   ├── key-resolution.ts           # vscode.authentication.getSession wrapper
│   ├── stream-batcher.ts           # 100ms debounce for stream:delta
│   ├── sse-server.ts               # Optional browser SSE variant
│   ├── agent-anthropic.ts          # Copied from AllOfUs (unchanged)
│   ├── jsonc-edit.ts               # Copied from AllOfUs (unchanged)
│   └── types/
│       ├── finding.ts              # Extended Finding interface
│       ├── kf-messages.ts          # Host↔webview message protocol types
│       └── kf-session.ts           # ChainStep, KFMode, SessionState types
├── src/resources/
│   ├── kf-orchestrator.md          # Compiled from module 00
│   ├── kf-mode-registry.json       # Compiled mode index
│   └── kf-modes/
│       ├── navigator.md            # Compiled from module 01
│       ├── builder.md              # Compiled from module 02
│       ├── coordinator.md          # Compiled from module 03
│       ├── expert.md               # Compiled from module 05
│       ├── critic.md               # Compiled from module 07
│       ├── synthesizer.md          # Compiled from module 08
│       ├── debugger.md             # Compiled from module 09
│       ├── strategist.md           # Compiled from module 10
│       └── calibrator.md          # Compiled from module 11
└── src/webview/
    ├── panel.html                  # Webview HTML template (with nonce CSP)
    ├── panel.css                   # VS Code theme variable styles
    └── panel.js                    # Webview-side message handlers
```

---

### KFSession Class Design

```typescript
// src/KFSession.ts
export class KFSession {
  private agent: AnthropicAgent | null = null;
  private apiKey: string | null = null;
  private currentMode: string | null = null;
  private chainHistory: ChainStep[] = [];
  private running = false;

  // Lazy init — NOT called in activate()
  async init(context: vscode.ExtensionContext): Promise<boolean> {
    const session = await vscode.authentication.getSession(
      'dev-api-keys', ['anthropic'], { createIfNone: false }
    );
    if (!session) return false;
    this.apiKey = session.accessToken;
    this.agent = createAnthropicAgent({
      apiKey: this.apiKey,
      model: 'claude-sonnet-4-5',
      maxSteps: 5,
    });
    return true;
  }

  async send(content: string, mode: string, batcher: StreamBatcher): Promise<void> {
    if (!this.agent) throw new Error('KFSession not initialized');

    // Load mode system prompt from compiled resource
    const systemPrompt = await modeRouter.getSystemPrompt(mode);
    this.agent.setInstructions(systemPrompt);
    this.currentMode = mode;
    this.running = true;

    const step: ChainStep = { mode, input: content, output: '', startedAt: Date.now() };
    this.chainHistory.push(step);

    // Wire events
    this.agent.on('stream:delta', (d, acc) => batcher.push(d, acc));
    this.agent.on('stream:end', (text) => { step.output = text; step.endedAt = Date.now(); });
    this.agent.on('tool:call', (name, args) => { /* emit to panel */ });
    this.agent.on('error', (err) => { /* emit to panel */ });

    await this.agent.send(content);
    this.running = false;
  }

  invalidateKey() { this.apiKey = null; this.agent = null; }
  getChainHistory() { return [...this.chainHistory]; }
  getCurrentMode() { return this.currentMode; }
  isRunning() { return this.running; }
  clearChain() { this.chainHistory = []; this.currentMode = null; }
}
```

---

### Webview Message Protocol

```typescript
// src/types/kf-messages.ts

// Host → Webview
type HostMessage =
  | { type: 'session:state'; chainHistory: ChainStep[]; currentMode: string | null; isRunning: boolean }
  | { type: 'stream:batch'; delta: string; accumulated: string; timestamp: number }
  | { type: 'stream:start'; mode: string }
  | { type: 'stream:end'; fullText: string; mode: string; durationMs: number }
  | { type: 'tool:call'; name: string; args: unknown }
  | { type: 'tool:result'; toolUseId: string; result: string }
  | { type: 'findings:update'; findings: Finding[] }
  | { type: 'error'; message: string };

// Webview → Host
type WebviewMessage =
  | { type: 'ready' }                                        // always first, on load
  | { type: 'send'; content: string; mode: string }          // user submits prompt
  | { type: 'mode:select'; mode: string }                    // mode picker change
  | { type: 'chain:clear' }                                  // reset session
  | { type: 'wiki:file'; content: string; title: string }    // accretion trigger
  | { type: 'open:setup' };                                  // open dev-keys.setup
```

---

### package.json Manifest (key fields)

```json
{
  "name": "kf-vscode",
  "displayName": "KnowledgeForge",
  "version": "0.1.0",
  "publisher": "local",
  "engines": { "vscode": "^1.90.0" },
  "extensionDependencies": ["local.dev-keys"],
  "activationEvents": ["onStartupFinished"],
  "main": "./dist/extension.js",
  "contributes": {
    "commands": [
      { "command": "kf.send",        "title": "KF: Send to Active Mode" },
      { "command": "kf.setMode",     "title": "KF: Select Mode" },
      { "command": "kf.clearChain",  "title": "KF: Clear Chain" },
      { "command": "kf.openPanel",   "title": "KF: Open Panel" },
      { "command": "kf.wikiFile",    "title": "KF: File to Wiki" }
    ],
    "views": {
      "explorer": [
        { "type": "webview", "id": "kf.panel", "name": "KnowledgeForge" }
      ]
    },
    "configuration": {
      "title": "KnowledgeForge",
      "properties": {
        "kf.defaultMode": {
          "type": "string",
          "default": "navigator",
          "description": "Default KF mode for new sessions"
        },
        "kf.maxSteps": {
          "type": "number",
          "default": 5,
          "description": "Max agentic loop steps per send()"
        }
      }
    }
  }
}
```

---

### Webview Panel Design

**Layout (sidebar panel):**
```
┌─────────────────────────────────┐
│ ● KnowledgeForge    [⊕][✕][↺] │  ← status bar row: mode badge + controls
├─────────────────────────────────┤
│ [Navigator ▾]  conf: 0.9  💡   │  ← mode picker + confidence + decision type
├─────────────────────────────────┤
│ ░░░░░░░░░░░░░░░░░░░░░░          │  ← reasoning depth / step progress bar
├─────────────────────────────────┤
│                                 │
│  Streaming output here...       │  ← live token stream (incremental append)
│  tokens append at ~100ms        │
│                                 │
├─────────────────────────────────┤
│ Chain: Builder → Expert → ●     │  ← chain history pills (● = active)
├─────────────────────────────────┤
│ ⚠ Finding [HIGH]: ...           │  ← adversarial findings (if any)
├─────────────────────────────────┤
│ [Type here...]          [Send]  │  ← input row
└─────────────────────────────────┘
```

**Mode badge colors** (using VS Code theme variables):
- Navigator: `--vscode-charts-blue`
- Builder: `--vscode-charts-green`
- Expert: `--vscode-charts-purple`
- Critic: `--vscode-charts-red`
- Debugger: `--vscode-charts-orange`
- Strategist: `--vscode-charts-yellow`

**Decision type indicator** (icon next to confidence):
- Reckoning: ⚡ (fast, direct)
- Evaluative: ⚖ (weighing)
- Predictive: 🔮
- Novel: 🔬 (flag for human review)

---

## Phase Plan

### Phase 0 — COMPLETE
- `local.dev-keys` installed in VS Code
- `dev-api-keys` AuthProvider live globally

### Phase 1 — MVP (proves end-to-end concept)
**Goal:** Type a prompt in VS Code, it routes to a KF mode, streams to the panel.

Tasks:
1. Run `kf-compile --target vscode` → emit mode resources (needs `vscode.yaml` ✅)
2. Scaffold KF-VSCode extension (`package.json`, `tsconfig`, `src/extension.ts`)
3. `key-resolution.ts` + `KFSession.ts` (skeleton — init + send only)
4. `stream-batcher.ts`
5. `KFPanel.ts` (minimal: input box + streaming output div)
6. Wire: `activate()` → register `kf.send` command → `KFSession.send()` → stream to panel
7. `tsc --noEmit` clean, `vsce package`, install

**Effort:** ~3 days  
**Success metric:** "debug this function" in panel → Debugger mode activates → response streams in → no blank panel on close/reopen

### Phase 2 — Mode routing + chain visualization
**Goal:** Automatic mode routing (KF orchestrator logic), chain history pills, mode picker.

Tasks:
1. `mode-router.ts` — reads orchestrator.md + mode-registry.json, classifies intent
2. Mode picker command (`kf.setMode`) + mode badge in panel
3. Chain history pills (ChainStep[] → pill row)
4. Decision classification indicator (reckoning/evaluative/novel)
5. `tool:call` / `tool:result` events shown in panel

**Effort:** ~4 days  
**Success metric:** "why is X broken and should we fix or rebuild?" → Debugger → Strategist chain runs automatically, both pills shown

### Phase 3 — Wiki accretion + findings panel
**Goal:** File agent output to wiki from within VS Code.

Tasks:
1. "File to wiki" inline action on agent output
2. `wiki:file` webview→host message → writes to `knowledgeforge-core/wiki/`
3. Adversarial findings panel (Finding[] rendered in panel)
4. Confidence + grounding score display
5. `kf.wikiFile` command palette entry

**Effort:** ~3 days  
**Success metric:** Agent produces analysis → user clicks "File to wiki" → `.md` appears in knowledgeforge-core/wiki/ with correct metadata header

### Phase 4 — Browser SSE variant (optional)
**Goal:** Access KF reasoning from any browser (mobile, second screen).

Tasks:
1. `sse-server.ts` adapted from AllOfUs `web-server.ts`
2. KFSession broadcast → SSE channel
3. Browser UI (adapted from AllOfUs web server HTML)
4. `kf.startBrowser` command

**Effort:** ~2 days  
**Dependency:** Phase 1 complete (KFSession must exist)

---

## Open Questions (to resolve before Phase 2)

1. **Compiler extension for VS Code sections:** The current compiler (`kf-compile.py`) only knows `CC_SECTION_MARKERS`. The `vscode.yaml` verbatim approach works for MVP (copies full module content). Phase 2 may want VS Code-specific sections (`## VSCode Panel`, `## VSCode Command`) to allow module authors to write VS Code-optimized mode content without including the full Claude Code instructions. Decide before writing Phase 2 modules.

2. **Same VS Code instance as Claude Code:** When KF-VSCode and Claude Code are both active, they can share the `dev-api-keys` auth session. But if Claude Code's KF is also running, two KF instances are active simultaneously. Is that desirable (different contexts)? Or should KF-VSCode detect Claude Code's KF and defer? Likely fine to run both — they're different UX surfaces.

3. **Wiki write path:** Phase 3 wiki accretion writes to `knowledgeforge-core/wiki/`. This requires the extension to know the path to knowledgeforge-core. Options: (a) VS Code setting `kf.wikiPath`, (b) detect from workspace git remote, (c) hardcode to `~/Scripts/knowledgeforge-core/wiki/` as default. Option (a) is cleanest.

4. **KF mode for VS Code vs Claude Code:** Should KF-VSCode use the same 26-module spec as KF-CC, or a VS Code-optimized subset? MVP answer: same spec, verbatim copy. Long-term: VS Code-specific sections in modules may be warranted once usage patterns are clear.

---

## Files Written in This Session

- `platform-bindings/vscode.yaml` — compiler binding for VS Code target
- `plans/kf-vscode-platform.md` — high-level plan + prompt (Phase 0 status)
- `plans/kf-vscode-implementation.md` — this file (full implementation plan)
