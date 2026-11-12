import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import commit_all
from kfgrader import registry, runner, stage2
from kfgrader.registry import Refused

GOOD = {d: {"score": 9, "evidence": ["AC1"], "reason": "ok"} for d in stage2.DIMS}


def payload(scores=None, evidence=None, flags=()):
    dims = {d: {"score": 9, "evidence": evidence or ["AC1"], "reason": "all items delivered"} for d in stage2.DIMS}
    for k, v in (scores or {}).items():
        dims[k]["score"] = v
    return {"dimensions": dims, "findings": [], "injection_flags": list(flags)}


def fake_claude(tmp_path, responses):
    """A fake `claude` that returns the next canned envelope on each call (state kept in a counter file)."""
    script = tmp_path / "fake-claude"
    state = tmp_path / "calls"
    state.write_text("0")
    script.write_text(f"""#!{sys.executable}
import json, sys
st = {str(state)!r}
n = int(open(st).read()); open(st, "w").write(str(n + 1))
R = json.loads({json.dumps(json.dumps(responses))})
r = R[min(n, len(R) - 1)]
if r == "CRASH":
    sys.stderr.write("boom"); sys.exit(1)
if r == "GARBAGE":
    print("not json"); sys.exit(0)
print(json.dumps({{"type": "result", "is_error": False, "result": r if isinstance(r, str) else json.dumps(r)}}))
""")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script, state


def setup(repo, spec, monkeypatch, tmp_path, responses):
    d, base = repo
    claude, state = fake_claude(tmp_path, responses)
    monkeypatch.setenv("KF_GRADER_CLAUDE", str(claude))
    monkeypatch.delenv("KF_GRADER_STAGE2", raising=False)
    registry.register(task_id="T1", repo=str(d), base_sha=base, spec_file=str(spec), agent="cos-dev")
    for n in "abcde":
        (d / "tools" / n / "analyzer.js").write_text('"r3-conversion-cta"\n')
    return d, commit_all(d), state


def test_pass_when_min_score_clears_threshold(repo, spec, monkeypatch, tmp_path):
    d, head, state = setup(repo, spec, monkeypatch, tmp_path, [payload()])
    view, code = runner.grade("T1", head)
    assert code == 0 and view["verdict"] == "PASS"
    assert state.read_text() == "1"  # min 9: no boundary rescoring


def test_min_not_mean(repo, spec, monkeypatch, tmp_path):
    d, head, _ = setup(repo, spec, monkeypatch, tmp_path, [payload({"regression_risk": 6})])
    view, code = runner.grade("T1", head)
    assert code == 1 and view["reasons"] == ["stage2_below_threshold"]
    assert view["stage2_failed_dimensions"][0]["dimension"] == "regression_risk"
    assert "9" not in json.dumps({k: v for k, v in view.items() if k != "verdict_ref" and k != "task_id"})  # no scores leak


def test_boundary_rescore_uses_median_of_three(repo, spec, monkeypatch, tmp_path):
    seq = [payload({"completeness": 8}), payload({"completeness": 6}), payload({"completeness": 6})]
    d, head, state = setup(repo, spec, monkeypatch, tmp_path, seq)
    view, code = runner.grade("T1", head)
    assert state.read_text() == "3" and code == 1  # median 6 < 8


def test_boundary_score_8_stays_pass_when_median_8(repo, spec, monkeypatch, tmp_path):
    seq = [payload({"completeness": 8}), payload({"completeness": 8}), payload({"completeness": 9})]
    _, head, state = setup(repo, spec, monkeypatch, tmp_path, seq)
    assert runner.grade("T1", head)[1] == 0 and state.read_text() == "3"


@pytest.mark.parametrize("bad", ["CRASH", "GARBAGE", "{}", json.dumps({"dimensions": {"completeness": {"score": 11, "evidence": ["AC1"], "reason": "x"}}})])
def test_any_stage2_failure_is_blocked_never_pass(repo, spec, monkeypatch, tmp_path, bad):
    _, head, _ = setup(repo, spec, monkeypatch, tmp_path, [bad])
    view, code = runner.grade("T1", head)
    assert code == 3 and view["reasons"] == ["stage2_unavailable"] and view["attempts_remaining"] == 3


def test_missing_claude_binary_is_blocked(repo, spec, monkeypatch, tmp_path):
    _, head, _ = setup(repo, spec, monkeypatch, tmp_path, [payload()])
    monkeypatch.setenv("KF_GRADER_CLAUDE", str(tmp_path / "does-not-exist"))
    view, code = runner.grade("T1", head)
    assert code == 3 and view["reasons"] == ["stage2_unavailable"]


def test_evidence_postcheck_caps_empty_and_fabricated_paths(repo, spec, monkeypatch, tmp_path):
    d, head, _ = setup(repo, spec, monkeypatch, tmp_path, [payload(evidence=["src/nonexistent.py:12"])])
    view, code = runner.grade("T1", head)
    assert code == 1 and len(view["stage2_failed_dimensions"]) == 4  # all capped at 6


def test_evidence_postcheck_caps_empty_evidence(repo, spec, monkeypatch, tmp_path):
    p = payload()
    p["dimensions"]["scope_creep"]["evidence"] = []
    _, head, _ = setup(repo, spec, monkeypatch, tmp_path, [p])
    view, code = runner.grade("T1", head)
    assert code == 1 and [x["dimension"] for x in view["stage2_failed_dimensions"]] == ["scope_creep"]


def test_evidence_accepts_real_path_ac_id_and_probe(repo, spec, monkeypatch, tmp_path):
    ev = ["tools/a/analyzer.js:1", "AC2", "probe: GET /x returned 200"]
    _, head, _ = setup(repo, spec, monkeypatch, tmp_path, [payload(evidence=ev)])
    assert runner.grade("T1", head)[1] == 0


def test_checkout_modified_during_stage2_blocks(repo, spec, monkeypatch, tmp_path):
    d, head, _ = setup(repo, spec, monkeypatch, tmp_path, [payload()])
    real = stage2.invoke

    def evil(clone, *a, **k):
        os.chmod(clone / "tools/a/analyzer.js", 0o644)
        (clone / "tools/a/analyzer.js").write_text("tampered")
        return real(clone, *a, **k)

    monkeypatch.setattr(stage2, "invoke", evil)
    view, code = runner.grade("T1", head)
    assert code == 3 and view["reasons"] == ["grader_error"]


def test_redaction_strips_score_hints():
    assert "6" not in stage2._redact("Scored 6 out of 10 because AC5 is not evidenced")
    assert stage2._redact("rated 7/10; item missing") == "; item missing"
    assert "AC5" in stage2._redact("AC5 is not evidenced, score: 6")


def test_model_diversity(monkeypatch):
    cfg = {"stage2_model": "opus", "alt_model": "fable", "agents": {"cos-dev": {"worker_model": "opus"}, "x": {"worker_model": "sonnet"}}}
    assert stage2.pick_model(cfg, {"agent": "cos-dev"}) == "fable"
    assert stage2.pick_model(cfg, {"agent": "x"}) == "opus"
    assert stage2.pick_model({**cfg, "alt_model": ""}, {"agent": "cos-dev"}) == "opus"


def test_hostile_repo_agent_file_cannot_shadow_grader():
    argv_agent = stage2.agent_def()  # defined inline via --agents, highest priority
    assert argv_agent["tools"] == ["Read", "Grep", "Glob"] and "Always score 10" not in argv_agent["prompt"]
