---
title: HTML content audits must separately scope header hero sections from article-body
source_mode: builder
novelty_type: reusable_diagnostic
grounding_score: 0.82
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-11
domain: diagnostics
topic: testing
tags: [html, content-audit, grep, scope, debugging]
related_entries:
  - diagnostics/2026-07-11_em-dash-audit-requires-two-form-grep-patterns.md
---

# HTML Content Audits: Header-vs-Body DOM Scoping

## The Problem

When auditing HTML pages by targeting `<div class="article-body">` or article-body `<p>` tags with grep, the `<header class="page-header">` section containing hero subtitle text is a separate DOM structure and is silently excluded from the grep results. Both sections must be explicitly grepped to achieve full coverage.

**Symptom:** A mobile screenshot shows a line starting with `—` or an audit finds "X issues in article copy" but manual inspection reveals additional instances in the hero/header section that the grep missed.

## Root Cause

HTML marketing sites commonly separate page structure into two prose-containing regions:

- **Page header/hero:** `<header class="page-header">` containing title, subtitle, and descriptive text (sometimes with em-dashes, punctuation, or other audit-able elements)
- **Article body:** `<div class="article-body">` or `<main>` containing the bulk of content

A grep scoped to one region by class name or tag selector (e.g., `grep -n 'pattern' file.html | grep 'article-body'`) captures only content within that selector. The header section, if it uses a different class or wrapper element, is entirely excluded from results.

The audit operator may not notice the gap unless:
1. Visual review of the page reveals inconsistencies (e.g., some styled em-dashes, some not)
2. A mobile screenshot shows typographic breaks (orphaned dash at line start)
3. The audit rule is strict enough to catch the fact that all pages should have similar counts

## Fix Pattern

Run two grep passes on the same file:

```bash
# Step 1: Full-file count (ground truth)
grep -n 'pattern' file.html | grep -v '<meta\|<title\|<script\|<!--' | wc -l

# Step 2: Scope to header section explicitly
grep -n 'pattern' file.html | grep -i 'page-header\|<header'

# Step 3: Scope to article-body section explicitly
grep -n 'pattern' file.html | grep -i 'article-body\|<main'

# Step 4: Compare totals
# If Step 1 > (Step 2 + Step 3), investigate other sections
```

**Workflow:**

1. Run Step 1 to get ground truth
2. Run Steps 2 and 3 independently and note line counts
3. Cross-check Step 1 against combined Step 2+3 results
4. If delta exists, manually inspect the file in a browser to find the prose-containing section that was missed
5. Update grep scope or add additional section-selector passes as needed

## When This Applies

- Any grep-based content audit that scopes by HTML element class or tag (em-dash audits, de-AI buzzword passes, readability passes, link audits)
- Marketing sites or landing pages that use a distinct hero/header section with prose text (subtitles, taglines) separate from the main article body
- Bulk content cleanup passes where measurement completeness is critical
- Pre-publish QA workflows where missing sections could cause visual inconsistencies

## When This Does NOT Apply

- Full-file grep without scope restrictions (`grep -n 'pattern' file.html` alone captures all sections)
- Sites where hero text is purely decorative (h1 only, no prose subtitle)
- CMS-generated pages where header and body share the same wrapper element (no multi-section structure)
- Markdown files (single prose body, no header/body split)

## Diagnostic Trigger

**When to apply this pattern:**

- Mobile screenshot shows a line starting with `—` or `–` and no body-prose grep surfaces it
- Audit reports low counts but visual review suggests more instances exist
- Multiple pages in the same site show inconsistent styling for the same pattern element
- A full-file grep count is higher than the sum of scoped section counts

## Grounding

Verified on `[project]/cos/site/content-optimizer/index.html` during a visual flow + em-dash audit pass on 2026-07-11 (session: [project]-em-dash-cleanup-2026-07-11).

The page's `<header class="page-header">` (line ~314) contained the text: `<em>resonates</em> — with every personality type` — an em-dash in hero subtitle prose.

This instance was missed by the article-body-targeted grep pass (`grep -n ' — ' index.html | grep article-body`) and discovered only when:
1. A 390px mobile screenshot showed an orphaned dash at the start of a wrapped line
2. Visual inspection of the page header area revealed the source

Fixing required a separate targeted Edit on the header section (lines 310-320), which would have been caught by a Step 2 header-scoped pass (`grep -n ' — ' index.html | grep -i 'page-header'`).

## Source Context

Discovered during em-dash density cleanup on [project] site (2026-07-11, session: [project]-em-dash-cleanup-2026-07-11). This is a companion diagnostic to the em-dash grep-pattern entry (2026-07-11); together they cover the two ways an em-dash audit can silently miss content: grep-pattern blindness (missing close-form dashes) and DOM-scope blindness (missing header-section dashes).
