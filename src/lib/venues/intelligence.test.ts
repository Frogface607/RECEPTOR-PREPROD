import { describe, expect, test } from "vitest";
import {
  DEFAULT_VENUE_INTELLIGENCE,
  normalizeVenueProfile,
} from "./intelligence";

describe("normalizeVenueProfile", () => {
  test("returns default profile for invalid data", () => {
    expect(normalizeVenueProfile(null)).toEqual(DEFAULT_VENUE_INTELLIGENCE);
  });

  test("fills missing arrays from defaults", () => {
    const profile = normalizeVenueProfile({
      format: "Гастробар",
      positioning: "Авторская кухня и вечерняя посадка",
      researchStatus: "researched",
    });

    expect(profile.format).toBe("Гастробар");
    expect(profile.positioning).toBe("Авторская кухня и вечерняя посадка");
    expect(profile.researchStatus).toBe("researched");
    expect(profile.ownerGoals.length).toBeGreaterThan(0);
  });
});
