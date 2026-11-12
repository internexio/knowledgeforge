"""Production sandbox checks. Skipped unless a Docker daemon and the kf-grader-runner image are available
(build it with: docker build -t kf-grader-runner tools/kf-grader/runner).

These exist because the subprocess backend used by the other tests cannot see Docker-only failures: the first real
run found that `cp -a` fails on the unprivileged tmpfs root, which broke every command AC in production."""
import os
import subprocess

import pytest

from kfgrader import sandbox

CFG = {"limits": {"cpus": 1, "memory": "512m", "pids": 128}, "runner_image": "kf-grader-runner"}


def _docker_ready() -> bool:
    try:
        return subprocess.run(["docker", "image", "inspect", "kf-grader-runner"], capture_output=True, timeout=20).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


pytestmark = pytest.mark.skipif(not _docker_ready(), reason="docker daemon or kf-grader-runner image not available")


@pytest.fixture
def src(tmp_path, monkeypatch):
    monkeypatch.setenv("KF_GRADER_SANDBOX", "docker")
    monkeypatch.delenv("KF_GRADER_TEST_MODE", raising=False)
    d = tmp_path / "src"
    (d / "sub").mkdir(parents=True)
    (d / "a.txt").write_text("hello\n")
    (d / "sub" / "b.txt").write_text("b\n")
    for p in (d / "a.txt", d / "sub" / "b.txt"):
        os.chmod(p, 0o444)
    os.chmod(d / "sub", 0o555)
    os.chmod(d, 0o555)  # mimic the read-only grader checkout
    yield d
    os.chmod(d, 0o755)
    os.chmod(d / "sub", 0o755)


def run(src, cmd, **kw):
    return sandbox.run(src, cmd, kw.pop("timeout", 30), cfg=CFG, **kw)


def test_copy_succeeds_runs_unprivileged_and_copy_is_writable(src):
    r = run(src, "id -u && cat a.txt sub/b.txt && echo more >> a.txt && echo x > sub/new && wc -l < a.txt")
    assert r.exit_code == 0, r.stderr
    assert r.stdout.split() == ["65534", "hello", "b", "2"]
    assert (src / "a.txt").read_text() == "hello\n"  # host source untouched


def test_source_mount_is_read_only(src):
    r = run(src, "touch /src/x; echo rc=$?")
    assert "Read-only file system" in r.stderr and "rc=1" in r.stdout


def test_network_none_by_default_and_bridge_only_on_opt_in(src):
    probe = "python3 -c \"import socket;socket.create_connection(('1.1.1.1',80),timeout=5);print('connected')\""
    assert "connected" not in run(src, probe).stdout
    assert "connected" in run(src, probe, network="bridge").stdout


def test_exit_code_and_timeout_kill(src):
    assert run(src, "exit 7").exit_code == 7
    r = run(src, "sleep 60", timeout=3)
    assert r.timed_out and r.exit_code == 124
    leftovers = subprocess.run(["docker", "ps", "-aq", "--filter", "name=kfg-"], capture_output=True, text=True).stdout.strip()
    assert leftovers == ""
