"""Drift alarms (Module 16 metrics 11-13), weekly digest and human spot-checks. Pure functions first, I/O after."""
from __future__ import annotations

import datetime as dt
import json
import math
import random
from pathlib import Path

from . import registry, verdict
from .registry import Refused

WINDOW = 20


# ---------------------------------------------------------------- pure functions (Module 16)
def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (centre - margin) / d), min(1.0, (centre + margin) / d)


def first_attempt_alarm(prev_passes: int, prev_n: int, cur_passes: int, cur_n: int) -> bool:
    if cur_n < WINDOW or prev_n < WINDOW:
        return False
    if wilson(cur_passes, cur_n)[0] > wilson(prev_passes, prev_n)[1]:
        return True
    return cur_passes / cur_n > 0.9


def clustering_alarm(pass_min_scores: list[int], threshold: int) -> bool:
    if len(pass_min_scores) < 10:
        return False
    return sum(1 for s in pass_min_scores if s == threshold) / len(pass_min_scores) > 0.5


def false_pass_rate(false_passes: int, checks: int) -> dict:
    lo, hi = wilson(false_passes, checks)
    return {"false_passes": false_passes, "spot_checks": checks, "rate": (false_passes / checks) if checks else None,
            "wilson_95": [round(lo, 3), round(hi, 3)]}


def spot_check_target(passes_this_week: int) -> int:
    return 0 if passes_this_week == 0 else min(3, max(1, math.ceil(0.2 * passes_this_week)))


# ---------------------------------------------------------------- ledger I/O
def _ledger(h: Path, name: str) -> Path:
    return h / "ledger" / name


def _read_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    out = []
    for line in p.read_text().splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def _append(p: Path, obj: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a") as f:
        f.write(json.dumps(obj, sort_keys=True) + "\n")


def record(h: Path, v: dict, agent: str | None) -> None:
    scores = [d["score"] for d in ((v.get("stage2") or {}).get("dimensions") or {}).values()]
    _append(_ledger(h, "metrics.jsonl"), {
        "ts": v["timestamp"], "task_id": v["task_id"], "agent": agent or "unknown", "attempt": v["attempt"],
        "graded": v["graded"], "verdict": v["verdict"], "reasons": v["reasons"], "head_sha": v["head_sha"],
        "min_stage2": min(scores) if scores else None, "mode": v.get("mode"), "verdict_ref": v.get("verdict_ref"),
    })


def alert(h: Path, kind: str, detail: str) -> None:
    _append(_ledger(h, "alerts.jsonl"), {"ts": registry.now(), "kind": kind, "detail": detail})


# ---------------------------------------------------------------- digest
def _agent_stats(rows: list[dict], threshold: int) -> dict:
    graded = [r for r in rows if r["graded"]]
    by_task: dict[str, list[dict]] = {}
    for r in graded:
        by_task.setdefault(r["task_id"], []).append(r)
    firsts = [sorted(v, key=lambda r: r["attempt"])[0] for v in by_task.values()]
    firsts.sort(key=lambda r: r["ts"])
    cur, prev = firsts[-WINDOW:], firsts[-2 * WINDOW:-WINDOW]
    cur_p, prev_p = sum(r["verdict"] == "PASS" for r in cur), sum(r["verdict"] == "PASS" for r in prev)
    pass_scores = [r["min_stage2"] for r in graded if r["verdict"] == "PASS" and r["min_stage2"] is not None][-WINDOW:]
    return {
        "graded_tasks": len(by_task),
        "first_attempt_pass_rate": {"current": f"{cur_p}/{len(cur)}", "previous": f"{prev_p}/{len(prev)}",
                                    "alarm": first_attempt_alarm(prev_p, len(prev), cur_p, len(cur))},
        "threshold_clustering": {"passes_in_window": len(pass_scores),
                                 "share": (round(sum(s == threshold for s in pass_scores) / len(pass_scores), 2) if pass_scores else None),
                                 "alarm": clustering_alarm(pass_scores, threshold)},
        "blocked_cap_reached": sum("cap_reached" in r["reasons"] for r in rows),
        "blocked_other": sum(r["verdict"] == "BLOCKED" and "cap_reached" not in r["reasons"] for r in rows),
    }


def build_digest(h: Path, since: str | None) -> dict:
    cfg = registry.load_config(h)
    rows = _read_jsonl(_ledger(h, "metrics.jsonl"))
    if since:
        rows = [r for r in rows if r["ts"][:10] >= since]
    agents = sorted({r["agent"] for r in rows})
    spot = _read_jsonl(_ledger(h, "spotchecks.jsonl"))
    regs = [json.loads(p.read_text()) for p in sorted((h / "registrations").glob("*.json"))]
    canary = {}
    cp = _ledger(h, "canary_state.json")
    if cp.exists():
        canary = json.loads(cp.read_text())
    return {
        "generated_at": registry.now(), "since": since,
        "agents": {a: _agent_stats([r for r in rows if r["agent"] == a], int(cfg["threshold"])) for a in agents},
        "grader_false_pass_rate": false_pass_rate(sum(s["result"] == "false_pass" for s in spot), len(spot)),
        "canary": canary or {"healthy": None, "note": "canary --all has not run on this host"},
        "registrations_by_key": {k: sum(1 for r in regs if r.get("registered_via") == k) for k in sorted({r.get("registered_via", "?") for r in regs})},
        "alerts": _read_jsonl(_ledger(h, "alerts.jsonl"))[-10:],
    }


# ---------------------------------------------------------------- spot-check
def spotcheck_next(h: Path) -> dict:
    cfg = registry.load_config(h)
    threshold = int(cfg["threshold"])
    iso = lambda ts: dt.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").isocalendar()[:2]  # noqa: E731
    week = dt.datetime.now(dt.timezone.utc).isocalendar()[:2]
    passes = [r for r in _read_jsonl(_ledger(h, "metrics.jsonl")) if r["verdict"] == "PASS" and r["graded"] and iso(r["ts"]) == week]
    done = {s["verdict_ref"] for s in _read_jsonl(_ledger(h, "spotchecks.jsonl"))}
    target = spot_check_target(len(passes))
    already = sum(1 for r in passes if r["verdict_ref"] in done)
    open_ = [r for r in passes if r["verdict_ref"] not in done]
    at_threshold = [r for r in open_ if r["min_stage2"] == threshold]
    rest = [r for r in open_ if r["min_stage2"] != threshold]
    random.SystemRandom().shuffle(rest)
    chosen = (at_threshold + rest)[: max(0, target - already)]
    return {"week": f"{week[0]}-W{week[1]:02d}", "passes_this_week": len(passes), "target": target, "already_checked": already,
            "select": [{"verdict_ref": r["verdict_ref"], "task_id": r["task_id"], "agent": r["agent"], "at_threshold": r["min_stage2"] == threshold}
                       for r in chosen]}


def spotcheck_record(h: Path, ref: str, result: str, note: str) -> dict:
    if result not in ("ok", "false_pass"):
        raise Refused("--result must be ok or false_pass")
    p = (h / ref).resolve()
    if h.resolve() not in p.parents or not p.is_file():
        raise Refused(f"verdict ref not found: {ref}")
    v = json.loads(p.read_text())
    if not verdict.check_signature(h, v)[0] or v.get("verdict") != "PASS":
        raise Refused("verdict ref is not a valid signed PASS verdict")
    _append(_ledger(h, "spotchecks.jsonl"), {"ts": registry.now(), "verdict_ref": ref, "task_id": v["task_id"], "result": result, "note": note})
    spot = _read_jsonl(_ledger(h, "spotchecks.jsonl"))
    out = {"recorded": ref, "result": result, **false_pass_rate(sum(s["result"] == "false_pass" for s in spot), len(spot))}
    if result == "false_pass":
        alert(h, "false_pass", f"{v['task_id']} {ref}: {note}")
        out["next"] = f"kf-grade canary add-from --task-id {v['task_id']}"
    return out


def cli(a) -> int:
    h = registry.ensure_layout()
    if a.cmd == "digest":
        d = build_digest(h, a.since)
        if getattr(a, "json", False):
            print(json.dumps(d, indent=2, sort_keys=True))
            return 0
        print(f"KF Completion Gate digest ({d['generated_at']}{', since ' + a.since if a.since else ''})")
        for ag, s in d["agents"].items():
            print(f"- {ag}: {s['graded_tasks']} graded tasks; first-attempt pass {s['first_attempt_pass_rate']['current']} "
                  f"(prev {s['first_attempt_pass_rate']['previous']}){' ALARM' if s['first_attempt_pass_rate']['alarm'] else ''}; "
                  f"threshold clustering {s['threshold_clustering']['share']}{' ALARM' if s['threshold_clustering']['alarm'] else ''}; "
                  f"BLOCKED cap_reached {s['blocked_cap_reached']}, other {s['blocked_other']}")
        fp = d["grader_false_pass_rate"]
        print(f"- false passes: {fp['false_passes']}/{fp['spot_checks']} spot-checks (95% Wilson {fp['wilson_95']})")
        print(f"- canary: {d['canary']}")
        print(f"- registrations by key: {d['registrations_by_key']}")
        return 0
    if a.action == "next":
        print(json.dumps(spotcheck_next(h), indent=2))
        return 0
    if not (a.verdict_ref and a.result):
        raise Refused("spotcheck record requires --verdict-ref and --result")
    print(json.dumps(spotcheck_record(h, a.verdict_ref, a.result, a.note), indent=2))
    return 0
