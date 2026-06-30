---
title: cos-grounding co-citation rescue protocol — upgrading weak single-source claims via store-resident meta-analysis
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.92
staleness_risk: stable
importance: 3
pinned: false
created: 2026-06-29
domain: methodologies
topic: evidence-grounding
tags: cos-grounding, evidence-grounding, research-methodology, co-citation, grounding-rubric
related_entries:
  - methodologies/2026-06-26_berger-style-effective-evidence-base-framing-claim-verification.md
  - diagnostics/2026-06-22_html-unescape-before-json-ld-serialization.md
---

# cos-grounding co-citation rescue protocol

When a claim has composite < 0.8 due to weak evidential support (single applied paper, low cc), a co-citation rescue can push it to grounded status WITHOUT finding a new paper — using a high-cc meta-analysis already in the references store.

## When This Applies

Conditions for attempting a co-citation rescue:

1. Claim has a single source with evidence_tier: applied and cc < 50
2. Domain transfer is same (1.0×) or adjacent/cross (0.7–0.8×)
3. A meta-analysis covering the SAME CONSTRUCT may already exist in the references store or be findable via Asta

The rescue cannot work if domain is cross (0.7×) AND no same-domain co-citation is available:
- Max composite with cross domain + co-citation: 1.0 × 0.85 × 0.7 = 0.595 → still under 0.8
- Rescue requires domain to be same (1.0×) OR adjacent enough (≥0.94×) for co-citation to push composite ≥ 0.8

## When This Does NOT Apply

Do not attempt a co-citation rescue if:
- The anchor meta-analysis tests a DIFFERENT independent variable or mechanism than the claim (construct mismatch is disqualifying)
- No available co-citation candidate exists in the references store or via Asta search
- Domain transfer is cross (0.7×) without an adjacent-fit alternative
- The claim's original single source is already evidence_tier: meta-analysis (already the highest tier)

## The Rescue Math

Two-source co-citation raises evidential_support from 0.7 (single applied) to 0.85 (meta + applied):

| Configuration | Composite |
|--------------|-----------|
| Single applied, same domain | 1.0 × 0.70 × 1.0 = 0.70 → rebuild_needed |
| Meta + applied co-citation, same domain | 1.0 × 0.85 × 1.0 = 0.85 → grounded |
| Meta + applied co-citation, cross domain (0.7×) | 1.0 × 0.85 × 0.7 = 0.595 → still rebuild_needed |
| Single applied, cross domain | 1.0 × 0.70 × 0.7 = 0.49 → rebuild_needed |

## Protocol Steps

### Step 1: Identify the construct

State the SPECIFIC construct the claim is about. This is not the topic — it's the mechanism.

Example: For fs-002: the construct is "narrative transportation reduces counter-arguing and increases attitude change" (not just "persuasion" or "storytelling").

Precision here is critical because construct mismatch is the single most common failure mode in co-citation rescue.

### Step 2: Check the references store first

Before querying Asta, run: `python3 -c "import os, yaml; ..."` or grep the references/papers/ directory for papers with matching keywords. High-cc papers already curated to the store are the fastest rescue path.

Look for:
- Papers with citation_count ≥ 200 (Tier-1 meta-analysis threshold)
- evidence_tier: meta-analysis in their YAML
- Topic and construct overlap with the claim

### Step 3: Validate construct overlap (CRITICAL)

The co-citation anchor must cover the SAME CONSTRUCT, not just a related topic.

**Anti-pattern caught in 2026-06-29 session:**

hape-002 was about **value-SIGNAL CONTENT VARIANCE** in subject lines (varying the content to signal email value). Sahni et al. 2018 (cc>200) was about **NAME PERSONALIZATION** in subject lines. These look related (both are "subject line optimization") but test different constructs (IV differs: content-value signal vs. name-in-subject). Using Sahni as co-citation would create construct confusion and would not be defensible.

**Always ask:** "Does the anchor meta-analysis test the SAME independent variable and mechanism as the claim?"

### Step 4: Role assignment

When the rescue succeeds, assign roles explicitly in the evidence YAML:
- The meta-analysis becomes `role: anchor` (mechanism foundation)
- The original applied paper becomes `role: application` (domain-specific application of the mechanism)
- The claim text should lead with the meta-analysis and trail with the application:
  "Meta-analytic evidence confirms [mechanism] (Author et al., YEAR). [Application author] apply the mechanism in [specific context]..."

### Step 5: Re-score

Update the evidence YAML:
- Add the meta-analysis as a second source entry
- Update evidential_support to 0.85 (two-source co-citation)
- Recalculate composite_score
- Update verdict to "grounded" if composite ≥ 0.8
- Update ship_ready to true
- Add upgrade notes to the notes: field with the re-score rationale

## Canonical Example: fs-002 (2026-06-29)

**Claim:** Framing a persuasive message inside a story inoculates audiences against reactance

**Original state:** Single source — Gans & Zhan 2023 (cc=5, applied), domain same. Composite: 1.0 × 0.7 × 1.0 = 0.70. rebuild_needed.

**Rescue:** Found van Laer et al. 2014 (JCR meta-analysis, cc=744) already in store as pers-001 anchor. Same construct: narrative transportation → reduced counter-arguing → attitude change. Gans & Zhan is the APPLICATION of that mechanism to inoculation-against-reactance specifically.

**Result:** Two-source co-citation: retrieval=1.0 × evidential=0.85 × domain=1.0 = composite 0.85. Verdict: grounded. ship_ready: true.

## When the Rescue Fails

If the Asta search returns no construct-matching meta-analysis, or if the best candidate has a different IV/mechanism, the rescue fails. Do NOT force a cross-construct co-citation to get the score up — that's the single most common path to a misleading citation.

Failed rescue → apply the appropriate disposition type (MECHANISM-NOTE, QUALITATIVE-REFRAME, etc.) — see the companion wiki entry on cos-grounding disposition taxonomy.

## Asta Search Strategy for Rescue Candidates

Run two targeted snippet_search queries:
1. `[construct keyword] meta-analysis [domain]` — targets meta-analyses specifically
2. `[mechanism name] field experiment [domain context]` — targets applied replications

If both return only the original paper or tangential papers (wrong construct), the rescue is dead. Log the search queries in the evidence YAML notes field.

## Source Context

This protocol emerged from the cos-grounding upgrade work (session: cos-grounding-upgrade-2026-06-29) where five rebuild_needed claims (fs-002, hape-002, hape-003, sc-001, b5-002) were dispositioned. Two succeeded via co-citation rescue (fs-002 grounded; hape-002 grounded), while the others required mechanism reframing. The protocol distills the decision tree and anti-patterns encountered during those rescues, particularly the construct-mismatch failure that nearly propagated on hape-002 before being caught via explicit construct-overlap validation.
