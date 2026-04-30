# Permission Model

## Module Metadata

```yaml
module:
  title: Permission Model
  version: 7.0.1
  purpose: Layered permission system that classifies action risk, enforces capability restrictions per sub-agent, and gates autonomous behavior with human checkpoints
  topics: [permissions, risk-classification, capability-restriction, autonomous-governance, sub-agent-safety, accretion-permissions]
  contexts: [autonomous-deployment, sub-agent-architecture, mode-chains, production-safety]
  difficulty: advanced
  related: [03_Coordination_Patterns, 04_Specification_Templates, 13_Decision_Classification, 14_Metacognitive_Monitor, 16_Operational_Bounds, 19_Memory_Architecture, 21_Knowledge_Accretion]
  added_in: "6.1"
  implements: "Directive 5 (Layered Permission Model), Directive 6 (Fork-Join Capabilities)"
  changelog:
    7.0.1:
      date: 2026-04-29
      changes:
        - Expanded Allow-With-Mutation section — added hook output contract, audit trail spec (.kf/state/permission_mutations.jsonl with fields), and explicit deny-vs-mutate decision rule
        - 7.0.0 had mutation policies table and implementation note; missing the concrete hook interface, audit path, and when to prefer mutation over denial
        - Source: plans/hooks-mastery-integration.md ([project]-swd.12)
    7.0.0:
      date: 2026-04-14
      changes:
        - Add allow-with-mutation permission tier — path normalization, safety flags, cost annotation policies
    6.2.0: |
      - Added accretion permission rules — MEDIUM base, HIGH for customer-facing knowledge bases (Module 21 integration)
      - Added accretion_permissions yaml block
      - Added accretion to risk escalation rules
```

---

## Core Approach

As KF moves toward autonomous operation with sub-agent architecture, every action needs a risk classification and every sub-agent needs a capability boundary. The permission model prevents privilege escalation, enforces least-privilege per mode, and ensures human oversight on high-stakes decisions.

**Primary function:** Classify every KF action by risk tier and enforce capability restrictions per mode when deployed as sub-agents.

**Key insight:** The decision classification tree (Module 13) provides a natural risk mapping — reckonings are low-risk, novel judgments are high-risk. But chain length compounds risk, so a three-mode chain producing evaluative output should be classified higher than a single evaluative judgment.

**Design principle:** Right-size the permission surface to our actual threat model. KF's risk is bad recommendations, not arbitrary code execution. Gate the recommendations, not the reasoning.

---

## Three-Tier Risk Classification

### Tier Definitions

```yaml
risk_tiers:
  LOW:
    description: Actions with minimal consequence if wrong. Auto-approve.
    actions:
      - Reckonings (factual lookups, direct answers)
      - Mode routing decisions
      - Formatting and restructuring output
      - Reading artifacts or context
      - Updating the routing index (Module 19)
      - Navigator disambiguation
    approval: automatic
    logging: minimal (count only)
    
  MEDIUM:
    description: Actions with moderate consequence — correctible but costly to undo. Auto-approve with logging.
    actions:
      - Evaluative judgments (single mode)
      - Mode chaining (2-mode chains)
      - Context compression and consolidation
      - Artifact creation (drafts)
      - Predictive judgments with explicit assumptions
      - ODS profile updates to existing assertions
      - Knowledge base accretion — filing to persistent storage (Module 21)
    approval: automatic
    logging: full (action, reasoning, confidence, mode chain)
    
  HIGH:
    description: Actions with significant consequence — irreversible or affects downstream systems. Require human confirmation.
    actions:
      - Novel judgments (no precedent, high stakes)
      - Strategy recommendations that affect product decisions
      - ODS profile generation that will feed COS bridging
      - Mode chains of 3+ modes (compounding error risk)
      - Any action flagged by adversarial verification as uncertain
      - Artifact promotion from draft to approved
      - Irreversible recommendations (documented as such by Strategist)
      - Knowledge base accretion to customer-facing knowledge bases (Module 21 domain escalation)
    approval: human confirmation required
    logging: full + rationale + alternatives considered
```

### Risk Escalation Rules

```yaml
risk_escalation:
  chain_length_escalation:
    rule: "Chain length compounds risk. A 3+ mode chain is at minimum MEDIUM regardless of terminal decision type."
    mapping:
      single_mode_reckoning: LOW
      single_mode_evaluative: MEDIUM
      single_mode_predictive: MEDIUM
      single_mode_novel: HIGH
      two_mode_chain: max(terminal_tier, MEDIUM)
      three_plus_mode_chain: max(terminal_tier, MEDIUM) — review for HIGH
      
  confidence_escalation:
    rule: "Low confidence escalates risk tier by one level."
    trigger: Confidence below 0.5 on output
    action: Escalate risk tier (LOW → MEDIUM, MEDIUM → HIGH)
    
  adversarial_escalation:
    rule: "Adversarial verification finding escalates risk tier."
    trigger: Critic adversarial pass surfaces severity 2+ issue
    action: Escalate to HIGH regardless of original tier
    
  domain_escalation:
    rule: "ODS-to-COS bridging is always HIGH."
    trigger: Any output that feeds COS personality scoring
    action: Set to HIGH — organizational profiles affect customer-facing recommendations
    
  accretion_escalation:
    rule: "Knowledge base accretion to customer-facing knowledge bases is always HIGH."
    trigger: Accretion candidate targets a knowledge base that feeds customer-facing products (Science Advisor evidence tiers, COS claims, ODS scoring)
    action: Set to HIGH — bad knowledge in production bases propagates to customer output
```

---

## Allow-With-Mutation (Third Permission Tier)

Extend the binary allow/deny model with a mutation tier. Some operations should be allowed but with their inputs sanitized or annotated before execution:

**Mutation policies:**

| Policy | Trigger | Mutation |
|--------|---------|----------|
| Path normalization | Absolute paths outside project root | Rewrite to relative path within project |
| Safety flag injection | Destructive shell commands (rm, drop, truncate) | Inject `--dry-run` or `--interactive` flag |
| Cost annotation | LLM API calls with large context | Prepend token estimate to tool input |
| Scope restriction | File writes to sensitive directories | Redirect to sandbox path |

**Hook output contract:** Mutations are applied via the `PermissionRequest` hook. The hook returns:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow",
      "updatedInput": {
        "command": "{sanitized_command}"
      },
      "message": "Input sanitized: {what changed and why}"
    }
  }
}
```

The hook receives the proposed tool call, applies the matching mutation policy, and returns the modified input. Claude executes the mutated version — the original is preserved in the audit log.

**Audit trail:** Every mutation is logged to `.kf/state/permission_mutations.jsonl`:

```json
{
  "timestamp": "ISO-8601",
  "policy_applied": "path_normalization | safety_flags | cost_annotation | scope_restriction",
  "original_input": { ... },
  "mutated_input": { ... },
  "message": "what changed"
}
```

If a mutation changes the semantic meaning of the operation (not just format), surface the change to the user before execution.

**Deny vs. mutate — decision rule:**

| Situation | Decision |
|-----------|----------|
| Intent is valid, execution is unsafe | Mutate — allow with sanitized input |
| Intent is invalid or out-of-scope | Deny — block entirely |
| Mutation would change semantic meaning and user hasn't confirmed | Surface to user before executing |

Prefer mutation over denial when the intent is valid but the execution is unsafe. Denial is for operations that shouldn't happen at all.

---

## Capability Profiles Per Mode

When deployed as sub-agents, each mode operates with the minimum capability set required for its function. This prevents a sub-agent from exceeding its mandate.

### Capability Declarations

```yaml
capability_profiles:
  navigator:
    role: Route requests to appropriate mode
    read: [user_request, routing_index, session_state]
    write: [routing_decision]
    create: nothing
    modify: nothing
    escalate: [ambiguity_that_cannot_be_resolved]
    restriction: "Cannot create artifacts, make decisions, or produce final output. Routing only."
    
  builder:
    role: Create specifications and artifacts
    read: [user_request, routing_index, session_state, pattern_library, strategic_context]
    write: [specification_draft, system_prompt_draft, design_decisions]
    create: [new_artifacts within assigned scope]
    modify: [own_artifacts only]
    escalate: [scope_unclear, requirements_conflict, novel_design_decision]
    restriction: "Cannot modify artifacts created by other modes. Cannot approve own output. Scoped to artifact assigned by orchestrator."
    
  critic:
    role: Review and validate artifacts
    read: [artifact_under_review, routing_index, session_state, all_session_artifacts]
    write: [critique_output, severity_assessments, finding_reports]
    create: [critique_artifacts]
    modify: nothing — read-only on reviewed artifact
    escalate: [severity_disagreement, insufficient_context_for_review]
    restriction: "Cannot modify the source artifact. Read-only access to artifact under review. Write access only to review output."
    
  expert:
    role: Domain-specific deep analysis
    read: [artifact_under_analysis, domain_context, routing_index, session_state]
    write: [analysis_output, findings, adversarial_depth_results]
    create: [analysis_artifacts]
    modify: nothing
    escalate: [domain_outside_expertise, novel_pattern_encountered]
    restriction: "Cannot modify analyzed artifacts. Analysis output only."
    
  debugger:
    role: Diagnose problems and identify root causes
    read: [all_session_context, error_logs, hypothesis_history, monitor_data]
    write: [diagnostic_output, hypothesis_tree, root_cause_report]
    create: [diagnosis_artifacts]
    modify: nothing
    escalate: [all_hypotheses_eliminated, evidence_insufficient]
    restriction: "Full read access for diagnosis. Write access only to diagnostic output."
    
  strategist:
    role: Evaluate options and recommend decisions
    read: [all_session_context, routing_index, operational_bounds, constraints]
    write: [recommendation_output, trade_off_analysis, priority_rankings]
    create: [strategy_artifacts]
    modify: nothing
    escalate: [novel_decision_requiring_human, irreversible_decision_identified]
    restriction: "Cannot implement recommendations. Write access only to recommendation output."
    
  synthesizer:
    role: Extract patterns from examples
    read: [examples_provided, routing_index, session_state, temporal_context]
    write: [pattern_output, framework_output, anti_patterns]
    create: [synthesis_artifacts]
    modify: nothing
    escalate: [insufficient_examples, contradictory_patterns]
    restriction: "Read-only on source examples. Write access only to synthesis output."
    
  calibrator:
    role: Generate AI coder configurations
    read: [project_context, stack_requirements, compliance_needs, routing_index]
    write: [configuration_output, complexity_assessment]
    create: [configuration_artifacts]
    modify: nothing
    escalate: [novel_compliance_requirement, stack_conflict_unresolvable]
    restriction: "Cannot deploy configurations. Write access only to config output."
```

### Inheritance and Escalation Rules

```yaml
sub_agent_rules:
  inheritance:
    rule: "Sub-agents inherit the parent orchestrator's risk tier but cannot escalate their own permissions."
    example: "A Builder sub-agent spawned for LOW-risk spec generation cannot autonomously make HIGH-risk strategy recommendations."
    
  capability_violation:
    detection: "Orchestrator monitors sub-agent actions against capability profile."
    response: "Block the action, log the violation, continue with warning."
    repeated_violation: "Terminate sub-agent, escalate to orchestrator for reassignment."
    
  cross_mode_restriction:
    rule: "No sub-agent can modify another sub-agent's output directly."
    enforcement: "All cross-mode communication goes through the orchestrator."
    exception: "Critic can annotate (not modify) any artifact for review purposes."
```

---

## Blocking Budget

When operating autonomously, KF enforces time and processing limits before requiring a human checkpoint.

```yaml
blocking_budget:
  principle: "Cap autonomous processing time before surfacing a checkpoint."
  
  budgets:
    interactive_session:
      description: "User is actively engaged in conversation"
      budget: "No autonomous processing — every output is visible to user"
      checkpoint: "Natural turn-taking serves as continuous checkpoint"
      
    mode_chain_execution:
      description: "Multi-mode chain running with intermediate steps"
      budget: "Surface checkpoint after each mode completes"
      checkpoint: "Show intermediate output: 'Step N complete. [summary]. Proceeding to step N+1.'"
      
    background_consolidation:
      description: "Memory consolidation or profile maintenance"
      budget: "30 seconds maximum processing"
      checkpoint: "If consolidation exceeds budget, output partial results and flag"
      
    autonomous_sensing:
      description: "ODS continuous sensing or proactive monitoring"
      budget: "60 seconds maximum before surfacing findings"
      checkpoint: "Present findings for human review before acting on them"
      
  overrides:
    user_absent: "If no user interaction for 5+ minutes during active chain, pause and wait"
    high_risk_action: "Always checkpoint before HIGH-risk actions regardless of budget"
```

---

## Permission Gate Protocol

For interactive sessions (current deployment), the permission model operates as behavioral constraints in the prompt. For autonomous deployment (future), it becomes an enforcement layer.

```yaml
permission_gate:
  interactive_mode:
    description: "Current deployment — user is in the loop"
    enforcement: "Behavioral. Orchestrator follows risk classification for output framing."
    low_risk: "Answer directly. No ceremony."
    medium_risk: "Include confidence and reasoning. Flag assumptions."
    high_risk: "Explicit flag: 'This is a high-stakes decision. My recommendation is X because Y. This warrants review before acting.'"
    
  autonomous_mode:
    description: "Future deployment — sub-agents operating with reduced supervision"
    enforcement: "Programmatic. Permission gate checks before action execution."
    low_risk: "Auto-execute. Log count."
    medium_risk: "Auto-execute. Full logging."
    high_risk: "Queue for human approval. Do not execute until confirmed."
    
  gate_sequence:
    1. Classify action risk tier (using decision type + chain length + confidence)
    2. Check sub-agent capability profile (can this agent perform this action?)
    3. Apply domain escalation rules (ODS/COS bridging, irreversibility)
    4. If HIGH: surface checkpoint and wait for confirmation
    5. Log action and outcome regardless of tier
```

---

## ODS-Specific Permission Rules

Organizational profiles require elevated permission standards because they feed customer-facing products. ODS modules (ODS_00 through ODS_10) are maintained as a separate module set and integrated at the orchestrator level.

```yaml
ods_permissions:
  profile_read:
    tier: LOW
    description: "Reading existing organizational profile data"
    
  profile_update_existing:
    tier: MEDIUM
    description: "Updating an existing assertion with newer data"
    requires: "Source data reference. Logging of what changed and why."
    
  profile_new_assertion:
    tier: HIGH
    description: "Adding a new assertion to an organizational profile"
    requires: "Human confirmation. Grounding score ≥ 0.6. Source data reference."
    
  profile_to_cos_bridge:
    tier: HIGH
    description: "Any profile data used for COS personality scoring"
    requires: "Adversarial review passed. Human confirmation."
    
  profile_consolidation:
    tier: MEDIUM
    description: "Background consolidation of profile data"
    requires: "Diff output showing all changes. No silent modifications."
```

---

## Circuit Breakers

Prevent runaway retry loops and compounding failures.

```yaml
circuit_breakers:
  consecutive_failure:
    threshold: 3
    description: "If any KF mode produces errors on 3 consecutive attempts"
    action: "Halt execution. Surface the failure with diagnostic context. Do not retry."
    output: |
      "Mode [X] failed 3 consecutive times. Failure pattern: [description].
      Options: (1) Retry with different approach, (2) Skip this step, (3) Escalate."
    logging: "Full diagnostic for post-mortem"
    
  chain_failure:
    threshold: 2
    description: "If a mode chain fails at the same step on 2 attempts"
    action: "Abort chain. Surface partial results from completed steps."
    output: |
      "Chain [A → B → C] failed at step [B] on second attempt.
      Step A output: [summary]. Recommended: reformulate or decompose."
    
  adversarial_overload:
    threshold: "Adversarial yield > 80% on a single artifact"
    description: "If adversarial review finds issues in >80% of sections"
    action: "Flag artifact for rebuild rather than incremental revision."
    output: "Adversarial review found pervasive issues. Recommend rebuilding rather than patching."
```

---

## Constraints

- Permission tiers are additive — an action at the intersection of two tiers takes the higher tier
- Sub-agents cannot escalate their own permissions. Only the orchestrator can reclassify.
- Circuit breakers are fail-safe — they halt, not retry
- ODS profile-to-COS bridging is always HIGH, with no override
- The blocking budget is right-sized to SEMalytics interaction patterns, not Anthropic's Claude Code numbers
- In interactive mode, the human is always in the loop — permission gates frame output, not block it
- Logging is not optional for MEDIUM and HIGH actions

---

## Success Criteria

- No HIGH-risk action executes without human confirmation in autonomous mode
- All MEDIUM actions are logged with sufficient detail for post-mortem
- Permission classification is deterministic: given an action description, the system consistently assigns the correct tier
- Sub-agents operate within their capability profiles — no capability violations in production
- Circuit breakers prevent runaway loops — no action retried more than 3 times
- Chain length escalation catches compound risk that single-action classification misses

---

## Attribution

| Element | Source |
|---------|--------|
| Three-tier risk classification | Claude Code six-gate model, simplified for our threat surface |
| Capability profiles per mode | Claude Code fork-join with restricted capabilities |
| Sub-agent inheritance rules | Claude Code coordinator/worker capability restriction pattern |
| Chain-length risk escalation | Our design — addresses compound error risk |
| Blocking budget | Claude Code KAIROS pattern, right-sized for SEMalytics |
| Circuit breakers | Claude Code circuit breaker pattern (3-failure threshold) |

---

## Related Modules

- `Agent Instructions (orchestrator)` — Enforces permission gates and capability restrictions
- `03_Coordination_Patterns.md` — Mode chains trigger risk escalation rules
- `04_Specification_Templates.md` — Agent specs include capability_when_subagent declarations
- `13_Decision_Classification.md` — Decision types map to base risk tiers
- `14_Metacognitive_Monitor.md` — Monitor signals can trigger risk escalation
- `16_Operational_Bounds.md` — Circuit breakers complement bounds-based corrective actions
- `19_Memory_Architecture.md` — (6.1) Index updates are LOW-risk; consolidation is MEDIUM-risk
- `21_Knowledge_Accretion.md` — (6.2) Accretion is MEDIUM base; customer-facing knowledge bases escalate to HIGH

## CC Doc

# Module 20: Permission Model — Execution Protocol
**Apply when:** [KF-ROUTE] load list includes M20, or mode is about to produce output with significant downstream consequence

Classify every action by risk tier and frame outputs accordingly.

## Three-Tier Risk Classification

**LOW:** Auto-approve. Reckonings, routing decisions, formatting, reading artifacts, routing index updates. No framing overhead — answer directly.

**MEDIUM:** Auto-approve with full logging. Evaluative judgments (single mode), 2-mode chains, context compression, artifact creation (drafts), predictive judgments with explicit assumptions, knowledge base accretion. Include confidence and reasoning. Flag assumptions explicitly.

**HIGH:** Human confirmation required. Novel judgments, strategy recommendations affecting product decisions, 3+ mode chains, adversarial findings at severity 2+, artifact promotion from draft to approved, customer-facing knowledge base accretion. Flag explicitly: *"This is a high-stakes decision. My recommendation is X because Y. This warrants review before acting."*

## Risk Escalation Rules

```
Single mode, reckoning: LOW
Single mode, evaluative: MEDIUM
Single mode, novel: HIGH
Two-mode chain: max(terminal_tier, MEDIUM)
Three+ mode chain: max(terminal_tier, MEDIUM) → review for HIGH
Confidence < 0.5: escalate tier by one level
Adversarial finding severity 2+: escalate to HIGH regardless
```

## Capability Profile (Mode Restrictions)

| Mode | Cannot Do |
|------|-----------|
| Navigator | Create artifacts, make decisions |
| Builder | Modify others' outputs, approve own output |
| Critic | Modify source artifact (annotate only) |
| Expert | Modify analyzed artifacts |
| Debugger | Implement fixes |
| Strategist | Implement recommendations |
| Synthesizer | Modify source examples |
| Calibrator | Deploy configurations |

Sub-agents cannot escalate their own permissions beyond what the orchestrator assigns. No sub-agent modifies another sub-agent's output.

## Circuit Breakers

3 consecutive failures → halt that mode, surface diagnostics, do NOT auto-retry. 2 consecutive failures at same chain step → abort chain, surface partial results. Adversarial overload (> 80% sections flagged) → flag for rebuild, not incremental revision.
