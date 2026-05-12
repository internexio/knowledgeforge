---
title: Dogfood the safety machinery — end-to-end apply-path tests via the system's own atomic install + undo
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-12
domain: patterns
topic: validation
tags: quality-gate, adversarial, empirical
related_entries: [infrastructure/2026-05-12_self-watchdog-autonomous-fix-cycles.md, infrastructure/2026-05-12_empty-stdin-crontab-wipe-footgun.md]
---

# Dogfood the Safety Machinery — End-to-End Apply-Path Tests via the System's Own Atomic Install + Undo

## The Pattern

When validating an autonomous remediation system (anything that detects
a problem, applies a fix, and supports rollback), you have three layers
of confidence to choose from:

1. **Unit tests** — detector emits a Finding object with the right
   shape. Cheap, fast, but tells you nothing about whether the apply
   path actually mutates real substrate.
2. **Integration tests with mocks** — apply path runs through stubbed
   `_install_crontab` / `_write_log` / `_exec_action`. Catches more
   bugs, but the mocks paper over real-world edge cases (permission
   errors, line-ending quirks, atomic-rename semantics).
3. **End-to-end against live substrate** — plant a synthetic input
   directly into the live substrate (crontab, file system, database),
   run the real apply, verify the real mutation, run the real undo,
   verify the real reverse, then restore baseline.

Layer 3 is gold-standard but feels too risky to do safely. The trick
is that a well-designed remediation system *already provides the
safety primitives you need* to do it: atomic-install with backup,
idempotent undo, byte-stable restore. Use those primitives to write
the test.

## The Recipe

```
1. Take a baseline snapshot of the live substrate (e.g. crontab text)
   via the system's own snapshot helper (not raw shell).
2. Build a synthetic input that exercises ONE specific code path
   (one new finding type, one new operation type, etc.).
3. Install the synthetic input via the system's own guarded install
   helper — the one the production code uses. This proves the install
   path itself is in good shape AND uses the same atomicity contract
   as production.
4. Run the real cycle (NOT dry-run). Assert:
   - heartbeat status == "ok"
   - applied_count == expected
   - the synthetic finding is in findings.jsonl
   - the substrate mutation actually happened (verify in the LIVE
     substrate, not in a memoized snapshot)
   - the undo log has the corresponding reverse_op record
5. Run the system's own undo command for the cycle.
   Assert the mutation is reversed (substrate matches step-3
   post-install state).
6. Restore the baseline via the same guarded install helper from step 1.
   Assert byte-equality with the original snapshot — `diff baseline live`
   should print nothing.
7. Clean up any auxiliary artifacts (test scripts, temp files).
```

The key invariant: every "destructive" step is paired with a verified
reversal. If any assertion fails, you stop and investigate before
running step 6 — the test scaffold is self-revealing about which
layer failed.

## Concrete Example ([project] Dreaming)

During Round-2 validation of the dreaming system's new A1 + A3
crontab-disable behavior, end-to-end testing of the full Detect → Apply
→ Undo → Restore loop was needed against the live crontab on the laptop
without permanently mutating anything.

```python
from dream import cycle

# Step 1 — baseline snapshot via the system's own helper
original = cycle._crontab_snapshot()  # 27 lines

# Step 2 — synthetic input: 2 entries, one A1, one A3
test_lines = [
    "*/30 * * * * ~/.../test-orphan-with-archive.sh ... # DREAM-TEST",
    "*/30 * * * * ~/.../archive/test-points-at-archive.sh ... # DREAM-TEST",
]
new = original.rstrip("\n") + "\n" + "\n".join(test_lines) + "\n"

# Step 3 — guarded install (uses the empty-stdin wipe guard)
cycle._install_crontab(new, prior_text=original)

# Step 4 — real cycle
import subprocess
subprocess.run(["python3", "-m", "dream.cli", "cycle"], check=True)
# verify: last-run.json shows applied_count=2, status=ok
# verify: crontab now has both DREAM-TEST lines prefixed `# DREAMING-DISABLED:`
# verify: undo.jsonl has 2 new records with operation=crontab_disable

# Step 5 — system's own undo
subprocess.run(["python3", "-m", "dream.cli", "undo-cycle", cycle_id], check=True)
# verify: crontab has DREAM-TEST lines back to active (no DREAMING-DISABLED: prefix)

# Step 6 — restore baseline via guard
current = cycle._crontab_snapshot()
cycle._install_crontab(original, prior_text=current)
# verify: diff baseline live → IDENTICAL

# Step 7 — clean up test scripts
```

Total test time: ~30 seconds. All four layers exercised: detector,
apply, undo, restore. No external test framework or mocks.

## When This Applies

- Any autonomous remediation system that has both an atomic-install
  contract AND an undo contract (the two together are what make this
  safe — undo without atomic-install means you might restore to a
  half-mutated state; atomic-install without undo means the test
  becomes one-way)
- Substrate-hygiene systems (cron, filesystem, package manifests,
  configuration files, schema migrations)
- Systems where unit tests have proven *insufficient* in production —
  the gap between "the detector emits the right Finding shape" and
  "the cycle actually fixed the thing" has bitten you before

## When This Does NOT Apply

- Systems with no undo contract (can't safely test in production-like
  conditions — must use staging or VMs)
- Systems where the substrate mutation has side effects outside the
  system's own state (notifications fired, external API calls made,
  alerts paged — undo can't unsend an alert)
- Systems with global locks that would block other cycles for the
  test duration (must coordinate)
- One-shot pipelines (CI builds, deploys) — these are already tested
  end-to-end by the platform they run on

## Anti-Patterns

- **Mocking the install helper in the test**: defeats the purpose;
  you're back to layer-2 confidence
- **Testing against a snapshot of substrate, not live**: a snapshot
  taken at test start doesn't reflect concurrent mutations from other
  cron jobs / agents
- **Skipping the restore-byte-equality check**: silent baseline drift
  is exactly the failure mode you're trying to detect
- **Running the test concurrently with the system's own scheduled
  cycle**: lock contention may make the test flaky, OR the scheduled
  cycle may run mid-test and apply additional auto-fixes you'll
  attribute to the test cycle by mistake

## Source Context

Discovered during [project] Dreaming Tier 1 Round-2 validation,
2026-05-12. After deploying new A1 + A3 cron-orphan-disable behavior,
the user requested rapid end-to-end validation without waiting 22 hours
for the next scheduled 06:00 cycle. The recipe above exercised all layers:

- A1 detector (cron-orphan-archive-available → action=crontab_disable)
- A3 detector (cron-references-archive → action=crontab_disable)
- B detector (uptime.log oversized → action=log_rotate, via new SCAN_TARGETS)
- The new empty-stdin install guard (filed separately at
  `wiki/infrastructure/2026-05-12_empty-stdin-crontab-wipe-footgun.md`)
- The undo path via `dream.cli undo-cycle <cycle_id>`
- The atomic-install path via `cycle._install_crontab(new, prior_text=)`

All assertions passed. Crontab was byte-identical to the baseline after
restore. The test gave full-stack confidence in the Round-2 changes in
approximately 30 seconds, with no waiting and no risk of silent baseline
drift. Recipe proved repeatable enough for use in all future substrate-mutating
policy changes in this system.
