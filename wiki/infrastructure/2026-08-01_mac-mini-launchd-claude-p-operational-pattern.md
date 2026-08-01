---
title: Mac Mini launchd + claude -p operational pattern
source_mode: debugger
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-08-01
domain: infrastructure
topic: ops
tags: claude-code, launchd, macos, automation, infrastructure
related_entries:
  - infrastructure/2026-05-14_claude-cli-bare-disables-oauth-keychain-auth.md
  - infrastructure/2026-06-13_plistlib-vs-plutil-xml-parser-divergence.md
  - infrastructure/2026-05-13_launchd-cwd-trap-relative-tool-lookups.md
  - infrastructure/2026-06-10_launchd-subprocess-shell-alias-resolution-gotcha.md
  - infrastructure/2026-07-14_scheduled-social-post-pipeline-json-queue-python-scheduler-launchd.md
---

# Mac Mini launchd + claude -p Operational Pattern

## What was learned

Claude Code CLI (`claude -p`) can be invoked non-interactively from macOS launchd user agents, enabling scheduled/automated AI-assisted workflows on Mac Mini without interactive auth. The full OAuth auth pipeline (subscription-billed) remains accessible, and full skill invocations (including multi-step COS analysis) execute correctly from launchd context.

## When This Applies

Any scenario where you need `claude -p` (headless prompt execution) to run from a launchd plist on macOS:
- Scheduled automation tasks driven by AI analysis
- Cron replacement for long-running intelligence gathering
- Orchestra-triggered jobs that need AI-assisted decision-making
- Mac Mini daemon processes that invoke Claude for analysis or synthesis

## When This Does NOT Apply

- LaunchDaemons (root-level, system context) — those don't have user keychain access; launchd itself uses the calling user's context
- Interactive Claude Code sessions (use Happy or Claude Code Bash directly)
- Scenarios where you need real-time terminal feedback (launchd jobs are fire-and-forget by design)
- Workflows requiring keychain prompts for other credentials (launchd runs headless with no TCC UI)

## Concrete Setup (verified 2026-08-01 on Mac Mini M4, macOS 15)

### Step 1: Install standalone CLI

Do NOT rely on the bundled binary inside happy-coder or other packaging. Install as a standalone:

```bash
npm install -g @anthropic-ai/claude-code
```

Verify:
```bash
which claude        # → /opt/homebrew/bin/claude
claude --version    # → v2.1.220+
```

### Step 2: Fix `/tmp/claude-<uid>` symlink (Claude Code v2.1.220+ quirk)

Claude Code v2.1.220 checks this path on startup; if it's a symlink it refuses to run. On first launchd invocation, you'll see an error like `Cannot create working directory` or similar.

**One-time fix (ephemeral, survives until reboot):**

```bash
rm /tmp/claude-501  # or whatever uid
mkdir -p /tmp/claude-501
```

**For production plists (persists across reboots):** Use `CLAUDE_CODE_TMPDIR` environment variable instead:

```xml
<key>EnvironmentVariables</key>
<dict>
    <key>CLAUDE_CODE_TMPDIR</key>
    <string>~/.tmp/claude-launchd</string>
</dict>
```

Create the directory once:

```bash
mkdir -p ~/.tmp/claude-launchd
```

### Step 3: Set PATH explicitly in plist

launchd gets a minimal PATH (`/usr/bin:/bin:/usr/sbin:/sbin`) that does not include `/opt/homebrew/bin` where the claude binary lives. Explicitly set PATH in the plist:

```xml
<key>ProgramArguments</key>
<array>
    <string>/bin/sh</string>
    <string>-c</string>
    <string>PATH=/opt/homebrew/bin:/usr/bin:/bin claude -p "your prompt" 2>&1</string>
</array>
```

### Step 4: OAuth auth is accessible

The OAuth token (created via `claude login` in an interactive session, stored in keychain) IS accessible from launchd user agents. No special configuration needed — the keychain lookup happens transparently during `claude -p` execution. Billing goes to the user's Claude subscription bucket (not requiring `--bare` mode or a separate API key).

### Step 5: Full skill invocations work

Multi-step skill sequences execute correctly from launchd context. Example:

```bash
claude -p "/cos analyze full --input 'communication text' --target-framework HAPE" 2>&1
```

The COS analysis skill, including all internal delegation steps, completes and returns structured results.

## Complete plist Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.example.claude-scheduled-job</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/sh</string>
        <string>-c</string>
        <string>PATH=/opt/homebrew/bin:/usr/bin:/bin claude -p "your prompt here" 2>&1</string>
    </array>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>CLAUDE_CODE_TMPDIR</key>
        <string>~/.tmp/claude-launchd</string>
    </dict>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>/var/log/claude-job.log</string>
    
    <key>StandardErrorPath</key>
    <string>/var/log/claude-job-error.log</string>
    
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

Save as `~/Library/LaunchAgents/com.example.claude-scheduled-job.plist` and load:

```bash
launchctl load ~/Library/LaunchAgents/com.example.claude-scheduled-job.plist
```

## Verification

After loading the plist, verify a full cycle:

1. **Check plist is loaded:**
   ```bash
   launchctl list | grep claude-scheduled-job
   ```

2. **Manually trigger the job:**
   ```bash
   launchctl start com.example.claude-scheduled-job
   ```

3. **Check output:**
   ```bash
   tail -f /var/log/claude-job.log
   ```

Should see full Claude analysis output or skill results. If you see auth errors (`"Not logged in"`), verify:
- OAuth keychain entry exists: `security find-generic-password -s "claude.ai" 2>/dev/null | head -5`
- plist does NOT include `--bare` flag (which disables keychain lookup)

## When This Applies in Existing Workflows

- **cos-manager scheduled audits:** COS analysis tasks triggered by launchd at fixed times
- **[project] bridge relay:** Automation that needs AI-assisted decision gates
- **multi-stage intelligence gathering:** Scheduled data fetch + COS analysis + report generation

## Gotchas and Trade-Offs

| Aspect | Behavior |
|--------|----------|
| Startup latency | ~1-2 sec for Claude CLI overhead (hooks, MCP, keychain lookup) |
| Auth model | OAuth subscription billing (no per-call cost tracking by tag) |
| Skills | All Claude Code skills execute; skill output goes to stdout (capture in log file) |
| Error handling | Stderr captured to StandardErrorPath; launchd does not retry on failure |
| Concurrency | One job fires per scheduled interval; overlapping runs cause lock contention (use unique tmpdir per job if parallelizing) |
| Logging | Combine StandardOutPath + StandardErrorPath for full visibility |

## Grounding

**Verified 2026-08-01 on Mac Mini M4, macOS 15:**

1. Installed `claude` via npm globally
2. Created test plist with `/cos analyze full` skill invocation
3. Loaded plist via `launchctl load`
4. Triggered job via `launchctl start`
5. Confirmed full COS analysis output in StandardOutPath log file
6. Verified OAuth token was used (not requiring `--bare` + `ANTHROPIC_API_KEY`)
7. Multi-step skill operations (analyze → frame → synthesize) all completed in launchd context

**Deployment reference:** cos-manager morning-sweep audit task (pending deployment to Mac Mini)

## Source Context

Extracted from cos-manager session 2026-08-01 debugging Mac Mini orchestration for automated COS analysis workflows. Initial investigation revealed that Claude Code CLI can run non-interactively from launchd, with OAuth auth working transparently. The `/tmp/claude-<uid>` symlink issue was a v2.1.220-specific quirk discovered during plist loading; the CLAUDE_CODE_TMPDIR workaround provides a production-safe alternative. Full skill invocations (including COS analyze_full) execute successfully, enabling scheduled intelligence gathering on Mac Mini without manual intervention.
