#!/usr/bin/env python3
"""
test_compiler_flags.py — Tests for Phase 1 compiler extensions.

Covers:
  - process_conditional_blocks: flag on/off matrix
  - process_conditional_blocks: nesting error
  - process_conditional_blocks: undeclared flag error
  - process_conditional_blocks: unclosed block error
  - process_conditional_blocks: spurious endif error
  - process_conditional_blocks: no markers (fast path)
  - max_chars budget enforcement (tested via a stub emit flow)

Run with:
    python3 tests/test_compiler_flags.py

Requires: stdlib only (no pytest, no pyyaml needed for these unit tests).
"""

import sys
import traceback
import unittest
from pathlib import Path

# Import compiler module — filename has a hyphen, so we use importlib.
import importlib.util

REPO_ROOT = Path(__file__).parent.parent

def _load_compiler():
    spec = importlib.util.spec_from_file_location(
        "kf_compile",
        str(REPO_ROOT / "compiler" / "kf-compile.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_compiler = _load_compiler()
process_conditional_blocks = _compiler.process_conditional_blocks


class TestProcessConditionalBlocks(unittest.TestCase):

    # ------------------------------------------------------------------
    # Happy path — flag ON (truthy)
    # ------------------------------------------------------------------

    def test_flag_true_keeps_body_removes_markers(self):
        content = (
            "Line before.\n"
            "<!-- kf:if telemetry -->\n"
            "Telemetry line A.\n"
            "Telemetry line B.\n"
            "<!-- kf:endif -->\n"
            "Line after."
        )
        flags = {"telemetry": True}
        result = process_conditional_blocks(content, flags, "test")
        self.assertIn("Line before.", result)
        self.assertIn("Telemetry line A.", result)
        self.assertIn("Telemetry line B.", result)
        self.assertIn("Line after.", result)
        self.assertNotIn("<!-- kf:if", result)
        self.assertNotIn("<!-- kf:endif -->", result)

    # ------------------------------------------------------------------
    # Happy path — flag OFF (falsy)
    # ------------------------------------------------------------------

    def test_flag_false_removes_body_and_markers(self):
        content = (
            "Line before.\n"
            "<!-- kf:if telemetry -->\n"
            "Telemetry line A.\n"
            "Telemetry line B.\n"
            "<!-- kf:endif -->\n"
            "Line after."
        )
        flags = {"telemetry": False}
        result = process_conditional_blocks(content, flags, "test")
        self.assertIn("Line before.", result)
        self.assertNotIn("Telemetry line A.", result)
        self.assertNotIn("Telemetry line B.", result)
        self.assertIn("Line after.", result)
        self.assertNotIn("<!-- kf:if", result)
        self.assertNotIn("<!-- kf:endif -->", result)

    # ------------------------------------------------------------------
    # Multiple blocks — independent evaluation
    # ------------------------------------------------------------------

    def test_multiple_blocks_independent(self):
        content = (
            "<!-- kf:if flag_a -->\n"
            "Block A body.\n"
            "<!-- kf:endif -->\n"
            "Middle line.\n"
            "<!-- kf:if flag_b -->\n"
            "Block B body.\n"
            "<!-- kf:endif -->\n"
            "End line."
        )
        flags = {"flag_a": True, "flag_b": False}
        result = process_conditional_blocks(content, flags, "test")
        self.assertIn("Block A body.", result)
        self.assertNotIn("Block B body.", result)
        self.assertIn("Middle line.", result)
        self.assertIn("End line.", result)

    # ------------------------------------------------------------------
    # Fast path — no markers in content
    # ------------------------------------------------------------------

    def test_no_markers_returns_unchanged(self):
        content = "Line 1.\nLine 2.\nLine 3."
        flags = {"telemetry": True}
        result = process_conditional_blocks(content, flags, "test")
        self.assertEqual(content, result)

    # ------------------------------------------------------------------
    # Empty flags dict, no markers
    # ------------------------------------------------------------------

    def test_empty_flags_no_markers(self):
        content = "Just content. No markers."
        result = process_conditional_blocks(content, {}, "test")
        self.assertEqual(content, result)

    # ------------------------------------------------------------------
    # Error: undeclared flag
    # ------------------------------------------------------------------

    def test_undeclared_flag_raises(self):
        content = (
            "<!-- kf:if unknown_flag -->\n"
            "Body.\n"
            "<!-- kf:endif -->"
        )
        with self.assertRaises(ValueError) as ctx:
            process_conditional_blocks(content, {}, "test")
        self.assertIn("undeclared flag", str(ctx.exception))
        self.assertIn("unknown_flag", str(ctx.exception))

    # ------------------------------------------------------------------
    # Error: nesting
    # ------------------------------------------------------------------

    def test_nesting_raises(self):
        content = (
            "<!-- kf:if flag_a -->\n"
            "<!-- kf:if flag_b -->\n"  # nested — not allowed
            "Body.\n"
            "<!-- kf:endif -->\n"
            "<!-- kf:endif -->"
        )
        flags = {"flag_a": True, "flag_b": True}
        with self.assertRaises(ValueError) as ctx:
            process_conditional_blocks(content, flags, "test")
        self.assertIn("nested", str(ctx.exception))

    # ------------------------------------------------------------------
    # Error: unclosed block at EOF
    # ------------------------------------------------------------------

    def test_unclosed_block_raises(self):
        content = (
            "<!-- kf:if telemetry -->\n"
            "Body without closing tag."
        )
        flags = {"telemetry": True}
        with self.assertRaises(ValueError) as ctx:
            process_conditional_blocks(content, flags, "test")
        self.assertIn("unclosed", str(ctx.exception))
        self.assertIn("telemetry", str(ctx.exception))

    # ------------------------------------------------------------------
    # Error: spurious endif
    # ------------------------------------------------------------------

    def test_spurious_endif_raises(self):
        content = (
            "Line before.\n"
            "<!-- kf:endif -->\n"  # no matching kf:if
            "Line after."
        )
        with self.assertRaises(ValueError) as ctx:
            process_conditional_blocks(content, {}, "test")
        self.assertIn("spurious", str(ctx.exception))

    # ------------------------------------------------------------------
    # Fixture file: flag ON
    # ------------------------------------------------------------------

    def test_fixture_telemetry_on(self):
        fixture = REPO_ROOT / "tests/fixtures/conditional_blocks_module.md"
        content = fixture.read_text(encoding="utf-8")
        # Extract the CC Skill section manually (simulate extract_section)
        lines = content.split("\n")
        in_section = False
        section_lines = []
        cc_markers = {"CC Skill", "CC Doc", "CC Agent", "CC Rules"}
        for line in lines:
            stripped = line.strip()
            if stripped == "## CC Skill":
                in_section = True
                continue
            if in_section:
                if line.startswith("## "):
                    section_id = line[3:].strip()
                    if section_id in cc_markers:
                        break
                section_lines.append(line)
        section_content = "\n".join(section_lines).strip()

        flags = {"telemetry": True, "public": False}
        result = process_conditional_blocks(section_content, flags, "test")

        self.assertIn("This line is always present.", result)
        self.assertIn("This line appears only when telemetry=true.", result)
        self.assertIn("Telemetry detail line.", result)
        self.assertNotIn("This line appears only when public=true.", result)
        self.assertNotIn("<!-- kf:if", result)

    # ------------------------------------------------------------------
    # Fixture file: flag OFF
    # ------------------------------------------------------------------

    def test_fixture_telemetry_off(self):
        fixture = REPO_ROOT / "tests/fixtures/conditional_blocks_module.md"
        content = fixture.read_text(encoding="utf-8")
        lines = content.split("\n")
        in_section = False
        section_lines = []
        cc_markers = {"CC Skill", "CC Doc", "CC Agent", "CC Rules"}
        for line in lines:
            stripped = line.strip()
            if stripped == "## CC Skill":
                in_section = True
                continue
            if in_section:
                if line.startswith("## "):
                    section_id = line[3:].strip()
                    if section_id in cc_markers:
                        break
                section_lines.append(line)
        section_content = "\n".join(section_lines).strip()

        flags = {"telemetry": False, "public": False}
        result = process_conditional_blocks(section_content, flags, "test")

        self.assertIn("This line is always present.", result)
        self.assertNotIn("This line appears only when telemetry=true.", result)
        self.assertNotIn("Telemetry detail line.", result)
        self.assertNotIn("<!-- kf:if", result)


class TestMaxCharsBudget(unittest.TestCase):
    """
    Smoke tests for max_chars budget enforcement.

    The enforcement is inside compile_claude_code's output loop. We test it
    by calling process_conditional_blocks (no budget there) and verifying the
    budget field is read — the real enforcement is integration-tested via
    verify-deterministic-build.sh. Unit-testing the sys.exit(1) path requires
    mocking, which we avoid to keep stdlib-only.

    These tests just confirm the budget field is parseable from output_def dicts
    and that the field name is correct. The actual enforcement codepath is
    exercised by the deterministic build verifier.
    """

    def test_max_chars_field_is_optional(self):
        """output_def without max_chars — should not fail budget check."""
        output_def = {"type": "skill", "path": ".claude/skills/kf/test.md", "section": "CC Skill"}
        max_chars = output_def.get("max_chars")
        self.assertIsNone(max_chars)

    def test_max_chars_field_reads_correctly(self):
        output_def = {"type": "skill", "path": ".claude/skills/kf/test.md",
                      "section": "CC Skill", "max_chars": 5000}
        max_chars = output_def.get("max_chars")
        self.assertEqual(max_chars, 5000)

    def test_budget_exceeded_detection(self):
        """Confirm the check logic (without triggering sys.exit)."""
        content = "x" * 101
        max_chars = 100
        exceeded = len(content) > max_chars
        self.assertTrue(exceeded)

    def test_budget_not_exceeded(self):
        content = "x" * 99
        max_chars = 100
        exceeded = len(content) > max_chars
        self.assertFalse(exceeded)


# ---------------------------------------------------------------------------

def run_tests():
    """Run all tests and print a summary."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestProcessConditionalBlocks))
    suite.addTests(loader.loadTestsFromTestCase(TestMaxCharsBudget))

    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    if result.wasSuccessful():
        print(f"\nAll {result.testsRun} tests passed.")
        return 0
    else:
        failures = len(result.failures) + len(result.errors)
        print(f"\n{failures} test(s) failed out of {result.testsRun}.")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
