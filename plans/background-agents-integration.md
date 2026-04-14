# Background Agents → KnowledgeForge Integration Plan

**Source:** ColeMurray/background-agents + Ramp Builders blog + Modal blog + Ramp Labs self-maintaining
**Research date:** 2026-04-13 | **Plan version:** 1.0

---

## Strategic Value

Background Agents is primarily a reference architecture — its patterns are relevant when KF moves to hosted multi-tenant deployment, not for the current Claude Code/Projects runtime. However, two patterns transfer immediately: pure decision functions for operational logic, and the reproduce-before-fix discipline validated across Ramp's production systems.

The Ramp sources provide the strongest operational evidence in the entire research set: 50%+ of merged PRs written by agents, 1,000+ auto-generated monitors, and the explicit lesson that nightly audits without specific missions fail while monitor-driven maintenance succeeds.

---

## Module Updates

### 1. Module 09 (Debugger) — Reproduce Before Fix (Mandatory Step)

**What changes:** Add "reproduce the failure" as a mandatory step in the Debugger protocol, between Phase 4 (Root Cause Identification) and Phase 5 (Remediation & Prevention).

**Why it works:** This is the single most validated pattern in the research — confirmed independently by Background Agents, Ramp self-maintaining, and Agent Orchestrator. Ramp's explicit finding: "Sandboxed reproduction improves results. The agent reproduces the failure against live code and only pushes a fix once that reproduction test passes." Adding it as a mandatory protocol step (not advisory) prevents the Debugger's documented failure mode of recommending fixes based on hypothesis alone.

**Spec delta:**
```yaml
# Add to Debugger → Diagnostic Protocol → between Phase 4 and Phase 5
phase_4b_reproduction:
  title: "Failure Reproduction"
  position: After root cause identification, before remediation
  mandatory: true  # Not skippable

  protocol:
    1. Construct minimal reproduction case from root cause analysis
    2. Execute reproduction in isolated environment (sandbox, test, REPL)
    3. Confirm reproduction triggers the same symptoms as reported
    4. If reproduction fails:
       - Root cause identification confidence drops by 0.2
       - Return to Phase 3 with additional hypothesis: "Root cause is correct
         but reproduction conditions are incomplete"
    5. If reproduction succeeds:
       - Lock root cause as confirmed (confidence floor: 0.85)
       - Reproduction case becomes the verification test for the fix

  skip_conditions:
    - Problem is purely conceptual (architectural review, spec analysis)
    - No executable environment available
    - Reproduction would require production data access (flag as limitation)

  output:
    reproduction_status: enum[confirmed, failed, skipped]
    reproduction_case: string  # Exact steps or code to reproduce
    verification_test: string  # How to confirm the fix works
```

**Priority:** T1 — Adopt. This should be in the next spec update. Estimated effort: 1 hour (spec addition to Module 09).

---

### 2. Module 16 (Operational Bounds) — Pure Decision Functions

**What changes:** Extract KF's operational decision logic (circuit breakers, context pressure responses, mode failure handling) into pure functions with no side effects.

**Why it works:** Background Agents' `decisions.ts` implements all spawn lifecycle decisions as pure functions that take state and return a decision. They're independently testable and composable. KF's circuit breakers are currently embedded in mode agent prose specs — untestable, unverifiable, and spread across multiple modules.

**Spec delta:**
```yaml
# Add to Operational Bounds → Decision Functions
pure_decision_architecture:
  principle: >
    All operational decisions (circuit break, escalation, compression,
    mode retry) are pure functions: input state → output decision.
    No side effects in the decision function. Side effects happen
    in the caller after the decision is made.

  decision_catalog:
    circuit_break:
      input: {mode, consecutive_failures, max_retries}
      output: enum[retry, halt, escalate]
      logic: |
        if consecutive_failures >= max_retries: halt
        elif consecutive_failures >= max_retries - 1: escalate
        else: retry

    context_response:
      input: {utilization_pct, active_mode, task_criticality}
      output: enum[continue, compress, handoff, halt]
      logic: |
        if utilization_pct < 80: continue
        elif utilization_pct < 90 and task_criticality == high: compress
        elif utilization_pct < 90: handoff
        else: halt

    spawn_decision:  # Adapted from background-agents decisions.ts
      input: {session_status, has_active_ws, time_since_last, failure_count, cooldown_period}
      output: enum[resume, restore, skip, wait, spawn, block]
      logic: |
        priority_order:
          1. existing_session + ready → resume
          2. snapshot_available → restore
          3. spawning_or_connecting → skip
          4. ready + active + recent → skip
          5. ready + no_ws + within_cooldown → wait
          6. failures >= 3 within 5min → block (circuit breaker)
          7. all_clear → spawn

  testability:
    rule: >
      Every decision function must be expressible as a truth table.
      If it can't be written as input → output without context,
      it's not pure — refactor until it is.
    test_format: |
      Given: {state}
      When: decision_function(state)
      Then: {expected_output}
```

**Priority:** T2 — Adapt. Estimated effort: 4 hours (refactor existing circuit breaker specs into pure decision catalog).

---

### 3. Module 21 (Knowledge Accretion) — Monitor Generation from Code Diffs

**What changes:** Add "monitor/validation generation" as an accretion pattern — when code changes are made, generate corresponding validation checks.

**Why it works:** Ramp's self-maintaining system generates Datadog monitors from every PR merge — one monitor per ~75 lines of code, 1,000+ monitors total. The principle transfers: when KF modules are updated, corresponding wiki validation checks, eval criteria, or quality gate updates should be generated. This closes the "code changed but tests didn't" gap.

**Spec delta:**
```yaml
# Add to Knowledge Accretion → Accretion Patterns
monitor_generation:
  trigger: Module spec change (new version, new capability, changed protocol)
  action:
    - Generate validation check for the changed behavior
    - File check to wiki/validation/{module}_{check_name}.md
    - Link check to source module version
  example:
    change: "Module 09 adds mandatory reproduce-before-fix step"
    generated_check:
      name: debugger_reproduction_present
      validates: "Debugger output includes reproduction_status field"
      severity: sev_2_if_missing
  
  ramp_lesson:
    succeeded: Monitor-driven maintenance (specific mission per trigger)
    failed: Nightly audit without specific mission (same ground, ineffective)
    kf_implication: >
      Don't schedule generic "lint everything" runs.
      Generate specific validation checks per change, triggered by
      the change itself.
```

**Priority:** T2 — Adapt. Estimated effort: 3 hours (spec + exemplar validation checks for existing modules).

---

### 4. Module 21 (Knowledge Accretion) — Artifact-Embedded State (Dedup Pattern)

**What changes:** Document Ramp's pattern of embedding deduplication state in the artifact it describes, as a zero-database dedup technique for accretion.

**Why it works:** Ramp stores the fix PR link in the Datadog monitor description itself. Subsequent agents see the link and stand down — no external deduplication database needed. Applied to KF accretion: when a wiki entry is created from a Critic finding, embed the finding's fingerprint in the wiki entry metadata. Future Critic runs that surface the same finding can skip accretion by checking the wiki entry's embedded fingerprint.

**Spec delta:**
```yaml
# Add to Knowledge Accretion → Deduplication
artifact_embedded_dedup:
  principle: >
    Store deduplication state IN the artifact it describes.
    No external dedup database needed.
  implementation:
    - Every accreted wiki entry includes source_fingerprint in frontmatter
    - Fingerprint = hash of (source_mode + finding_key + core_content_hash)
    - Before accreting a new candidate: check if any existing entry
      has a matching source_fingerprint
    - If match: skip accretion (already captured)
    - If partial match (same finding_key, different content): update existing entry
  benefit: >
    Self-contained dedup. Works offline. No state synchronization.
    Wiki entries are the source of truth for what's been captured.
```

**Priority:** T2 — Adapt. Estimated effort: 2 hours (spec + frontmatter format).

---

### 5. Reference Architecture — Durable Objects for Hosted KF

**What changes:** Document as reference architecture for future multi-tenant KF deployment.

**Why it matters (future):** SessionDO with private SQLite per session, WebSocket hibernation for zero-cost idle connections, and child sessions as first-class primitives are the right architecture for a hosted KF. Key details worth preserving:

- 8-table schema with 30 migrations (session, participants, messages, events, artifacts, sandbox, ws_client_mapping, subscriptions)
- WebSocket hibernation: `ws_client_mapping` persists auth across DO cold starts
- Proactive sandbox warming on keystroke (start before user hits Enter)
- Child sessions with depth tracking for parallel sub-tasks

**Accretion candidate:**
```yaml
accretion_candidate:
  source: Background Agents research
  novelty_type: reference_architecture
  knowledge_target: wiki/infrastructure/durable-objects-session-architecture.md
  staleness_risk: slow_decay
  importance: 2  # Future reference, not current need
```

**Priority:** T3 — Reference. Accrete to wiki for when the hosting architecture conversation happens.

---

## Ramp Operational Lessons (Cross-Cutting)

These aren't module-specific updates but operational principles validated at Ramp's scale:

| Lesson | KF Implication |
|--------|---------------|
| "Detect everything, notify selectively" | Module 14 should observe broadly but intervene narrowly |
| Nightly audits without specific missions fail | Don't schedule generic linter runs — trigger-specific checks |
| "Agents should have agency — limited only by model intelligence" | KF modes should provide maximum context, not maximum constraint |
| Triage before act (fast classifier before expensive work) | Module 13 Decision Classification is this — validate it's always first |
| Multiplayer requires user-scoped tokens (not bot tokens) | Module 20 Permission relevance when KF supports multiple users |
| GPT-5 for debugging, Opus 4.6 for triage | Model selection per task type — relevant for KF's future self-hosted inference layer |

---

## Implementation Sequence

```
1. Reproduce-before-fix in Debugger (Module 09)       ← spec addition, highest confidence
2. Artifact-embedded dedup (Module 21)                 ← spec addition, enables #3
3. Monitor generation from changes (Module 21)         ← depends on dedup for self-check
4. Pure decision functions (Module 16)                 ← refactor, medium effort
5. Durable Objects reference architecture (accretion)  ← documentation only
```

---

## Version Target

Reproduce-before-fix is a Protocol-level addition to Module 09. Combined with the pure decision function refactor of Module 16, these warrant inclusion in **KF 6.7.0**.
