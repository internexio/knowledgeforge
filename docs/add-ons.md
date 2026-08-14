# KnowledgeForge — Optional Add-ons

KF works out of the box without any of these. Each integration unlocks specific
capabilities; all degrade gracefully when unavailable. `install.sh` deploys
`~/.claude/kf-integrations.yaml` on first run — edit it to enable or disable
any integration without restarting.

---

## MemPalace — Semantic Wiki Search

**What it does:** Powers KF's Tier 0 semantic wiki search (Module 22). Without it,
wiki search falls back to grep — lower recall, no semantic ranking.

**Install:**

```bash
pip install mempalace
claude plugin install --scope user mempalace
```

**Repo:** [github.com/milla-jovovich/mempalace](https://github.com/milla-jovovich/mempalace) (MIT)

**Config:** Enabled by default in `~/.claude/kf-integrations.yaml`. No API key required.

---

## Gemini Routing — Pre-Prompt Classifier

**What it does:** `kf-route.py` calls Gemini Flash Lite before each prompt to classify
the request and inject a `[KF-ROUTE]` directive. This is what makes mode selection
instant and accurate — the right protocol loads before Claude even starts reading your
message. Without it, KF routes natively via the built-in routing table (correct but
slower to reach the right mode on ambiguous prompts).

**Get an API key:** [aistudio.google.com](https://aistudio.google.com/apikey) (free tier available)

**Add to your shell environment:**

```bash
export GEMINI_API_KEY=your-key-here
```

**Config:** Enabled by default. Set `gemini_routing: enabled: false` in
`~/.claude/kf-integrations.yaml` to fall back to native routing.

---

## Beads — Task Tracking

**What it does:** `bd` (Beads) is an AI-native task tracker that lives in your repo.
KF uses it for session-start priority awareness, in-workflow `bd ready/close/update`
calls, and the `br prime` context-priming step before compaction. Without it, task
tracking is skipped; all other KF behavior is unaffected.

**Install:** Follow the instructions at
[github.com/steveyegge/beads](https://github.com/steveyegge/beads)

**Config:** Enabled by default. KF's hooks (`br-prime-safe.sh`) fail silently if `bd`
or `br` aren't on PATH — no broken behavior.

---

## GitNexus — Code Intelligence

**What it does:** GitNexus indexes your codebase's symbol table and call graph.
When available, KF's impact-analysis directives (`gitnexus_impact`,
`gitnexus_detect_changes`, `gitnexus_rename`) activate for safe refactoring and
blast-radius assessment before edits. Without it, all directives degrade to no-ops
and KF uses standard file/grep navigation.

**Install:**

```bash
npm install -g gitnexus
gitnexus analyze          # index the current project
```

Register the MCP in `~/.claude/settings.json`:

```json
"mcpServers": {
  "gitnexus": {
    "type": "stdio",
    "command": "gitnexus",
    "args": ["mcp"]
  }
}
```

**Repo:** [github.com/nordic-ai/gitnexus](https://github.com/nordic-ai/gitnexus)

**Config:** Enabled by default in `~/.claude/kf-integrations.yaml`.

---

## Asta — Expert Research Variant

**What it does:** The Asta MCP connects KF's Expert (research) mode to the
[Allen AI Semantic Scholar corpus](https://www.semanticscholar.org/) — paper retrieval,
citation grounding, claim verification. Without it, Expert research falls back to
WebSearch (grounding capped at 0.6, output flagged `degraded=true`, ship disposition
unavailable). All other Expert variants are unaffected.

**Access:** Request an API key from [Allen AI](https://allenai.org/). The MCP endpoint
is `https://asta-tools.allen.ai/mcp/v1`.

Register in `.mcp.json` (write the key literally — `${VAR}` interpolation in MCP
headers is unreliable in Claude Code):

```json
"mcpServers": {
  "asta": {
    "type": "streamable-http",
    "url": "https://asta-tools.allen.ai/mcp/v1",
    "headers": { "x-api-key": "your-asta-key-here" }
  }
}
```

**Config:** Enabled by default. Set `asta: enabled: false` to skip it entirely.

---

## COS — Communications Optimization System

**What you unlock:** When you're reviewing copy, messaging, or B2B content, KF's
Critic stops returning freeform critique and starts returning this:

> *Input:* "We help enterprise teams cut review cycles in half by automating the handoff
> between strategy and execution. Built for RevOps and marketing ops leaders who are tired
> of copy-paste workflows and misaligned messaging."

```
Framework 1 — Engagement (HAPE)
  emotional_impact:  6/10  — pain-agitation frame active; no proof point to spike impact
  novelty:           4/10  — "cut X in half" is a saturated pattern; differentiation gap
  relevance:         8/10  — tightly matched to RevOps/marketing-ops problem space

Framework 2 — Personality Fit (Big Five)
  best_fit_profile:  High N + Low C personas (ops leaders under review-cycle pressure)
  framing_match:     pain-first approach fits; loss aversion will outperform gain framing
  mismatch_risk:     High-C buyers will ask for specifics before engaging

Framework 3 — Strategic Clarity
  value_prop:        present but abstract — "half" needs a reference anchor (half of what?)
  differentiation:   weak — "automate handoffs" describes 20+ adjacent tools
  cta:               absent — directive but no next action specified

Framework 4 — Framing (Sovereign Mind)
  dominant_frame:    loss ("stop losing deals") — emotionally active, correctly placed last
  authority_gap:     solution authority not established; problem authority present

Framework 5 — Persuasion (business domain)
  social_proof:      absent — highest-priority gap for enterprise buyers
  authority_signals: absent
  urgency:           moderate (loss frame carries it)

Framework 6 — Platform (LinkedIn)
  register:          appropriate professional tone
  hook_strength:     weak — line 1 doesn't stop the scroll; specificity hook missing
  recommended_fix:   lead with a concrete outcome or customer signal before the pitch

Framework 7 — Quality
  clarity:           7/10
  concision:         8/10
  specificity:       4/10  — add one anchor metric to move this to 7+

Top 3 recommendations:
  1. Replace "half" with a specific metric or customer result
  2. Add a one-line social proof signal (customer segment + outcome)
  3. Move the loss-frame line to position 1 as the scroll-stopping hook
```

Seven frameworks. Scored. Ranked. Every Critic pass on comms content.

COS is an AI copywriting analysis engine for B2B, grounded in personality psychology
and 860+ peer-reviewed papers. The KF integration surfaces its analysis directly in
your workflow — no context switching.

**What it adds to KF:**

- **Critic (comms variant)** — `analyze_full_comms` via COS MCP: 4–7 framework
  structured analysis (engagement, personality fit, strategic clarity, framing,
  persuasion, platform, quality). Degrades gracefully to standard Critic output
  without COS MCP.
- **Synthesizer (comms domain)** — emits `cos_template_output` alongside pattern
  frameworks when comms-domain signals are detected
- **Calibrator (comms-heavy)** — emits `cos_agent_profile_output` +
  `cos_audience_profile_output` for comms-heavy project configurations

**Access:** [Try COS free for 7 days →](https://semalytics.com/cos) Subscription
includes MCP access.

**Config:** Once installed, set `cos: enabled: true` in `~/.claude/kf-integrations.yaml`
(defaults to `true` — the MCP prefix `mcp__cos-mcp__` must be registered).

---

## Orchestra — Multi-Agent Coordination

**What it does:** Orchestra is a multi-agent task queue with SSE push, artifact
passing, and cross-machine handoffs. When enabled, KF can coordinate across machines
and agent sessions — queue work for a remote agent, pull pending tasks, pass
structured artifacts between sessions. Without it, all Orchestra tool calls are
silently skipped; single-session KF is fully unaffected.

Orchestra is opt-in (`enabled: false` by default) because it requires a running
Orchestra server and is only useful in multi-machine or parallel-agent setups.

**Access:** Orchestra is a private service. Contact **David Pedersen** to request
access: dpedersen@semalytics.com

Register the SSE endpoint in `~/.claude/settings.json`:

```json
"mcpServers": {
  "orchestra": {
    "type": "sse",
    "url": "https://your-orchestra-server/sse"
  }
}
```

Then set `orchestra: enabled: true` in `~/.claude/kf-integrations.yaml`.

---

## Controlling Which Add-ons Are Active

All integrations are managed through `~/.claude/kf-integrations.yaml`. The file is
deployed by `install.sh` on first install (non-destructive — not overwritten on updates).

```yaml
integrations:
  mempalace:       enabled: true   # semantic wiki search
  gemini_routing:  enabled: true   # pre-prompt classifier (needs GEMINI_API_KEY)
  beads:           enabled: true   # task tracking (bd/br CLIs)
  gitnexus:        enabled: true   # code intelligence MCP
  asta:            enabled: true   # Expert research (needs Allen AI key + MCP)
  cos:             enabled: true   # comms analysis (needs COS MCP)
  orchestra:       enabled: false  # multi-agent coordination (opt-in)
```

Hooks read this file on every invocation — no restart needed after changes.
