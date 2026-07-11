---
title: Dual-layer false-positive suppression for lexical linters — ALLOWLIST + FOIL_MARKERS
source_mode: debugger
source_session: redacted
novelty_type: reusable_pattern
grounding_score: 0.95
staleness_risk: stable
importance: 4
pinned: false
created: 2026-07-07
domain: patterns
topic: scanner-suppression
tags: linting, regex, false-positives, content-moderation, pattern-matching, testing
related_entries:
  - patterns/2026-07-04_triage-tool-suppressed-store-labels-with-per-entry-bead-link.md
  - diagnostics/2026-06-20_linter-tracked-file-scope-misses-filesystem-state.md
  - patterns/2026-05-20_per-detector-error-isolation-audit-pipelines.md
  - patterns/2026-05-12_sanitization-three-pass-grep-discipline.md
---

# Dual-Layer False-Positive Suppression for Lexical Content Linters

## The Problem

Lexical linters (regex-based content scanners that flag banned words/phrases) suffer from false positives when banned terms appear in legitimate contexts: metadata fields, proper nouns, review attestations, backtick code spans, or meta-references that explicitly discuss the banned terms rather than using them. A single allowlist or a single exclusion pattern is insufficient — the same word can be legitimate in one sentence position and a drift violation in another.

Examples from real lint runs:
- Timestamp field `Generated: 2026-07-04` contains the banned term `2026` (if that were banned)
- Framework name `Platform-Specific Optimization` contains `Optimization` (if optimization as a directive is banned)
- Review footer `report body reviewed for banned verbs` explicitly names a banned verb to document what was checked
- Code span `` `generate_report()` `` contains a banned verb in a quoted identifier

A naive allowlist catches structural patterns but misses context-dependent cases. A naive FOIL list (negation patterns) catches context but requires hand-curated sentence fragments. The two layers together give precision with maintainability.

## The Two-Layer Solution

### Layer 1 — ALLOWLIST (span-based suppression)

Regex patterns that match SPANS of text where a banned term is inherently legitimate regardless of sentence context. A match position is suppressed if it falls within an allowlisted span.

**When to use:** The legitimate use has a structural/format signature — timestamp, backtick, specific phrase, or proper noun.

**Coverage:**
- Metadata fields with structured formats: `Generated: 2026-07-04`, `Created: YYYY-MM-DD`
- Proper nouns / framework names: `Platform-Specific Optimization`, `COS v2.0`
- Review attestation footers: `report body reviewed for banned verbs`
- Code spans: `` `generate_report()` ``, `` `optimize_bid` ``
- Architectural terms used as nouns: `constrained-generation`

**Implementation (Python):**

```python
ALLOWLIST_PATTERNS = [
    re.compile(r"\bGenerated:[^\n\d]*\d{4}-\d{2}-\d{2}", re.IGNORECASE),
    re.compile(r"Platform-Specific Optimization"),
    re.compile(r"report body reviewed for banned verbs\b[^\n]+"),
    re.compile(r"`[^`\n]+`"),
    re.compile(r"\bconstrained-generation\b"),
]

def _covered_by_allowlist(text: str, match_start: int, match_end: int) -> bool:
    """Check if a match position falls within an allowlisted span."""
    for pattern in ALLOWLIST_PATTERNS:
        for m in pattern.finditer(text):
            if m.start() <= match_start and match_end <= m.end():
                return True
    return False
```

### Layer 2 — FOIL_MARKERS (sentence-level context suppression)

Regex patterns that detect sentences where a banned term is used in a meta/negation context rather than as a directive. Applied at the sentence level containing the match.

**When to use:** The legitimate use is context-dependent — task description, negation, meta-reference, or explicit discussion of the term.

**Coverage:**
- Task descriptions that mention the banned verb as a label: `pivot rewrite task`, `rewrite pass`
- Marketing task references: `marketing rewrite`
- Negation contexts: `None of these describe`, `our own deprecated`
- Meta-references: `"rewrite" describing`, `Distinct from the banned`

**Implementation (Python):**

```python
FOIL_MARKERS = [
    re.compile(r"\bpivot\s+rewrite\b", re.IGNORECASE),
    re.compile(r"\brewrite\s+pass\b", re.IGNORECASE),
    re.compile(r"\bmarketing\s+rewrite\b", re.IGNORECASE),
    re.compile(r"\bour\s+own\s+deprecated\b", re.IGNORECASE),
    re.compile(r"\bNone\s+of\s+these\s+describe\b", re.IGNORECASE),
    re.compile(r'"rewrite"\s+describing\b', re.IGNORECASE),
    re.compile(r"\bDistinct from the banned\b", re.IGNORECASE),
]

def _has_foil_marker(sentence: str) -> bool:
    """Check if a sentence contains a foil marker (meta/negation context)."""
    return any(p.search(sentence) for p in FOIL_MARKERS)
```

### Integration into the Lint Pipeline

Apply both layers after the banned-term regex fires but before emitting a violation:

```python
def should_suppress(text: str, match_start: int, match_end: int, sentence: str) -> bool:
    """Suppress violation if either layer suppresses it."""
    if _covered_by_allowlist(text, match_start, match_end):
        return True  # Layer 1: structural pattern match
    if _has_foil_marker(sentence):
        return True  # Layer 2: sentence-level context
    return False  # No suppression; emit violation
```

## When to Use Which Layer

| Situation | Layer |
|-----------|-------|
| The legitimate use has a structural/format signature (timestamp, backtick, specific phrase) | ALLOWLIST (Layer 1) |
| The legitimate use is context-dependent (task description, negation, meta-reference) | FOIL_MARKERS (Layer 2) |
| The term is legitimate in ALL positions in a fixed phrase | ALLOWLIST |
| The term is legitimate only when the surrounding sentence signals meta-usage | FOIL_MARKERS |

## Testing Discipline

For each new ALLOWLIST or FOIL_MARKER entry, write:

1. **A positive test:** the false-positive class should now pass (no violation)
2. **A regression guard:** the core violation case still fires

**Example:**

```python
def test_platform_specific_optimization_not_flagged(self):
    # "optimize" inside "Platform-Specific Optimization" is a proper noun
    # — should pass (no violation)
    self.assertEqual(lint("Platform-Specific Optimization framework"), [])

def test_bare_optimize_still_flagged(self):
    # bare "optimize" as a directive should still fail
    violations = lint("COS will optimize your content")
    self.assertGreater(len(violations), 0)

def test_foil_marker_marketing_rewrite_not_flagged(self):
    # "rewrite" in task name "marketing rewrite" should pass
    self.assertEqual(
        lint("Track the marketing rewrite on the board."), []
    )

def test_bare_rewrite_directive_still_flagged(self):
    # bare "rewrite" as a directive should fail
    violations = lint("We will rewrite the guide.")
    self.assertGreater(len(violations), 0)
```

## When This Pattern Does NOT Apply

- **Structured data (JSON, YAML) rather than prose** — use field-level exclusion rules instead (e.g. `"skip_lint": true` in a JSON field)
- **Security-sensitive terms (injection strings, secrets)** — do not add allowlists; every occurrence should fire (the content moderation risk outweighs false-positive cost)
- **False-positive rate < 1%** — the overhead of maintaining two suppression layers may not be worth it vs. just accepting occasional false positives

## Anti-Patterns to Avoid

- **Adding to ALLOWLIST for context-dependent cases.** Foil markers are the right tool. An overly broad ALLOWLIST pattern can suppress real violations.
  - BAD: `re.compile(r"rewrite")` would suppress all "rewrite" violations
  - GOOD: `re.compile(r"marketing\s+rewrite")` suppresses only in context
  
- **Using FOIL_MARKERS for structural patterns.** Allowlist is more precise and more maintainable.
  - BAD: `re.compile(r"\bany task\s+rewrite\b")` (context-dependent, fragile across task descriptions)
  - GOOD: Allowlist pattern for backticks or quoted identifiers

- **Skipping regression guards.** A new allowlist entry can silently suppress a real violation in a different context.
  - BAD: Add ALLOWLIST entry, assume it works, move on
  - GOOD: Add ALLOWLIST entry + regression test for the core violation case

- **Not documenting the entry.** Six months later, a maintainer won't know why `` `optimize` `` is allowlisted and may remove it.
  - BAD: `re.compile(r"`[^`\n]+`")` (no explanation)
  - GOOD: Add a comment with context and a link to the issue/bead

## Grounding

Implemented in `cos-manager/scripts/lint_kp003.py` for the kp-003 drift linter (bead cos-manager-k3v, closed 2026-07-07).

**Before:** 5+ false positives on STATE_REPORT init audit packet blocking initial filing.
- `Generated: 2026-07-04` flagged as violation (timestamp contained a date number)
- `Platform-Specific Optimization` flagged as violation (proper noun contained `optimization`)
- Review footer `report body reviewed for banned verbs` flagged (was documenting the check, not using the verb)

**After:** 0 violations on the same packet, 37/37 tests pass (14 false-positive classes + 3 regression guards).

The ALLOWLIST/FOIL_MARKERS architecture was the minimal fix — alternative approaches (whitelist entire documents, disable the linter for certain files, hand-code per-file exceptions) would have either missed real drift or sacrificed precision. Two-layer suppression kept the scan precise while eliminating the noise.

## Source Context

cos-manager-kp003-lint-fix session, 2026-07-07. The kp-003 drift linter was preventing the first scheduled run of cos-manager by flagging false positives in the STATE_REPORT format itself. This pattern resolved the blocking issue and became a reusable template for content-moderation linters across the fleet.
