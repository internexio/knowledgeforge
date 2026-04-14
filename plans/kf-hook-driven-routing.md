# KnowledgeForge Claude Code: Hook-Driven Routing Architecture

**Version:** 0.1 (Proposal) | **Date:** 2026-04-14
**Problem:** CP consistently outperforms CC because Claude Projects has semantic search over all knowledge while Claude Code requires the agent to know what to load before it knows it needs it.

---

## Why CP Wins

Claude Projects gives Claude semantic search over every module file in project knowledge. When a user asks "review this spec," Claude's project knowledge search finds Module 07 (Critic), Module 12 (Calibration Layer), and Module 15 (Grounding Scores) automatically — even if the user never mentioned calibration or grounding. The retrieval is need-driven and complete.

Claude Code has no equivalent. The agent sees CLAUDE.md (always loaded), can be told to read skills, and can browse docs — but it must *recognize the need first*. A cross-cutting module buried at line 200 of a SKILL.md under "Cross-Cutting Concerns" doesn't generate enough signal for the agent to proactively load it. The agent commits to an approach, produces output, and the calibration/grounding/metacognitive layers never fire because the agent never knew to consult them.

**The gap isn't knowledge — it's retrieval timing.** CC has all the same knowledge on disk. It just doesn't know which files to read before it starts working.

---

## The Hook-Driven Solution

A `UserPromptSubmit` hook runs a fast, cheap LLM (Gemma 3, OLMo, Llama — even a free-tier model) BEFORE Claude sees the prompt. This LLM does one thing: classify the request against the full KF module inventory and output routing directives that tell Claude exactly what to load.

```
User types prompt
       │
       ▼
┌──────────────────────────────┐
│   UserPromptSubmit Hook      │
│                              │
│   1. Read prompt from stdin  │
│   2. Call fast LLM (local    │
│      Ollama or free API)     │
│   3. LLM has compact KF     │
│      module index (~2K tok)  │
│   4. LLM returns:           │
│      - decision_type         │
│      - primary_mode          │
│      - cross_cutting_modules │
│      - routing_notes         │
│   5. Format as routing block │
│   6. Prepend to prompt       │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│   Claude Code Main Agent     │
│                              │
│   Sees augmented prompt:     │
│   "[KF-ROUTE: mode=Critic,  │
│    decision=evaluative,      │
│    load: 07, 12, 15]         │
│    ---                       │
│    Review this spec and..."  │
│                              │
│   → Loads Critic skill       │
│   → References Calibration   │
│   → Applies Grounding Scores │
│   → Executes with full       │
│     cross-cutting awareness  │
└──────────────────────────────┘
```

**Why this works:** The fast LLM only does classification — well within a 3-7B model's capability. It doesn't need to reason about the spec or produce the review. It just needs to read "review this spec" and output "Critic mode, evaluative judgment, also load Calibration and Grounding." Claude does the actual thinking.

---

## The Full Restructuring

### Current CC Architecture (Problem)

```
CLAUDE.md (~30-35K tokens)
├── Full orchestrator prompt
├── All mode triggers
├── All behavioral rules
├── Cross-cutting module references (buried)
└── Everything competing for attention in one file

.claude/skills/knowledgeforge/SKILL.md
├── Mode routing table
├── Cross-cutting concerns (buried at bottom)
└── Agent can't see this until it decides to look
```

**Failure mode:** CLAUDE.md is so dense that cross-cutting modules lose salience. The agent reads 30K tokens of instructions, retains the loudest signals (mode triggers, identity), and loses the quieter ones (grounding scores, calibration layer, metacognitive checks).

### Proposed CC Architecture (Solution)

```
CLAUDE.md (~5-8K tokens)                    ← MUCH thinner
├── Identity (KF 6.x orchestrator)
├── Meta-principle (patch weaknesses, not scaffold strengths)
├── Decision classification behavior (4 types)
├── "When you see [KF-ROUTE], follow its directives"
├── Quality gate summary (what to check before delivering)
├── Accretion check reminder
└── Forward navigation rule

.claude/skills/kf/                          ← One skill per mode
├── builder.md                              (loaded when UserPromptSubmit says "mode=Builder")
├── critic.md
├── debugger.md
├── strategist.md
├── expert.md
├── synthesizer.md
├── navigator.md
├── coordinator.md
└── calibrator.md

.claude/docs/knowledgeforge/                ← Reference docs (not skills)
├── 12_calibration_layer.md                 (loaded when routing says "also load: 12")
├── 13_decision_classification.md
├── 14_metacognitive_monitor.md
├── 15_grounding_scores.md
├── 16_operational_bounds.md
├── 17_temporal_knowledge.md
├── 18_salience_allocation.md
├── 19_memory_architecture.md
├── 20_permission_model.md
├── 21_knowledge_accretion.md
├── 22_semantic_wiki_search.md
├── 23_taxonomy_enforcement.md
└── 24_verbatim_history_mining.md

.claude/hooks/
├── kf-route.py                             ← UserPromptSubmit hook (THE key piece)
├── kf-stop-validator.py                    ← Stop hook (completion gate)
├── kf-precompact.py                        ← PreCompact hook (state survival)
├── kf-postcompact.py                       ← PostCompact hook (minimal re-injection)
└── kf-edit-nudge.py                        ← PostToolUse hook (checkpoint reminder)

.claude/commands/
├── kf-build.md                             ← /kf-build slash command
├── kf-critique.md                          ← /kf-critique
├── kf-debug.md
├── kf-strategize.md
└── kf-expert.md

.kf/                                        ← Runtime state (created at runtime)
├── state/
│   ├── active_mode
│   ├── routing_index.yaml
│   ├── edit_count
│   └── session_summary.md
└── transcripts/
```

### What Each Layer Does

| Layer | Purpose | Token Budget | When Loaded |
|-------|---------|-------------|-------------|
| CLAUDE.md | Identity + behavioral rules + "follow routing directives" | ~5-8K | Always |
| Skill file | Full mode protocol for the active mode | ~3-6K each | When hook says to |
| Doc file | Cross-cutting module reference | ~2-5K each | When hook says to |
| Hook output | Routing directive prepended to prompt | ~100-200 tokens | Every prompt |

**Total context per request:** ~5-8K (CLAUDE.md) + ~3-6K (one skill) + ~4-10K (2-3 cross-cutting docs) + ~200 (routing) = **~12-24K tokens**

vs. current: ~30-35K (CLAUDE.md) + whatever the agent decides to load

The proposed architecture is both thinner AND more complete — it loads less total but more of the *right* content.

---

## The Routing Hook: `kf-route.py`

### Hook Configuration

```json
// .claude/settings.json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "python3 .claude/hooks/kf-route.py"
      }
    ]
  }
}
```

### What the Hook Does

```python
#!/usr/bin/env python3
"""
KF Routing Hook — UserPromptSubmit
Runs a fast LLM to classify the user's prompt and inject routing directives.
"""
import sys
import json
import subprocess

# Read hook stdin
hook_input = json.loads(sys.stdin.read())
user_prompt = hook_input.get("prompt", "")

# The compact KF module index — this is what the fast LLM sees
KF_INDEX = """
KnowledgeForge modes (pick ONE primary):
- Builder: create, build, generate, write spec, scaffold
- Critic: review, check, validate, find gaps, what's missing, lint
- Debugger: broken, not working, failing, diagnose, why is
- Strategist: priorities, trade-offs, should I, what next, which option
- Expert: deep analysis, domain question, how does X work
- Synthesizer: patterns, commonalities, framework from examples
- Coordinator: multi-agent, workflow, coordination
- Calibrator: setup, CLAUDE.md, configure AI coder
- Navigator: genuinely ambiguous (ONLY if top-2 modes produce different output types)

Decision types:
- reckoning: verifiable correct answer, answer directly
- evaluative: judgment against existing criteria
- predictive: judgment about future outcomes
- novel: no relevant precedent

Cross-cutting modules (include when relevant):
- M12 Calibration: high-stakes evaluation, irreversible decisions, benchmarks
- M13 Decision Classification: always relevant (but usually handled by CLAUDE.md)
- M14 Metacognitive Monitor: long sessions, complex chains, stuck detection
- M15 Grounding Scores: claims from prior knowledge, uncertain premises
- M17 Temporal Knowledge: "when did this change", temporal reasoning
- M21 Knowledge Accretion: output might have reuse value beyond this session

Output JSON only:
{"mode": "...", "decision_type": "...", "cross_cutting": [...], "notes": "..."}
"""

# Call fast LLM via Ollama (local) or free API
routing_prompt = f"{KF_INDEX}\n\nClassify this user request:\n\"{user_prompt}\""

try:
    result = subprocess.run(
        ["ollama", "run", "gemma3:4b", "--format", "json"],
        input=routing_prompt,
        capture_output=True,
        text=True,
        timeout=10  # 10 second ceiling
    )
    routing = json.loads(result.stdout.strip())
except Exception:
    # Fallback: no routing directive, Claude handles it raw
    # This is the graceful degradation — hook failure doesn't break anything
    sys.exit(0)

# Format routing directive
mode = routing.get("mode", "")
decision_type = routing.get("decision_type", "")
cross_cutting = routing.get("cross_cutting", [])
notes = routing.get("notes", "")

# Build the directive block
directive_parts = []
if mode:
    directive_parts.append(f"mode={mode}")
if decision_type:
    directive_parts.append(f"decision={decision_type}")
if cross_cutting:
    modules = ", ".join(str(m) for m in cross_cutting)
    directive_parts.append(f"load=[{modules}]")

if not directive_parts:
    # Nothing to route — let Claude handle it naturally
    sys.exit(0)

directive = " | ".join(directive_parts)
if notes:
    directive += f" | {notes}"

# Build skill loading hints
skill_hint = ""
if mode:
    skill_hint = f"\nLoad skill: .claude/skills/kf/{mode.lower()}.md"

doc_hints = ""
if cross_cutting:
    doc_files = []
    module_map = {
        "M12": "12_calibration_layer.md",
        "M14": "14_metacognitive_monitor.md",
        "M15": "15_grounding_scores.md",
        "M17": "17_temporal_knowledge.md",
        "M21": "21_knowledge_accretion.md",
    }
    for m in cross_cutting:
        if m in module_map:
            doc_files.append(f".claude/docs/knowledgeforge/{module_map[m]}")
    if doc_files:
        doc_hints = "\nReference docs: " + ", ".join(doc_files)

# Inject routing block into prompt
augmented_prompt = (
    f"[KF-ROUTE: {directive}]{skill_hint}{doc_hints}\n"
    f"---\n"
    f"{user_prompt}"
)

# Output modified prompt via hook protocol
output = {
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "updatedPrompt": augmented_prompt
    }
}
print(json.dumps(output))
sys.exit(0)
```

### What Claude Sees

**User typed:** "Review this spec and tell me what's missing"

**Claude receives (after hook):**
```
[KF-ROUTE: mode=Critic | decision=evaluative | load=[M12, M15]]
Load skill: .claude/skills/kf/critic.md
Reference docs: .claude/docs/knowledgeforge/12_calibration_layer.md, .claude/docs/knowledgeforge/15_grounding_scores.md
---
Review this spec and tell me what's missing
```

**User typed:** "What port does PostgreSQL use?"

**Claude receives:** (no routing — hook exits 0 with no output because decision_type=reckoning needs no mode activation)
```
What port does PostgreSQL use?
```

**User typed:** "Should we open-source the framework?"

**Claude receives:**
```
[KF-ROUTE: mode=Strategist | decision=novel | load=[M12, M15, M21] | high-stakes, irreversible — flag for human review]
Load skill: .claude/skills/kf/strategist.md
Reference docs: .claude/docs/knowledgeforge/12_calibration_layer.md, .claude/docs/knowledgeforge/15_grounding_scores.md, .claude/docs/knowledgeforge/21_knowledge_accretion.md
---
Should we open-source the framework?
```

---

## CLAUDE.md: The Thin Orchestrator

```markdown
# KnowledgeForge 7.0 Orchestrator

You are the KnowledgeForge orchestrator. Your job: process every request
through the correct reasoning pattern at the correct depth.

## Meta-Principle
KF modes patch model weaknesses, not scaffold strengths. If you handle
it natively, don't add overhead.

## Routing Directives
When a prompt begins with [KF-ROUTE: ...], follow its directives:
- `mode=X` → Load the indicated skill from .claude/skills/kf/X.md
  and execute using that mode's protocol
- `decision=X` → Frame your response at the indicated depth
  (reckoning: direct answer; evaluative: structured analysis;
  predictive: assumptions + ranges; novel: expanded + flag for review)
- `load=[M12, M15, ...]` → Read the indicated docs from
  .claude/docs/knowledgeforge/ and apply their protocols
  during execution

When NO routing directive is present, the request is either a reckoning
or the routing hook couldn't classify it. Answer directly using your
best judgment. If it feels like it needs a mode, load the skill yourself.

## Decision Types (Always Apply)
- Reckoning: verifiable answer → under 50 tokens, no overhead
- Evaluative: judgment against criteria → structured, explicit confidence
- Predictive: future outcomes → document assumptions, probability ranges
- Novel: no precedent → expand fully, flag for human review

## Quality Gates (Always Check Before Delivering)
- Directly addresses what was asked
- Reasoning depth matches decision type
- Actionable without follow-up
- Forward navigation included
- No unnecessary hedging — state confidence explicitly

## Accretion Check
After producing evaluative+ output: does this contain knowledge worth
persisting? If novel AND reusable beyond this session, flag as accretion
candidate. Skip for reckonings and routine outputs.

## Mode Chaining
When a request needs multiple modes, state the plan:
"This needs N steps: 1. [Mode A] for X. 2. [Mode B] for Y."
The routing hook handles single-mode requests. For chains, you
manage the sequence — load each skill in order.

## Chain Auto-Verification
Chains producing evaluative+ output automatically include a Critic
pass. Load .claude/skills/kf/critic.md for adversarial review.
Framing: "Find the failure mode the producing mode missed."

## Circuit Breakers
3 consecutive failures in any mode → halt, surface diagnostics, options.
Don't retry. Don't push through.
```

**That's ~2,500 tokens.** Compare to the current ~30-35K. The difference is everything that used to be in CLAUDE.md is now in skill files and doc files, loaded on-demand by hook directive.

---

## Skill Files: One Per Mode

Each skill contains the FULL mode protocol — everything currently in the mode's module spec that's needed for execution. Example structure:

```markdown
# .claude/skills/kf/critic.md

## Critic Agent — KnowledgeForge Mode

### Purpose
Review artifacts for completeness, consistency, and correctness.
Challenge assumptions. Find what's missing.

### Protocol
1. Completeness: Are all required elements present?
2. Consistency: Do parts agree with each other?
3. Assumptions: What's assumed but not stated?
4. Edge cases: What breaks under unusual conditions?

### Severity Framework
- Sev 1 (Critical): Blocks functionality or causes incorrect behavior
- Sev 2 (Major): Significant gap but workaround exists
- Sev 3 (Minor): Improvement opportunity, not blocking

### Output Format
[Full output template]

### Quality Gates
- Findings have specific location + specific fix
- Severity levels consistently applied
- ≤ 15 findings
- Bias checks documented if high-stakes

### Variants
- Standard: Review a single artifact
- Adversarial: "Find the flaw the author missed" (auto-verify in chains)
- Linter: Knowledge base health check (scan all entries)
- Audit: Infrastructure inventory + SPOF analysis

### Integration
- After Critic, if Builder revision needed: Critic ↔ Builder loop
  (max one automatic revision cycle; persistent Sev 2 → escalate to user)
- Accretion: Contradictions found during linting are accretion candidates
```

---

## Doc Files: Cross-Cutting Reference

These are loaded when the routing hook identifies them as relevant. They contain the cross-cutting module's protocol — not as a "skill to execute" but as "rules to apply during execution."

```markdown
# .claude/docs/knowledgeforge/15_grounding_scores.md

## Grounding Scores — Apply During Mode Execution

When reasoning builds on claims from prior knowledge or uncertain
premises, assign grounding scores:

1.0  Directly observed (API response, file read, test output)
0.8  Computed from grounded data (deterministic transform)
0.6  High-confidence inference from grounded observations
0.4  Linguistic inference with partial verification
0.2  LLM output with some support
0.1  Pure LLM output, no verification

### Propagation Rule
Conclusion grounding = min(premise groundings) × inference confidence

### When to Apply
- Expert mode: all domain claims
- Builder mode: design decision rationale
- Strategist mode: option evaluation premises
- Debugger mode: hypothesis confidence

### When to Skip
- Reckonings (answer is verifiable by definition)
- Direct observations (grounding = 1.0 by default)
```

This is ~200 tokens. Loaded only when relevant. Not competing for attention in a 30K CLAUDE.md.

---

## The Fast LLM: Selection and Configuration

### Model Options (Ranked by Fit)

| Model | Size | Speed | Cost | Where to Run | Notes |
|-------|------|-------|------|-------------|-------|
| Gemma 3 4B | 4B | ~200ms | Free (Ollama) | Local | Best balance of speed + accuracy for classification |
| OLMo 3 1B | 1B | ~50ms | Free (Ollama) | Local | Fastest, but may miss edge cases |
| Llama 3.2 3B | 3B | ~150ms | Free (Ollama) | Local | Good alternative to Gemma |
| Gemma 3 12B | 12B | ~500ms | Free (Ollama) | Local | Higher accuracy, still fast enough |
| Free OpenRouter model | Varies | ~300ms | Free tier | API | No local GPU needed |

**Recommendation:** Gemma 3 4B via Ollama. Fast enough (~200ms overhead per prompt), accurate enough for intent classification, runs on CPU, no API dependency.

### Fallback Strategy

```
Primary:   Ollama (local Gemma 3 4B)     ← no latency, no cost, no network
Fallback:  Free OpenRouter model          ← if Ollama unavailable
Emergency: No routing (hook exits 0)      ← Claude handles it raw, like current CC
```

**Graceful degradation is critical.** If the hook fails, the system works exactly like today's CC. No routing directive → Claude uses CLAUDE.md rules alone. The hook is additive, not load-bearing for basic operation.

### The Module Index (What the Fast LLM Sees)

The fast LLM gets a ~2K token compact index of all KF modules. This is the ONLY context it needs — no mode protocols, no module specs. Just trigger phrases and module descriptions.

```
MODES (pick one primary):
Builder: create, build, generate, write spec → artifact output
Critic: review, check, validate, find gaps → recommendation output
Debugger: broken, failing, diagnose, not working → analysis output
Strategist: priorities, should I, trade-offs, which option → recommendation output
Expert: deep analysis, how does X work, domain question → analysis output
Synthesizer: patterns, commonalities, framework from examples → analysis output
Coordinator: multi-agent, workflow, coordination → artifact output
Calibrator: setup, CLAUDE.md, configure AI coder → artifact output
Navigator: ONLY if genuinely ambiguous (two candidates, different output types)
[none]: direct answer, no mode needed (reckonings, casual chat)

CROSS-CUTTING (include when conditions match):
M12 Calibration: when output is high-stakes, irreversible, or benchmarking
M14 Metacognitive Monitor: when task is complex, multi-step, or long-running
M15 Grounding Scores: when reasoning depends on uncertain or prior knowledge
M17 Temporal Knowledge: when request involves time, change, freshness
M21 Knowledge Accretion: when output might have reuse value beyond session

DECISION TYPES:
reckoning: verifiable answer exists → no mode needed
evaluative: judgment against known criteria → mode with structured output
predictive: judgment about future → mode with assumptions documented
novel: no precedent → mode with full expansion, flag for review
```

This is small enough that even a 1B model can process it accurately.

---

## How This Closes the CP-CC Gap

| Capability | CP (Current) | CC (Current) | CC (With Hook Routing) |
|-----------|-------------|-------------|----------------------|
| Module retrieval | Semantic search — finds right module automatically | Agent must know to load | Hook tells agent exactly what to load |
| Cross-cutting modules | Always searchable | Buried in SKILL.md — rarely loaded | Hook identifies and injects before execution |
| Context efficiency | ~200K window, all loaded | ~30-35K CLAUDE.md + optional | ~12-24K — thinner but more targeted |
| Mode activation | Orchestrator prompt recognizes trigger | Skill matching or manual | Hook pre-classifies, skill loads on directive |
| Reckonings | Orchestrator handles directly | CLAUDE.md handles (but 30K context waste) | Hook says "no mode" → 5K CLAUDE.md handles directly |
| Novel judgments | Full framework in context | Partial — cross-cutting modules often missed | Hook loads full module set: skill + M12 + M15 + M21 |

**The hook replicates CP's semantic retrieval** by doing classification externally and injecting the results. CP asks "which modules are relevant?" at query time via search. The hook asks the same question via a fast LLM. The mechanism differs but the outcome is the same: Claude gets the right modules loaded before it starts working.

---

## Slash Commands: Mode Shortcuts

For power users who know which mode they want, slash commands bypass the hook entirely:

```markdown
# .claude/commands/kf-critique.md
---
description: "Activate KF Critic mode for artifact review"
hooks:
  Stop:
    - hooks:
        - type: command
          command: "python3 .claude/hooks/kf-stop-validator.py --mode critic"
---

Read the Critic skill from .claude/skills/kf/critic.md.
Also read these cross-cutting docs:
- .claude/docs/knowledgeforge/12_calibration_layer.md
- .claude/docs/knowledgeforge/15_grounding_scores.md

Then review the artifact the user specifies using the Critic protocol.
Apply Calibration Layer if the review is high-stakes.
Apply Grounding Scores to all evaluative claims.
```

`/kf-critique Review the Builder spec for Module 25` → Critic activates with all cross-cutting modules, Stop hook enforces completion checklist. No routing hook needed — the slash command is the explicit route.

---

## Migration from Current CC

### Phase 1: Build the Hook (Day 1)

1. Install Ollama + Gemma 3 4B (or chosen model)
2. Write `kf-route.py` with the compact module index
3. Test: 20 representative prompts → verify routing accuracy
4. Add to `.claude/settings.json` as UserPromptSubmit hook

**Validation:** Run same 20 prompts with and without hook. Measure: does the hook select the same mode a KF expert would? Target: >85% agreement.

### Phase 2: Decompose CLAUDE.md (Day 2-3)

1. Extract each mode's protocol into `.claude/skills/kf/{mode}.md`
2. Extract each cross-cutting module into `.claude/docs/knowledgeforge/{module}.md`
3. Slim CLAUDE.md to ~5-8K tokens (identity + routing directive handler + quality gates)
4. Add "When you see [KF-ROUTE], follow its directives" to CLAUDE.md

**Validation:** Run the same 20 prompts against decomposed CC. Compare output quality to current CC and to CP.

### Phase 3: Add Stop Validator + Slash Commands (Day 4)

1. Port Stop hook validator with per-mode checklists
2. Create slash commands for each mode
3. Add PreCompact/PostCompact hooks for state survival

**Validation:** Attempt to complete a Builder session with deliberately incomplete output. Verify Stop hook blocks.

### Phase 4: Tune (Week 2)

1. Run 50 diverse prompts through the full pipeline
2. Measure: routing accuracy, cross-cutting module recall, output quality
3. Compare systematically to CP output quality on the same prompts
4. Adjust module index wording, model choice, or routing logic based on gaps

---

## Multi-Model Extension

The routing hook is the natural integration point for multi-model selection. Currently it just classifies and routes. In the multi-model variant, it also selects the model:

```python
# In kf-route.py, after classification:
if decision_type == "reckoning" and in_training_distribution:
    model_directive = "model=local:gemma3:4b"  # answer locally, near-zero cost
elif decision_type == "novel":
    model_directive = "model=openrouter:anthropic/claude-opus-4"
elif decision_type == "evaluative":
    model_directive = "model=openrouter:anthropic/claude-sonnet-4"
```

This only works in the web agents variant (Claude Code is locked to Claude). But the routing hook architecture is the same — the web agents variant just adds model selection to the routing output.

**For CC specifically:** The model is always Claude (CC constraint). But the hook still adds value by selecting the right skill and cross-cutting modules. The multi-model benefit comes when this same architecture ports to the web agents variant.

---

## Relationship to the Universal Architecture

This proposal is compatible with the `knowledgeforge-core` compilation model from the Universal Architecture doc. The compiler would:

1. Read canonical module specs from `knowledgeforge-core/modules/`
2. Generate skill files (`.claude/skills/kf/{mode}.md`) per mode
3. Generate doc files (`.claude/docs/knowledgeforge/{module}.md`) per cross-cutting module
4. Generate the thin CLAUDE.md with model-specific patches
5. Generate the compact module index for the routing hook
6. Generate the hook script with the current model selection rules

The routing hook is the **runtime equivalent of the compiler's model-profile system.** The compiler applies patches at build time; the hook applies routing at request time. Both use the same knowledge: which model has which weaknesses, and which modules patch them.

---

## Open Questions

### 1. Hook Latency Budget

The UserPromptSubmit hook adds ~200-500ms per prompt (local LLM inference). Is this acceptable? For interactive use, 200ms is imperceptible. For rapid back-and-forth debugging sessions, it might feel sluggish if Ollama is loaded from cold start.

**Mitigation:** Keep Ollama warm with a periodic heartbeat. Or use the OLMo 1B model which runs in ~50ms even on CPU.

### 2. Routing Accuracy Floor

If the fast LLM misroutes (Debugger instead of Critic), the wrong skill loads. Claude might still produce a reasonable output (it can reason about specs even in Debugger mode), but it won't apply the Critic protocol.

**Mitigation:** The CLAUDE.md thin orchestrator retains decision classification behavior. If the routing feels wrong, Claude can override: "The routing suggested Debugger, but this looks like a review request. Loading Critic instead." The routing is a hint, not a mandate — same as Module 19's skeptical verification rule.

### 3. Prompt Modification vs. Context Injection

Two hook mechanisms are available:
- **Modify the prompt** (`updatedPrompt`): prepend routing directives to the user's message
- **Inject silent context** (`additionalContext`): add context invisible to the user

Prompt modification is more transparent (user can see the routing in the conversation). Silent context is cleaner UX but less debuggable.

**Recommendation:** Use prompt modification during development (visible routing = easier debugging). Switch to silent context injection once routing accuracy is validated.

### 4. Skill Loading Compliance

When the hook says "Load skill: .claude/skills/kf/critic.md", does Claude Code actually load it? Skills are typically invoked by name, not by file path. The hook may need to use the skill's registered name rather than the file path.

**Research needed:** Test whether Claude Code responds to file path hints in prompts, or whether the skill must be invoked via its SKILL.md `name` field. If the latter, the routing directive should output the skill name, not the path.

### 5. Doc File Loading

`.claude/docs/` files are available for Claude to read but aren't automatically loaded like skills. The routing directive says "Reference docs: ..." — does Claude actually read them?

**Mitigation:** The CLAUDE.md instruction "When a routing directive says `load=[M12, M15]`, read those files before starting" makes this explicit. But compliance depends on attention to the instruction vs. attention to the user's actual question.

**Alternative:** The hook could use the `additionalContext` mechanism to inline the key content from cross-cutting modules directly, rather than asking Claude to read files. This trades context window space for loading reliability.

---

## Summary

| Dimension | Current CC | Proposed CC |
|-----------|-----------|-------------|
| CLAUDE.md size | ~30-35K tokens | ~5-8K tokens |
| Mode loading | Hope agent recognizes need | Hook pre-classifies and directs |
| Cross-cutting modules | Buried, rarely loaded | Hook identifies, injects directive |
| Routing intelligence | Embedded in dense prompt | External fast LLM (cheap, fast) |
| Graceful degradation | N/A | Hook failure → current behavior |
| Context efficiency | Everything loaded, little used | Only relevant content loaded |
| Quality gate enforcement | Advisory (in prompt) | Mandatory (Stop hook + slash command hooks) |
| Reckonings | 30K context for a 5-word answer | 5K context, no skill load |
| Novel judgments | Cross-cutting modules often missed | Full module set loaded by directive |
