---
title: ES2020/ES2021 lib divergence — local tsc green, CI tsc red on String.replaceAll
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 4
created: 2026-05-12
domain: compiler
topic: version-incompatibility
tags: typescript, ci, version-incompatibility, es2020, es2021, build-systems, frontend
related_entries: []
---

# ES2020/ES2021 lib divergence — local tsc green, CI tsc red on String.replaceAll

## The Footgun

`String.replaceAll` is an ES2021 feature. If a project's `tsconfig.json` has `"target": "ES2020"` (or `"lib": ["ES2020", "DOM"]`), recent local toolchains (TypeScript 5.4+, Node 23+) often permit `.replaceAll()` because their bundled `lib.es2021.string.d.ts` leaks into type resolution. The CI image, pinned to a specific TypeScript version and Node LTS, will reject the same code with:

```
Property 'replaceAll' does not exist on type 'string'. Do you need to change
your target library? Try changing the 'lib' compiler option to 'es2021' or later.
```

## Symptom Signature

- Local `npm run typecheck` → 0 errors
- CI `tsc --noEmit` → fails on a single `.replaceAll(` call
- Code targets a string global-replace (e.g., `status.replaceAll('_', ' ')`)
- Error message explicitly names the missing ES2021 feature

## When This Applies

- Any TypeScript project with `target: ES2020` or `lib: ["ES2020", ...]`
- Especially React/Vite/Next.js projects where lib defaults trail target by a year
- Devs on bleeding-edge Node (22+) won't catch this locally

## When This Does NOT Apply

- Projects targeting ES2021+ (`replaceAll` is in-spec)
- Projects using `String.prototype.replace(/pattern/g, ...)` already
- Projects with pinned TypeScript/Node versions matching CI exactly

## Fix

Replace `.replaceAll(needle, replacement)` with `.replace(/<needle>/g, replacement)` — pure ES2015, semantically identical for single-character/literal-string cases. For regex-special characters in `needle`, escape them first.

Example from this session (COS SEO Planner Slice 9):

```typescript
// BEFORE (CI failure):
{status.replaceAll('_', ' ')}

// AFTER (CI green):
{status.replace(/_/g, ' ')}
```

## Prevention

- **Pin TypeScript version explicitly** in `package.json` so local devs match CI exactly
  ```json
  "typescript": "5.4.2"
  ```
- **Or bump `tsconfig.target` to `ES2021`** once browser support is acceptable (all modern browsers support it since 2021)
- **Pre-commit hook**: run `tsc --noEmit` with the same version CI uses to catch mismatches before commit
- **CI visibility**: log the exact TypeScript and Node versions at the start of the type-check job

## Root Cause

TypeScript's type library resolution is version-dependent. Newer toolchains bundle newer lib files (e.g., `lib.es2021.string.d.ts`) that leak into the resolution even when `target` is set lower. When the `lib` option is not explicitly set, TypeScript's default behavior changes with the toolchain version. CI's pinned, older version doesn't have this lib file bundled, so type-checking fails.

## Grounding

Verified in COS SEO Planner Slice 9 (2026-05-12). Commit `3813f9b` is the hotfix. Local environment: Node 23, TypeScript 5.4.2. CI environment: pinned TypeScript version (older LTS). The same file type-checked green locally and red in CI within 1m42s of CI run. Switch to `.replace(/_/g, ' ')` deployed clean to both `internexio/cos` and SEMalytics/cos production.

## Related Reading

- [TypeScript lib files reference](https://www.typescriptlang.org/tsconfig#lib)
- [ES2021 features](https://www.ecma-international.org/ecma-262/12.0/)
- Browser support for `String.prototype.replaceAll()`: all modern browsers, IE excluded

## Source Context

Discovered during SEO Planner CI hotfix session (2026-05-12). A React component using `.replaceAll()` for whitespace normalization passed local type-checking but failed CI on the same file. Root cause: CI's TypeScript version didn't have ES2021 lib bundled; local node had it from `node_modules`. The fix was a one-line regex change from `.replaceAll('_', ' ')` to `.replace(/_/g, ' ')`.
