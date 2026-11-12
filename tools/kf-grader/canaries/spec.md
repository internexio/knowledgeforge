# Canary task: conversion reveal hook

Replace the dead-end copy in all five analyzers with the conversion hook.

```yaml kf-acceptance
acceptance_criteria:
  - id: AC1
    type: grep_count
    pattern: "r3-conversion-cta"
    paths: ["tools/*/analyzer.js"]
    per_file: true
    op: ">="
    value: 1
  - id: AC2
    type: grep_count
    pattern: "Try again tomorrow"
    paths: ["tools/*/analyzer.js"]
    per_file: true
    op: "=="
    value: 0
  - id: AC3
    type: command
    run: "sh tests/test_smoke.sh"
    expect: {exit_code: 0}
```
