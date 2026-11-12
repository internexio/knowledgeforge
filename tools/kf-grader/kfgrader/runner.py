"""Grading orchestration: refuse -> clone -> Stage 1 (ACs, tamper, probes) -> Stage 2 -> decide -> sign -> store."""
from __future__ import annotations

import fcntl
import json
import os
import shutil
import stat
import subprocess
import uuid
from contextlib import contextmanager
from pathlib import Path

from . import VERSION, acs, decide as decide_mod, metrics, probes, registry, sandbox, stage2, tamper, verdict
from .registry import Refused

EXIT = {"PASS": 0, "FAIL": 1, "BLOCKED": 3, "PENDING": 4}
SHA = registry.SHA_RE


@contextmanager
def task_lock(h: Path, task_id: str):
    (h / "locks").mkdir(parents=True, exist_ok=True)
    with open(h / "locks" / f"{task_id}.lock", "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def rm_tree(p: Path) -> None:
    """Remove a (read-only) checkout: restore owner write on directories first so entries can be unlinked."""
    for root, dirs, _files in os.walk(p):
        os.chmod(root, stat.S_IRWXU)
        for d in dirs:
            dp = os.path.join(root, d)
            if not os.path.islink(dp):
                os.chmod(dp, stat.S_IRWXU)
    shutil.rmtree(p)


def canary_healthy(h: Path) -> bool:
    p = h / "ledger" / "canary_state.json"
    if not p.exists():
        return True  # first run: the go-live runbook requires a canary pass before any agent leaves `off`
    try:
        return bool(json.loads(p.read_text()).get("healthy"))
    except ValueError:
        return False


def clone_at(repo: str, head: str, dest: Path) -> None:
    base = ["git", "-c", "core.hooksPath=/dev/null", "-c", "protocol.ext.allow=never"]
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    r = subprocess.run([*base, "clone", "--quiet", "--no-checkout", repo, str(dest)], capture_output=True, timeout=600, env=env)
    if r.returncode != 0:
        raise RuntimeError("clone failed: " + r.stderr.decode("utf-8", "replace").strip())
    r = subprocess.run([*base, "-C", str(dest), "checkout", "--quiet", "--detach", head], capture_output=True, timeout=600, env=env)
    if r.returncode != 0:
        raise Refused(f"head_sha {head[:12]} not found in {repo}")
    for root, dirs, files in os.walk(dest):
        if ".git" in dirs:
            dirs.remove(".git")
        for n in files + dirs:
            fp = os.path.join(root, n)
            if not os.path.islink(fp):
                os.chmod(fp, os.stat(fp).st_mode & ~0o222)


def worker_view(v: dict, cap: int) -> dict:
    """Redacted worker-facing view: no scores, no probe catalog, no Stage 2 prompt, no rescore rule."""
    s2 = v.get("stage2") or {}
    failed_dims = [
        {"dimension": d, "reason": x.get("reason", "")}
        for d, x in (s2.get("dimensions") or {}).items()
        if isinstance(x, dict) and x.get("failed")
    ]
    graded = v.get("graded_total", 0)
    return {
        "task_id": v["task_id"],
        "attempt": v["attempt"],
        "verdict": v["verdict"],
        "reasons": v["reasons"],
        "failed_acs": [{"id": r["id"], "output": r["output"]} for r in v.get("stage1", []) if not r["passed"]],
        "tamper_violations": v.get("tamper", {}).get("violations", []),
        "observations": [p["observation"] for p in v.get("probes", []) if not p["passed"]],
        "stage2_failed_dimensions": failed_dims,
        "attempts_remaining": max(0, cap - graded),
        "verdict_ref": v.get("verdict_ref"),
    }


def _blocked_view(task_id: str, reason: str, cap: int) -> dict:
    return {"task_id": task_id, "attempt": 0, "verdict": "BLOCKED", "reasons": [reason], "failed_acs": [],
            "tamper_violations": [], "observations": [], "stage2_failed_dimensions": [], "attempts_remaining": cap,
            "verdict_ref": None}


def precheck(task_id: str, head_sha: str) -> None:
    """Refusals that never consume an attempt and never touch the store."""
    sandbox.kind()  # raises Refused for subprocess outside test mode
    registry.check_task_id(task_id)
    registry.check_sha(head_sha)


def refuse_duplicate(graded: list[dict], head_sha: str) -> None:
    if graded and graded[-1]["head_sha"] == head_sha:
        raise Refused(f"head_sha {head_sha[:12]} was already graded as attempt {graded[-1]['attempt']}; commit a change first")


def grade(task_id: str, head_sha: str) -> tuple[dict, int]:
    precheck(task_id, head_sha)
    h = registry.ensure_layout()
    cfg = registry.load_config(h)
    cap, threshold = int(cfg["cap"]), int(cfg["threshold"])
    reg = registry.load_registration(h, task_id)
    if reg is None:
        return _blocked_view(task_id, "not_registered", cap), EXIT["BLOCKED"]

    with task_lock(h, task_id):
        prior = verdict.load_valid(h, task_id)
        graded = [v for v in prior if v.get("graded")]
        refuse_duplicate(graded, head_sha)
        n = len(graded) + 1
        lock_ok, lock_msg = registry.check_lock(h)
        healthy = canary_healthy(h)

        tamper_v: list[str] = []
        stage1: list[dict] = []
        probe_r: list[dict] = []
        s2_full: dict | None = None
        s2_scores: dict | None = None
        notes: list[str] = []
        infra_error = False

        short_circuit = (not healthy) or (not lock_ok) or n > cap
        if not lock_ok:
            notes.append(lock_msg)
        workdir = h / "work" / task_id / f"{n}-{uuid.uuid4().hex[:8]}"
        try:
            if not short_circuit:
                try:
                    clone_at(reg["repo"], head_sha, workdir)
                    have_base = subprocess.run(["git", "-C", str(workdir), "cat-file", "-e", f"{reg['base_sha']}^{{commit}}"],
                                               capture_output=True).returncode == 0
                    tamper_v = tamper.check(workdir, reg["base_sha"], head_sha, reg) if have_base else [
                        "history_rewrite: base_sha missing from repository"]
                    ctx = acs.Ctx(src=workdir, files=acs.tracked_files(workdir), target_url=reg.get("target_url"),
                                  network=reg.get("network", "none"), cfg=cfg)
                    stage1 = acs.run_all(reg["acceptance_criteria"], ctx)
                    probe_r = probes.run_probes(reg=reg, ctx=ctx, clone=workdir, head=head_sha, cfg=cfg, home=h)
                    clean = not tamper_v and all(r["passed"] for r in stage1) and all(p["passed"] for p in probe_r)
                    if clean and os.environ.get("KF_GRADER_STAGE2") != "off":
                        s2_full = stage2.run(reg=reg, clone=workdir, head=head_sha, cfg=cfg, home=h,
                                             stage1=stage1, probes=probe_r)
                        if s2_full:
                            s2_scores = {d: x["score"] for d, x in s2_full["dimensions"].items()}
                except Refused:
                    raise
                except Exception as e:  # noqa: BLE001 - infrastructure failure must never become a pass
                    infra_error = True
                    notes.append(f"{type(e).__name__}: {e}")
            d = decide_mod.decide(
                registered=True, canary_healthy=healthy, grader_ok=lock_ok and not infra_error, attempt_n=n, cap=cap,
                threshold=threshold, stage1_results=stage1, tamper_violations=tamper_v, probe_results=probe_r, stage2=s2_scores,
            )
        finally:
            if workdir.exists():
                rm_tree(workdir)
            parent = workdir.parent
            if parent.exists() and not any(parent.iterdir()):
                parent.rmdir()

        v = {
            "schema_version": 1,
            "task_id": task_id,
            "attempt": n,
            "seq": len(verdict.load_all(h, task_id)) + 1,
            "graded": d["consumed"],
            "graded_total": len(graded) + (1 if d["consumed"] else 0),
            "timestamp": registry.now(),
            "repo": reg["repo"],
            "base_sha": reg["base_sha"],
            "head_sha": head_sha,
            "spec_sha256": reg["spec_sha256"],
            "grader_version": VERSION,
            "lock_hash": registry.lock_hash(h),
            "mode": (cfg.get("agents", {}).get(reg.get("agent") or "", {}) or {}).get("mode", "off"),
            "test_mode": registry.test_mode(),
            "sandbox": sandbox.kind(),
            "stage1": stage1,
            "tamper": {"violations": tamper_v},
            "probes": probe_r,
            "stage2": s2_full,
            "verdict": d["verdict"],
            "reasons": d["reasons"],
            "notes": notes,
        }
        name = verdict.next_name(h, task_id, n)
        v["verdict_ref"] = f"verdicts/{task_id}/{name}"
        verdict.sign(h, v)
        verdict.write(h, v, name)
        metrics.record(h, v, reg.get("agent"))
        if "grader_error" in v["reasons"] or "canary_unhealthy" in v["reasons"]:
            metrics.alert(h, v["reasons"][0], f"{task_id}: {'; '.join(notes) or 'see verdict'}")
        return worker_view(v, cap), EXIT[v["verdict"]]


def status(task_id: str) -> tuple[dict, int]:
    registry.check_task_id(task_id)
    h = registry.ensure_layout()
    cfg = registry.load_config(h)
    cap = int(cfg["cap"])
    reg = registry.load_registration(h, task_id)
    if reg is None:
        raise Refused(f"unknown task_id {task_id!r}")
    pend = verdict.verdict_dir(h, task_id) / "pending.json"
    if pend.exists():
        return {"task_id": task_id, "verdict": "PENDING", "attempts_remaining": cap}, EXIT["PENDING"]
    prior = verdict.load_valid(h, task_id)
    if not prior:
        return {"task_id": task_id, "verdict": "PENDING", "reasons": ["no_submission"], "attempts_remaining": cap}, EXIT["PENDING"]
    return worker_view(prior[-1], cap), EXIT[prior[-1]["verdict"]]
