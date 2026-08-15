# Thanks & Credits

KnowledgeForge grew out of a lot of late-night experimentation, a pile of other
people's GitHub repos, and more meetup conversations than I can reconstruct. These
are the contributions I can trace directly. The ones I can't are no less real.

---

## Direct Contributions

**James Hutchinson** ([@anjinMeili](https://github.com/anjinMeili)) — The A-RAG
hierarchical retrieval framework and multi-hop reasoning patterns from his AllOfUs
project directly shaped [Entity Relationship Analysis (Module 25)](../modules/25_entity_relationship_analysis.md). The idea of
treating entities as first-class graph nodes before reasoning fires came from
studying his work.

**PNW AGI Group** — The group's research archive was a significant source for
several foundational modules. Allen's 13 temporal interval relations (simplified
to KF's 4-relation model in [Module 17](../modules/17_temporal_knowledge.md)), the SYNAPSE competitive inhibition
algorithm that became [Module 18](../modules/18_salience_allocation.md)'s salience allocation, and the ingredients of
the four-part decision taxonomy in [Module 13](../modules/13_decision_classification.md) all trace back to materials from
this group. Access to their repo was the catalyst.

---

## Infrastructure

**Allen Institute for AI** — The [Asta Scientific Corpus MCP](https://allenai.org)
connects KF's Expert research variant to the Semantic Scholar paper corpus. Peer-reviewed
evidence retrieval in Expert mode runs on their infrastructure.

**MemPalace** — Semantic wiki search (Module 22) and verbatim history mining
(Module 24) depend on MemPalace for vector recall. Without it, KF degrades to grep.

---

## Research That Validated the Design

These papers didn't contribute to KF directly — they showed up after the fact and
confirmed that the architecture was pointed in the right direction.

- **Sofroniew et al.** — "Emotion Concepts and their Function in a Large Language
  Model," Transformer Circuits Thread, April 2026. Mechanistic evidence that LLM
  behavior is shaped by suppressable linear directions — exactly the model KF's
  patching-over-scaffolding principle assumes.

- **Duggan et al.** (Tufts HRI Lab) — ICRA 2026. Neuro-symbolic methods achieving
  ~3× success rate and ~100× energy efficiency over end-to-end neural approaches on
  structured long-horizon tasks. Independent empirical grounding for KF's hybrid
  deterministic/LLM architecture.

- **Ng et al.** — "Spontaneous Activity Reshaping Hypothesis," Psychological Review,
  2026. Biological-level mechanism for why conditional suppression (KF's mode
  activation model) outperforms preemptive scaffolding.

---

## The Broader Community

A lot of what ended up in KF started as a half-formed idea from someone's GitHub repo,
a demo at an AI Tinkers meetup, a Slack thread in a local AGI group, or a conversation
that went somewhere unexpected. I didn't always write down where things came from.

To everyone building in the open — sharing experiments that didn't fully work,
publishing half-finished frameworks, showing up to meetups with something to demo —
this kind of work compounds in ways that are hard to trace and easy to underestimate.
Thank you.

---

## License Note

KnowledgeForge is released under Apache-2.0. External tools and integrations carry
their own licenses — see each project's repository for details.
