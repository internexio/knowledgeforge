---
title: Protocol-doc drift catch — L3 installers should verify concrete tool signatures against live schema before pasting, and push corrections UP
source_mode: builder
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.75
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-06
domain: orchestration
topic: multi-repo-protocol-drift
tags: multi-repo-orchestration, protocol-drift, mcp-tools, spec-vs-implementation, L2-L3, corrective-artifact, coordination-hierarchy
related_entries:
  - patterns/2026-06-10_mcp-tool-response-shape-live-verification-before-parsing.md
  - patterns/2026-06-26_skill-spec-vs-canonical-doc-staleness-silent-drift.md
  - patterns/2026-05-22_spec-to-implementation-gap-distinct-review-pass.md
  - infrastructure/2026-05-12_vendoring-drift-detection.md
  - infrastructure/2026-05-25_hook-installed-vs-source-drift-direct-edits.md
revises: null
superseded_by: null
---

# Protocol-doc drift catch — L3 installers should verify concrete tool signatures against live schema before pasting, and push corrections UP

## Pattern

In multi-repo orchestrator systems where a Layer-2 coordinator publishes a spec / protocol doc that Layer-3 repos install verbatim into their own CLAUDE.md / AGENTS.md / setup-doc — the spec doc often cites *concrete tool signatures* (MCP tool names + parameter names, CLI flags, SDK method calls). These signatures drift silently when the underlying tool evolves. The publisher (L2) rarely re-verifies against the live schema; L2 is focused on protocol semantics, not signature freshness.

The mechanism that catches drift is the *installer* (L3), which is running the tool WHILE installing the block. The installer discovers the drift by getting a schema error on the very first call.

## The three-move framework

1. **Verify signatures at install time.** When pasting a spec block that cites concrete tool calls, run a lightweight schema check first — either call the tool with a probe payload, or read the tool's live schema (e.g. `ToolSearch("select:<tool>")` for MCP tools). Compare against the block's example calls.

2. **Fix locally + install the corrected block.** Adjust the pasted content to use the current-correct signatures. Mark the fix with a HTML-comment block like `<!-- ORCHESTRATOR CORRECTION: session_id → claimed_by (verified against MCP schema 2026-07-04) -->` so future readers can see the drift trace.

3. **Push the correction UP to the publisher.** File a bead in the publisher's tracker (if it has one) OR send a corrective research/handoff artifact via the coordinator's own channel. The publisher can then update the spec so the next installer doesn't hit the same trap.

## Concrete grounding — sem-tools L3 install (2026-07-04)

Installed the L3 repo-agent block from `~/Scripts/cos-manager/protocols/repo_agent_claudemd_block.md` (commit 9884fcc) into `sem-tools/CLAUDE.md`. Two tool signatures in the spec's example calls didn't match the live Orchestra MCP schema:

- **Spec:** `claim_artifact(artifact_id=..., session_id="{{agent_id}}-$(date -u +%Y-%m-%d)")`
  **Actual (verified via ToolSearch):** parameter is `claimed_by`, not `session_id`. Live error: `Input validation error: 'claimed_by' is a required property`.

- **Spec:** `push_artifact(target="cos-advisor", ...)`
  **Actual:** parameter is `destination`, not `target`. Live error: `Input validation error: 'destination' is a required property`.

Both errors would have fired on the L3's very first live handling of a nudge — before which the L3 agent has no way to verify the spec is stale. Every remaining L3 installer ([project], semalytics-gtm, client-project) would hit the same trap installing verbatim.

The block was fixed during install and a corrective research artifact (`art_ed3e57f4`) was pushed to `cos-advisor` with the specific parameter-name diffs, root-cause analysis, and a suggested spec edit including a "verified against orchestra mcp schema YYYY-MM-DD" note to catch future drift.

## When this applies

- Multi-repo systems with L1 (strategy) / L2 (coordination) / L3 (execution) layering (KF's typical shape; cos-manager's specific shape)
- Any spec doc that cites *concrete API signatures* — MCP tool params, SDK method names, CLI flag names
- Any protocol block designed to be *pasted verbatim* into multiple downstream repos

## When this does NOT apply

- Spec docs describing pure semantics ("call the tool that lists artifacts") without concrete signatures — no drift surface.
- Single-repo systems where publisher and installer are the same agent.
- One-shot config blocks that don't cite tool calls (e.g. code-of-conduct blocks).

## Why L2 doesn't catch drift itself

- L2 wrote the spec once and moved on to coordinating.
- L2's normal work (dispatch, drift lint on outbound content) doesn't touch its own protocol docs.
- The publisher-vs-consumer asymmetry: the publisher can't easily test a signature the way an installer can (which has the tool in hand at install time).

## Sibling patterns this connects to

- **README drift** — same shape, different scope. READMEs cite CLI flags that get renamed; users hit the drift, but rarely file corrections upstream. Multi-repo L3 installers are strictly better positioned than end-users because they're already writing to the coordinator's channel.
- **API integration test drift** — when an integration test bakes in an API's response shape and the API evolves. The test's failure IS the drift catch. Same underlying pattern: automated verification at boundary layer catches specification-vs-reality gap.
- **OpenAPI spec vs actual endpoint** — same asymmetry, different tools; contract tests catch it.

## Relationship to existing wiki entries

- [[patterns/2026-06-10_mcp-tool-response-shape-live-verification-before-parsing]] — sibling: focuses on verifying **response shape** live before writing parsing code. This entry focuses on **call-site signatures** (parameter names) in protocol docs before pasting them into installers. Both hinge on live-schema verification, but at different points in the integration lifecycle: response-shape verification catches drift when *consuming* a tool's output; signature verification catches drift when *authoring the call* into a spec.
- [[patterns/2026-06-26_skill-spec-vs-canonical-doc-staleness-silent-drift]] — sibling: same drift shape (published-doc lags underlying source-of-truth), but the drift surface differs. That entry is about **domain content drift** (positioning locks, anti-patterns) where the skill lags the canonical doc. This entry is about **API signature drift** where the L2 protocol doc lags the tool's live schema. Both need version-pinning ("verified against X on YYYY-MM-DD") to be visible.
- [[patterns/2026-05-22_spec-to-implementation-gap-distinct-review-pass]] — related: spec-to-implementation gap as a distinct review category. This entry is the multi-repo/protocol-doc specialization — the "implementation" is the tool schema, and the "spec" is a protocol doc distributed to N downstream installers.
- [[infrastructure/2026-05-12_vendoring-drift-detection]] — related: vendored copies drifting from upstream. The L3 installer situation is a vendoring pattern (each L3 vendors the L2 block into its CLAUDE.md). The corrective-push-UP mechanic is what makes this pattern durable — vendoring drift is usually caught downstream, but the fix has to flow back upstream.

## Governance suggestion for coordinators (L2)

When publishing a spec doc that cites concrete tool signatures, include a machine-readable manifest of the signatures used, and a lint step (run periodically, or at each protocol edit) that compares the manifest against live tool schemas. That way drift gets caught centrally, not by the first L3 installer.

## Diagnostic signal

A protocol / spec / repo-agent block that:

- Cites concrete MCP tool calls, SDK methods, or CLI flags in example code
- Contains NO "verified against ... on YYYY-MM-DD" annotation
- Is designed to be pasted verbatim into multiple downstream repos
- Was authored by a coordinator that doesn't itself invoke the tools (publisher-consumer asymmetry)

...is a high-probability drift surface. The first L3 installer that runs the block live is the earliest natural detector.

## Source Context

Discovered while installing the cos-manager L3 repo-agent block into `sem-tools/CLAUDE.md` on 2026-07-04 as part of the SEM-tools polling handler bootstrap. The block's example calls used stale MCP parameter names (`session_id`, `target`) that had evolved to `claimed_by` and `destination` in the live Orchestra MCP schema. The installer (sem-tools L3 session) was the first agent to compare the spec against the live schema — the L2 coordinator (cos-manager) had authored the block against an earlier schema and hadn't re-verified. Fixed locally, pushed corrective artifact `art_ed3e57f4` to `cos-advisor` for spec update. Grounding score 0.75 reflects direct observation of two concrete drift instances in a single install session; slow_decay staleness because the underlying pattern (publisher-consumer asymmetry in multi-repo orchestrator systems) remains stable even as specific tool APIs churn.
