---
title: KF Governance Over Async Transport — AgentRadio Open Problems Mapped to KF Modules
source_mode: builder
novelty_type: transferable_framework
grounding_score: 0.82
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-08-09
source_fingerprint: knowledgeforge-core-e49 / AgentRadio arXiv 2026 (Coral AI Labs) — mid-chain premise invalidation bead; six open problems identified in AgentRadio §5 Discussion
domain: orchestration
topic: agent-coordination
tags: premise-invalidation, mid-chain-re-entry, async-transport, agent-communication, multi-agent
related_entries:
  - wiki/orchestration/2026-06-14_compile-pipeline-pr-supersedence-snapshot-merge-pattern.md
  - wiki/patterns/mode-variants-taxonomy.md
---

# KF Governance Over Async Transport — AgentRadio Open Problems Mapped to KF Modules

## Context

AgentRadio (Coral AI Labs, arXiv 2026) studied multi-agent task execution where intermediate results are broadcast asynchronously between agents. A key failure mode observed: the MinIO team converged on an incorrect final answer with high confidence because a mid-execution discovery (premise-invalidating evidence found by a downstream agent) was never propagated back to the upstream agent that had made the now-invalidated claim.

AgentRadio §5 identifies six open governance problems that any framework supporting mid-chain communication must address. This entry maps each to the KF module(s) that provide or constrain the answer, along with the specific mechanism.

---

## Open Problem Mapping

| AgentRadio Open Problem | KF Module | Mechanism |
|------------------------|-----------|-----------|
| **Interruption-worthiness** — When is a mid-chain discovery worth halting execution vs. logging and continuing? | M07 (Critic), M00 (Orchestrator) | Severity threshold (Sev1 = log only; Sev2/Sev3 = halt and re-enter). The adversarial Critic's severity system provides the decision signal. M00's re-entry rule is a deterministic predicate over `upstream_invalidation.severity` — no LLM judgment at the gate. |
| **Recipient selection** — Which upstream step should receive the invalidation signal? | M04 (Handoff Contract), M19 (Memory Architecture) | `upstream_invalidation.invalidated_step_id` is an explicit field in the response_schema — the signaling step names the specific chain step whose premise was invalidated. M19's `routing_decision_log` carries the full chain topology as the ground truth for resolving the named ID. |
| **Evidence sufficiency** — How much evidence is required to justify an interrupt? | M15 (Grounding Scores), M04 (Handoff Contract validation) | ui-check-3 (cross-field) requires `evidence_ref` to be non-null and resolvable for Sev2+ signals. M15 grounding score methodology applies to the evidence_ref target. Sev1 signals may carry evidence without the resolvability requirement. |
| **Cost limits** — How do you bound the cost of re-execution triggered by an interrupt? | M16 (Operational Bounds), M18 (Salience Allocation) | M16 token-cost-per-mode metric (#9) bounds individual re-entry steps. The 3-failure circuit breaker (M00) caps cumulative re-entry attempts at 3 per step — but note re-entry from `upstream_invalidation` is exempt from the failure counter (correction, not failure). M18 salience allocation governs attention across competing tasks when re-entry competes with live work. |
| **Permissions** — Who is authorized to issue upstream invalidation signals? | M20 (Permission Model) | `capabilities_when_subagent.write` restricts what a step can signal back. Only target_mode steps within the declared chain (not external or ad-hoc agents) can populate `upstream_invalidation`. Risk tier escalation (M20) applies: a Sev2+ signal from a sub-chain step escalates the chain's risk tier before re-entry. |
| **Provenance** — How is the chain of evidence documented for the invalidating claim? | M00 (Orchestrator), M19 (routing_decision_log) | `upstream_invalidation.evidence_ref` is a resolvable pointer (NOT prose) — provenance traces to a specific artifact, not a natural-language claim. Every re-entry activation writes a `routing_decision_log` entry with `re_route_reason = "upstream_invalidation: invalidated_step_id=<id> evidence_ref=<ref>"`. Re-routed entries archive permanently per M19 retention policy. |

---

## KF Implementation Status (as of v7.23.0)

The mid-chain premise invalidation feature (bead `knowledgeforge-core-e49`) ships in v7.23.0 and addresses interruption-worthiness, recipient selection, and evidence sufficiency fully. Cost limits and permissions are addressed via existing module machinery (M16, M18, M20) without new additions. Provenance is covered by the routing_decision_log extension (M19 7.4.0 trigger `downstream_step_premise_invalidation`).

**AgentRadio problems NOT yet fully closed by KF v7.23.0:**
- Cost limits: No per-re-entry budget cap beyond the 3-failure circuit breaker. A single high-cost re-entry step has no token ceiling below the global context limit.
- Permissions: `capabilities_when_subagent` restricts write access structurally but does not yet include a per-contract `invalidation_authorized` flag — any target_mode in a chain that has response_schema can signal upstream_invalidation.

These remain as known gaps for future KF versions.

---

## Decision Type

Evaluative judgment — mapping against known AgentRadio open problems with clear grounding in both the paper (published findings) and KF module specs (verified against current module versions).

---

## Transferability

This mapping pattern — "take an external framework's open-problem taxonomy and map each problem to the governance module that answers it" — is reusable for other incoming research (e.g., future agent-communication papers). The six-problem taxonomy (interruption-worthiness, recipient selection, evidence sufficiency, cost limits, permissions, provenance) is a useful checklist for evaluating any mid-chain signaling system.
