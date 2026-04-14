# Specification Templates

## Module Metadata

```yaml
module:
  title: Specification Templates
  version: 6.6.0
  purpose: Provide complete, reusable templates for agents, processes, and coordination
  topics: [templates, specifications, formats, schemas, capability-profiles, risk-tiers, infrastructure-architecture, hosting-audit, era-specification]
  contexts: [agent-creation, process-design, documentation, infrastructure-planning, entity-modeling]
  difficulty: intermediate
  related: [02_Builder_Agent, 03_Coordination_Patterns, 05_Expert_Agent_Example, 07_Critic_Agent, 08_Synthesizer_Agent, 09_Debugger_Agent, 10_Strategist_Agent, 11_Calibrator_Agent, 12_Calibration_Layer, 13_Decision_Classification, 14_Metacognitive_Monitor, 15_Grounding_Scores, 17_Temporal_Knowledge, 19_Memory_Architecture, 20_Permission_Model, 21_Knowledge_Accretion]
  changelog:
    6.6.0: |
      - Added ERA Specification Template (Expert ERA → Builder chain)
      - Added ERA row to Usage Notes template table
      - Added KF 6.6 field summary table
      - Added era-specification to topics
    6.3.0: |
      - Added Infrastructure Architecture Specification template (Expert → Builder chain, infrastructure domain)
      - Added Hosting Audit & Decomposition Readiness template (Critic audit variant)
      - Added KF 6.3 field summary table
    6.2.0: |
      - Added accretion_candidate field to output specs (Module 21 integration)
      - Added KF 6.2 field summary table entry
      - Added 21_Knowledge_Accretion to related modules
    6.1.0: |
      - Added capabilities_when_subagent field to agent spec (D6)
      - Added risk_tier field to agent spec (D5)
      - Added verification_required field to chain output specs
      - Updated KF field summary table for new modules
```

---

## Core Approach

A specification is complete when another agent or human can implement it without asking clarifying questions. These templates ensure nothing is forgotten.

**KF 6.0 additions:** Templates now include decision type metadata (KF-5), testability/calibration fields (KF-1), grounding scores (KF-3), monitor integration (KF-2), temporal metadata (KF-6), and dependency graph fields (Coordinator). Fields marked `# NEW 6.0` below.

**KF 6.1 additions:** Templates now include sub-agent capability profiles (Module 20), risk tier classification (Module 20), and verification flags (Module 03). Fields marked `# NEW 6.1` below.

**KF 6.3 additions:** Two new infrastructure planning templates: Infrastructure Architecture Specification (created by Expert → Builder chain) and Hosting Audit & Decomposition Readiness (created by Critic audit variant). Fields marked `# NEW 6.3` below.

**KF 6.6 additions:** ERA Specification Template — structured entity graph output from Expert (ERA) → Builder chain. Captures entities, relationships, cardinality, and adversarial findings including implicit entities and undocumented couplings. Fields marked `# NEW 6.6` below.

---

## Agent Specification Template

```yaml
agent:
  # IDENTITY
  id: [unique-identifier]  # e.g., "navigator-001"
  name: [Human-readable name]
  version: [semantic version]  # e.g., "1.0.0"
  
  # PURPOSE (one sentence)
  purpose: [What specific problem does this agent solve?]
  
  # CAPABILITIES
  capabilities:
    primary:  # Core functions — what it MUST do
      - [capability_1]
      - [capability_2]
    secondary:  # Supporting functions — what helps it do the core
      - [capability_3]
      - [capability_4]
    domains:  # Knowledge areas
      - [domain_1]
      - [domain_2]
      
  # INPUTS
  inputs:
    - name: [input_name]
      type: string | number | boolean | object | array
      required: true | false
      description: [What this is and where it comes from]
      grounding_score: [0.0-1.0]  # NEW 6.0 — expected grounding of this input (KF-3)
      schema:  # If object or array
        [field]: [type]
      validation:  # Optional
        [rule]: [value]
        
  # OUTPUTS
  outputs:
    - name: [output_name]
      type: response | artifact | action | notification
      format: json | markdown | code | yaml
      structure:
        [field]: [type and description]
      grounding_expectation: [minimum grounding score for output claims]  # NEW 6.0 (KF-3)
      examples:
        - [example output]
        
  # DESIGN DECISIONS                    # NEW 6.0 section (KF-5)
  design_decisions:
    - decision: [what was decided]
      decision_type: reckoning | evaluative_judgment | predictive_judgment | novel_judgment
      locked: true | false              # reckonings are locked; judgments may be revisited
      rationale: [why — depth matches decision_type]
      # reckoning: no rationale needed (it's a fact)
      # evaluative: brief rationale (criteria-based)
      # predictive: assumptions documented
      # novel: expanded rationale + flag for monitoring
        
  # CONSTRAINTS (what it CANNOT do)
  constraints:
    - [explicit_boundary_1]
    - [explicit_boundary_2]
    - [resource_limit]
    - [scope_restriction]
    
  # INTEGRATION
  integration:
    receives_from:
      - agent_id: [source_agent]
        message_types: [what it receives]
    sends_to:
      - agent_id: [target_agent]
        message_types: [what it sends]
    coordination: sequential | parallel | hierarchical | consensus | hybrid  # NEW 6.0 — hybrid added
    
  # MONITORING                          # NEW 6.0 section (KF-2)
  monitoring:
    primary_risk: circular_reasoning | context_overflow | confidence_degradation
    secondary_risk: [second most likely failure mode]
    threshold_overrides:                # Optional — override defaults for this agent
      confidence_floor: [0.0-1.0]
      max_strategy_switches: [number]
      
  # CAPABILITIES WHEN SUB-AGENT         # NEW 6.1 section (Module 20)
  capabilities_when_subagent:
    read: [what this agent can read when operating as a chain step]
    write: [what this agent can write — typically only its own output type]
    create: [what artifacts this agent can create]
    modify: [what this agent can modify — typically nothing except own output]
    escalate: [conditions requiring orchestrator approval]
    restriction: [plain-language summary of boundaries]
    
  # RISK TIER                           # NEW 6.1 section (Module 20)
  risk_tier:
    base_tier: LOW | MEDIUM | HIGH       # Based on decision type of typical output
    chain_escalation: true | false       # Does chain participation escalate tier?
    domain_escalation:                   # Domain-specific overrides
      - condition: [when this applies]
        tier: [escalated tier]
    verification_required: true | false  # Does output require adversarial verification in chains?
    
  # ERROR HANDLING
  error_handling:
    - condition: [what could go wrong]
      response: [what agent does]
      escalation: [where to route if unresolvable]
      
  # SUCCESS CRITERIA
  success_criteria:
    - [measurable_outcome_1]
    - [measurable_outcome_2]
    
  # TESTABILITY                         # NEW 6.0 section (KF-1)
  testability:
    evaluation_criteria:
      - criterion: [measurable quality dimension]
        scoring_method: [how to score 1-10]
        expected_variance: low | moderate | high  # Variance expectation for multi-run calibration
    calibration_guidance: >
      "To evaluate this spec, score against the above criteria across 3 runs.
      Stable scores (σ < 0.3) indicate robust quality."
    
  # METADATA
  metadata:
    created: [date]
    author: [who created this]
    last_updated: [date]
    status: draft | active | deprecated
    pattern_applied: [if created from pattern]
    validated_by: [critic review status]
```

---

## System Prompt Template

```markdown
# [Agent Name]

## Purpose
[One sentence: what problem does this agent solve?]

## Capabilities
[Bullet list of specific actions this agent performs]
- [Action 1]
- [Action 2]
- [Action 3]

## Constraints
[Explicit boundaries — what this agent does NOT do]
- Do not [boundary 1]
- Do not [boundary 2]
- [Scope restriction]

## Response Patterns

**For [request type 1]:**
[Structure of response]

**For [request type 2]:**
[Structure of response]

## Integration

**Receives from:**
- [Agent]: [What to expect]

**Sends to:**
- [Agent]: [What to deliver]

**Handoff format:**
[Message structure for agent communication]

## Examples

**Input:** [Example request]
**Output:** [Example response]

---

**Input:** [Another example]
**Output:** [Corresponding response]
```

---

## Critique Template (For Critic Agent)

```yaml
critique:
  # IDENTITY
  id: [unique-critique-id]
  artifact_reviewed: [artifact id or name]
  reviewer: critic-001
  timestamp: [iso_datetime]
  
  # SUMMARY
  summary:
    overall_assessment: ready_for_implementation | needs_revision | major_gaps
    risk_level: critical | high | medium | low
    finding_count:
      critical: [number]
      high: [number]
      medium: [number]
      low: [number]
    calibration:                         # NEW 6.0 (KF-1)
      runs: [N — number of evaluation runs]
      overall_stability: stable | moderate | unstable
  
  # FINDINGS
  critical_gaps:  # Blocks implementation
    - id: [finding_id]
      title: [short description]
      location: [specific section/line]
      issue: [what's missing or wrong]
      impact: [why this blocks implementation]
      fix: [specific remediation]
      decision_type: reckoning | evaluative_judgment  # NEW 6.0 (KF-5)
      confidence: [σ=X, N=Y]            # NEW 6.0 (KF-1) — severity stability across runs
      grounding: [0.0-1.0]              # NEW 6.0 (KF-3) — how grounded is the evidence
      
  high_priority:  # Significant problems
    - id: [finding_id]
      title: [short description]
      location: [specific section/line]
      problem: [what's wrong]
      risk: [what could happen]
      fix: [specific remediation]
      decision_type: reckoning | evaluative_judgment  # NEW 6.0
      confidence: [σ=X, N=Y]            # NEW 6.0
      grounding: [0.0-1.0]              # NEW 6.0
      
  medium_priority:  # Notable improvements
    - id: [finding_id]
      # same structure as high_priority
      
  low_priority:  # Minor enhancements
    - id: [finding_id]
      # same structure
  
  # ANALYSIS
  contradictions:
    - description: [contradiction description]
      location_1: [where first statement appears]
      location_2: [where contradicting statement appears]
      conflict: [how they contradict]
      resolution: [how to reconcile]
      
  unstated_assumptions:
    - assumption: [what's being assumed]
      location: [where assumption is implicit]
      risk: [what happens if assumption is false]
      recommendation: [how to make explicit]
      
  edge_cases:
    - scenario: [edge case description]
      current_handling: [what spec says or doesn't say]
      recommended_handling: [what should happen]
      suggested_addition: [where and how to address]
  
  # BIAS CHECKS                         # NEW 6.0 section (KF-1)
  bias_checks:
    label_bias:
      tested: true | false
      detected: true | false
      method: [name_stripping | N/A]
    verbosity_bias:
      tested: true | false
      detected: true | false
      mitigation: [if detected, what was adjusted]
    position_bias:
      tested: true | false
      detected: true | false
  
  # POSITIVES
  working_well:
    - [strength_1]
    - [strength_2]
    
  # RECOMMENDATIONS
  recommendations_prioritized:
    1. [highest priority fix]
    2. [second priority fix]
    3. [third priority fix]
```

---

## Synthesis Template (For Synthesizer Agent)

```yaml
synthesis:
  # IDENTITY
  id: [unique-synthesis-id]
  topic: [domain or topic area]
  synthesizer: synthesizer-001
  timestamp: [iso_datetime]
  
  # SOURCES
  sources_analyzed:
    - source_id: [id]
      type: [agent-spec | process | code | research]
      description: [brief description]
      
  # EXECUTIVE SUMMARY
  summary: [One paragraph: what patterns emerged and what they enable]
  
  # PATTERNS
  patterns:
    - name: [descriptive pattern name]
      structure: [core elements defining this pattern]
      confidence: [σ=X, N=Y, across Z examples]  # NEW 6.0 (KF-1)
      when_to_use:
        - [condition_1]
        - [condition_2]
      when_not_to_use:
        - [anti-condition_1]
        - [anti-condition_2]
      examples_from_sources:
        - source: [source_id]
          manifestation: [how pattern appears]
      variation_points:
        - [what can be customized]
      temporal_context:                  # NEW 6.0 (KF-6)
        first_observed: [when pattern first appeared]
        stability: stable | evolving | emerging | declining
        domain_scope: universal | domain-specific | era-specific
        
  # FRAMEWORK
  unifying_framework:
    core_principle: [deep insight connecting patterns]
    decision_tree:
      - condition: [if this]
        pattern: [use this pattern]
    pattern_relationships:
      - patterns: [pattern_a, pattern_b]
        relationship: complementary | sequential | alternatives
        reasoning: [why]
        
  # ANTI-PATTERNS (strengthened in 6.0 — mandatory, one per pattern minimum)
  anti_patterns:
    - name: [anti-pattern name]
      for_pattern: [which pattern this is the anti-pattern of]  # NEW 6.0
      looks_like: [how it manifests]
      why_fails: [consequence]
      failure_example: [specific scenario demonstrating the failure]  # NEW 6.0 — required
      instead: [correct approach]
      
  # ABSTRACTION LEVELS
  abstraction_ladder:
    meta: [highest level principle]
    abstract: [general patterns]
    intermediate: [pattern compositions]
    concrete: [specific examples]
    
  # APPLICABILITY
  applicability:
    applies_to: [explicit scope]
    does_not_apply_to: [explicit exclusions]
    open_questions: [areas needing refinement]
    
  # VALIDATION
  validation:
    - source: [source_id]
      patterns_found: [list]
      status: validated | partial | exception
```

---

## Diagnosis Template (For Debugger Agent)

```yaml
diagnosis:
  # IDENTITY
  id: [unique-diagnosis-id]
  problem_name: [short description]
  debugger: debugger-001
  timestamp: [iso_datetime]
  
  # PROBLEM SUMMARY
  problem:
    expected_behavior: [what should happen]
    actual_behavior: [what is happening]
    symptoms:
      - [observable symptom 1]
      - [observable symptom 2]
    context:
      frequency: [how often]
      environment: [where]
      history: [what changed recently]
    attempted_fixes:
      - [what was tried]
      - [result]
      
  # MONITOR DATA                        # NEW 6.0 section (KF-2)
  monitor_data:
    checks_triggered:
      - check: circular_reasoning | context_overflow | confidence_degradation | none
        detail: [what the monitor observed, if anything]
    interventions_applied:
      - strategy: CONTINUE | FLAG_UNCERTAINTY | COMPRESS_CONTEXT | SWITCH_STRATEGY | ASK_CLARIFICATION | ESCALATE
        detail: [what was done]
    stuck_detected: true | false
      
  # HYPOTHESES
  hypotheses:
    - id: [hypothesis_id]
      description: [what could cause this]
      probability: [high | medium | low]
      test_cost: [easy | medium | hard]
      priority: [1-N based on probability/cost matrix]
      status: pending | tested | eliminated | confirmed
      
  # DIAGNOSTIC TESTS
  tests:
    - id: [test_id]
      hypothesis_tested: [hypothesis_id]
      test_description: [what to check]
      prediction_if_true: [expected observation]
      prediction_if_false: [expected observation]
      actual_result: [what was observed]
      conclusion: [supports | refutes | inconclusive]
      
  # ROOT CAUSE
  root_cause:
    description: [identified root cause]
    confidence: [0.0-1.0]
    calibrated_confidence: [σ=X, N=Y]   # NEW 6.0 (KF-1) — multi-run stability
    grounding: [0.0-1.0]                # NEW 6.0 (KF-3) — evidence trust level
    evidence:
      - [supporting evidence 1]
      - [supporting evidence 2]
    causal_chain: [sequence from cause to symptoms]
    eliminated_hypotheses:
      - hypothesis: [id]
        reason: [why eliminated]
        
  # TEMPORAL CONTEXT                    # NEW 6.0 section (KF-6)
  temporal_context:
    first_occurrence: [when problem first appeared]
    related_changes: [what changed around that time]
    recurrence_pattern: [if recurring, what's the pattern]
    knowledge_diff: [what was known before vs. after the error]
        
  # VERIFICATION
  verification:
    steps:
      - [step to confirm diagnosis]
    expected_results: [what confirms diagnosis]
    
  # REMEDIATION
  fix:
    immediate:
      action: [what to do now]
      expected_outcome: [result]
      verification: [how to confirm]
    long_term:
      action: [systemic fix]
      rationale: [why this prevents recurrence]
      
  # PREVENTION
  prevention:
    monitoring:
      - [what to monitor]
    process_changes:
      - [what to change]
    documentation:
      - [what to document]
```

---

## Strategic Decision Template (For Strategist Agent)

```yaml
strategic_decision:
  # IDENTITY
  id: [unique-decision-id]
  decision_type: prioritization | sequencing | build_buy_defer | architectural
  decision_classification: reckoning | evaluative_judgment | predictive_judgment | novel_judgment  # NEW 6.0 (KF-5)
  strategist: strategist-001
  timestamp: [iso_datetime]
  time_horizon: immediate | short-term | medium-term | long-term
  
  # CONTEXT
  context:
    goals:
      - goal: [goal description]
        priority: [1-N]
        weight: [0.0-1.0]
    constraints:
      - [resource constraint]
      - [time constraint]
      - [technical constraint]
    current_state: [where we are now]
    stakeholders:
      - [who cares and their priority]
      
  # OPTIONS ANALYZED
  options:
    - id: [option_id]
      name: [option name]
      description: [what this option entails]
      decision_type: reckoning | evaluative_judgment | predictive_judgment | novel_judgment  # NEW 6.0 (KF-5) — per option
      alignment:
        - goal: [goal_id]
          score: [high | medium | low]
          reasoning: [why]
      costs:
        direct: [time, money, resources]
        opportunity: [what else could be done]
        switching: [if we change later]
      benefits:
        immediate: [value delivered]
        strategic: [positioning]
        capability: [what we learn/build]
      risks:
        - risk: [what could go wrong]
          probability: [low | medium | high]
          impact: [low | medium | high]
          mitigation: [how to reduce]
      dependencies:
        requires: [what must happen first]
        enables: [what becomes easier]
        
  # TRADE-OFF ANALYSIS
  trade_offs:
    matrix:
      # Options as rows, goals as columns, scores as cells
    pareto_analysis: [which options are dominated, which are frontier]
    key_trade_offs:
      - choice: [option A vs option B]
        gains: [what A provides over B]
        sacrifices: [what B provides over A]
        decision_factor: [what tips the balance]
        
  # CALIBRATED RANKING                  # NEW 6.0 section (KF-1)
  calibrated_ranking:
    runs: [N]
    rankings:
      - option: [option_id]
        mean_score: [X]
        std_dev: [σ]
        rank_stability: [ranked #N in M of N runs]
    overall_stability: stable | moderate | unstable
    bias_checks:
      position_bias: tested | not_tested
      label_bias: tested | not_tested
    close_calls:
      - options: [option_A, option_B]
        note: [why these are close — rankings swap across runs]
        
  # RECOMMENDATION
  recommendation:
    selected_option: [option_id]
    rationale:
      - [reason 1]
      - [reason 2]
    optimizes_for:
      - [what this choice prioritizes]
    sacrifices:
      - [what this choice gives up]
    why_acceptable: [why trade-off makes sense now]
    confidence: [σ=X, N=Y]              # NEW 6.0 (KF-1)
    
  # REVERSIBILITY
  reversibility:
    score: [low | medium | high]
    sunk_cost: [already invested]
    switching_cost: [to change course]
    decision_checkpoints:
      - trigger: [when to reassess]
        signal: [what would indicate need to reverse]
        
  # SEQUENCING (if multiple items)
  sequencing:
    phases:
      - phase: [phase number/name]
        items: [what to do]
        duration: [estimated time]
        deliverable: [what's produced]
        success_criteria: [how to know it's done]
    dependencies:
      - item: [item_id]
        depends_on: [prerequisite_id]
    rationale: [why this sequence]
    
  # RISK ANALYSIS
  risks:
    - id: [risk_id]
      description: [what could go wrong]
      probability: [percentage or category]
      impact: [severity]
      mitigation: [how to reduce]
      fallback: [if risk materializes]
      
  # SUCCESS METRICS
  success_metrics:
    - timeframe: [when to measure]
      metric: [what to measure]
      target: [success threshold]
      failure_signal: [when to worry]
      
  # DECISION FRAMEWORK
  decision_framework:
    for_similar_decisions:
      - condition: [when this applies]
        recommendation: [what to choose]
    heuristics:
      - [decision rule for quick reference]
```

---

## Process Specification Template

```yaml
process:
  # IDENTITY
  id: [unique-identifier]
  name: [Human-readable name]
  version: [semantic version]
  
  # PURPOSE
  purpose: [Why this process exists]
  
  # TRIGGER
  trigger:
    type: event | schedule | request | condition
    source: [where trigger comes from]
    condition: [when this fires]
    
  # INPUTS
  inputs:
    - name: [input_name]
      type: [type]
      source: [where it comes from]
      required: true | false
      
  # DEPENDENCY GRAPH                    # NEW 6.0 section (Coordinator)
  dependency_graph:
    hard_dependencies:                  # A's output feeds B — B cannot start without A
      - from: [step_id]
        to: [step_id]
    soft_dependencies:                  # A's output improves B — B works without but better with
      - from: [step_id]
        to: [step_id]
    parallel_clusters:                  # Groups of steps with no hard deps between them
      - [step_id, step_id, ...]
    critical_path: [longest hard dependency chain]
    coordination_points:                # Where multiple inputs converge
      - step: [step_id]
        inputs_from: [step_ids]
        aggregation: synthesize | vote | weighted | first-valid
      
  # STEPS
  steps:
    - id: step_1
      name: [Human-readable step name]
      agent: [agent_id that performs this]
      mode: navigator | builder | coordinator | expert | critic | synthesizer | debugger | strategist | calibrator
      action: [what happens]
      decision_type: reckoning | evaluative_judgment | predictive_judgment | novel_judgment  # NEW 6.0 (KF-5)
      inputs:
        - [from trigger or previous steps]
      outputs:
        - name: [output_name]
          type: [type]
      success_criteria: [how we know this step succeeded]
      error_handling:
        on_failure: retry | skip | abort | escalate
        max_retries: [number]
        fallback: [alternative action]
        
    - id: step_2
      # ... same structure
      depends_on: [step_1]  # Explicit dependency
      
  # BRANCHING (if needed)
  branches:
    - condition: [when this branch activates]
      steps: [step_ids to execute]
      
  # MONITORING                          # NEW 6.0 section (KF-2)
  monitoring:
    per_step:
      - step: [step_id]
        primary_risk: [most likely failure mode]
    escalation_path: [where ESCALATE signals go]
      
  # COMPLETION
  completion:
    success_criteria:
      - [overall success condition 1]
      - [overall success condition 2]
    outputs:
      - name: [final_output]
        type: [type]
        destination: [where it goes]
    next_steps:
      - [what happens after this process]
      
  # METADATA
  metadata:
    estimated_duration: [time]
    created: [date]
    owner: [responsible party]
```

---

## Message Template

```yaml
message:
  # ROUTING
  id: [unique_message_id]
  conversation_id: [thread_identifier]
  timestamp: [iso_datetime]
  
  from: [source_agent_id]
  to: [target_agent_id]
  
  # TYPE
  type: request | response | notification | error
  priority: low | normal | high | urgent
  mode: navigator | builder | coordinator | expert | critic | synthesizer | debugger | strategist | calibrator
  decision_type: reckoning | evaluative_judgment | predictive_judgment | novel_judgment  # NEW 6.0 (KF-5)
  
  # CONTENT
  content:
    # For requests:
    action: [what to do]
    parameters:
      [param]: [value]
    context:
      [relevant_state]
    expected_response:
      format: [expected format]
      deadline: [when needed]
      
    # For responses:
    status: success | partial | failure
    result:
      [output_data]
    confidence: [0.0-1.0]
    grounding: [0.0-1.0]                # NEW 6.0 (KF-3)
    next_suggested: [follow-up action if any]
    
    # For errors:
    error_code: [code]
    error_message: [human-readable description]
    recovery_options:
      - [option_1]
      - [option_2]
      
  # METADATA
  metadata:
    timeout: [seconds]
    retry_count: [number]
    trace_id: [for debugging]
    graph_position: [step in dependency graph]  # NEW 6.0 (Coordinator)
```

---

## Handoff Template

```yaml
handoff:
  # ROUTING
  id: [unique_handoff_id]
  timestamp: [iso_datetime]
  
  from: [source_agent_id]
  from_mode: [mode that completed]
  to: [target_agent_id]
  to_mode: [mode being activated]
  return_to: [agent_id | "user" | "none"]
  
  # WHAT HAPPENED
  source_action:
    task_completed: [what source agent did]
    result: [outcome]
    confidence: [0.0-1.0]
    grounding: [0.0-1.0]                # NEW 6.0 (KF-3) — how grounded is the result
    
  # WHAT WAS LEARNED
  discoveries:
    new_information:
      - [discovery_1]
      - [discovery_2]
    updated_understanding:
      - [changed_belief_1]
    open_questions:
      - [question_1]
      
  # INSTRUCTION FOR TARGET
  instruction:
    task: [specific action required]
    decision_type: reckoning | evaluative_judgment | predictive_judgment | novel_judgment  # NEW 6.0 (KF-5)
    reasoning_budget: minimal | moderate | significant | maximum                           # NEW 6.0 (KF-5)
    constraints:
      - [limit_1]
      - [limit_2]
    expected_output:
      format: [format]
      structure: [schema]
    deadline: [if applicable]
    
  # GRAPH POSITION                      # NEW 6.0 section (Coordinator)
  graph_position:
    step: [current step in dependency graph]
    completed_dependencies: [what has been resolved]
    remaining_dependencies: [what still needs to happen]
    next_coordination_point: [where outputs will converge]
    
  # PRESERVED CONTEXT
  context:
    original_request: [what started this]
    user_expertise: beginner | intermediate | advanced
    goals:
      stated: [explicit goals]
      inferred: [likely goals]
    constraints: [user-mentioned limits]
    decisions_made:
      - decision: [what]
        by: [who]
        reasoning: [why]
        decision_type: reckoning | evaluative_judgment | predictive_judgment | novel_judgment  # NEW 6.0
        reversible: true | false
    chain_position: [step X of Y]
    modes_engaged: [list of modes used so far]
```

---

## Context Object Template

```yaml
context:
  # SESSION
  session:
    id: [unique_session_id]
    started: [timestamp]
    current_phase: [where we are]
    modes_engaged: [navigator, builder, critic, ...]
    dependency_graph:                    # NEW 6.0 (Coordinator)
      hard_deps: [list of A → B edges]
      parallel_clusters: [groups]
      critical_path: [longest chain]
    
  # USER
  user:
    expertise_level: beginner | intermediate | advanced
    expertise_signals:
      - [signal that indicated level]
    stated_goals:
      - [explicit request 1]
      - [explicit request 2]
    inferred_goals:
      - goal: [what we think they need]
        confidence: [0.0-1.0]
        signal: [why we think this]
    constraints:
      - [limit_1]
      - [limit_2]
    preferences:
      format: [preferred output format]
      depth: [preferred detail level]
      
  # TASK
  task:
    objective: [end goal]
    completed:
      - step: [what was done]
        by: [which agent]
        mode: [which mode]
        when: [timestamp]
    pending:
      - step: [what remains]
        assigned_to: [agent or unassigned]
        decision_type: [reckoning | evaluative | predictive | novel]  # NEW 6.0 (KF-5)
    blockers:
      - issue: [what's blocking]
        since: [timestamp]
        
  # DECISIONS
  decisions:
    - id: [decision_id]
      decision: [what was decided]
      by: [agent_id]
      mode: [mode that made decision]
      decision_type: reckoning | evaluative_judgment | predictive_judgment | novel_judgment  # NEW 6.0
      reasoning: [why]
      timestamp: [when]
      reversible: true | false
      affects: [what this decision impacts]
      
  # ARTIFACTS
  artifacts:
    - id: [artifact_id]
      type: specification | critique | synthesis | diagnosis | strategy
      created_by: [agent_id]
      mode: [mode that created]
      version: [current version]
      status: draft | reviewed | approved
      grounding_score: [0.0-1.0]         # NEW 6.0 (KF-3)
      
  # MONITOR STATE                       # NEW 6.0 section (KF-2)
  monitor:
    active_checks: [which checks are running]
    recent_interventions:
      - intervention: [type]
        timestamp: [when]
        resolved: true | false
    current_strategy_level: DIRECT_ANSWER | DECOMPOSE | SEARCH | VERIFY | ESCALATE
```

---

## Assessment Template

```yaml
assessment:
  # WHAT WE'RE TESTING
  agent_id: [agent being assessed]
  version: [version tested]
  assessed_by: [who conducted assessment]
  date: [when]
  
  # CALIBRATION                         # NEW 6.0 section (KF-1)
  calibration:
    runs_per_scenario: [N]
    overall_stability: stable | moderate | unstable
    bias_checks_performed:
      - position_bias: [tested/not_tested, detected/not_detected]
      - label_bias: [tested/not_tested, detected/not_detected]
      - verbosity_bias: [tested/not_tested, detected/not_detected]
    bias_adjustments_applied: [list of adjustments, if any]
  
  # SUCCESS CRITERIA
  success_criteria:
    - criterion: [measurable outcome]
      target: [specific threshold]
      actual: [measured result]
      std_dev: [σ across N runs]         # NEW 6.0
      passed: true | false
      stability: stable | moderate | unstable  # NEW 6.0
      
  # TEST SCENARIOS
  test_scenarios:
    - id: scenario_1
      name: [Human-readable name]
      description: [what this tests]
      test_type: strength | boundary | weakness  # NEW 6.0 — Calibench categories
      input: [example input]
      expected_output: [what should happen]
      actual_output: [what did happen]
      passed: true | false
      mean_score: [across N runs]        # NEW 6.0
      std_dev: [σ]                       # NEW 6.0
      notes: [observations]
      
  # FAILURE MODES
  failure_modes:
    - mode: [type of failure]
      condition: [what triggers it]
      frequency: rare | occasional | frequent
      severity: low | medium | high | critical
      severity_confidence: [σ=X, N=Y]   # NEW 6.0 (KF-1)
      mitigation: [how to handle]
      
  # QUALITY METRICS
  quality_metrics:
    relevance:
      score: [0-10]
      std_dev: [σ across N runs]         # NEW 6.0
      notes: [observations]
    completeness:
      score: [0-10]
      std_dev: [σ]                       # NEW 6.0
      notes: [observations]
    accuracy:
      score: [0-10]
      std_dev: [σ]                       # NEW 6.0
      notes: [observations]
    actionability:
      score: [0-10]
      std_dev: [σ]                       # NEW 6.0
      notes: [observations]
      
  # SUMMARY
  summary:
    overall_status: pass | fail | conditional
    calibrated_confidence: [σ=X, N=Y — stability of overall assessment]  # NEW 6.0
    strengths:
      - [strength_1]
      - [strength_2]
    weaknesses:
      - [weakness_1]
      - [weakness_2]
    recommendations:
      - [recommendation_1]
      - [recommendation_2]
```

---

## AI Coder Configuration Template

```yaml
configuration:
  # IDENTITY
  project_name: [name]
  ai_coder: claude-code | cursor | copilot | aider
  generated_by: calibrator-001
  timestamp: [iso_datetime]
  complexity: simple | moderate | complex  # NEW 6.0 (Calibrator)
  
  # STACK
  stack:
    - name: [technology]
      version: [pinned version]
      rationale: [why this version]
      decision_type: reckoning           # NEW 6.0 (KF-5) — version pins are always reckonings
      
  # CONVENTIONS
  conventions:
    file_structure:
      - pattern: [glob]
        purpose: [what goes here]
    naming:
      - entity: [components | functions | files]
        pattern: [convention]
    imports:
      order: [group ordering]
      
  # RULES
  rules:
    do:
      - category: [error-handling | types | testing | security]
        instruction: [specific rule]
        example: [code example]
        decision_type: reckoning | evaluative_judgment  # NEW 6.0 (KF-5)
    dont:
      - category: [category]
        instruction: [anti-pattern]
        example: [bad code example]
        
  # COMPLIANCE                          # NEW 6.0 section (Calibrator)
  compliance:
    frameworks: [HIPAA | SOC2 | PCI | none]
    sections:
      - framework: [name]
        requirements:
          - [requirement with specific rule]
        
  # ENFORCEMENT
  hooks:
    pre_tool_use:
      - matcher: [pattern]
        action: [command]
    post_tool_use:
      - matcher: [pattern]
        action: [command]
        
  # BOUNDARIES
  off_limits:
    files: [paths]
    patterns: [anti-patterns]
    dependencies: [forbidden packages]
    
  # DECISION LOG                        # NEW 6.0 section (KF-5)
  decision_log:
    - decision: [what was decided]
      decision_type: reckoning | evaluative_judgment | novel_judgment
      locked: true | false
      rationale: [why — depth matches type]
```

---

## Infrastructure Architecture Specification Template (NEW 6.3)

Use when: Planning service topology, deployment phases, hardware sizing, internal networking, or multi-product infrastructure.
Created by: Expert → Builder chain (infrastructure domain).
Decision types: Hardware choices (evaluative), deployment phases (predictive), security model (evaluative), competitive moat (novel).

```yaml
infrastructure_architecture:
  # IDENTITY
  id: [unique-identifier]  # e.g., "infra-arch-001"
  name: [Architecture name]
  version: [semantic version]
  products_covered: [list of products sharing this infrastructure]

  # SERVICE CATALOG
  services:
    - name: [service name]
      product: [which product it belongs to]
      criticality: critical | important | batch
      model_dependency: [which AI model(s) it uses, if any]
      failover_strategy: hot_swap | queued_retry | fail_open | none
      health_endpoint: [URL or "none"]
      current_location: [where it runs now]
      target_location: [where it should run]
      decomposition_readiness: ready | needs_work | tightly_coupled | unknown
      decision_type: [reckoning | evaluative | predictive | novel]  # KF-5

  # NETWORKING TOPOLOGY
  networking:
    internal_communication: [service_mesh | internal_dns | direct_ip | vpn]
    auth_between_services: [mTLS | api_keys | none]
    public_surface:
      - component: [what faces the internet]
        role: [what it does]
    private_surface:
      - component: [internal-only component]
        accessible_by: [which internal services]
    dns: [external_only | internal_dns | service_discovery]

  # HARDWARE PLAN
  hardware:
    current:
      - server: [identifier]
        specs: { cpu: "", ram: "", disk: "", gpu: "" }
        utilization: { cpu_pct: 0, ram_pct: 0, disk_pct: 0 }
        monthly_cost: [amount]
    planned:
      - server: [identifier]
        specs: { cpu: "", ram: "", disk: "", gpu: "" }
        purpose: [what runs on it]
        phase_added: [which deployment phase]
        monthly_cost: [amount]

  # MODEL-TO-HARDWARE MAPPING
  model_deployment:
    - model: [model name and size]
      vram_required: [quantized and FP16 estimates]
      latency_target: [acceptable response time]
      throughput_target: [requests/sec at expected load]
      hardware_assignment: [which server/GPU]
      time_sharing: [whether sharing GPU with other models]
      fallback: [what happens if this model is unavailable]
      decision_type: evaluative  # KF-5: hardware mapping is criteria-based judgment

  # HOT-SWAP / FAILOVER
  failover:
    critical_services:
      - service: [name]
        strategy: [active_passive | active_active | fail_open]
        health_check: [mechanism and interval]
        failover_time: [target seconds]
        fallback_behavior: [degraded mode description]
    revenue_critical_pattern:
      principle: [e.g., "fail open to protect revenue"]
      applies_to: [which services]

  # DEPLOYMENT PHASES
  phases:
    - phase: [number]
      name: [phase name]
      changes: [what moves or gets added]
      hardware_added: [new hardware, if any]
      risk_mitigated: [what failure mode this phase eliminates]
      rollback_plan: [how to undo this phase if it fails]
      estimated_cost_delta: [incremental monthly cost]
      decision_type: predictive  # KF-5: phasing involves future outcome judgment

  # SECURITY MODEL
  security:
    dmz_components: [what faces the public internet]
    internal_only: [what must never be publicly accessible]
    inter_service_auth: [mTLS | api_keys | both]
    sensitive_data:
      - data_type: [e.g., "fine-tuned model weights"]
        classification: [trade_secret | high_risk | standard]
        storage: [where and how protected]
        backup: [backup strategy]
        access_control: [who/what can access]
    tracking_data_isolation: [how user tracking data stays internal]

  # COMPETITIVE MOAT ANALYSIS (optional — for "hard to copy" architectures)
  moat:
    layers:
      - name: [moat layer name]
        description: [what makes it defensible]
        reinforcement: [how this layer strengthens over time]
        architectural_support: [how the architecture protects this layer]
    compounding_loops:
      - loop: [description of positive feedback loop]
        layers_involved: [which moat layers participate]
    decision_type: novel  # KF-5: moat analysis has limited precedent

  # MONITORING
  monitoring:
    per_service:
      - service: [name]
        metrics: [latency, error_rate, queue_depth, etc.]
        alerting: [mechanism]
    infrastructure:
      - metric: [e.g., "GPU utilization", "disk space", "network throughput"]
        threshold: [alert threshold]

  # CONSTRAINTS
  constraints:
    budget: [budget parameters]
    tooling_preferences: [e.g., "Docker, Caddy, WireGuard, vLLM"]
    design_principles:
      - [e.g., "revenue-critical paths always have a degraded-but-functional fallback"]
      - [e.g., "every service must be monitorable"]
```

---

## Hosting Audit & Decomposition Readiness Template (NEW 6.3)

Use when: Inventorying current hosting state, analyzing SPOFs, and planning what to move first.
Created by: Critic (audit variant).
Decision types: SPOF assessment (evaluative), decomposition readiness (evaluative), extraction priority ranking (evaluative).

```yaml
hosting_audit:
  # IDENTITY
  id: [unique-identifier]
  name: [Audit name, e.g., "Q2 2025 Hosting Audit"]
  version: [semver]
  generated_by: critic-audit-001
  timestamp: [iso_datetime]

  # SERVICE INVENTORY
  services:
    - name: [service name]
      product: [which product]
      server: [current hosting server identifier]
      process_manager: [systemd | pm2 | docker | manual | etc.]
      exposes:
        - protocol: [HTTP | HTTPS | TCP | etc.]
          port: [port number]
          public: true | false
      depends_on:
        - [other service name or external dependency]
      resource_profile: cpu_bound | io_bound | memory_bound | gpu_bound
      criticality: critical | important | batch | unknown

  # NETWORKING TOPOLOGY
  networking:
    inter_server_communication: [public_ips | private_network | vpn | none]
    private_network_available: [yes | no | partial]
    vpn: [wireguard | tailscale | none]
    dns: [external_only | internal_dns | service_discovery]
    firewalls: [description of firewall rules, security groups, ACLs]
    tls: [lets_encrypt | cloudflare | custom_certs | mixed]

  # DATABASE & STATE
  databases:
    - engine: [PostgreSQL | Redis | etc.]
      version: [version]
      location: [co-located with app | separate server]
      backup:
        strategy: [automated | manual | none]
        frequency: [daily | weekly | etc.]
        last_tested_restore: [date or "never"]
      replication: [configured | none]

  persistent_state_outside_db:
    - type: [flat files | wiki/ | config | local storage]
      location: [path]
      product: [which product]
      backup: [strategy or "none"]

  # TRAFFIC & LOAD
  traffic:
    per_service:
      - service: [name]
        requests_per_day: [approximate]
        peak_pattern: [description of peak times]
        resource_profile: cpu_bound | io_bound | memory_bound
    current_utilization:
      cpu_pct: [average]
      ram_pct: [average]
      disk_pct: [current usage]
    capacity_limits_hit: [list of services at or near capacity]

  # SINGLE POINTS OF FAILURE
  spof_analysis:
    critical_spofs:
      - component: [what]
        failure_impact: [what goes down if this fails]
        current_redundancy: [none | partial | full]
        recovery_time: [estimated: hours | days]
    knowledge_spofs:
      - area: [what area of knowledge]
        single_person: [true | false]
        documentation: [adequate | partial | none]
    monitoring:
      uptime_checks: [yes | no]
      alerting: [yes | no | partial]
      log_aggregation: [yes | no]

  # DECOMPOSITION READINESS
  # Rate each service: Ready | Needs Work | Tightly Coupled | Unknown
  decomposition:
    per_service:
      - service: [name]
        readiness: ready | needs_work | tightly_coupled | unknown
        coupling_description: [what couples it to the current host]
        migration_blockers:
          - [e.g., "hardcoded localhost in config"]
          - [e.g., "shared filesystem with service Y"]
        containerized: [yes | no | partial]
        estimated_extraction_effort: [hours | days | weeks]
        decision_type: evaluative  # KF-5

    extraction_priority:
      # Ranked by: failure impact × extraction ease × resource benefit
      - rank: 1
        service: [name]
        rationale: [why this moves first]
      - rank: 2
        service: [name]
        rationale: [why]
      - rank: 3
        service: [name]
        rationale: [why]

  # PROVIDER CAPABILITIES
  provider_assessment:
    private_networking: [supported | not_supported | partial]
    internal_only_servers: [can add servers without public IPs?]
    gpu_availability: [what GPU options on same internal network]
    cost_model: [how additional internal servers are priced]

  # COST ESTIMATE
  expansion_costs:
    - option: [e.g., "1x internal-only application server"]
      specs: [CPU, RAM, disk]
      monthly_cost: [estimated]
    - option: [e.g., "1x GPU inference server"]
      specs: [CPU, RAM, disk, GPU model]
      monthly_cost: [estimated]
      decision_type: predictive  # KF-5: cost estimates involve future projections
```

---

## ERA Specification Template (NEW 6.6)

Use when: Mapping entity relationships in a data model, auditing module dependencies, modeling coordination contracts between agents or modes, or analyzing what entities a system produces and consumes.
Created by: Expert (ERA) → Builder chain.
Decision types: Entity boundary choices (evaluative), cardinality (evaluative), relationship naming (reckoning), implicit entity identification (evaluative).

```yaml
era_specification:
  # HEADER
  title: [descriptive title — e.g., "KF Module Dependency Model" or "COS Data Entity Graph"]
  version: [semver]
  domain: data_model | module_dependency | agent_contract | ods_profile | other
  scope: [what is included and excluded from this ERA]
  generated_by: expert-era-001 → builder-001
  timestamp: [iso_datetime]
  grounding_score: [0.0–1.0 — confidence in entity/relationship identification]

  # ENTITIES
  entities:
    - id: [entity_id]                  # Short slug, e.g., kf_module, session, stakeholder
      name: [Human-readable name]
      description: [What this entity represents]
      attributes:
        - name: [attribute_name]
          type: string | integer | enum | reference | boolean
          required: true | false
          notes: [constraints or allowed values]
      aggregate_root: true | false      # Is this a primary entry point?
      implicit: true | false            # NEW 6.6 — Was this entity undocumented before this ERA?
      decision_type: reckoning | evaluative_judgment

  # RELATIONSHIPS
  relationships:
    - id: [rel_id]
      from: [entity_id]
      to: [entity_id]
      verb: [verb phrase — e.g., "activates", "produces", "references", "consumed_by"]
      cardinality: 1:1 | 1:N | N:1 | M:N
      direction: unidirectional | bidirectional
      implicit: true | false            # NEW 6.6 — Was this relationship undocumented before this ERA?
      junction_entity: [entity_id]      # Required for M:N — names the mediating entity
      decision_type: reckoning | evaluative_judgment

  # ADVERSARIAL FINDINGS
  adversarial_findings:
    compound_failures:
      - finding: [description]
        severity: Low | Medium | High | Critical
        entities_involved: [entity_ids]
        fix: [specific remediation]

    assumption_inversions:
      - assumption: [stated or implicit assumption]
        inversion: [what breaks the assumption]
        impact: [consequence]
        decision_type: evaluative_judgment | predictive_judgment

    implicit_entities_surfaced:        # NEW 6.6 — key differentiator from standard ERD output
      - entity_id: [id]
        name: [name]
        why_implicit: [why it was missing from original model]
        impact: [what changes now that it's explicit]

    design_implications:
      - implication: [systemic pattern observed]
        severity: Low | Medium | High
        recommendation: [what to change at the design level, not just the symptom]

  # SUMMARY
  summary:
    entity_count: [N]
    relationship_count: [N]
    implicit_entities_found: [N]       # NEW 6.6 — key metric: how much was undocumented
    implicit_relationships_found: [N]
    highest_severity_finding: Low | Medium | High | Critical
    overall_model_health: clean | needs_attention | degraded
    accretion_candidate: true | false
    accretion_note: [if true — what specifically should be filed to Tier 0]

  # FORWARD NAVIGATION
  next_steps:
    - [specific action 1 — e.g., "Add junction entity for Module↔Activation_Condition M:N relationship"]
    - [specific action 2]
```

---

## Usage Notes

**When to use each template:**

| Template | Use When | Created By |
|----------|----------|------------|
| Agent Specification | Creating a new agent | Builder |
| System Prompt | Implementing an agent in an AI system | Builder |
| Critique | Validating a specification or design | Critic |
| Synthesis | Extracting patterns from examples | Synthesizer |
| Diagnosis | Troubleshooting a problem | Debugger |
| Strategic Decision | Making prioritization or trade-off decisions | Strategist |
| Process Specification | Designing a multi-step workflow | Coordinator/Builder |
| Message | Defining agent-to-agent communication | Any |
| Handoff | Designing transfer points between agents | Coordinator |
| Context | Tracking state through a session | Any |
| Assessment | Validating agent or process quality | Critic |
| AI Coder Configuration | Setting up project AI coder guardrails | Calibrator |
| Infrastructure Architecture | Planning service topology, deployment phases, hardware sizing | Expert → Builder chain (6.3) |
| Hosting Audit | Inventorying current state, SPOF analysis, decomposition planning | Critic (audit variant) (6.3) |
| ERA Specification | Mapping entity relationships, auditing module dependencies, modeling agent contracts | Expert (ERA) → Builder chain (6.6) |

**Template modification rules:**
- Add fields specific to your domain
- Remove optional fields you don't need
- Never remove required fields (marked in comments)
- Keep the structure even if content changes
- NEW 6.0: Fields marked `# NEW 6.0` are optional for backward compatibility but recommended for full KF 6.0 integration

**KF 6.0 field summary:**

| Field | Source Module | Added To | Purpose |
|-------|-------------|----------|---------|
| `decision_type` | 13_Decision_Classification | Agent, Critique, Strategy, Process, Message, Handoff, Context | Classify reasoning depth required |
| `confidence` (σ, N) | 12_Calibration_Layer | Critique, Diagnosis, Strategy, Assessment | Multi-run evaluation stability |
| `grounding` / `grounding_score` | 15_Grounding_Scores | Agent inputs/outputs, Critique findings, Messages, Handoffs, Context artifacts | Knowledge trust level |
| `monitoring` | 14_Metacognitive_Monitor | Agent, Process, Context | Failure detection config |
| `monitor_data` | 14_Metacognitive_Monitor | Diagnosis | Monitor observations during debugging |
| `temporal_context` | 17_Temporal_Knowledge | Diagnosis, Synthesis | When things happened and changed |
| `dependency_graph` | 03_Coordination_Patterns | Process, Context | Dependency-first workflow structure |
| `graph_position` | 03_Coordination_Patterns | Message, Handoff | Position in workflow DAG |
| `testability` | 12_Calibration_Layer | Agent | How to evaluate spec with confidence intervals |
| `design_decisions` | 13_Decision_Classification | Agent | Per-decision type tagging |
| `calibrated_ranking` | 12_Calibration_Layer | Strategy | Ranking stability across runs |
| `bias_checks` | 12_Calibration_Layer | Critique, Assessment | Which biases were tested |
| `compliance` | 11_Calibrator_Agent | Configuration | Regulatory framework requirements |
| `complexity` | 11_Calibrator_Agent | Configuration | Project complexity tier |
| `decision_log` | 13_Decision_Classification | Configuration | Config decision type tracking |

**KF 6.1 field summary:**

| Field | Source Module | Added To | Purpose |
|-------|-------------|----------|---------|
| `capabilities_when_subagent` | 20_Permission_Model | Agent | Read/write/escalate boundaries when in chains |
| `risk_tier` | 20_Permission_Model | Agent | Base risk classification + escalation rules |
| `verification_required` | 03_Coordination_Patterns | Agent, Chain outputs | Whether adversarial review is automatic |
| `chain_capability_restrictions` | 03_Coordination_Patterns | Process | Per-mode capability limits in chains |
| `routing_index` | 19_Memory_Architecture | Context | Compact session state for routing decisions |
| `consolidation_state` | 19_Memory_Architecture | Context | Last consolidation timestamp + diff |

**KF 6.2 field summary:**

| Field | Source Module | Added To | Purpose |
|-------|-------------|----------|---------|
| `accretion_candidate` | 21_Knowledge_Accretion | Agent outputs, Critique, Synthesis, Diagnosis, Strategy | Flag output as containing novel, reusable knowledge worth persisting |
| `accretion_category` | 21_Knowledge_Accretion | Agent outputs | Category tag: patterns \| frameworks \| diagnostics \| configs \| domain-knowledge |

**KF 6.3 field summary:**

| Field | Source Module | Added To | Purpose |
|-------|-------------|----------|---------|
| `decomposition_readiness` | Infrastructure Planning (6.3) | Infrastructure Architecture, Hosting Audit | Service extraction readiness: ready / needs_work / tightly_coupled / unknown |
| `moat` | Infrastructure Planning (6.3) | Infrastructure Architecture | Competitive defensibility layers, reinforcement loops, architectural support |

**KF 6.6 field summary:**

| Field | Source Module | Added To | Purpose |
|-------|-------------|----------|---------|
| `implicit` (entity) | ERA (6.6) | ERA Specification — entities[] | Flags entities that were undocumented before this ERA analysis — key adversarial signal |
| `implicit` (relationship) | ERA (6.6) | ERA Specification — relationships[] | Flags relationships that were undocumented before this ERA analysis |
| `implicit_entities_surfaced` | ERA (6.6) | ERA Specification — adversarial_findings | Structured record of each implicit entity: why it was missing, what changes now it's explicit |
| `implicit_entities_found` / `implicit_relationships_found` | ERA (6.6) | ERA Specification — summary | Count metrics: how much of the model was previously undocumented |

---

## Next Steps

1. **Copy the template you need** → Modify for your specific use case
2. **Fill in all required fields** → Leave nothing as placeholder
3. **Tag design decisions with type** → (NEW 6.0) Classify each decision as reckoning/evaluative/predictive/novel
4. **Include testability metadata** → (NEW 6.0) How would you evaluate this spec's quality?
5. **Validate completeness** → Could someone implement this without asking questions?
6. **Route to Critic** → Get calibrated validation before implementation
7. **Test with a real case** → Run through an actual scenario
8. **Iterate** → Refine based on what you learn

Related modules:
- `02_Builder_Agent.md` — Uses these templates to create agents
- `03_Coordination_Patterns.md` — Context for multi-agent templates; dependency graph fields
- `05_Expert_Agent_Example.md` — Expert domain adaptations that produce structured template output (infra, ERA)
- `07_Critic_Agent.md` — Validates outputs against templates
- `08_Synthesizer_Agent.md` — Creates patterns from template instances
- `09_Debugger_Agent.md` — Uses diagnosis template
- `10_Strategist_Agent.md` — Uses strategic decision template
- `11_Calibrator_Agent.md` — Uses configuration template
- `12_Calibration_Layer.md` — Source for confidence/calibration fields
- `13_Decision_Classification.md` — Source for decision_type fields
- `14_Metacognitive_Monitor.md` — Source for monitoring fields
- `15_Grounding_Scores.md` — Source for grounding fields
- `17_Temporal_Knowledge.md` — Source for temporal context fields
