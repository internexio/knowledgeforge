---
title: Google Rich Results SoftwareApplication schema requirements — price string and SearchAction format
source_mode: builder
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-14
domain: integration
topic: schema-org-validation
tags: seo, structured-data, schema-org, gotcha, google
related_entries: [2026-06-22_html-unescape-before-json-ld-serialization.md]
---

# Google Rich Results SoftwareApplication Schema Requirements — Price String and SearchAction Format

Two commonly wrong patterns in SoftwareApplication JSON-LD schema that Google's Rich Results validator flags as errors. Both are gotchas in the canonical schema.org spec that trip static-HTML authors and programmatic generators.

## SoftwareApplication: `offers.price` must be a string, not a number

**WRONG (numeric price):**

```json
{
  "@type": "SoftwareApplication",
  "offers": {
    "@type": "Offer",
    "price": 0,
    "priceCurrency": "USD"
  }
}
```

**CORRECT (string price):**

```json
{
  "@type": "SoftwareApplication",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  }
}
```

**Why:** schema.org's `schema:price` property accepts `Text` values, not `Number`. Google's Rich Results validator for SoftwareApplication strictly enforces string type even for `0` (free tier pricing). Numeric `0` returns a "price must be a string" validation error. The spec is stricter on SoftwareApplication than on other types (e.g., Product is more lenient).

---

## WebSite: `SearchAction.query-input` must be a PropertyValueSpecification object, not a string

**WRONG (deprecated old Google-specific format):**

```json
{
  "@type": "SearchAction",
  "target": "https://example.com/search?q={search_term_string}",
  "query-input": "required name=search_term_string"
}
```

**CORRECT (standard schema.org PropertyValueSpecification):**

```json
{
  "@type": "SearchAction",
  "target": {
    "@type": "EntryPoint",
    "urlTemplate": "https://example.com/search?q={search_term_string}"
  },
  "query-input": {
    "@type": "PropertyValueSpecification",
    "valueRequired": true,
    "valueName": "search_term_string"
  }
}
```

**Why:** The string format `"required name=search_term_string"` was a Google-specific annotation that predates the standard schema.org `PropertyValueSpecification` type. This pattern was deprecated by Google in favor of the standard schema.org spec. Google's Rich Results validator now rejects the string format and requires the `PropertyValueSpecification` object with explicit `valueRequired` and `valueName` fields. The `target` also becomes an `EntryPoint` object rather than a bare URL string.

---

## How to Fix at Scale (Python)

```python
import json, re

def fix_json_schema(match):
    raw = match.group(1)
    try:
        data = json.loads(raw)
        modified = False
        
        # Fix SoftwareApplication price
        if data.get('@type') == 'SoftwareApplication':
            offers = data.get('offers', {})
            if isinstance(offers.get('price'), (int, float)):
                offers['price'] = str(int(offers['price']))
                data['offers'] = offers
                modified = True
        
        # Fix WebSite SearchAction query-input
        if '@graph' in data:
            for item in data['@graph']:
                if item.get('@type') == 'WebSite':
                    for action in item.get('potentialAction', []):
                        if action.get('@type') == 'SearchAction':
                            old_qi = action.get('query-input', '')
                            if isinstance(old_qi, str) and 'required name=' in old_qi:
                                val_name = old_qi.replace('required name=', '').strip()
                                action['query-input'] = {
                                    '@type': 'PropertyValueSpecification',
                                    'valueRequired': True,
                                    'valueName': val_name
                                }
                                modified = True
        
        if modified:
            return f'<script type="application/ld+json">{json.dumps(data, indent=2)}</script>'
    except:
        pass
    return match.group(0)

# Apply to HTML content
content = re.sub(
    r'<script type=["\']application/ld\+json["\']>(.*?)</script>',
    fix_json_schema,
    content,
    flags=re.DOTALL
)
```

**Usage notes:**
- Regex targets `<script type="application/ld+json">` blocks and extracts their JSON payload
- Handles both single-schema and `@graph` (multi-schema) documents
- Silently passes unmatched JSON through unchanged
- Apply idempotently across HTML files (safe to re-run on already-fixed pages)

---

## When This Applies

- Static HTML pages with manually authored JSON-LD schemas
- Any SoftwareApplication schema with a numeric price (including free tiers where price is `0`)
- Any WebSite schema using the old string `query-input` format in SearchAction
- Mass fixes across tool product pages, pricing pages, or documentation
- Pages built by template engines that assemble JSON-LD from price or search-action fields

---

## When This Does NOT Apply

- Schemas generated by CMS plugins that are already standards-compliant (Yoast, Rank Math, etc.)
- Schemas where price is already a string
- Cases where SearchAction `query-input` is already a PropertyValueSpecification object
- Pages where the schema structure diverges significantly from these two patterns

---

## Source Context

Discovered during semalytics.com SEO remediation (Jul 2026). A crawl audit tool flagged 10 tool pages and 1 pricing page (169 total rows) with "Google rich results validation error" for SoftwareApplication and WebSite schemas. Root cause analysis via live page JSON-LD inspection confirmed:
- **SoftwareApplication price error:** 10 pages with numeric `price: 0`
- **SearchAction query-input error:** 11 static HTML files using deprecated string format

Fixed with the Python regex approach above across 11 static HTML files. Verified live via `curl https://example.com/page | python3 -c "import sys, json, re; match = re.search(r'...')" to extract and validate post-fix JSON-LD.

Related: `2026-06-22_html-unescape-before-json-ld-serialization.md` covers entity handling in JSON-LD values. This entry complements that with schema-validation format requirements.
