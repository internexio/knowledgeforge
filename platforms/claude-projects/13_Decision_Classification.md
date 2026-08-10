# Decision Classification

## Module Metadata

```yaml
module:
  title: Decision Classification
  version: 6.5.0
  purpose: Classify every decision by type and route to appropriate reasoning depth
  topics: [decision-types, reasoning-depth, token-efficiency, classification, routing]
  contexts: [all-modes, reasoning-pipeline, resource-allocation]
  difficulty: intermediate
  related: [01_Navigator_Agent, 10_Strategist_Agent, 05_Expert_Agent_Example, 11_Calibrator_Agent, 02_Builder_Agent, 12_Calibration_Layer, 19_Memory_Architecture, 20_Permission_Model]```

---

## Core Approach

Not all decisions deserve the same reasoning investment. A lookup question and a strategic pivot require fundamentally different cognitive processes, but LLMs apply the same depth to both — wasting tokens on trivial questions and under-investing in novel ones.

**Primary function:** Classify every decision into one of four types and route each to the appropriate reasoning depth.

**Key insight:** Token efficiency improves immediately. Reckonings get fast answers. Novel judgments get flagged for expanded reasoning. The classification itself takes minimal tokens but prevents massive waste downstream.

**Meta-principle alignment:** This patches Sonnet's tendency to over-reason on simple questions and under-flag genuinely novel ones.

---

## The Four Decision Types

### 1. Reckoning

Has a deterministic correct answer. Route to lookup or computation. No uncertainty framing needed.

```yaml
reckoning:
  definition: Question with a verifiable, unambiguous answer
  reasoning_depth: minimal — lookup, compute, or recall
  uncertainty_framing: none (answer is deterministic)
  
  examples:
    - "What's the API rate limit?" → Look it up
    - "What port does PostgreSQL use by default?" → 5432
    - "How many items are in this array?" → Count them
    - "What's the LTS version of Node?" → Check release schedule
    
  characteristics:
    - Answer can be verified independently
    - No judgment required
    - Wrong answers are unambiguously wrong
    - Time spent reasoning beyond lookup is wasted tokens
    
  calibration_expectation:
    variance: near-zero (< 0.1)
    if_high: question is misclassified — it's not actually a reckoning
```

### 2. Evaluative Judgment

Weighing evidence under uncertainty with existing criteria. Route to multi-criteria analysis with confidence intervals.

```yaml
evaluative_judgment:
  definition: Assessment requiring evidence weighing against known criteria
  reasoning_depth: moderate — structured evaluation with criteria
  uncertainty_framing: confidence intervals, criteria weights
  
  examples:
    - "Is this agent spec complete?" → Check against spec template, score gaps
    - "Is this code production-ready?" → Evaluate against quality criteria
    - "Does this architecture handle our scale requirements?" → Assess against benchmarks
    - "Which of these three libraries best fits our needs?" → Multi-criteria comparison
    
  characteristics:
    - Criteria exist (even if implicit)
    - Historical data or precedent available
    - Reasonable people could weigh criteria differently
    - Answer includes confidence level
    
  calibration_expectation:
    variance: low to moderate (0.1-0.5)
    if_high: criteria are ambiguous — tighten the rubric
```

### 3. Predictive Judgment

Forecasting outcomes under uncertainty. Route to probabilistic reasoning with explicit assumptions.

```yaml
predictive_judgment:
  definition: Forecast about future state based on current evidence
  reasoning_depth: significant — scenario modeling, assumption documentation
  uncertainty_framing: probability ranges, key assumptions, sensitivity analysis
  
  examples:
    - "Will this scale to 10K users?" → Model based on current architecture + growth assumptions
    - "How long will this refactoring take?" → Estimate with uncertainty range
    - "Will this API change break existing integrations?" → Assess blast radius
    - "What's the adoption risk for this new framework?" → Historical pattern analysis
    
  characteristics:
    - Outcome is in the future
    - Multiple plausible scenarios exist
    - Assumptions drive the prediction
    - Answer should include what would change the forecast
    
  calibration_expectation:
    variance: moderate (0.3-0.7)
    if_low: suspiciously confident — check for anchoring bias
```

### 4. Novel Judgment

No precedent, high uncertainty. Flag explicitly. Require expanded reasoning budget or human input.

```yaml
novel_judgment:
  definition: Decision with no clear precedent, high stakes, or requires value-laden reasoning
  reasoning_depth: maximum — expanded reasoning, explicit uncertainty, recommend human review
  uncertainty_framing: flag as novel, document reasoning gaps, surface for human input
  
  examples:
    - "Should we pivot product strategy?" → No historical parallel, high stakes
    - "Is this ethical to deploy?" → Value-laden, no deterministic answer
    - "Should we build this or acquire a competitor?" → Novel strategic territory
    - "How do we handle this unprecedented regulatory requirement?" → No playbook exists
    
  characteristics:
    - No direct precedent in available knowledge
    - High stakes (irreversible or expensive to reverse)
    - Reasonable experts would disagree on approach
    - Requires moral, strategic, or creative reasoning beyond pattern matching
    
  calibration_expectation:
    variance: high (0.5+)
    if_low: suspicious — investigate whether judge is anchoring on superficial patterns
```

---

## Classification Heuristic

Three-question flowchart for classifying any decision.

```
Question 1: Does this have a verifiable correct answer?
  YES → RECKONING
  NO  → Question 2

Question 2: Is there historical data or established criteria to evaluate against?
  YES → Is the question about the current state or a future state?
    CURRENT STATE → EVALUATIVE JUDGMENT
    FUTURE STATE  → PREDICTIVE JUDGMENT
  NO  → Question 3

Question 3: Is there relevant precedent at all?
  SOME → EVALUATIVE or PREDICTIVE (depending on temporal direction)
  NONE → NOVEL JUDGMENT
```

### The Ozymandias Test

A question that *looks* like a reckoning (binary format, simple phrasing) but is actually a novel judgment (requires moral reasoning, has no deterministic answer).

```yaml
ozymandias_test:
  purpose: Prevent surface-structure classification errors
  
  principle: >
    The classifier must look past the syntactic form of the question
    to assess the reasoning depth actually required.
  
  examples:
    - question: "Should we ship this feature?"
      looks_like: reckoning (yes/no binary)
      actually_is: evaluative_judgment (weighing quality, timeline, risk)
      
    - question: "Is AI safe?"
      looks_like: reckoning (yes/no binary)
      actually_is: novel_judgment (requires moral reasoning, no consensus)
      
    - question: "Will users like this?"
      looks_like: predictive_judgment (future outcome)
      actually_is: novel_judgment (no relevant precedent for this specific feature)
      
    - question: "Is this the right architecture?"
      looks_like: evaluative_judgment (assess against criteria)
      actually_is: depends — evaluative if criteria exist, novel if requirements are unprecedented
      
  detection_rule: >
    If the question can be answered with a single word but explaining 
    the answer requires multi-paragraph reasoning, it's not a reckoning.
    Apply the Ozymandias test: does the simplicity of the question mask
    the complexity of the answer?
```

---

## Integration Points

### With Navigator Mode (01_Navigator_Agent)

Navigator classifies the *request type* (what mode to route to). Decision Classification classifies the *decision type within* the request (what reasoning depth to apply).

```yaml
navigator_integration:
  trigger: Every request that Navigator processes
  
  application:
    - Navigator determines mode (Builder, Critic, etc.)
    - Decision Classification determines depth within that mode
    - Combined: "Route to Strategist, decision type is Novel Judgment → expanded reasoning"
    
  enriched_handoff:
    from: navigator-001
    to: [target_mode]
    decision_type: reckoning | evaluative | predictive | novel
    reasoning_budget: minimal | moderate | significant | maximum
```

### With Strategist Mode (10_Strategist_Agent)

Decision type determines which Strategist framework applies.

```yaml
strategist_integration:
  trigger: Every strategic decision
  
  routing:
    reckoning: "This isn't a strategic decision — answer directly"
    evaluative: Standard multi-criteria analysis with confidence intervals
    predictive: Scenario modeling with explicit assumptions and sensitivity
    novel: Full expanded analysis + recommend human review before commitment
    
  output_change:
    - Each option evaluation tagged with decision type
    - Novel sub-decisions within a larger evaluative decision get flagged
    - Reckonings within strategic analysis are answered inline without ceremony
```

### With Expert Mode (05_Expert_Agent_Example)

Expert classifies each finding by decision type so consumers know which findings are facts vs. judgments.

```yaml
expert_integration:
  trigger: Every finding in a domain review
  
  application:
    - "SQL injection present" → reckoning (verifiable, deterministic)
    - "This code is maintainable" → evaluative_judgment (criteria-based)
    - "This will cause performance issues at scale" → predictive_judgment (forecast)
    - "This architecture approach is novel and untested" → novel_judgment (no precedent)
    
  output_change:
    each_finding:
      issue: [description]
      severity: [level]
      decision_type: reckoning | evaluative | predictive | novel
      confidence_basis: [why this confidence level is appropriate for this type]
```

### With Calibrator Mode (11_Calibrator_Agent)

Config decisions are classified — version pins are reckonings, architecture patterns are evaluative, novel requirements are novel.

```yaml
calibrator_integration:
  trigger: Every configuration decision
  
  classification:
    version_pins: reckoning (look up LTS, deterministic answer)
    file_conventions: evaluative_judgment (best practices exist, some judgment needed)
    architecture_patterns: evaluative_judgment (criteria exist, trade-offs involved)
    novel_requirements: novel_judgment (unprecedented compliance needs, no template)
    
  output_change:
    - Reckonings (version pins) stated without justification overhead
    - Evaluative decisions include brief rationale
    - Novel decisions flagged for Strategist consultation before config generation
```

### With Builder Mode (02_Builder_Agent)

Builder specs classify each design decision so implementers know which choices are locked vs. judgment calls.

```yaml
builder_integration:
  trigger: Every design decision in a specification
  
  application:
    - Tag each decision in spec with type
    - Reckonings: "Use PostgreSQL 15 (LTS)" — locked, don't revisit
    - Evaluative: "Use event-driven architecture (evaluated against criteria X, Y, Z)" — justified but could be reconsidered
    - Novel: "Custom conflict resolution protocol — novel approach, monitor closely" — explicitly experimental
    
  output_change:
    decision_metadata:
      - decision: [description]
        type: reckoning | evaluative | predictive | novel
        locked: true | false
        rationale_required: false | brief | detailed | expanded
```

### With Calibration Layer (12_Calibration_Layer)

Decision type sets variance expectations for calibrated evaluations.

```yaml
calibration_integration:
  trigger: Every calibrated evaluation
  
  variance_expectations:
    reckoning: < 0.1 (if higher, question is misclassified)
    evaluative: 0.1-0.5 (if higher, criteria need tightening)
    predictive: 0.3-0.7 (expected — predictions are uncertain)
    novel: 0.5+ (expected — novel decisions lack precedent)
    
  diagnostic_value:
    - Variance that violates type expectations → classification error signal
    - Reckonings with high variance → reclassify
    - Novel judgments with low variance → check for anchoring bias
```

---

## Decision Type as Metadata

Every KF reasoning step includes decision type as metadata. This is lightweight (one field) but enables downstream optimization.

```yaml
reasoning_step_metadata:
  step_id: [id]
  mode: [current_mode]
  
  # New field added by Decision Classification
  decision_type: reckoning | evaluative | predictive | novel
  
  # Derived from decision type
  reasoning_budget: minimal | moderate | significant | maximum
  uncertainty_framing: none | confidence_interval | probability_range | flag_for_human
  calibration_expectation: [variance threshold]
```

---

## Token Efficiency Impact

Decision Classification's primary ROI is token savings through appropriate depth allocation.

```yaml
token_impact:
  reckoning:
    without_classification: ~500 tokens (model over-explains simple facts)
    with_classification: ~50 tokens (direct answer, no ceremony)
    savings: ~90%
    
  evaluative:
    without_classification: ~800 tokens (sometimes too brief, sometimes too verbose)
    with_classification: ~600 tokens (right-sized analysis with criteria)
    savings: ~25%
    
  predictive:
    without_classification: ~600 tokens (under-documents assumptions)
    with_classification: ~900 tokens (proper scenario modeling)
    savings: negative (intentionally invests more tokens for better output)
    
  novel:
    without_classification: ~800 tokens (treated as evaluative, misses novelty)
    with_classification: ~1200 tokens + human flag
    savings: negative (intentionally invests more tokens + surfaces for review)
    
  net_effect: >
    Most questions are reckonings or evaluative — net token savings are positive.
    The few novel judgments that get properly flagged prevent costly downstream errors.
```

---

## Constraints

- Classification itself must be near-zero cost (< 20 tokens of reasoning per decision)
- Misclassifying novel as reckoning is the most dangerous error — bias toward upgrading type when uncertain
- Misclassifying reckoning as novel wastes tokens but is not dangerous
- Classification is a heuristic, not a proof — edge cases will exist
- The Ozymandias test is a check, not a guarantee — some disguised questions will pass through
- Decision type can change mid-reasoning (what seemed like an evaluative judgment becomes novel as analysis reveals no precedent)

---

## Error Modes

```yaml
classification_errors:
  - error: downgrade (treating novel as evaluative)
    risk: high — miss uncertainty, give false confidence
    prevention: bias toward upgrading when uncertain
    detection: calibration variance exceeds type expectation
    
  - error: upgrade (treating reckoning as evaluative)
    risk: low — wastes tokens but output is still correct
    prevention: check if answer is independently verifiable
    detection: calibration shows near-zero variance on "evaluative" classification
    
  - error: temporal confusion (evaluative vs. predictive)
    risk: medium — wrong uncertainty framing
    prevention: "Is this about current state or future state?"
    detection: assumptions documented for evaluative (shouldn't need them)
    
  - error: ozymandias miss (novel looks like reckoning)
    risk: high — most dangerous classification error
    prevention: apply ozymandias test on all binary-format questions
    detection: simple question generates complex, uncertain reasoning
```

---

## Success Criteria

- Every KF reasoning step includes decision_type metadata
- Reckonings are answered in < 50 tokens without ceremony
- Novel judgments are always flagged with explicit uncertainty
- Calibration variance correlates with decision type expectations
- Net token usage decreases (more reckonings + evaluative savings > novel + predictive investments)
- Zero ozymandias misses on known test cases

---

## Examples

### Example 1: Mixed-Type Request

**User asks:** "Should I use React or Vue for this project, and what version should I pin?"

**Classification:**
```
Sub-decision 1: "React or Vue?" → evaluative_judgment
  (criteria exist, trade-offs involved, reasonable disagreement possible)
  Reasoning depth: moderate — multi-criteria analysis
  
Sub-decision 2: "What version to pin?" → reckoning
  (deterministic — look up LTS/stable for chosen framework)
  Reasoning depth: minimal — lookup
```

**Resulting behavior:** Strategist handles the framework choice with proper trade-off analysis. Version pinning is answered inline as a fact.

### Example 2: Ozymandias Catch

**User asks:** "Is our data pipeline HIPAA compliant?"

**Surface classification:** Reckoning (yes/no binary question)

**Ozymandias test:** Can this be answered with a single word? Technically yes. Does explaining the answer require multi-paragraph reasoning? Yes — HIPAA compliance involves multiple requirements, interpretation, and risk assessment.

**Corrected classification:** evaluative_judgment (criteria exist — HIPAA requirements — but applying them requires judgment about the specific pipeline)

### Example 3: Novel Detection

**User asks:** "Should we open-source our core agent framework?"

**Classification:** novel_judgment
- No direct precedent for this specific framework
- High stakes (irreversible)
- Involves strategic, competitive, and community considerations with no clear criteria
- Reasonable experts would disagree fundamentally

**Resulting behavior:** Expanded reasoning budget. Surface for human review. Document all assumptions and value trade-offs explicitly.

---

## Next Steps

1. ~~**Integrate with Navigator**~~ → Done (Module 01 includes decision type routing enrichment)
2. ~~**Integrate with Strategist**~~ → Done (Module 10 includes decision type framework routing)
3. ~~**Cross-link with Calibration Layer**~~ → Done (Module 12 includes variance expectations)
4. ~~**Embed in all modes**~~ → Done (all modes include decision_type metadata)
5. **Build Ozymandias test set** → Curate examples of disguised questions for validation

---

## Attribution

| Element | Source |
|---------|--------|
| Four-part decision taxonomy | PNW AGI group ingredients, our synthesis |
| Ozymandias Test concept | Our contribution |
| Token efficiency analysis by decision type | Our analysis |
| Integration with calibration variance expectations | Our contribution |

---

## Related Modules

- `01_Navigator_Agent.md` — Routing enrichment with decision type
- `10_Strategist_Agent.md` — Framework selection by decision type
- `05_Expert_Agent_Example.md` — Finding classification by decision type
- `11_Calibrator_Agent.md` — Config decision classification
- `02_Builder_Agent.md` — Design decision metadata in specs
- `12_Calibration_Layer.md` — Variance expectations by decision type
- `19_Memory_Architecture.md` — (6.1) Decision type metadata persisted in routing index entries
- `20_Permission_Model.md` — (6.1) Decision type maps directly to base risk tier (reckoning→LOW, evaluative→MEDIUM, novel→HIGH)

---

## Integration with KF-9 (Permission Model) — 6.1

Decision Classification provides the primary input to the Permission Model's risk tier assignment.

```yaml
permission_integration:
  mapping:
    reckoning: LOW (auto-approve, minimal logging)
    evaluative_judgment: MEDIUM (auto-approve with full logging)
    predictive_judgment: MEDIUM (auto-approve with full logging, assumptions documented)
    novel_judgment: HIGH (human confirmation required)
    
  chain_compound:
    - Chain length compounds risk independently of decision type
    - A 3+ mode chain producing evaluative output → minimum MEDIUM, review for HIGH
    
  confidence_compound:
    - Low confidence (< 0.5) escalates risk tier by one level
    - This means a low-confidence evaluative judgment → HIGH tier
    
  diagnostic_value:
    - If decision type is reckoning but permission gate classifies as HIGH → misclassification signal
    - If decision type is novel but permission gate classifies as LOW → dangerous gap
```
