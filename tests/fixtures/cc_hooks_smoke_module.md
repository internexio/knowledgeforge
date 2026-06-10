# Smoke Test Module — cc_hooks + cc_rules emitter

## Module Metadata

```yaml
module:
  title: cc_hooks/cc_rules smoke fixture
  version: 0.1.0
  purpose: |
    Synthetic fixture exercising the Phase 2 cc emitter pipeline.
    Used by tests/compiler/test_phase2_emitters.py (or manual verification)
    to confirm that emit_cc_rules_for_module and emit_settings_fragment
    produce the expected output shapes.
  topics: [test-fixture]
  contexts: [compiler-testing]
  difficulty: trivial
  related: []

cc_rules:
  - filename: smoke-typescript-imports.md
    paths:
      - "**/*.{ts,tsx}"
    body_section: "CC Rules — TypeScript imports"

  - filename: smoke-debugger-wiki-conventions.md
    paths:
      - "wiki/diagnostics/**/*.md"
    body_section: "CC Rules — Debugger wiki conventions"

cc_hooks:
  - hook_event: PreToolUse
    type: command
    command: "scripts/kf-hooks/smoke-assert-tests-passed.sh"
    matcher:
      tools: ["Bash"]
      pattern: "git commit"
    source_rule: "smoke-debugger-wiki-conventions"
```

---

## Core Approach

This fixture exists solely to exercise the cc_rules and cc_hooks emitter pipeline
under controlled conditions. It is NOT a KnowledgeForge module — it is a smoke
test artifact. It should never appear in a real binding's `module_outputs`.

---

## CC Rules — TypeScript imports

- Imports must be at the top of the file, before any non-import statements
- Side-effect-only imports (e.g., polyfills) are permitted; they sit immediately
  above named imports
- Type imports use `import type { ... }` syntax to support tree-shaking

---

## CC Rules — Debugger wiki conventions

When filing a Debugger diagnostic to `wiki/diagnostics/`:
- Filename pattern: `YYYY-MM-DD_<slug>.md`
- Title is the symptom, not the root cause
- Body opens with reproduction, then root cause, then fix

## CC Doc

End-of-file CC marker to bound the preceding CC Rules section.
Convention: cc_rules sections must be clustered with other CC sections
(CC Skill / CC Doc / CC Agent / CC Rules — X) with no intervening
non-CC `##` headings. The existing `extract_section()` in kf-compile.py
stops only at the next CC marker; non-CC headings between cc_rules
entries cause over-extraction.
