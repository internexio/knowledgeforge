---
title: AES Export MANIFEST Registration — Silent Failure When Detector Extras Are Unpopulated
source_mode: builder
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-10
domain: diagnostics
topic: error-handling
tags: grounding, quality-gate, api, classification
related_entries: []
---

# AES Export MANIFEST Registration — Silent Failure When Detector Extras Are Unpopulated

## The Problem

In pipelines with a MANIFEST dict that maps detector names to generator functions, a misalignment between detector and generator can pass all tests and produce valid-looking outputs while delivering zero actual results. The failure mode is silent: the generator returns `[]`, the HTTP endpoint returns 200, and the operator downloads an empty file.

### Concrete Example (client-project)

The AES export pipeline registers detectors to generator functions via a MANIFEST:

```python
MANIFEST = {
    "geo_overreach": make_geo_bid_modifier_changes,
    # ... other registrations
}
```

Each generator reads detector-populated `Finding.extras` to construct `Change` objects:

```python
def make_geo_bid_modifier_changes(finding: Finding) -> list[Change]:
    campaign_name = _get_extra(finding, "campaign_name")
    location_path = _get_extra(finding, "location_path")
    modifier_fraction = _get_extra(finding, "modifier_fraction")
    
    if not (campaign_name and location_path and modifier_fraction):
        return []  # Defensive guard: silently passes if keys are missing
    
    # ... build Change objects
```

The `GeoOverreachDetector` emitted `Finding` objects but never populated any extras:

```python
class GeoOverreachDetector:
    def detect(self, account: Account) -> list[Finding]:
        # ... detection logic
        for geo in problem_geos:
            findings.append(Finding(
                detector="geo_overreach",
                extras={}  # EMPTY — nothing populated
            ))
        return findings
```

**Result:** Every call to `build_change_file(account_id, kind="geo_overreach")` succeeds (HTTP 200, valid zip), but contains zero change elements. The operator imports it into Editor and nothing happens.

## Why It's Subtle

- **The guard clause `if not (...): return []` is defensively correct** but masks the upstream bug instead of surfacing it
- **Generator-in-isolation tests pass** because they mock extras as populated
- **The HTTP endpoint returns 200 with valid bytes** — all downstream code succeeds
- **Only end-to-end tests would surface it** — and only if they verify that the file contains data, not just that it's structurally valid

## Diagnostic Pattern

When a registered generator consistently produces empty results:

1. **Check whether the corresponding detector populates `finding.extras` at all** — grep the detector code for `extras=` assignments
2. **Verify that extras keys the generator reads match keys the detector writes** — look for mismatches in key names or conditional logic
3. **Cross-reference both directions:**
   - Generator: `_get_extra(finding, "key")` — what does it read?
   - Detector: `extras["key"] = value` — what does it write?

If the sets don't overlap or if `extras={}` is the default, you've found the mismatch.

## Fix Pattern (Two Parts)

1. **Update the detector to populate required extras on each emitted Finding**
   - Make extras a first-class part of the Finding construction, not an afterthought
   - Include all keys the generator will read

2. **Add detector-level tests asserting that required extras keys are present**
   - Test the actual detector, not a mock
   - Assert `finding.extras["key"]` is set to a non-empty value
   - This creates a live contract between detector and generator

## Prevention

For each new MANIFEST registration, write a **detector-integration test** that:
- Runs the actual detector on real or fixture data
- Asserts that emitted Findings have all required extras keys populated
- Verifies the generator can process the output without hitting guard clauses

This prevents two separately-tested units from silently diverging.

### Example Test Structure

```python
def test_geo_overreach_detector_populates_required_extras():
    """Verify GeoOverreachDetector sets all keys required by generator."""
    detector = GeoOverreachDetector()
    findings = detector.detect(fixture_account)
    
    for finding in findings:
        assert finding.extras.get("location_path"), "Missing location_path"
        assert finding.extras.get("geo_type"), "Missing geo_type"
    
    # Then verify the generator can process them:
    changes = make_geo_bid_modifier_changes(findings[0])
    assert len(changes) > 0, "Generator returned empty despite valid extras"
```

## When This Applies

- Multi-stage pipelines where one stage (detector) populates data consumed by another (generator)
- Schemas where guard clauses return empty on missing data, masking contract violations
- Registries mapping producers to consumers (MANIFEST dicts, service locators, etc.)
- Test coverage that validates stages in isolation but not their integration

## When This Does NOT Apply

- Single-stage pipelines where producer and consumer are tightly coupled
- Systems where missing data raises an exception rather than returning empty
- Scenarios where empty results are a valid output (not a signal of misconfiguration)

## Source Context

Found 2026-07-10 in client-project (sa-ltx, geo-negative exporter). The `geo_overreach` → `bid_modifier` registration had existed since bid_modifier.py's creation but the detector never set extras. The registration was removed and replaced with `geo_negative.py` generator, which correctly receives `location_path` and `geo_type` from an updated `GeoOverreachDetector`. Three new detector-level assertions added to `test_geo_overreach.py`; three more to `test_zip_overreach.py`. Full test suite: 507/507 green.

Incident closed via fix bead sa-ltx #2.
