"""Verdict files: ed25519-signed, bound to head_sha. `verify` needs only the public key."""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .registry import atomic_write, check_task_id, test_mode

SIG_FIELDS = ("content_sha256", "signature")


def ensure_keys(h: Path) -> None:
    key, pub = h / "keys" / "verdict.key", h / "keys" / "verdict.pub"
    if key.exists() and pub.exists():
        return
    priv = Ed25519PrivateKey.generate()
    atomic_write(
        key,
        priv.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode(),
        mode=0o600,
    )
    atomic_write(
        pub,
        priv.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode(),
        mode=0o644,
    )


def canonical(v: dict) -> bytes:
    body = {k: val for k, val in v.items() if k not in SIG_FIELDS}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sign(h: Path, v: dict) -> dict:
    priv = serialization.load_pem_private_key((h / "keys" / "verdict.key").read_bytes(), password=None)
    c = canonical(v)
    v["content_sha256"] = hashlib.sha256(c).hexdigest()
    v["signature"] = base64.b64encode(priv.sign(c)).decode()
    return v


def check_signature(h: Path, v: dict) -> tuple[bool, str]:
    try:
        c = canonical(v)
        if v.get("content_sha256") != hashlib.sha256(c).hexdigest():
            return False, "content_sha256 mismatch"
        pub = serialization.load_pem_public_key((h / "keys" / "verdict.pub").read_bytes())
        pub.verify(base64.b64decode(v.get("signature", ""), validate=True), c)
        return True, "ok"
    except (InvalidSignature, binascii.Error, ValueError, TypeError, KeyError, OSError) as e:
        return False, f"signature invalid ({type(e).__name__})"


def verdict_dir(h: Path, task_id: str) -> Path:
    return h / "verdicts" / check_task_id(task_id)


def load_all(h: Path, task_id: str) -> list[tuple[Path, dict | None]]:
    out = []
    for p in sorted(verdict_dir(h, task_id).glob("attempt-*.json")):
        try:
            out.append((p, json.loads(p.read_text())))
        except (ValueError, OSError):
            out.append((p, None))
    return out


def load_valid(h: Path, task_id: str) -> list[dict]:
    """Verdicts whose signature verifies, oldest first (by seq). Forged files are ignored."""
    good = [v for _, v in load_all(h, task_id) if v is not None and check_signature(h, v)[0]]
    return sorted(good, key=lambda v: v.get("seq", 0))


def next_name(h: Path, task_id: str, attempt: int) -> str:
    d = verdict_dir(h, task_id)
    name, k = f"attempt-{attempt}.json", 0
    while (d / name).exists():
        k += 1
        name = f"attempt-{attempt}.{k}.json"
    return name


def write(h: Path, v: dict, name: str) -> None:
    d = verdict_dir(h, v["task_id"])
    d.mkdir(parents=True, exist_ok=True)
    atomic_write(d / name, json.dumps(v, indent=2, sort_keys=True) + "\n", mode=0o600)


def verify(h: Path, task_id: str, head_sha: str, allow_test: bool = False) -> tuple[bool, str]:
    """True iff a signed PASS verdict exists for exactly this head_sha. Scans every attempt file."""
    seen_forged = 0
    for _, v in load_all(h, task_id):
        if v is None:
            seen_forged += 1
            continue
        ok, why = check_signature(h, v)
        if not ok:
            seen_forged += 1
            continue
        if v.get("head_sha") != head_sha or v.get("verdict") != "PASS":
            continue
        if v.get("test_mode") and not allow_test:
            return False, "verdict was produced in test mode; pass --allow-test to accept"
        return True, f"PASS verdict attempt {v.get('attempt')} for {head_sha[:12]}"
    return False, f"no valid PASS verdict for head {head_sha[:12]}" + (f" ({seen_forged} unverifiable file(s) ignored)" if seen_forged else "")
