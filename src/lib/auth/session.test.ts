import { describe, expect, test } from "vitest";
import { resolveSessionUser, DEMO_USER } from "./session";

describe("resolveSessionUser", () => {
  test("demo mode (supabase absent) → synthetic demo user", () => {
    const user = resolveSessionUser({ configured: false, supabaseUser: null });
    expect(user).toEqual(DEMO_USER);
    expect(user?.isDemo).toBe(true);
  });

  test("configured + logged in → real user", () => {
    const user = resolveSessionUser({
      configured: true,
      supabaseUser: { id: "u1", email: "boss@frogface.space" },
    });
    expect(user).toEqual({
      id: "u1",
      email: "boss@frogface.space",
      isDemo: false,
    });
  });

  test("configured + not logged in → null (must authenticate)", () => {
    const user = resolveSessionUser({ configured: true, supabaseUser: null });
    expect(user).toBeNull();
  });

  test("demo user carries a stable id for fixtures", () => {
    expect(DEMO_USER.id).toBe("demo-user");
  });
});
