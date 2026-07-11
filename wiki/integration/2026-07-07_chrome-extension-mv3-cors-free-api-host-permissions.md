---
title: Chrome Extension MV3: CORS-free API calls via host_permissions in background service worker
source_mode: builder
novelty_type: new_pattern
grounding_score: 0.90
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-07
domain: integration
topic: external-tools
tags: api, empirical
related_entries: []
revises: null
superseded_by: null
---

# Chrome Extension MV3: CORS-free API calls via host_permissions in background service worker

## Pattern: CORS-free API calls from a Chrome Extension background service worker

### What it is

In Chrome Extension Manifest V3, adding the target API's origin to `host_permissions` in manifest.json causes Chrome to bypass CORS enforcement for fetch calls made from the background service worker. No proxy server, no relay, no server-side CORS header changes needed.

### When it applies

- Building a Chrome Extension (MV3) that needs to call a first-party or third-party REST API from the background service worker
- The extension owns or has API access to the target service (so CORS bypass is intentional, not a workaround for hostile third parties)
- You want to avoid proxy infrastructure and keep the extension self-contained

### When it does NOT apply

- Content scripts (injected into web pages) — host_permissions alone does not bypass CORS for content scripts; message routing through the background worker is still needed
- Firefox/Safari WebExtensions — the host_permissions CORS bypass behaviour is Chrome-specific
- Cases where you do NOT control the target API and CORS bypass would violate ToS

### Implementation

In manifest.json:
```json
{
  "manifest_version": 3,
  "host_permissions": ["https://your-api.example.com/*"],
  "background": { "service_worker": "background/service-worker.js" }
}
```

In service-worker.js — plain fetch, no special headers needed:
```javascript
const res = await fetch("https://your-api.example.com/api/endpoint", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${apiKey}`
  },
  body: JSON.stringify(payload)
});
```

No `Access-Control-Allow-Origin` header on the server, no proxy, no relay. Chrome treats background service workers with matching host_permissions as trusted callers.

### Why content scripts still need message passing

Content scripts run in the web page context where normal CORS rules apply. The pattern is: content script → chrome.runtime.sendMessage → background service worker → fetch (CORS-bypassed) → response back to content script.

### Additional: do NOT add the "tabs" permission for API access

The "tabs" permission triggers a permission warning during extension install ("Read your browsing history"). It does not help with CORS. Use activeTab + host_permissions instead.

## When This Applies

- Building a Chrome Extension (MV3) that makes API calls from the background service worker to a known origin
- You control or have authorized access to the target API
- You want to avoid proxy relay infrastructure

## When This Does NOT Apply

- Content scripts — CORS still applies; must message through background worker
- Firefox/Safari WebExtensions — Chrome-specific feature
- APIs you don't control or where CORS bypass violates terms of service
- MV2 extensions — the mechanism is the same but MV2 uses different background script model

## Grounding

Verified in cos-browser-analyzer build (2026-07-07): background/service-worker.js calls POST /api/analyze/full on semalytics.com with host_permissions: ["https://semalytics.com/*"]. Extension loads and API calls succeed without any CORS errors or proxy infrastructure. CLAUDE.md in cos-browser-analyzer documents this explicitly.

## Anti-patterns

- Adding "tabs" permission instead — install warning, doesn't help CORS
- Proxy infrastructure — unnecessary when host_permissions suffices
- Calling the API from content scripts directly — CORS blocks these

## Source Context

Discovered during Chrome extension build for cos-browser-analyzer (2026-07-07). The extension needed to call the COS backend API from a background service worker without a proxy relay. Adding the target origin to host_permissions in manifest.json was sufficient to bypass CORS enforcement entirely — Chrome's trust model for background workers with matching host_permissions allows direct API access. Grounding: working code in cos-browser-analyzer extension; 0.90 confidence reflects direct implementation + successful API calls from service worker without CORS errors or server-side workarounds.
