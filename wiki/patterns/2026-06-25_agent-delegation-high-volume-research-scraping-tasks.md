---
title: Agent delegation for high-volume research and scraping tasks (≥20 fetches)
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-25
domain: patterns
topic: agent-delegation
tags: [agent-delegation, research-tasks, context-management, multi-fetch, scraping]
related_entries:
  - orchestration/2026-05-30_parallel-agent-triage-backlog-reconciliation.md
  - orchestration/2026-06-12_parallel-spec-parallel-critic-pattern-independent-beads.md
  - orchestration/context-manager-protocol.md
---

# Agent delegation for high-volume research and scraping tasks (≥20 fetches)

## The pattern

When a task requires 20+ WebFetch calls or extensive multi-page scraping, delegate to a research agent rather than executing serially in main context. The token math is decisive:

- **Serial in main context:** 29 fetches × ~5 KB each = ~150 KB pollution of main context window
- **Agent-delegated:** agent returns ~7 K tokens of structured table + per-event paragraphs
- **Compression ratio:** ~20× because the agent synthesizes per-event into a single row

Wall-clock cost is moderate: today's 29 Luma event scrapes ran in 234 s (4 min) inside one general-purpose agent. The agent ran 29 WebFetch calls in sequence and returned compact structured output.

## When to apply

- Web research task requires ≥20 page fetches
- Operator wants a synthesized structured table, not raw page dumps
- Per-page content is mostly reductive (extract a few fields, summarize)
- Main context needs to stay clean for follow-up synthesis

## When NOT to apply

- <10 fetches — overhead of agent spawn isn't worth it
- Operator wants to see each raw page (debugging, validation)
- Each page returns unique content the agent can't compress (e.g., long-form articles)
- Per-page extraction needs operator-in-the-loop judgment

## Prompt structure that worked

- Self-contained brief (agent has no session context)
- Explicit per-event extraction fields
- Output format specified (markdown table + per-row detail paragraphs)
- Time/budget cap per fetch
- Honest reporting instruction ("if a page is sparse, return sparse data — don't fabricate")
- All URLs listed inline in the prompt

## Concrete grounding (2026-06-25)

- Task: scrape 29 Luma event pages for Seattle Tech Week 2026 planning
- Agent type: general-purpose
- Result: structured master table + per-event detail paragraphs returned
- Wall clock: 234 s (4 min)
- Tool uses: 29 (one WebFetch per event)
- Main-context tokens consumed by return: ~7 K (vs estimated ~150 K for serial)
- Quality: 4 data-quality issues correctly flagged (1 wrong URL, 1 duplicate event, 1 auth-pattern, 1 Web3-flag); operator confirmed all 4 actionable

## Adjacent patterns

- Parallel agents for fully-independent sub-tasks (different domain queries) — same principle, multiple agents
- "Heavy lift in agent, judgment in main" — separation of concerns between research and synthesis
