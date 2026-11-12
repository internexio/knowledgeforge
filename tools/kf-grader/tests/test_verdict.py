import json

from kfgrader import registry, verdict


def make(h, **kw):
    v = {"task_id": "T1", "attempt": 1, "seq": 1, "graded": True, "head_sha": "a" * 40, "verdict": "PASS", "test_mode": False}
    v.update(kw)
    return verdict.sign(h, v)


def test_sign_verify_roundtrip(grader_env):
    h = registry.ensure_layout()
    v = make(h)
    verdict.write(h, v, verdict.next_name(h, "T1", 1))
    assert verdict.verify(h, "T1", "a" * 40)[0]
    assert not verdict.verify(h, "T1", "b" * 40)[0]  # bound to head_sha


def test_edited_field_breaks_signature(grader_env):
    h = registry.ensure_layout()
    v = make(h, verdict="FAIL")
    v["verdict"] = "PASS"  # forge after signing
    verdict.write(h, v, "attempt-1.json")
    assert not verdict.verify(h, "T1", "a" * 40)[0]


def test_recomputed_hash_without_key_is_rejected(grader_env):
    import hashlib

    h = registry.ensure_layout()
    v = make(h, verdict="FAIL")
    v["verdict"] = "PASS"
    v["content_sha256"] = hashlib.sha256(verdict.canonical(v)).hexdigest()  # a plain hash is recomputable by anyone
    verdict.write(h, v, "attempt-1.json")
    ok, why = verdict.verify(h, "T1", "a" * 40)
    assert not ok and "signature" in why or "unverifiable" in why


def test_other_instance_key_rejected(grader_env, tmp_path, monkeypatch):
    h = registry.ensure_layout()
    monkeypatch.setenv("KF_GRADER_HOME", str(tmp_path / "other"))
    h2 = registry.ensure_layout()
    verdict.write(h2, make(h2), "attempt-1.json")
    (h / "verdicts" / "T1").mkdir(parents=True)
    (h / "verdicts" / "T1" / "attempt-1.json").write_text((h2 / "verdicts" / "T1" / "attempt-1.json").read_text())
    assert not verdict.verify(h, "T1", "a" * 40)[0]


def test_test_mode_verdict_needs_flag(grader_env):
    h = registry.ensure_layout()
    verdict.write(h, make(h, test_mode=True), "attempt-1.json")
    assert not verdict.verify(h, "T1", "a" * 40)[0]
    assert verdict.verify(h, "T1", "a" * 40, allow_test=True)[0]


def test_garbage_files_ignored_not_crashing(grader_env):
    h = registry.ensure_layout()
    d = h / "verdicts" / "T1"
    d.mkdir(parents=True)
    (d / "attempt-7.json").write_text("{not json")
    (d / "attempt-8.json").write_text(json.dumps({"verdict": "PASS"}))
    assert not verdict.verify(h, "T1", "a" * 40)[0]
    assert verdict.load_valid(h, "T1") == []
