---
title: Em-dash audit requires two separate grep patterns (close-form and spaced-form)
source_mode: builder
novelty_type: reusable_diagnostic
grounding_score: 0.92
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-11
domain: diagnostics
topic: testing
tags: [empirical, grounding, quality-gate, classification]
related_entries:
  - patterns/2026-07-11_css-chip-group-nowrap-guards-html-infographic-text-rendering.md
---

# Em-dash Audit: Two-Form Grep Coverage

## The Problem

When auditing HTML pages for em-dash density (e.g., enforcing a ≤1-per-150-words rule or ≤2-per-page limit), a naive grep for ` — ` (space-em-space) misses all em-dashes written in compact/close form (`—` with no surrounding spaces). In a real cleanup pass on the semalytics.com marketing site (29 pages, ~100 em-dashes total), the first pass caught only space-surrounded instances. A subsequent visual review revealed 53 more close-form em-dashes across 7 files that required a complete second pass.

**Symptom:** Audit reports "X em-dashes found" but manual review finds significantly more, scattered across specific files.

## Root Cause

Two distinct typographic conventions coexist in HTML content:

- **Spaced form:** `word — word` (common in UK/editorial style, also common in CMS-generated content where styling auto-inserts spaces)
- **Close form:** `word—word` (common in US style guides and AI-generated copy)

These require different grep patterns. A single grep for either form misses the other entirely. The gap is not a measurement error — it's a grep-pattern blindness that the audit operator may not notice if they don't visually inspect the flagged pages afterward.

## Fix: Always grep for the raw character first

```bash
# Step 1: Count ALL em-dashes (raw character, catches both forms)
grep -c '—' file.html

# Step 2: Identify spaced instances
grep -n ' — ' file.html | grep -v '<t[dh]\|<meta\|<title\|og:\|ld+json\|<!--\|<script'

# Step 3: Identify close-form instances
grep -n '[a-zA-Z0-9]—[a-zA-Z0-9]' file.html | grep -v '<t[dh]\|<meta\|<title\|og:\|ld+json\|<!--\|<script'
```

**Workflow:**

1. Run Step 1 to get the ground truth count
2. Run Steps 2 and 3 to enumerate instances for triage
3. Compare Step 1 output to Step 2+3 totals — any delta indicates a form you missed
4. If delta is nonzero, refine the grep patterns (e.g., add escaped-entity variants like `&mdash;` or `—`)

## Exclusion filter

When counting prose em-dashes (vs. all em-dashes), exclude:

- `<td>` and `<th>` table cells (UI data, not prose)
- `<meta>` and `<title>` SEO elements
- `og:` and `twitter:` OG/social tags
- `ld+json` / `<script>` blocks (JSON-LD structured data uses `—`)
- HTML comments `<!--`
- Pricing labels like `Signal — $0/month` (UI chrome)
- Quoted example copy inside `<p>` (e.g., `"Your copy — like this example — stays uncounted"`)

The grep `-v` filter above covers most standard cases. For edge cases (e.g., em-dashes in data attributes), extend the exclusion list.

## When This Applies

- Any HTML content audit that enforces an em-dash density rule or count limit
- Copy review workflows across static HTML sites, CMS exports, or AI-generated content
- Pre-publish QA checklists for editorial style enforcement
- Bulk content cleanup passes where measurement completeness is critical

## When This Does NOT Apply

- Markdown files (em-dash usage differs; typically only `---` or explicit `—`)
- JSON/YAML data files (em-dash as literal character is rare; usually Unicode escape or encoded)
- Pure-text content without HTML structure wrapping (no tag-based exclusion needed)
- Single-file audits where visual inspection is feasible (the two-pass technique is only necessary for scale)

## Grounding

Verified directly in [project] session (2026-07-11): first pass using ` — ` grep found ~95 em-dashes across 29 pages; second pass using raw `—` character grep found 53 additional instances across 7 files that required fixes. Session commit fec0b1b documents the second-pass remediation.

Real-world file set: semalytics.com/cos marketing site (~29 HTML pages, 8KB-30KB each). Audit operator ran first pass, caught ~95 dashes, deployed content revision. Later QA review flagged visual appearance issues ("why are these dashes different?"), prompting the second grep pass that uncovered the 53 close-form instances.

## Source Context

Discovered during em-dash density cleanup on [project] site rebrand (2026-07-11, session: [project]-site-emdash-cleanup). The rule itself (≤1 dash per 150 words in body prose) is documented in `~/.claude/projects/-Users-dp-Scripts/memory/feedback_em_dash_density.md`; this entry captures the auditing technique to make the rule measurable and complete.
