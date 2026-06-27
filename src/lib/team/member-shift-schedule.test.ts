import { describe, expect, test } from "vitest";
import { buildMemberShiftSchedule } from "./member-shift-schedule";
import type { StaffMember } from "./team-os";

const member: StaffMember = {
  id: "staff-service",
  name: "Маша",
  roleId: "service",
  venueId: "dev-venue",
  status: "active",
  shiftLabel: "зал",
  hourlyRate: 350,
};

describe("buildMemberShiftSchedule", () => {
  test("matches plain iiko employee shifts by staff name", () => {
    const schedule = buildMemberShiftSchedule({
      member,
      shifts: [
        {
          shiftId: "shift-1",
          openTime: "2026-06-26T16:00:00",
          closeTime: "2026-06-27T00:00:00",
          revenue: 90000,
          items: 160,
          employee: "Маша",
        },
      ],
    });

    expect(schedule).toMatchObject([
      {
        shiftId: "shift-1",
        dateKey: "2026-06-26",
        revenue: 90000,
        items: 160,
        hours: 8,
      },
    ]);
    expect(schedule[0]?.timeLabel).toContain("16:00");
  });

  test("matches worker rows by member id and uses worker sales and hours", () => {
    const schedule = buildMemberShiftSchedule({
      member,
      shifts: [
        {
          shiftId: "shift-2",
          openTime: "2026-06-26T12:00:00",
          closeTime: "2026-06-26T22:00:00",
          revenue: 120000,
          items: 220,
          employee: "Смена",
          workers: [
            {
              memberId: "staff-service",
              name: "Мария",
              hours: 7.5,
              sales: 45000,
            },
            {
              memberId: "staff-cook",
              name: "Илья",
              hours: 10,
              sales: 75000,
            },
          ],
        },
      ],
    });

    expect(schedule[0]).toMatchObject({
      shiftId: "shift-2",
      revenue: 45000,
      hours: 7.5,
    });
  });

  test("sorts shifts and skips unrelated employees", () => {
    const schedule = buildMemberShiftSchedule({
      member,
      shifts: [
        {
          shiftId: "late",
          openTime: "2026-06-28T18:00:00",
          closeTime: "2026-06-29T03:00:00",
          revenue: 70000,
          items: 120,
          employee: "Маша",
        },
        {
          shiftId: "other",
          openTime: "2026-06-27T18:00:00",
          closeTime: "2026-06-28T03:00:00",
          revenue: 80000,
          items: 140,
          employee: "Илья",
        },
        {
          shiftId: "early",
          openTime: "2026-06-26T18:00:00",
          closeTime: "2026-06-27T03:00:00",
          revenue: 90000,
          items: 150,
          employee: "Маша",
        },
      ],
    });

    expect(schedule.map((item) => item.shiftId)).toEqual(["early", "late"]);
  });
});
