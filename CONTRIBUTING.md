# Contributing to KnowledgeForge

## Before You Start

Read `CLAUDE.md` for the full module conventions, versioning rules, and git commit format. Short version below.

## What Lives Here

`knowledgeforge-core` is the canonical source. All platform variants (`knowledgeforge-cc`, `knowledgeforge-cp`) compile from here via `compiler/kf-compile.py`. Do not edit variant repos directly for module-level changes.

## Module Edits

- Bump the module version for every content change (patch for corrections, minor for behavior changes, major for protocol overhauls).
- Add a changelog entry in the module file.
- Update `kf.yaml` version and changelog if the change is module-minor or major.
- Run `python3 scripts/check-identity-drift.py` to verify embedded version strings match the module header.

## Adding a Module

Modules are numbered sequentially (`NN_name.md`). The next available slot is visible from the `modules/` directory. New modules require:
1. The file under `modules/` with a complete header (version, date, changelog).
2. An entry in `kf.yaml` `modules:` section.
3. A platform binding decision in the relevant `platform-bindings/*.yaml` files.

## Wiki Entries

Every wiki entry requires a valid taxonomy header (`domain`, `topic`, `tags`, `source_fingerprint`, `date`). Check `taxonomy/` for the controlled vocabulary before creating an entry. Entries with invalid taxonomy fields are rejected.

## Commit Format

```
{type}({scope}): {description}
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
Scopes: `module-NN`, `compiler`, `hooks`, `plans`, `wiki`, `taxonomy`, `profiles`

## Pull Requests

- One logical change per PR.
- Pass `python3 scripts/check-identity-drift.py` (exit 0) before submitting.
- For compiler changes, verify with `scripts/verify-deterministic-build.sh`.
- Describe what changed and why. Reference any module version bumps.

## Code of Conduct

See `CODE_OF_CONDUCT.md`.
