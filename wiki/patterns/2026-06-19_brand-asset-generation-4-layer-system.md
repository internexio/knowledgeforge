---
title: Brand asset generation system — separate spec from concept, sanitize known failure modes, chain generators with fallback
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-06-19
domain: patterns
topic: brand-asset-generation
tags: brand-assets, image-generation, system-architecture, prompt-engineering, generator-fallback, content-workflow
related_entries:
  - methodologies/2026-06-17_tracker-state-drift-at-session-boundary.md
  - patterns/2026-06-16_lock-llm-json-output-with-explicit-schema-example.md
  - patterns/2026-06-16_anthropic-model-eol-incident-response-three-phase-fix.md
  - patterns/2026-05-22_spec-to-implementation-gap-distinct-review-pass.md
---

# Brand Asset Generation System — 4-Layer Architecture

## The Pattern

When a project needs to repeatedly generate on-brand visual assets (hero images, illustrations, social graphics) from text concepts, the failure mode without structure is consistent: brand drift across generations, the same prompt-engineering mistakes repeated, manual brand-touch-up on every asset. The fix is a permanent 4-layer system that separates the brand identity from the per-asset concept: **spec / sanitize / wrap / chain**. Each layer is independently maintainable; the spec layer accretes hard-won prompt-engineering knowledge as a data structure rather than as script changes.

## When This Applies

- Any project producing >5 on-brand visual assets per month
- Workflows where the same operator writes multiple concepts (consistency across handoffs matters)
- Multi-generator landscapes where different models have different strengths (editorial vs literal interpretation)
- Cases where the brand visual identity is stable (decisions on palette/style are made and don't churn weekly)
- Asset pipelines where model drift (deprecations, API changes) would otherwise break the workflow

## When This Does NOT Apply

- One-off assets where building infrastructure costs more than the savings
- Brands that intentionally vary visual style per asset (the spec layer adds friction)
- Generators with built-in brand systems that handle this internally (rare in 2026)
- Operators producing single-image experiments where prompt-iteration IS the workflow

## The 4 Layers

### Layer 1 — Brand visual identity spec (single source of truth)

A canonical document captures palette, style, hard constraints, and verified model+API specifics. Lives in `wiki/templates/` (or equivalent). Human-readable prose for operators + machine-readable JSON block for scripts.

The spec covers:
- **Palette**: color names (NOT hex codes — see Layer 2 for why)
- **Style**: minimalist editorial, flat vector, etc. — adjectives the operator chose
- **Hard constraints**: what the asset must NEVER have (text, logos, human figures, etc.)
- **Known failure modes**: trigger words and patterns that historically caused bad output, with the response (strip vs warn)
- **Verified models**: model IDs that work as of the last verification date; remediation steps if they drift to 404

### Layer 2 — Sanitizer (strip known-bad patterns, warn on triggers)

Per-asset concept text gets sanitized before being sent to the generator:
- **Strip patterns**: regex that removes inline hex codes, color codes, or any literal-text-as-label triggers (image models often render hex codes like `#F28C18` as visible text labels in the output)
- **Warn words**: words that historically caused unwanted label/text generation (semantic categories like "active"/"retired"/"icons" can produce visible labels or person-silhouettes even when the prompt says "no text")
- **Warnings are logged but not stripped** — the operator decides whether to rewrite the concept

The sanitizer is part of the spec (JSON block) so it can be extended without script changes. When a new failure mode is discovered, the operator adds to the sanitizer rules in the spec doc; the next generation picks up the change. **This is the layer most teams skip** — building it as a data structure (JSON in the spec, not hard-coded in script) lets operators extend it without engineering work.

### Layer 3 — Brand wrapping (prefix + concept + suffix)

The operator only writes the CONCEPT (shapes and arrangement, e.g., "a horizontal row of six small circles, three orange, three outlined"). The wrapper applies:
- **Prefix**: the canonical style preamble from the spec ("A minimalist editorial illustration on a soft cream off-white background. Flat editorial vector style, brand graphic.")
- **Concept**: operator's text, post-sanitize
- **Suffix**: the canonical constraint coda ("Pure abstract geometric composition. 16:9 aspect ratio. Just shapes and lines. No text. No letters...")

Result: every generation has the same brand wrapping; only the concept varies. Concepts stay short (50-100 words); style stays consistent across hundreds of assets.

### Layer 4 — Generator chain with auto-fallback

Some generators are good for some brief shapes (FLUX Pro: editorial composition, asymmetric balance, magazine-cover vibe — but unreliable on literal shape counts). Others are good for others (Imagen 4: literal interpreter, counts shapes faithfully — but less editorially distinctive). Lock primary + fallback with auto-fall-through:
- Try primary first
- On HTTP error / filtered output / no images returned, fall through to fallback automatically
- Per-asset override flag for cases where the operator knows in advance which generator suits the brief (e.g., "this concept requires exactly 5 shapes — go straight to Imagen")

The chain choice is recorded in the spec doc with a side-by-side test that informed the decision. Future generator additions go through the same comparison. The chain insulates against model drift / API outages — when the primary model is deprecated or returns 404, work continues automatically (compare with the [Anthropic model-EOL incident response](2026-06-16_anthropic-model-eol-incident-response-three-phase-fix.md) pattern, which addresses the same drift problem at the LLM layer).

## How to Apply (Concrete Recipe)

1. **Create the brand spec doc** with both prose explanation and a fenced ` ```json ` block the script can parse. Capture palette, style, hard constraints, sanitizer rules, default generator chain.
2. **Refactor the asset-gen script** to: (a) load the brand spec, (b) sanitize the concept against the spec's rules, (c) wrap with spec's prefix + suffix, (d) dispatch to the generator chain, (e) auto-fallback on failure.
3. **Convert existing concept prompts** in source materials to concept-only style — strip the style boilerplate that the wrapper now adds, strip inline hex codes that the sanitizer would strip anyway.
4. **Document the failure mode → sanitizer rule mapping** every time a new bad-output pattern is observed. This is how the system improves over time without code changes.

## Worked Instance — client-project Brand Image System (2026-06-19)

- **Project**: client-project blog hero illustrations for a B2B SaaS measurement-instrument brand
- **Brand identity**: orange + navy on cream, minimalist editorial flat-vector style, no text/no human figures
- **Generator chain locked 2026-06-19**: FLUX Pro (`fal.ai`, `fal-ai/flux-pro`) primary for editorial vibe; Imagen 4 (Google, `imagen-4.0-generate-001`) fallback for literal shape counts
- **Sanitizer rules**: strip patterns for hex codes in parens and bare hex codes; warn words for `active`, `retired`, `labeled`, `tagged`; warn phrases for ` icon `, ` icons `, `icons of`
- **Spec doc**: `wiki/templates/brand-illustration-system.md` with JSON block for machine consumption
- **Script**: `scripts/gen-hero-image.py` with `load_brand_spec()`, `sanitize_concept()`, `apply_brand_wrapping()`, `build_final_prompt()`, generator dispatcher with primary+fallback
- **Test harness**: `scripts/test-image-generators.py` runs the same concept through all candidate generators side-by-side, saves with generator-name prefix to a test dir for visual comparison
- **Verified**: ran through 6 blog post hero images in a single session — 5/6 produced acceptable output on first generation; 1 needed per-asset generator override

### Specific failure modes discovered

- **FLUX consistently drifts on polygon counts** (pentagon → heptagon → star in successive runs; "5 bars" → 1 bar; "4 circles in square" → 4 circles but asymmetric)
- **Imagen 4 honors counts literally** but produces less editorially distinctive output
- **Both generators ignore "no text" instructions** when the prompt contains semantic categories (`active`/`retired`) or inline hex codes — hence the sanitizer

## Composes With

- The **demonstration-gap framework** (explained-never-shown) diagnostic: when a brand spec describes constraints but the system never enforces them, the explanation is decorative. The sanitizer layer is the enforcement of the spec's "known failure modes" section.
- [tracker-state-drift-at-session-boundary](../methodologies/2026-06-17_tracker-state-drift-at-session-boundary.md): each generated asset should be recorded in the tracker — concept, generator used, file path — or the workflow loses state at session boundaries.
- Workflow protocols that include asset generation as a discrete step (the brand asset system is the implementation of "Step 3: Generate hero images")
- [Lock LLM JSON output with explicit schema example](2026-06-16_lock-llm-json-output-with-explicit-schema-example.md) — same principle at the text-generation layer: the sanitizer + wrapper is the image-generation equivalent of schema-locking.

## Why This Is a Strong Transferable Framework

- The 4-layer separation (spec / sanitize / wrap / chain) is content-agnostic: it works for hero images, ad creatives, presentation slides, product screenshots, anywhere consistent brand output is needed
- The sanitizer layer is the part most teams skip — building it as a data structure (JSON in the spec, not hard-coded in script) lets operators extend it without engineering work
- The generator chain with auto-fallback insulates against model drift / API outages — when the primary model is deprecated or returns 404, work continues automatically
- The per-asset override (e.g., `--generator imagen` for shape-critical briefs) is the right escape hatch: defaults handle 80%, the override handles the 20% where the operator knows in advance which tool suits

## Anti-patterns This Prevents

- **Style boilerplate copy-pasted into every concept prompt** — drifts across operator sessions, becomes hand-edited per-asset.
- **Sanitizer rules buried in script comments** — invisible to next operator, lost on script rewrite.
- **Single hardcoded generator** — one API outage or model deprecation stops the workflow.
- **Manual post-generation brand touch-up** — the symptom that the spec layer is missing or unenforced.
