---
title: Reviewer Sovereignty via disable-model-invocation and Verbatim Output Constraint in Claude Code Plugins
source_mode: synthesizer
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.90
staleness_risk: slow_decay
importance: 4
created: 2026-07-14
domain: integration
topic: external-tools
tags: adversarial, quality-gate, api, delegation, chain
related_entries: []
---

# Reviewer Sovereignty via `disable-model-invocation` + Verbatim Output Constraint

## Pattern: Preventing Reviewer Capture When Delegating to External Models

When building a Claude Code slash command that delegates reasoning to an external model (Gemini, GPT-4o, etc.), two constraints together prevent **reviewer capture** — the failure mode where Claude softens, summarizes, or reinterprets another model's critique:

1. **`disable-model-invocation: true`** in the command's frontmatter opts Claude out of LLM processing entirely. Claude becomes a transport pipe — it receives the subprocess stdout and emits it without any model involvement.

2. **Explicit verbatim constraint** in the command markdown: "Return the command stdout verbatim, exactly as-is. Do not paraphrase, summarize, or add commentary before or after it."

Without `disable-model-invocation`, Claude's default behavior is to interpret and re-present tool output — findings get softened, severity gets hedged, adversarial framing gets replaced with balanced perspective. The verbatim constraint catches cases where disable-model-invocation isn't available; disable-model-invocation makes the verbatim constraint structurally enforced.

## When This Applies

- Any Claude Code plugin where a different model/tool performs the actual analysis
- Adversarial review systems, security audits, second-opinion patterns
- Situations where the reviewer's output must reach the user unmediated by Claude's interpretation layer
- Delegated reasoning chains where the external model's framing must be preserved intact

## When This Does NOT Apply

- When Claude IS the reviewer — no reviewer-capture risk exists, verbatim constraint is irrelevant
- When Claude adds genuine value post-processing (e.g., routing external output to the right action or downstream consumer)
- When the external tool output is structured data meant for further processing, not human consumption
- When intermediate summaries or reframing improve clarity for the end user

## Implementation Notes

- `disable-model-invocation: true` is a Claude Code plugin API flag — available in command-definition frontmatter only, not in CLAUDE.md or skills
- The `allowed-tools` list still applies even with disable-model-invocation — the command can still call node/git subprocesses
- The verbatim constraint should appear even WITH disable-model-invocation as defense-in-depth and explicit documentation of intent
- The adversarial framing (system prompt, attack surface, attack heuristics) lives entirely in the external reviewer's prompt, not in Claude's instruction layer
- Verify the external tool's output reaches stdout cleanly; stderr or log output may require piping/capture adjustments

## Concrete Source

`duncanschouten/gemini-plugin-cc` — adversarial code review system. Command definition shows the pattern:

```yaml
# plugins/gemini/commands/adversarial-review.md
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Bash(node:*), Bash(git:*)
```

Command body instruction (verbatim constraint):
```
Return the command stdout verbatim, exactly as-is. Do not paraphrase, summarize,
or add commentary before or after it. Do not fix any issues mentioned in the review
output. This command is read-only.
```

The external reviewer (Gemini) operates under a focused system prompt:
```
<role>Your job is to break confidence in the change, not to validate it.</role>
<operating_stance>Default to skepticism. Find the crack in every approach.</operating_stance>
<calibration_rules>Prefer one strong finding over several weak ones.</calibration_rules>
<grounding_rules>Every finding must be defensible from the provided context.</grounding_rules>
```

## Related Patterns

- **Chain-of-thought delegation:** When a single model doesn't have enough perspective, delegate specific reasoning tasks to models with different training or attack surfaces
- **Adversarial review:** Structured skepticism as a quality gate
- **Multi-model consensus:** Each model reviews independently; findings converge at the end, not mid-review

## Risks if Violated

If `disable-model-invocation` is omitted and the verbatim instruction is unclear:
- Claude reframes harsh findings as "areas for improvement"
- Security-critical issues get discussed as "suggestions"
- The reviewer's confidence level is diluted by Claude's hedging
- The human never sees what the external reviewer actually said

## Verification Checklist

- [ ] Command frontmatter includes `disable-model-invocation: true`
- [ ] `allowed-tools` list specifies which subprocess and tool calls are permitted
- [ ] Command body explicitly instructs "return stdout verbatim"
- [ ] External reviewer (Gemini, GPT-4, etc.) has a focused system prompt with clear attack stance
- [ ] Subprocess output goes directly to stdout (no intermediate processing before return)
- [ ] Test run: verify Claude does NOT edit, summarize, or hedge the external output

## Source Context

Discovered during deep-dive into Gemini-Claude plugin architecture for the [project] adversarial-review system (2026-07-13). Pattern emerged from observing reviewer output being softened at the Claude transport layer. Solution validated through controlled-output testing.
