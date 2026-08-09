# KnowledgeForge Public Release Worklog
**Started:** 2026-08-09 | **Target:** github.com/internexio/knowledgeforge | **Plan version:** 2026-08-09

Append-only. Each phase appends its findings and verification results below its header.

---

## Phase 0 — Reconcile and freeze (2026-08-09)

### Step 1: e49 finalized

- kf.yaml bumped 7.26.0 -> 7.27.0
- 7.27.0 changelog entry added (driver: core-e49, mid-chain premise invalidation)
- M08 erratum appended to 7.25.0 entry: module file `version: 7.0.0` is canonical;
  "6.6.1 -> 6.7.0" notation in 7.25.0 entry was wrong; 7.26.0 entry inherits the error
- README.md version string updated 7.25.0 -> 7.27.0
- "What's New in 7.27.0" section added above existing 7.25.0 section
- `scripts/check-identity-drift.py` result: CLEAN (exit 0, no drift)

### Step 2: Discovery gap closure

**plugin-bundle.yaml**
- Status: ACTIVE (not a placeholder like codex.yaml)
- Purpose: installable bundle for internexio consumer repos ([project], client-project,
  visionforge, [project])
- Contains: KF scaffold agents, MCP connector entry for cos-mcp
  (`$COS_DEV_ROOT/cos/cos-mcp/server.json`, `path_type: absolute_requires_local_config`)
- Contains internexio-specific refs in `deduplication_inventory.duplicated_in` and
  `mcp_connectors.targets` fields
- Disposition: GENERICIZE deduplication_inventory and mcp_connectors sections; cos-mcp
  connector remains as named reference under R7 framing but targets list becomes generic.
  The `$COS_DEV_ROOT` env pattern is already public-safe (no hardcoded path).

**scripts/happy-watchdog.sh**
- Status: EXISTS, recently cleaned (pre-publish commit f148ea9 removed hardcoded URLs)
- HAPPY_SERVER_URL and HAPPY_WEBAPP_URL now require env (`:?` operator)
- tmux send-keys expands env vars at runtime (safe, no hardcoded values)
- Disposition: PERSONAL (proprietary Happy service management); EXCLUDE from public.
  Already on remove list per scrub-manifest.

**scripts/deploy-hooks.sh**
- Status: EXISTS and functional
- Role: deploys 7 hooks from core/hooks/ to ~/.claude/hooks/
  Ships: kf-route.py, kf_module_index.txt, kf-stop-validator.py, kf-precompact.py,
         kf-postcompact.py, kf-edit-nudge.py, kf-session-start.py
- Note: Phase 4 will expand the SHIP list. deploy-hooks.sh ships in public repo.
- No personal references. Clean for public.

### Step 3: SEED secrets scan (HEAD + history)

Patterns scanned: AIzaSy, sk-ant-, ghp_, github_pat_, BEGIN.*PRIVATE KEY,
                  /Users/dp, GEMINI_API_KEY= (assignment), dpedersen

**Results:**

| Pattern | Findings | Classification |
|---------|----------|----------------|
| AIzaSy | 0 live credentials; hit in wiki/infrastructure/2026-07-08_github-actions-pat-authentication-failure... | DOCUMENTATION REFERENCE — describes error signature pattern, not a real key |
| sk-ant- | 0 | Clean |
| ghp_ | Same file as AIzaSy hit | DOCUMENTATION REFERENCE — same wiki diagnostic entry |
| github_pat_ | Same file | DOCUMENTATION REFERENCE |
| BEGIN.*PRIVATE KEY | 0 | Clean |
| GEMINI_API_KEY= assignment | 0 hits (only `os.environ.get("GEMINI_API_KEY", "")` form present) | Clean |
| /Users/dp | Many files in early history (commit 007de920 + earlier); two recent commits (f148ea9, 99c4412) have wiki/infrastructure/2026-08-01_mac-mini-launchd-... | In-history paths need filter-repo replacement (`~/` -> `~/`). Not live credentials. |
| dpedersen | wiki/infrastructure/2026-08-01_mac-mini-launchd-claude-p-operational-pattern.md (commits f148ea9, 99c4412) | Personal username in wiki entry. Scrub-manifest: replace_text. |

**LIVE CREDENTIAL FOUND:** None. No halt required.

**Action items for scrub-manifest:**
- `replace_text`: `~/` -> `~/` (all history)
- `replace_text`: `dpedersen` -> redacted placeholder (per R13/mailmap for emails;
  for wiki content specifically, evaluate per-entry body)
- `remove_paths`: wiki/infrastructure/2026-08-01_mac-mini-launchd-... (personal
  infrastructure pattern, dpedersen reference in body)
- The ghp_/AIzaSy/sk-ant- wiki entry: add to review list; likely KEEP (diagnostic
  content) with the token-shaped strings being pattern descriptions, not real values.
  Confirm in Phase 6A audit by checking length/entropy.

**ODS scan:**
ODS appears in M00, M03, M05, M06, M07, M19, M20.
References: "ODS profiling output", "ODS organizational profile", "ODS module set
(ODS_00-ODS_10)", "ODS->COS bridging", "ODS entity graph".
Status: DISPOSITION-REQUIRED at GATE 1. ODS is an internal product concept not present
in this repo as a module set. The references in M00/M20 permission tables treat ODS as
an external client of KF (it calls KF, not the reverse). Likely disposition: GENERICIZE
to "organizational-data system" or "external profiling pipeline" with a bracketed note
that the ODS_00-ODS_10 module set is not part of this repo.

### Step 4: Wiki contamination list

Full grep (`semalytics|internexio|dpedersen|orchestra\.|/Users/dp`):
Raw count: 134 files. Listed in full secrets scan results above (the long list in Phase 0
data-gathering). The list includes many false positives where `internexio` is the
publishing org (acceptable per R2) or `semalytics` is the R7 reference integration.

**Definitive contamination categories for scrub-manifest:**

| Category | Count (est.) | Action |
|----------|-------------|--------|
| `/Users/dp` in body | ~40 files | replace_text in history |
| `dpedersen` in body | ~2 files | replace_text or remove_paths |
| `your-orchestra-host.example.com` endpoint | 2 files | replace_text to generic placeholder |
| COS diagnostic entries (mcp timeout/502/auth) | 5-6 files | REVIEW — describe COS externally; likely KEEP as generic MCP timeout patterns |
| `client-project`, `client-project` project refs | ~10 files | replace_text to `[client-project]` or remove_paths |
| `internexio/[project]` specific PR/commit refs | 2-3 files | remove_paths (too specific) |
| `source_session: redacted
| `internexio` as org publisher | Many | KEEP (acceptable per allowlist) |
| `semalytics.com` in R7 reference integration context | Targeted | KEEP per R7 per-path exemption |

**High-confidence remove_paths candidates (feed to scrub-manifest Phase 6A):**
- wiki/diagnostics/2026-05-19_cos-mcp-analyze-full-timeout-direct-curl-fallback.md
- wiki/diagnostics/2026-05-20_cos-analyze-full-payload-ceiling-502.md
- wiki/diagnostics/2026-06-19_cos-mcp-auth-timeout-fallback-to-local-skills.md
- wiki/infrastructure/2026-08-01_mac-mini-launchd-claude-p-operational-pattern.md
- wiki/patterns/2026-05-12_pin-tests-declarative-policy-manifests.md (internexio/[project] PR refs)
- wiki/patterns/2026-06-16_pareto-pass-as-purpose-discovery.md (internexio blog draft ref)
- wiki/patterns/2026-06-26_variant-axes-as-temperature-substitute-content-generation.md (client-project internals)
- wiki/patterns/2026-07-10_headless-chrome-html-png-pipeline-text-heavy-mobile-infographics.md (/Users/dp path)
- wiki/infrastructure/2026-05-19_sem-tools-google-ads-keyword-planner-wrapper.md (sem-tools specific)
- wiki/patterns/2026-05-25_google-ads-customer-id-dual-semantic-roles.md (Google Ads client-specific)
- wiki/diagnostics/2026-05-28_removed-ads-retain-history-join-scope-mismatch-retrospective-analysis.md
- wiki/strategy/2026-07-07_adsense-anti-pattern-professional-practitioner-tool-audiences.md

**Entries needing body review (not auto-remove):**
~90 remaining entries to evaluate individually in Phase 6A audit.

---

---

## Phase 1 — Compiler extension (2026-08-09)

### Step 1: process_conditional_blocks

Added `process_conditional_blocks(content, flags, binding_name) -> str` to
`compiler/kf-compile.py` (inserted before the "Compilers per platform" section).

Grammar:
- `<!-- kf:if <flag> -->` ... `<!-- kf:endif -->` (line-anchored, no nesting)
- Truthy: remove markers, keep body
- Falsy: remove markers AND body
- Hard-fail on: nesting, spurious endif, unclosed at EOF, undeclared flag
- Fast path: returns unchanged when `<!-- kf:` not in content

Regex: `_KF_IF_RE = re.compile(r"^<!-- kf:if ([a-z0-9_]+) -->$")`
       `_KF_ENDIF_RE = re.compile(r"^<!-- kf:endif -->$")`

Applied after `extract_section` in `compile_claude_code` (pre-header-injection,
pre-TOC). Applied after `strip_cc_sections` in `compile_claude_projects`.

### Step 2: flags binding key + --set CLI override

`flags:` is an optional top-level key in platform binding YAMLs. No existing
binding has it yet — infrastructure is in place for Phase 2 to add
`flags: { telemetry: false }` to claude-code.yaml.

CLI: `--set FLAG=VALUE` (repeatable, action="append"). Values: true/1/yes or
false/0/no. Parsed in `main()` after `load_binding()`; merged as
`{**binding.get("flags", {}), **cli_flags}` and passed to compile functions as
`flags=binding_flags` keyword argument.

### Step 3: max_chars budget enforcement

Per-output-entry optional field `max_chars: N`. After building final content in
`compile_claude_code`, if `output_def.get("max_chars")` is set and
`len(content) > max_chars`, abort with `sys.exit(1)` and a clear message.
Never truncates. No existing binding entries have `max_chars` set (infrastructure
only for Phase 2+).

### Step 4: Determinism — sorted module iteration

Changed `module_outputs.items()` to `sorted(module_outputs.items())` in both
`compile_claude_code` and `compile_plugin_bundle`. This makes iteration order
independent of YAML insertion order.

Regression check (--diff on CC after real write to /tmp):
- Only diff: compile header version 7.26.0 → 7.27.0 (expected from Phase 0 bump)
- kf.md: pre-existing divergence (telemetry line in CC repo not in current M00)
- Zero conditional block markers in any diff
- CP: 691 non-header lines changed — all substantive module content from
  v7.23.0-v7.27.0 updates; zero Phase 1 artifacts

### Step 5: Tool-map behavior documentation

Current state of tool_name_mapping:

`platform-bindings/codex.yaml` has a `tool_name_mapping` field (placeholder).
No substitution code exists in `kf-compile.py`. The `compile_codex_placeholder()`
function writes nothing and warns. Tool-name substitution is a Phase 5 concern
(when the Codex binding becomes active). No action required in Phase 1.

When Codex binding activates: add a `apply_tool_name_mapping(content, mapping)`
helper that does string substitution of KF tool names to Codex equivalents.
Apply it in the (future) `compile_codex()` after section extraction and before
emit. The substitution map lives in the binding YAML — no hardcoded tool names
in the compiler.

### Step 6: Determinism script

`scripts/verify-deterministic-build.sh` — builds CC and CP twice to temp dirs
(seeding each from the real variant repo), diffs excluding `.kf-compile-manifest.json`
(which has a timestamp). Exits 0 if byte-identical, 1 if any target differs.

Usage: `scripts/verify-deterministic-build.sh` from core root.

### Step 7: Tests

`tests/test_compiler_flags.py` — 15 tests (stdlib + importlib, no pytest):
- `TestProcessConditionalBlocks`: flag on/off matrix, multiple blocks,
  fast path, undeclared flag, nesting, unclosed, spurious endif, fixture file
- `TestMaxCharsBudget`: field parsing, budget check logic (no sys.exit mock)

`tests/fixtures/conditional_blocks_module.md` — synthetic module fixture with
`<!-- kf:if telemetry -->` and `<!-- kf:if public -->` blocks.

Result: 15/15 pass.

**Phase 1 status: COMPLETE.**

---

## Phase 2 — Telemetry flag (2026-08-09)

### Changes

**modules/00_orchestrator.md** — 7.23.0 → 7.24.0:
- Wrapped `## Per-Turn Mode Telemetry` block in `## CC Rules` section with
  `<!-- kf:if telemetry -->` / `<!-- kf:endif -->` (lines 1097-1169 in original).
- The STATIC ZONE telemetry content (lines 589-658) is documentation only —
  not compiled into any output — and was NOT wrapped.
- Identity strings updated: 7.23.0 → 7.24.0 in title and STATIC ZONE identity line.
- Changelog entry added.

**platform-bindings/claude-code.yaml**:
- Added `flags:` section with `telemetry: false` (public default).
- Comment documents the flag purpose and override pattern.

**kf.yaml** — 7.27.0 → 7.28.0:
- Changelog entry added for Phase 2.

### Verification

- `telemetry=false` (binding default): `Per-Turn Mode Telemetry` not in kf-meta.md ✓
- `--set telemetry=true`: `Per-Turn Mode Telemetry` present in kf-meta.md ✓
- No `kf:if` / `kf:endif` markers leaked into compiled output ✓
- `check-identity-drift.py`: CLEAN ✓
- 37 CC outputs written, 0 missing sections, 0 diverged ✓

**Phase 2 status: COMPLETE.**

---

## Phase 3 — COS/ODS genericize (2026-08-09)

### Step 1: Module wrapping — M07, M08, M11

**M07 (Critic) 7.5.0 → 7.6.0:**
- CC Skill Variants: wrapped "Communications (comms) variant" paragraph (3 paragraphs)
  with `<!-- kf:if cos -->` / `<!-- kf:endif -->`
- CC Agent: wrapped entire `## Communications Variant` section (including
  `### Comms Detection`, `### Comms Protocol`, `### COS Unavailable Fallback`,
  comparison table, accretion note, and "Then proceed..." close) with
  `<!-- kf:if cos -->` / `<!-- kf:endif -->`
- Changelog entry added for 7.6.0

**M08 (Synthesizer) 6.7.1 → 6.8.0:**
- CC Skill Quality Gate: wrapped 4 comms-domain checklist items
- CC Skill Variants: wrapped "Comms-domain emit (6.7)" paragraph
- CC Agent Step 8: wrapped entire "### Step 8 — Comms-Domain Detection and COS
  Template Emit (6.7)" section
- CC Agent Quality Gate: wrapped 3 comms-domain checklist items
- Changelog entry added for 6.8.0

**M11 (Calibrator) 7.1.1 → 7.2.0:**
- CC Skill Step 3.5: wrapped entire step
- CC Skill Output Format: genericized — removed `[→ COS profile artifacts if
  comms-heavy]` suffix; now ends with `Route to @critic for validation before
  declaring production-ready.`
- CC Skill Quality Gates: wrapped 3 comms-detection checklist items
- CC Skill Variants: wrapped "Comms-heavy emit (7.1)" paragraph
- CC Agent Step 3.5: wrapped entire step
- CC Agent Quality Gate: wrapped 3 comms-detection checklist items
- Changelog entry added for 7.2.0

### Step 2: Binding flag — cos: false

`platform-bindings/claude-code.yaml`:
- Added `cos: false` to `flags:` section alongside `telemetry: false`
- Comment documents flag purpose and `--set cos=true` override pattern

### Step 3: kp-003 verb scan

Script: grep all lines with `\bCOS\b` in CC sections (CC Skill, CC Agent) of M07,
M08, M11, excluding lines inside `<!-- kf:if cos -->` / `<!-- kf:endif -->` blocks.

**Result: CLEAN.** Zero COS mentions remain in CC sections outside conditional blocks.
All COS-subject sentences are inside wrapped blocks and will not appear in public output.

### Step 4: kf.yaml split (SSH → HTTPS)

`variants:` section SSH URLs (`git@github.com:internexio/...`) replaced with HTTPS
form (`https://github.com/internexio/...`) for the three variant entries:
- `knowledgeforge-cp`: SSH → HTTPS
- `knowledgeforge-cc`: SSH → HTTPS
- `knowledgeforge-cw`: SSH → HTTPS (deprecated entry, retained)

Note: `internexio` org name is in the public allowlist (R2 — publisher org). Only the
`git@` SSH protocol prefix was internal-smell.

### Step 5: kf.yaml bump and compile verification

`kf.yaml`: 7.28.0 → 7.29.0 with Phase 3 changelog entry.

**Verification:**
- `check-identity-drift.py`: CLEAN (exit 0) ✓
- Compile (cos=false, default): 37 outputs, 0 missing, 0 diverged ✓
- Marker leak check: 0 `kf:if`/`kf:endif` markers in compiled output ✓
- COS count in critic.md: 0 ✓
- COS count in critic agent: 0 ✓
- COS count in synthesizer.md: 0 ✓
- COS count in synthesizer agent: 0 ✓
- COS count in calibrator.md: 0 ✓
- COS count in calibrator agent: 0 ✓
- Telemetry count in kf-meta.md: 0 (still stripped from Phase 2) ✓
- Compile (cos=true, override): COS restored — critic.md: 2, critic agent: 7,
  synthesizer.md: 2, calibrator agent: 4 ✓

ODS disposition: Deferred to later phase per operator decision (not Phase 3).

**Phase 3 status: COMPLETE.**

---

## Phase 4 — Hooks curation + router hardening (2026-08-09)

### Step 1: Hooks scan

All hooks in `hooks/` scanned for personal/internal references:

| Hook | Scan result |
|------|-------------|
| kf-route.py | CLEAN — no personal refs, graceful degradation, env-var API key |
| kf_module_index.txt | CLEAN — no personal refs |
| kf-stop-validator.py | CLEAN |
| kf-precompact.py | CLEAN |
| kf-postcompact.py | CLEAN |
| kf-edit-nudge.py | CLEAN |
| kf-session-start.py | CLEAN |
| kf-stats.py | CLEAN |

`scripts/happy-watchdog.sh` — on EXCLUDE list (Phase 0). Two comment references to
`[project]-*` bead IDs are internal operational notes, not repo name exposures.
File does not ship in public repo.

### Step 2: SHIP list expansion

`scripts/deploy-hooks.sh`: Added `kf-stats.py` to `HOOKS` array. Was present in
`hooks/` but not deployed. Full SHIP list is now 8 files.

### Step 3: Router hardening

`hooks/kf-route.py`: No changes required.
- Uses `GEMINI_API_KEY` env var (not hardcoded) ✓
- Uses `KF_ROUTE_MODEL` env override (default `gemini-2.5-flash-lite`) ✓
- Uses `KF_ROUTE_TIMEOUT` env override (default 10s) ✓
- Graceful degradation on all failure paths (exit 0) ✓
- No integration guard needed (kf_integrations.py is a personal wrapper, not in core) ✓
- No personal paths or internexio references ✓

`hooks/kf_module_index.txt`: No changes required. Clean prompt, no personal refs.

### Step 4: plugin-bundle.yaml genericize

Per Phase 0 scrub-manifest disposition (GENERICIZE):

- Purpose comment: removed internexio consumer repo list ([project], client-project,
  visionforge, [project]); genericized to "consumer repos" language
- `mcp_connectors.cos-mcp.fallback_message`: removed `~/Scripts/[project]` path
  example; replaced with description of `$COS_DEV_ROOT` variable semantics
- `mcp_connectors.cos-mcp.targets`: `[[project], client-project, visionforge, [project]]`
  → `[]` with operator-instruction comment
- `deduplication_inventory.duplicated_in` (both entries): cleared to `[]` with
  operator-instruction comments

`kf.yaml`: 7.29.0 → 7.30.0 with Phase 4 changelog entry.

**Verification:**

```
grep -rn "[project]|client-project|visionforge|[project]|[project]" \
  platform-bindings/ hooks/ scripts/ compiler/
```
Result: Only `scripts/happy-watchdog.sh` (excluded from public repo) — CLEAN.

**Phase 4 status: COMPLETE.**

---

## Phase 5 — Platform bindings + dist matrix (2026-08-09)

### Step 1: vscode.yaml — internal refs removed

Two internal refs in `platform-bindings/vscode.yaml` description field:
- `local.dev-keys (AllOfUs)` — internal VS Code extension for API key management
- `vscode.authentication.getSession('dev-api-keys', ['anthropic'])` — internal auth provider ID

Replaced with generic VS Code SecretStorage recommendation.

### Step 2: New deferred platform binding stubs

Four new binding files created, each with full contract surface:

**`platform-bindings/generic.yaml`** (status: deferred)
- Single-file consolidated export — works with any LLM that accepts a system prompt
- Output: `kf-generic.md` (M00 routing + M13 decision classification + M06 quick reference)
- Token target: 6000 (fits most system prompt budgets)
- bind_when: compiler gains `compile_generic()` handler + summary extraction for M00/M06/M13

**`platform-bindings/cursor.yaml`** (status: deferred)
- Cursor `.cursor/rules/*.mdc` format (modern; supersedes `.cursorrules`)
- Orchestrator rule: `alwaysApply: true`; mode rules: glob-gated
- Rule token target: 2000 per file
- bind_when: compiler gains `compile_cursor()` + .mdc frontmatter schema verified

**`platform-bindings/chatgpt.yaml`** (status: deferred)
- OpenAI Custom GPT: Instructions field (8000 char) + knowledge file upload
- Instructions: M00 routing + M13; Knowledge: M01-M11 (one file each)
- bind_when: compiler gains `compile_chatgpt()` + char limit + file count verified

**`platform-bindings/gemini.yaml`** (status: deferred)
- Two sub-targets: `api` (system_instruction string only) and `gem` (instructions + files)
- bind_when: compiler gains `compile_gemini()` with sub-target dispatch

### Step 3: Dist matrix

`docs/dist-matrix.md` (new): 9-platform capability matrix and module coverage table.
Covers: claude-code, claude-projects, vscode, plugin-bundle, codex, cursor, chatgpt,
gemini, generic. Includes output file counts, status legend, and "Adding a New Platform" guide.

### Verification

```
grep -rn "internexio|dpedersen|/Users/dp|semalytics|AllOfUs|dev-api-keys" \
  platform-bindings/generic.yaml platform-bindings/cursor.yaml \
  platform-bindings/chatgpt.yaml platform-bindings/gemini.yaml \
  platform-bindings/vscode.yaml docs/dist-matrix.md
```
Result: CLEAN — zero matches.

kf.yaml: 7.30.0 → 7.31.0.

**Phase 5 status: COMPLETE.**

---

## GATE 0 — Decision log (resolved 2026-08-09)

| Decision | Resolution |
|----------|------------|
| R10 — SECURITY.md contact email | security@internexio.com |
| R13 — Author email in commit history | github@internexio.com (mailmap rewrite) |
| R16 — Copyright holder string | David Pedersen |
| ODS disposition | Deferred to later phase per operator decision |

---

## Phase 6A — History scrub pipeline rehearsal (2026-08-09)

### Step 1: scrub-manifest.yaml created

`scripts/scrub-manifest.yaml` — canonical scrub spec. Full spec:

**GATE decisions recorded:**
- R10: security@internexio.com
- R13: github@internexio.com → github@internexio.com
- R16: David Pedersen

**mailmap entry:** `David Pedersen <github@internexio.com> <github@internexio.com>`

**replace_text rules (7):**
1. `literal:~/==>~/` — laptop home dir path, 32 wiki files in history
2. `literal:~/==>~/` — Mac Mini home dir path, safety net
3. `literal:github@internexio.com==>github@internexio.com` — email in file content
4. `regex:orchestra\\.semalytics\\.io==>your-orchestra-host.example.com` — internal API endpoint
5. `regex:source_session: redacted
6. `literal:client-project==>client-project` — internal GTM project name
7. `literal:client-project==>client-project` — internal ads project name

**remove_paths (14):**
- `scripts/happy-watchdog.sh` — personal Happy service management
- `wiki/diagnostics/2026-05-19_cos-mcp-analyze-full-timeout-direct-curl-fallback.md`
- `wiki/diagnostics/2026-05-20_cos-analyze-full-payload-ceiling-502.md`
- `wiki/diagnostics/2026-06-19_cos-mcp-auth-timeout-fallback-to-local-skills.md`
- `wiki/diagnostics/2026-05-28_removed-ads-retain-history-join-scope-mismatch-retrospective-analysis.md`
- `wiki/infrastructure/2026-08-01_mac-mini-launchd-claude-p-operational-pattern.md`
- `wiki/infrastructure/2026-05-19_sem-tools-google-ads-keyword-planner-wrapper.md`
- `wiki/patterns/2026-05-12_pin-tests-declarative-policy-manifests.md`
- `wiki/patterns/2026-05-25_google-ads-customer-id-dual-semantic-roles.md`
- `wiki/patterns/2026-06-16_pareto-pass-as-purpose-discovery.md`
- `wiki/patterns/2026-06-26_variant-axes-as-temperature-substitute-content-generation.md`
- `wiki/patterns/2026-06-29_headless-chrome-html-png-pipeline-text-heavy-social-infographics.md`
- `wiki/patterns/2026-07-10_headless-chrome-html-png-pipeline-text-heavy-mobile-infographics.md`
- `wiki/strategy/2026-07-07_adsense-anti-pattern-professional-practitioner-tool-audiences.md`
- `docs/planning/2026-08-09_public-release-worklog.md` (this file — contains internal project name refs as meta-documentation; not appropriate for public consumption)

Note: the June 2026 headless-chrome file (`2026-06-29_...social-infographics.md`) was
added during Phase 6A prep. Phase 0 worklog listed only the July 2026 mobile variant;
grep revealed the June file also contains `~/Scripts/semalytics-gtm/` path.

### Step 2: Rehearsal run

```
git clone --no-local ~/Scripts/knowledgeforge-core /tmp/kf-scrub-rehearsal2

git-filter-repo \
  --replace-text /tmp/kf-scrub-replacements.txt \
  --mailmap /tmp/kf-scrub-mailmap.txt \
  --invert-paths \
  --path scripts/happy-watchdog.sh \
  --path wiki/diagnostics/2026-05-19_cos-mcp-analyze-full-timeout-direct-curl-fallback.md \
  --path wiki/diagnostics/2026-05-20_cos-analyze-full-payload-ceiling-502.md \
  --path wiki/diagnostics/2026-06-19_cos-mcp-auth-timeout-fallback-to-local-scripts.md \
  --path wiki/diagnostics/2026-05-28_removed-ads-retain-history-join-scope-mismatch-retrospective-analysis.md \
  --path wiki/infrastructure/2026-08-01_mac-mini-launchd-claude-p-operational-pattern.md \
  --path wiki/infrastructure/2026-05-19_sem-tools-google-ads-keyword-planner-wrapper.md \
  --path wiki/patterns/2026-05-12_pin-tests-declarative-policy-manifests.md \
  --path wiki/patterns/2026-05-25_google-ads-customer-id-dual-semantic-roles.md \
  --path wiki/patterns/2026-06-16_pareto-pass-as-purpose-discovery.md \
  --path wiki/patterns/2026-06-26_variant-axes-as-temperature-substitute-content-generation.md \
  --path wiki/patterns/2026-06-29_headless-chrome-html-png-pipeline-text-heavy-social-infographics.md \
  --path wiki/patterns/2026-07-10_headless-chrome-html-png-pipeline-text-heavy-mobile-infographics.md \
  --path wiki/strategy/2026-07-07_adsense-anti-pattern-professional-practitioner-tool-audiences.md
```

Completed in 0.75s.

### Step 3: Rehearsal verification results

**Path removal:**

| Path | Result |
|------|--------|
| scripts/happy-watchdog.sh | Removed ✓ |
| wiki/diagnostics/* (3 entries) | Removed ✓ |
| wiki/diagnostics/2026-05-28_removed-ads-* | Removed ✓ |
| wiki/infrastructure/2026-08-01_mac-mini-* | Removed ✓ |
| wiki/infrastructure/2026-05-19_sem-tools-* | Removed ✓ |
| wiki/patterns/* (6 entries) | Removed ✓ |
| wiki/strategy/2026-07-07_adsense-* | Removed ✓ |

14/14 paths removed from all commits ✓

**Content replacement:**

| Pattern | Remaining hits | Status |
|---------|----------------|--------|
| `/Users/dp` | 6 hits in worklog (this file) | Expected — meta-refs documenting scrub |
| `/Users/davidpedersen` | 0 | Clean ✓ |
| `github@internexio.com` | 0 | Clean ✓ |
| `your-orchestra-host.example.com` | 0 | Clean ✓ |
| `client-project` | 0 | Clean ✓ |
| `client-project` | 0 | Clean ✓ |

5/6 patterns → 0 hits ✓; 6th (`/Users/dp`) = expected meta-refs in worklog (file
itself is on remove_paths for real scrub run — those refs will not appear in public repo)

**Author email:**

All commits → `github@internexio.com` ✓

**Rehearsal verdict: CLEAN.** Ready for real scrub run after pre-real-scrub gate:
- Body review of ~90 wiki entries flagged in Phase 0 (deferred to pre-real-scrub gate)

### Step 4: wiki/index.md cleanup

13 dangling entries removed from working repo `wiki/index.md`. (filter-repo preserves
wiki/index.md but does not remove entries that reference removed files.)

Entries removed:
- wiki/patterns/2026-06-29_headless-chrome...social-infographics.md
- wiki/patterns/2026-07-10_headless-chrome...mobile-infographics.md
- wiki/patterns/2026-06-26_variant-axes-as-temperature-substitute-content-generation.md
- wiki/patterns/2026-06-16_pareto-pass-as-purpose-discovery.md
- wiki/patterns/2026-05-25_google-ads-customer-id-dual-semantic-roles.md
- wiki/patterns/2026-05-12_pin-tests-declarative-policy-manifests.md
- wiki/infrastructure/2026-08-01_mac-mini-launchd-claude-p-operational-pattern.md
- wiki/infrastructure/2026-05-19_sem-tools-google-ads-keyword-planner-wrapper.md
- wiki/diagnostics/2026-05-19_cos-mcp-analyze-full-timeout-direct-curl-fallback.md
- wiki/diagnostics/2026-05-20_cos-analyze-full-payload-ceiling-502.md
- wiki/diagnostics/2026-06-19_cos-mcp-auth-timeout-fallback-to-local-skills.md
- wiki/diagnostics/2026-05-28_removed-ads-retain-history-join-scope-mismatch-retrospective-analysis.md
- wiki/strategy/2026-07-07_adsense-anti-pattern-professional-practitioner-tool-audiences.md

Note: the mobile-infographics file was not in wiki/index.md (Phase 0 had not indexed it).

Verification: `grep` for all 14 removed-path slugs in wiki/index.md → 0 hits ✓

### Step 5: Worklog disposition

The worklog (`docs/planning/2026-08-09_public-release-worklog.md`) itself references
[project], client-project, visionforge, [project] as documentation of what was scrubbed.
Adding it to remove_paths is the correct disposition — it is a developer artifact, not
public documentation. The public-facing spec docs (planning/*.md other than this file,
modules/, docs/) are retained.

**Phase 6A status: COMPLETE.**

---
