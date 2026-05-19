---
title: sem-tools Google Ads Keyword Planner wrapper — canonical reference location + setup
source_mode: builder
novelty_type: template_candidate
grounding_score: 0.9
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-19
domain: integration
topic: seo-research
tags: google-ads, keyword-planner, seo-research, python-sdk, oauth, canonical-reference
related_entries: []
---

# sem-tools Google Ads Keyword Planner Wrapper — Canonical Reference Location + Setup

## Overview

The canonical Google Ads Keyword Planner API wrapper for David's environment lives at `~/Scripts/sem-tools/`, not at `~/Scripts/tuannw/` or `~/Scripts/tuan-dev/` (which reference it but do not contain the actual wrapper). This entry exists primarily to disambiguate the location and provide the invocation pattern for future SEO research tasks.

SEMrush was canceled in early 2026. sem-tools is the replacement for all keyword selection, competitive analysis, and content brief sizing work.

## Installation & Setup

### Location
```
~/Scripts/sem-tools/
├── .venv/                    # Virtual environment
├── .env                       # Credentials (NOT in git)
└── (source code)
```

### Dependencies
- `google-ads` Python SDK (pinned in `requirements.txt`)
- Python `>=3.9`

### Credentials Setup

Stored in `~/Scripts/sem-tools/.env`:
- `GOOGLE_DEVELOPER_TOKEN` — Google Ads API developer token
- `GOOGLE_OAUTH_REFRESH_TOKEN` — OAuth 2.0 refresh token
- `GOOGLE_CUSTOMER_ID` — Google Ads customer ID (typically 10 digits, dashes optional)

These are configured once and do not expire during normal use (refresh token auto-rotates).

## Canonical Invocation Pattern

From any project ([project], semalytics, etc.), run Python scripts using the venv:

```bash
~/Scripts/sem-tools/.venv/bin/python <your-script>.py
```

Or activate the venv first:
```bash
source ~/Scripts/sem-tools/.venv/bin/activate
python <your-script>.py
deactivate
```

### Code Example (from `cos/site/seo-research/check-keywords-seo-audit-page.py`)

```python
from google.ads.googleads.client import GoogleAdsClient

# Load credentials from .env
client = GoogleAdsClient.load_from_storage(
    version="v17",
    path_to_private_key_file=None,  # .env sets all vars
    env_path="~/Scripts/sem-tools/.env"
)

# Get Keyword Plan Idea Service
svc = client.get_service("KeywordPlanIdeaService")
req = client.get_type("GenerateKeywordHistoricalMetricsRequest")

# Configure request
req.customer_id = customer_id  # Must match GOOGLE_CUSTOMER_ID from .env
req.keywords = CANDIDATES  # list[str], typically 50-10k keywords
req.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
req.language = "languageConstants/1000"  # English
req.geo_target_constants.append("geoTargetConstants/2840")  # United States

# Execute
response = svc.generate_keyword_historical_metrics(request=req)
```

### Response Structure

Each keyword in the response includes:

```python
for idea in response.results:
    keyword_text = idea.keyword_idea.text
    metrics = idea.keyword_metrics
    # Available fields:
    # - monthly_search_volumes: list[MonthlySearchVolume]
    # - competition_level: LOW, MEDIUM, HIGH
    # - competition_index: 0-100 (relative competition, indexed)
    # - low_top_of_page_bid_micros: estimate in microcurrency
    # - high_top_of_page_bid_micros: estimate in microcurrency
```

Monthly search volumes are keyed by month/year; use the most recent 12 months for averages.

## When This Applies

- **SEO keyword research** — competitive analysis, volume estimates, bid-range guidance
- **Content brief generation** — sizing topics by search demand
- **Keyword selection for a new page or pillar** — validate demand before writing
- **Periodic audit of owned keywords** — track volume changes, competitive pressure

## When This Does NOT Apply

- Real-time keyword bidding or campaign creation (use Google Ads UI directly)
- Analysis requiring more than ~10k concurrent keywords (API has per-request limits; batch in chunks of 1k-2k)
- Searches in non-English languages (need different `language` constant; see Google Ads API docs)

## Error Handling Notes

### "Invalid API key" (401 UNAUTHENTICATED)
- Check `GOOGLE_OAUTH_REFRESH_TOKEN` in `.env` — may have expired or been invalidated
- Check `GOOGLE_DEVELOPER_TOKEN` — must be from the exact Google Ads account tied to the customer ID
- Check `GOOGLE_CUSTOMER_ID` — must match the Google Ads account that authorized the token

### "Resource not found" (404 INVALID_ARGUMENT)
- `customer_id` mismatch — ensure it matches `GOOGLE_CUSTOMER_ID` from `.env`
- Language constant invalid — validate against `languageConstants/` enum

### Request timeout or rate limiting
- Split keyword batches into chunks of 1k-2k
- Add 5-10 second pauses between requests if handling 10k+ keywords

## Common Gotchas

- **Don't hardcode the customer ID** — always read from `.env`
- **Monthly search volumes are indexed to 100 = highest month in timeframe** — not absolute counts
- **Competition level is categorical** (LOW/MEDIUM/HIGH), not numeric; use `competition_index` for finer sorting
- **Bid ranges are estimates** and vary by placement (top vs sidebar); interpret as ranges, not absolutes
- **`.env` is .gitignored** — never commit credentials; each dev/server gets its own copy

## Source Context

Entry created to disambiguate location after repeated confusion between `sem-tools/` (the actual wrapper), `tuannw/` (historical reference), and `tuan-dev/` (contains notes but not the wrapper). Wrapper is stable, grounding verified by active use in `cos/site/seo-research/check-keywords-seo-audit-page.py`. Saves 5-10 minutes per session locating the wrapper and prevents re-implementing the Google Ads OAuth dance.
