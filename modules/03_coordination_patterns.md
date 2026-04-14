# Agent Coordination Patterns

## Module Metadata

```yaml
module:
  title: Agent Coordination Patterns
  version: 6.6.1
  purpose: Design multi-agent workflows by mapping dependencies first, then deriving the coordination pattern from the graph
  topics: [coordination, multi-agent, workflows, handoffs, orchestration, dependency-mapping, verification, capability-restriction]
  contexts: [complex-tasks, agent-teams, workflow-design]
  difficulty: advanced
  related: [01_Navigator_Agent, 02_Builder_Agent, 04_Specification_Templates, 07_Critic_Agent, 08_Synthesizer_Agent, 09_Debugger_Agent, 10_Strategist_Agent, 11_Calibrator_Agent, 14_Metacognitive_Monitor, 16_Operational_Bounds, 18_Salience_Allocation, 19_Memory_Architecture, 20_Permission_Model]
  changelog:
    6.6.1: |
      - Added coordination_handoff_schema output contract for Coordinator → Builder transfer (ERA finding F8)
      - Defines required fields: dependency_graph, pattern_name, critical_path, parallel_clusters, handoff_protocol
      - Maps to Builder's requirements input structure
      - Closes the last undocumented inter-mode handoff contract
    6.2.0: |
      - Version alignment with KF 6.2
      - Chains producing evaluative+ outputs are candidates for Knowledge Accretion (Module 21) downstream
    6.1.0: |
      - Added verification_required flag on chain outputs (D4)
      - Added capability restrictions per mode in handoff protocol (D6)
      - Added mode transition cost heuristic (D3)
      - Integrated with Memory Architecture (Module 19) for handoff context
      - Integrated with Permission Model (Module 20) for chain risk escalation
```

---

## Core Approach

Multi-agent systems fail when handoffs lose context or when agents step on each other's work. Good coordination starts with understanding what depends on what — the pattern emerges from the dependency graph, not from selecting a taxonomy entry.

**Primary challenge:** Getting agents to work together without losing information or duplicating effort.

**Key insight:** Map dependencies first, derive the pattern from the graph. Don't select a pattern then force-fit the workflow.

**Meta-principle:** This patches Sonnet's weakness (rigid pattern selection) rather than scaffolding its strength (flexible ad-hoc coordination). Raw Sonnet already combines approaches flexibly. The value-add here is *systematic* dependency analysis that prevents missed handoffs and implicit ordering assumptions.

---

## Dependency-First Workflow Design

### The Workflow Decomposition Protocol

Given a multi-agent task, derive the coordination pattern from the dependency graph rather than selecting one up front.

```yaml
workflow_decomposition:
  step_1_enumerate:
    action: List all subtasks required to complete the goal
    output: Flat list of subtasks with brief descriptions
    
  step_2_hard_dependencies:
    action: For each pair of subtasks, ask "Does A's output feed B?"
    output: Directed edges representing hard dependencies (B cannot start without A's output)
    notation: "A → B" means A must complete before B starts
    
  step_3_soft_dependencies:
    action: For each pair without hard dependency, ask "Would A's output improve B?"
    output: Dashed edges representing soft dependencies (B works without A but works better with it)
    notation: "A ⇢ B" means B benefits from A but doesn't require it
    
  step_4_draw_graph:
    action: Construct the dependency graph from steps 2-3
    output: DAG (directed acyclic graph) of subtask relationships
    validation: Check for cycles — cycles indicate task decomposition error
    
  step_5_identify_parallel_clusters:
    action: Find groups of subtasks with no hard dependencies between them
    output: Sets of parallelizable work
    
  step_6_identify_sequential_chains:
    action: Find longest paths of hard dependencies
    output: Critical path(s) that determine minimum completion time
    
  step_7_identify_coordination_points:
    action: Find nodes where multiple inputs converge
    output: Aggregation/synthesis points requiring conflict resolution
    
  step_8_derive_pattern:
    action: The graph implies the pattern — read it, don't select one
    output: Hybrid coordination pattern that matches the actual dependency structure
```

### Example: Workflow Decomposition in Practice

**Task:** Create, validate, and deploy a new agent with strategic context.

```yaml
subtasks:
  A: Strategic context assessment (Strategist)
  B: Pattern extraction from existing agents (Synthesizer)
  C: Agent specification creation (Builder)
  D: Structural review (Critic)
  E: Failure mode analysis (Debugger)
  F: Domain validation (Expert)
  G: Revision if needed (Builder)
  H: Deployment approval

hard_dependencies:
  A → C  # Builder needs strategic context
  B → C  # Builder needs patterns to apply
  C → D  # Critic needs spec to review
  C → E  # Debugger needs spec for failure analysis
  C → F  # Expert needs spec for domain validation
  D → G  # Revision needs critique
  E → G  # Revision needs failure analysis
  F → G  # Revision needs domain feedback
  G → H  # Deployment needs revised spec

soft_dependencies:
  A ⇢ B  # Synthesizer benefits from strategic context but doesn't require it

derived_pattern:
  phase_1: A and B in parallel (no hard deps between them; A ⇢ B is soft)
  phase_2: C sequential (requires both A and B outputs)
  phase_3: D, E, F in parallel (all need C, none need each other)
  phase_4: G sequential (requires D, E, F — coordination point)
  phase_5: H sequential (requires G)
  
  description: >
    Parallel start → sequential creation → parallel validation → 
    sequential revision → sequential deployment. This is a hybrid pattern 
    that was derived from the dependency graph, not selected from a menu.
```

### Coordinator → Builder Handoff Schema (6.6.1)

Formal output contract for the Coordinator → Builder handoff. Builder's `requirements` input must be populated from these fields. Absence of any required field is an incomplete coordination output — complete the analysis before handing off.

```yaml
coordination_handoff_schema:
  required_fields:
    problem_to_solve:
      type: string
      maps_to: "Builder.inputs.requirements.problem_to_solve"
      source: "Step 1 (enumerate subtasks) + user's original objective"
      description: One-sentence statement of what the completed workflow must achieve.

    dependency_graph:
      type: object
      maps_to: "Builder.inputs.requirements.integration_needs"
      source: "Steps 2–4 (graph derivation)"
      schema:
        nodes: array[string]   # Subtask or agent names
        edges:
          hard: array[tuple]   # [source, target] pairs — B cannot start without A
          soft: array[tuple]   # [source, target] pairs — B benefits from A
        cycles_detected: boolean  # Must be false — cycles indicate decomposition error
      description: The dependency graph as derived by the decomposition protocol.

    pattern_name:
      type: string
      maps_to: "Builder.inputs.requirements.constraints"
      source: "Step 8 (pattern derived from graph)"
      enum: [pipeline, parallel_cluster, hub_and_spoke, consensus, hierarchical, hybrid]
      description: Coordination pattern derived from the graph. Do not select before graphing.

    critical_path:
      type: array[string]
      maps_to: "Builder.inputs.requirements.constraints"
      source: "Step 6 (sequential chain identification)"
      description: Ordered list of agents/subtasks on the longest hard-dependency chain.

    parallel_clusters:
      type: array[array[string]]
      maps_to: "Builder.inputs.requirements.desired_outputs"
      source: "Step 5 (parallel cluster identification)"
      description: Groups of subtasks with no hard dependencies between them.

    handoff_protocol:
      type: array[object]
      maps_to: "Builder.inputs.requirements.integration_needs"
      source: "Steps 6–7 (sequential chains + convergence points)"
      schema:
        - from: string
          to: string
          dependency_type: hard | soft
          convergence_point: boolean
          context_to_carry: array[string]

  optional_fields:
    target_users:
      type: string
      maps_to: "Builder.inputs.requirements.target_users"
    success_metrics:
      type: array[string]

  validation:
    before_handing_to_builder: |
      Verify all required fields are populated.
      Verify cycles_detected is false.
      Verify pattern_name matches the graph structure (not pre-selected).
      If any required field is absent, complete the coordination analysis before handoff.
    decision_type: reckoning
```

---

## The Four Pattern Vocabulary

Sequential, Parallel, Hierarchical, and Consensus remain as **vocabulary for describing what emerged** from dependency analysis. They are not a selection menu.

### Sequential

```
A → B → C → output
```

**Emerges when:** The dependency graph shows a single chain with no parallelizable clusters.

**Rules:**
- Each agent completes fully before handoff
- Output of A becomes input of B
- Clear completion criteria at each step

### Parallel

```
      ┌→ A ─┐
input ├→ B ─┤→ Aggregator → output
      └→ C ─┘
```

**Emerges when:** The dependency graph shows a cluster of tasks with no hard dependencies between them, converging at a coordination point.

**Rules:**
- All parallel agents receive the same input (or outputs from prior sequential steps)
- Agents work independently
- Aggregator resolves differences at the coordination point

### Hierarchical

```
       Coordinator
      /     |     \
     A      B      C
```

**Emerges when:** The dependency graph is complex enough to require dynamic routing, iteration, or runtime decisions about which subtasks to execute.

**Rules:**
- Coordinator has full visibility of the graph
- Can reassign, iterate, or terminate based on intermediate results
- State lives with Coordinator

### Consensus

```
[A, B, C] ↔ deliberation ↔ unified output
```

**Emerges when:** The dependency graph shows a coordination point where multiple perspectives must be reconciled before proceeding, and the reconciliation itself is iterative.

**Rules:**
- Agents share and critique each other's outputs
- Explicit stopping condition
- Document reasoning, not just conclusion

### Hybrid Patterns

Most real workflows are hybrids. The dependency graph naturally produces them.

```yaml
hybrid_examples:
  - name: "Parallel-then-sequential"
    description: "Steps 1-3 parallel, step 4 aggregates, steps 5-6 sequential"
    emerges_when: Independent analysis followed by synthesis followed by action
    
  - name: "Sequential-with-parallel-validation"
    description: "Build sequentially, validate in parallel, revise sequentially"
    emerges_when: Creation is sequential but quality checks are independent
    
  - name: "Hierarchical-with-consensus-gates"
    description: "Coordinator manages workflow with consensus required at key decision points"
    emerges_when: Complex workflow with high-stakes decisions requiring agreement
```

---

## Common Mode Coordination Flows

### Creation with Validation

```
Builder → [Critic, Expert, Debugger] (parallel) → Builder (if revisions) → Deploy
```

```yaml
flow:
  name: creation_with_validation
  derived_from: dependency_graph
  
  dependencies:
    Builder → Critic (hard: Critic needs spec)
    Builder → Expert (hard: Expert needs spec for domain check)
    Builder → Debugger (hard: Debugger needs spec for failure analysis)
    Critic → Builder_revise (hard: revision needs critique)
    Expert → Builder_revise (hard: revision needs domain feedback)
    Debugger → Builder_revise (hard: revision needs failure analysis)
    
  pattern: sequential → parallel → sequential
  
  coordination_point:
    at: Builder_revise
    aggregation: synthesize all three validation outputs
    conflict_resolution: Critic severity ranking takes precedence for prioritization
```

### Diagnosis with Strategic Fix

```
Debugger → Strategist → Builder
```

```yaml
flow:
  name: diagnosis_with_strategic_fix
  derived_from: dependency_graph
  
  dependencies:
    Debugger → Strategist (hard: strategy needs diagnosis)
    Strategist → Builder (hard: implementation needs strategic decision)
    
  pattern: sequential (simple chain)
```

### Pattern-Driven Agent Creation

```
[Strategist, Synthesizer] (parallel) → Builder → Critic → Deploy
```

```yaml
flow:
  name: pattern_driven_creation
  derived_from: dependency_graph
  
  dependencies:
    Strategist → Builder (hard: needs strategic context)
    Synthesizer → Builder (hard: needs patterns to apply)
    Builder → Critic (hard: needs spec to review)
    
  soft_dependencies:
    Strategist ⇢ Synthesizer (context improves pattern extraction)
    
  pattern: parallel start → sequential chain
```

---

## State Management

### Context Object

```yaml
coordination_context:
  session:
    id: [unique_session_id]
    started: [timestamp]
    current_step: [where in the dependency graph]
    dependency_graph: [the derived graph]
    modes_engaged: [list of modes used]
    
  user:
    expertise_level: beginner | intermediate | advanced
    stated_goals: [explicit requests]
    inferred_goals: [underlying needs]
    constraints: [limits mentioned]
    
  task:
    objective: [end goal]
    completed: [done subtasks]
    pending: [remaining subtasks]
    blockers: [current issues]
    critical_path: [longest dependency chain]
    
  decisions:
    - decision: [what was decided]
      by: [which agent]
      reasoning: [why]
      timestamp: [when]
      reversible: true | false
      
  artifacts:
    - artifact_id: [unique_id]
      type: specification | critique | diagnosis | strategy
      created_by: [agent_id]
      version: [current version]
      status: draft | reviewed | approved
```

### Handoff Protocol

Every handoff includes:

1. **What happened** — Agent's output/conclusion
2. **What was learned** — New information discovered
3. **What to do next** — Instruction for receiving agent
4. **What context carries forward** — Relevant state
5. **Position in dependency graph** — Where this handoff sits in the overall flow

```yaml
handoff:
  from: [source_agent]
  to: [target_agent]
  
  what_happened:
    action_taken: [what source agent did]
    result: [outcome]
    confidence: [how sure]
    
  what_was_learned:
    new_information: [discoveries]
    updated_understanding: [changed beliefs]
    
  instruction:
    task: [specific action for target]
    constraints: [limits on target's work]
    expected_output: [what to return]
    
  graph_position:
    step: [current step in dependency graph]
    completed_dependencies: [what has been resolved]
    remaining_dependencies: [what still needs to happen]
    next_coordination_point: [where outputs will converge]
    
  context:
    [preserved context object]
```

---

## Automatic Adversarial Verification (6.1)

Mode chains that produce evaluative or higher output automatically include an adversarial Critic pass. This is not optional for qualifying chains.

```yaml
verification_required:
  flag: true
  
  qualifying_chains:
    - Any chain that produces a specification (Builder output)
    - Any chain that produces a strategy recommendation (Strategist output)
    - Any chain that produces an ODS organizational profile
    - Any chain of 3+ modes (compound error risk regardless of output type)
    
  verification_protocol:
    agent: Critic (adversarial variant)
    framing: "Your goal is to find the failure mode that the producing agent missed. Assume the output has at least one significant flaw."
    scope: Final chain output only (not intermediate handoffs)
    severity_filter: Report findings at severity 2+ only
    
  on_finding:
    severity_2_plus: Flag in output. Escalate risk tier per Module 20.
    no_findings: Record clean pass. Continue to delivery.
    
  yield_tracking:
    metric: "Percentage of adversarial passes that surface severity 2+ findings"
    healthy_range: 20% – 80%
    below_20: "Adversarial prompting too soft — tighten framing"
    above_80: "Artifact quality too low — flag for rebuild rather than review"
    
  skip_conditions:
    - Single-mode reckoning output (no chain, no judgment)
    - Two-mode chain where terminal output is a reckoning
    - User explicitly requests skipping verification ("just give me the draft")
```

---

## Capability Restrictions in Chains (6.1)

When modes operate as steps in a chain, each step has restricted capabilities. This prevents a sub-agent from exceeding its mandate.

```yaml
chain_capability_restrictions:
  principle: "Each mode in a chain operates with minimum required capabilities."
  
  per_mode:
    navigator:
      in_chain_role: "Route or disambiguate only"
      can_read: [user_request, routing_index]
      can_write: [routing_decision]
      cannot: [create artifacts, make decisions, produce final output]
      
    builder:
      in_chain_role: "Create artifacts within assigned scope"
      can_read: [all prior chain outputs, routing_index, patterns]
      can_write: [specification_draft, design_decisions]
      cannot: [modify other modes' outputs, approve own output]
      
    critic:
      in_chain_role: "Review artifacts — read-only on source"
      can_read: [artifact_under_review, all chain context]
      can_write: [critique_output, severity_assessments]
      cannot: [modify the source artifact]
      
    expert:
      in_chain_role: "Analyze — output findings only"
      can_read: [artifact_under_analysis, domain context]
      can_write: [analysis_output, findings]
      cannot: [modify analyzed artifacts]
      
    debugger:
      in_chain_role: "Diagnose — full read, write diagnostic output only"
      can_read: [all session context, error data]
      can_write: [diagnostic_output, root_cause_report]
      cannot: [modify artifacts, implement fixes]
      
    strategist:
      in_chain_role: "Recommend — cannot implement"
      can_read: [all session context, constraints]
      can_write: [recommendation_output, trade_off_analysis]
      cannot: [implement recommendations, modify artifacts]
      
    synthesizer:
      in_chain_role: "Extract patterns — read-only on examples"
      can_read: [examples, session context]
      can_write: [pattern_output, anti_patterns]
      cannot: [modify source examples]
      
    calibrator:
      in_chain_role: "Generate config — cannot deploy"
      can_read: [project context, stack requirements]
      can_write: [configuration_output]
      cannot: [deploy configurations]
      
  enforcement:
    - Orchestrator validates each step's output against capability profile
    - Cross-mode modification goes through orchestrator, never direct
    - Capability violation: block action, log, continue with warning
    
  reference: "Full capability profiles in 20_Permission_Model.md"
```

---

## Mode Transition Cost Heuristic (6.1)

Mode switches have a cost — they invalidate cached context and load new instructions. Factor this into chaining decisions.

```yaml
mode_transition_cost:
  principle: "A mode switch that invalidates the prompt cache should deliver proportional value."
  
  cost_factors:
    context_reload: "New mode instructions loaded into dynamic zone"
    state_swap: "Tier 2 state saved/loaded (Module 19)"
    cache_invalidation: "Dynamic zone change breaks cache suffix"
    
  decision_heuristic:
    - If the next mode's contribution is < 20% of total chain value, handle inline instead
    - If two modes have overlapping capabilities for this task, use the already-active one
    - If a Critic pass would add only formatting-level findings, skip adversarial verification
    
  examples:
    high_value_switch: "Builder → Critic: Specification review catches structural issues. Switch justified."
    low_value_switch: "Expert → Strategist for a single trivial prioritization. Handle inline."
    skip_switch: "Builder output is a simple template fill. Auto-verification would yield only low-severity findings. Skip."
```

---

## Conflict Resolution

When agents disagree at coordination points:

### Resolution Matrix

| Conflict Type | Resolution Strategy | Authority |
|---------------|---------------------|-----------|
| Factual disagreement | Check sources, weight by expertise | Expert |
| Priority disagreement | Defer to Coordinator or user | Strategist |
| Approach disagreement | Run both if feasible, compare | Synthesizer |
| Scope disagreement | Clarify with user | Navigator |
| Quality disagreement | Critic severity framework | Critic |
| Strategic disagreement | Trade-off analysis | Strategist |
| Diagnosis disagreement | Additional evidence required | Debugger |

### Resolution Protocol

```yaml
conflict_resolution:
  detection:
    trigger: Outputs from parallel agents contradict or are incompatible at coordination point
    
  process:
    1. Classify conflict type (factual / priority / approach / scope / quality / strategic / diagnostic)
    2. Route to authority agent for resolution
    3. If authority agent is one of the conflicting agents, escalate to Coordinator or user
    4. Document resolution reasoning
    5. Update dependency graph if conflict reveals new dependencies
```

---

## Integration with KF-2 (Metacognitive Monitor)

Coordinator monitors agent execution in real-time via the Metacognitive Monitor.

```yaml
monitor_integration:
  trigger: During any coordinated workflow execution
  
  capabilities:
    - Detect when an agent is stuck (circular reasoning, context overflow)
    - Receive intervention signals (COMPRESS_CONTEXT, SWITCH_STRATEGY, ESCALATE)
    - Reassign subtasks when agent fails
    - Interrupt and redirect based on monitor signals
    
  escalation_path:
    monitor_detects_failure → Coordinator receives signal → 
    Coordinator reassigns or terminates subtask → 
    Workflow continues with fallback plan
```

## Integration with KF-7 (Salience Allocation)

When multiple agents compete for resources, Coordinator uses salience scoring instead of static priority.

```yaml
salience_integration:
  trigger: Resource contention between agents in parallel execution
  
  application:
    - Compute salience for each competing agent's subtask
    - Highest salience wins resource allocation
    - Starvation prevention: minimum allocation floor for all queued subtasks
    - Log allocation decisions for post-workflow analysis
```

---

## Communication Protocol

Standard message format between agents:

```yaml
message:
  id: [unique_message_id]
  timestamp: [iso_datetime]
  
  routing:
    from: [source_agent_id]
    to: [target_agent_id]
    conversation_id: [thread tracker]
    graph_position: [step in dependency graph]
    
  type: request | response | notification | error
  
  content:
    action: [what to do (for requests)]
    result: [what was done (for responses)]
    data: [relevant payload]
    
  metadata:
    priority: normal | high | urgent
    timeout: [seconds]
    retry_policy: none | once | exponential
    mode: [current mode]
    decision_type: reckoning | evaluative | predictive | novel
```

---

## Example: Full-Cycle Agent Development

**Task:** Create, validate, and deploy a new agent with quality assurance.

**Step 1: Enumerate subtasks**
```
A: Assess strategic context (Strategist)
B: Extract applicable patterns (Synthesizer)
C: Create specification (Builder)
D: Structural review (Critic)
E: Failure mode analysis (Debugger)
F: Domain validation (Expert)
G: Revise specification (Builder)
H: Final approval
```

**Step 2-3: Map dependencies**
```
Hard: A → C, B → C, C → D, C → E, C → F, D → G, E → G, F → G, G → H
Soft: A ⇢ B
```

**Step 4: Draw graph**
```
    A ──┐
        ├──→ C ──→ ┌ D ─┐
    B ──┘           │ E ─┤──→ G ──→ H
                    └ F ─┘
```

**Step 5: Parallel clusters**
```
Cluster 1: {A, B} — no hard deps between them
Cluster 2: {D, E, F} — no hard deps between them
```

**Step 6: Sequential chains**
```
Critical path: A → C → D → G → H (or A → C → E → G → H, or A → C → F → G → H)
All paths through C and G are equally critical.
```

**Step 7: Coordination points**
```
C: Receives from A and B (must aggregate before proceeding)
G: Receives from D, E, and F (must aggregate all validation feedback)
```

**Step 8: Derived pattern**
```
Parallel(A,B) → Sequential(C) → Parallel(D,E,F) → Sequential(G) → Sequential(H)
```

This is a hybrid pattern — not forced into one taxonomy entry.

---

## Next Steps

1. **Map your workflow's dependencies** → Use the decomposition protocol
2. **Derive the pattern** → Read the graph, don't select from a menu
3. **Define coordination points** → Where do outputs converge?
4. **Plan conflict resolution** → How will disagreements at coordination points be handled?
5. **Design handoffs** → Customize context for your domain
6. **Build agents** → `02_Builder_Agent.md` for each specialist
7. **Test the full flow** → Simulate the complete dependency graph

---

## Related Modules

- `01_Navigator_Agent.md` — Disambiguation before coordination begins
- `02_Builder_Agent.md` — Creating specialist agents
- `04_Specification_Templates.md` — Standard formats for coordination configs
- `07_Critic_Agent.md` — Quality validation at coordination points + adversarial verification in chains
- `08_Synthesizer_Agent.md` — Pattern extraction across agent teams
- `09_Debugger_Agent.md` — Diagnosis within coordinated systems
- `10_Strategist_Agent.md` — Strategic decisions for coordination
- `11_Calibrator_Agent.md` — Project setup flows
- `14_Metacognitive_Monitor.md` — Real-time agent failure detection during coordination
- `18_Salience_Allocation.md` — Dynamic resource allocation for competing agents
- `19_Memory_Architecture.md` — (6.1) Routing index for handoff context preservation
- `20_Permission_Model.md` — (6.1) Chain risk escalation and capability restriction enforcement
