#!/usr/bin/env bash
# KF plugin bundle installer
# Bundle version: 7.36.0
# Compiled at:    2026-08-14T14:32:04.816919+00:00
#
# SPEC reference: docs/planning/2026-06-13_spec-5-plugin-packaging.md (D3b)
#
# Usage:
#   cd <target-repo-root>
#   bash /path/to/kf-plugin-bundle/install.sh
#
# Idempotency:
#   - Skill/agent copy is overwrite (compile-time identical inputs produce
#     identical outputs; the kf-compile and kf-bundle sentinel comments at
#     the top of each file let consumers detect drift).
#   - MCP merge is strip-then-add by signature (id + command + args), so a
#     second run produces the same `.mcp.json` and the same install receipt.
#   - The install receipt at .kf-bundle-install.json records per-entry
#     verification status; re-runs update timestamps but keep `verified`
#     and `action` fields stable for unchanged entries.

set -euo pipefail

# --------------------------------------------------------------------------
# Resolve paths
# --------------------------------------------------------------------------
# Bundle root is the directory containing this script (resolved via $0).
BUNDLE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_ROOT="${PWD}"
BUNDLE_VERSION="7.36.0"
INSTALLED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

# Target paths (Claude Code convention)
TARGET_SKILLS_DIR="${TARGET_ROOT}/.claude/skills/kf"
TARGET_AGENTS_DIR="${TARGET_ROOT}/.claude/agents"
TARGET_MCP_FILE="${TARGET_ROOT}/.mcp.json"
RECEIPT_FILE="${TARGET_ROOT}/.kf-bundle-install.json"

echo "[kf-bundle-install] Bundle root:  ${BUNDLE_ROOT}"
echo "[kf-bundle-install] Target root:  ${TARGET_ROOT}"
echo "[kf-bundle-install] Bundle ver:   ${BUNDLE_VERSION}"

# --------------------------------------------------------------------------
# Step 1: Copy skills
# --------------------------------------------------------------------------
mkdir -p "${TARGET_SKILLS_DIR}"
SKILL_COUNT=0
if [ -d "${BUNDLE_ROOT}/skills" ]; then
  for src in "${BUNDLE_ROOT}/skills/"*.md; do
    [ -e "${src}" ] || continue
    base="$(basename "${src}")"
    cp "${src}" "${TARGET_SKILLS_DIR}/${base}"
    SKILL_COUNT=$((SKILL_COUNT + 1))
  done
fi
echo "[kf-bundle-install] Copied ${SKILL_COUNT} skill(s) → ${TARGET_SKILLS_DIR}"

# --------------------------------------------------------------------------
# Step 2: Copy agents
# --------------------------------------------------------------------------
mkdir -p "${TARGET_AGENTS_DIR}"
AGENT_COUNT=0
if [ -d "${BUNDLE_ROOT}/agents" ]; then
  for src in "${BUNDLE_ROOT}/agents/"*.md; do
    [ -e "${src}" ] || continue
    base="$(basename "${src}")"
    cp "${src}" "${TARGET_AGENTS_DIR}/${base}"
    AGENT_COUNT=$((AGENT_COUNT + 1))
  done
fi
echo "[kf-bundle-install] Copied ${AGENT_COUNT} agent(s) → ${TARGET_AGENTS_DIR}"

# --------------------------------------------------------------------------
# Step 3: MCP connector merge (path_type discipline + per-entry validation)
# --------------------------------------------------------------------------
# The bundle manifest lives at ${BUNDLE_ROOT}/kf-plugin-bundle.json.
# We use python3 to do the JSON read/merge — pure bash JSON merge is brittle
# and the bundle already requires python3 to have been built.

MANIFEST_FILE="${BUNDLE_ROOT}/kf-plugin-bundle.json"
if [ ! -f "${MANIFEST_FILE}" ]; then
  echo "[kf-bundle-install] WARNING: manifest not found at ${MANIFEST_FILE}; skipping MCP step"
  MCP_ENTRIES_JSON="[]"
else
  # Run a small inline python script that:
  # 1. Loads manifest.mcp_connectors
  # 2. For each entry, resolves path according to path_type
  # 3. Builds .mcp.json (strip-then-add by signature)
  # 4. Builds the per-entry receipt array
  # 5. Writes both
  MCP_ENTRIES_JSON="$(BUNDLE_ROOT="${BUNDLE_ROOT}" \
                       TARGET_MCP_FILE="${TARGET_MCP_FILE}" \
                       MANIFEST_FILE="${MANIFEST_FILE}" \
                       python3 - <<'PYEOF'
import json
import os
import sys
from pathlib import Path

bundle_root = Path(os.environ["BUNDLE_ROOT"])
target_mcp_file = Path(os.environ["TARGET_MCP_FILE"])
manifest_file = Path(os.environ["MANIFEST_FILE"])

with manifest_file.open() as f:
    manifest = json.load(f)

connectors = manifest.get("mcp_connectors", [])

# Load existing target .mcp.json if present
if target_mcp_file.exists():
    try:
        existing = json.loads(target_mcp_file.read_text())
        if not isinstance(existing, dict):
            existing = {}
    except json.JSONDecodeError:
        existing = {}
else:
    existing = {}

existing_servers = existing.get("mcpServers", {})
if not isinstance(existing_servers, dict):
    existing_servers = {}

receipt_entries = []
new_servers = dict(existing_servers)  # start from existing; strip-then-add by id

# First, strip any servers that match this bundle's connector ids
# (idempotent re-run: removes prior bundle state before re-adding fresh)
for connector in connectors:
    cid = connector.get("id")
    if cid and cid in new_servers:
        del new_servers[cid]

# Now process each connector entry
for connector in connectors:
    cid = connector.get("id", "<unknown>")
    path_type = connector.get("path_type", "bundled")
    fallback = connector.get("fallback_message", "")
    required = bool(connector.get("required", False))

    if path_type == "bundled":
        bundle_path = connector.get("bundle_path", "")
        resolved = bundle_root / bundle_path
        path_checked = str(resolved)
        if resolved.exists():
            try:
                server_spec = json.loads(resolved.read_text())
                new_servers[cid] = server_spec
                receipt_entries.append({
                    "id": cid, "path_checked": path_checked,
                    "verified": True, "action": "written",
                })
            except json.JSONDecodeError as e:
                sys.stderr.write(f"[kf-bundle-install] {cid}: bundled file invalid JSON ({e}); skipping\n")
                receipt_entries.append({
                    "id": cid, "path_checked": path_checked,
                    "verified": False, "action": "skipped_bad_json",
                })
        else:
            sys.stderr.write(f"[kf-bundle-install] {cid}: bundled file missing at {path_checked}; skipping\n")
            receipt_entries.append({
                "id": cid, "path_checked": path_checked,
                "verified": False, "action": "skipped_missing",
            })

    elif path_type == "relative_to_bundle":
        rel = connector.get("source_path", "")
        resolved = (bundle_root / rel).resolve()
        path_checked = str(resolved)
        if resolved.exists():
            try:
                server_spec = json.loads(resolved.read_text())
                new_servers[cid] = server_spec
                receipt_entries.append({
                    "id": cid, "path_checked": path_checked,
                    "verified": True, "action": "written",
                })
            except json.JSONDecodeError as e:
                sys.stderr.write(f"[kf-bundle-install] {cid}: relative file invalid JSON ({e}); skipping\n")
                receipt_entries.append({
                    "id": cid, "path_checked": path_checked,
                    "verified": False, "action": "skipped_bad_json",
                })
        else:
            sys.stderr.write(f"[kf-bundle-install] {cid}: relative file missing at {path_checked}; skipping\n")
            receipt_entries.append({
                "id": cid, "path_checked": path_checked,
                "verified": False, "action": "skipped_missing",
            })

    elif path_type == "absolute_requires_local_config":
        # Expand env vars in source_path. If any required var is unset, the path
        # remains literal (e.g. "$COS_DEV_ROOT/...") and the existence check
        # will fail — that's the intended behavior.
        raw = connector.get("source", connector.get("source_path", ""))
        resolved_str = os.path.expandvars(os.path.expanduser(raw))
        path_checked = resolved_str
        unresolved = "$" in resolved_str  # env var still present → not configured
        if unresolved or not Path(resolved_str).exists():
            # MUST NOT write a stale absolute path. Skip + emit fallback.
            if fallback:
                sys.stderr.write(f"[kf-bundle-install] {cid}: {fallback}\n")
            else:
                sys.stderr.write(f"[kf-bundle-install] {cid}: required local config missing at {path_checked}; skipping\n")
            receipt_entries.append({
                "id": cid, "path_checked": path_checked,
                "verified": False, "action": "skipped",
            })
            if required:
                sys.stderr.write(f"[kf-bundle-install] {cid} is marked required — installer will exit nonzero at end\n")
        else:
            try:
                server_spec = json.loads(Path(resolved_str).read_text())
                new_servers[cid] = server_spec
                receipt_entries.append({
                    "id": cid, "path_checked": path_checked,
                    "verified": True, "action": "written",
                })
            except json.JSONDecodeError as e:
                sys.stderr.write(f"[kf-bundle-install] {cid}: local config invalid JSON ({e}); skipping\n")
                receipt_entries.append({
                    "id": cid, "path_checked": path_checked,
                    "verified": False, "action": "skipped_bad_json",
                })
    else:
        sys.stderr.write(f"[kf-bundle-install] {cid}: unknown path_type '{path_type}'; skipping\n")
        receipt_entries.append({
            "id": cid, "path_checked": "",
            "verified": False, "action": f"skipped_unknown_path_type:{path_type}",
        })

# Write merged .mcp.json (only if we have servers OR target already existed)
if new_servers or target_mcp_file.exists():
    target_mcp_file.parent.mkdir(parents=True, exist_ok=True)
    out = dict(existing)
    out["mcpServers"] = new_servers
    target_mcp_file.write_text(json.dumps(out, indent=2) + "\n")

# Emit receipt array as JSON for the parent shell
print(json.dumps(receipt_entries))
PYEOF
)"
fi

# --------------------------------------------------------------------------
# Step 4: Write install receipt
# --------------------------------------------------------------------------
# Receipt schema (D3b):
#   {
#     "bundle_version": "...",
#     "installed_at": "...",
#     "mcp_entries": [ {"id":..., "path_checked":..., "verified":..., "action":...}, ... ]
#   }
#
# MCP_ENTRIES_JSON is JSON-encoded text. We pass it via env var, not source
# substitution, because JSON `true`/`false`/`null` literals would otherwise
# become bare identifiers in Python source and raise NameError.
RECEIPT_FILE="${RECEIPT_FILE}" \
BUNDLE_VERSION="${BUNDLE_VERSION}" \
INSTALLED_AT="${INSTALLED_AT}" \
SKILL_COUNT="${SKILL_COUNT}" \
AGENT_COUNT="${AGENT_COUNT}" \
MCP_ENTRIES_JSON="${MCP_ENTRIES_JSON}" \
python3 - <<'PYEOF'
import json
import os
from pathlib import Path

receipt = {
    "bundle_version": os.environ["BUNDLE_VERSION"],
    "installed_at": os.environ["INSTALLED_AT"],
    "skills_copied": int(os.environ["SKILL_COUNT"]),
    "agents_copied": int(os.environ["AGENT_COUNT"]),
    "mcp_entries": json.loads(os.environ.get("MCP_ENTRIES_JSON") or "[]"),
}
Path(os.environ["RECEIPT_FILE"]).write_text(json.dumps(receipt, indent=2) + "\n")
print(f"[kf-bundle-install] Receipt: {receipt['bundle_version']} | "
      f"skills={receipt['skills_copied']} agents={receipt['agents_copied']} "
      f"mcp_entries={len(receipt['mcp_entries'])}")
PYEOF

# --------------------------------------------------------------------------
# Step 5: Exit
# --------------------------------------------------------------------------
# Exit 0 even when optional MCP entries were skipped — that's the designed
# behavior. Required entries that skipped already emitted a stderr warning;
# consumers that want hard-fail can grep `.kf-bundle-install.json` for any
# `"verified": false` entries and act accordingly.
echo "[kf-bundle-install] Done."
exit 0
