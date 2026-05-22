---
title: Cross-project capability audit via structured repo-agent prompt
source_mode: strategist
novelty_type: transferable_framework
grounding_score: 0.80
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-21
tags: delegation, routing, chain, grounding, accretion
related_entries: [architecture/2026-05-18_bead-as-context-anchor-deferred-runbooks.md, orchestration/schema-first-elicitation-order.md, methodologies/2026-05-13_find-consumer-first-before-data-migration.md]
---

# Cross-Project Capability Audit via Structured Repo-Agent Prompt

When planning work in Project A that depends on capabilities in Project B, you have three naive options:
- Read Project B's code yourself (slow, depth-limited by context budget)
- Ask the user open-ended questions (limited by their working memory)
- Guess and ship (high blast radius)

A better option: send a structured prompt to a Claude Code session pointed at Project B and ingest its response back. This is "soliciting an audit from a sibling agent" — and it dramatically outperforms ad-hoc questions.

## The Prompt Anatomy

```
[CONTEXT BLOCK]
Cross-project capability handoff. I'm a different Claude Code session in
`/path/to/project-A` planning [SPECIFIC WORK]. I need detail from
project-B that I couldn't infer from a quick file survey.

[ANTI-DUPLICATION BLOCK]
Context I already have (don't repeat unless I'm wrong):
- [bullet of confirmed facts about Project B's structure]
- [bullet of confirmed APIs / env / data state]
- [bullet of what I've already read]

[INTENT BLOCK]
Workstreams I'm planning (in priority order):
  Sprint 0 — [outcome description]
  Sprint 1 — [outcome description]
  ...

[STRUCTURE CONSTRAINT]
Please answer the questions below. Format the response as a single markdown
document I can paste back. Use the exact section headers I give so I can find
each answer quickly. Cite file paths and line numbers where relevant. Skip
anything you genuinely don't know rather than guessing.

[QUESTIONS BY SECTION]
## A. [Topic block 1]
1. [specific question]
2. [specific question]
...

## B. [Topic block 2]
...

## H. Anything I'm missing
NN. What capability does [Project B] have that I haven't asked about,
    relevant to [the work]? One-shot brainstorm: ~5 bullets if anything.
```

## Why Each Block Matters

- **Context block** — tells the audit agent it's NOT in conversation with the user. Suppresses introductory throat-clearing.
- **Anti-duplication block** — every fact you list saves the audit agent a tool call. Saves their context and yours.
- **Intent block** — frames the audit. The agent prioritizes its depth on questions that map to your stated sprints, not equally across the codebase.
- **Structure constraint** — REQUIRED for ingest. Without "use the exact section headers I give," responses come back as flowing prose and you can't paste-and-parse. Adding "cite file:line" raises the grounding floor.
- **Sections A–H** — numbered or lettered questions. The audit agent answers inline under each header, returning a paste-able document.
- **Section H "Anything I'm missing"** — the highest-value block. The audit agent has just spent 5+ tool calls on your codebase. Ask them what else they noticed that you didn't ask about. Repeatedly this surfaces the gotchas you'd otherwise discover at integration time.

## When This Applies

- Any task in Project A blocked on partial knowledge of Project B's internals.
- Multi-repo workspaces where capability boundaries shift faster than memory.
- Build-don't-buy migrations where the replacement project's coverage needs validation before commitment.
- Cross-DB migrations needing schema/permission validation on the remote before writing deployment scripts.

## When This Does NOT Apply

- Project B is small enough that you can read it directly in <5 tool calls.
- The question is "does X exist?" — that's a single grep, not a delegation.
- You don't trust the audit agent's grounding (audit response without file:line citations is heavy bias surface).
- The knowledge gap is so foundational that you need interactive clarification, not a unidirectional audit.

## Anti-Pattern: Open-Ended "Tell Me About Project B"

Without section structure and questions, audit responses are:
- 80% restating what you already know (anti-duplication block prevents this)
- Light on file:line evidence (structure constraint demands it)
- Skip the gotchas (Section H asks specifically)

Unstructured handoffs yield high-context responses that can't be parsed back programmatically or re-used across sessions.

## Concrete Grounding

Used during a SEMrush→sem-tools replacement planning session (2026-05-21).

- ~25 questions across sections A–H
- Received 600+ line markdown response with file:line citations throughout
- Surfaced 3 critical issues the planning agent had not asked about, including a silent-failure config-pointer issue that would have broken production rank tracking post-cutover
- Response remained paste-able as a single block
- Receiving session could grep on the section headers for downstream planning

This pattern prevents the class of failures where knowledge exists in Project B but is never transferred because the handoff was too informal.

## Source Context

Cross-project delegation pattern from SEMrush-to-sem-tools migration planning session (semrush-to-sem-tools-cutover-2026-05-21). Extracted as transferable framework for multi-repo architectures where sibling agents need to coordinate across project boundaries without losing fidelity.
