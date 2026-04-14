# KnowledgeForge Universal: Multi-Platform, Multi-Model Architecture

**Version:** 0.1 (Proposal) | **Date:** 2026-04-14
**Scope:** Re-architect KF from a single-platform prompt system to a compiled, multi-platform, multi-model orchestration framework with a single source of truth.

---

## The Problem in Three Sentences

KnowledgeForge exists in three copies (CP, CC, CW) that drift independently. Adding a fourth variant (web agents) will make drift unmanageable. Every research package like the AI Tinkerers findings must be manually applied to each variant, and the meta-principle ("patch weaknesses, don't scaffold strengths") can't be enforced when you don't know which model's weaknesses you're patching.

---

## Architectural Thesis

KnowledgeForge is currently three things conflated into one:

1. **Knowledge corpus** — the module specs, patterns, wiki entries, decision taxonomy
2. **Runtime orchestrator** — the behavioral prompt that routes, executes, and verifies
3. **Platform binding** — how it manifests in Claude Projects vs Claude Code vs Cowork

These must be separated. The knowledge corpus is the single source of truth. The orchestrator is *compiled* per platform and per model from that corpus. The platform binding is the thinnest possible adaptation layer.

```
┌─────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE CORPUS                          │
│                   (Single Source of Truth)                    │
│                                                              │
│  knowledgeforge-core/                                        │
│  ├── modules/          # 01-24+ module specs (canonical)     │
│  ├── wiki/             # Tier 0 accreted knowledge           │
│  ├── templates/        # Specification templates             │
│  ├── taxonomy/         # Controlled vocabulary (Module 23)   │
│  ├── model-profiles/   # Per-model weakness/strength maps    │
│  └── platform-bindings/# Per-platform adaptation rules       │
│                                                              │
├──────────────── COMPILER ────────────────────────────────────┤
│                                                              │
│  kf-compile                                                  │
│  ├── Target: platform × model → runtime artifact             │
│  ├── Inputs: corpus + model-profile + platform-binding       │
│  └── Outputs: deployable prompt/config per target            │
│                                                              │
├──────────────── RUNTIME TARGETS ─────────────────────────────┤
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ CP       │ │ CC       │ │ CW       │ │ Web Agents   │   │
│  │(Projects)│ │(Claude   │ │(Cowork)  │ │(FastAPI +    │   │
│  │          │ │ Code)    │ │          │ │ OpenRouter)  │   │
│  │ Static   │ │ CLAUDE.md│ │ cos-cw   │ │ API-driven   │   │
│  │ project  │ │ + skills │ │ plugin   │ │ orchestrator │   │
│  │ knowledge│ │ + hooks  │ │          │ │              │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
│                                                              │
│  Each target may use different models:                       │
│  CP: Claude Opus/Sonnet (Anthropic native)                   │
│  CC: Claude Sonnet/Opus (Claude Code native)                 │
│  CW: Claude Sonnet (Cowork native)                           │
│  Web: Any model via OpenRouter (dynamic selection)           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 1: The Source of Truth

### `knowledgeforge-core` Repository

A new repo that contains *only* canonical knowledge. No platform-specific artifacts. No prompt files. Pure content.

```
knowledgeforge-core/
├── README.md
├── kf.yaml                         # Version, model-profile index, platform index
├── modules/
│   ├── 00_orchestrator.md          # Core behavioral rules (platform-agnostic)
│   ├── 01_navigator.md
│   ├── 02_builder.md
│   ├── ...
│   └── 24_verbatim_history.md
├── wiki/                           # Tier 0 accreted knowledge
│   ├── index.md
│   └── {domain}/{topic}.md
├── templates/
│   ├── specification.yaml
│   ├── infrastructure.yaml
│   ├── era.yaml
│   └── ...
├── taxonomy/
│   └── controlled_vocabulary.yaml  # Module 23 canonical vocab
├── model-profiles/
│   ├── _schema.yaml                # Profile format definition
│   ├── claude-opus-4.yaml
│   ├── claude-sonnet-4.yaml
│   ├── gpt-5.yaml
│   ├── gemini-3.yaml
│   ├── llama-4.yaml
│   └── olmo-3-7b.yaml
├── platform-bindings/
│   ├── claude-projects.yaml
│   ├── claude-code.yaml
│   ├── cowork.yaml
│   └── web-agents.yaml
└── compiler/
    └── kf-compile.py               # The compilation script
```

### Relationship to Existing Repos

| Repo | New Role | What Changes |
|------|----------|-------------|
| `knowledgeforge-core` (NEW) | Single source of truth | Canonical modules, wiki, model profiles |
| `knowledgeforge-cp` | Compiled output target | Receives compiled project knowledge files. Stops being hand-edited. |
| `knowledgeforge-cc` | Compiled output target | Receives compiled CLAUDE.md + skills + hooks. Stops being hand-edited. |
| `knowledgeforge-cw` | Compiled output target | Receives compiled Cowork plugin config. Stops being hand-edited. |
| `knowledgeforge-web` (NEW) | Compiled output target | Receives compiled API orchestrator config for web agent deployment. |

**The rule:** You edit `knowledgeforge-core`. You run `kf-compile`. Compiled artifacts flow to target repos. Target repos are *never* hand-edited — they're build artifacts.

### Research Ingestion Workflow

When you drop a research package like the AI Tinkerers findings:

```
1. Research lands in knowledgeforge-core/wiki/ as accreted entries
2. Module updates are made in knowledgeforge-core/modules/
3. Model profile updates (if model-specific findings) go to model-profiles/
4. Run kf-compile --all
5. All four targets receive updated artifacts simultaneously
6. Each target gets model-appropriate prompt variants automatically
```

No more applying the same finding to three repos independently.

---

## Part 2: Model Profiles and the Meta-Principle

### The Core Problem

"Patch weaknesses, don't scaffold strengths" requires *knowing* each model's weaknesses. A prompt that patches Claude Sonnet's tendency to skip hypotheses might scaffold GPT-5's tendency to over-hypothesize. The same mode, aimed at different models, needs different emphasis.

### Model Profile Schema

Each model gets a weakness/strength map that the compiler uses to adjust prompt generation:

```yaml
# model-profiles/claude-sonnet-4.yaml
model:
  id: claude-sonnet-4
  provider: anthropic
  context_window: 200000
  output_limit: 64000
  supports_tools: true
  supports_streaming: true
  cost_per_mtok_input: 3.00
  cost_per_mtok_output: 15.00

strengths:
  # Things this model handles natively — KF should NOT add overhead here
  - id: intent_decomposition
    description: "Strong at decomposing complex requests into sub-tasks"
    confidence: 0.9
    implication: "Navigator overhead on clear intents is wasteful"

  - id: structured_output
    description: "Reliable YAML/JSON generation with minimal coercion"
    confidence: 0.85
    implication: "SAP cascade can start at level 1 (strict parse) with high success"

  - id: long_context_recall
    description: "Maintains coherence across 100K+ token contexts"
    confidence: 0.8
    implication: "Less aggressive Tier 2 pruning needed vs shorter-context models"

weaknesses:
  # Things this model fails at — KF MUST add structure here
  - id: hypothesis_skipping
    description: "Tends to commit to first plausible hypothesis without exploring alternatives"
    severity: high
    modes_affected: [debugger, strategist, expert]
    patch: "Enforce explicit hypothesis enumeration before evaluation"

  - id: tradeoff_hiding
    description: "Presents recommendations without surfacing downsides"
    severity: high
    modes_affected: [strategist, builder]
    patch: "Require explicit trade-off section with named losers"

  - id: gap_blindness
    description: "Produces complete-looking output that omits edge cases"
    severity: medium
    modes_affected: [builder, critic]
    patch: "Adversarial depth section mandatory; completeness checklist"

  - id: self_preference_bias
    description: "Rates own outputs higher than warranted"
    severity: medium
    modes_affected: [calibration, critic_auto_verify]
    patch: "Cross-model judge for evaluative outputs"

  - id: premature_stopping
    description: "Attempts to stop before all deliverables are complete"
    severity: medium
    modes_affected: [builder, synthesizer]
    patch: "Stop hook completion gate with per-mode checklists"

calibration:
  # Decision type thresholds — how much overhead this model needs per type
  reckoning_overhead: none
  evaluative_overhead: light      # Structured output + confidence
  predictive_overhead: moderate   # Assumption documentation + probability ranges
  novel_overhead: full            # Full framework activation
```

```yaml
# model-profiles/gpt-5.yaml
model:
  id: gpt-5
  provider: openai
  context_window: 256000
  output_limit: 32000
  supports_tools: true
  supports_streaming: true
  cost_per_mtok_input: 5.00
  cost_per_mtok_output: 15.00

strengths:
  - id: structured_reasoning
    description: "Strong multi-step chain-of-thought without explicit prompting"
    confidence: 0.85
    implication: "Debugger hypothesis chains need less scaffolding"

  - id: instruction_following
    description: "Precise adherence to format specifications"
    confidence: 0.9
    implication: "Mode output format enforcement can be lighter"

weaknesses:
  - id: over_hypothesizing
    description: "Generates excessive hypotheses, burying the likely cause"
    severity: medium
    modes_affected: [debugger]
    patch: "Cap hypothesis generation at 5; require priority ranking before exploration"

  - id: verbosity_under_uncertainty
    description: "Produces long hedging paragraphs when uncertain rather than stating uncertainty"
    severity: medium
    modes_affected: [expert, strategist]
    patch: "Enforce confidence score + max 2 sentences per uncertainty acknowledgment"

  - id: shallow_adversarial
    description: "Adversarial critique is surface-level — finds formatting issues, misses logic flaws"
    severity: high
    modes_affected: [critic, auto_verify]
    patch: "Adversarial prompt must include: compound failures, blast radius, assumption inversion"

  - id: context_window_degradation
    description: "Quality degrades in middle of long contexts (lost in the middle)"
    severity: medium
    modes_affected: [all]
    patch: "Critical information at start and end of prompts; more aggressive Tier 2 pruning"
```

```yaml
# model-profiles/olmo-3-7b.yaml
model:
  id: olmo-3-7b-instruct
  provider: self-hosted
  context_window: 32000
  output_limit: 8000
  supports_tools: false
  supports_streaming: true
  cost_per_mtok_input: 0.00  # self-hosted
  cost_per_mtok_output: 0.00

strengths:
  - id: fast_classification
    description: "Extremely fast at intent classification and routing decisions"
    confidence: 0.75
    implication: "Ideal for KF intent router — decision classification at near-zero cost"

  - id: deterministic_tasks
    description: "Reliable on reckoning-type questions within training distribution"
    confidence: 0.7
    implication: "Can handle reckonings without routing to larger models"

weaknesses:
  - id: reasoning_depth
    description: "Breaks down on multi-step reasoning beyond 3-4 steps"
    severity: critical
    modes_affected: [all_except_navigator]
    patch: "NEVER use for evaluative+ decision types. Route to larger model."

  - id: hallucination_rate
    description: "Higher hallucination rate on domain-specific questions"
    severity: high
    modes_affected: [expert, builder]
    patch: "Grounding score floor 0.4 for all outputs. Mandatory verification."

  - id: instruction_adherence
    description: "Inconsistent at following complex multi-part instructions"
    severity: high
    modes_affected: [all]
    patch: "Single-instruction prompts only. Decompose complex instructions."

calibration:
  reckoning_overhead: light       # Can handle but verify
  evaluative_overhead: DO_NOT_USE # Route to larger model
  predictive_overhead: DO_NOT_USE
  novel_overhead: DO_NOT_USE

role_restriction: intent_router_only  # Flag for compiler
```

### How the Compiler Uses Profiles

The compiler reads a module spec and a model profile, then generates a model-specific prompt variant:

```python
# Pseudocode for compiler logic
def compile_mode(module_spec, model_profile):
    output = base_prompt(module_spec)

    for weakness in model_profile.weaknesses:
        if module_spec.mode_id in weakness.modes_affected:
            # Inject the patch into the mode's prompt
            output = inject_patch(output, weakness.patch, weakness.severity)

    for strength in model_profile.strengths:
        if overlaps(strength, module_spec.constraints):
            # Remove scaffolding that this model doesn't need
            output = remove_scaffolding(output, strength.id)

    # Apply calibration overhead level
    overhead = model_profile.calibration[module_spec.decision_type]
    if overhead == "DO_NOT_USE":
        output = generate_routing_redirect(module_spec, model_profile)
    elif overhead == "none":
        output = strip_overhead(output)

    return output
```

**Example: Debugger mode compiled for two models**

| Prompt Element | Claude Sonnet | GPT-5 |
|----------------|--------------|-------|
| Hypothesis generation | "Generate ALL plausible hypotheses before evaluating ANY" (patches hypothesis_skipping) | "Generate at most 5 hypotheses, ranked by probability" (patches over_hypothesizing) |
| Trade-off section | "Include explicit downsides for each fix option" (patches tradeoff_hiding) | Standard — GPT-5 handles this natively |
| Adversarial depth | Standard | "Find LOGIC flaws, not formatting issues. Check: compound failures, blast radius, assumption inversion" (patches shallow_adversarial) |
| Uncertainty handling | Standard | "State confidence as a number. Max 2 sentences acknowledging uncertainty." (patches verbosity_under_uncertainty) |

Same module spec. Same knowledge corpus. Different compiled prompts. Each patches the specific model's weaknesses.

---

## Part 3: Dynamic Model Selection

### The Routing Layer

For the web agents variant (and eventually for CC/CW when they gain multi-model support), KF needs a model selection layer that chooses the right model for each task.

```
┌─────────────────────────────────────────────┐
│              KF ORCHESTRATOR                 │
│                                              │
│  1. Classify decision type                   │
│  2. Identify required mode                   │
│  3. Assess task characteristics              │
│  4. Select model from model roster           │
│  5. Load compiled prompt for mode × model    │
│  6. Execute                                  │
│  7. Verify output quality                    │
│                                              │
└─────────────────────────────────────────────┘
```

### Model Selection Criteria

```yaml
model_roster:
  # Ordered by capability tier
  tier_0_router:
    model: olmo-3-7b-instruct  # or equivalent small model
    provider: self-hosted
    use_for:
      - Decision classification (reckoning/evaluative/predictive/novel)
      - Intent routing (which mode?)
      - Simple reckonings within training distribution
    never_for:
      - Evaluative+ reasoning
      - Any output that will be surfaced to user without verification
    cost: ~$0 (self-hosted)
    latency: <100ms

  tier_1_workhorse:
    model: claude-sonnet-4  # or gpt-5-mini, gemini-3-flash
    provider: openrouter  # or direct API
    use_for:
      - Evaluative judgments
      - Standard mode execution (Builder, Critic, Debugger)
      - Most chains under 3 modes
    cost: ~$3-5/Mtok input
    latency: 1-3s TTFT

  tier_2_frontier:
    model: claude-opus-4  # or gpt-5, gemini-3-pro
    provider: openrouter  # or direct API
    use_for:
      - Novel judgments
      - 3+ mode chains
      - Adversarial verification (cross-model judge)
      - High-stakes evaluative judgments
    cost: ~$15-30/Mtok input
    latency: 3-8s TTFT

  tier_3_specialized:
    models:
      - molmo-4b: visual analysis (Leonardo framework)
      - claude-haiku-4.5: high-volume low-stakes processing
    use_for:
      - Domain-specific tasks matching model specialization
    cost: varies
```

### Selection Algorithm

```yaml
model_selection:
  step_1_classify:
    # Use tier_0_router for classification
    input: user_request
    output: decision_type, candidate_modes, task_complexity
    model: tier_0_router
    fallback: tier_1_workhorse  # if router confidence < 0.7

  step_2_select:
    rules:
      - decision_type == reckoning AND in_training_distribution:
          model: tier_0_router  # answer directly, near-zero cost
      - decision_type == reckoning AND NOT in_training_distribution:
          model: tier_1_workhorse
      - decision_type == evaluative:
          model: tier_1_workhorse
      - decision_type == predictive:
          model: tier_1_workhorse  # with tier_2 for adversarial verify
      - decision_type == novel:
          model: tier_2_frontier
      - chain_length >= 3:
          model: tier_2_frontier  # compound error risk
      - auto_verify_needed:
          verify_model: different_provider(execution_model)
          # Cross-provider judge isolation (from Orchestra research)

  step_3_override:
    # User can always force a specific model
    trigger: "use opus for this" or explicit model parameter
    action: Override selection, log override reason

  step_4_cost_guard:
    # Operational Bounds integration
    budget_remaining: check against session/daily budget
    if_over_budget: downgrade tier unless decision_type == novel
    log: model_selected, cost_estimate, selection_reason
```

### OpenRouter Integration

```yaml
openrouter_config:
  base_url: "https://openrouter.ai/api/v1"
  # Use OpenRouter for multi-provider access with fallback

  primary_models:
    evaluative: "anthropic/claude-sonnet-4"
    frontier: "anthropic/claude-opus-4"
    judge: "openai/gpt-5"  # cross-provider for judge isolation

  fallback_chain:
    # If primary fails, fall through
    - "anthropic/claude-sonnet-4"
    - "openai/gpt-5-mini"
    - "google/gemini-3-flash"

  provider_preferences:
    sort: "latency"  # or "price" for cost-sensitive deployments
    # Quantization warning: avoid INT4 for evaluative+ tasks
    quantization_ceiling: "fp8"  # minimum precision for KF work

  routing_strategy:
    simple_tasks: sort_by_price
    complex_tasks: sort_by_latency  # speed matters for chains
    adversarial: force_different_provider  # judge isolation
```

---

## Part 4: Platform Bindings

### What Each Platform Needs

```yaml
# platform-bindings/claude-projects.yaml
platform:
  id: claude-projects
  constraints:
    no_filesystem: true
    no_hooks: true
    no_multi_model: true  # locked to Claude
    context_source: project_knowledge_files
    max_files: ~50 (practical limit)
    accretion_mode: surface_to_user  # can't auto-file

  compilation_target:
    format: markdown_files
    output_dir: knowledgeforge-cp/
    structure:
      - Agent_Instructions.md  # Compiled orchestrator (model-specific for Claude)
      - modules/01-24.md       # Compiled module specs
      - wiki/*.md              # Tier 0 knowledge (copied directly)
      - templates/*.md         # Specification templates

  model_profile: claude-sonnet-4  # or claude-opus-4, determined at compile time
  compilation_notes: >
    CP gets the full orchestrator as a single behavioral prompt.
    No hooks, no dynamic model selection. Patches are baked into
    the prompt text at compile time.
```

```yaml
# platform-bindings/claude-code.yaml
platform:
  id: claude-code
  constraints:
    has_filesystem: true
    has_hooks: true  # SessionStart, Stop, PreCompact, PostToolUse, etc.
    has_subagents: true  # one level deep
    no_multi_model: true  # locked to Claude (currently)
    context_source: CLAUDE.md + .claude/skills/ + .claude/commands/
    max_claude_md: ~35000 tokens
    accretion_mode: auto_file  # writes to wiki/

  compilation_target:
    format: claude_code_project
    output_dir: knowledgeforge-cc/
    structure:
      - CLAUDE.md              # Compiled orchestrator (static zone)
      - .claude/skills/kf/     # Lazy-loaded mode files
      - .claude/commands/       # Slash commands per mode
      - .claude/hooks/          # Hook scripts (Stop gate, PreCompact, etc.)
      - .claude/hooks/validators/  # Per-mode completion validators
      - .kf/state/             # Runtime state directory (not compiled — created at runtime)
      - wiki/                  # Tier 0 knowledge

  model_profile: claude-sonnet-4  # CC model is set by claude config
  compilation_notes: >
    CC gets the lazy-dispatch architecture: thin router in CLAUDE.md,
    full mode specs in .claude/skills/kf/{mode}.md.
    Hooks are compiled from hook templates + model-specific patches.
    Subagent delegation rules baked into CLAUDE.md.
```

```yaml
# platform-bindings/cowork.yaml
platform:
  id: cowork
  constraints:
    has_filesystem: true  # via Cowork plugin
    no_hooks: false       # Cowork has its own lifecycle
    has_subagents: false  # single agent
    no_multi_model: true  # locked to Claude
    context_source: plugin_config + project_files
    accretion_mode: auto_file

  compilation_target:
    format: cowork_plugin
    output_dir: knowledgeforge-cw/
    structure:
      - cos-cw/config.yaml    # Plugin configuration
      - cos-cw/modes/         # Mode definitions
      - cos-cw/knowledge/     # Tier 0 knowledge subset

  model_profile: claude-sonnet-4
  compilation_notes: >
    CW gets a subset of KF modes relevant to Cowork's use case
    (likely: Builder, Critic, Expert, Strategist — not Calibrator).
    Plugin format constraints determine compilation output.
```

```yaml
# platform-bindings/web-agents.yaml
platform:
  id: web-agents
  constraints:
    has_filesystem: true
    has_hooks: true  # application-level hooks
    has_subagents: true  # multi-agent via API
    multi_model: true  # OpenRouter / direct APIs
    context_source: API request + persistent state (Supabase/Redis)
    accretion_mode: auto_file  # writes to database + wiki

  compilation_target:
    format: fastapi_application
    output_dir: knowledgeforge-web/
    structure:
      - app/
      │   ├── orchestrator.py      # Compiled routing logic
      │   ├── modes/               # Per-mode prompt templates (per-model variants)
      │   ├── model_selector.py    # Dynamic model selection
      │   ├── profiles/            # Model profiles (loaded at runtime)
      │   └── hooks/               # Application-level hook equivalents
      - prompts/
      │   ├── claude-sonnet-4/     # Compiled prompts for each model
      │   ├── gpt-5/
      │   ├── gemini-3/
      │   └── olmo-3-7b/
      - config/
      │   ├── openrouter.yaml      # Provider configuration
      │   └── model_roster.yaml    # Model selection rules

  model_profiles: [all]  # Web agents compile for ALL model profiles
  compilation_notes: >
    Web agents get the full multi-model treatment: one prompt set per
    model, dynamic selection at runtime, cross-model judge isolation.
    This is the only platform that exercises the full model selection
    algorithm.
```

---

## Part 5: The Compiler

### What `kf-compile` Does

```
kf-compile [--target TARGET] [--model MODEL] [--all]

Arguments:
  --target: claude-projects | claude-code | cowork | web-agents
  --model:  claude-sonnet-4 | claude-opus-4 | gpt-5 | all
  --all:    Compile all targets × all applicable models

Steps:
  1. Read knowledgeforge-core/ as canonical source
  2. Validate module consistency (cross-references, version alignment)
  3. For each target × model combination:
     a. Load platform binding constraints
     b. Load model profile
     c. For each module:
        - Apply model-specific patches (weakness → inject, strength → strip)
        - Apply platform constraints (token limits, feature availability)
        - Generate compiled prompt/config
     d. Assemble target-specific output structure
     e. Write to target output directory
  4. Generate compilation manifest (what changed, what was patched)
  5. Run validation checks (compiled output fits platform constraints)
```

### Compilation Manifest

Every compilation produces a manifest so you know what happened:

```yaml
# knowledgeforge-cc/.kf-manifest.yaml (auto-generated, do not edit)
compilation:
  source: knowledgeforge-core@v6.7.0
  target: claude-code
  model: claude-sonnet-4
  timestamp: 2026-04-14T10:30:00Z
  compiler_version: 0.1.0

patches_applied:
  - module: 09_debugger
    weakness: hypothesis_skipping
    patch: "Enforce explicit hypothesis enumeration before evaluation"
    location: .claude/skills/kf/debugger.md:L42-L48

  - module: 10_strategist
    weakness: tradeoff_hiding
    patch: "Require explicit trade-off section with named losers"
    location: .claude/skills/kf/strategist.md:L67-L73

scaffolding_removed:
  - module: 01_navigator
    strength: intent_decomposition
    removed: "Redundant intent verification step"
    location: CLAUDE.md:L120

constraints_applied:
  - platform: claude-code
    constraint: max_claude_md_tokens
    action: "Orchestrator prompt compressed to 32,847 tokens (ceiling: 35,000)"

validation:
  total_tokens: 32847
  within_budget: true
  cross_references_valid: true
  version_consistency: true
```

---

## Part 6: Research Ingestion Pipeline

### End-to-End Flow

When a research package arrives (like the AI Tinkerers findings):

```
Step 1: ANALYZE
  Drop research document into knowledgeforge-core/inbox/
  Run: kf-analyze-research inbox/ai-tinkerers-2026-04-13.md
  Output: Proposed changes categorized by:
    - Module updates (spec deltas)
    - New wiki entries (accretion candidates)
    - Model profile updates (if model-specific findings)
    - New platform binding requirements (if platform-specific)

Step 2: REVIEW
  Human reviews proposed changes
  Approves, modifies, or rejects each item
  This is the human-in-the-loop gate

Step 3: APPLY
  Approved changes written to knowledgeforge-core/
  Version bumped in kf.yaml
  Changelog updated

Step 4: COMPILE
  Run: kf-compile --all
  All targets regenerated simultaneously
  Manifest shows exactly what changed per target

Step 5: VALIDATE
  Run: kf-validate --all
  Check: compiled outputs fit platform constraints
  Check: cross-references valid
  Check: no regression in mode routing accuracy (if test suite exists)

Step 6: DEPLOY
  Push compiled artifacts to target repos
  Each repo receives only its compiled output
  Git diff shows exactly what changed
```

### The `kf-analyze-research` Tool

This could be a KF mode chain itself (Expert → Strategist → Builder):

```yaml
research_analysis_chain:
  step_1_expert:
    mode: expert
    domain: kf_architecture
    input: research_document
    output: findings_with_kf_mappings

  step_2_strategist:
    mode: strategist
    input: expert_findings
    output: prioritized_changes (T1/T2/T3 tiers)

  step_3_builder:
    mode: builder
    input: prioritized_changes
    output:
      - module_spec_deltas (per affected module)
      - wiki_entries (per accretion candidate)
      - model_profile_updates (if applicable)
      - platform_binding_updates (if applicable)

  auto_verify: true  # Critic pass on all outputs
```

---

## Part 7: Web Agents Architecture

### Why a Web Agents Variant?

The web agents variant is the only platform that exercises multi-model selection. It's also the integration point for COS, Leonardo, and other internexio systems that need KF orchestration over API.

```
┌─────────────────────────────────────────────────────────────┐
│                    WEB AGENTS                                │
│                                                              │
│  FastAPI Application                                         │
│  ├── POST /orchestrate                                       │
│  │   ├── Classify decision type (tier_0 model)               │
│  │   ├── Select mode (symbolic routing)                      │
│  │   ├── Select model (task × cost × latency)                │
│  │   ├── Load compiled prompt (mode × model)                 │
│  │   ├── Execute via OpenRouter or direct API                │
│  │   ├── Validate output (SAP cascade if structured)         │
│  │   ├── Auto-verify if evaluative+ (cross-model judge)      │
│  │   └── Return result + metadata                            │
│  │                                                           │
│  ├── POST /chain                                             │
│  │   ├── Multi-mode chain execution                          │
│  │   ├── Per-step model selection (may use different models)  │
│  │   └── Chain state management (Supabase/Redis)             │
│  │                                                           │
│  ├── POST /accrete                                           │
│  │   ├── Submit accretion candidate                          │
│  │   ├── Taxonomy validation (Module 23)                     │
│  │   └── File to wiki/ or database                           │
│  │                                                           │
│  └── WebSocket /stream                                       │
│      └── Streaming mode execution with progress updates      │
│                                                              │
│  State: Supabase (persistent) + Redis (session)              │
│  Auth: API key + optional OAuth for COS integration          │
│  Models: OpenRouter (primary) + self-hosted OLMo (router)    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Per-Step Model Selection in Chains

A single chain can use different models for different steps:

```
Chain: "Review security and tell me what to fix first"

Step 1: Expert (security review)
  Model: claude-opus-4 (frontier — high-stakes analysis)
  Compiled prompt: prompts/claude-opus-4/expert_security.md

Step 2: Auto-verify (adversarial Critic)
  Model: gpt-5 (cross-provider judge isolation)
  Compiled prompt: prompts/gpt-5/critic_adversarial.md

Step 3: Strategist (prioritization)
  Model: claude-sonnet-4 (workhorse — structured analysis)
  Compiled prompt: prompts/claude-sonnet-4/strategist.md

Total cost: ~$0.15 (vs ~$0.45 if all-Opus)
Quality: Higher (cross-model verification catches self-preference bias)
```

---

## Part 8: Migration Path

### Phase 1: Extract (Weeks 1-2)

Create `knowledgeforge-core` by extracting canonical content from `knowledgeforge-cp` (current source of truth).

- Copy modules/ from CP project knowledge
- Copy wiki/ entries
- Copy templates/
- Create initial model profile for claude-sonnet-4 (based on accumulated knowledge of Sonnet's failure modes)
- Create platform binding for claude-projects

At end of Phase 1: CP still works exactly as before. Core repo exists as a parallel copy.

### Phase 2: Compiler MVP (Weeks 3-4)

Build `kf-compile` that can regenerate the CP variant from core.

- Compile core → CP output
- Diff against current CP content
- Fix any compilation gaps until diff is zero (or intentionally improved)
- Validation: compiled CP is functionally identical to hand-maintained CP

At end of Phase 2: CP can be generated from core. Both paths work.

### Phase 3: CC Compilation (Weeks 5-6)

Extend compiler to generate CC variant.

- Create platform binding for claude-code
- Implement lazy-dispatch compilation (router + mode files)
- Implement hook template compilation
- Validate against current CC hand-maintained content

At end of Phase 3: CP and CC are both compiled from core.

### Phase 4: Multi-Model Profiles (Weeks 7-8)

Build model profiles for GPT-5, Gemini-3, OLMo-3.

- Create profile schema
- Profile each model's weaknesses via literature + testing
- Implement compiler patch/strip logic
- Generate model-specific prompt variants
- Validate: mode outputs improve on each model vs. generic prompt

At end of Phase 4: Prompts are model-aware.

### Phase 5: Web Agents (Weeks 9-12)

Build the FastAPI web agents variant.

- Implement OpenRouter integration
- Implement dynamic model selection
- Implement chain execution with per-step model selection
- Implement cross-model judge isolation
- COS integration point

At end of Phase 5: Full multi-platform, multi-model KF.

### Phase 6: CW + Research Pipeline (Weeks 13-14)

- Cowork compilation target
- Research ingestion pipeline (`kf-analyze-research`)
- End-to-end validation

---

## Part 9: Open Questions

### 1. Model Profile Maintenance

Model profiles will need continuous updating as models improve. How to systematize:
- Automated benchmark suite per model (Module 12 Calibration)
- "Canary" prompts that test each documented weakness
- Profile versioning tied to model versions
- Community contributions to profiles (if KF goes open-source)

### 2. Prompt Compilation vs. Runtime Adaptation

Two approaches to model-specific prompts:
- **Compile-time:** Generate all variants ahead of time (current proposal)
- **Runtime:** Generate model-specific prompts on-the-fly using a meta-prompt

Compile-time is deterministic, cacheable, and auditable. Runtime is more flexible but harder to debug. Recommendation: start with compile-time, add runtime adaptation as an optimization later for edge cases.

### 3. Cost Budget Allocation

When using multiple models in a chain, how to allocate budget:
- Per-chain budget? Per-session budget? Per-day budget?
- Who decides when to downgrade from Opus to Sonnet?
- How to handle budget exhaustion mid-chain?

Recommendation: Per-session budget with per-chain soft limits. Automatic downgrade for evaluative tasks. Hard stop for novel tasks (don't downgrade — pause and ask user).

### 4. Self-Hosted Router Performance

OLMo 3 7B as intent router: is the accuracy sufficient for decision classification? The router must correctly distinguish reckoning from evaluative from novel. A misclassification sends the request to the wrong model tier with the wrong prompt.

Recommendation: Build a 200-question test suite for decision classification. Measure OLMo accuracy. If below 85%, use Claude Haiku as the router instead (cheap but more accurate).

### 5. Versioning Across Targets

When core bumps to 6.8.0, all targets should reflect this. But what if a target has platform-specific patches that haven't been upstreamed?

Recommendation: No target-specific patches. All patches go through core. Targets are pure compilation outputs. If a platform needs something special, it goes in the platform binding, not in the target repo.

---

## Summary

| Before | After |
|--------|-------|
| 3 repos, manual sync, CP as source of truth | 1 source of truth, N compiled targets |
| Same prompt for every model | Per-model prompts that patch specific weaknesses |
| Manual research application to each repo | Single ingestion → compile → all targets updated |
| Claude-only | Multi-model with dynamic selection |
| No cost optimization | Tiered model selection by task complexity |
| Adversarial verify uses same model | Cross-model judge isolation by default |
| Platform binding mixed into module specs | Clean separation: corpus / compiler / bindings |

The meta-principle evolves from "patch weaknesses, don't scaffold strengths" to **"know which model's weaknesses you're patching, and compile the right patches for each."**
