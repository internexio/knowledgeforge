# Grader Agent Recommendation (2026-11-07)

### Architecture in one picture

```
 dispatcher (David / cos-manager)            worker (cos-dev, sem-tools, ...)
        │ kf-grade register                          │ git commit; kf-grade submit
        ▼   (dispatcher SSH key)                     ▼   (worker SSH key: submit/status only)
 ┌──────────────────────────── GRADER HOST (home lab) ─────────────────────────────┐
 │ store/  registrations (spec snapshot + sha256)   verdicts (ed25519-signed)       │
 │ runner: fresh clone @ head_sha ──► Stage 1 (deterministic, container, no LLM)   │
 │                                   ├─ executable ACs                              │
 │                                   ├─ tamper diff vs base_sha                     │
 │                                   └─ hidden probes                               │
 │         only if Stage 1 passes ──► Stage 2: `claude -p --agent kf-grader`        │
 │                                    (Read/Grep/Glob only, read-only checkout)     │
 │         pure decide() ──► verdict JSON ──► sign ──► store (+ Orchestra copy)     │
 └──────────────────────────────────────────────────────────────────────────────────┘
        ▲ kf-grade verify (public key)                ▲ Stop hook nudge (managed settings)
 completion consumer: cos-manager / Orchestra gate     worker session
```

Design principle: the LLM is the smallest possible part of the gate. Stage 1, tamper detection, the attempt cap, signing and the final verdict are code. The LLM only scores qualitative dimensions, and only after code has already said the work exists.

### R1. Separation of duties

- [evaluative] The grader runs on a separate host as a separate Unix user, in a fresh headless Claude Code process per grading. It is **never a subagent of the worker**. A subagent's task prompt is written by its parent, so a worker-spawned grader would be graded on the worker's framing. That alone disqualifies in-session subagent invocation.
- Inputs come only from sources the worker does not control:
  - (a) **Task spec**: snapshotted at registration by the dispatcher (`kf-grade register`), stored on the grader host with its sha256. The grader reads the snapshot, never a copy relayed by the worker and never the repo's copy at head.
  - (b) **Artifacts**: the grader clones the repo itself at the submitted `head_sha` and computes `git diff base_sha..head_sha`. `base_sha`, `target_url`, probe URLs and allowed paths come from the registration.
- The worker's submission is two values: `task_id` and `head_sha`. There is no field for a self-report, so it cannot become evidence. Commit messages and code comments are in the diff and are treated as untrusted data (Module 07 untrusted-input boundary).

### R2. The grader runs the checks itself

- [evaluative] Build prompts carry a machine-readable AC block (fenced ` ```yaml kf-acceptance `, schema in Module 04). AC types: `command`, `grep_count`, `http_status`, `dom_check`, `judgment`. Every non-`judgment` AC is executed by the runner against the fresh checkout or the registered target URL. Worker-pasted output is never read.
- `command` ACs run in a disposable container: the checkout is mounted read-only at `/src`, copied to an ephemeral `/work`, run as an unprivileged user, network `none` unless the registration opts into `bridge` (Module 20 HIGH tier), with CPU, memory and wall-clock limits. `grep_count`, `http_status` and `dom_check` run in the runner's own Python against the read-only checkout or the target URL.
- A registration with zero executable ACs is refused. Prose-only prompts must be converted at registration time, before work starts, so the worker cannot influence the checks.
- `dom_check` parses static HTML only. JS-rendered content needs a `command` AC that runs a headless browser in the container. This is a known limitation, not a gap to work around.

### R3. The grader cannot fix work

Enforced in layers. Each layer alone is insufficient; together the LLM has no write path and the runner has no push path.

| Layer | Mechanism | Verified against |
|---|---|---|
| Claude Code tool surface | Agent file `kf-grader.md` frontmatter `tools: Read, Grep, Glob` (allowlist; no Bash, Edit, Write, NotebookEdit, WebFetch). Launch flags repeat it: `--tools "Read,Grep,Glob" --disallowedTools "mcp__*" --strict-mcp-config --permission-mode dontAsk`. | sub-agents doc (frontmatter `tools` is an allowlist; `disallowedTools` removes tools); cli-reference (`--tools`, `--disallowedTools`, `--strict-mcp-config`) |
| Claude Code settings | Grader user's `~/.claude/settings.json` denies `Edit`, `Write`, `Bash`, `NotebookEdit`, `WebFetch`, `WebSearch`; launched with `--setting-sources user` so no project settings from the cloned repo load. | settings doc (deny rules; sources) ; cli-reference (`--setting-sources`) |
| OS | Checkout owned by the grader user and bind-mounted read-only into containers; grader host holds no git push credentials and no deploy credentials. | n/a (OS) |
| Output path | The LLM never writes the verdict. It returns JSON via `--json-schema`; the runner validates it and writes the verdict. | cli-reference (`--json-schema`, print mode) |

Rejected: `isolation: worktree`. The worktrees doc describes it as edit isolation (a separate copy the agent can still modify), not read-only, and it only applies to subagents, which R1 rules out.

Documentation sources (fetched 2026-11-07; the build must re-verify against the installed `claude --version`):
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/cli-reference
- https://code.claude.com/docs/en/settings
- https://code.claude.com/docs/en/worktrees

### R4. Tamper detection

Automatic FAIL (`reason: tamper`) on any of:
1. **Protected path modified or deleted** between `base_sha` and `head_sha` (`git diff --name-status`; statuses M, D, R count; A counts only under `.claude/**` and `.kf/**`). Adding new tests is allowed; editing existing ones is not. Default protected globs: `tests/**`, `test/**`, `**/__tests__/**`, `**/*.test.*`, `**/*_test.*`, `**/test_*.*`, `**/fixtures/**`, `conftest.py`, `pytest.ini`, `jest.config.*`, `vitest.config.*`, `.github/workflows/**`, `.claude/**`, `.kf/**`, plus the spec's own repo path if the registration names one. A registration may add `allow_modify` globs when the task legitimately edits a protected file.
2. **Test-harness redefinition**: `package.json` `scripts` object differs between base and head (JSON compare, not text diff).
3. **History rewrite**: `base_sha` is not an ancestor of `head_sha`.
4. **Grader self-integrity**: the runner verifies sha256 of the agent file, rubric prompt, probe pool and config against `grader.lock` before every run. Mismatch means the grader refuses to grade (`BLOCKED: grader_error`) and alerts. Workers cannot write the grader host at all; the lock catches operator mistakes and partial deploys.
5. Thresholds and the cap live in grader-host config, not in any repo. A repo file claiming to set them is a protected-path violation under `.kf/**` or `.claude/**` and is otherwise ignored.

### R5. Two-stage verdict, hard gate first

- **Stage 1 (deterministic)**: every executable AC, the tamper check and the hidden probes. Any failure = FAIL. No score can override it.
- **Stage 2 (judgment)**: runs only if Stage 1 passes. Four dimensions scored 0–10 by integer, each with mandatory evidence (file:line, AC id or probe observation):

| Dimension | 10 | 8 | 6 | 4 |
|---|---|---|---|---|
| completeness vs spec | every spec item delivered with cited evidence | every item delivered; only cosmetic gaps the requester would not send back | one item partial or unevidenced | a core item or several items missing |
| regression risk | no behavior outside scope changed; probes clean | out-of-scope edits are mechanical (imports, formatting) | one plausible behavior change outside scope, untested | evident breakage or removed functionality |
| scope creep (features beyond spec) | nothing beyond spec | small enabling additions a spec item needs | one unrequested feature, option or UI element | several unrequested features |
| unrequested changes (unrelated files) | diff confined to files the spec implies | ≤2 incidental edits, each justified by the spec | unrelated refactor or rename in other modules | broad unrelated churn |

- **Pass rule [evaluative]: the minimum dimension score must be ≥ 8.** Not the mean: a mean lets a strong dimension hide a regression, which is exactly the compensation a gamed submission exploits. 8 is anchored as "the requester would not send it back". 7 would admit one partial item; 9 is not used as a gate because LLM scores at 8 vs 9 are unstable run to run, and an unstable gate teaches the worker to retry rather than fix.
- **Evidence post-check (deterministic)**: the runner caps any dimension whose evidence list is empty, or cites a path not in the repo, at 6.
- **Boundary rescoring (Module 12)**: if the minimum score is 7 or 8, the runner runs Stage 2 twice more independently and uses the per-dimension median.
- **Default stance FAIL**: Stage 2 uses the Module 07 adversarial framing ("this submission has at least one significant flaw; find it") and the Module 07 inverse-premise check. Grader crash, timeout, schema-invalid output or a missing `claude` binary yield `BLOCKED: stage2_unavailable`, never PASS. Silent-pass is never allowed (same rule as Contract A).

### R6. Anti-gaming of the grader itself

- **Submission cap: 3 graded attempts per task.** [evaluative] Attempt 1 catches honest misses, attempt 2 is the fix, attempt 3 is margin. The 10-18 incident was two consecutive false reports, so a cap of 3 bounds the damage of a repeat to one escalation. A FAIL on attempt 3 becomes BLOCKED (`cap_reached`) and escalates to David. Attempt 4+ is refused without grading. Only graded attempts count: infrastructure errors and `stage2_unavailable` do not consume one. Resubmitting the same `head_sha` as the previous graded attempt is refused (exit 2) without consuming one.
- **Feedback redaction**: the worker-facing view contains failed AC ids with the grader's literal output, tamper violation paths, probe failures phrased as observations ("GET /pricing returned 500") and, for Stage 2, the failing dimension names with one evidence-cited sentence each. It withholds numeric scores, the probe catalog, the Stage 2 prompt and the boundary-rescore rule. Rubric anchors (the table in R5) are public by design: knowing that complete means "every spec item with evidence" pushes toward the goal. What gets gamed is surface features, and those are what stay private.
- **Hidden probes** (pool on the grader host, every applicable probe runs, URLs sampled per run):
  - P1 cross-target recheck: presence/absence ACs re-checked on the deployed pages from `probe_urls`.
  - P2 untouched-page health: 2 sampled `probe_urls` whose source files are not in the diff must return 200.
  - P3 repo-wide absence: absence ACs re-checked across all files with the same extensions as the AC paths, not only the listed paths.
  - P4 full regression suite: the registration's `test_command`, if present.
  - P5 deploy/commit match: if the registration has `deployed_sha_probe {url, regex}`, the deployed build SHA must equal `head_sha`.
- **Model diversity [predictive, moderate confidence]**: run Stage 2 on a different model than the worker where the account allows it (config `stage2_model`, per-agent `worker_model`; default rule: if the worker runs `opus`, grade with `fable` when available, else `opus`). Claude Code exposes no temperature flag (cli-reference has none), so diversity comes from model, system prompt (the grader prompt shares nothing with worker prompts), and `omitClaudeMd: true`. Trade-off: a different model reduces correlated blind spots but its score calibration differs, which the canaries and spot-checks absorb. The larger blind-spot reduction comes from Stage 1 being code, not from model choice; same-model grading with this prompt is acceptable.

### R7. Verdict integrity

- **Verdict file**: `store/verdicts/<task_id>/attempt-<n>.json` on the grader host, with a copy pushed to Orchestra as an artifact once that integration exists. Fields: task id, attempt, UTC timestamp, repo, base/head SHA, spec sha256, grader version and lock hash, mode (shadow/enforce), every Stage 1 check with its literal output (4 KB cap per check), tamper result, probe results, Stage 2 scores and evidence, verdict PASS/FAIL/BLOCKED, reason codes, `content_sha256`, `signature`.
- **Integrity [evaluative]**: a plain hash is recomputable by anyone, so it proves nothing about origin. Verdicts are **signed with ed25519**; the private key exists only on the grader host. Anyone can verify offline with the public key (`kf-grade verify`), including hooks on the worker machine.
- **Enforcement point**:
  1. **Primary (hard gate)**: the completion consumer (cos-manager dispatch gate, later Orchestra `complete_artifact`) marks a task done only when `kf-grade verify --task-id T --head-sha <delivered head>` exits 0. A worker's claim cannot satisfy it, and a later commit invalidates it (verdict is bound to `head_sha`).
  2. **Secondary (nudge)**: a `Stop` hook deployed via managed settings on the worker machine (`/Library/Application Support/ClaudeCode/managed-settings.d/50-kf-grader.json` on macOS). When an active task exists for the repo, the last assistant message contains completion language, and `verify` fails, the hook returns `{"decision":"block","reason":"Run kf-grade submit ..."}`. It blocks once: if `stop_hook_active` is true it allows the stop, because the hard gate catches anything that slips. Managed hooks cannot be switched off by `disableAllHooks` in user or project settings.
- Hook behavior verified against https://code.claude.com/docs/en/hooks (Stop and SubagentStop can block via exit 2 or `decision: "block"`; `stop_hook_active` and `last_assistant_message` inputs; managed hooks survive `disableAllHooks` set outside managed settings) and https://code.claude.com/docs/en/managed-settings (paths, `managed-settings.d/` drop-ins). A secondary source reports Claude Code overrides a Stop block after 8 consecutive blocks; unverified against the primary page, and irrelevant here because the hook blocks at most once.

### R8. Grading the grader

- **Canary set** (fixtures in `tools/kf-grader/canaries/`, full list in build prompt §6): 11 known-bad cases (C1–C11) that must FAIL or fail verification, including C1, the 2026-10-18 replay, plus 2 **positive controls that must PASS**. Without positive controls a grader that fails everything passes its own canaries.
- **Go-live gate**: no agent may move to `enforce` until `kf-grade canary --all` matches every expected outcome with Stage 2 enabled on the grader host. Re-run weekly by cron and on any `grader.lock` change. **Any canary mismatch puts the gate fail-closed**: every submission returns `BLOCKED: canary_unhealthy` and David is alerted. [evaluative] Fail-closed stalls completions, not work. A gate that degrades to open on its own failure is not a gate.
- **Human spot-check**: David re-verifies 20% of PASS verdicts, minimum 1 and maximum 3 per week, selected by the grader host (never by the worker), always including PASSes whose minimum Stage 2 score equals the threshold. `kf-grade spotcheck record` logs ok/false_pass. Every false pass becomes a new canary (`kf-grade canary add-from --task-id`), so the grader's misses turn into deterministic regression tests.
- **Drift alarms** (pure functions, Module 16):
  - `first_attempt_pass_rate` per agent, rolling 20 graded tasks. Alarm when the current window's Wilson lower bound exceeds the previous window's Wilson upper bound (a significant jump), or the rate exceeds 0.9.
  - `threshold_clustering`: share of PASS verdicts whose minimum Stage 2 score equals the threshold, last 20 PASSes. Alarm above 0.5. This is the Module 15 uniform-score gaming check applied to the grader.
  - `grader_false_pass_rate`: spot-check false passes / spot-checks, reported with Wilson interval.

### R9. How other agents query it

- **Interface [evaluative]**: one CLI, `kf-grade`, reached over SSH forced commands on the grader host. Two keys: the **worker key** (`authorized_keys` forced command allows only `submit` and `status`) and the **dispatcher key** (`register`, `digest`, `spotcheck`, `canary`). No new service, no new vendor, existing SSH auth.
  - Rejected: subagent invocation (R1). MCP tool: viable later as a thin wrapper over the same CLI for agents without a shell, not needed for cos-dev. Orchestra message: the right async path for non-shell agents (semalytics-gtm, semalytics-ads if they run without a shell); Phase 3.
- **Input schema** (`submit`): `{task_id, head_sha}`. That is all.
- **Output schema**: worker-facing view `{task_id, attempt, verdict, reasons[], failed_acs[{id, output}], tamper_violations[], observations[], stage2_failed_dimensions[{dimension, reason}], attempts_remaining, verdict_ref}`. Exit codes: 0 PASS, 1 FAIL, 2 refused/usage, 3 BLOCKED, 4 PENDING.
- **Rollout (per agent, config `agents.<name>.mode: off | shadow | enforce`)**: cos-dev `shadow` for 10 graded tasks (verdicts recorded, not enforced; David compares with his own judgment), then `enforce`. Then sem-tools (code-heavy), then semalytics-gtm and semalytics-ads (judgment-heavy; see R10). `off` restores current behavior exactly: the hook no-ops and the dispatch gate falls back to the paste rule.
- **2026-10-18 paste-the-output rule**: kept while an agent is `off` or `shadow`. **Superseded** for an agent in `enforce`: the completion report cites `verdict_ref` instead of pasting output, because the grader's output is the evidence and pasted output adds nothing the gate trusts.

### R10. Future extension: content work (analysis only)

The same failure class applies to Site Monitor's full-auto fix queue, and it is sharper there: a fixer that can read the SEMalytics scorer's function, weights or exemplar texts can raise the score by matching surface features the scorer rewards without making the copy better for a real reader. The scorer then measures the fixer's model of the scorer. Recommendation: content grading needs **both** a held-out scorer component the fixer never sees (weights and at least one framework withheld from the fixer's context, run only by the grader) **and** held-out test texts or reader checks (a fixed panel of pages with human-rated quality, re-scored after each scorer change, so a scorer drift that rewards gaming shows up as disagreement with the panel). A score-delta cap per fix cycle (large jumps go to human review) is the cheap first defense. No design or build in this run.

### R11. Costs

All figures are estimates [predictive]; assumptions stated.

- **Per task tokens**: Stage 1 uses none. Stage 2 per run ≈ 15–45K input (spec ≤8K, diff inline ≤30K, else file list plus Read calls; rubric and prompt ~3K) and 2–4K output. Assuming 1.5 submissions per task, Stage 1 passing on ~70% of them, and boundary rescoring on ~15% of Stage 2 runs: ≈ 1.5 × 0.7 × 1.3 ≈ 1.4 Stage 2 runs per task, ≈ 40–100K tokens per task. `--max-budget-usd 3` caps a single run.
- **Per task runtime**: Stage 1 0.5–5 min (dominated by the project's own test suite); Stage 2 2–6 min per run.
- **Phase 2 build effort**: this prompt, one Claude Code run (est. 4–8 agent hours across M1–M3). David one-time: grader host setup 2–3 h (Docker, Unix user, keys, `claude setup-token`), canary review 1 h, shadow review of 10 cos-dev tasks ~1.5 h.
- **David ongoing**: weekly digest 10 min + spot-checks ≤3 × 10 min + escalations ~2 × 5–10 min ≈ **40–60 min/week at ≤15 graded tasks/week**. Above ~25 tasks/week the spot-check cap holds time constant but widens the false-pass interval, and escalations grow with volume. **Flag**: the ≤1 founder-hour/week target holds only if escalation volume stays at ~2/week; if BLOCKED escalations exceed 4/week, the fix is better ACs at registration, not more of David's time.
