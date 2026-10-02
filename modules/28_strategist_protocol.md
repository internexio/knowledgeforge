# Strategist Protocol

## Module Metadata

```yaml
module:
  title: Strategist Protocol
  version: 1.0.0
  purpose: Formal boot sequence, directive issuance format, receive-and-decide flow, champion confirmation gate, and hash-mismatch recovery for the strategist (chat agent) in the M26 two-agent research loop — patches the gap where M26/M27 document only the executor side with a structured CC Doc
  topics: [two-agent-topology, strategist-protocol, directive-issuance, champion-confirmation, hash-mismatch-recovery, research-loop]
  contexts: [multi-session-research, optimization-projects, two-agent-coordination, research-loop]
  difficulty: advanced
  related: [26_Research_Loop_Protocol, 27_Project_Continuity_Layer, 19_Memory_Architecture, 21_Knowledge_Accretion]
  added_in: "7.1"
  changelog:
    1.0.0:
      date: 2026-09-14
      driver: nightwatch-5m26
      changes:
        - Initial module — fills the strategist-side gap identified in nightwatch-4q4g post-ship review (Sev 3b)
        - Boot sequence for chat agent (no SessionStart hook injection — self-orient from prior findings artifacts and STATE.md)
        - Directive issuance format with expected_ledger_hash, directive_text, directive_id, promote_confirmed
        - Receive-and-decide flow (Q1/Q2/Q3 interpretation, four decision paths)
        - Champion confirmation gate (verification checklist, confirmation directive format, rejection format)
        - Hash mismatch recovery (re-issue with executor-reported actual hash)
        - Deadcheck hit recovery (abandon vs reframe, reframe conditions)
        - Never list and anti-patterns table
        - CC Doc section (~100 lines) for use as runtime quick-reference
```

---

## The Problem This Patches

M26 defines the full research loop protocol and M27 provides the enforcement substrate. Both modules include CC Doc sections — but both are written from the **executor's perspective** (Claude Code with filesystem access). M26's CC Doc covers the executor boot sequence, iteration commands, and post-iteration checklist. M27's CC Doc covers "executor and strategist-side verification tasks" but devotes only a few sentences to the strategist.

A strategist running the two-agent research loop has no formal protocol. They must infer their role from the M26 theory section — which is comprehensive but not a checklist. This leads to recurring failures:

- **Stale hash in directive** — strategist uses a remembered hash rather than the one in the latest findings artifact; executor blocks at step_2 every iteration
- **Inline state in directive** — strategist pastes STATE.md content or DECISION bodies into the artifact body; creates a second source of truth that drifts on the next rebuild
- **Missed champion gate** — strategist issues `promote_confirmed: true` without reviewing both gates; overfit promotion slips through
- **Hash mismatch recovery loop** — strategist doesn't know how to re-issue; both agents stall waiting for each other

M28 patches this by providing the strategist with the same level of CC Doc coverage that the executor has in M26.

---

## Roles and Responsibilities Recap

The strategist is the **decision maker**, not the implementer. All writes to the ledger and variants directory go through the executor.

```yaml
strategist_does:
  - Approve hypotheses before executor begins implementation
  - Issue DIRECTIVE artifacts to the executor via Orchestra
  - Interpret findings artifacts and decide direction (approve/redirect/reject/promote)
  - Confirm champion promotion (or reject the recommendation)
  - Issue holdout gate waivers and human submission gate approvals
  - Decide when to abandon a dead direction vs. reframe it

strategist_does_not_do:
  - Write to variant files directly
  - Append ledger events (VARIANT, DECISION, CHAMPION, DIRECTIVE, FACT, DEADIDEA)
  - Run kf-project commands (no filesystem access in canonical chat setup)
  - Run deadcheck directly — executor runs it; strategist reads the result
  - Self-promote a variant to champion
  - Issue new research directions to itself — loop is sequential; one active directive at a time

state_reference:
  primary: ledger_head_hash field from most recent executor findings artifact
  secondary: STATE.md (if accessible via shared filesystem or uploaded to session context)
  never: memory or prior session context (these drift after context compaction)
```

---

## Boot Sequence

The strategist is in a chat session. The SessionStart hook is an executor-side mechanism and does NOT fire for the strategist. The strategist must self-orient at the start of every session.

### Step 1: Locate state_hash

```
Priority order (first match wins):

1. Most recent executor findings artifact in this conversation
   → read the `ledger_head_hash` field

2. STATE.md uploaded or accessible in session context
   → read the `state_hash` line at the top of the STATE.md header

3. Neither available (first session or fresh context)
   → Ask executor: "Please run `kf-project verify` and report the output before I issue a directive."
   → Do NOT issue a directive until you have a confirmed hash from the executor.
```

### Step 2: Orient on current state

Before issuing any directive, know:

| What | Source | Why |
|---|---|---|
| `state_hash` | Latest findings artifact or STATE.md | Goes into `expected_ledger_hash` of your first directive |
| Current CHAMPION | STATE.md → Champions section | Baseline to beat; gate thresholds reference it |
| Open DIRECTIVEs | STATE.md → Open Directives section | Are you issuing redundant work? |
| DEADIDEA list | STATE.md → Dead Ideas section | Know what's already falsified before proposing directions |
| live FACTs | STATE.md → Facts table | Promote threshold, eval_game_count, primary fitness metric |

### Step 3: Announce starting point

State aloud (for conversation traceability):

```
Session start: state_hash is `<hash>`
Current champion: <metric value> on <metric key> [or: no champion yet]
Open directives: <any> [or: none]
```

---

## Directive Issuance

A directive is a push_artifact to the executor's Orchestra inbox. Issue **one at a time** — the loop is sequential.

### Format

```yaml
orchestra_push:
  type: research_directive
  fields:
    expected_ledger_hash: <ledger_head_hash from most recent findings artifact>
    directive_text: "<hypothesis to test — specific enough for deadcheck to evaluate>"
    directive_id: "new"          # "new" for a new direction; existing dir-xxxx to reclaim a dropped one
    promote_confirmed: null      # null = no promotion decision; true = confirm; false = reject
  optional_fields:
    holdout_gate_waiver: true    # include only when waiving holdout gate; explain in directive_text
    human_submission_gate_approval: true  # include only when authorizing external submission
```

### Rules

- `expected_ledger_hash` **must** come from the most recent executor findings artifact — never from memory, never from an earlier artifact in the session, never guessed
- If you haven't received a findings artifact in this session yet: ask executor for `kf-project verify` output first
- `directive_text` must be specific enough for deadcheck keyword matching. "Try something different with nitrogen" is too vague; "Reduce nitrogen application frequency from daily to every-3-days on sandy soil variants" is actionable
- Never include STATE.md content, DECISION bodies, or FACT values in the directive body — reference ledger IDs only; strategist reads STATE.md separately for context
- Use `directive_id: "new"` unless reclaiming a specific previously-dropped directive from the ledger

---

## Receive-and-Decide Flow

When executor pushes a findings artifact:

### 1. Extract mandatory fields

```
ledger_head_hash  →  save this; it becomes expected_ledger_hash in your NEXT directive
directive_id      →  confirm this matches the directive you issued
findings          →  human-readable result summary
questions         →  Q1/Q2/Q3 open questions from executor
promote_recommended  →  boolean (if present)
deadcheck_hit       →  boolean (if present)
```

### 2. Answer Q1/Q2/Q3 (always read, even if not explicitly asked)

| Question | Purpose | How to use it |
|---|---|---|
| Q1: What mechanism drove this result? | Understand causality, not just metric delta | Informs whether the approach generalizes or is environment-specific |
| Q2: Any interaction with previously tested factors? | Surface compounding effects | Determines whether to follow up on the interaction or isolate further |
| Q3: What direction to explore next? | Executor's hypothesis for next iteration | Accept, redirect, or override with your own direction |

### 3. Decide — four paths

**Approve** — evidence is clear; continue or follow executor's Q3 suggestion:
```yaml
expected_ledger_hash: <hash from this findings artifact>
directive_text: "<next hypothesis>"
directive_id: "new"
promote_confirmed: null
```

**Redirect** — evidence is clear; you want a different direction than Q3:
```yaml
expected_ledger_hash: <hash from this findings artifact>
directive_text: "<your hypothesis, different from executor's Q3>"
directive_id: "new"
promote_confirmed: null
```

**Reject / Re-run** — insufficient evidence; ask for a modified evaluation:
```yaml
expected_ledger_hash: <hash from this findings artifact>
directive_text: "<same hypothesis with modified eval parameters — e.g. increase N from 50 to 100 games>"
directive_id: "new"
promote_confirmed: null
```

**Promote** — `promote_recommended: true` and you agree → use Champion Confirmation Gate below.

---

## Champion Confirmation Gate

Triggered when executor reports `promote_recommended: true`.

### Verification checklist (run before issuing confirmation)

```
[ ] 1. Read findings.verdict — does the metric improvement make sense given the approach?
[ ] 2. Check promote_gate — must be "pass" (or explicitly waived)
[ ] 3. Check holdout_gate — must be "pass" (or explicitly waived with reason)
[ ] 4. If holdout_gate=fail: is the failure acceptable (e.g., holdout set is unrepresentative)?
        → Only waive if you have a specific reason to believe the holdout gate is wrong
[ ] 5. Check human_submission_gate — is this a project that requires external submission approval?
        → If yes, decide now whether you're also approving submission
```

### Confirmation directive (both gates pass)

```yaml
expected_ledger_hash: <hash from promote-recommendation findings artifact>
directive_text: "Promote decision <decision_id> to champion. Promote gate: pass. Holdout gate: pass. Confirm promotion."
directive_id: "new"
promote_confirmed: true
```

### Confirmation with holdout gate waiver

```yaml
expected_ledger_hash: <hash from findings>
directive_text: "Promote decision <decision_id>. Holdout gate: fail — waived because <specific reason>."
directive_id: "new"
promote_confirmed: true
holdout_gate_waiver: true
```

### Rejection (you disagree with promotion recommendation)

```yaml
expected_ledger_hash: <hash from findings>
directive_text: "Reject promotion. Reason: <why the evidence doesn't support promotion>. Next: <new direction or request for more evidence>."
directive_id: "new"
promote_confirmed: false
```

---

## Hash Mismatch Recovery

The executor reports: actual hash ≠ `expected_ledger_hash` in your directive.

**This means the ledger advanced after you prepared the directive** (e.g., executor ran rebuild mid-session, a prior directive was claimed, or another agent appended events).

```
1. Read executor's report — they will state the actual current hash
2. Read what events advanced the ledger (executor should describe them)
3. Confirm the new ledger state is still consistent with your intended direction
4. Re-issue directive with the updated hash:
```

```yaml
expected_ledger_hash: <actual hash reported by executor>
directive_text: "<same directive text, or updated if the new events change your direction>"
directive_id: "new"
promote_confirmed: null
```

Do NOT re-issue the same directive with the same stale hash — it will mismatch again.
Do NOT ask the executor to "just use" your stale hash — they are correctly blocking.

---

## Deadcheck Hit Recovery

The executor reports `deadcheck_hit: true` with `deadcheck_detail`.

### Read the detail

```yaml
deadcheck_detail:
  pattern: "<the falsified approach text>"
  tags: ["<tag1>", "<tag2>"]
  killing_decision: "<decision_id>"
  evidence: "<what evidence falsified it>"
```

### Decide

**Abandon** — the direction is genuinely falsified for this project context:
```
Issue a new directive with a completely different hypothesis direction.
```

**Reframe** — you believe the dead idea's failure conditions don't apply here:
```
Issue a new directive with a reformulated hypothesis text that:
  (a) explicitly addresses why the dead idea's failure condition doesn't apply
  (b) is phrased differently enough to clear deadcheck keyword overlap
The executor runs deadcheck on the reframed text. If it still hits: abandon.
```

**Never bypass deadcheck** by issuing a special flag or authority override — the gate is enforced at the executor side. The only path past it is a hypothesis that genuinely clears deadcheck.

---

## Never

- Issue a directive without `expected_ledger_hash` — executor cannot verify state
- Use a hash from memory, a prior session, or a prior artifact in this session — always use the hash from the **most recent** findings artifact
- Include STATE.md content, FACT values, or DECISION bodies in the directive body — reference ledger IDs only; state belongs in the ledger, not in handoff artifacts
- Issue two concurrent directives to the same executor — the loop is sequential; one active directive at a time
- Self-promote to champion (`promote_confirmed: true` without executor's `promote_recommended: true` first)
- Bypass deadcheck through reframing while ignoring the dead idea's evidence — the reframe must address the failure condition, not just change the vocabulary
- Re-issue a directive with a stale hash — always re-issue with the executor-reported actual hash
- Issue promote_confirmed without checking both promote_gate AND holdout_gate

---

## Anti-Patterns

| Anti-Pattern | Consequence | Correct Approach |
|---|---|---|
| Using a cached/remembered state_hash | Hash mismatch every iteration; executor blocks; recovery overhead per session | Read hash from most recent findings artifact; ask executor for `kf-project verify` on session start if no prior artifact |
| Including STATE.md data inline in directive | Two sources of truth; artifact goes stale on next rebuild | Reference ledger IDs; read STATE.md separately for strategist context |
| Issuing promote_confirmed without reviewing gates | Overfit or insufficiently evidenced champion; holdout degradation promoted | Run the champion confirmation checklist before issuing; waive explicitly only with reason |
| Two concurrent directives to same executor | Both executors act on same ledger state; second directive gets hash mismatch at step 2 | One directive at a time; await findings before next directive |
| Reframing dead ideas without addressing falsification reason | Semantically equivalent idea clears keyword deadcheck; same failure mode re-enters loop | State explicitly in directive_text why the failure condition doesn't apply to the reframe |
| Not reading Q1/Q2/Q3 before deciding direction | Miss executor's evidence on mechanism and interactions; re-derive same failed hypotheses | Read all three questions; factor Q2 interaction findings into next direction |
| Asking executor to bypass hash verification | Ledger state ambiguity; two agents diverge on what the current champion or DIRECTIVE state is | Never bypass; always re-issue with correct hash; 30 seconds of overhead prevents hours of diverged state |

---

## Related Modules

- `26_Research_Loop_Protocol.md` — the loop structure M28 operates within; defines Orchestra handoff formats, gate criteria, and known failure modes
- `27_Project_Continuity_Layer.md` — the ledger substrate; all executor operations (kf-project append, rebuild, deadcheck, verify) go through M27 primitives
- `19_Memory_Architecture.md` — four-tier memory; DECISION and CHAMPION events accrete to Tier 0 wiki; compaction affects session context
- `21_Knowledge_Accretion.md` — falsified DECISIONs as anti-knowledge candidates; champion DECISIONs as validated pattern candidates

---

## CC Doc

# Module 28: Strategist Protocol — Chat Agent Reference
**Apply when:** Running as strategist (chat agent) in an M26 two-agent research loop. You issue directives to an executor (Claude Code), receive findings, and decide loop direction. You do NOT have filesystem access; all ledger operations go through the executor.

## Session Start

1. **Find state_hash** — from most recent executor findings artifact (`ledger_head_hash` field). If none: ask executor to run `kf-project verify` and report the hash before you issue anything.
2. **Orient on STATE.md** — if accessible, read: CHAMPION (baseline to beat), DEADIDEA list (what's falsified), open DIRECTIVEs (anything in flight?), live FACTs (promote_threshold, eval_game_count).
3. **Announce:**
   ```
   Session start: state_hash `<hash>`. Champion: <value> on <metric> [or: none]. Open directives: <any>.
   ```

## Issue a Directive

```yaml
# Push to executor's Orchestra inbox
type: research_directive
expected_ledger_hash: <ledger_head_hash from MOST RECENT findings artifact — never from memory>
directive_text: "<specific hypothesis — specific enough for deadcheck to evaluate>"
directive_id: "new"       # or existing dir-xxxx to reclaim a dropped directive
promote_confirmed: null   # null | true | false
# optional: holdout_gate_waiver: true  (only when waiving; explain in directive_text)
# optional: human_submission_gate_approval: true  (only when approving external submission)
```

**Rules:** one directive at a time; no STATE.md content or FACT values inline; hash must be from latest findings, never guessed.

## Read Findings & Decide

From executor findings artifact:

```
ledger_head_hash  →  save; becomes expected_ledger_hash in NEXT directive
findings          →  result summary
questions         →  Q1 (mechanism) / Q2 (interactions) / Q3 (next direction)
promote_recommended  →  see Champion Confirmation below
deadcheck_hit       →  see Deadcheck Hit below
```

| Decision | Condition | Action |
|---|---|---|
| Approve | Evidence clear; follow direction | Issue new directive, next hypothesis |
| Redirect | Evidence clear; different direction | Issue new directive, your hypothesis |
| Re-run | Insufficient evidence | Issue same direction, modified eval params |
| Promote | promote_recommended=true + you agree | Champion Confirmation Gate |

## Champion Confirmation Gate

```
Before issuing promote_confirmed: true:
[ ] Read verdict — metric improvement makes sense?
[ ] promote_gate = pass?
[ ] holdout_gate = pass? (if fail: waive with explicit reason only)
[ ] human_submission_gate — approval needed?
```

Confirmation:
```yaml
expected_ledger_hash: <hash from promote-recommendation findings>
directive_text: "Promote decision <decision_id>. Gates reviewed: promote=pass, holdout=pass."
directive_id: "new"
promote_confirmed: true
```

Rejection:
```yaml
promote_confirmed: false
directive_text: "<reason; what to try instead>"
```

## Hash Mismatch Recovery

Executor reports: actual hash ≠ your expected_ledger_hash.

```
1. Read executor's report — get the actual current hash
2. Understand what events advanced the ledger
3. Re-issue with the correct hash:
```
```yaml
expected_ledger_hash: <actual hash from executor report>
directive_text: "<same or updated direction>"
directive_id: "new"
promote_confirmed: null
```

Never re-issue the same stale hash. Never ask executor to bypass hash verification.

## Deadcheck Hit Recovery

Executor reports `deadcheck_hit: true` with `deadcheck_detail` (pattern, tags, killing_decision, evidence).

- **Abandon** — direction is genuinely falsified → issue new directive with a different hypothesis
- **Reframe** — failure condition doesn't apply here → issue new directive that explicitly states why, phrased to clear deadcheck. If executor's deadcheck still hits: abandon.

You cannot bypass deadcheck. Only the executor runs it; only a genuinely different hypothesis passes it.

## Never

- Issue directive without `expected_ledger_hash`
- Use a hash from memory or a prior session artifact — always take it from the latest findings
- Include STATE.md content or DECISION bodies in directive body
- Issue two concurrent directives
- Issue `promote_confirmed: true` without reviewing both gate states first
- Re-issue the same stale hash after a mismatch report
