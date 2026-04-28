import type {
  AccessLevel,
  DecodeResult,
  KeyPair,
  ResolveResult,
  TrustEntry,
} from "../types";

const BASE = "/api";

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
  if (!r.ok) {
    const detail = await r.text();
    throw new Error(`POST ${path} -> ${r.status}: ${detail}`);
  }
  return r.json();
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`GET ${path} -> ${r.status}`);
  return r.json();
}

export const api = {
  health: () => get<{ status: string }>("/health"),
  generateKey: () => post<KeyPair>("/generate-key", {}),
  sign: (private_key: string, layer_a: string, layer_b: string) =>
    post<{ signature: string }>("/sign", { private_key, layer_a, layer_b }),
  verify: (
    public_key: string,
    layer_a: string,
    layer_b: string,
    signature: string,
  ) =>
    post<{ valid: boolean }>("/verify", {
      public_key,
      layer_a,
      layer_b,
      signature,
    }),
  encode: (layer_a: string, layer_b: string, layer_c: string) =>
    post<{ encoded: string }>("/encode", { layer_a, layer_b, layer_c }),
  qrImage: (encoded: string, opts?: { box_size?: number; border?: number }) =>
    post<{ image_png_base64: string }>("/qr-image", {
      encoded,
      box_size: opts?.box_size ?? 8,
      border: opts?.border ?? 4,
      error_correction: "H",
    }),
  decode: (payload: string) =>
    post<DecodeResult>("/decode", { payload }),
  resolve: (
    payload: string,
    access_level: AccessLevel,
    public_key?: string,
  ) =>
    post<ResolveResult>("/resolve", {
      payload,
      access_level,
      ...(public_key ? { public_key } : {}),
    }),
  trustList: () => get<{ entries: TrustEntry[] }>("/trust"),
  trustSign: (issuer_id: string, layer_a: string, layer_b: string) =>
    post<{ issuer_id: string; signature: string; public_key: string }>(
      `/trust/${encodeURIComponent(issuer_id)}/sign`,
      { layer_a, layer_b },
    ),
};

// utf-8 string -> hex helper (browser-safe)
export function strToHex(s: string): string {
  const bytes = new TextEncoder().encode(s);
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export function hexToStr(hex: string): string {
  if (!hex) return "";
  const bytes = new Uint8Array(
    hex.match(/.{1,2}/g)?.map((b) => parseInt(b, 16)) ?? [],
  );
  return new TextDecoder().decode(bytes);
}
