---
title: Ghost blog + Python-Markdown pipeline — enable pymdownx.magiclink for bare-URL autolink
source_mode: debugger
source_session: redacted
novelty_type: config_pattern
grounding_score: 0.90
staleness_risk: slow_decay
importance: 3
domain: patterns
topic: tooling
tags: [ghost-blog, python-markdown, tooling, url-linkification, content-pipeline]
created: 2026-07-06
pinned: false
related_entries: []
---

# Ghost blog + Python-Markdown pipeline — enable pymdownx.magiclink for bare-URL autolink

## Problem

When staging Ghost drafts from a markdown source (converted server-side via the Python `markdown` library), bare URLs like `semalytics.com/tools/foo/` render as plain text — no `<a>` tag. The reader sees a URL but can't click it.

## Root cause

The default Python-Markdown extension bundle (`extra`, `tables`, `fenced_code`, `sane_lists`, `nl2br`) does NOT include autolink. The CommonMark autolink `<url>` syntax requires explicit `<>` wrapping. Bare URLs stay as bare text. Operators must hand-wrap every URL in `[text](url)` syntax to get clickable links.

## Fix

Add `pymdownx.magiclink` (from the PyMdown Extensions package: `pip install pymdown-extensions`) to the extensions list.

```python
extensions = ["extra", "tables", "fenced_code", "sane_lists", "nl2br"]
try:
    import pymdownx.magiclink  # noqa: F401
    extensions.append("pymdownx.magiclink")
except ImportError:
    pass
return markdown.markdown(md, extensions=extensions, output_format="html5")
```

The try/except graceful fallback lets the pipeline work in environments where pymdownx isn't installed — links just stay bare rather than the pipeline breaking.

## Grounded example (client-project, 2026-07-06)

Two Ghost blog drafts staged with CTA line `→ semalytics.com/tools/ad-copy-analyzer/` (bare URL). Live post rendered the URL as plain text; reader saw the URL but couldn't click. Operator feedback: "Neither draft has links to anywhere else on the site. It has text urls but they are not linked."

After adding pymdownx.magiclink, bare URLs auto-linkify into `<a href="https://semalytics.com/tools/ad-copy-analyzer/">semalytics.com/tools/ad-copy-analyzer/</a>` at conversion time.

## Applies to

Any content pipeline that:

- Uses Python `markdown` library for HTML conversion
- Wants operators to write bare URLs (or shortcuts) without hand-wrapping every one in `[text](url)`
- Publishes to Ghost, static site generators, custom CMS backends, or any HTML-consumption platform

## Alternative approach (not implemented in this session)

Send raw markdown to Ghost via a Mobiledoc/Lexical `markdown` card structure. Ghost renders the markdown at display time using its own parser (which DOES autolink bare URLs by default). More work to implement (requires constructing Mobiledoc JSON with the markdown card) but bypasses the Python-Markdown extension question entirely and gives Ghost's parser full ownership of the render. Trade-off: less control over the intermediate HTML from the operator's side.

## Related caveats

- Ghost's admin editor iframe uses its own CSS and doesn't apply the site theme's link color rules. Bare URLs will render as clickable but may look unstyled (white/default) in the editor even when they'll render correctly (orange/underlined) on the live site or via the Preview URL. If the operator complains about "white on white" links in the admin editor view, verify with the Preview button (eye icon) which loads the theme CSS.
