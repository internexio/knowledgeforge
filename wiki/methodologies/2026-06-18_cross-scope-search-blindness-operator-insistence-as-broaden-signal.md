---
title: Cross-scope search blindness — sweep all instances on first "not found", treat operator insistence as broaden-search signal
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-18
domain: methodologies
topic: search-strategy
tags: search-strategy, project-management, multi-project-tooling, operator-feedback, epistemic-humility, tracker-hygiene
related_entries:
  - methodologies/2026-06-17_tracker-state-drift-at-session-boundary.md
  - diagnostics/2026-05-23_beads-multi-database-working-directory-gotcha.md
  - methodologies/2026-05-23_beads-disk-reconciliation-discipline.md
  - methodologies/2026-06-09_read-bead-status-before-claiming-verify-explicit-deferral.md
  - diagnostics/2026-05-21_test-wrapped-tool-directly-narrowing-search-space.md
---

# Cross-Scope Search Blindness — Sweep All Instances First, Treat Operator Insistence as Broaden-Search Signal

## The Pattern

When tooling lives in multiple project-scoped instances on the same machine — `.beads/` directories across many sibling project folders, multiple `.notion/` workspaces, multiple `.git/` repos with related but distinct content, multi-account file-stores — agents searching for an entity default to the project they're CWD'd in and miss instances in sibling projects. The failure mode is symmetric across tooling types: the search returns negative results, the agent reports "doesn't exist," and the operator (who has ground-truth) pushes back. The agent's natural next move is to RE-CONFIRM the same negative finding with more thorough searches *in the same scope*. The correct move is to BROADEN the scope.

Pattern name: **"Cross-scope search blindness"** + **"Operator-insistence as broaden-search signal."**

Two tightly-coupled facets of one lesson.

## Facet 1 — Scope Myopia on Multi-Project Tooling

When `find / -name ".beads" -type d` would have returned 10+ instances on the machine, the agent searched only the local one ten different ways. The same shape applies to ANY multi-instance tooling pattern: `find / -name ".kf"`, `find / -name "venv"`, multiple notion workspaces, multiple GitHub orgs with sibling repos, multiple credential stores, multiple agent-memory stores. Default scope is "what I'm CWD'd in"; default scope is wrong when the entity could live in a sibling instance.

## Facet 2 — Operator-Insistence Updates the Search-Space Prior

When a user pushes back on the agent's "doesn't exist" finding with escalating directness ("are you sure?" → "check again" → "it's there, I'm telling you" → frustration), the cooperative-system signal is "your search space is too narrow." The agent's natural response is "let me re-confirm" (re-running the same search more thoroughly). The correct response is "let me widen" (sweep all sibling instances, check different naming conventions, check related stores). The cost of widening is small; the cost of N additional rounds of re-confirming the same negative is large — both in operator trust and in time.

## Recognition Signature

Both facets share the same trigger sequence:

- Agent has searched the local instance comprehensively (multiple keywords, multiple statuses, multiple commands)
- Agent has confidently concluded "doesn't exist"
- Operator pushes back, insisting the entity exists
- Agent is tempted to re-confirm the same negative with even more thorough local search
- The right move is to instead enumerate ALL instances of the relevant tooling on the system and search each

## When This Pattern Applies

- Beads / `bd` CLI projects with `.beads/` directories per project
- Multi-repo Git environments where related content lives in sibling repos
- Multi-workspace Notion / Confluence / Linear / Jira environments
- Multi-account credential or token stores
- Multi-tenant file-storage (Google Drive accounts, Dropbox accounts, S3 buckets)
- Any tooling where the same on-disk pattern (`.X/`) appears in multiple sibling project directories
- When an operator pushes back on an agent's negative finding with insistence

## When It Does NOT Apply

- Single-instance tooling where there's only one possible location for the entity
- Cases where the operator confirms the search space and just wants a re-confirmation
- Hallucination scenarios where the operator misremembers (rare, but possible — apply the rule once, surface evidence, then escalate honestly if still no match)

## How To Apply (Concrete Recipe)

- **On the FIRST "doesn't exist" claim, before reporting it:** sweep `find ~/Scripts -name ".X" -type d` (or equivalent for the tooling) and check each instance, not just the local one.
- **On operator pushback (round 2 of insistence at the latest):** if not already done, broaden the search space — different naming conventions, different sibling stores, different project-folder names that might contain the entity.
- **Don't re-confirm a negative more than once in the same scope.** Re-confirming N times burns operator trust without producing new information. The third negative finding in the same scope is the same as the first.
- **Treat operator insistence as updated prior on existence**, not as a request to re-search the same space. Operator has ground-truth context the agent doesn't.

## Concrete Fix-Recipe to Encode as Default

When asked to find or check ANY entity in tooling that uses on-disk directories (`.beads/`, `.kf/`, `.git/`, `.notion/`, etc.):

1. Identify the tool's on-disk pattern (e.g., `.beads/`)
2. Run `find ~/Scripts -name "PATTERN" -type d` (or operator's project root) to enumerate ALL instances
3. Search each instance in turn
4. Only then report "found in X" or "not found anywhere"

On operator pushback after a negative finding, default response is **"let me broaden"** not **"let me re-confirm."**

## Concrete Grounding (the producing session)

- Operator asked the agent (client-project project) to find content-idea beads for next week's blog posts
- Agent's CWD was `client-project`, where the bead store at `.beads/` had 15 active beads, none containing topic ideas
- **Round 1:** agent searched 8+ keywords (blog, content, ideas, topics, week, calendar, post, editorial). Reported "doesn't exist."
- Operator pushed back: "There should be one that unlocked Today. It should include ideas for the 3 posts next week."
- **Round 2:** agent searched additional keywords, checked closed beads, checked memories, checked wiki templates. Same negative. Reported "doesn't exist" more confidently with size of search as evidence.
- Operator pushed back again: "They should be open beads, which were waiting for TODAYS date"
- **Round 3:** agent inspected bead JSON schema, noted no date-unlock field exists, reported the bead schema doesn't even support what the operator was describing. Doubled down on "doesn't exist."
- Operator pushed back with profanity: "YES it's for the BLOG! it's in teh fucking beds beads"
- **Round 4:** agent FINALLY ran `find ~/Scripts -name ".beads" -type d` — returned 10 instances. Searched `[project]/cos/.beads`, found the entire `content-roll-out-q3` cluster: 24 beads, 8 weeks of pre-planned content, three beads for next week (cos-8b4k Mon, cos-03h8 Wed, cos-nsdf Fri) each with full briefs (OCEAN targets, COS frameworks to apply, 6-section structure, image specs, pre-publish checklists).
- **Total cost of scope myopia:** 4 rounds of agent stubbornness + operator frustration + ~30 minutes of wasted exchange + trust damage that took explicit naming/apology to begin repairing.
- **Total cost of the correct move (cross-project sweep on round 1):** one `find` command. The information would have been available in round 1.

## Why This Is a Strong Transferable Pattern

- Multi-project / multi-instance tooling is the modern norm, not the exception. Every developer's machine has many sibling project directories with parallel tooling.
- Operator-insistence-as-signal-to-broaden composes with general epistemic humility patterns: when someone with ground-truth says you're wrong, broadening the search is cheaper than continuing to defend the same negative.
- The fix is mechanical (one command pattern: `find` for sibling stores) and the upside is large (operator trust preserved, time saved).
- This is the kind of pattern that should be encoded as default behavior on the FIRST "doesn't exist" claim, not as an after-the-fact lesson.

## Composes With

- **Sibling entry: [[2026-06-17_tracker-state-drift-at-session-boundary]]** (filed 2026-06-17). That entry is about *syncing artifacts back to trackers at session boundaries*; this entry is about *searching trackers scoped correctly in the first place*. Both are tracker-hygiene patterns. Together they cover the two directions of "how to keep the tracker honest": don't let work products drift out, and don't search the wrong tracker for work products that already exist.
- **[[2026-05-23_beads-multi-database-working-directory-gotcha]]** — covers the operations-side failure of the same multi-`.beads/` topology (`bd close` silently fails when run from the wrong cwd). This new entry covers the search-side failure of the same topology. Both share root cause: `bd` selects its DB by walking up from cwd, so a project root with sibling subproject DBs creates silent scope-isolation. Together they cover both halves of the topology hazard.
- **[[2026-05-23_beads-disk-reconciliation-discipline]]** — session-start reconciliation discipline. Adjacent: it asks "what's already done in the tracker?" while this entry asks "where else might the tracker live?"
- **kf-meta.md always-on patches**, specifically **"Goal-Driven Execution"** ("Brief plan with verify steps; loop until criteria met") and **"Think Before Coding"** ("State assumptions explicitly. Surface multiple interpretations rather than silently choosing.") The default-scope assumption is exactly the kind of silent choice the patch warns against.
- **Verify-the-premise rule** (`~/.claude/rules/verify-premise-before-defensive-bead.md`) — same shape: when an agent confidently asserts a negative finding, the failure mode is almost always a too-narrow read of the evidence surface.

## Source Context

Discovered live in a 2026-06-17 semalytics-gtm session where the operator asked the agent to find pre-planned content beads for next week's blog posts. The beads existed in a sibling project's `.beads/` directory (`[project]/cos/.beads/`), but the agent searched only the local `client-project/.beads/` four times across four operator pushbacks before finally running `find ~/Scripts -name ".beads" -type d`. The find returned 10 instances on the machine; the relevant cluster (24 beads of pre-planned content) was in one of them. The cost of the correct move on round 1 was a single `find` command. The cost of scope myopia was four rounds of escalating operator frustration and explicit trust repair.
