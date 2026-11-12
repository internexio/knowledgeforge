"""kf-grade CLI. Exit codes: submit/status 0 PASS, 1 FAIL, 2 refused/usage, 3 BLOCKED, 4 PENDING."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from . import registry, runner, verdict
from .registry import Refused


def _out(obj: object) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="kf-grade", description="KF Completion Gate")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="create KF_GRADER_HOME layout and ed25519 keypair if absent")
    lk = sub.add_parser("lock", help="refresh grader.lock after an intentional config/agent change")
    lk.add_argument("--refresh", action="store_true", required=True)

    r = sub.add_parser("register", help="snapshot a task spec (dispatcher only)")
    r.add_argument("--task-id", required=True)
    r.add_argument("--repo", required=True)
    r.add_argument("--base-sha", required=True)
    r.add_argument("--spec", required=True)
    r.add_argument("--agent")
    r.add_argument("--target-url")
    r.add_argument("--probe-urls", default="")
    r.add_argument("--test-command")
    r.add_argument("--allow-modify", action="append", default=[])
    r.add_argument("--spec-repo-path")
    r.add_argument("--network", default="none", choices=["none", "bridge"])
    r.add_argument("--deployed-sha-probe")

    s = sub.add_parser("submit", help="submit head_sha for grading (worker)")
    s.add_argument("--task-id", required=True)
    s.add_argument("--head-sha", required=True)
    s.add_argument("--wait", action="store_true")

    st = sub.add_parser("status", help="latest worker-view verdict")
    st.add_argument("--task-id", required=True)

    v = sub.add_parser("verify", help="exit 0 iff a signed PASS verdict exists for head_sha")
    v.add_argument("--task-id", required=True)
    v.add_argument("--head-sha", required=True)
    v.add_argument("--allow-test", action="store_true")

    c = sub.add_parser("canary", help="run the canary suite")
    c.add_argument("--all", action="store_true")
    c.add_argument("--id")
    c.add_argument("--json", action="store_true")
    c.add_argument("rest", nargs="*", help="add-from --task-id ID")
    c.add_argument("--task-id")

    d = sub.add_parser("digest", help="weekly digest (dispatcher)")
    d.add_argument("--since")
    sp = sub.add_parser("spotcheck", help="spot-check selection and logging (dispatcher)")
    sp.add_argument("action", nargs="?", default="next", choices=["next", "record"])
    sp.add_argument("--verdict-ref")
    sp.add_argument("--result", choices=["ok", "false_pass"])
    sp.add_argument("--note", default="")

    g = sub.add_parser("_grade")  # internal: detached grading for non-wait submit
    g.add_argument("--task-id", required=True)
    g.add_argument("--head-sha", required=True)
    return p


def cmd_submit(a) -> int:
    runner.precheck(a.task_id, a.head_sha)
    if a.wait or os.environ.get("KF_GRADER_DETACHED") == "1":
        view, code = runner.grade(a.task_id, a.head_sha)
        _out(view)
        return code
    h = registry.ensure_layout()
    if registry.load_registration(h, a.task_id) is None:
        view, code = runner.grade(a.task_id, a.head_sha)
        _out(view)
        return code
    runner.refuse_duplicate([v for v in verdict.load_valid(h, a.task_id) if v.get("graded")], a.head_sha)
    pend = verdict.verdict_dir(h, a.task_id) / "pending.json"
    pend.parent.mkdir(parents=True, exist_ok=True)
    registry.atomic_write(pend, json.dumps({"head_sha": a.head_sha, "started": registry.now()}))
    subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve().parent.parent / "bin" / "kf-grade"), "_grade",
         "--task-id", a.task_id, "--head-sha", a.head_sha],
        start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        env={**os.environ, "KF_GRADER_DETACHED": "1"},
    )
    _out({"task_id": a.task_id, "verdict": "PENDING", "head_sha": a.head_sha})
    return 4


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    try:
        if a.cmd == "init":
            h = registry.ensure_layout()
            _out({"home": str(h), "public_key": str(h / "keys" / "verdict.pub")})
            return 0
        if a.cmd == "lock":
            h = registry.ensure_layout()
            registry.write_lock(h)
            _out({"lock": "refreshed"})
            return 0
        if a.cmd == "register":
            _out(registry.register(
                task_id=a.task_id, repo=a.repo, base_sha=a.base_sha, spec_file=a.spec, agent=a.agent,
                target_url=a.target_url, probe_urls=[u for u in a.probe_urls.split(",") if u],
                test_command=a.test_command, allow_modify=a.allow_modify, spec_repo_path=a.spec_repo_path,
                network=a.network, deployed_sha_probe=a.deployed_sha_probe))
            return 0
        if a.cmd == "submit":
            return cmd_submit(a)
        if a.cmd == "_grade":
            view, _ = runner.grade(a.task_id, a.head_sha)
            return 0
        if a.cmd == "status":
            view, code = runner.status(a.task_id)
            _out(view)
            return code
        if a.cmd == "verify":
            registry.check_task_id(a.task_id)
            registry.check_sha(a.head_sha)
            h = registry.ensure_layout()
            ok, why = verdict.verify(h, a.task_id, a.head_sha, allow_test=a.allow_test)
            _out({"verified": ok, "reason": why})
            return 0 if ok else 1
        if a.cmd == "canary":
            from . import canary

            return canary.cli(a)
        if a.cmd in ("digest", "spotcheck"):
            from . import metrics

            return metrics.cli(a)
    except Refused as e:
        sys.stderr.write(f"kf-grade: refused: {e}\n")
        return 2
    finally:
        if getattr(a, "cmd", None) == "_grade":
            try:
                (verdict.verdict_dir(registry.home(), a.task_id) / "pending.json").unlink()
            except OSError:
                pass
    return 2
