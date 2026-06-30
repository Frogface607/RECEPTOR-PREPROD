import { describe, expect, it } from "vitest";
import { buildFocusedTeamTaskHref, buildTeamHref } from "./team-links";

describe("team links", () => {
  it("builds a Team OS link with the default manager role", () => {
    expect(
      buildTeamHref({
        venueId: "venue-1",
        hash: "#team-actions",
      }),
    ).toBe("/team?role=venue_manager&venueId=venue-1#team-actions");
  });

  it("preserves BI period params and focused task", () => {
    expect(
      buildTeamHref({
        venueId: "venue-1",
        hash: "#team-actions",
        periodParams: {
          period: "CUSTOM",
          from: "2026-05-01",
          to: "2026-06-01",
        },
        params: {
          focusTaskId: "task-1",
        },
      }),
    ).toBe(
      "/team?role=venue_manager&venueId=venue-1&period=CUSTOM&from=2026-05-01&to=2026-06-01&focusTaskId=task-1#team-actions",
    );
  });

  it("encodes venue and extra params safely", () => {
    expect(
      buildTeamHref({
        venueId: "venue with spaces",
        hash: "#team-actions",
        params: {
          prefillMemberName: "Мария Иванова",
        },
      }),
    ).toBe(
      "/team?role=venue_manager&venueId=venue+with+spaces&prefillMemberName=%D0%9C%D0%B0%D1%80%D0%B8%D1%8F+%D0%98%D0%B2%D0%B0%D0%BD%D0%BE%D0%B2%D0%B0#team-actions",
    );
  });

  it("focuses a created task without dropping the current team context", () => {
    expect(
      buildFocusedTeamTaskHref({
        venueId: "venue-1",
        taskId: "task-42",
        currentSearch:
          "role=operations_manager&period=CUSTOM&from=2026-05-01&to=2026-06-01",
      }),
    ).toBe(
      "/team?role=operations_manager&period=CUSTOM&from=2026-05-01&to=2026-06-01&venueId=venue-1&focusTaskId=task-42#team-actions",
    );
  });
});
