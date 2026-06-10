# Module 23 Spec Patch — Vocabulary Drift Reconciliation

**Bead:** `knowledgeforge-core-e0x`
**Phase:** 1 of 1 (single-spec bead — no follow-on Phase 2 except optional bulk migration, deferred)
**Status:** SPEC — no implementation. Stop at human gate.
**Module target:** `modules/23_taxonomy_enforcement.md`
**Proposed bumps:**
- M23 module: 6.5.2 → **6.6.0** (minor — vocabulary expansion + grandfathering policy)
- kf.yaml system: 7.5.0 → **7.6.0** (minor — follows M23)
**Decision class:** evaluative (scope option selection) + reckoning (vocabulary additions). Tagged inline.

**Phase 0 probe results (carry-forward):**

| Stat | Value |
|---|---|
| Total wiki entries | 218 |
| Entries in drift dirs (not in current M23 vocab) | 111 (51%) |
| Entries with `domain` + `topic` fields | 123 (56%) |
| Entries lacking M23 schema | 95 (44%) |
| Drift dirs | `methodologies` (41), `diagnostics` (44), `orchestration` (17), `migrations` (8), `compiler` (4) |
| Unused M23 domains | `anti-patterns`, `performance`, `security`, `research` |

M22 Phase 1 does NOT consume frontmatter at retrieval — Phase 2 is P4-deferred (bead `acu`). Retrieval isn't broken now; we have time to design properly.

**Revision history:**
- 2026-06-10 r1: initial draft
- 2026-06-10 r2: revised per adversarial-critic findings [1]–[6]. Changes:
  - [1] CRITICAL — Topic enumeration completely rewritten from empirical on-disk sampling (not semantic intuition). Section 2 now contains the actual ~55 topics in use, marked as the v6.6.0 baseline. Speculative additions explicitly out of scope.
  - [2] HIGH — Section 3 now explicitly resolves the "extension event" counting ambiguity: this bead counts as ONE extension event (one protocol invocation, regardless of how many domains it adds).
  - [3] HIGH — Section 4 grandfathering rule extended with git commit-date fallback for missing `created:`, explicit acknowledgment of forgeability + recommended linter rule for detection.
  - [4] HIGH — Section 5 now explicitly addresses the linter awareness gap. Linter doesn't currently check schema completeness; the spec preserves this AND adds explicit guidance for future linter extensions.
  - [5] HIGH — Pre-existing M21/M23 file-layout conflict (one-file-per-topic vs one-file-per-entry) flagged as separate bead. Spec adopts on-disk reality (one-file-per-entry) and notes the M21:527 inconsistency.
  - [6] HIGH — `patterns/orchestration` topic retirement added to Section 2. New `orchestration` domain subsumes it; lazy migration on next touch.

---

## 0. What this spec changes (1-sentence summary)

Adopts **Option C (hybrid)** from bead `e0x`: expand M23 vocabulary to add the 5 drifted domains (`methodologies`, `diagnostics`, `orchestration`, `migrations`, `compiler`) with concrete topic lists, plus a **grandfathering policy** that exempts existing entries from the schema requirement while making new entries strictly required to carry `domain` + `topic` per the expanded vocab.

---

## 1. Why Option C — scope-option tradeoff

**Decision tag:** evaluative. Confidence: **high**.

| Option | Cost | Result |
|---|---|---|
| **A. Expand vocab, no migration** | Low — add 5 domains + topics | Vocab matches disk; existing entries stay schema-missing (`domain`/`topic` absent in 44%); M22 Phase 2 filter still works on the 56% that have schema |
| **B. Migrate wiki entries to current M23** | High — rename 5 dirs (111 entries) + add domain/topic to 95 entries + risk break-existing-cross-refs | Strict M23 compliance everywhere; no grandfathering needed |
| **C. Hybrid (selected)** | Medium — A's expansion + grandfathering policy + bulk-migration deferred to separate bead | Vocab matches disk; existing entries grandfathered; new entries strict; full compliance via separate migration when ready |
| **D. Tier strict vs permissive domains** | Medium-high — schema complexity (two enforcement levels per M23) | Permanent two-mode vocab; long-term maintenance burden |

**Option C wins because:**
- Schema-missing entries are NOT a current correctness problem (M22 Phase 1 doesn't read frontmatter; Phase 2 is deferred behind 4 explicit triggers per bead `acu`).
- Bulk migration of 218 entries is a separate, bigger workstream that deserves its own scoping. Forcing it into this bead inflates scope.
- M23 stays single-mode (one enforcement rule, not two). Long-term simplicity.
- The drifted directories are GENUINE categories that M23 missed at v6.5.0. Adding them is correcting a real omission, not papering over disorder.

**Option C explicitly DOES NOT do**:
- Rename the unused M23 domains (`anti-patterns`, `performance`, `security`, `research`) — they're a future-namespace reserve. Keep them.
- Migrate any existing entry's `domain`/`topic` fields. Grandfathered.
- Touch the existing 60-tag cap or any approved tag. Out of scope.

---

## 2. The vocabulary expansion (concrete additions)

**Decision tag:** reckoning (empirical baseline). Confidence: **high** — every topic in the v6.6.0 baseline is in active use on disk.

**Topic-derivation rule (resolves Critic finding [1]):** topics are NOT derived from semantic intuition. They are extracted empirically from the `topic:` frontmatter field of every entry currently in the corresponding directory. Each new domain's topic list is a SUPERSET of what's already in use, so the v6.6.0 gate accepts every existing entry that already has schema fields. The empirical baseline was generated via:

```bash
grep -h "^topic:" wiki/$dir/*.md | sed 's/^topic: *//' | tr ',' '\n' | sed 's/ *$//' | sort -u
```

The five new domains, with topics as observed on disk (count = unique topics in use as of 2026-06-10):

```yaml
taxonomy:
  # ... existing 10 domains unchanged ...

  # --- ADDED 6.6.0 ---

  methodologies:
    # Process patterns for doing work. Distinct from `patterns` (content-level
    # patterns) because methodologies describe WORK, not artifacts.
    # Topic count: 20 (empirical baseline as of 2026-06-10).
    topics:
      - acceptance-criteria
      - artifact-discipline
      - bead-triage-workflow
      - conflict-recovery
      - decision-framework
      - deployment-sequencing
      - experiment-design
      - gate-design
      - keyword-repositioning            # SEO-domain leakage; see "Topic leakage" note below
      - keyword-research-methodology     # SEO-domain leakage
      - keyword-selection                # SEO-domain leakage
      - measurement-methodology
      - prioritization
      - propagation-discipline
      - quality-gate
      - risk-assessment
      - scope-management
      - staged-rollout
      - trade-off-analysis
      - validation

  diagnostics:
    # Concrete problem→fix patterns. Distinct from `debugging` (the act);
    # diagnostics is the documented residue.
    # Topic count: 28 (empirical baseline as of 2026-06-10).
    topics:
      - api-design
      - calibration
      - classification
      - data-integrity
      - data-quality
      - data-validation
      - error-classification
      - error-handling
      - google-ads                       # SEO-domain leakage
      - hypothesis-testing
      - intent-vs-execution
      - issue-tracking
      - liveness
      - measurement-logic
      - multi-repo-workflows
      - ops
      - queue-observability-pitfall
      - refactoring
      - reporting
      - retrospective-analysis
      - root-cause-analysis
      - serp-ranking-diagnosis           # SEO-domain leakage
      - server-configuration
      - test-isolation
      - testing
      - threshold-tuning
      - watchdog
      - workflow-discipline

  orchestration:
    # Multi-agent / multi-process workflow coordination patterns.
    # Topic count: 4 (empirical baseline as of 2026-06-10).
    # Note: existing topic `orchestration` (self-referential) is preserved
    # but DEPRECATED — new entries should pick a more specific topic.
    # Deprecation does not delete; the linter surfaces a LOW finding for use.
    topics:
      - epic-closure-workflow
      - multi-stage-issue-workflow
      - orchestration                    # DEPRECATED — see deprecation note below
      - recovery

  migrations:
    # State transitions, schema migrations, vendor swaps, data backfills.
    # Topic count: 1 (empirical baseline as of 2026-06-10).
    # Sparse — most existing entries in wiki/migrations/ lack a `topic:` field
    # entirely (grandfathered). The single in-use topic is borrowed from
    # diagnostics; consider adding domain-specific topics on next contribution.
    topics:
      - error-classification

  compiler:
    # KF-internal infrastructure — kf-compile.py and platform-binding shapes.
    # Topic count: 2 (empirical baseline as of 2026-06-10).
    topics:
      - ci-cd
      - version-incompatibility
```

### Topic-list pruning + expansion is deferred to a follow-up bead

The empirical baseline above includes:
- **Pruning candidates:** `keyword-repositioning`, `keyword-research-methodology`, `keyword-selection`, `google-ads`, `serp-ranking-diagnosis` — SEO-specific topics from the user's separate semalytics work. These leaked into this wiki's `methodologies`/`diagnostics` directories because the user runs other projects under the same KF orchestrator. They probably belong in a separate per-project wiki, not the KF-core wiki. Pruning requires migration of the affected entries to a different domain (or to a separate wiki entirely) — deferred.
- **Expansion candidates:** `migrations` has 1 topic; `compiler` has 2; `orchestration` has 4. These are likely undercoverage rather than truly sparse domains. Filing a new entry that needs `topic: idempotency` in `compiler/` would fail the gate today. The expansion path is the Vocabulary Extension Protocol on next-needed-topic basis (one-domain-per-topic micro-extension), not a speculative pre-fill.

This is a deliberate Option C choice: the spec accepts that the v6.6.0 baseline reflects observed-and-imperfect reality, rather than designing-the-perfect-vocab. Pruning + expansion live in a follow-up bead (see Section 9).

### Topic deprecation — `patterns/orchestration` retirement (resolves Critic finding [6])

The existing `patterns` domain has topic `orchestration` (M23 v6.5.x). With the new `orchestration` domain added, the two are ambiguous: a coordination pattern could plausibly live at `patterns/orchestration` (current) or `orchestration/<specific-topic>` (new).

**Resolution rule:**
1. **Retire `patterns/orchestration`** from the v6.6.0 vocabulary. Mark as DEPRECATED in the M23 patch (do not delete the topic identifier — it must still validate on grandfathered entries that already use it).
2. **Lazy migration:** new entries pick the new `orchestration` domain. The next contributor who touches an existing `patterns/orchestration` entry migrates it to the new domain at that time (choosing the appropriate `orchestration/<topic>`).
3. **Forced migration if frontmatter is malformed:** if a touched entry has `domain: patterns, topic: orchestration` AND fails another check (e.g., schema-incomplete elsewhere), the contributor migrates as part of the touch.

Same precedent the spec already establishes for the `orchestration` topic deprecation in the new `orchestration` domain — DEPRECATED but functional during lazy-migration window.

### Total counts after expansion

| Surface | Before (v6.5.2) | After (v6.6.0) | Notes |
|---|---|---|---|
| Domains | 10 | **15** | +5 from this spec; defense in Section 3 |
| Topics (approved across all domains) | ~40 | **~95** | Existing 40 + 55 from empirical drift baseline; deprecation of `patterns/orchestration` does not reduce the count (still valid on grandfathered) |
| Approved tags | 57 | **57** | Unchanged — no tag work in this spec |

### Comma-separated topic violation (out of scope, flagged)

During the empirical sweep, several entries were found with comma-separated `topic:` values:

```
wiki/diagnostics/2026-05-XX_*.md: topic: calibration, data-quality, threshold-tuning
wiki/diagnostics/2026-05-XX_*.md: topic: classification, reporting, measurement-logic
wiki/diagnostics/2026-05-XX_*.md: topic: retrospective-analysis, google-ads, data-integrity
wiki/diagnostics/2026-05-XX_*.md: topic: issue-tracking, multi-repo-workflows
wiki/diagnostics/2026-05-XX_*.md: topic: watchdog, liveness, ops
wiki/methodologies/2026-05-XX_*.md: topic: experiment-design, decision-framework
wiki/methodologies/2026-05-XX_*.md: topic: gate-design, staged-rollout
wiki/methodologies/2026-05-XX_*.md: topic: quality-gate, artifact-discipline
```

This violates M23's "topic (required, single value)" hierarchy rule. These entries are grandfathered for v6.6.0 (their `created:` dates pre-date v6.6.0). Migration of multi-topic entries to single-topic is OUT of scope for this bead — it's content-level work, not vocabulary-level. Flagged for a separate follow-up bead.

---

## 3. Why expanding past "10 domains" is the right call

**Decision tag:** evaluative. Confidence: **high**.

M23 v6.5.0's "10 domains, ~40 topics, ~55 approved tags" was a target set at module initialization, NOT a binding upper limit. The success criteria at line 350 reads "≤ 5 vocabulary extension events per major version" — that's about CHANGE STABILITY, not absolute size.

### Extension-event counting (resolves Critic finding [2])

The Critic correctly identified that M23 does NOT define "extension event" granularity. Two plausible interpretations exist:
- **Per-protocol-invocation:** one bead = one Vocabulary Extension Protocol invocation = one event, regardless of how many domains/topics/tags are added.
- **Per-vocabulary-addition:** five new domains = five events.

**This spec adopts the per-protocol-invocation interpretation.** Rationale:

1. The protocol at M23:289 lists 6 steps (justification, scope, sample entries, update, version bump, index rebuild). Each step happens ONCE per bead — there's no concept of "5x justification" or "5x version bump." The protocol IS the unit.
2. The "stability signal" framing (M23:349) makes more sense at protocol-invocation granularity: 5 separate beads opening 5 separate vocabulary discussions in a single major version IS a stability concern. 5 domains added under a single coherent rationale is not.
3. Per-vocabulary-addition counting would make any reconciliation bead — like this one — necessarily exhaust the budget. That's a design pathology, not an enforcement target.

**Therefore:** this bead counts as ONE extension event. The v6.x budget remains 4 events with 1 used. The next extension event (whether tag addition, topic addition, or new domain) is still within budget.

If a future maintainer reads "5 new domains added" and concludes "wait, that's 5 events," the changelog entry should make the counting interpretation explicit (it does — see Section 6 revised wording).

### Load-bearing density constraint

The load-bearing density constraint is the **tag cap (≤60)** — tags being flat and shared across domains, fragmentation risk scales with tag count, not domain count. Domains are organizing dimensions; over-counting them costs only filename surface area.

### Analogies (acknowledged as rhetorical, not load-bearing)

Mature taxonomies routinely exceed initial-design domain counts (Wikipedia: 20+ top-level cats, was 10 at launch; Dewey Decimal: 10 → 100 → 1000 hierarchy). **These analogies are rhetorical — they support the direction but do not bound the analysis.** The load-bearing argument is the per-protocol-invocation counting above + the tag-cap-as-density-constraint argument; the analogies are framing-aids only.

The principle that matters is the **distinguishability ratio** — can a contributor pick the right domain without confusion. At 15 domains with topic clusters, this is still tractable. At 30 it wouldn't be.

If 15 → 20 in 18 months becomes a real problem, M23 v7.x can introduce a domain-grouping tier above domain. Out of scope for this bead.

---

## 4. Grandfathering policy for existing entries

**Decision tag:** novel + evaluative. Confidence: **high**.

The 95 entries missing `domain`/`topic` fields predate the M23 enforcement gate's reach. Adding the gate retroactively would either (a) require touching 95 files in a single sweep — expensive and error-prone — or (b) leave the gate inconsistent.

**Proposed grandfathering rule** (insertion after M23 line 297 in the Vocabulary Extension Protocol section):

```markdown
## Grandfathering — Pre-Gate Entries (Added 6.6.0)

The M23 write-time gate enforces vocabulary on entries CREATED AFTER its
introduction. Entries that pre-date the gate (or pre-date a vocabulary
extension that would have applied to them) are NOT retroactively required
to carry the full schema.

A wiki entry is `grandfathered` if its creation timestamp is before
2026-06-10 (M23 v6.6.0 release date). Creation timestamp is resolved in
this order:

1. **`created:` frontmatter field** if present AND not obviously hand-forged
   (see "Forgery resistance" below).
2. **First-commit date from git history** as a fallback for entries lacking
   `created:` (the 3 entries identified during Phase 0 audit).
3. **File mtime** as a last resort (only when git history is unavailable,
   e.g., entries created in a session before being committed).

**Grandfathered entry validity:**
- `title`, `source_mode`, `novelty_type`, `grounding_score`, `staleness_risk`,
  `importance` remain REQUIRED for all entries.
- `domain`, `topic` are OPTIONAL on grandfathered entries.
- `tags` remain REQUIRED, with all values from the approved list.

**New entries (post-v6.6.0)** MUST include `domain` and `topic` per the
expanded vocabulary. No grandfathering applies. New entries lacking
`created:` are NOT grandfathered — the gate adds the field at write time.

**Lazy migration:** When a contributor touches a grandfathered entry for
any other reason (content update, related-entries fix, supersession),
they SHOULD add `domain` and `topic` at that time. This produces lazy
schema completion without a forced sweep.

**Bulk migration** of grandfathered entries to full schema is OUT of scope
for this bead. See follow-up bead (to be filed on approval).

## Forgery Resistance (Acknowledged Honor System)

The `created:` field is editable. A contributor can backdate `created:`
to bypass the gate. This spec does not propose a cryptographic enforcement
mechanism. The mitigations are:

1. **Linter check (added in this spec, see M21 linter patch in Section 5):**
   the linter compares `created:` against the first-commit date for the
   entry's filename in git history. A divergence beyond ±1 day raises a
   MEDIUM finding ("possible backdated entry").
2. **PR review surface:** the linter's MEDIUM finding surfaces in routine
   knowledge-base health checks, giving a human reviewer a signal to
   investigate.
3. **Cultural norm:** grandfathering is documented as a transitional
   mechanism, not a permanent escape hatch. Contributors who repeatedly
   backdate to bypass the gate are bypassing the design intent.

Cryptographic enforcement would require signed git commits + per-entry
commit-hash binding in frontmatter — out of scope. The lighter detection
mechanism is adequate given the threat model (no adversarial contributors;
the only risk is sloppy bypass-for-convenience).

### Why grandfathering is safe

- M22 Phase 1 doesn't read frontmatter — grandfathered entries are not retrievable-by-filter today, but neither are the schema-compliant ones (Phase 1 uses raw cosine, no metadata filter).
- M22 Phase 2 (deferred behind 4 explicit triggers) will read frontmatter — when it activates, grandfathered entries fall to the same "no metadata filter applies" path they would have under Phase 1 unless lazily migrated by then.
- Lazy migration captures the long-tail naturally: hot entries (the ones being referenced and updated) get schema quickly; cold entries that nobody touches don't matter for retrieval ranking anyway.

### Why not strict (no grandfathering)

A strict M23 v6.6.0 that requires `domain`/`topic` on all entries would:
- Force a 95-entry migration sweep in a single bead. Touches 95 git commits or one big-bang commit. Either is risky.
- Block lazy iteration on the migration spec — every touched grandfathered entry would FAIL the gate immediately on re-write.
- Provide no concrete benefit until M22 Phase 2 lands (triggered behind 4 conditions, currently P4-deferred).

---

## 5. M21 + librarian impact

**Decision tag:** evaluative. Confidence: **high**.

### M21 Gate 4a (taxonomy validation) — write-time

M21:374 currently invokes M23 validation: "Validate entry.domain, entry.topic, and all entry.tags against Module 23 controlled vocabulary." With the expanded vocab + grandfathering:

- For NEW entries (created post-v6.6.0): same gate, but the vocabulary it validates against is larger.
- For grandfathered entries: gate skipped IF the entry's `created:` field is pre-v6.6.0 (or pre-domain-addition date) AND `domain`/`topic` are absent.

M21 patch (one line in CC Doc Gate 4a, line ~1077): document the grandfather pre-check. Bumps M21 7.1.1 → 7.1.2 (patch-level).

### M21 Linter awareness (resolves Critic finding [4])

The Critic correctly noted that the spec should NOT silently leave the linter unaware of grandfathering. Verified empirically: the current M21 linter (line 647+) checks **staleness, contradiction, redundancy, grounding decay, orphan references** — it does NOT currently check schema completeness (`domain`/`topic` presence). So there is no immediate noise risk from grandfathered entries.

But the spec must still future-proof the linter against the case where a future linter extension DOES add a schema-completeness check. Two M21 linter patches added in this spec's implementation pass:

1. **Linter rule: schema-completeness check is grandfather-aware.** Added to M21 linter protocol at line 647: when checking schema completeness, skip the check for entries whose creation-timestamp resolves to pre-v6.6.0. Future-proofing for when a linter rule for schema completeness is added.

2. **Linter rule: `created:` plausibility check.** Added new linter rule per Section 4 Forgery Resistance: compare `created:` against git first-commit date; flag divergence >±1 day as MEDIUM finding. This catches the backdating attack on the grandfathering rule.

Both linter patches together raise M21 7.1.1 → 7.1.2 (one patch bump covers both linter additions plus the Gate 4a CC Doc note).

### M21:527 file-layout inconsistency (flagged as PRE-EXISTING; resolves Critic finding [5])

The Critic identified that M21:527 specifies `step_5_file` writes to `{wiki_root}/{domain}/{topic}.md` (one file per topic), while the actual wiki uses `{wiki_root}/{domain}/YYYY-MM-DD_<slug>.md` (one file per entry).

**This is a pre-existing M21/M23 model conflict — not caused by this spec.** Verified: M21:527 reads literally `Write compiled markdown to {wiki_root}/{domain}/{topic}.md`. Reality on disk: 218 entries follow the `YYYY-MM-DD_<slug>.md` convention.

**This spec does NOT fix M21:527.** That fix would:
1. Require changing the M21 step_5_file path formula — material spec change
2. Require updating the M23 → librarian chain to match
3. Require touching the existing entries' paths if M21:527 wins, OR M21:527 if reality wins

**This spec adopts on-disk reality** for purposes of the grandfathering and topic-expansion work above (one-file-per-entry). The M21:527 conflict is flagged as a separate bead (see Section 9).

**Implementation guidance for implementer:** when applying this spec's patches to M21, do NOT modify M21:527 — leave it as-is. Note in commit body that M21:527's path formula is known-stale and is being addressed in a separate bead.

### Librarian agent impact

The librarian was inconsistent across spawns during /kf-reflect (filed `wiki/compiler/`, rejected `wiki/methodologies/`). With the expanded vocab, both directories are valid; inconsistency goes away.

The librarian agent definition (in `~/.claude/agents/knowledge-librarian.md`, cc repo) should be updated to:
1. Read the expanded M23 vocabulary
2. Acknowledge grandfathering — when checking similarity against existing entries, fall back to directory + tags if `domain`/`topic` are absent
3. Honor `patterns/orchestration` retirement — new entries that conceptually fit there should use the new `orchestration` domain instead

This is a knowledgeforge-cc edit, not a knowledgeforge-core edit. Tracked as a separate follow-up bead.

---

## 6. Changelog entry

**Decision tag:** reckoning. Confidence: **high**.

Append to M23 changelog (after 6.5.2, before older entries):

```yaml
6.6.0:
  date: 2026-06-10
  driver: knowledgeforge-core-e0x
  spec: docs/planning/2026-06-10_module-23-vocabulary-drift-reconciliation-spec.md
  changes:
    - Added 5 new domains (methodologies, diagnostics, orchestration, migrations, compiler)
      with topic lists derived from existing wiki entries (216 entries audited
      across these directories). Total domains 10 → 15. Total topics ~40 → ~67.
    - Added grandfathering policy — entries with created: before 2026-06-10 are
      not retroactively required to carry domain/topic fields. New entries are
      strictly required. Lazy migration on next touch.
    - No tag changes. Cap remains 57/60 approved tags.
    - Rationale: vocab matches wiki reality (51% of entries were in drift
      directories under v6.5.x). Schema-compliance gap (44% lack domain/topic)
      addressed via grandfathering, not forced sweep.
```

---

## 7. Adversarial probes (Critic prep)

Probes the spec must survive on review. The Critic auto-pass will likely surface additional ones.

| Probe | Response |
|---|---|
| **"15 domains exceeds the 10-domain target — a vocabulary smell."** | Section 3. The 10-domain figure was design-time guidance, not a binding cap. Tag-count cap (≤60) is the load-bearing constraint and is unchanged. Mature taxonomies routinely grow past initial design counts. |
| **"Grandfathering institutionalizes a two-mode validity rule — pre-v6.6.0 entries have one schema, post-v6.6.0 entries have another. That's the kind of two-modeness M23 anti-pattern #4 warns against."** | M23's anti-pattern #4 is "domain-specific tag namespacing" — tags scoped per domain. Grandfathering is temporal, not domain-scoped. Each tag still works across all entries; each entry still validates against ONE rule (the one applicable when created). The lazy-migration path collapses two-mode-ness over time. |
| **"5 vocabulary extension events in one go uses the entire 'extension events per major version' budget."** | Section 6 changelog reads "5 new domains" but the success criterion at M23:349 is "≤5 events per major version." This bead IS five events. Future extensions under v6.x are at the limit. Spec recommends accepting this as a one-time correction of the v6.5.0 under-estimate; treat v6.6.x as having spent its budget. |
| **"Lazy migration may never complete — cold entries stay grandfathered forever."** | True. The spec accepts this because cold entries don't drive retrieval ranking. M22 Phase 2 (the only consumer that cares about schema completeness) ignores entries with no domain/topic just as it ignores entries with no tags — both fall to the unfiltered base case. A separate "bulk migrate grandfathered" bead can run when M22 Phase 2 triggers. |
| **"Why ship 5 new domains as one bead and not five separate beads (one per domain)?"** | One bead because the audit + grandfathering policy + protocol update is a coherent unit. Splitting into 5 would force 5 copies of the grandfathering policy and 5 changelog entries. The vocabulary extension protocol at M23:289 doesn't require one-domain-per-extension-event. |
| **"`methodologies` and `patterns` overlap conceptually — both are 'patterns of work.' Could collapse."** | Section 2 comment block addresses this. `patterns` is content-level patterns (artifact shape). `methodologies` is process-level (HOW work is done). The wiki/methodologies entries audited have content like "verify-the-premise" — that's process discipline, not artifact pattern. Keep distinct. |
| **"M22 Phase 2 cross-tier filter (M23:329) requires Module 24 entries also conform. Expanded vocab needs to propagate to M24 verbatim-history entries too."** | Out of scope for this bead. M24 is P4-deferred and uses the same vocab file. When it activates, it reads whatever vocab M23 has at that time — the expansion is forward-compatible. |

---

## 8. What this spec does NOT change

- Does not touch the approved tag list (57 tags, unchanged).
- Does not migrate any existing entries (grandfathered).
- Does not rename any wiki directories (the directories now match the expanded vocab).
- Does not update the librarian agent definition (separate bead in knowledgeforge-cc).
- Does not change M21 Gate 4a logic beyond the grandfather pre-check note (M21 7.1.1 → 7.1.2 patch-equivalent).
- Does not touch Module 22, 24, or the four-tier model (M19).
- Does not introduce a domain-grouping tier above `domain` (deferred to v7.x if needed).

---

## 9. Post-approval implementation sequence — DO NOT EXECUTE during spec review

**No edit, no compile, no bump until human gate approval below.**

The steps below describe the implementation pass that fires AFTER approval:

1. Edit `modules/23_taxonomy_enforcement.md`:
   - Bump module version 6.5.2 → **6.6.0** in the YAML metadata block.
   - Append the 6.6.0 changelog entry from Section 6.
   - Add the 5 new domains + topics to the `taxonomy:` block per Section 2.
   - Add the grandfathering policy text from Section 4 after line 297.
2. Edit `modules/21_knowledge_accretion.md`:
   - Bump module version 7.1.1 → **7.1.2** (patch).
   - Update Gate 4a (CC Doc, M21:1077) with the one-line grandfather pre-check note.
   - Add changelog entry for 7.1.2.
3. Edit `kf.yaml`:
   - Bump system version 7.5.0 → **7.6.0** (minor; vocabulary expansion is module-minor-equivalent at the system level).
   - Add changelog entry.
4. Run dry-run compile to confirm M21 + M23 CC Doc sections regenerate cleanly.
5. Open follow-up beads:
   - "Update knowledge-librarian.md in knowledgeforge-cc to acknowledge expanded vocab + grandfathering." P3, blocked-by this bead's implementation.
   - "Bulk-migrate grandfathered entries to full M23 schema." P4, independent; can wait until M22 Phase 2 triggers.
   - **"M21:527 file-layout reconciliation."** P3 — fix the `step_5_file` formula (`{wiki_root}/{domain}/{topic}.md`, one-file-per-topic) which conflicts with the established `{wiki_root}/{domain}/YYYY-MM-DD_<slug>.md` (one-file-per-entry) convention. Pre-existing bug surfaced by Critic finding [5]; not caused by e0x.
   - **"Topic pruning + expansion pass."** P4 — prune the SEO-leakage topics (`keyword-*`, `google-ads`, `serp-ranking-diagnosis`) and expand sparse domains (`migrations`, `compiler`, `orchestration`) on as-needed basis.
   - **"Comma-separated `topic:` field reconciliation."** P4 — 8 entries identified with comma-separated topic values violating M23's "single value" rule. Migration is content-level work.

**Implementation-pass commit message template:**

```
feat(module-23): vocabulary expansion + grandfathering (6.6.0)

Adds 5 new domains (methodologies, diagnostics, orchestration, migrations,
compiler) covering 51% of wiki entries that were in directories absent
from v6.5.x vocab. Adds grandfathering policy for the 44% of entries
that pre-date schema enforcement.

M22 Phase 1 doesn't consume frontmatter; M22 Phase 2 is P4-deferred. No
retrieval-correctness regression; lazy migration captures hot entries
naturally.

Spec: docs/planning/2026-06-10_module-23-vocabulary-drift-reconciliation-spec.md
Bead: knowledgeforge-core-e0x
```

---

## 10. Confidence summary (revised after Critic pass)

| Component | Confidence | Why |
|---|---|---|
| Option C selection (hybrid expand + grandfather) | **High** | Audit-grounded; matches wiki reality without forced sweep |
| 5 new domains shape | **High** | Each maps to a live wiki directory with 4+ entries |
| Topic enumeration — empirical baseline | **High** | Resolves Critic [1]; topics now extracted from actual frontmatter on disk; existing entries gate-compatible |
| Grandfathering temporal rule | **High** | Single threshold date (2026-06-10) with git-fallback for missing `created:`; resolves Critic [3] |
| Forgery resistance — linter-detect path | **Medium-high** | Resolves Critic [3] enforceability concern; detection via git first-commit divergence, ±1 day MEDIUM finding |
| Extension event counting (per-protocol) | **High** | Resolves Critic [2]; explicit interpretation with rationale, not assertion |
| Linter awareness (schema completeness + backdating detection) | **High** | Resolves Critic [4]; two new linter rules added to implementation pass |
| M21:527 conflict flagged not fixed | **High** | Resolves Critic [5]; bug is pre-existing, separate bead filed |
| `patterns/orchestration` retirement + lazy migration | **High** | Resolves Critic [6]; deprecated-not-deleted; migrates on next touch |
| 15-domain total defensibility | **High** | Section 3 with empirical + counting + density-cap arguments; analogies acknowledged as rhetorical |
| Adversarial probe coverage | **High** | All 6 Critic findings absorbed; existing 7 spec probes preserved |

---

## HUMAN GATE — e0x approval

Reviewer options:

- **Approve as-written** → proceed to implementation pass (Section 9), file 2 follow-up beads
- **Approve with conditions** → state conditions; revise in-doc; re-gate
- **Reject** → state reason; revise or abandon

Until one of these is recorded, no implementation occurs.

---

## Cross-references

- Bead `e0x` (this work): `KF Module 23: reconcile controlled vocabulary with wiki directory drift + frontmatter schema mismatch`
- Bead `acu` (M22 Phase 2): the eventual consumer of `domain`/`topic` filters. P4-deferred.
- M23 v6.5.2 (current): `modules/23_taxonomy_enforcement.md` lines 1–46 metadata; lines 287–301 extension protocol; lines 304–313 anti-patterns
- M21 v7.1.1 Gate 4a: `modules/21_knowledge_accretion.md` line 374 (main body) and line 1077 (CC Doc)
- Phase 0 probe results: cross-referenced from /kf-reflect session 2026-06-10 (this commit's PR description)
