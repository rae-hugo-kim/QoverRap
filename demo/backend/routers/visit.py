"""Visit-collection (stamp rally) endpoints for the QoverwRap demo (M2).

Trust model B: an attendee presents their ticket at a booth → the booth verifies
the ticket signature (real member?) → on success the booth issues a "visit marker"
signed with the event operator's key → the marker accrues to the attendee's
collection. Unlike "scan a poster" models, this requires a *real member* to be
*physically there* presenting a valid ticket.

Identity-blind ("양자적 감정"): the marker binds to
``visitor_token = sha256(ticket Layer C)[:32]`` — deterministic per ticket, so a
holder's markers group together, yet no PII (name/seat/serial/holder) is carried.

The marker itself is a QoverwRap wire-format payload (Layer A + JSON Layer B +
Ed25519 Layer C), so it is independently re-verifiable offline (POST /visit/verify).

Application-layer only — the patent-frozen core (src/qoverwrap/) is reused, never modified.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from qoverwrap.crypto import sign_layers, verify_signature
from qoverwrap.decoder import decode_layers
from qoverwrap.encoder import encode_layers

from .. import booth_registry, trust_registry
from ..redemption_store import RedemptionStore
from ..schemas import (
    BoothInfo,
    BoothListResponse,
    VisitCollectRequest,
    VisitCollectResponse,
    VisitVerifyRequest,
    VisitVerifyResponse,
)
from .redeem import get_store

router = APIRouter(prefix="/api", tags=["visit"])

_KST = timezone(timedelta(hours=9))


def _require_demo_signing() -> None:
    """Marker issuance signs with an operator private key — gate like trust.py:46."""
    if os.environ.get("QWR_ENABLE_DEMO_SIGNING", "").strip() != "1":
        raise HTTPException(status_code=403, detail="demo signing disabled")


@router.get("/booths", response_model=BoothListResponse)
def list_booths() -> BoothListResponse:
    return BoothListResponse(
        booths=[
            BoothInfo(
                booth_id=b.booth_id,
                issuer_id=b.issuer_id,
                booth_name=b.booth_name,
                collection=b.collection,
                emoji=b.emoji,
            )
            for b in booth_registry.list_booths()
        ]
    )


@router.post("/visit/collect", response_model=VisitCollectResponse)
def visit_collect(
    req: VisitCollectRequest,
    store: RedemptionStore = Depends(get_store),
) -> VisitCollectResponse:
    _require_demo_signing()

    booth = booth_registry.get_booth(req.booth_id)
    if booth is None:
        raise HTTPException(status_code=404, detail="unknown_booth")

    # 1. Verify the presented ticket (trust model B: real member?). Decode failures
    #    are a malformed request (422); a well-formed but unverifiable ticket is a
    #    business outcome (200 ticket_invalid) — and must never touch the counter.
    try:
        ticket_a, ticket_b, ticket_c = decode_layers(req.ticket_payload)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # The ticket must be (a) a genuine valid signature from a registered issuer, AND
    # (b) issued by THIS booth's operator. An IU-concert ticket collects IU booths
    # only — that binding is fixed. A holder who ALSO bought a Tigers ticket collects
    # Tigers booths with THAT ticket without limit (different ticket → different event
    # → its own booths; one person can amass several event collections). Cross-event
    # (IU ticket → Tigers booth) is refused as wrong_issuer; forged / unregistered /
    # signatureless as ticket_invalid. Neither rejection touches the counter.
    ticket_issuer = trust_registry.parse_issuer(ticket_a)
    pub = trust_registry.route_public_key(ticket_a)
    if pub is None or not ticket_c or not verify_signature(pub, ticket_a, ticket_b, ticket_c):
        return VisitCollectResponse(status="ticket_invalid", booth_id=req.booth_id)
    if ticket_issuer != booth.issuer_id:
        return VisitCollectResponse(status="wrong_issuer", booth_id=req.booth_id)

    # 2. Identity-blind binding token: deterministic per ticket (Ed25519 sig is
    #    deterministic), carries no PII. Same ticket → same token; different ticket
    #    → different token. (Per-ticket grouping; per-member grouping across a
    #    holder's multiple tickets would be a separate credential-id layer.)
    visitor_token = hashlib.sha256(ticket_c).hexdigest()[:32]

    # Resolve the booth operator's key *before* consuming a slot — the config lookup
    # is cheap and side-effect-free, so a misconfigured booth must not burn a slot.
    entry = trust_registry.get_entry(booth.issuer_id)
    if entry is None:  # booth misconfigured against an unregistered operator
        raise HTTPException(status_code=500, detail="booth issuer not registered")

    # 3. One badge per (visitor_token × booth_id). Redeem FIRST so a duplicate visit
    #    skips marker signing entirely. booth_id lives inside the (later) signed Layer
    #    B, so a different booth_id is automatically a different badge.
    status, _ = store.redeem(f"visit:{booth.booth_id}:{visitor_token}", max_uses=1)
    if status != "ok":  # already_used → this ticket already collected this booth
        return VisitCollectResponse(
            status="already_collected",
            booth_id=booth.booth_id,
            booth_name=booth.booth_name,
            visitor_token=visitor_token,
            collection=booth.collection,
            emoji=booth.emoji,
        )

    # 4. Slot consumed → assemble + sign the visit marker under the operator's key.
    visited_at = datetime.now(tz=_KST).isoformat(timespec="seconds")
    marker_a = trust_registry.format_layer_a(booth.issuer_id, f"{booth.booth_name} 방문 마커")
    marker_b = json.dumps(
        {
            "kind": "visit",
            "booth_id": booth.booth_id,
            "booth_name": booth.booth_name,
            "visitor_token": visitor_token,
            "visited_at": visited_at,
            "collection": booth.collection,
        },
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    marker_c = sign_layers(entry.private_key, marker_a, marker_b)
    marker_payload = encode_layers(marker_a, marker_b, marker_c)
    return VisitCollectResponse(
        status="collected",
        booth_id=booth.booth_id,
        booth_name=booth.booth_name,
        visitor_token=visitor_token,
        visited_at=visited_at,
        collection=booth.collection,
        emoji=booth.emoji,
        marker_payload=marker_payload,
    )


@router.post("/visit/verify", response_model=VisitVerifyResponse)
def visit_verify(req: VisitVerifyRequest) -> VisitVerifyResponse:
    """Offline re-verification of a visit marker (no codec dependency)."""
    try:
        marker_a, marker_b, marker_c = decode_layers(req.marker_payload)
    except (TypeError, ValueError):
        return VisitVerifyResponse(verified=False)

    pub = trust_registry.route_public_key(marker_a)
    if pub is None or not marker_c or not verify_signature(pub, marker_a, marker_b, marker_c):
        return VisitVerifyResponse(verified=False)

    try:
        data = json.loads(marker_b)
    except (ValueError, UnicodeDecodeError):
        return VisitVerifyResponse(verified=False)
    if not isinstance(data, dict) or data.get("kind") != "visit":
        return VisitVerifyResponse(verified=False)

    return VisitVerifyResponse(
        verified=True,
        booth_id=data.get("booth_id"),
        booth_name=data.get("booth_name"),
        visitor_token=data.get("visitor_token"),
        visited_at=data.get("visited_at"),
        collection=data.get("collection"),
    )
