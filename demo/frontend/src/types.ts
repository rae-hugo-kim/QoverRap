export type AccessLevel = "public" | "authenticated" | "verified";

export type LayerBFormat = "json" | "cbor" | "cbor_aggr";

export type SchemaKind = "baseball_ticket" | "festival_pass" | "wristband";

/** Mirrors the backend TicketLayerB schema (layer_b_codec.py, schema_id 1). */
export interface BaseballTicket {
  kind: "baseball_ticket";
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

/** Mirrors the backend FestivalPass schema (layer_b_codec.py, schema_id 2). */
export interface FestivalPass {
  kind: "festival_pass";
  /** required */
  festival_id: string;
  /** required */
  serial: string;
  /** required — ISO 8601 */
  issued_at: string;
  /** optional (default "") — day label, NOT a timestamp */
  day?: string;
  zone?: string;
  tier?: string;
  gate?: string;
  holder?: string;
}

/** Mirrors the backend Wristband schema (layer_b_codec.py, schema_id 3). */
export interface Wristband {
  kind: "wristband";
  /** required */
  band_id: string;
  /** required */
  serial: string;
  /** required — ISO 8601 */
  issued_at: string;
  /** optional (default "") */
  tier?: string;
  /** optional (default "") — ISO 8601 expiry */
  valid_until?: string;
  holder?: string;
}

/** Discriminated union over the backend Layer B schema catalog, keyed on `kind`. */
export type LayerBTicket = BaseballTicket | FestivalPass | Wristband;

/** Field descriptor from GET /api/schemas (catalog.py → SchemaFieldInfo). */
export interface SchemaFieldInfo {
  name: string;
  required: boolean;
  is_timestamp: boolean;
}

/** A single Layer B schema descriptor from GET /api/schemas (SchemaInfo). */
export interface SchemaInfo {
  kind: string;
  schema_id: number;
  fields: SchemaFieldInfo[];
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
  /** Layer B schema kinds this issuer may emit (trust_registry.py). */
  allowed_schemas: string[];
}

export interface ResolveResult {
  layer_a: string;
  layer_b: string | null;
  /** Layer B decoded via the demo codec; null when Layer B is absent/empty/undecodable */
  layer_b_ticket?: LayerBTicket | null;
  /** Layer B serialization format derived from the leading tag byte */
  layer_b_format?: LayerBFormat | null;
  /** Decoded Layer B schema kind; null when Layer B is absent/empty/undecodable */
  layer_b_schema?: string | null;
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
