---
title: Adversarial Critic framing produces self-fulfilling reject on sound output
source_mode: direct
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-16
tags: prompt-engineering, orchestration, critic, llm-failure-mode, empirical, calibration
related_entries:
  - methodologies/2026-05-13_critic-triage-routing-strategist-vs-defer-doc.md
domain: methodologies
topic: quality-gate
---

# Adversarial Critic Framing → Self-Fulfilling Reject

## The Pattern

When an LLM "Critic" or adversarial-review mode is instructed to **assume the output has at least one significant flaw**, it will produce at least one finding on every input — including well-grounded, sound output. Combined with a verdict rule that any High/Critical finding → reject, this guarantees systematic rejection regardless of input quality. The instruction creates the failure it claims to detect.

## Empirical Evidence

[project] wiki-linter pipeline, May 2026:

- **Stage 1 prompt fragment (original):** "Your goal is to find the failure mode the producing agent missed. Assume the output has at least one significant flaw."
- **Verdict rule:** Any High or Critical finding → `verdict=reject`.
- **Observed:** 9 sampled Critic calls (4 in initial qfqw probe, 5 in a follow-up live run) on legitimate orphan_link findings from the wiki-linter — all 9 produced `verdict=reject`, each invocation finding a different "High" severity issue. The variance across runs proved the rejection was framing-driven, not evidence-driven.
- **Cost:** Approximately $0.70 over 4 calls — not just a quality bug but a recurring spend.

## The Mechanism

Two stacked design choices push the model toward systematic reject:

1. **The "assume at least one flaw" instruction.** When you tell a language model to find something, it complies. If genuine flaws exist, it finds them. If not, it invents one — usually pitched as "speculative concern" or "missing edge case." The model is doing what was asked.
2. **The "any High → reject" verdict rule.** When (1) reliably produces at least one finding and the model is free to pick the severity, the path of least linguistic resistance is often "High" (the prompt's adversarial framing makes "Low" feel inappropriate). One High collapses the verdict to reject.

The two together form a closed loop. Soften only the verdict (Option B) and the prompt still produces noise. Soften only the prompt without explicitly permitting clean output (Option A done partially) and the model may still hedge by stretching for Mediums.

## The Fix (Option A from the original triage)

Replace the assumption with explicit permission for the "clean" outcome:

```
Your job is to surface real failure modes the producing agent missed, IF ANY EXIST.

Sound output is a valid result. If the worker output has no significant flaws, 
return adversarial_findings=[] and verdict="clean". DO NOT invent findings to 
justify the call. Empty findings on sound output is the correct answer, not a 
failure of the Critic.
```

Also tighten severity guidance: "reserve High/Critical for flaws that would break the action being proposed — not stylistic or speculative concerns."

## Why This Phrasing Works

- **"IF ANY EXIST"** caps the request — it permits a null finding set.
- **"Sound output is a valid result"** reframes the success criterion. The model is no longer being graded on its ability to surface flaws; it is being graded on accuracy.
- **"Do NOT invent findings to justify the call"** is the only line that directly cuts off the fabrication path. Without it, models that have internalized "be helpful by producing complete output" will still confabulate.
- **"Empty findings on sound output is the correct answer"** gives the model a positive frame for the null case — without it, returning an empty list can feel like task-failure.

## When This Applies

- Any LLM-as-Critic / red-team / adversarial-review prompt.
- Any "find the issue" style worker where the input may legitimately be clean.
- Any pipeline where a Critic's reject blocks downstream dispatch and false rejection has measurable cost (operator time, wasted compute, dropped legitimate output).

## When This Does NOT Apply

- Cases where the input is known to contain flaws and the task is "categorize the flaws." There, the assumption is accurate and the framing matches the task.
- One-shot security audits where over-finding is preferred to under-finding (the cost asymmetry runs the other way).

## Trap: "Soften the verdict instead"

It's tempting to keep the adversarial prompt and just loosen "High → reject" to "Critical → reject." This works less well than softening the prompt directly. The model still produces noise findings; you just push the rejection threshold up by one notch. The findings still pollute downstream logs and audit trails, and the model still spends tokens manufacturing speculative concerns. Fixing the prompt removes the work entirely.

## Source Context

Implemented in [project] iteration_loop, commit `4e10fd2` (closes [project]-qfqw). Test suite includes a regression-pin assertion that the calibration phrasing stays in place — see `iteration_loop/tests/test_critic_adversarial.py::test_compose_prompt_does_not_assume_flaws_exist`. The pin test prevents accidental revert.

## Empirical Validation (Controlled Replay, 2026-05-16)

After fixing the wiki (which removed all live orphans), validation was performed by reconstructing wiki state at commit `07635d6` (what the 02:00 fire actually saw) in a git worktree and replaying the 6 raw findings through the calibrated `critic_adversarial.critic_adversarial()`. Result:

| Pre-fix prompt | Post-fix prompt |
|---|---|
| 5/5 verdict=reject (live 02:00 fire) | **6/6 verdict=clean** |
| Avg cost ~$0.40/call (4-call sample) | Avg cost $0.12/call (6-call sample) |
| Total cost waste: $2+ per cycle | Total cost: $0.71 |

Cost dropped because the model stops manufacturing fabricated High-severity findings (which inflate token output). The first call paid the warm-cache miss ($0.21); subsequent calls amortized to ~$0.10 each.

**Interpretation:** "clean" is the correct verdict for legitimate orphan_link findings. The Critic's job is to surface flaws in the *worker output*, not the underlying wiki entry. An accurate orphan report is a sound worker output. The framing change correctly separated "did the worker do its job" from "is the world OK."

**Open calibration risk:** We've now seen the prompt swing from 100% reject to 100% clean on the same input. We have no negative-control data — i.e., we haven't fed the new prompt a deliberately broken finding to confirm it still catches real flaws. Next session worth doing: inject a synthetic finding with a wrong file path, wrong severity, and missing evidence, and confirm verdict=reject or =passable.

## Related

- **Critic-finding triage** (sibling entry) — routing strategy for findings AFTER Critic produces them; this entry fixes the Critic stage itself
- **Option B: Loosen verdict threshold** — alternative fix (less effective) — not yet a wiki entry
- **Option C: Add confidence field** — confidence-gated severity (complementary but not primary fix) — not yet a wiki entry
