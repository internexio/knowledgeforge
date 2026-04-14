#!/usr/bin/env python3
"""
run_routing_tests.py — KF Phase 1 Routing Accuracy Test Runner

Tests the kf-route.py hook against the routing_test_suite.yaml.
Calls Gemini Flash Lite directly (bypasses hook stdin protocol for simpler testing).

Usage:
    python3 tests/run_routing_tests.py [--suite tests/routing_test_suite.yaml] [--verbose]
    python3 tests/run_routing_tests.py --model gemini-2.0-flash  # use a different model

Env:
    GEMINI_API_KEY  required

Targets:
    Mode accuracy:           >85%
    Cross-cutting recall:    >80%
"""

import sys
import json
import os
import argparse
import urllib.request
import urllib.error
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing pyyaml. Run: pip install pyyaml")
    sys.exit(1)

# ─── Config ───────────────────────────────────────────────────────────────────

REPO_ROOT    = Path(__file__).parent.parent
INDEX_PATH   = REPO_ROOT / "hooks" / "kf_module_index.txt"
DEFAULT_SUITE = REPO_ROOT / "tests" / "routing_test_suite.yaml"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def gemini_url(model: str) -> str:
    return (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={GEMINI_API_KEY}"
    )

# ─── Classify via Gemini ──────────────────────────────────────────────────────

def classify(prompt: str, index: str, model: str, timeout: int = 10) -> dict:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    routing_input = f"{index}\"{prompt}\""

    body = json.dumps({
        "contents": [
            {"parts": [{"text": routing_input}]}
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0,
            "maxOutputTokens": 200,
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        gemini_url(model),
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")

    data = json.loads(raw)
    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    return json.loads(text)

# ─── Normalizers ──────────────────────────────────────────────────────────────

def normalize_mode(val) -> set:
    if val is None or val == "null":
        return {None, "null", "none", ""}
    if isinstance(val, list):
        return {v.lower() if v else None for v in val}
    return {val.lower()}


def normalize_cc(val) -> set:
    if not val:
        return set()
    return {str(m).upper() for m in val}


def mode_match(actual: str, expected_set: set) -> bool:
    actual_norm = (actual or "").lower() or None
    return actual_norm in expected_set or (actual_norm in ("", None) and None in expected_set)


def cc_recall(actual: list, expected: set) -> float:
    if not expected:
        return 1.0
    actual_set = normalize_cc(actual)
    hits = actual_set & expected
    return len(hits) / len(expected)

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="KF Routing Test Runner")
    parser.add_argument("--suite",   default=str(DEFAULT_SUITE), help="Path to test suite YAML")
    parser.add_argument("--model",   default="gemini-2.5-flash-lite", help="Gemini model to use")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all results")
    parser.add_argument("--timeout", type=int, default=10, help="HTTP timeout per call (seconds)")
    args = parser.parse_args()

    if not GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY not set. Run: source ~/.zshrc")
        sys.exit(1)

    # Load test suite
    suite_path = Path(args.suite)
    if not suite_path.exists():
        print(f"Test suite not found: {suite_path}")
        sys.exit(1)
    with open(suite_path) as f:
        suite = yaml.safe_load(f)
    tests = suite.get("tests", [])

    # Load module index
    if not INDEX_PATH.exists():
        print(f"Module index not found: {INDEX_PATH}")
        sys.exit(1)
    index = INDEX_PATH.read_text(encoding="utf-8")

    print(f"\nKF Routing Test Runner")
    print(f"Model:  {args.model}")
    print(f"Suite:  {suite_path.name}  ({len(tests)} tests)")
    print(f"{'─' * 60}")

    results = []
    for i, test in enumerate(tests, 1):
        test_id = test.get("id", f"t{i:02d}")
        prompt  = test["prompt"]
        expected_mode_raw = test.get("expected_mode")
        expected_decision = test.get("expected_decision", "")
        expected_cc_raw   = test.get("expected_cross_cutting", [])

        expected_modes = normalize_mode(expected_mode_raw)
        expected_cc    = normalize_cc(expected_cc_raw)

        print(f"[{i:02d}/{len(tests)}] {test_id}: {prompt[:55]}", end="", flush=True)

        try:
            routing = classify(prompt, index, args.model, args.timeout)
        except urllib.error.HTTPError as e:
            print(f"  ✗ HTTP {e.code}: {e.reason}")
            results.append({"id": test_id, "mode_pass": False, "cc_recall": 0.0, "error": f"HTTP {e.code}"})
            continue
        except TimeoutError:
            print(f"  ⏱ TIMEOUT")
            results.append({"id": test_id, "mode_pass": False, "cc_recall": 0.0, "error": "timeout"})
            continue
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            results.append({"id": test_id, "mode_pass": False, "cc_recall": 0.0, "error": str(e)})
            continue

        actual_mode     = routing.get("mode")
        actual_decision = routing.get("decision_type", "")
        actual_cc       = routing.get("cross_cutting") or []

        m_pass = mode_match(actual_mode, expected_modes)
        cc_r   = cc_recall(actual_cc, expected_cc)
        results.append({
            "id":               test_id,
            "mode_pass":        m_pass,
            "cc_recall":        cc_r,
            "actual_mode":      actual_mode,
            "actual_decision":  actual_decision,
            "actual_cc":        actual_cc,
            "expected_mode":    expected_mode_raw,
            "expected_decision":expected_decision,
            "expected_cc":      list(expected_cc),
        })

        status = "✓" if m_pass else "✗"
        cc_str = f"  CC:{cc_r:.0%}" if expected_cc else ""
        print(f"  {status} mode={actual_mode or 'null'} decision={actual_decision}{cc_str}")

        if args.verbose and not m_pass:
            print(f"       Expected: {expected_mode_raw}  |  Got: {actual_mode}")
            if expected_cc and cc_r < 1.0:
                missing = expected_cc - normalize_cc(actual_cc)
                print(f"       Missing CC: {missing}")

    # ─── Summary ──────────────────────────────────────────────────────────────

    total       = len(results)
    mode_passes = sum(1 for r in results if r["mode_pass"])
    errors      = sum(1 for r in results if r.get("error"))

    cc_tests = [r for r in results if r.get("expected_cc")]
    cc_avg   = sum(r["cc_recall"] for r in cc_tests) / len(cc_tests) if cc_tests else 1.0
    mode_pct = mode_passes / total if total else 0

    print(f"\n{'─' * 60}")
    print(f"Results: {mode_passes}/{total} mode correct  ({mode_pct:.0%})")
    print(f"Cross-cutting recall: {cc_avg:.0%}  (across {len(cc_tests)} tests with expected CC)")
    if errors:
        print(f"Errors/timeouts: {errors}")

    MODE_TARGET = 0.85
    CC_TARGET   = 0.80

    print(f"\n{'─' * 60}")
    mode_ok = mode_pct >= MODE_TARGET
    cc_ok   = cc_avg  >= CC_TARGET
    print(f"Mode accuracy:   {mode_pct:.0%}  target >{MODE_TARGET:.0%}  {'✓ PASS' if mode_ok else '✗ FAIL'}")
    print(f"CC recall:       {cc_avg:.0%}  target >{CC_TARGET:.0%}  {'✓ PASS' if cc_ok else '✗ FAIL'}")

    failures = [r for r in results if not r["mode_pass"] and not r.get("error")]
    if failures:
        print(f"\nMode mismatches ({len(failures)}):")
        for r in failures:
            print(f"  {r['id']}: expected={r['expected_mode']}  got={r.get('actual_mode','?')}")

    if mode_ok and cc_ok:
        print(f"\n✓ VALIDATION PASSED — ready to deploy to knowledgeforge-cc")
        sys.exit(0)
    else:
        print(f"\n✗ Below target — iterate on kf_module_index.txt and retest")
        sys.exit(1)


if __name__ == "__main__":
    main()
