---
title: Vendoring drift — detect unreviewed divergence between vendored content and its source-of-truth
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-12
domain: infrastructure
topic: ci-validation
tags: quality-gate, validation, adversarial, ci, multi-repo, vendoring
related_entries: []
---

# Vendoring drift — make divergence between vendored copies and source-of-truth visible

## The Problem

"Vendoring" means embedding a copy of upstream content directly into
your repo: bundled skills, copied schemas, embedded module specs,
inlined library files. The benefit is that the consuming repo is
self-contained (clone → use, no transitive cloning required). The
cost is **silent drift**: when upstream evolves, the vendored copy
doesn't — and there's no built-in mechanism to alert you.

Drift accumulates invisibly:
- Upstream maintainer edits a description, fixes a typo, expands a
  scope statement — vendored copy unchanged
- Upstream adds a new file — vendored repo doesn't get it
- Upstream deprecates a file — vendored repo still ships it
- Six months later, the vendored copy is a meaningful subset / older
  variant of what users actually expect

Discovered concretely: a public-ready repo had vendored 23 skill
bodies from a canonical source. A diff against the current canonical
versions revealed **17 of 23 had content drift** (description tightening,
scope expansions in mode skills, signpost links added), totaling roughly
800 lines of unreviewed divergence. Plus 6 entirely new skills had been
added upstream that the vendored repo didn't have at all.

This kind of drift is invisible to:
- Git log (the vendored repo's history shows nothing happening)
- Dependency scanners (vendored content isn't a dependency)
- Test suites (vendored content is data, not code paths)
- Code review (nobody opens an issue to "compare to upstream"
  unless something fails)

## The Pattern

When a repo vendors content from another repo, add **explicit drift
detection**. Pick one (or more) of these mechanisms by cost / coverage:

### Option 1: CI drift-check job

```yaml
- name: Check vendored skills haven't drifted
  run: |
    git clone --depth 1 https://github.com/<source> /tmp/upstream
    for skill in vendored/*/; do
      diff -r "$skill" "/tmp/upstream/skills/$(basename $skill)" || {
        echo "DRIFT: $skill"
        exit 1
      }
    done
```

Fails the build when ANY drift exists. Forces a conscious "accept
upstream + bump my vendored copy" PR, or "reject upstream + pin a
note". The cost is one CI minute per build.

### Option 2: Pinned version + scheduled comparison

Store the upstream commit hash in a `VENDORED_SOURCE` file. A weekly
scheduled CI job clones upstream at HEAD, diffs against your pinned
hash, opens an Issue if there's a non-empty diff. Cost: one CI minute
per week.

### Option 3: Manual periodic audit

Add a calendar reminder ("audit vendored content quarterly"). Cheaper
than CI, but humans forget. Use only when CI is unavailable or the
vendored content is small enough that drift is rare.

### Option 4: Submodule / subtree

Use `git submodule` or `git subtree` instead of copying. Drift becomes
explicit (submodule pointer change shows up in git status). Cost: more
complex contributor onboarding (`git clone --recursive`), and submodule
ergonomics are notoriously poor. Reasonable for content that updates
frequently and where contributors are expected to handle submodules.

## When This Applies

- Multi-repo systems where one repo embeds copies of files from another
  (vendored libraries, embedded skill catalogs, bundled config schemas,
  inlined module specifications)
- "Public-ready" or "self-contained-distribution" repos that copy from
  private / canonical sources, where the consuming repo's freshness
  matters to users
- Cases where the cost of drift > the cost of a CI check (most cases —
  drift compounds, CI checks are constant)

## When This Does NOT Apply

- One-time forks where divergence is intended (the vendored copy IS
  going to evolve independently)
- Vendored content that's truly inert (e.g., a static legal disclaimer
  pulled from a parent project that genuinely never changes)
- Cases where the upstream isn't a single canonical location (e.g.,
  community-contributed plugin systems where drift IS the model)

## Anti-Patterns

- **Trusting "I'll remember to update it"**: humans don't. Either
  automate the check or accept the drift consciously.
- **Drift-check that only compares hashes**: hash-equal is fine, but
  hash-different doesn't tell you what changed. Use `diff -r` output
  so the report is actionable.
- **Failing CI on drift but never updating the vendored copy**: CI
  failure becomes noise, eventually disabled. Pair the check with a
  documented update workflow (and ideally a make target like
  `make refresh-vendored`).
- **Vendoring without a SOURCE marker**: the consuming repo should
  declare WHAT it vendored and from WHERE. A file like
  `vendored/SOURCE.md` documenting upstream + the last sync date
  makes "is this current?" answerable in seconds.

## Cost vs Value

Cost: CI option is ~1 minute per build. Manual audit is 30 minutes
per cycle. Submodule is ongoing onboarding friction.

Value: avoids the "users discover the vendored copy is months behind
upstream" failure mode, which is hard to recover from once it
accumulates. The 17-out-of-23 drift number is roughly 3 months of
unreviewed changes — that gap would have grown indefinitely without
the manual audit that surfaced it.

## Source Context

Discovered during [project]-nwpub skill refresh, 2026-05-12. The
public-ready `nwpub` repo vendored 23 KF + COS skills from `~/.claude/skills/`
(the canonical install). A manual `diff -r` against the current
canonical versions showed:
- 17 of 23 vendored skills had content drift (descriptions
  tightened, scope expanded, signpost links added)
- 6 entirely new skills existed upstream and weren't vendored
- 1 new skill (`cos-copy`) had organization-specific brand voice
  that intentionally shouldn't be vendored

The refresh was a one-time sync. To prevent recurrence, a follow-up
should add either Option 1 (CI drift check) or Option 4 (subtree)
with a documented refresh workflow. The PR that surfaced this was
github.com/internexio/nwpub/pull/1.
