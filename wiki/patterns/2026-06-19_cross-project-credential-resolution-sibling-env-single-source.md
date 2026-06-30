---
title: Cross-project credential resolution — read API keys from a sibling project's existing .env rather than duplicating into every environment
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.8
staleness_risk: stable
importance: 3
pinned: false
created: 2026-06-19
domain: patterns
topic: credential-management
tags: credentials, multi-project-tooling, single-source-of-truth, dev-environment, key-management
related_entries:
  - methodologies/2026-06-18_cross-scope-search-blindness-operator-insistence-as-broaden-signal.md
  - methodologies/2026-06-17_tracker-state-drift-at-session-boundary.md
  - infrastructure/2026-05-19_sem-tools-google-ads-keyword-planner-wrapper.md
---

# Cross-Project Credential Resolution — Read API Keys from a Sibling Project's Existing .env Rather Than Duplicating Into Every Environment

## The Pattern

When a credential (API key, token, secret) is needed in a project but already exists in a sibling project's already-configured `.env`, read it from there rather than duplicating into the current project's environment. The sibling project becomes the single source of truth for that credential.

Pattern name: **"Cross-project credential resolution."**

## The Default Failure Mode (What Most Setups Do)

When a new project needs API key X:

1. Operator adds `export X_API_KEY=...` to `~/.zshrc` (or `.env`, or shell-rc-of-the-week)
2. Other projects that already have key X also have their own copies of it
3. Key rotation requires updating N places
4. Some projects miss the rotation, fail silently or with cryptic auth errors

Result: drift between projects. Some have stale keys. Some have the new key. The same secret is duplicated 5+ times across the filesystem.

## The Pattern (Single Source of Truth via Sibling Project .env)

Identify which project OWNS the credential (the one that uses it most intensively, has the most credentials of the same type, or has the most mature `.env` discipline). For new projects that need access:

1. Constant in the new project's script: `SIBLING_ENV = Path("~/Scripts/sibling-project/backend/.env")`
2. Helper function `_load_env_file(path)` parses the flat KEY=VALUE file (small, stdlib-only)
3. Credential resolver checks env first, then the sibling .env: `key = os.environ.get("X_API_KEY") or _load_env_file(SIBLING_ENV).get("X_API_KEY")`
4. The sibling project's existing `.env` remains the canonical store; the consuming project never duplicates

## When This Pattern Applies

- Multi-project monorepo-like setups (e.g., `~/Scripts/projectA/`, `~/Scripts/projectB/`, ...) where the same operator works across multiple repos
- Stable, established projects with mature `.env` discipline that have already wired in the relevant credentials
- Read-only credential sharing (the consuming project only reads; the owning project rotates/manages)
- Projects on the same machine (file path is shared)

## When This Pattern Does NOT Apply

- Projects on different machines (the sibling `.env` isn't accessible)
- When the credential needs different scopes/permissions per project (the sibling's key may have different scopes than needed)
- When key rotation cadence differs between projects (the sibling-owner may rotate without notifying consumers)
- Production environments — secrets-management services (Vault, AWS Secrets Manager, etc.) are the right answer there. This pattern is for local development / personal-machine workflows.

## How to Apply (Concrete Recipe)

1. Identify the canonical owner of the credential (the project where it was first configured + uses it most)
2. In the consuming project's script, add a constant pointing at the sibling's `.env` path
3. Add a small `_load_env_file()` helper (stdlib-only, ~10 lines of Python)
4. In credential resolution: env first, sibling .env second, `None` third (let the caller decide how to fail)
5. Document the dependency in the consuming project's setup docs: "Requires FAL_API_KEY in either env or ~/Scripts/sibling/backend/.env"

## Composes With

- **[[2026-06-18_cross-scope-search-blindness-operator-insistence-as-broaden-signal]]** (filed 2026-06-18): that pattern was about SEARCHING across project scopes when the operator insists an entity exists; this pattern is about RESOLVING credentials across project scopes. Same scope-widening discipline, applied to a different action. When you can't find a credential, sweep `find ~/Scripts -name ".env" -type f` to locate which sibling owns it (same broaden-search discipline).
- **[[2026-06-17_tracker-state-drift-at-session-boundary]]**: tracker hygiene at the sibling-project level — the credential's canonical location should be documented so future sessions don't try to duplicate it.

## Concrete Grounding from the Producing Session

- **Project:** client-project needed access to fal.ai and Ideogram V3 image generation APIs
- **Discovery:** `FAL_API_KEY` was already configured in `~/Scripts/visionforge/backend/.env` (visionforge is a full-stack T2I product that uses fal.ai + Ideogram in production)
- **Implementation:** `scripts/gen-hero-image.py` defines `VISIONFORGE_ENV = Path("~/Scripts/visionforge/backend/.env")` and `get_fal_api_key()` returns `os.environ.get("FAL_API_KEY") or _load_env_file(VISIONFORGE_ENV).get("FAL_API_KEY")`
- **Result:** client-project doesn't duplicate the key into its own `.env` or `~/.zshrc`; visionforge owns it; rotation only happens in one place
- **Documentation:** Brand spec doc explicitly documents this dependency: "visionforge owns the canonical key — no duplication into ~/.zshrc"
- **Why it works:** Both projects are on the same operator machine + the operator never rotates the key in only one place

## Why This Is a Strong Transferable Pattern

- The friction-cost is near-zero: ~10 lines of Python to wire it up, one constant per credential
- The benefit compounds: every additional consuming project that uses this pattern instead of duplicating saves N future rotation headaches
- It surfaces the dependency in code (the path is visible) rather than burying it in undocumented `~/.zshrc` lines
- It composes cleanly with the cross-scope-search pattern: when you can't find a credential, sweep `find ~/Scripts -name ".env" -type f` to locate which sibling owns it (same broaden-search discipline)

## Anti-Pattern This Prevents

- **"Credential proliferation":** same key value appearing in `~/.zshrc`, `projectA/.env`, `projectB/.env`, `~/Library/Application Support/sometool/config.json`, etc. — most stay stale through rotation, drift accumulates, eventual silent auth failure
- **"Lost-credential blindness":** when the operator says "I have that key configured somewhere" and the agent dismisses it without searching for which sibling project owns it (this is the credential-specific instance of cross-scope search blindness)

## Source Context

Discovered live in a 2026-06-19 client-project session where the operator needed fal.ai and Ideogram V3 access for brand-asset image generation. Rather than adding `FAL_API_KEY` to `~/.zshrc` or creating a new `.env` in client-project, the agent identified that `~/Scripts/visionforge/backend/.env` already had the key configured (visionforge is a production T2I product). The implementation pattern — `VISIONFORGE_ENV` constant + `_load_env_file()` helper + env-first-then-sibling resolution — was extracted as a reusable pattern because every multi-project operator on a single machine faces this same credential-duplication problem.
