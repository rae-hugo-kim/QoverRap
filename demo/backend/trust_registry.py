"""In-memory trust registry mapping issuer-id -> Ed25519 public key + UI theme.

This module is application-layer policy, NOT part of the QoverwRap patent claim.
The patent claim is about the payload structure (single QR with delimiter + base64
header containing 3 logical layers + embedded signature). The registry is one of
many ways a service operator could deploy that technology.

Layer A convention:
    qwr:<issuer-id>|<human-readable message>

The issuer-id is parsed from the prefix; if absent, no routing is performed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from qoverwrap.crypto import generate_keypair


PREFIX = "qwr:"
SEPARATOR = "|"


@dataclass(frozen=True)
class TrustEntry:
    issuer_id: str
    display_name: str
    theme_color: str
    accent_color: str
    logo_text: str
    private_key: bytes  # demo-only; real deployments would NEVER ship private keys
    public_key: bytes


def _build_demo_registry() -> dict[str, TrustEntry]:
    """Generate a fresh keypair per demo issuer at process start.

    Demo-only: each backend restart issues new keys. Themed QR codes signed in
    one session are not verifiable across restarts. Acceptable for the demo.
    """
    issuers = [
        ("tigers-2026", "Tigers Baseball Club", "#000000", "#FFCC00", "TIGERS"),
        ("violet-fandom", "Violet Fandom", "#6E00B3", "#F2C7FF", "V"),
        ("comic-con-2026", "Comic Con 2026", "#0A2540", "#FF4D6D", "CC26"),
    ]
    out: dict[str, TrustEntry] = {}
    for issuer_id, display_name, color, accent, logo in issuers:
        priv, pub = generate_keypair()
        out[issuer_id] = TrustEntry(
            issuer_id=issuer_id,
            display_name=display_name,
            theme_color=color,
            accent_color=accent,
            logo_text=logo,
            private_key=priv,
            public_key=pub,
        )
    return out


_REGISTRY: dict[str, TrustEntry] = _build_demo_registry()


def list_entries() -> list[TrustEntry]:
    return list(_REGISTRY.values())


def get_entry(issuer_id: str) -> Optional[TrustEntry]:
    return _REGISTRY.get(issuer_id)


def parse_issuer(layer_a: str) -> Optional[str]:
    """Extract issuer-id from a Layer A string with the qwr: convention.

    Returns None if Layer A does not start with qwr: or has no separator.
    """
    if not layer_a.startswith(PREFIX):
        return None
    rest = layer_a[len(PREFIX):]
    if SEPARATOR not in rest:
        return None
    issuer_id, _ = rest.split(SEPARATOR, maxsplit=1)
    return issuer_id or None


def route_public_key(layer_a: str) -> Optional[bytes]:
    """Look up the trusted public key for the issuer encoded in Layer A.

    Returns the public key bytes if the issuer is registered, else None.
    """
    issuer = parse_issuer(layer_a)
    if issuer is None:
        return None
    entry = _REGISTRY.get(issuer)
    return entry.public_key if entry else None


def format_layer_a(issuer_id: str, message: str) -> str:
    """Convenience helper to build a properly prefixed Layer A string."""
    return f"{PREFIX}{issuer_id}{SEPARATOR}{message}"
