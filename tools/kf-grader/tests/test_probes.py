import http.server
import socketserver
import threading
from pathlib import Path

import pytest

from conftest import commit_all, git
from kfgrader import acs, probes, registry


@pytest.fixture
def site(tmp_path):
    root = tmp_path / "www"
    root.mkdir()
    for n in ("index", "pricing", "tools"):
        (root / f"{n}.html").write_text(f"<html><body>{n}</body></html>")

    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(root), **k)

        def log_message(self, *a):
            pass

    srv = socketserver.TCPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield root, f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def ctx_for(d, reg):
    return acs.Ctx(src=d, files=acs.tracked_files(d), target_url=reg.get("target_url"))


def base_reg(base, **kw):
    r = {"acceptance_criteria": [], "base_sha": base, "agent": "x", "target_url": None, "probe_urls": [], "network": "none"}
    r.update(kw)
    return r


def run(d, reg, head):
    h = registry.ensure_layout()
    (h / "config" / "probes.yaml").write_text("sample_size: 99\nextra_urls: {}\n")
    return probes.run_probes(reg=reg, ctx=ctx_for(d, reg), clone=d, head=head, cfg=registry.load_config(h), home=h)


def test_p3_repo_wide_absence_catches_relocated_string(repo):
    d, base = repo
    for n in "abcde":
        (d / "tools" / n / "analyzer.js").write_text("ok\n")
    (d / "tools/a/strings.js").write_text('export const M = "Try again tomorrow";\n')
    head = commit_all(d)
    ac = {"id": "AC2", "type": "grep_count", "pattern": "Try again tomorrow", "paths": ["tools/*/analyzer.js"], "per_file": True, "op": "==", "value": 0}
    res = run(d, base_reg(base, acceptance_criteria=[ac]), head)
    assert [r["passed"] for r in res if r["id"] == "P3"] == [False]
    assert "strings.js" in res[0]["observation"]


def test_p3_clean_and_presence_acs_ignored(repo):
    d, base = repo
    for n in "abcde":
        (d / "tools" / n / "analyzer.js").write_text("ok\n")
    head = commit_all(d)
    acs_ = [{"id": "AC2", "type": "grep_count", "pattern": "Try again tomorrow", "paths": ["tools/*/analyzer.js"], "per_file": True, "op": "==", "value": 0},
            {"id": "AC1", "type": "grep_count", "pattern": "ok", "paths": ["tools/*/analyzer.js"], "per_file": True, "op": ">=", "value": 1}]
    res = run(d, base_reg(base, acceptance_criteria=acs_), head)
    assert len(res) == 1 and res[0]["passed"]


def test_p2_deleted_page_fails_and_modified_page_is_skipped(repo, site):
    d, base = repo
    www, url = site
    (d / "site").mkdir()
    for n in ("index", "pricing", "tools"):
        (d / "site" / f"{n}.html").write_text(f"{n}")
    base = commit_all(d)
    (d / "site/pricing.html").unlink()          # deleted: never "touched", must still return 200
    (www / "pricing.html").unlink()
    (d / "site/tools.html").write_text("edited")  # modified: out of P2 scope even if it were broken
    (www / "tools.html").unlink()
    head = commit_all(d)
    res = run(d, base_reg(base, target_url=url, probe_urls=["/index.html", "/pricing.html", "/tools.html"]), head)
    p2 = {r["observation"].split()[1]: r["passed"] for r in res if r["id"] == "P2"}
    assert p2 == {f"{url}/index.html": True, f"{url}/pricing.html": False}


def test_p4_test_command(repo):
    d, base = repo
    (d / "x").write_text("x")
    head = commit_all(d)
    assert run(d, base_reg(base, test_command="exit 0"), head)[0]["passed"]
    bad = run(d, base_reg(base, test_command="exit 3"), head)[0]
    assert not bad["passed"] and "exited 3" in bad["observation"]


def test_p5_deployed_sha(repo, site):
    d, base = repo
    www, url = site
    (d / "x").write_text("x")
    head = commit_all(d)
    (www / "build.txt").write_text(f"build: {head[:12]}\n")
    reg = base_reg(base, deployed_sha_probe={"url": f"{url}/build.txt", "regex": r"build: ([0-9a-f]+)"})
    assert run(d, reg, head)[0]["passed"]
    (www / "build.txt").write_text("build: deadbeefcafe\n")
    r = run(d, reg, head)[0]
    assert not r["passed"] and "does not match" in r["observation"]


def test_p1_sibling_selector_recheck(repo, site):
    d, base = repo
    www, url = site
    (www / "tools").mkdir()
    (www / "tools" / "a.html").write_text('<div data-hook="cta"></div>')
    (www / "tools" / "b.html").write_text("<p>no cta here</p>")
    (d / "x").write_text("x")
    head = commit_all(d)
    ac = {"id": "AC4", "type": "dom_check", "url": "/tools/a.html", "selector": "[data-hook='cta']", "op": ">=", "value": 1}
    reg = base_reg(base, acceptance_criteria=[ac], target_url=url, probe_urls=["/tools/b.html", "/pricing.html"])
    res = [r for r in run(d, reg, head) if r["id"] == "P1"]
    assert len(res) == 1 and not res[0]["passed"] and "tools/b.html" in res[0]["observation"]  # /pricing.html is not a sibling
