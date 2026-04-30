# KF Vision & Roadmap Artifacts — Implementation Spec

**Status:** Ready for implementation  
**Author:** KnowledgeForge session, 2026-04-30  
**Target:** knowledgeforge-cw — two new commands + two new wiki artifact types  
**Effort estimate:** 4–6 hours total

---

## Problem Statement

KF's wiki is entirely backward-looking. Every entry captures something *learned* — a pattern, a decision, a finding. There is no artifact answering:

- *"What is this project trying to become?"* (vision)
- *"What are we building next, and in what order?"* (roadmap)

This creates a navigation blind spot: KF can recall what was decided but cannot check whether current work is still aligned with where the project is going. This spec fills that gap with two new wiki artifact types and two new slash commands.

**Inspiration:** [northstar by SebastianSKnorr](https://github.com/SebastianSKnorr/northstar) — a pure-markdown approach to session orientation. KF's implementation differs by: (1) integrating with the four-tier memory architecture and accretion system, (2) treating vision as periodically-revised rather than set-once, and (3) enforcing brevity via structured format constraints.

---

## Scope

Two deliverables:

| Deliverable | File | Command |
|-------------|------|---------|
| Vision artifact | `wiki/vision.md` | `/kf-vision` |
| Roadmap artifact | `wiki/roadmap.md` | `/kf-roadmap` |

Both are **human-initiated, human-authored** artifacts. KF formats and maintains; it does not generate the content autonomously.

---

## Artifact 1: `wiki/vision.md`

### Purpose

Answers: *"What is this project trying to become, and by what principles?"*

This is the strategic orientation layer. It is short by design — max 5 principles, each one sentence. If a principle can't be stated in one sentence, it isn't clear yet.

### File Format

```yaml
---
type: vision
scope: project
status: active          # active | under_revision | archived
version: 1
last_reviewed: YYYY-MM-DD
half_life_days: 60      # M17 staleness gate
review_triggers:
  - roadmap_horizon_complete
  - phase_count_completed: 3
  - days_since_review: 60
---

# Project Vision

## What We're Building
[1–2 sentences. Concrete — not aspirational fluff. What this is.]

## Why It Matters
[1–2 sentences. The problem this solves and for whom.]

## Principles (max 5)
1. [Principle] — [1-sentence rationale]
2. [Principle] — [1-sentence rationale]
3. [Principle] — [1-sentence rationale]

## What We're Explicitly Not Building
- [Item 1]
- [Item 2]
[Scoping out is as important as scoping in.]

## Revision Log
| Version | Date | What Changed | Why |
|---------|------|-------------|-----|
| 1 | YYYY-MM-DD | Initial creation | /kf-vision create |
```

### Format Constraints (enforced by the command)

- Max 5 principles
- Each principle: one sentence max + one-sentence rationale
- "Not Building" list: required, not optional
- Revision log: append-only — never delete prior versions from the log

### Loading Behavior (4-Tier Memory)

`wiki/vision.md` is **Tier 0** — persistent wiki — loaded selectively:

| Trigger | Action |
|---------|--------|
| Builder, Strategist, or Coordinator routing on multi-phase work | Auto-load as context prefix |
| User says "vision", "northstar", "direction", "where are we going" | Load explicitly |
| `/kf-roadmap create` or `update` | Load vision first (roadmap must align with vision) |
| TaskMaster morning standup | Summarize principles in 1 line |
| Explicit request | Always load |

**Not loaded:** Reckonings, single-entity Debugger requests, COS tasks, Navigator exchanges.

---

## Artifact 2: `wiki/roadmap.md`

### Purpose

Answers: *"What are we building next, and in what order?"*

This is the tactical execution layer — dependency-ordered phases with explicit outcomes. Distinct from vision (which is why/what we're becoming) and from beads/issues (which track individual tasks).

### File Format

```yaml
---
type: roadmap
scope: project          # project | domain
domain: ""              # M23 vocabulary for domain-scoped roadmaps
status: active          # active | paused | completed | archived
horizon: Q2-2026        # human-readable planning horizon (max 90 days recommended)
last_reviewed: YYYY-MM-DD
half_life_days: 30      # shorter than vision — roadmaps go stale faster
linked_vision_version: 1  # vision version this roadmap was written against
linked_wiki_entries:    # wiki entries that informed this roadmap
  - wiki/engineering/example-entry.md
---

# Project Roadmap

## Horizon Goal
[1 sentence — what "done" looks like at the end of this horizon.]

---

## Phases

### Phase 1: [Name]
**Status:** completed | in_progress | ready | blocked | deferred
**Depends on:** [Phase N] or none
**Knowledge prerequisites:** [wiki entries that should exist before starting] or none
**Outcome:** What "done" looks like — specific and verifiable.
**Accretion note:** Key learnings to file when this phase completes.

---

### Phase 2: [Name]
**Status:** ready
**Depends on:** Phase 1
**Knowledge prerequisites:** none
**Outcome:** ...
**Accretion note:** ...

---

### Phase 3: [Name]
**Status:** blocked
**Blocked by:** [reason — external dependency, pending decision, etc.]
**Outcome:** ...

---

## Deferred / Parking Lot
Items that are real but not sequenced. Not forgotten — explicitly deferred.

- [Item] — deferred until [condition]

---

## Revision Log
| Date | Change | Trigger |
|------|--------|---------|
| YYYY-MM-DD | Initial creation | /kf-roadmap create |
```

### Key Design Rules

- **Horizon max 90 days.** Longer horizons produce phases that are perpetually "future." Archive completed phases; create new roadmap per horizon.
- **`accretion_note` is pre-committed intent.** When a phase is created, the author states what learnings they expect to file. This makes accretion proactive rather than reactive.
- **`knowledge_prerequisites` creates bidirectional links.** A phase that depends on a wiki entry existing links the forward plan to the knowledge graph.

### Loading Behavior

Same as `wiki/vision.md` — Tier 0, loaded selectively on planning intent. When both exist, load vision before roadmap (vision is the frame; roadmap is the execution within it).

---

## Command 1: `/kf-vision`

### Modes

```
/kf-vision create         — Full elicitation, produces wiki/vision.md v1
/kf-vision update         — Differential revision, produces version diff for confirmation
/kf-vision review         — Read-only staleness check, no file changes
```

---

### `/kf-vision create` — Full Elicitation Protocol

**When to use:** No `wiki/vision.md` exists yet, or starting a new project.

**5-question elicitation sequence:**

```
1. What problem does this solve, and for whom? (1–3 sentences)

2. What does success look like in 12 months? 
   Be specific — not "widely adopted" but "X teams use it for Y."

3. What are the 3–5 principles that should guide every significant decision?
   For each: state the principle AND the tradeoff it encodes
   (e.g., "Latency over features — we'd rather ship nothing than ship slow")

4. What are you explicitly NOT building?
   Name at least 2 things that might seem like natural inclusions but are out of scope.

5. What single change in the world would make you abandon or pivot this vision entirely?
   (Tests whether the vision is grounded in reality)
```

**Behavior:**
- Ask questions sequentially — do not front-load all 5 at once
- After all 5 answers, produce a draft `wiki/vision.md` in the specified format
- Present the draft for human review before writing to disk
- Do not write the file until the human confirms

**Output:** `wiki/vision.md` version 1, with today's date as `last_reviewed`.

---

### `/kf-vision update` — Differential Revision

**When to use:** Vision exists but needs refreshing. Should feel like a 5-minute check-in, not a full rewrite.

**Protocol:**

Load current `wiki/vision.md`. Display the current content in summary form, then ask exactly four questions:

```
Current vision (v[N], last reviewed [date]):

What We're Building: [current statement]
Principles: [numbered list]
Not Building: [current list]

Four questions — answer only what has changed. "No change" is a valid answer for any.

1. Has what you're building shifted? If yes, how?

2. Any principles that no longer ring true, or new ones to add?
   (Remember: max 5. Adding one may mean removing one.)

3. Has the "not building" list changed?

4. One insight from recent work that should be encoded here?
```

**If all answers are "no change":** Update `last_reviewed` only. Write: *"Vision confirmed current. No changes. `last_reviewed` updated to [today]."*

**If changes are proposed:** Show a diff, not a rewrite:

```
Proposed changes to vision v[N] → v[N+1]:

  Principle 2: "[old]"
           → "[new]"
  Reason: [what the human said]

  No other changes.

Confirm? (yes / edit / discard)
```

Write only after confirmation. Append to revision log. Never delete prior revision log entries.

---

### `/kf-vision review` — Staleness Check (Read-Only)

Load vision, evaluate against staleness triggers:

| Trigger | Message |
|---------|---------|
| `days_since_review > half_life_days` | "Vision last reviewed N days ago (half-life: 60 days). Consider `/kf-vision update` before this session." |
| Roadmap horizon just completed | "You've reached the end of your planning horizon. Update vision before writing the next roadmap." |
| 3+ roadmap phases completed since last vision review | "3 phases completed since last vision review. Consider whether any learnings should update the vision." |

No file changes. No confirmation required. Output is advisory.

---

## Command 2: `/kf-roadmap`

### Modes

```
/kf-roadmap create              — Full elicitation, produces wiki/roadmap.md
/kf-roadmap update              — Status updates + differential revision
/kf-roadmap review              — Read-only staleness check
/kf-roadmap complete-phase <n>  — Close a phase, trigger accretion review
```

---

### `/kf-roadmap create` — Full Elicitation Protocol

**Prerequisite check:** If `wiki/vision.md` does not exist, prompt: *"No vision file found. Consider `/kf-vision create` first — roadmap phases should align with the project vision. Continue without it? (yes / create vision first)"*

**5-question elicitation:**

```
1. What is the planning horizon? (e.g., "Q2 2026", "next 8 weeks", "until v2 launch")

2. What does "done" look like at the end of this horizon?
   One sentence, specific and verifiable.

3. What are the 3–7 major phases of work within this horizon?
   For each phase, give: a name, a one-sentence outcome, and what it depends on.

4. Which phases are in progress right now?

5. What's explicitly deferred — real work that's not in this horizon?
```

**Behavior:**
- After elicitation, produce draft `wiki/roadmap.md` with phases in dependency order
- Show draft for review before writing
- Write only after confirmation

---

### `/kf-roadmap complete-phase <n>` — Phase Completion Protocol

**This is the accretion integration hook — the most important command mode.**

When a phase is marked complete:

1. Flip phase N status to `completed`
2. Display the phase's `accretion_note`
3. Run accretion review:

```
Phase [N] — "[name]" marked complete.

Accretion note: "[what was pre-committed]"

Accretion review:
- Did this phase produce any learnings worth filing to the wiki?
- Any patterns, decisions, or anti-patterns that should be preserved?
- Any wiki entries that should be updated based on what you learned?

(Answer "none" if nothing warrants filing — that's a valid outcome.)
```

4. For each learning the human identifies, route to Module 21 accretion filing protocol
5. Check `knowledge_prerequisites` of subsequent phases — if this completion satisfies a prerequisite, flag that the blocked phase may now be ready
6. Suggest `/kf-roadmap update` to reassess remaining phase statuses

---

### `/kf-roadmap update` — Status Update + Differential Revision

Load current roadmap. Display phase statuses. Ask:

```
Current phases:
  Phase 1: [name] — [status]
  Phase 2: [name] — [status]
  ...

Two questions:

1. Have any phase statuses changed? (in_progress → completed, blocked → ready, etc.)

2. Has the scope of any phase changed, or do new phases need to be added?
```

For status changes only: update in-place, no version bump, no diff.  
For scope/phase changes: show diff, require confirmation, bump revision log.

---

## Module Integration Points

### Module 14 (Metacognitive Monitor) — Drift Detection

When Builder or Strategist produces output that explicitly contradicts a stated vision principle, surface **once per session**:

> *"Vision principle [N] says '[principle].' The current [spec/recommendation] does [X], which pulls against it. Working against the principle deliberately, or should we revisit?"*

**Trigger conditions:**
- Explicit contradiction only — not vague tension
- Must be specific: "this design does X, but principle N says Y"
- Once per session per principle — do not repeat
- Accept any answer including "working against it deliberately"

**Not triggered by:** Work that's outside the vision scope but not contradicting it.

---

### Module 17 (Temporal Knowledge) — Staleness Gate

Add two new entries to the staleness trigger predicate:

```yaml
- artifact_type: vision
  half_life_days: 60       # from wiki/vision.md frontmatter
  severity_at_1x: LOW      # advisory — vision rarely blocks work
  severity_at_2x: MEDIUM   # surface more prominently

- artifact_type: roadmap
  half_life_days: 30       # from wiki/roadmap.md frontmatter
  severity_at_1x: LOW
  severity_at_2x: MEDIUM
```

In-progress phases that haven't moved in > 2× their expected duration also trigger a staleness signal, even if `last_reviewed` is recent.

---

### Module 21 (Knowledge Accretion) — Phase Completion Trigger

Add to the accretion trigger list:

```yaml
accretion_triggers:
  # ... existing triggers ...
  - roadmap_phase_completed:
      action: run_accretion_review
      source: phase.accretion_note
      prompt: "Phase [N] complete — were there learnings worth filing?"
```

**Bidirectional link — prerequisite satisfaction check:**  
When a new wiki entry is filed via accretion, check `wiki/roadmap.md` for any phase with `knowledge_prerequisites` listing that entry's path. If found, surface: *"Phase [N] listed this as a knowledge prerequisite. It may now be ready to start."*

Roadmap files themselves are **never** accretion candidates — they are planning artifacts, not knowledge artifacts.

---

### Module 25 (ERA) — Planned Entity Advisory

When ERA extracts entities from a query and any of those entities appear in upcoming roadmap phases, add an advisory to the ERA output record:

```yaml
era_roadmap_advisory:
  entity: "[name]"
  appears_in_phase: N
  planned_change: "[what phase N does to this entity]"
  advisory: "Consider planned Phase N coupling in current design decision."
```

Advisory only — ERA does not block on planned relationships.

---

### Relationship Between the Two Artifacts

```
wiki/vision.md      →  informs  →  wiki/roadmap.md
      ↑                                   ↓
      |                           phase completion
      |                                   ↓
      └──── revision informed ────── wiki entries (accretion)
```

**Workflow rule:** When writing a new roadmap (new horizon), load vision first. If vision and proposed phases are misaligned, update vision before writing the roadmap — not after.

`wiki/roadmap.md` stores `linked_vision_version` — if the current vision version is higher than this field, surface: *"This roadmap was written against vision v[N]. Current vision is v[M]. Consider `/kf-roadmap update` to check alignment."*

---

## Anti-Patterns

| Anti-Pattern | Consequence | Correct Approach |
|---|---|---|
| Auto-generating vision principles without human input | Vision reflects Claude's assumptions, not actual project intent | Human provides principles via elicitation; Claude formats and enforces structure |
| Loading vision/roadmap in every session | Context pollution — irrelevant to most tasks | Load selectively based on routing trigger |
| Treating roadmap entries as accretion candidates | Wrong information type — forward plans aren't learnings | Roadmap produces accretion candidates when phases complete; roadmap file itself is never filed as a wiki entry |
| Never reviewing — letting vision/roadmap go stale | Silent navigation drift; Claude gives contextually outdated strategic advice | M17 staleness gate fires at half-life; `/kf-vision review` and `/kf-roadmap review` on trigger |
| Horizon > 90 days on roadmap | Everything is perpetually "future" — phases never feel actionable | Archive completed phases; create new roadmap per horizon |
| Full re-elicitation on every update | Destroys continuity; people stop updating | `/kf-vision update` is differential — 4 targeted questions, not a full rewrite |
| Vision document grows to cover everything | Long vision = diluted signal; all principles feel equally important | Enforced brevity: max 5 principles, each 1 sentence |
| Blocking work when vision/roadmap don't exist | Most work doesn't need strategic orientation | These are optional infrastructure — their absence is not an error |

---

## Implementation Order

### Step 1 — Proof of format (30 min)
Write `wiki/vision.md` and `wiki/roadmap.md` for the current project manually using the formats above. Validate that the structure captures what's needed before building the commands.

### Step 2 — `/kf-vision` command (2 hours)
Build `.claude/commands/kf-vision.md` in `knowledgeforge-cw`. Implement all three modes (create, update, review). Test against a real project.

### Step 3 — `/kf-roadmap` command (2 hours)
Build `.claude/commands/kf-roadmap.md`. Implement all four modes. The `complete-phase` mode is the most important — it's the accretion integration hook.

### Step 4 — M17 staleness integration (30 min)
Add `artifact_type: vision` and `artifact_type: roadmap` to Module 17's trigger predicate. Update the module spec.

### Step 5 — M21 accretion trigger (30 min)
Add `roadmap_phase_completed` to Module 21's accretion trigger list. Update the module spec.

### Step 6 — M14 drift detection (1 hour, lower priority)
Add the principle-contradiction detection logic to Module 14's metacognitive monitor. This requires more careful tuning — too sensitive and it fires constantly; too conservative and it never fires.

**Minimum viable delivery:** Steps 1–3 only. Steps 4–6 add integration depth but the commands work without them.

---

## Files to Create/Modify

| Action | File | Notes |
|--------|------|-------|
| Create | `wiki/vision.md` | Project vision — manual first, then via command |
| Create | `wiki/roadmap.md` | Project roadmap — manual first, then via command |
| Create | `.claude/commands/kf-vision.md` | New slash command |
| Create | `.claude/commands/kf-roadmap.md` | New slash command |
| Modify | `modules/17_temporal_knowledge.md` | Add vision/roadmap to staleness trigger predicate |
| Modify | `modules/21_knowledge_accretion.md` | Add phase completion to accretion triggers |
| Modify | `modules/14_metacognitive_monitor.md` | Add vision principle drift detection |

---

*End of spec.*
