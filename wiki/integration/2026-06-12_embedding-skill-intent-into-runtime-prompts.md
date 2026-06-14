---
title: Operationalizing Claude Code skill intent in non-CC runtimes by embedding guidance into prompts
source_mode: direct
novelty_type: new_pattern
grounding_score: 0.7
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-06-12
domain: integration
topic: llm-api
tags: api, prompt-engineering, automation, scheduling, grounding
related_entries: []
---

# Operationalizing Claude Code skill intent in non-CC runtimes by embedding guidance into prompts

## The Problem

Claude Code (CC) skills like `cos-copy` are first-class primitives in interactive CC sessions — invoke them via the Skill tool, they apply their expertise to the current artifact, return refined output. But CC skills are NOT callable from arbitrary Python runtimes (cron jobs, web servers, background workers). They live inside the CC harness.

Real case from sem-tools-xcu: I needed a nightly Python cron job to draft customer-review owner-replies via the Anthropic API. The product spec called for "passing each draft through the cos-copy de-AI gate as a final step." cos-copy is a CC skill — its rules (banned AI-ese phrases, banned structural patterns, brand-voice enforcement) are defined inside a CC skill folder. The cron has no CC harness; calling cos-copy directly is impossible.

## Three Options, with Tradeoffs

**Option A: Skip the de-AI gate in the runtime path.**

Accept that drafts may have AI fingerprints; rely on the human-in-the-loop step (on-site manager reviewing each draft) to catch them.

- Pro: simplest.
- Con: defeats the purpose of automating drafts. Manager edits become rewrite-from-scratch in practice.

**Option B: Implement a second-pass Anthropic call.**

Pass the first draft to a "de-AI review" prompt that flags fingerprints and asks for a rewrite.

- Pro: closest analog to the interactive cos-copy flow.
- Con: 2x API cost, 2x latency, and the second pass might INTRODUCE fingerprints that the first pass avoided. Premature for <10 reviews/week.

**Option C (the pattern): Embed the skill's RULES directly into the single first-pass prompt.**

Rather than calling cos-copy on the output, build cos-copy's intent into the input.

For this case, the prompt template (`unified_reply_v1.txt`) literally lists banned phrases and structural patterns from the cos-copy skill:

- "Thank you for your valuable feedback"
- "We're delighted to hear"
- "Our team strives to"
- parallel triplets ("the food, the service, and the atmosphere")
- formulaic open-middle-close structure
- markdown / bullet points / emoji

Plus structural constraints (50-150 words, reference specific review content, no farewell formula, plain text only).

## When This Applies

When you want to use a CC skill's intent from a runtime context AND:

- the skill's rules are mostly enumerable (banned/required things, structural constraints) rather than requiring iterative refinement,
- the output is going through a single LLM call anyway (so embedding the rules costs nothing extra),
- cost/latency matter (so a second-pass call is wasteful).

## When This Does NOT Apply

- Skills that depend on TOOL USE (e.g., a CC skill that grep's a codebase or runs shell commands) — those need a real runtime equivalent, not a prompt embedding.
- Skills whose value is multi-turn refinement (critic-style "find 15 issues" / builder "fix all 15" loops). Embedding the rules into a single call can't replicate the iteration.
- Skills with persistent state or memory across invocations.

## Limitations

- Output quality depends on the LLM following the embedded rules. Smaller / cheaper models (Haiku tier) follow explicit constraints reasonably but may slip into fingerprints under length pressure.
- You lose the CC skill's evolutionary updates — if cos-copy adds new banned phrases over time, the embedded prompt drifts. Pin a version (e.g., `prompt_version: "unified_reply_v1"`) and re-import from the live skill on a cadence.
- No second-pair-of-eyes effect. The same model that generated the draft is also enforcing the rules. A separate Anthropic call adds independence at the cost of $.

## Architectural Note: Track the Prompt Version

To make rule drift visible:

- Store the prompt version (e.g., "unified_reply_v1") on every generated artifact.
- When the skill updates upstream, bump to v2 (new file), regenerate stale drafts, A/B compare.

In sem-tools-xcu this looks like:

- `customer_review_drafts.prompt_version` column
- `sem/reviews/prompts/unified_reply_v1.txt` (versioned filename)
- `sem reviews draft --all-stale` regenerates whenever the source content changes

## Concrete Grounding

- Implemented in sem-tools-xcu commit `90acfa3` (internexio/sem-tools).
- Prompt template at `sem/reviews/prompts/unified_reply_v1.txt` — banned phrases section lifted from the cos-copy skill description.
- Documented decision in `sem/reviews/drafter.py` module docstring under "cos-copy de-AI gate" heading.
- NOT yet validated by running the drafter against real Anthropic — currently exercised end-to-end with a fake generator (so the pattern is implementation-validated but not output-quality-validated). That's why grounding is 0.7 not 0.9.

## Why This Is Worth Saving

The "Claude Code skill, but from a Python runtime" gap will keep coming up as more skills exist and people want to use them in production. This pattern (embed the rules in the prompt; pin a version; regenerate on drift) is broadly applicable across teams that build skills AND production runtimes.

## Source Context

Session: sem-tools-xcu-drafter (2026-06-12). Building a nightly customer-review reply drafter as a Python cron job using the Anthropic API. The product spec required de-AI gate via the cos-copy skill, which is not callable from non-CC runtimes. Decision to embed cos-copy's rules (banned phrases, structural constraints, length/tone guidelines) directly into the first-pass prompt template rather than add a second API call for review/refinement.
