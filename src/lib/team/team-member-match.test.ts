import { describe, expect, test } from "vitest";
import {
  findStaffMemberByName,
  isLikelySameTeamMemberName,
  normalizeTeamMemberName,
} from "./team-member-match";
import type { StaffMember } from "./team-os";

const baseMember = {
  roleId: "service",
  venueId: "venue-1",
  status: "active",
  shiftLabel: "",
} satisfies Omit<StaffMember, "id" | "name">;

describe("team member name matching", () => {
  test("normalizes punctuation, case and yo letters", () => {
    expect(normalizeTeamMemberName("  Алёна-Сервис! ")).toBe("алена сервис");
  });

  test("matches short Team OS names to fuller iiko names", () => {
    expect(isLikelySameTeamMemberName("Мария", "Мария Иванова")).toBe(true);
    expect(isLikelySameTeamMemberName("Иван Петров", "Петров Иван")).toBe(
      true,
    );
  });

  test("does not choose a fuzzy match when staff candidates are ambiguous", () => {
    const staff: StaffMember[] = [
      { ...baseMember, id: "maria-1", name: "Мария" },
      { ...baseMember, id: "maria-2", name: "Мария И." },
    ];

    expect(findStaffMemberByName(staff, "Мария Иванова")).toBeUndefined();
  });
});
