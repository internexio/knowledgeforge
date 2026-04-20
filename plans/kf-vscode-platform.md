# KF-VSCode Platform Plan
**Status:** Planning  
**Date:** 2026-04-19  
**Depends on:** AllOfUs repo (`~/Scripts/AllOfUs/`), knowledgeforge-core compiler  

---

## Summary

New KnowledgeForge platform target: a VS Code extension that surfaces KF's
reasoning modes through a visual GUI. VS Code is the 4th compiler target
alongside Claude Code, Claude Projects, and Cowork.

AllOfUs (`github.com/AnjinMeili/AllOfUs`) provides ~60% of the extension
scaffolding. KF-VSCode depends on AllOfUs for credential management and
reuses its webview, SSE server, and agent patterns.

**Phase 0 is complete:** `local.dev-keys` installed in VS Code. AllOfUs's
`AuthenticationProvider` (`dev-api-keys`) is registered globally. KF-VSCode
will source its Anthropic key via `vscode.authentication.getSession()`.

---

## Architectural Decision (locked)

> Do NOT make AllOfUs a platform or plugin host. It wasn't designed for
> that and has an upstream repo. Instead:
>
> - AllOfUs installed globally → credential provider only
> - KF-VSCode declares `extensionDependencies: ["local.dev-keys"]`
> - KF-VSCode calls `vscode.authentication.getSession('dev-api-keys', ['anthropic'])`
> - AllOfUs manages the key UI; KF-VSCode never shows a key input

---

## AllOfUs Reuse Map

| Component | File | KF-VSCode Use | Effort |
|---|---|---|---|
| AuthProvider | `dev-keys/src/extension.ts` | API key mgmt — rename provider ID to `kf` | 1 |
| Webview scaffold | `dev-keys/src/setup-panel.ts` | KF mode dashboard — message protocol, CSP, singleton pattern reusable; card UI needs full redesign | 2 |
| SSE server infra | `dev-keys/src/web-server.ts` | Browser KF streaming UI — routes + HTML need KF rewrites | 2 |
| JSONC editor | `src/jsonc-edit.ts` | KF config management — zero changes needed | 1 |
| Audit Finding interface | `src/audit-permissions.ts` | KF adversarial findings shape — maps directly | 1 |
| Anthropic agent | `src/agent-anthropic.ts` | EventEmitter streaming bridge to webview — needs KFSession wiring | 2 |

**Key design constraint:** AllOfUs is isolation-first (credentials isolated per
call). KF needs the opposite — a singleton `KFSession` owning chain state read
by webview, SSE server, and auth provider. Design KF-VSCode around `KFSession`
as the single source of truth; treat all UI surfaces as read-only consumers.

**Streaming constraint:** VS Code's webview message channel has measurable
latency at token velocity. Batch `stream:delta` events at ~100ms intervals
before posting to the webview. Do not post per-token.

**Panel reopen constraint:** Webview singleton — if user closes/reopens panel
mid-chain, `KFSession` in the extension host must restore chain state. The
webview is disposable; the host is not.

---

## Planning Prompt

Paste this into a `knowledgeforge-core` Claude Code session to generate the
full implementation plan:

---

```
Plan a new KnowledgeForge platform target: KF-VSCode — a VS Code extension
that surfaces KF's reasoning modes through a visual GUI.

## Context you need

### KF compiler baseline
KF-core already compiles 26 canonical modules to 3 platform targets (Claude
Code, Claude Projects, Cowork). The pattern is:
  1. Create platform-bindings/vscode.yaml with module→output mapping
  2. Define output structure (VS Code extension file layout)
  3. kf-compile --target vscode --output <path>

VS Code is a new 4th platform target with zero existing scaffolding.

### AllOfUs repo (~/Scripts/AllOfUs/) — components to reuse
A production VS Code extension codebase. Analyze these files before planning:

- dev-keys/src/extension.ts     → AuthenticationProvider for API key mgmt
- dev-keys/src/setup-panel.ts   → Webview panel + message protocol pattern
- dev-keys/src/web-server.ts    → Local HTTP + SSE server (browser variant)
- src/agent-anthropic.ts        → EventEmitter streaming agent (Anthropic SDK)
- src/jsonc-edit.ts             → JSONC-preserving settings editor
- src/audit-permissions.ts      → VS Code settings auditor (Finding interface)

Pre-analyzed reuse map (effort 1–5 scale):
  - AuthProvider:        effort 1 — near copy-paste, rename provider ID to kf
  - Webview scaffold:    effort 2 — message protocol/CSP/singleton reusable;
                                    card UI needs full redesign for KF modes
  - SSE server infra:    effort 2 — routes + HTML need KF-specific rewrites
  - audit Finding iface: effort 1 — maps to KF adversarial findings shape
  - jsonc-edit.ts:       effort 1 — direct dependency, zero changes
  - agent-anthropic.ts:  effort 2 — EventEmitter bridge to webview is ready;
                                    needs KFSession wiring

### Auth integration (already decided — do not re-litigate)
AllOfUs is installed globally as `local.dev-keys`. KF-VSCode will:
  - Declare `extensionDependencies: ["local.dev-keys"]` in its manifest
  - Source Anthropic keys via:
      vscode.authentication.getSession('dev-api-keys', ['anthropic'])
  - Never show its own key input UI

### Critical design constraints
1. KFSession singleton: AllOfUs is isolation-first; KF needs the opposite.
   Design a singleton KFSession class in the extension host that owns all
   chain state. Webview, SSE server, and auth provider are read-only consumers.

2. Streaming batching: VS Code webview message channel has latency at token
   velocity. Batch stream:delta events at ~100ms intervals. Never post per-token.

3. Panel reopen: Webview is disposable, host is not. KFSession must restore
   current chain state when user closes and reopens the panel mid-chain.

4. Extension host constraints: No direct shell access. Tool execution via
   vscode.workspace APIs or explicit child_process calls only.

### What KF-VSCode must do
1. Route user input to KF modes (Builder/Critic/Debugger/Strategist/Expert/
   Synthesizer/Calibrator/Coordinator/Navigator) via the 26-module orchestrator
2. Stream reasoning output in real time to a VS Code webview sidebar panel
3. Visualize the mode chain (e.g., Expert → Critic → Strategist) with per-step
   timing and findings
4. Show decision classification (reckoning/evaluative/predictive/novel) and
   confidence/grounding scores
5. Accrete knowledge to the KF wiki from within the editor
6. Optionally: expose a browser UI via the SSE web server for non-VS Code use

## What to produce

A full implementation plan covering:

1. COMPILER BINDING
   - vscode.yaml platform binding spec (which of the 26 modules compile to
     what extension outputs: commands, webview scripts, config schema)
   - Recommended module subset for MVP (not all 26 modes needed Day 1)
   - Output directory structure for the VS Code extension package

2. EXTENSION ARCHITECTURE
   - File structure for the extension package
   - KFSession class design (owns chain state, drives webview + SSE)
   - Message protocol between extension host ↔ webview (types, payloads)
   - How agent-anthropic.ts events wire into KFSession → webview
   - Authentication flow using AllOfUs AuthProvider

3. WEBVIEW PANEL DESIGN
   - Mode dashboard layout (active mode badge, chain history, confidence meter)
   - Streaming text display (incremental append, batched at 100ms)
   - Adversarial findings panel (reusing Finding interface from AllOfUs)
   - Decision classification indicator (reckoning/evaluative/predictive/novel)
   - Wiki accretion trigger (inline "file this" action on agent output)

4. PHASE PLAN
   - Phase 0: COMPLETE — AllOfUs installed, auth provider live
   - Phase 1 MVP: smallest thing that proves the concept works end-to-end
   - Phase 2: Full streaming + mode routing in the panel
   - Phase 3: Chain visualization + wiki accretion
   - Phase 4: Browser SSE variant
   - Effort estimates per phase

5. OPEN QUESTIONS TO RESOLVE
   - Which KF modes are highest value to surface in VS Code first?
   - Should KF-VSCode compile from knowledgeforge-core (new build target),
     or be a standalone extension that imports KF as a TypeScript library?
   - How does KF-VSCode interact with Claude Code when both are active in
     the same VS Code instance? (shared AuthProvider session is one bridge)

Use @coordinator to map component dependencies first. Use @builder for
architecture sections. Use @strategist for phase plan and prioritization.
Flag anything needing adversarial review before implementation starts.
```

---

## Phase Status

| Phase | Status | Notes |
|---|---|---|
| 0 — Install AllOfUs, wire auth | ✅ Complete | `local.dev-keys` installed; `dev-api-keys` AuthProvider live |
| 1 — Compiler binding + extension scaffold | 🔲 Not started | Run planning prompt first |
| 2 — Streaming + mode routing in panel | 🔲 Not started | |
| 3 — Chain visualization + wiki accretion | 🔲 Not started | |
| 4 — Browser SSE variant | 🔲 Not started | |

---

## Related

- `~/Scripts/AllOfUs/` — source for reusable components
- `~/Scripts/AllOfUs/src/agent-anthropic.ts` — Anthropic streaming agent
- `~/Scripts/AllOfUs/dev-keys/dev-keys-0.1.0.vsix` — installed extension
- `wiki/architecture/pattern-extraction-reuse-heuristic.md` — AllOfUs analysis
