---
title: The story-told test — do header + column labels alone deliver the argument?
source_mode: critic
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-07-06
domain: diagnostics
topic: data-visualization
tags: infographics, data-visualization, content-review, communication-QA, mobile-scannability
related_entries:
  - patterns/2026-06-29_headless-chrome-html-png-pipeline-text-heavy-social-infographics.md
  - diagnostics/2026-06-16_demonstration-gap-framework-explained-never-shown.md
  - diagnostics/2026-06-16_moat-left-offstage-evidence-grounded-brand-copy.md
---

# The Story-Told Test — Do Header + Column Labels Alone Deliver the Argument?

## Core Principle

When reviewing a data infographic (before/after, comparison grid, multi-column layout, quadrant chart, any structural comparison), the sharpest QA test is:

**Do the header + column labels alone tell the argument, if all body text is stripped?**

If YES → the infographic is scan-first, mobile-safe, and continues to work when the reader doesn't stop to read the body copy. High-C readers who scan then decide will get the argument in one pass.

If NO → the header opens an info gap the visual doesn't close. Cognitive load INCREASES rather than decreases; the reader must piece together what the header set up vs. what the columns actually show.

## Scope

Applies to: any data infographic with structural comparison components (columns, rows, quadrants, matrices) — the kind rendered via HTML/CSS + screenshot for social/blog embedding. See related pattern [[patterns/2026-06-29_headless-chrome-html-png-pipeline-text-heavy-social-infographics]] for the production pipeline these comparison assets typically ride.

Does NOT apply to: single-photo social atoms, abstract hero images (FLUX/Imagen editorial style with no textual comparison), or long-form narrative illustrations that rely on flow rather than instantaneous comprehension.

## Grounded Example (client-project, 2026-07-06)

**V1 header:** "Your prompt has three axes. Most people leave one blank."
**V1 columns:** ADJECTIVES vs OPERATIONAL OCEAN

The header promised 3 axes. The columns showed 2 failure modes of ONE axis (voice). Info gap opened by header (3 axes → viewer expects 3) was not closed by the visual (only 2 columns of one axis's variants).

User feedback: "The image speaks to 3 axes, which one is usually blank? Run this through COS, think it can be clearer."

**V2 header:** "Adjectives don't have a voice. Instructions do."
**V2 columns:** same (ADJECTIVES vs OPERATIONAL OCEAN)

Now header + column labels alone tell the argument: adjectives fail (left column), instructions win (right column). Body text supplies detail but is not required to grasp the point. Story-told test passes.

## Application Procedure

1. Before rendering any comparison-structured infographic to production output, mentally strip the body text.
2. Read what remains: header + eyebrow + column labels only.
3. Ask: does the argument still stand?
4. If yes → ship. If no → the header (usually) needs to reframe to match what the columns actually show. Rewriting body copy rarely fixes a header-columns mismatch.

## Why It Works

This test detects **broken info gaps** — cases where the header sets up an expectation the visual doesn't deliver. High-C readers notice the mismatch first ("Wait, where are the 3 axes?") and add cognitive load rather than getting the argument in one scan.

The failure mode is subtle because the body text usually DOES tell the argument — so a review that reads the body first will judge the piece as clear. Only a scan-first read (mental strip of body text) surfaces the info gap. Most design-review checklists cover this implicitly under "clarity" or "visual hierarchy" without naming the specific test.

## Related Principles

**Peak-End rule.** The header IS the peak setup on scan-first reads. If the header's promise doesn't cash out in the columns, the "end" (the CTA or brand mark) inherits a weaker peak — the reader closes the tab having done extra work to reconcile header vs. visual, and the brand mark absorbs the cost.

**Info-gap consistency.** The underlying principle (header sets up expectation → visual must close it) is not new. What is new is the specific TEST for detecting the failure: strip the body, read what's left, check if the argument stands.

## Related Wiki Entries

- [[patterns/2026-06-29_headless-chrome-html-png-pipeline-text-heavy-social-infographics]] — pipeline for producing the comparison infographics this test reviews. Story-told is the QA gate before the render call.
- [[diagnostics/2026-06-16_demonstration-gap-framework-explained-never-shown]] — sibling content-review diagnostic. Demonstration Gap is about prose that names a framework without enacting it; Story-Told is about visuals that promise a structural argument without delivering it. Both are forms of "asserted-not-enacted" clarity failure, one prose, one visual.
- [[diagnostics/2026-06-16_moat-left-offstage-evidence-grounded-brand-copy]] — another content-review diagnostic from the same review lineage.
