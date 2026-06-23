import { describe, expect, test } from "vitest";
import { normalizeStaffLoginToEmail } from "./staff-login";

describe("staff login normalization", () => {
  test("keeps regular email logins", () => {
    expect(normalizeStaffLoginToEmail(" Manager@Example.Ru ")).toBe(
      "manager@example.ru",
    );
  });

  test("maps short staff logins to the internal domain", () => {
    expect(normalizeStaffLoginToEmail("masha.service")).toBe(
      "masha.service@staff.receptorai.pro",
    );
  });

  test("rejects unsafe short logins", () => {
    expect(normalizeStaffLoginToEmail("ма")).toBeNull();
    expect(normalizeStaffLoginToEmail("ab")).toBeNull();
  });
});
