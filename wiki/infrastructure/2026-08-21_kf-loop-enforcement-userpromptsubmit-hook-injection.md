---
title: KF loop enforcement via UserPromptSubmit hook injection
source_mode: builder
novelty_type: new_pattern
grounding_score: 0.95
staleness_risk: stable
importance: 4
pinned: false
created: 2026-08-21
domain: infrastructure
topic: ops
tags: [routing, quality-gate, deployment]
related_entries:
  - wiki/architecture/hook-consequence-asymmetry.md
  - wiki/strategy/2026-05-18_terse-by-design-orchestrator-overhead-only-patches-failure-modes.md
---

# KF Loop Enforcement via UserPromptSubmit Hook Injection

## What It Is

A pattern for enforcing behavioral protocols that would otherwise decay as session context grows. Active loops inject their rules into every UserPromptSubmit turn via a hook, so the model re-reads them on each prompt regardless of how much context has accumulated.

The key insight: behavioral rules that should persist across long sessions need to be re-injected on every prompt, not just loaded once at startup. Session context naturally pushes older context below the context window; a rule stated once at the beginning of a session gets buried after 50+ turns. Re-injecting via hook ensures the rules stay active for the entire session duration.

## Implementation

### Registry and Hook

- **Registry:** `~/.claude/kf/loops/registry.yaml` — global, persists across sessions
- **Hook:** `kf-loop.py` registered as a UserPromptSubmit hook in `~/.claude/settings.json`
- **Injection point:** Hook reads registry on each prompt, finds active loops, appends `[KF-LOOPS ACTIVE]` block to userPrompt with each loop's rules
- **Rules injection location:** Appended AFTER the user's actual message, keeping user intent visible to the model without displacement

### CLI Subcommands

```
kf-loop enable <loop_name>       # Activate a loop for the session
kf-loop pause <loop_name>        # Temporarily suspend a loop
kf-loop disable <loop_name>      # Turn off a loop (persists in registry)
kf-loop create <name> --rule "..." # Register a custom loop
kf-loop status                   # Show active loops
kf-loop list                     # Show all available loops
```

### Built-in Loops (as of 2026-08-21)

- `de-ai` — strip AI fingerprints from all outputs (tricolon-punchlines, "X is not Y" structures, etc.)
- `decision-tag` — tag every evaluative+ output with decision type (reckoning, evaluative, predictive, novel)
- `accretion-check` — flag evaluative+ outputs as KB candidates for Module 21 accretion

### Key Design Decisions

1. **Rules inject into `userPrompt` (not system prompt):** UserPromptSubmit hooks can modify the prompt field. Injecting into userPrompt appends after the user's actual message, keeping it visible to the model without displacing user intent.

2. **Pauseable, not permanent:** Rules can be suspended mid-session via `kf-loop pause` without removing them from the registry. Supports ad-hoc workflow adjustments.

3. **Lightweight registry:** Plain YAML file, no database. Registry round-trips across sessions without corruption. Serialization handles newline escaping in custom rules.

4. **Per-prompt re-injection:** Rules are read and injected on EVERY UserPromptSubmit turn. This is intentional — it costs negligible latency (YAML parse + string append ~5ms) and guarantees rules stay active across long sessions.

## When This Applies

- **Any behavioral rule that must survive long sessions:** Rules that decay when buried by context (de-AI enforcement, decision tagging, citation requirements)
- **Rules that are contextual/optional:** Should be pauseable mid-session without removing from registry (e.g., temporarily disable accretion-check when bulk-testing output before filing)
- **Rules that persist across multiple sessions:** Stored in registry, not just in-context (e.g., a project-specific decision taxonomy that applies to every session in that context)

## When This Does NOT Apply

- **One-off session behaviors:** Just state them in the prompt; don't create a loop
- **Rules that should fire on specific tool events:** Use PostToolUse or PostCompact hooks instead of UserPromptSubmit
- **Project-specific rules:** Use project CLAUDE.md or project-scoped settings instead of global loops; global loops should be universally applicable

## Grounding

Built and deployed 2026-08-21 in knowledgeforge-core session. Smoke tested across all subcommands:
- `kf-loop enable de-ai`, `kf-loop pause accretion-check`, `kf-loop status` — all working
- Hook injection mode: rules correctly appended to userPrompt on every turn
- Registry round-trips: serialize/parse cycle verified including newline escaping in custom rules
- Committed at `3262274` and `6f69698`

## Source Context

Developed as part of KF infrastructure hardening to prevent behavioral protocol decay in long sessions. UserPromptSubmit hooks provide a clean re-injection mechanism that's lower-latency than re-parsing CLAUDE.md and simpler than maintaining per-mode state files.

## Related

- Module 21 (Knowledge Accretion) — accretion-check loop flags outputs for KB filing
- Module 02 (Builder) — decision-tag loop supports builder output classification
- `wiki/architecture/hook-consequence-asymmetry.md` — framework for classifying hook types and exit behaviors
- `wiki/strategy/2026-05-18_terse-by-design-orchestrator-overhead-only-patches-failure-modes.md` — loop injection as an alternative to bloated system prompts
