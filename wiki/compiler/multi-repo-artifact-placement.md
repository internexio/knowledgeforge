# Multi-Repo Compile Pipeline: Artifact Placement for Human Navigation

```yaml
metadata:
  source_mode: direct
  source_session: redacted
  created: "2026-04-15T00:00:00Z"
  confidence: 0.95
  grounding_score: 0.95
  grounding_source: "Observed directly while implementing kf-compile load map feature"
  novelty_type: reusable_pattern
  staleness_risk: stable
  importance: 3
  pinned: false
  accreted_in: "7.0.0"
  source_fingerprint: "session:2748dcca-13e3-4cf1-87a3-bf6a55ba87c7 / kf-compile load-map 2026-04-15"
```

---

## Pattern

**Compiled artifacts that carry relative links back to their source must live in the source repo, not the derived/variant repo.**

GitHub resolves relative markdown links only within the same repository. A link like `modules/02_builder.md#cc-skill` works when the file containing it is in `knowledgeforge-core`. The same link in `knowledgeforge-cc` resolves to nothing — GitHub has no mechanism for cross-repo relative paths.

---

## Concrete Form

```
knowledgeforge-core/              ← source repo
├── modules/
│   └── 02_builder.md             ← link target lives here
└── .kf-load-map-claude-code.md   ← map MUST live here too
                                     so modules/02_builder.md#cc-skill resolves

knowledgeforge-cc/                ← variant repo
└── .kf-compile-manifest.json     ← machine-readable only (no links needed)
```

---

## Rule

| Artifact type | Where it lives | Why |
|---|---|---|
| Human-navigable map (MD with links) | Source repo root | Relative links resolve on GitHub |
| Machine-readable manifest (JSON) | Variant repo | No links, no placement constraint |
| Compiled outputs | Variant repo | That's the point of the variant |

---

## Anti-Pattern

Writing the human-navigable map to the variant repo with links like `../../knowledgeforge-core/modules/file.md#section` — these paths do not traverse repo boundaries on GitHub. They appear broken in the UI even if they would resolve on a local filesystem where both repos are siblings.

---

## Generalization

Applies to any multi-repo compile pipeline where:
- Repo A is the source of truth (specs, modules, templates)
- Repo B is the compiled output (agents, skills, docs)
- A human-navigable index/map needs links into Repo A's files

The map belongs in Repo A. The compiled artifacts belong in Repo B.

---

## Discovery Context

Emerged while adding a GitHub-navigable section load map to `kf-compile.py`. Initial implementation wrote the MD to the variant repo (`knowledgeforge-cc`) with relative paths crossing into `knowledgeforge-core`. Links were broken on GitHub. Fix: write the MD to `CORE_ROOT` where `modules/` is a direct sibling — links become trivial.
