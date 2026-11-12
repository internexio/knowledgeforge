"""Stage 2 judgment (R5): headless `claude -p --agent kf-grader`, read-only, schema-validated, runner decides.

Failure of any kind (missing binary, timeout, non-zero exit, bad JSON, schema-invalid) returns None, which `decide()` turns
into BLOCKED stage2_unavailable. A checkout modified during Stage 2 raises (BLOCKED grader_error): isolation failed.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import yaml

from . import tamper
from .registry import TOOL_DIR

DIMS = ("completeness", "regression_risk", "scope_creep", "unrequested_changes")
DIFF_CAP = 400_000
PATH_LIKE = re.compile(r"^[\w./@+-]+(?::\d+(?:-\d+)?)?$")


class Stage2Unavailable(Exception):
    pass


# ---------------------------------------------------------------- agent definition
def agent_def() -> dict:
    """Parse agent/kf-grader.md into the dict `claude --agents` accepts. Defined inline (highest priority) so a
    `.claude/agents/kf-grader.md` inside the graded repo can never shadow it."""
    text = (TOOL_DIR / "agent" / "kf-grader.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        raise Stage2Unavailable("agent/kf-grader.md has no frontmatter")
    fm, body = yaml.safe_load(m.group(1)), m.group(2).strip()
    split = lambda s: [t.strip() for t in str(s).split(",") if t.strip()]  # noqa: E731
    return {"description": fm["description"], "prompt": body, "tools": split(fm["tools"]),
            "disallowedTools": split(fm.get("disallowedTools", "")), "model": fm.get("model", "opus")}


def pick_model(cfg: dict, reg: dict) -> str:
    """R6 model diversity: if the worker runs opus and an alternative is configured, grade with the alternative."""
    worker = (cfg.get("agents", {}).get(reg.get("agent") or "", {}) or {}).get("worker_model")
    alt = cfg.get("alt_model") or ""
    if alt and worker and worker == cfg.get("stage2_model", "opus"):
        return alt
    return cfg.get("stage2_model", "opus")


# ---------------------------------------------------------------- packet
def tree_checksum(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if ".git" in rel.parts:
            continue
        if p.is_file() and not p.is_symlink():
            h.update(str(rel).encode() + b"\0" + hashlib.sha256(p.read_bytes()).digest())
        elif p.is_symlink():
            h.update(str(rel).encode() + b"\0->" + os.readlink(p).encode())
    return h.hexdigest()


def build_packet(pdir: Path, reg: dict, clone: Path, head: str, stage1: list[dict], probes: list[dict]) -> None:
    pdir.mkdir(parents=True)
    judgment = [a for a in reg["acceptance_criteria"] if a["type"] == "judgment"]
    lines = [f"# Grading packet: task {reg['task_id']}", "", f"Spec snapshot sha256: {reg['spec_sha256']}",
             f"base_sha: {reg['base_sha']}", f"head_sha: {head}", "", "## Task spec (authoritative snapshot)", "", reg["spec_text"], "",
             "## Protected paths (modifying or deleting an existing file matching these is automatic FAIL; none were.",
             "Adding NEW files, including new tests, is allowed by policy and is not scope creep or an unrequested change by itself.)", ""]
    lines += [f"- `{g}`" for g in tamper.PROTECTED]
    lines += ["", "## Stage 1 results (all passed, or you would not be reading this)", ""]
    lines += [f"- {r['id']} ({r['type']}): passed" for r in stage1]
    lines += ["", "## Probe observations", ""] + ([f"- {p['id']}: {p['observation']}" for p in probes] or ["- none registered"])
    lines += ["", "## Judgment criteria (score under completeness)", ""]
    lines += [f"- {a['id']}: {a['text']}" for a in judgment] or ["- none"]
    lines += ["", "## Your task", "", "Score the four dimensions per your instructions. Return only the JSON object."]
    (pdir / "packet.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    diff = tamper.git(clone, "diff", "--no-color", f"{reg['base_sha']}..{head}").stdout
    note = ""
    if len(diff) > DIFF_CAP:
        stat = tamper.git(clone, "diff", "--stat", f"{reg['base_sha']}..{head}").stdout
        note = f"[diff truncated at {DIFF_CAP} bytes; read the checkout for the rest]\n--- stat ---\n{stat.decode('utf-8', 'replace')}"
        diff = diff[:DIFF_CAP]
    (pdir / "diff.patch").write_bytes(diff + (b"\n" + note.encode() if note else b""))


# ---------------------------------------------------------------- invocation + validation
def invoke(clone: Path, pdir: Path, model: str, cfg: dict) -> dict:
    schema = json.dumps(json.loads((TOOL_DIR / "schemas" / "stage2-output.schema.json").read_text()))
    argv = [
        os.environ.get("KF_GRADER_CLAUDE", "claude"), "-p", "--agent", "kf-grader",
        "--agents", json.dumps({"kf-grader": agent_def()}),
        "--tools", "Read,Grep,Glob", "--disallowedTools", "mcp__*", "--strict-mcp-config",
        "--permission-mode", "dontAsk", "--setting-sources", "user", "--no-session-persistence",
        "--model", model, "--max-turns", "30", "--max-budget-usd", str(cfg.get("stage2_budget_usd", 3)),
        "--add-dir", str(pdir), "--json-schema", schema, "--output-format", "json",
        f"Grade the submission described in {pdir}/packet.md. Follow your instructions exactly.",
    ]
    try:
        p = subprocess.run(argv, cwd=clone, capture_output=True, text=True, stdin=subprocess.DEVNULL,
                           timeout=int(cfg.get("stage2_timeout_s", 900)))
    except FileNotFoundError:
        raise Stage2Unavailable("claude binary not found")
    except subprocess.TimeoutExpired:
        raise Stage2Unavailable("stage 2 timed out")
    if p.returncode != 0:
        raise Stage2Unavailable(f"claude exited {p.returncode}: {p.stderr.strip()[:300]}")
    try:
        env = json.loads(p.stdout)
    except ValueError:
        raise Stage2Unavailable("claude output is not JSON")
    if not isinstance(env, dict) or env.get("is_error"):
        raise Stage2Unavailable(f"claude reported an error: {str(env.get('result'))[:200] if isinstance(env, dict) else env}")
    payload = env.get("structured_output")
    if payload is None:
        payload = env.get("result")
    if isinstance(payload, str):
        s = re.sub(r"^```(?:json)?\s*|\s*```$", "", payload.strip())
        try:
            payload = json.loads(s)
        except ValueError:
            raise Stage2Unavailable("stage 2 result is not JSON")
    return validate(payload)


def validate(obj: object) -> dict:
    if not isinstance(obj, dict) or not isinstance(obj.get("dimensions"), dict):
        raise Stage2Unavailable("schema: missing dimensions")
    dims = obj["dimensions"]
    if set(dims) != set(DIMS):
        raise Stage2Unavailable(f"schema: dimensions must be exactly {DIMS}")
    out = {}
    for k in DIMS:
        d = dims[k]
        if not isinstance(d, dict) or isinstance(d.get("score"), bool) or not isinstance(d.get("score"), int) or not 0 <= d["score"] <= 10:
            raise Stage2Unavailable(f"schema: {k}.score must be an integer 0..10")
        ev = d.get("evidence", [])
        if not isinstance(ev, list) or not all(isinstance(e, str) for e in ev) or not isinstance(d.get("reason", ""), str):
            raise Stage2Unavailable(f"schema: {k} evidence/reason malformed")
        out[k] = {"score": d["score"], "evidence": ev, "reason": d.get("reason", "")}
    findings = obj.get("findings", [])
    flags = obj.get("injection_flags", [])
    if not isinstance(findings, list) or not isinstance(flags, list) or not all(isinstance(f, str) for f in flags):
        raise Stage2Unavailable("schema: findings/injection_flags malformed")
    return {"dimensions": out, "findings": [f for f in findings if isinstance(f, dict)], "injection_flags": flags}


# ---------------------------------------------------------------- deterministic post-checks
def _evidence_ok(items: list[str], ac_ids: set[str], clone: Path, deleted: set[str]) -> bool:
    good = 0
    for raw in items:
        item = raw.strip()
        if not item:
            continue
        head = re.split(r"[\s:]", item, maxsplit=1)[0]
        if head in ac_ids or item.lower().startswith("probe"):
            good += 1
            continue
        if PATH_LIKE.match(item) and ("/" in item or "." in item):
            path = re.sub(r":\d+(?:-\d+)?$", "", item)
            if (clone / path).exists() or path in deleted:
                good += 1
            else:
                return False  # cites a path that is not in the repo
    return good >= 1


def post_check(run: dict, reg: dict, clone: Path, head: str, threshold: int) -> dict:
    ac_ids = {a["id"] for a in reg["acceptance_criteria"]}
    deleted = {p for s, p in tamper.changed(clone, reg["base_sha"], head) if s == "D"}
    for k, d in run["dimensions"].items():
        if not _evidence_ok(d["evidence"], ac_ids, clone, deleted):
            d["score"] = min(d["score"], 6)
            d["evidence_capped"] = True
        d["failed"] = d["score"] < threshold
        d["reason"] = _redact(d["reason"])
    return run


def _redact(text: str) -> str:
    text = re.sub(r"\b(?:(?:score[sd]?|rated?|rating)\s+(?:of|at|as|is|was)?\s*)?\d{1,2}\s*(?:/|out of)\s*10\b", "", text, flags=re.I)
    text = re.sub(r"\b(?:score[sd]?|rated?|rating)\b\s*(?:of|at|as|:|=|is|was)?\s*\d{1,2}\b", "", text, flags=re.I)
    return re.sub(r"\s{2,}", " ", text).strip()


def _median_merge(runs: list[dict], threshold: int) -> dict:
    merged = {"dimensions": {}, "findings": [], "injection_flags": [], "runs": len(runs)}
    for k in DIMS:
        scores = sorted(r["dimensions"][k]["score"] for r in runs)
        med = int(statistics.median(scores))
        src = next(r["dimensions"][k] for r in runs if r["dimensions"][k]["score"] == med)
        merged["dimensions"][k] = {**src, "score": med, "failed": med < threshold, "all_scores": scores}
    seen = set()
    for r in runs:
        for f in r["findings"]:
            key = json.dumps(f, sort_keys=True)
            if key not in seen:
                seen.add(key)
                merged["findings"].append(f)
        for fl in r["injection_flags"]:
            if fl not in merged["injection_flags"]:
                merged["injection_flags"].append(fl)
    return merged


# ---------------------------------------------------------------- entry point
def run(*, reg: dict, clone: Path, head: str, cfg: dict, home: Path, stage1: list[dict], probes: list[dict]) -> dict | None:
    threshold = int(cfg["threshold"])
    model = pick_model(cfg, reg)
    pdir = home / "work" / "packets" / uuid.uuid4().hex[:12]
    before = tree_checksum(clone)
    try:
        build_packet(pdir, reg, clone, head, stage1, probes)
        runs = [post_check(invoke(clone, pdir, model, cfg), reg, clone, head, threshold)]
        lo = min(d["score"] for d in runs[0]["dimensions"].values())
        if cfg.get("boundary_rescore", True) and lo in (7, 8):
            for _ in range(2):  # Module 12 boundary rescoring: two more independent runs, per-dimension median
                runs.append(post_check(invoke(clone, pdir, model, cfg), reg, clone, head, threshold))
        result = _median_merge(runs, threshold)  # one run: the median of one is itself
    except Stage2Unavailable as e:
        sys.stderr.write(f"[kf-grade] stage2 unavailable: {e}\n")
        return None
    finally:
        shutil.rmtree(pdir, ignore_errors=True)
    after = tree_checksum(clone)
    if before != after:
        raise RuntimeError("Stage 2 modified the read-only checkout; isolation failed")
    result.update({"model": model, "checkout_sha256_before": before, "checkout_sha256_after": after})
    return result
