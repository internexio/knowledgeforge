import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import commit_all
from kfgrader import canary, cli, metrics, registry, runner, ssh_gate, verdict
from kfgrader.registry import Refused
from test_stage2 import fake_claude, payload

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- pure metrics (Module 16 metrics 11-13)
def test_wilson_known_values():
    lo, hi = metrics.wilson(5, 20)
    assert (round(lo, 3), round(hi, 3)) == (0.112, 0.469)
    assert metrics.wilson(0, 0) == (0.0, 1.0)
    lo, hi = metrics.wilson(20, 20)
    assert hi == pytest.approx(1.0) and lo > 0.83


@pytest.mark.parametrize("prev,cur,expect", [
    ((2, 20), (19, 20), True),    # significant jump (and > 0.9)
    ((10, 20), (11, 20), False),  # within noise
    ((17, 20), (19, 20), True),   # > 0.9 absolute
    ((2, 19), (19, 20), False),   # previous window incomplete: no alarm
    ((2, 20), (19, 19), False),   # current window incomplete: no alarm
])
def test_first_attempt_alarm(prev, cur, expect):
    assert metrics.first_attempt_alarm(prev[0], prev[1], cur[0], cur[1]) is expect


def test_first_attempt_alarm_wilson_boundary():
    # Alarm iff the current window's Wilson lower bound exceeds the previous window's upper bound (rate stays <= 0.9).
    assert metrics.wilson(12, 20)[0] > metrics.wilson(2, 20)[1]
    assert metrics.first_attempt_alarm(2, 20, 12, 20) is True
    assert metrics.wilson(8, 20)[0] < metrics.wilson(2, 20)[1]
    assert metrics.first_attempt_alarm(2, 20, 8, 20) is False


def test_clustering_alarm():
    assert metrics.clustering_alarm([8] * 6 + [9] * 4, 8) is True       # 0.6 > 0.5
    assert metrics.clustering_alarm([8] * 5 + [9] * 5, 8) is False      # 0.5 is not above 0.5
    assert metrics.clustering_alarm([8] * 9, 8) is False                # fewer than 10 PASSes: insufficient data


def test_spot_check_target_bounds():
    assert [metrics.spot_check_target(n) for n in (0, 1, 5, 6, 15, 16, 100)] == [0, 1, 1, 2, 3, 3, 3]


def test_false_pass_rate_reports_interval():
    r = metrics.false_pass_rate(1, 10)
    assert r["rate"] == 0.1 and r["wilson_95"][0] < 0.1 < r["wilson_95"][1]
    assert metrics.false_pass_rate(0, 0)["rate"] is None


# ---------------------------------------------------------------- ledger, digest, spot-check (needs a real PASS)
def pass_one(repo, spec, monkeypatch, tmp_path, task="T1", scores=None):
    d, base = repo
    claude, _ = fake_claude(tmp_path, [payload(scores)])
    monkeypatch.setenv("KF_GRADER_CLAUDE", str(claude))
    monkeypatch.delenv("KF_GRADER_STAGE2", raising=False)
    registry.register(task_id=task, repo=str(d), base_sha=base, spec_file=str(spec), agent="cos-dev")
    for n in "abcde":
        (d / "tools" / n / "analyzer.js").write_text('"r3-conversion-cta"\n')
    head = commit_all(d)
    view, code = runner.grade(task, head)
    assert code == 0, view
    return d, head, view


def test_metrics_recorded_and_digest(repo, spec, monkeypatch, tmp_path):
    _, head, view = pass_one(repo, spec, monkeypatch, tmp_path)
    h = registry.home()
    rows = metrics._read_jsonl(h / "ledger" / "metrics.jsonl")
    assert len(rows) == 1 and rows[0]["verdict"] == "PASS" and rows[0]["min_stage2"] == 9 and rows[0]["agent"] == "cos-dev"
    d = metrics.build_digest(h, None)
    assert d["agents"]["cos-dev"]["graded_tasks"] == 1
    assert d["registrations_by_key"] == {"local": 1}


def test_spotcheck_next_and_record(repo, spec, monkeypatch, tmp_path):
    _, head, view = pass_one(repo, spec, monkeypatch, tmp_path, scores={"completeness": 8})
    h = registry.home()
    nxt = metrics.spotcheck_next(h)
    assert nxt["target"] == 1 and [s["verdict_ref"] for s in nxt["select"]] == [view["verdict_ref"]]
    rec = metrics.spotcheck_record(h, view["verdict_ref"], "false_pass", "missed the empty hook")
    assert rec["false_passes"] == 1 and "canary add-from --task-id T1" in rec["next"]
    assert metrics.spotcheck_next(h)["select"] == []  # quota met for this week
    with pytest.raises(Refused):
        metrics.spotcheck_record(h, "verdicts/nope.json", "ok", "")
    alerts = metrics._read_jsonl(h / "ledger" / "alerts.jsonl")
    assert alerts and alerts[-1]["kind"] == "false_pass"


def test_spotcheck_prefers_threshold_passes(repo, spec, monkeypatch, tmp_path):
    pass_one(repo, spec, monkeypatch, tmp_path, scores={"completeness": 8})
    nxt = metrics.spotcheck_next(registry.home())
    assert nxt["select"][0]["at_threshold"] is True


def test_add_from_creates_canary_that_replays(repo, spec, monkeypatch, tmp_path):
    pass_one(repo, spec, monkeypatch, tmp_path)
    out = canary.add_from("T1")
    assert out["canary"] == "X-T1"
    with pytest.raises(Refused, match="already exists"):
        canary.add_from("T1")
    # The same fake Stage 2 still passes this submission, so the replay canary must report a mismatch (a false pass persists).
    results, code = canary.run_suite(["X-T1"])
    assert code == 1 and "former false pass must FAIL" in results[0]["detail"]


def test_add_from_requires_signed_pass(repo, spec):
    d, base = repo
    registry.register(task_id="T9", repo=str(d), base_sha=base, spec_file=str(spec), agent="cos-dev")
    with pytest.raises(Refused, match="no signed PASS"):
        canary.add_from("T9")


# ---------------------------------------------------------------- SSH gate
SHA = "a" * 40


@pytest.mark.parametrize("role,cmd,ok", [
    ("worker", f"kf-grade submit --task-id T --head-sha {SHA} --wait", True),
    ("worker", "status --task-id T", True),
    ("worker", f"verify --task-id T --head-sha {SHA}", True),
    ("worker", "register --task-id T --repo r --base-sha x --spec s", False),
    ("worker", "canary --all", False),
    ("worker", "digest", False),
    ("worker", "bash -c 'id'", False),
    ("dispatcher", "register --task-id T --repo r --base-sha x --spec s --test-command 'a && b; c | d'", True),
    ("dispatcher", "digest --since 2026-11-01", True),
    ("dispatcher", "rm -rf /", False),
    ("nobody", "status --task-id T", False),
])
def test_ssh_gate_roles(role, cmd, ok):
    if ok:
        assert ssh_gate.parse(role, cmd)[0] in ssh_gate.ROLES[role]
    else:
        with pytest.raises(PermissionError):
            ssh_gate.parse(role, cmd)


def test_ssh_gate_rejects_interactive_and_unparseable():
    with pytest.raises(PermissionError, match="interactive"):
        ssh_gate.parse("worker", None)
    with pytest.raises(PermissionError, match="unparseable"):
        ssh_gate.parse("worker", "status --task-id 'unterminated")


def test_ssh_gate_end_to_end_records_key_id(repo, spec, monkeypatch):
    d, base = repo
    monkeypatch.setenv("SSH_ORIGINAL_COMMAND", f"kf-grade register --task-id T1 --repo {d} --base-sha {base} --spec {spec} --agent cos-dev")
    assert ssh_gate.main(["dispatcher", "david"]) == 0
    assert registry.load_registration(registry.ensure_layout(), "T1")["registered_via"] == "dispatcher:david"
    monkeypatch.setenv("SSH_ORIGINAL_COMMAND", "kf-grade register --task-id T2 --repo x --base-sha y --spec z")
    assert ssh_gate.main(["worker", "cos-dev"]) == 2  # denied


def test_ssh_client_mode_forwards_quoted_argv(monkeypatch, tmp_path):
    log = tmp_path / "ssh.log"
    fake = tmp_path / "fake-ssh"
    fake.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$@\" > {log}\nexit 3\n")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("KF_GRADER_MODE", "ssh")
    monkeypatch.setenv("KF_GRADER_SSH_TARGET", "kfgrader@grader.example.invalid")
    monkeypatch.setenv("KF_GRADER_SSH_BIN", str(fake))
    rc = cli.main(["submit", "--task-id", "T 1", "--head-sha", SHA, "--wait"])
    assert rc == 3
    lines = log.read_text().splitlines()
    assert lines[-2] == "kfgrader@grader.example.invalid"
    assert lines[-1] == f"kf-grade submit --task-id 'T 1' --head-sha {SHA} --wait"


def test_ssh_client_mode_requires_target(monkeypatch):
    monkeypatch.setenv("KF_GRADER_MODE", "ssh")
    monkeypatch.delenv("KF_GRADER_SSH_TARGET", raising=False)
    assert cli.main(["status", "--task-id", "T1"]) == 2


# ---------------------------------------------------------------- Stop hook
HOOK = ROOT / "hooks" / "kf-grade-stop.sh"


def run_hook(tmp_path, repo_dir, verify_rc, message, task=True, stop_hook_active=False):
    active = tmp_path / "active"
    active.mkdir(exist_ok=True)
    if task:
        (active / f"{repo_dir.name}.json").write_text(json.dumps({"task_id": "T1"}))
    fake = tmp_path / "kf-grade-fake"
    fake.write_text(f"#!/bin/sh\necho \"$@\" >> {tmp_path / 'verify.log'}\nexit {verify_rc}\n")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "KF_GRADE_BIN": str(fake), "KF_GRADER_ACTIVE_DIR": str(active)}
    payload_ = {"cwd": str(repo_dir), "last_assistant_message": message, "stop_hook_active": stop_hook_active}
    r = subprocess.run(["sh", str(HOOK)], input=json.dumps(payload_), capture_output=True, text=True, env=env)
    assert r.returncode == 0  # a nudge never fails the session
    return r.stdout.strip()


def test_hook_blocks_completion_claim_without_verified_pass(repo, tmp_path):
    d, _ = repo
    out = json.loads(run_hook(tmp_path, d, verify_rc=1, message="All acceptance criteria met. Done."))
    assert out["decision"] == "block" and "kf-grade submit --task-id T1" in out["reason"]
    assert "verify --task-id T1" in (tmp_path / "verify.log").read_text()


def test_hook_allows_when_verified(repo, tmp_path):
    d, _ = repo
    assert run_hook(tmp_path, d, verify_rc=0, message="Done.") == ""


@pytest.mark.parametrize("kw", [
    {"message": "Working on it, three files left."},       # no completion language
    {"message": "Done.", "task": False},                    # no active task for this repo
    {"message": "Done.", "stop_hook_active": True},         # already blocked once: allow
])
def test_hook_allows_otherwise(repo, tmp_path, kw):
    d, _ = repo
    assert run_hook(tmp_path, d, verify_rc=1, **kw) == ""


def test_hook_degrades_to_allow_on_garbage_input(tmp_path):
    r = subprocess.run(["sh", str(HOOK)], input="not json", capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout == ""


def test_managed_settings_is_valid_json_with_stop_hook():
    cfg = json.loads((ROOT / "hooks" / "managed-settings.kf-grader.json").read_text())
    assert cfg["hooks"]["Stop"][0]["hooks"][0]["type"] == "command"
