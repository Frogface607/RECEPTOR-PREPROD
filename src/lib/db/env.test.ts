import { describe, expect, test } from "vitest";
import { isSupabaseAdminConfigured, isSupabaseConfigured } from "./env";

describe("isSupabaseConfigured", () => {
  test("false when url/key absent", () => {
    expect(isSupabaseConfigured({})).toBe(false);
  });

  test("false when only url present", () => {
    expect(
      isSupabaseConfigured({
        NEXT_PUBLIC_SUPABASE_URL: "https://abc.supabase.co",
      }),
    ).toBe(false);
  });

  test("false for placeholder values", () => {
    expect(
      isSupabaseConfigured({
        NEXT_PUBLIC_SUPABASE_URL: "your-url-here",
        NEXT_PUBLIC_SUPABASE_ANON_KEY: "your-anon-key",
      }),
    ).toBe(false);
  });

  test("true when a real-looking url + anon key are present", () => {
    expect(
      isSupabaseConfigured({
        NEXT_PUBLIC_SUPABASE_URL: "https://wzfcioqeejajhxrhcxqv.supabase.co",
        NEXT_PUBLIC_SUPABASE_ANON_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc",
      }),
    ).toBe(true);
  });

  test("requires the url to look like a supabase https endpoint", () => {
    expect(
      isSupabaseConfigured({
        NEXT_PUBLIC_SUPABASE_URL: "not-a-url",
        NEXT_PUBLIC_SUPABASE_ANON_KEY: "eyJhbGciOiJIUzI1NiJ9.real",
      }),
    ).toBe(false);
  });

  test("admin mode requires service role key", () => {
    const env = {
      NEXT_PUBLIC_SUPABASE_URL: "https://wzfcioqeejajhxrhcxqv.supabase.co",
      NEXT_PUBLIC_SUPABASE_ANON_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc",
    };

    expect(isSupabaseAdminConfigured(env)).toBe(false);
    expect(
      isSupabaseAdminConfigured({
        ...env,
        SUPABASE_SERVICE_ROLE_KEY: "service-role",
      }),
    ).toBe(true);
  });
});
