---
title: React + Supabase anonymous sessions: guard login redirect with !isAnonymous
source_mode: debugger
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 3
created: 2026-07-29
domain: integration
topic: supabase-integration
tags: auth, react, supabase, anonymous-sessions, redirect
related_entries: []
---

# React + Supabase Anonymous Sessions: Guard Login Redirect with !isAnonymous

## Problem

In React apps using Supabase anonymous sessions, the auth context exposes a `canAccess: boolean` that returns true for BOTH fully-authenticated users AND anonymous-session users. If a login page contains a redirect effect like:

```typescript
useEffect(() => {
  if (canAccess && !loading) {
    navigate('/chat');
  }
}, [canAccess, loading, navigate]);
```

...then any user with an anonymous session (which may be bootstrapped for ALL visitors via a `bootstrapSession()` call on app init) gets immediately redirected away from the login page before they can sign in. The observable symptom: clicking "Log In" navigates briefly to the login page then bounces to the app's main page.

## Root Cause

`canAccess` is defined as `mode === 'authenticated' || mode === 'anonymous'`. Anonymous sessions are created proactively (e.g., via `bootstrapSession()` on app mount) to enable unauthenticated API calls. By the time a user clicks "Log In", their anonymous session already exists and `canAccess` is true.

## Fix

Add `!isAnonymous` to the redirect guard:

```typescript
useEffect(() => {
  if (canAccess && !isAnonymous && !loading) {
    navigate('/chat');
  }
}, [canAccess, isAnonymous, loading, navigate]);
```

This allows anonymous users to stay on the login page to actually authenticate, while still redirecting already-authenticated users away.

## When This Applies

- React app with Supabase auth using anonymous sessions
- Anonymous sessions are bootstrapped proactively for all visitors (not just on demand)
- Auth context has separate `canAccess` (covers anonymous) and `isAnonymous` flags
- Login page has a "redirect away if already has access" effect

## When It Does NOT Apply

- Apps where anonymous sessions are never created proactively (only on explicit "try without signing up" user action — in that case, a user landing on the login page wouldn't have a session yet)
- Auth contexts where `canAccess` is false for anonymous users

## Source Context

Verified in COS (semalytics.com/cos) production codebase during login-mobile-fixes-2026-07 session. `bootstrapSession()` is called in main.tsx on every app mount. AuthContext defines `canAccess: state.mode === 'authenticated' || state.mode === 'anonymous'`. The bug was live in production: clicking the login link on the marketing homepage redirected users to /chat instead of showing the login form. Fixed 2026-07-27.
