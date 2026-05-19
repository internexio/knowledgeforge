---
title: PostgREST or_() filter-injection — sanitize free-text before interpolation
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-13
tags: security, postgrest, supabase, sql-injection-analog, input-sanitization, defense-in-depth
related_entries: []
---

# PostgREST or_() filter-injection — sanitize free-text before interpolation

## The vulnerability class

PostgREST treats `,`, `.`, `(`, `)`, `%`, `:`, `*` as filter syntax inside
`.or_()` and `.and_()` predicates. F-stringing user-controlled values into
those predicates lets an attacker break out of the intended filter context
and append additional predicates that broaden — or completely bypass — the
caller's other filters.

Classic exploit shape (free-text search param interpolated into an `or_()`):

```python
# Vulnerable
query = (
    client.table("analysis_results")
    .select("...")
    .eq("user_id", current_user.id)        # intended owner scope
    .or_(f"title.ilike.%{search}%,input_snippet.ilike.%{search}%")
)
```

Crafted `search = "x%,user_id.eq.<target>"` lets the attacker widen
the `or` to include other users' rows. The `.eq("user_id", ...)` filter
is AND'd at the top level, but a sufficiently exotic injection can either
balance parens to break out of the `or` context or smuggle additional
predicates through that get OR'd with the original intent.

This is the SQL-injection analog for PostgREST clients — the syntax tokens
that an attacker can use to extend a query are different from raw SQL but
the consequence (filter widening / scope bypass) is the same.

## The fix: strip-then-interpolate

A single regex-strip + length cap, applied at the chokepoint where the
free-text value would otherwise hit the filter expression:

```python
# app/services/repositories/_filters.py
_SAFE_ILIKE_RE = re.compile(r"[^A-Za-z0-9 _-]")

def safe_ilike_term(raw: str | None, max_len: int = 100) -> str:
    if not raw:
        return ""
    return _SAFE_ILIKE_RE.sub("", raw).strip()[:max_len]
```

Apply at the call site, and skip the predicate entirely if the sanitized
term is empty (don't pass `""` through — `ilike.%%` matches every row):

```python
if search:
    safe = safe_ilike_term(search)
    if safe:
        query = query.or_(
            f"title.ilike.%{safe}%,input_snippet.ilike.%{safe}%"
        )
```

## When This Applies

- Any direct interpolation of user-supplied strings into PostgREST filter
  expressions (`.or_(...)`, `.and_(...)`, `.filter(column, "...")` raw forms).
- Most common with search / query-string params that flow through to an
  `ilike` predicate; less common with structured filters that use the
  typed `.eq("col", value)` API (which the client serializes safely).

## When This Does NOT Apply

- Filter chains that only use the typed builders (`.eq`, `.ilike` with
  separate args, `.in_`, etc.) — those serialize values through the
  client, not via string interpolation.
- Values that are UUIDs or other strict-format types validated upstream
  (no PostgREST metacharacters survive the format check).

## Threat-model framing

This is a `Standard / Required` security control on any user-search
endpoint, not defense-in-depth. The exploit needs no XSS prerequisite —
an authed attacker hitting their own search endpoint can extract other
users' data.

## Concrete grounding

COS production bug: `app/services/repositories/analysis_result.py:list_analysis_results`
took a `search` query param from `chat.py:list_analysis_history` and
f-stringed it raw into `.or_(f"title.ilike.%{search}%,input_snippet.ilike.%{search}%")`.
Fixed by introducing `app/services/repositories/_filters.py::safe_ilike_term` and
applying it at the single interpolation point. Tested with the audit's
specific payload `x%,user_id.eq.attacker-target` — sanitized to
`xuser_ideqattacker-target`, harmless substring noise. Commit `2aa8128`,
audit ref CODE_REVIEW_2026-05-12.md MEDIUM-1. 17 unit tests cover the
sanitizer + the behavioral guarantee that `or_()` never sees raw
metacharacters.

## Scope discipline

Other `or_()` interpolation sites in the same codebase (`user_profile.py`,
`conversation.py`) take UUIDs and cookie-validated session_ids from auth
deps, not from free-text request bodies. Audit didn't flag those; the
fix scope held to the actual user-controlled vector. If a future code
review surfaces interpolated UUIDs that aren't format-validated,
sanitize them too — but the helper is for free-text, not for typed IDs.

## Source Context

COS production audit 2026-05-12 (MEDIUM-1 finding). The vulnerability was
discovered during security review of the search-by-analysis-result endpoint,
which interpolated user-supplied search terms directly into PostgREST filter
predicates. The fix (safe_ilike_term helper + input validation at call sites)
is reusable across any PostgREST codebase that accepts free-text search params.
