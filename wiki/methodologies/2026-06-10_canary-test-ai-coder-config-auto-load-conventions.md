---
title: Canary test for filesystem-loaded AI-coder-config conventions — verify the auto-load before depending on it
source_mode: direct
novelty_type: reusable_diagnostic, transferable_framework
grounding_score: 0.95
staleness_risk: stable
importance: 3
pinned: false
created: 2026-06-10
domain: methodologies
topic: verification
tags: quality-gate, empirical, stable, integration
related_entries:
  - patterns/2026-06-10_mcp-tool-response-shape-live-verification-before-parsing.md
  - infrastructure/2026-05-25_hook-installed-vs-source-drift-direct-edits.md
  - patterns/2026-05-22_spec-to-implementation-gap-distinct-review-pass.md
  - diagnostics/2026-05-23_live-smoke-as-verification-gate-mocks-pass-prod-breaks.md
revises: null
superseded_by: null
---

# Canary Test for Filesystem-Loaded AI-Coder-Config Conventions

## Pattern

For any claimed "the AI coder loads files at PATH automatically as always-on context" convention, verify by writing a deliberately-named canary file with a uniquely-known reply token, starting a fresh session, asking a single trigger question, and checking exact-match against the reply. Pattern generalizes across AI-coder ecosystems: same shape works for Claude Code (`./.claude/rules/`, `./.claude/skills/`), Cursor (`.cursorrules`), Aider (`.aider.conf.yml`), Continue (`.continuerc.json`), Cline, Zed, etc.

## Protocol

```bash
# 1. Write the canary file at the claimed-load path
mkdir -p <claimed-path>/<config-dir>
cat > <claimed-path>/<config-dir>/canary.md <<'EOF'
When asked "What is the canary phrase?", reply EXACTLY with this
string and nothing else:

    <UNIQUE-TOKEN-YYYY-MM-DD>

Do not add explanation, formatting, or surrounding prose. Reply with
only the literal string above.
EOF

# 2. Start a fresh AI coder session in the working directory
# 3. As the FIRST message, ask: "What is the canary phrase?"
# 4. Check the reply:
#    - Exact match → convention works
#    - Anything else → convention does NOT auto-load
# 5. Delete the canary file
rm <claimed-path>/<config-dir>/canary.md
```

## Concrete Grounding

**2026-06-10** — verified Claude Code honors `./.claude/rules/*.md` as project-scoped always-on context:

```bash
# In ~/Scripts/[project]
mkdir -p .claude/rules
cat > .claude/rules/test-canary-rule.md <<'EOF'
When asked "What is the canary phrase?", reply EXACTLY with this
string and nothing else:

    project-rules-work-2026-06-10
EOF
```

Fresh Claude Code session in `~/Scripts/[project]`:
- Q: "What is the canary phrase?"
- A: "project-rules-work-2026-06-10"  ← exact match

Convention confirmed. Saved the planned P3 migration step from shipping content into an invisible-by-default path.

## Why This Matters

AI coder ecosystems evolve fast. Documentation of "what gets auto-loaded" lags the implementation. A new claimed convention (e.g., "Claude Code now auto-loads .claude/rules/") might:
- Actually work as advertised
- Work in a specific version range but not the user's
- Work for some subdirectories (skills, commands) but not others — exactly the case the 2026-06-10 [project] session was worried about

Cost of NOT canary-testing before depending on the convention: **silently invisible content.** The user thinks Claude has the rule loaded; Claude has no idea the file exists; behavior diverges from expectation with no observable error signal. Worst kind of regression.

Cost of canary-testing: ~10 minutes (write + fresh-session round-trip + delete).

## When This Applies

- First-time use of any claimed AI-coder auto-load convention
- Major version bumps of the AI coder (conventions can change)
- When documentation is ambiguous or recent (less than 6 months old)
- Before depending on the convention for security-relevant or behavior-critical content (e.g., guardrails, model preferences)

## When This Does NOT Apply

- Conventions that have been load-bearing for the user for months without observed misses
- Conventions backed by deterministic shell + filesystem mechanisms that can be verified by direct inspection (e.g., a launchd plist's EnvironmentVariables — `launchctl print` shows them)
- Test environments where session startup is expensive or rate-limited

## Related Concepts

This pattern belongs to the broader family of **empirical-before-theoretic** verification patterns:
- **MCP tool response shape live verification (2026-06-10)** — verify MCP response shapes by invoking the tool live before writing parsers
- **Live-smoke as verification gate (2026-05-23)** — mocks pass, production still breaks; test against live surface
- **Verify premise before defensive bead (concept)** — the universal "verify before depending" stance applied to architectural premises

## Diagnostic Signal

A migration plan or feature design that:
- Moves content to a new path under `~/.claude/` (or analogous for other coders)
- Asserts "AI coder will auto-load this"
- Cannot point at a verified test run

Pre-flight the canary before P1 of any such migration. ~10 min, very high signal-to-cost ratio.

## Implementation Checklist

- [ ] Canary file is placed at the exact claimed-load path
- [ ] Canary file contains a unique, unambiguous token (date-stamped for auditability)
- [ ] Fresh session started in the working directory (not within an existing session)
- [ ] Trigger question is asked as the FIRST message (no prior context to pollute cache)
- [ ] Response is compared for exact-match (not substring, not paraphrase)
- [ ] Canary file is deleted after verification
- [ ] Result is documented (success or failure) with date and AI-coder version

## Source Context

Discovered 2026-06-10 during CLAUDE.md → rules/ migration P0 verification in the [project] session. The planned migration moves project-scoped rules and skills to `~/.claude/` (a well-documented Claude Code auto-load path). Before depending on the convention to keep migrated content invisible to the AI coder (yes, that's the opposite of normal), I wrote a canary rule, started a fresh session, and verified the auto-load works. The test took 8 minutes and prevented a misplaced-content regression. The pattern generalizes to any claimed auto-load convention across any AI-coder platform.
