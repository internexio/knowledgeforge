---
title: Wiki Index
type: index
---

# Wiki Index

## Entries by Category

### Patterns

- [2026-05-16] Migrating Zustand toggle-state to URL routing for deep-linkable views — transferable_framework — `patterns/2026-05-16_zustand-toggle-to-url-routing-migration.md`
- [2026-05-15] Post-deliberation per-entity aggregation pattern (synthesizer pass) — new_pattern — `patterns/2026-05-15_post-deliberation-per-entity-aggregation-pattern.md`
- [2026-05-15] REST client tolerance — distinguish 200 OK from 201 Created — new_pattern — `patterns/2026-05-15_rest-client-tolerance-http-status.md`
- [2026-05-14] Claude CLI Subscription Subprocess Context Trim — cwd + --setting-sources — reusable_diagnostic — `patterns/2026-05-14_claude-cli-subscription-subprocess-context-trim.md`
- [2026-05-14] Claude CLI structured-output vs result routing — json-schema callers must check structured_output first — reusable_diagnostic — `patterns/2026-05-14_claude-cli-structured-output-vs-result-routing.md`
- [2026-05-14] Collapse N-useState chorus into discriminated union + reducer — new_pattern — `patterns/2026-05-14_collapse-usestate-discriminated-union-reducer.md`
- [2026-05-14] Autouse fake-stages fixture for neutralizing subprocess-invoking pipeline tests — new_pattern — `patterns/2026-05-14_autouse-fake-stages-fixture-subprocess-pipeline-tests.md`
- [2026-05-14] Spec-environment pattern mismatch — dual-pattern regex + authoritative downstream check — new_pattern — `patterns/2026-05-14_spec-environment-dual-pattern-regex-authoritative-check.md`
- [2026-05-14] File-based stub for deferred external dispatch surfaces — new_pattern — `patterns/2026-05-14_file-based-stub-deferred-dispatch-surfaces.md`
- [2026-05-13] Best-effort bash pipeline runner — subshell + pipefail + sed-prefix + WARN-not-fail composition — new_pattern — `patterns/2026-05-13_best-effort-bash-pipeline-runner.md`
- [2026-05-13] Collapse near-duplicate fetchers by making the rich shape canonical — transferable_framework — `patterns/2026-05-13_collapse-duplicate-fetchers-rich-canonical.md`
- [2026-05-13] Conditional UPDATE for atomic queue claim — single-row claim via WHERE + RETURNING — new_pattern — `patterns/2026-05-13_conditional-update-for-atomic-queue-claim.md`
- [2026-05-13] Content-addressed cache with versioned hash prefix — new_pattern — `patterns/2026-05-13_content-addressed-cache-versioned-hash-prefix.md`
- [2026-05-13] Helper extraction beats loop refactor when per-step state diverges — transferable_framework — `patterns/2026-05-13_helper-extraction-beats-loop-refactor-state-divergence.md`
- [2026-05-13] Jinja2 `{% raw %}` required when migrating .format() templates with literal curly braces — new_pattern — `patterns/2026-05-13_jinja2-raw-block-format-migration.md`
- [2026-05-13] Per-request-instantiated service with instance-attribute caches is dead state — reusable_diagnostic — `patterns/2026-05-13_per-request-instantiated-service-dead-cache-state.md`
- [2026-05-13] Phased god-module split — facade-first, late-bound helpers, simplest-first sequencing — transferable_framework — `patterns/2026-05-13_phased-god-module-split-facade-first.md`
- [2026-05-13] Validator-after-ownership-gate pattern for shared CRUD scaffolds — new_pattern — `patterns/2026-05-13_validator-after-ownership-gate-shared-crud-scaffolds.md`
- [2026-05-12] FastAPI StreamingResponse pre-flight gates must raise BEFORE construction — new_pattern — `patterns/2026-05-12_fastapi-streaming-preflight-gates.md`
- [2026-05-12] Sanitization discipline for public-ready repos — three-pass grep + skip-or-sanitize decision tree — new_pattern — `patterns/2026-05-12_sanitization-three-pass-grep-discipline.md`
- [2026-05-12] Pin-tests for declarative policy manifests — cheap regression guard against accidental entry deletion — new_pattern — `patterns/2026-05-12_pin-tests-declarative-policy-manifests.md`
- [2026-05-12] Dogfood the safety machinery — end-to-end apply-path tests via the system's own atomic install + undo — transferable_framework — `patterns/2026-05-12_dogfood-apply-undo-end-to-end-testing.md`
- [2026-05-11] Archival is retirement, not relocation — autonomous fix systems must honor the difference — transferable_framework — `patterns/2026-05-11_archival-retirement-not-relocation.md`
- [2026-05-11] Atomic-write stubs for pipelines that read-and-write the same file — reusable_diagnostic — `patterns/2026-05-11_atomic-write-stubs-for-readwrite-pipelines.md`
- [2026-05-11] Audit-log event vocabularies — read-side must accept routing-suffixed forms — new_pattern — `patterns/2026-05-11_audit-log-event-vocabulary-mismatch.md`
- [2026-05-10] Mode-Label-with-Variants Taxonomy — new_pattern — `patterns/mode-variants-taxonomy.md`

### Architecture

- [2026-05-14] Domain exceptions should not carry HTTP metadata — transferable_framework — `architecture/2026-05-14_domain-exceptions-exclude-http-metadata.md`
- [2026-05-14] Identity registry + append-only event log — separate "who/what" from "what happened" — new_pattern — `architecture/2026-05-14_identity-registry-append-only-event-log-separation.md`
- [2026-05-10] Pattern Extraction & Reuse Heuristic — transferable_framework — `architecture/pattern-extraction-reuse-heuristic.md`
- [2026-04-18] Scaffolding vs Patching Pattern — new_pattern — `architecture/scaffolding-vs-patching-pattern.md`
- [2026-04-18] Neuro-Symbolic Pattern Validation — new_pattern — `architecture/neuro-symbolic-pattern-validation.md`
- [2026-04-18] Imagination as Suppression Validates Patching — new_pattern — `architecture/imagination-as-suppression-validates-patching.md`
- [2026-04-18] Skills vs Agents Design Boundary — new_pattern — `architecture/skills-vs-agents-design-boundary.md`
- [2026-04-18] Hook Consequence Asymmetry — new_pattern — `architecture/hook-consequence-asymmetry.md`

### Orchestration

- [2026-05-14] Cost meter must always emit release event on cycle exit, even on overrun — new_pattern — `orchestration/2026-05-14_cost-meter-always-emit-release-on-cycle-exit.md`
- [2026-05-13] Coalesce at enqueue, every coalesce gets a row — new_pattern — `orchestration/2026-05-13_coalesce-at-enqueue-every-coalesce-gets-a-row.md`
- [2026-05-13] One reconciliation pipeline, called twice (startup + periodic) — new_pattern — `orchestration/2026-05-13_one-reconciliation-pipeline-called-twice.md`
- [2026-05-08] Multi-Framework CP Composition — new_pattern — `orchestration/multi-framework-cp-composition.md`
- [2026-05-08] KF Version Gap Bridging — reusable_diagnostic — `orchestration/kf-version-gap-bridging.md`
- [2026-04-20] Schema-First Elicitation Order — new_pattern — `orchestration/schema-first-elicitation-order.md`
- [2026-04-20] Adversarial Filename Audit — reusable_diagnostic — `orchestration/adversarial-filename-audit.md`
- [2026-04-20] Disambiguation Loop Hint Injection — new_pattern — `orchestration/disambiguation-loop-hint-injection.md`
- [2026-04-18] Context Manager Protocol — new_pattern — `orchestration/context-manager-protocol.md`
- [2026-04-15] Spec-Commit Before Impl-Commit — new_pattern — `orchestration/spec-commit-before-impl-commit.md`
- [2026-04-15] Codemod-Driven Big Bang Rename — transferable_framework — `orchestration/codemod-driven-big-bang-rename.md`

### Infrastructure

- [2026-05-15] Realigning diverged git remotes via content-equivalence check + force-push — reusable_diagnostic — `infrastructure/2026-05-15_diverged-git-remotes-content-equivalence-realign.md`
- [2026-05-15] Silent-success scripts — monitor by state artifact, not log file — reusable_diagnostic — `infrastructure/2026-05-15_silent-success-scripts-state-artifact-freshness.md`
- [2026-05-14] Claude CLI --bare disables OAuth/keychain — subscription-billed subprocess workers must omit it — reusable_diagnostic — `infrastructure/2026-05-14_claude-cli-bare-disables-oauth-keychain-auth.md`
- [2026-05-14] File-based timer-poll pattern for deferred async acknowledgement — transferable_framework — `infrastructure/2026-05-14_file-based-timer-poll-deferred-ack-semantics.md`
- [2026-05-14] Self-identity-minting CLI flag for cron-scheduled workers — new_pattern — `infrastructure/2026-05-14_self-identity-minting-cli-flag-cron-workers.md`
- [2026-05-14] Idempotent watchdog producer pattern — detector + check_and_alert + dated state file + CLI + cron block — transferable_framework — `infrastructure/2026-05-14_idempotent-watchdog-producer-pattern.md`
- [2026-05-13] Bash `$RANDOM` in command-substitution subshells is deterministic across rapid calls — reusable_diagnostic — `infrastructure/2026-05-13_bash-random-deterministic-command-substitution-subshells.md`
- [2026-05-13] Default to extension over sibling for existing infrastructure — new_pattern — `infrastructure/2026-05-13_default-extension-over-sibling-infrastructure.md`
- [2026-05-13] docker compose down/up container-name race in deploy scripts — reusable_diagnostic — `infrastructure/2026-05-13_docker-compose-down-up-container-name-race.md`
- [2026-05-13] POSIX atomic-append for concurrent JSONL writers — flock unnecessary under PIPE_BUF — transferable_framework — `infrastructure/2026-05-13_posix-append-pipe-buf-concurrent-jsonl-writers.md`
- [2026-05-13] launchd CWD-is-slash trap for CWD-relative CLIs — reusable_diagnostic — `infrastructure/2026-05-13_launchd-cwd-trap-relative-tool-lookups.md`
- [2026-05-13] Deployment-gap audit checklist for shadow-mode patterns — reusable_diagnostic — `infrastructure/2026-05-13_deployment-gap-audit-shadow-mode-patterns.md`
- [2026-05-12] Vendoring drift — detect unreviewed divergence between vendored content and its source-of-truth — new_pattern — `infrastructure/2026-05-12_vendoring-drift-detection.md`
- [2026-05-12] Self-watchdog — autonomous fix systems need external cycle-alive checks — transferable_framework — `infrastructure/2026-05-12_self-watchdog-autonomous-fix-cycles.md`
- [2026-05-12] Empty-stdin crontab wipe — pipeline-failure footgun — reusable_diagnostic — `infrastructure/2026-05-12_empty-stdin-crontab-wipe-footgun.md`
- [2026-05-11] Python package CLIs under cron — module form required for relative imports — reusable_diagnostic — `infrastructure/2026-05-11_python-package-cli-under-cron.md`
- [2026-04-18] Flat Namespace Prefix Convention — new_pattern — `infrastructure/flat-namespace-prefix-convention.md`

### Compiler

- [2026-05-13] Trailing-newline divergence between Python triple-quoted strings and Jinja2 default rendering — new_pattern — `compiler/2026-05-13_trailing-newline-divergence-python-jinja2.md`
- [2026-05-12] ES2020/ES2021 lib divergence — local tsc green, CI tsc red on String.replaceAll — reusable_diagnostic — `compiler/2026-05-12_es2020-es2021-lib-divergence-string-replacall.md`
- [2026-04-18] Multi-Repo Artifact Placement — reusable_diagnostic — `compiler/multi-repo-artifact-placement.md`

### Diagnostics

- [2026-05-15] Check exit code before parsing CLI output — failures emit help that greedy-matches success regexes — reusable_diagnostic — `diagnostics/2026-05-15_check-exit-code-before-cli-output-parsing.md`
- [2026-05-13] PostgREST or_() filter-injection — sanitize free-text before interpolation — reusable_diagnostic — `diagnostics/2026-05-13_postgrest-or-filter-injection-sanitize-freetext.md`
- [2026-05-13] Asymmetric write-time guard coverage across parallel write paths — reusable_diagnostic — `diagnostics/2026-05-13_asymmetric-write-time-guard-coverage.md`
- [2026-05-13] bd search idempotency grep trap — match `^Found` header, not query string — reusable_diagnostic — `diagnostics/2026-05-13_bd-search-idempotency-grep-trap.md`
- [2026-05-13] Content-diff mtime preservation inverts liveness signal on idle-but-healthy systems — new_pattern — `diagnostics/2026-05-13_content-diff-mtime-inversion-idle-systems.md`
- [2026-05-13] Fabricated-default fallback at call site hides upstream data quality bugs — reusable_diagnostic — `diagnostics/2026-05-13_fabricated-default-fallback-at-call-site.md`
- [2026-05-13] Pricing-table key vs default value — don't collapse identical literals when extracting settings — reusable_diagnostic — `diagnostics/2026-05-13_pricing-table-key-vs-default-value-collapse.md`
- [2026-05-13] Python `logging.extra=` reserved-key hazard — reusable_diagnostic — `diagnostics/2026-05-13_python-logging-extra-reserved-keys-hazard.md`
- [2026-05-13] unittest.mock.patch targets shift when a module becomes a package — reusable_diagnostic — `diagnostics/2026-05-13_unittest-mock-patch-targets-shift-module-to-package.md`
- [2026-04-18] Handoff Payload Schema Gap — reusable_diagnostic — `diagnostics/handoff-payload-schema-gap.md`

### Methodologies

- [2026-05-15] Pre-emptive scope sweep of downstream tasks after a strategic verdict supersedes them — transferable_framework — `methodologies/2026-05-15_pre-emptive-scope-sweep-downstream-verdict.md`
- [2026-05-15] Two-call Anthropic cache prefix verification — synthetic probe before shipping cached prompts — reusable_diagnostic — `methodologies/2026-05-15_two-call-anthropic-cache-prefix-verification.md`
- [2026-05-14] Structural-invariant acceptance over wall-clock measurement on stubbed code paths — transferable_framework — `methodologies/2026-05-14_structural-invariant-acceptance-over-wall-clock-stubbed-paths.md`
- [2026-05-14] Healthy-system gate trap — failure-mode thresholds never trip in working systems — reusable_diagnostic — `methodologies/2026-05-14_healthy-system-gate-trap-empirical-thresholds.md`
- [2026-05-13] Find-consumer-first before designing data migrations — reusable_diagnostic — `methodologies/2026-05-13_find-consumer-first-before-data-migration.md`
- [2026-05-13] Critic-finding triage — Strategist for spec-MUST violations, deferred-doc for forward-compat — emerging_pattern — `methodologies/2026-05-13_critic-triage-routing-strategist-vs-defer-doc.md`
- [2026-05-13] Verify audit-doc structural claims against current code before designing the fix — reusable_diagnostic — `methodologies/2026-05-13_verify-audit-claims-before-designing-fix.md`
- [2026-04-18] External Source to KF Mapping — template_candidate — `methodologies/external-source-to-kf-mapping.md`

### Migrations

- [2026-05-16] Verify FK target table on remote before writing migrations against renamed tables — reusable_diagnostic — `migrations/2026-05-16_verify-fk-target-table-remote-before-migration.md`
- [2026-04-18] Big-Bang Rename: Supabase, FastAPI, React — transferable_framework — `migrations/big-bang-rename-supabase-fastapi-react.md`

---

## Index Stats

- **Total entries:** 81
- **Entry types:** new_pattern (35), transferable_framework (16), reusable_diagnostic (28), template_candidate (1), emerging_pattern (1)
- **Domains:** patterns (24), architecture (8), orchestration (10), infrastructure (17), compiler (3), diagnostics (10), methodologies (7), migrations (2)
- **Avg grounding score:** 0.85 (across grounded entries)
- **Staleness risk distribution:** stable (79), slow_decay (2), fast_decay (1)

