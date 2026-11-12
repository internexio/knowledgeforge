# kf-grader install runbook

You execute this. The build did not install anything, write `~/.claude/`, write managed settings, edit Orchestra, or change any live agent's instructions or dispatch rules.

Two machines are involved:

- **Grader host** (home lab: Mac Mini or NAS): runs `kf-grade`, Docker, and the headless `claude` for Stage 2.
- **Worker machine** (where cos-dev and the other workers run): gets the worker SSH key, the Stop hook, and `kf-grade` in client mode.

Every command below says where it runs. Nothing here is destructive; the rollback is at the end.

## 1. Grader host: prerequisites

Run on the grader host as an admin user.

1. Docker running (`docker version` prints a server section).
2. Python 3.11 or newer with the deps: `python3.11 -m pip install PyYAML cryptography` (or `pip install -e /opt/kf-grader-src/tools/kf-grader`).
3. Claude Code installed, version 2.1 or newer (`claude --version`). The build confirmed these flags exist on 2.1.319: `--agent --agents --tools --disallowedTools --json-schema --setting-sources --strict-mcp-config --max-budget-usd --no-session-persistence --permission-mode --max-turns --output-format --add-dir --model`. Re-check on your version: `claude --help | grep -E -- '--(agents|tools|disallowedTools|json-schema|setting-sources)'`.
4. A dedicated Unix user and the store root:

```bash
sudo useradd -m -s /bin/bash kfgrader                       # Linux; on macOS use sysadminctl
sudo install -d -o kfgrader -g kfgrader -m 0750 /opt/kf-grader
sudo install -d -o kfgrader -g kfgrader -m 0700 /opt/kf-grader/keys
sudo -u kfgrader git clone https://github.com/internexio/knowledgeforge /opt/kf-grader-src   # or copy tools/kf-grader here
sudo ln -sfn /opt/kf-grader-src/tools/kf-grader/bin /opt/kf-grader/bin
```

The grader user must hold **no git push credentials and no deploy credentials**. It needs read access to the repos it clones (a read-only deploy key or a local mirror).

## 2. Grader host: initialize

Run as `kfgrader` on the grader host. Success: the last command prints a public key path and `grader.lock` exists.

```bash
sudo -iu kfgrader
export KF_GRADER_HOME=/opt/kf-grader
echo 'export KF_GRADER_HOME=/opt/kf-grader' >> ~/.profile
docker build -t kf-grader-runner /opt/kf-grader-src/tools/kf-grader/runner
/opt/kf-grader/bin/kf-grade init                 # creates layout, ed25519 keypair, config, grader.lock
ls /opt/kf-grader/grader.lock /opt/kf-grader/keys/verdict.pub
claude setup-token                               # authenticates headless Claude Code for the grader user
```

If `docker build` hangs on `load metadata` on macOS, the process to look for is `docker-credential-desktop get` waiting on a Keychain prompt. The base image is public, so build with a throwaway config that has no credential helper: `D=$(mktemp -d); echo '{}' > "$D/config.json"; DOCKER_CONFIG="$D" docker build -t kf-grader-runner /opt/kf-grader-src/tools/kf-grader/runner` (add `DOCKER_HOST=unix://$HOME/.docker/run/docker.sock` if the CLI can't find the socket). Verify the production sandbox once: `cd /opt/kf-grader-src/tools/kf-grader && python3 -m pytest -q tests/test_sandbox_docker.py` (skips if Docker or the image is missing, so check it says `4 passed`).

Install the grader's own Claude settings (deny rules; the agent itself is defined inline by the runner so a graded repo cannot shadow it):

```bash
mkdir -p ~/.claude/agents
cp /opt/kf-grader-src/tools/kf-grader/agent/grader-settings.json ~/.claude/settings.json
cp /opt/kf-grader-src/tools/kf-grader/agent/kf-grader.md ~/.claude/agents/kf-grader.md   # fallback copy for --agent resolution
/opt/kf-grader/bin/kf-grade lock --refresh       # record hashes of the config and agent file in grader.lock
```

Edit `/opt/kf-grader/config/grader.yaml` if needed (threshold, cap, `alt_model`, per-agent `mode`), then run `kf-grade lock --refresh` again. Any later edit to `grader.yaml`, `probes.yaml` or the agent file without a refresh makes every submission return `BLOCKED: grader_error`. That is the intended tripwire.

## 3. Grader host: SSH keys

Create one key pair per worker machine and one for the dispatcher **on the machines that will use them** (`ssh-keygen -t ed25519`). Give the dispatcher key a passphrase and never load it into an agent's environment (residual risk RR1).

Append forced-command lines to `~kfgrader/.ssh/authorized_keys` on the grader host, using `install/authorized_keys.example` as the template. The worker key allows `submit`, `status`, `verify`. The dispatcher key adds `register`, `digest`, `spotcheck`, `canary`. Success check from the worker machine:

```bash
ssh kfgrader@GRADER_HOST 'kf-grade status --task-id nope'    # exit 2 "unknown task_id"; proves the gate answers
ssh kfgrader@GRADER_HOST 'kf-grade register --task-id x'     # exit 2 "denied" with the worker key
```

## 4. Grader host: canary gate (before any agent leaves `off`)

Run as `kfgrader` on the grader host with Stage 2 enabled (do not set `KF_GRADER_STAGE2=off`, do not set `KF_GRADER_TEST_MODE`). Success: exit 0 and every line `match`. Any `mismatch` or `incomplete` means do not enable.

```bash
/opt/kf-grader/bin/kf-grade canary --all
echo "exit=$?"            # must be exit=0
```

A pass writes `ledger/canary_state.json` with `healthy: true`. A mismatch writes `healthy: false`, which fails the gate closed (every submission returns `BLOCKED: canary_unhealthy`) until a later `canary --all` passes. Stage 2 canaries (C6, C8, K1, K2) call the model and take a few minutes.

## 5. Worker machine

Run on the worker machine (the Mac where cos-dev runs).

1. Install a client: copy `tools/kf-grader` to a stable path and put `bin/kf-grade` on `PATH`, then set:

```bash
export KF_GRADER_MODE=ssh
export KF_GRADER_SSH_TARGET=kfgrader@GRADER_HOST
```

2. Install the Stop hook and managed settings (needs sudo; this is the step that makes the hook impossible to disable with `disableAllHooks` in user or project settings):

```bash
sudo install -m 0755 tools/kf-grader/hooks/kf-grade-stop.sh /usr/local/libexec/kf-grade-stop.sh
sudo mkdir -p "/Library/Application Support/ClaudeCode/managed-settings.d"
sudo cp tools/kf-grader/hooks/managed-settings.kf-grader.json "/Library/Application Support/ClaudeCode/managed-settings.d/50-kf-grader.json"
```

3. Confirm inside a Claude Code session with `/status` that the managed settings source is listed.
4. The hook only acts when a repo has an active-task marker. The dispatcher's register wrapper writes `~/.kf-grader/active/<repo-name>.json` containing `{"task_id": "..."}` (build that wrapper in the cos-manager follow-up; until then you can create the file by hand for a test).

## 6. Rollout

Set one agent at a time in `/opt/kf-grader/config/grader.yaml`, then `kf-grade lock --refresh`:

```yaml
agents:
  cos-dev: {mode: shadow, worker_model: opus}
```

- `off`: current behavior exactly (hook no-ops, dispatch gate falls back to the paste rule).
- `shadow`: verdicts recorded, not enforced. Keep cos-dev here for 10 graded tasks and compare each verdict with your own judgment.
- `enforce`: the signed verdict is the completion condition. The completion consumer calls `kf-grade verify --task-id T --head-sha <delivered head>` and accepts only exit 0.

Order: cos-dev, then sem-tools, then semalytics-gtm and semalytics-ads (judgment-heavy; read R10 in the recommendation first).

Weekly cron on the grader host (as `kfgrader`; edit with `crontab -e`, which you run yourself):

```cron
15 6 * * 1  /opt/kf-grader/bin/kf-grade canary --all >> /opt/kf-grader/ledger/canary-cron.log 2>&1
30 6 * * 1  /opt/kf-grader/bin/kf-grade digest --since $(date -v-7d +\%F 2>/dev/null || date -d '7 days ago' +\%F) >> /opt/kf-grader/ledger/digest.log 2>&1
```

Weekly human routine (about 10 minutes plus up to 3 spot-checks):

```bash
ssh kfgrader@GRADER_HOST 'kf-grade digest'
ssh kfgrader@GRADER_HOST 'kf-grade spotcheck next'
# re-verify each selected verdict yourself, then record the result
ssh kfgrader@GRADER_HOST 'kf-grade spotcheck record --verdict-ref verdicts/T1/attempt-1.json --result ok --note "checked"'
ssh kfgrader@GRADER_HOST 'kf-grade canary add-from --task-id T1'   # only after a false_pass
```

## 7. Rollback

- Per agent: set `mode: off` in `grader.yaml`, then `kf-grade lock --refresh`. Behavior reverts to the paste rule.
- Remove the hook: `sudo rm "/Library/Application Support/ClaudeCode/managed-settings.d/50-kf-grader.json"` on the worker machine.
- The grader host can be stopped without affecting workers that are `off`.

## Environment reference

| Variable | Meaning |
|---|---|
| `KF_GRADER_HOME` | store root (default `/opt/kf-grader`) |
| `KF_GRADER_MODE` | `local` (direct) or `ssh` (client forwards to the grader host; needs `KF_GRADER_SSH_TARGET`) |
| `KF_GRADER_SANDBOX` | `docker` (production default) or `subprocess` (refused outside test mode) |
| `KF_GRADER_TEST_MODE=1` | tests only: permits the subprocess sandbox and stamps verdicts `test_mode: true`, which `verify` rejects without `--allow-test` |
| `KF_GRADER_STAGE2=off` | skip Stage 2; a submission that passes Stage 1 returns `BLOCKED: stage2_unavailable` |
| `KF_GRADER_CLAUDE` | path to the `claude` binary (default `claude`) |
| `KF_GRADER_PYTHON` | interpreter for `bin/kf-grade` to re-exec under if the first python lacks PyYAML or cryptography |
