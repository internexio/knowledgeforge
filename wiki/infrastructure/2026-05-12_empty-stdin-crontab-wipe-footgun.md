---
title: Empty-stdin crontab wipe — pipeline-failure footgun
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-12
domain: infrastructure
topic: ops
tags: scheduling, quality-gate, adversarial, empirical
related_entries: [patterns/2026-05-11_atomic-write-stubs-for-readwrite-pipelines.md]
---

# Empty-stdin crontab wipe — pipeline-failure footgun

`crontab -` reads its replacement crontab from stdin. If stdin is empty,
it silently installs an empty crontab — wiping every entry, no warning,
no error. This makes the common shell idiom

```bash
crontab -l 2>/dev/null | sed "s|OLD|NEW|g" | crontab -
```

dangerous: if `sed` errors (e.g. unbalanced parens in a `-E` pattern on
BSD sed, malformed escape, etc.), `sed` exits non-zero with an empty
stdout, the empty stdout flows to `crontab -`, and the user's crontab
is gone. There is no error message from `crontab -` itself; you
discover the wipe by running `crontab -l` and seeing zero lines.

## Concrete failure observed

On macOS during a [project] dreaming deployment (2026-05-12), I ran:

```bash
crontab -l | sed -E 's|^(.*scripts/archive/(...)\.sh.*)$|# DREAMING-DISABLED: \1|' | crontab -
```

BSD sed rejected the `-E` capture-group syntax with
"RE error: parentheses not balanced" and exited non-zero with empty
stdout. `crontab -` accepted the empty stdin and the 26-line crontab
was replaced with 0 lines. Recovery: a tempfile backup taken
immediately before the operation was the only thing that saved the
machine's automation.

## Detection symptoms

- `crontab -l` returns zero lines after a pipeline that "should have"
  rewritten lines
- The pipeline's stderr may contain the sed/awk/jq error, but you
  won't notice it if you piped stderr away or ran the pipeline
  unattended
- Scheduled jobs simply stop firing — you discover this hours/days
  later when logs go silent

## Mitigation (two layers)

### Layer 1: tempfile + non-empty pre-check (shell)

Build the proposed crontab into a tempfile, validate it is non-empty
when the backup was non-empty, then install:

```bash
crontab -l > "$BACKUP" 2>/dev/null || : > "$BACKUP"
PROPOSED=$(mktemp)
trap 'rm -f "$PROPOSED"' EXIT
if ! crontab -l 2>/dev/null | sed "s|OLD|NEW|g" > "$PROPOSED"; then
    echo "FATAL: pipeline failed; restoring backup"
    crontab "$BACKUP" || true
    exit 1
fi
if [ -s "$BACKUP" ] && [ ! -s "$PROPOSED" ]; then
    echo "FATAL: proposed crontab is empty but backup is not"
    exit 1
fi
crontab "$PROPOSED"
```

The key invariant: if the prior crontab had any content, the new one
must too. `mktemp` + explicit `crontab "$tmpfile"` (not stdin) also
makes the failure mode visible in shell exit codes.

### Layer 2: in-process guard (Python / any cron-editing tool)

Wrap the actual install call in a function that takes both the new
text AND the prior text, and refuses to install when prior had
entries but proposed has zero:

```python
def install_crontab(text: str, prior_text: str | None = None) -> None:
    if prior_text is not None:
        def _count(s):
            return sum(
                1 for line in s.splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            )
        if _count(prior_text) > 0 and _count(text) == 0:
            raise ValueError(
                "refusing to install empty crontab: prior had "
                f"{_count(prior_text)} active entries, proposed has 0"
            )
    subprocess.run(["crontab", "-"], input=text, text=True, check=True)
```

This catches the same failure mode at the API boundary — useful when
the pipeline is constructed programmatically and a tempfile dance is
inconvenient.

## When This Applies

- Any script or tool that edits the crontab via the `crontab -l | ... | crontab -` idiom
- Any autonomous remediation system that auto-applies crontab changes
  (e.g. [project] Dreaming Cat A auto-fixes — every cycle could wipe
  the crontab if a malformed op slipped through)
- Cross-platform shell scripts where BSD vs GNU tool differences can
  silently produce empty pipeline output

## When This Does NOT Apply

- Tools that use the `crontab(1)` file-mode (`crontab /path/to/file`)
  exclusively — file-mode requires the file to exist with content,
  failing more visibly
- Linux-only environments using GNU sed exclusively where the
  `-E`-and-parens-on-BSD trap doesn't fire (though other pipeline
  failure modes still apply: jq schema errors, awk syntax errors, etc.)
- Systems that maintain their crontab via configuration management
  (Ansible, Puppet, Chef) where the pipeline isn't shell-invoked

## Source Context

Discovered during [project] Dreaming Tier 1 deployment, 2026-05-12.
The wipe occurred during a manual edit (not the dreaming system itself
— the dreaming system already used the file-mode install pattern in
the post-pipe validation step). Recovery was via a tempfile backup
captured 30 seconds before the wipe. The fix was committed across
two files: a Python-side guard in `dream/cycle.py`
`_install_crontab(text, prior_text=...)`, and a shell-side tempfile +
validate refactor in `scripts/install-dreaming.sh`. The post-mortem
revealed both layers were needed: shell scripts use the shell
idiom; programmatic users use the function. 4 unit tests added to
prevent regression. See PR #1 commits 4cbaf51 and aeca186 in
internexio/[project].
