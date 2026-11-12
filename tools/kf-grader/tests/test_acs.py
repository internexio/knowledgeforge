import pytest

from kfgrader import acs
from kfgrader.registry import Refused


def test_globs():
    assert acs.match_glob("tools/*/analyzer.js", "tools/a/analyzer.js")
    assert not acs.match_glob("tools/*/analyzer.js", "tools/a/b/analyzer.js")
    assert acs.match_glob("**/test_*.*", "tests/test_smoke.sh")
    assert acs.match_glob("**/test_*.*", "test_x.py")
    assert acs.match_glob("tests/**", "tests/a/b.py")
    assert acs.match_glob("conftest.py", "pkg/conftest.py", basename_any=True)
    assert not acs.match_glob("conftest.py", "pkg/conftest.py")


def test_parse_requires_executable_ac():
    with pytest.raises(Refused, match="no executable AC"):
        acs.parse_ac_block("```yaml kf-acceptance\nacceptance_criteria:\n  - {id: A, type: judgment, text: x}\n```")
    with pytest.raises(Refused, match="no ```yaml kf-acceptance"):
        acs.parse_ac_block("just prose")


@pytest.mark.parametrize("bad", [
    "{id: A, type: grep_count, pattern: x, paths: [a], op: '>>', value: 1}",
    "{id: A, type: nope}",
    "{id: 'a b', type: command, run: x}",
    "{id: A, type: command}",
])
def test_parse_rejects_bad_ac(bad):
    with pytest.raises(Refused):
        acs.parse_ac_block(f"```yaml kf-acceptance\nacceptance_criteria:\n  - {bad}\n```")


def test_duplicate_ids_rejected():
    with pytest.raises(Refused, match="duplicate"):
        acs.parse_ac_block("```yaml kf-acceptance\nacceptance_criteria:\n  - {id: A, type: command, run: x}\n  - {id: A, type: command, run: y}\n```")


def test_grep_count_per_file_and_zero_files(tmp_path):
    (tmp_path / "a.js").write_text("x\nfoo\nfoo bar\n")
    (tmp_path / "b.js").write_text("nothing\n")
    ctx = acs.Ctx(src=tmp_path, files=["a.js", "b.js"])
    ac = {"id": "A", "type": "grep_count", "pattern": "foo", "paths": ["*.js"], "per_file": True, "op": ">=", "value": 1}
    ok, out = acs.run_grep_count(ac, ctx)
    assert not ok and "b.js: 0" in out and "a.js" not in out
    ok, _ = acs.run_grep_count({**ac, "per_file": False}, ctx)
    assert ok  # aggregate 2 >= 1
    ok, out = acs.run_grep_count({**ac, "paths": ["zzz/*.js"]}, ctx)
    assert not ok and "no files matched" in out


def test_dom_selector():
    html = '<div data-hook="r3-conversion-cta" class="a b" id="x"></div><p>t</p>'
    assert acs.count_selector(html, "[data-hook='r3-conversion-cta']") == 1
    assert acs.count_selector(html, "div.a.b#x") == 1
    assert acs.count_selector(html, ".zz") == 0
    with pytest.raises(ValueError):
        acs.count_selector(html, "div p")


def test_executor_crash_is_a_failed_check(tmp_path):
    ctx = acs.Ctx(src=tmp_path, files=[])
    res = acs.run_all([{"id": "A", "type": "grep_count", "pattern": "[", "regex": True, "paths": ["*"], "op": ">=", "value": 1}], ctx)
    assert res[0]["passed"] is False
