---
title: Self-identity-minting CLI flag for cron-scheduled workers
source_mode: builder
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.9
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-14
domain: infrastructure
topic: ops
tags: cli-design, cron-workers, bead-tracking, audit-trail, identity-creation, [project], iteration-loop
related_entries:
  - infrastructure/2026-05-14_idempotent-watchdog-producer-pattern.md
  - infrastructure/2026-05-13_launchd-cwd-trap-relative-tool-lookups.md
  - architecture/2026-05-14_identity-registry-append-only-event-log-separation.md
---

# Self-Identity-Minting CLI Flag for Cron-Scheduled Workers

## The Problem

Cron-scheduled workers that emit findings to an external tracking system (beads issue, Jira ticket, GitHub issue) traditionally require the handle to be **passed in** at deployment time. This creates friction:

1. Someone must create the parent issue first
2. The ID threads through the cron entry or launchd plist
3. All historical findings collapse under one issue, losing per-cycle audit trails
4. Queries like "What did the linter find on date X?" require grep/timestamp filtering, not clean tracking

The iteration-loop v0 wiki-linter originally used this model: `--bd-id <id>`, with install scripts auto-creating a persistent bead and reusing it for all cycles. This solved the deployment friction but introduced data quality problems.

## The Pattern

Add a **`--auto-create-bead`** (or analogous) CLI flag that mints a fresh identity *at run time*, before the worker scans. The flag is **mutually exclusive** with the pre-supplied-ID flag; one of the two must be set.

```python
# scripts/wiki_linter.py
parser = argparse.ArgumentParser()
parser.add_argument("--bd-id", default=None, ...)
parser.add_argument("--auto-create-bead", action="store_true", ...)

args = parser.parse_args()

# Mutual exclusivity validation
if bool(args.bd_id) == bool(args.auto_create_bead):
    parser.error("exactly one of --bd-id or --auto-create-bead must be set")

if args.auto_create_bead:
    bd_id = wiki_linter.create_audit_bead(args.wiki_root)
else:
    bd_id = args.bd_id
```

Each cycle gets its own identity without deployment-time coupling. The minting function runs **before** any scanning and aborts with a typed error on failure, preventing fabrication of IDs downstream:

```python
def create_audit_bead(wiki_root: Path) -> str:
    """Mint a fresh bead for this cycle's audit output.
    
    Raises AuditBeadCreateError on any failure (non-zero exit, garbage stdout).
    Aborts before any scanning — failures are fail-closed, not silent.
    """
    timestamp = datetime.utcnow().isoformat(timespec="seconds")
    title = f"wiki-linter {timestamp}"
    
    completed = subprocess.run(
        ["bd", "create", "--silent", "--title", title],
        capture_output=True, timeout=10, text=True,
    )
    
    if completed.returncode != 0:
        raise AuditBeadCreateError(
            f"bd create failed: rc={completed.returncode}, "
            f"stderr={completed.stderr.strip()}"
        )
    
    bead_id = completed.stdout.strip()
    
    # Whitelist valid ID format
    if not bead_id or "\n" in bead_id or " " in bead_id:
        raise AuditBeadCreateError(f"unexpected stdout: {bead_id!r}")
    
    return bead_id
```

The cron/launchd entry is simple:
```bash
0 6 * * * cd ~/Scripts/knowledgeforge-core && python3 -m wiki_linter.cli --auto-create-bead
```

No ID pre-allocation. No persistent parent beads. Each cycle is standalone and traceable.

## When This Applies

- Cron / launchd / systemd / Kubernetes cronjob workers that emit per-cycle audit output
- Workers whose findings would otherwise pile into a single persistent parent bead, losing the per-cycle slice
- Any worker where the cost of one issue per run is acceptable (low-frequency cycles like nightly / weekly)
- Systems using `bd` or similar issue trackers that support CLI identity creation with `--silent` mode

## When This Does NOT Apply

- High-frequency cycles (per-minute / per-hour) — bead churn would overwhelm the tracker. Use a persistent parent + dated notes instead
- Multi-worker single-cycle orchestration (one cycle, many workers) — the identity belongs to the cycle, not each worker; mint at the orchestrator level
- Cases where the parent issue carries cross-cycle context (status, design notes, related-PR links) that must persist — keep it static
- Workers whose identity is ephemeral in the system (fire-and-forget logging with no external handle requirement)

## Failure Modes & Protections

**Failure mode: non-zero exit from `bd create`**
- Cause: `bd` CLI broken, auth missing, tracker down
- Protection: `if completed.returncode != 0: raise AuditBeadCreateError(...)`
- Behavior: worker aborts before scanning; cycle fails cleanly, visible in cron log

**Failure mode: garbage stdout from `bd create`**
- Cause: misconfigured `bd` flags, unexpected formatter version
- Protection: `if not bead_id or "\n" in bead_id or " " in bead_id: raise AuditBeadCreateError(...)`
- Behavior: worker aborts; no fabricated ID sent downstream

**Failure mode: `bd create` timeout**
- Cause: tracker hung, network issue
- Protection: `timeout=10` in subprocess call
- Behavior: worker aborts after 10 seconds; visible in cron log as a timeout

The key discipline: **fail before scanning, not after**. A corrupted identity is worse than a failed scan.

## Concrete Grounding

- **Shipped:** [project] commit 51cb843 (2026-05-14), `scripts/wiki_linter.py` with `--auto-create-bead` flag
- **Implementation:** `iteration_loop/workers/wiki_linter.py::create_audit_bead()` with three error branches:
  - Non-zero exit → `AuditBeadCreateError`
  - Garbage stdout → `AuditBeadCreateError`
  - Timeout → caught by subprocess timeout
- **Tests:** 4 dedicated tests covering happy path + three failure modes. 225 total tests passing
- **Smoke test:** Against `~/Scripts/knowledgeforge-core/wiki`, minted bead `[project]-8les`, scanned 41 findings, all stamped with that bead
- **Tracking bead:** [project]-tqud (closed with shipping reference)

## Source Context

Extracted from iteration-loop v0 wiki-linter implementation (2026-05-14). The linter originally required a pre-created persistent bead for all cycles. Refactoring to auto-mint per-cycle identities revealed a reusable pattern applicable to any cron worker needing external handles. This pattern is complementary to (not a replacement for) the identity-registry + append-only event log pattern documented elsewhere — it solves the bootstrap/deployment-time identity question, not the runtime mutation question. Related to the idempotent-watchdog-producer pattern (which addresses detection + dedup structure) but orthogonal to it (watchdog producers benefit from auto-created beads too, but the creation is optional, not prescriptive).
