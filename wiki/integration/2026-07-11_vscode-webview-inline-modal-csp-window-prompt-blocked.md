---
title: VS Code Webview — window.prompt() Blocked, Use Inline Overlay Div for Modal Text Input
source_mode: builder
novelty_type: reusable_diagnostic
grounding_score: 0.82
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-11
domain: integration
topic: vscode-extension-integration
tags: vscode, webview, ui-patterns, csp, modal-dialog
related_entries: [integration/2026-07-11_vscode-extension-local-server-spawn-capture-auth-pattern.md]
---

# VS Code Webview: window.prompt() Blocked — Use Inline Overlay Div for Modal Text Input

## The Constraint

VS Code webviews run under a strict Content Security Policy. `window.prompt()`, `window.alert()`, and `window.confirm()` are all **blocked** — they silently no-op or throw. This means any flow requiring user text input (e.g., "enter a title to file this to wiki") cannot use the native browser dialog APIs.

## The Pattern: Hidden Overlay Div

Use a hidden overlay `<div>` in the webview HTML. Show/hide it via JS. Wire keyboard shortcuts (Enter to confirm, Esc to cancel) and backdrop click to close. The overlay element pretends to be a modal—it's not, but to the user, it behaves like one.

### HTML (in the webview template)

```html
<div id="wiki-overlay" hidden>
  <div id="wiki-dialog" role="dialog" aria-label="File to KF wiki">
    <div class="wiki-dialog-title">File to KF wiki</div>
    <input type="text" id="wiki-title-input" placeholder="Entry title…" />
    <div class="wiki-dialog-actions">
      <button id="wiki-dialog-cancel">Cancel</button>
      <button id="wiki-dialog-confirm">File</button>
    </div>
  </div>
</div>
```

### CSS — Overlay Hides Cleanly With `[hidden]` Attribute

```css
#wiki-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

#wiki-overlay[hidden] {
  display: none;
}

#wiki-dialog {
  background: var(--vscode-editor-background);
  border: 1px solid var(--vscode-editor-foreground);
  border-radius: 4px;
  padding: 16px;
  max-width: 600px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

#wiki-dialog-title {
  font-weight: bold;
  margin-bottom: 12px;
}

#wiki-title-input {
  width: 100%;
  padding: 8px;
  margin-bottom: 12px;
  background: var(--vscode-input-background);
  color: var(--vscode-input-foreground);
  border: 1px solid var(--vscode-input-border);
  border-radius: 2px;
}

#wiki-title-input:focus {
  outline: none;
  border-color: var(--vscode-focusBorder);
}

.wiki-dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.wiki-dialog-actions button {
  padding: 6px 12px;
  cursor: pointer;
  background: var(--vscode-button-background);
  color: var(--vscode-button-foreground);
  border: none;
  border-radius: 2px;
}

.wiki-dialog-actions button:hover {
  background: var(--vscode-button-hoverBackground);
}

#wiki-dialog-cancel {
  background: transparent;
  color: var(--vscode-button-foreground);
}
```

### JavaScript — Show, Wire Shortcuts, Send Message

```javascript
const wikiOverlay = document.getElementById('wiki-overlay');
const wikiDialog = document.getElementById('wiki-dialog');
const wikiTitleInput = document.getElementById('wiki-title-input');
const wikiDialogConfirm = document.getElementById('wiki-dialog-confirm');
const wikiDialogCancel = document.getElementById('wiki-dialog-cancel');
const btnWiki = document.getElementById('btn-wiki');

// Show overlay when the user clicks "File to Wiki"
btnWiki.addEventListener('click', () => {
  const suggestedTitle = autoSuggestTitle(accumulatedText);
  wikiTitleInput.value = suggestedTitle;
  wikiOverlay.hidden = false;
  wikiTitleInput.focus();
  wikiTitleInput.select();  // Auto-select so user can type to replace
});

// Confirm: send message to extension host
wikiDialogConfirm.addEventListener('click', () => {
  const title = wikiTitleInput.value.trim();
  if (!title) {
    wikiTitleInput.focus();
    return;
  }
  vscode.postMessage({ type: 'wiki:file', content: accumulatedText, title });
  wikiOverlay.hidden = true;
});

// Cancel button
wikiDialogCancel.addEventListener('click', () => {
  wikiOverlay.hidden = true;
});

// Keyboard shortcuts
wikiTitleInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') wikiDialogConfirm.click();
  if (e.key === 'Escape') wikiDialogCancel.click();
});

// Backdrop click closes
wikiOverlay.addEventListener('click', (e) => {
  if (e.target === wikiOverlay) wikiOverlay.hidden = true;
});

// Helper: auto-suggest title from first non-blank line
function autoSuggestTitle(text) {
  const lines = text.split('\n');
  for (const line of lines) {
    const clean = line.trim().replace(/^#+\s*|\*+|`+|@|>|/g, '');
    if (clean) return clean.slice(0, 100);
  }
  return 'New Entry';
}
```

## Key Decisions & Rationale

**`[hidden]` attribute + `display: none` in CSS (NOT inline style)**
- DO NOT use `display: none` inline style. VS Code webviews block inline styles unless you use a nonce. The `[hidden]` CSS selector lives in the external stylesheet and is safe.
- The `[hidden]` pseudo-selector is idiomatic HTML and clean.

**`position: fixed; inset: 0`**
- `inset` is shorthand for `top: 0; right: 0; bottom: 0; left: 0`. VS Code webviews support modern CSS. Using `inset` is cleaner than four separate properties.
- `fixed` ensures the overlay always covers the viewport, even when webview content scrolls.

**Auto-suggest the title**
- Pre-fill the input from the first meaningful line of the content (strip markdown headers `#`, bold `*`, code backticks, blockquote `>`, etc.).
- Users can edit it freely. Eliminates the blank-field frustration of a pure prompt.
- The helper function `autoSuggestTitle()` is trivial and gives you 80% UX wins.

**Don't disable the trigger button while dialog is open**
- The overlay backdrop blocks clicks on the button anyway (z-index: 100 covers the whole viewport).
- Keeping the trigger button focusable avoids weird tab-order navigation issues.

**Use VS Code theme variables**
- `var(--vscode-editor-background)`, `var(--vscode-input-background)`, `var(--vscode-button-background)`, etc.
- The dialog automatically respects the user's theme (light, dark, high-contrast) without hardcoded colors.

## When This Applies

- Any VS Code extension webview that needs a modal text input (rename, file, annotate, tag, create)
- Any webview context where `window.prompt()` is blocked (all VS Code webviews; most sandboxed iframes)
- Flows where the user needs to review/edit a pre-suggested value, not just confirm a binary yes/no

## When This Does NOT Apply

- **VS Code Quick Pick / Input Box API.** If you control the extension host (not webview-only), use `vscode.window.showInputBox()` instead — it's native, accessible, and keyboard-accessible by default. Only resort to the overlay pattern when you're webview-only or when the input must live in-webview for UX reasons (e.g., embedded in the main content flow).
- **Simple confirmation dialogs (no text input).** Use a styled `<div>` with two buttons, no input needed. Or use the overlay pattern but remove the input field.
- **Flows where the value is fully derived (no user editing).** If you can compute the value deterministically, just send the message directly — don't ask.

## Source Context

Implemented in kf-vscode, `src/KFPanel.ts` (HTML template) + `src/webview/panel.js` (JS logic) + `src/webview/panel.css` (styling). Session: kf-vscode-phase3-wiki-accretion-trigger. Clean typecheck (`tsc`), clean build. The `[hidden]` + CSS pattern verified to work correctly under VS Code's CSP—no nonce-gated scripts needed, no inline styles required for overlay behavior. Commit 0a93f43 (kf-vscode).
