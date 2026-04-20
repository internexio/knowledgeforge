# Neuro-Symbolic Architecture Validation

```yaml
metadata:
  source_mode: expert
  source_session: redacted
  created: "2026-04-07T00:00:00Z"
  confidence: 0.85
  grounding_score: 0.80
  grounding_source: "Paper verified 2026-04-19 via HRI Lab page and project site. Main findings confirmed: ~2.8x success, ~100x energy, generalization to unseen variants. One claim (50 demos vs 300) could not be verified from public sources — PDF binary, not parsed."
  verification_status: verified_partial
  novelty_type: reusable_analysis
  staleness_risk: stable
  importance: 4
  pinned: false
  accreted_in: "6.4.0"
  citation: |
    Duggan et al., "The Price Is Not Right: Neuro-Symbolic Methods Outperform VLAs on
    Structured Long-Horizon Manipulation Tasks with Significantly Lower Energy Consumption."
    ICRA 2026. Tufts HRI Lab.
    https://hrilab.tufts.edu/publications/dugganetal26icra/
    PDF: https://hrilab.tufts.edu/publications/dugganetal26icra.pdf
    Project: https://price-is-not-right.github.io
```

---

## Pattern

Symbolic orchestration (planning, routing, quality gates) + neural execution (reasoning within structured modes) = neuro-symbolic architecture.

KnowledgeForge is this pattern: decision classification, mode triggers, chain patterns, and quality gates are the symbolic layer. Claude reasoning within activated modes is the neural layer.

---

## Empirical Evidence

**Duggan et al., "The Price Is Not Right," ICRA 2026 (Tufts HRI Lab)**
Full title: *Neuro-Symbolic Methods Outperform VLAs on Structured Long-Horizon Manipulation Tasks with Significantly Lower Energy Consumption*
Links: [paper page](https://hrilab.tufts.edu/publications/dugganetal26icra/) · [project site](https://price-is-not-right.github.io)

Head-to-head: neuro-symbolic (PDDL symbolic planner + learned control) vs. fine-tuned Vision-Language-Action models on structured long-horizon manipulation (Towers of Hanoi benchmark):

- **~2.8× success rate**: 95% (neuro-symbolic) vs. 34% (best VLA) on the 3-block task
- **~100× training energy efficiency**: VLA fine-tuning consumes "nearly two orders of magnitude" more energy
- **Generalizes to unseen task variants**: neuro-symbolic achieves 78% on unseen 4-block variant; both VLAs fail completely (0%)
- **50 structured demos > 300 full-trajectory demos** — composability wins over raw data volume [claimed in original accretion; not confirmed from public sources — verify in PDF if citing]

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
