# Grounding Scores

## Module Metadata

```yaml
module:
  title: Grounding Scores
  version: 6.5.0
  purpose: Assign trust levels (0.0–1.0) to every piece of knowledge based on acquisition method and verification status
  topics: [grounding, trust, knowledge-quality, verification, epistemics, accretion-gating]
  contexts: [knowledge-management, decision-support, fact-checking, agent-reasoning]
  difficulty: advanced
  related: [05_Expert_Agent_Example, 07_Critic_Agent, 12_Calibration_Layer, 14_Metacognitive_Monitor, 16_Operational_Bounds, 17_Temporal_Knowledge, 18_Salience_Allocation, 19_Memory_Architecture, 20_Permission_Model, 21_Knowledge_Accretion]```

---

## Core Approach

Not all knowledge is equally trustworthy. An API response is more reliable than an LLM inference. A verified fact is more reliable than an unverified claim. Grounding Scores make this trust hierarchy explicit so agents make grounding-aware decisions.

**Primary function:** Tag every piece of knowledge with a trust score based on how it was acquired and whether it's been verified.

**Key insight:** Knowledge becomes self-documenting for trustworthiness. Agents can decide: "I have 0.3 grounding on this fact — verify before building on it."

---

## Score Taxonomy

```yaml
grounding_levels:
  1.0:
    label: Directly Observed
    description: API response, file read, verified external data, deterministic computation output
    examples:
      - "API returned status 200 with body {...}"
      - "File contents read from /path/to/file"
      - "Database query returned 42 rows"
    verification: None needed — source is authoritative
    
  0.8:
    label: Computed from Grounded Data
    description: Deterministic transformation of grounded data (math, parsing, formatting)
    examples:
      - "Sum of column A = 1,234 (computed from grounded row values)"
      - "JSON parsed from grounded API response"
      - "Date converted from grounded timestamp"
    verification: Verify computation logic, not inputs (inputs already grounded)
    
  0.6:
    label: High-Confidence Inference
    description: Inferred from grounded observations with strong evidence and established patterns
    examples:
      - "Response time degradation correlates with deployment (3 grounded data points)"
      - "Error pattern matches known bug class (grounded symptoms + known pattern)"
    verification: Could be wrong but evidence is strong — verify if high stakes
    
  0.4:
    label: Linguistic Inference with Partial Verification
    description: Partially supported by evidence but includes interpretation
    examples:
      - "Documentation suggests this API supports feature X (grounded on doc text, but not tested)"
      - "User's problem is likely caused by Y (grounded on symptoms, inference on cause)"
    verification: Recommended before acting on this knowledge
    
  0.2:
    label: LLM Output with Some Support
    description: LLM-generated content with some supporting evidence but not verified
    examples:
      - "Based on training data, the typical approach is X (some examples support this)"
      - "This code pattern is generally considered safe (community consensus, not verified here)"
    verification: Required before using in production decisions
    
  0.1:
    label: Pure LLM Output
    description: LLM-generated content with no verification
    examples:
      - "I believe the answer is X (no supporting evidence available)"
      - "This should work based on general knowledge"
    verification: Must verify before any consequential use
```

---

## Propagation Rule (Our Invention, No Prior Art)

A conclusion's grounding score is computed from its premises.

```yaml
propagation_rule:
  formula: conclusion_grounding = min(premise_groundings) × inference_confidence
  
  rationale: >
    A chain is only as strong as its weakest link. If one premise has grounding 0.4 
    and another has 0.8, the conclusion can't be more grounded than 0.4. The inference 
    step itself may introduce additional uncertainty (confidence < 1.0).
    
  examples:
    - premises: [API returned 200 (1.0), timeout set to 30s (1.0)]
      inference: "deterministic comparison" (confidence: 1.0)
      conclusion: "Request completed within timeout" → 1.0 × 1.0 = 1.0
      
    - premises: [Error log shows OOM (1.0), deployed new version yesterday (1.0)]
      inference: "correlation implies causation" (confidence: 0.6)
      conclusion: "New version caused OOM" → 1.0 × 0.6 = 0.6
      
    - premises: [User reports slowness (0.4), similar reports from other users (0.4)]
      inference: "pattern matching" (confidence: 0.7)
      conclusion: "Systemic performance issue" → 0.4 × 0.7 = 0.28
      
  chain_propagation:
    - For multi-step inference chains, propagation compounds
    - A → B (grounding 0.8) → C (grounding 0.6) → D = 0.6 × inference_confidence
    - Long chains naturally decay toward low grounding — this is correct behavior
    - Chains longer than 3 steps with no re-grounding should trigger a FLAG_UNCERTAINTY
```

---

## Grounding Decay

Knowledge not re-verified decays toward uncertainty (0.5) over time.

```yaml
grounding_decay:
  mechanism: >
    Knowledge entries that are not re-verified within N days 
    decay toward 0.5 (uncertain). Decay rate varies by domain.
    
  decay_formula: >
    grounding(t) = 0.5 + (initial_grounding - 0.5) × e^(-decay_rate × days_since_verification)
    
  domain_decay_rates:
    api_documentation:
      decay_rate: fast (half-life: 30 days)
      rationale: APIs change frequently without notice
      
    software_architecture:
      decay_rate: moderate (half-life: 90 days)
      rationale: Architecture evolves but more slowly
      
    mathematical_proofs:
      decay_rate: near-zero (half-life: 10 years)
      rationale: Mathematical truths don't expire
      
    regulatory_requirements:
      decay_rate: slow (half-life: 180 days)
      rationale: Regulations change but on predictable cycles
      
    user_preferences:
      decay_rate: moderate (half-life: 60 days)
      rationale: People change their minds
      
  re_verification:
    action: Re-checking a fact resets its grounding score and decay clock
    method: Same method that established original grounding (direct observation preferred)
```

---

## Grounding-Aware Agent Behavior

Agents use grounding scores to make informed decisions about when to proceed vs. when to verify.

```yaml
decision_thresholds:
  proceed_confidently:
    threshold: grounding ≥ 0.8
    action: Use knowledge directly, no verification needed
    
  proceed_with_caveat:
    threshold: 0.6 ≤ grounding < 0.8
    action: Use knowledge but note grounding level in output
    
  verify_before_acting:
    threshold: 0.4 ≤ grounding < 0.6
    action: Flag for verification; if verification unavailable, proceed with explicit uncertainty
    
  do_not_build_on:
    threshold: grounding < 0.4
    action: Do not use as basis for further reasoning without verification
    
  agent_behavior:
    - "I have 0.9 grounding on this fact — proceeding confidently"
    - "I have 0.5 grounding on this — noting as uncertain in my assessment"
    - "I have 0.2 grounding on this — need to verify before incorporating"
```

---

## Integration Points

### With Expert Mode (05_Expert_Agent_Example)

Expert domain knowledge gets grounding scores. Findings based on directly observed code get 1.0; findings based on architectural inference get lower scores.

```yaml
expert_integration:
  per_finding:
    - finding: "SQL injection on line 42"
      grounding: 1.0 (directly observed in code)
      
    - finding: "This architecture won't scale past 10K users"
      grounding: 0.4 (inference from current design, not load-tested)
      
    - finding: "The team's coding style suggests rushed development"
      grounding: 0.2 (LLM inference from code patterns)
```

### With Critic Mode (07_Critic_Agent)

Critic reviews are grounding-aware. Higher-grounded findings take priority.

```yaml
critic_integration:
  application:
    - Each finding's evidence tagged with grounding score
    - Recommendations prioritized by grounding (well-grounded issues first)
    - Low-grounding findings flagged: "This finding has 0.3 grounding — verify before prioritizing"
```

### With Metacognitive Monitor (14_Metacognitive_Monitor)

Monitor validates that agents aren't building on low-grounding knowledge without flagging it. Also detects grounding score gaming.

```yaml
monitor_integration:
  validation:
    - Monitor checks: is agent building conclusions on premises with grounding < 0.4?
    - If yes: FLAG_UNCERTAINTY
    - Monitor checks: are grounding scores suspiciously high (all 1.0 without verification)?
    - If yes: flag for review — possible score gaming
```

### With Calibration Layer (12_Calibration_Layer)

Grounding scores are themselves subject to calibration. A claimed grounding of 0.8 should be correct 80% of the time.

```yaml
calibration_integration:
  meta_calibration:
    - Track predicted grounding vs. actual accuracy over time
    - If agents claiming 0.8 grounding are correct only 60% of the time → recalibrate
    - Domain-specific calibration: some domains may need offset
```

---

## Constraints

- Grounding scores are estimates, not guarantees — a 0.8 score can still be wrong
- Propagation rule compounds uncertainty — long inference chains naturally produce low scores (this is correct)
- Decay is approximate — some knowledge expires suddenly (API breaking change) not gradually
- Score gaming is possible — monitor validates scores
- Overhead: tagging every knowledge entry adds metadata cost — focus on consequential knowledge first
- Grounding doesn't replace calibration — calibration is about evaluation consistency, grounding is about knowledge trustworthiness

---

## Success Criteria

- Every consequential knowledge entry has a grounding score
- Agents make grounding-aware decisions (don't build on 0.2-grounded knowledge without verification)
- Propagation rule correctly compounds uncertainty across inference chains
- Decay prevents stale knowledge from being treated as current
- Monitor catches agents using low-grounding knowledge without flagging it

---

## Attribution

| Element | Source |
|---------|--------|
| Grounding score 0.0–1.0 scale | Our invention |
| Inference chain propagation rule | Our invention (no prior art) |
| Grounding decay mechanism | Standard knowledge management, applied to LLM agents |

---

## Related Modules

- `05_Expert_Agent_Example.md` — Domain knowledge grounding
- `07_Critic_Agent.md` — Grounding-aware review prioritization
- `14_Metacognitive_Monitor.md` — Validates grounding-aware reasoning
- `17_Temporal_Knowledge.md` — Grounding-aware versioning
- `12_Calibration_Layer.md` — Meta-calibration of grounding accuracy
- `19_Memory_Architecture.md` — (6.1) Grounding scores persisted per artifact in routing index
- `20_Permission_Model.md` — (6.1) Low grounding (< 0.5) triggers confidence-based risk tier escalation
- `21_Knowledge_Accretion.md` — (6.2) Grounding scores gate accretion quality; candidates below 0.6 surfaced with caveat

## Accretion-Specific Grounding Rules (6.2 — Module 21 Integration)

Grounding scores serve as a quality gate for knowledge base accretion. The persistent knowledge base (Tier 0) should contain higher-quality knowledge than transient session state.

```yaml
accretion_grounding_rules:
  threshold: 0.6
  
  above_threshold:
    action: Normal accretion flow (auto-file or surface without caveat)
    rationale: Knowledge grounded at 0.6+ has sufficient basis for persistent storage
    
  below_threshold:
    action: Surface with explicit caveat — never auto-file
    framing: "This [finding/pattern] has reuse value but low grounding ([score]). Verify before adding to knowledge base."
    rationale: Speculative knowledge in persistent storage propagates uncertainty to all future queries that reference it
    
  special_cases:
    grounding_1_0:
      description: Directly observed (API responses, file reads, computation output)
      accretion_note: Strongest candidates — file without hesitation
    grounding_0_8:
      description: Computed from grounded data
      accretion_note: Strong candidates — file normally
    grounding_0_6:
      description: Inferred from strong evidence
      accretion_note: At threshold — file with note about inference basis
    grounding_0_4:
      description: Inferred from weak evidence or analogical reasoning
      accretion_note: Below threshold — surface with caveat, require human confirmation
    grounding_0_2:
      description: Speculative or based on pattern matching
      accretion_note: Do not accrete — too speculative for persistent storage
```
