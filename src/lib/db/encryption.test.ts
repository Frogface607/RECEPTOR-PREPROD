import { describe, expect, test } from "vitest";
import { decryptSecret, encryptSecret } from "./encryption";

const env = {
  ENCRYPTION_KEY:
    "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
};

describe("credential encryption", () => {
  test("round-trips a secret as Supabase bytea hex strings", () => {
    const encrypted = encryptSecret("iiko-api-login-123", env);

    expect(encrypted.ciphertext).toMatch(/^\\x[0-9a-f]+$/);
    expect(encrypted.iv).toMatch(/^\\x[0-9a-f]{24}$/);
    expect(decryptSecret(encrypted, env)).toBe("iiko-api-login-123");
  });

  test("requires a 32-byte hex ENCRYPTION_KEY", () => {
    expect(() => encryptSecret("secret", { ENCRYPTION_KEY: "bad" })).toThrow(
      /ENCRYPTION_KEY/,
    );
  });
});
