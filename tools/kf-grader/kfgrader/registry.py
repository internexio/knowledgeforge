"""Store layout, grader config, registrations and grader.lock."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

import yaml

from . import VERSION

TOOL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_HOME = "/opt/kf-grader"
TASK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class Refused(Exception):
    """Usage error or refused request (CLI exit 2)."""


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def home() -> Path:
    return Path(os.environ.get("KF_GRADER_HOME", DEFAULT_HOME))


def test_mode() -> bool:
    return os.environ.get("KF_GRADER_TEST_MODE") == "1"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def atomic_write(path: Path, text: str, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    tmp.write_text(text, encoding="utf-8")
    if mode is not None:
        os.chmod(tmp, mode)
    os.replace(tmp, path)


def check_task_id(task_id: str) -> str:
    if not TASK_RE.match(task_id or ""):
        raise Refused(f"invalid task_id {task_id!r}: use [A-Za-z0-9._-], 1-64 chars, starting alphanumeric")
    return task_id


def check_sha(sha: str, label: str = "head_sha") -> str:
    if not SHA_RE.match(sha or ""):
        raise Refused(f"{label} must be a 40-char lowercase hex SHA")
    return sha


# ---------------------------------------------------------------- layout / config
def ensure_layout(h: Path | None = None) -> Path:
    h = h or home()
    fresh = not (h / "keys" / "verdict.key").exists()
    for d in ("keys", "registrations", "verdicts", "work", "config", "ledger", "locks"):
        (h / d).mkdir(parents=True, exist_ok=True)
    os.chmod(h / "keys", 0o700)
    cfg = h / "config" / "grader.yaml"
    if not cfg.exists():
        atomic_write(cfg, (TOOL_DIR / "config" / "grader.defaults.yaml").read_text())
    probes = h / "config" / "probes.yaml"
    if not probes.exists():
        atomic_write(probes, (TOOL_DIR / "config" / "probes.example.yaml").read_text())
    from . import verdict  # local import: verdict imports this module

    verdict.ensure_keys(h)
    if fresh or not (h / "grader.lock").exists():
        write_lock(h)
    return h


def load_config(h: Path | None = None) -> dict:
    h = h or home()
    defaults = yaml.safe_load((TOOL_DIR / "config" / "grader.defaults.yaml").read_text())
    p = h / "config" / "grader.yaml"
    cfg = yaml.safe_load(p.read_text()) if p.exists() else {}
    merged = dict(defaults)
    merged.update(cfg or {})
    return merged


def load_probes(h: Path | None = None) -> dict:
    h = h or home()
    p = h / "config" / "probes.yaml"
    return (yaml.safe_load(p.read_text()) or {}) if p.exists() else {}


# ---------------------------------------------------------------- grader.lock
def _lock_targets(h: Path) -> dict[str, Path]:
    t = {"config/grader.yaml": h / "config" / "grader.yaml", "config/probes.yaml": h / "config" / "probes.yaml"}
    for rel in ("agent/kf-grader.md", "agent/grader-settings.json"):
        p = TOOL_DIR / rel
        if p.exists():
            t[rel] = p
    return t


def _lock_doc(h: Path) -> dict:
    return {
        "grader_version": VERSION,
        "files": {k: sha256_bytes(p.read_bytes()) for k, p in sorted(_lock_targets(h).items()) if p.exists()},
    }


def write_lock(h: Path | None = None) -> None:
    h = h or home()
    atomic_write(h / "grader.lock", json.dumps(_lock_doc(h), indent=2, sort_keys=True) + "\n")


def check_lock(h: Path | None = None) -> tuple[bool, str]:
    h = h or home()
    lock = h / "grader.lock"
    if not lock.exists():
        return False, "grader.lock missing"
    try:
        recorded = json.loads(lock.read_text())
    except ValueError as e:
        return False, f"grader.lock unreadable: {e}"
    current = _lock_doc(h)
    if recorded.get("files") != current["files"]:
        diff = sorted(set(recorded.get("files", {}).items()) ^ set(current["files"].items()))
        return False, "grader.lock mismatch: " + ", ".join(sorted({k for k, _ in diff}))
    return True, "ok"


def lock_hash(h: Path | None = None) -> str:
    h = h or home()
    p = h / "grader.lock"
    return sha256_bytes(p.read_bytes()) if p.exists() else ""


# ---------------------------------------------------------------- registrations
def reg_path(h: Path, task_id: str) -> Path:
    return h / "registrations" / f"{check_task_id(task_id)}.json"


def load_registration(h: Path, task_id: str) -> dict | None:
    p = reg_path(h, task_id)
    return json.loads(p.read_text()) if p.exists() else None


def register(
    *,
    task_id: str,
    repo: str,
    base_sha: str,
    spec_file: str,
    agent: str | None = None,
    target_url: str | None = None,
    probe_urls: list[str] | None = None,
    test_command: str | None = None,
    allow_modify: list[str] | None = None,
    spec_repo_path: str | None = None,
    network: str = "none",
    deployed_sha_probe: str | None = None,
) -> dict:
    from . import acs

    h = ensure_layout()
    check_task_id(task_id)
    check_sha(base_sha, "base_sha")
    if reg_path(h, task_id).exists():
        raise Refused(f"task_id {task_id!r} already registered (immutable)")
    if network not in ("none", "bridge"):
        raise Refused("--network must be none or bridge")
    sp = Path(spec_file)
    if not sp.is_file():
        raise Refused(f"spec file not found: {spec_file}")
    spec_text = sp.read_text(encoding="utf-8")
    ac_list = acs.parse_ac_block(spec_text)  # raises Refused on bad/empty block
    repo_ref = repo
    if Path(repo).exists():
        repo_ref = str(Path(repo).resolve())
        r = subprocess.run(
            ["git", "-C", repo_ref, "cat-file", "-e", f"{base_sha}^{{commit}}"],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode != 0:
            raise Refused(f"base_sha {base_sha[:12]} not found in {repo_ref}")
    dsp = None
    if deployed_sha_probe:
        url, sep, rx = deployed_sha_probe.partition("::")
        if not sep or not url or not rx:
            raise Refused("--deployed-sha-probe must be URL::REGEX")
        dsp = {"url": url, "regex": rx}
    reg = {
        "task_id": task_id,
        "registered_at": now(),
        "registered_via": os.environ.get("KF_GRADER_KEY_ID", "local"),
        "agent": agent,
        "repo": repo_ref,
        "base_sha": base_sha,
        "spec_text": spec_text,
        "spec_sha256": sha256_bytes(spec_text.encode("utf-8")),
        "acceptance_criteria": ac_list,
        "target_url": target_url,
        "probe_urls": probe_urls or [],
        "test_command": test_command,
        "allow_modify": allow_modify or [],
        "spec_repo_path": spec_repo_path,
        "network": network,
        "deployed_sha_probe": dsp,
    }
    atomic_write(reg_path(h, task_id), json.dumps(reg, indent=2, sort_keys=True) + "\n", mode=0o600)
    return {"task_id": task_id, "spec_sha256": reg["spec_sha256"], "registered_at": reg["registered_at"]}
