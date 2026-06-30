---
title: Allen AI Asta Scientific Corpus MCP — operational gotchas reference
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-06-26
domain: integration
topic: external-tools
tags: mcp, api, sidecar, empirical, volatile
source_fingerprint: cos-grounding-build-2026-06-26 — every gotcha hit and resolved in-session with concrete error logs and resolution traces; audit trail in cos-grounding/findings/PHASE2_CHECKPOINT.md + FDD/FII/FJJ checkpoints
related_entries:
  - patterns/2026-06-10_mcp-tool-response-shape-live-verification-before-parsing.md
  - patterns/2026-06-19_cross-project-credential-resolution-sibling-env-single-source.md
  - integration/2026-06-22_mcp-streamable-http-sessions-wiped-on-container-restart.md
---

# Allen AI Asta Scientific Corpus MCP — operational gotchas reference

Operational gotchas observed during the cos-grounding build (2026-06-26) using the Allen AI Asta Scientific Corpus MCP at `https://asta-tools.allen.ai/mcp/v1`. Each gotcha includes the failure pattern, root cause, and the workaround that resolved it. Pin behavior to **as of 2026-06-26**; Asta API behavior may change.

## 1. In-session MCP returns 403 even with valid key

**Pattern:** Claude Code's in-session `mcp__asta__*` tools return HTTP 403 Forbidden for all calls, while the same `x-api-key: $KEY` via curl returns HTTP 200.

**Root cause:** `${ASTA_TOOL_KEY}` interpolation in `.mcp.json` `headers` block is not reliably expanded by Claude Code's HTTP MCP client as of 2026-06 (open issues #14977 / #28293).

**Workaround:** rewrite `.mcp.json` with the literal key in the `x-api-key` header field; add `.mcp.json` to `.gitignore`; keep a `.mcp.json.example` template with a placeholder for repo discoverability. Operator session restart picks up the new config.

## 2. `get_paper_batch` with `fields=references` fails on chunks > 10

**Pattern:** Batched `get_paper_batch` with `fields` including `references` returns `'NoneType' object is not iterable` when chunk size exceeds ~10-20 papers. Smaller chunks succeed.

**Root cause:** likely a serialization issue when one paper in the batch has malformed/null entries in its references list — the error kills the entire batch, not just the offending paper. Large batches statistically include at least one problem paper.

**Workaround:** chunk to ≤10 papers per call. For metadata fields without `references`, batches of 100+ work fine. Use `--max-time 90` per call because large reference lists (50-200 refs per meta-analysis) take 30-60s to serialize.

## 3. Title-search is fuzzy-threshold-sensitive and inconsistent

**Pattern:** `search_paper_by_title` returns `"Title match not found"` for queries that should obviously match, then resolves on a shortened version of the same title.

**Root cause:** Asta's title-matching uses an undocumented fuzzy-similarity threshold that varies by query length. Long verbose titles can fail where short distinctive titles + `venues` + `publication_date_range` filters succeed.

**Workaround:** implement a fallback ladder in the curator pipeline — full-title → loose-title → short-title + filters → DOI lookup → manual flag. Prefer DOI lookup whenever a DOI is known: `get_paper(paper_id="DOI:10.x/y")` is dramatically more reliable than any title-search variant.

## 4. SSRN / ResearchGate / Wharton block bot user-agents

**Pattern:** WebFetch and curl-with-browser-User-Agent both return 403 (SSRN, ResearchGate) or 404 (Wharton faculty PDFs) for paywalled academic papers' abstract / preprint pages.

**Root cause:** robust bot detection that goes beyond UA spoofing. JavaScript rendering may also be required for some sites.

**Workaround:** when source-body verification is needed for a paywalled paper, the path is **operator manual browser-download** to `~/Downloads/`, then archive to `references/papers/<s2_id>.pdf` (gitignored) and extract via `pdftotext -layout`. No agent-side automation path exists for these sources as of 2026-06.

## 5. `tldr` field rejected by `get_citations` despite docstring listing it

**Pattern:** `get_citations` returns `"Unrecognized or unsupported fields: [tldr]"` when `fields` includes `tldr`, even though the tool's docstring lists `tldr` as an available field.

**Root cause:** docstring is stale or `tldr` is only available on `get_paper` / `search_paper_by_title` endpoints, not on `get_citations`.

**Workaround:** drop `tldr` from `get_citations` calls; use `abstract` instead if needed for triage. Confirm available fields per-endpoint empirically rather than trusting the docstring.

## 6. SSE response parsing — two paths

**Pattern:** Asta returns SSE-framed JSON responses where the paper data appears in EITHER `result.structuredContent.result` (search_paper_by_title path) OR `result.content[0].text` as a JSON-encoded string (get_paper path). Parsers that assume one path silently fail on the other.

**Workaround:** parser must try `structuredContent.result` first, then fall back to JSON-parsing `content[0].text`. Asta also emits keep-alive `: ping` SSE lines during slow queries — strip these before parsing.

## 7. Rate limit: 10 req/sec per endpoint

Documented; in practice 4-way parallel via `xargs -P 4` with no per-call delay stays comfortably under the limit and is the recommended pattern for sequential recovery of failed batches.

## Bib-corpus → Asta integration pattern

When migrating a legacy BibTeX corpus into a references store:

1. Parse bib entries — many include `CorpusId:N` in URL fields (Semantic Scholar's canonical ID format).
2. For CorpusId-bearing entries: `get_paper_batch(["CorpusId:N1", "CorpusId:N2", ...])` with batches of 100-273 (no `references` field) resolves all in one call.
3. For non-CorpusId entries: URL-pattern extraction recovers most — `doi.org/<doi>` → `DOI:<doi>`, `aclanthology.org/<id>` → `ACL:<id>`, `pdfs.semanticscholar.org/<sha-prefix>/<sha-suffix>.pdf` → `<paperId-SHA>`.
4. Concrete result this session: 343 bib entries → 312 successfully ingested (273 CorpusId + 39 URL-recovered); 16 entries deferred (ACM citation-cfm URLs, ScienceDirect PIIs, obscure conference URLs).

## Grounding

Every gotcha listed was hit, diagnosed, and worked around in a single session (cos-grounding-build, 2026-06-26) with concrete error logs and resolution traces. Audit trail:

- `~/Scripts/cos-grounding/findings/PHASE2_CHECKPOINT.md`
- `~/Scripts/cos-grounding/findings/FDD_CHECKPOINT-2026-06-26.md`
- `~/Scripts/cos-grounding/findings/FII_CHECKPOINT-2026-06-26.md`
- `~/Scripts/cos-grounding/findings/FJJ_CHECKPOINT-2026-06-26.md`

Endpoint: `https://asta-tools.allen.ai/mcp/v1`. Behavior pinned to 2026-06-26 — Asta is under active development; revisit if any of these are still relevant when next used.

## Related

- `patterns/2026-06-10_mcp-tool-response-shape-live-verification-before-parsing.md` — verify MCP response shape live before writing parsing code (the SSE two-path gotcha is a textbook case).
- `patterns/2026-06-19_cross-project-credential-resolution-sibling-env-single-source.md` — credential resolution patterns relevant to gotcha #1.
- `integration/2026-06-22_mcp-streamable-http-sessions-wiped-on-container-restart.md` — adjacent MCP-HTTP operational gotcha entry.
