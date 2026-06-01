export type AccessLevel = "public" | "authenticated" | "verified";

export type LayerBFormat = "json" | "cbor" | "cbor_aggr";

/** Mirrors the backend TicketLayerB schema (layer_b_codec.py). */
export interface TicketLayerB {
  kind?: "ticket";
  /** required */
  event_id: string;
  /** required */
  serial: string;
  /** required — ISO 8601 */
  issued_at: string;
  /** optional (default "") */
  section?: string;
  seat?: string;
  gate?: string;
  datetime?: string;
  opponent?: string;
  holder?: string;
}

export interface KeyPair {
  private_key: string;
  public_key: string;
}

export interface TrustEntry {
  issuer_id: string;
  display_name: string;
  theme_color: string;
  accent_color: string;
  logo_text: string;
  public_key: string;
}

export interface ResolveResult {
  layer_a: string;
  layer_b: string | null;
  /** Layer B decoded via the demo codec; null when Layer B is absent/empty/undecodable */
  layer_b_ticket?: TicketLayerB | null;
  /** Layer B serialization format derived from the leading tag byte */
  layer_b_format?: LayerBFormat | null;
  /** Hex Ed25519 signature when verified; diagnostic only */
  signature: string | null;
  verified: boolean;
  issuer_id: string | null;
  routed_public_key: string | null;
}

export interface DecodeResult {
  layer_a: string;
  layer_b: string;
  layer_c: string;
}

// ---- visit collection (stamp rally) ----------------------------------------

export interface BoothInfo {
  booth_id: string;
  issuer_id: string;
  booth_name: string;
  collection: string;
  emoji: string;
}

export interface VisitCollectResponse {
  status: "collected" | "already_collected" | "ticket_invalid" | "wrong_issuer";
  booth_id: string;
  booth_name?: string | null;
  /** sha256(ticket Layer C)[:32] — pseudonymous, no PII */
  visitor_token?: string | null;
  visited_at?: string | null;
  collection?: string | null;
  emoji?: string | null;
  /** full wire-format marker for offline re-verification (collected only) */
  marker_payload?: string | null;
}

export interface VisitVerifyResponse {
  verified: boolean;
  booth_id?: string | null;
  booth_name?: string | null;
  visitor_token?: string | null;
  visited_at?: string | null;
  collection?: string | null;
}
