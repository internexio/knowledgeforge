import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def grader_env(tmp_path, monkeypatch):
    monkeypatch.setenv("KF_GRADER_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("KF_GRADER_TEST_MODE", "1")
    monkeypatch.setenv("KF_GRADER_SANDBOX", "subprocess")
    monkeypatch.setenv("KF_GRADER_STAGE2", "off")
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    return tmp_path / "home"


def git(cwd, *args):
    r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


@pytest.fixture
def repo(tmp_path):
    """Fixture repo with a protected test, package.json, and five analyzers; returns (path, base_sha)."""
    d = tmp_path / "repo"
    d.mkdir()
    subprocess.run(["git", "init", "-q", str(d)], check=True)
    git(d, "config", "user.email", "t@example.invalid")
    git(d, "config", "user.name", "t")
    for n in "abcde":
        (d / "tools" / n).mkdir(parents=True)
        (d / "tools" / n / "analyzer.js").write_text('return "Try again tomorrow";\n')
    (d / "tests").mkdir()
    (d / "tests" / "test_smoke.sh").write_text("exit 0\n")
    (d / "package.json").write_text('{"scripts": {"test": "sh tests/test_smoke.sh"}}\n')
    git(d, "add", "-A")
    git(d, "commit", "-q", "-m", "base")
    return d, git(d, "rev-parse", "HEAD")


def commit_all(d, msg="c"):
    git(d, "add", "-A")
    git(d, "commit", "-q", "-m", msg)
    return git(d, "rev-parse", "HEAD")


SPEC = """# t
```yaml kf-acceptance
acceptance_criteria:
  - {id: AC1, type: grep_count, pattern: "r3-conversion-cta", paths: ["tools/*/analyzer.js"], per_file: true, op: ">=", value: 1}
  - {id: AC2, type: grep_count, pattern: "Try again tomorrow", paths: ["tools/*/analyzer.js"], per_file: true, op: "==", value: 0}
  - {id: AC3, type: command, run: "sh tests/test_smoke.sh", expect: {exit_code: 0}}
```
"""


@pytest.fixture
def spec(tmp_path):
    p = tmp_path / "spec.md"
    p.write_text(SPEC)
    return p
