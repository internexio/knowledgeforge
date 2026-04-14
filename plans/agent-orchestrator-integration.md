# Agent Orchestrator → KnowledgeForge Integration Plan

**Source:** ComposioHQ/agent-orchestrator ~0.2.2-0.3.0 | TypeScript monorepo
**Research date:** 2026-04-13 | **Plan version:** 1.0

---

## Strategic Value

Agent Orchestrator answers the multi-agent coordination problem with a clean 7-slot plugin system and a reaction engine that closes the CI/review feedback loop automatically. Two patterns have direct KF value: the reaction engine architecture (state machine → auto-respond → retry + escalate) and the PostToolUse-as-metadata-bus pattern. A third — the plugin slot architecture — validates KF's existing mode-based composition model while surfacing a gap: KF has no equivalent to AO's Lifecycle Manager as a non-pluggable core.

---

## Module Updates

### 1. Module 16 (Operational Bounds) — Reaction Engine for Lifecycle Events

**What changes:** Add a declarative reaction system to Operational Bounds that maps state transitions to automatic responses with configurable retry budgets and escalation thresholds.

**Why it works:** AO's reaction system (`ci-failed → send-to-agent, retries: 2, escalateAfter: 2`) is the cleanest implementation of "detect state → auto-respond → escalate if unresolved" found in the research. KF's current circuit breakers are binary (3 failures → halt). A reaction engine would add graduated response: retry with context → retry with modified approach → escalate.

**Spec delta:**
```yaml
# Add to Operational Bounds → Reaction Engine
reactions:
  context_pressure:
    trigger: context_utilization > 80%
    auto: true
    action: compress_context  # Module 14 intervention
    retries: 1
    escalate_after: 1  # if compression doesn't bring below 80%, escalate

  mode_failure:
    trigger: mode_error
    auto: true
    action: retry_with_modified_approach
    retries: 2
    escalate_after: 2  # matches current 3-failure circuit breaker

  confidence_drift:
    trigger: confidence_calibration_drift > 10%
    auto: true
    action: flag_for_review
    retries: 0  # no retry — immediate flag
    escalate_after: 0

  stale_state_detected:
    trigger: skeptical_verification_failure
    auto: true
    action: refresh_state
    retries: 1
    escalate_after: 1

  # Schema for custom reactions
  reaction_schema:
    trigger: string  # state transition or metric threshold
    auto: boolean  # execute without human confirmation
    action: enum[retry, compress, flag, escalate, send_to_mode, halt]
    retries: integer
    escalate_after: integer | duration
    escalation_target: enum[user, different_mode, halt]
```

**Relationship to existing circuit breakers:** The reaction engine subsumes the current 3-failure circuit breaker. Circuit breakers become a specific reaction configuration (`retries: 2, escalate_after: 2, action: halt`), not a separate mechanism.

**Priority:** T2 — Adapt. Estimated effort: 6 hours (spec + integration with Module 14 and existing circuit breakers).

---

### 2. Module 14 (Metacognitive Monitor) — PostToolUse as Metadata Bus

**What changes:** Use PostToolUse hooks to extract and surface metadata from tool outputs, enabling the Monitor to observe agent state without polling or prompt injection.

**Why it works:** AO's Claude Code plugin installs a PostToolUse hook that intercepts `gh pr create` output, extracts the PR URL, and writes it to a session metadata file. The dashboard learns about PRs without polling. Applied to KF: PostToolUse hooks can extract mode outputs (decision classifications, confidence scores, artifact IDs) and write them to `.kf/state/` for the Monitor to observe.

**Spec delta:**
```yaml
# Add to Metacognitive Monitor → Observation Channels
metadata_bus:
  mechanism: PostToolUse hook
  trigger: After any Write|Edit|Bash tool call
  extraction:
    - Pattern match for KF-tagged outputs (decision_type, confidence, artifact_id)
    - Write extracted metadata to .kf/state/monitor_observations.jsonl
    - Append-only log — Monitor reads tail for recent state
  benefit: >
    Monitor observes agent state passively via tool output interception,
    not actively via prompt injection. Zero context cost.
  integration:
    - Feeds Operational Bounds metrics (context utilization, error rate)
    - Feeds Calibration Layer (confidence scores over time)
    - Feeds routing index updates (decisions made, artifacts produced)
```

**Priority:** T2 — Adapt. Estimated effort: 3 hours (hook script + state file format).

---

### 3. Module 03 (Coordination Patterns) — Dual Fingerprinting for Incremental Dispatch

**What changes:** When coordinating multi-step work that produces incremental outputs, track both "what exists" and "what was dispatched" as separate fingerprints.

**Why it works:** AO's `lastXxxFingerprint` (what exists on the PR) vs `lastXxxDispatchHash` (what was sent to the agent) enables new comments to be dispatched without re-processing unchanged ones. This is directly applicable to KF's Critic ↔ Builder revision loop — Critic produces findings, Builder addresses some, Critic re-reviews. Currently KF re-processes all findings on each loop iteration.

**Spec delta:**
```yaml
# Add to Coordination Patterns → Incremental Dispatch
dual_fingerprinting:
  pattern: Track state_fingerprint and dispatch_fingerprint separately
  application:
    critic_builder_loop:
      state_fingerprint: Hash of all current Critic findings
      dispatch_fingerprint: Hash of findings sent to Builder for revision
      delta: state_fingerprint != dispatch_fingerprint → new findings exist
      action: Dispatch only new/changed findings to Builder
    benefit: >
      Prevents Builder from re-addressing already-fixed findings.
      Reduces loop iterations. Aligns with 6.6.1 loop_exit_protocol.
```

**Priority:** T2 — Adapt. Estimated effort: 2 hours (spec change to Critic ↔ Builder loop protocol).

---

### 4. Module 03 (Coordination Patterns) — Plugin Slot Architecture Validation

**What changes:** No spec change needed. Document AO's 7-slot plugin architecture as validation of KF's mode-based composition model, and note the architectural gap.

**Why it matters:** AO separates a non-pluggable Lifecycle Manager core from 7 pluggable slots. KF's orchestrator (Agent Instructions) is the non-pluggable core; modes are the pluggable slots. The architectures are isomorphic. However, AO's slots have formal TypeScript interfaces with required methods; KF's mode contracts are prose-specified. This validates the direction but highlights that KF would benefit from formalizing mode interfaces.

**Accretion candidate:**
```yaml
accretion_candidate:
  source: Agent Orchestrator research
  novelty_type: architectural_validation
  knowledge_target: wiki/coordination/plugin-slot-architecture.md
  content: >
    AO's 7-slot plugin system validates KF's mode composition model.
    Gap: KF mode contracts are prose-specified; AO's are TypeScript interfaces.
    Future work: formalize mode interfaces (inputs, outputs, required methods)
    to enable static validation of mode chains.
```

**Priority:** T3 — Reference. No immediate action.

---

### 5. Module 09 (Debugger) — CI Failure Feedback Loop Pattern

**What changes:** Add a "feedback loop" diagnostic pattern to the Debugger spec for situations where automated tests provide iterative failure signals.

**Why it works:** AO's CI failure feedback loop (poll → detect failure → send logs to agent → agent fixes → poll again → verify) is a structured pattern for the common "tests are failing, fix them" debugging workflow. The key details: fingerprint the failure set so only *new* failures trigger re-dispatch, and escalate after N retries.

**Spec delta:**
```yaml
# Add to Debugger → Diagnostic Patterns
automated_feedback_loop:
  trigger: Iterative test/CI failure signals available
  protocol:
    1. Receive failure signal with failure details (logs, stack traces)
    2. Fingerprint the failure set (hash of failing test names + error types)
    3. Generate hypotheses from failure details (not just failure count)
    4. Apply fix, verify against reproduction
    5. On next failure signal: compare fingerprint to previous
       - Same fingerprint → fix didn't work, escalate hypothesis priority
       - Different fingerprint → original fix worked, new issue introduced
       - Subset fingerprint → partial fix, continue
    6. After {retries} iterations with same fingerprint → escalate to user
  integration: >
    Feeds into Operational Bounds reaction engine (retries + escalation).
    Fingerprint comparison is deterministic — no LLM needed.
```

**Priority:** T2 — Adapt. Estimated effort: 2 hours (spec addition to Module 09).

---

## Patterns Noted but Not Adopted

| Pattern | Reason for deferral |
|---------|-------------------|
| GraphQL batch enrichment with ETag caching | API optimization pattern. Reference for when KF tools query external APIs on polling cycles. Not current need. |
| OpenClaw bidirectional integration | Interesting orchestration-of-orchestrators pattern. Not relevant until KF coordinates with external systems. |
| Worktree isolation (`~/.worktrees/{project}/{session}/`) | Claude Code native capability. AO adds path safety assertions (`^[a-zA-Z0-9_-]+$`) worth noting. |
| tmux-based runtime management | Low-level process orchestration. KF operates at a higher abstraction level. |
| Self-built demo (61 merged agent PRs) | Impressive validation but not a transferable pattern. |

---

## Implementation Sequence

```
1. Dual fingerprinting for Critic ↔ Builder loop (Module 03)  ← quick spec win
2. PostToolUse metadata bus (Module 14)  ← depends on hook infrastructure from Orchestra plan
3. CI failure feedback loop (Module 09)  ← spec addition, no dependencies
4. Reaction engine (Module 16)  ← largest change, subsumes circuit breakers
5. Plugin slot documentation (accretion)  ← reference only
```

---

## Dependency Note

Items 2 and 4 depend on the Claude Code hook infrastructure established in the Orchestra integration plan. The implementation sequence should interleave: Orchestra hooks first → AO patterns on top.

---

## Version Target

Reaction engine (Module 16) is a significant architectural change warranting **KF 6.7.0**. The other items are spec additions that can land incrementally.
