import { describe, expect, test } from "vitest";
import { buildSecondBrainLaunchPath } from "./second-brain-launch";

describe("second brain launch path", () => {
  test("starts with restaurant memory when there is no venue yet", () => {
    const path = buildSecondBrainLaunchPath({
      venue: null,
      firstVenueHref: "/onboarding?new=1",
    });

    expect(path.readyCount).toBe(0);
    expect(path.totalCount).toBe(5);
    expect(path.focus).toMatchObject({
      id: "context",
      title: "Память ресторана",
      href: "/onboarding?new=1",
    });
    expect(path.items.map((item) => item.id)).toEqual([
      "context",
      "people",
      "field_note",
      "advisor",
      "iiko",
    ]);
  });

  test("asks for a shift summary after context and people are ready", () => {
    const path = buildSecondBrainLaunchPath({
      firstVenueHref: "/dashboard/venue-1",
      venue: {
        id: "venue-1",
        iikoConnected: false,
        contextRequiredPercentage: 100,
        teamMembersCount: 4,
        fieldNotesCount: 0,
      },
    });

    expect(path.readyCount).toBe(2);
    expect(path.focus).toMatchObject({
      id: "field_note",
      status: "память пустая",
      action: "Оставить итог",
    });
  });

  test("opens the advisor when memory, people and field notes exist", () => {
    const path = buildSecondBrainLaunchPath({
      firstVenueHref: "/dashboard/venue-1",
      venue: {
        id: "venue-1",
        iikoConnected: true,
        contextRequiredPercentage: 100,
        teamMembersCount: 6,
        fieldNotesCount: 3,
      },
    });

    expect(path.readyCount).toBe(5);
    expect(path.focus.id).toBe("context");
    expect(path.headline).toContain("готов");
    expect(path.items.find((item) => item.id === "advisor")).toMatchObject({
      ready: true,
      href: "/dashboard/venue-1?chat=1",
      action: "Открыть советника",
    });
  });
});
