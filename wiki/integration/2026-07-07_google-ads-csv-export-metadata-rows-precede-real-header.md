---
title: Google Ads CSV export header detection — metadata rows precede the real header
source_mode: debugger, builder
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-07
domain: integration
topic: external-tools
tags: api, classification, error-handling, data-validation, empirical
related_entries: [infrastructure/2026-05-19_sem-tools-google-ads-keyword-planner-wrapper.md, patterns/2026-05-25_google-ads-customer-id-dual-semantic-roles.md]
---

# Google Ads CSV Export: Metadata Rows Precede the Real Column Header

## The Issue

Google Ads UI exports (downloaded via Reports → Keywords → Download) prepend several metadata rows before the actual column header row. A CSV parser that assumes "first non-blank row = header" will silently return zero results because it reads the metadata row (e.g. "Google Ads") as the header, finds no "Keyword" column, and returns an empty dataset.

## Exact Format of a Google Ads UI Keyword Export

```
"Google Ads",,,,,,,,,,
"",,,,,,,,,,
"Account","Date range","Account currency",,,,
"My Account Name","Jan 1 – Dec 31 2024","USD",,,,
"",,,,,,,,,,
"Campaign","Ad group","Keyword","Match type","Keyword state","Max. CPC",...
"Campaign A","Ad Group 1","running shoes","Broad","Enabled","$1.20",...
...data rows...
"",,,,,,,,,,
"Total","","","","","$X",...
```

Key observations:
- Lines 1–5 are metadata (account name, date range, currency)
- Line 6 is the actual header with "Campaign", "Ad group", "Keyword", "Match type", etc.
- Last row is a "Total" summary row that is NOT prefixed with `#` or `--`

## The Bug Pattern

Any parser written like this fails:

```js
// WRONG: takes the first non-blank row
for (let i = 0; i < lines.length; i++) {
  if (!lines[i] || /^[#\-]{2}/.test(lines[i])) continue;
  headerIdx = i;  // picks up "Google Ads" metadata row
  break;
}
```

This assumes the first non-comment row is always the header. With metadata rows, the parser selects line 0 instead of line 5, looks for a "Keyword" column in the metadata, finds nothing, and returns zero results.

## The Fix

Scan every row looking for one that actually contains a keyword-like column header:

```js
// CORRECT: find the row containing a keyword-like column
const COL_KEYWORD = ['keyword', 'keyword text', 'search term', 'keyword or phrase'];
const normaliseHeader = h => h.toLowerCase().trim().replace(/[""„‟""'`]/g, '').trim();

let headerIdx = -1;
for (let i = 0; i < lines.length; i++) {
  if (!lines[i] || /^[#\-]{2}/.test(lines[i])) continue;
  const fields = parseCsvRow(lines[i]).map(normaliseHeader);
  if (fields.some(h => COL_KEYWORD.includes(h))) {
    headerIdx = i;
    break;
  }
}
```

Also handle the summary row at the bottom:

```js
const SUMMARY_CELLS = new Set(['total', 'all campaigns', 'all ad groups', 'search term']);
// Inside data row loop:
if (SUMMARY_CELLS.has(keyword.toLowerCase())) continue;
```

## Additional Format Issues to Handle

- **UTF-8 BOM**: Strip with `text.replace(/^﻿/, '')` or `text.replace(/^﻿/, '')`
- **Windows line endings**: Split on `/\r?\n/` not just `\n`
- **Curly/smart quotes** in Excel-saved CSVs: Strip `"`, `"`, `„`, `‟` from header cells (as shown in `normaliseHeader` above)
- **Google Ads Editor exports**: Cleaner format, starts directly with headers — the fix handles both since it still scans for the keyword column

## Applicability

### When This Applies

- Any project that accepts Google Ads keyword exports as CSV input (e.g., keyword audit tools, SEM/SEO analysis platforms)
- Any CSV parser built against "clean" CSVs that later encounters Google Ads / Excel exports
- Also applicable to other Google products (Google Analytics, Google Search Console exports) which follow similar metadata-prepend patterns

### When This Does NOT Apply

- Google Ads API responses (JSON, not CSV)
- Google Ads Editor bulk exports (cleaner format but the fix still works harmlessly)
- Third-party tool exports (SEMrush, Ahrefs) which have their own header conventions
- Hand-curated CSV files with explicit header rows

## Grounding

Diagnosed and fixed in **keywordplannertools** (July 2026). User uploaded a real Google Ads account export; parser returned zero keywords despite the export containing valid keyword data. Root cause confirmed by direct inspection of the export format and payload tracing. Fix deployed and verified to correctly identify the header row on both Google Ads UI exports and Google Ads Editor exports.

## Source Context

Debugger mode: identified parser hang during keywordplannertools CSV parser testing. Builder mode: implemented the column-scan fix and tested against multiple export formats. Session `keywordplannertools-csv-parser-fix`, 2026-07-07.

## Related Entries

- `infrastructure/2026-05-19_sem-tools-google-ads-keyword-planner-wrapper.md` — canonical Google Ads integration reference for keyword research
- `patterns/2026-05-25_google-ads-customer-id-dual-semantic-roles.md` — Google Ads API authentication and data-scoping patterns
