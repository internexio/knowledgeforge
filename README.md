# KnowledgeForge

> Structured reasoning infrastructure for AI coding assistants. Decision-aware
> routing, adversarial verification, session-persistent memory, and cross-session
> knowledge accretion — across 27 specialized modules and 9 reasoning modes.

**Version:** 7.36.0 | **Status:** Active | **Modules:** 27 (M00–M26) | **License:** Apache-2.0

**Platforms:** [Claude Code](platforms/claude-code/) · [Claude Projects](platforms/claude-projects/) · [ChatGPT Projects 🧪](platforms/chatgpt/) · [Codex CLI 🧪](platforms/codex/) · [VSCode 🧪](platforms/vscode/) · [Plugin Bundle 🧪](platforms/plugin-bundle/) · [Cursor 🧪 planned](platforms/cursor/) · [Gemini 🧪 planned](platforms/gemini/)

> Only the Claude Code and Claude Projects variants are currently considered tested. All non-Claude targets are experimental.

---

## Why KnowledgeForge?

LLMs have predictable failure modes. Without structure, a factual lookup and a high-stakes
architectural decision go through the same reasoning process. KF patches the failures
that matter:

| Failure Mode | Without KF | With KF |
|---|---|---|
| **Wrong reasoning depth** | Novel strategic question treated like a factual lookup | Decision classification routes each to the correct depth first |
| **Skipping hypotheses** | "The bug is in X" stated without evidence | Debugger requires >0.8 confidence; documents hypothesis → elimination path |
| **Hidden trade-offs** | "Use option A" without mentioning what you sacrifice | Strategist: quantified trade-offs + reversibility always assessed |
| **Spec gaps** | Ships incomplete requirements | Critic: systematic completeness check + adversarial variant assuming ≥1 flaw |
| **Session drift** | Routing accuracy degrades as context fills | Three-tier memory: routing index always loaded, utilization plateaus |
| **Retry loops** | Keeps trying the same failing approach | Circuit breakers: 3 failures → halt, surface pattern, present options |
| **Missing adversarial thinking** | "Looks good to me" without real challenge | Auto-verification fires on qualifying chains — framed to find what the producing agent missed |

> **"KF modes patch Claude's weaknesses, not scaffold its strengths."**
>
> Modes activate only when they prevent a known failure. Most requests route directly.

### How It Works

```
Request arrives
    │
    ▼
Decision Classification (always, silent)
    │
    ├── Reckoning (verifiable answer)
    │       └── Answer directly. <50 tokens. No mode.
    │
    ├── Evaluative judgment (criteria exist)
    │       └── Structured analysis with confidence. Mode if needed.
    │
    ├── Predictive judgment (future outcomes)
    │       └── Explicit assumptions + probability ranges. Mode activated.
    │
    └── Novel judgment (no precedent)
            └── Full expanded reasoning. Human review flagged. Mode activated.
```

---

## Install

### Claude Code

Works with Claude Code, Windsurf, and Zed — any editor that supports the `~/.claude/` agent convention.

```bash
git clone https://github.com/internexio/knowledgeforge
cd knowledgeforge
bash install.sh
```

`install.sh` copies the pre-compiled variant from `platforms/claude-code/.claude/` to `~/.claude/`. No compiler required. Restart your editor after install.

**Optional: faster pre-prompt routing.** Set `GEMINI_API_KEY` in your environment to enable the routing hook — it classifies every request before Claude sees it, injecting the right mode directive automatically. Degrades gracefully without the key.

See [`docs/install.md`](docs/install.md) for the full install guide, `settings.json` configuration, and add-ons overview.

---

### Claude Projects

> **Before re-uploading:** delete all existing KnowledgeForge knowledge files first. Claude Projects appends rather than replaces — duplicate filenames create a contradiction source where retrieval cannot distinguish canonical from stale.

1. Create or open a Claude Project at [claude.ai](https://claude.ai)
2. **Project Instructions** → paste the full contents of [`platforms/claude-projects/00_Project_Instructions-Claude.md`](platforms/claude-projects/00_Project_Instructions-Claude.md)
3. **Project Knowledge** → upload all 26 files from [`platforms/claude-projects/`](platforms/claude-projects/) (`01_Navigator_Agent.md` through `26_KF_Loop_Substrate.md`)
4. Start a conversation — routing is automatic

> M26 (KF-LOOP Substrate) is required. The orchestrator uses the loop substrate for iterative self-improvement patterns across five loop instances. Omitting it leaves the loop orchestration primitive unspecified.

See [`platforms/claude-projects/`](platforms/claude-projects/) for the full install guide. See [`EXPLORATION_PROMPTS.md`](EXPLORATION_PROMPTS.md) for ready-to-paste prompts that exercise specific KF behaviors.

---

### ChatGPT Projects

> **Experimental:** This variant has not received the same validation coverage as the Claude variants.

Pre-compiled files are in [`platforms/chatgpt/`](platforms/chatgpt/) — no build step needed.

1. Open your ChatGPT Project → **Settings > Instructions** → paste the contents of `platforms/chatgpt/kf-chatgpt-instructions.md`
2. **Knowledge** → upload all files from `platforms/chatgpt/knowledge/`

> Before re-uploading: delete existing KF knowledge files first. ChatGPT does not deduplicate by filename.
>
> If you hit a file limit (Custom GPTs cap at 20): prioritize `knowledge/01`–`knowledge/11` (the mode specs) over the infrastructure modules `12`–`26`.

To recompile after module changes:

```bash
python3 compiler/kf-compile.py --target chatgpt --output platforms/chatgpt
```

See [`platforms/chatgpt/`](platforms/chatgpt/) for the full install guide.

---

### Codex CLI

> **Experimental:** Codex support is under active testing and currently exposes only part of Codex's native customization surface.

Pre-compiled output is in [`platforms/codex/`](platforms/codex/) — no build step needed.

Install into one project:

```bash
bash install.sh --codex --project /path/to/your/project
```

Or install globally for all local Codex projects:

```bash
bash install.sh --codex --global
```

The global install writes `~/.codex/AGENTS.md`; the project install writes `AGENTS.md` in the selected project. If either target already contains different instructions, the installer refuses to replace it unless you add `--force`, which creates a timestamped backup first. Use `--dry-run` to preview either command.

To recompile after module changes:

```bash
python3 compiler/kf-compile.py --target codex --output platforms/codex
```

Project instructions are more specific, so keep the project install for repositories that need different behavior. See [`platforms/codex/`](platforms/codex/) for the full install guide.

---

### VSCode (experimental)

```bash
python3 compiler/kf-compile.py --target vscode --output ./dist/vscode
```

See [`platforms/vscode/load-map.md`](platforms/vscode/load-map.md) for what gets generated and where it deploys inside a VSCode extension.

---

### Plugin bundle

> **Experimental:** Bundle generation is implemented, but this distribution has not received the same validation coverage as the Claude variants.

For tool-agnostic deployment (any platform that can load agent files via a plugin):

```bash
python3 compiler/kf-compile.py --target plugin-bundle --output ./dist/plugin-bundle
bash ./dist/plugin-bundle/install.sh
```

See [`platforms/plugin-bundle/load-map.md`](platforms/plugin-bundle/load-map.md) for the full file manifest.

---

## Agent Modes

| Mode | Purpose | Patches This Failure Mode |
|------|---------|--------------------------|
| **Navigator** | Resolve genuinely ambiguous requests | Mis-routing on unclear intent |
| **Builder** | Generate complete specifications (PDIA) | Incomplete specs, missing integration points |
| **Coordinator** | Design multi-agent workflows | Dependency drift, bad handoffs |
| **Expert** | Deep domain analysis with adversarial depth | Surface-level analysis, missed compound failures |
| **Critic** | Systematic gap detection + adversarial variant | "Looks good" without actually checking |
| **Synthesizer** | Extract reusable patterns from examples | Over-specific solutions, no transferable framework |
| **Debugger** | Hypothesis-driven root cause analysis | "I think the bug is..." without evidence |
| **Strategist** | Options analysis with explicit trade-offs | Hidden trade-offs, single-objective optimization |
| **Calibrator** | Complexity-appropriate AI coder config | Enterprise scaffolding on hobby projects |

Modes chain automatically. "Fix this bug" runs Debugger then Builder. "Review and tell me what to fix first" runs Critic then Strategist. The chain plan is declared in the response before execution.

**Mode trigger signals:**

| Signal | Mode | Notes |
|--------|------|-------|
| "Create", "build", "generate spec", "write", "implement", "scaffold" | **Builder** | PDIA method; auto-verify on chain output |
| "Review", "validate", "find gaps", "audit", "sanity check", "LGTM?" | **Critic** | 4 variants: regular / linter / audit / adversarial |
| "Health check the knowledge base", "lint the wiki" | **Critic (linter)** | Staleness, contradictions, redundancy |
| "Hosting audit", "infrastructure inventory", "SPOF analysis" | **Critic (audit)** | Decomposition readiness |
| "Not working", "debug", "failing", "why is this", "root cause" | **Debugger** | Hypothesis-driven; requires >0.8 confidence |
| "Prioritize", "trade-offs", "should I", "which option", "ROI" | **Strategist** | Explicit trade-offs + reversibility assessment |
| "Find patterns", "extract", "what do these have in common" | **Synthesizer** | Every pattern requires ≥1 anti-pattern |
| "Setup project", "CLAUDE.md", "AI coder config", "guardrails" | **Calibrator** | Complexity-appropriate; avoids over-engineering |
| "Deep analysis", "blast radius", "threat model", "architecture review" | **Expert** | Adversarial depth; emits decision_type_exercised |
| "Design infrastructure", "plan service topology", "GPU sizing", "model deployment" | **Expert (infra/ML)** | Expert analyzes; Builder produces architecture doc |
| "Map entity relationships", "audit module dependencies", "model agent contracts" | **Expert (ERA)** | Entity graph + ERA Specification Template |
| "Find evidence for", "ground this claim", "what does the research say" | **Expert (research)** | Semantic Scholar MCP; WebSearch fallback available |
| "Workflow", "multi-agent", "orchestrate", "fan out", "delegate" | **Coordinator** | Dependency-first; derives coordination pattern from graph |
| Genuinely ambiguous intent with different output types for top-2 candidates | **Navigator** | One targeted question; then routes |

---

## Optional Integrations

Configured via `~/.claude/kf-integrations.yaml` (created by `install.sh`). All enabled by default; set `enabled: false` to opt out.

| Integration | Purpose | Fallback |
|-------------|---------|---------|
| `gemini_routing` | Gemini Flash Lite classifies prompts before Claude sees them; injects `[KF-ROUTE]` directives | Native routing via orchestrator table |
| `mempalace` | Semantic wiki search + knowledge graph (M22) | grep-based wiki search |
| `beads` | Task tracker — session priority awareness, `bd ready/close` in workflows | No task tracking; workflow guidance intact |
| `asta` | Semantic Scholar MCP for Expert research variant — paper retrieval, citation grounding | WebSearch fallback; grounding capped at 0.6 |
| `cos` | COS MCP for comms-domain analysis and copy generation (M07/M08/M11) | Standard KF output only |
| `gitnexus` | Code impact analysis, call graph navigation, safe refactoring | Standard file/grep navigation |

---

## Modules

| # | Module | Purpose |
|---|--------|---------|
| M00 | Orchestrator | Agent identity, mode routing, mode chaining |
| M01 | Navigator | Ambiguity detection and resolution |
| M02 | Builder | Spec and implementation generation (PDIA method) |
| M03 | Coordination Patterns | Multi-agent workflow design, handoff contracts |
| M04 | Specification Templates | Reusable spec formats, trigger disambiguators |
| M05 | Expert Agent | Deep analysis, adversarial depth (5 variants) |
| M06 | Quick Reference | Routing table, signal guide |
| M07 | Critic Agent | Review, validation, audit (4 variants) |
| M08 | Synthesizer Agent | Pattern extraction, abstraction, anti-patterns |
| M09 | Debugger Agent | Hypothesis-driven root-cause diagnosis |
| M10 | Strategist Agent | Trade-off evaluation, reversibility, sequencing |
| M11 | Calibrator Agent | Complexity-appropriate AI coder configuration |
| M12 | Calibration Layer | Multi-pass evaluation, judge isolation |
| M13 | Decision Classification | Reckoning / evaluative / predictive / novel |
| M14 | Metacognitive Monitor | Failure-mode self-detection |
| M15 | Grounding Scores | Knowledge trust 0.0–1.0 |
| M16 | Operational Bounds | Circuit breakers, resource limits |
| M17 | Temporal Knowledge | Knowledge age and decay rates |
| M18 | Salience Allocation | Multi-task attention weighting |
| M19 | Memory Architecture | Tier 0–3 memory system |
| M20 | Permission Model | Risk tiers (LOW / MEDIUM / HIGH) and capability gates |
| M21 | Knowledge Accretion | Cross-session knowledge persistence |
| M22 | Semantic Wiki Search | Two-phase retrieval, grep fallback |
| M23 | Taxonomy Enforcement | Controlled vocabulary validation |
| M24 | Verbatim History Mining | Conversation turn storage and recall |
| M25 | Entity Relationship Analysis | ERA post-routing pass: entity graph, cardinality, coupling |
| M26 | KF-LOOP Substrate | Iterative self-improvement loops — eight-stage orchestration primitive (cadence, gate, stratify, recall, reason, verify, act, observe); Wilson-CI gate; five loop instances |

---

## Repository Structure

This repo is the canonical source. All platform variants compile from here.

| Repo | Role |
|------|------|
| **knowledgeforge** (this) | Module specs, plans, wiki, compiler |
| `knowledgeforge-cc` | Claude Code variant (pre-compiled) |
| `knowledgeforge-cp` | Claude Projects variant (pre-compiled) |

Changes go into this repo first, then compile out. Never edit variant repos directly for module changes — they are compiler outputs.

```
modules/           # 27 canonical module specs (M00–M26)
compiler/          # kf-compile.py — builds platform variants from source
platform-bindings/ # Per-platform adaptation rules (YAML)
platforms/         # Per-platform install guides and load maps
hooks/             # Claude Code hooks (routing, session, validation)
wiki/              # Tier 0 accreted knowledge base
taxonomy/          # Controlled vocabulary (15 domains, ~40 topics, ~55 tags)
model-profiles/    # Per-model weakness/strength maps
templates/         # Spec templates (Module 04)
tests/             # Routing and module test suites
docs/              # Platform distribution matrix, planning docs
```

---

## Compiling from Source

```bash
# Claude Code (pre-compiled output lives in-repo at platforms/claude-code/)
python3 compiler/kf-compile.py --target claude-code --output platforms/claude-code

# Claude Projects (pre-compiled output lives in-repo at platforms/claude-projects/)
python3 compiler/kf-compile.py --target claude-projects --output platforms/claude-projects

# ChatGPT Projects (pre-compiled output lives in-repo at platforms/chatgpt/)
python3 compiler/kf-compile.py --target chatgpt --output platforms/chatgpt

# Codex CLI (pre-compiled output lives in-repo at platforms/codex/)
python3 compiler/kf-compile.py --target codex --output platforms/codex

# VSCode extension resources
python3 compiler/kf-compile.py --target vscode --output /path/to/output

# Plugin bundle
python3 compiler/kf-compile.py --target plugin-bundle --output /path/to/output

# Verify determinism (build twice, diff)
bash scripts/verify-deterministic-build.sh
```

Compilation flags can override binding defaults:

```bash
# Enable optional integration blocks (e.g. COS)
python3 compiler/kf-compile.py --target claude-code --set cos=true --output /tmp/kf-cc
```

See `docs/dist-matrix.md` for the full platform capability and module coverage matrix.

---

## Core Principles

1. **Decision classification first** — every request classified before any mode fires
2. **Mode activation only when needed** — patches weaknesses, doesn't scaffold strengths
3. **Direct answers** — no preamble, no hedging, no unnecessary overhead
4. **Adversarial depth** — qualifying chains get automatic adversarial review
5. **Actionable outputs** — user can proceed without follow-up
6. **Forward navigation** — every response ends with next steps

---

## Version History

| Version | Date | Focus |
|---------|------|-------|
| v1 | Apr 2025 | Proof of concept — structured output patterns |
| v2 | Apr 2025 | Agent instructions and navigation |
| v3.1 | Jun 2025 | Comprehensive platform with N8N integration |
| v4 | Dec 2025 | The Great Simplification — 41 files → 7 |
| v5 | Jan 2026 | Expanded modes: Critic, Synthesizer, Debugger, Strategist |
| v5.1 | Jan 2026 | Calibrator Agent; module refinements |
| v6.0 | Mar 2026 | Cognitive architecture: 7 infrastructure modules, meta-principle established |
| v6.1 | Apr 2026 | Prompt routing, three-tier memory, adversarial verification, permission model |
| v6.2 | Apr 2026 | Knowledge Accretion (M21): compile-query-enhance, four-tier memory |
| v6.3 | Apr 2026 | Infrastructure Planning: Expert domain adaptations, architecture + hosting audit templates |
| v6.3.1 | Apr 2026 | Knowledge Maintenance: importance-weighted decay, autonomous maintenance cycle |
| v6.4 | Apr 2026 | Neuro-symbolic identity: empirical validation, token cost observability |
| v6.5 | Apr 2026 | Semantic wiki search (M22), taxonomy enforcement (M23), verbatim history mining (M24) |
| v7.0.0 | Apr 2026 | Compiler pipeline: knowledgeforge-core as single source, kf-compile.py, CI automation |
| v7.1 | Apr 2026 | M25 Entity Relationship Analysis; loop detection; kf-fit-check skill |
| v7.2 | May 2026 | Typed mode handoffs (Handoff_Contract); mode-selection accuracy metric; routing decision log |
| v7.3 | May 2026 | M22 Phase 1 MemPalace: dup-check gate at calibrated 0.85 threshold |
| v7.4 | Jun 2026 | M21 activation_profile on accretion candidates (substrate-agnostic dispatch) |
| v7.5 | Jun 2026 | Compiler Phase 2: cc_rules + settings.kf.json emitters |
| v7.6 | Jun 2026 | M23 vocab: 5 new domains, ~55 new topics, grandfathering policy |
| v7.7 | Jun 2026 | Always-on behavioral patches (Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven) |
| v7.8 | Jun 2026 | M25 entity → path-glob resolver (GitNexus-primary + cached-grep fallback) |
| v7.9 | Jun 2026 | M21 linter violation-event counter |
| v7.10 | Jun 2026 | M20 sub-policies: verifier + accretion candidate tool tier policies |
| v7.11 | Jun 2026 | SPEC 4: accretion vetting gate, Contract B, Knowledge Librarian agent |
| v7.12 | Jun 2026 | SPEC 1: adversarial-critic Untrusted Input Boundary; Contract A |
| v7.13 | Jun 2026 | Per-turn KF-MODE telemetry marker (observability-only) |
| v7.14–7.16 | Jun 2026 | M23 vocab expansion + cleanup (compiler + orchestration domains) |
| v7.17–7.18 | Jun 2026 | Per-turn marker: tool-calling three-case rule; 76.6% → 100% compliance |
| v7.19 | Jun 2026 | M21 native:true gate activated (three-signal content classifier) |
| v7.20 | Jul 2026 | M19 tier model: `.claude/rules/` as compiled Tier 0 projection |
| v7.21 | Jul 2026 | M24 + M19 MemPalace Phase 1/2 split: actual tool surface documented |
| v7.22 | Jul 2026 | Audit remediation: Always-On in STATIC ZONE, 13-contract registry, grounding gate boundary |
| v7.23 | Jul 2026 | M22 Phase 2 active: semantic wiki search operational |
| v7.24 | Jul 2026 | M07 Critic comms-domain variant via COS MCP |
| v7.25 | Jul 2026 | M08/M11 COS emit: Synthesizer + Calibrator comms-domain structured output |
| v7.26 | Jul 2026 | M07 adversarial inverse-premise check; kf-integrations opt-in/out; br-prime-safe.sh |
| v7.27–7.32 | Jul–Aug 2026 | Mid-chain re-entry rule; upstream_invalidation signal; OSS hygiene files; public release |
| v7.33 | Aug 2026 | OSS hygiene: Apache-2.0, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md |
| **v7.34** | **Aug 2026** | **M26 KF-LOOP Substrate added — eight-stage iterative loop primitive, five loop catalog entries, Wilson-CI gate** |
| **v7.35** | **Aug 2026** | **Loop catalog complete — four remaining loop specs written: adversarial-yield, kb-health, pattern-extraction, cos-grounding** |
| **v7.36** | **Aug 2026** | **M00 v7.25.0 with M26 awareness — module reference table, routing, and identity strings updated** |

---

## Contributing

See `CONTRIBUTING.md` for module conventions, versioning rules, and commit format.
See `SECURITY.md` for the vulnerability reporting process.

---

## License

Apache-2.0. Copyright 2026 David Pedersen. See `LICENSE`.
