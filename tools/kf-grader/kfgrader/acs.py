"""AC block parsing (Module 04 `kf-acceptance`) and executors for every non-judgment AC type."""
from __future__ import annotations

import operator
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

import yaml

from .registry import Refused

AC_TYPES = ("command", "grep_count", "http_status", "dom_check", "judgment")
ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
BLOCK_RE = re.compile(r"```yaml[ \t]+kf-acceptance[ \t]*\r?\n(.*?)\r?\n```", re.DOTALL)
OPS = {"==": operator.eq, "!=": operator.ne, ">=": operator.ge, "<=": operator.le, ">": operator.gt, "<": operator.lt}
OUT_CAP = 4096


def cap(s: str, n: int = OUT_CAP) -> str:
    return s if len(s) <= n else s[:n] + f"\n[truncated {len(s) - n} bytes]"


# ---------------------------------------------------------------- globs
def glob_to_regex(pat: str) -> re.Pattern:
    i, out = 0, ""
    while i < len(pat):
        if pat.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pat.startswith("**", i):
            out += ".*"
            i += 2
        elif pat[i] == "*":
            out += "[^/]*"
            i += 1
        elif pat[i] == "?":
            out += "[^/]"
            i += 1
        elif pat[i] == "[" and pat.find("]", i + 1) != -1:
            j = pat.find("]", i + 1)
            body = pat[i + 1 : j]
            if body.startswith("!"):
                body = "^" + body[1:]
            out += "[" + body.replace("\\", "\\\\") + "]"
            i = j + 1
        else:
            out += re.escape(pat[i])
            i += 1
    return re.compile("^" + out + "$")


def match_glob(pat: str, path: str, basename_any: bool = False) -> bool:
    if glob_to_regex(pat).match(path):
        return True
    if basename_any and "/" not in pat:
        return bool(glob_to_regex(pat).match(path.rsplit("/", 1)[-1]))
    return False


# ---------------------------------------------------------------- parsing / validation
def parse_ac_block(spec_text: str) -> list[dict]:
    blocks = BLOCK_RE.findall(spec_text)
    if not blocks:
        raise Refused("spec has no ```yaml kf-acceptance block")
    acs: list[dict] = []
    for b in blocks:
        try:
            doc = yaml.safe_load(b)
        except yaml.YAMLError as e:
            raise Refused(f"kf-acceptance block is not valid YAML: {e}")
        if not isinstance(doc, dict) or not isinstance(doc.get("acceptance_criteria"), list):
            raise Refused("kf-acceptance block must contain an acceptance_criteria list")
        acs.extend(doc["acceptance_criteria"])
    seen: set[str] = set()
    for ac in acs:
        validate_ac(ac, seen)
    if not any(a["type"] != "judgment" for a in acs):
        raise Refused("spec has no executable AC (all judgment): registration refused")
    return acs


def _need(ac: dict, *keys: str) -> None:
    for k in keys:
        if k not in ac or ac[k] in (None, ""):
            raise Refused(f"AC {ac.get('id')}: missing field {k!r} for type {ac.get('type')}")


def validate_ac(ac: object, seen: set[str]) -> None:
    if not isinstance(ac, dict):
        raise Refused("each AC must be a mapping")
    aid = ac.get("id")
    if not isinstance(aid, str) or not ID_RE.match(aid):
        raise Refused(f"AC id {aid!r} invalid (use [A-Za-z0-9_-]+)")
    if aid in seen:
        raise Refused(f"duplicate AC id {aid}")
    seen.add(aid)
    t = ac.get("type")
    if t not in AC_TYPES:
        raise Refused(f"AC {aid}: unknown type {t!r}")
    if t == "command":
        _need(ac, "run")
        if not isinstance(ac.get("expect", {}), dict):
            raise Refused(f"AC {aid}: expect must be a mapping")
    elif t == "grep_count":
        _need(ac, "pattern", "paths", "op", "value")
        if not isinstance(ac["paths"], list) or not ac["paths"]:
            raise Refused(f"AC {aid}: paths must be a non-empty list")
        if ac["op"] not in OPS:
            raise Refused(f"AC {aid}: op must be one of {sorted(OPS)}")
        if ac.get("regex"):
            try:
                re.compile(ac["pattern"])
            except re.error as e:
                raise Refused(f"AC {aid}: bad regex: {e}")
    elif t == "http_status":
        _need(ac, "url", "expect")
    elif t == "dom_check":
        _need(ac, "url", "selector", "op", "value")
        if ac["op"] not in OPS:
            raise Refused(f"AC {aid}: op must be one of {sorted(OPS)}")
    elif t == "judgment":
        _need(ac, "text")


# ---------------------------------------------------------------- context
@dataclass
class Ctx:
    src: Path
    files: list[str]
    target_url: str | None = None
    network: str = "none"
    cfg: dict = field(default_factory=dict)


def tracked_files(src: Path) -> list[str]:
    r = subprocess.run(["git", "-C", str(src), "ls-files", "-z"], capture_output=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError("git ls-files failed: " + r.stderr.decode("utf-8", "replace"))
    return [p for p in r.stdout.decode("utf-8", "surrogateescape").split("\0") if p]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def count_matches(text: str, pattern: str, is_regex: bool) -> int:
    """grep -c semantics: number of lines containing a match."""
    if is_regex:
        rx = re.compile(pattern)
        return sum(1 for line in text.splitlines() if rx.search(line))
    return sum(1 for line in text.splitlines() if pattern in line)


def select_files(ctx: Ctx, globs: list[str]) -> list[str]:
    return [p for p in ctx.files if any(match_glob(g, p) for g in globs)]


# ---------------------------------------------------------------- executors
def run_grep_count(ac: dict, ctx: Ctx) -> tuple[bool, str]:
    files = select_files(ctx, ac["paths"])
    if not files:
        return False, f"no files matched paths {ac['paths']}"
    op, want = OPS[ac["op"]], ac["value"]
    counts = {f: count_matches(read_text(ctx.src / f), ac["pattern"], bool(ac.get("regex"))) for f in files}
    if ac.get("per_file", True):
        bad = {f: c for f, c in counts.items() if not op(c, want)}
        ok = not bad
        lines = [f"{f}: {c} (want {ac['op']} {want})" for f, c in sorted(bad.items())]
        return ok, cap("\n".join(lines)) if lines else f"{len(files)} files ok"
    total = sum(counts.values())
    return op(total, want), f"total {total} across {len(files)} files (want {ac['op']} {want})"


def _fetch(url: str, timeout: int = 20) -> tuple[int | None, str, str]:
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):  # noqa: ANN001
            return None

    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, headers={"User-Agent": "kf-grader/0.1"})
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.status, r.read(2_000_000).decode("utf-8", "replace"), ""
    except urllib.error.HTTPError as e:
        return e.code, "", ""
    except Exception as e:  # noqa: BLE001
        return None, "", f"{type(e).__name__}: {e}"


def resolve_url(url: str, target: str | None) -> str:
    if re.match(r"^https?://", url):
        return url
    if not target:
        raise Refused_NoTarget(url)
    return urllib.parse.urljoin(target.rstrip("/") + "/", url.lstrip("/"))


class Refused_NoTarget(Exception):
    pass


def run_http_status(ac: dict, ctx: Ctx) -> tuple[bool, str]:
    try:
        url = resolve_url(ac["url"], ctx.target_url)
    except Refused_NoTarget:
        return False, f"relative url {ac['url']!r} but registration has no target_url"
    code, _, err = _fetch(url)
    want = ac["expect"] if isinstance(ac["expect"], list) else [ac["expect"]]
    if code is None:
        return False, f"GET {url} failed: {err}"
    return code in want, f"GET {url} returned {code} (want {want})"


class _Collect(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.elems: list[tuple[str, dict]] = []

    def handle_starttag(self, tag, attrs):  # noqa: ANN001
        self.elems.append((tag, {k: (v or "") for k, v in attrs}))

    handle_startendtag = handle_starttag


_TOKEN = re.compile(r"""(?:(?P<tag>^[A-Za-z][\w-]*)|#(?P<id>[\w-]+)|\.(?P<cls>[\w-]+)|\[(?P<attr>[\w:-]+)(?:(?P<aop>[~|^$*]?=)(?P<aval>"[^"]*"|'[^']*'|[^\]]*))?\])""")


def parse_selector(sel: str) -> list[tuple[str, tuple]]:
    sel, toks, pos = sel.strip(), [], 0
    if not sel or re.search(r"[\s>+~,]", re.sub(r"\[[^\]]*\]", "", sel)):
        raise ValueError("only a single compound selector is supported (tag, #id, .class, [attr=val])")
    while pos < len(sel):
        m = _TOKEN.match(sel, pos)
        if not m or m.end() == pos:
            raise ValueError(f"unsupported selector syntax at {sel[pos:]!r}")
        if m.group("tag"):
            toks.append(("tag", (m.group("tag").lower(),)))
        elif m.group("id"):
            toks.append(("id", (m.group("id"),)))
        elif m.group("cls"):
            toks.append(("cls", (m.group("cls"),)))
        else:
            val = m.group("aval")
            if val is not None and val[:1] in "\"'":
                val = val[1:-1]
            toks.append(("attr", (m.group("attr"), m.group("aop"), val)))
        pos = m.end()
    return toks


def _elem_matches(tag: str, attrs: dict, toks: list) -> bool:
    for kind, a in toks:
        if kind == "tag" and tag != a[0]:
            return False
        if kind == "id" and attrs.get("id") != a[0]:
            return False
        if kind == "cls" and a[0] not in attrs.get("class", "").split():
            return False
        if kind == "attr":
            name, aop, val = a
            if name not in attrs:
                return False
            v = attrs[name]
            if aop == "=" and v != val:
                return False
            if aop == "~=" and val not in v.split():
                return False
            if aop == "^=" and not v.startswith(val):
                return False
            if aop == "$=" and not v.endswith(val):
                return False
            if aop == "*=" and val not in v:
                return False
    return True


def count_selector(html: str, selector: str) -> int:
    toks = parse_selector(selector)
    p = _Collect()
    p.feed(html)
    return sum(1 for tag, attrs in p.elems if _elem_matches(tag, attrs, toks))


def run_dom_check(ac: dict, ctx: Ctx) -> tuple[bool, str]:
    try:
        url = resolve_url(ac["url"], ctx.target_url)
    except Refused_NoTarget:
        return False, f"relative url {ac['url']!r} but registration has no target_url"
    code, body, err = _fetch(url)
    if code != 200:
        return False, f"GET {url} returned {code if code is not None else err}"
    try:
        n = count_selector(body, ac["selector"])
    except ValueError as e:
        return False, f"selector error: {e}"
    ok = OPS[ac["op"]](n, ac["value"])
    return ok, f"{url} selector {ac['selector']!r} matched {n} (want {ac['op']} {ac['value']}); static HTML only"


def run_command(ac: dict, ctx: Ctx) -> tuple[bool, str]:
    from . import sandbox

    exp = ac.get("expect") or {}
    res = sandbox.run(ctx.src, ac["run"], int(ac.get("timeout_s", ctx.cfg.get("limits", {}).get("command_timeout_s", 300))),
                      network=ctx.network, cfg=ctx.cfg)
    out = f"exit={res.exit_code}{' (timed out)' if res.timed_out else ''}\n--stdout--\n{res.stdout}\n--stderr--\n{res.stderr}"
    ok = (not res.timed_out) and res.exit_code == exp.get("exit_code", 0)
    rx = exp.get("stdout_regex")
    if ok and rx and not re.search(rx, res.stdout):
        ok = False
        out += f"\nstdout did not match /{rx}/"
    return ok, cap(out)


EXECUTORS = {"grep_count": run_grep_count, "http_status": run_http_status, "dom_check": run_dom_check, "command": run_command}


def run_all(ac_list: list[dict], ctx: Ctx) -> list[dict]:
    """Execute every non-judgment AC. Never reads worker-supplied output."""
    results = []
    for ac in ac_list:
        if ac["type"] == "judgment":
            continue
        try:
            ok, out = EXECUTORS[ac["type"]](ac, ctx)
        except Exception as e:  # noqa: BLE001 - an executor crash is a failed check, never a pass
            ok, out = False, f"executor error: {type(e).__name__}: {e}"
        results.append({"id": ac["id"], "type": ac["type"], "passed": bool(ok), "output": cap(out)})
    return results
