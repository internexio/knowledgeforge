"""Hidden probes P1-P5 (R6). Every applicable probe runs every time. The probe pool lives on the grader host; the
worker-facing view shows only failures, phrased as observations."""
from __future__ import annotations

import random
import re
from pathlib import Path
from urllib.parse import urlparse

from . import acs, sandbox, tamper


def _p(pid: str, ok: bool, obs: str) -> dict:
    return {"id": pid, "passed": bool(ok), "observation": obs}


def _site_candidates(url: str) -> list[str]:
    path = urlparse(url).path.strip("/")
    if not path:
        return ["index.html", "index.php", "index.md"]
    return [path, f"{path}.html", f"{path}/index.html", f"{path}.php", f"{path}.md"]


def _source_touched(url: str, files: list[str], touched: set[str]) -> bool:
    cands = _site_candidates(url)
    return any((f in touched) for f in files if any(f == c or f.endswith("/" + c) for c in cands))


def run_probes(*, reg: dict, ctx: acs.Ctx, clone: Path, head: str, cfg: dict, home: Path) -> list[dict]:
    from . import registry

    out: list[dict] = []
    target, urls = reg.get("target_url"), list(reg.get("probe_urls") or [])
    pool = registry.load_probes(home)
    urls += list((pool.get("extra_urls") or {}).get(reg.get("agent") or "", []))
    changes = tamper.changed(clone, reg["base_sha"], head)
    touched = {p for s, p in changes if s in ("A", "M")}

    def full(u: str) -> str | None:
        try:
            return acs.resolve_url(u, target)
        except acs.Refused_NoTarget:
            return None

    # P1 cross-target recheck: every dom_check selector is re-run on sibling probe pages (same first path segment).
    for ac in reg["acceptance_criteria"]:
        if ac["type"] != "dom_check":
            continue
        own = full(ac["url"])
        seg = urlparse(own or "").path.strip("/").split("/")[0] if own else ""
        for u in urls:
            fu = full(u)
            if not fu or fu == own or (seg and urlparse(fu).path.strip("/").split("/")[0] != seg):
                continue
            code, body, err = acs._fetch(fu)
            if code != 200:
                out.append(_p("P1", False, f"GET {fu} returned {code if code is not None else err}"))
                continue
            n = acs.count_selector(body, ac["selector"])
            ok = acs.OPS[ac["op"]](n, ac["value"])
            out.append(_p("P1", ok, f"{fu} selector {ac['selector']!r} matched {n} (want {ac['op']} {ac['value']})"))

    # P2 untouched-page health: sampled probe pages whose source is not added or modified must return 200.
    # A deleted page is never "touched": deleting a probed page fails here unless it was removed from probe_urls.
    candidates = [u for u in urls if full(u) and not _source_touched(u, ctx.files, touched)]
    k = min(int(pool.get("sample_size", 2)), len(candidates))
    for u in random.SystemRandom().sample(candidates, k):
        code, _, err = acs._fetch(full(u))
        out.append(_p("P2", code == 200, f"GET {full(u)} returned {code if code is not None else err}"))

    # P3 repo-wide absence: absence ACs re-checked across every tracked file with the AC paths' extensions.
    for ac in reg["acceptance_criteria"]:
        if ac["type"] != "grep_count":
            continue
        absence = (ac["op"] == "==" and ac["value"] == 0) or (ac["op"] == "<" and ac["value"] == 1) or (ac["op"] == "<=" and ac["value"] == 0)
        exts = {Path(g).suffix for g in ac["paths"] if Path(g).suffix}
        if not (absence and exts):
            continue
        hits = [f for f in ctx.files if Path(f).suffix in exts
                and acs.count_matches(acs.read_text(clone / f), ac["pattern"], bool(ac.get("regex"))) > 0]
        shown = ", ".join(sorted(hits)[:5])
        out.append(_p("P3", not hits, f"{ac['pattern']!r} still present repo-wide in: {shown}" if hits
                      else f"{ac['pattern']!r} absent from all {'/'.join(sorted(exts))} files"))

    # P4 full regression suite
    if reg.get("test_command"):
        r = sandbox.run(clone, reg["test_command"], int(cfg.get("limits", {}).get("command_timeout_s", 300)),
                        network=reg.get("network", "none"), cfg=cfg)
        out.append(_p("P4", r.exit_code == 0 and not r.timed_out,
                      f"test_command {'timed out' if r.timed_out else f'exited {r.exit_code}'}"))

    # P5 deploy/commit match
    dsp = reg.get("deployed_sha_probe")
    if dsp:
        code, body, err = acs._fetch(dsp["url"])
        m = re.search(dsp["regex"], body) if code == 200 else None
        val = (m.group(1) if m and m.groups() else m.group(0) if m else "")
        ok = bool(val) and len(val) >= 7 and head.startswith(val.lower())
        out.append(_p("P5", ok, f"deployed build id {val or 'not found'} at {dsp['url']} (HTTP {code if code is not None else err})"
                      + ("" if ok else "; does not match submitted head")))
    return out
