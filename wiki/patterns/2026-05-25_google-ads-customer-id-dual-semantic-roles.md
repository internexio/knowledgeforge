---
title: Google Ads customer_id has dual semantic roles — auth context vs data context
source_mode: direct
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-05-25
domain: integration
topic: api-integration
tags: google-ads, api-integration, oauth, mcc, keyword-research, permissions, multi-tenant-patterns
related_entries: [infrastructure/2026-05-19_sem-tools-google-ads-keyword-planner-wrapper.md]
---

# Google Ads customer_id Has Dual Semantic Roles — Auth Context vs Data Context

When integrating Google Ads API, the `customer_id` field on a request serves **two fundamentally different roles** depending on the endpoint — and conflating them produces unnecessary PERMISSION_DENIED errors and needless MCC (Manager Account) header complexity.

## Pattern: Two Distinct customer_id Roles

### Role 1 — Auth/Billing Context (Public-Universe Endpoints)

For endpoints that query the **public keyword universe** (search volume, CPC, competition, keyword ideas), `customer_id` is used for:

- **Billing/quota attribution** — the account whose API quota gets consumed
- **Auth verification** — does this OAuth principal have access to ANY Google Ads account?
- **NOT for data access scoping** — the data returned is identical regardless of which `customer_id` you pass

Endpoints in this category:
- `KeywordPlanIdeaService.GenerateKeywordHistoricalMetrics`
- `KeywordPlanIdeaService.GenerateKeywordIdeas`
- (likely) `KeywordPlanService.GenerateForecastMetrics`
- (likely) any "public web data" endpoints

**Critical implication:** If your OAuth grant gives you direct access to ANY customer (e.g., your own primary account), you can use that `customer_id` for keyword research queries about ANY topic / brand / competitor — including queries that pertain to client accounts you don't have MCC access to. This sidesteps multi-tenant permission headaches.

### Role 2 — Data Access Context (Per-Account Endpoints)

For endpoints that query **a specific account's data** (campaigns, ad groups, performance metrics, conversion tracking, audiences), `customer_id` IS the data scope. The OAuth principal must have:

- Direct access to that customer, OR
- MCC manager access (in which case the `login-customer-id` header on the request must specify the manager's customer ID)

Endpoints in this category:
- `GoogleAdsService.Search` for `campaign`, `ad_group`, `keyword_view`, `conversion_action`, etc.
- All campaign-management writes
- All audience-management

For these endpoints, **you cannot sidestep the permission model** — you must have legitimate access to the account whose data you're querying.

## Concrete Grounding — 2026-05-25 sem-tools Restaurant Client Setup

**Context:** sem-tools tracks SEO/PPC for restaurant clients. The restaurants share a Google Ads customer_id of 2613868947 (MCC sub-account managed by an MCC the OAuth grant doesn't have access to). semalytics.com's own Google Ads account is at 5104372170, directly accessible by the OAuth grant.

**Failure case — initial interpretation:**

Calling `GenerateKeywordHistoricalMetrics` with `customer_id="2613868947"` (the restaurant client's account) returned:

```
Request made: ClientCustomerId: 2613868947, ... IsFault: True,
FaultMessage: User doesn't have permission to access customer.
Note: If you're accessing a client customer, the manager's customer
id must be set in the 'login-customer-id' header.
StatusCode.PERMISSION_DENIED, authorization_error: USER_PERMISSION_DENIED
```

Initial assumption: "We must obtain MCC manager_customer_id from the client, set up a `login-customer-id` header."

**Resolution — probing with a different customer_id:**

Calling the same endpoint with `customer_id="5104372170"` (semalytics's account, which we DO have direct access to) for the identical restaurant-vertical keywords:

```
keyword="lacabar"           vol=30      cpc=null  comp=LOW  trend=47mo
keyword="pho tacoma"        vol=1300    cpc=null  comp=LOW  trend=47mo
keyword="happy hour tacoma" vol=1300    cpc=null  comp=LOW  trend=47mo
```

**Result:** No permission error. Full 48-month historical trend data. The brand search volume for the restaurant client's brand visible in the response. The keyword data is identical to what the restaurant client would receive.

**Lesson:** `GenerateKeywordHistoricalMetrics` does not need client-specific `customer_id` for public keyword data. The Role 1 mechanism (auth verification + quota) is all that matters.

## Implementation Pattern

Maintain TWO customer_id concepts in configuration:

```python
class GoogleAdsConfig:
    # Used for keyword research endpoints (public-universe queries).
    # Should be any customer_id the OAuth grant has DIRECT access to.
    # Sidesteps MCC PERMISSION_DENIED for arbitrary topic queries.
    research_customer_id: str

    # Used for per-account data endpoints (campaigns, conversions).
    # Must match the customer whose data you want; requires MCC
    # login_customer_id header if accessed via a manager.
    login_customer_id: str  # the MCC, set on the client/header
    # per-domain customer_id is on the domain row, used at request time
```

In sem-tools, this wired as:

```python
research_customer_id = (
    self.config.google_ads.customer_id  # env-level, semalytics's
    or domain["google_ads_customer_id"]   # fallback to per-domain
)
results = client.get_keyword_metrics(
    keywords=batch, customer_id=research_customer_id,
)
```

The fallback allows per-domain override if needed, but the default is the org-level direct-access account.

## When This Applies

- Any multi-tenant SEO/PPC integration where Google Ads is queried across many client domains (agencies, SaaS platforms)
- Keyword research workflows on behalf of clients without direct MCC access to every client account
- Any keyword research that uses Google Ads as a free vendor instead of paid alternatives (SEMrush, DataForSEO)
- Disambiguation when a `PERMISSION_DENIED` error on a public-data endpoint makes you wonder if you need more permissions

## When This Does NOT Apply

- Pulling per-account performance metrics (campaign-level CTR, conversion counts, search-term reports) — these **require** the actual customer_id being queried, and MCC headers if the principal doesn't have direct access
- Writes (creating campaigns, updating bids) — same requirement
- Audience-management — same requirement
- Any endpoint that's explicitly documented as "scoped to a specific customer" — check Google Ads API reference; if it says "returns data for this customer", you need data access

## Related sem-tools Artifacts

- **sem-tools-kcr** (KeywordIntel routing) — updated 2026-05-25 to use `config.google_ads.customer_id` as research customer
- **sem-tools-ueg** (closed 2026-05-25) — pivoted away from DataForSEO Historical SERPs once this workaround unblocked Google Ads for restaurants
- **`.env` setting** `GOOGLE_ADS_CUSTOMER_ID=5104372170` (semalytics's direct account) — this is the research customer_id in our setup

## Connection to Module 22 (Semantic Wiki Search)

This entry disambiguates a **semantic API field** (`customer_id`) that has context-dependent meaning. Future Semantic Wiki Search should tag Role 1 vs Role 2 usage separately so queries like "which Google Ads endpoints can I call without client access?" return only the Role 1 ones.

## Source Context

Grounded in sem-tools-google-ads-mcc-sidestep session on 2026-05-25. Direct debugging of PERMISSION_DENIED errors while integrating Google Ads keyword research for multi-tenant restaurant client setup. The insight saves hours of implementation time by eliminating the need to chase MCC access for a problem that doesn't require it.
