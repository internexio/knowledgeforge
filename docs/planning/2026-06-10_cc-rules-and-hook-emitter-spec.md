# CC Target Spec Patch — Rules Emitter + Hook Emitter (Phase 2)

**Bead:** `knowledgeforge-core-5fd`
**Phase:** 2 of 2 (Phase 1 = M21 activation_profile, bead `y4b`, approved 2026-06-10)
**Status:** SPEC — no implementation. Stop at human gate.
**Targets:**
- `platform-bindings/claude-code.yaml` (cc binding extension)
- `compiler/kf-compile.py` (new emitter functions in `compile_claude_code()`)
- M21 runtime block (a small additional spec patch in M21 — see Section 5)
**Proposed cc binding version bump:** 7.0 → **7.1** (additive; new output types and special_outputs)
**KF system version:** bumps to **7.5.0** on Phase 2 implementation (Phase 1 took 7.3.1 → 7.4.0; Phase 2 takes 7.4.x → 7.5.0)
**Decision class:** evaluative (ownership-rule resolution, threshold design) + novel (new emitter classes). Tagged inline.

**Substrate verified:** `docs.claude.com/en/memory`, `/en/claude-directory`, `/en/settings` — fetched 2026-06-10 (same fetch that grounded Phase 1).

**Phase 1 carry-forward (from y4b):** Expected `trigger` distribution under Option A is ~90% `invariant` / ~10% `task_bound` / <1% `path_bound`. **Design this emitter assuming sparse `path_bound`.** Treat `invariant` as the common path, `task_bound` as the secondary path (routes to skill, not rule), `path_bound` as the explicit-override case.

**Revision history:**
- 2026-06-10 r1: initial draft
- 2026-06-10 r2: revised per adversarial-critic findings [1]–[6]. Changes:
  - [1] (Critical) install.sh merge pseudocode now strips KF-managed entries BEFORE extending — idempotent on re-install
  - [2] (High) `_kf_source_rule` sentinel locked AND moved into a dedicated `kf_hooks` parallel key in `settings.kf.json` to eliminate user-data-destruction path
  - [3] (High) `extract_section()` `CC_SECTION_MARKERS` gap added to implementation sequence + cc_rules section convention renamed to `## CC Rules — X` (plural, matches existing marker)
  - [4] (High) `kf_*` provenance metadata moved out of YAML frontmatter into an HTML comment block — definitively not parsed by substrate
  - [5] (High) hook emitter explicitly reframed as deferred-activation at v1 (same pattern as Phase 1's `native` field) — inert until at least one module ships cc_hooks AND the linter violation counter lands
  - [6] (High) Phase 1 prerequisite gated by verifiable check (kf-compile dry-run manifest reference) and step_5b extracted as standalone M21 patch in Phase 2's implementation pass (no modification of approved Phase 1 spec)

---

## 0. What this spec changes (1-sentence summary)

Adds two emitter classes to the cc compile target — `cc_rules` (compile-time path-gated `.claude/rules/*.md` writes) and `cc_settings_fragment` (`.claude/settings.kf.json` written by the compiler, install-time-merged by `cc/install.sh` into `.claude/settings.json`) — and specifies the runtime rules write path inside the M21 accretion loop, with an explicit namespace partition between compile-time and runtime entries to keep them reconcilable.

---

## 1. Substrate facts (verified 2026-06-10)

**Decision tag:** reckoning. Confidence: **high**. All facts below come from docs.claude.com pages fetched 2026-06-10.

- **`.claude/rules/`** is a directory of `.md` files. All `.md` files discovered recursively (subdirs supported). Rules WITHOUT `paths:` frontmatter load at launch with the same priority as `.claude/CLAUDE.md`. Rules WITH `paths:` frontmatter load only when Claude reads a matching file (any tool use that reads a path matched by a glob in the frontmatter). User-level rules (`~/.claude/rules/`) load before project rules; project wins on conflict.
- **Glob support** in `paths:` includes `**/*.ext`, `src/**/*`, brace expansion `**/*.{ts,tsx}`, and multiple-pattern arrays.
- **Symlinks** are resolved; circular symlinks handled gracefully.
- **`settings.json`** has scopes user (`~/.claude/settings.json`), project (`.claude/settings.json`), local (`.claude/settings.local.json`), and managed. **Arrays merge across layers.** The file is watched live; a `ConfigChange` hook fires on each detected change.
- **`hooks` key** is top-level in `settings.json`. Hook events confirmed: `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop`, `SessionStart`, `PreCompact`, `ConfigChange`, `InstructionsLoaded`.
- **Hook entry shape** (from docs):
  ```json
  "hooks": {
    "PreToolUse": [
      {
        "type": "command" | "http",
        "command": "string",
        "matcher": { "pattern": "...", "tools": [...] }
      }
    ]
  }
  ```
- **`InstructionsLoaded` hook** is observability gold: fires when instruction files load, useful for debugging path-gated rule loading. Not required for Phase 2 but worth noting.

---

## 2. The load-bearing Phase 2 decision — ownership-rule resolution

**Decision tag:** evaluative. Confidence: **high**.

The cc binding (`platform-bindings/claude-code.yaml`) currently declares two explicit ownership boundaries that conflict with the handoff's requested hook emitter:

```yaml
# From the existing binding (Phase 0 finding):
output_structure:
  settings: ".claude/settings.json"   # Not compiled — platform config only
# ...
# special_outputs section:
#   Hooks — NOT compiled. As of 2026-05-19, knowledgeforge-cc is the
#   authoritative source for .claude/hooks/ ...
```

Two ways forward; we pick the second.

### Considered: Option A — flip the ownership rule

Make the compiler authoritative for `settings.json` and `.claude/hooks/`. **Rejected.** The cc repo has hand-authored hooks (e.g., `kf-stop-validator`, `mempalace-wiki-mine`, `kf-session-start`) that pre-date this work and that no module spec describes. A flip would either (a) require the compiler to no-op on these files (special-cased per filename — fragile) or (b) require migrating the hooks into module specs (large scope expansion).

### Selected: Option B — fragment-merge via separate compiled file

The compiler writes `.claude/settings.kf.json` (a NEW file, fully compiler-owned). The `cc/install.sh` script shallow-merges it into `.claude/settings.json` at install time. The hooks-from-modules path is INDEPENDENT of the hand-authored `.claude/hooks/*.py` ownership — modules don't author hook *scripts*, they author hook *entries* in settings.json that *reference* scripts (existing or runtime-generated).

**Why this works:**

- `.claude/settings.kf.json` is a fully compiler-owned file. Compile is idempotent on it; user never edits it.
- `.claude/settings.json` remains cc-owned. The merge happens at install time, not compile time — cc has full control over when/how to merge.
- The merge is shallow: top-level keys from `.kf.json` overwrite or extend `.claude/settings.json`. For the `hooks` key specifically, arrays MERGE rather than overwrite (per the substrate's documented layer-merge semantics — we mirror that contract).
- Rollback is trivial: delete `.claude/settings.kf.json`, re-run install.sh, KF-managed hooks vanish.
- The existing `Hooks — NOT compiled` declaration in the cc binding stays accurate: hook *scripts* in `.claude/hooks/` remain not compiled. Hook *entries* in `settings.kf.json` ARE compiled. Two different artifacts.

**Cost:** cc's install.sh gains a JSON merge step (~30 lines of jq or Python). Acceptable.

### Carry-forward for cc binding update

The binding's existing prose comments need a small clarifying edit on implementation. Proposed:

```yaml
# Settings.json — partial ownership split (added 7.1)
#   .claude/settings.json itself: cc-owned (not compiled)
#   .claude/settings.kf.json:     fully compiled — see special_outputs.cc_settings_fragment
#   At install time, cc/install.sh shallow-merges settings.kf.json into settings.json.
#   For the `hooks` top-level key, arrays MERGE (cc's existing entries preserved).
settings: ".claude/settings.json"

# Hooks scripts — NOT compiled (unchanged).
# Hook entries (declarations in settings.json) — compiled via cc_settings_fragment (added 7.1).
```

---

## 3. Rules emitter — compile-time feed

**Decision tag:** novel + evaluative (decomposition rule). Confidence: **high**.

### What graduates out of `kf-meta.md`

`kf-meta.md` today is a single file compiled from Module 00's `## CC Rules` section. It contains the meta-principle, decision classification quick reference, and any always-on guidance. With Phase 2:

- **Stays in `kf-meta.md` (the invariant tier):** Meta-principle, decision classification rubric, the Ozymandias Test, any guidance that applies REGARDLESS of which files the session touches.
- **Graduates out to discrete `.claude/rules/kf/<topic>.md` files (path-gated tier):** Any guidance that is conditionally relevant — applies only when working with files matching specific patterns. Example: rules that only fire when editing TypeScript, Python, Markdown, or specific subdirectory shapes.

### Decomposition rule (the deterministic call)

A new YAML frontmatter block on module specs declares which rules to emit and their gating. **Section heading convention uses `CC Rules — X` (plural), matching the existing `CC_SECTION_MARKERS` set in `compiler/kf-compile.py:50` — see Section 7 implementation note for why singular would silently break `extract_section()`.**

```yaml
# Example: at the top of a module .md file
---
# ... existing module metadata ...
cc_rules:
  # Each entry produces one .claude/rules/kf/<filename>.md
  - filename: typescript-imports.md
    paths:
      - "**/*.{ts,tsx}"
    body_section: "CC Rules — TypeScript imports"
    # Compiler extracts ## CC Rules — TypeScript imports section from the module body
    # and emits it as the file content (minus the heading), with paths: frontmatter.
    # The "CC Rules — " prefix matches the existing CC_SECTION_MARKERS startswith
    # logic in kf-compile.py:79–80, so subsequent ## CC Rules — Y headings stop
    # the extraction at the right boundary.

  - filename: filing-protocol-debugger-output.md
    paths:
      - "wiki/diagnostics/**/*.md"
    body_section: "CC Rules — Debugger wiki conventions"
---
```

**Migration of existing kf-meta.md content:** A separate one-time spec audit (not in this bead) determines which existing kf-meta.md sections are path-scopable. Until that audit happens, kf-meta.md remains the monolith. Phase 2 just adds the *mechanism*; migration is a follow-up bead.

### Output structure

```
your-project/.claude/rules/
├── kf-meta.md                   # Compiled from Module 00 ## CC Rules (existing — unchanged)
└── kf/                          # NEW — namespace partition for compile-time path-gated rules
    ├── typescript-imports.md
    ├── filing-protocol-debugger-output.md
    └── ...                      # One file per module cc_rules entry
```

The `kf/` subdir is the namespace. The substrate auto-discovers subdirs, so loading is transparent.

### kf-compile.py changes

New emitter function `emit_cc_rules_partition()`:

```python
def emit_cc_rules_partition(module_path: Path, frontmatter: dict, output_root: Path,
                            dry_run: bool, manifest: list[dict]) -> None:
    """
    Compile cc_rules entries from a module's frontmatter into .claude/rules/kf/*.md.
    Each entry produces one path-gated rule file. Body content is the section named
    in body_section, extracted via extract_section().
    """
    for rule_entry in frontmatter.get("cc_rules", []):
        out_path = output_root / ".claude/rules/kf" / rule_entry["filename"]
        body = extract_section(module_content, rule_entry["body_section"])
        # Compose frontmatter + body
        content = compose_path_gated_rule(rule_entry["paths"], body)
        emit(module_path.name, out_path, content, rule_entry["body_section"])
```

Existing emit() (line 318) wraps the write with dry-run + manifest accounting.

---

## 4. Rules emitter — runtime feed

**Decision tag:** novel. Confidence: **high**.

### When the runtime rule write fires

In the M21 accretion loop (per y4b's `claude_code_runtime.filing` block, after `step_4b_embedding` and `step_5_file`):

- IF `candidate.activation_profile.trigger == path_bound`
- AND `candidate.activation_profile.path_globs` is non-empty
- AND `candidate.scope == project` (path_bound + global is rejected at step_3c per y4b)

THEN ALSO write `.claude/rules/kf-runtime/<slug>.md` with `paths:` frontmatter populated from `path_globs`.

### Output structure

```
your-project/.claude/rules/
├── kf-meta.md
├── kf/                          # Compile-time partition (Section 3)
│   └── ...
└── kf-runtime/                  # NEW — namespace partition for runtime accreted rules
    ├── 2026-06-10_some-pattern.md
    └── ...
```

### Rule file shape (runtime-written)

**Per Critic finding [4], all KF-internal provenance metadata lives in an HTML comment block at the bottom of the file — NOT in the YAML frontmatter.** The substrate's `paths:` parser behavior on unknown sibling YAML keys is not documented in `docs.claude.com/en/claude-directory`. Three behaviors are possible (silent ignore / warning / treat-as-malformed-and-load-unscoped), and the worst case silently un-gates the rule. HTML comments are definitively not parsed as YAML, so this risk is eliminated by construction.

```markdown
---
paths:
  - "<glob1>"
  - "<glob2>"
---

# <title from candidate.knowledge_target>

<candidate body content>

<!--
KF-RUNTIME-RULE — written by M21 accretion loop. Linter-managed.
kf_source: accretion_loop
kf_bead: <bead_id_or_session>
kf_candidate_id: <candidate-hash>
kf_created: <iso datetime>
kf_activation_profile:
  trigger: path_bound
  decidability: <true|false>
  miss_cost: <low|medium|high>
-->
```

The metadata block is enclosed in an HTML comment. The M21 linter parses it via regex extraction of the `KF-RUNTIME-RULE` block. Module 21 substrate confirms HTML block comments are stripped from CLAUDE.md before context injection (`docs.claude.com/en/memory`, "Block-level HTML comments are stripped before the content is injected into Claude's context") — `.claude/rules/*.md` follows the same load path as CLAUDE.md when unscoped, so the same stripping applies. For path-gated rules, the substrate's behavior on HTML comments is not separately documented, but the worst case is that the comment block is read as content; even then, the substrate cannot parse it as YAML and cannot mis-interpret the gating. Safe by construction.

### Why `.claude/rules/kf-runtime/` and not `.claude/rules/kf/`

**Namespace partition is the idempotency contract.** See Section 6.

### Small M21 spec patch needed (cross-references y4b)

This Phase 2 spec requires a tiny M21 addition in addition to the y4b patches. Append to `step_5_file` (or as a new `step_5b_emit_path_gated_rule`):

```yaml
step_5b_emit_path_gated_rule:
  # Runs after step_5 wiki write, before user_surface.
  condition: activation_profile.trigger == path_bound AND scope == project
  action:
    - Write .claude/rules/kf-runtime/<slug>.md with paths: frontmatter from path_globs
    - Body: candidate body content (markdown)
    - Append provenance frontmatter (kf_* fields) for linter/Module 14 audit
  on_error:
    - Wiki write already succeeded; log error to compile.md and continue
    - Do NOT roll back the wiki entry
```

This is small enough to fold into y4b's M21 patches OR ship as a separate v7.4.1 minor patch. **Recommendation:** fold into y4b's implementation pass (one M21 edit, one compile) — cleaner. Update y4b's Section 11 implementation sequence to include this step.

---

## 5. Hook emitter (deferred-activation at v1)

**Decision tag:** novel + evaluative (threshold). Confidence: **high** on shape, **medium** on threshold defaults (calibration-needed).

### v1 activation policy — deferred-activation (resolves Critic finding [5])

Per Critic finding [5], the hook emitter ships in inert-default mode at v1, structurally analogous to Phase 1's `native` field:

- **At v1, no module ships `cc_hooks` entries.** Migration of any rule to hook tier requires (a) the linter violation counter (follow-up bead "M21: linter health check — count rule violation events"), (b) the kf-meta.md migration audit (separate follow-up), and (c) at least 30 days of linter data per the graduation threshold below.
- **The compiler MUST handle the empty case cleanly.** `.claude/settings.kf.json` may be emitted as `{"hooks": {}}` or omitted entirely; the spec locks the OMIT case (no file written) so `cc/install.sh` knows to skip the merge step.
- **Effect at v1:** the hook emitter exists in the compiler, accepts `cc_hooks` frontmatter, and would work if any module shipped entries. Zero entries ship at v1. Zero hooks are written.
- **Why ship the emitter now instead of waiting:** same rationale as Phase 1's `native` field. The schema lock-in cost of adding the emitter later (after Phase 2 rules emitter is established) is higher than the cost of a temporarily-inert emitter. Field shape is the contract.

### v1 test fixture (required for implementation to validate emitter)

Because no production module has `cc_hooks` at v1, the implementation pass MUST add a `tests/fixtures/cc_hooks_smoke_module.md` test fixture with one synthetic `cc_hooks` entry. The compiler must successfully emit the corresponding `.claude/settings.kf.json` against this fixture under `--target claude-code` with `--fixture-only`. This test is added in implementation step 5; without it, the emitter cannot be exercised at v1.

### When the hook emitter fires (post-v1, once cc_hooks entries exist)

- Compile-time only. Runtime hook emission is deferred to a future bead — runtime cc has no signal source that beats a recurrence-counted Critic linter pass for hook eligibility, and the linter is currently periodic, not real-time.
- The hook emitter reads from a NEW frontmatter block on module specs (parallel to `cc_rules`):

```yaml
# Example module frontmatter
---
cc_hooks:
  - hook_event: PreToolUse
    matcher:
      tools: ["Bash"]
      pattern: "git commit"
    command: "scripts/kf-hooks/assert-tests-passed.sh"
    type: command
    source_rule: "filing-protocol-tests-before-commit"
    # source_rule points to a cc_rules entry that graduated to hook tier
---
```

### Hook trigger threshold — rule → hook graduation

**Decision tag:** evaluative. Confidence: **medium**.

The handoff asked for "recurrence count or equivalent." The natural counter is the Module 21 linter health check (M21:477). It runs periodically; each run can count rule activations and rule violations per rule file.

**Proposed graduation rule:**

A `.claude/rules/kf/<filename>.md` entry graduates to a hook entry in `cc_hooks` when ALL of:
1. `activation_profile.decidability == true` (mechanical predicate exists)
2. `activation_profile.miss_cost == high`
3. The linter has recorded **≥ 3 violation events** across **≥ 2 distinct sessions** in the last **30 days**

Defaults: `3 / 2 / 30d`. Tunable in a calibration bead.

**What counts as a violation event:** The linter detects via direct check (e.g., the rule said "always X before Y" and the session shows Y without X). This requires per-rule machinery — for v1, only rules tagged with a `linter_check` block in their cc_rules entry are eligible for graduation. Rules without `linter_check` stay path-gated forever (acceptable: they're advisory).

### Hook output structure (resolves Critic findings [1] and [2])

**Storage convention (locked, not deferred):** KF-managed hook entries live in a `kf_hooks` parallel top-level key in `.claude/settings.kf.json`, NOT mixed with hand-authored `hooks` entries. The install-time merge step uses this separation to make idempotency simple: at each install, strip the entire `kf_hooks`-derived contribution from `.claude/settings.json`, then re-add. No sentinel-field detection is needed; the strip targets entries WRITTEN by a previous install (tracked via a sidecar manifest), not entries with a magic field.

```json
// .claude/settings.kf.json shape
{
  "kf_hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": "scripts/kf-hooks/assert-tests-passed.sh",
        "matcher": {
          "tools": ["Bash"],
          "pattern": "git commit"
        },
        "_kf_source_rule": "filing-protocol-tests-before-commit"
      }
    ]
  },
  "_kf_compiled_at": "2026-06-10T15:00:00Z"
}
```

The `_kf_source_rule` and `_kf_compiled_at` fields are KF-internal metadata. **They are reserved keys.** Hand-authored hook entries in `.claude/settings.json` MUST NOT use the `_kf_` prefix. Reserved-key documentation goes into the cc CLAUDE.md as part of the Phase 2 implementation pass.

### cc/install.sh merge step (idempotent — resolves Critic finding [1])

The install step uses a sidecar manifest at `.claude/.kf-install-manifest.json` to track which hook entries were last written. Strip-then-add makes the operation idempotent on N consecutive installs:

```bash
# Pseudocode for cc/install.sh addition (idempotent)
if [ -f .claude/settings.kf.json ]; then
  python3 - <<'PY'
import json
from pathlib import Path

base_path = Path(".claude/settings.json")
kf_path = Path(".claude/settings.kf.json")
manifest_path = Path(".claude/.kf-install-manifest.json")

base = json.loads(base_path.read_text()) if base_path.exists() else {}
kf = json.loads(kf_path.read_text())

# Step 1 — STRIP previously-installed KF hooks (using sidecar manifest)
prior = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"hook_signatures": []}
prior_sigs = set(prior.get("hook_signatures", []))

def sig(entry):
    # Stable signature for a hook entry — used to identify previously-installed entries
    return json.dumps({k: v for k, v in entry.items() if not k.startswith("_kf_")}, sort_keys=True)

base.setdefault("hooks", {})
for event, entries in list(base["hooks"].items()):
    base["hooks"][event] = [e for e in entries if sig(e) not in prior_sigs]
    if not base["hooks"][event]:
        del base["hooks"][event]

# Step 2 — ADD newly-compiled KF hooks
new_sigs = []
for event, entries in kf.get("kf_hooks", {}).items():
    base["hooks"].setdefault(event, []).extend(entries)
    for e in entries:
        new_sigs.append(sig(e))

# Step 3 — Write base + sidecar manifest
base_path.write_text(json.dumps(base, indent=2))
manifest_path.write_text(json.dumps({"hook_signatures": new_sigs}, indent=2))
PY
fi
```

**Idempotency guarantees:**
- Re-running install with unchanged `.claude/settings.kf.json` produces zero net change to `.claude/settings.json` (strip removes N entries, add re-adds the same N — final state is byte-identical except for the sidecar timestamp).
- Re-running install after `.kf.json` SHRINKS (e.g., hook graduated back down to rule tier) correctly removes the now-unwanted entry (strip removes it; add doesn't re-add).
- Re-running install after `.kf.json` GROWS adds only the new entries (strip removes old N; add adds new N+M).
- **User-authored hand-edits in `.claude/settings.json` are preserved.** The strip step targets entries by stable signature in the sidecar manifest, not by `_kf_source_rule` presence. A user who hand-authors an entry with `_kf_source_rule` set (or any other reserved-prefix collision) is NOT silently deleted — the strip only removes entries whose signature is in the manifest from the last install.

**Sidecar manifest location:** `.claude/.kf-install-manifest.json`. Hidden file (dot-prefix). Should be added to `cc/.gitignore` (cc-local install state, not source-controlled).

---

## 6. Idempotency / reconciliation contract

**Decision tag:** novel. Confidence: **high**.

The risk: compile-time and runtime emitters writing into the same directory could collide on filename, clobber each other, or leave orphaned files after the source disappears.

### Partition by subdirectory

| Writer | Output partition | Lifecycle |
|---|---|---|
| Compile-time `emit_cc_rules_partition()` | `.claude/rules/kf/*.md` | Full re-write on each compile. Pre-existing files in `kf/` deleted if not present in current compile manifest. |
| Runtime M21 accretion loop | `.claude/rules/kf-runtime/*.md` | Appended on accretion. Linter-managed (see below). |
| Compile-time `emit_settings_fragment()` | `.claude/settings.kf.json` | Full re-write on each compile. |
| User / cc / cc-install.sh | `.claude/settings.json` (excluding `_kf_source_rule` entries) | Hand-managed. cc preserves. |

### Rules for compile-time partition `.claude/rules/kf/`

- On each compile, the manifest enumerates all expected files
- Compiler deletes any `.claude/rules/kf/*.md` not in the manifest (orphan cleanup)
- This means: removing a `cc_rules` entry from a module → next compile removes the file. Clean.

### Rules for runtime partition `.claude/rules/kf-runtime/`

- Runtime appends only; never deletes during accretion
- The Module 21 linter (existing health check, M21:477) is responsible for periodic cleanup:
  - Stale entry (no matching code in the repo for the `paths:` globs anymore) → flag for archive
  - Supersession (newer entry covers same content) → mark older as `supersedeed_by`
  - Native-suppression after-the-fact (entry's `native: true` was set by human review after filing) → archive
- The linter writes archive metadata; manual deletion is the human path. Auto-deletion is OUT of scope for v1 (avoids silent loss).

### Why partition by subdirectory and not by filename prefix

Filename prefix (e.g., `kf-runtime-foo.md` vs `kf-foo.md`) works but pollutes the `ls` view and makes prefix collisions possible if a user writes a file starting with `kf-`. Subdirectory partition is unambiguous and matches the substrate's recursive discovery.

---

## 7. Integration with `compiler/kf-compile.py` + cc binding

**Decision tag:** reckoning. Confidence: **high**.

### Binding additions (`platform-bindings/claude-code.yaml`)

Append to `special_outputs`:

```yaml
special_outputs:
  # ... existing entries ...

  # NEW — compile-time path-gated rules (added 7.1)
  cc_rules:
    description: |
      Per-module cc_rules: frontmatter entries are compiled into
      .claude/rules/kf/*.md with paths: frontmatter. See spec
      docs/planning/2026-06-10_cc-rules-and-hook-emitter-spec.md
    output_dir: ".claude/rules/kf/"
    cleanup: "remove orphans not present in current manifest"

  # NEW — compiled settings.json fragment (added 7.1)
  cc_settings_fragment:
    description: |
      Per-module cc_hooks: frontmatter entries are compiled into
      .claude/settings.kf.json. cc/install.sh shallow-merges into
      .claude/settings.json at install time.
    output_path: ".claude/settings.kf.json"
    install_merge: true   # signal to cc/install.sh
```

### kf-compile.py additions

In `compile_claude_code()` (line 308):

```python
# After existing per-module emit loop, add:
emit_cc_rules_partition_pass(module_outputs, output_root, dry_run, manifest)
emit_settings_fragment(module_outputs, output_root, dry_run, manifest)
```

Two new helper functions (~50 lines each, stdlib only):

- `emit_cc_rules_partition_pass()` — iterates modules, calls `emit_cc_rules_partition()` per module, then runs orphan cleanup
- `emit_settings_fragment()` — collects all `cc_hooks` entries across modules, composes the JSON, writes to `.claude/settings.kf.json`

### No new dependencies

Per project CLAUDE.md: "No external dependencies unless absolutely necessary — use stdlib." JSON write uses `json.dump`. Glob matching is not needed at compile time (the compiler just propagates the glob strings). Stays stdlib.

### Dry-run behavior

Existing `--dry-run` flag covers both new emitters via the `emit()` wrapper. Existing `--diff` mode shows new files in the diff manifest.

---

## 8. Migration / rollout

**Decision tag:** evaluative. Confidence: **high**.

This spec lands a mechanism. It does NOT migrate existing kf-meta.md content. Migration is intentionally a separate bead because:

1. The mechanism can land and be tested with zero migrated content (kf-meta.md remains the monolith).
2. Migration requires per-section judgment about which rules are truly path-scopable.
3. Splitting mechanism from migration lets reviewers approve the field shape without committing to specific content moves.

**Follow-up beads to open on Phase 2 approval:**
- "M00: audit kf-meta.md for path-scopable sections and migrate to cc_rules entries." P3, blocked-by 5fd.
- "M21: linter health check — count rule violation events for hook graduation." P3, blocked-by 5fd.
- "cc/install.sh: implement settings.kf.json shallow-merge step." P2, blocked-by 5fd (because spec defines the contract).

---

## 9. Adversarial probes (Critic prep — for the auto-Critic gate)

| Probe | Response |
|---|---|
| **"`cc_rules` and `cc_hooks` frontmatter blocks duplicate module-section authoring (CC Rule sections AND frontmatter)."** | The frontmatter declares which sections to extract + their paths/hook configs. The section bodies remain the single source of content. Frontmatter is metadata about extraction, not duplicate content. Same shape as existing `outputs` declarations. |
| **"Install-time merge in cc/install.sh introduces a sync drift mode — if compile runs but install doesn't, .claude/settings.json is stale."** | True. The drift is observable (compile manifest lists `.claude/settings.kf.json` content; user can diff). For high-correctness shops, a post-compile install.sh trigger eliminates this. The drift is acceptable because the rule is install-time-merged, not compile-time-merged — explicitly user-controlled. |
| **"Runtime accretion writing to .claude/rules/kf-runtime/ during an active session means the next file Claude reads might trigger a path-gated rule it didn't have at session start."** | Yes. This is intentional — it's the runtime-growth-of-the-tree behavior the handoff requested. The substrate confirms `InstructionsLoaded` hook fires when files load; observability is built in. |
| **"Linter-managed cleanup of `.claude/rules/kf-runtime/` is hand-waved — no actual deletion mechanism specified."** | Correct, and intentional. v1 manual-deletion is the safe path. Auto-deletion in v2 requires a separate calibration bead with false-positive analysis. Punted explicitly. |
| **"Hook graduation threshold (3 / 2 / 30d) is invented; no calibration data."** | Yes — it's a default. The calibration bead (follow-up #2) is the place that tunes it. Same pattern as M21's existing thresholds (novelty, grounding ≥ 0.6) — start with sensible defaults, calibrate via M12. |
| **"Compile orphan-cleanup deletes user-edited files in `.claude/rules/kf/`."** | If a user hand-edits a compiled file, the next compile re-writes it (same as the existing `--check-divergence` flag for other compiled outputs at kf-compile.py line 281). `.claude/rules/kf/` is compiler-owned; users edit at their own risk. Mitigation: the divergence check fires on hand-edited files. |
| **"What if a hand-authored hook entry in `.claude/settings.json` matches the same event + matcher as a KF-compiled one? Both fire."** | Arrays merge per substrate contract. Both fire. This is the user's responsibility to detect and resolve; the spec does not promise deduplication. If duplicate detection is wanted, it goes in cc/install.sh. |
| **"`cc_rules` frontmatter on Module N requires a `## CC Rule — X` section in Module N. The spec doesn't enforce this binding."** | Compiler's `extract_section()` raises if the named section is missing. Failure is at compile time, not runtime. Acceptable surface for a compile error. |

---

## 10. What this spec does NOT change

- Does not flip cc ownership of `.claude/hooks/` scripts (still cc-authored).
- Does not flip cc ownership of `.claude/settings.json` (still cc-authored, merged-into at install).
- Does not migrate existing kf-meta.md content (mechanism only).
- Does not specify the linter violation-count machinery (deferred to follow-up).
- Does not specify the entity→path-glob resolver (covered by y4b's follow-up `8gp`).
- Does not change `paths:` frontmatter semantics — uses the substrate as-is.
- Does not touch knowledgeforge-cw.

---

## 11. Post-approval implementation sequence — DO NOT EXECUTE during spec review

This is the Phase 2 deliverable. **No emitter implementation, no binding edit, no kf.yaml bump until human gate approval at the bottom of this document.**

The steps below describe what an implementation pass will look like AFTER approval. They are documentation of intent, not instructions to the reviewer.

### Prerequisite — verifiable gate (resolves Critic finding [6])

Phase 1 (y4b) implementation MUST have landed in M21 (v7.4.0 with `activation_profile` block). Per Critic finding [6], the gate must be verifiable, not prose:

```bash
# Run BEFORE starting any Phase 2 implementation step.
python3 compiler/kf-compile.py --target claude-code --output /tmp/kf-check --dry-run 2>&1 | grep -E "21_knowledge_accretion|version"
# Expected output must include "version 7.4.0" or higher AND reference activation_profile in the M21 doc section.
# If the output shows 7.3.x or no activation_profile reference, STOP — Phase 1 has not landed.
```

If the gate fails, do not proceed with Phase 2 implementation. Either complete Phase 1 implementation first, or revise this spec to drop its Phase 1 dependencies (rules emitter Section 3 is independent of activation_profile; hook emitter Section 5 and runtime emitter Section 4 are not).

### Step_5b lands in Phase 2 implementation pass — not retroactively in y4b

Per Critic finding [6], the previous draft proposed "fold step_5b into y4b's implementation pass." Since y4b is already approved, modifying its spec is itself a gate event. The safer path is to ship `step_5b_emit_path_gated_rule` as a standalone small M21 patch in Phase 2's implementation pass (Step 4 below). This requires an M21 minor bump within Phase 2's scope: v7.4.0 → v7.4.1 in this implementation pass (step_5b only), then v7.4.1 → v7.5.0 once all of Phase 2 lands. Net: two minor bumps within a single implementation cycle. Alternative: fold step_5b and the system 7.5.0 bump into one M21 edit with version 7.5.0 — simpler. Implementer chooses.

### Steps that an approved implementation pass will execute

1. **Verify prerequisite gate (above).** Do not proceed if Phase 1 has not landed.
2. **Edit `platform-bindings/claude-code.yaml`:** Apply Section 2 binding clarifying-comment edit + Section 7 `special_outputs.cc_rules` + `cc_settings_fragment` additions. Bump platform binding to 7.1.
3. **Edit `compiler/kf-compile.py`:**
   - **Add `"CC Rules"` already in `CC_SECTION_MARKERS`** — confirmed; the convention `## CC Rules — X` uses the existing marker via the `startswith(m + " ")` clause at line 79–80. No marker update needed (confirmed Section 3 convention rename resolves the original concern).
   - Add `emit_cc_rules_partition()`, `emit_cc_rules_partition_pass()`, `emit_settings_fragment()`. Wire into `compile_claude_code()`. Stdlib only.
   - On empty `cc_hooks` aggregate across all modules: SKIP writing `.claude/settings.kf.json` entirely (do not emit `{}` — emit nothing). Per Section 5 v1 activation policy.
4. **Edit `modules/21_knowledge_accretion.md`:** Add Section 5's `step_5b_emit_path_gated_rule` to the `claude_code_runtime.filing` block AS A STANDALONE PATCH (not folded into y4b). Bump M21 to v7.4.1 OR v7.5.0 (implementer choice — see "Step_5b lands in Phase 2" above).
5. **Add test fixture:** Create `tests/fixtures/cc_hooks_smoke_module.md` with one synthetic `cc_hooks` entry (per Section 5 v1 test fixture requirement). Add a `--fixture-only` CLI flag to kf-compile.py OR a separate `tests/compiler/test_emit_settings_fragment.py` integration test. Implementer chooses test surface.
6. **Edit `kf.yaml`:** Bump system version to 7.5.0; changelog entry covering BOTH the M21 step_5b patch AND the compiler additions.
7. **Test compile:** `python3 compiler/kf-compile.py --target claude-code --output ~/Scripts/knowledgeforge-cc --dry-run` — verify the new emitters appear in the manifest with no errors. At v1 with no migrated content, the dry-run produces empty `.claude/rules/kf/` (orphan-cleanup may delete pre-existing kf-meta.md content, so verify the manifest does NOT mark kf-meta.md as orphan — kf-meta.md lives at `.claude/rules/kf-meta.md`, NOT under `kf/`, so the orphan-cleanup scope is correctly limited).
8. **Land the actual compile output** (`--diff` mode for review, then real compile).
9. **Update cc/install.sh:** This is a separate edit to the knowledgeforge-cc repo (not core). The merge step is in Section 5's pseudocode. The sidecar manifest at `.claude/.kf-install-manifest.json` is added to cc's `.gitignore`.
10. **Open follow-up beads (Section 8):** kf-meta.md migration audit, linter violation counter, cc/install.sh merge step (if implemented separately from step 9), Section 8 entries as documented.
11. **Update cc CLAUDE.md** (in knowledgeforge-cc, not core) noting the new `.claude/settings.kf.json` artifact, the install-time merge contract, and the reserved `_kf_*` prefix for hook entries.

### Implementation-pass commit messages (use when approved)

```
feat(compiler): cc target rules + hook emitters (7.5.0)

Adds emit_cc_rules_partition (compile-time .claude/rules/kf/*.md from
module cc_rules frontmatter) and emit_settings_fragment (.claude/settings.kf.json
from module cc_hooks frontmatter, install-time-merged into settings.json
by cc/install.sh). Resolves ownership-rule contradiction via fragment-merge
(Section 2). Idempotency: kf/ subdir for compile-time, kf-runtime/ subdir
for runtime accretion writes.

Spec: docs/planning/2026-06-10_cc-rules-and-hook-emitter-spec.md
Bead: knowledgeforge-core-5fd
Phase 1 dep: knowledgeforge-core-y4b (M21 v7.4.0+)
```

---

## 12. Confidence summary (revised after Critic pass)

| Component | Confidence | Why |
|---|---|---|
| Ownership-rule resolution (Option B fragment-merge) | **High** | Substrate-confirmed layered merge; preserves cc-authored hook scripts; clean rollback |
| Compile-time rules emitter shape (`cc_rules` frontmatter) | **High** | Section convention renamed to `CC Rules — X` (plural) per Critic [3]; uses existing `extract_section()` correctly via the `startswith(m + " ")` clause |
| `kf_*` metadata in HTML comments, not YAML frontmatter | **High** | Resolves Critic [4]; eliminates the un-verified-substrate-behavior risk |
| Runtime rules emitter (standalone M21 step_5b patch) | **High** | Resolves Critic [6]; landed in Phase 2 implementation pass, not retroactively in y4b |
| Idempotency contract (subdir partition + sidecar manifest) | **High** | Resolves Critic [1]; strip-then-add via signature manifest; user-authored entries preserved (resolves Critic [2]) |
| Hook emitter deferred-activation at v1 (inert until cc_hooks entries ship) | **High** | Resolves Critic [5]; explicit framing matches Phase 1's `native` pattern |
| Hook emitter shape (`cc_hooks` → `kf_hooks` parallel key in `settings.kf.json`) | **High** | Substrate-confirmed schema; reserved-key prefix locked, not deferred |
| Hook trigger threshold (3 / 2 / 30d) | **Medium** | Defaults invented; calibration bead is the place that tunes |
| Integration with kf-compile.py | **High** | Mirrors existing emitter shape; stdlib only |
| Phase 1 prerequisite (verifiable gate) | **High** | Resolves Critic [6]; explicit dry-run check before any Phase 2 step |
| Migration deferred to follow-up | **High** | Mechanism / migration split lets reviewers gate the mechanism |
| Adversarial probe coverage (Section 9 + Critic-r2 findings absorbed) | **High** | Eight in-spec probes + six Critic findings absorbed; spec is hardened |

---

## HUMAN GATE — Phase 2 approval

**This is where the chain stops.** Reviewer options:

- **Approve as-written** → proceed to implementation pass (Section 11 above), open three follow-up beads (Section 8)
- **Approve with conditions** → state conditions; revise in-doc; re-gate
- **Reject** → state reason; revise or abandon

Until one of these is recorded, no implementation occurs.

---

## Cross-references

- **Phase 1 spec (y4b, approved 2026-06-10):** `docs/planning/2026-06-10_module-21-activation-profile-spec.md`
- **M21 surfaces:** `modules/21_knowledge_accretion.md` — candidate metadata (line 288), Dispatcher Boundary (line 936), filing protocol (line 347)
- **cc binding:** `platform-bindings/claude-code.yaml` — `output_structure.rules_dir`, `special_outputs.{static_agents, static_commands}` for prior precedent of ownership boundaries
- **Compiler:** `compiler/kf-compile.py` — `compile_claude_code()` at line 308, `emit()` at line 318, `extract_section()` at line 53
- **Substrate primary sources (fetched 2026-06-10):**
  - `docs.claude.com/en/memory` — CLAUDE.md, auto-memory, `.claude/rules/`
  - `docs.claude.com/en/claude-directory` — `.claude/` structure
  - `docs.claude.com/en/settings` — settings.json schema, hooks contract
