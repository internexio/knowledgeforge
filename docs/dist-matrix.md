# KnowledgeForge Distribution Matrix

Platform binding inventory — capabilities, module coverage, and implementation status.

**Version:** 7.30.0 | **Updated:** 2026-08-09

---

## Platform Capabilities

| Capability | claude-code | claude-projects | vscode | codex | cursor | chatgpt | gemini | generic |
|---|---|---|---|---|---|---|---|---|
| **Status** | active | active | active | deferred | deferred | deferred | deferred | deferred |
| Filesystem | ✓ | — | ✓ | ✓ | ✓ | — | — | — |
| Hooks | ✓ | — | — | — | — | — | — | — |
| Sub-agents | ✓ | — | — | — | — | — | — | — |
| Skills (on-demand) | ✓ | — | — | — | — | — | — | — |
| Docs directory | ✓ | — | — | — | — | — | — | — |
| Slash commands | ✓ | — | ✓ | — | — | — | — | — |
| MCP servers | ✓ | — | — | — | ✓ | — | — | — |
| Project knowledge | — | ✓ | — | — | — | ✓ | ✓(gem) | — |

---

## Module Coverage by Platform

| Module | Topic | claude-code | claude-projects | vscode | codex | cursor | chatgpt | gemini | generic |
|---|---|---|---|---|---|---|---|---|---|
| M00 | Orchestrator | agent + rules | verbatim | verbatim | deferred | deferred | instructions | instructions | instructions |
| M01 | Navigator | skill + agent | verbatim | resource | deferred | deferred | knowledge | — | — |
| M02 | Builder | skill + agent | verbatim | resource | deferred | deferred | knowledge | — | — |
| M03 | Coordinator | skill + agent | verbatim | resource | deferred | deferred | knowledge | — | — |
| M04 | Spec Templates | — | verbatim | — | deferred | deferred | — | — | — |
| M05 | Expert | skill + agent | verbatim | resource | deferred | deferred | knowledge | — | — |
| M06 | Quick Reference | — | verbatim | — | deferred | deferred | — | — | instructions |
| M07 | Critic | skill + agent(×2) | verbatim | resource | deferred | deferred | knowledge | — | — |
| M08 | Synthesizer | skill + agent | verbatim | resource | deferred | deferred | knowledge | — | — |
| M09 | Debugger | skill + agent | verbatim | resource | deferred | deferred | knowledge | — | — |
| M10 | Strategist | skill + agent | verbatim | resource | deferred | deferred | knowledge | — | — |
| M11 | Calibrator | skill + agent | verbatim | resource | deferred | deferred | knowledge | — | — |
| M12 | Calibration Layer | doc | verbatim | — | deferred | deferred | — | — | — |
| M13 | Decision Classification | doc | verbatim | — | deferred | deferred | instructions | instructions | instructions |
| M14 | Metacognitive Monitor | doc | verbatim | — | deferred | deferred | — | — | — |
| M15 | Grounding Scores | doc | verbatim | — | deferred | deferred | — | — | — |
| M16 | Operational Bounds | doc | verbatim | — | deferred | deferred | — | — | — |
| M17 | Temporal Knowledge | doc | verbatim | — | deferred | deferred | — | — | — |
| M18 | Salience Allocation | doc | verbatim | — | deferred | deferred | — | — | — |
| M19 | Memory Architecture | doc | verbatim | — | deferred | deferred | — | — | — |
| M20 | Permission Model | doc | verbatim | — | deferred | deferred | — | — | — |
| M21 | Knowledge Accretion | doc + agent | verbatim | — | deferred | deferred | — | — | — |
| M22 | Semantic Wiki Search | doc | verbatim | — | deferred | deferred | — | — | — |
| M23 | Taxonomy Enforcement | doc | verbatim | — | deferred | deferred | — | — | — |
| M24 | Verbatim History Mining | doc | verbatim | — | deferred | deferred | — | — | — |
| M25 | Entity Relationship Analysis | doc | verbatim | — | deferred | deferred | — | — | — |

**Key:** `skill + agent` = extracted CC Skill + CC Agent sections | `verbatim` = full module content | `resource` = full content as extension resource | `instructions` = summary in system instructions | `knowledge` = uploaded knowledge file | `deferred` = platform not yet implemented | `—` = not applicable or omitted

---

## Output File Counts

| Platform | Active outputs | Notes |
|---|---|---|
| claude-code | 37 files | skills, agents, docs, rules; verified by compiler |
| claude-projects | 26 files | all modules verbatim |
| vscode | 10 files | orchestrator + 9 mode resources + mode registry |
| plugin-bundle | varies | agent subset for embedding in consumer repos |
| codex | 0 (deferred) | TOML agent format pending tool-name mapping |
| cursor | 0 (deferred) | .mdc rules format |
| chatgpt | 0 (deferred) | instructions + knowledge files |
| gemini | 0 (deferred) | system instruction or gem format |
| generic | 0 (deferred) | single consolidated markdown |

---

## Binding Status Legend

| Status | Meaning |
|---|---|
| `active` | Compiler target implemented; outputs verified |
| `deferred` | Contract surface defined; compiler target not yet implemented |
| `deprecated` | Target removed; artifacts frozen (knowledgeforge-cw) |

---

## Adding a New Platform

1. Create `platform-bindings/<platform>.yaml` with `status: deferred`
2. Define `capabilities:`, `constraints:`, `output_structure:`, `module_outputs:`, `contract_surface:`, `bind_when:`
3. Add a compiler handler (`compile_<platform>()`) in `compiler/kf-compile.py`
4. Add `<platform>` to the `--target` argparse choices
5. Verify: `python3 compiler/kf-compile.py --target <platform> --output /tmp/test-<platform>`
6. Update this matrix
