---
title: MemPalace search results include raw frontmatter in first drawer text
source_mode: debugger
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-07-07
domain: integration
topic: semantic-search
tags: mempalace, semantic-search, frontmatter, api, empirical
related_entries: []
---

# MemPalace search results include raw frontmatter in first drawer text

## Pattern

When MemPalace mines a Markdown file with YAML frontmatter, the first drawer it creates includes the raw frontmatter block verbatim. Searching via `tool_search` (or `mempalace_search` MCP) returns this drawer in results, making metadata available without reading the source file.

## Concrete verification (2026-07-07)

During Module 22 Phase 2 implementation, `tool_search` results for wiki queries showed:

```python
{
  "text": "---\ntitle: Nginx rate-limit zones must distinguish...\nsource_mode: direct\n...\ndomain: infrastructure\ntopic: server-configuration\n---\n\n# Nginx rate-limit zones...",
  "wing": "wiki-kf-core",
  "room": "general",
  "source_file": "2026-06-20_nginx-rate-limit-zones-credential-vs-read-only-auth-endpoints.md",
  "similarity": -0.253
}
```

The `text` field for the first drawer starts with `---` (the YAML frontmatter delimiter) and includes all frontmatter fields (`domain`, `topic`, `tags`, `importance`, `staleness_risk`, etc.) before the markdown body.

## Implication for client-side processing

A Phase 2 wrapper that needs to filter by `domain`, `topic`, or `tags` does NOT need to:
- Read the source file from disk
- Maintain a separate metadata index
- Make additional MCP tool calls

It can parse frontmatter directly from the `text` field of search results. For a pool of 50 candidates, this eliminates 50 file reads.

## Implementation pattern

```python
def _parse_frontmatter(text: str) -> dict:
    if not text or not text.startswith("---"):
        return {}
    rest = text[3:]
    end_idx = rest.find("\n---")
    if end_idx == -1:
        return {}
    fm_text = rest[:end_idx].strip()
    # parse key: value lines from fm_text
    ...
```

**Caveat:** Only the FIRST drawer of each file contains frontmatter. Later drawers (content chunks) do not. A deduplication step that groups drawers by `source_file` and checks each for frontmatter is needed.

## When this applies

- Any MemPalace project using YAML frontmatter in Markdown files
- Client-side filtering of MemPalace search results (domain, topic, tags, importance)
- Building score-fusion wrappers that need metadata alongside semantic similarity

## When it does NOT apply

- Files without YAML frontmatter (no `---` at the start)
- MemPalace projects using the knowledge graph (`kg_add`) rather than `mine` — different text storage model
- Projects where frontmatter structure is non-standard or absent

## Source Context

Discovered during knowledgeforge-core Phase 2 Module 22 implementation (2026-07-07) when evaluating MemPalace search result shape for candidate filtering in the semantic wiki search subsystem. The pattern enables zero-copy metadata extraction from search result payloads.
