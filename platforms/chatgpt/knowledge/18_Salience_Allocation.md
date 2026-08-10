# Salience-Based Resource Allocation

## Module Metadata

```yaml
module:
  title: Salience-Based Resource Allocation
  version: 7.1.0
  purpose: Replace equal resource allocation with dynamic allocation based on task relevance to current goals
  topics: [resource-allocation, salience, prioritization, competitive-inhibition, goal-alignment]
  contexts: [multi-agent-coordination, resource-contention, queue-management, orchestra-integration]
  difficulty: advanced
  related: [03_Coordination_Patterns, 10_Strategist_Agent, 14_Metacognitive_Monitor, 15_Grounding_Scores, 16_Operational_Bounds, 19_Memory_Architecture, 20_Permission_Model, 21_Knowledge_Accretion]```

---

## Core Approach

When multiple agents compete for the same resources (tokens, compute time, human attention), equal allocation is wasteful. A task that directly serves the current strategic goal should get more resources than a maintenance task. Salience scoring makes this allocation dynamic and explicit.

**Primary function:** Allocate resources to agents/tasks based on computed relevance to current goals, not static priority.

**Key insight:** Salience is not static priority. It's a dynamic score that changes as goals shift, urgency evolves, and knowledge quality improves. What's salient now may not be salient in an hour.

**Prerequisites:** Requires KF-2 (monitor for stuck detection), KF-3 (grounding scores for quality input), and KF-4 (operational bounds for capacity tracking).

---

## Salience Formula

```yaml
salience:
  formula: goal_relevance × urgency × grounding_quality
  
  components:
    goal_relevance:
      range: 0.0 – 1.0
      definition: How directly this task serves the current primary goal
      scoring:
        1.0: Directly on critical path to primary goal
        0.8: Supports primary goal but not on critical path
        0.6: Serves secondary goal
        0.4: Maintenance/hygiene task
        0.2: Nice-to-have, no goal alignment
        0.0: No relevance to any current goal
        
    urgency:
      range: 0.0 – 1.0
      definition: Time sensitivity of this task
      scoring:
        1.0: Blocking other work right now
        0.8: Needed within current work session
        0.6: Needed today
        0.4: Needed this week
        0.2: No time pressure
        
    grounding_quality:
      range: 0.0 – 1.0
      definition: How well-grounded is the case for doing this task (from KF-3)
      scoring:
        - Based on grounding score of the evidence justifying the task
        - Well-grounded tasks (clear requirements, verified need) score high
        - Speculative tasks (unverified assumptions about need) score low
        
  example_calculations:
    - task: "Fix production SQL injection"
      goal_relevance: 1.0 (critical path — security)
      urgency: 1.0 (blocking deployment)
      grounding: 1.0 (verified by code scan)
      salience: 1.0 × 1.0 × 1.0 = 1.0
      
    - task: "Refactor auth module for readability"
      goal_relevance: 0.6 (secondary goal — code quality)
      urgency: 0.2 (no time pressure)
      grounding: 0.8 (code review confirmed need)
      salience: 0.6 × 0.2 × 0.8 = 0.096
      
    - task: "Investigate possible memory leak"
      goal_relevance: 0.8 (supports primary goal — reliability)
      urgency: 0.6 (needed today, not blocking)
      grounding: 0.4 (suspected from logs, not confirmed)
      salience: 0.8 × 0.6 × 0.4 = 0.192
```

---

## Competitive Inhibition

When multiple agents compete for the same resource, highest salience wins.

```yaml
competitive_inhibition:
  mechanism:
    - All competing tasks compute salience
    - Highest salience gets resource allocation
    - Lower-salience tasks queued or given minimum allocation
    
  tie_breaking:
    - If salience scores within 5% of each other: allocate proportionally
    - If exact tie: urgency component breaks tie (more urgent wins)
    - If still tied: goal_relevance breaks tie
    
  resource_types:
    token_budget: How many tokens an agent can consume per task
    compute_priority: Which agent runs first when queue is full
    human_attention: Which agent's output is presented to human first
    context_window: How much context an agent can claim
```

### Inhibition-first framing — spec note (7.1.0)

The Competitive Inhibition section above implements selection as amplification-first: compute salience for all competing tasks, route resources to the highest scorer. This is functionally correct.

A complementary framing — suppression-first — shifts the design question from "which task to boost" to "which tasks to silence." The distinction matters for hook design:

- **Amplification-first:** load the relevant module when routing commits
- **Suppression-first:** suppress irrelevant module attention before routing commits, let the relevant signal settle

Both produce the same allocation outcome at steady state. The difference is in where the work happens: before or after the routing decision.

**Relevance to Phase 1 pre-prompt routing hook:** The UserPromptSubmit hook (Phase 1 critical path) decides which context to load before Claude sees the prompt. Framing this as suppression (prevent irrelevant module attention from loading) rather than amplification (load relevant modules) may produce lower-overhead implementations — suppression is a gate, amplification is a loader.

**Source:** This framing note is grounded in Ng et al. (2026), "Spontaneous Activity Reshaping Hypothesis" (Psychological Review) — see `wiki/architecture/imagination-as-suppression-validates-patching.md` for the mechanism and three KF convergences.

**Status:** Spec-level observation only. Current implementation (highest salience wins) is unchanged. Revisit during Phase 1 hook design revision.

---

## Starvation Prevention

Low-salience tasks still need to execute eventually. Starvation prevention ensures no task waits indefinitely.

```yaml
starvation_prevention:
  minimum_allocation_floor:
    rule: Every queued task gets minimum 5% of available resources regardless of salience
    rationale: Prevents permanent starvation of low-priority work
    
  aging_boost:
    rule: Tasks waiting longer than N time units get salience boost
    formula: effective_salience = base_salience + (wait_time / max_wait) × aging_weight
    aging_weight: 0.2 (waiting long enough adds up to 0.2 to salience)
    max_wait: deployment_specific (e.g., 24 hours)
    
  mandatory_execution:
    rule: Any task waiting longer than max_wait executes at next opportunity
    rationale: Even low-salience tasks have a deadline for execution
```

---

## Capacity Tracking

Uses KF-4 (Operational Bounds) data to know how much capacity is available.

```yaml
capacity_tracking:
  inputs_from_operational_bounds:
    - Current context utilization per agent
    - Current cost rate vs. budget ceiling
    - Current error rate per agent
    
  allocation_decisions:
    - If total capacity at 80%+: only high-salience tasks get new allocation
    - If cost approaching ceiling: only critical-path tasks continue
    - If an agent's error rate > 15%: reduce allocation to that agent, redistribute
```

---

## Feedback Loop

Track whether high-salience tasks actually produce high-value outputs. Calibrate salience scoring over time.

```yaml
feedback_loop:
  tracking:
    per_task:
      salience_at_allocation: [computed score]
      outcome_quality: [measured post-completion]
      value_delivered: [did this actually help the goal?]
      
  calibration:
    - If high-salience tasks consistently produce low-value output → salience model is miscalibrated
    - If low-salience tasks consistently produce high-value output → salience model is missing signal
    - Adjust component weights based on historical correlation
    
  reporting:
    frequency: After every N tasks (default 20)
    output: Salience calibration report with adjustment recommendations
```

---

## TTL on Idle Agent Registrations

Agents that aren't contributing get deprioritized automatically.

```yaml
idle_pruning:
  mechanism:
    - Track last useful output per registered agent
    - Agents with no useful output in N time units get salience penalty
    - Penalty: multiply all task salience for that agent by 0.5
    - If no useful output in 2N time units: agent deregistered from active pool
    
  reactivation:
    - Deregistered agents can be reactivated on demand
    - Reactivation resets TTL clock
    - Useful to prevent resource waste on agents that were spun up speculatively
```

---

## Integration Points

### With Coordinator (03_Coordination_Patterns)

Coordinator uses salience for resource allocation during multi-agent workflows.

```yaml
coordinator_integration:
  replaces: Static priority assignment
  
  application:
    - When parallel agents compete for resources → salience determines allocation
    - When sequential chain has optional branches → salience determines which branches execute
    - When workflow has more subtasks than capacity → salience determines execution order
    
  coordinator_actions:
    - Compute salience for each pending subtask
    - Allocate resources proportional to salience (with starvation floor)
    - Re-compute salience when goals change or tasks complete
```

### With Strategist (10_Strategist_Agent)

Strategist provides goal_relevance scores and goal hierarchy that drives salience computation.

```yaml
strategist_integration:
  data_provided_by_strategist:
    - Current goal hierarchy (primary, secondary, maintenance)
    - Goal weights (if multiple primary goals)
    - Strategic context that affects relevance scoring
    
  salience_actions:
    - Strategist decision to reprioritize → all salience scores recomputed
    - New strategic goal → existing tasks re-scored for relevance
    - Goal completed → dependent tasks lose relevance, salience drops
```

### With Metacognitive Monitor (14_Metacognitive_Monitor)

Stuck detection triggers salience reallocation.

```yaml
monitor_integration:
  trigger: Monitor detects agent is stuck (ESCALATE event)
  
  salience_response:
    - Stuck agent's current task salience reduced to minimum
    - Resources freed by stuck agent redistributed to other agents
    - If stuck task was high-salience: flag for human attention
    - Stuck agent can regain salience when unstuck
```

### With Grounding Scores (15_Grounding_Scores)

Grounding quality is a direct input to salience formula.

```yaml
grounding_integration:
  - Task grounding_quality derived from KF-3 grounding scores
  - Well-grounded tasks (verified need, clear requirements) get higher salience
  - Speculative tasks (assumed need, unverified) get lower salience
  - This naturally prioritizes doing things we *know* need doing over things we *think* might
```

### With Operational Bounds (16_Operational_Bounds)

Bounds data determines available capacity for allocation.

```yaml
bounds_integration:
  - Context utilization → how much context capacity available per agent
  - Cost rate → how much budget remains for allocation
  - Error rate → reliability weighting for agent assignment
  - When bounds are tight (high utilization, near budget): only high-salience work proceeds
```

### With Orchestra

Salience integrates with Orchestra's queue prioritization.

```yaml
orchestra_integration:
  application:
    - Orchestra priority (1-10) maps to salience as a starting point
    - Salience computation enriches static priority with dynamic factors
    - High-salience tasks get priority in Orchestra queues
    - Starvation prevention applies to Orchestra queue management
```

### With Knowledge Accretion Access Logs (21_Knowledge_Accretion) (6.3.1)

Access-driven salience from wiki access logs provides a knowledge-level signal: which entries are most frequently and recently consulted. This complements the existing task-level and goal-level salience signals.

```yaml
access_log_integration:
  signal_type: "Knowledge-level salience — which wiki entries matter most right now"
  source: "wiki/.access_summary.json (Module 21 access logging rollup)"
  application:
    - Top-accessed entries inform which knowledge to surface proactively during mode activation
    - Bottom-accessed entries signal candidates for archival or deprioritization
    - Access patterns reveal which domains are currently active — use as a proxy for goal_relevance when explicit goal hierarchy is unavailable
  distinction: "Task-level salience (existing) asks 'which task matters most?' Knowledge-level salience asks 'which knowledge matters most?' Both inform resource allocation."
```

---

## Constraints

- Salience formula is a heuristic — component weights may need calibration per deployment
- Goal_relevance depends on having a current goal hierarchy (requires Strategist input)
- Grounding_quality depends on KF-3 being operational
- Competitive inhibition can over-concentrate resources — starvation prevention is essential
- Feedback loop requires task outcome measurement — not always available
- Salience recomputation has cost — don't recompute on every event, batch updates

---

## Success Criteria

- High-salience tasks complete faster than low-salience tasks
- No task starves indefinitely (starvation prevention working)
- Resources shift when goals change (salience is truly dynamic)
- Feedback loop identifies miscalibrated salience within 20 tasks
- Stuck agents release resources promptly via monitor integration
- Cost stays within bounds while prioritizing highest-value work

---

## Attribution

| Element | Source |
|---------|--------|
| SYNAPSE salience concept | PNW AGI archive — partially defined |
| Competitive inhibition algorithm | Conceptual in archive — our implementation |
| Starvation prevention with aging boost | Standard scheduling theory, applied to LLM agents |
| Feedback loop for salience calibration | Our design |

---

## Related Modules

- `03_Coordination_Patterns.md` — Uses salience for resource allocation
- `10_Strategist_Agent.md` — Provides goal hierarchy driving relevance scores
- `14_Metacognitive_Monitor.md` — Stuck detection triggers reallocation
- `15_Grounding_Scores.md` — Grounding quality input to salience
- `16_Operational_Bounds.md` — Capacity data for allocation decisions
- `19_Memory_Architecture.md` — (6.1) Routing index tracks task salience state across session turns
- `21_Knowledge_Accretion.md` — (6.3.1) Access-driven salience signal from wiki access logs
