# Project Continuity Layer

## Module Metadata

```yaml
module:
  title: Project Continuity Layer
  version: 1.0.1
  purpose: Append-only event ledger and enforcement substrate that maintains decision provenance and verified truth across multi-session, multi-agent research projects — STATE.md and SQLite are demoted to generated projections; every invariant is enforced below the model via hooks and pre-commit rather than by discipline
  topics: [event-ledger, append-only, decision-provenance, state-projection, write-gate, boot-handshake, deadcheck, compaction-ritual, multi-agent-continuity]
  contexts: [multi-session-research, optimization-projects, research-loop, cross-agent-state, project-continuity]
  difficulty: advanced
  related: [19_Memory_Architecture, 21_Knowledge_Accretion, 22_Semantic_Wiki_Search, 25_Entity_Relationship_Analysis, 26_Research_Loop_Protocol]
  added_in: "7.1"
  changelog:
    1.0.1:
      date: 2026-09-07
      driver: critic-review-2026-09-07
      changes:
        - Sev 2a: Added kf-project PATH prerequisite guard to CC Doc Boot Sequence
        - Sev 2c: Added SessionStart hook creation note for .kf_boot_pending — clarifies who creates the file and what absence means
        - Sev 3a: Added deadcheck paraphrase caveat (keyword overlap ≥30%; CLEAR is necessary but not sufficient)
        - Sev 3c: Added VARIANT ID uniqueness requirement and undefined-rebuild-behavior warning to CC Doc VARIANT comment
    1.0.0:
      date: 2026-09-08
      driver: kaggriculture-pilot-2026-09-08
      changes:
        - Initial module — validated in kaggriculture multi-session agricultural economics simulation pilot
        - Six event types (FACT, DECISION, DEADIDEA, DIRECTIVE, CHAMPION, VARIANT) with full schema
        - kf-project CLI primitives (append, rebuild, deadcheck, verify) — stdlib only, ~200 lines
        - Boot handshake protocol (SessionStart hook + .kf_boot_pending marker + echo confirmation)
        - Write-gate invariants (Gate 1 boot, Gate 2 variant-path) enforced via PreToolUse hook
        - Deadcheck protocol with keyword overlap (≥30%) and tag match algorithm
        - Projection/rebuild spec (STATE.md generated-only, SQLite tables, idempotent rebuild)
        - Compaction ritual (PreCompact hook — non-blocking, transcript backup, SessionStart recovery injection)
        - Two-phase deployment plan (Phase 1 now, Phase 2 after first multi-session run)
        - Known gaps documented (semantic near-duplicate detection, gate truth vs existence, CHAMPION merge conflicts)
```

---

## The Problem This Patches

Multi-session research projects fail to compound because their state substrate is fragile: STATE.md is hand-edited and diverges from reality; key decisions vanish after context compaction; two agents act on different mental models of what the current champion is; falsified strategies re-enter consideration because the anti-knowledge store isn't enforced.

The conventional fix is discipline — "always update STATE.md," "always record your decisions," "remember to check prior results." Discipline fails at scale, fails under context pressure, and fails when handing off between agents.

The Project Continuity Layer replaces discipline with enforcement. Truth lives in a git-committed JSONL ledger that can only be appended to. Projections (STATE.md, SQLite) are rebuilt from it, never edited. Writes to variant files are gated on ledger entries. Boot state is confirmed by hash echo before any action is allowed. Compaction is handled by a hook that backs up transcripts before they are destroyed.

---

## Core Architectural Principle

**Truth = the git-committed JSONL event log in `ledger/`. Everything else is a rebuildable projection.**

```yaml
architecture_principles:
  truth_layer:
    location: ledger/ directory (JSONL files)
    durability: git-committed after every append
    mutability: append-only — no line is ever edited or deleted
    supersession: new event with supersedes=<prior_id> field; old event remains readable
    audit_trail: the git commit log IS the audit trail — every ledger state is reachable by hash

  projection_layer:
    includes: [STATE.md, SQLite database]
    durability: regenerated on demand from ledger replay
    mutability: generated-only — hand-edits are rejected by pre-commit hook
    rebuild_command: kf-project rebuild
    idempotency: delete projections, run rebuild, get byte-identical output (modulo timestamp fields)

  enforcement_layer:
    boot_handshake: SessionStart hook + .kf_boot_pending + echo confirmation
    write_gate: PreToolUse hook blocks variant/ writes without open VARIANT event
    pre_commit: rejects STATE.md hand-edits; rejects variant/ commits without ledger entry
    deadcheck: CLI gate that exits nonzero on falsified pattern match

  failure_modes:
    fail_closed: intent violations → block (write-gate exits 2)
    fail_safe: hook load errors → allow (never permanently block the agent)
    rationale: |
      A hook that blocks legitimate work when it fails to load causes deadlock.
      An intent violation (writing without ledger entry) is caught and blocked
      even at the cost of friction — that friction is the point.
```

---

## Event Schema

The ledger contains six event types. One JSON object per line. Type field is always uppercase.

### FACT

```yaml
fact_schema:
  description: |
    Verified ground truth about the project — numeric values, configuration, definitions,
    measured parameters. One "live" value per key = newest non-superseded event.
    Re-derivation MUST append a superseding FACT with explicit source field.
  fields:
    id:
      type: string
      format: "fact-{uuid4-short}"
      required: true
    type:
      type: string
      value: "FACT"
      required: true
    key:
      type: string
      description: Identifier for the fact — kebab-case, e.g. "primary_fitness_metric", "promote_threshold"
      required: true
    value:
      type: any (string | number | boolean | list)
      required: true
    unit:
      type: string | null
      description: Unit of measurement when applicable — e.g. "games", "percent", "USD"
    source:
      type: string
      description: Where this value comes from — e.g. "measured:eval-run-42", "derived:fertilizer-model-v3", "manual:strategist"
      required: true
    verified_by:
      type: string | null
      description: Agent or process that verified the value, if distinct from source
    ts:
      type: ISO8601
      required: true
    supersedes:
      type: string (fact id) | null
      description: ID of the FACT event this supersedes; null if first assertion of this key
  live_value_rule: |
    For any given key, the live FACT is the newest event for that key that has not
    itself been superseded (i.e., no other FACT has supersedes=this_id).
    Rebuild computes live values by replaying all FACTs in timestamp order.
  example: |
    {"id":"fact-a1b2","type":"FACT","key":"promote_threshold","value":0.02,"unit":"fraction","source":"manual:strategist","verified_by":null,"ts":"2026-09-08T10:00:00Z","supersedes":null}
```

### DECISION

```yaml
decision_schema:
  description: |
    Primary record of what was tried, what evidence was collected, and whether the
    hypothesis held. The research artifact — future sessions read these to understand
    what the project has learned.
  fields:
    id:
      type: string
      format: "dec-{uuid4-short}"
      required: true
    type:
      type: string
      value: "DECISION"
      required: true
    hypothesis:
      type: string
      description: What approach was tested — specific enough that deadcheck can match against it
      required: true
    evidence:
      type: list<string>
      description: Numeric results, eval methodology, sample outputs, confidence intervals
      required: true
      min_length: 1
    verdict:
      type: string
      description: |
        Human-readable conclusion — e.g. "pass: +4.2% win rate vs champion, CI [2.1%, 6.3%]"
        or "falsified: -1.8% vs champion; soil model penalizes this approach under drought"
      required: true
    status:
      type: string
      enum: [live, superseded, falsified]
      required: true
      note: |
        "live" = hypothesis held, approach remains valid
        "falsified" = evidence contradicts hypothesis; triggers DEADIDEA derivation by rebuild
        "superseded" = replaced by a newer DECISION on the same question; old evidence preserved
    supersedes:
      type: string (decision id) | null
    killed_by:
      type: string (decision id) | null
      description: ID of the DECISION that provided the killing evidence, when status=falsified
    ts:
      type: ISO8601
      required: true
    author_agent:
      type: string
      description: Which agent recorded this decision — e.g. "executor", "strategist", "executor:session-4"
      required: true
  example: |
    {"id":"dec-c3d4","type":"DECISION","hypothesis":"Increase nitrogen dosage 20% above baseline","evidence":["win_rate: 0.48 vs champion 0.51","eval: 100-game paired","CI: [-5.1%, -0.9%] entirely negative"],"verdict":"falsified: reduces yield under drought stress conditions in eval function","status":"falsified","supersedes":null,"killed_by":null,"ts":"2026-09-08T14:30:00Z","author_agent":"executor"}
```

### DEADIDEA

```yaml
deadidea_schema:
  description: |
    Registry entry for a falsified approach. NOT hand-authored — derived only.
    Auto-derived by kf-project rebuild from DECISION events with status=falsified.
    May also be explicitly appended with explicit tag list by executor when
    a falsified direction warrants immediate deadcheck registration before rebuild runs.
    Tags are controlled vocabulary used by deadcheck matching.
  fields:
    id:
      type: string
      format: "dead-{uuid4-short}"
      required: true
    type:
      type: string
      value: "DEADIDEA"
      required: true
    pattern:
      type: string
      description: |
        Description of the falsified approach — specific enough for keyword matching.
        Derived from the hypothesis field of the killing DECISION.
      required: true
    tags:
      type: list<string>
      description: |
        Controlled vocabulary tags for deadcheck matching.
        Derived from key terms in hypothesis + verdict.
        Examples: ["nitrogen", "dosage-increase", "drought-sensitive"]
      required: true
      min_length: 1
    killing_evidence:
      type: string
      description: Summary of the evidence that falsified this approach (from DECISION.verdict)
      required: true
    decision_id:
      type: string
      description: ID of the DECISION event that produced this dead idea
      required: true
    ts:
      type: ISO8601
      required: true
  derivation_rule: |
    kf-project rebuild auto-derives DEADIDEA events from all DECISION events with
    status=falsified that do not already have a corresponding DEADIDEA event.
    Derivation is idempotent — running rebuild twice does not create duplicate DEADIDEAs.
  example: |
    {"id":"dead-e5f6","type":"DEADIDEA","pattern":"Increase nitrogen dosage 20% above baseline","tags":["nitrogen","dosage-increase","drought-sensitive","fertilizer"],"killing_evidence":"reduces yield under drought stress; CI [-5.1%,-0.9%] entirely negative over 100-game eval","decision_id":"dec-c3d4","ts":"2026-09-08T14:31:00Z"}
```

### DIRECTIVE

```yaml
directive_schema:
  description: |
    Work item issued by the strategist to the executor. Claiming a directive = appending
    a new DIRECTIVE event with the same id and status=claimed. Two-agent safe — no
    locking mechanism needed because appends are serialized through git commits.
  fields:
    id:
      type: string
      format: "dir-{uuid4-short}"
      required: true
    type:
      type: string
      value: "DIRECTIVE"
      required: true
    text:
      type: string
      description: What the executor is being asked to try — the hypothesis to test
      required: true
    status:
      type: string
      enum: [open, claimed, done, dropped]
      required: true
    claimed_by:
      type: string | null
      description: Agent identifier that claimed this directive; null when status=open
    depends_on:
      type: list<string>
      description: List of DIRECTIVE ids that must reach status=done before this one begins
      default: []
    ts:
      type: ISO8601
      required: true
  claiming_pattern: |
    Executor claims by appending a new DIRECTIVE event with:
      - same id as the original
      - status: "claimed"
      - claimed_by: "<executor_agent_id>"
    The live directive state = newest event for that id.
    This is two-agent safe: if both agents attempt to claim simultaneously,
    both appends commit, but the newest one wins as the live state.
  example: |
    {"id":"dir-g7h8","type":"DIRECTIVE","text":"Test phosphorus reduction 10% from baseline on sandy soil variants","status":"claimed","claimed_by":"executor","depends_on":[],"ts":"2026-09-08T15:00:00Z"}
```

### CHAMPION

```yaml
champion_schema:
  description: |
    Live pointer to the current best-performing variant on a given metric.
    The live champion = newest CHAMPION event per metric key.
    champion_ref points to the DECISION id of the approach — not a file path.
  fields:
    id:
      type: string
      format: "champ-{uuid4-short}"
      required: true
    type:
      type: string
      value: "CHAMPION"
      required: true
    champion_ref:
      type: string (DECISION id)
      description: The DECISION event id of the approach that holds the championship
      required: true
    metric:
      type: string
      description: |
        Which metric this championship covers — matches a FACT key.
        E.g. "primary_fitness_metric", "win_rate_vs_baseline"
      required: true
    value:
      type: number
      description: The metric value achieved by this champion
      required: true
    gate_state:
      type: object
      fields:
        promote_gate: enum [pass, fail, waived]
        holdout_gate: enum [pass, fail, waived]
        human_submission_gate: enum [pass, pending, not_required]
      required: true
    ts:
      type: ISO8601
      required: true
  live_champion_rule: |
    For each metric key, the live champion = newest CHAMPION event for that metric.
    Prior CHAMPION events are preserved (audit trail) but superseded by the newer one.
  example: |
    {"id":"champ-i9j0","type":"CHAMPION","champion_ref":"dec-k1l2","metric":"primary_fitness_metric","value":0.573,"gate_state":{"promote_gate":"pass","holdout_gate":"pass","human_submission_gate":"not_required"},"ts":"2026-09-08T18:00:00Z"}
```

### VARIANT

```yaml
variant_schema:
  description: |
    Record of a specific implementation attempt within a directive.
    decision_id is the enforcement anchor: the write-gate PreToolUse hook blocks ALL
    writes to variants/ directory until a VARIANT event with result_metric=pending exists.
    VARIANT events must be closed (result_metric set to actual value) after evaluation.
  fields:
    id:
      type: string
      format: "var-{uuid4-short}"
      required: true
    type:
      type: string
      value: "VARIANT"
      required: true
    directive_id:
      type: string (DIRECTIVE id)
      description: Which directive this variant implements
      required: true
    decision_id:
      type: string (DECISION id) | "pending"
      description: |
        MANDATORY. The DECISION event that records this variant's outcome.
        "pending" at open time; superseded by a new VARIANT event with actual
        decision_id once the DECISION is appended.
      required: true
    files:
      type: list<string>
      description: Paths of files written during this variant's implementation
      default: []
    result_metric:
      type: number | "pending" | "aborted"
      description: |
        "pending" = variant is open; implementation in progress
        <number> = evaluation complete; this is the primary fitness metric value
        "aborted" = implementation abandoned before evaluation
      required: true
    ts:
      type: ISO8601
      required: true
  open_variant_rule: |
    A VARIANT event with result_metric="pending" is "open".
    The write-gate checks for the existence of an open VARIANT event before
    allowing writes to the variants/ directory.
    Multiple open VARIANT events = error state; rebuild reports this.
  example_open: |
    {"id":"var-m3n4","type":"VARIANT","directive_id":"dir-g7h8","decision_id":"pending","files":[],"result_metric":"pending","ts":"2026-09-08T15:05:00Z"}
  example_closed: |
    {"id":"var-m3n4","type":"VARIANT","directive_id":"dir-g7h8","decision_id":"dec-o5p6","files":["variants/phosphorus-10pct-reduction-v1.py"],"result_metric":0.541,"ts":"2026-09-08T17:30:00Z"}
```

---

## Ledger Format and Storage

```yaml
ledger_storage:
  format: JSONL (one JSON object per line)
  location: ledger/ directory in project root
  file_layout:
    option_single: ledger/kf_events.jsonl — all event types in one file
    option_split:
      - ledger/decisions.jsonl
      - ledger/facts.jsonl
      - ledger/variants.jsonl
      - ledger/directives.jsonl
      - ledger/champions.jsonl
      - ledger/deadideas.jsonl
    note: Implementation choice per project; kf-project CLI abstracts over layout

  auto_commit:
    trigger: Every kf-project append call
    message_format: "ledger: {TYPE} {id} — {summary}"
    summary_derivation:
      FACT: first 50 chars of key + value
      DECISION: first 50 chars of hypothesis
      DEADIDEA: first 50 chars of pattern
      DIRECTIVE: first 50 chars of text
      CHAMPION: metric + value
      VARIANT: directive_id + result_metric
    purpose: |
      The git commit trail IS the audit trail.
      Every ledger state is reachable by hash.
      state_hash = git rev-parse --short HEAD

  state_hash:
    definition: git rev-parse --short HEAD on the ledger repository
    length: 8 characters
    use: |
      Shared state reference between strategist and executor.
      Included in every Orchestra handoff artifact.
      Boot handshake requires echo of correct state_hash.
```

---

## kf-project CLI Primitives

```yaml
kf_project_cli:
  implementation: Python stdlib only, ~200 lines, no external dependencies
  location: scripts/kf-project (executable script in project root)

  commands:
    append:
      syntax: kf-project append <TYPE> '<json>'
      behavior:
        1. Parse json argument
        2. Validate required fields for TYPE (see schema above)
        3. Validate status enum values if present
        4. Validate decision_id mandatory on VARIANT events
        5. Inject type field (uppercase) and ts field (ISO8601 now) if not provided
        6. Append validated JSON object as single line to ledger file
        7. git add ledger/ && git commit -m "ledger: {TYPE} {id} — {summary}"
      exit_codes:
        0: success
        1: validation failure (prints reason to stderr)
        2: git commit failure (prints git error to stderr)

    rebuild:
      syntax: kf-project rebuild
      behavior:
        1. Delete STATE.md and SQLite database
        2. Replay all JSONL lines in ledger/ in timestamp order
        3. Compute live FACTs (newest non-superseded per key)
        4. Compute live DECISIONs (status != superseded)
        5. Compute live DIRECTIVEs (newest event per id)
        6. Compute live CHAMPION (newest event per metric)
        7. Derive DEADIDEA events for any falsified DECISION without existing DEADIDEA
        8. Write STATE.md (generated projection — see Projection Spec)
        9. Write SQLite tables (one table per event type)
        10. Verify idempotency: re-run step 2-9 and compare output hashes
      exit_codes:
        0: success
        1: ledger parse error (prints offending line to stderr)
        2: idempotency check failed (prints diff to stderr)

    deadcheck:
      syntax: kf-project deadcheck "<idea description>"
      behavior:
        1. Load DEADIDEA projection from STATE.md or SQLite (rebuild if stale)
        2. Normalize input: lowercase, strip punctuation
        3. For each DEADIDEA entry:
           a. Keyword overlap check: count words from DEADIDEA.pattern that appear in input
              hit if count / total_pattern_words >= 0.30
           b. Tag match check: any DEADIDEA.tags keyword appears in input
              hit if any tag word found in input (exact lowercase match)
        4. On any hit:
           - Print: DEADCHECK HIT
           - Print: pattern, tags, killing_evidence, decision_id
           - exit 1
        5. On all clear:
           - Print: DEADCHECK CLEAR — no matching dead ideas
           - exit 0
      mandatory: |
        Callers MUST check exit code. exit 1 = proposal blocked.
        This is not advisory — the M26 loop protocol treats exit 1 as a hard stop.

    verify:
      syntax: kf-project verify
      behavior:
        1. Run git rev-parse --short HEAD
        2. Print: state_hash: <hash>
      exit_codes:
        0: success
        1: not a git repository or git unavailable

  validation_rules_per_type:
    FACT: [id, key, value, source, ts]
    DECISION: [id, hypothesis, evidence (min 1), verdict, status, ts, author_agent]
    DEADIDEA: [id, pattern, tags (min 1), killing_evidence, decision_id, ts]
    DIRECTIVE: [id, text, status, ts]
    CHAMPION: [id, champion_ref, metric, value, gate_state, ts]
    VARIANT: [id, directive_id, decision_id, result_metric, ts]
    status_enums:
      DECISION.status: [live, superseded, falsified]
      DIRECTIVE.status: [open, claimed, done, dropped]
      CHAMPION.gate_state.promote_gate: [pass, fail, waived]
      CHAMPION.gate_state.holdout_gate: [pass, fail, waived]
      CHAMPION.gate_state.human_submission_gate: [pass, pending, not_required]
```

---

## Boot Handshake Protocol

The boot handshake prevents the executor from acting on stale state — it forces explicit confirmation of the current ledger hash before any writes are permitted.

```yaml
boot_handshake:
  trigger: SessionStart hook runs at every new Claude Code session in a PCL project

  sessionstart_hook_actions:
    1. Run kf-project verify → get current state_hash
    2. Write .kf_boot_pending with content: expected_state_hash=<hash>
    3. Inject into session context:
       - state_hash: <hash>
       - live FACTs: full table (key → value, unit, source)
       - live DECISIONs: top-N by recency, each with hypothesis+evidence+verdict (NOT just IDs)
       - DEADIDEA list: full pattern+tags for every entry
       - current CHAMPION: metric + value + champion_ref + gate_state per metric key
       - open DIRECTIVEs: text + status + claimed_by per open/claimed directive
    4. Include instruction in injected context:
       "Echo the state_hash to confirm boot. Then rm .kf_boot_pending to clear the write-gate."

  agent_confirmation_sequence:
    1. Agent reads injected context
    2. Agent echoes: "Boot confirmed. state_hash: <hash>"
    3. Agent runs: rm .kf_boot_pending
    4. Write-gate is now cleared; normal operation resumes

  preToolUse_hook_behavior_during_boot:
    - ALL Write and Edit tool calls to paths matching variants/** are blocked
    - Error message returned: "Boot handshake pending. Echo state_hash `<hash>` then `rm .kf_boot_pending`."
    - Other tool calls (Read, Bash for non-write operations) are not blocked
    - Block exits immediately when .kf_boot_pending does not exist

  on_source_compact:
    description: |
      After context compaction, SessionStart fires again. The injected context
      uses the same schema, but emphasis shifts:
      - Inject full hypothesis+evidence+verdict for each DECISION (rationale survival)
      - Inject complete DEADIDEA list (pattern+tags+evidence) so deadcheck has full context
      - Do NOT inject file lists or path-based context — compaction erases file state anyway
    purpose: |
      Rationale (hypothesis+evidence+verdict) survives compaction.
      File state (what files exist, what was written) does not.
      The compacted agent can re-derive file state from ledger VARIANT events.

  failure_mode_boot_timeout:
    description: |
      Agent fails to echo state_hash (confused context, compaction artifact, etc.)
    resolution: |
      Write-gate remains active. Agent sees the block error message on next Write attempt.
      Block error includes expected hash. Agent can echo hash at that point and remove marker.
    rule: Boot confirmation is never auto-cleared by timeout — only by agent echo + rm.
```

---

## Write-Gate Invariants

The PreToolUse hook intercepts Write and Edit tool calls before they execute.

```yaml
write_gate:
  implementation: Claude Code PreToolUse hook (exit code determines allow/block)
  intercepted_tools: [Write, Edit]

  gate_1_boot:
    name: Boot handshake gate
    condition: .kf_boot_pending file exists in project root
    action: block
    exit_code: 2
    error_message: |
      "Boot handshake pending. Echo state_hash `{hash}` then `rm .kf_boot_pending`."
    fail_safe: |
      If hook fails to load or throws an exception: allow (exit 0).
      Never permanently block due to hook infrastructure failure.
    fail_closed: |
      If .kf_boot_pending exists and hash can be read: block (exit 2).
      This is an intent violation — the agent has not confirmed it knows current state.

  gate_2_variant_path:
    name: Variant write-without-ledger gate
    condition: |
      target path matches variants/** AND
      no open VARIANT event exists in ledger (result_metric=pending)
    action: block
    exit_code: 2
    error_message: |
      "No open VARIANT event. Create a ledger entry first: kf-project append VARIANT '{...}'"
    determination_of_open_variant: |
      Read STATE.md or query SQLite for VARIANT events with result_metric="pending".
      If STATE.md is absent (pre-first-rebuild), query the JSONL ledger directly.
      If ledger is also absent (fresh project, no appends yet): allow (no variant history to protect).
    fail_safe: |
      If hook fails to load: allow.
      If SQLite/STATE.md read fails: allow (fail-safe, not fail-closed on load errors).
    fail_closed: |
      If ledger is readable and no open VARIANT found: block.

  non_intercepted_paths:
    - ledger/ — kf-project CLI owns this; direct writes go through append command
    - STATE.md — pre-commit hook handles this (not PreToolUse)
    - .kf/ — internal PCL state; not gated
    - All paths outside variants/ — not gated by write-gate

  principle:
    fail_closed_on_intent: Intent violations (known bad state) → block
    fail_safe_on_load: Hook infrastructure failures → allow
    rationale: |
      A blocked intent violation is friction that prevents data corruption.
      A blocked agent due to hook failure is a deadlock that prevents all work.
      These have opposite costs — distinguish them.
```

---

## Deadcheck Protocol

```yaml
deadcheck_protocol:
  input: Free-text idea description (the proposed hypothesis or approach)
  source_data: DEADIDEA projection from STATE.md or SQLite

  normalization:
    input_prep: lowercase the input; strip punctuation; tokenize on whitespace
    pattern_prep: same normalization applied to DEADIDEA.pattern for comparison
    tags: already controlled vocabulary; compare as lowercase exact tokens

  match_algorithm:
    keyword_overlap:
      description: Fraction of pattern words that appear in the normalized input
      threshold: >= 0.30 (30% overlap triggers a hit)
      example: |
        pattern: "increase nitrogen dosage 20% above baseline" (5 content words)
        input: "try boosting nitrogen application above normal levels"
        overlap: nitrogen, above = 2/5 = 0.40 → HIT
    tag_match:
      description: Any DEADIDEA tag keyword appears in the normalized input
      threshold: any single tag match (not all tags required)
      example: |
        tags: ["nitrogen", "dosage-increase", "drought-sensitive"]
        input: "test higher nitrogen concentration in wet conditions"
        match: "nitrogen" found in input → HIT

  on_hit:
    output:
      - "DEADCHECK HIT"
      - pattern: <DEADIDEA.pattern>
      - tags: <DEADIDEA.tags>
      - killing_decision: <DEADIDEA.decision_id>
      - evidence: <DEADIDEA.killing_evidence>
    exit_code: 1
    caller_action: |
      M26 loop blocks iteration.
      Push findings artifact with deadcheck_hit=true and deadcheck_detail.
      Do not append VARIANT or DECISION.

  on_clear:
    output: "DEADCHECK CLEAR — no matching dead ideas found"
    exit_code: 0
    caller_action: Proceed to VARIANT event append and implementation

  mandatory_usage:
    when: Before every new VARIANT in the M26 loop
    how: kf-project deadcheck "<proposed approach>"
    not_advisory: |
      exit 1 from deadcheck is a hard stop. The loop protocol (M26) does not provide
      an override path for the executor — only the strategist can issue a modified directive
      that produces a different (clear-passing) hypothesis.
    strategist_override_path: |
      Strategist may issue a new directive with a deliberately reframed hypothesis
      that addresses why the dead idea's conditions don't apply to the new context.
      Executor runs deadcheck on the reframed text. If it clears, proceed.
      If it still hits, push findings to strategist — do not force past the gate.

  known_limitation_phase_1: |
    Deadcheck uses keyword overlap and tag matching only.
    Semantic near-duplicates that avoid the pattern's exact vocabulary can evade detection.
    Example: "reduce soil nitrogen consumption" describes the same failing approach as
    "increase nitrogen dosage" under the evaluation function, but keyword overlap is near zero.
    Phase 2 fix: semantic embedding search via M22 (see Two-Phase Deployment section).
```

---

## Projection and Rebuild Spec

```yaml
projection_spec:
  state_md:
    description: Human-readable generated summary of current ledger state
    header_banner: |
      <!-- GENERATED — DO NOT EDIT. Source: ledger/. Rebuild: kf-project rebuild. -->
    sections:
      state_hash: Current git HEAD short SHA
      facts_table: Markdown table of live FACTs (key | value | unit | source)
      champions: Per-metric champion (metric | value | decision_ref | gates)
      live_decisions: |
        Top-N live DECISIONs by recency, each showing:
        - hypothesis (one line)
        - evidence (bulleted)
        - verdict (one line)
        - status: live
      dead_ideas: |
        All DEADIDEA entries:
        - pattern (one line)
        - tags (inline list)
        - killing_evidence (one line)
        - decision_id (reference)
      open_directives: |
        All DIRECTIVEs with status open or claimed:
        - text
        - status
        - claimed_by (if claimed)
    generated_only_enforcement:
      pre_commit_check: |
        Pre-commit hook reads STATE.md diff. If diff exists and the GENERATED banner
        is present in the original file but the diff touches lines below the banner,
        the commit is rejected with:
        "STATE.md is generated — do not edit. Run kf-project rebuild instead."
      exception: |
        If STATE.md does not exist in the commit (new project or deleted for rebuild),
        the pre-commit check is skipped for that file.

  sqlite_projection:
    description: Queryable projection of ledger for analysis and deadcheck
    tables:
      facts: (id, key, value, unit, source, verified_by, ts, supersedes, is_live)
      decisions: (id, hypothesis, evidence_json, verdict, status, supersedes, killed_by, ts, author_agent)
      deadideas: (id, pattern, tags_json, killing_evidence, decision_id, ts)
      directives: (id, text, status, claimed_by, depends_on_json, ts, is_current)
      champions: (id, champion_ref, metric, value, gate_state_json, ts, is_current)
      variants: (id, directive_id, decision_id, files_json, result_metric, ts, is_open)
    rebuild_behavior: |
      Drop all tables. Re-create schema. Replay all JSONL lines in timestamp order.
      Compute is_live, is_current, is_open flags during replay.
    idempotency_check: |
      After rebuild, hash STATE.md and SQLite table dumps.
      Run rebuild again. Compare hashes.
      If they differ (modulo timestamp fields), exit 2 with diff.

  idempotency_definition:
    byte_identical_modulo: |
      STATE.md hash is identical if the ledger has not changed between two rebuilds.
      SQLite table dumps are byte-identical modulo row insertion order
      (rows inserted in timestamp order — deterministic).
    timestamp_fields_excluded: |
      The rebuild timestamp (time rebuild was run) is excluded from idempotency hash.
      All ledger-derived timestamps (event ts fields) are included.
```

---

## Compaction Ritual

The compaction ritual prevents decision loss when Claude's context window fills and the compaction summarizer runs.

```yaml
compaction_ritual:
  trigger: Claude Code PreCompact hook — fires before context compaction begins
  
  critical_constraint:
    rule: NEVER exit nonzero from PreCompact
    reason: |
      A nonzero exit from PreCompact causes Claude to retry compaction indefinitely,
      or blocks the session at the context wall — a documented deadlock pattern.
      All operations in PreCompact must be wrapped in try/except; on any error,
      log to stderr and exit 0.
    verified: kaggriculture pilot — any hook failure at the context wall causes session deadlock

  hook_actions:
    1. Back up raw transcript turns to SQLite transcript_backup table:
       - table: transcript_backup
       - fields: (session_id, turn_number, role, content, ts, compaction_session)
       - source: current session transcript (all turns not yet backed up)
       - on_failure: log to stderr; exit 0 (transcript backup is best-effort)

    2. Write .compact_marker:
       - content: compaction_ts=<ISO8601>
       - purpose: SessionStart hook detects this on next session and adjusts injection

    3. On any exception: log to stderr; exit 0 (never block)

  sessionstart_recovery_after_compaction:
    trigger: SessionStart hook detects .compact_marker
    injection_adjustments:
      - Inject full hypothesis+evidence+verdict for each live DECISION (not just titles)
      - Inject complete DEADIDEA list with pattern+tags+evidence
      - Inject current CHAMPION per metric with gate_state
      - Inject open DIRECTIVEs with full text
      - DO NOT inject file lists or working directory state (compaction erases file context)
    rationale: |
      Rationale (hypothesis+evidence+verdict) is what the agent needs to reason about
      prior work. File state can be re-derived from VARIANT events. Injecting file lists
      post-compaction produces false confidence — the agent thinks it knows what files
      exist but the compacted context has no grounding for those claims.
    then: Normal boot handshake (state_hash injection + .kf_boot_pending + echo confirmation)

  transcript_backup_schema:
    table: transcript_backup
    location: project.sqlite (same database as projection tables)
    fields:
      id: integer primary key autoincrement
      session_id: text (UUID for this session)
      turn_number: integer
      role: text (user | assistant)
      content: text
      ts: text (ISO8601)
      compaction_session: integer (increments each time .compact_marker fires)
    retention: permanent (never pruned by PCL — user manages)
    purpose: |
      Raw transcript backup for post-hoc analysis.
      NOT used for live session injection (that uses the ledger, not transcripts).
      Provides audit trail for understanding how decisions developed.
```

---

## Pre-Commit Hooks

```yaml
pre_commit_hooks:
  hook_1_state_md_protection:
    trigger: git commit containing changes to STATE.md
    check: |
      Does the staged STATE.md diff touch lines below the GENERATED banner?
    on_yes:
      reject: true
      message: "STATE.md is generated — do not edit. Run kf-project rebuild instead."
    on_no: allow
    exception: STATE.md is being created fresh (new file) — allow

  hook_2_variant_ledger_coupling:
    trigger: git commit containing additions to variants/ directory
    check: |
      Does the same commit also contain an append to the ledger JSONL file(s)?
    on_no:
      reject: true
      message: "Variant file committed without ledger entry. Run kf-project append VARIANT first."
    on_yes: allow
    exception: |
      If variants/ file is being deleted or renamed (not new content), allow.
      If this is the initial project setup commit (no ledger yet exists), allow.
    note: |
      This hook enforces that every variant file write is traceable to a ledger event.
      It catches the case where the write-gate (PreToolUse) was bypassed or unavailable.

  installation:
    command: kf-project install-hooks
    locations: .git/hooks/pre-commit (chains from existing hooks if present)
```

---

## Two-Phase Deployment

```yaml
deployment:
  phase_1:
    description: Ship now — minimal substrate for the research loop to compound
    components:
      - JSONL ledger (six event types, kf-project CLI)
      - kf-project append / rebuild / deadcheck / verify commands
      - SessionStart hook (state_hash + live state injection + .kf_boot_pending)
      - PreToolUse hook (Gate 1 boot + Gate 2 variant-path)
      - PreCompact hook (transcript backup + .compact_marker)
      - Pre-commit hooks (STATE.md protection + variant-ledger coupling)
      - STATE.md demotion (generated-only, GENERATED banner)
      - Backfill: existing decisions and facts from working docs → ledger events
    deliverable: One complete multi-session research loop with no discipline dependencies

  phase_2:
    description: After first full multi-session run with Phase 1 substrate
    gating_condition: |
      At least one champion promotion has completed with holdout gate pass.
      At least two sessions have run with compaction ritual firing at least once.
    components:
      - Semantic near-duplicate detection for dead ideas via Module 22 embeddings
      - CHAMPION merge conflict detection (surface git conflicts as human-review prompts)
      - Entity-scoped metadata filter via Module 25 ERA on VARIANT file entities
    rationale: |
      Phase 2 components add precision — they catch evasive dead ideas and
      cross-entity champion conflicts. They require a working ledger with real data
      to calibrate. Shipping them before Phase 1 data exists = premature optimization.

  backfill_procedure:
    when: Phase 1 deployment into a project with existing decisions/facts in prose docs
    steps:
      1. Run kf-project verify — confirm git is initialized in project
      2. For each known fact in prose docs: kf-project append FACT '{"key":...,"value":...,"source":"backfill:manual"}'
      3. For each known decision: kf-project append DECISION '{"hypothesis":...,"evidence":[...],"verdict":...,"status":"live"/"falsified",...}'
      4. For each falsified decision: kf-project append DEADIDEA (or let rebuild derive it)
      5. kf-project rebuild
      6. Verify STATE.md reflects all backfilled state
    note: |
      Backfill timestamps use the best-known historical date (from prose docs or git log).
      If unknown, use backfill date with source="backfill:date-uncertain".
```

---

## Known Gaps (Log, Don't Solve in Phase 1)

```yaml
known_gaps:
  semantic_near_duplicates:
    description: |
      Deadcheck keyword overlap (≥30%) and tag matching fail on semantically equivalent
      hypotheses that use different surface vocabulary. A proposal to "reduce soil
      nitrogen consumption" evades the dead idea for "increase nitrogen dosage" even
      though both approaches fail under the same evaluation function condition.
    phase_2_fix: Semantic embedding search via Module 22 against DEADIDEA corpus
    phase_1_mitigation: |
      Tag list on DEADIDEA events should include synonyms and related terms.
      Executor should run deadcheck against multiple phrasings when in doubt.

  gate_checks_existence_not_truth:
    description: |
      The write-gate (PreToolUse Gate 2) checks that an open VARIANT event exists —
      it does not verify that the VARIANT's directive_id references a valid DIRECTIVE,
      or that the DIRECTIVE was issued by the strategist rather than self-issued.
    implication: |
      A sufficiently motivated agent can create its own DIRECTIVE and VARIANT events
      without strategist input and bypass the intent of the loop protocol.
    mitigation: |
      The protocol is designed for cooperative agents (strategist + executor roles
      with distinct trust scopes). If adversarial agent behavior is a concern,
      add a signature field to DIRECTIVE events and verify at VARIANT open time.
      This is Phase 2+ work.

  champion_merge_conflicts:
    description: |
      If both strategist and executor append CHAMPION events for the same metric
      in a narrow time window (e.g., during a handoff race), git may produce a
      merge conflict on the ledger JSONL file.
    handling: |
      This is a feature, not a bug. The merge conflict forces human review of
      which champion event is authoritative. Do not auto-resolve.
    resolution_procedure: |
      Human reads both conflicting CHAMPION events. Keeps the one with higher metric
      value (or whichever passes both gates). Removes the conflict markers.
      Appends a new CHAMPION event as the authoritative resolution.
      Runs kf-project rebuild.
```

---

## Integration Points

### Module 19 (Memory Architecture)
PCL events feed the four-tier memory model. FACT and DECISION events accrete to Tier 0 wiki when they meet M21 thresholds. PreCompact hook backs up raw transcripts to SQLite (Tier 3 substrate). SessionStart injection is the PCL's interface to the session context window.

### Module 21 (Knowledge Accretion)
Falsified DECISION events with strong evidence are ACCRETION_CANDIDATEs for anti-knowledge entries (novelty_type: anti_pattern). Champion-producing DECISION events with holdout gate pass and ≥3 replication runs are accretion candidates for methodology entries (novelty_type: validated_pattern).

### Module 22 (Semantic Wiki Search)
Phase 2: deadcheck delegates near-duplicate matching to M22 embedding search over the DEADIDEA corpus, after Phase 1 keyword/tag matching returns clear. Entity-scoped metadata filter from M25 narrows the search scope.

### Module 25 (Entity Relationship Analysis)
Phase 2: ERA runs on VARIANT files[] paths at each iteration. Entities in variants (crop type, dosage schedule, soil model variant name) become metadata filter keys for M22 DEADIDEA retrieval. Prevents false clears where the dead idea applies to the same entities but the keyword overlap is low.

### Module 26 (Research Loop Protocol)
M26 is the consumer of M27's substrate. Every loop operation (pre-iteration deadcheck, DIRECTIVE claiming, VARIANT gating, DECISION recording, CHAMPION promotion, rebuild, boot handshake) goes through M27 primitives. M27 defines the what (event schema, CLI, hooks); M26 defines the when and why (loop structure, gate criteria, handoff format).

---

## Anti-Patterns

| Anti-Pattern | Consequence | Correct Approach |
|---|---|---|
| Hand-editing STATE.md | Next rebuild overwrites the edit; divergence between human intent and ledger truth | Edit the ledger (via kf-project append); STATE.md is generated |
| Skipping rebuild after DECISION | DEADIDEA registry not updated; next deadcheck misses the new dead idea | Step 9 rebuild is mandatory after every DECISION append |
| Writing DEADIDEA events manually | Creates dead ideas without a backing DECISION; evidence chain broken | Let rebuild derive DEADIDEA from falsified DECISION, or append with explicit decision_id |
| Appending VARIANT without decision_id placeholder | Violates schema; rebuild errors; write-gate state indeterminate | Always include decision_id: "pending" at open time |
| Exiting PreCompact hook with nonzero | Session deadlock at context wall | PreCompact MUST always exit 0; wrap everything in try/except |
| Treating deadcheck as advisory | Falsified strategies re-enter; iteration budget wasted | Check exit code; exit 1 = hard stop; no executor override |
| Multiple open VARIANT events | Ambiguous write-gate state; rebuild reports error | Close each VARIANT (append new event with actual result_metric) before opening next |

---

## Related Modules

- `19_Memory_Architecture.md` — four-tier memory; PCL events feed Tier 0 (accretion) and Tier 3 (transcript backup)
- `21_Knowledge_Accretion.md` — falsified DECISIONs as anti-knowledge; champion DECISIONs as validated patterns
- `22_Semantic_Wiki_Search.md` — Phase 2 semantic deadcheck against DEADIDEA corpus
- `25_Entity_Relationship_Analysis.md` — Phase 2 entity-scoped metadata filter from VARIANT files
- `26_Research_Loop_Protocol.md` — the consumer protocol; M27 is its substrate

---

## CC Doc

# Module 27: Project Continuity Layer — Execution Protocol
**Apply when:** Working in a project that uses the PCL substrate (ledger/ directory present, kf-project CLI available). This covers both executor and strategist-side verification tasks.

The PCL is the enforcement substrate for multi-session research projects. Truth = the ledger. STATE.md and SQLite are generated projections. Never edit them directly.

## Boot Sequence

Prerequisite: `kf-project` must be on PATH (symlinked from the project root to `/usr/local/bin/` or `/opt/homebrew/bin/`). Verify with `which kf-project`; if missing, install from the project root per the repo README before proceeding.

The SessionStart hook creates `.kf_boot_pending` on every session start, writing the state_hash as its content. If the file is absent after session start, the hook is not installed or failed — variant writes are unguarded. Verify hook installation before proceeding.

SessionStart injects: `state_hash`, live FACTs, live DECISIONs (hypothesis+evidence+verdict), DEADIDEA list, CHAMPION pointer(s), open DIRECTIVEs.

```bash
# Step 1: Confirm you have the state_hash from injected context
# Step 2: Echo it
echo "Boot confirmed. state_hash: <hash from context>"
# Step 3: Clear the write-gate
rm .kf_boot_pending
# Write-gate is now clear. Variant writes are permitted.
```

Until `.kf_boot_pending` is removed, all Write/Edit calls to `variants/` are blocked with:
`"Boot handshake pending. Echo state_hash <hash> then rm .kf_boot_pending."`

## Deadcheck (mandatory before any new variant)

```bash
kf-project deadcheck "<proposed approach description>"
# exit 0 = CLEAR — proceed
# exit 1 = HIT — output includes pattern, tags, killing_decision, evidence — STOP
```

Check the exit code. exit 1 is a hard stop. Report the hit to the strategist.

Caveat: deadcheck uses keyword overlap (≥30%) — paraphrased or conceptually equivalent ideas can clear the gate. CLEAR is necessary but not sufficient evidence of novelty.

## Append Commands (one JSON object, all on one line)

```bash
# FACT — record a verified ground truth value
kf-project append FACT '{"id":"fact-xxxx","key":"promote_threshold","value":0.02,"unit":"fraction","source":"manual:strategist"}'

# DECISION — record what was tried and what evidence showed
kf-project append DECISION '{"id":"dec-xxxx","hypothesis":"Test phosphorus reduction 10%","evidence":["win_rate: 0.541 vs 0.520 champion","eval: 100-game paired","CI: [1.1%,3.1%] positive"],"verdict":"pass: +2.1% above promote threshold","status":"live","author_agent":"executor"}'

# VARIANT — open before any writes to variants/; close after evaluation
# IDs must be unique per ledger — check ledger before appending; kf-project does not
# validate uniqueness. Duplicate IDs produce undefined rebuild behavior (last-event wins).
# Open:
kf-project append VARIANT '{"id":"var-xxxx","directive_id":"dir-yyyy","decision_id":"pending","files":[],"result_metric":"pending"}'
# Close (supersedes open event with actual values):
kf-project append VARIANT '{"id":"var-xxxx","directive_id":"dir-yyyy","decision_id":"dec-xxxx","files":["variants/phosphorus-10pct-v1.py"],"result_metric":0.541}'

# DIRECTIVE — claim a directive from strategist (status=claimed)
kf-project append DIRECTIVE '{"id":"dir-yyyy","text":"Test phosphorus reduction 10% from baseline on sandy soil variants","status":"claimed","claimed_by":"executor","depends_on":[]}'

# CHAMPION — only after strategist confirmation of promotion
kf-project append CHAMPION '{"id":"champ-xxxx","champion_ref":"dec-xxxx","metric":"primary_fitness_metric","value":0.541,"gate_state":{"promote_gate":"pass","holdout_gate":"pass","human_submission_gate":"not_required"}}'

# DEADIDEA — normally auto-derived by rebuild; explicit append when needed immediately
kf-project append DEADIDEA '{"id":"dead-xxxx","pattern":"Increase nitrogen dosage above baseline","tags":["nitrogen","dosage-increase","drought-sensitive"],"killing_evidence":"reduces yield under drought; CI [-5.1%,-0.9%]","decision_id":"dec-yyyy"}'
```

## Rebuild and Verify

```bash
# Rebuild STATE.md + SQLite from ledger (mandatory after every DECISION append)
kf-project rebuild

# Check current state_hash (include this in every Orchestra findings artifact)
kf-project verify
```

## Write-Gate Error Messages

| Message | Meaning | Resolution |
|---|---|---|
| `"Boot handshake pending. Echo state_hash <hash> then rm .kf_boot_pending."` | Boot incomplete | Echo the hash, then `rm .kf_boot_pending` |
| `"No open VARIANT event. Create a ledger entry first: kf-project append VARIANT '{...}'"` | Writing to variants/ without open ledger entry | Run the VARIANT append command first |

## Post-Compaction Session

After context compaction, SessionStart re-injects decision rationale (hypothesis+evidence+verdict) and the full DEADIDEA list. File state is NOT re-injected — re-derive it from VARIANT events if needed. Boot handshake still runs — echo state_hash and rm .kf_boot_pending before acting.

## Never

- Edit STATE.md directly — it is generated by `kf-project rebuild`
- Skip `kf-project rebuild` after a DECISION append
- Treat deadcheck as advisory — exit 1 is a hard stop
- Exit PreCompact hook with nonzero — wrap everything in try/except, always exit 0
- Append a VARIANT event without `decision_id` field (use "pending" as placeholder)
- Promote to champion without strategist confirmation in directive artifact
