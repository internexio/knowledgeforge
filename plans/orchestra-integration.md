# Orchestra → KnowledgeForge Integration Plan

**Source:** paulonasc/orchestra v0.5.1 | Bash + TypeScript
**Research date:** 2026-04-13 | **Plan version:** 1.0

---

## Strategic Value

Orchestra solves session amnesia — agents forget everything between runs. Its file-based hook + state architecture survives compaction, which is KF's single biggest unsolved operational failure mode in Claude Code. Three patterns are directly adoptable; two require adaptation.

---

## Module Updates

### 1. Module 14 (Metacognitive Monitor) — PostToolUse Edit-Count Nudge

**What changes:** Add a new intervention strategy to the Monitor's ladder — a tool-response-injected nudge after N edits without checkpoint.

**Why it works:** Agents cannot ignore tool responses the way they ignore prose instructions. Orchestra's `orchestra-post-tool-nudge.sh` counts `Edit|Write` calls per session and injects at threshold 10. This is a direct patch for the Monitor's current gap: it detects stuck agents but has no mechanism for "drifting without saving" agents.

**Spec delta:**
```yaml
# Add to mode_monitoring_profiles → all modes
edit_count_nudge:
  trigger: PostToolUse hook counting Edit|Write|Bash(write) calls
  threshold: 10 (configurable per mode)
  injection: "KF: {N} edits since last checkpoint. Consider saving progress."
  injection_target: tool_response (not user prompt)
  rationale: "Tool responses are attended to; prompt-level reminders are skipped"
  reset_on: checkpoint, manual save, session boundary
```

**Implementation:** Claude Code hook script. ~30 lines bash. File counter at `.kf/edit_count`.

**Priority:** T1 — Adopt. Estimated effort: 2 hours.

---

### 2. Module 19 (Memory Architecture) — PreCompact/PostCompact Survival Chain

**What changes:** Add compaction survival hooks as a formalized Tier 1/Tier 2 persistence mechanism.

**Why it works:** Orchestra's three-hook compaction chain is the only production-validated approach to surviving Claude Code's context compaction. PreCompact flushes state + echoes context. PostCompact re-injects *minimal* paths/summaries — intentionally less than SessionStart to avoid re-triggering compaction. This asymmetry is the key insight KF currently lacks.

**Spec delta:**
```yaml
# Add to Memory Architecture → Tier 1 lifecycle
compaction_survival:
  pre_compact:
    actions:
      - Flush routing index to .kf/state/routing_index.yaml
      - Flush active Tier 2 state to .kf/state/tier2_{mode}.yaml
      - Write session summary to .kf/state/session_summary.md
      - Echo critical context as hook output (injected into compaction input)
    budget: Full state — compaction hasn't happened yet

  post_compact:
    actions:
      - Inject routing index paths (not contents)
      - Inject one-line Tier 2 summary (not full state)
      - Inject active task name + current step only
    budget: Minimal — avoid re-triggering compaction
    asymmetry_rule: >
      PostCompact MUST inject less than PreCompact echoed.
      If PostCompact injects full state, context immediately re-fills
      and triggers another compaction cycle.

  session_start:
    actions:
      - Full state injection (routing index, Tier 2, task context)
      - MEMORY.md filtered by active repo/project
    budget: Full — session start has maximum headroom
```

**Implementation:** Three hook scripts + `.kf/state/` directory structure. ~150 lines total.

**Priority:** T1 — Adopt. Estimated effort: 4 hours. This is the highest-impact single change for Claude Code deployment.

---

### 3. Module 19 (Memory Architecture) — SessionStart Silent Context Injection

**What changes:** Use `additionalContext` hook output to silently load KF session state before Claude's first turn.

**Why it works:** The `SessionStart` hook can inject text into the conversation invisibly to the user. KF can load active mode, last decision, current context tier, and routing index snapshot without cluttering the conversation. This replaces the current approach of relying on CLAUDE.md static loading for session recovery.

**Spec delta:**
```yaml
# Add to Memory Architecture → Session Lifecycle
session_start_injection:
  hook_event: SessionStart
  output_format:
    hookSpecificOutput:
      hookEventName: SessionStart
      additionalContext: |
        [KF SESSION STATE]
        Active mode: {from .kf/state/active_mode}
        Routing index: {from .kf/state/routing_index.yaml}
        Last decision: {from routing index, most recent entry}
        Current task: {from .kf/state/task_context.yaml}
        [END KF SESSION STATE]
  source_discrimination:
    startup: Full state injection
    resume: Full state injection
    clear: Routing index only (user cleared intentionally)
    compact: Minimal injection (PostCompact handles this)
```

**Implementation:** SessionStart hook script reading `.kf/state/`. ~50 lines.

**Priority:** T1 — Adopt. Estimated effort: 1 hour (depends on compaction hooks existing first).

---

### 4. Navigator (Module 01) / All Mode Agents — Lazy Command File Dispatch

**What changes:** Split KF mode agents into a lightweight router (always loaded) and deferred instruction files (loaded on demand per activation).

**Why it works:** Orchestra's SKILL.md is 247 lines — a lookup table. Full implementation lives in 8 command files, each loaded only when that command fires. Current KF mode agents load their full spec every activation, consuming context budget even when most of the spec is irrelevant to the current task step. Splitting would reduce constant context load by an estimated 40-60%.

**Spec delta:**
```yaml
# Architectural change to all mode agents
lazy_dispatch:
  router:
    location: CLAUDE.md (static zone)
    content: Mode trigger phrases + one-line descriptions + file paths
    budget: ~500 tokens total for all modes (vs ~8000+ currently)
    rule: "Read ONE mode file per activation. Do not preload."

  mode_files:
    location: .claude/kf/modes/{mode_name}.md
    content: Full mode protocol, quality gates, integration points
    loaded_when: Mode is activated by router
    unloaded_when: Mode transition completes

  ci_validation:
    pattern: Orchestra's gen-skill.ts
    check: All mode files referenced in router exist and are non-empty
```

**KF-specific adaptation required:** Orchestra uses string-match subcommand dispatch. KF needs semantic intent classification in the router, which is harder to split from the mode instructions. The router must include enough semantic context to classify correctly without loading the full spec.

**Risk:** Router too thin → misroutes. Router too thick → loses the context savings. Need to calibrate empirically.

**Priority:** T2 — Adapt. Estimated effort: 8-12 hours (split + validate no routing regression).

---

### 5. Module 12 (Calibration Layer) — Cross-Provider Judge Isolation

**What changes:** Specify that behavioral evals use a different model family for judging than the model being evaluated.

**Why it works:** Orchestra uses `gpt-5.4-mini` specifically to avoid self-evaluation bias. KF's Calibration Layer specifies multi-run assessment but doesn't address the known ceiling of single-model self-evaluation (documented in KF's own PR/FAQ findings: self-preference bias makes Devil's Advocate the weakest link).

**Spec delta:**
```yaml
# Add to Calibration Layer → Bias Taxonomy
judge_isolation:
  rule: >
    When running behavioral evaluations, the judge model MUST be from
    a different model family than the agent being evaluated.
  rationale: >
    Self-evaluation bias is documented (KF PR/FAQ research: two-model
    critique captures ~80% of multi-model benefit). Cross-provider
    judging eliminates the self-preference confound.
  implementation:
    claude_agent: Use OpenAI judge (gpt-5.4-mini or equivalent)
    openai_agent: Use Claude judge
    fallback: If cross-provider unavailable, use different model tier
              (e.g., Opus evaluates Sonnet output)
```

**Priority:** T1 — Adopt. Estimated effort: 1 hour (spec change only; implementation is per-eval).

---

### 6. Module 17 (Temporal Knowledge) — Research Staleness Gate

**What changes:** Add a freshness check that fires before building on previously-researched material.

**Why it works:** Orchestra flags research older than 7 days when an agent is about to build from it. KF has importance-weighted decay and domain half-life tables but no concrete "check before build" gate.

**Spec delta:**
```yaml
# Add to Temporal Knowledge → Staleness Detection
research_staleness_gate:
  trigger: Before Builder or Expert mode operates on knowledge with staleness_risk != stable
  check: >
    If source material's last_verified date exceeds the domain half-life
    from the decay table, flag to user: "This research is {N} days old
    (domain half-life: {H} days). Verify before building on it?"
  action_on_stale:
    - Flag with severity proportional to staleness ratio (age / half-life)
    - Do not block — user decides whether to proceed
    - If user proceeds, tag output with caveat: "Built on unverified research from {date}"
```

**Priority:** T2 — Adapt. Estimated effort: 2 hours.

---

## Patterns Noted but Not Adopted

| Pattern | Reason for deferral |
|---------|-------------------|
| Worktree auto-link via SessionStart hook | Useful but not KF-specific — general Claude Code ergonomics |
| Two-tier telemetry (community → anonymous → off) | Relevant only if KF becomes a distributed product |
| CLAUDE.md HTML comment markers for idempotent update | Good practice but tooling concern, not framework concern |
| Heartbeat cron anti-recursion | Edge case — document as known hazard, don't spec a module |

---

## Implementation Sequence

```
1. PreCompact/PostCompact hooks (Module 19)     ← foundation for everything else
2. SessionStart silent injection (Module 19)     ← depends on state files from #1
3. PostToolUse edit-count nudge (Module 14)      ← independent, quick win
4. Cross-provider judge isolation (Module 12)    ← spec change, no code dependency
5. Research staleness gate (Module 17)           ← spec change + minor hook
6. Lazy command dispatch (all modes)             ← largest effort, highest risk
```

---

## Version Target

These changes collectively warrant a **KF 6.7.0** minor version bump. The compaction survival chain is the marquee feature — it's the first time KF has a validated answer to "what happens when Claude Code compacts mid-session."
