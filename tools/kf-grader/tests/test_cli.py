import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import commit_all, git

KF = str(Path(__file__).resolve().parent.parent / "bin" / "kf-grade")


def kf(*args, env=None):
    r = subprocess.run([sys.executable, KF, *args], capture_output=True, text=True, env={**os.environ, **(env or {})})
    return r.returncode, r.stdout, r.stderr


def reg(repo, spec, task="T1"):
    d, base = repo
    rc, out, err = kf("register", "--task-id", task, "--repo", str(d), "--base-sha", base, "--spec", str(spec), "--agent", "cos-dev")
    assert rc == 0, err
    return d, base


def fix_all(d):
    for n in "abcde":
        (d / "tools" / n / "analyzer.js").write_text('"r3-conversion-cta"\n')


def test_register_is_immutable_and_validates(repo, spec):
    reg(repo, spec)
    d, base = repo
    rc, _, err = kf("register", "--task-id", "T1", "--repo", str(d), "--base-sha", base, "--spec", str(spec))
    assert rc == 2 and "already registered" in err
    rc, _, err = kf("register", "--task-id", "../x", "--repo", str(d), "--base-sha", base, "--spec", str(spec))
    assert rc == 2
    prose = spec.parent / "prose.md"
    prose.write_text("no ac block here")
    rc, _, err = kf("register", "--task-id", "T2", "--repo", str(d), "--base-sha", base, "--spec", str(prose))
    assert rc == 2 and "kf-acceptance" in err


def test_unknown_flag_and_bad_sha_exit_2(repo, spec):
    reg(repo, spec)
    assert kf("submit", "--task-id", "T1", "--head-sha", "abc", "--wait")[0] == 2
    assert kf("submit", "--task-id", "T1", "--head-sha", "a" * 40, "--bogus")[0] == 2


def test_unregistered_is_blocked(repo):
    rc, out, _ = kf("submit", "--task-id", "nope", "--head-sha", "a" * 40, "--wait")
    assert rc == 3 and json.loads(out)["reasons"] == ["not_registered"]


def test_report_only_fails_then_resubmit_refused_then_pass_needs_stage2(repo, spec):
    d, base = reg(repo, spec)
    (d / "REPORT.md").write_text("All acceptance criteria met.\n")
    h1 = commit_all(d)
    rc, out, _ = kf("submit", "--task-id", "T1", "--head-sha", h1, "--wait")
    v = json.loads(out)
    assert rc == 1 and v["verdict"] == "FAIL" and {a["id"] for a in v["failed_acs"]} >= {"AC1", "AC2"}
    assert v["attempts_remaining"] == 2
    assert "score" not in out  # redaction: no numeric scores in the worker view
    assert kf("submit", "--task-id", "T1", "--head-sha", h1, "--wait")[0] == 2
    fix_all(d)
    h2 = commit_all(d)
    rc, out, _ = kf("submit", "--task-id", "T1", "--head-sha", h2, "--wait")
    assert rc == 3 and json.loads(out)["reasons"] == ["stage2_unavailable"]
    assert json.loads(out)["attempts_remaining"] == 2  # stage2_unavailable did not consume an attempt
    assert kf("verify", "--task-id", "T1", "--head-sha", h2, "--allow-test")[0] == 1


def test_cap_converts_third_fail_to_blocked(repo, spec):
    d, _ = reg(repo, spec)
    codes = []
    for i in range(4):
        (d / "REPORT.md").write_text(f"try {i}\n")
        rc, out, _ = kf("submit", "--task-id", "T1", "--head-sha", commit_all(d), "--wait")
        codes.append((rc, json.loads(out)["reasons"]))
    assert codes[0][0] == 1 and codes[1][0] == 1
    assert codes[2][0] == 3 and "cap_reached" in codes[2][1] and "stage1_fail" in codes[2][1]
    assert codes[3] == (3, ["cap_reached"])


def test_subprocess_sandbox_refused_outside_test_mode(repo, spec):
    d, _ = reg(repo, spec)
    (d / "x").write_text("x")
    rc, _, err = kf("submit", "--task-id", "T1", "--head-sha", commit_all(d), "--wait", env={"KF_GRADER_TEST_MODE": ""})
    assert rc == 2 and "subprocess" in err


def test_grader_lock_mismatch_blocks_not_passes(repo, spec, grader_env):
    d, _ = reg(repo, spec)
    (grader_env / "config" / "grader.yaml").write_text("threshold: 1\ncap: 3\n")  # operator edit without lock refresh
    (d / "x").write_text("x")
    rc, out, _ = kf("submit", "--task-id", "T1", "--head-sha", commit_all(d), "--wait")
    assert rc == 3 and json.loads(out)["reasons"] == ["grader_error"]


def test_canary_unhealthy_is_fail_closed(repo, spec, grader_env):
    d, _ = reg(repo, spec)
    (grader_env / "ledger").mkdir(exist_ok=True)
    (grader_env / "ledger" / "canary_state.json").write_text('{"healthy": false}')
    (d / "x").write_text("x")
    rc, out, _ = kf("submit", "--task-id", "T1", "--head-sha", commit_all(d), "--wait")
    assert rc == 3 and json.loads(out)["reasons"] == ["canary_unhealthy"]


def test_canary_suite_with_stage2_off(grader_env):
    rc, out, _ = kf("canary", "--all", "--json")
    res = json.loads(out)
    assert rc in (0, 5), out
    assert all(r["status"] != "mismatch" for r in res["results"]), res


def test_worker_view_never_contains_stage2_scores():
    from kfgrader import runner

    v = {"task_id": "T", "attempt": 1, "verdict": "FAIL", "reasons": ["stage2_below_threshold"], "graded_total": 1,
         "stage2": {"dimensions": {"completeness": {"score": 6, "failed": True, "reason": "AC5 not evidenced"}}}}
    view = runner.worker_view(v, 3)
    assert view["stage2_failed_dimensions"] == [{"dimension": "completeness", "reason": "AC5 not evidenced"}]
    assert "6" not in json.dumps(view)
