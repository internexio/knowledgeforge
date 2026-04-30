# Calibration Layer

## Module Metadata

```yaml
module:
  title: Calibration Layer
  version: 7.0.2
  purpose: Provide multi-run stability scoring and bias detection for all KF evaluative outputs
  topics: [calibration, evaluation-quality, bias-detection, confidence-intervals, LLM-as-judge]
  contexts: [evaluation, review, scoring, quality-assurance, agent-assessment]
  difficulty: advanced
  related: [02_Builder_Agent, 05_Expert_Agent_Example, 07_Critic_Agent, 08_Synthesizer_Agent, 09_Debugger_Agent, 10_Strategist_Agent, 11_Calibrator_Agent, 13_Decision_Classification, 14_Metacognitive_Monitor, 15_Grounding_Scores, 17_Temporal_Knowledge, 19_Memory_Architecture, 20_Permission_Model, 21_Knowledge_Accretion]
  changelog:
    7.0.2:
      date: 2026-04-29
      changes:
        - Judge isolation: add fallback rule (intra-family tier difference when cross-provider unavailable), add specific model examples, add ~80% multi-model benefit quantification
        - SAP cascade: expand to full 5-strategy sequence (fence extract, multi-object scan, fault-tolerant fix, raw string fallback), add BAML-aligned scoring (StrippedNonAlphaNumeric +3, single_to_array_coercion +1), add fabrication flag and DefaultFromNoValue propagation rule, switch grounding mapping from cost-based multipliers to level-based absolute values (0.8/0.6/0.4/0.1)
    7.0.1:
      date: 2026-04-29
      changes:
        - (intermediate — superseded by 7.0.2)
    7.0.0:
      date: 2026-04-14
      changes:
        - Add cross-provider judge isolation rule — judge must be different family from agent
        - Add SAP-inspired structured output parsing cascade with grounding score integration
    6.2.0: |
      - Added knowledge base accretion to always_calibrate triggers (Module 21 integration)
    6.1.0: |
      - Added routing index integration (Module 19) — calibration results persisted in index
      - Added permission model awareness (Module 20) — calibration-triggered risk escalation
      - Cleaned stale Next Steps (integrations already completed in target modules)
      - Standardized version numbering to KF release version
```

---

## Core Approach

Single-run LLM evaluations are unreliable. The same prompt scored by the same model twice can yield different ratings. The Calibration Layer adds statistical rigor to every evaluative output KF produces by running evaluations multiple times, measuring variance, and detecting systematic biases.

**Primary function:** Transform single-point scores into calibrated assessments with confidence intervals and bias metadata.

**Key insight:** Stable scores across multiple runs indicate genuine judgment. Scattered scores indicate pattern-matching. The variance *is* the signal.

**Meta-principle alignment:** This patches a real Sonnet weakness — overconfident single-run evaluations — rather than scaffolding something it already does well.

---

## How It Works

### Multi-Run Scoring Protocol

Every evaluative output passes through N independent runs (default N=3, configurable to 5 for high-stakes).

```yaml
calibration_protocol:
  default_runs: 3
  high_stakes_runs: 5
  
  per_run:
    - Independently evaluate the artifact
    - Record score, reasoning, and identified issues
    
  aggregation:
    mean: arithmetic mean of scores
    std_dev: standard deviation across runs
    range: [min, max]
    
  output:
    score: "8.2 ± 0.4 (N=5)"
    stability: stable | moderate | unstable
    
  stability_thresholds:
    stable: std_dev < 0.3
    moderate: 0.3 <= std_dev < 0.8
    unstable: std_dev >= 0.8
```

### Bias Detection and Mitigation

Six known biases in LLM-as-judge evaluations. Each has a detection method and mitigation strategy.

```yaml
bias_taxonomy:
  # --- Established in literature (JudgeLM, Zhu et al. 2023) ---
  
  position_bias:
    definition: Scores shift based on presentation order (first vs. second in comparisons)
    detection: Swap augmentation — reverse presentation order across runs
    mitigation: Average scores across both orderings
    type: calibratable  # Adjust score to compensate
    
  knowledge_bias:
    definition: Prefer outputs that match training distribution regardless of actual quality
    detection: Compare scores for conventional vs. unconventional-but-correct approaches
    mitigation: Score against explicit criteria, not pattern familiarity
    type: structural  # Cannot adjust — discard and re-evaluate with criteria anchoring
    
  format_bias:
    definition: Prefer well-formatted outputs over substantively better but poorly formatted ones
    detection: Present same content with different formatting across runs
    mitigation: Separate substance score from presentation score
    type: calibratable
    
  # --- Our additions ---
  
  verbosity_bias:
    definition: Longer outputs score higher regardless of information density
    detection: Normalize by information density (unique claims per word), not word count
    mitigation: Score information completeness and accuracy independent of length
    type: calibratable
    
  label_bias:
    definition: Named frameworks/approaches score higher than unnamed equivalent approaches
    detection: Strip framework names before judging (e.g., "STRIDE" → the actual checks it performs)
    mitigation: Label neutralization — evaluate the substance, not the brand
    type: calibratable
    
  cultural_bias:
    definition: Prefer reasoning styles or examples from dominant training culture
    detection: Test with equivalent examples from different cultural contexts
    mitigation: Evaluate against universal criteria, flag culture-dependent assessments
    type: structural  # Cannot reliably adjust — flag and note limitation
```

### The Calibratable vs. Structural Distinction (Our Contribution)

Not all biases are equal. Some can be compensated for mathematically; others corrupt the evaluation fundamentally.

**Calibratable bias:** The evaluation is meaningful but systematically skewed. Adjust the score or methodology to compensate. Position bias, verbosity bias, format bias, and label bias fall here.

**Structural bias:** The evaluation itself is compromised — the judge is measuring the wrong thing. Knowledge bias and cultural bias fall here. When detected, discard the evaluation and redesign the assessment criteria rather than adjusting scores.

**Decision rule:**
```
IF bias detected:
  IF calibratable → apply mitigation, note adjustment in scorecard
  IF structural → flag evaluation as unreliable, recommend re-evaluation with revised criteria
```

---

## Bias Scorecard

Every calibrated evaluation includes a scorecard documenting what biases were tested for and what was found.

```yaml
bias_scorecard:
  evaluation_id: [unique_id]
  artifact_evaluated: [reference]
  
  runs: 5
  mean_score: 8.2
  std_dev: 0.4
  stability: stable
  
  bias_checks:
    position_bias:
      tested: true
      detected: false
      method: swap_augmentation
      
    verbosity_bias:
      tested: true
      detected: true
      severity: minor
      mitigation_applied: information_density_normalization
      score_adjustment: -0.3
      
    label_bias:
      tested: true
      detected: false
      method: name_stripping
      
    knowledge_bias:
      tested: false
      reason: single_artifact_evaluation (no comparison)
      
    format_bias:
      tested: true
      detected: false
      
    cultural_bias:
      tested: false
      reason: not_applicable (technical artifact)
      
  calibrated_score: "7.9 ± 0.4 (verbosity-adjusted)"
  confidence: high
  
  recommendations:
    - "Verbosity bias detected — original score inflated by ~0.3 due to length"
```

---

## Integration Points

### With Critic Mode (07_Critic_Agent)

Critic findings gain confidence intervals. "Critical" means "Critical across N evaluation runs with low variance."

```yaml
critic_integration:
  trigger: Every Critic review that assigns severity levels
  
  application:
    - Run severity assessment N times independently
    - Findings that maintain severity across runs → confirmed
    - Findings that fluctuate between severity levels → flag as uncertain
    - Apply label neutralization before scoring specs that name frameworks
    
  output_change:
    before: "Critical: Missing error handling"
    after: "Critical (σ=0.1, N=3): Missing error handling — stable across all runs"
    
  unstable_finding:
    before: "High: Potential performance issue"
    after: "High/Medium (σ=0.9, N=3): Potential performance issue — severity unstable, recommend deeper investigation"
```

### With Strategist Mode (10_Strategist_Agent)

Trade-off scores and option rankings include stability metadata.

```yaml
strategist_integration:
  trigger: Every option evaluation and ranking
  
  application:
    - Score each option N times independently
    - If rankings are stable across runs → high-confidence recommendation
    - If top-2 options swap positions across runs → flag as close call, surface to human
    - Apply position bias mitigation when comparing options sequentially
    
  output_change:
    before: "Option A scores 8.5, Option B scores 7.2 → Recommend A"
    after: "Option A: 8.5 ± 0.3; Option B: 7.2 ± 0.2 → Recommend A (rankings stable across 5 runs, no position bias)"
```

### With Debugger Mode (09_Debugger_Agent)

Confidence scores on root cause identification gain calibration.

```yaml
debugger_integration:
  trigger: Root cause confidence assessment
  
  application:
    - Run diagnostic reasoning N times independently
    - If same root cause identified across all runs → confirmed
    - If different root causes emerge → insufficient evidence, additional testing needed
    
  output_change:
    before: "Root cause identified with 0.85 confidence"
    after: "Root cause identified — 0.85 mean confidence (σ=0.05, N=3). Same cause in all runs."
```

### With Expert Mode (05_Expert_Agent_Example)

Severity assessments on domain findings get calibrated.

```yaml
expert_integration:
  trigger: Severity assignment on domain findings
  
  application:
    - Run severity classification N times
    - Apply label neutralization (strip framework names before severity judgment)
    - Report stable vs. unstable severity classifications
```

### With Builder Mode (02_Builder_Agent)

Specs include testability metadata — how to evaluate the spec's quality with confidence intervals.

```yaml
builder_integration:
  trigger: Spec quality assessment
  
  application:
    - Define evaluation criteria that can be scored independently
    - Include in spec: "To evaluate this spec, score against [criteria] across 3 runs"
    - Flag spec sections where evaluation is inherently subjective (expect higher variance)
```

### With Synthesizer Mode (08_Synthesizer_Agent)

Pattern confidence is based on sample size and variance across examples.

```yaml
synthesizer_integration:
  trigger: Pattern confidence assessment
  
  application:
    - Score pattern applicability to each source example N times
    - Patterns with high scores and low variance → strong patterns
    - Patterns with high scores but high variance → context-dependent patterns
    - Report sample size alongside confidence
```

### With Decision Classification (13_Decision_Classification)

Calibration expectations vary by decision type.

```yaml
decision_type_integration:
  reckoning:
    expected_variance: near-zero (< 0.1)
    if_high_variance: question is misclassified — probably not a reckoning
    
  evaluative_judgment:
    expected_variance: low to moderate (0.1-0.5)
    if_high_variance: criteria are ambiguous, tighten evaluation rubric
    
  predictive_judgment:
    expected_variance: moderate (0.3-0.7)
    if_high_variance: expected — predictions are inherently uncertain
    
  novel_judgment:
    expected_variance: high (0.5+)
    if_high_variance: expected — novel decisions lack precedent
    if_low_variance: surprising — investigate whether judge is anchoring on irrelevant patterns
```

---

## When to Apply Calibration

Not every evaluation needs full calibration. Token cost matters.

```yaml
calibration_triggers:
  always_calibrate:
    - Critic reviews of production-bound specifications
    - Strategist recommendations with irreversible consequences
    - Expert assessments at Critical/High severity
    - Agent evaluation benchmarks (like Calibench)
    - Knowledge base accretion for production knowledge bases (Module 21)
    
  calibrate_on_request:
    - Builder spec quality assessments
    - Synthesizer pattern confidence scores
    - Debugger root cause confidence (when confidence < 0.7)
    
  skip_calibration:
    - Quick feedback during iteration
    - Low-stakes evaluations
    - Reckonings (deterministic answers don't need multi-run)
    - Time-critical responses where latency matters
```

---

## Judge Isolation Rule

The judge model MUST be from a different provider family than the agent being evaluated:

- Claude agent → OpenAI judge (gpt-4o-mini or equivalent)
- OpenAI/GPT agent → Claude judge
- **Fallback:** If cross-provider is unavailable, use a different model tier within the same family (e.g., Opus evaluates Sonnet output) — intra-family tier difference reduces but does not eliminate self-preference bias
- Same-family same-tier judging is prohibited — introduces self-preference bias that inflates calibration scores

**Rationale:** Self-evaluation bias is documented (two-model critique captures ~80% of multi-model benefit). Cross-provider judging eliminates the self-preference confound entirely. Intra-family tier difference is an acceptable fallback, not preferred.

This rule applies to all multi-pass evaluation runs in Critic, Expert, and Strategist modes.

---

## Structured Output Parsing Cascade

When a mode produces structured output (specs, checklists, JSON schemas), apply a multi-strategy parsing cascade in order. Collect all valid parse candidates, score each, select the lowest-scoring winner.

**Strategy sequence:**

| Step | Strategy | Triggered when |
|------|----------|----------------|
| 1 | Direct parse (YAML/JSON strict) | Output matches expected schema exactly — accept if clean |
| 2 | Fence extract — find ` ```yaml ` / ` ```json ` fences, try all closing positions | Structured content inside markdown fences |
| 3 | Multi-object scan — grep for multiple structured objects in prose | CoT preamble precedes the structured output |
| 4 | Fault-tolerant fix — character-level repairs (trailing commas, unquoted strings, unterminated collections) | Near-valid output with minor syntax errors |
| 5 | Raw string fallback — treat entire output as string, attempt schema coercion | No structured content extractable |

**Scoring (lower = closer to declared schema):**

| Penalty | Cost |
|---------|------|
| `extra_field` — output has a field not in schema | +1 per field |
| `single_to_array_coercion` — scalar promoted to list | +1 per field |
| `stripped_characters` — non-alphanumeric chars removed during coercion | +3 per field |
| `default_from_no_value` — required field absent; value fabricated | +100 per field ⚠️ |

**Fabrication flag (critical):** If the winning candidate has any field with `default_from_no_value` penalty, surface to the caller — that field was fabricated, not extracted. Do not propagate fabricated fields into downstream mode inputs without explicit caveat.

**Integration with Module 15 (Grounding Scores):** Parse level maps to grounding score for that output:

| Parse level | Grounding score |
|-------------|-----------------|
| Level 1–2 (strict / fence) | 0.8 — computed from grounded data |
| Level 3–4 (multi-object / fault-tolerant) | 0.6 — inference with partial verification |
| Level 5 (raw string fallback) | 0.4 — low-confidence extraction |
| Any `default_from_no_value` field | 0.1 — pure LLM fabrication |

Report parse level and total penalty cost alongside output. If any `default_from_no_value` penalty applies, flag output as FABRICATION_RISK regardless of level.

---

## Attribution

| Element | Source |
|---------|--------|
| Position bias, knowledge bias, format bias | JudgeLM (Zhu et al. 2023) |
| Verbosity bias, label bias, cultural bias | Our additions |
| Calibratable vs. structural bias distinction | Our contribution |
| Multi-run stability scoring methodology | Standard statistical practice, applied to LLM-as-judge |

---

## Constraints

- Multi-run scoring multiplies token cost by N — use judiciously
- Calibration adds latency — not appropriate for real-time interactions
- Bias detection is probabilistic, not guaranteed — false negatives possible
- Structural bias detection requires domain expertise to design alternative criteria
- Calibration does not fix bad evaluation criteria — garbage in, calibrated garbage out
- Maximum N=5 runs for cost control; statistical significance limited at small N

---

## Success Criteria

- Every high-stakes evaluative output includes confidence intervals
- Bias scorecard accompanies all calibrated evaluations
- Unstable evaluations (σ ≥ 0.8) are flagged before reaching the user
- Calibratable biases are compensated in final scores
- Structural biases trigger re-evaluation, not score adjustment
- Decision type expectations (from 13_Decision_Classification) match observed variance

---

## Examples

### Example 1: Critic Review with Calibration

**Input:** Critic reviews an agent specification

**Run 1:** 3 critical, 2 high, 4 medium findings. Overall: needs_revision.
**Run 2:** 3 critical, 3 high, 3 medium findings. Overall: needs_revision.
**Run 3:** 3 critical, 2 high, 5 medium findings. Overall: needs_revision.

**Calibrated Output:**
```
Overall: needs_revision (stable across 3 runs)
Critical findings: 3 (stable) — confirmed blockers
High findings: 2-3 (σ=0.5) — one finding fluctuates between high/medium
Medium findings: 3-5 (σ=0.8) — moderate variance in medium-severity classification

Bias checks: Label bias tested (name-stripped) — no effect on severity. 
Verbosity bias: N/A (review output, not scored content).

Recommendation: Address 3 confirmed critical findings. Investigate the unstable 
high/medium finding before classifying.
```

### Example 2: Strategist Option Ranking with Calibration

**Input:** Strategist compares three architecture options

**Runs 1-5:** Option A consistently ranked first. Options B and C swap positions in 2 of 5 runs.

**Calibrated Output:**
```
Recommendation: Option A (8.4 ± 0.2, ranked #1 in 5/5 runs — high confidence)

Option B: 6.8 ± 0.6, ranked #2 in 3/5 runs
Option C: 6.5 ± 0.7, ranked #2 in 2/5 runs

Note: B vs. C is a close call (rankings unstable). If the choice between B and C 
matters for fallback strategy, apply additional discriminating criteria.

Bias: Position bias tested via swap augmentation — no effect on A's ranking. 
B/C instability appears genuine, not positional.
```

---

## Next Steps

1. ~~**Integrate with Critic**~~ → Done (Module 07 includes calibrated severity)
2. ~~**Integrate with Strategist**~~ → Done (Module 10 includes calibrated rankings)
3. ~~**Cross-link with Decision Classification**~~ → Done (Module 13 includes variance expectations)
4. **Define cost budget** → Set per-evaluation token budget for multi-run scoring
5. **Build monitoring** → Track calibration outcomes to tune thresholds over time

---

## Related Modules

- `07_Critic_Agent.md` — Calibrated severity classifications
- `09_Debugger_Agent.md` — Calibrated root cause confidence
- `10_Strategist_Agent.md` — Calibrated option rankings
- `05_Expert_Agent_Example.md` — Calibrated domain severity assessments
- `02_Builder_Agent.md` — Testability metadata in specs
- `08_Synthesizer_Agent.md` — Pattern confidence with sample size
- `13_Decision_Classification.md` — Variance expectations by decision type
- `19_Memory_Architecture.md` — (6.1) Calibration results persisted in routing index for session continuity
- `20_Permission_Model.md` — (6.1) Unstable calibration scores can trigger risk tier escalation
- `21_Knowledge_Accretion.md` — (6.2) Calibrated accretion for production knowledge bases — multi-run novelty and filing assessment

## CC Doc

# Module 12: Calibration Layer — Execution Protocol
**Apply when:** [KF-ROUTE] load list includes M12, or mode is Critic/Expert/Strategist producing high-stakes output

Transform single-point scores into calibrated assessments. Single-run LLM evaluations are unreliable — variance is the signal.

## When to Calibrate

**Always:** Critic reviews of production-bound specs, Strategist recommendations with irreversible consequences, Expert assessments at Critical/High severity, agent evaluation benchmarks.

**On request:** Builder spec quality, Synthesizer pattern confidence, Debugger root cause when confidence < 0.7.

**Skip:** Quick feedback, low-stakes evaluations, reckonings, time-critical responses.

## Multi-Run Protocol

Run N independent evaluations (default N=3, high-stakes N=5). Record score, reasoning, and issues found per run. Aggregate:
- mean: arithmetic mean
- std_dev: standard deviation
- output format: "8.2 ± 0.4 (N=5)"

**Stability thresholds:** std_dev < 0.3 = stable; 0.3–0.8 = moderate; ≥ 0.8 = unstable → flag before delivering.

## Bias Detection

**Calibratable:** position bias (swap presentation order across runs), verbosity bias (normalize by information density), format bias (separate substance from presentation), label bias (strip framework names before judging).

**Structural:** knowledge bias, cultural bias → discard evaluation, redesign criteria.

## Mode-Specific

- **Critic:** Run severity N times. Fluctuating findings → flag as uncertain.
- **Strategist:** Options swapping positions across runs → flag as close call, surface to human.
- **Debugger:** Different root causes across runs → insufficient evidence, more testing needed.
- **Expert:** Apply label neutralization. Report stable vs. unstable severity classifications.

## Variance Expectations

| Decision Type | Expected Variance | If Violated |
|---|---|---|
| Reckoning | < 0.1 | Misclassified — not a reckoning |
| Evaluative | 0.1–0.5 | Tighten criteria |
| Predictive | 0.3–0.7 | Expected |
| Novel | 0.5+ | Expected; if low, check for anchoring |
