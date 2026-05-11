# Audit-Log Event Vocabularies — Read-Side Must Accept Routing-Suffixed Forms

```yaml
metadata:
  title: Audit-log event vocabularies — read-side must accept routing-suffixed forms
  source_mode: direct
  source_session: redacted
  created: "2026-05-11T00:00:00Z"
  date: "2026-05-11"
  confidence: 0.75
  grounding_score: 0.75
  grounding_source: |
    Discovered during [project] Dreaming Tier 1 — Phase I8 (cycle orchestration).
    Integration test `test_per_finding_duplicate_skipped` caught the mismatch at end-to-end stage.
    Write side was emitting `filed_per_finding` events; read-side dedup logic only recognized bare `filed`.
    Second cycle re-emitted the same finding because `is_active()` returned False.
    Root cause verified: contract mismatch between write-side event naming and read-side state derivation.
  novelty_type: new_pattern
  staleness_risk: slow_decay
  importance: 3
  pinned: false
  domain: patterns
  topic: validation
  tags: [grounding, quality-gate, adversarial]
  accreted_in: "6.5"
  related:
    - modules/21_Knowledge_Accretion.md
    - wiki/diagnostics/handoff-payload-schema-gap.md
```

---

## Pattern

When designing an append-only event log where multiple write sites distinguish themselves via suffixed event names (e.g., `filed_per_finding`, `filed_summary`, `filed_sev1` — each a variant of `filed` carrying routing/context information), **the read-side functions that compute derived state must treat the suffixed forms as equivalent to the bare form for state-machine purposes.** Otherwise the write side and the read side will silently drift apart: every write looks fine in the log, but state-derivation queries return wrong answers.

The contract violation manifests as:
- Unit tests pass (each event-emit verified independently in isolation)
- End-to-end tests fail (per-finding mode emits the same finding every cycle because dedup never trips)
- No error — silent divergence in derived state

### The Pattern

**Write side:** Emit specific event names (`filed_per_finding`, `filed_summary`) to preserve audit trail expressiveness — operator can see WHY the event was filed without spelunking into a separate field.

**Read side:** Pattern-match on prefixes (`filed*`, `closed*`, `dismissed*`) when deriving state, NOT exact matches.

### Wrong (Read-Side Too Narrow)

```python
def is_active(fingerprint):
    for ev in events_for(fingerprint):
        if ev["event"] == "filed":     # exact match — misses filed_per_finding
            return True
    return False
```

Test passes: `is_active(fp)` → True for a bare `"filed"` event
Integration test fails: `is_active(fp)` → False when the event is `"filed_per_finding"` because the exact match misses it.

### Right (Prefix-Aware)

```python
def is_active(fingerprint):
    for ev in events_for(fingerprint):
        if ev["event"].startswith("filed") or ev["event"] in ("refired", "material_change"):
            return True
        # ...handle closing events similarly with prefix awareness
    return False
```

Both unit and end-to-end tests now pass because the read side accepts any `filed*` variant.

---

## Detection Symptoms

The bug presents as:
- "Dedup never trips" — state derivation queries always return the "not active" answer
- "State never closes" — closing predicates fail the same way
- Unit tests at individual event level pass; end-to-end tests fail
- No error or exception; the logic is "correct" in isolation but contracts are broken
- Second cycle of the same task re-emits the same finding/alert/issue because the dedup check `is_active()` returns False

---

## Mitigation: Choose ONE Policy Up Front

### Option 1: Bare-Only Events

Write site emits only `filed`/`closed`/`dismissed`. Routing/context goes in a separate `mode` field. Read side stays simple (`if ev["event"] == "filed"`), but loses audit-log expressiveness — operators cannot see routing rationale from the event name alone.

**Trade-off:** Simpler read-side code, less audit trail clarity.

### Option 2: Prefix-Tolerant Reads (Recommended)

Write side emits any `filed_*` variant. Read side normalizes via prefix match. Audit log stays expressive (the suffix encodes useful context), but every read-side function must use prefix logic — easy to miss in new code.

**Trade-off:** Richer audit trail, but requires code-review discipline to enforce prefix matching everywhere state is derived.

**Recommended when:** The audit log is operator-facing (the suffix encodes useful context for debugging/troubleshooting).

**Make it enforceable:** Add a code-review checklist item:
- "All state-derivation functions (`is_active()`, `is_open()`, dedup checks) use `.startswith()` or regex prefix match, not exact string equality."
- Consider a validation helper:
  ```python
  def event_matches_base(event_name: str, base: str) -> bool:
      """Check if event_name is base or a base_* variant."""
      return event_name == base or event_name.startswith(f"{base}_")
  ```

---

## When This Applies

- Event-sourced systems where event names carry context beyond the state transition
- Audit logs that downstream queries derive state from (dedup checks, "is this still open?", "when was X last touched?")
- Systems where the spec uses suffixed event names for documentation clarity but the implementation must derive state
- Any place where you find yourself writing `if event == "foo":` over a stream that another component writes `foo_variant_a`/`foo_variant_b` into
- Integration tests reveal state divergence but unit tests pass

## When This Does NOT Apply

- Closed audit logs where nothing reads them computationally (humans only)
- Strict state machines where each transition has exactly one event name by design, enforced at the schema level
- Systems with a separate state table maintained alongside the event log (derivation from events is unneeded)
- Event vocabularies that use structured enum types, not free-form string names (the type system catches mismatches at compile time)

---

## Source Context

Discovered during **[project] Dreaming Tier 1 — Phase I8** (cycle orchestration). The findings system spec used:
```python
findings.append_to_log(f, event="filed_per_finding")
```
to record routing decisions, but the dedup check only recognized bare `"filed"` events:
```python
def is_active(fingerprint):
    for ev in findings.events_for(fingerprint):
        if ev["event"] == "filed":  # exact match
            return True
    return False
```

**End-to-end test** `test_per_finding_duplicate_skipped` failed: the second cycle re-emitted the same finding because dedup never tripped. Neither write nor read function had a bug in isolation; the bug was in the **contract between them** — write side and read side expected different event names.

The fix widened `is_active()` to use prefix matching:
```python
if ev["event"].startswith("filed"):
    return True
```

Caught at integration-test stage, not unit-test stage — a characteristic of contract violations.

