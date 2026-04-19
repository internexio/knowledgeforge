# Neuro-Symbolic Architecture Validation

```yaml
metadata:
  source_mode: expert
  source_session: redacted
  created: "2026-04-07T00:00:00Z"
  confidence: 0.5
  grounding_score: 0.3
  grounding_source: "Citation unverified — no DOI, arXiv ID, or URL present. ICRA 2026 proceedings were not publicly available at session date (2026-04-07). Treat empirical numbers as unconfirmed."
  verification_status: unconfirmed
  novelty_type: reusable_analysis
  staleness_risk: stable
  importance: 4
  pinned: false
  accreted_in: "6.4.0"
  citation: "Duggan et al., 'The Price Is Not Right,' ICRA 2026. Tufts HRI Lab. [UNVERIFIED — no DOI or URL]"
```

---

## Pattern

Symbolic orchestration (planning, routing, quality gates) + neural execution (reasoning within structured modes) = neuro-symbolic architecture.

KnowledgeForge is this pattern: decision classification, mode triggers, chain patterns, and quality gates are the symbolic layer. Claude reasoning within activated modes is the neural layer.

---

## Reported Finding (Unconfirmed)

> ⚠️ **Verification required before citing externally.** The paper below could not be verified at accretion time — no DOI, arXiv ID, or public URL was found, and ICRA 2026 proceedings were not yet public on 2026-04-07. The quantitative numbers (~3×, ~100×, 50 demos) are unconfirmed. The core neuro-symbolic *pattern* is independently sound; the empirical support below is unverified.
>
> To verify: search "The Price Is Not Right" + Tufts HRI Lab on Google Scholar, arXiv, or ICRA 2026 proceedings.

**Duggan et al., "The Price Is Not Right," ICRA 2026 (Tufts HRI Lab) [UNVERIFIED]**

Reported findings — neuro-symbolic vs. end-to-end on structured long-horizon tasks:

- **~3× success rate** over end-to-end approaches [unverified]
- **~100× training energy efficiency** [unverified]
- **Generalizes to unseen task variants** — pure neural models fail completely on these [unverified]
- **50 structured demos > 300 full-trajectory demos** — composability wins over raw data volume [unverified]

---

## KF Mapping

| Paper Finding | KF Equivalent |
|---------------|---------------|
| Symbolic planner | Decision Classification (M13), mode triggers, chain patterns |
| Neural executor | Claude reasoning within activated modes |
| Composable structure | Pareto reduction, mode chaining as compositional planning |
| Structure hurts natively-handled tasks | Pass-through optimization, the meta-principle |
| Execution fidelity > planning correctness | Calibration Layer (M12), Grounding Scores (M15), Metacognitive Monitor (M14) |
| Computational cost as first-class metric | Operational Bounds (M16), Token Cost Per Mode (metric #9) |

---

## Reuse Context

Reference this entry when:
- Describing KF architecture to external collaborators
- Justifying pass-through optimization (structure must earn its keep)
- Defending Pareto reduction as a design strategy
- Evaluating whether to add new modes (each must patch a failure the neural layer can't handle alone)
- Making the case for structured agent frameworks vs. raw prompting
