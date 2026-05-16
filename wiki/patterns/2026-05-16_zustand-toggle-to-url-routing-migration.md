---
title: Migrating Zustand toggle-state to URL routing for deep-linkable views
source_mode: builder
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-16
domain: patterns
topic: synthesis
tags: routing, quality-gate, accretion
related_entries: []
---

# Migrating Zustand toggle-state to URL routing for deep-linkable views

Single-page features in React frequently start with one route plus a Zustand store field that toggles between conditional render branches (`activeId ? <DetailView/> : <ListView/>`). This works until any of these become valuable:

- Sharing a specific detail view's URL externally
- Browser back-button returning from detail → list
- Multiple browser tabs holding independent views
- Bookmarking a specific item view
- Analytics keyed on per-route page-views
- Deep links from email/chat into a specific item view

At that point the toggle-state-in-Zustand becomes the anti-pattern. The fix is mechanical: replace the toggle with React Router routes + `useParams` + `useNavigate`. URL becomes the source of truth.

## Migration Steps (Apply in Order)

Each step is independently green-able; apply them sequentially to avoid blocking the test suite.

### 1. Add the new routes alongside the old one in the router

Replace the old single route with a 301-style `<Navigate to="/new-default" replace />`. New routes target new page components:

```javascript
// App.tsx
const router = createBrowserRouter([
  {
    path: '/feature',
    element: <Navigate to="/feature/new" replace />
  },
  {
    path: '/feature/new',
    element: <NewPage />
  },
  {
    path: '/feature/items/:id',
    element: <DetailPage />
  },
  // ... other routes
]);
```

### 2. Create new page components by splitting the monolithic page

- The "no activeId" branch becomes the list/composition page (its route is the new default)
- The "activeId set" branch becomes the detail page (its route uses `:id` URL param via `useParams`)

```javascript
// pages/NewPage.tsx
export function NewPage() {
  return (
    <div>
      <ProposalPanel />
      <HistoryList />
    </div>
  );
}

// pages/DetailPage.tsx
import { useParams } from 'react-router-dom';

export function DetailPage() {
  const { id } = useParams<{ id: string }>();
  return <RunDashboard runId={id!} />;
}
```

### 3. Convert mutation handlers to use `useNavigate()`

Find all call sites of the old setter (e.g., `setActiveId`). Replace with `navigate()`:

```javascript
// Before
const { setActiveId } = useBuyersCommitteeStore();
setActiveId(run.runId);

// After
const navigate = useNavigate();
navigate(`/feature/items/${run.runId}`);
```

Grep for the setter name to find all call sites: `grep -r "setActiveId" src/`

### 4. Convert list-row click handlers

Use either `<Link>` (semantic, accessibility-friendly) or `onClick={() => navigate(...)}` if the click handler does other work:

```javascript
// Option A: Semantic link
<Link to={`/feature/items/${id}`}>
  <div className="row">{item.name}</div>
</Link>

// Option B: Click handler with additional logic
<div onClick={() => { 
  logAnalytics('row_clicked', id);
  navigate(`/feature/items/${id}`);
}}>
  {item.name}
</div>
```

### 5. Convert back-buttons

Replace `setActiveId(null)` with `navigate()` to the list route:

```javascript
// Before
<button onClick={() => setActiveId(null)}>Back</button>

// After
const navigate = useNavigate();
<button onClick={() => navigate('/feature/new')}>Back</button>
```

### 6. Remove the Zustand field and setter from the store

Delete `activeId` and `setActiveId` from your store interface and implementation. Leave a one-line comment noting the migration:

```javascript
// Zustand store (before)
interface BuyersCommitteeStore {
  activeRunId: string | null;
  setActiveRunId: (id: string | null) => void;
}

// Zustand store (after)
interface BuyersCommitteeStore {
  // activeRunId removed 2026-05-16 — migrated to URL routing for deep-linkability
  // See wiki: 2026-05-16_zustand-toggle-to-url-routing-migration.md
}
```

### 7. Delete the old monolithic page file

Once nothing imports it, remove the old page component file (e.g., `pages/BuyersCommittee.tsx`).

## When This Applies

- React app using React Router + Zustand (or any UI store holding navigation state)
- The "toggle between branches" Zustand field maps cleanly to a route param
- No collaborator using the page expects the state to persist across reloads in a non-URL way
- You have use cases for deep-linking, bookmarking, or sharing URLs to specific views

## When This Does NOT Apply

- The "toggle" represents UI mode that legitimately shouldn't be URL-encoded (e.g., dark mode, sidebar collapsed, draft form values) — those are user-preferences or draft-state, not navigation
- The conditional render isn't 1:1 with what a user would call "this view" (e.g., a modal that overlays the same logical page)
- Server-side rendering or SEO are not concerns AND the app has zero deep-link or share use cases — the migration cost isn't paid back
- The store field is shared across multiple independent features (you'd need a multi-route refactor instead)

## Source Context

Grounded in the Buyers Committee (BC) routing split, shipped in COS cos-3bu.6 on 2026-05-16.

**Before:** `frontend/src/pages/BuyersCommittee.tsx` was one component with `useBuyersCommitteeStore.activeRunId`. The conditional render: `activeRunId ? <RunDashboard runId={activeRunId} onBack={() => setActiveRunId(null)} /> : <CohortBuilder + RunHistoryList />`. The `ProposalRunPanel` (which creates a new run) called `setActiveRunId(run.runId)` to "switch view." Run-history rows called the same setter to navigate to detail.

**After:** 4 routes in App.tsx:
- `/buyers-committee` → 301 redirect → `/new`
- `/buyers-committee/new` → NewRunPage
- `/buyers-committee/runs/:runId` → RunPage
- `/buyers-committee/personas` → PersonasPage

Three new page components (NewRunPage, RunPage, PersonasPage) + a shared BcNav. `ProposalRunPanel` calls `navigate(\`/buyers-committee/runs/${run.runId}\`)`. Run-history rows call `navigate(\`/buyers-committee/runs/${id}\`)`. Back-button on RunPage navigates to `/new`. Zustand `activeRunId` + `setActiveRunId` deleted from the store (block comment explains the migration). Old monolithic page deleted.

**Results:**
- Shareable deep links to individual runs
- Browser back-button works as expected
- The `/personas` route is reachable without forcing the user through `/new` first
- Total work: ~250 net new lines + ~70 deletions across 7 files
- CI: typecheck clean, lint 0 errors, 209 frontend tests pass
- Production deploy was a clean fast-forward

**Pattern in sibling feature:** Expert Council (EC) had already shipped the equivalent split (`expert-council/runs/:runId` + `expert-council/experts` + EcNav). BC migration cribbed the EC structure directly — when a sibling feature has the split, mirror it for consistency.
