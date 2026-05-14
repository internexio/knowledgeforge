---
title: Content-addressed cache with versioned hash prefix
source_mode: code-dive
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.99
staleness_risk: stable
importance: 5
pinned: false
created: 2026-05-13
domain: patterns
topic: validation
tags: quality-gate, tier-1, empirical, stable
related_entries: []
---

# Content-Addressed Cache with Versioned Hash Prefix

## The Pattern

Build a cache key by hashing all inputs that determine the output. Prepend a **format version string** as the first thing fed to the hash. Reuse the cache directory on hash match; rebuild on miss. When the cache format itself needs to change (layout, serialization, etc.), bump the prefix from `v1` to `v2` — all existing keys become uncomputable from new code, naturally invalidating the cache without an explicit migration.

## Code Reference

**Paperclip** (`packages/adapters/claude-local/src/server/prompt-cache.ts:88–110`)

```typescript
async function buildClaudePromptBundleKey(input: {
  skills: SkillEntry[];
  instructionsContents: string | null;
}): Promise<string> {
  const hash = createHash("sha256");
  hash.update("paperclip-claude-prompt-bundle:v1\n");  // <-- versioned prefix
  if (input.instructionsContents) {
    hash.update("instructions\n");
    hash.update(input.instructionsContents);
  } else {
    hash.update("instructions:none\n");
  }
  const sortedSkills = [...input.skills].sort(
    (a, b) => a.runtimeName.localeCompare(b.runtimeName)
  );
  for (const entry of sortedSkills) {
    hash.update(`skill:${entry.key}:${entry.runtimeName}\n`);
    await hashPathContents(entry.source, hash, entry.runtimeName, new Set());
  }
  return hash.digest("hex");
}
```

The magic is line 4: **`hash.update("paperclip-claude-prompt-bundle:v1\n")`**. If the cache format changes, bump to `v2`. Old cache directories become orphaned (no code computes their key). New code writes new directories. The migration is a one-line change.

## Why This Matters

Without a versioned prefix: changing the cache layout requires either:
1. A migration script that converts old cache dirs to new format (work + risk), OR
2. Delete the entire cache root on deploy (users lose cached artifacts)

With a versioned prefix: bump `v1` → `v2` in a single line. The old cache becomes unaccessible automatically — no migration, no deletion script, no manual intervention. Old dirs get garbage-collected by whatever cleanup loop you have. The tradeoff is explicitly manageable.

## Pattern Mechanics

### Content-Addressing
The hash is built from ALL inputs that determine output. If any input changes, the hash changes, and the cache key becomes uncomputable from that set of inputs.

### Sorting for Stability
Skills are sorted by `runtimeName` before hashing. Same set of skills in different config order → same hash. Order-independence is crucial.

```typescript
const sortedSkills = [...input.skills].sort(
  (a, b) => a.runtimeName.localeCompare(b.runtimeName)
);
```

### Versioning Provides Clean Invalidation
The prefix `paperclip-claude-prompt-bundle:v1` is hashed first. On format change, bump to `v2`:

```typescript
hash.update("paperclip-claude-prompt-bundle:v2\n");  // all old keys now uncomputable
```

All old cache dirs are orphaned. No code computes their keys. They don't conflict with new dirs. They can be deleted by a cleanup loop that runs periodically.

## Three Other Techniques From This Code

### 1. Symlink, Don't Copy, for Materialization
Each cache dir contains symlinks back to the canonical source files. Edits to upstream sources propagate. Disk usage is minimal.

**Trade-off:** Backup tools need `-L` (follow symlinks), and cache dirs become invalid if the source moves.

### 2. Canonicalize Paths and Names
Hash both the `entry.key` (the canonical name) and `entry.runtimeName` (the display name). If the mapping between them changes, the hash changes. Avoids name-resolution ambiguity.

### 3. Namespace Cache Per Tenant
Each cache root is scoped to a tenant: `companies/<id>/cache/<hash>/`. Same hash across tenants doesn't collide. Soft isolation built into the path.

## When to Use

- Any artifact that's expensive to (re)build from inputs: compiled prompts, processed knowledge bases, prepared workspaces, derived datasets, LLM prompt bundles
- Anywhere the "did the inputs change?" question is more expensive than "did the hash change?"
- Multi-tenant systems where different users have different cache hierarchies
- Cases where you anticipate format evolution (the versioning payoff grows over time)

## When NOT to Use

- Inputs that are hard to canonicalize (e.g., set-of-pointers where the pointed-to thing keeps changing). Hash will churn, invalidating the cache on every build.
- Cases where you need to pin a specific *version* of an input (e.g., a marketplace skill v1.2.3). Content-addressing pins to "the content you had at config time," not a semver. Fine for self-host, problematic for marketplaces where consumers need version locks.
- Caches with frequent, legitimate churn. If inputs change on nearly every build (e.g., timestamps embedded in payloads), the cache hit rate bottoms out and the caching logic becomes overhead.

## Trap: Implicit Cache GC Leak

**Paperclip does not explicitly delete old bundles.** After N heartbeats with N different input combinations, you have N cache directories accumulating. Over months, this becomes a disk leak.

**Add a "delete bundles unused for X days" loop.** Examples:

```python
# Python: delete cache dirs not accessed in 30 days
import os
import time
CACHE_ROOT = "companies/{id}/cache"
RETENTION_DAYS = 30
cutoff = time.time() - (RETENTION_DAYS * 86400)
for bundle_hash in os.listdir(CACHE_ROOT):
    bundle_path = os.path.join(CACHE_ROOT, bundle_hash)
    if os.path.getatime(bundle_path) < cutoff:
        shutil.rmtree(bundle_path)
```

```bash
# Bash: same idea, more concise
find /path/to/cache -type d -mtime +30 -exec rm -rf {} \;
```

## Related Patterns

- **Atomic-write-then-rename** — the `ensureReadableFile` pattern for the write operations inside the cache dir itself
- **Vendoring drift detection** — if cache contents are vendored to another repo, you'll need drift checks (Module 23 discipline)

## When This Applies

- Artifact caching systems with potential format evolution
- Build systems that trade regeneration cost for cache complexity
- Multi-tenant systems with isolated cache hierarchies
- LLM prompt bundle assembly where input changes should invalidate the cached prompt

## When This Does NOT Apply

- Simple key-value caches where the format never changes (versioning adds no value)
- Caches that are purely ephemeral (restarting the service clears them anyway)
- Cases where you can't afford the "old cache directories accumulate" problem — e.g., extremely constrained disk, or legal retention limits that force deletion of old data

## Grounding

**Verified in Paperclip (2026-05-13):**
- `buildClaudePromptBundleKey` is the canonical key-builder for Claude prompt bundles
- Used in `ensureReadableFile(bundleKey, bundleDir, async () => /* build bundle */)`
- Handles format versioning via the `v1` prefix on line 4 of the hash update
- Sorts skills by `runtimeName` for deterministic key generation
- Production code in use by the Claude Code native IDE

## Source Context

Extracted from **paperclip prompt-cache.ts code dive, 2026-05-13**. The `buildClaudePromptBundleKey` function demonstrates a rarely-seen but clever pattern for managing cache invalidation through format versioning. The versioned-prefix trick avoids explicit migrations and makes cache format evolution nearly costless. Generalizes to any expensive-to-build artifact cache (knowledge bases, compiled configs, prepared datasets, LLM bundles).
