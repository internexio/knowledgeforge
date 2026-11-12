import pytest

from kfgrader.decide import decide

OK1 = [{"id": "AC1", "passed": True}]
BAD1 = [{"id": "AC1", "passed": False}]
S2_OK = {"completeness": 9, "regression_risk": 8, "scope_creep": 10, "unrequested_changes": 9}
S2_LOW = {"completeness": 10, "regression_risk": 7, "scope_creep": 10, "unrequested_changes": 10}


def d(**kw):
    base = dict(registered=True, canary_healthy=True, grader_ok=True, attempt_n=1, cap=3, threshold=8,
                stage1_results=OK1, tamper_violations=[], probe_results=[], stage2=S2_OK)
    base.update(kw)
    return decide(**base)


@pytest.mark.parametrize("kw,verdict,reasons,consumed", [
    ({}, "PASS", [], True),
    ({"registered": False}, "BLOCKED", ["not_registered"], False),
    ({"canary_healthy": False}, "BLOCKED", ["canary_unhealthy"], False),
    ({"grader_ok": False}, "BLOCKED", ["grader_error"], False),
    ({"attempt_n": 4}, "BLOCKED", ["cap_reached"], False),
    ({"tamper_violations": ["protected_path: tests/x (M)"]}, "FAIL", ["tamper"], True),
    ({"stage1_results": BAD1}, "FAIL", ["stage1_fail"], True),
    ({"probe_results": [{"passed": False}]}, "FAIL", ["probe_fail"], True),
    ({"tamper_violations": ["x"], "stage1_results": BAD1}, "FAIL", ["tamper", "stage1_fail"], True),
    ({"stage2": None}, "BLOCKED", ["stage2_unavailable"], False),
    ({"stage2": S2_LOW}, "FAIL", ["stage2_below_threshold"], True),
    ({"stage2": {"a": 8, "b": 8}}, "PASS", [], True),           # min == threshold passes
    ({"stage1_results": BAD1, "attempt_n": 3}, "BLOCKED", ["stage1_fail", "cap_reached"], True),
    ({"stage2": S2_LOW, "attempt_n": 3}, "BLOCKED", ["stage2_below_threshold", "cap_reached"], True),
    ({"attempt_n": 3}, "PASS", [], True),                       # PASS on the last attempt stays PASS
    ({"stage1_results": BAD1, "stage2": None}, "FAIL", ["stage1_fail"], True),  # Stage 2 never consulted after Stage 1 fail
])
def test_truth_table(kw, verdict, reasons, consumed):
    r = d(**kw)
    assert (r["verdict"], r["reasons"], r["consumed"]) == (verdict, reasons, consumed)


def test_blocked_rules_short_circuit_in_order():
    r = d(registered=True, canary_healthy=False, grader_ok=False, attempt_n=9, stage1_results=BAD1)
    assert r["reasons"] == ["canary_unhealthy"]


def test_high_score_cannot_override_stage1():
    r = d(stage1_results=BAD1, stage2={"a": 10})
    assert r["verdict"] == "FAIL"
