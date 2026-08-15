# KnowledgeForge — Glossary

Acronyms, invented terms, and framework-specific vocabulary used across KF documentation.

Entries marked **KF-specific** are terms coined or given specific meaning within KnowledgeForge — they may not match general usage elsewhere.

---

## A

**ACCRETION_CANDIDATE** *(KF-specific)*
A flag emitted when a mode produces output that meets two conditions: (1) it's not already in the knowledge base, and (2) it has reuse value for future sessions. When flagged, the Knowledge Librarian agent evaluates it for filing. See [Module 21](../modules/21_knowledge_accretion.md).

**AGI**
Artificial General Intelligence.

**API**
Application Programming Interface.

**A-RAG** *(KF-specific)*
Architectural Retrieval Augmented Generation. A hierarchical retrieval pattern (keyword → semantic → chunk) developed by James Hutchinson. Influenced KF's [Entity Relationship Analysis](../modules/25_entity_relationship_analysis.md) (Module 25). See [Credits](credits.md).

**attempt_ledger** *(KF-specific)*
A cross-session persistence table stored in [Module 19](../modules/19_memory_architecture.md) (Memory Architecture). Records every hypothesis explored by a KF-LOOP iteration alongside a summary of the reasoning used. The exclusion constraint (Invariant I2) prevents the loop from re-exploring hypotheses already documented in the ledger. See [Module 26](../modules/26_kf_loop_substrate.md).

---

## C

**CC** *(KF-specific)*
Claude Code — the CLI-based variant of KnowledgeForge. Pre-compiled output lives in `platforms/claude-code/`. See [install guide](install.md).

**CI**
Confidence Interval (in Wilson-CI gate context) or Continuous Integration (in CI/CD pipeline context). Context disambiguates.

**CI/CD**
Continuous Integration / Continuous Deployment.

**CLI**
Command-Line Interface.

**COS** *(KF-specific in this context)*
Communications Optimization System — a structured comms analysis engine grounded in personality psychology and peer-reviewed research. Integrates with KF's Critic, Synthesizer, and Calibrator modes for B2B copy analysis. See [Add-ons](add-ons.md) and [semalytics.com/cos](https://semalytics.com/cos).

**CP** *(KF-specific)*
Claude Projects — the knowledge-file-based variant of KnowledgeForge. Pre-compiled output lives in `platforms/claude-projects/`. See [install guide](install.md).

---

## D

**degraded=true** *(KF-specific)*
A flag on Expert (research) mode output indicating that Asta MCP was unavailable and the response fell back to WebSearch. When `degraded=true`, grounding is capped at 0.6 and ship disposition is unavailable. See [Module 05](../modules/05_expert_agent.md).

**DIAGNOSE** *(KF-specific)*
One of three Wilson-CI gate outcomes. Fires when neither WAIT nor PROMOTE conditions are met — typically indicating anomalous variance requiring human inspection before the loop continues. See [Module 26](../modules/26_kf_loop_substrate.md).

---

## E

**ERA** *(KF-specific)*
Entity Relationship Analysis — a post-routing pass that extracts entities, maps their relationships, and derives graph properties (cardinality, coupling, dependency shape) before the primary mode executes. Defined in [Module 25](../modules/25_entity_relationship_analysis.md). Fires automatically on Builder, Coordinator, Expert, Strategist, and Critic requests involving more than one entity.

---

## G

**grounding score** *(KF-specific)*
A 0.0–1.0 trust score assigned to knowledge claims. ≥0.6 required to file an accretion candidate. Claims with grounding < 0.6 must carry explicit caveats. Defined in [Module 15](../modules/15_grounding_scores.md).

---

## H

**HAPE** *(COS-specific)*
**H**igh **A**rousal **P**ositive **E**ngagement — COS's proprietary engagement scoring framework. Measures whether content generates the high-arousal positive emotional state associated with sharing, action-taking, and memory encoding. One of the seven analysis frameworks surfaced by the Critic (comms variant).

---

## I

**I1 / I2** *(KF-specific)*
KF-LOOP substrate invariants. **I1**: deterministic GROUP BY evidence stratification must run before the `reason` stage fires — prevents LLM from reasoning over unstratified evidence pools. **I2**: the attempt_ledger exclusion constraint — hypotheses documented in prior iterations cannot be re-explored. See [Module 26](../modules/26_kf_loop_substrate.md).

---

## J

**JSON**
JavaScript Object Notation.

**JWT**
JSON Web Token — a compact, URL-safe token format for stateless authentication.

---

## K

**KB** *(KF-specific in this context)*
Knowledge Base — the `wiki/` directory tree in Claude Code, or the Project Knowledge files in Claude Projects. Managed by [Module 21](../modules/21_knowledge_accretion.md) (Knowledge Accretion) and [Module 22](../modules/22_semantic_wiki_search.md) (Semantic Wiki Search).

**KF** *(KF-specific)*
KnowledgeForge — this framework.

**KF-LOOP** *(KF-specific)*
The iterative self-improvement loop primitive defined in [Module 26](../modules/26_kf_loop_substrate.md). Eight-stage orchestration: cadence → gate → stratify → recall → reason → verify → act → observe. Instances include mode-calibration (reference), adversarial-yield, kb-health, pattern-extraction, and cos-grounding.

**KF-MODE** *(KF-specific)*
Per-turn telemetry marker embedded in responses (internal builds only) indicating which reasoning mode was active. Used for compliance measurement against routing benchmarks.

**KF-ROUTE** *(KF-specific)*
A directive injected into prompts by the `kf-route.py` hook before Claude sees them. Format: `[KF-ROUTE: mode=X | decision=Y | load=[...]]`. Tells the orchestrator which mode to activate and which skill files to load. Requires Gemini API key; degrades gracefully without it.

---

## L

**LLM**
Large Language Model.

**LTS**
Long-Term Support — a software release designated for extended maintenance. KF install guides recommend LTS versions for dependencies.

---

## M

**MCP**
Model Context Protocol — Anthropic's open protocol for connecting AI models to external tools and data sources. KF integrations (MemPalace, GitNexus, Asta, COS, Orchestra) are all MCP servers.

**MFA**
Multi-Factor Authentication.

**ML**
Machine Learning.

---

## N

**native:true** *(KF-specific)*
A classifier signal in [Module 21](../modules/21_knowledge_accretion.md) (Knowledge Accretion) indicating that an accretion candidate was generated from in-context evidence rather than retrieved from external sources. One of three signals in the content classifier gate. Only `native:true` candidates are eligible for auto-filing.

---

## O

**OCEAN** *(psychology)*
Big Five personality trait model: **O**penness, **C**onscientiousness, **E**xtraversion, **A**greeableness, **N**euroticism. Used by COS for personality-matched communication analysis.

**OCR**
Optical Character Recognition.

**OSS**
Open-Source Software.

**Ozymandias Test** *(KF-specific)*
A routing heuristic: if a yes/no question requires multi-paragraph reasoning to answer, it is not a reckoning — upgrade the decision type. Named after the Shelley poem as a reminder that things presented as settled often aren't. Defined in [Module 13](../modules/13_decision_classification.md).

---

## P

**PDIA** *(KF-specific)*
**P**urpose → **D**esign → **I**mplementation → **A**ssessment — the four-phase method used by the Builder mode to generate specifications. Purpose defines the problem and success criteria. Design records decisions and trade-offs. Implementation produces the artifact. Assessment validates it against the stated purpose. See [Module 02](../modules/02_builder.md).

**PII**
Personally Identifiable Information.

**PROMOTE** *(KF-specific)*
One of three Wilson-CI gate outcomes. Fires when the lower bound of the Wilson confidence interval exceeds the promote_threshold — indicating sufficient evidence has accumulated and the loop can advance to the next phase. For saturation loops (pattern-extraction), PROMOTE fires on a *low* ci_lower (space exhausted). See [Module 26](../modules/26_kf_loop_substrate.md).

---

## R

**R@N** *(information retrieval)*
Recall at N — the fraction of relevant items retrieved in the top N results. R@5 means "of all relevant items, how many appear in the top 5?" KF's verbatim + semantic retrieval achieves 96.6% R@5. See [Module 24](../modules/24_verbatim_history_mining.md).

**RAG**
Retrieval-Augmented Generation — a pattern where relevant documents are retrieved from a knowledge store and included in the prompt context before generation.

**REST**
Representational State Transfer — an architectural style for web APIs.

**routing_decision_log** *(KF-specific)*
A persistent log in [Module 19](../modules/19_memory_architecture.md) (Memory Architecture) that records every routing decision made within a session: which mode was selected, the decision type, confidence, and outcome. Used for session continuity and accuracy measurement.

---

## S

**SAP** *(KF-specific in this context)*
Structured Assertion Protocol — a parsing cascade used in [Module 12](../modules/12_calibration_layer.md) (Calibration Layer) to extract structured output from mode responses across multiple fallback strategies.

**Sev1 / Sev2 / Sev3** *(KF-specific)*
Severity levels used by Critic and Adversarial Critic modes. **Sev1**: critical — blocks ship. **Sev2**: significant — should fix before ship. **Sev3**: advisory — worth noting, doesn't block. Adversarial Critic reports Sev2+ only.

**SPOF**
Single Point of Failure — a component whose failure brings down the entire system. Used in Critic (audit variant) infrastructure reviews. See [Exploration Prompt 18](../EXPLORATION_PROMPTS.md).

**SSE**
Server-Sent Events — a push protocol where a server streams events to a client over a persistent HTTP connection. Used by Orchestra MCP.

**STATIC ZONE** *(KF-specific)*
A section of [Module 00](../modules/00_orchestrator.md) (Orchestrator) containing behavioral rules that are embedded in every compiled platform variant, including Claude Projects. Content in the STATIC ZONE cannot be stripped by compile-time flags — it's always present.

**SYNAPSE** *(KF-specific in this context)*
A salience algorithm concept from the PNW AGI Group's research archive. Competitive inhibition model: suppress competing activations before amplifying the target. Informed [Module 18](../modules/18_salience_allocation.md) (Salience Allocation). See [Credits](credits.md).

---

## T

**Tier 0 / Tier 1 / Tier 2 / Tier 3** *(KF-specific)*
The four-tier memory architecture defined in [Module 19](../modules/19_memory_architecture.md). **Tier 0**: persistent domain knowledge — the `wiki/` directory or Project Knowledge files, always available. **Tier 1**: routing index — loaded at session start, tracks decisions and modes. **Tier 2**: mode state — on-demand skill files loaded when a mode activates. **Tier 3**: verbatim history — session turns stored verbatim for semantic retrieval via MemPalace.

**TTL**
Time to Live — how long a cached value is considered valid before expiring.

---

## U

**upstream_invalidation** *(KF-specific)*
A response field a downstream chain step can set when it discovers the prior step's premise was wrong. When non-null at Sev2+, the orchestrator halts forward chain execution and re-enters at the invalidated step with the corrective evidence. Re-entry is exempt from the 3-failure circuit breaker. Defined in [Module 00](../modules/00_orchestrator.md). See [Exploration Prompt 23](../EXPLORATION_PROMPTS.md).

---

## W

**WAIT** *(KF-specific)*
One of three Wilson-CI gate outcomes. Fires when insufficient evidence has accumulated to reach a conclusion — the loop continues collecting observations. The default gate state at low trial counts. See [Module 26](../modules/26_kf_loop_substrate.md).

**WASM**
WebAssembly — a binary instruction format for a stack-based virtual machine, designed for high-performance execution in browsers and serverless runtimes.

**Wilson-CI** *(KF-specific in this context)*
Wilson Score Confidence Interval — a statistical method for computing confidence intervals on binary proportions (success/failure series) that is well-behaved at small sample sizes. Used as KF-LOOP's deterministic gate mechanism: the lower bound of the Wilson interval drives WAIT / PROMOTE / DIAGNOSE decisions without requiring LLM judgment. See [Module 26](../modules/26_kf_loop_substrate.md).

---

## Y

**YAML**
YAML Ain't Markup Language — a human-readable data serialization format. Used for KF configuration files (`kf.yaml`, `kf-integrations.yaml`, platform bindings).
