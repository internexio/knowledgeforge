# Module 21 Spec Patch — Linter Violation Counter for Hook Graduation

**Bead:** `knowledgeforge-core-8zt`
**Phase:** 1 of 1 (single-bead spec; impl tracked separately)
**Status:** SPEC — no implementation. Stop at human gate.
**Module target:** `modules/21_knowledge_accretion.md`
**Proposed bumps (versions verified 2026-06-12):**
- M21 module: 7.1.3 (or 7.1.4 if 8gp lands first) → **7.2.0** (minor — defended in Section 4 against Critic-finding-[5] data-destruction concern)
- kf.yaml system: 7.7.1 (or 7.8.0 if 8gp lands first) → minor bump follows M21
**Decision class:** evaluative (counter design + storage location) + reckoning (graduation criteria already settled in `5fd`). Tagged inline.

**Revision history:**
- 2026-06-12 r1: initial draft
- 2026-06-12 r2: revised per adversarial-critic findings [1]–[5]. Changes:
  - [1] CRITICAL — compile-time snapshot freshness check added. `load_graduation_snapshot()` rejects snapshots older than `window_days` (treats all rules as not-yet-graduated; emits warning).
  - [2] HIGH — compile-time numeric re-derivation. Don't trust `eligible_for_graduation` flag blindly; re-compute from stored `event_count` and `session_ids` length against thresholds. Tampering the flag without also tampering the counts is detected.
  - [3] HIGH — `linter_check.kind` constrained to stateless artifact patterns at v1. Session-event-ordering patterns are documented as deferred to a follow-up bead (per Section 3 — the alternative real-time hook path). The example replaced with a stateless one.
  - [4] HIGH — counter storage location moved to `.kf/linter/` (already gitignored as `.kf/`). Linter scan adds dotfile-exclusion rule. No collision with wiki linter checks.
  - [5] HIGH — semver classification justified explicitly. Log rotation is not breaking because the event log has no external consumer contract; the snapshot is the contract surface and is rebuilt-not-rotated. Justification added to Section 4.

---

## 0. What this spec changes (1-sentence summary)

Adds a violation-event counter to M21's Knowledge Base Linter so that path-gated rules emitted by the Phase 2 cc_rules emitter can graduate to hooks when their violation pattern meets the threshold from Phase 2 spec Section 5 (≥3 violations across ≥2 distinct sessions in the last 30 days). Counter state lives in a sidecar file colocated with the wiki; the linter reads-and-decides, the cc_hooks emitter consumes the graduation flag at compile time.

---

## 1. Why this work matters now

**Decision tag:** reckoning. Confidence: **high**.

From Phase 2 spec (`5fd` Section 5):

> The hook emitter ships in inert-default mode at v1, structurally analogous to Phase 1's `native` field.

The cc_hooks emitter exists in the compiler, accepts `cc_hooks` frontmatter, and would work if any module shipped entries. **Zero entries ship at v1.** Modules cannot author `cc_hooks` entries without violation-history evidence; violation history is only counted by the linter; the linter doesn't have a counter today.

This bead closes the inert-emitter situation by providing the counting machinery. Without it, the Phase 2 hook emitter remains permanently inert.

---

## 2. Constraints inherited from existing M21 + 5fd

**Decision tag:** reckoning. Confidence: **high**.

| Constraint | Source | Implication |
|---|---|---|
| **Graduation threshold: ≥3 violations across ≥2 distinct sessions in last 30 days** | `5fd` Section 5 | Hard requirement; counter must support per-session tagging + 30-day window |
| **Linter is periodic, not real-time** | M21:679 ("Health check the knowledge base" trigger; not on every event) | Counter must be event-recorded continuously but evaluated lazily |
| **Linter scans entries, not events** | M21:683 ("Scan all entries in the knowledge base") | Counter is a NEW data source for the linter; not a re-use of existing scan logic |
| **Only `cc_rules` entries with `linter_check` block are eligible for graduation** | `5fd` Section 5 ("for v1, only rules tagged with a `linter_check` block in their cc_rules entry are eligible") | Counter must scope to opted-in rules; ignore others |
| **No new external dependencies** | Project CLAUDE.md — "No external dependencies unless absolutely necessary" | Counter storage must use stdlib |

---

## 3. Counter design (Strategist analysis)

**Decision tag:** evaluative (storage location + event-record mechanism). Confidence: **high** on shape; **medium** on threshold-of-threshold (the per-rule activation policy below — calibratable).

### Three storage options

| Option | Storage | Pro | Con |
|---|---|---|---|
| **A. SQLite sidecar** (`{wiki_root}/.linter-counter.db`) | Single binary file; query-efficient | Atomic writes; range queries; future-extensible | Binary file complicates git history; new dependency on stdlib `sqlite3` |
| **B. JSON sidecar** (`{wiki_root}/.linter-counter.json`) | Plain text; git-diff-friendly | Stdlib only; reviewable in PRs; merges work | Concurrent-write risk in multi-session use; full-rewrite on every event |
| **C. Append-only log** (`{wiki_root}/.linter-events.log`) | One line per event; rotation-friendly | Trivially append-safe; simplest mental model; replay-able | Linter must parse/aggregate on every run; growth-management story needed |

### Recommendation: **C (append-only event log) + B (aggregated snapshot)**

**Hybrid that gets the best of both:**

1. **Event recording (write path):** When a violation event fires, append a single line to `.kf/linter/events.log` — `{ISO datetime}\t{session_id}\t{rule_filename}\t{event_type}`. Append-only is multi-session-safe (no concurrent-write hazard); rotation handled by linter (see below). Storage location is `.kf/linter/` (not `{wiki_root}/`) because operational linter state is not wiki content — resolves Critic finding [4].

2. **Aggregation snapshot (read path):** When the linter runs, it reads the event log, computes a snapshot keyed by rule_filename — `{rule_filename: {session_count, event_count, first_seen, last_seen, eligible_for_graduation}}` — and writes the snapshot to `.kf/linter/counter.json` (overwriting). Snapshot is auditable locally; not committed to git (per `.gitignore` rule `.kf/`).

3. **Log rotation:** After snapshot is written, the linter truncates events older than 30 days from the log (the window required by `5fd` Section 5). Events <30 days old stay so the next linter run can re-aggregate.

### Storage location resolves wiki contamination (Critic finding [4])

The initial draft placed counter state in `{wiki_root}/.linter-*` (same partition as existing `wiki/.linter_offset` at M21:727). The Critic correctly identified two problems:
1. Wiki is git-tracked content; per-machine linter state pollutes commits.
2. M21's existing linter scan iterates entries in `{wiki_root}/` — `.linter-counter.json` could be checked by the schema-completeness rule (added 7.1.2 per e0x) and falsely flag as schema-invalid.

The fix is to move counter state to `.kf/linter/` (subdir under the already-gitignored `.kf/`). This composes with KF's existing operational-state partition and exempts it from the wiki linter scan by being outside `{wiki_root}/`.

**A separate small M21 patch (in the same implementation pass) moves `wiki/.linter_offset` to `.kf/linter/offset` for consistency.** This is a one-line existing-file move — backwards-compatible because the offset is per-machine operational state that nothing else reads.

This composes well:
- Event recording: cheap, concurrent-safe (`a+` append in any language)
- Snapshot computation: only happens on linter runs (periodic, not real-time)
- Storage growth: bounded by 30-day window + rotation
- Reviewability: snapshot is plain JSON, diff-friendly in PRs
- Stdlib: no new dependencies

### Event-recording trigger

A violation event fires when **a session that has loaded a path-gated rule (`.claude/rules/kf/*.md`) subsequently produces output that contradicts the rule's directive**. Detecting that is the hard part. Two viable approaches:

**3a. Linter detection (recommended for v1) — STATELESS ARTIFACT PATTERNS ONLY:** During the existing linter scan, the linter checks the wiki content artifacts (entry frontmatter, body text, compile.md log) for evidence of rule-directive violation patterns. The check is rule-specific — the rule's `linter_check` block (in its cc_rules frontmatter, per `5fd` Section 5) declares what counts as a violation.

**Critical constraint (resolves Critic finding [3]):** at v1, `linter_check.kind` is restricted to STATELESS ARTIFACT PATTERNS. The linter's evidence sources are wiki entries, compile logs, and entry frontmatter — these are artifacts, not session event streams. Patterns that require temporal ordering ("event X preceded event Y in this session") are NOT evaluable from these sources and are not supported at v1.

```yaml
# In a cc_rules entry's frontmatter (v1 supported pattern)
cc_rules:
  - filename: wiki-entries-have-source-context.md
    paths: ["wiki/**/*.md"]
    body_section: "CC Rules — Wiki entry source context"
    linter_check:
      kind: frontmatter_field_missing
      field: "Source Context"
      target_files: "wiki/**/*.md"
      # Logical: "wiki entry filed without Source Context heading" → violation
```

Other stateless `linter_check.kind` values for v1:
- `frontmatter_field_missing` — field absence in matched files
- `frontmatter_field_value_disallowed` — frontmatter field has a value outside an approved list
- `body_pattern_present` — regex pattern appears in entry body
- `body_pattern_absent` — regex pattern required to appear in entry body does not

**3b. Session-ordering patterns (DEFERRED to follow-up bead):** Patterns like "git commit preceded a test run" require session event ordering, which is not in the v1 evidence sources. A follow-up bead can specify either (a) a session log format with canonical path and linter access pattern, or (b) a PostToolUse hook approach that records candidate events. Both are out of scope for v1; rules that need temporal-ordering checks stay in the rule tier without graduation eligibility until that bead lands.

### Counter snapshot schema

`{wiki_root}/.linter-counter.json`:

```json
{
  "snapshot_at": "2026-06-12T14:30:00Z",
  "window_days": 30,
  "rules": {
    "tests-before-commit.md": {
      "first_event": "2026-05-25T09:12:00Z",
      "last_event": "2026-06-12T11:44:00Z",
      "session_ids": ["sess-aaa", "sess-bbb", "sess-ccc"],
      "event_count": 7,
      "eligible_for_graduation": true,
      "graduation_reason": "7 events across 3 sessions, both thresholds met"
    },
    "imports-sorted.md": {
      "first_event": "2026-06-10T15:00:00Z",
      "last_event": "2026-06-12T11:00:00Z",
      "session_ids": ["sess-bbb"],
      "event_count": 2,
      "eligible_for_graduation": false,
      "graduation_reason": "1 session (need ≥2); 2 events (need ≥3)"
    }
  }
}
```

### How the cc_hooks emitter consumes graduation

**Compile time** (added in this spec to Phase 2 emitter logic): `kf-compile.py` reads `.kf/linter/counter.json` before emitting. For each module's `cc_hooks` entry that references a `source_rule`, the emitter performs THREE checks (not just one) before emitting the hook:

1. **Snapshot freshness check** (resolves Critic finding [1]): if `snapshot.snapshot_at` is older than `window_days` (30 days), treat ALL entries as not-yet-graduated. Emit compile warning: "graduation snapshot is stale (last run: {date}); all hooks held inert until linter re-runs." Reason: a graduated-flag from a stale snapshot may no longer reflect reality (the supporting violations may have aged past the window).
2. **Numeric re-derivation check** (resolves Critic finding [2]): don't trust the snapshot's `eligible_for_graduation` boolean. Recompute it at compile time from the snapshot's stored numbers — `entry.event_count >= 3 AND len(entry.session_ids) >= 2`. If recomputed result differs from stored flag, emit compile warning: "snapshot eligibility flag for {rule} contradicts its own counts; tampering or schema drift suspected; treating as not-graduated." This catches hand-edits to the flag that left the counts untouched.
3. **Existence check**: source_rule must reference an actual cc_rules entry that exists in the compiled set; otherwise compile warning and skip.

If all three checks pass, the hook entry is emitted into `settings.kf.json`. Otherwise the entry stays inert.

This means: modules can author `cc_hooks` entries opportunistically; the emitter gates them by three independent checks; calibration happens organically; tampering attacks within the compile-before-linter window are detected at compile time.

---

## 3a. Semver justification — minor bump defended against finding [5]

**Decision tag:** evaluative. Confidence: **high**.

The Critic correctly noted that log rotation (truncating events >30 days from `.kf/linter/events.log`) is a destructive operation on persistent state. Under a strict reading of the project CLAUDE.md versioning rule, destructive protocol additions could be considered breaking.

**Justification for minor bump:**

1. **The event log has no external contract surface.** It is a per-machine, gitignored operational artifact. No module reads from it directly except this M21 linter itself. Rotating it cannot break any external consumer because no external consumer exists.
2. **The snapshot IS the contract surface, and it is rebuilt, not rotated.** Each linter run regenerates the snapshot from the post-rotation events. The contract surface (what other modules read) has no concept of "old data was here." From the perspective of downstream consumers, the snapshot has always been "current window only."
3. **30-day window matches `5fd` Section 5** — the spec doesn't invent a new policy; it implements an already-approved threshold. The destructiveness is inherent to the policy, not a new design choice in this bead.
4. **Recalibration scenarios** (Critic's concern about future window adjustments): if a future bead changes the window from 30 days to 60, the FIRST linter run after the change would have only 30 days of evidence (because the old rotation already deleted >30-day events). The new 60-day window would populate organically over the next 30 days. This is a one-time recalibration latency, not a permanent loss of capability.

Therefore: minor bump (7.1.x → 7.2.0) is correct. The Critic's concern is acknowledged and the rationale is recorded so that a future maintainer can revisit the call.

---

## 4. M21 changelog + linter protocol additions

**Decision tag:** reckoning. Confidence: **high**.

### Linter protocol additions (M21:683)

Four new linter responsibilities:

```yaml
linter_behavior:
  protocol:
    # ... existing checks ...
    6.5 Exclude operational dotfiles from scan — when iterating wiki entries,
        skip any file whose name starts with `.` (dotfile exclusion). Prevents
        the linter from checking its own state files (.linter-counter.json,
        .linter_offset, etc.) against wiki entry schema rules. Resolves a
        latent collision between the schema-completeness check (added 7.1.2)
        and operational state files.
    7. Record violation events — for each cc_rules entry with a linter_check
       block (and linter_check.kind in {frontmatter_field_missing,
       frontmatter_field_value_disallowed, body_pattern_present,
       body_pattern_absent}; temporal-ordering kinds NOT supported at v1),
       evaluate the pattern against the wiki entries that match
       linter_check.target_files. Append matches to .kf/linter/events.log
       (tab-separated: timestamp\tsession_id\trule_filename\tevent_type).
    8. Aggregate snapshot — after scanning, rotate events older than 30
       days from the log; compute per-rule counts (events, sessions,
       first/last seen, eligibility); write .kf/linter/counter.json.
       Snapshot file is the source of truth for graduation decisions.

  output_format:
    # ... existing format ...
    # NEW — added 7.2.0:
    ### Graduation candidates ([count])
    [rules that crossed the graduation threshold this run; recommendation
     to add cc_hooks entry referencing the rule]
```

### Changelog entry

```yaml
7.2.0:
  date: 2026-06-12
  driver: knowledgeforge-core-8zt
  spec: docs/planning/2026-06-12_module-21-linter-violation-counter-spec.md
  changes:
    - Added violation-event counter to Knowledge Base Linter. Two new linter
      responsibilities: event recording (append to .linter-events.log) and
      snapshot aggregation (write .linter-counter.json keyed by rule filename).
    - Counter window — 30 days. Graduation threshold — ≥3 events across ≥2
      distinct sessions (per Phase 2 spec 5fd Section 5).
    - New linter output section: "Graduation candidates" listing rules that
      crossed the threshold; recommendation includes the cc_hooks frontmatter
      stub the module author would add.
    - Compile-time gating — Phase 2 cc_hooks emitter now reads the snapshot
      and emits hook entries only when source_rule has graduated; non-graduated
      entries log a compile warning and stay inert.
    - Storage — hybrid append-only event log + JSON snapshot. Both files in
      {wiki_root}/; .linter-events.log is rotation-managed by the linter
      (30-day window); .linter-counter.json is the auditable graduation source.
```

---

## 5. cc_hooks emitter integration (small Phase 2 patch)

**Decision tag:** reckoning. Confidence: **high**.

The Phase 2 cc_hooks emitter (`kf-compile.py:emit_settings_fragment`) currently aggregates ALL `cc_hooks` entries unconditionally and writes `settings.kf.json`. With this spec, the emitter adds a graduation pre-check:

```python
# Pseudocode for the additions to emit_settings_fragment
def emit_settings_fragment(hooks_aggregate, output_root, ...):
    # NEW — load graduation snapshot
    snapshot = load_graduation_snapshot()  # reads .linter-counter.json from wiki_root
    
    filtered_hooks = {}
    for event, entries in hooks_aggregate.items():
        filtered = []
        for entry in entries:
            source_rule = entry.get("_kf_source_rule")
            if source_rule and not snapshot.is_graduated(source_rule):
                sys.stderr.write(
                    f"[kf-compile] cc_hooks: '{entry['command']}' references "
                    f"rule '{source_rule}' not yet graduated; skipping (this is normal "
                    f"for v1)\n"
                )
                continue
            filtered.append(entry)
        if filtered:
            filtered_hooks[event] = filtered
    
    # ... rest unchanged ...
```

**Effect:** module authors can write `cc_hooks` entries opportunistically (with `source_rule` reference). The emitter gates them. Once the linter snapshot graduates a rule, the corresponding hook activates on next compile — natural lifecycle, no manual flip.

---

## 6. Adversarial probes (Critic prep)

| Probe | Response |
|---|---|
| **"Event log can grow unbounded in long-running sessions."** | Rotation managed by linter after every snapshot — events >30 days drop. Bounded growth proportional to violation rate, not session count. |
| **"What's a 'session' for graduation purposes?"** | Each KF session has a session_id (per Module 19 routing decision log). The linter records session_id with each event; aggregation counts distinct session_ids. Same definition as elsewhere in KF. |
| **"linter_check block is module-author-declared. What stops a malicious or sloppy author from declaring a pattern that ALWAYS matches?"** | LOW Critic finding — same protection as existing accretion_calibration. Calibration cycle catches degenerate patterns. Author is also the audit reviewer of the snapshot (which is plain JSON in git). |
| **"Rotation deletes events older than 30 days but the snapshot caches eligibility forever — could a once-graduated rule stay graduated even after evidence ages out?"** | No. Snapshot is regenerated from scratch each linter run (overwriting, not appending). If 30-day window contains insufficient events, eligibility flips back to false. Auto-degrade is correct semantic. |
| **"What about concurrent linter runs?"** | Linter runs are periodic, not concurrent (Module 21:679 trigger is "Health check the knowledge base"; one at a time per knowledge base). Event log append is multi-writer safe (the only concurrent writers); snapshot writer is single. |
| **"What if .linter-counter.json gets hand-edited?"** | Same trust model as the rest of the wiki — git tracks changes; reviewer responsibility. Linter rebuilds from event log on next run, so hand-edits don't persist. |
| **"Does the cc_hooks emitter need to handle missing snapshot file gracefully?"** | Yes — Section 5 pseudocode missing. Adding: if snapshot file absent, treat all rules as not-yet-graduated (all hooks stay inert, log compile warning). Fresh wikis pre-linter-run get this default. |

---

## 7. What this spec does NOT change

- Does not change the Phase 2 cc_hooks emitter's output format; only adds a pre-check.
- Does not change M21's existing 5 linter checks (staleness, contradiction, redundancy, grounding-decay, orphan-references).
- Does not propagate to M22/M24.
- Does not introduce a real-time event hook (deferred — current linter-detection approach is cheap-enough).
- Does not specify per-mode session counting (sessions are KF-session-level, not per-mode).
- Does not change the 30-day window (per `5fd`; if calibration shows wrong, separate bead).

---

## 8. Post-approval implementation sequence — DO NOT EXECUTE during spec review

1. **Verify gate:** confirm M21's current version (likely 7.1.3 or 7.1.4 depending on 8gp landing first).
2. **Edit M21:** bump module 7.1.x → 7.2.0; append changelog entry; extend `linter_behavior.protocol` with steps 7 and 8; add "Graduation candidates" output section; document storage format for `.linter-events.log` and `.linter-counter.json`.
3. **Edit `compiler/kf-compile.py`:** add `load_graduation_snapshot()`, extend `emit_settings_fragment()` with graduation pre-check (Section 5 pseudocode).
4. **Edit `platform-bindings/claude-code.yaml`:** document the snapshot-file dependency under `special_outputs.cc_settings_fragment` (currently says "omit_if_empty: true" — add note that graduation pre-check may also omit individual entries).
5. **Edit `kf.yaml`:** bump system version (7.7.x → 7.8.0 or 7.9.0 depending on 8gp landing first); changelog entry.
6. **Verify compile** — `python3 compiler/kf-compile.py --target claude-code --output /tmp/kf-cc-dryrun --dry-run`.
7. **Open follow-up beads:**
   - **"Linter-counter calibration cycle"** — P3 — measure threshold effectiveness across N real linter runs; tune 3/2/30d defaults if signal warrants.
   - **"Real-time event hook (optional)"** — P4 — only if linter-detection misses too many real events; deferred today.

---

## 9. Confidence summary

| Component | Confidence | Why |
|---|---|---|
| Hybrid storage (event log + snapshot) | **High** | Stdlib only; multi-session-safe append; reviewable JSON |
| Graduation pre-check at compile time | **High** | Small, isolated patch to existing emitter |
| linter_check declarative block per rule | **Medium-high** | Author-declared patterns; relies on author judgment; calibration cycle catches abuse |
| 30-day window + 3/2 thresholds | **Medium** | Inherited from `5fd`; calibration cycle scheduled |
| Linter-detection (not real-time) | **High** | Lower overhead; sufficient for periodic graduation decisions |
| Forward-compatible emitter behavior | **High** | Modules without `cc_hooks` entries unaffected; modules with entries log warning + stay inert until graduation |

---

## HUMAN GATE — 8zt approval

- **Approve** → proceed to implementation pass (Section 8), file 2 follow-up beads
- **Approve with conditions** → state conditions; revise; re-gate
- **Reject** → state reason; revise or abandon

---

## Cross-references

- Bead `8zt`: this work
- Bead `5fd` (Phase 2 spec): `docs/planning/2026-06-10_cc-rules-and-hook-emitter-spec.md` Section 5 — threshold + inert-default policy
- Phase 2 impl (commit `0fb9fb4`): `kf-compile.py:emit_settings_fragment` — the function being extended
- Bead `8gp`: independent spec; may land before or after this bead. M21 patches don't conflict.
