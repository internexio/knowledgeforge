# kf-grader: KnowledgeForge Completion Gate (reference implementation)

An independent grader for agent work. A worker submits two values, `task_id` and `head_sha`. The grader clones the repo itself, runs every executable acceptance criterion, checks for tampering, runs hidden probes, and only then asks an LLM to score the qualitative dimensions. The signed verdict file, not the worker's claim, decides whether the work is done.

Design and rationale: `docs/recommendations/grader-agent-rec-2026-11-07.md`. Module spec: `modules/30_Completion_Gate.md`. Host runbook: `INSTALL.md`.

## Threat model

The worker is trusted to try, not to grade itself. Defended failure class: 2026-10-18, two build cycles reported "all acceptance criteria met" with the code absent. Out of scope here: a worker with shell access on the grader host (workers get a forced-command SSH key that allows `submit` and `status` only).

## Layout

| Path | Role |
|---|---|
| `bin/kf-grade` | CLI entrypoint (re-execs under a python with PyYAML + cryptography if the first one lacks them) |
| `kfgrader/decide.py` | pure decision function, truth-table tested |
| `kfgrader/acs.py`, `sandbox.py` | AC block parser and executors; Docker sandbox (subprocess backend is test-only) |
| `kfgrader/tamper.py` | protected paths, `package.json` scripts diff, history rewrite |
| `kfgrader/verdict.py` | ed25519 signing, `verify` (public key only) |
| `kfgrader/runner.py` | orchestration, attempt cap, redacted worker view |
| `kfgrader/canary.py` | canary suite (known-bad cases and positive controls) |
| `canaries/` | fixture builder, patches, expected outcomes |

## Quick start (tests, no Docker, no LLM)

```bash
cd tools/kf-grader
export KF_GRADER_HOME=$(mktemp -d) KF_GRADER_TEST_MODE=1 KF_GRADER_SANDBOX=subprocess KF_GRADER_STAGE2=off
python3.11 -m pip install -e '.[dev]'   # PyYAML, cryptography, pytest
python3.11 -m pytest -q -p no:cacheprovider tests
bin/kf-grade canary --all               # exit 5 = incomplete (Stage 2 off), 0 = all match, 1 = mismatch
```

Without `KF_GRADER_TEST_MODE=1`, `KF_GRADER_SANDBOX=subprocess` is refused and verdicts are not accepted by `verify` unless `--allow-test` is passed.

## Modes (per agent, `config/grader.yaml`)

`off` restores current behavior exactly. `shadow` records verdicts without enforcing. `enforce` makes the verdict the completion condition.
