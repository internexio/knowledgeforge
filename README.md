# KnowledgeForge

**Version:** 7.32.0 | **Status:** Active | **Modules:** 26 (M00–M25) | **License:** Apache-2.0

Reasoning orchestration layer for AI coding assistants. Routes requests to specialized modes with targeted context injection, patching known failure modes: skipping hypotheses, hiding trade-offs, missing gaps, over-engineering simple problems.

**Platforms:** [Claude Code](platforms/claude-code/) · [Claude Projects](platforms/claude-projects/) · [ChatGPT Projects 🧪](platforms/chatgpt/) · [Codex CLI 🧪](platforms/codex/) · [VSCode 🧪](platforms/vscode/) · [Plugin Bundle 🧪](platforms/plugin-bundle/) · [Cursor 🧪 planned](platforms/cursor/) · [Gemini 🧪 planned](platforms/gemini/)

> Only the Claude Code and Claude Projects variants are currently considered tested. All non-Claude targets are experimental.

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

See [`platforms/claude-code/`](platforms/claude-code/) for the full install guide and load map.

---

### Claude Projects

> **Before re-uploading:** delete all existing KnowledgeForge knowledge files first. Claude Projects appends rather than replaces — duplicate filenames create a contradiction source where retrieval cannot distinguish canonical from stale.

1. Create or open a Claude Project at [claude.ai](https://claude.ai)
2. **Project Instructions** → paste the full contents of [`platforms/claude-projects/00_Project_Instructions-Claude.md`](platforms/claude-projects/00_Project_Instructions-Claude.md)
3. **Project Knowledge** → upload all 25 files from [`platforms/claude-projects/`](platforms/claude-projects/) (`01_Navigator_Agent.md` through `25_Entity_Relationship_Analysis.md`)
4. Start a conversation — routing is automatic

> M25 (ERA) is required. The orchestrator runs Entity Relationship Analysis as a post-routing pass on Builder, Coordinator, Expert, Strategist, and Critic requests. Omitting it leaves five routing paths unguarded.

See [`platforms/claude-projects/`](platforms/claude-projects/) for the full install guide.

---

### ChatGPT Projects

> **Experimental:** This variant has not received the same validation coverage as the Claude variants.

Pre-compiled files are in [`platforms/chatgpt/`](platforms/chatgpt/) — no build step needed.

1. Open your ChatGPT Project → **Settings > Instructions** → paste the contents of `platforms/chatgpt/kf-chatgpt-instructions.md`
2. **Knowledge** → upload all files from `platforms/chatgpt/knowledge/`

> Before re-uploading: delete existing KF knowledge files first. ChatGPT does not deduplicate by filename.
>
> If you hit a file limit (Custom GPTs cap at 20): prioritize `knowledge/01`–`knowledge/11` (the mode specs) over the infrastructure modules `12`–`25`.

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

## Modes

| Mode | Trigger signals | Notes |
|------|----------------|-------|
| **Builder** | "create", "build", "generate spec", "write", "implement", "scaffold" | PDIA method; auto-verify on chain output |
| **Critic** | "review", "validate", "find gaps", "audit", "sanity check", "LGTM?" | 4 variants: regular, linter, audit, adversarial |
| **Critic (linter)** | "health check the knowledge base", "lint the wiki" | Staleness, contradictions, redundancy |
| **Critic (audit)** | "hosting audit", "infrastructure inventory", "SPOF analysis" | Decomposition readiness |
| **Debugger** | "not working", "debug", "failing", "why is this", "root cause" | Hypothesis-driven; requires >0.8 confidence |
| **Strategist** | "prioritize", "trade-offs", "should I", "which option", "ROI" | Explicit trade-offs + reversibility assessment |
| **Synthesizer** | "find patterns", "extract", "what do these have in common" | Every pattern requires at least one anti-pattern |
| **Calibrator** | "setup project", "CLAUDE.md", "AI coder config", "guardrails" | Complexity-appropriate; avoids over-engineering |
| **Expert** | "deep analysis", "blast radius", "threat model", "architecture review" | Adversarial depth; emits decision_type_exercised |
| **Expert (infra/ML)** | "design infrastructure", "plan service topology", "GPU sizing", "model deployment" | Expert analyzes; Builder produces architecture doc |
| **Expert (ERA)** | "map entity relationships", "audit module dependencies", "model agent contracts" | Entity graph + ERA Specification Template |
| **Expert (research)** | "find evidence for", "ground this claim", "what does the research say" | Semantic Scholar MCP; WebSearch fallback available |
| **Coordinator** | "workflow", "multi-agent", "orchestrate", "fan out", "delegate" | Dependency-first; derives coordination pattern from graph |
| **Navigator** | Ambiguous intent with different output types for top-2 candidates | One targeted question; then routes |

Modes chain automatically. "Fix this bug" runs Debugger then Builder. "Review and tell me what to fix first" runs Critic then Strategist. Declared in the response before execution.

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

## Repository Structure

This repo is the canonical source. All platform variants compile from here.

| Repo | Role |
|------|------|
| **knowledgeforge** (this) | Module specs, plans, wiki, compiler |
| `knowledgeforge-cc` | Claude Code variant (pre-compiled) |
| `knowledgeforge-cp` | Claude Projects variant (pre-compiled) |

Changes go into this repo first, then compile out. Never edit variant repos directly for module changes — they are compiler outputs.

```
modules/           # 26 canonical module specs (M00–M25)
compiler/          # kf-compile.py — builds platform variants from source
platform-bindings/ # Per-platform adaptation rules (YAML)
platforms/         # Per-platform install guides and load maps
hooks/             # Claude Code hooks (routing, session, validation)
wiki/              # Tier 0 accreted knowledge base
taxonomy/          # Controlled vocabulary (10 domains, ~40 topics, ~55 tags)
model-profiles/    # Per-model weakness/strength maps
templates/         # Spec templates (Module 04)
tests/             # Routing and module test suites
docs/              # Platform distribution matrix, planning docs
```

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

## Contributing

See `CONTRIBUTING.md` for module conventions, versioning rules, and commit format.
See `SECURITY.md` for the vulnerability reporting process.

---

## License

Apache-2.0. Copyright 2026 David Pedersen. See `LICENSE`.
