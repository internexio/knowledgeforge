import re
from pathlib import Path

from kfgrader import stage2

ROOT = Path(__file__).resolve().parents[3]
AGENT = Path(__file__).resolve().parent.parent / "agent" / "kf-grader.md"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def test_tools_allowlist_is_read_only():
    text = AGENT.read_text()
    assert re.search(r"^tools: *Read, *Grep, *Glob *$", text, re.M)
    m = re.search(r"^disallowedTools: *(.*)$", text, re.M)
    assert {"Bash", "Edit", "Write", "NotebookEdit", "WebFetch"} <= {t.strip() for t in m.group(1).split(",")}
    d = stage2.agent_def()
    assert d["tools"] == ["Read", "Grep", "Glob"]
    assert "Bash" in d["disallowedTools"] and "Write" in d["disallowedTools"]


def test_untrusted_input_boundary_matches_module_07():
    src = (ROOT / "modules" / "07_critic_agent.md").read_text()
    m = re.search(r"## Untrusted Input Boundary\n\n(.*?)\n\n", src, re.S)
    assert m, "Module 07 Untrusted Input Boundary section not found"
    para = norm(m.group(1))
    agent = AGENT.read_text()
    assert "<!-- source: Module 07 Untrusted Input Boundary; keep in sync -->" in agent
    assert para in norm(agent), "agent file Untrusted Input Boundary drifted from Module 07"


def test_agent_body_within_budget_and_has_rubric_dimensions():
    body = AGENT.read_text().split("---\n", 2)[2]
    assert len(body.splitlines()) <= 150
    for dim in stage2.DIMS:
        assert dim in body
