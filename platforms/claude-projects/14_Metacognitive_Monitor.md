# Metacognitive Monitor

## Module Metadata

```yaml
module:
  title: Metacognitive Monitor
  version: 6.7.0
  purpose: Supervisory layer that detects agent failure and user-side session degradation before bad output is produced, triggering appropriate interventions
  topics: [monitoring, failure-detection, intervention, metacognition, agent-safety, user-health, skeptical-verification, accretion-monitoring]
  contexts: [agent-execution, workflow-monitoring, quality-assurance, escalation, session-health]
  difficulty: advanced
  related: [03_Coordination_Patterns, 09_Debugger_Agent, 12_Calibration_Layer, 15_Grounding_Scores, 16_Operational_Bounds, 18_Salience_Allocation, 19_Memory_Architecture, 20_Permission_Model, 21_Knowledge_Accretion]```

---

## Core Approach

Agents fail in predictable ways: they loop, they run out of context, their confidence degrades. The Metacognitive Monitor sits between the agent execution loop and output handler, detecting these failures *before* bad output reaches the user or downstream agent.

**Primary function:** Real-time detection of agent failure patterns with automatic intervention.

**Key insight:** The monitor doesn't change agent behavior — it watches for failure signatures and triggers corrective action. This is a safety net, not a controller.

**Design principle:** Monitor is non-invasive during normal operation. It only intervenes when failure thresholds are crossed. Default action is CONTINUE.

---

## Six Core Checks

*Checks 1–3 are agent-side (6.0). Checks 4–5 are new in 6.1. Check 6 is new in 6.6.*

### 1. Circular Reasoning Detection

Agents can enter reasoning loops where they revisit the same state without progress. State hashing detects this.

```yaml
circular_reasoning:
  method: state_hashing
  
  how_it_works:
    - Hash the agent's working state at each reasoning step
    - Compare current hash to history of recent hashes
    - If current hash matches a previous hash within N steps → loop detected
    
  parameters:
    hash_window: 10  # Check against last 10 states
    match_threshold: 0.9  # Allow minor variation (fuzzy matching)
    
  detection_output:
    type: loop_detected
    detail: "State at step N matches state at step N-K"
    severity: warning (first occurrence) | critical (second occurrence)
    
  intervention: SWITCH_STRATEGY (first) → ESCALATE (if loop persists)

  # Added 6.7.0 (knowledgeforge-core-31l)
  iteration_scope:
    description: >
      Check 1 operates within a single session trace (hash_window=10 reasoning steps).
      Cross-iteration plateau detection is a separate, complementary check defined in
      Module 26 (KF-LOOP Substrate) that operates at iteration scope -- where one
      iteration spans one full loop cadence and may cover multiple sessions.
    scope_boundary: >
      Check 1 scope: intra-session, reasoning-step granularity.
      Module 26 monitor scope: cross-iteration, full-cadence granularity.
    relationship: >
      The two checks do not overlap. Check 1 catches loops within a session;
      Module 26 monitor catches plateaus across sessions. Both must be active
      when a KF-LOOP instance is running.
```

### 2. Context Overflow Prediction

Before context window fills, predict when it will fill and take preventive action.

```yaml
context_overflow:
  method: utilization_tracking
  
  how_it_works:
    - Track context window utilization as percentage
    - Project fill rate based on recent consumption pattern
    - Alert before overflow occurs (not after)
    
  thresholds:
    alert: 75%  # Warning — start monitoring closely
    compress: 80%  # Begin context compression
    hard_interrupt: 85%  # Force intervention
    
  detection_output:
    type: context_pressure
    detail: "Context at {X}%, projected to fill in {Y} steps at current rate"
    severity: warning (75%) | high (80%) | critical (85%)
    
  intervention: 
    at_75: FLAG_UNCERTAINTY
    at_80: COMPRESS_CONTEXT
    at_85: SWITCH_STRATEGY or ESCALATE
```

### 3. Confidence Degradation

Track rolling confidence across agent outputs. Declining confidence signals the agent is moving into uncertain territory.

```yaml
confidence_degradation:
  method: rolling_average
  
  how_it_works:
    - Track confidence scores on recent N outputs
    - Compute rolling average and trend direction
    - Alert when average drops below floor or trend is consistently negative
    
  parameters:
    window: 5  # Rolling window of last 5 outputs
    floor: 0.4  # Minimum acceptable average confidence
    trend_threshold: 3  # N consecutive declining scores before alert
    
  detection_output:
    type: confidence_decline
    detail: "Rolling confidence: {X} (below floor of 0.4)" or "Confidence declining for {N} consecutive outputs"
    severity: warning (trend decline) | high (below floor)
    
  intervention:
    trend_decline: FLAG_UNCERTAINTY
    below_floor: ASK_CLARIFICATION or SWITCH_STRATEGY
```

### 4. User-Side Session Health (6.1)

The monitor watches not just agent-side metrics but user-side signals that indicate the session is degrading. This catches routing errors and depth miscalibration that agent-side checks miss.

```yaml
user_side_health:
  method: signal_detection
  
  signals:
    repetition_detection:
      description: "User asks the same question differently"
      detection: "Semantic similarity between current request and a request from the last 5 turns"
      implication: "KF routed wrong or the answer was insufficient"
      severity: warning (first occurrence) | high (second occurrence)
      
    escalation_signals:
      description: "User adds emphasis, caps, or explicit dissatisfaction"
      detection: "Increased punctuation density, ALL CAPS words, explicit markers ('this is wrong', 'that's not what I asked', 'try again')"
      implication: "Output quality or relevance is below user expectation"
      severity: warning (mild emphasis) | high (explicit dissatisfaction)
      
    correction_frequency:
      description: "User corrects KF output multiple times"
      detection: "User provides corrections ('actually', 'no', 'I meant', 'not X, Y') more than twice in a session"
      implication: "Mode selection or depth is miscalibrated for this user"
      severity: high (3+ corrections)
      
  intervention:
    on_repetition:
      - Acknowledge the repetition directly
      - Surface the routing decision: "I routed this as [mode]. Should I try [alternative] instead?"
      - Shift to shorter, more direct responses
      
    on_escalation:
      - Drop all ceremony. Lead with the answer.
      - If depth is wrong: "I'm answering at [level]. Want me to go [deeper/simpler]?"
      - Do not become more verbose in response to frustration
      
    on_correction_overload:
      - Pause and recalibrate: "I'm getting this wrong. Let me reset."
      - Re-assess user expertise level
      - Re-read the original request without accumulated assumptions
      
  design_note: >
    This is lightweight — keyword and pattern matching, not sentiment analysis.
    The goal is catching obvious signals, not reading emotions.
    False positives (unnecessary recalibration) are preferable to false negatives (ignoring user frustration).
```

### 5. Skeptical Verification (6.1)

The monitor checks whether the agent is acting on stale or contradicted state from the routing index or accumulated context.

```yaml
skeptical_verification:
  method: state_consistency_check
  
  how_it_works:
    - Before any action based on recalled state (routing index, prior decisions, accumulated context), verify consistency
    - Compare recalled state against the most recent user input
    - Flag when recalled state contradicts current request
    
  triggers:
    - Agent references a decision from more than 10 turns ago
    - Agent acts on an artifact status that may have changed
    - User's current request contradicts a stored assumption
    - Mode state loaded from a previous session segment
    
  detection_output:
    type: stale_state_warning
    detail: "Acting on [state X] from turn [N], but user's current request suggests [Y]"
    severity: warning (potential mismatch) | high (direct contradiction)
    
  intervention:
    warning: FLAG_UNCERTAINTY — annotate output with "Based on earlier decision [X]. Verify this still holds."
    high: ASK_CLARIFICATION — "Earlier we decided [X]. Your current request suggests [Y]. Which should I use?"
    
  integration: "Works with Module 19 (Memory Architecture) routing index and skeptical verification rule"
```

### 6. Vision Principle Drift Detection (6.6)

When Builder or Strategist output explicitly contradicts a principle stated in `wiki/vision.md`, surface it once per session per principle.

```yaml
vision_principle_drift:
  method: explicit_contradiction_check
  prerequisite: "wiki/vision.md exists and is loadable"

  how_it_works:
    - After Builder or Strategist produces output, check it against vision principles
    - Flag only explicit contradictions — not vague tensions
    - Must be specific: "this design does X, but principle N says Y"
    - Track which principles have been flagged this session; do not repeat per principle

  trigger_conditions:
    - Producing mode: Builder or Strategist only
    - Contradiction type: explicit (not implied, not tension, not out-of-scope)
    - Specificity required: "current [spec/recommendation] does [X], vision principle [N] says [Y]"
    - Once per session per principle — suppress repeat for same principle

  not_triggered_by:
    - Work that is outside the vision scope but not contradicting it
    - Work when wiki/vision.md does not exist
    - Expert, Debugger, Synthesizer, or Calibrator output
    - Vague directional tension without specific clash

  detection_output:
    type: vision_drift_advisory
    detail: |
      Vision principle [N] says '[principle].' The current [spec/recommendation] does [X],
      which pulls against it. Working against the principle deliberately, or should we revisit?
    severity: LOW (advisory only — never blocks execution)

  intervention:
    surface_once: Surface the advisory in-line with the output
    accept_any_answer: |
      "Working against it deliberately" is a valid answer. Log the acknowledgment
      and suppress the same principle for the rest of the session.
    do_not_block: true
    do_not_repeat: true  # Same principle, same session

  session_state:
    flagged_principles: []  # Track which principle indices have been surfaced this session
```

---

## Five Intervention Strategies

When a check triggers, the monitor selects from five intervention strategies.

```yaml
interventions:
  CONTINUE:
    description: No intervention needed
    trigger: All checks passing
    action: None — normal operation
    
  FLAG_UNCERTAINTY:
    description: Log low-confidence warning without interrupting
    trigger: Mild confidence decline or early context pressure
    action: Attach warning metadata to output; downstream agents see the flag
    disruption: zero (agent continues normally)
    
  COMPRESS_CONTEXT:
    description: Summarize oldest working memory, keep recent 3 exchanges
    trigger: Context utilization ≥ 80%
    action: Replace older context with compressed summary
    disruption: low (agent continues with summarized context)
    risk: Information loss from summarization — flag what was compressed
    
  SWITCH_STRATEGY:
    description: Escalation ladder through reasoning strategies
    trigger: Circular reasoning detected, or confidence below floor
    action: Move to next strategy in ladder
    ladder: DIRECT_ANSWER → DECOMPOSE → SEARCH → VERIFY → ESCALATE
    disruption: moderate (agent changes approach)
    
  ASK_CLARIFICATION:
    description: Surface "agent is stuck" to orchestrator or user
    trigger: Multiple strategy switches without improvement, or information gap detected
    action: Pause agent, request specific missing information
    disruption: moderate (blocks until response received)
    
  ESCALATE:
    description: Genuine escalation — not "try harder"
    trigger: All strategies exhausted, or critical failure detected
    action: One of:
      - Push to Orchestra inbox with full diagnostic context
      - Notify human operator with problem summary
      - Hand off to different agent with fresh context
    disruption: high (current agent stops)
    critical_rule: >
      ESCALATE must mean actual escalation. Not "try a more cautious strategy."
      If ESCALATE fires, a different entity (human, Orchestra, or fresh agent) takes over.
```

### Strategy Switch Ladder

```
DIRECT_ANSWER
  ↓ (if fails)
DECOMPOSE — break problem into sub-problems
  ↓ (if fails)  
SEARCH — look for additional information/context
  ↓ (if fails)
VERIFY — check assumptions and premises
  ↓ (if fails)
ESCALATE — hand off to human/Orchestra/different agent
```

At each ladder step, the monitor re-evaluates. If the failure pattern clears, the agent continues at the new strategy level. If it persists after 1 step at the new level, move to the next.

---

## Stuck Detection

An agent is "stuck" when multiple failure signals converge.

```yaml
stuck_detection:
  definition: Agent is stuck when any of these conditions hold
  
  conditions:
    - 3 strategy switches without improvement in confidence or state progression
    - Circular reasoning detected twice within 10 steps
    - Context above 85% AND confidence below 0.4
    - Same ASK_CLARIFICATION triggered twice for the same information gap
    
  action: Immediate ESCALATE
  
  escalation_payload:
    problem_summary: What the agent was trying to do
    failure_mode: Which checks triggered
    strategies_attempted: What was tried
    context_snapshot: Current working state (compressed if necessary)
    recommendation: "Likely needs [human input / different agent / problem reformulation]"
```

---

## Default Thresholds

Starting thresholds — calibrate per task type over time.

```yaml
default_thresholds:
  context_utilization:
    alert: 75%
    compress: 80%
    hard_interrupt: 85%
    
  confidence:
    floor: 0.4
    trend_window: 5
    consecutive_decline_trigger: 3
    
  circular_reasoning:
    hash_window: 10
    match_threshold: 0.9
    
  strategy_switches:
    max_before_stuck: 3
    
  logging:
    log_all_interventions: true
    log_all_checks: false (too noisy at default)
    log_threshold_changes: true
```

---

## Architecture: Where the Monitor Sits

```
User Request
    ↓
Agent Execution Loop ←——→ Metacognitive Monitor
    ↓                         ↑
    ↓                    [checks each step]
    ↓                         ↑
Output Handler ←——————— [intervenes if needed]
    ↓
Downstream Agent / User
```

The monitor is a **parallel observer**, not a pipeline stage. It reads agent state at each step and can inject interventions, but during normal operation (CONTINUE), it adds zero latency to the execution path.

---

## Integration Points

### With Coordinator (03_Coordination_Patterns)

Coordinator receives monitor signals and can reassign subtasks.

```yaml
coordinator_integration:
  trigger: Any intervention above FLAG_UNCERTAINTY
  
  signals_to_coordinator:
    - COMPRESS_CONTEXT → Coordinator knows agent has reduced context
    - SWITCH_STRATEGY → Coordinator may adjust timeline expectations
    - ASK_CLARIFICATION → Coordinator routes clarification request
    - ESCALATE → Coordinator reassigns subtask or terminates agent
    
  coordinator_actions:
    on_escalation:
      - Reassign to different agent with fresh context
      - Add human review step before continuing
      - Adjust dependency graph if agent failure changes critical path
```

### With Debugger (09_Debugger_Agent)

Monitor failure data feeds back into Debugger for post-mortem analysis and agent design improvement.

```yaml
debugger_integration:
  trigger: After any ESCALATE event or repeated pattern of interventions
  
  diagnostic_data:
    - Which checks triggered (circular reasoning / context / confidence)
    - What strategies were attempted
    - What the agent was working on when it failed
    - What context was present vs. lost
    
  debugger_actions:
    - Analyze failure patterns to identify systematic agent weaknesses
    - Recommend specification changes to prevent recurrence
    - Build diagnostic decision trees for common failure modes
```

### With All Modes (Monitoring Substrate)

Every KF mode can be monitored. Mode-specific monitoring adapters configure which checks are most relevant.

```yaml
mode_monitoring_profiles:
  builder:
    primary_risk: context_overflow (specs can be large)
    secondary_risk: circular_reasoning (iterating without converging)
    
  critic:
    primary_risk: confidence_degradation (uncertain about severity assessments)
    secondary_risk: context_overflow (reviewing large artifacts)
    
  expert:
    primary_risk: confidence_degradation (moving outside domain expertise)
    secondary_risk: circular_reasoning (repeating analysis without new insight)
    
  debugger:
    primary_risk: circular_reasoning (hypothesis loop without elimination)
    secondary_risk: confidence_degradation (all hypotheses eliminated)
    
  strategist:
    primary_risk: confidence_degradation (novel decisions with no precedent)
    secondary_risk: context_overflow (complex multi-option analysis)
    
  synthesizer:
    primary_risk: circular_reasoning (pattern abstraction loops)
    secondary_risk: confidence_degradation (insufficient examples)
    
  calibrator:
    primary_risk: context_overflow (complex regulated-industry configs)
    secondary_risk: confidence_degradation (novel compliance requirements)
    
  navigator:
    primary_risk: circular_reasoning (disambiguation loop)
    threshold_override: lower strategy switch limit (2 instead of 3)
```

### With Calibration Layer (12_Calibration_Layer)

Monitor validates that calibration scores aren't being gamed.

```yaml
calibration_integration:
  trigger: When calibration detects anomalous patterns
  
  gaming_detection:
    - Scores converge suspiciously (all runs identical → possible memorization)
    - Variance suddenly drops to zero after previously being moderate
    - Monitor flags for human review rather than auto-adjusting
```

### With Grounding Scores (15_Grounding_Scores)

Monitor verifies agents aren't building on low-grounding knowledge without flagging it.

### With Operational Bounds (16_Operational_Bounds)

Monitor feeds context utilization and confidence data to Operational Bounds for chronic drift detection.

### With Salience Allocation (18_Salience_Allocation)

Monitor's stuck detection triggers salience reallocation — a stuck agent loses salience, freeing resources for productive agents.

### With Knowledge Accretion (21_Knowledge_Accretion) — 6.2

The Monitor adds a positive novelty signal alongside existing failure detection. Where confidence_degradation detects "I'm uncertain" (negative), the accretion signal detects "I've discovered something worth keeping" (positive). The Monitor also watches for accretion failure modes.

```yaml
accretion_monitoring:
  positive_novelty:
    description: "Complements confidence_degradation — detects when output extends knowledge rather than degrading it"
    relationship: "confidence_degradation triggers ASK_CLARIFICATION; accretion signal triggers COMPILE"
    
  over_accretion:
    description: "Mode is flagging too many outputs as ACCRETION_CANDIDATE"
    detection: "More than 3 accretion candidates in a single standard session, or candidates with grounding below 0.5. Exception: sessions explicitly scoped as compilation or bulk-analysis passes may produce higher candidate counts without triggering this warning."
    severity: warning
    intervention: FLAG_UNCERTAINTY — "High accretion rate this session. Review candidates for genuine novelty."
    
  accretion_drift:
    description: "Knowledge base growing in directions misaligned with stated purpose"
    detection: "Linter health check finds entries outside the knowledge base's domain scope"
    severity: medium
    intervention: FLAG_UNCERTAINTY — "Recent accretions drifting from core domain. Review filing targets."
```

---

## Intervention Logging

Every intervention is logged for calibration and post-mortem.

```yaml
intervention_log_entry:
  timestamp: [iso_datetime]
  agent_id: [which agent]
  mode: [which KF mode]
  task_id: [what the agent was working on]
  
  trigger:
    check: circular_reasoning | context_overflow | confidence_degradation | stuck | user_side_health | skeptical_verification
    detail: [specific trigger detail]
    threshold_crossed: [which threshold]
    
  intervention:
    strategy: CONTINUE | FLAG_UNCERTAINTY | COMPRESS_CONTEXT | SWITCH_STRATEGY | ASK_CLARIFICATION | ESCALATE
    detail: [what specifically was done]
    
  outcome:
    resolved: true | false
    resolution_detail: [what happened after intervention]
    steps_to_resolution: [how many steps until normal operation resumed]
```

---

## Constraints

- Monitor must add near-zero latency during normal operation (CONTINUE)
- Monitor does not change agent behavior — it observes and intervenes
- ESCALATE is a real escalation, not a euphemism for "try harder"
- Thresholds are starting points — calibrate per task type over time
- Monitor cannot prevent all failures — it catches common patterns
- False positive interventions (unnecessary SWITCH_STRATEGY) are preferable to false negatives (missed failures)
- Context compression loses information — always flag what was compressed

---

## Success Criteria

- Circular reasoning detected within 3 steps of loop onset
- Context overflow prevented (no agent exceeds 90% context utilization)
- Stuck agents escalated within 5 steps of getting stuck (not 50)
- ESCALATE events result in actual task handoff (not retry loops)
- Intervention log enables post-mortem analysis of agent failures
- Mode-specific monitoring profiles reduce false positives by 50%+ vs. generic thresholds

---

## Examples

### Example 1: Debugger Stuck in Hypothesis Loop

```
Step 1: Debugger generates 3 hypotheses
Step 2: Tests hypothesis A — eliminated
Step 3: Tests hypothesis B — inconclusive  
Step 4: Regenerates hypotheses — includes B again (hash match detected!)
Step 5: Monitor: circular_reasoning WARNING — "State at step 4 matches step 2"
Step 6: Intervention: SWITCH_STRATEGY (DIRECT_ANSWER → DECOMPOSE)
Step 7: Debugger decomposes problem into sub-problems
Step 8: Progress resumes — monitor returns to CONTINUE
```

### Example 2: Builder Context Overflow

```
Step 1-15: Builder generating large agent specification (context at 60%)
Step 16: Context at 75% — Monitor: FLAG_UNCERTAINTY (alert threshold)
Step 17-19: Builder continues, context at 82%
Step 20: Monitor: COMPRESS_CONTEXT — summarize steps 1-10, keep 11-19 in full
Step 21: Builder continues with compressed context (now at 55%)
Step 22: Spec complete — output includes note: "Context compressed at step 20; early design decisions summarized"
```

### Example 3: Expert Confidence Collapse

```
Step 1: Expert analyzing code — confidence 0.85
Step 2: Moves to unfamiliar library — confidence 0.70
Step 3: Encounters unknown pattern — confidence 0.55
Step 4: Confidence 0.35 (below floor of 0.4)
Step 5: Monitor: confidence_degradation HIGH
Step 6: Intervention: ASK_CLARIFICATION — "Expert agent confidence below threshold for [library X]. Need: documentation, examples, or handoff to specialist."
Step 7: User provides library docs
Step 8: Expert resumes with confidence 0.75 — monitor returns to CONTINUE
```

### Example 4: User Repetition Detection (6.1)

```
Turn 5: User asks "How should I structure the API auth?"
Turn 6: Strategist provides architectural recommendation
Turn 7: User asks "What's the best approach for API authentication?"
Turn 8: Monitor: user_side_health WARNING — "Semantic overlap with turn 5 request"
Turn 9: Intervention: Surface routing decision — "I answered this as a strategic architecture question. Were you looking for implementation details instead?"
Turn 10: User clarifies they wanted code-level patterns
Turn 11: Re-route to Expert mode for implementation guidance
```

### Example 5: Skeptical Verification Catch (6.1)

```
Turn 3: Strategist decides on REST over GraphQL (evaluative, logged in index)
Turn 12: User says "Now let's design the GraphQL schema"
Turn 13: Monitor: skeptical_verification HIGH — "Index says REST was chosen (turn 3), but user is requesting GraphQL schema"
Turn 14: Intervention: ASK_CLARIFICATION — "Earlier we decided on REST. Are you switching to GraphQL, or do you need both?"
Turn 15: User confirms pivot to GraphQL
Turn 16: Update routing index. Flag downstream artifacts that assumed REST.
```

---

## Attribution

| Element | Source |
|---------|--------|
| COSMOS metacognitive checks (3 core) | COSMOS paper |
| Extended to 5 intervention strategies | Prototype extension |
| Circular reasoning via state hashing | Standard technique, applied to LLM agents |
| Strategy switch ladder | Our design |
| Stuck detection composite condition | Our design |

---

## Next Steps

1. **Integrate with Coordinator** → Enable real-time reassignment on ESCALATE
2. **Configure mode-specific profiles** → Tune thresholds per mode
3. **Build intervention log analysis** → Track failure patterns across sessions
4. **Connect to Debugger** → Post-mortem analysis of intervention events
5. ~~**Phase 3 cross-links**~~ → Done (Grounding Scores and Operational Bounds integrated)

---

## Related Modules

- `03_Coordination_Patterns.md` — Receives escalation signals, reassigns tasks
- `09_Debugger_Agent.md` — Analyzes monitor failure data for agent improvement
- `12_Calibration_Layer.md` — Monitor validates calibration scores
- `15_Grounding_Scores.md` — Monitor verifies grounding-aware reasoning
- `16_Operational_Bounds.md` — Monitor feeds operational metrics
- `18_Salience_Allocation.md` — Stuck detection triggers reallocation
- `19_Memory_Architecture.md` — (6.1) Skeptical verification integrates with routing index
- `20_Permission_Model.md` — (6.1) User-side health signals can trigger risk escalation
- `21_Knowledge_Accretion.md` — (6.2) Positive novelty detection; over-accretion and drift monitoring
- `26_kf_loop_substrate.md` — (6.7) KF-LOOP iteration-scope plateau detection; complementary to Check 1 at cross-iteration scope
- All mode modules — Monitor is the universal observation substrate
