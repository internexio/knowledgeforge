---
title: PHP 8 array_combine throws ValueError — @ suppression does NOT catch it
source_mode: critic
novelty_type: reusable_diagnostic
grounding_score: 1.0
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-26
tags: empirical, quality-gate, migrations, php, breaking-change, exception-handling
related_entries: []
---

# PHP 8 `array_combine` throws ValueError — `@` suppression doesn't catch it

## The breaking change

PHP 8.0 changed `array_combine`'s mismatched-array behavior:

- **PHP 7.x**: returns `false` + raises an E_WARNING
- **PHP 8.x**: throws `ValueError`

This breaks a common PHP 7 defensive idiom:

```php
$record = @array_combine($header, $data);
if ($record === false) {
    // handle mismatch
}
```

In PHP 8, the `@` operator suppresses WARNINGS and NOTICES but **does not catch exceptions**. The `===false` check is dead code — `array_combine` never returns `false` in PHP 8, it throws. The exception propagates uncaught unless a `try/catch` wraps the call.

## When this hits

Any of these patterns in a PHP 7 → PHP 8 migration:

```php
// Pattern A: defensive @ with === false
$result = @array_combine($a, $b);
if ($result === false) { ... }

// Pattern B: no try/catch around per-row CSV/data parsing
while ($row = fgetcsv($handle)) {
    $record = array_combine($header, $row);  // No try/catch
    process($record);
}

// Pattern C: assumed-safe per-row processing in a transaction
DB::beginTransaction();
foreach ($rows as $row) {
    SeoSnapshot::create(array_combine(...));
}
DB::commit();
```

Patterns A and B silently break for malformed rows. Pattern C fails catastrophically — one bad row aborts the whole batch transaction.

## When this DOES apply

- PHP 7 → 8 migrations
- Code that processes externally-sourced data (CSV imports, API payloads, user uploads) where row shape isn't guaranteed
- Long-running batch jobs where defensive per-row error isolation is intended
- Anywhere the original code used `@array_combine` or checked `=== false` after calling `array_combine`

## When this DOES NOT apply

- New PHP 8+ code written from scratch (you'd never use the `@` idiom)
- Code where both arrays are guaranteed-same-length by construction (typed objects, controlled inputs)
- Anywhere `array_combine` is called once on a known-shape pair

## Diagnostic signature

If a Laravel artisan command using `array_combine` on CSV rows crashes mid-batch with:

```
ValueError 

  array_combine(): Argument #1 ($keys) and argument #2 ($values) must have the same number of elements
```

…it's this trap. The `@` operator above the call is a red herring — it's not protecting you.

## The fix

Three options, in order of preference:

### Option 1: Pre-check count, drop @ entirely (cleanest)

```php
try {
    if (count($data) !== count($header)) {
        // log + skip + continue
    }
    $record = array_combine($header, $data);  // safe now
} catch (\Throwable $e) {
    // catches anything else
}
```

### Option 2: Wrap in try/catch (preserves @ for unrelated warnings)

```php
try {
    $record = @array_combine($header, $data);
} catch (\ValueError $e) {
    // handle mismatch
}
```

### Option 3: Use array_map for explicit zipping (avoids the function entirely)

```php
$record = [];
foreach ($header as $i => $key) {
    $record[$key] = $data[$i] ?? null;  // safe even if data is shorter
}
```

Option 3 is also safer because it handles short rows by inserting nulls rather than erroring.

## Concrete grounding

Found during a critic review of a Laravel 11.36.1 artisan CSV import command (`ImportSeoSnapshots`). The original code had:

```php
$record = @array_combine($header, $data);
if ($record === false || empty($record['domain'])) {
    $skipped++;
    continue;
}
```

The `===false` check was dead code under PHP 8.2.28. A single malformed CSV row would have thrown `ValueError`, propagated past the surrounding try/catch (which was nested inside the if-block), and aborted the entire batch via `DB::beginTransaction()` rollback. Fix applied: moved into try/catch, added explicit `count($data) !== count($header)` pre-check.

Caught during a 3-pass critic review chain (sem-tools-9nj code review, finding #1 in pass 2). Not caught in the original implementation despite testing on well-formed CSVs because the malformed-row path was never exercised.

## Related PHP 8 breaking changes

PHP 8 also tightened these (worth checking in the same migration):

- `array_keys($arr, null)` — match mode changed
- Implicit float-to-int conversion now emits deprecation warning
- String-to-number comparison now uses different rules

But `array_combine` is the one most commonly hit by the `@`+`===false` defensive idiom.

## Source context

PHP 7 → 8 migration validation; empirical finding from production code review of CSV import batch job.
