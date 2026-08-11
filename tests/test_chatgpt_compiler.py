#!/usr/bin/env python3
"""Contract tests for the ChatGPT Projects compiler target."""

import copy
import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent


def _load_compiler():
    spec = importlib.util.spec_from_file_location(
        "kf_compile_chatgpt_tests",
        REPO_ROOT / "compiler" / "kf-compile.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


compiler = _load_compiler()


class TestChatGPTCompiler(unittest.TestCase):
    def setUp(self):
        self.binding = compiler.load_binding("chatgpt")
        self.tempdir = tempfile.TemporaryDirectory()
        self.output_root = Path(self.tempdir.name) / "output"
        self.output_root.mkdir()

    def tearDown(self):
        compiler.MODULES_DIR = REPO_ROOT / "modules"
        self.tempdir.cleanup()

    def compile(self, binding=None):
        return compiler.compile_chatgpt(
            binding or self.binding,
            self.output_root,
            dry_run=False,
            diff_mode=False,
            version="test",
        )

    def isolated_modules(self):
        module_root = Path(self.tempdir.name) / "modules"
        shutil.copytree(REPO_ROOT / "modules", module_root)
        compiler.MODULES_DIR = module_root
        return module_root

    def test_successful_real_compilation_contracts(self):
        manifest = self.compile()
        kernel_path = self.output_root / "kf-chatgpt-instructions.md"
        kernel = kernel_path.read_text(encoding="utf-8")
        constraints = self.binding["constraints"]

        self.assertEqual(len(manifest), len(self.binding["filename_map"]))
        self.assertLessEqual(len(kernel), constraints["instructions_target_chars"])
        self.assertLessEqual(len(kernel), constraints["instructions_char_limit"])
        for required in constraints["required_knowledge_files"]:
            self.assertIn(required, kernel)
            self.assertTrue((self.output_root / required).is_file())
        instruction_entry = next(
            entry for entry in manifest
            if entry["output"] == "kf-chatgpt-instructions.md"
        )
        self.assertEqual(instruction_entry["section"], "ChatGPT Instructions")
        self.assertNotIn("Claude Code", kernel)
        self.assertNotIn("## CC ", kernel)
        self.assertIn("degraded", kernel.lower())

        for artifact in self.output_root.rglob("*.md"):
            content = artifact.read_text(encoding="utf-8").lower()
            for term in constraints["forbidden_terms"]:
                self.assertNotIn(term.lower(), content, str(artifact))

    def test_required_knowledge_must_be_mapped(self):
        binding = copy.deepcopy(self.binding)
        source = next(
            key for key, value in binding["filename_map"].items()
            if value == binding["constraints"]["required_knowledge_files"][0]
        )
        del binding["filename_map"][source]
        with self.assertRaisesRegex(RuntimeError, "not mapped"):
            self.compile(binding)

    def test_kernel_must_reference_exact_required_path(self):
        module_root = self.isolated_modules()
        orchestrator = module_root / "00_orchestrator.md"
        content = orchestrator.read_text(encoding="utf-8")
        content = content.replace(
            "knowledge/01_Navigator_Agent.md", "01_Navigator_Agent.md"
        )
        orchestrator.write_text(content, encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "does not reference"):
            self.compile()

    def test_target_budget_exceeded_fails(self):
        binding = copy.deepcopy(self.binding)
        binding["constraints"]["instructions_target_chars"] = 100
        with self.assertRaisesRegex(RuntimeError, "exceed budget"):
            self.compile(binding)

    def test_hard_limit_exceeded_fails(self):
        binding = copy.deepcopy(self.binding)
        binding["constraints"]["instructions_target_chars"] = 99
        binding["constraints"]["instructions_char_limit"] = 100
        with self.assertRaisesRegex(RuntimeError, "exceed hard limit"):
            self.compile(binding)

    def test_forbidden_term_in_artifact_fails(self):
        module_root = self.isolated_modules()
        source = module_root / "01_navigator.md"
        content = source.read_text(encoding="utf-8")
        first_line, remainder = content.split("\n", 1)
        source.write_text(
            first_line + "\n\nForbidden marker: GITNEXUS\n" + remainder,
            encoding="utf-8",
        )
        with self.assertRaisesRegex(RuntimeError, "forbidden platform term"):
            self.compile()


if __name__ == "__main__":
    unittest.main(verbosity=2)
