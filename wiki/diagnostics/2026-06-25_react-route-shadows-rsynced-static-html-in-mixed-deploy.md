---
title: React-route schema/meta edits are shadowed when site/ is rsynced but a Docker container actually serves the route
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-06-25
domain: diagnostics
topic: deployment-verification
tags: react, vite, deployment, schema-org, nginx, debugging, docker
related_entries:
  - infrastructure/2026-05-20_static-site-rsync-excludes-leak-prevention.md
  - infrastructure/2026-05-13_deployment-gap-audit-shadow-mode-patterns.md
  - diagnostics/2026-05-23_post-flip-structural-verification-routing-vs-downstream.md
  - diagnostics/2026-05-23_live-smoke-as-verification-gate-mocks-pass-prod-breaks.md
---

# React-route schema/meta edits are shadowed when site/ is rsynced but a Docker container actually serves the route

In a mixed-source deployment where:

- A static site is rsynced to `/var/www/<host>/`
- A React/Vite (or Next.js, CRA) app is built into a Docker image and
  served at one or more route prefixes (`/app/`, `/cos/`, etc.) via
  nginx `proxy_pass` to the container

...edits to `site/<route>/index.html` are SHADOWED at runtime. nginx
routes the request to the React container; the container serves the
pre-built HTML compiled from `frontend/index.html` (the Vite source
template) into `dist/index.html`. The static rsynced file on disk at
`/var/www/<host>/<route>/index.html` is never touched by a real
request.

## Concrete failure mode (verified 2026-06-25 on [project])

1. Sweep script applies schema changes to all `site/**/index.html`.
2. `site/<route>/index.html` now has new JSON-LD; sweep validates
   cleanly (file content is correct).
3. CI rsyncs `site/` to `/var/www/<host>/` — succeeds.
4. `curl https://<host>/<route>/` — returns the OLD HTML (from the
   React container build). Schema diff shows missing blocks, old
   `og:image` filename, pre-v2 Organization shape, etc.

## Why it survives normal verification

- File-level `grep` on the repo says the change is there (true — in
  the source file).
- CI logs say rsync succeeded (true — to disk).
- Test deploy "looks live" if you check the file with `cat` on the
  server (true — file is on disk).
- Only curling the live URL and inspecting the SERVED HTML reveals
  the shadow. The deploy succeeded; the served route just isn't
  using that file.

## How to detect

- Before claiming a sweep is verified on a React-served route,
  `curl` the route and inspect a unique marker from your change
  (a new `@id`, a new field, the new logo URL). If the marker is
  absent, the rsync is being shadowed.
- Look at the page source for distinctive React-build markers like
  `<script type="module" crossorigin src="/<route>/assets/index-*.js">`
  or content that only exists in `frontend/index.html`. If those
  are present, you're looking at the container's HTML, not your
  rsync.

## How to fix

- Apply the same changes to `frontend/index.html` (the Vite source
  template). Frontend Docker image rebuild ships your edits to the
  container, which then serves them. CI cycle is longer than rsync
  (~13-15 min for image build vs. <1 min for rsync) but is the
  actual ship path.
- Optionally also keep the same content in `site/<route>/index.html`
  so the rsynced file matches the served file — but recognize it
  as documentation, not the live source. Or revert it to avoid
  future devs' confusion.

## Generalization (where this applies beyond [project])

Any project where static content and a built SPA both touch the
same URL path. Common when:

- Marketing site is static (Hugo, Jekyll, plain HTML) under one
  root and a product app is React/Vue/Svelte under a sub-route.
- nginx config has both a `try_files` static fallback AND a
  `proxy_pass` to an app container, and the `proxy_pass` wins for
  the relevant route prefix.
- Build pipelines copy the SPA's built `index.html` into a path
  that ALSO has a static source file with the same name.

## Where this does NOT apply

- Pure static-only deploys (every route file is what's served).
- Pure SPA-only deploys (no rsync layer at all).
- SSR setups (Next.js with full server rendering) where the source
  template isn't shadowed but transformed per request — different
  class of issue.

## Grounding

[project] session 2026-06-25, beads `cos-fek6`:

- v1 commit `8bdf2ee` shipped to `site/cos/index.html`; CI succeeded.
- Post-deploy prod curl found only 2 of 5 expected JSON-LD blocks.
- Investigation revealed React container at `/cos/` was serving
  `frontend/index.html` built artifacts, not the rsynced static file.
- Commit `514177f` (cos-fek6 v2) re-applied to `frontend/index.html`
  and verified live.

<!-- KF-MODE: synthesizer | DECISION: evaluative -->
