export type AccessLevel = "public" | "authenticated" | "verified";

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
  layer_c: string | null;
  verified: boolean;
  issuer_id: string | null;
  routed_public_key: string | null;
}

export interface DecodeResult {
  layer_a: string;
  layer_b: string;
  layer_c: string;
}
