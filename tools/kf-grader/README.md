# kf-grader: KnowledgeForge Completion Gate

An independent grader for agent work. A worker submits two values, `task_id` and `head_sha`. The grader clones the repo itself, runs every executable acceptance criterion, checks for tampering, runs hidden probes, and only then asks an LLM to score the qualitative dimensions. A signed verdict file, not the worker's claim, decides whether the work is done.

This is the reference implementation of [Module 30 (Completion Gate)](../../modules/30_Completion_Gate.md). The design and its rationale are in [`docs/recommendations/grader-agent-rec-2026-11-07.md`](../../docs/recommendations/grader-agent-rec-2026-11-07.md). To run it on real hosts, follow [`INSTALL.md`](INSTALL.md).

## Why it exists

On 2026-10-18 two consecutive build cycles reported "all acceptance criteria met" while the code was missing. Every miss was detectable by a grep already in the prompt. Pasting the command output per criterion still trusts the worker to paste honestly. The root cause is structural: an agent that produces work and sees its own grading drifts toward the grader instead of the goal.

The fix is a grader the worker cannot steer. The LLM is the smallest possible part of it. Stage 1, tamper detection, the attempt cap, signing and the final verdict are code. The LLM only scores qualitative dimensions, and only after code has already said the work exists.

## How a submission flows

```
dispatcher: kf-grade register        worker: kf-grade submit --task-id T --head-sha SHA
      |                                        |
      v                                        v
  registration (spec snapshot + sha256)   fresh clone at head_sha
                                               |
                          Stage 1 (code, no LLM, Docker sandbox)
                            executable ACs, tamper check, hidden probes
                                               |  any failure = FAIL
                                               v
                          Stage 2 (headless claude, Read/Grep/Glob only)
                            4 dimensions scored 0-10, pass if minimum >= 8
                                               |
                          decide() -> ed25519-signed verdict -> store
                                               |
              completion consumer: kf-grade verify --task-id T --head-sha SHA  (exit 0 = done)
```

## What it checks

| Layer | What |
|---|---|
| Acceptance criteria | Five AC types in a ` ```yaml kf-acceptance ` block: `command` (runs in a container), `grep_count`, `http_status`, `dom_check` (static HTML only), `judgment` (goes to Stage 2). A spec with no executable AC is refused at registration. |
| Tamper | Modified or deleted protected paths (tests, fixtures, workflows, `.claude/**`, `.kf/**`), a changed `package.json` `scripts` object, or a `base_sha` that is not an ancestor of `head_sha`. Adding new test files is allowed. |
| Hidden probes | P1 sibling-page selector recheck, P2 untouched-page health, P3 repo-wide absence, P4 the registration's `test_command`, P5 deployed build SHA equals `head_sha`. |
| Stage 2 | completeness, regression risk, scope creep, unrequested changes. Pass rule is the minimum, not the mean. Scores with no real evidence are capped at 6. A minimum of 7 or 8 triggers two more runs and a per-dimension median. |

A crash, timeout, schema-invalid output or missing `claude` binary yields `BLOCKED`, never `PASS`. Each worker gets 3 graded attempts per task, and the worker-facing view never contains scores or the probe catalog.

## Commands

| Command | Who | Purpose |
|---|---|---|
| `kf-grade init` | operator | create the store layout, ed25519 keypair, config and `grader.lock` |
| `kf-grade lock --refresh` | operator | re-record config and agent file hashes after an intentional change |
| `kf-grade register ...` | dispatcher | snapshot a task spec (`--task-id --repo --base-sha --spec`, optional `--agent --target-url --probe-urls --test-command --allow-modify --network --deployed-sha-probe`) |
| `kf-grade submit --task-id T --head-sha SHA [--wait]` | worker | grade a submission |
| `kf-grade status --task-id T` | worker | latest worker-view verdict |
| `kf-grade verify --task-id T --head-sha SHA [--allow-test]` | anyone | exit 0 only if a signed PASS verdict exists for exactly that SHA |
| `kf-grade canary [--all \| --id ID \| add-from --task-id T]` | dispatcher | run the canary suite, or turn a false pass into a new canary |
| `kf-grade digest [--since DATE] [--json]` | dispatcher | weekly digest with drift alarms |
| `kf-grade spotcheck [next \| record ...]` | dispatcher | pick and log human spot-checks |

Exit codes for `submit` and `status`: 0 PASS, 1 FAIL, 2 refused or usage error, 3 BLOCKED, 4 PENDING. For `canary`: 0 all outcomes as expected, 1 any mismatch, 5 incomplete (Stage 2 off or unavailable).

Over SSH, two forced-command keys split the commands: the worker key allows `submit`, `status` and `verify`, and the dispatcher key adds the rest. See `install/authorized_keys.example`.

## Layout

| Path | Role |
|---|---|
| `bin/kf-grade` | CLI entrypoint (re-execs under a Python that has PyYAML and cryptography if the first one lacks them) |
| `bin/kf-grade-ssh` | SSH forced-command gate |
| `kfgrader/decide.py` | pure decision function, truth-table tested |
| `kfgrader/acs.py`, `sandbox.py` | AC block parser and executors; Docker sandbox (the subprocess backend is test-only) |
| `kfgrader/tamper.py`, `probes.py` | tamper detection, hidden probes P1 to P5 |
| `kfgrader/stage2.py` | headless Stage 2 invocation, schema validation, evidence post-check, boundary rescoring |
| `kfgrader/verdict.py`, `kfgrader/runner.py` | signing and verification, orchestration, attempt cap, redacted worker view |
| `kfgrader/metrics.py`, `canary.py`, `ssh_gate.py` | drift alarms, digest and spot-checks; canary suite; SSH gate |
| `agent/kf-grader.md` | the Stage 2 grader agent definition (read-only tools) |
| `hooks/` | worker-machine Stop hook and its managed-settings snippet |
| `canaries/` | fixture builder, patches and expected outcomes for 13 canaries |
| `schemas/`, `config/`, `runner/Dockerfile`, `install/` | JSON schemas, default config, sandbox image, SSH key template |

## Quick start (no Docker, no LLM)

```bash
cd tools/kf-grader
python3.11 -m pip install -e '.[dev]'     # PyYAML, cryptography, pytest
python3.11 -m pytest -q -p no:cacheprovider tests
export KF_GRADER_HOME=$(mktemp -d) KF_GRADER_TEST_MODE=1 KF_GRADER_SANDBOX=subprocess KF_GRADER_STAGE2=off
bin/kf-grade canary --all                  # exit 5: Stage 2 canaries are incomplete with Stage 2 off
```

Without `KF_GRADER_TEST_MODE=1`, `KF_GRADER_SANDBOX=subprocess` is refused, and `verify` rejects test-mode verdicts unless you pass `--allow-test`. Python 3.11 or newer is required.

The suite has 117 tests. Four of them exercise the real Docker sandbox and skip cleanly when Docker or the `kf-grader-runner` image is missing; build it with `docker build -t kf-grader-runner runner`. Run those at least once before trusting the sandbox, because the subprocess backend cannot see Docker-only failures.

## Canaries

The suite holds 11 known-bad submissions (C1 to C11, including a replay of the 2026-10-18 incident) that must FAIL, and 2 positive controls (K1, K2) that must PASS. A grader that fails everything would pass its own bad-case canaries, so the positive controls matter. A canary mismatch puts the gate fail-closed: every submission returns `BLOCKED: canary_unhealthy` until a later full run passes.

## Modes

Per agent in `$KF_GRADER_HOME/config/grader.yaml` (the repo ships defaults in `config/grader.defaults.yaml`): `off` restores current behavior exactly, `shadow` records verdicts without enforcing them, and `enforce` makes the verdict the completion condition. Move an agent out of `off` only after `kf-grade canary --all` matches every outcome with Stage 2 enabled.

## Environment

| Variable | Meaning |
|---|---|
| `KF_GRADER_HOME` | store root (default `/opt/kf-grader`) |
| `KF_GRADER_MODE` | `local`, or `ssh` to forward commands to the grader host (needs `KF_GRADER_SSH_TARGET`) |
| `KF_GRADER_SANDBOX` | `docker` (production default) or `subprocess` (test only) |
| `KF_GRADER_TEST_MODE=1` | tests only; stamps verdicts `test_mode: true` |
| `KF_GRADER_STAGE2=off` | skip Stage 2; a submission that passes Stage 1 then returns `BLOCKED: stage2_unavailable` |
| `KF_GRADER_CLAUDE`, `KF_GRADER_PYTHON` | path to `claude`; interpreter for the re-exec |

## Known limits

- The gate is only as strong as the registered checks. A `grep_count` for a feature string can be satisfied by a comment, so pair it with a `command` or `dom_check` AC.
- `dom_check` parses static HTML only. JavaScript-rendered content needs a `command` AC that runs a headless browser in the container.
- Stage 2 is still an LLM. It is bounded by Stage 1, the evidence check, the canaries and weekly human spot-checks, and is not trusted on its own.
- Not built yet: the Orchestra `complete_artifact` gate, the dispatcher's register wrapper that writes the Stop hook's active-task marker, an MCP wrapper, and content-quality grading.
- If the dispatcher and a worker run as the same Unix user, the worker could read the dispatcher key and register a weaker task. Keep the dispatcher key passphrase-protected and out of agent environments.
