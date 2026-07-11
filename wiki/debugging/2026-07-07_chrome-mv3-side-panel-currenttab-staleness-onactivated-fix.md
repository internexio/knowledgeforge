---
title: Chrome MV3 Side Panel — currentTab Staleness and the onActivated Fix
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-07
domain: debugging
topic: root-cause-analysis
tags: api, routing, grounding, quality-gate
related_entries: []
---

# Chrome MV3 Side Panel — currentTab Staleness and the onActivated Fix

## Problem

Chrome MV3 side panels initialize with a single snapshot of the active tab, captured in a `DOMContentLoaded` handler:

```js
document.addEventListener("DOMContentLoaded", async () => {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  currentTab = tabs[0];   // stale after any tab switch
  await refreshIdleState();
  // ... wire buttons
});
```

`currentTab` is never updated after initialization. When the user switches tabs while the panel stays open, all subsequent operations (`chrome.tabs.sendMessage`, any tab-scoped API) silently target the wrong tab. The panel appears to work but analyzes or manipulates stale content from the original tab.

The bug is **silent** — no error messages, no console warnings. `chrome.tabs.sendMessage` succeeds to the wrong (but valid) tab ID, so the failure surface is strictly semantic: the wrong page gets analyzed.

## Detection Signal

- Analysis result (e.g., "Analyze Page" button) runs successfully but returns content clearly from a different tab than the one currently visible in the browser
- No error in the console — `chrome.tabs.sendMessage` to the stale tab ID succeeds silently
- Clicking the same button on a different tab after switching doesn't re-fetch from the new tab

## Root Cause

Side panels persist per-window, not per-tab (by default). A side panel stays open when the user navigates between tabs. The initial `DOMContentLoaded` queries the currently active tab once. Without an event listener for tab switches, the cached `currentTab` reference is never refreshed.

The Chrome `tabs.onActivated` event fires whenever the user clicks a different tab in the same window. This event supplies `tabId` and `windowId`. The fix is to listen for this event and update the cached tab reference.

## Fix

Add a `chrome.tabs.onActivated` listener immediately after the `DOMContentLoaded` block:

```js
chrome.tabs.onActivated.addListener(async ({ tabId }) => {
  currentTab = { id: tabId };
  await refreshIdleState(); // re-fetch page context for the new tab
});
```

**Key details:**

- Only `tabId` and `windowId` are needed from the event — `onActivated` provides these unconditionally without requiring `"tabs"` permission (which would trigger scary install warnings)
- `currentTab` need only carry `{ id }` since downstream code (e.g., `chrome.tabs.sendMessage(currentTab.id, ...)`) uses only the ID
- `chrome.tabs.query` returns a full tab object, but the cached reference can be minimal
- The listener should call `refreshIdleState()` or equivalent to re-establish page context (DOM extraction, platform detection, etc.) for the newly active tab

## When This Applies

- Any MV3 extension with a persistent side panel (Chrome 116+, using `chrome.sidePanel` API)
- The panel stays open across tab switches (side panels persist per-window by default; no explicit per-tab binding)
- Page content (text, title, platform detection) is tab-specific and must be re-fetched when focus shifts

## When This Does NOT Apply

- **Popup extensions** — popups close on tab switch, so `currentTab` is always fresh when the popup opens
- **Background service workers** — these don't hold a per-window `currentTab` reference in the UI context
- **Extensions that explicitly bind the panel to a specific tab** — via `chrome.sidePanel.setOptions({ tabId: specificTabId })`, in which case the panel itself closes or disables when that tab closes
- **Extensions that don't need tab-specific state** — for example, settings or global-search panels that don't analyze page content

## Verification

The bug was surfaced and fixed in the cos-browser-analyzer extension (bead `cos-browser-analyzer-3wt`, 2026-07-08). Symptoms before the fix:
- Opened the COS Analyzer side panel
- Clicked "Analyze Page" on a LinkedIn post → got a score for the post
- Switched to a different tab (e.g., Twitter) and clicked "Analyze Page" → got the same score as the LinkedIn post (analyzing stale content)
- Fix applied: added the `onActivated` listener
- Switched tabs again and clicked "Analyze Page" → correctly analyzed the new tab's content

## When This Does NOT Apply

(See section above for non-applicable scenarios.)

## Source Context

Debugged during extension wiring and initialization for cos-browser-analyzer (Source mode: debugger → builder; Session: cos-browser-analyzer-extension-wiring). The bug would have remained latent during single-tab usage but surfaced immediately in real-world multi-tab browsing. User-facing symptom: "Why does the extension analyze the wrong page?"
