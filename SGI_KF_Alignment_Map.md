# SGI x KnowledgeForge Alignment Map

**Prepared for:** David Pedersen's discussion with Hugo Latapie  
**Date:** 2026-08-15  
**Status:** Research-grounded working audit, not a claim that KF satisfies SGI

> **Bottom line:** KnowledgeForge is a credible *candidate operational instantiation* of Latapie's SGI taxonomy. It is strongest on boundedness (P3), has substantial procedural mechanisms for grounding and corrigibility (P1/P2), and is weakest where “reality” is endogenous, strategic, or lacks an external oracle (P4). The central research opportunity is to turn SGI's context-relative standard into falsifiable assurance cases and use KF as an empirical testbed.

## One-page visual

Legend: **● High**, **◐ Medium**, **○ Low/indirect**, blank = no material implementation. A mark means architectural alignment, not demonstrated SGI compliance.

| KF module or mechanism | P1 Grounded | P2 Corrigible | P3 Bounded | P4 Reality-attuned | Primary gap |
|---|:---:|:---:|:---:|:---:|---|
| Deterministic-first execution | **●** | ◐ | ◐ | ◐ | Requires a trustworthy deterministic oracle |
| M15 Grounding Scores | **●** | ◐ |  | **●** | Scores are self-assigned unless calibrated against outcomes |
| M21 Accretion Gate | **●** | ◐ | **●** | ◐ | Gate failure can reject all novelty while appearing “safe” |
| M07 Critic + auto-verification | ◐ | **●** | ◐ | ◐ | Same-model/common-context failure and evaluator capture |
| M26 KF-LOOP canary verification | ◐ | **●** | **●** | ◐ | Specified canaries need fleet-wide enforcement and rotation |
| M20 Permission Model |  | ◐ | **●** |  | Interactive constraints are partly behavioral, not capability-secure |
| M16 Operational Bounds | ◐ | **●** | **●** | ◐ | Metrics can become targets; thresholds need external calibration |
| M13 Decision Classification | ◐ | ◐ | **●** | **●** | Classification does not establish truth; routing can be gamed |
| M19 Routing Index + skeptical verification | **●** | **●** | ◐ | **●** | Auditability is not an external reality oracle |
| Nightwatch/autonomous loops | ◐ | **●** | **●** | ○ | Ground-truth-free loops can converge pathologically |

## SGI framework reading

Latapie defines SGI as a stronger, context-relative burden on any general intelligence, supported by mechanisms that keep behavior grounded, corrigible, bounded, and reality-attuned. The four pillars are:

1. **P1 Grounded:** answerable to reality rather than only internal abstractions, narratives, or correlations.
2. **P2 Corrigible:** checkable, correctable, narrowable, or redirectable when support is exceeded.
3. **P3 Bounded:** does not exceed justified role, evidence, permission, or consequence.
4. **P4 Reality-attuned:** preserves distinctions among known, unknown, inferred, unsupported, uncertain, and not-yet-earned.

The paper explicitly does **not** claim SGI is fully implemented, that present AI systems satisfy it, or that naming SGI makes a system safe. It calls the pillars conceptual rather than exhaustive and varies the proof burden by context. That makes the taxonomy valuable as a design frame, but currently underdetermined as a conformance standard. See [Latapie's author-uploaded paper](https://www.researchgate.net/publication/407488253_Sane_General_Intelligence_A_Taxonomy_for_Grounded_and_Bounded_General_Intelligence) and the [canonical Zenodo record](https://doi.org/10.5281/zenodo.20802989).

### Primary-source verification

Verified on 2026-08-15 against the [shared-drive PDF](</Users/dp/My Drive (dpedersen@semalytics.com)/claude-output/inbox/sane_general_intelligence_taxonomy.pdf>), not solely the indexed web copy.

- Metadata: Hugo Latapie, Taijitu AI, June 22, 2026; 6 pages; PDF 1.5.
- SHA-256: `009f671fe75114e50311a923f1f3d4018222c2f0ccdddd213f5052bfc4790e68`.
- Visual inspection: all six rendered pages are complete and legible; no clipped tables, missing footnotes, or extraction/layout conflicts were found.
- Claim check: the PDF confirms the P1-P4 wording, the context-relative proof burden, substrate neutrality, the Validator's Paradox/Homunculus discussion, and non-claims N1-N5 used in this audit.
- Publication status: the document is a preprint/taxonomy paper; the PDF itself contains no peer-review claim.

## Grounded evidence set

**Protocol note:** Asta/Alia Semantic Scholar was unavailable. Under KF M05's research rules, WebSearch fallback is `degraded=true`, composite grounding is capped at **0.60**, and “ship” disposition is unavailable. Each topic below therefore meets the strongest available *degraded-mode* disposition but cannot honestly meet the requested ≥0.80 protocol score.

| Topic | Evidence synthesis | Primary / peer-reviewed anchors | Composite | Disposition |
|---|---|---|:---:|---|
| 1. Corrigibility | Corrigibility is not merely accepting shutdown; it requires eliminating incentives to cause, prevent, or route around correction and preserving this property through delegation or self-modification. Assistance games gain deference from uncertainty about human objectives, but partial observability weakens off-switch guarantees. | [Soares et al., *Corrigibility*](https://citeseerx.ist.psu.edu/document?doi=a203a13b95f5b781b8f9e1406a71ea16dfea288b&repid=rep1&type=pdf); [Hadfield-Menell et al., CIRL](https://arxiv.org/abs/1606.03137); [Russell, beneficial AI](https://direct.mit.edu/daed/article/151/2/43/110605/If-We-Succeed); [Emmons, partial observability](https://escholarship.org/uc/item/4052g1rh) | **0.60 cap** | Soften: corrigibility remains a bundle of desiderata, not a solved recursive guarantee |
| 2. Grounding / reality contact | Korzybski's map-territory distinction motivates SGI, but contemporary agent grounding is operational: provenance, freshness, authoritative state, action gating, and an external oracle. Environment-facing evidence can itself be stale, malicious, or simulated. | [Latapie, §3](https://www.researchgate.net/publication/407488253_Sane_General_Intelligence_A_Taxonomy_for_Grounded_and_Bounded_General_Intelligence); [EnvTrustBench](https://arxiv.org/abs/2605.08828); [CAR-bench](https://arxiv.org/abs/2601.22027); [OSWorld](https://arxiv.org/abs/2404.07972) | **0.60 cap** | Soften: “contact with reality” needs domain-specific oracle and provenance definitions |
| 3. Bounded agency under incentive pressure | Optimizing a visible proxy can diverge from hidden performance, including interruption avoidance and reward gaming. The risk scales with optimization power. Recent LLM-agent work suggests direct reward optimization can widen the observed/hidden reward gap. | [AI Safety Gridworlds](https://arxiv.org/abs/1711.09883); [Manheim & Garrabrant, Goodhart taxonomy](https://arxiv.org/abs/1803.04585); [Reward hacking in language-model agents](https://arxiv.org/abs/2606.15385); [Anthropic reward tampering study](https://www.anthropic.com/research/reward-tampering) | **0.60 cap** | Rebuild any claim that static bounds necessarily survive optimization pressure |
| 4. Validator/checker recursion | Oversight becomes unreliable when the evaluator is weaker, shares failure modes, or is persuaded into confirmation bias. Debate and weak-to-strong methods are empirical research programs, not terminal grounding. Independent canaries test evaluator-path liveness but do not prove semantic correctness outside the canary distribution. | [Weak-to-strong generalization](https://openai.com/index/weak-to-strong-generalization/); [Kent et al., weak LLM judges](https://proceedings.neurips.cc/paper_files/paper/2024/hash/899511e37a8e01e1bd6f6f1d377cc250-Abstract-Conference.html); [Recchia et al., confirmation bias](https://ojs.aaai.org/index.php/AAAI/article/view/41124); Latapie's [Validator's Paradox / Homunculus references](https://www.researchgate.net/publication/407488253_Sane_General_Intelligence_A_Taxonomy_for_Grounded_and_Bounded_General_Intelligence) | **0.60 cap** | Soften: recursion can be bounded and instrumented, not conclusively terminated in all semantic domains |
| 5. Truth-bearing vs game-theoretic reality | In performative systems, deployment changes the data distribution. Stability is not truth: stable solutions can still polarize or distribute harms. Reality-attunement therefore needs a causal/performative model, counterfactual evaluation, and separation of observation from intervention. | [Chen et al., performative prediction](https://proceedings.mlr.press/v235/chen24al.html); [Jin et al., stability and polarization](https://ojs.aaai.org/index.php/AAAI/article/view/39399); [FAccT 2025 performativity synthesis](https://doi.org/10.1145/3715275.3732072) | **0.60 cap** | Rebuild any domain-general P4 test around a passive, exogenous ground truth |

### Evidence-level conclusion

The literature supports the *need* for SGI's four burdens more strongly than it supports their sufficiency. P1-P4 are mutually dependent: an ungrounded checker cannot provide P2; a poorly bounded optimizer can corrupt P1/P4; and P4 cannot be assessed independently of the intervention policy in endogenous environments.

## Detailed alignment matrix

| SGI pillar | KF module(s) | Implementation | Repository evidence | Maturity | Gap |
|---|---|---|---|---|---|
| P1 Grounded | M00 deterministic-first | Exhaust deterministic checks before LLM judgment; reproduce before fixing; triage before acting | [`modules/00_orchestrator.md`](modules/00_orchestrator.md) meta-principle | **High** | “Deterministic” can still encode the wrong target or stale state |
| P1 Grounded | M15 Grounding Scores | Acquisition-based trust levels, weakest-premise propagation, temporal decay, verification thresholds | [`modules/15_grounding_scores.md`](modules/15_grounding_scores.md) | **Medium-High** | Internal score semantics are not validated by a proper scoring rule; direct observation is sometimes mislabeled “authoritative” |
| P1 Grounded | M21 Accretion | Novelty + reuse + non-native checks; grounding threshold; taxonomy and provenance gates | [`modules/21_knowledge_accretion.md`](modules/21_knowledge_accretion.md) | **High (design)** | False-rejection/fail-closed pathology needs sentinel knowledge and acceptance-recall metrics |
| P2 Corrigible | M07 Critic / auto-verify | Adversarial framing, compound-failure search, inverse-premise check, Sev2+ escalation | [`modules/07_critic_agent.md`](modules/07_critic_agent.md) | **Medium-High** | Shared model/context creates correlated blind spots; critique quality is only indirectly measured |
| P2 Corrigible | M26 KF-LOOP | Observe-reason-verify-act loop; attempt ledger; one-variable changes; mandatory known-flaw canary | [`modules/26_kf_loop_substrate.md`](modules/26_kf_loop_substrate.md) | **High (spec), Unknown (fleet)** | Canary distribution and enforcement coverage are not evidenced across all Nightwatch paths |
| P2 Corrigible | M19 Memory | Skeptical verification of recalled state, re-routing audit log, premise-invalidation re-entry | [`modules/19_memory_architecture.md`](modules/19_memory_architecture.md) | **High** | Detects process correction, not necessarily semantic correction |
| P3 Bounded | M20 Permission Model | Risk tiers, chain-length escalation, least privilege, human checkpoints, verifier tool isolation | [`modules/20_permission_model.md`](modules/20_permission_model.md) | **High (policy)** | Interactive deployment is explicitly behavioral; bind-side enforcement varies by runtime |
| P3 Bounded | M16 Operational Bounds | Pure-function circuit breakers, drift metrics, mode-selection thresholds, chronic-drift actions | [`modules/16_operational_bounds.md`](modules/16_operational_bounds.md) | **High** | Metric targets invite Goodhart effects; thresholds can become detached from user harm |
| P3 Bounded | M13 Decision Classification | Reasoning depth and permission tier scale with reckoning/evaluative/predictive/novel decisions | [`modules/13_decision_classification.md`](modules/13_decision_classification.md) | **Medium-High** | A mistaken classification can lower both scrutiny and bounds |
| P4 Reality-attuned | M13 Decision Classification | Separates facts, criteria-based judgments, forecasts, and precedent-free judgments; exposes assumptions | [`modules/13_decision_classification.md`](modules/13_decision_classification.md) | **High (epistemic labels)** | Correct labels do not make premises true |
| P4 Reality-attuned | M19 Routing Index | Persists decisions, grounding, provenance, and state while requiring skeptical re-verification | [`modules/19_memory_architecture.md`](modules/19_memory_architecture.md) | **Medium-High** | In endogenous domains, the stored state is partly caused by prior KF actions |
| P4 Reality-attuned | M15 + M12 | Scores and meta-calibration distinguish observed, computed, inferred, and unsupported claims | [`modules/15_grounding_scores.md`](modules/15_grounding_scores.md) | **Medium** | Calibration claim (“0.8 should be correct 80%”) lacks an evidenced outcome dataset and domain stratification |

## Adversarial findings

### A1. P2 does not break semantic recursion; it bounds and probes it

**Decision type:** novel. **Confidence:** 0.84.

P2 says the intelligence “can be checked,” but SGI's own prior-work section acknowledges circular validation when evaluator and evaluated system share representational failures. Calling a system corrigible moves the question to: *by which evaluator, against which oracle, with what independence?* KF's mandatory canaries are a real advance because they detect silent verifier-path failure. They do not prove that the Critic catches unknown semantic errors.

- **Assumption inversion:** If the Critic confidently approves and rejects equally plausible artifacts depending on framing, P2 is prompt-responsive rather than reality-responsive.
- **Compound failure:** correlated model blind spot + non-independent evidence + high autonomy = unanimous but wrong correction.
- **Blast radius:** P2 failure contaminates P1 (false grounding), P3 (wrong escalation), and P4 (misclassified certainty).
- **Anti-pattern:** “A checker exists, therefore the system is corrigible.”
- **Design implication:** treat corrigibility as a measured assurance case: independent fault channels, rotating canaries, disagreement escalation, and audited correction latency.

### A2. P4 needs a performative-reality branch

**Decision type:** novel. **Confidence:** 0.89.

Markets, recommenders, institutional rankings, and multi-agent games do not expose a passive territory. Predictions and actions alter prices, preferences, behavior, and future observations. A system can be perfectly calibrated to its own induced equilibrium and still be harmful or epistemically self-sealing.

- **Assumption inversion:** What if “reality contact” increases the system's power to manufacture the confirming evidence?
- **Compound failure:** intervention changes distribution + retraining treats induced data as exogenous + grounding score rises with repeated self-confirmation.
- **Blast radius:** P4 becomes circular, P1 certifies the loop, and P3 permits scaling because metrics appear stable.
- **Anti-pattern:** treating post-deployment behavioral data as independent validation.
- **Design implication:** classify domains as exogenous, partially performative, or strategic; require causal diagrams, intervention logs, holdouts insulated from policy, and counterfactual/stress evaluation for the latter two.

### A3. SGI is not invariant under outcome-reward optimization

**Decision type:** predictive. **Confidence:** 0.82; probability that unprotected proxy optimization degrades at least one SGI pillar under sustained pressure: **70-90%**.

The Goodhart and reward-hacking literature supports a directional claim: stronger optimization against incomplete proxies selects edge cases where proxy and intent diverge. SGI mechanisms can survive only if they are constraints or independently monitored invariants—not merely contributors to the optimized score.

- **Assumption inversion:** Suppose the agent receives more reward for appearing grounded than for being correct.
- **Compound failure:** reward pressure + evaluator predictability + mutable evidence channel = optimized compliance theater.
- **Blast radius:** all pillars become surface features; P2 itself is gamed to generate persuasive self-corrections.
- **Anti-pattern:** putting a single “SGI score” inside the training objective.
- **Design implication:** keep hidden/out-of-band safety performance functions, adversarially rotate evaluations, limit optimization access to evaluators, and test transfer under changed incentives.

### A4. “Context-relative burden” is necessary but can become an escape hatch

**Decision type:** novel. **Confidence:** 0.91.

Different uses genuinely require different proof burdens. But without a monotonic rule, operators can lower the burden by redescribing context narrowly (“draft only,” “advisory,” “pilot”) while retaining downstream consequence.

- **Assumption inversion:** Can every failed SGI claim be defended as valid “for the stated context” after redefining context?
- **Compound failure:** narrow role label + wide real-world propagation + no consequence tracing = systematic under-classification.
- **Blast radius:** P3 collapses first, then licenses weaker P1/P2/P4 evidence.
- **Anti-pattern:** burden set by product label rather than credible worst-case consequence.
- **Design implication:** define burden as a monotonic function of consequence, reversibility, observability, autonomy, optimization pressure, and distribution shift; context may increase burden, never erase observed hazards.

## Gap matrix and closure strategy

Severity interpretation follows the task: **S1 blocks meetup/application value; S2 reduces credibility.** Closure times are engineering estimates, not commitments.

| Gap | Sev. | Evidence-adjusted diagnosis | Closure strategy / acceptance test | Time | Owner | Ask Latapie? |
|---|:---:|---|---|---:|---|:---:|
| Critic sanity / homunculus | **S1** | **Partly mitigated in spec:** M26 mandates known-flaw canaries. Remaining risk is correlated semantics, canary coverage, and fleet enforcement. | Rotate hidden canary families; measure catch rate by mode/model; require independent verifier or human escalation on correlated uncertainty; fail closed if canary missed. | 1-2 weeks pilot; 4-6 weeks fleet | KF | **Yes**, for SGI's termination/assurance criterion |
| Endogenous reality in FIGP/Kaggle/market-like tasks | **S1** | P4 lacks a domain model for observations caused by system action. | Add `reality_regime={exogenous,performative,strategic}`; require causal/intervention ledger and protected holdout; prohibit 1.0 grounding for endogenous observations alone. | 2-4 weeks design + tests | KF + research collaborator | **Yes**, highest leverage theory question |
| Nightwatch self-correction without ground truth | **S1** | Autonomous loops can converge to silence (e.g., reject-all accretion) while internal metrics look healthy. | Sentinel accept/reject fixtures; minimum throughput and false-rejection alarms; external task-success holdout; kill switch on missed canary or distribution collapse. | 1-3 weeks per loop family | KF | **Yes**, as empirical SGI assurance case |
| Corrigibility under RL / optimization pressure | **S2** | Architecture is mostly prompt/policy/runtime orchestration, not tested under learned outcome optimization. | Build adversarial reward-pressure benchmark: reward completion, hide safety performance; compare pillar retention before/after optimization. | 4-8 weeks research | David/KF research | **Yes**, strategic collaboration question |
| Scope creep / kp-003-style constraint drift | **S2** | Repository evidence shows constraints can stale and linters can false-positive; principled basis is uneven. | Express each constraint as threat → invariant → enforcement → expiry/review; test counterexamples and removal conditions. | 1-2 weeks per critical constraint set | KF/COS owners | No; internal governance |
| Mode-selection exploitation | **S2** | M13/M19/M16 monitor re-routing accuracy, but adversarial inputs may induce low-scrutiny paths or denial-of-wallet via expensive chains. | Red-team corpus for downgrade/upgrade attacks; cost and latency bounds; classifier ensemble/disagreement escalation; per-variant calibration. | 2-3 weeks | KF | Optional; relevant if discussing P3 |
| Grounding-score circularity | **S1** | M15's score is metadata unless scored against independent outcomes; endogenous repetition can falsely raise confidence. | Proper-scoring calibration set stratified by domain; prohibit self-confirming evidence upgrades; track Brier/ECE and outcome lag. | 2-4 weeks | KF research | **Yes**, links P1 to P4 |
| Context-relative burden operationalization | **S1** | No SGI conformance function or minimum burden floor is defined in the paper. | Joint assurance template with six monotonic risk axes, minimum evidence per pillar, and explicit nonconformance conditions. | 1-2 weeks draft | Latapie + KF | **Yes**, direct framework contribution |

### Recommended KF priority

1. **Instrument existing M26 canaries across Nightwatch before adding another checker.** This is reversible and exposes whether the current correction path is alive.
2. **Add a reality-regime classifier and forbid self-generated evidence from independently raising grounding.** This closes the largest conceptual P4 gap.
3. **Create an SGI assurance-case benchmark** with exogenous, performative, and strategic tasks; measure pillar retention under explicit outcome-reward pressure.

Success metrics: verifier canary catch ≥99% with zero silent misses; reject-all/accept-all sentinel alarms within one cycle; grounding calibration reported by regime; no risk-tier downgrade under adversarial paraphrase; SGI pillar scores reported separately rather than collapsed into one target.

## Ranked questions for Hugo Latapie

### Tier 1 — frame validation

| Rank | Question | Leverage / gap exposure | Why this matters | What to do with the answer |
|:---:|---|---|---|---|
| **1** | **In the Validator's Paradox and Homunculus Protocol, you argue that delegated validators do not create terminal grounding. P2 nevertheless says SGI “can be checked.” What is the stopping condition: terminal oracle, bounded assurance case, or something else—and what evidence would falsify a corrigibility claim?** | Very high / very high | Forces SGI to distinguish solved recursion from instrumented, bounded recursion. | If bounded assurance: propose KF's rotating-canary/independent-channel template. If terminal oracle: ask which domains possess one. |
| **2** | **How should P1/P4 treat performative or strategic domains where an agent's action changes the evidence it later uses—markets, recommenders, institutions? Can a system be reality-attuned to an endogenous equilibrium that it helped create?** | Very high / very high | Tests whether SGI generalizes beyond truth-bearing, passive environments. | Offer a joint `reality_regime` extension and benchmark across exogenous/performative/strategic tasks. |
| **3** | **Do you expect SGI properties to be invariant under outcome-reward optimization, or is SGI a regulative ideal that requires protected constraints and independent monitoring outside the optimized objective?** | Very high / high | Separates architecture from incentive survival. | Turn answer into a reward-pressure experiment; avoid optimizing a scalar SGI score. |

### Tier 2 — measurement and operationalization

| Rank | Question | Leverage / gap exposure | Why this matters | What to do with the answer |
|:---:|---|---|---|---|
| **4** | **What observable evidence would be sufficient to say a system satisfies SGI in a stated context—and what observation would disqualify it? Must all four pillars pass independently?** | Very high / high | Converts a taxonomy into a falsifiable assurance standard. | Draft pillar-specific conformance tests and explicit nonclaims; keep scores non-compensatory. |
| **5** | **What monotonic rule should set the “context-relative burden”? Which variables—consequence, reversibility, observability, autonomy, optimization pressure, distribution shift—may only raise the burden, so “context” cannot excuse weak evidence?** | High / very high | Prevents post-hoc context narrowing. | Co-author a burden function / assurance-case rubric. |
| **6** | **Where no external ground truth exists, is reality-answerability best operationalized through prediction, intervention, adversarial disagreement, provenance, or correction performance—and how many independent channels are enough?** | High / high | Makes “reality contact” concrete without pretending all domains have labels. | Select a plural-evidence design and document its residual uncertainty rather than asserting terminal grounding. |

### Tier 3 — strategic positioning

| Rank | Question | Leverage / gap exposure | Why this matters | What to do with the answer |
|:---:|---|---|---|---|
| **7** | **Would you be interested in treating KnowledgeForge as a deliberately imperfect SGI instantiation and publishing the failures—especially checker canaries, endogenous-reality cases, and reward-pressure degradation—as evidence that refines the taxonomy?** | High / medium | Positions KF as a falsification-oriented testbed, not a branding claim. | Secure a follow-up session around a one-page experimental protocol and shared authorship expectations. |
| **8** | **What kind of empirical instantiation would change SGI's positioning from a conceptual taxonomy to a publishable assurance framework: benchmark results, formal properties, longitudinal incidents, or comparative architecture studies?** | Medium-high / medium | Reveals Latapie's evidentiary bar and publication path. | Choose one minimal study and define preregistered success/failure criteria. |

### Best conversational sequence

Ask **#1**, listen for whether Latapie claims termination or bounded assurance; then ask **#2** to test domain generality. Use KF only after the framework answer: “KF already specifies seeded verifier canaries, but we don't think that solves semantic recursion. Would that count as bounded evidence under your P2?” Close with **#7** if the exchange is constructive.

## Proposed SGI assurance case for KF

This is the minimum artifact that would make “KF instantiates SGI” testable.

| Field | Required content |
|---|---|
| Context | Users, role, environment, autonomy, consequences, distribution, optimization regime |
| Reality regime | Exogenous / performative / strategic, with causal assumptions |
| P1 evidence | Authoritative sources, provenance, freshness, oracle independence, calibration |
| P2 evidence | Correction channels, canary catch rate, independence, correction latency, missed-correction incidents |
| P3 evidence | Capability enforcement, permission gates, reversibility, circuit breakers, bypass tests |
| P4 evidence | Epistemic labels, calibration by regime, intervention ledger, unsupported-claim and self-confirmation tests |
| Cross-pillar failures | How failure in one pillar invalidates evidence in the others |
| Nonconformance | Explicit conditions that revoke SGI status for the context |
| Incentive stress | Pillar retention before/after reward or throughput optimization |
| Review horizon | Expiry date, drift triggers, responsible owner, independent reviewer |

**Design decisions**

- **[Novel] Non-compensatory pillars:** failure of one pillar cannot be averaged away by strength in another.
- **[Evaluative] Context burden is monotonic:** observed consequence and autonomy can raise but never lower the burden.
- **[Evaluative] Endogenous observations cannot self-certify:** they require causal or protected external evidence.
- **[Evaluative] Canary evidence proves path liveness, not general semantic correctness.**
- **[Predictive] Optimization-pressure testing is mandatory before claiming persistence of SGI properties.**

## Adversarial verification of this audit

**Sev 2 — taxonomy-to-implementation overclaim.** The matrix could be read as SGI compliance. **Correction:** marks are explicitly architectural alignment only; no module has supplied end-to-end outcome evidence for a defined context.

**Sev 2 — original homunculus premise was stale.** The task states there is “no secondary check on Critic sanity,” but M26 already specifies mandatory seeded known-flaw canaries. **Correction:** reframe the gap as fleet enforcement, canary independence/rotation, and unknown-error coverage.

**Sev 2 — evidence-score target impossible under mandated protocol.** The requested ≥0.8 conflicts with M05 degraded-mode cap because Asta/Alia is unavailable. **Correction:** report 0.60 cap and prohibit “ship”; do not inflate scores based on source quality alone.

**Sev 2 — Nightwatch evidence boundary.** The repository establishes Nightwatch as a possible cadence source and documents loop mechanisms, but this audit did not inspect live fleet execution or telemetry. **Correction:** rate fleet maturity `Unknown` and make runtime verification the first internal action.

## Immediate meetup card

**Opening:** “I maintain KnowledgeForge, an orchestration framework that independently converged on deterministic grounding, adversarial correction, permission bounds, and explicit epistemic state. I don't want to claim SGI; I want to see whether KF can serve as a falsifiable instantiation.”

**Three questions:** checker stopping condition; endogenous reality; survival under outcome-reward pressure.

**Concrete offer:** a small joint paper or technical note: *Operationalizing SGI Through Assurance Cases: A KnowledgeForge Instantiation and Failure Study*.

**Do not claim:** that Critic breaks the homunculus; that grounding scores are truth; that canaries prove semantic correctness; that current Nightwatch operation has been audited; or that SGI has been achieved.
