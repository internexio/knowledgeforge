---
title: plistlib vs plutil — strict vs lenient XML parsing of `--` in launchd plist comments
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: stable
importance: 3
pinned: false
created: 2026-06-13
domain: infrastructure
topic: server-configuration
tags: stable, empirical, quality-gate, filesystem, scheduling
related_entries: ["infrastructure/2026-06-10_launchd-subprocess-shell-alias-resolution-gotcha.md", "infrastructure/2026-05-13_launchd-cwd-trap-relative-tool-lookups.md", "methodologies/2026-06-10_canary-test-ai-coder-config-auto-load-conventions.md"]
---

# plistlib vs plutil — Strict vs Lenient XML Parsing of `--` in launchd Plist Comments

## Finding

macOS's `plutil -lint` and Python's `plistlib.load()` use different XML parsers with different strictness levels. A `.plist` file can pass `plutil -lint` while crashing `plistlib` with `xml.parsers.expat.ExpatError: not well-formed (invalid token)`.

The most common cause: the literal sequence `--` (double hyphen) appears inside an XML comment `<!-- ... -->`. Per the XML 1.0 spec, `--` is reserved inside comments — the parser sees `--` and expects `-->` to close the comment, and fails if the next chars are anything else.

## Concrete Grounding

Observed 2026-06-13 in `~/Library/LaunchAgents/com.[project].iteration-loop-exec-consumer.plist` on the laptop. The plist's docstring comment contained the literal phrase `one-shot \`claude --print\` Claude Code subprocess`, putting `--print` inside the `<!-- ... -->` block.

Behavior:
```
$ plutil -lint ~/Library/LaunchAgents/com.[project].iteration-loop-exec-consumer.plist
... : OK

$ python3 -c "import plistlib; plistlib.load(open('.../same-file', 'rb'))"
xml.parsers.expat.ExpatError: not well-formed (invalid token): line 8, column 61
```

Both parsers were inspecting the same file. `plutil` is Apple's lenient parser that accepts the file; `plistlib` uses expat (strict XML) which rejects it. The launchd runtime itself uses Apple's parser, so the plist still works at runtime — the failure is purely in tooling that uses `plistlib`.

## When This Applies

- Any Python tool that programmatically reads, validates, or rewrites macOS plist files (e.g. install scripts, manifest renderers, lint checks, plist inventory tools).
- Specifically watch hand-written launchd plists where the comment header describes the command being launched and the command takes `--flag` args (`--print`, `--config`, `--once`, `--no-cache`, ...). The flags get documented in the comment, and the `--` triggers the parse error.
- Any plist-reading code that works on a developer's machine but fails in a CI pipeline or automated validation script — the strictness divergence is almost always the culprit.

## When This Does NOT Apply

- `plutil -lint` is not affected — uses Apple's parser.
- launchd runtime itself is not affected — also Apple's parser.
- plist files generated programmatically (e.g. rendered by a templating installer with no source comments) almost never trip this — generators don't emit `--` inside comments.
- Plist files that contain no XML comments (rare for launchd plists, which conventionally document their purpose).

## Fix Patterns

1. **Rewrite the offending comment to avoid `--`.** E.g. change `--print` to `-\-print` or `--print` → `'print' flag` in prose. Cheap, works immediately.
2. **If you control the plist generator** (e.g. a manifest-driven installer), ensure the renderer either strips source comments or escapes `--` in any comment it preserves.
3. **As a workaround in tooling:** shell out to `plutil -convert xml1 -o - <file>` to round-trip through Apple's parser, then feed the cleaned output to plistlib. Works but is slow per-file.

## Diagnostic Verification

```bash
# Two-step verification: Apple's lenient parser vs expat strict parser

plutil -lint <file>      # Apple's lenient parser — if this passes, file is valid at runtime
python3 -c "import plistlib; plistlib.load(open('<file>','rb'))"  # expat strict — may fail

# If the two diverge on the same file:
# 1. Search for comment lines containing `--` not at the closing
grep -nE '<!--.*--.*-->' <file>

# 2. Inspect the matching lines for `--flag` patterns or other XML-reserved-in-comments sequences
# 3. Rewrite the comment to avoid the reserved sequence
```

## Root Cause

XML 1.0 spec reserves `--` for comment delimiters. Per section 2.5:

> Comments may appear anywhere in a document outside other markup.

The sequence `--` is historically a comment-delimiter lookahead and triggers early-termination on strict parsers. Apple's plutil relaxes this constraint; expat (used by Python's plistlib) enforces it. Both are "correct" under different interpretations of the XML spec.

## Source Context

Discovered 2026-06-13 during [project] ajyo sub-task 3 (manifest schedule fills). The iteration-loop-exec-consumer LaunchAgent's plist contained a docstring comment about the `claude --print` subprocess, and the `--print` flag triggered an ExpatError when the [project] morning-brief script tried to programmatically validate the plist via plistlib. The plist was valid at runtime (launchd doesn't parse it that way), but tooling that reads plists must expect this divergence.
