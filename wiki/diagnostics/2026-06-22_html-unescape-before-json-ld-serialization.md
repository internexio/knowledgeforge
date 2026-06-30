---
title: HTML-unescape before JSON-LD serialization
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.8
staleness_risk: stable
importance: 3
pinned: false
created: 2026-06-22
domain: diagnostics
topic: data-integrity
tags: json-ld, schema-org, html-parsing, seo, gotcha
related_entries: []
---

# HTML-unescape before JSON-LD serialization

When you extract `<title>` or `<meta name="description">` content from HTML
and serialize it into JSON-LD (or any non-HTML JSON output), HTML entities
must be decoded FIRST. JSON-LD values are raw text, not HTML — Google's
parser, schema validators, and AI engines render entities literal.

Symptom: a page title like

    <title>Trust &amp; Security | SEMalytics</title>

becomes JSON-LD

    "name": "Trust &amp; Security | SEMalytics"

which renders to AI consumers as the literal string "Trust &amp; Security"
— not "Trust & Security". Google's Rich Results test will flag, AI Overviews
will reproduce the malformed text, and structured-data validators will warn.

Fix:

    import html
    name = html.unescape(re.search(r'<title>(.+?)</title>', src, re.DOTALL).group(1).strip())

Apply to: title, description, and any other HTML-sourced text destined for
a JSON string value.

Edge cases worth handling: numeric entities (`&#x27;`, `&#38;`),
named entities beyond &amp; (`&lt;`, `&gt;`, `&quot;`, `&apos;`,
`&nbsp;`, `&copy;`), and the rare case of mixed-encoding pages.
`html.unescape` handles all standard cases.

## When This Applies

Any code that extracts HTML-attribute or HTML-content text and emits JSON,
YAML, plain-text logs, or anything that doesn't itself decode entities.
Most common surfaces:

- WebPage / Article / Product JSON-LD `name`, `description`, `headline`
- Open Graph and Twitter card meta extracted from HTML and re-emitted as JSON
- Sitemap generators that pull titles from rendered HTML
- Log lines that capture page titles for analytics
- LLM-bound context payloads that include HTML-sourced strings

## When This Does NOT Apply

HTML-to-HTML transformations (the entities remain valid in the target
context). If the destination renders HTML, leave the entities intact —
unescaping there would produce double-encoded or broken markup.

## Source Context

Grounding: cos-1wp1 sweep (2026-06-22 [project]). Wrote a script to inject
WebPage JSON-LD into 96 static HTML pages, extracting `name` from
`<title>`. Two pages had `&amp;` in the title (the team page with
"Founder &amp; CEO" and trust/index.html with "Trust &amp; Security").
The JSON-LD shipped with `"name": "Founder &amp; CEO"` until caught by a
follow-up grep. Patched the script with `html.unescape()` and surgically
fixed both pages.
