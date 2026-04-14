# KnowledgeForge Core — Single Source of Truth

## Role of This Repo

`knowledgeforge-core` is the canonical source for all KnowledgeForge module specs, plans, wiki, and (when built) the compiler. All variant repos (`knowledgeforge-cp`, `knowledgeforge-cc`, `knowledgeforge-cw`, `knowledgeforge-web`) derive from here.

**Current version:** 7.0.0-alpha (see `kf.yaml`)
**Current phase:** Phase 0 — Repo setup and sync

---

## Stack

- **Python**: 3.11+ — compiler scripts, hook scripts, test runners
- **YAML**: kf.yaml, platform bindings, model profiles, test suites
- **Markdown**: all module specs, plan docs, wiki entries
- **Shell**: utility scripts in `scripts/`

## Directory Structure

```
knowledgeforge-core/
├── CLAUDE.md                   # This file
├── README.md                   # Public-facing overview
├── kf.yaml                     # Version, metadata, variant registry
├── IMPLEMENTATION_PLAN.md      # Master plan (Phase 0–10)
├── modules/                    # Canonical module specs (00–25)
├── plans/                      # Architecture session docs, integration plans
├── wiki/                       # Tier 0 accreted knowledge
│   └── architecture/
├── templates/                  # Spec templates from Module 04
├── taxonomy/                   # Controlled vocabulary from Module 23
├── model-profiles/             # Per-model weakness/strength maps
│   └── _schema.yaml
├── platform-bindings/          # Per-platform adaptation rules
├── compiler/                   # kf-compile tooling (Phase 6)
├── docs/
│   └── planning/               # Session notes, drift audits
├── tests/                      # Test suites (routing, modules)
│   └── routing_test_suite.yaml
└── scripts/                    # Utility scripts
```

---

## Module File Conventions

### Naming
- Format: `NN_lowercase_with_underscores.md`
- Range: `00_orchestrator.md` → `25_entity_relationship_analysis.md`
- New modules get the next sequential number

### Every Module Must Have

```markdown
# Module NN: [Name]
**Version:** X.Y.Z
**Last Updated:** YYYY-MM-DD
**Changelog:**
- X.Y.Z: [What changed]
```

### When Editing Modules
DO:
- Bump the module version (patch for corrections, minor for behavior changes, major for protocol overhauls)
- Add a changelog entry with date and description
- Update `kf.yaml` if the change affects the overall system version
- Cross-check references to this module in other modules before changing interface

DON'T:
- Edit module files without bumping the version
- Remove a module's section without checking cross-references (grep first)
- Rename modules without updating `kf.yaml` and all referencing files
- Edit `knowledgeforge-cp` or `knowledgeforge-cc` directly — changes go here first, then compile out

---

## Python Scripts (Compiler + Hooks)

### Version
Python 3.11+. No external dependencies unless absolutely necessary — use stdlib.

### Error Handling
DO:
- Every script must handle graceful degradation: if it fails, `exit 0` (not `exit 1`) unless the failure should block
- Hooks MUST exit 0 on non-critical failures — blocking Claude is a last resort
- Log failures to stderr with context: `sys.stderr.write(f"[kf-route] Ollama unavailable: {e}\n")`
- Include explicit timeouts on all subprocess/network calls

DON'T:
- Let unhandled exceptions propagate in hook scripts (Claude sees the traceback, not the output)
- Use `sys.exit(1)` in hooks without intentional blocking semantics
- Hardcode paths — use `Path(__file__).parent` relative resolution

### Pattern for Hook Scripts
```python
#!/usr/bin/env python3
"""
kf-{hook-name}.py — [brief description]
Hook type: [UserPromptSubmit | Stop | PreCompact | PostCompact | PostToolUse | SessionStart]
Graceful degradation: [what happens on failure]
"""
import sys
import json
from pathlib import Path

def main():
    try:
        data = json.load(sys.stdin)
        # ... logic ...
        result = process(data)
        print(json.dumps(result))
    except Exception as e:
        sys.stderr.write(f"[kf-{hook}] {e}\n")
        # Graceful degradation: pass through unmodified
        print(json.dumps(data))
        sys.exit(0)

if __name__ == "__main__":
    main()
```

---

## YAML Files

### kf.yaml — Version Source of Truth
- Bump `version` when any module changes
- Keep `changelog` up to date with every commit
- `variants` section tracks all downstream repos

### Test Suites
Format:
```yaml
tests:
  - prompt: "..."
    expected_mode: builder | critic | debugger | strategist | expert | synthesizer | navigator | coordinator | calibrator | null
    expected_decision: reckoning | evaluative | predictive | novel
    expected_cross_cutting: [M12, M15]  # module numbers
```

### Model Profiles
Must follow `model-profiles/_schema.yaml`. Don't add fields the schema doesn't define.

---

## Plan Documents

Plan docs live in `plans/`. They are read-only reference — do not edit them to reflect "what happened." Instead:
- Create new docs in `docs/planning/` for session notes, drift audits, decisions
- Reference plan docs by filename, don't copy content out

---

## Wiki Entries

Wiki follows KF taxonomy (see `taxonomy/` and Module 23). Every wiki entry:

```markdown
---
domain: [controlled vocabulary domain]
topic: [controlled vocabulary topic]
tags: [controlled vocabulary tags]
source_fingerprint: [hash or identifier of source]
date: YYYY-MM-DD
---
```

DO NOT create wiki entries with invalid domain/topic/tags — check `taxonomy/` first.

---

## Versioning

| Component | When to bump |
|-----------|-------------|
| Module patch (X.Y.Z → X.Y.Z+1) | Typo fixes, clarifications, no behavior change |
| Module minor (X.Y.Z → X.Y+1.0) | New behavior, additional rules, protocol extension |
| Module major (X.Y.Z → X+1.0.0) | Protocol overhaul, breaking interface change |
| `kf.yaml` system version | Any module minor or major bump |

---

## Git Conventions

### Commit Format
```
{type}({scope}): {description}

{body if needed}
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
Scopes: `module-NN`, `compiler`, `hooks`, `plans`, `wiki`, `taxonomy`, `profiles`

Examples:
```
feat(module-09): Add Phase 4b reproduction step to Debugger
fix(module-12): Correct judge isolation rule wording
docs(plans): Add cc-drift-audit from Phase 0 analysis
```

### Branching
- `main` — stable, always compilable
- `phase/{N}` — work branches per implementation phase
- `module/{NN}-{description}` — targeted module edits

---

## Off-Limits

- Do not modify files in `plans/` — they are reference artifacts from architecture sessions
- Do not commit `.env` files or API keys
- Do not edit `knowledgeforge-cp`, `knowledgeforge-cc`, or `knowledgeforge-cw` from this repo
- Do not create wiki entries without a `source_fingerprint` (Module 21 requirement)
- Do not add Python dependencies without documenting them in the script header

---

## Before Committing

- [ ] Module version bumped if module content changed
- [ ] `kf.yaml` changelog updated
- [ ] No hardcoded paths in Python scripts
- [ ] Hook scripts exit 0 on non-critical failures
- [ ] Wiki entries have valid taxonomy fields
- [ ] Commit message follows format above

---

## Active Work

See `IMPLEMENTATION_PLAN.md` for the full Phase 0–10 roadmap.
Current: Phase 0 — establishing canonical repo structure and syncing from CP.

Next: Phase 1 — `UserPromptSubmit` hook + Gemma 3 4B routing classifier.
