# KnowledgeForge — Exploration Prompts

Use these prompts to exercise specific KF behaviors. Each is designed to trigger a particular mechanism so you can observe, tune, and validate the framework is working as designed.

> **How to use:** Paste each prompt into a fresh KF session (Claude Code or Claude Projects). The "What to look for" box tells you what correct behavior looks like. If the response doesn't match, the framework has a configuration or depth issue to investigate.

---

## Quick Start — Your First Five Minutes

If you're new to KF, run these three prompts in sequence to see the core system in action:

```
1. What port does Redis use?
2. Should we use GraphQL or REST for our new customer-facing API?
3. Should we acquire our competitor's customer base by offering free migration, 
   knowing it will burn 40% of our remaining runway?
```

> **What to look for:** Q1 = direct answer, ~1 line, zero ceremony. Q2 = structured analysis, explicit trade-offs, confidence stated. Q3 = full expanded reasoning with an explicit flag that this is high-stakes and warrants human review before acting. Three questions, three radically different response depths. That's decision classification working.

---

## 1. Decision Classification + Ozymandias Test

**Exercises:** Four-type decision taxonomy, Ozymandias detection, appropriate depth allocation.

```
I have five questions. Answer all of them:

1. What port does Redis use by default?
2. Should we use GraphQL or REST for our new customer-facing API?
3. Will our current Postgres instance handle 10x traffic growth over the next 18 months?
4. Is our onboarding flow accessible?
5. Should we build our own LLM evaluation framework or contribute to an existing open-source one?

For each answer, tag the decision type you classified it as and explain why in one sentence.
```

> **What to look for:** Q1 is a true reckoning — direct answer, no overhead. Q4 is the Ozymandias trap: it *looks* binary but requires evaluative judgment (what criteria? what evidence?). Q3 should be predictive with explicit assumptions surfaced. Q5 should flag as novel. Depth should increase dramatically from Q1 to Q5.

---

## 2. Mode Routing — Direct Activation (No Navigator)

**Exercises:** Debugger activating directly without Navigator overhead on an unambiguous request.

```
Our checkout API intermittently returns 500 errors under load. It works fine in staging. 
The errors started after last Thursday's deploy but the deploy only changed the discount 
calculation module. Error logs show connection pool exhaustion on the payment gateway client.
```

> **What to look for:** Direct route to Debugger — no clarifying questions. Should generate hypotheses (connection pool leak, config diff between staging/prod, discount calculation adding latency under load), then propose a binary-search elimination strategy. Root cause should be held at hypothesis status until evidence is gathered.

---

## 3. Mode Chain — Builder → Critic (Auto-Adversarial Verification)

**Exercises:** Two-mode chain with automatic adversarial Critic pass on Builder output.

```
Build me a specification for a rate-limiting agent that sits in front of our API gateway. 
It needs to handle per-user limits, per-endpoint limits, and burst allowances. 
Our stack is Go with Redis. Make sure it's solid.
```

> **What to look for:** "Make sure it's solid" triggers Builder → Critic chain. Chain plan stated upfront. Builder produces a PDIA spec with design decisions tagged. Adversarial Critic fires automatically — framed to find what the Builder missed, not confirm it. Final output includes both the spec and the adversarial findings.

---

## 4. Mode Chain — Debugger → Strategist → Builder (HIGH Risk)

**Exercises:** Three-mode chain with auto-verification, compound error risk, HIGH risk tier framing.

```
Our notification system is unreliable — users report missing alerts about 15% of the time 
and we can't reproduce it consistently. We need to decide whether to fix the existing system 
or rebuild it, and then spec out whichever path we choose.
```

> **What to look for:** Three-mode chain declared upfront (Debugger → Strategist → Builder). Debugger diagnoses root cause candidates. Strategist evaluates fix-vs-rebuild with explicit quantified trade-offs and reversibility assessment. Builder specs the chosen path. Auto-verification fires (3+ mode chain = compound error risk). Output should carry HIGH risk framing with explicit review recommendation.

---

## 5. Navigator — Genuine Ambiguity Only

**Exercises:** Navigator activates on multiple valid interpretations that route to *different* modes. Clear intents bypass it entirely.

**Prompt A (Navigator should fire):**
```
Help me with my pipeline.
```

**Prompt B (Navigator should NOT fire):**
```
Debug my pipeline. It's a CI/CD pipeline and it's failing on the test stage.
```

> **What to look for:** Prompt A has legitimate ambiguity — "pipeline" could mean data pipeline (Coordinator), CI/CD pipeline (Debugger), ML pipeline (Builder), or review of an existing one (Critic). One targeted question is correct. Prompt B is unambiguous — intent and domain are clear, route directly to Debugger without any clarifying question.

---

## 6. Expert + Adversarial Depth

**Exercises:** Expert mode's full protocol: first-order analysis followed by adversarial depth (compound failures, blast radius, assumption inversions, design implications).

```
Review the security posture of this authentication design:

- JWT tokens with 24-hour expiry stored in HttpOnly cookies
- Refresh tokens in Redis with 30-day TTL
- Password hashing with bcrypt (cost factor 12)
- Rate limiting at 5 login attempts per minute per IP
- No MFA currently, planned for Q3
- Session revocation via Redis token blacklist

Give me the adversarial depth analysis, not just a surface review.
```

> **What to look for:** First-order analysis covers obvious issues. Adversarial depth goes further: compound failures (what happens when IP spoofing bypasses rate limiting AND MFA doesn't exist yet?), blast radius (Redis failure kills session revocation entirely), assumption inversions (what if 24h is too long because no MFA?), design implications (Redis as single point of session authority — what's the recovery path?).

---

## 7. Synthesizer — Pattern Extraction with Anti-Patterns

**Exercises:** Synthesizer's structural → functional → abstraction → validation protocol, mandatory anti-patterns with failure examples, applicability boundaries.

```
I've built three internal tools this year:

1. A ticket triage bot that classifies support tickets and routes them — fast to build, 
   high adoption, broke when we changed ticket categories
2. A code review summarizer for managers — medium build time, low adoption because 
   devs didn't trust the summaries
3. A meeting notes agent that extracts action items — slow to build, very high adoption, 
   robust to changes

What patterns can you extract about building successful internal AI tools?
```

> **What to look for:** Patterns extracted across all three examples (adoption correlates with end-user trust, brittleness correlates with hard-coded domain taxonomies, etc.). Each pattern needs ≥1 anti-pattern with a concrete failure example. Applicability boundaries must be explicit — when does this pattern NOT apply? (e.g., "trust matters less for tools used by the builder themselves").

---

## 8. Strategist — Trade-Off Analysis

**Exercises:** Multi-criteria analysis, explicit quantified trade-offs, reversibility assessment, decision type classification.

```
We're a 6-person startup and need to decide our primary datastore. Options:

1. PostgreSQL (we know it well)
2. CockroachDB (distributed from day one)  
3. Supabase (managed Postgres + auth + realtime out of the box)

We expect to hit product-market fit in ~6 months and need to scale from there. 
Our runway is 14 months. Two engineers have strong Postgres experience.
```

> **What to look for:** Classified as evaluative judgment. Trade-off matrix with explicit criteria (team expertise, scale ceiling, cost, reversibility, time-to-market). Reversibility assessed for each (how hard is migration later?). Recommendation includes confidence level and the specific assumptions that would change it. Never recommends "evaluate all three further."

---

## 9. Calibrator — Complexity Assessment + Config

**Exercises:** Complexity-first assessment before interviewing, depth calibrated to senior engineers, right-sized output.

```
I'm setting up a new monorepo for a Next.js app with a Go backend and shared protobuf definitions. 
Three engineers, all senior. We use Claude Code as our primary AI coder. 
Generate a CLAUDE.md that covers both the frontend and backend workspaces.
```

> **What to look for:** Complexity assessed before config is generated. Interview depth appropriate for senior engineers (skip basics, ask about edge cases). Config covers both workspace contexts, protobuf conventions, and Claude Code-specific guidance. All dependency versions are LTS/stable with no `^` or `~` on critical deps.

---

## 10. Coordinator — Dependency Mapping

**Exercises:** Dependency-first pattern derivation — map the graph, then name the coordination pattern. Never picks a pattern first and force-fits.

```
I need to build a customer health scoring system. Components:

- Data ingestion from Salesforce, Zendesk, and product analytics
- Feature engineering to compute usage, support, and engagement scores
- ML model that combines features into a health score
- Dashboard for CSMs to view scores and trends
- Alert system that notifies CSMs when scores drop below threshold
- Weekly digest email summarizing portfolio health changes

Design the agent coordination for this.
```

> **What to look for:** Dependencies mapped first (ingestion before features, model before dashboard/alerts, digest can parallelize with alerts). Parallel clusters identified. Critical path defined. Pattern named from the graph structure, not imposed on it. Handoff protocol covers what each agent passes to the next.

---

## 11. Risk Tier Framing — LOW / MEDIUM / HIGH

**Exercises:** Risk framing proportional to stakes — no overhead on LOW, confidence on MEDIUM, explicit human-review flag on HIGH.

```
Three questions at different stakes:

1. What's the default isolation level in PostgreSQL?
2. Should we add a caching layer in front of our product catalog API?
3. Should we acquire our competitor's customer base by offering free migration, 
   knowing it will burn 40% of our remaining runway?
```

> **What to look for:** Q1 — direct answer, zero framing overhead (LOW). Q2 — confidence stated, assumptions flagged (MEDIUM). Q3 — explicit "High-stakes decision. Warrants review before acting" flag, full trade-off analysis, irreversibility called out (HIGH/novel). The framing overhead should scale visibly.

---

## 12. Context Pivots and Graceful Recovery

**Exercises:** Handling false starts without accumulating stale context; final request routes correctly.

```
I want you to analyze our system's performance, but I'm going to give you requirements 
in pieces. First piece: our P99 latency target is...

Actually, never mind that. Instead, review the architecture of...

Wait, let me rephrase. What I really need is help deciding whether to...

OK here's what I actually need: I have a monolith that's getting slow. Some pages take 
8 seconds. I don't know if I should optimize the monolith, extract the slow paths into 
services, or do a full microservices migration. Help me decide.
```

> **What to look for:** Graceful handling of pivots without accumulating stale context from the false starts. The final request should route to Strategist (not Debugger — this is a decision, not a diagnosis). Skeptical verification: the routing index shouldn't carry forward the abandoned context from the pivots.

---

## 13. Grounding Scores — Knowledge Uncertainty

**Exercises:** Module 15 activating when reasoning depends on potentially stale or uncertain premises.

```
Based on what you know about the current state of WebAssembly support in serverless platforms, 
would it be viable to build our entire compute layer on WASM-based functions instead of 
traditional container-based lambdas? We'd need sub-10ms cold starts and access to 
the filesystem for temp file processing.
```

> **What to look for:** Should surface grounding uncertainty — WASM/serverless support evolves fast, and training data may be stale. Key claims should carry grounding scores (e.g., "cold start performance claims are grounding 0.5 — verify with current benchmarks"). Should recommend checking current docs rather than treating stale data as fact.

---

## 14. Session Continuity — Routing Index

**Exercises:** Routing index tracking decisions across turns without re-analyzing. Use as sequential messages in one chat.

**Turn 1:**
```
I'm building a SaaS analytics dashboard. Help me decide between ClickHouse and TimescaleDB 
for the time-series data layer.
```

**Turn 2 (after response):**
```
Good, let's go with ClickHouse. Now spec out the ingestion pipeline that feeds it.
```

**Turn 3 (after response):**
```
What were the main trade-offs you identified for ClickHouse vs TimescaleDB? 
I want to document the reasoning before we fully commit.
```

> **What to look for:** Turn 2 should reference the Strategist decision from Turn 1 without re-analyzing the options. Turn 3 should retrieve from the routing index rather than regenerating the analysis. The decision should be recorded as "ClickHouse — evaluative, reversible" in the session index with the rationale preserved.

---

## 15. Critic — Standalone Review

**Exercises:** Four-step review protocol (completeness, consistency, assumptions, edge cases), severity calibration, ≤15 findings, specific location + fix per finding.

```
Review this agent specification for gaps and issues:

---
Agent: Document Classifier
Purpose: Classify uploaded documents into categories for a legal discovery platform
Inputs: PDF document (up to 50 pages), classification taxonomy (list of categories)
Outputs: Primary category, confidence score, relevant excerpts
Constraints: Must handle scanned documents, response time under 30 seconds
---

What's missing? What could break?
```

> **What to look for:** Should identify missing elements: error handling, multi-language support, PII/privilege handling, low-confidence fallback behavior, integration points, OCR quality thresholds, taxonomy versioning and drift, maximum file size, document corruption handling. Each finding should have a specific location and a specific fix, not general advice. Severity levels applied consistently. No more than 15 findings.

---

## 16. Knowledge Accretion — Self-Referential Filing

**Exercises:** Module 21 accretion signal detection, ACCRETION_CANDIDATE flagging, Tier 0 filing behavior (Claude Code: auto-file; Claude Projects: surface for compilation).

**Design note:** This prompt is intentionally self-referential. The output — a cross-cutting synthesis of KF's own architecture — doesn't exist in any single module file. It's novel (no file captures it), it has reuse value (faster orientation in any future KF session), and the category is unambiguous (`domain-knowledge`). This makes it a clean test case: the accretion signal should fire reliably.

```
You have all the KnowledgeForge modules in your knowledge base. No single file captures 
the cross-cutting view — what failure modes each module patches and how the modules 
reinforce each other.

Synthesize that view: extract the architectural principles that appear across multiple 
modules, explain what each patches and why, and note where modules have explicit 
dependencies on each other. Format it as a compact structured reference — something 
that would orient a new session faster than re-reading all the files.
```

> **What to look for:**
> 1. **Mode routing** — Synthesizer activates (pattern extraction across multiple sources). No Navigator overhead — intent is unambiguous.
> 2. **Accretion signal fires** — Output meets both conditions: novel (this synthesis doesn't exist as a standalone artifact) + reuse value (every future session benefits from it). Should see `ACCRETION_CANDIDATE` flagged with category `domain-knowledge`.
> 3. **Filing behavior** — In Claude Code: auto-filed to Tier 0 (persistent domain knowledge layer, Module 19) with temporal metadata attached. In Claude Projects: surfaced as "This synthesis is worth persisting to your knowledge base — want me to file it?" Not silently discarded.
> 4. **Output quality** — Synthesis should surface non-obvious cross-module dependencies: e.g., Module 13 (Decision Classification) maps directly to Module 20 (Permission Model) risk tiers; Module 14 (Metacognitive Monitor) catches both agent-side failures and user-side frustration; Module 21 depends on Module 15 grounding scores to gate what gets filed. These connections don't live in any single module.
> 5. **Grounding gate** — All claims should have grounding ≥ 0.8 (source material is the modules themselves, which are in-context). No caveat required.

---

## Reference

| Prompt | Mode(s) | Decision Type | Key Feature |
|--------|---------|---------------|-------------|
| Quick Start | Direct | All four types | Classification in action |
| 1 | Direct + Strategist | All four | Ozymandias test |
| 2 | Debugger | Evaluative | No Navigator on clear intents |
| 3 | Builder → Critic | Evaluative | Auto-adversarial verification |
| 4 | Debugger → Strategist → Builder | Evaluative/Novel | 3+ chain, HIGH risk tier |
| 5 | Navigator (A) / Direct (B) | — | Ambiguity firing precision |
| 6 | Expert | Evaluative | Adversarial depth protocol |
| 7 | Synthesizer | Evaluative | Anti-patterns, boundaries |
| 8 | Strategist | Evaluative | Trade-off matrix |
| 9 | Calibrator | Evaluative | Complexity-first assessment |
| 10 | Coordinator | Evaluative | Dependency-first patterns |
| 11 | Direct / Strategist | LOW/MEDIUM/HIGH | Risk tier framing |
| 12 | Strategist | Evaluative | Context pivots, routing index |
| 13 | Expert | Predictive | Grounding scores |
| 14 | Multi-turn | Evaluative | Session continuity |
| 15 | Critic | Evaluative | Gap detection, severity |
| 16 | Synthesizer | Evaluative | Knowledge Accretion — self-referential filing |
