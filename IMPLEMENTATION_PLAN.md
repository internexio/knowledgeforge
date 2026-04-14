# KnowledgeForge 7.0 — Master Implementation Plan

**Date:** 2026-04-14
**Scope:** Transform KF from a single-platform prompt system into a compiled, multi-platform, multi-model framework with hook-driven routing and a single source of truth.
**Source:** AI Tinkerers research session (2026-04-13) + architecture sessions (2026-04-14)

---

## Context for Any Agent Working on This

This plan synthesizes findings from three connected architecture sessions. The reference documents are in this repo:

```
knowledgeforge-core/
├── plans/
│   ├── kf-67-master-plan.md              # Module update plan from 6 research projects
│   ├── kf-universal-architecture.md       # Multi-platform, multi-model compiler architecture
│   ├── kf-hook-driven-routing.md          # Hook-driven CC routing (the key breakthrough)
│   ├── orchestra-integration.md           # Orchestra → KF integration specifics
│   ├── baml-integration.md               # BAML → KF integration specifics
│   ├── agent-orchestrator-integration.md  # Agent Orchestrator → KF integration specifics
│   ├── hooks-mastery-integration.md       # claude-code-hooks-mastery → KF integration specifics
│   ├── background-agents-integration.md   # Background Agents / Ramp → KF integration specifics
│   └── ai-research-skills-integration.md  # AI Research Skills → KF integration specifics
└── this file (IMPLEMENTATION_PLAN.md)
```

### The Repos

| Repo | Role | Current State |
|------|------|--------------|
| `knowledgeforge-core` | **Single source of truth** (NEW) | Being set up now — canonical modules, wiki, plans |
| `knowledgeforge-cp` | Claude Projects variant | Current source of truth (will become compilation target) |
| `knowledgeforge-cc` | Claude Code variant | Decomposed from CP, drifting independently |
| `knowledgeforge-cw` | Cowork variant | Decomposed from CP, drifting independently |
| `knowledgeforge-web` | Web agents variant (FUTURE) | Does not exist yet |

### The Core Problem Being Solved

Claude Projects outperforms Claude Code because CP has semantic search over all module files — it finds the right module when needed. CC requires the agent to *know* to load something before it knows it needs it. Cross-cutting modules (Calibration, Grounding Scores, Metacognitive Monitor) buried in a SKILL.md never get loaded because there isn't enough context for the agent to recognize the need.

### The Solution

A `UserPromptSubmit` hook runs a fast local LLM (Gemma 3 4B via Ollama) BEFORE Claude sees the prompt. This LLM classifies the request against a compact KF module index and injects routing directives — telling Claude exactly which skill to load and which cross-cutting docs to reference. This replicates CP's semantic retrieval at ~200ms overhead and zero API cost.

---

## Phase 0: Repo Setup and Sync (Day 1)

### Goal
Establish `knowledgeforge-core` as the canonical repo. Pull current state from all three variant repos. Identify drift.

### Steps

1. **Initialize knowledgeforge-core structure:**
```
knowledgeforge-core/
├── README.md
├── kf.yaml                         # Version, metadata
├── plans/                          # All plan documents from this chat
├── modules/                        # Canonical module specs (from CP)
│   ├── 00_orchestrator.md          # Agent Instructions (the orchestrator)
│   ├── 01_navigator.md
│   ├── 02_builder.md
│   ├── 03_coordination_patterns.md
│   ├── 04_specification_templates.md
│   ├── 05_expert_agent.md
│   ├── 06_quick_reference.md
│   ├── 07_critic_agent.md
│   ├── 08_synthesizer_agent.md
│   ├── 09_debugger_agent.md
│   ├── 10_strategist_agent.md
│   ├── 11_calibrator_agent.md
│   ├── 12_calibration_layer.md
│   ├── 13_decision_classification.md
│   ├── 14_metacognitive_monitor.md
│   ├── 15_grounding_scores.md
│   ├── 16_operational_bounds.md
│   ├── 17_temporal_knowledge.md
│   ├── 18_salience_allocation.md
│   ├── 19_memory_architecture.md
│   ├── 20_permission_model.md
│   ├── 21_knowledge_accretion.md
│   ├── 22_semantic_wiki_search.md
│   ├── 23_taxonomy_enforcement.md
│   └── 24_verbatim_history_mining.md
├── wiki/                           # Tier 0 accreted knowledge
│   └── neuro-symbolic-pattern-validation.md
├── templates/                      # Specification templates (from Module 04)
├── taxonomy/                       # Controlled vocabulary (from Module 23)
├── model-profiles/                 # Per-model weakness/strength maps (NEW)
├── platform-bindings/              # Per-platform adaptation rules (NEW)
└── compiler/                       # kf-compile tooling (FUTURE)
```

2. **Copy canonical modules from knowledgeforge-cp** into `knowledgeforge-core/modules/`. These are the source of truth — CP has the most complete, most recent specs.

3. **Diff knowledgeforge-cc against core modules.** Identify where CC has drifted. Document drift in `plans/cc-drift-audit.md`. Any CC-specific improvements that should be upstreamed go back into core modules.

4. **Diff knowledgeforge-cw against core modules.** Same process. Document in `plans/cw-drift-audit.md`.

5. **Place all plan documents** from the architecture sessions into `plans/`.

### Deliverables
- [ ] `knowledgeforge-core` repo initialized with canonical modules
- [ ] Drift audit for CC and CW documented
- [ ] All plan documents in `plans/`
- [ ] README.md documenting the repo's role as single source of truth

### Validation
Run `diff` between core modules and each variant. Zero unexplained differences.

---

## Phase 1: Pre-Prompt Hook — The Foundation (Days 2-4)

### Goal
Build and validate the `UserPromptSubmit` hook that runs a fast LLM to classify user prompts and inject KF routing directives into Claude Code sessions.

### Why This Is First
Everything else depends on this. The hook is what closes the CP-CC gap. Without it, decomposing CLAUDE.md into skills/docs would make CC *worse* (less context, no retrieval). With it, decomposition makes CC *better* (targeted context, proactive retrieval).

### Steps

1. **Install Ollama + Gemma 3 4B** (or chosen fast model) on the development machine.
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
# Pull model
ollama pull gemma3:4b
# Test
echo '{"mode":"test"}' | ollama run gemma3:4b --format json
```

2. **Create the compact KF module index** (~2K tokens). This is what the fast LLM sees — NOT the full module specs. Just mode names, trigger phrases, cross-cutting module conditions, and decision type definitions.
```
File: knowledgeforge-cc/.claude/hooks/kf_module_index.txt
```
Content: See `kf-hook-driven-routing.md` → "The Module Index" section for the full text.

3. **Write `kf-route.py`** — the UserPromptSubmit hook script.
```
File: knowledgeforge-cc/.claude/hooks/kf-route.py
```
Core logic (see `kf-hook-driven-routing.md` for full implementation):
- Read user prompt from hook stdin JSON
- Call Ollama with prompt + module index
- Parse JSON response: `{mode, decision_type, cross_cutting, notes}`
- Format routing directive: `[KF-ROUTE: mode=X | decision=Y | load=[M12, M15]]`
- Output modified prompt via hook protocol
- Graceful degradation: if Ollama fails, exit 0 (no routing = current behavior)

4. **Add hook to `.claude/settings.json`:**
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "python3 .claude/hooks/kf-route.py"
      }
    ]
  }
}
```

5. **Build test suite — 30 representative prompts:**
```yaml
# File: knowledgeforge-core/tests/routing_test_suite.yaml
tests:
  # Reckonings (should NOT activate a mode)
  - prompt: "What port does PostgreSQL use?"
    expected_mode: null
    expected_decision: reckoning

  - prompt: "What's the default branch name in git?"
    expected_mode: null
    expected_decision: reckoning

  # Builder
  - prompt: "Create a spec for a new monitoring agent"
    expected_mode: builder
    expected_decision: evaluative
    expected_cross_cutting: [M13]

  - prompt: "Build me a CLAUDE.md for this project"
    expected_mode: calibrator
    expected_decision: evaluative

  # Critic
  - prompt: "Review this spec and tell me what's missing"
    expected_mode: critic
    expected_decision: evaluative
    expected_cross_cutting: [M12, M15]

  - prompt: "Health check the knowledge base"
    expected_mode: critic  # linter variant
    expected_decision: evaluative
    expected_cross_cutting: [M21]

  # Debugger
  - prompt: "The API is returning 500 errors on the auth endpoint"
    expected_mode: debugger
    expected_decision: evaluative

  # Strategist
  - prompt: "Should we use PostgreSQL or MongoDB for this project?"
    expected_mode: strategist
    expected_decision: evaluative
    expected_cross_cutting: [M15]

  - prompt: "Should we open-source the framework?"
    expected_mode: strategist
    expected_decision: novel
    expected_cross_cutting: [M12, M15, M21]

  # Expert
  - prompt: "How does Claude Code's compaction mechanism work?"
    expected_mode: expert
    expected_decision: evaluative

  # Synthesizer
  - prompt: "What patterns do these three repos have in common?"
    expected_mode: synthesizer
    expected_decision: evaluative
    expected_cross_cutting: [M21]

  # Chains
  - prompt: "Review the API security and tell me what to fix first"
    expected_mode: expert  # first in chain
    expected_decision: evaluative
    expected_cross_cutting: [M12, M15]

  # Ambiguous (Navigator should fire)
  - prompt: "Help me with my agent"
    expected_mode: navigator
    expected_decision: evaluative

  # Infrastructure
  - prompt: "Audit my hosting setup"
    expected_mode: critic  # audit variant
    expected_decision: evaluative
    expected_cross_cutting: [M15]

  # ERA
  - prompt: "Map the entity relationships between KF modules"
    expected_mode: expert  # ERA domain
    expected_decision: evaluative
    expected_cross_cutting: [M21]

  # Add 15 more covering edge cases, mixed signals, and your domain-specific requests
```

6. **Run test suite.** Measure routing accuracy against expected values.
```bash
python3 tests/run_routing_tests.py --suite tests/routing_test_suite.yaml
```
Target: >85% mode accuracy, >80% cross-cutting module recall.

7. **Iterate on the module index** if accuracy is below target. Common fixes:
   - Add trigger phrases the fast LLM missed
   - Add negative examples ("NOT Debugger when user says 'review'")
   - Adjust cross-cutting module conditions

### Deliverables
- [x] ~~Ollama + Gemma 3 4B running locally~~ → **Substituted: Gemini Flash Lite API** (free tier, ~300ms, no local install; `GEMINI_API_KEY` required in env)
- [x] `kf-route.py` hook script with graceful degradation — deployed to `~/.claude/hooks/`
- [x] Compact module index (`kf_module_index.txt`) — co-located with hook script
- [x] 30-prompt routing test suite with expected values — `tests/routing_test_suite.yaml`
- [ ] Test results showing >85% routing accuracy — pending `tests/run_routing_tests.py` run
- [x] Hook registered globally in `~/.claude/settings.json` pointing to `~/.claude/hooks/kf-route.py`
- [x] `scripts/deploy-hooks.sh` — source in `knowledgeforge-core/hooks/`, deploy to `~/.claude/hooks/`; all non-CP variants benefit from one global deploy

### Validation Gate
Run 10 real prompts in a live Claude Code session with the hook active. Verify:
- Routing directives appear in the prompt ✓ (smoke tested: debugger route, reckoning passthrough)
- Claude responds to routing directives (loads indicated skills/docs) — pending Phase 2 (skills don't exist yet)
- Reckonings get no routing overhead ✓ (smoke tested: silent exit 0)
- Novel judgments get full module set — pending Phase 2

---

## Phase 2: Decompose CLAUDE.md into Skills + Docs (Days 5-7)

### Goal
Split the monolithic CLAUDE.md into a thin orchestrator + per-mode skills + cross-cutting docs. The hook from Phase 1 makes this safe — Claude knows what to load because the hook tells it.

### Steps

1. **Write the thin CLAUDE.md** (~5-8K tokens).
```
File: knowledgeforge-cc/CLAUDE.md
```
Content: See `kf-hook-driven-routing.md` → "CLAUDE.md: The Thin Orchestrator" section. Key elements:
- Identity (KF 7.0 orchestrator)
- Meta-principle
- Decision classification behavior (4 types)
- Routing directive handler ("When you see [KF-ROUTE], follow its directives")
- Quality gate summary
- Accretion check reminder
- Mode chaining behavior
- Auto-verification rule
- Circuit breakers
- **ENH-004:** Token economics pre-flight gate in chain dispatch logic — LOW tier invisible, MEDIUM tier log note, HIGH tier surface options before launching. Fire on 3+ mode chains or Expert + adversarial Critic. (See `enhancements/enh-004-token-economics-preflight.md`)

2. **Extract each mode into a skill file:**
```
Files: knowledgeforge-cc/.claude/skills/kf/{mode}.md
```
For each mode (builder, critic, debugger, strategist, expert, synthesizer, navigator, coordinator, calibrator):
- Extract the full mode protocol from the current module spec
- Include: purpose, protocol steps, output format, quality gates, variants, integration notes
- Do NOT include cross-cutting module content (that's in docs)
- Each skill should be self-contained: an agent loading only CLAUDE.md + this skill should be able to execute the mode
- **ENH-001** (Builder + Expert skills): Add assumption surface step — before building, identify load-bearing factual premises from user input and surface them with consequence statements. One pass, not a gate. (See `enhancements/enh-001-sycophantic-guard.md`)
- **ENH-002** (Critic skill): Add functional correctness check after gap-finding pass. Update adversarial framing to lead with "does this do what the user actually needs, or does it correctly solve the wrong problem?" before semantic review. (See `enhancements/enh-002-functional-correctness.md`)
- **ENH-003** (Coordinator skill): Add harness sizing pre-check before dependency mapping — infer harness type, classify task scope, surface mismatch if found. Matched cases are invisible. (See `enhancements/enh-003-harness-sizing.md`)
- **ENH-005** (Expert skill): Add structured blast radius checklist (blast radius / reversibility / frequency / verifiability) as required template on HIGH-risk Expert outputs. Checklist verdict feeds permission framing. (See `enhancements/enh-005-blast-radius-checklist.md`)

3. **Extract cross-cutting modules into doc files:**
```
Files: knowledgeforge-cc/.claude/docs/knowledgeforge/{module}.md
```
For each cross-cutting module (12-24):
- Extract the "apply during execution" protocol — the rules, not the full spec
- Keep each doc to ~200-500 tokens — just the essential protocol
- Full spec stays in `knowledgeforge-core/modules/` for reference

4. **Create slash commands for each mode:**
```
Files: knowledgeforge-cc/.claude/commands/kf-{mode}.md
```
Each command:
- Pre-loads the correct skill
- Pre-loads relevant cross-cutting docs
- Optionally declares mode-specific Stop hook validators
- Bypasses the routing hook (explicit route, no classification needed)

5. **A/B test: decomposed vs. monolithic.**
Run the same 10 prompts on:
- Current CC (monolithic CLAUDE.md)
- Decomposed CC (thin CLAUDE.md + hook + skills + docs)
- CP (the gold standard)

Score each output on: mode correctness, cross-cutting module application, output completeness, decision type depth.

### Deliverables
- [ ] Thin CLAUDE.md (~5-8K tokens) with ENH-004 token economics pre-flight baked in
- [ ] 9 skill files (one per mode) with ENH-001/002/003/005 baked in during extraction
- [ ] 13 doc files (cross-cutting modules 12-24)
- [ ] 9 slash commands (one per mode)
- [ ] A/B test results comparing decomposed CC vs. monolithic CC vs. CP

### Validation Gate
Decomposed CC output quality matches or exceeds CP on the test prompts. If it doesn't, identify which module(s) are being missed and adjust routing or CLAUDE.md instructions.

---

## Phase 3: Hook Infrastructure — Stop Gate + State Survival (Days 8-10)

### Goal
Add the remaining hooks that transform quality gates from advisory to mandatory and ensure state survives compaction.

### Steps

1. **Stop hook validator** (`kf-stop-validator.py`):
   - Read active mode from `.kf/state/active_mode`
   - Load mode-specific completion checklist
   - Validate output against checklist
   - Return `{"decision": "block", "reason": "Missing: X, Y"}` if incomplete
   - Guard against infinite loops via `stop_hook_active` field
   - Reference: `hooks-mastery-integration.md` → item 1

2. **PreCompact hook** (`kf-precompact.py`):
   - Flush routing index to `.kf/state/routing_index.yaml`
   - Flush active Tier 2 state
   - Write session summary
   - Back up transcript to `.kf/transcripts/`
   - Reference: `orchestra-integration.md` → item 2
   - **ENH-006 (compaction anchor):** Preserve verbatim in compaction output — the user's original stated intent for the current task, any explicit constraints/out-of-scope declarations, and the current mode chain + step. Never summarize these. This is the anchor the next session resumes from. (See `enhancements/enh-006-spec-drift-checkpoint.md`)

3. **PostCompact hook** (`kf-postcompact.py`):
   - Inject routing index paths (NOT full contents)
   - Inject one-line Tier 2 summary
   - Inject active task name + current step only
   - MUST inject less than PreCompact to avoid re-triggering compaction
   - Reference: `orchestra-integration.md` → item 2

4. **PostToolUse edit-count nudge** (`kf-edit-nudge.py`):
   - Count Edit|Write tool calls via `.kf/state/edit_count`
   - After 10 edits without checkpoint: inject nudge into tool response
   - Reference: `orchestra-integration.md` → item 3

5. **SessionStart context injection** (`kf-session-start.py`):
   - Load `.kf/state/` files
   - Inject active mode, routing index, last decision as `additionalContext`
   - Discriminate by source: startup (full) vs. resume (full) vs. compact (minimal)
   - Reference: `orchestra-integration.md` → item 3

6. **Register all hooks in `.claude/settings.json`:**
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {"type": "command", "command": "python3 .claude/hooks/kf-route.py"}
    ],
    "Stop": [
      {"type": "command", "command": "python3 .claude/hooks/kf-stop-validator.py"}
    ],
    "PreCompact": [
      {"type": "command", "command": "python3 .claude/hooks/kf-precompact.py"}
    ],
    "PostCompact": [
      {"type": "command", "command": "python3 .claude/hooks/kf-postcompact.py"}
    ],
    "PostToolUse": [
      {"type": "command", "command": "python3 .claude/hooks/kf-edit-nudge.py"}
    ],
    "SessionStart": [
      {"type": "command", "command": "python3 .claude/hooks/kf-session-start.py"}
    ]
  }
}
```

### Deliverables
- [ ] Stop hook with per-mode completion checklists
- [ ] PreCompact + PostCompact hook pair with asymmetric injection with ENH-006 spec anchor
- [ ] PostToolUse edit-count nudge
- [ ] SessionStart context injection
- [ ] `.kf/state/` directory structure created at runtime
- [ ] All hooks registered in `.claude/settings.json`

### Validation Gate
- Start a Builder session → produce deliberately incomplete spec → attempt to stop → verify Stop hook blocks
- Work for 20+ turns → trigger compaction → verify state survives → resume without re-prompting
- Make 12 edits without checkpointing → verify nudge appears in tool response

---

## Phase 4: Module Spec Updates from Research (Days 11-14)

### Goal
Apply the spec-level changes identified in the six per-project integration plans. These are prose changes to module specs — no code, no hooks.

### Steps

Apply changes in dependency order:

1. **Module 09 (Debugger) — Reproduce before fix** (from `background-agents-integration.md`):
   - Add Phase 4b (Failure Reproduction) between Root Cause Identification and Remediation
   - Mandatory step: construct reproduction case, verify it triggers same symptoms
   - Add `reproduction_status` output field: `confirmed | failed | skipped`

2. **Module 12 (Calibration Layer) — Cross-provider judge isolation** (from `orchestra-integration.md`):
   - Add judge isolation rule: judge model MUST be different family than agent
   - Claude agent → OpenAI judge; OpenAI agent → Claude judge

3. **Module 12 (Calibration Layer) — SAP-inspired output cascade** (from `baml-integration.md`):
   - Add multi-strategy parsing cascade for structured outputs
   - Scoring system: lower = better (ExtraKey +1, DefaultFromNoValue +100)
   - Integration with Module 15: parse level → grounding score mapping

4. **Module 07 (Critic) — Boundary scoring for severity** (from `baml-integration.md`):
   - When finding sits at severity boundary, score against both levels
   - Report winning severity with margin to next candidate

5. **Module 03 (Coordination) — Dual fingerprinting** (from `agent-orchestrator-integration.md`):
   - Track `state_fingerprint` and `dispatch_fingerprint` separately for Critic ↔ Builder loop
   - Dispatch only new/changed findings, not full re-review

6. **Module 17 (Temporal Knowledge) — Research staleness gate** (from `orchestra-integration.md`):
   - Before building on researched material, check age vs. domain half-life
   - Flag stale research to user; tag output with caveat if user proceeds

7. **Module 21 (Knowledge Accretion) — Artifact-embedded dedup** (from `background-agents-integration.md`):
   - Store `source_fingerprint` in wiki entry frontmatter
   - Before accreting: check for matching fingerprint in existing entries

8. **Module 21 (Knowledge Accretion) — Terminal state concept** (from `ai-research-skills-integration.md`):
   - Define terminal state: findings are self-contained, complete, no critical open questions
   - Only terminal artifacts accrete to Tier 0; intermediates stay in Tier 2

9. **Module 02 (Builder) — Pre-registration git protocol** (from `ai-research-skills-integration.md`):
   - Spec commits precede implementation commits
   - `spec({module}): description` before `impl({module}): description`
   - Confirmatory vs. exploratory tagging

10. **Module 09 (Debugger) — CI failure feedback loop** (from `agent-orchestrator-integration.md`):
    - Fingerprint failure set; dispatch only new failures
    - Escalate after N retries with same fingerprint

11. **Module 20 (Permission Model) — Input mutation** (from `hooks-mastery-integration.md`):
    - Extend from allow/deny to allow-with-mutation
    - Policies: path normalization, safety flags, cost annotation

12. **Module 16 (Operational Bounds) — Pure decision functions** (from `background-agents-integration.md`):
    - Extract circuit breaker logic into pure functions (input → output, no side effects)
    - Each function expressible as a truth table

13. **Add new meta-principle to orchestrator:**
    - "Deterministic first. Before invoking LLM judgment, exhaust deterministic checks. Before fixing, reproduce. Before acting, triage."

14. **Module 03 (Coordination) — Spec drift mid-chain checkpoint** (from `enhancements/enh-006-spec-drift-checkpoint.md`):
    - For chains of 3+ modes, insert a spec re-validation step between mode 2 and mode 3
    - Extract original goal from chain start; compare against modes 1-2 trajectory
    - Aligned: invisible, proceed. Drifted: surface drift + proposed correction before launching next mode
    - User-initiated pivots update the locked spec; silent model drift does not
    - Note: the compaction spec anchor piece is handled in Phase 3 PreCompact hook

15. **Module 11 (Calibrator) — Context hygiene audit** (from `enhancements/enh-007-context-hygiene.md`):
    - Add context hygiene audit as a named step in Calibrator setup and periodic review
    - Fires on: new project setup, explicit "audit my context" request, or performance degradation signal
    - Five-dimension checklist: instruction conflicts, staleness, verbosity, wiki hygiene, memory decay
    - Surface only — never auto-modify files; user decides on all recommendations

### Deliverables
- [x] 15 module spec updates applied to `knowledgeforge-core/modules/` (13 original + ENH-006 Coordinator + ENH-007 Calibrator)
- [x] Version bumped to 7.0.0 in `kf.yaml` and all module headers
- [x] Changelog entries added to each modified module

### Validation Gate
Run Critic (linter variant) across all updated modules. Check for internal consistency, cross-reference validity, and no orphan references.

---

## Phase 5: Model Profiles (Days 15-18)

### Goal
Create per-model weakness/strength maps that inform prompt compilation and the routing hook's model selection (for the web agents variant).

### Steps

1. **Define profile schema** (`model-profiles/_schema.yaml`):
   - Model metadata (id, provider, context window, cost, capabilities)
   - Strengths (things the model handles natively — KF should NOT add overhead)
   - Weaknesses (things the model fails at — KF MUST add structure)
   - Calibration overrides (decision type → overhead level)
   - Reference: `kf-universal-architecture.md` → Part 2

2. **Build Claude Sonnet 4 profile** — the primary CC model:
   - Strengths: intent decomposition, structured output, long context recall
   - Weaknesses: hypothesis skipping, trade-off hiding, gap blindness, self-preference bias, premature stopping
   - Source: accumulated KF operational experience + research findings

3. **Build Claude Opus 4 profile** — the frontier model:
   - Generally stronger than Sonnet on all dimensions
   - Document where overhead can be reduced vs. Sonnet
   - Key difference: novel judgment handling (Opus needs less scaffolding)

4. **Build GPT-5 profile** — the cross-provider judge:
   - Strengths: structured reasoning, instruction following
   - Weaknesses: over-hypothesizing, verbosity under uncertainty, shallow adversarial, lost-in-the-middle
   - Source: public benchmarks + KF PR/FAQ research findings

5. **Build OLMo 3 7B profile** — the self-hosted router candidate:
   - Strengths: fast classification, deterministic tasks
   - Weaknesses: reasoning depth (breaks at 3-4 steps), hallucination rate, instruction adherence
   - Role restriction: `intent_router_only`

6. **Build Gemini 2.5 Flash Lite profile** — the actual hook routing model (Phase 1 substituted Gemma 3 4B → Gemini Flash Lite due to hardware constraints):
   - Document classification accuracy from Phase 1 test suite results
   - Calibrate: which decision types can this model classify reliably?

### Deliverables
- [x] Profile schema defined
- [x] 5 model profiles created (Sonnet, Opus, GPT-5, OLMo, Gemini 2.5 Flash Lite)
- [x] Each profile includes strength/weakness evidence sources

### Validation Gate
For each profiled weakness, verify the corresponding KF module/mode actually patches it. For each profiled strength, verify removing the scaffolding doesn't degrade output.

---

## Phase 6: Compiler MVP (Days 19-25)

### Goal
Build `kf-compile` that can regenerate the CC variant from `knowledgeforge-core`. This proves the compilation model works before extending to other targets.

### Steps

1. **Create platform binding for Claude Code** (`platform-bindings/claude-code.yaml`):
   - Document all CC constraints (has filesystem, has hooks, no multi-model, etc.)
   - Define compilation output structure (CLAUDE.md + skills + docs + hooks + commands)
   - Token budget for CLAUDE.md (~5-8K target)

2. **Write `kf-compile.py`** — the compiler:
   - Read canonical modules from `modules/`
   - Read model profile for the target model
   - Read platform binding for the target platform
   - For each mode module: generate skill file with model-specific patches
   - For each cross-cutting module: generate doc file (condensed protocol)
   - Generate thin CLAUDE.md with model-specific behavioral adjustments
   - Generate compact module index for the routing hook
   - Write all outputs to the CC repo structure
   - Generate compilation manifest (what was patched, what was stripped)

3. **Validate: compile → diff against hand-crafted CC.**
   - Run `kf-compile --target claude-code --model claude-sonnet-4`
   - Diff compiled output against Phase 2 hand-crafted skills/docs
   - Resolve differences until compiled output is functionally equivalent

4. **Create platform binding for Claude Projects** (`platform-bindings/claude-projects.yaml`):
   - No hooks, no multi-model, context source = project knowledge files
   - Compilation output: full module specs as project knowledge files + compiled orchestrator

5. **Compile CP variant and diff against current CP.**
   - Validate compiled CP is functionally identical to hand-maintained CP
   - This proves the canonical modules in core are the actual source of truth

6. **Create platform binding for Cowork** (`platform-bindings/cowork.yaml`):
   - Subset of modes relevant to Cowork
   - Plugin format constraints

### Deliverables
- [ ] Platform bindings for CC, CP, CW
- [ ] `kf-compile.py` that generates all three variants
- [ ] Compilation manifest format defined and generated
- [ ] Compiled CC matches hand-crafted CC (or is intentionally improved)
- [ ] Upgrade `sync-modules-cp.yml` to invoke compiler instead of direct file copy (see `docs/planning/cross-repo-sync.md`)
- [ ] Add `CORE_SYNC_TOKEN` secret to knowledgeforge-core and activate both sync workflows
- [ ] Compiled CP matches current CP

### Validation Gate
Full round-trip: edit a module in core → compile → verify change appears in all three target repos.

---

## Phase 7: Architectural Changes (Days 26-35)

### Goal
Implement the larger structural changes from the research that were deferred from Phase 4 because they require more effort and carry higher risk.

### Steps

1. **Module 16 (Operational Bounds) — Reaction engine** (from `agent-orchestrator-integration.md`):
   - Declarative reaction system: trigger → auto-respond → retry → escalate
   - Subsumes existing circuit breakers (they become a reaction configuration)
   - New reactions: context_pressure, mode_failure, confidence_drift, stale_state

2. **Module 08 (Synthesizer) — Two-loop research architecture** (from `ai-research-skills-integration.md`):
   - Inner loop: rapid pattern extraction passes (5-10 per cycle)
   - Outer loop: reflective synthesis + direction decision (DEEPEN/BROADEN/PIVOT/CONCLUDE)
   - CONCLUDE criteria: findings are self-contained, abstract-ready
   - Integration with Monitor: stuck inner loop → force outer loop

3. **Module 14 (Metacognitive Monitor) — Command-level scoped hooks** (from `hooks-mastery-integration.md`):
   - Declare hooks in slash command frontmatter (fire only for that command)
   - Mode-specific Stop validators that don't affect other modes

4. **Module 21 (Knowledge Accretion) — Monitor generation from diffs** (from `background-agents-integration.md`):
   - When module specs change, generate corresponding validation checks
   - File checks to `wiki/validation/{module}_{check_name}.md`
   - Don't schedule generic linter runs — trigger-specific checks per change

5. **Lazy command dispatch exploration** (from `orchestra-integration.md`):
   - This is the HIGHEST RISK item — if the Phase 1-2 hook + skills approach works well, lazy dispatch may be unnecessary
   - Evaluate: does the hook-driven architecture already solve the context budget problem that lazy dispatch was meant to address?
   - If yes: document as "solved by hook routing" and close
   - If no: implement Orchestra-style split router + deferred command files

### Deliverables
- [ ] Reaction engine spec and integration with existing bounds
- [ ] Two-loop synthesis architecture in Synthesizer spec
- [ ] Command-level scoped hooks for key modes
- [ ] Monitor generation for module changes
- [ ] Decision on lazy dispatch (adopt or close)

### Validation Gate
Full pipeline test: multi-mode chain (Builder → Critic → Builder revision) with all Phase 3-7 infrastructure active. Regression check against Phase 2 baseline.

---

## Phase 8: Web Agents Variant (Days 36-50)

### Goal
Build the FastAPI web agents variant — the only platform that exercises multi-model selection and dynamic routing.

### Steps

1. **Scaffold FastAPI application** (`knowledgeforge-web/`):
   - `POST /orchestrate` — single-mode execution
   - `POST /chain` — multi-mode chain execution
   - `POST /accrete` — submit accretion candidate
   - `WebSocket /stream` — streaming mode execution

2. **Implement model selection algorithm:**
   - Tier 0 (router): OLMo 3 7B or Gemma 3 for classification
   - Tier 1 (workhorse): Claude Sonnet 4 via OpenRouter for evaluative
   - Tier 2 (frontier): Claude Opus 4 for novel + GPT-5 for cross-model judge
   - Cost guard integration with Operational Bounds

3. **Implement OpenRouter integration:**
   - Unified API for all providers
   - Fallback chains per task type
   - Provider preferences (sort by latency or price)

4. **Implement per-step model selection in chains:**
   - Different models for different chain steps
   - Cross-provider judge isolation for auto-verification

5. **Compile prompts for all model × mode combinations:**
   - Use `kf-compile --target web-agents --model all`
   - Store in `prompts/{model_id}/{mode}.md`

6. **State management:**
   - Supabase for persistent state (routing index, accretion, session history)
   - Redis for session state (active mode, Tier 2 working state)

7. **COS integration point:**
   - API endpoint for COS to call KF orchestration
   - KF modes callable from COS analyzers

### Deliverables
- [ ] FastAPI application with all endpoints
- [ ] OpenRouter integration with fallback chains
- [ ] Dynamic model selection working
- [ ] Cross-model judge isolation verified
- [ ] Compiled prompts for all model × mode combinations
- [ ] COS integration endpoint

### Validation Gate
Execute the same "Review security and prioritize fixes" chain via:
- Claude Projects (gold standard)
- Claude Code (hook-driven)
- Web agents (multi-model)

Compare output quality across all three. Web agents should match or exceed CP due to cross-model verification.

---

## Phase 9: Research Ingestion Pipeline (Days 51-55)

### Goal
Build the `kf-analyze-research` tool that processes research packages and proposes updates across all targets simultaneously.

### Steps

1. **Build research analysis chain** (Expert → Strategist → Builder):
   - Expert: analyze findings, map to KF modules
   - Strategist: prioritize changes (T1/T2/T3)
   - Builder: generate spec deltas, wiki entries, profile updates

2. **Build `kf-analyze-research` CLI:**
   - Input: research document (markdown)
   - Output: proposed changes categorized by type
   - Human review gate before application

3. **Build `kf-apply-research` CLI:**
   - Input: approved changes from analysis
   - Action: apply to core modules, bump versions, update changelogs
   - Trigger: `kf-compile --all` to regenerate all targets

4. **Test end-to-end with AI Tinkerers findings:**
   - Drop the research document into `inbox/`
   - Run analysis
   - Review proposed changes
   - Apply
   - Compile all targets
   - Verify changes propagated correctly

### Deliverables
- [ ] `kf-analyze-research` tool
- [ ] `kf-apply-research` tool
- [ ] End-to-end test with real research package
- [ ] Documentation for research ingestion workflow

### Validation Gate
Drop a new research package → analyze → apply → compile → verify all four targets updated correctly with zero manual intervention after the review gate.

---

## Phase 10: Continuous Validation and Tuning (Ongoing)

### Goal
Establish ongoing measurement and calibration of the full system.

### Steps

1. **Routing accuracy monitoring:**
   - Log every routing decision (prompt → mode → decision_type → cross_cutting)
   - Weekly review: are there systematic misroutes?
   - Expand test suite as new patterns emerge

2. **CP-CC parity tracking:**
   - Monthly: run 20 identical prompts through CP and CC
   - Score outputs blind
   - Track parity gap over time (goal: CC ≥ CP)

3. **Model profile maintenance:**
   - When models update (Sonnet 4.1, GPT-5.1, etc.), re-run weakness canaries
   - Update profiles, recompile affected targets

4. **Accretion health:**
   - Track accretion rate, reuse rate, linter yield
   - Quarterly knowledge base health check

5. **Hook performance monitoring:**
   - Track hook latency (target: <500ms for routing hook)
   - Track hook failure rate (target: <1%)
   - Monitor for infinite loop conditions in Stop hook

### Deliverables
- [ ] Monitoring dashboard or log analysis scripts
- [ ] Monthly parity report template
- [ ] Model profile update checklist
- [ ] Accretion health metrics

---

## Execution Timeline Summary

| Phase | Days | Description | Key Dependency |
|-------|------|-------------|---------------|
| **0** | 1 | Repo setup and sync | None |
| **1** | 2-4 | Pre-prompt routing hook | Ollama + Gemma |
| **2** | 5-7 | Decompose CLAUDE.md | Phase 1 (hook must work first) |
| **3** | 8-10 | Stop gate + state survival hooks | Phase 2 (.kf/ structure) |
| **4** | 11-14 | Module spec updates from research | Phase 0 (canonical modules in core) |
| **5** | 15-18 | Model profiles | Phase 4 (updated specs inform profiles) |
| **6** | 19-25 | Compiler MVP | Phase 2 + 5 (both inputs ready) |
| **7** | 26-35 | Architectural changes | Phase 4 (spec foundation) |
| **8** | 36-50 | Web agents variant | Phase 5 + 6 (profiles + compiler) |
| **9** | 51-55 | Research ingestion pipeline | Phase 6 (compiler must exist) |
| **10** | Ongoing | Monitoring and tuning | All phases |

**Critical path:** Phase 0 → Phase 1 → Phase 2 → Phase 3 → (Phase 4 parallel) → Phase 6

**Phase 4 can run in parallel** with Phases 1-3 since it's spec-only changes to core modules.

---

## Success Criteria (End State)

| Metric | Target |
|--------|--------|
| CC output quality vs. CP | CC ≥ CP on blind comparison |
| Routing hook accuracy | >90% mode selection, >85% cross-cutting recall |
| Hook latency | <500ms per prompt |
| Compaction survival | 100% routing state preserved |
| Stop gate enforcement | 0 incomplete outputs bypass gate |
| Research ingestion time | <1 day from drop to all targets updated |
| Cross-model verification | Adversarial yield >20% (catches real issues) |
| Context efficiency | CLAUDE.md <8K tokens, total per-request <25K |

---

## Version Mapping

| Version | Content |
|---------|---------|
| **KF 6.6.1** | Current state (CP source of truth) |
| **KF 7.0.0** | Hook-driven routing + decomposed CC + all research spec updates (Phases 1-4) |
| **KF 7.1.0** | Compiler MVP + model profiles (Phases 5-6) |
| **KF 7.2.0** | Architectural changes + web agents (Phases 7-8) |
| **KF 7.3.0** | Research ingestion pipeline (Phase 9) |
