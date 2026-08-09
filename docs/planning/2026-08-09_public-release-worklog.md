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

## Pending decisions for GATE 0

| Decision | Status | Notes |
|----------|--------|-------|
| R10 — SECURITY.md contact email | NEEDS USER INPUT | Provide disclosure email before Phase 7 |
| R13 — Author email in commit history | NEEDS USER INPUT | Mailmap to noreply? Or is github@internexio.com public-safe? |
| R16 — Copyright holder string | NEEDS USER INPUT | internexio Inc. / David Pedersen / other |
| ODS disposition | DECISION REQUIRED AT GATE 1 | Keep/genericize; see Step 3 above |
