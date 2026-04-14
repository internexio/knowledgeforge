# Operational Bounds

## Module Metadata

```yaml
module:
  title: Operational Bounds
  version: 6.5.0
  purpose: Maintain key agent operational metrics within defined ranges and trigger corrective behavior when metrics drift
  topics: [operational-safety, metric-monitoring, bounds-checking, corrective-action, chronic-drift, cache-efficiency, circuit-breakers]
  contexts: [agent-operations, quality-assurance, cost-management, reliability]
  difficulty: advanced
  related: [03_Coordination_Patterns, 10_Strategist_Agent, 14_Metacognitive_Monitor, 15_Grounding_Scores, 18_Salience_Allocation, 19_Memory_Architecture, 20_Permission_Model]
  changelog:
    6.4.0: |
      - Added metric #9: Token Cost Per Mode — per-mode token tracking, 40% chain budget ceiling
    6.2.0: |
      - Version alignment with KF 6.2
      - Accretion rate monitoring deferred to Module 21 (Metacognitive Monitor catches over-accretion)
    6.1.0: |
      - Added cache hit rate metric with 80% floor (D3)
      - Added circuit breaker tracking (D3/D4)
      - Added mode transition cost as operational metric (D3)
      - Added consolidation efficiency metric (D2, integrates with Module 19)
      - Integrated with Permission Model (Module 20) for circuit breaker enforcement
```

---

## Core Approach

The Metacognitive Monitor (KF-2) catches acute failures — loops, overflows, confidence collapse. Operational Bounds catches **chronic drift** — slow degradation that doesn't trigger acute alarms but degrades overall system quality over time.

**Primary function:** Keep agent operational metrics within healthy ranges. Trigger corrective action when metrics drift out of bounds.

**Key insight:** The goal is not optimization of any single metric — it's keeping all metrics within acceptable ranges simultaneously. An agent that's cheap but inaccurate is as unhealthy as one that's accurate but expensive.

**Two-layer safety:** Monitor detects acute failures. Bounds prevent chronic drift. Together they cover the full failure spectrum.

---

## Operational Bounds

### 1. Context Utilization

```yaml
context_utilization:
  healthy_range: 40% – 80%
  
  below_40:
    diagnosis: Agent is wasting context capacity
    risk: Under-utilizing available information; may be doing shallow analysis
    corrective_action: 
      - Check if agent is discarding relevant context
      - Verify agent is loading appropriate background knowledge
      
  above_80:
    diagnosis: Context pressure building
    risk: Context overflow imminent; quality degradation from compression
    corrective_action:
      - COMPRESS_CONTEXT (via KF-2 monitor)
      - Hand off to fresh agent if compression insufficient
      - For chronic high utilization: redesign task decomposition (smaller subtasks)
      
  measurement: (tokens_used / context_window_size) × 100
  check_frequency: Every agent output
```

### 2. Error Rate

```yaml
error_rate:
  measurement: Rolling average of last 10 tasks
  alarm_threshold: > 15%
  
  below_15:
    status: healthy
    action: CONTINUE
    
  above_15:
    diagnosis: Agent is failing too frequently
    risk: Unreliable output; downstream agents receiving bad input
    corrective_action:
      - Switch to verification mode (slower, more careful)
      - Increase confidence threshold before emitting output
      - If error rate persists above 15% after mode switch: ESCALATE
      
  error_definition:
    - Task produces output that fails downstream validation
    - Task requires human correction
    - Task is rejected by receiving agent
    - Task confidence below threshold
```

### 3. Confidence Calibration

```yaml
confidence_calibration:
  measurement: predicted_accuracy vs. actual_accuracy over rolling window
  drift_threshold: ± 10%
  
  well_calibrated:
    definition: Agent's confidence predictions match actual accuracy within ±10%
    status: healthy
    
  overconfident:
    definition: Predicted accuracy exceeds actual by > 10%
    diagnosis: Agent is too confident — claiming accuracy it doesn't have
    risk: Downstream agents trust outputs that shouldn't be trusted
    corrective_action:
      - Flag outputs for human review until calibration improves
      - Reduce confidence scores by observed offset
      - Investigate: is the agent skipping verification steps?
      
  underconfident:
    definition: Actual accuracy exceeds predicted by > 10%
    diagnosis: Agent is too cautious — flagging good outputs as uncertain
    risk: Unnecessary escalation; wasted human review time
    corrective_action:
      - Adjust confidence floor upward
      - Investigate: is the agent being triggered by noise, not signal?
```

### 4. API Cost Per Task

```yaml
cost_bounds:
  measurement: Token cost per task per agent per hour
  ceiling: Budget-dependent (set per agent, per deployment)
  
  within_budget:
    status: healthy
    action: CONTINUE
    
  approaching_ceiling:
    threshold: 80% of budget
    corrective_action:
      - Queue non-urgent tasks
      - Continue critical path only
      - Flag for human decision: increase budget or reduce scope?
      
  over_ceiling:
    corrective_action:
      - Pause all non-critical agent activity
      - ESCALATE to human for budget decision
      - Log which tasks consumed the budget (for future planning)
```

### 5. Cache Hit Rate (6.1)

```yaml
cache_hit_rate:
  measurement: Percentage of API calls that hit the prompt cache prefix
  floor: 80%
  
  above_80:
    status: healthy
    action: CONTINUE
    
  below_80:
    diagnosis: Prompt changes are breaking the cache too frequently
    risk: Increased API cost and latency from full prompt reprocessing
    corrective_action:
      - Audit recent prompt changes for cache-breaking patterns
      - Check if mode transitions are modifying the static zone (they shouldn't)
      - Verify dynamic boundary is correctly placed
      - If chronic: redesign the prompt split between static and dynamic zones
      
  check_frequency: hourly (aggregate)
  
  note: >
    This metric matters for cost efficiency at scale. At low volume,
    cache misses are tolerable. Monitor but don't over-optimize until
    API call volume justifies the effort.
```

### 6. Circuit Breaker State (6.1)

```yaml
circuit_breaker_tracking:
  measurement: Consecutive failure count per mode, per chain step
  threshold: 3 consecutive failures triggers circuit breaker
  
  healthy:
    description: No mode has hit the circuit breaker threshold
    action: CONTINUE
    
  tripped:
    description: A mode has failed 3+ consecutive times
    action: |
      - Halt execution of that mode
      - Surface failure diagnostics to user/orchestrator
      - Do NOT auto-retry — circuit breaker must be manually reset
      - Log full diagnostic for post-mortem
    risk_tier: "Automatically escalated to HIGH per Module 20"
    
  tracking:
    per_mode: [builder, critic, expert, debugger, strategist, synthesizer, calibrator]
    per_chain: Track consecutive failures at each chain step independently
    reset_condition: Any successful execution resets the counter for that mode
    
  chain_breaker:
    threshold: 2 consecutive failures at the same chain step
    action: Abort chain. Surface partial results from completed steps.
```

### 7. Mode Transition Cost (6.1)

```yaml
mode_transition_cost:
  measurement: Additional latency and token cost from mode switches
  
  tracking:
    per_transition: Record (from_mode, to_mode, latency_delta_ms, token_delta)
    rolling_average: Last 20 transitions
    
  healthy_range: "Transition cost < 15% of total chain execution cost"
  
  above_15_percent:
    diagnosis: Mode switches are expensive relative to value delivered
    corrective_action:
      - Review chain design — are there unnecessary intermediate modes?
      - Check if inline handling would suffice for low-value steps
      - Verify static/dynamic boundary is preserving cache prefix
      
  note: >
    This metric is informational during interactive sessions.
    It becomes actionable for autonomous deployment where
    transition cost directly impacts throughput.
```

### 8. Consolidation Efficiency (6.1)

```yaml
consolidation_efficiency:
  measurement: Context utilization reduction after consolidation cycle (Module 19)
  target: ≥ 20% reduction when triggered
  
  above_20_reduction:
    status: healthy
    action: CONTINUE
    
  below_20_reduction:
    diagnosis: Consolidation isn't compressing enough. Either too little closeable state or consolidation logic is too conservative.
    corrective_action:
      - Check if routing index has too many open items (close completed work)
      - Check if Tier 2 state is being retained unnecessarily
      - If chronic: task decomposition may need redesign (smaller subtasks)
      
  check_frequency: every_consolidation_event
```

---

### 9. Token Cost Per Mode (6.4)

```yaml
token_cost_per_mode:
  measurement: Total tokens consumed per mode activation (input + output)

  tracking:
    per_mode: [navigator, builder, critic, expert, debugger, strategist, synthesizer, calibrator]
    rolling_average: Last 20 activations per mode
    per_chain: Aggregate token cost with mode-level breakdown

  healthy_range: "No single mode consumes > 40% of chain token budget"

  above_40_percent:
    diagnosis: One mode is dominating chain cost disproportionately
    corrective_action:
      - Review if mode scope is too broad (decompose into sub-tasks)
      - Check if mode is re-deriving knowledge available in Tier 0/Tier 1
      - Evaluate whether pass-through would suffice for that step

  rationale: >
    Computational cost is a first-class metric in neuro-symbolic systems.
    The static/dynamic cache boundary is an implicit energy optimization;
    this metric makes overhead tracking explicit. Validated by Duggan et al.
    (ICRA 2026): ~100x energy efficiency of neuro-symbolic over end-to-end
    maps to per-invocation cost awareness at runtime.

  check_frequency: every_chain_completion

  note: >
    Informational in interactive sessions. Actionable in autonomous
    deployment and when optimizing API spend.
```

---

## Corrective Action Summary

| Metric | Out of Bounds | Corrective Action |
|--------|---------------|-------------------|
| Context utilization > 80% | Compress, summarize, or hand off to fresh agent |
| Context utilization < 40% | Verify agent is loading relevant context |
| Error rate > 15% | Switch to verification mode (slower, more careful) |
| Confidence drift > +10% | Flag outputs for review, reduce confidence scores |
| Confidence drift > -10% | Adjust confidence floor upward |
| Cost > 80% budget | Queue non-urgent tasks, critical path only |
| Cost > 100% budget | Pause non-critical activity, ESCALATE |
| Cache hit rate < 80% | Audit prompt changes, verify static/dynamic boundary |
| Circuit breaker tripped | Halt mode, surface diagnostics, do not auto-retry |
| Transition cost > 15% chain cost | Review chain design, consider inline handling |
| Consolidation < 20% reduction | Close completed work, check Tier 2 retention |
| Mode token cost > 40% of chain | Decompose task, check Tier 0/1 for re-derivable knowledge, evaluate pass-through |

---

## Interaction with Metacognitive Monitor (KF-2)

Operational Bounds and the Monitor are complementary layers.

```yaml
two_layer_safety:
  monitor_catches:
    - Circular reasoning (acute — happens within one task)
    - Context overflow (acute — happens within one task)
    - Confidence collapse (acute — drops suddenly within one task)
    - Stuck agents (acute — detected within minutes)
    - User-side session degradation (6.1 — detected within turns)
    - Stale state usage (6.1 — detected before action)
    
  bounds_catches:
    - Creeping context waste (chronic — develops over many tasks)
    - Rising error rate (chronic — develops over 10+ tasks)
    - Calibration drift (chronic — develops over many evaluations)
    - Budget creep (chronic — develops over hours/days)
    - Cache efficiency decline (6.1 — develops over many mode transitions)
    - Circuit breaker patterns (6.1 — repeated failures in specific modes)
    - Consolidation inefficiency (6.1 — develops over many sessions)
    
  data_flow:
    - Monitor feeds real-time metrics to Bounds
    - Bounds tracks rolling averages from Monitor data
    - Monitor handles acute intervention; Bounds handles chronic correction
    - When both trigger simultaneously: Monitor intervention takes precedence (acute > chronic)
```

---

## Integration Points

### With Coordinator (03_Coordination_Patterns)

Coordinator uses Bounds data for resource allocation and agent assignment.

```yaml
coordinator_integration:
  data_provided:
    - Per-agent error rates (for reliability-weighted assignment)
    - Per-agent cost rates (for budget-aware scheduling)
    - Per-agent context utilization (for load balancing)
    
  coordinator_actions:
    - Avoid assigning tasks to agents with error rate > 15%
    - Prefer lower-cost agents for non-critical tasks
    - Spread load across agents to prevent context exhaustion
```

### With Strategist (10_Strategist_Agent)

Strategist uses Bounds data for cost/quality trade-off analysis.

```yaml
strategist_integration:
  data_provided:
    - Current cost per task across agent pool
    - Quality metrics (error rate, calibration accuracy)
    - Capacity utilization
    
  strategist_actions:
    - Include operational cost in strategic trade-off analysis
    - Flag when quality improvements require cost increases
    - Recommend agent pool adjustments based on bounds data
```

### With Grounding Scores (15_Grounding_Scores)

Bounds monitors grounding score distribution across agent outputs.

```yaml
grounding_integration:
  monitoring:
    - Track average grounding score per agent over time
    - Alert if average grounding trends downward (agent relying more on unverified inference)
    - Alert if grounding scores are suspiciously uniform (possible gaming)
```

---

## Default Bounds Configuration

```yaml
default_bounds:
  context_utilization:
    lower: 40%
    upper: 80%
    check_frequency: every_output
    
  error_rate:
    rolling_window: 10 tasks
    alarm_threshold: 15%
    check_frequency: every_task_completion
    
  confidence_calibration:
    drift_threshold: 10%
    measurement_window: 20 evaluations
    check_frequency: every_20_evaluations
    
  cost:
    ceiling: deployment_specific
    warning_at: 80% of ceiling
    check_frequency: hourly
    
  # NEW 6.1 bounds
  cache_hit_rate:
    floor: 80%
    check_frequency: hourly
    
  circuit_breaker:
    consecutive_failure_threshold: 3
    chain_failure_threshold: 2
    check_frequency: every_task_completion
    reset_on: successful_execution
    
  mode_transition_cost:
    ceiling: 15% of chain execution cost
    check_frequency: every_chain_completion
    
  consolidation_efficiency:
    minimum_reduction: 20%
    check_frequency: every_consolidation_event
    
  logging:
    log_all_bound_violations: true
    log_corrective_actions: true
    log_circuit_breaker_events: true
    log_bounds_checks: false (too noisy)
```

---

## Constraints

- Bounds are ranges, not targets — the goal is staying within bounds, not optimizing any single metric
- Corrective actions have costs — switching to verification mode trades speed for accuracy
- Bounds need calibration per deployment — defaults are starting points
- Chronic drift detection requires history — Bounds becomes useful after ~20 tasks, not immediately
- Cost bounds are deployment-specific — no universal default
- Bounds can conflict (e.g., reducing cost may increase error rate) — Strategist resolves

---

## Success Criteria

- All agent operational metrics stay within defined bounds 95% of the time
- Chronic drift detected before it causes downstream failures
- Corrective actions resolve bound violations within the next 5 tasks
- Cost stays within budget without sacrificing critical-path quality
- Two-layer safety (Monitor + Bounds) catches both acute and chronic failures

---

## Related Modules

- `14_Metacognitive_Monitor.md` — Acute failure detection (complementary layer)
- `03_Coordination_Patterns.md` — Resource allocation using bounds data
- `10_Strategist_Agent.md` — Cost/quality trade-off analysis
- `15_Grounding_Scores.md` — Grounding distribution monitoring
- `19_Memory_Architecture.md` — (6.1) Consolidation efficiency metric source
- `20_Permission_Model.md` — (6.1) Circuit breakers enforce permission model's halt-on-failure rule
