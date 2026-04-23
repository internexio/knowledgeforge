# Accretion Check: User Education Layer

**Date:** 2026-04-23

## Candidate: Navigator Confusion Detection (Loop Detection)

- **Novel:** yes — Zero matches in wiki for confusion-detection, loop-detection, framing-hint, disambiguation-loop, or consecutive-fire terms. Pattern is new in Module 01 v6.6.3.
- **Reuse value:** yes — The pattern solves a class of problem (user stuck in clarification loop, needs vocabulary hint rather than more clarification) that recurs in any agent with intent routing. The intervention point (second consecutive fire), state inference from context, and hint-must-use-actual-vocabulary constraint are all non-obvious. General applicability confirmed: customer support bots, code assistant mode dispatch, any multi-mode agent.
- **Decision:** FILE
- **Wiki path:** wiki/orchestration/disambiguation-loop-hint-injection.md

## Candidate: Quickstart Skill (User Education)

- **Novel:** unclear — A quickstart pattern (short onboarding UX for new users) is a broadly documented UX pattern. Without a specific KF-variant quickstart with non-obvious constraints, this would be a surface-level filing.
- **Reuse value:** conditional — If the quickstart encodes KF-specific routing vocabulary or a non-standard interaction sequence, yes. If it is a generic "here are five example prompts" document, no.
- **Decision:** SKIP pending concrete artifact — evaluate if/when a KF quickstart is authored and contains non-obvious design decisions. A quickstart document is user documentation, not an architectural pattern.

## Candidate: Fit-Check Skill (Routing)

- **Novel:** unclear — A fit-check (does this request match my domain?) is a well-known pattern in agent routing. The question is whether KF's variant has a distinctive implementation.
- **Reuse value:** conditional — If the fit-check uses a specific predicate structure, threshold, or exits-vs-routes distinction that is non-obvious, yes. The pattern of "check fit before dispatching to specialist" is already implicit in the orchestrator module.
- **Decision:** SKIP pending concrete artifact — evaluate if/when a fit-check skill is implemented. The abstract pattern (check fit before dispatch) has insufficient delta over what the orchestrator already documents.
