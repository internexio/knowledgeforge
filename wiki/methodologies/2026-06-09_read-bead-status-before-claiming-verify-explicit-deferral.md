---
title: Read the bead's own status before implementing — "design only / defer until X" is a stop signal
source_mode: direct
source_session: redacted
novelty_type: methodology
grounding_score: 0.85
staleness_risk: stable
importance: 4
created: 2026-06-09
tags: beads, workflow, bead-triage, planning, verify-before-act
related_entries:
  - methodologies/2026-05-26_deterministic-scan-before-claiming-refactor-audit-beads.md
  - architecture/2026-05-18_bead-as-context-anchor-deferred-runbooks.md
  - orchestration/2026-05-30_bead-tracker-workflow-pipeline-triage-decisions-build-deploy.md
  - orchestration/2026-05-30_preflight-cred-gap-detection-bead-build-halt-decompose.md
domain: methodologies
topic: bead-triage-workflow
---

# Read the Bead's Own Status Before Implementing — "Design Only / Defer Until X" Is a Stop Signal

## The Rule

Before claiming and building a bead picked from `bd ready`, read the bead's **full description** and explicitly look for these status flags. If found, **STOP and surface the situation to the user** before writing code:

- "Status: design only" / "Design only"
- "Defer implementation until X" (where X is a trigger condition)
- "Current topology does not need this"
- "Build this when needed" / "placeholder for future work"

Do NOT claim the bead first and then ask. Claiming implies commitment to build; asking after claiming reads as scope-uncertainty rather than scope-respect. The read-then-ask sequence protects both the user's intent and the bead's own embedded guidance.

## Why This Matters

`bd ready` only knows about two things: **dependency graph** and **status field** (which is just open/closed/in-progress). It doesn't parse the bead's description — so a P4 backlog item can appear "ready" while being explicitly shelved by its author's own text.

Implementing a shelved bead:
1. **Violates the bead's own guidance** — you're doing the exact opposite of what the author decided.
2. **Ships dead code** — the current topology has no consumer for this feature; it's built on hypothetical future requirements.
3. **Creates confusion for future readers** — they see committed code that contradicts the bead's rationale. Was the author wrong? Was the decision reversed? Ambiguity costs debugging time later.

The read-then-ask pattern is cheap insurance: 30-60 seconds of text scan avoids 2-4 hours of wasted build time or code review friction.

## The Pattern in Practice

When you pick a bead and run `bd show <id>`:

1. **Read the entire description** — don't stop at the first action item.
2. **Scan for the flag phrases** (design-only, defer, placeholder, unnecessary in current topology).
3. **If present, respond to the user with:**
   - Plain-English summary of what the bead is about and why it exists
   - Explicit acknowledgement that the bead is currently shelved by its author
   - A short options list: defer further / write design doc only / build it (with concrete justification) / close entirely
4. **Wait for user decision before claiming.**

Example response structure:
```
This bead is about [plain description]. The bead notes end with: "Status: design only. Defer until [X]."

The author explicitly shelved implementation pending [trigger condition].

Options:
1. DEFER — leave the bead open, revisit when [X] happens (no work this session)
2. DESIGN-DOC ONLY — spend 45 min writing a specification but don't implement
3. BUILD — proceed with full implementation (requires justification: why build now?)
4. CLOSE — the need no longer exists; retire the bead

What's your call?
```

## When This Applies

- Any bead with explicit status flags in its description (design-only, defer-until, placeholder)
- Beads at P3/P4 priority with shelving language
- Backlog items that reference external conditions not yet met (vendor pricing, customer request, infra availability)

## When This Does NOT Apply

- Beads without explicit status flags — `bd ready` returning a clean, implementable item
- Beads at P0/P1 with active dependency unblock (those carry implicit urgency that overrides shelving language even if present)
- Greenfield beads with zero prior context (none of the flag phrases apply)

## Grounding (the source session)

**Date:** 2026-06-09, session: orchestra-eqm-pause-before-build

User said: "Pick up orchestra-eqm" expecting normal implementation flow.

Bead description ended with:
```
Status: design only. Defer implementation until a real no-shared-FS scenario
shows up. Current topology using XDG_CONFIG_HOME does not need this. Build
this when needed.
```

**Correct response:** pause, surface the deferred status, ask options.

**User decision:** design-doc-only + defer 2 weeks.

**What would have been wrong:** claiming and building immediately, shipping unneeded scaffolding code, creating a merge conflict and review friction for code the topology doesn't consume yet.

## Companion to the Producer-Side Rule

This is the **consumer-side** companion to the producer-side rule in the global CLAUDE.md:

> "Verify the premise before filing a defensive/hardening bead. When the bead's body is 'X is missing and should be added,' read the FULL relevant function/route/config — not just up to where the obvious end-of-block appears."

That rule fires when **creating** beads (verify the problem is real). This rule fires when **consuming** beads (verify the problem hasn't been deferred). Together, they sandwich the bead lifecycle: sound premise on creation, respected intent on execution.

## Source Context

Discovered during orchestra-eqm bead processing in the claude-orchestra-dev project. User initiated a normal "pick and build" workflow. Bead read revealed explicit shelving by the author. The pause-and-ask pattern emerged as a reusable consumer-side triage rule and prevents both wasted build time and code-review friction on unneeded implementations.
