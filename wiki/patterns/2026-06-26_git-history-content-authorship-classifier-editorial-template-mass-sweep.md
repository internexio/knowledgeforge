---
title: Git-history content authorship classifier (EDITORIAL > TEMPLATE-FILL > MASS-SWEEP)
source_mode: builder
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-26
tags: git, content-authorship, e-e-a-t, seo, schema-org, audit, classifier, methodology
related_entries:
  - patterns/2026-05-29_fastapi-api-surface-classification-auth-dependency-extraction.md
---

# Git-history content authorship classifier

## Purpose

Distinguish substantively-authored pages from template-generated or mechanically-edited pages by classifying each page's git commit history. Built for E-E-A-T (schema.org `editor` field) attribution decisions but applies to any author-attribution audit: who gets credit for this page's content?

## The 3-tier classifier

Each commit subject is classified into one of three buckets, in this resolution order:

### EDITORIAL (counts as authorship)

Signal: commit subject names the page slug, OR uses verbs that imply substantive editorial action.

Patterns that fire EDITORIAL:
- `answer-first`, `ship cos-XXX`, `pivot`, `refocus`, `rewrite`, `Rewrite`
- `fix(voice)`, `fix(seo)` + page slug named, `fix(site)` + page slug named
- `CTR-focused`, `new guide`, `augment.*guide`, `commercial hook lede`
- `add /X/ landing page` (single-page addition)
- `site(seo):`, `seo:.*for `, `site(<page>):` scoped commits
- `Vary opener labels`, `Replace 100 "X" sentence openers` (voice sweeps that touched each page meaningfully)

### TEMPLATE-FILL (does NOT count as authorship)

Signal: commit creates multiple pages at once with formulaic descriptions.

Patterns that fire TEMPLATE:
- `Add MBTI type pages batch [N]`
- `Complete all 16 MBTI type pages`
- `Add DISC hub + 4 type pages`
- `Add OCEAN hub + 5 trait pages`
- `Add guides section with 10 BLUF articles`
- Any "Add X hub + N type pages" creating multiple pages from a template

### MASS-SWEEP (does NOT count as authorship)

Signal: structural / SEO infrastructure edit that touches many pages mechanically.

Patterns that fire MASS-SWEEP:
- `schema`, `json-ld`, `ImageObject`, `WebPage`, `org.logo`
- `sweep`, `canonical`, `sitemap`, `nav`, `meta`, `og:`, `breadcrumb`
- `[skip ci]`, `footer`, `css`, `style(`, `chore`, `Merge `, `em-dash`
- `Organization author`, `publisher`, `apply.*publisher`
- `editorial reframe note across`, `trademark compliance across`
- `route all CTAs`, `Ahrefs site audit`, `cross-link sweep`
- Project-specific bead IDs that map to known infrastructure sweeps

## Resolution-order rule (IMPORTANT)

When a single commit subject matches BOTH editorial AND mass-sweep patterns, EDITORIAL wins. Example: `guides: ship cos-r0fp AI Search Ranking Factors + em-dash density retroactive trim [skip ci]` — the `ship cos-` editorial signal beats the `em-dash` and `[skip ci]` mass-sweep signals. Without this resolution-order rule, "ship" commits with bundled style-trim suffixes get mis-classified as mass-sweeps.

Order in code: `if EDITORIAL: return EDITORIAL; elif TEMPLATE: return TEMPLATE; elif MASS: return MASS; else: return OTHER`.

## Use `--follow` to track through renames

URL canonicalization restructures (e.g., flat `.html` → `dir/index.html`) break naive git-log queries — the file's apparent first commit is the rename, not its actual creation. Use `git log --follow --format='%h|%s' -- <path>` to track through the rename.

## Co-Authored-By trailer is NOT a useful signal

When using Claude Code or similar AI-assisted commit workflows, almost every commit will have `Co-Authored-By: Claude <noreply@anthropic.com>`. Don't use this to distinguish authored vs generated content — both have it.

## Fallback: "core landing" overlay

Some pages predate visible git tracking (e.g., synced from production at repo init, ported from another system). They appear as having only mass-sweep commits but are clearly David-authored editorial content. For those, maintain a known-good-landings set:

```python
LIKELY_OWNED_LANDINGS = {
    'ai-copywriter', 'brand-voice', 'content-optimizer',
    'marketing-measurement', 'message-intelligence',
    'personality-communication', 'science', 'website-copywriting',
    # ... etc
}
```

Decision tree: if EDITORIAL commits found → [x]; elif OTHER commits but no TEMPLATE → [x]; elif in `LIKELY_OWNED_LANDINGS` and no TEMPLATE → [x] with rationale "core landing — likely David-authored pre-tracking"; elif TEMPLATE-only → [ ]; else → [ ].

## Validated grounding

Built and run on the [project] project on 2026-06-26 for the cos-o8ca E-E-A-T attribution sweep (74 pages across 19 sections). Output: 71 [x] / 3 [ ] verdicts. Operator (David Pedersen) reviewed the marked checklist and accepted with no overrides. The 70 pages that received `editor=Person David` schema were rsync'd to prod the same session and verified live.

## When to use

- E-E-A-T schema attribution decisions (who gets `editor`, `author`?)
- Content-ownership audits (who actually shaped this page?)
- Bus-factor analysis for content (what would be lost if X stopped contributing?)
- Refactor planning (which pages have heavy editorial commitment vs. template churn?)

## When NOT to use

- Code-authorship analysis (this is for content pages — `git blame` is better for code attribution)
- Single-author repos with no template-generation workflow (everyone is authoring; classifier returns [x] universally)
- Repos where commit messages are uninformative (cleanup needed first, or use diff-size heuristics instead)

## Companion implementation

Python reference implementation: `~/Scripts/[project]/cos/docs/planning/cos-o8ca-author-audit-checklist.md` shows the marked output; the classifier itself was run as inline Python in the session producing it (no standalone script extracted yet). If revived as a tool, key APIs:
- `get_commits(path)` — `git log --follow --format='%h|%s' -- <path>`
- `classify(subject)` — returns one of EDITORIAL / TEMPLATE / MASS / OTHER, EDITORIAL-first
- `decide(commits, slug)` — applies the decision tree above
