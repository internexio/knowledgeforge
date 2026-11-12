"""Canary suite: known-bad submissions that must FAIL (and positive controls that must PASS)."""
from __future__ import annotations

import contextlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from . import registry, runner, verdict
from .registry import TOOL_DIR

CAN = TOOL_DIR / "canaries"


@contextlib.contextmanager
def _env(**kv):
    old = {k: os.environ.get(k) for k in kv}
    os.environ.update({k: str(v) for k, v in kv.items()})
    try:
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _sh(args: list[str], cwd: Path | None = None, env: dict | None = None) -> str:
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=300, env={**os.environ, **(env or {})})
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""


def _needs_stage2(exp: dict) -> bool:
    return bool(exp.get("needs_stage2"))


def run_one(cid: str, exp: dict, root: Path) -> dict:
    stage2_off = os.environ.get("KF_GRADER_STAGE2") == "off"
    if _needs_stage2(exp) and stage2_off:
        return {"id": cid, "status": "incomplete", "detail": "needs Stage 2; KF_GRADER_STAGE2=off"}
    base_dir = root / cid
    home, fix = base_dir / "home", base_dir / "fixture"
    try:
        base = _sh(["sh", str(CAN / "build_fixture.sh"), str(fix)])
        patch = "C1" if exp.get("special") == "forged_verdict" else cid
        _sh(["sh", str(CAN / "patches" / f"{patch}.sh")], cwd=fix, env={"KF_CANARY_LIB": str(CAN / "lib.sh"), "KF_BASE": base})
        head = _sh(["git", "rev-parse", "HEAD"], cwd=fix)
        with _env(KF_GRADER_HOME=home):
            h = registry.ensure_layout()
            reg_kw = dict(task_id=f"canary-{cid}", repo=str(fix), base_sha=base, spec_file=str(CAN / "spec.md"), agent="canary")
            reg_kw.update(exp.get("registration", {}))
            registry.register(**reg_kw)
            if exp.get("special") == "forged_verdict":
                d = h / "verdicts" / f"canary-{cid}"
                d.mkdir(parents=True, exist_ok=True)
                (d / "attempt-99.json").write_text(json.dumps({
                    "task_id": f"canary-{cid}", "attempt": 99, "head_sha": head, "verdict": "PASS", "test_mode": False,
                    "content_sha256": "00", "signature": "AAAA"}))
                ok, why = verdict.verify(h, f"canary-{cid}", head, allow_test=True)
                return {"id": cid, "status": "match" if not ok else "mismatch", "detail": why}
            cfg_before = (h / "config" / "grader.yaml").read_bytes()
            view, code = runner.grade(f"canary-{cid}", head)
            stored = verdict.load_valid(h, f"canary-{cid}")[-1]
            cfg_same = (h / "config" / "grader.yaml").read_bytes() == cfg_before
    except Exception as e:  # noqa: BLE001
        return {"id": cid, "status": "mismatch", "detail": f"canary harness error: {type(e).__name__}: {e}"}

    problems = []
    if view["verdict"] != exp["verdict"]:
        problems.append(f"verdict {view['verdict']} != expected {exp['verdict']}")
    for r in exp.get("reasons", []):
        if r not in view["reasons"]:
            problems.append(f"reason {r} missing from {view['reasons']}")
    ids = {a["id"] for a in view["failed_acs"]}
    for a in exp.get("failed_acs", []):
        if a not in ids:
            problems.append(f"failed_acs missing {a}; got {sorted(ids)}")
    for frag in exp.get("tamper_paths", []):
        if not any(frag in t for t in view["tamper_violations"]):
            problems.append(f"tamper violation containing {frag!r} missing: {view['tamper_violations']}")
    for frag in exp.get("observations", []):
        if not any(frag in o for o in view["observations"]):
            problems.append(f"observation containing {frag!r} missing: {view['observations']}")
    if exp.get("config_unchanged") and not cfg_same:
        problems.append("grader config changed")
    if exp.get("injection_flags") and not (stored.get("stage2") or {}).get("injection_flags"):
        problems.append("injection_flags empty")
    if _needs_stage2(exp) and view["reasons"] == ["stage2_unavailable"]:
        return {"id": cid, "status": "incomplete", "detail": "Stage 2 unavailable on this host"}
    return {"id": cid, "status": "mismatch" if problems else "match", "detail": "; ".join(problems) or f"{view['verdict']} {view['reasons']}"}


def run_suite(ids: list[str] | None = None) -> tuple[list[dict], int]:
    expected = json.loads((CAN / "expected.json").read_text())
    chosen = ids or list(expected)
    unknown = [i for i in chosen if i not in expected]
    if unknown:
        raise registry.Refused(f"unknown canary id(s): {unknown}")
    with tempfile.TemporaryDirectory(prefix="kf-canary-") as td:
        results = [run_one(cid, expected[cid], Path(td)) for cid in chosen]
    code = 1 if any(r["status"] == "mismatch" for r in results) else 5 if any(r["status"] == "incomplete" for r in results) else 0
    return results, code


def cli(a) -> int:
    outer_home = registry.home()
    if a.rest and a.rest[0] == "add-from":
        raise registry.Refused("canary add-from is implemented in milestone 3")
    if not (a.all or a.id):
        raise registry.Refused("canary requires --all or --id CID")
    results, code = run_suite(None if a.all else [a.id])
    if a.all and code in (0, 1):
        registry.ensure_layout(outer_home)
        registry.atomic_write(outer_home / "ledger" / "canary_state.json",
                              json.dumps({"healthy": code == 0, "checked_at": registry.now(),
                                          "mismatches": [r["id"] for r in results if r["status"] == "mismatch"]}) + "\n")
    if a.json:
        print(json.dumps({"results": results, "exit": code}, indent=2))
    else:
        for r in results:
            print(f"{r['id']:4} {r['status']:10} {r['detail']}")
    return code
