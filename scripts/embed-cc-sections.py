#!/usr/bin/env python3
"""
embed-cc-sections.py — Bootstrap compilation sections into core modules.

Reads existing hand-crafted CC files and embeds their content into the
corresponding core module files as ## CC Skill / ## CC Doc / ## CC Agent
/ ## CC Rules sections. Run once to establish the canonical source of truth
in core; from then on, edit the sections in core (not the CC files directly).

Usage:
    python3 scripts/embed-cc-sections.py --cc /path/to/knowledgeforge-cc
    python3 scripts/embed-cc-sections.py --cc /path/to/knowledgeforge-cc --dry-run
"""

import argparse
import sys
from pathlib import Path

CORE_ROOT = Path(__file__).parent.parent
MODULES_DIR = CORE_ROOT / "modules"


def section_exists(module_content: str, section_name: str) -> bool:
    return f"\n## {section_name}\n" in module_content or \
           module_content.startswith(f"## {section_name}\n")


def embed_section(module_path: Path, section_name: str, content: str,
                  dry_run: bool) -> str:
    """Append a ## section to a module file. Returns status string."""
    module_content = module_path.read_text(encoding="utf-8")

    if section_exists(module_content, section_name):
        return "already_present"

    new_content = module_content.rstrip("\n") + f"\n\n## {section_name}\n\n{content}\n"

    if dry_run:
        return "would_embed"
    else:
        module_path.write_text(new_content, encoding="utf-8")
        return "embedded"


def find_module(module_num: str) -> Path | None:
    matches = list(MODULES_DIR.glob(f"{module_num}_*.md"))
    return matches[0] if matches else None


def main():
    parser = argparse.ArgumentParser(
        description="Embed CC compilation sections into core modules"
    )
    parser.add_argument("--cc", required=True,
                        help="Path to knowledgeforge-cc repo root")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without writing")
    args = parser.parse_args()

    cc_root = Path(args.cc).resolve()
    if not cc_root.exists():
        sys.stderr.write(f"CC repo not found: {cc_root}\n")
        sys.exit(1)

    skills_dir = cc_root / ".claude" / "skills" / "kf"
    agents_dir = cc_root / ".claude" / "agents"
    docs_dir = cc_root / ".claude" / "docs" / "knowledgeforge"
    rules_dir = cc_root / ".claude" / "rules"

    results = []

    def process(module_num: str, section_name: str, src_path: Path):
        module = find_module(module_num)
        if module is None:
            results.append((module_num, section_name, "module_not_found"))
            return
        if not src_path.exists():
            results.append((module.name, section_name, f"src_missing: {src_path.name}"))
            return
        content = src_path.read_text(encoding="utf-8").strip()
        status = embed_section(module, section_name, content, args.dry_run)
        results.append((module.name, section_name, status))

    # --- Module 00: orchestrator ---
    process("00", "CC Agent",  agents_dir / "kf.md")
    process("00", "CC Rules",  rules_dir / "kf-meta.md")

    # --- Mode modules: skill + agent ---
    mode_map = {
        "01": ("navigator",   "navigator"),
        "02": ("builder",     "builder"),
        "05": ("expert",      "expert"),
        "07": ("critic",      "critic"),
        "08": ("synthesizer", "synthesizer"),
        "09": ("debugger",    "debugger"),
        "10": ("strategist",  "strategist"),
        "11": ("calibrator",  "calibrator"),
    }

    for module_num, (skill_name, agent_name) in mode_map.items():
        process(module_num, "CC Skill", skills_dir / f"{skill_name}.md")
        process(module_num, "CC Agent", agents_dir / f"{agent_name}.md")

    # --- Cross-cutting modules: doc ---
    doc_map = {
        "12": "12_calibration_layer.md",
        "13": "13_decision_classification.md",
        "14": "14_metacognitive_monitor.md",
        "15": "15_grounding_scores.md",
        "16": "16_operational_bounds.md",
        "17": "17_temporal_knowledge.md",
        "18": "18_salience_allocation.md",
        "19": "19_memory_architecture.md",
        "20": "20_permission_model.md",
        "21": "21_knowledge_accretion.md",
        "22": "22_semantic_wiki_search.md",
        "23": "23_taxonomy_enforcement.md",
        "24": "24_verbatim_history_mining.md",
    }

    for module_num, doc_file in doc_map.items():
        process(module_num, "CC Doc", docs_dir / doc_file)

    # --- Report ---
    mode = "DRY RUN" if args.dry_run else "EMBED"
    print(f"\nCC Section Bootstrap [{mode}]")
    print("=" * 60)
    for (module, section, status) in results:
        if status == "embedded":
            marker = "  +"
        elif status == "would_embed":
            marker = "  +"
        elif status == "already_present":
            marker = "  ·"
        else:
            marker = "  !"
        print(f"{marker} [{section}] in {module} → {status}")

    counts = {}
    for _, _, s in results:
        counts[s] = counts.get(s, 0) + 1

    print("=" * 60)
    embedded = counts.get("embedded", counts.get("would_embed", 0))
    skipped = counts.get("already_present", 0)
    errors = sum(v for k, v in counts.items()
                 if k not in ("embedded", "would_embed", "already_present"))
    action = "Would embed" if args.dry_run else "Embedded"
    print(f"{action}: {embedded}  Already present: {skipped}  Errors: {errors}")


if __name__ == "__main__":
    main()
