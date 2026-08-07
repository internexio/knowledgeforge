---
title: KF-MODE telemetry marker client-side parsing for UI enrichment
source_mode: builder
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.87
staleness_risk: stable
importance: 3
created: 2026-07-11
domain: integration
topic: streaming-ui-enrichment
tags: [kf-vscode, telemetry, streaming, webview, ui-enrichment]
related_entries:
  - compiler/2026-07-11_kf-mode-marker-must-land-in-first-20-lines-compiled-agent-files.md
pinned: false
---

# KF-MODE Telemetry Marker Client-Side Parsing for UI Enrichment

## Pattern: KF-MODE Marker Client-Side Parsing for UI Enrichment

### What it is

The KF response telemetry marker (`<!-- KF-MODE: <mode> | DECISION: <class> | ADVERSARIAL: <0|1> -->`) is embedded in every KF assistant response. In the kf-vscode extension, this marker is parsed on the client side (in the webview's `panel.js`) to drive two UI enrichments:

1. **Decision type badges** — each finalized chain pill shows a colored badge (reckoning/evaluative/predictive/novel)
2. **Adversarial findings auto-detection** — when `ADVERSARIAL:1` is present, the response text is scanned for `[HIGH]`/`[CRITICAL]`/`[MEDIUM]`/`[SEV1]`/`[SEV2]` patterns and surfaced in the findings panel

### Implementation (panel.js)

```javascript
// Parse the LAST KF-MODE marker in the response (most recent/relevant)
function parseKFMarker(text) {
  const re = /<!--\s*KF-MODE:\s*([\w,\s]+?)\s*\|\s*DECISION:\s*(\w+)(?:\s*\|\s*ADVERSARIAL:\s*(\d))?[^>]*-->/gi;
  let last = null;
  let m;
  while ((m = re.exec(text)) !== null) last = m;
  if (!last) return null;
  return {
    modes: last[1].split(',').map((s) => s.trim().toLowerCase()),
    decision: last[2].toLowerCase(),
    adversarial: last[3] === '1',
  };
}

// Call on stream:end
const marker = parseKFMarker(msg.fullText);
finalizeChainPill(msg.mode, msg.durationMs, marker?.decision ?? null);
if (marker?.adversarial) {
  const findings = parseFindings(msg.fullText);
  if (findings.length > 0) renderFindings(findings);
}
```

### Key decisions

- **Parse the LAST marker**: a multi-step response may have multiple KF-MODE markers (one per step). The last one reflects the most recently completed reasoning step.
- **Client-side, not server-side**: server doesn't need to parse its own output; keeps routes clean
- **Adversarial findings parsed on demand**: only scan for `[HIGH]`/`[CRITICAL]` patterns when the marker explicitly signals adversarial ran — avoids false positives on normal response text

### Adversarial findings parser

```javascript
function parseFindings(text) {
  const findings = [];
  const re = /\[(CRITICAL|HIGH|MEDIUM|SEV[- ]?[12])\][:\s]+([^\n]+)/gi;
  let m;
  while ((m = re.exec(text)) !== null) {
    const tag = m[1].toUpperCase().replace(/[- ]/g, '');
    const severity = (tag === 'CRITICAL' || tag === 'HIGH' || tag === 'SEV1') ? 'high' : 'medium';
    findings.push({ severity, message: m[2].trim() });
  }
  return findings;
}
```

## When This Applies

- Any client (webview, browser, desktop) consuming KF streaming output that wants to show per-step decision metadata
- Works on the `fullText` (complete response) — not on streaming deltas
- Requires KF instrumentation to be active (KF-MODE markers must be present in responses)
- Multi-step chains where decision classification varies per step — client needs to surface the final classification

## When This Does NOT Apply

- Real-time per-token enrichment (markers only appear at the END of the response)
- Clients consuming raw Anthropic API output without KF system prompts (no markers present)
- Server-side extraction (no benefit over client-side; adds server complexity for no gain)
- Single-decision responses where client doesn't care about classification granularity

## Grounding

Implemented in kf-vscode `src/webview/panel.js` (commit 0a93f43). Typechecked and built clean. Tested flow: stream:end fires → parseKFMarker called on fullText → decision badge appears on chain pill.

## Source Context

Generated during kf-vscode phase 3 chain-visualization feature development. The pattern emerged when designing UI surfaces for streaming KF responses that need decision-type badges and findings highlights. Grounding: live implementation in kf-vscode, verified working on local builds.
