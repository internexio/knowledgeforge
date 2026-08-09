# Module NN: Conditional Blocks Test Fixture
**Version:** 1.0.0
**Last Updated:** 2026-08-09

This fixture is used by `tests/test_compiler_flags.py` to test `process_conditional_blocks`.
It is NOT a real KF module — do not include it in any compile binding.

---

## CC Skill

This line is always present.

<!-- kf:if telemetry -->
This line appears only when telemetry=true.
Telemetry detail line.
<!-- kf:endif -->

This line is always present after the block.

<!-- kf:if public -->
This line appears only when public=true.
<!-- kf:endif -->

Final always-present line.

## CC Doc

Doc section with a conditional block.

<!-- kf:if telemetry -->
Telemetry docs paragraph.
<!-- kf:endif -->

Doc section end.
