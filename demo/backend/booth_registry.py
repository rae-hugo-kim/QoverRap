"""In-memory booth registry for visit-collection (stamp rally) — application layer.

A "booth" is a physical on-site location (gate, photo zone, sponsor stand) that
issues signed "visit markers" under an event operator's key. This is application
policy, NOT part of the QoverwRap patent claim.

Each booth maps to a registered trust issuer (the event *operator*). The operator's
single key signs every visit marker; the ``booth_id`` is metadata carried inside the
signed marker (Layer B), so it cannot be forged and two booths with identical
content still produce distinct badges (Seoul gate1 != Busan gate1).

What counts as "one booth" (split by city, by game, etc.) is an *operating* policy
expressed here as data — the implementation only guarantees that a distinct
``booth_id`` yields a distinct badge.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Booth:
    booth_id: str       # globally unique — the immutable id baked into the signed marker
    issuer_id: str      # which registered operator key signs/verifies this booth's markers
    booth_name: str     # display label
    collection: str     # stamp-rally group these booths belong to
    emoji: str          # badge glyph for the collection grid


# Demo seed. issuer_id MUST be a registered trust issuer (trust_registry.py) so the
# marker's Layer A routes to the operator's public key on re-verification.
_BOOTHS: dict[str, Booth] = {
    "tigers-seoul-gate1": Booth(
        "tigers-seoul-gate1", "tigers-2026", "서울 게이트1", "tigers-2026-stamprally", "⚾"
    ),
    "tigers-busan-gate1": Booth(
        "tigers-busan-gate1", "tigers-2026", "부산 게이트1", "tigers-2026-stamprally", "🌊"
    ),
    "tigers-fanzone": Booth(
        "tigers-fanzone", "tigers-2026", "팬존 포토부스", "tigers-2026-stamprally", "📸"
    ),
    "violet-popup": Booth(
        "violet-popup", "violet-fandom", "VF 팝업스토어", "violet-2026", "💜"
    ),
}


def list_booths() -> list[Booth]:
    return list(_BOOTHS.values())


def get_booth(booth_id: str) -> Optional[Booth]:
    return _BOOTHS.get(booth_id)
