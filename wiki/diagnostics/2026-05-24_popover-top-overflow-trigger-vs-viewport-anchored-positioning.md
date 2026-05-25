---
title: Popover top-overflow — trigger-anchored vs viewport-anchored positioning
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.65
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-24
tags: css,react,tailwind,ui-bugs,positioning,popover,modal
related_entries: []
---

# Popover Top-Overflow — Trigger-Anchored vs Viewport-Anchored Positioning

## Problem Signature

A popover or dropdown rendered with `position: absolute; bottom: 100%` (Tailwind `absolute bottom-full`) appears above its trigger. When users open it, the top of the popover is offscreen above the viewport. Setting a `max-height` (e.g. `max-h-[80vh]`) does NOT fix this — the popover still overflows the top when it grows toward its max.

## Root Cause

`absolute bottom-full` positions the popover relative to its TRIGGER, not the viewport. The popover's bottom edge sits just above the trigger. Its top edge is at `trigger_y - popover_height`. If the trigger is not pinned at the bottom of the viewport, then any popover height that exceeds `(trigger_y - viewport_top)` overflows.

### Concrete Example

- Viewport height: 800px
- `max-h-[80vh]` on viewport = max 640px popover height
- Trigger at y=750px (near bottom): popover top = 750 - 640 - 8(margin) = 102px → visible ✓
- Trigger at y=400px (middle): popover top = 400 - 640 - 8 = -248px → overflow ✗

The `max-h` constrains the popover's maximum size but does not constrain where its top edge ends up. Adding tighter height constraints will not prevent the overflow.

## Diagnostic Recognition

**Key signals:**
- User reports "the popover header is offscreen above the viewport" or "I can't see the top of the popover"
- Existing CSS already includes `max-h-[*vh]` constraints
- Adding more height constraints does not resolve the issue
- The popover visually "floats" relative to its trigger position in the viewport

**What this is NOT:**
- A height problem (adding tighter `max-h` will not help)
- A z-index problem (overflow is directional, not stacking)
- An overflow hidden issue (content is actually clipped outside the viewport)

## Fix: Viewport-Anchored Positioning

Switch from `absolute bottom-full` (trigger-anchored) to `fixed bottom-N right-M` (viewport-anchored). The popover becomes positioned relative to the viewport, with its bottom edge a known distance from the viewport bottom. `max-h-[calc(100vh-Nrem)]` then meaningfully bounds total visible height because the popover position is also viewport-relative.

### Code Example

```diff
- <div className="absolute bottom-full right-0 z-50 mb-2 ... max-h-[80vh] overflow-y-auto">
+ <div className="fixed bottom-20 right-4 z-50 ... max-h-[calc(100vh-6rem)] overflow-y-auto sm:bottom-24">
```

**Parameters to tune:**
- `bottom-N`: Distance in rem from viewport bottom. Choose to clear the chat input, trigger area, or other floating elements below.
- `max-h-[calc(100vh-Nrem)]`: Total visible height budget. Leave room for the trigger area + visual margin. Example: `max-h-[calc(100vh-6rem)]` reserves 6rem for UI below the popover.
- `sm:bottom-24`: Responsive variant for mobile vs desktop breakpoints.

## Trade-offs

**Advantages:**
- Cannot overflow the viewport at any trigger position
- `max-h` becomes a real, predictable bound on total visible height
- Internal scroll behavior is reliable
- Works for triggers anywhere on screen (not just bottom-anchored)

**Disadvantages:**
- Loses the visual "tail pointing to the trigger" coupling — popover floats at a fixed viewport position
- Requires careful responsive variants (`sm:`, `md:`) for mobile vs desktop layouts
- z-index ordering needs review — popover is no longer in the same stacking context as the trigger
- May require adjusting other floating UI (sticky inputs, bottom bars) to coexist visually

## When This Applies

- Help popovers, command menus, autocomplete dropdowns
- Action sheets or floating context menus from toolbar buttons
- Any trigger that sits anywhere EXCEPT the very bottom of the viewport
- Popover content that can grow tall (multiple sections, glossaries, examples, long lists)

## When This Does NOT Apply

- Popovers from triggers GUARANTEED to be at the bottom of the viewport (sticky bottom bars)
  → Use `absolute bottom-full` with careful trigger positioning
- Popovers from triggers near the TOP of the viewport
  → Use `absolute top-full` (will overflow downward); same diagnostic in reverse, switch to `fixed top-N`
- True centered modal dialogs
  → Use a proper centered modal pattern (e.g., `fixed inset-0 flex items-center justify-center`)
- Projects using Floating-UI, Radix Popover, Popper.js, or similar libraries
  → Reach for the library instead — they handle collision detection automatically

## Recognition Pattern for Future Sessions

If you encounter a popover overflow report where:
1. A prior fix added `max-height` constraints
2. The issue persists or worsens on smaller viewports
3. The popover header is consistently clipped above the viewport

The **next move is the trigger-anchored → viewport-anchored switch**, not more height constraints. Successive attempts at `max-h-[60vh]`, `max-h-[40vh]`, etc. will keep failing because the positioning model is wrong, not the height value.

## Source Context

[project] session 2026-05-23 (cos-kcs FreeformGuide popover). Initial fix added `max-h-[80vh]` on the popover; user reported the top was still above the viewport. Second fix switched to `fixed bottom-20 right-4 sm:bottom-24` with `max-h-[calc(100vh-6rem)]`; user-verified resolved. This diagnostic captures the reasoning that led to the solution.
