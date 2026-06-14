# SPEC 5 — Plugin packaging via kf-compile bundle target

**Status:** LOCKED (Phase 2 spec-commit complete, human-approved 2026-06-13)
**Date:** 2026-06-13
**Driver bead:** `knowledgeforge-core-f8a`
**Phase chain:** Probe → ERA → Strategist → Builder → Critic (1 revision cycle) → spec-commit
**Decision type:** evaluative (existing patterns from 4 prior compile targets)
**Risk tier (Module 20):** MEDIUM
**Reversibility:** full (revert commit; 4 existing compile targets untouched)
**Phase 3 implementation:** gated separately

---

## Cross-spec dependencies

- **SPEC 1** (this session): Independent. Plugin bundle MAY emit adversarial-critic.md if SPEC 1 has already merged (Module 07's `## CC Agent (Adversarial Variant)` section must exist for the bundle's manifest to populate). If SPEC 1 has not merged, bundle skips adversarial-critic entry — non-blocking.
- **SPEC 4** (this session): Independent. Plugin bundle MAY emit knowledge-librarian.md if SPEC 4 has already merged.
- **No upstream Module updates required.** SPEC 5 touches `kf-compile.py` + new binding + new manifest schema + new installer template only.

---

## Purpose

`kf-compile.py` gains a 5th target `plugin-bundle` that emits an installable bundle of shared skills + MCP connectors. internexio repos ([project], client-project, visionforge, [project], etc.) consume the bundle by reference rather than re-implementing inline. Eliminates the duplication surfaced in the Phase 0 SPEC 5 evidence probe: KF orchestrator scaffolding present in 5 repos, cos-mcp present in 3 repos.

---

## Design

### D1. New compile target `plugin-bundle`

`kf-compile.py` explicit patches:

1. **Line 989 argparse:** append `"plugin-bundle"` to the `choices` list:
   ```python
   choices=["claude-code", "claude-projects", "cowork", "vscode", "plugin-bundle"]
   ```

2. **Lines 1058-1061 dispatch block:** append branch:
   ```python
   elif args.target == "plugin-bundle":
       manifest = compile_plugin_bundle(
           binding, output_root, args.dry_run, args.diff, version,
           check_divergence=args.check_divergence,
       )
   ```

3. **New function `compile_plugin_bundle()`** parallel to `compile_claude_code()`. Emits a directory structure:
   ```
   {output_root}/
     kf-plugin-bundle.json           # Bundle manifest (skills + connectors + version)
     skills/                         # Compiled skills
       builder.md
       critic.md
       ...
     agents/                         # Compiled agents
       adversarial-critic.md         # if SPEC 1 merged
       knowledge-librarian.md        # if SPEC 4 merged
       ...
     mcp/                            # Connector configs (path-validated)
       cos-mcp.json                  # if cos_dev_root resolved
     install.sh                      # Consumer-side installer (D3)
   ```

- **Decision type:** evaluative.
- **Confidence:** 0.85.

### D2. New binding `platform-bindings/plugin-bundle.yaml`

```yaml
target: plugin-bundle
status: active

output_structure:
  manifest_path: "kf-plugin-bundle.json"
  skills_dir: "skills/"
  agents_dir: "agents/"
  mcp_dir: "mcp/"
  installer_path: "install.sh"

bundle_manifest_schema: "compiler/plugin-manifest-schema.yaml"

module_outputs:
  # KF orchestrator scaffold (present in 5+ repos per probe)
  00: {outputs: [{type: agent, path: "agents/kf.md", section: "CC Agent"}]}
  02: {outputs: [{type: agent, path: "agents/builder.md", section: "CC Agent"}]}
  07:
    outputs:
      - {type: agent, path: "agents/critic.md", section: "CC Agent"}
      - {type: agent, path: "agents/adversarial-critic.md",
         section: "CC Agent (Adversarial Variant)",
         requires_module_version: ">=7.5.0"}   # SPEC 1 must be merged
  21:
    outputs:
      - {type: agent, path: "agents/knowledge-librarian.md",
         section: "CC Agent (Knowledge Librarian)",
         requires_module_version: ">=7.5.0"}   # SPEC 4 must be merged
  # ... other modes ...

mcp_connectors:
  - id: cos-mcp
    source: "$COS_DEV_ROOT/cos/cos-mcp/server.json"
    path_type: absolute_requires_local_config
    fallback_message: |
      cos-mcp source path not found. Set $COS_DEV_ROOT environment variable
      to your [project] clone root, OR skip this connector.
    targets: [[project], client-project, visionforge, [project]]
    required: false

consumer_installer:
  template: "compiler/plugin-bundle-install.sh.tmpl"

deduplication_inventory:
  # Reference, not enforcement. Documents what the bundle replaces.
  - id: kf-orchestrator-scaffold
    duplicated_in: [[project], client-project, visionforge, [project], [project]]
  - id: cos-mcp-connector
    duplicated_in: [[project] (canonical), [project] (clone), visionforge (reference)]
```

`requires_module_version` is a NEW per-output field that lets the bundle skip emissions when the source module hasn't yet been upgraded to expose the named section. The compiler logs the skip as a manifest entry with `status: skipped_version_gate`.

- **Decision type:** evaluative.
- **Confidence:** 0.8.

### D2b. Bundle version stamping + session-start version check

Compiler emits an HTML-comment version stamp in each installed skill/agent file header (in addition to the existing kf-compile sentinel):

```
<!-- kf-bundle: skill=builder | bundle_version=1.2.3 | source_module=02_builder.md | module_version=7.4.0 -->
```

Manifest schema gains `min_consumer_bundle_version` per skill reference (D3 below). Consumer loop definitions may declare:
```yaml
requires:
  kf-plugin-bundle: ">=1.2.0"
```

Orchestrator (`kf.md` compiled CC Agent block) gains a session-start check: read installed skill stamps for any skill referenced in the current session; if `bundle_version < required min` → surface a non-blocking advisory:
```
Stale bundle: skill X is v[stale] but session requires ≥v[min].
Re-install plugin bundle before relying on this skill.
```

**Sunset:** Version-stamp parsing added to orchestrator in same release as SPEC 5. Orphan-stamp tolerance window: 30 days post-rollout (skills installed before SPEC 5 land without the stamp; orchestrator treats as `bundle_version: unknown`, advisory-only).

- **Decision type:** evaluative.
- **Confidence:** 0.85.

### D3. Bundle manifest schema (`compiler/plugin-manifest-schema.yaml`)

```yaml
plugin_manifest:
  version: string              # tracks kf.yaml version
  bundle_id: string            # e.g., "kf-plugin-bundle"
  bundle_version: semver       # bumped on bundle composition change

  skills:
    - name: string
      path: string             # relative to bundle root
      module_source: string
      module_version: string
      min_consumer_bundle_version: semver   # optional

  agents:
    - name: string
      path: string
      module_source: string
      module_version: string
      tools_required: array    # informational
      min_consumer_bundle_version: semver   # optional

  mcp_connectors:
    - id: string
      path_type: bundled | relative_to_bundle | absolute_requires_local_config
      source_path: string                   # only present if path_type != bundled
      bundle_path: string                   # only present if path_type == bundled
      fallback_message: string              # required when path_type == absolute_requires_local_config
      required: boolean
      install_command: string

  install_protocol:
    - step: copy_skills_to_target_repo
    - step: copy_agents_to_target_repo
    - step: register_mcp_connectors_in_target_settings
    - step: emit_install_receipt   # writes .kf-bundle-install.json
```

- **Decision type:** evaluative.
- **Confidence:** 0.85.

### D3b. Path type discipline + install-time validation

Bundle-side installer (`install.sh` written by compiler from template) MUST:

1. For each MCP entry, resolve path according to `path_type`:
   - `bundled` → copy from bundle to target `.mcp.json` (always succeeds).
   - `relative_to_bundle` → resolve `source_path` relative to bundle root; copy.
   - `absolute_requires_local_config` → check `[ -f "$RESOLVED_PATH" ]`; if missing, emit `fallback_message` to stderr AND SKIP THIS ENTRY (do NOT write a stale path to `.mcp.json`).

2. Record each entry outcome in `.kf-bundle-install.json` receipt:
   ```json
   {
     "bundle_version": "1.2.3",
     "installed_at": "2026-06-13T14:00:00Z",
     "mcp_entries": [
       {"id": "cos-mcp", "path_checked": "~/Scripts/[project]/cos/cos-mcp/server.json",
        "verified": true, "action": "written"},
       {"id": "other-mcp", "path_checked": "/missing/path", "verified": false, "action": "skipped"}
     ]
   }
   ```

3. Merge MCP entries into `{target_repo}/.mcp.json` via strip-then-add by signature (signature = `{id, command, args}`). Receipt enables idempotent re-runs.

- **Decision type:** evaluative.
- **Confidence:** 0.8.

### D4. Reference-not-inline contract (portability hedge)

Consumer loop definitions today contain inlined skill bodies. Post-SPEC-5, definitions become reference form:

```yaml
# Consumer loop definition
mode_chain:
  - mode: builder
    skill: kf-plugin-bundle/builder      # reference, not inlined body
```

Bundle install resolves the reference at the target-repo `.claude/skills/kf/builder.md`. Definitions bind to AGENTS.md/SKILL.md/MCP shape — not to vendor glue — so they stay portable across Claude Code and Codex.

**SPEC 5 specifies the publication side only.** Consumer-side migration (per-repo loop definition rewrites) is follow-on work. No SPEC 5 commit edits consumer repos.

- **Decision type:** evaluative.
- **Confidence:** 0.85.

---

## Implementation (Phase 3 — out of scope)

### Pre-flight inventory

All of the following must land in the same squash-merge PR:

- [ ] `compiler/kf-compile.py`:
  - Line 989: append `"plugin-bundle"` to argparse `choices`
  - Lines 1058-1061: append `elif args.target == "plugin-bundle":` dispatch branch
  - New function `compile_plugin_bundle()` per D1
- [ ] `platform-bindings/plugin-bundle.yaml`: create per D2
- [ ] `compiler/plugin-manifest-schema.yaml`: create per D3
- [ ] `compiler/plugin-bundle-install.sh.tmpl`: consumer-side installer template per D3b

### Smoke test (acceptance gate)

```bash
python3 compiler/kf-compile.py --target plugin-bundle --output /tmp/kf-bundle-test --dry-run
```

Pass criteria:
- Exits 0
- Manifest non-empty
- At least one `would_write` entry for `agents/builder.md` (independent of SPEC 1/4 merge state)
- If SPEC 1 merged: manifest also shows `agents/adversarial-critic.md`
- If SPEC 4 merged: manifest also shows `agents/knowledge-librarian.md`
- If neither merged: manifest shows `skipped_version_gate` entries for those agents

CI gate: command exits 0 AND manifest non-empty.

### Real-write test

```bash
python3 compiler/kf-compile.py --target plugin-bundle --output /tmp/kf-bundle-test
ls /tmp/kf-bundle-test/
# Expected:
#   kf-plugin-bundle.json
#   skills/
#   agents/
#   mcp/
#   install.sh
cat /tmp/kf-bundle-test/skills/builder.md | head -2
# Expected first line:
#   <!-- Generated by kf-compile | source: 02_builder.md | type: skill | version: 7.X.X -->
# Expected second line:
#   <!-- kf-bundle: skill=builder | bundle_version=... | source_module=02_builder.md | module_version=... -->
```

### Consumer-side install test (post-bundle-build)

In a fresh test repo:
```bash
bash /tmp/kf-bundle-test/install.sh
ls .claude/skills/kf/
# Expected: builder.md, critic.md, ... (per bundle)
cat .kf-bundle-install.json
# Expected: receipt per D3b
```

Idempotency: re-run produces no net change.

---

## Assessment (testability)

| Test | Pass criterion |
|---|---|
| Dispatch routes correctly | `--target plugin-bundle` enters `compile_plugin_bundle()` (not generic fallthrough) |
| Manifest schema validates | `plugin-manifest-schema.yaml` is valid YAML; conformant manifests pass validation |
| Skill files carry bundle-version stamp | `head -2` of each installed skill matches D2b format |
| MCP path validation | Installer with `$COS_DEV_ROOT` unset skips cos-mcp entry with fallback message; receipt records `verified: false, action: skipped` |
| Idempotent install | Second run of `install.sh` produces identical receipt; no `.mcp.json` drift |
| Version gate skip | If Module 07 lacks `CC Agent (Adversarial Variant)` section, manifest entry has `status: skipped_version_gate`, not error |

---

## Adversarial findings resolution (Phase 2 revision cycle 1)

| Critic finding | Resolution |
|---|---|
| Sev-1 [1] install.sh destructive on concurrent/repeated runs; cos-mcp absolute-path baking | D3b adds `path_type` discipline; installer validates paths AND skips entries (not stale-writes) on missing config; receipt records per-entry verification status |
| Sev-2 [2] No bundle-version stamping; stale skill body produces invisible drift | D2b adds version stamp in installed file header; manifest schema has `min_consumer_bundle_version`; orchestrator session-start advisory check |
| Sev-2 [3] argparse choices not updated; SPEC produces dead CLI invocation | D1 explicitly patches line 989 (choices) AND lines 1058-1061 (dispatch); smoke test command added as acceptance gate |

No findings persisting after revision cycle 1. Loop exit: `findings_resolved_on_revision`.

---

## Revision history

- 2026-06-13: SPEC 5 v1 drafted by Builder (decision_type_exercised=evaluative_judgment).
- 2026-06-13: Adversarial pass returned 3 Sev-2+ findings (1 CRITICAL, 2 HIGH).
- 2026-06-13: Revision cycle 1 — Patches 5A/5B/5C applied; all findings resolved.
- 2026-06-13: Human approval at Phase 2 spec-commit gate. Locked.
