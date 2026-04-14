# claude-code-hooks-mastery → KnowledgeForge Integration Plan

**Source:** disler/claude-code-hooks-mastery | Python (UV single-file scripts)
**Research date:** 2026-04-13 | **Plan version:** 1.0

---

## Strategic Value

This repo is the definitive hooks reference — 13 hook events fully implemented with production patterns. The single most important finding: **Stop hooks with `decision: "block"` force Claude to continue working when it tries to stop.** This is a mandatory completion gate KF currently lacks. Combined with `PermissionRequest` input mutation (pre-execution sanitization) and command-level scoped hooks, this repo provides three patterns that directly patch KF gaps.

---

## Module Updates

### 1. Module 14 (Metacognitive Monitor) — Stop Hook as Mandatory Completion Gate

**What changes:** Add a Stop hook that validates mode output completeness before allowing session termination. `decision: "block"` forces continuation until validation passes.

**Why it works:** KF's quality gates are advisory — they list what should be present but can't enforce it. The Stop hook creates a hard enforcement layer: Claude literally cannot stop until the validation script confirms all required elements exist.

**Spec delta:**
```yaml
# Add to Metacognitive Monitor → Enforcement Layer
stop_gate:
  mechanism: Stop hook with decision: "block" response
  validation_script: .claude/hooks/kf-stop-validator.py
  protocol:
    1. On Claude Stop event, read stop hook stdin JSON
    2. Check stop_hook_active field — if true, skip (prevent infinite loop)
    3. Determine active KF mode from .kf/state/active_mode
    4. Load mode-specific completion checklist
    5. Validate output against checklist
    6. If incomplete: return {"decision": "block", "reason": "Missing: {items}"}
    7. If complete: return {"decision": "approve"} (or exit 0)

  mode_checklists:
    builder:
      - PDIA elements present (Problem, Design, Implementation, Acceptance)
      - Design decisions tagged with decision type
      - Testability metadata included
    critic:
      - Findings have location + fix
      - Severity levels applied
      - Finding count ≤ 15
    expert:
      - Adversarial depth section present
      - decision_type_exercised field present
    strategist:
      - Trade-offs explicit
      - Reversibility assessed
    synthesizer:
      - Every pattern has ≥1 anti-pattern
      - Applicability boundaries explicit
    debugger:
      - Root cause confidence > 0.8
      - Diagnostic path documented

  infinite_loop_guard:
    field: stop_hook_active (boolean in Stop hook stdin)
    rule: >
      If stop_hook_active is true, the current stop was caused by a
      previous block. Do NOT block again — this prevents infinite loops.
      Log the incomplete state and allow stop.

  scoped_variant:
    mechanism: Command-level hooks in slash command frontmatter
    example: >
      /kf-build could declare its own Stop validators that only fire
      for that command — e.g., validate spec file exists and contains
      required sections. Other commands use the default validator.
```

**Critical implementation detail:** The `stop_hook_active` guard is mandatory. Without it, blocking a Stop causes Claude to continue, which eventually triggers another Stop, which blocks again — infinite loop. The guard field is provided in the hook's stdin JSON.

**Priority:** T1 — Adopt. Estimated effort: 4 hours (validator script + per-mode checklists). This is the highest-leverage single pattern from the entire research set.

---

### 2. Module 20 (Permission Model) — PermissionRequest Input Mutation

**What changes:** Extend KF's Permission Model from allow/deny decisions to include pre-execution input mutation via the `PermissionRequest` hook's `updatedInput` field.

**Why it works:** The PermissionRequest hook can rewrite tool inputs before the tool runs. Current KF Permission (Module 20) only gates actions (allow or deny). Input mutation enables a third option: allow, but sanitize first. Use cases: path normalization (prevent writes outside `.kf/`), safety-flag injection (add `--dry-run` to destructive commands), cost estimate annotation (inject budget context into API calls).

**Spec delta:**
```yaml
# Add to Permission Model → Capability Gates
input_mutation:
  mechanism: PermissionRequest hook with updatedInput field
  hook_output:
    hookSpecificOutput:
      hookEventName: PermissionRequest
      decision:
        behavior: "allow"
        updatedInput:
          # Original tool input, modified before execution
          command: "{sanitized_command}"
        message: "Input sanitized: {what changed}"

  mutation_policies:
    path_normalization:
      trigger: Write|Edit tool with path outside allowed directories
      action: Rewrite path to .kf/ or reject
    safety_flags:
      trigger: Bash tool with destructive commands (rm, drop, truncate)
      action: Inject --dry-run or --interactive flag
    cost_annotation:
      trigger: Tool calls to external APIs
      action: Inject budget context header or parameter

  audit:
    rule: Every mutation logged to .kf/state/permission_mutations.jsonl
    fields: [timestamp, original_input, mutated_input, policy_applied]

  relationship_to_deny:
    - Deny = block execution entirely (existing behavior)
    - Mutate = allow execution with modified input (new behavior)
    - Prefer mutation over denial when the intent is valid but the execution is unsafe
```

**Priority:** T1 — Adopt. Estimated effort: 3 hours (hook script + mutation policies).

---

### 3. Module 14 (Metacognitive Monitor) — Command-Level Scoped Hooks

**What changes:** Document the pattern of declaring hooks in slash command frontmatter so they fire only for that command.

**Why it works:** The `/plan_w_team` example declares Stop hook validators that enforce 7 required sections — but only when that specific command is running. Other commands aren't affected. Applied to KF: `/kf-build` could have Builder-specific Stop validation, `/kf-critique` could have Critic-specific validation, without cross-contamination.

**Spec delta:**
```yaml
# Add to Metacognitive Monitor → Scoped Monitoring
command_scoped_hooks:
  mechanism: Slash command frontmatter hook declarations
  pattern:
    # In .claude/commands/kf-build.md frontmatter:
    hooks:
      Stop:
        - hooks:
            - type: command
              command: >-
                uv run .claude/hooks/validators/kf-builder-stop.py
            - type: command
              command: >-
                uv run .claude/hooks/validators/validate_file_contains.py
                --directory specs --extension .md
                --contains '## Problem' --contains '## Design Decisions'

  benefit: >
    Mode-specific enforcement without global hook pollution.
    Default Stop validator handles general KF quality gates.
    Command-level validators add mode-specific requirements.

  layering:
    global: .claude/settings.json Stop hooks (always fire)
    command: Slash command frontmatter hooks (fire only for that command)
    execution: Both layers execute — command hooks are additive, not replacement
```

**Priority:** T1 — Adopt. Estimated effort: 2 hours (slash command definitions + validator scripts).

---

### 4. Module 19 (Memory Architecture) — `$CLAUDE_ENV_FILE` Session Persistence

**What changes:** Document `$CLAUDE_ENV_FILE` as a mechanism for persisting environment variables across a Claude Code session, usable by SessionStart hooks.

**Why it works:** Writing `KEY=VALUE` to the path specified by `$CLAUDE_ENV_FILE` persists env vars for the session duration. KF can use this to set `KF_ACTIVE_MODE`, `KF_SESSION_ID`, `KF_LAST_DECISION_TYPE` as env vars readable by all subsequent hooks without file I/O.

**Spec delta:**
```yaml
# Add to Memory Architecture → Session Lifecycle
env_file_persistence:
  mechanism: $CLAUDE_ENV_FILE (available in SessionStart hook)
  usage:
    session_start_hook: |
      echo "KF_SESSION_ID=$(date +%s)" >> "$CLAUDE_ENV_FILE"
      echo "KF_ACTIVE_MODE=none" >> "$CLAUDE_ENV_FILE"
      echo "KF_EDIT_COUNT=0" >> "$CLAUDE_ENV_FILE"
  benefit: >
    Env vars are available to all subsequent hooks without file reads.
    Faster than .kf/state/ file lookups for frequently-accessed state.
  limitation: >
    Only available in SessionStart. Cannot be updated mid-session via hooks.
    For mutable state, continue using .kf/state/ files.
```

**Priority:** T2 — Adapt. Estimated effort: 30 minutes (documentation + SessionStart hook update).

---

### 5. Module 17 (Temporal Knowledge) — PreCompact Transcript Backup

**What changes:** Add PreCompact hook behavior that backs up the full transcript before compaction.

**Why it works:** `pre_compact.py` in the hooks-mastery repo reads the transcript path from stdin and copies it to a timestamped backup. KF should adopt this as a Tier 3 (archived history) preservation mechanism — the full transcript is the richest source for Verbatim History Mining (Module 24).

**Spec delta:**
```yaml
# Add to Temporal Knowledge → Compaction Lifecycle
transcript_backup:
  mechanism: PreCompact hook
  trigger: Manual or auto compaction
  action:
    - Read transcript_path from hook stdin JSON
    - Copy to .kf/transcripts/{session_id}_{timestamp}.jsonl
    - Optionally feed to Module 24 (Verbatim History Mining) for indexing
  retention: >
    Keep last 5 transcripts per session. Older transcripts archived
    to .kf/archive/ with metadata-only index for search.
```

**Priority:** T2 — Adapt. Estimated effort: 1 hour.

---

## Hook Execution Limits Reference

From the official docs and this repo, for KF hook design:

| Type | Default Timeout | KF Usage |
|------|----------------|----------|
| Command | 600 seconds | Stop validators, PreCompact backup |
| HTTP | 30 seconds | Not currently planned |
| Prompt | 30 seconds | Not recommended — adds LLM latency to hook chain |
| Agent | 60 seconds | Stop validation when deeper codebase verification needed |

**Design rule for KF hooks:** Prefer command type. Keep hooks under 5 seconds for PostToolUse (fires frequently). Stop validators can take longer since they fire once per session.

---

## Patterns Noted but Not Adopted

| Pattern | Reason for deferral |
|---------|-------------------|
| TTS notification system (ElevenLabs → OpenAI → pyttsx3) | Accessibility feature, not framework concern |
| SubagentStop LLM-summarized audio | Interesting UX but not KF's problem space |
| `fcntl.flock` for concurrent audio queue | Concurrency primitive. Document as reference for parallel hook coordination. |
| Agent naming in SubagentStop | Personalization. Not relevant to KF. |

---

## Implementation Sequence

```
1. Stop hook validator with mode checklists (Module 14)  ← highest impact
2. PermissionRequest input mutation (Module 20)          ← security layer
3. Command-level scoped hooks (Module 14)                ← requires slash commands
4. PreCompact transcript backup (Module 17)              ← quick win
5. $CLAUDE_ENV_FILE persistence (Module 19)              ← documentation + minor hook
```

---

## Dependency Note

The Stop hook validator is the foundation. Command-level scoped hooks build on top of it. Both depend on the `.kf/state/active_mode` file established in the Orchestra integration plan's SessionStart injection.

---

## Version Target

Stop hook completion gate + PermissionRequest mutation are significant enforcement additions warranting **KF 6.7.0**. These transform quality gates from advisory to mandatory.
