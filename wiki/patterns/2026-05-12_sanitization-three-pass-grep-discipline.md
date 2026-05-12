---
title: Sanitization discipline for public-ready repos — three-pass grep + skip-or-sanitize decision tree
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.80
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-12
domain: patterns
topic: validation
tags: quality-gate, validation, adversarial
related_entries: []
---

# Sanitization discipline for public-ready repos

## The Problem

A "public-ready" repo (PRR) is a repo intended for sharing — public GitHub, customer/partner distribution, open source — that's generated from or maintained alongside a private / personal / operator-specific source. The PRR must be free of:

- Operator paths (`/Users/<me>/`, `~/Scripts/<my-tree>/`)
- Operator identifiers (your username, your email, your phone, your API keys, your machine hostnames)
- Organization-specific content (your company name in places where it shouldn't appear, your internal product names, your customer/account references, your internal slack channels)
- Internal-only operational context (private cron jobs, dev-only shortcuts, security-sensitive paths)

When pulling content INTO a PRR — typically from a personal install of an upstream tool — naive copying leaks these. Even after one sanitization pass, future updates can re-introduce them. The discipline below catches this.

## The Three-Pass Grep Rhythm

For every batch of files copied into the PRR:

**Pass 1: BEFORE copy** — scope the operator-specific surface.

Grep the SOURCE files for any of your operator strings:

```bash
PATTERNS='/Users/<you>|<your-username>|<your-email>|<your-org>|<your-machine>'
grep -rilE "$PATTERNS" "$SOURCE_DIR"
```

This produces the list of files that need either skipping or sanitizing. If the list is short, decide per-file before copying.

**Pass 2: AFTER copy** — verify nothing slipped through.

Re-run the same grep on the DESTINATION (the PRR's working tree). Should return empty. If it returns hits, either you forgot to sanitize a file or the patterns missed something (operator paths in generated output, embedded screenshots, etc.).

```bash
grep -rilE "$PATTERNS" "$PRR_DIR" 2>&1
```

**Pass 3: BEFORE push** — sanity check after any edits/additions.

Final grep before `git push`. Catches the case where you edited a file post-copy and accidentally pasted in operator context (debug paths, sample data, your own examples).

The cost of Pass 3 is ~5 seconds. The cost of a leak post-push is "force-push or amend a public commit", which is both painful and often visible in mirror caches.

## The Skip-or-Sanitize Decision Tree

For each file that fails Pass 1, decide:

```
Is the personal/org content INTRINSIC to the file's value?
  Yes → SKIP the file entirely
        - Example: a brand-voice guide for "<your company> copy"
        - Example: a personal contacts database
        - Example: an org-specific compliance checklist
  No → SANITIZE
        Is the match a single hardcoded value that has a portable form?
          Yes → REPLACE with a portable placeholder or env-var pattern
                - `/Users/me/X/wiki/` → `~/.claude/wiki/` (default)
                  with a signpost about alternate locations
                - `me@myorg.com` → `<your-email>` placeholder
                - Hardcoded port 9876 → `${SERVICE_PORT:-9876}`
          No → THINK HARDER
                Probably the value is more entangled than it looks.
                Re-evaluate skip vs more-invasive-sanitization.
```

### Concrete examples from a real refresh

| Match | Decision | Action |
|---|---|---|
| `cos-copy/SKILL.md` — entire file is one org's brand voice rules | SKIP | Excluded from the sync |
| `kf-reflect.md` — one line with hardcoded wiki path | SANITIZE | Replaced `/Users/<me>/X/wiki/` with `~/.claude/wiki/` + signpost text |
| `cos-strategy/SKILL.md` — references to "cos-copy" skill (which we skipped) | LEAVE | The reference is to a skill name; the skill itself doesn't ship. Users with cos-copy installed see correct cross-references; users without it see a no-op signpost. |

## When This Applies

- Maintaining a public/distributable repo alongside a personal / organizational install
- Vendoring files from `~/.claude/`, `~/.config/`, `~/.zshrc`-derived configs, or any operator-specific source
- Open-sourcing code that was originally developed against a specific internal codebase
- Any time you're about to `cp -r ~/...stuff/... my-public-repo/`

## When This Does NOT Apply

- Repos that are genuinely operator-private (no external audience, no plan to share)
- Repos where the operator IS the organization (solo founder publishing their own work — the org names ARE the brand)
- Repos with comprehensive CI sanitization rules that gate every merge (the three-pass rhythm is for cases where humans are the last line of defense)

## Anti-Patterns

- **One-pass grep**: only running the check once (typically BEFORE copy) misses what slipped through, what your edits introduced post-copy, and what new operator strings emerged in the latest upstream content.
- **Trusting a `.gitignore` to handle sanitization**: gitignore excludes whole files, not lines within files. Doesn't help when the operator path is embedded inside a SKILL.md that you DO want to ship (minus that one line).
- **Sanitizing too aggressively**: replacing every example with `<placeholder>` makes the docs unusable. Keep concrete examples that don't tie back to a specific operator (`~/Code/my-project` is fine; `/Users/me/Scripts/specific-thing-only-I-have` is not).
- **Skipping the "public" repo visibility check**: a repo can be named with a `pub` suffix but actually be private on GitHub. Don't loosen sanitization discipline based on the name — apply it as if the repo were public, because eventually it might be.

## Cost vs Value

Cost: ~10 seconds for each grep pass × 3 passes per sync. Decision tree adds 1-5 minutes for files that hit Pass 1.

Value: catches operator-context leaks BEFORE they hit GitHub, which is the cheap window. Post-push recovery requires force-pushes (often visible in mirror caches) and possibly key-rotation if the leak was a credential. The discipline catches all the cheap-to-fix mistakes before they become expensive.

## Source Context

Discovered during [project]-nwpub skill refresh, 2026-05-12. The public-ready `nwpub` repo received an update of 23 vendored skills + 6 new skills + 13 slash commands from the canonical install. The three-pass grep identified:
- 1 file with intrinsic org content (`cos-copy/SKILL.md`) → skipped
- 1 file with a single hardcoded path (`kf-reflect.md`) → sanitized
- 28 other files with no matches → copied as-is

Post-copy grep was empty across the final 29 skills + 14 commands. PR: github.com/internexio/nwpub/pull/1.

The "skip-or-sanitize" decision tree generalized the per-file judgments into a repeatable rule. Future skill refreshes can apply the same rhythm without re-deriving the policy.

## When This Applies
[See section above]

## When This Does NOT Apply
[See section above]
