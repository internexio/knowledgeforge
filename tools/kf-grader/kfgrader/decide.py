"""Pure decision function (build prompt 4.6). No I/O. Truth-table tested."""
from __future__ import annotations

PASS, FAIL, BLOCKED = "PASS", "FAIL", "BLOCKED"


def decide(
    *,
    registered: bool,
    canary_healthy: bool,
    grader_ok: bool,
    attempt_n: int,
    cap: int,
    threshold: int,
    stage1_results: list[dict],
    tamper_violations: list[str],
    probe_results: list[dict],
    stage2: dict | None,
) -> dict:
    """Return {verdict, reasons, consumed}. `consumed` = this submission counts as a graded attempt.

    stage2 is None or {dimension: int score}. Order is fixed by the spec; BLOCKED rules short-circuit,
    FAIL reasons accumulate.
    """
    if not registered:
        return {"verdict": BLOCKED, "reasons": ["not_registered"], "consumed": False}
    if not canary_healthy:
        return {"verdict": BLOCKED, "reasons": ["canary_unhealthy"], "consumed": False}
    if not grader_ok:
        return {"verdict": BLOCKED, "reasons": ["grader_error"], "consumed": False}
    if attempt_n > cap:
        return {"verdict": BLOCKED, "reasons": ["cap_reached"], "consumed": False}

    reasons: list[str] = []
    if tamper_violations:
        reasons.append("tamper")
    if any(not r.get("passed") for r in stage1_results):
        reasons.append("stage1_fail")
    if any(not r.get("passed") for r in probe_results):
        reasons.append("probe_fail")

    if not reasons:
        if not stage2:
            return {"verdict": BLOCKED, "reasons": ["stage2_unavailable"], "consumed": False}
        if min(stage2.values()) < threshold:
            reasons.append("stage2_below_threshold")

    if not reasons:
        return {"verdict": PASS, "reasons": [], "consumed": True}
    if attempt_n == cap:
        return {"verdict": BLOCKED, "reasons": reasons + ["cap_reached"], "consumed": True}
    return {"verdict": FAIL, "reasons": reasons, "consumed": True}
