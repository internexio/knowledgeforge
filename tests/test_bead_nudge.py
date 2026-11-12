"""Tests for scripts/kf-bead-nudge.py and its wiring in scripts/git-hooks/pre-commit (bead knowledgeforge-core-4tu)."""
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
NUDGE = ROOT / "scripts" / "kf-bead-nudge.py"
HOOK = ROOT / "scripts" / "git-hooks" / "pre-commit"
REMINDER = "[kf] Staged module changes — did you close the driving bead? Run:"


def make_fake_bd(bindir: Path, rows: str = "", exit_code: int = 0, sleep: float = 0, stderr: str = "") -> None:
    bindir.mkdir(exist_ok=True)
    bd = bindir / "bd"
    bd.write_text(
        "#!/bin/sh\n"
        f"[ {sleep} != 0 ] && sleep {sleep}\n"
        f"printf '%s' {stderr!r} >&2\n"
        f"cat <<'EOF'\n{rows}EOF\n"
        f"exit {exit_code}\n"
    )
    bd.chmod(bd.stat().st_mode | stat.S_IEXEC)


@pytest.fixture
def repo(tmp_path):
    """A temp git repo with the real nudge script, a stub drift check, and the real pre-commit installed."""
    r = tmp_path / "repo"
    (r / "scripts").mkdir(parents=True)
    (r / "modules").mkdir()
    shutil.copy(NUDGE, r / "scripts" / "kf-bead-nudge.py")
    (r / "scripts" / "check-identity-drift.py").write_text("import sys\nsys.exit(int(open(__import__('os').path.join(__import__('os').path.dirname(__file__), 'drift_rc')).read()))\n")
    (r / "scripts" / "drift_rc").write_text("0")
    subprocess.run(["git", "init", "-q", str(r)], check=True)
    for k, v in (("user.email", "t@example.invalid"), ("user.name", "t"), ("commit.gpgsign", "false")):
        subprocess.run(["git", "-C", str(r), "config", k, v], check=True)
    hook = r / ".git" / "hooks" / "pre-commit"
    shutil.copy(HOOK, hook)
    hook.chmod(hook.stat().st_mode | stat.S_IEXEC)
    (r / "README.md").write_text("x\n")
    subprocess.run(["git", "-C", str(r), "add", "README.md", "scripts"], check=True)
    subprocess.run(["git", "-C", str(r), "commit", "-q", "-m", "init", "--no-verify"], check=True)
    return r


def env_with(bindir: Path, **extra) -> dict:
    return {**os.environ, "PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}", **extra}


def stage(repo: Path, path: str, text: str = "change\n") -> None:
    (repo / path).write_text(text)
    subprocess.run(["git", "-C", str(repo), "add", path], check=True)


def run_nudge(repo: Path, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(repo / "scripts" / "kf-bead-nudge.py")], cwd=repo, capture_output=True, text=True, env=env)


def commit(repo: Path, env: dict, msg: str = "c") -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), "commit", "-m", msg], capture_output=True, text=True, env=env)


ROWS = "◐ knowledgeforge-core-j2c P2 Build the thing\n◐ knowledgeforge-core-4tu P3 Add hook\n"


def test_module_change_with_in_progress_bead_prints_reminder(repo, tmp_path):
    make_fake_bd(tmp_path / "bin", ROWS)
    stage(repo, "modules/05_x.md")
    r = run_nudge(repo, env_with(tmp_path / "bin"))
    assert r.returncode == 0
    assert REMINDER in r.stderr and "bd close knowledgeforge-core-j2c" in r.stderr and "bd close knowledgeforge-core-4tu" in r.stderr
    assert r.stdout == ""


def test_non_module_change_is_silent_and_does_not_call_bd(repo, tmp_path):
    make_fake_bd(tmp_path / "bin", ROWS)
    marker = tmp_path / "bd_called"
    (tmp_path / "bin" / "bd").write_text(f"#!/bin/sh\ntouch {marker}\n")
    stage(repo, "docs.md")
    stage(repo, "modules/notes.txt")          # under modules/ but not a numbered .md
    r = run_nudge(repo, env_with(tmp_path / "bin"))
    assert r.returncode == 0 and r.stderr == "" and not marker.exists()


def test_no_in_progress_beads_is_silent(repo, tmp_path):
    make_fake_bd(tmp_path / "bin", "No issues found.\n")  # what real `bd list --status=in_progress` prints when nothing is claimed
    stage(repo, "modules/05_x.md")
    r = run_nudge(repo, env_with(tmp_path / "bin"))
    assert r.returncode == 0 and r.stderr == ""


def test_bd_warnings_on_stderr_do_not_become_beads(repo, tmp_path):
    make_fake_bd(tmp_path / "bin", ROWS, stderr="Warning: .beads has permissions 0755 (recommended: 0700)\nwarning: beads.role not configured\n")
    stage(repo, "modules/05_x.md")
    r = run_nudge(repo, env_with(tmp_path / "bin"))
    assert r.stderr.count("bd close") == 2 and "Warning" not in r.stderr


@pytest.mark.parametrize("fake", ["missing", "error", "slow"])
def test_degrades_silently_when_bd_unavailable(repo, tmp_path, fake):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    env = env_with(bindir, KF_BEAD_NUDGE_TIMEOUT="1")
    if fake == "error":
        make_fake_bd(bindir, ROWS, exit_code=1)
    elif fake == "slow":
        make_fake_bd(bindir, ROWS, sleep=5)
    else:
        env["PATH"] = f"{bindir}{os.pathsep}/usr/bin{os.pathsep}/bin"  # no bd anywhere
    stage(repo, "modules/05_x.md")
    t0 = time.time()
    r = run_nudge(repo, env)
    assert r.returncode == 0 and REMINDER not in r.stderr
    assert time.time() - t0 < 4  # a hung bd is cut off by the timeout


def test_many_beads_are_capped(repo, tmp_path):
    rows = "".join(f"◐ proj-b{i} P2 t{i}\n" for i in range(8))
    make_fake_bd(tmp_path / "bin", rows)
    stage(repo, "modules/05_x.md")
    r = run_nudge(repo, env_with(tmp_path / "bin"))
    assert r.stderr.count("bd close") == 5 and "(+3 more)" in r.stderr


def test_hook_shows_reminder_and_commit_still_succeeds(repo, tmp_path):
    make_fake_bd(tmp_path / "bin", ROWS)
    stage(repo, "modules/05_x.md")
    r = commit(repo, env_with(tmp_path / "bin"))
    assert r.returncode == 0, r.stderr
    assert REMINDER in r.stderr


def test_hook_silent_for_non_module_commit(repo, tmp_path):
    make_fake_bd(tmp_path / "bin", ROWS)
    stage(repo, "docs.md")
    r = commit(repo, env_with(tmp_path / "bin"))
    assert r.returncode == 0 and REMINDER not in r.stderr


def test_drift_failure_still_blocks_and_nudge_is_still_shown(repo, tmp_path):
    (repo / "scripts" / "drift_rc").write_text("1")
    make_fake_bd(tmp_path / "bin", ROWS)
    stage(repo, "modules/05_x.md")
    r = commit(repo, env_with(tmp_path / "bin"))
    assert r.returncode != 0                       # the drift check keeps its blocking semantics
    assert REMINDER in r.stderr


def test_hook_commit_succeeds_even_if_nudge_script_is_broken(repo, tmp_path):
    (repo / "scripts" / "kf-bead-nudge.py").write_text("raise SystemExit(7)\n")
    make_fake_bd(tmp_path / "bin", ROWS)
    stage(repo, "modules/05_x.md")
    assert commit(repo, env_with(tmp_path / "bin")).returncode == 0
