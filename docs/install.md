# KnowledgeForge — Installation Guide

Two install paths for Claude Code: **plugin** (recommended, no git required) and
**manual clone** (for pinned local installs or when the plugin registry isn't
available). Both produce the same result: KF artifacts in `~/.claude/` ready to use.

For other platforms see [Claude Projects](#claude-project-setup),
[ChatGPT](#chatgpt-projects), [Codex CLI](#codex-cli),
[VSCode](#vscode-experimental), and [Plugin Bundle](#plugin-bundle-experimental).

---

## Claude Code — Plugin Install (Recommended)

```bash
/plugin install kf
/kf:bootstrap
```

`/kf:bootstrap` is a required one-time post-install step. It copies KF's always-on
rules (`kf-meta.md`) and mode docs into `~/.claude/` — Claude Code's plugin spec
doesn't auto-load rules or arbitrary docs subdirs, so this step bridges that gap.

**After updates:**

```bash
/plugin update kf
/kf:bootstrap   # re-run to sync rules and docs with the new version
```

---

## Claude Code — Manual Clone

Use this if you want a pinned local install, prefer to inspect before installing,
or the plugin path isn't available.

```bash
git clone https://github.com/internexio/knowledgeforge
cd knowledgeforge
bash install.sh
```

`install.sh` copies the pre-compiled variant from `platforms/claude-code/.claude/` into `~/.claude/`:

| Directory | What's copied |
|-----------|--------------|
| `~/.claude/agents/` | Mode agent definitions (builder, critic, debugger, etc.) |
| `~/.claude/commands/` | Slash commands (`/kf-reflect`, `/kf-status`) |
| `~/.claude/rules/` | Always-on rules (`kf-meta.md`) |
| `~/.claude/skills/kf/` | Mode execution protocols |
| `~/.claude/hooks/` | Pre-prompt classifier + lifecycle hooks |
| `~/.claude/docs/knowledgeforge/` | Cross-cutting cognitive infrastructure docs |
| `~/.claude/kf-integrations.yaml` | Integration config (deployed once, not overwritten on updates) |

**After updates:** `git pull && bash install.sh` — safe to re-run; `kf-integrations.yaml`
is preserved.

No compiler required. The pre-compiled output for Claude Code lives at
`platforms/claude-code/` in this repo and is updated with every release.

---

## Configure settings.json

After either Claude Code install path, add these entries to `~/.claude/settings.json`:

```json
{
  "agent": "kf",
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/kf-route.py",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

**`"agent": "kf"`** — sets the KF orchestrator as the default agent for all Claude
Code sessions in this install. Without this, you need to invoke KF explicitly per session.

**`kf-route.py` hook** — classifies each prompt before Claude reads it, injects a
`[KF-ROUTE]` directive that loads the right reasoning mode immediately. Requires
`GEMINI_API_KEY` in your environment (see [Add-ons](add-ons.md)).

Without the hook, KF still works — Claude routes natively via its built-in routing
table. Correct results, but mode selection is slower on ambiguous prompts.

---

## Claude Project Setup

KF also works inside a Claude Project (claude.ai). Setup is manual — no install script,
no hooks. The pre-compiled output lives at `platforms/claude-projects/` in this repo.

> **Before re-uploading:** Delete **all** existing project knowledge files first. Claude
> Projects does not replace files — it appends. Duplicate filenames create a live
> contradiction source where retrieval can't distinguish canonical from stale.
> Clean-slate each upload cycle.

1. Create (or open) a Claude Project at [claude.ai](https://claude.ai)
2. Go to **Project Instructions** → paste the full contents of
   `platforms/claude-projects/00_Project_Instructions-Claude.md`
3. Under **Project Knowledge**, upload all 26 knowledge files:

**Core Agents (11 files)**

| File | Purpose |
|------|---------|
| `01_Navigator_Agent.md` | Ambiguity detection and routing |
| `02_Builder_Agent.md` | Specification generation (PDIA method) |
| `03_Coordination_Patterns.md` | Multi-agent workflow design + Handoff Contract Registry (13 contracts) |
| `04_Specification_Templates.md` | Reusable spec formats + trigger disambiguators |
| `05_Expert_Agent_Example.md` | Deep analysis, adversarial depth (5 variants: regular / infra / ml-infra / era / research) |
| `06_Quick_Reference.md` | Routing table and signal guide |
| `07_Critic_Agent.md` | Review, validation, adversarial variant (4 variants: regular / linter / audit / adversarial) |
| `08_Synthesizer_Agent.md` | Pattern extraction and abstraction |
| `09_Debugger_Agent.md` | Hypothesis-driven root-cause diagnosis |
| `10_Strategist_Agent.md` | Trade-off evaluation, sequencing |
| `11_Calibrator_Agent.md` | Complexity-appropriate AI coder configuration |

**Cognitive Infrastructure (15 files)**

| File | Purpose |
|------|---------|
| `12_Calibration_Layer.md` | Multi-pass evaluation, judge isolation |
| `13_Decision_Classification.md` | Reckoning / evaluative / predictive / novel routing |
| `14_Metacognitive_Monitor.md` | Acute failure detection (loops, overflow, confidence collapse) |
| `15_Grounding_Scores.md` | Evidence quality scoring (0.0–1.0) |
| `16_Operational_Bounds.md` | Metrics, circuit breakers, mode-selection accuracy (9 variants) |
| `17_Temporal_Knowledge.md` | Knowledge age, decay, planning artifact staleness |
| `18_Salience_Allocation.md` | Multi-task attention weighting |
| `19_Memory_Architecture.md` | Four-tier memory, routing index, routing decision log |
| `20_Permission_Model.md` | Risk tiers (LOW/MEDIUM/HIGH) and capability gates |
| `21_Knowledge_Accretion.md` | Cross-session knowledge persistence, compile-query-enhance loop |
| `22_Semantic_Wiki_Search.md` | Metadata-gated semantic search over Tier 0 wiki |
| `23_Taxonomy_Enforcement.md` | Fixed controlled vocabulary (15 domains, ~40 topics, ~55 tags) |
| `24_Verbatim_History_Mining.md` | Verbatim Tier 3 storage + MemPalace semantic retrieval |
| `25_Entity_Relationship_Analysis.md` | ERA post-routing pass: entity graph, cardinality, coupling |
| `26_KF_Loop_Substrate.md` | Iterative self-improvement loops: eight-stage orchestration primitive, five loop instances |

4. Start a conversation — KF classifies and routes every request automatically.

> **M26 (KF-LOOP Substrate) is required.** The orchestrator uses the loop substrate for
> iterative self-improvement patterns. Omitting it leaves the loop orchestration
> primitive unspecified.

> **Expert research variant** requires the Asta/Alia Semantic Scholar MCP connected to
> your Claude Project. Without it, the research variant permanently operates in degraded
> mode (WebSearch fallback, grounding capped at 0.6, ship disposition unavailable). All
> other modes work normally.

> **Claude Projects don't support hooks or the local file system.** The `kf-route.py`
> pre-prompt classifier and add-ons that require local binaries (Beads, GitNexus) don't
> apply. MemPalace and the API-based integrations (Gemini, Asta, COS) work fine if
> registered as Project tools.

---

## Optional Add-ons

KF works without any add-ons. Seven optional integrations extend specific capabilities —
all degrade gracefully when unavailable. Managed via `~/.claude/kf-integrations.yaml`
(Claude Code) or Project tool registration (Claude Projects).

| Integration | What it adds | CC | CP |
|-------------|-------------|----|----|
| **MemPalace** | Semantic wiki search — upgrade from grep to vector recall | Yes | Yes (register as Project tool) |
| **Gemini Routing** | Pre-prompt classifier — instant, accurate mode selection | Yes | No (no hooks) |
| **Beads** | AI-native task tracking (`bd`/`br`) wired into KF session hooks | Yes | No (local binary) |
| **GitNexus** | Symbol table + call graph for blast-radius analysis before edits | Yes | No (local binary) |
| **Asta** | Peer-reviewed paper retrieval in Expert research mode | Yes | Yes (register as Project tool) |
| **COS** | Structured comms analysis in Critic, Synthesizer, and Calibrator | Yes | Yes (register as Project tool) |
| **Orchestra** | Multi-agent cross-machine coordination *(opt-in — access required)* | Yes | No |

**Gemini Routing setup:**

```bash
export GEMINI_API_KEY=your_key_here
# Add to ~/.zshrc or ~/.bashrc to persist
```

**MemPalace setup:**

```bash
pip install mempalace
claude plugin install --scope user mempalace
```

Full per-integration documentation — install steps, API keys, MCP registration, and
config options — is in [`docs/add-ons.md`](add-ons.md).

---

## ChatGPT Projects

> **Experimental:** This variant has not received the same validation coverage as the
> Claude variants.

Pre-compiled files are in [`platforms/chatgpt/`](../platforms/chatgpt/) — no build
step needed.

1. Open your ChatGPT Project → **Settings > Instructions** → paste the contents of
   `platforms/chatgpt/kf-chatgpt-instructions.md`
2. **Knowledge** → upload all files from `platforms/chatgpt/knowledge/`

> Before re-uploading: delete existing KF knowledge files first. ChatGPT does not
> deduplicate by filename.
>
> If you hit a file limit (Custom GPTs cap at 20): prioritize `knowledge/01`–`knowledge/11`
> (the mode specs) over the infrastructure modules `12`–`26`.

See [`platforms/chatgpt/`](../platforms/chatgpt/) for the full install guide.

---

## Codex CLI

> **Experimental:** Codex support is under active testing.

Pre-compiled output is in [`platforms/codex/`](../platforms/codex/) — no build step needed.

Install into one project:

```bash
bash install.sh --codex --project /path/to/your/project
```

Or install globally for all local Codex projects:

```bash
bash install.sh --codex --global
```

The global install writes `~/.codex/AGENTS.md`; the project install writes `AGENTS.md`
in the selected project. If either target already contains different instructions, the
installer refuses to replace it unless you add `--force` (creates a timestamped backup
first). Use `--dry-run` to preview either command.

See [`platforms/codex/`](../platforms/codex/) for the full install guide.

---

## VSCode (Experimental)

```bash
python3 compiler/kf-compile.py --target vscode --output ./dist/vscode
```

See [`platforms/vscode/load-map.md`](../platforms/vscode/load-map.md) for what gets
generated and where it deploys inside a VSCode extension.

---

## Plugin Bundle (Experimental)

For tool-agnostic deployment (any platform that can load agent files via a plugin):

```bash
python3 compiler/kf-compile.py --target plugin-bundle --output ./dist/plugin-bundle
bash ./dist/plugin-bundle/install.sh
```

See [`platforms/plugin-bundle/load-map.md`](../platforms/plugin-bundle/load-map.md) for
the full file manifest.

---

## Updating

**Claude Code (plugin):**

```bash
/plugin update kf
/kf:bootstrap   # always re-run after update
```

**Claude Code (manual clone):**

```bash
cd knowledgeforge
git pull
bash install.sh
```

**Claude Projects:** Re-run the full setup procedure — delete all existing knowledge
files, re-paste Project Instructions, re-upload all 26 knowledge files. There is no
incremental update path for Claude Projects.
