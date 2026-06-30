---
title: cos-grounding claim disposition taxonomy — five types for rebuild_needed claims
source_mode: direct
novelty_type: transferable_framework
grounding_score: 0.88
staleness_risk: stable
importance: 3
pinned: false
created: 2026-06-29
domain: methodologies
topic: decision-framework
tags: grounding, classification, quality-gate, peer-reviewed
related_entries:
  - methodologies/2026-06-29_cos-grounding-co-citation-rescue-protocol-upgrading-weak-single-source.md
  - methodologies/2026-06-26_two-corroborating-secondaries-can-share-the-same-error-primary-source-verification-not-optional.md
---

# cos-grounding claim disposition taxonomy

When a claim cannot reach standalone grounding (composite ≥ 0.8), use one of these five disposition types instead of leaving it as indefinite `rebuild_needed`.

## When This Applies

When running the cos-grounding rubric (composite_score = retrieval_grounding × evidential_support × domain_transfer), claims that fall below 0.8 may still have deployment value — but not as standalone peer-reviewed citations. Use the appropriate disposition type to route the claim toward its best-fit deployment surface.

Triggers:
- Composite score < 0.8 after attempting co-citation rescue (see companion wiki entry)
- Claim has reuse value but insufficient academic grounding
- Publication path exists outside the "science page" (inline mechanism notes, qualitative context, industry benchmarks, etc.)

## The Five Disposition Types

### MECHANISM-NOTE

**When to use:** Valid mechanism, anchor paper has very low citation count (cc ≤ 5), and no construct-matching meta-analysis exists in the references store.

**What it means:** The mechanism is real but the citation base is too thin to defend as a standalone academic claim on the science page.

**How to deploy:** Inline mechanism note with explicit context caveat. Drop any numeric figures (e.g., "~3% lift" in hape-002 was measured in a university student context — not deployable as a B2B benchmark). Cite the paper for the mechanism direction only.

**Canonical example:** hape-002 (Lasky-Fink & Rogers 2022, cc=1, value-signaling subject lines, PLOS ONE)

---

### QUALITATIVE-REFRAME

**When to use:** Valid finding with verbatim figures, but cc is low (cc ≤ 10) AND domain is cross (multiplier 0.7–0.8), meaning composite caps well below 0.8 even with a co-citation.

**What it means:** The directional insight is defensible; the specific figures are not.

**How to deploy:** Keep the mechanism insight as a qualitative note. Drop specific percentages / exact figures. Cite the paper for the directional claim only.

**Canonical example:** hape-003 (Kong, Zhu & Konstan 2020, cc=7, org email open rates 92-98% for faculty, ACM CSCW). Deployed as: "In high-trust professional contexts, the engagement challenge is at the click/action layer, not the inbox."

---

### INDUSTRY-BENCHMARK

**When to use:** The figure originates from an industry report (e.g., Chaffey 2020, practitioner benchmark studies) rather than peer-reviewed academic research, even if a peer-reviewed paper cites it.

**What it means:** The figure_check verdict is figure_verbatim_secondary — the paper cites an industry source, not a primary study. Industry benchmarks are excluded from the science/index.html citations.

**How to deploy:** Acceptable as context/background prose ("commercial email averages ~20% open rates — industry consensus") but must NOT appear in citation blocks on the science page.

**Canonical example:** sc-001 (Mathur et al. 2023 citing Chaffey 2020 + Pearlman 2012 for the 20% political email open rate)

**Key check:** Always verify whether the figure appears in the cited paper AS primary data or AS a secondary citation to an industry source.

---

### CO-CITATION

**When to use:** The paper adds replication provenance or format-specificity to an already-deployed claim (same construct, same direction). Domain transfer is cross and standalone composite is too low, but the paper adds meaningful context under an existing high-cc anchor.

**What it means:** The paper earns a "(Author1 et al., YEAR; Author2 et al., YEAR)" co-citation in existing site copy, but does not earn its own bullet or accordion.

**How to deploy:** Append co-citation to the already-deployed reference. Do not add a new standalone section.

**Canonical examples:**
  - plat-002 (Belanche et al. 2019, cc=120) → CO-CITATION under deployed plat-001 (Unnava 2021)
  - b5-002 (Matz & Kosinski 2019, cc=3) → CO-CITATION under deployed b5-001 (Matz et al. 2017 PNAS)

---

### CAVEAT-ONLY

**When to use:** The paper introduces a nuance, limitation, or calibration caveat that should accompany an existing deployed claim, but cannot stand alone. Low cc (≤ 5) but adds intellectual honesty.

**How to deploy:** Append as inline calibration note to existing content. Phrased as a caveat, not a standalone finding.

**Canonical example:** fs-003 (Amarnath & Jaidev 2023, cc=2) appended to Matz 2017 personality-targeting copy: "Calibrated targeting outperforms generic; over-inference can trigger reactance."

---

## Decision Heuristic

```
Is the anchor cc < 10 AND domain cross?
  → Can co-citation with high-cc same-construct meta rescue it? (check store)
      Yes → run co-citation rescue protocol (see companion wiki entry)
      No → check domain_transfer
           cross (0.7×): cap = 1.0 × 0.85 × 0.7 = 0.595 → MECHANISM-NOTE or QUALITATIVE-REFRAME
           adjacent (0.8×): cap = 1.0 × 0.85 × 0.8 = 0.68 → QUALITATIVE-REFRAME
           
Is the figure from a secondary citation (industry report)?
  → INDUSTRY-BENCHMARK (regardless of cc of citing paper)
  
Is the paper a replication/sister-study of a deployed claim?
  → CO-CITATION
  
Does the paper add a boundary condition/failure mode only?
  → CAVEAT-ONLY
```

## When NOT to Apply These Dispositions

- **Strong co-citation rescue available:** High-cc meta exists in store, same construct, domain ≥ adjacent. Run the rescue first; disposition is the fallback only if rescue fails.
- **Domain transfer is same (1.0×) and evidential can reach 0.85 via co-citation:** Composite = 0.85 → grounded status achievable. Do not downgrade to a disposition type.
- **Claim already deployed:** If this is a companion paper to existing site copy, file as CO-CITATION directly without going through `rebuild_needed`.

## Implementation (evidence YAML)

Write the disposition in the `recommended_text` field with the disposition type in ALL-CAPS at the start:
```
MECHANISM-NOTE (2026-06-29): [deployment text]
QUALITATIVE-REFRAME (2026-06-29): [deployment text]
INDUSTRY-BENCHMARK (2026-06-29): [context note]
CO-CITATION (2026-06-29): [co-citation format]
CAVEAT-ONLY (2026-06-29): [caveat phrasing]
```

Update `candidate_status` in manifest.json with the same type prefix so it is scannable (e.g., `candidate_status: MECHANISM-NOTE`).

## When This Does NOT Apply

- Claims with composite ≥ 0.8 after attempted rescue — file as GROUNDED, not disposition
- Claims with grounding_score < 0.6 overall — surface with caveat, do not file
- Claims missing prerequisite data (no cc, construct unclear, no domain_transfer metric) — return to caller for clarification

## Source Context

This taxonomy emerged from the cos-grounding upgrade work (session: cos-grounding-upgrade-2026-06-29) where five rebuild_needed claims (fs-002, hape-002, hape-003, sc-001, b5-002) were evaluated. Two succeeded via co-citation rescue (fs-002, hape-002 grounded to 0.85+); the others fell into these five disposition types based on their anchor-cc, domain-transfer, and figure-source characteristics. The taxonomy distills the decision tree and provides a repeatable framework for routing sub-0.8 claims toward their best-fit deployment surface without leaving them indefinitely orphaned in rebuild_needed state.
