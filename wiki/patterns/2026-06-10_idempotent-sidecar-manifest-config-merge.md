---
title: Idempotent merge of tool-managed fragments into hand-editable config via sidecar manifest
source_mode: builder + adversarial-critic
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-10
domain: patterns
topic: validation
tags: quality-gate, deployment, filesystem, accretion
related_entries:
  - patterns/2026-05-31_marker-based-auto-regen-markdown-pattern.md
  - patterns/2026-05-15_sidecar-mirror-upstream-missing-relations.md
  - infrastructure/2026-05-12_dogfood-apply-undo-end-to-end-testing.md
  - migrations/2026-05-20_idempotent-additive-column-sqlite-migrations.md
---

# Idempotent Merge of Tool-Managed Fragments into Hand-Editable Config Files via Sidecar Manifest

## Problem Shape

A tool (compiler, code generator, install script) needs to contribute a set of entries into a file that a user ALSO hand-edits. The naive approaches fail:

- **Append-on-every-run:** Duplicates on N-th invocation. Safe but pollutes.
- **Delete-and-re-add:** Destroys user-authored entries. Dangerous.
- **Marker-block strip-by-comment:** Requires comment syntax; fails on JSON/YAML. User can accidentally edit inside marker and lose their work.

None survive N-time idempotent invocation while preserving user edits.

## The Pattern: Sidecar Manifest

**Core insight:** Track tool-written entries by stable signature (e.g., JSON canonical form), recorded in a sidecar manifest file. On each install, use prior manifest to strip old entries, then add new ones. The sidecar always reflects the LAST install's contribution, not the current one.

### Three-part mechanism

1. **Tool emits to separate compiled file.** The TOOL writes its contribution to `.<tool>-compiled.json` (or `.kf-config.json`, `.ts-settings.json`, etc.). This file is fully tool-owned; the user never edits it.

2. **Compute stable signatures.** For each entry in the compiled file, compute a deterministic signature:
   ```python
   signature = hashlib.sha256(
     json.dumps(entry, sort_keys=True, separators=(",", ":"))
   ).hexdigest()
   ```
   Exclude any `_tool_*` sentinel fields from the signature so they don't affect matching.

3. **Strip-then-add idempotent merge:**
   ```
   STRIP PASS:
     Load prior manifest (sidecar JSON at `.<tool>-install-manifest.json`)
     For each signature in prior_manifest:
       Remove the corresponding entry from user's file
   
   ADD PASS:
     For each entry in compiled file:
       Compute its signature
       Add entry to user's file
       Record signature in updated manifest
   
   SAVE: Write updated manifest to sidecar file
   ```

### Idempotency properties

- **Re-running with unchanged compiled file → zero net change.** Strip removes the N entries from prior install; add re-adds the same N entries with identical signatures. File state is byte-identical.
- **Compiled file shrinks → orphans removed.** Prior install recorded 5 signatures; current has 3. Strip removes all 5; add re-adds the new 3. Result: cleaner file.
- **Compiled file grows → old entries cleaned up first.** Prior: 3 entries. Current: 7 entries. Strip removes the old 3; add inserts the new 7. Result: no duplication.
- **User hand-edits survive.** The strip pass targets signatures in the prior manifest. User-authored entries don't have signatures in the prior manifest (they were hand-written), so they're not removed. A user who accidentally uses the tool's reserved prefix in their own entry is safe because their entry's signature won't match anything in the prior manifest.

## Concrete Example (KnowledgeForge CC Phase 2)

**Setup:** The `kf-compile.py` compiler outputs CC-specific settings to `.claude/settings.kf.json`. The install script must merge these into the user's `.claude/settings.json` (which the user hand-edits for personal preferences).

**First install:**
```
Compiled: {
  "rules": ["kf-meta.md", "kf-rules.md"],
  "linters": [{"name": "kf-linter", ...}]
}
Manifest before: (empty)
Action: Add all entries, record signatures in manifest
Result: settings.json now has both user's hand-edits and the 2 tool entries
Manifest after: {
  "2e4f...": {"name": "kf-meta.md"},
  "1a3b...": {"name": "kf-linter", ...}
}
```

**Second install (same compiled content):**
```
Compiled: (unchanged)
Manifest before: {
  "2e4f...": ...,
  "1a3b...": ...
}
Action: Strip pass removes entries matching prior signatures
         Add pass re-adds the same entries
Result: settings.json unchanged (byte-identical)
Manifest after: (identical to before)
```

**Third install (compiled file shrinks — linter removed):**
```
Compiled: {
  "rules": ["kf-meta.md"]
}
Manifest before: {
  "2e4f...": {"name": "kf-meta.md"},
  "1a3b...": {"name": "kf-linter", ...}
}
Action: Strip removes both entries matching prior signatures
         Add re-adds only the single rules entry
Result: linter entry removed; rules entry re-added; user hand-edits untouched
Manifest after: {
  "2e4f...": {"name": "kf-meta.md"}
}
```

## Where This Applies

- **VS Code settings.json:** User-editable, extensions need to add keybindings, snippets. Sidecar manifest prevents duplicate keybinding on every settings update.
- **Shell rc files (.zshrc, .bashrc):** Install scripts adding PATH entries, aliases, functions. Sidecar tracks tool-added blocks (unlike marker comments, works with no `#` syntax).
- **GitHub Actions workflows:** Multiple tools want to add steps to a shared CI/CD flow. Sidecar manifest prevents duplicate steps.
- **Kubernetes manifests:** Multiple operators add ConfigMaps / Deployments. Sidecar tracks applied resources.
- **Package.json, pyproject.toml, Dockerfile:** Tool-managed dependencies, scripts, or build directives coexist with hand-authored entries.
- **Ansible inventories, Terraform state, Helm values:** Tool adds managed resources alongside hand-curated infrastructure.

## Counter-Pattern: Marker-Block Fragment Merge

An alternative is to wrap tool-written entries in marker comments (`# BEGIN <tool>` / `# END <tool>`) and strip-by-marker on each install. This is simpler when:

- The host file format supports comments (Markdown, YAML, shell, Terraform all do).
- Users are unlikely to edit inside the marker block by accident.
- You're OK with marker-block boundaries being strict spans (all tool content for a tool lives in one contiguous block; fragments can't be scattered).

**Trade-offs:**
- **Pros:** No sidecar file to manage; marker comments are self-documenting; easy to audit visually.
- **Cons:** Fails on JSON/YAML (no standard comment syntax for all contexts); user accidents inside marker blocks cause data loss; marker format must be standardized across all tools contributing to the file.

**Sidecar manifest is more robust** for:
- Non-comment-friendly formats (JSON, strict YAML)
- Environments where users might accidentally edit inside marker blocks
- Multi-tool contributions that can't coordinate on a unified marker syntax

## What This Does NOT Cover

### Multi-writer races
If two tools both manage entries in the same file with separate manifests, they must:
- Use distinct top-level keys (VS Code separates `keybindings` from `extensions`)
- Coordinate manifest writes (use `fcntl.flock()` for file-level locks)
- Or accept eventual consistency (sidecar updates are asynchronous)

### Atomic write
The strip-then-add sequence is two operations (load, modify, save). A crash between strip and add leaves the file in an intermediate state. Atomicity requires:
- Write to temp file
- Atomic `os.rename(temp, target)` to replace
- Read-check-write-replace pattern (atomic on most filesystems)

### Schema validation
This pattern assumes the entries being merged are independently valid (each entry's shape is correct). It does NOT validate the merged file's overall schema. Run a post-merge validator if the file's integrity is critical.

## Source Context

Designed in Phase 2 spec for the KnowledgeForge CC target's `settings.kf.json` → `settings.json` merge step. The adversarial-critic review (bead `knowledgeforge-core-5fd`, finding [1], CRITICAL severity) caught a non-idempotent pseudocode that would have appended duplicates on every install. The sidecar-manifest pattern was the resolution, surfacing as a generalizable framework applicable to any "tool-managed + hand-edited" config surface.

## Implementation Checklist

- [ ] Tool writes compiled entries to a separate file (not directly to user's file)
- [ ] Entries have a deterministic, content-addressed signature (JSON canonical form + hash)
- [ ] Sidecar manifest file exists and is version-controlled (or ignored if rebuild is fast)
- [ ] Strip pass loads prior manifest and removes old entries by signature
- [ ] Add pass inserts new entries and records signatures
- [ ] Sidecar manifest is always rewritten (not appended to) — it reflects LAST install
- [ ] User hand-edits are verified to survive at least one strip-add cycle
- [ ] Install script is idempotent (run 2× with no compiled changes → file unchanged)
- [ ] Documentation notes the sidecar file's purpose and lifecycle

## When This Becomes an Anti-Pattern

If you find yourself:
- Using separate "tool config" and "user config" files that never merge → just keep them separate; sidecar is overhead.
- Frequently shrinking or growing the tool's contribution set → frequent manifest rewrites; consider a database instead.
- Struggling to compute stable signatures because tool entries are non-deterministic → sidecar isn't your problem; first make entries deterministic.
- Running merge logic on every process startup (not just install) → performance cost; use a cached manifest or lazy evaluation.

## Grounding

Designed during KnowledgeForge Phase 2 cc-rules-and-hook-emitter spec (2026-06-10, bead `knowledgeforge-core-5fd`). The adversarial-critic review (finding [1]) identified that a naive append-only merge would duplicate entries on every re-install. Sidecar-manifest pattern was the proposed resolution. Implementation is pending in Phase 2 CC emitter work; pattern is documented preemptively based on the spec rationale and design precedents from related patterns (marker-based regen, sidecar-mirror, idempotent migrations).
