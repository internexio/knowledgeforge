#!/usr/bin/env python3
"""
kf-stats.py — KnowledgeForge usage statistics.
Hook type: standalone (run directly or via /kf-stats command)
Graceful degradation: exits cleanly if log is absent or malformed.

Reads ~/.claude/kf-usage.jsonl and displays routing metrics broken down
by Claude model version — making it easy to spot behaviour changes after
a model upgrade.

Usage:
    python3 ~/.claude/hooks/kf-stats.py [--days N]
"""

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "kf-usage.jsonl"
DEFAULT_DAYS = 30
W = 56  # output width


# ─── Data loading ─────────────────────────────────────────────────────────────

def load_entries(days: int) -> list[dict]:
    if not LOG_PATH.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    entries = []
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                ts_str = e.get("ts", "")
                if ts_str:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if ts >= cutoff:
                        entries.append(e)
            except Exception:
                pass
    return entries


# ─── Formatting helpers ────────────────────────────────────────────────────────

def bar(frac: float, width: int = 20) -> str:
    filled = max(0, min(width, round(frac * width)))
    return "█" * filled + "░" * (width - filled)


def pct(count: int, total: int) -> str:
    if total == 0:
        return "  0%"
    return f"{count / total:4.0%}"


def rule(label: str) -> str:
    dashes = W - len(label) - 4
    return f"── {label} {'─' * max(0, dashes)}"


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    days = DEFAULT_DAYS
    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        try:
            days = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            pass

    entries = load_entries(days)

    if not entries:
        print(f"\nNo KF usage data found in {LOG_PATH}.")
        print("kf-route.py hook must be active and at least one")
        print("non-trivial prompt submitted.")
        return

    total   = len(entries)
    routed  = [e for e in entries if e.get("routed")]
    direct  = [e for e in entries if not e.get("routed")
               and e.get("mode") not in ("gemini_error", "gemini_timeout", "error")]
    errors  = [e for e in entries
               if e.get("mode") in ("gemini_error", "gemini_timeout", "error")]

    route_rate = len(routed) / total if total else 0
    start_ts   = entries[0]["ts"][:10]
    end_ts     = entries[-1]["ts"][:10]

    print()
    print("═" * W)
    print(f"KF USAGE  {start_ts} → {end_ts}  [{days}d window]")
    print("═" * W)
    err_note = f"  ({len(errors)} classifier errors)" if errors else ""
    print(f"\nTotal requests logged: {total}{err_note}")

    # ── Routing rate ──────────────────────────────────────────────────────────
    print(f"\n{rule('Routing Rate')}")
    print(f"  KF-routed:  {len(routed):4d} {pct(len(routed), total)}  {bar(route_rate, 16)}")
    print(f"  Direct/raw: {len(direct):4d} {pct(len(direct), total)}  {bar(1 - route_rate, 16)}")

    # ── By model version ──────────────────────────────────────────────────────
    by_model = defaultdict(list)
    for e in entries:
        by_model[e.get("model", "unknown")].append(e)

    # Sort by first-seen so the timeline reads top-to-bottom
    model_order = sorted(by_model.keys(),
                         key=lambda m: min(e["ts"] for e in by_model[m]))
    latest_model = entries[-1].get("model", "unknown") if entries else "unknown"

    print(f"\n{rule('By Model Version')}")
    prev_mr = None
    for model_name in model_order:
        mes = by_model[model_name]
        mr = sum(1 for e in mes if e.get("routed")) / len(mes) if mes else 0
        tag = "  ← current" if model_name == latest_model else ""
        delta_tag = ""
        if prev_mr is not None:
            delta = mr - prev_mr
            if abs(delta) >= 0.03:
                direction = "▲" if delta > 0 else "▼"
                delta_tag = f"  {direction}{abs(delta):.0%}"
        print(f"  {model_name:<30} {len(mes):4d}  KF:{mr:4.0%}  {bar(mr, 8)}{delta_tag}{tag}")
        prev_mr = mr

    # ── Mode breakdown (routed only) ──────────────────────────────────────────
    if routed:
        print(f"\n{rule('Mode Breakdown — KF-routed')}")
        mode_counts: dict[str, int] = defaultdict(int)
        for e in routed:
            mode_counts[e.get("mode", "unknown")] += 1
        for mode_name, count in sorted(mode_counts.items(), key=lambda x: -x[1]):
            frac = count / len(routed)
            print(f"  {mode_name:<14} {count:4d} {pct(count, len(routed))}  {bar(frac, 10)}")

    # ── Mode breakdown per model (if multiple models) ─────────────────────────
    if len(model_order) > 1:
        print(f"\n{rule('Mode Breakdown By Model')}")
        for model_name in model_order:
            mes = by_model[model_name]
            routed_mes = [e for e in mes if e.get("routed")]
            if not routed_mes:
                continue
            mode_c: dict[str, int] = defaultdict(int)
            for e in routed_mes:
                mode_c[e.get("mode", "??")] += 1
            top = sorted(mode_c.items(), key=lambda x: -x[1])[:4]
            top_str = "  ".join(f"{m}:{c}" for m, c in top)
            print(f"  {model_name:<30} {top_str}")

    # ── Decision types ────────────────────────────────────────────────────────
    dt_counts: dict[str, int] = defaultdict(int)
    for e in entries:
        dt = e.get("decision_type", "")
        if dt:
            dt_counts[dt] += 1
    if dt_counts:
        dt_total = sum(dt_counts.values())
        print(f"\n{rule('Decision Types')}")
        for dt, count in sorted(dt_counts.items(), key=lambda x: -x[1]):
            print(f"  {dt:<14} {count:4d} {pct(count, dt_total)}")

    print(f"\n{'═' * W}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[kf-stats] {e}\n")
        sys.exit(0)
