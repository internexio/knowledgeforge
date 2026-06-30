---
title: Chrome MCP automation of React composers — Enter-to-send and onChange traps
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-05-18
tags: chrome-mcp, e2e-testing, react, automation, empirical, integration-pitfall
related_entries: []
domain: diagnostics
topic: testing
---

# Chrome MCP automation of React composers — Enter-to-send and onChange traps

## What this is

Two related testing-tool gotchas hit when automating any React chat
composer (or any input with "Enter to send · Shift+Enter for newline"
UX) using Chrome MCP — or, equivalently, Playwright fill() / Puppeteer
type() against React-controlled components.

## Trap 1: type_text with bare \n submits mid-message

Chrome MCP's `type_text` (and Playwright's `keyboard.type`, Puppeteer's
`page.keyboard.type`) emits literal keypresses for each character. A
`\n` in your input string fires Enter — which is exactly what most
chat composers interpret as "send."

Symptom: a multi-line prompt gets chopped at the first newline. The first
segment submits as a message; subsequent text lands in the now-empty
composer (or worse, fragments across multiple half-messages).

Workarounds:
1. Strip or replace newlines before typing (single-line input only).
2. Use a "set value + dispatch input event" path via evaluate_script
   instead of typed keystrokes.
3. If the UI offers a button click to submit, click that instead of
   relying on Enter — but check for keydown handlers that fire on
   Enter anyway.

## Trap 2: fill() / setting .value doesn't fire React's onChange

React-controlled inputs read from state, not the DOM. Setting the DOM's
`.value` directly bypasses the React state update — the input visually
shows the new text, but the "Send" button stays disabled because React
never received an `onChange` event.

Symptom: text appears in the textarea, but the submit button stays
disabled OR the submitted message is empty / stale.

Workaround (works for React 16/17/18 controlled inputs):

```javascript
(el) => {
  const ta = el.tagName === 'TEXTAREA' ? el : el.querySelector('textarea');
  if (!ta) return { ok: false };
  const setter = Object.getOwnPropertyDescriptor(
    window.HTMLTextAreaElement.prototype, 'value'
  ).set;
  setter.call(ta, 'my message here');
  ta.dispatchEvent(new Event('input', { bubbles: true }));
  return { ok: true, length: ta.value.length };
}
```

Invoke via Chrome MCP's `evaluate_script` (or Playwright's
`page.evaluate`). The native setter + bubbling 'input' event together
make React see the change.

Same pattern works for `<input>` — swap `HTMLTextAreaElement` for
`HTMLInputElement`.

## Combined recommended pattern

For multi-line content destined for a React composer that submits on Enter:

1. `evaluate_script` → set value via native setter + dispatch 'input'.
2. Click the textarea (focus it).
3. `press_key("Meta+Enter")` or click the Send button.

Avoid `type_text` for anything containing newlines.

## When this does NOT apply

- Plain HTML forms without React-state binding.
- Inputs where Enter does NOT submit (most form fields).
- Non-React frameworks (Vue uses different event semantics — `change`
  rather than `input` is more common).
- Multi-line dedicated editors (Monaco, CodeMirror) — they have their
  own value APIs.

## Real-world incident (grounding)

Caught during a Chrome MCP-driven E2E test of the COS chat composer
(2026-05-17). Both traps hit in the same session:
- Initial type_text with a 2-paragraph prompt got chopped at the first
  newline — model received only the preamble and asked "where's the
  paragraph?"
- Recovery attempt using `fill()` left the Send button disabled despite
  text visible in the textarea — onChange never fired.
- evaluate_script with the setter + input event pattern unblocked both.

## Source Context

Discovered during COS E2E testing via Chrome MCP session (2026-05-17).
The chat composer is a React-controlled textarea that submits on Enter.
Both traps emerged in the same test run: type_text chopped a multi-line
prompt at the first newline boundary, and a recovery attempt using
fill() rendered the UI unresponsive because React's onChange handler
never fired. The native setter + input dispatch pattern resolved both
issues. Grounding reflects direct production E2E testing against the
live chat composer.
