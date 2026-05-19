---
title: Read the validation spec, don't iterate on rejection — agent bias correction for taxonomy-gated writes
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.8
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-18
domain: patterns
topic: validation
tags: quality-gate, taxonomy, accretion, empirical
related_entries: []
---

# Read the Validation Spec, Don't Iterate on Rejection

## Pattern

When an enforcement gate (taxonomy validator, schema validator, lint gate, any "write-time rejector with controlled vocabulary") rejects an agent's input twice in a row, the agent's bias is to keep proposing variants of the input. Override that bias by reading the gate's spec ONCE instead — the spec is almost always cheaper than continued iteration.

## The Drift Mechanic (Why It Happens)

- Each rejection arrives with a suggestion ("nearest match")
- The suggestion feels like progress, so the agent tries another variant
- The agent never zooms out to read the underlying vocabulary
- After N rejections, total cost of iteration > cost of reading the spec once
- The spec is a finite enumeration — reading it provides full coverage of what's accepted; iterating samples one cell at a time

## Mitigation — The Read-the-Spec Heuristic

When the same gate rejects an agent's input for the second time in a session:

1. **Stop iterating immediately.** Don't propose variant #3.
2. **Locate the spec.** Most gates point to it in the rejection ("see Module 23", "see the schema at X").
3. **Read it whole.** Don't skim; the enumeration matters.
4. **Pick from the spec.** Now the agent has full coverage, not sampled coverage.
5. **Resume.** Subsequent submissions should pass first time.

## When This Applies

- Taxonomy gates (controlled vocabulary for tags, categories, types)
- Schema validators (JSON Schema, Pydantic, protobuf)
- Lint rules (style guides, naming conventions)
- Any write-time enforcement with a finite enumerated set

## When This Does NOT Apply

- Gates with no readable spec (raw semantic acceptance, fuzzy matching)
- One-off rejections that are typos or simple errors (read the spec is overkill)
- Rejections you understand but disagree with — escalate to a human, don't try to game the gate

## Grounding from Session

KnowledgeForge wiki accretion uses Module 23 controlled vocabulary (domain/topic/tags from a fixed enumeration). Two librarian rejections in one session:

- **Rejection 1:** Composite-vs-atomic MCP entry. Tags `model-context-protocol`, `agent-integration`, `crm`, `api-design`, `schema-budget`, `tool-design` all rejected. Librarian suggested replacements; agent moved on without reading Module 23.
- **Rejection 2:** Default-by-path tri-state pattern. Tag `patterns` (a domain, not a tag) plus missing `domain` and `topic` frontmatter. Librarian suggested specific revisions.
- **User directive:** "Batch-refile both rejected entries now — read Module 23 taxonomy first so the refile lands clean."
- **Action:** Read `~/Scripts/knowledgeforge-core/modules/23_Taxonomy_Enforcement.md` once. Took ~30 seconds. Got the full domain enumeration (10 domains), topic enumeration (~40 topics under domains), and approved tag list (57 tags).
- **Result:** Both refiles passed taxonomy gate first try. Two more wiki entries filed.

## Measured Outcome

2 rejections → 1 spec read → 0 rejections on refile. The variance-cut is the signal — the agent was on track to produce N more variant guesses before hitting the right combination by luck.

## Counterexample / Failure Mode to Watch

- Don't read every spec for every gate-encounter on the first try — overhead matters. The trigger is the **SECOND rejection in a row**, not the first. One rejection is signal; two is the agent doing something systematic.
- Some specs are too long to read in full (a 200-page style guide). In that case scan the index, jump to the relevant section. The pattern is "read the part that governs this enforcement", not "read everything."

## Cross-References

Pairs with anti-pattern of "iterating on rejection without re-reading the rules." See also: `methodologies/2026-05-18_polish-as-blocker-drift-explicit-ship-gate.md` — both involve the agent failing to step back. Polish-drift is about scope; this is about validation literacy.

## Source Context

Session: `cos-mcp-clarify-integration-phase2-3-prod-push`. User directed batch-refiling of two taxonomy-rejected wiki entries with the directive to read Module 23 first. Direct self-correction pattern surfaced in the process.
