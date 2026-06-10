/**
 * AES-256-GCM encryption for stored integration credentials.
 *
 * Supabase stores `bytea` as hex strings through PostgREST, so helpers return
 * `\x...` values that can be inserted directly into bytea columns.
 */

import { createCipheriv, createDecipheriv, randomBytes } from "crypto";

const IV_BYTES = 12;
const AUTH_TAG_BYTES = 16;

function encryptionKey(env: Record<string, string | undefined> = process.env): Buffer {
  const raw = (env.ENCRYPTION_KEY ?? "").trim();
  if (!/^[a-f0-9]{64}$/i.test(raw)) {
    throw new Error("ENCRYPTION_KEY must be a 32-byte hex string");
  }
  return Buffer.from(raw, "hex");
}

function toByteaHex(bytes: Buffer): string {
  return `\\x${bytes.toString("hex")}`;
}

function fromByteaHex(value: string | Uint8Array): Buffer {
  if (value instanceof Uint8Array) return Buffer.from(value);
  const hex = value.startsWith("\\x") ? value.slice(2) : value;
  return Buffer.from(hex, "hex");
}

export type EncryptedValue = {
  ciphertext: string;
  iv: string;
};

export function encryptSecret(
  plaintext: string,
  env: Record<string, string | undefined> = process.env,
): EncryptedValue {
  const iv = randomBytes(IV_BYTES);
  const cipher = createCipheriv("aes-256-gcm", encryptionKey(env), iv);
  const encrypted = Buffer.concat([
    cipher.update(plaintext, "utf8"),
    cipher.final(),
    cipher.getAuthTag(),
  ]);

  return {
    ciphertext: toByteaHex(encrypted),
    iv: toByteaHex(iv),
  };
}

export function decryptSecret(
  encrypted: EncryptedValue,
  env: Record<string, string | undefined> = process.env,
): string {
  const payload = fromByteaHex(encrypted.ciphertext);
  const iv = fromByteaHex(encrypted.iv);
  const body = payload.subarray(0, -AUTH_TAG_BYTES);
  const tag = payload.subarray(-AUTH_TAG_BYTES);

  const decipher = createDecipheriv("aes-256-gcm", encryptionKey(env), iv);
  decipher.setAuthTag(tag);
  return Buffer.concat([decipher.update(body), decipher.final()]).toString(
    "utf8",
  );
}
