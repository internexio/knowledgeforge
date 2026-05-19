---
title: Stale port-file in dynamic-port server discovery — verify via lsof, not just read
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.80
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-16
tags: empirical, stable, quality-gate, observability
domain: infrastructure
topic: server-configuration
related_entries: []
---

# Stale Port-File in Dynamic-Port Server Discovery

## The Trap

A server that binds to a dynamic/ephemeral port (e.g., `-P 0` or no explicit port) writes its chosen port to a discovery file (`.beads/dolt-server.port`, `.pid`, `.sock`, etc.) and clients read that file to find it. When the server restarts and is reassigned a different port, the discovery file is **not automatically updated**. Clients keep reading the stale file and get connection-refused errors.

The failure mode looks like a hung or down server when in fact the server is healthy and just on a different port than the discovery file claims.

## Empirical Case

[project] beads, 2026-05-16. Symptoms: `bd` commands failing with:

```
Error: failed to open database: Dolt server auto-started but still
unreachable at 127.0.0.1:49568: dial tcp 127.0.0.1:49568: connect:
connection refused
```

Diagnosis:
- `.beads/dolt-server.port` said **49568**.
- `ps aux | grep "dolt sql-server"` showed two dolt processes running.
- `lsof -nP -p <PID>` on the [project]-rooted dolt process revealed it was listening on **49775**, not 49568.
- `bash -c 'echo > /dev/tcp/127.0.0.1/49775'` succeeded; 49568 was closed.
- Fix: `echo -n "49775" > .beads/dolt-server.port`. Non-destructive realignment; no server restart needed.

## The Diagnostic Procedure

When a "server unreachable on port X" error occurs:

1. **Do NOT restart the server first.** Restart loses diagnostic state and may produce a third stale port if the bind is non-deterministic.
2. Check the process list — `ps aux | grep <server-name>` — to confirm the server is actually running.
3. Find which port the process is on:
   ```
   /usr/sbin/lsof -nP -p <PID> 2>&1 | grep LISTEN
   ```
   The output gives the actual `IP:port` the process is bound to.
4. Probe the actual port:
   ```
   bash -c 'echo > /dev/tcp/127.0.0.1/<port>' && echo OPEN
   ```
5. If actual port ≠ port-file, update the port-file. Backup first; the previous value may be useful evidence:
   ```
   cp .port .port.bak && echo -n "<actual-port>" > .port
   ```
6. Re-test the client.

## The Fix at the Source

Two ways to prevent recurrence:

- **Bind to a fixed port.** Trade ease-of-coexistence for stable discovery. Best when only one server instance is expected per repo.
- **Write the port file atomically after bind.** Many server bootstraps write the port file BEFORE bind completes (or never update it on restart). Move the write to a post-bind hook with `os.rename(tmp, target)` semantics.

## When to Use This Pattern

- Any local dev server with dynamic port assignment + a discovery file.
- Any service whose bootstrap path includes a "find available port" step.
- Any tool that reads a `.port` / `.sock` / `.pid` file rather than querying the OS for live state.

## When This Does NOT Apply

- Services with stable, well-known ports (no discovery file in the loop).
- Services discovered via DNS-SD / mDNS / consul / etcd (the registry handles liveness).
- Containerized services with port-mapping handled by Docker / Kubernetes (the container runtime owns discovery).

## Trap Within the Trap

Restarting the server "to fix" the connection error often makes things worse: the new bind may land on yet another port, and you've lost the chance to see the original mismatch. The `gt dolt status` / `bd doctor` style of tools should detect port-file divergence and surface it explicitly rather than just timing out.

## Source Context

Identified during a routine `bd show` attempt that returned a connection-refused error against the recorded port (49568). Two dolt processes were running — one on 49775 ([project]-rooted), one on 3307 (gt main config). The port file had been written at some earlier server-start time and never refreshed when the server restarted. Backup file `.port.bak` retained the stale value for audit. The fix was one shell command, took 30 seconds, and required no restart.

This pattern is a cousin of the bd validator-cache staleness issue (sibling pattern: `wiki/patterns/2026-05-15_reactive-cache-refresh-retry-on-stale-validator.md`) — both involve cached state diverging from current reality, with a reactive refresh-and-retry as the lightest-touch fix.

## Related

- **[[reactive-cache-refresh-retry-on-stale-validator]]** — same shape: cached state diverged, retry after refresh.
