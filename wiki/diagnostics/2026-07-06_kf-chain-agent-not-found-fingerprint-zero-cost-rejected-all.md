---
title: KF-chain agent-not-found fingerprint — findings=N rejected=N emitted=0 cost=$0
source_mode: debugger
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: stable
importance: 4
pinned: false
created: 2026-07-06
domain: diagnostics
topic: error-classification
tags: [error-classification, observability, grounding, quality-gate, classification]
related_entries:
  - patterns/2026-05-14_claude-cli-structured-output-vs-result-routing.md
  - infrastructure/2026-05-14_claude-cli-bare-disables-oauth-keychain-auth.md
  - compiler/2026-06-10_extract-section-cc-marker-stop-condition-over-extraction.md
---

# KF-Chain Agent-Not-Found Fingerprint

## Pattern

In [project]'s iteration-loop scheduler, a `claude --agent <mode>` subprocess that fails with "agent not found" (exit 1, empty stdout) produces a distinctive fingerprint in the scheduler summary and routing log that is easy to misread as a successful run with valid critic findings.

## The Fingerprint

**Scheduler summary (last JSON line of `~/.[project]/logs/iteration-loop-scheduler.out`):**
```json
{
  "workers": [
    {
      "name": "project-reviewer",
      "findings": 3,
      "emitted": 0,
      "rejected": 3,
      "cost": 0.0,
      "short_circuit_reason": null
    }
  ],
  "total_spent_usd": 0.0,
  "ceiling_hit": false
}
```

Three distinguishing signals:
1. `findings > 0` — worker produced output
2. `emitted = 0` and `rejected = findings` — all findings rejected at stage_1_critic
3. `cost = $0.00` — subprocess never billed (exited before API call)

**Routing log (`~/.claude/wiki/operations/routing-log/YYYY-MM.md`):**
```json
{
  "outcome": "rejected",
  "predicate_used": "v=reject adv=0 c=0.0000 | stage_1_critic: invalid_envelope_json (retri",
  "stage": "stage_4"
}
```

The `(retri` is a truncation of `(retried)` — the pipeline retried the subprocess once, same result.

## Root Cause

`kf_chain.py` calls `claude --agent <mode>` as a subprocess. When the compiled agent .md file has its YAML frontmatter in the wrong position (e.g., after the Sections navigation block instead of before it), Claude CLI's agent discovery fails silently: rc=1, stdout="", stderr="--agent 'critic' not found. Available agents: claude, cos, ...".

`_parse_envelope(completed.stdout)` returns None (empty stdout), setting `_chain_error = "invalid_envelope_json"`, which forces `verdict = "reject"` in `baking_pipeline.py:396`. The rejection is logged with `c=0.0000` because cost extraction runs after the parse — parse failure returns before extracting cost.

## How to Confirm

```bash
# Step 1: check routing log for the pattern
grep '"invalid_envelope_json"' ~/.claude/wiki/operations/routing-log/$(date +%Y-%m).md | head -3

# Step 2: verify the subprocess failure directly
claude --agent 'critic' --print 'test' 2>&1 | head -3
# Expected on broken build: "--agent 'critic' not found. Available agents: ..."

# Step 3: check kf-compile output for frontmatter position
head -10 ~/.claude/skills/critic.md
# Broken: frontmatter appears AFTER the Sections nav block, not before it
# Healthy: "---\nname: critic\n..." is the FIRST block
```

## Fix Class

- **Immediate:** Recompile knowledgeforge-core (`kf-compile`) to fix frontmatter position
- **Observability (shipped 2026-07-06, [project]-m8os):** `kf_chain.py` now includes `completed.stderr[:200]` in the rejection reason, so future occurrences show `rc=1: invalid_envelope_json: --agent 'critic' not found...` instead of the opaque `invalid_envelope_json`

## When This Pattern Does NOT Apply

- `cost > 0` → subprocess billed → agent ran successfully (rejection was a real critic verdict)
- `short_circuit_reason` is set → cache hit short-circuited the chain before subprocess
- `findings = 0` → worker produced no output (different failure mode; worker script itself may have crashed or returned empty envelope)

## Grounding

Observed 2026-07-06 during /nw-overnight review of [project] [project]-0b0f (project-reviewer anchor). Pattern held consistently across 12 consecutive rejections over 5 nights (2026-07-02 to 2026-07-06), all same root cause (knowledgeforge-core-oxp: kf-compile emitting mispositioned frontmatter). Confirmed by manual subprocess reproduction using `claude --agent 'critic' --print 'test'` in isolation.

**Verification steps taken:**
- Reproduced agent invocation failure directly in shell
- Inspected compiled agent file frontmatter position
- Traced stderr through kf_chain.py error handler
- Cross-referenced 12 consecutive scheduler runs with same error pattern
- Verified stderr now includes agent-not-found message after observability patch ([project]-m8os)

## Source Context

Extracted 2026-07-06 during /nw-overnight review of the baking-pipeline's stage_1_critic behavior. The iteration-loop scheduler was emitting high-volume (12/night) project-reviewer findings with 100% rejection rate and $0 cost, suggesting a systematic subprocess failure rather than valid critic verdicts. Manual diagnosis: knowledgeforge-core compilation was placing YAML frontmatter after the Sections navigation block (introduced in a stale kf-compile invocation). Claude CLI's agent discovery reads frontmatter-first, so it fails silently when frontmatter is not the opening block. Result: rc=1, empty stdout, which surfaces as invalid_envelope_json rejection. The pattern is reusable for debugging future kf-chain subprocess failures: high findings + high rejection + zero cost is a fingerprint for early subprocess exit.

