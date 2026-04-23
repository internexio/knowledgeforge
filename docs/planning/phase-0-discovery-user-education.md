# Phase 0 Discovery: User Education Layer

**Date:** 2026-04-23
**Purpose:** Pre-implementation discovery for KF User Education Layer patch

---

## 1. Existing User-Facing Docs

| Filename | Audience | First sentence | Conflicts with quickstart spec? |
|----------|----------|----------------|--------------------------------|
| `README.md` | User-facing (public) | "Single source of truth for the KnowledgeForge reasoning framework." | No — high-level intro, quickstart could cross-link here |
| `CLAUDE.md` | Agent-facing (project AI config) | "KnowledgeForge Core is the canonical source for all KF module specs, plans, wiki, and (when built) the compiler." | No — agent/contributor config, not user intro |
| `IMPLEMENTATION_PLAN.md` | Agent/contributor-facing | "Transform KF from a single-platform prompt system into a compiled, multi-platform, multi-model framework..." | No — internal roadmap, not end-user content |
| `load-map-claude-code.md` | Agent/contributor-facing | "KnowledgeForge Load Map — `claude-code`" | No — compile artifact, machine-navigable |
| `load-map-claude-projects.md` | Agent/contributor-facing | Load map for CP variant | No — compile artifact |
| `load-map-vscode.md` | Agent/contributor-facing | Load map for VSCode variant | No — compile artifact |
| `modules/06_quick_reference.md` | Agent-facing (loaded on demand) | "Quick lookup for all patterns, checklists, mode triggers, integration flows, and core concepts" | Partial — Module 06 is agent reference, not user decision tree; quickstart duplicates the routing table section intentionally at a shallower depth |

**Assessment:** No existing user-facing quickstart or onboarding doc exists. README.md is the closest entry point but assumes framework familiarity. No conflicts with a new quickstart — it fills a documented gap.

---

## 2. Module 01 Navigator — Findings

- **Current version:** 6.6.1 (module metadata yaml) / CC Skill version 7.0.0
- **Disambiguation protocol location:** "Ambiguity Detection Protocol" section, lines 187–237. Three-step protocol: Interpretation Generation (L190–198), Ambiguity Classification (L200–223), Resolution (L225–237).
- **Confusion detection insertion point:** No current "confusion detection" protocol for repeated ambiguous clarification exists. The closest is the "Anti-Patterns" section (L333–346), which notes: "Users who ask the same question differently (they didn't get what they needed — maybe ambiguity was missed)." The insertion point for a "second consecutive ambiguous clarification" amendment is **after the Anti-Patterns section, before Success Criteria** (between line 346 and line 349). Specifically, it belongs as a new sub-section under Ambiguity Detection Protocol: "Step 4 — Loop Detection" covering the circuit-breaker behavior when the user's second clarification response is itself ambiguous.
- **Circuit breaker protocol:** Not present as a named protocol in Module 01. Module 16 (Operational Bounds) defines the general circuit breaker: "3 consecutive failures → halt." Module 06 Quick Reference echoes this at line 374: "Circuit breakers: 3 consecutive failures → halt. 2 chain failures at same step → abort chain." Module 01 has no Navigator-specific circuit breaker — it currently relies on the "maximum one clarifying question per turn" constraint (L148) with no escalation path defined for the case where the user's answer to that question is also ambiguous.
- **Routing index schema change needed:** No. The routing index (Module 19, Tier 1 memory, ~150 chars/entry) stores modes engaged, decisions made, task state. Navigator routing decisions auto-populate this. Adding a confusion detection amendment does not require schema changes — it emits a routing decision like any other Navigator resolution.

---

## 3. Module 11 Calibrator — Overlap Analysis

- **Context Hygiene Audit behavior:** Five-dimension checklist (Module 11, lines 633–676): (1) Instruction Conflict Scan — multiple CLAUDE.md conflicts, duplicate instructions; (2) Staleness Check — rules referencing past system states; (3) Verbosity Assessment — context token load, compression candidates; (4) Wiki Hygiene — low grounding score entries, superseded topics; (5) Memory Decay Check — stale Tier 3 entries. Fires on new project setup, explicit request, or performance degradation signal. Output is a structured audit report. Surface-only, never auto-modifies.
- **Fit-check functional overlap estimate:** 15%
- **Overlap assessment:** CLEAR (<20%)
- **Basis for estimate:** The hypothetical fit-check skill (user describes work in 2-3 sentences, returns 2-3 most relevant KF modes) operates on *user request classification* — which mode fits this person's current task. Context Hygiene Audit operates on *project configuration health* — is the existing CLAUDE.md polluted, stale, or conflicting. These are orthogonal concerns. The 15% overlap is from both touching the Calibrator domain (setup/configuration signals) and both potentially surfacing Calibrator as a mode recommendation. No functional overlap in inputs, outputs, or protocol. The fit-check is a routing/onboarding tool; Context Hygiene Audit is a maintenance/health tool. They could be used in the same session (fit-check first, then hygiene audit if Calibrator is recommended) without any conflict.

---

## 4. Onboarding Term Grep Results

| Term | File | Line | Content snippet |
|------|------|------|-----------------|
| `onboarding` | `wiki/architecture/scaffolding-vs-patching-pattern.md` | 143 | "Onboarding contributors to KF — this entry plus `neuro-symbolic-pattern-validation` together explain the design philosophy" |

All other terms (`quickstart`, `tutorial`, `getting started`, `fit check`, `new user`) returned zero matches across the entire repo.

**Interpretation:** No existing quickstart infrastructure of any kind. The single "onboarding" reference is in a wiki Tier 0 entry as a reuse context annotation — it names two wiki entries as the design philosophy onboarding artifacts but does not constitute a user-facing guide. The gap is confirmed.

---

## 5. Mode Files — Decision Tree Viability

The 9 user-facing modes (excluding infrastructure modules 12–25):

| Mode | Module | Purpose (from metadata) | Single-entry viable? | Flag |
|------|--------|--------------------------|----------------------|------|
| Navigator | 01 | Detect and resolve genuinely ambiguous user requests — fires only when multiple valid interpretations exist | Yes — "Use when your request could mean two different things" | |
| Builder | 02 | Create new agents and complete specifications from requirements | Yes — "Use when creating a spec, agent, or system prompt" | |
| Coordinator | 03 | Design multi-agent workflows by mapping dependencies first, then deriving the coordination pattern from the graph | Yes — "Use when orchestrating multiple agents or workflows" | |
| Expert | 05 | Provide domain-specific analysis that forces second-order reasoning Sonnet naturally skips | Partial flag — Expert has three sub-variants (domain, infra, ERA). A single decision-tree entry works if described as "deep analysis with second-order effects" but the sub-variant routing is invisible to users. The tree entry must generalize across variants. | FLAG: Expert has 3 sub-variants (domain, infra, ERA) — decision tree entry must cover all three without sub-menu |
| Critic | 07 | Systematically challenge specifications, find unstated assumptions, and identify edge cases — including adversarial variant for automatic chain verification, knowledge base linter variant for health checks, and infrastructure audit variant for hosting assessment | Partial flag — same multi-variant issue as Expert; 3 explicit variants named in purpose. User-facing entry can generalize to "review, validate, or audit any artifact." | FLAG: Critic has 3 named variants (adversarial, linter, audit) — decision tree entry must stay at the generalization level |
| Synthesizer | 08 | Extract reusable patterns from disparate sources and identify unifying frameworks | Yes — "Use when finding patterns across multiple examples or artifacts" | |
| Debugger | 09 | Systematically diagnose problems through structured hypothesis testing and elimination | Yes — "Use when something is broken or behaving unexpectedly" | |
| Strategist | 10 | Make strategic decisions about what to build, when to build it, and what to defer through explicit trade-off reasoning | Yes — "Use when deciding between options or prioritizing work" | |
| Calibrator | 11 | Generate complexity-aware AI coder configuration that scales from hobby projects to regulated-industry deployments | Yes — "Use when setting up or auditing AI coder configuration" | |

**Summary:** 7 of 9 modes reduce cleanly to a single decision-tree entry. Expert and Critic both have multi-variant purposes that require the decision tree entry to stay at the generalization level (not expose sub-variants to users). This is achievable — the variants are implementation details, not user-facing routing branches.

---

## 6. Wiki Onboarding Entries

No Tier 0 entries address user onboarding, framework intro, or quickstart topics.

Existing entries by domain:
- `wiki/architecture/` — 3 entries: scaffolding-vs-patching-pattern, neuro-symbolic-pattern-validation, pattern-extraction-reuse-heuristic
- `wiki/orchestration/` — 4 entries: multi-framework-cp-composition, kf-version-gap-bridging, adversarial-filename-audit, schema-first-elicitation-order
- `wiki/infrastructure/` — 1 entry: flat-namespace-prefix-convention
- `wiki/compiler/` — 1 entry: multi-repo-artifact-placement

The `scaffolding-vs-patching-pattern` entry (line 143) mentions onboarding contributors as a reuse context but is not itself an onboarding document.

**Conclusion:** No wiki coverage of onboarding topics. No conflicts with adding new entries.

---

## 7. Skills Directory

- **Exists in core repo:** No — `skills/` directory does not exist in `knowledgeforge-core/`
- **Path convention:** Skills compile to `.claude/skills/kf/` in variant repos (e.g., `knowledgeforge-cc`). Source sections are embedded in module files under `## CC Skill` headings. The compiler extracts `## CC Skill` sections from each module and writes them to `.claude/skills/kf/{mode-name}.md` in the target variant repo.
- **Conventions (observed from load-map and module files):**
  - Skills live in module files as `## CC Skill` sections
  - Naming: `{lowercase-mode-name}.md` (e.g., `navigator.md`, `calibrator.md`)
  - Format: `# KF Mode: [Name]` header, `**Version:** X.X.X`, `**Loaded by:** [KF-ROUTE] directive or /kf-{mode} command`, then Purpose / Protocol / Output Format / Quality Gates / Variants sections
  - Section-Load Map at the end of each CC Skill points to the full module for deeper context
  - A new skill for user education (e.g., a quickstart or fit-check) would need a `## CC Skill` section added to a relevant module (or a new module if it warrants one), and a corresponding `## CC Agent` section if it should also be an agent

---

## 8. System Version (kf.yaml)

- **Current version:** 7.0.1
- **Phase:** 6 (Compiler MVP — complete)
- **Variants:**
  - `knowledgeforge-cp` — Claude Projects variant, compiled, status: compiled
  - `knowledgeforge-cc` — Claude Code variant, compiled, status: compiled
  - `knowledgeforge-cw` — Cowork variant, status: drifting
  - `knowledgeforge-web` — Web agents variant, status: future (Phase 8)

---

## 9. Module 06 Quick Reference

- **Exists:** Yes — `modules/06_quick_reference.md`
- **Version:** 6.6.0 (module metadata) / 6.6.1 (changelog)
- **User-facing content:** Partial. The Agent Modes table (lines 93–105) and Implicit Routing Table (lines 461–471 in the CC Agent section) are the closest to user-facing content. However, Module 06 is designed as an agent reference loaded on demand — it is comprehensive and internally-referenced, not a user entry point.
- **Cross-link target viability:** Yes — viable. The quickstart decision tree can cross-link to Module 06's Agent Modes table and the routing table for users who want full depth after getting their initial orientation. The quickstart would be the shallow entry; Module 06 is the deep reference. No content duplication concern — the quickstart is decisional ("which mode for my situation"), Module 06 is comprehensive reference.

---

## Escalation Flags

- **TAXONOMY_NOT_ENFORCED:** INFORMATIONAL — `taxonomy/` directory exists but is empty (only `.gitkeep`). Wiki entries use a `metadata:` block (not `domain:/topic:/tags:` frontmatter as the wiki entry template in CLAUDE.md describes). If a new wiki entry is created as part of the user education layer, it should follow the existing `metadata:` block convention from observed wiki entries rather than the CLAUDE.md template (which may be a spec-vs-implementation gap). Flag for resolution if wiki entries are part of deliverables.

- **NAVIGATOR_CIRCUIT_BREAKER_ABSENT:** INFORMATIONAL — No Navigator-specific circuit breaker protocol exists for the "second consecutive ambiguous clarification" case. The general Module 16 circuit breaker (3 failures → halt) applies but is not wired into Navigator's protocol explicitly. The confusion detection amendment will be the first instance of this escalation path in Module 01. No blocking issue — the insertion point is clear.

- **EXPERT_CRITIC_MULTI_VARIANT:** INFORMATIONAL — Both Expert (3 sub-variants) and Critic (3 sub-variants) have multi-variant purpose statements. Decision tree entries for these modes must stay at the generalization level. Implementation note only — not a blocker.

- **SKILLS_DIR_IN_CORE:** INFORMATIONAL — No `skills/` directory in `knowledgeforge-core/`. New skills are authored as `## CC Skill` sections inside module files, not as standalone files in core. A fit-check skill would be authored as a `## CC Skill` section in an appropriate module (likely Module 01 for routing assistance, or a new Module 26 for user education). Confirm which module is the right home before implementation.

---

## Phase 0 Exit Condition

**CLEAR TO PROCEED**

All discovery items resolved with no blocking escalations. Findings:
1. No existing user-facing quickstart, onboarding, or fit-check content — gap confirmed, no conflicts.
2. Module 01 insertion point for confusion detection identified (after Anti-Patterns section, before Success Criteria; label it "Step 4 — Loop Detection" under Ambiguity Detection Protocol).
3. Calibrator overlap is CLEAR at ~15% — no functional overlap with fit-check skill.
4. Expert and Critic multi-variant purposes require decision-tree entries to stay generalized — achievable.
5. Skills are authored as `## CC Skill` sections in module files; no standalone `skills/` dir in core.
6. kf.yaml is at 7.0.1; any module changes bump to 7.0.2 minimum.
7. Module 06 is a viable deep-reference cross-link target for the quickstart.
8. Taxonomy enforcement is aspirational (empty directory) — follow observed `metadata:` block convention for any new wiki entries.
