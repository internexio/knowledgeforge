---
title: Pattern Extraction & Reuse Heuristic — Agent Architecture Patterns
source_mode: expert → critic → strategist
source_session: redacted
created: '2026-04-18T00:00:00Z'
date: '2026-04-18'
confidence: 0.9
grounding_score: 0.9
grounding_source: Full source read of AllOfUs repo (src/agent.ts, dev-keys/src/*)
  + scan of 5 recent ~/Scripts/ projects (agi, visionforge, hinotes, partnership,
  knowledgeforge-core). Adversarial critic pass surfaced 6 High/Critical findings.
novelty_type: transferable_framework
staleness_risk: stable
importance: 4
pinned: false
accreted_in: '6.5'
related:
- modules/02_builder.md
- modules/07_critic_agent.md
- modules/21_knowledge_accretion.md
- wiki/architecture/scaffolding-vs-patching-pattern.md
domain: architecture
topic: chain-design
---

# Pattern Extraction & Reuse Heuristic — Agent Architecture Patterns

## The Heuristic

> **Extract a pattern from a source repo if:**
> - **(a)** It solves a problem you will hit in the next project
> - **(b)** It's non-trivial to get right independently
> - **(c)** The inner implementation doesn't require a full rewrite of its most valuable part
>
> **Reject if:** the problem is already solved in your environment, the inner implementation must be fully rewritten, or the value is narrow to a use case not on your roadmap.

Applies to library evaluation, framework adoption, and copy-from-repo decisions.

---

## Dual-History Pattern (Agent Architecture)

**Problem:** Multi-turn agents with tool use silently corrupt context when a single history array mixes UI display entries and SDK context entries.

**Solution:** Maintain two separate histories:
```typescript
messages[]      // UI display — role + text only
inputHistory[]  // SDK context — full structured items: text + tool_use + tool_result
```

Tool calls and results must appear in `inputHistory` as structured objects (matching SDK schema), not as plain text summaries. If you push a plain assistant text message where a `tool_use` + `tool_result` pair should be, the model loses the tool interaction from its context on the next turn.

**Source evidence:** `AllOfUs/src/agent.ts`. The design decision is documented in comments at lines 56–59. The `sendSync()` method in the same file demonstrates the tradeoff — it pushes `{ role: 'assistant', content: fullText }` into `inputHistory`, which is a documented design choice: it's constrained to tool-free interactions. In multi-turn sessions with tool calls, this loses the structured tool_use/tool_result pair from context and degrades model behavior. The constraint is noted in source; don't reuse `sendSync()` for tool-heavy flows.

**Anti-pattern:** Single `history[]` used for both UI and SDK. Works fine for single-turn; breaks silently in multi-turn agentic loops.

**Portability:** This pattern is SDK-agnostic. Applies to Anthropic, OpenAI, and any SDK where tool calls/results are structured objects in the message array.

---

## OpenRouter vs Anthropic Streaming — Not Compatible

**Problem:** OpenRouter SDK streaming is item-ID-based (stable IDs, progressive re-emission). Anthropic SDK streaming is delta-based (positional events, no IDs). Code written for one does not port to the other.

**OpenRouter model:**
```
getItemsStream() → items with stable IDs → deduplicate by ID as updates arrive
```

**Anthropic model:**
```
messages.stream() → content_block_delta events → accumulate by position index
tool_use blocks → input_json_delta events → accumulate JSON string, parse on stop
```

**Implication:** When reusing an agent class built on OpenRouter, extract only the EventEmitter shell and dual-history structure. The inner streaming loop requires a full rewrite against Anthropic's event schema.

---

## Secure Local Server Primitives

Non-obvious security requirements for any tool that runs a local HTTP server:

| Primitive | What it prevents | Implementation |
|---|---|---|
| Bind to `127.0.0.1` only | Remote access | `server.listen(port, '127.0.0.1')` |
| Constant-time token comparison | Timing attacks | `crypto.timingSafeEqual(a, b)` |
| Host header validation | DNS rebinding | Allow only `localhost:PORT` and `127.0.0.1:PORT` |
| Per-session random token | Session fixation | `crypto.randomBytes(32).toString('hex')` on server start |

**Gap to document:** If the token is delivered via URL parameter (then moved to sessionStorage), the landing page must still be protected or the token can be extracted by any same-user process that hits `/`. For dev-only tools this is acceptable. For longer-running or sensitive servers, deliver the token out-of-band (temp file) and require it on all routes.

**Source:** `AllOfUs/dev-keys/src/web-server.ts`

---

## Cross-Repo Synthesis: Durable Patterns (Apr 2026 scan)

Patterns appearing across 3+ recent projects. Higher recurrence = higher confidence they're general.

### Lookup Tables > Hardcoding
Behavior spec lives in structured data (Markdown tables, JSON, YAML). Agents query the table; logic doesn't change when the data does.

- **VisionForge:** Platform syntax, camera vocabulary, negative prompts in `platform-lookup-tables.md`. Change a row, not a function.
- **KF-core:** Module specs as Markdown → compiler reads them. Platform-specific outputs are derived, not hand-edited.
- **Implication for KF modes:** When a mode has platform-specific behavior (e.g., token limits per model, output format per platform), put it in a lookup table the mode reads, not in the mode's instruction text.

### Multi-Tier Orchestration: Router → Domain Specialist → Executor
Appears in KF, VisionForge, AllOfUs. The tier separation has consistent shape:
1. **Router** — intent classification, dispatch
2. **Domain specialist** — context-aware optimization (COS brief optimizer, key validator)
3. **Executor** — generation/action

Each tier has exactly one responsibility. Cross-tier coupling breaks the isolation.

### Ethical Gate as Hard Stop (Not Warning)
VisionForge's architecture specifies an ethical gate that hard-stops all downstream output paths — no bypass route — for prohibited content categories. The gate is a blocker in the routing logic, not a soft warning. Relevant for any KF chain that touches health, political, or manipulative content (COS modes already implement this via cos-ethics). Note: VisionForge is pre-implementation as of Apr 2026; the gate is an architectural constraint, not yet running code.

### Pattern Recurrence as Decision Trigger
Name a behavior pattern. Count documented instances. Define a threshold (e.g., 3). Threshold reached = pre-committed action, no in-the-moment deliberation needed.

- **Partnership repo:** Three named recurrence patterns (extractive pricing, conflict-via-laughter, credential leakage). Three instances = exit.
- **Implication for KF:** Could apply to metacognitive monitoring — name failure modes (circular reasoning, confidence collapse, mode thrash), count occurrences per session, trigger circuit breaker at threshold rather than requiring the monitor to judge in-context.

### Compilation for Platform Variants
Canonical source in one repo → compile to multiple platform-specific outputs. Never edit outputs directly; edits flow in via source and compile out.

- **KF-core:** `modules/*.md` → compiler → claude-code variant, claude-projects variant, cowork variant
- **AllOfUs agent:** Similar principle — `agent.ts` is the canonical class; platform-specific entry points (`headless.ts`, `cli.tsx`) are thin wrappers.

### Pre-Prompt Local Model Routing
Cheap local classification (Gemma 3 4B via Ollama, ~200ms, zero API cost) injects routing directives before the main model sees the prompt. Replicates semantic routing at low cost.

- **KF-core:** Phase 1 of implementation plan. Not yet built (as of Apr 2026).
- **Value:** Reduces main-model token consumption on routing decisions; enables fast mode-switching without burning context.

---

## Specific Project Notes (Evidence Base)

### AllOfUs (`~/Scripts/AllOfUs/`)
Agent framework on OpenRouter SDK. The credential store subsystem (`dev-keys/`) is production-quality: cross-platform (macOS Keychain via `security` CLI + Linux/Windows keyring), CLI + web UI + VS Code AuthenticationProvider, with dual-pass key validation (format + live HTTP ping). **Not needed** if keys are already in environment variables — the keychain path is never reached. The validation ping pattern (buildAuthHeaders + AbortSignal.timeout) is the only piece worth extracting for Anthropic-primary projects.

### agi (`~/Scripts/agi/`)
PNW AGI group research. Notable: judge bias detection suite (4-vector: position, verbosity, format, bounded disagreement) — verified pattern, run against any model used for evaluation. TEMPO temporal reasoning benchmark exists in the repo but no results file is present; claims about model performance on temporal tasks are unverified. Temporal reasoning reliability is a known model limitation, but specific benchmark evidence requires running the suite. The knowledge graph (concept nodes from session data + PageRank centrality) is a real architectural pattern but compiled output counts are not verifiable without running `prepare-data.py`.

### visionforge (`~/Scripts/visionforge/`)
Campaign-to-platform prompt engineering. Architecture-first development: full specs before Sprint 0 code. 7-step prompt assembly pipeline documented to function level before implementation. Status: docs production-ready, code pending.

### hinotes (`~/Scripts/hinotes/`)
HiDock transcript archive. Token lifecycle management for SaaS session auth: tokens expire → refresh from browser localStorage → store in gitignored `.token` file. Applies to any tool wrapping a consumer SaaS API with session-based auth.

### knowledgeforge-core (`~/Scripts/knowledgeforge-core/`)
KF canonical source. Pre-prompt routing hook (Phase 1) planned: local Gemma 3 4B classifies request type, injects routing directives, then main model handles. Load map files (`load-map-claude-code.md`) regenerated on each compile showing module → output file mapping. Makes compiled systems auditable.
