---
title: Dual opt-in pattern for elevated subprocess capability — require both producer dispatch AND consumer allowlist to agree
source_mode: builder
novelty_type: new_pattern, transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-10
tags: security, defense-in-depth, sandboxing, subprocess, capabilities, allowlist, dispatch, trust-boundary
related_entries:
  - patterns/2026-05-13_validator-after-ownership-gate-shared-crud-scaffolds.md
  - patterns/2026-05-18_composite-vs-atomic-mcp-tool-design.md
domain: infrastructure
topic: ops
---

# Dual Opt-In Pattern for Elevated Subprocess Capability

## Pattern

When a system allows workers to request elevated execution context
(different cwd, different env, different privileges, different
network access, etc.), implement the elevation as a **dual opt-in**:
the **producer** side carries a dispatch table mapping worker
identity → permitted elevation, AND the **consumer** side carries
an allowlist of permitted elevations. Both must agree before the
elevation takes effect; either side dissenting falls back to the
default capability silently.

This is a specialization of the "defense in depth" pattern, tuned
to the case where: (a) the worker is trusted but may have bugs,
(b) the consumer runs the dangerous action, and (c) the default
capability is safe.

## Why Both Sides

- **Producer-only**: a buggy producer (e.g., a compromised worker)
  could request an inappropriate elevation. Consumer trusts the
  producer absolutely → vulnerable.
- **Consumer-only**: every worker must pre-register every elevation
  it might need with the consumer's allowlist. Producers become
  coupled to consumer config — operational drag, and a request
  that wasn't pre-registered silently fails.
- **Dual opt-in**: producer authors the dispatch (knows its own
  needs); consumer authors the allowlist (controls what's
  operationally permitted). Both opt-ins are explicit, debuggable,
  and the system's failure mode is "fall back to default" rather
  than "execute the wrong thing."

## Concrete Grounding

Implemented 2026-06-10 in [project] jyku.3 cwd override (joint
shipment of beads 2he8 + btxj, commit 177e971):

- **Producer side**: `iteration_loop/telegram_stub.py` carries
  `_WORK_TYPE_TO_CWD` dispatch table. When the Tier-3 Approve
  button is built for a proposal, the button-builder reads
  `proposal.work_type` and injects `metadata.cwd` into the
  `queue_task` action payload IF AND ONLY IF the work_type is in
  the dispatch. Initial mapping:
  ```python
  _WORK_TYPE_TO_CWD = {
      "wiki-linter": str(Path.home() / "Scripts" / "knowledgeforge-core"),
  }
  ```
- **Consumer side**: `iteration_loop/exec_consumer.py`'s
  `_resolve_cwd(task_metadata)` reads `metadata.cwd` and validates
  against `CWD_ALLOWLIST` (built from the env var
  `[project]_EXEC_CWD_ALLOWLIST`, colon-separated). The plist
  sets it explicitly:
  ```xml
  <key>[project]_EXEC_CWD_ALLOWLIST</key>
  <string>~/Scripts/knowledgeforge-core</string>
  ```
- **Default fallback**: if either side hasn't opted in (work_type
  missing from dispatch OR cwd not in allowlist), `_resolve_cwd`
  silently returns `CWD_DEFAULT` and logs the skip reason
  (`cwd_override_not_allowlisted`) to stderr.

The two opt-ins are independent: the producer ships in source code
(telegram_stub dispatch), the consumer ships via operator-controlled
env config (plist EnvironmentVariables). An operator can disable
the elevation entirely by unsetting the env var without touching
the producer code; a developer can rev the producer dispatch
without operator action (the consumer's allowlist gates anyway).

## When This Applies

- Any system where the trust model is "producers are mostly
  trusted but may be buggy, and the action is high-blast-radius."
- Any subprocess execution surface that supports per-task config.
- Any IPC layer where messages can carry capability requests
  (e.g., MCP tool arguments, task queue metadata fields, RPC
  payloads).
- Any containerized dispatch where the producer defines which
  workload classes can request elevated environment bindings, and
  the orchestrator defines which bindings are operationally allowed.

## When This Does NOT Apply

- **Single-tenant systems** where there's exactly one producer and
  one consumer authored by the same team — the dispatch and
  allowlist would be the same person on both sides, duplicating
  the same data twice. Just enforce in one place.
- **Capability-token systems** with cryptographic delegation —
  those handle elevation differently (signed tokens, not
  bilateral negotiation).
- **Coarse-grained capabilities** where the default is "do
  nothing useful" — the dual opt-in is overkill; require the
  elevation always.

## Fix Forward — Applying This Pattern

When designing a new "worker requests special capability" surface:

1. Identify the elevation: cwd, env, network, fs access, etc.
2. Define the **producer dispatch**: keyed by some stable worker
   identifier (work_type, agent_id), maps to elevation value.
   Living in producer code is fine — that's where it's most
   auditable.
3. Define the **consumer allowlist**: ideally env-configurable
   (operator can rotate without code change), enumerated values
   of permitted elevations.
4. The **action site** (the place that executes the elevated
   operation) MUST consult both:
   - Was the elevation actually requested? (dispatch hit)
   - Is the requested elevation permitted? (allowlist hit)
   Either no → default capability with logged skip reason.
5. Make the fallback **silent + observable**: don't raise — log
   to stderr with a distinguishable reason code, and surface that
   reason in any audit trail so post-hoc debugging is tractable.

## Related Patterns

- **Validator-after-ownership-gate pattern** — sequential ordering
  of gates within a single operation. The dual opt-in pattern
  gates across two independent subsystems before any operation runs.
- **Composite vs atomic MCP tool design** — when to split tool
  responsibilities. The dual opt-in applies to the orchestration
  layer that routes tool requests to executors.

## Diagnostic Signal

A capability elevation surface where the security argument is
"the producer can be trusted to ask for the right thing" — push
back. That's single-opt-in by default. Either the producer is
load-bearing in the trust model (and needs to be audited
rigorously) or there should be a consumer-side check too. Code
review: look for `subprocess.run(cmd, cwd=arbitrary, env=arbitrary)`
where `arbitrary` came from a remote/IPC source without a
consumer-side allowlist gate.

## Source Context

[project] jyku.3 dispatch layer (beads 2he8 + btxj joint shipment,
2026-06-10). The pattern emerged when wiring Step-4 execution
consumers to accept cwd overrides from Step-3 Telegram decisions:
the producer (telegram_stub.py) needed to author which work types
could request elevation, but the consumer (exec_consumer.py) needed
independent operator control over which paths were actually
permitted. Either side dissenting falls back silently to avoid
silent failures from incomplete configuration on either side. This
generalized from a cwd-specific case to a parametric pattern
applicable to any subprocess capability elevation.
