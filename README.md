# KnowledgeForge

**Version:** 7.32.0 | **Status:** Active | **Modules:** 26 (M00-M25) | **License:** Apache-2.0

Reasoning orchestration layer for AI coding assistants. Routes requests to specialized modes with targeted context injection, patching known failure modes: skipping hypotheses, hiding trade-offs, missing gaps, over-engineering simple problems.

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

## Repository Structure

`knowledgeforge-core` is the source. All platform variants compile from here.

| Repo | Role |
|------|------|
| **knowledgeforge-core** (this) | Module specs, plans, wiki, compiler |
| `knowledgeforge-cc` | Claude Code variant (compiled) |
| `knowledgeforge-cp` | Claude Projects variant (compiled) |

Changes go into core first, then compile out. Never edit variant repos directly for module changes.

```
modules/           # 26 canonical module specs (M00-M25)
compiler/          # kf-compile.py — builds platform variants from core
platform-bindings/ # Per-platform adaptation rules (YAML)
hooks/             # Claude Code hooks (routing, session, validation)
wiki/              # Tier 0 accreted knowledge base
taxonomy/          # Controlled vocabulary (10 domains, ~40 topics, ~55 tags)
model-profiles/    # Per-model weakness/strength maps
templates/         # Spec templates (Module 04)
tests/             # Routing and module test suites
docs/              # Platform distribution matrix, planning docs
plans/             # Architecture session documents (read-only reference)
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
| M15 | Grounding Scores | Knowledge trust 0.0-1.0 |
| M16 | Operational Bounds | Circuit breakers, resource limits |
| M17 | Temporal Knowledge | Knowledge age and decay rates |
| M18 | Salience Allocation | Multi-task attention weighting |
| M19 | Memory Architecture | Tier 0-3 memory system |
| M20 | Permission Model | Risk tiers (LOW / MEDIUM / HIGH) and capability gates |
| M21 | Knowledge Accretion | Cross-session knowledge persistence |
| M22 | Semantic Wiki Search | Two-phase retrieval, grep fallback |
| M23 | Taxonomy Enforcement | Controlled vocabulary validation |
| M24 | Verbatim History Mining | Conversation turn storage and recall |
| M25 | Entity Relationship Analysis | ERA post-routing pass: entity graph, cardinality, coupling |

---

## Setup

### Claude Code (knowledgeforge-cc)

```bash
# Clone the compiled CC variant
git clone https://github.com/internexio/knowledgeforge-cc ~/.claude/knowledgeforge

# Deploy hooks (routing, session management, validation)
cd ~/.claude/knowledgeforge
bash scripts/deploy-hooks.sh
```

Skills and agents install under `~/.claude/skills/` and `~/.claude/agents/`. The routing hook (`kf-route.py`) fires on every prompt and injects mode directives before Claude sees the request.

The hook uses a fast LLM for routing classification. Set `GEMINI_API_KEY` in your environment, or set `KF_ROUTE_MODEL` to any compatible endpoint. The hook degrades gracefully if the classifier is unavailable.

### Claude Projects (knowledgeforge-cp)

> Before re-uploading: delete all existing project knowledge files first. Claude Projects appends rather than replaces. Duplicate filenames create a contradiction source where retrieval cannot distinguish canonical from stale.

1. Create or open a Claude Project at [claude.ai](https://claude.ai).
2. Go to **Project Instructions** and paste the full contents of `00_Project_Instructions-Claude.md` from `knowledgeforge-cp/`.
3. Under **Project Knowledge**, upload all 25 knowledge files from `knowledgeforge-cp/`.
4. Start a conversation. The system classifies and routes every request automatically.

Note: M25 (ERA) is required. The orchestrator runs ERA as a post-routing, pre-execution pass on Builder, Coordinator, Expert, Strategist, and Critic requests. Omitting it leaves five routing paths unguarded.

---

## Compiling from Core

If you have `knowledgeforge-core` and want to compile a variant:

```bash
# Claude Code variant
python3 compiler/kf-compile.py --target claude-code --output /path/to/knowledgeforge-cc

# Claude Projects variant
python3 compiler/kf-compile.py --target claude-projects --output /path/to/knowledgeforge-cp

# Verify determinism (build twice, diff)
bash scripts/verify-deterministic-build.sh
```

Compilation flags can override binding defaults:

```bash
# Example: enable optional integration blocks
python3 compiler/kf-compile.py --target claude-code --set cos=true --output /tmp/kf-cc-cos
```

See `docs/dist-matrix.md` for full platform capability and module coverage matrix.

---

## Contributing

See `CONTRIBUTING.md` for module conventions, versioning rules, and commit format.
See `SECURITY.md` for the vulnerability reporting process.

---

## License

Apache-2.0. Copyright 2026 David Pedersen. See `LICENSE`.
