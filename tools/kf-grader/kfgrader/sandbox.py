"""Command AC sandbox. Production = Docker (read-only source, no network, unprivileged). Test-only = subprocess."""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

from .registry import Refused, test_mode

OUT_CAP = 4096


@dataclass
class Result:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


def kind() -> str:
    k = os.environ.get("KF_GRADER_SANDBOX", "docker")
    if k not in ("docker", "subprocess"):
        raise Refused(f"KF_GRADER_SANDBOX must be docker or subprocess, got {k!r}")
    if k == "subprocess" and not test_mode():
        raise Refused("KF_GRADER_SANDBOX=subprocess is refused outside KF_GRADER_TEST_MODE=1")
    return k


def _cut(b: bytes | str | None) -> str:
    s = b.decode("utf-8", "replace") if isinstance(b, bytes) else (b or "")
    return s if len(s) <= OUT_CAP else s[:OUT_CAP] + f"\n[truncated {len(s) - OUT_CAP} bytes]"


def run(src: Path, cmd: str, timeout_s: int, network: str = "none", cfg: dict | None = None) -> Result:
    return _docker(src, cmd, timeout_s, network, cfg or {}) if kind() == "docker" else _subprocess(src, cmd, timeout_s)


def _docker(src: Path, cmd: str, timeout_s: int, network: str, cfg: dict) -> Result:
    lim = cfg.get("limits", {})
    name = f"kfg-{uuid.uuid4().hex[:12]}"
    argv = [
        "docker", "run", "--rm", "--name", name,
        "--network", "bridge" if network == "bridge" else "none",
        "--memory", str(lim.get("memory", "1g")), "--cpus", str(lim.get("cpus", 1)),
        "--pids-limit", str(lim.get("pids", 256)),
        "--user", "65534:65534", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "-v", f"{src}:/src:ro", "--tmpfs", "/work:rw,exec,size=512m,mode=1777", "-w", "/work",
        "-e", "HOME=/work",
        cfg.get("runner_image", "kf-grader-runner"),
        "sh", "-c", 'cp -a /src/. /work/ && exec sh -c "$0"', cmd,
    ]
    try:
        p = subprocess.run(argv, capture_output=True, timeout=timeout_s + 30, stdin=subprocess.DEVNULL)
        return Result(p.returncode, _cut(p.stdout), _cut(p.stderr))
    except subprocess.TimeoutExpired as e:
        subprocess.run(["docker", "kill", name], capture_output=True, timeout=30)
        return Result(124, _cut(e.stdout), _cut(e.stderr), timed_out=True)
    except FileNotFoundError:
        return Result(127, "", "docker binary not found", False)


def _subprocess(src: Path, cmd: str, timeout_s: int) -> Result:
    work = Path(tempfile.mkdtemp(prefix="kfg-sub-"))
    try:
        shutil.copytree(src, work / "w", symlinks=True)
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(work), "LANG": "C.UTF-8"}
        p = subprocess.Popen(["sh", "-c", cmd], cwd=work / "w", env=env, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        try:
            out, err = p.communicate(timeout=timeout_s)
            return Result(p.returncode, _cut(out), _cut(err))
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            out, err = p.communicate()
            return Result(124, _cut(out), _cut(err), timed_out=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)
