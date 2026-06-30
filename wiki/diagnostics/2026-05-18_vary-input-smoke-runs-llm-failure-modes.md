---
title: Vary input across smoke runs — different audiences expose different LLM-prompt failure modes
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.75
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-18
tags: diagnostics, llm, empirical, smoke-testing
related_entries: [diagnostics/2026-05-18_http-status-signatures-deploy-verification-smoke-test.md, methodologies/2026-05-15_two-call-anthropic-cache-prefix-verification.md, diagnostics/2026-05-13_fabricated-default-fallback-at-call-site.md]
domain: diagnostics
topic: testing
---

# Vary input across smoke runs — different audiences expose different LLM-prompt failure modes

## The Pattern

When smoke-testing LLM-driven endpoints, varying the INPUT across runs exposes more prompt failure modes than varying the prompt across runs. Run a 2–3 case smoke matrix with deliberately-different sender contexts and audience descriptions. Failures that hide on one input often surface on another.

## Why input-variation works better than prompt-variation

LLM prompt failures cluster around how the model interprets ambiguity in the input. A prompt rule like "don't fabricate proof points" is enforced more strictly when the context provides clear proof points (model has something to anchor to) and more loosely when the context is sparse (model fills the gap with plausible-sounding invention). The same prompt produces different failure modes against different inputs.

**Therefore:** changing inputs explores the prompt's behavior space more efficiently than changing the prompt and re-running against the same input.

## Practical heuristic — 3-case smoke matrix

For any new LLM endpoint, run at least:

- **Case A — Rich context:** Full sender_context with verifiable proof points (numbers, customer names, etc.). Tests: does the model use the real proof correctly?
- **Case B — Thin context:** Minimal sender_context. Tests: does the model fabricate when given little to anchor to?
- **Case C — Edge audience:** Different domain, different role, different signals than Case A. Tests: does the prompt generalize, or did it overfit to one shape?

Failures in B and C are the high-signal ones — they reveal what the prompt does when context is sparse or different.

## Concrete Grounding from COS Session

Smoke test 1 against `POST /analyze/optimize-email` (test env, COS backend):
- Input: VP Engineering at SaaS, rich context with "40% CI cost reduction" in sender_context
- Result: Clean. Generic value language. No fabricated specifics.
- Time: 5.5s
- **Initial conclusion based on this single smoke: "fake-claims fix works, ship it."**

Smoke test 2 against the same endpoint (same code, same prompt):
- Input: Bootstrapped founder of 5-person consultancy, sender_context = "fractional CRO agency that helps boutique consultancies build a repeatable outbound motion" (NO numbers, NO proof points)
- Result: Model fabricated a soft-hedged stat — "Teams we've worked with typically see their first qualified conversations within 3-4 weeks of implementation"
- The "3-4 weeks" claim was nowhere in sender_context
- Hedge ("typically") softened the violation but the number was still invented
- **Conclusion: the prompt's fabrication-ban was NOT closed; smoke 1 just happened to have rich enough context that the model didn't need to invent.**

Without the input-variation in smoke 2, this loophole would have shipped to production silently. The same prompt, the same code path, the same endpoint — but the sparse input revealed a failure mode that the rich input masked.

## When This Applies

- New LLM endpoints before production deploy
- Prompt hardening cycles (each hardening pass should be re-smoked across the matrix)
- LLM-as-judge or LLM-as-extractor where output shape or truthfulness matters
- Any feature where the prompt's behavior depends on input shape (sparse vs. rich, familiar vs. unfamiliar domain)

## When This Does NOT Apply

- Pure-determinism endpoints (no LLM in the path)
- Endpoints with strict structured-output validation (Pydantic / JSON Schema catches most failures pre-response)
- Throwaway / prototype work where the audience won't vary
- High-signal smoke passes that test transport layer (HTTP status codes, latency) — structure tests and semantic tests are complementary, not alternatives

## Failure modes to watch

- **Don't infinitely-expand the matrix.** 3 deliberately-different cases beats 10 random ones. Diminishing returns set in fast.
- **Don't use input-variation as a substitute for unit tests against parsed output shape.** Tests catch structural issues; smokes catch semantic-quality issues. Both are needed.
- **Some failures only emerge in production traffic distribution.** Smokes can't replace gradual rollout for high-stakes endpoints. Use this pattern during development and staging; assume unknown failure modes exist at production scale.
- **Context sparsity isn't the only axis.** Input domain (B2B vs. consumer), tone (formal vs. casual), or jargon (technical vs. plain language) can also expose failures. Pick the axes that matter for your prompt.

## Cross-references

- [diagnostics/2026-05-18_http-status-signatures-deploy-verification-smoke-test.md] — transport-layer signatures during smoke testing (complementary pattern)
- [methodologies/2026-05-15_two-call-anthropic-cache-prefix-verification.md] — verification strategy for cached prompts (similar verification mindset: probe the real behavior, not just the preconditions)
- [diagnostics/2026-05-13_fabricated-default-fallback-at-call-site.md] — call-site fallbacks that mask upstream issues (related failure class: lack of signal when things go wrong)

## Source Context

Discovered during post-deploy smoke testing in session `cos-mcp-clarify-integration-phase2-3-prod-push` (2026-05-18). New `optimize-email` endpoint added a "don't fabricate proof points" prompt rule. Smoke test 1 (rich context, VP audience) passed cleanly. Smoke test 2 (sparse context, founder audience) revealed the prompt rule was incomplete — soft-hedged fabrications still slipped through. The two-case grounding confirms: identical code + identical prompt produces different failure modes against different input shapes. Single-smoke confidence is misleading; input-variation is necessary to probe the full behavior space. Confidence: 0.75 (high fidelity on the specific endpoint and the two-case pattern; 0.25 reserved for generalization across wildly different prompt types and domains).
