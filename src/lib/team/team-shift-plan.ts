import { getTeamRole, type StaffMember } from "./team-os";

export type TeamShiftPlan = {
  id: string;
  venueId: string;
  memberId: string;
  shiftDate: string;
  shiftStart: string | null;
  shiftEnd: string | null;
  isDayOff: boolean;
  note: string;
  updatedAt: string;
};

export type TeamShiftPlanItem = {
  plan: TeamShiftPlan;
  dateLabel: string;
  timeLabel: string;
  hours: number;
  laborCost: number;
  missingRate: boolean;
};

export type TeamShiftPlanRow = {
  member: StaffMember;
  roleTitle: string;
  items: TeamShiftPlanItem[];
  plannedShifts: number;
  dayOffs: number;
  hours: number;
  laborCost: number;
  missingRateShifts: number;
};

export type TeamShiftPlanSummary = {
  rows: TeamShiftPlanRow[];
  plannedShifts: number;
  dayOffs: number;
  hours: number;
  laborCost: number;
  missingRateShifts: number;
};

export function buildTeamShiftPlanSummary(input: {
  staff: StaffMember[];
  plans: TeamShiftPlan[];
}): TeamShiftPlanSummary {
  const rows = input.staff
    .filter((member) => member.status !== "paused")
    .map((member) =>
      buildPlanRow({
        member,
        plans: input.plans.filter((plan) => plan.memberId === member.id),
      }),
    )
    .filter((row) => row.items.length > 0)
    .sort(
      (a, b) =>
        b.missingRateShifts - a.missingRateShifts ||
        b.plannedShifts - a.plannedShifts ||
        a.member.name.localeCompare(b.member.name, "ru"),
    );

  return {
    rows,
    plannedShifts: rows.reduce((sum, row) => sum + row.plannedShifts, 0),
    dayOffs: rows.reduce((sum, row) => sum + row.dayOffs, 0),
    hours: round(rows.reduce((sum, row) => sum + row.hours, 0)),
    laborCost: roundMoney(rows.reduce((sum, row) => sum + row.laborCost, 0)),
    missingRateShifts: rows.reduce(
      (sum, row) => sum + row.missingRateShifts,
      0,
    ),
  };
}

function buildPlanRow(input: {
  member: StaffMember;
  plans: TeamShiftPlan[];
}): TeamShiftPlanRow {
  const items = input.plans
    .slice()
    .sort((a, b) => {
      const dateDiff = a.shiftDate.localeCompare(b.shiftDate);
      if (dateDiff !== 0) return dateDiff;
      return (a.shiftStart ?? "").localeCompare(b.shiftStart ?? "");
    })
    .map((plan) => buildPlanItem(input.member, plan));

  return {
    member: input.member,
    roleTitle: getTeamRole(input.member.roleId).title,
    items,
    plannedShifts: items.filter((item) => !item.plan.isDayOff).length,
    dayOffs: items.filter((item) => item.plan.isDayOff).length,
    hours: round(items.reduce((sum, item) => sum + item.hours, 0)),
    laborCost: roundMoney(items.reduce((sum, item) => sum + item.laborCost, 0)),
    missingRateShifts: items.filter((item) => item.missingRate).length,
  };
}

function buildPlanItem(
  member: StaffMember,
  plan: TeamShiftPlan,
): TeamShiftPlanItem {
  const hours = plan.isDayOff
    ? 0
    : getShiftHours(plan.shiftStart, plan.shiftEnd);
  const missingRate =
    !plan.isDayOff &&
    hours > 0 &&
    (member.hourlyRate ?? 0) <= 0 &&
    (member.shiftPay ?? 0) <= 0;
  const laborCost =
    plan.isDayOff || missingRate
      ? 0
      : roundMoney(hours * (member.hourlyRate ?? 0) + (member.shiftPay ?? 0));

  return {
    plan,
    dateLabel: formatShiftPlanDate(plan.shiftDate),
    timeLabel: plan.isDayOff
      ? "выходной"
      : `${plan.shiftStart ?? "--:--"}-${plan.shiftEnd ?? "--:--"}`,
    hours,
    laborCost,
    missingRate,
  };
}

export function getShiftHours(
  shiftStart: string | null,
  shiftEnd: string | null,
): number {
  const start = parseTimeToMinutes(shiftStart);
  const end = parseTimeToMinutes(shiftEnd);
  if (start === null || end === null) return 0;

  const diff = end > start ? end - start : end + 24 * 60 - start;
  return round(diff / 60);
}

function parseTimeToMinutes(value: string | null): number | null {
  if (!value || !/^\d{2}:\d{2}$/.test(value)) return null;
  const [hoursRaw, minutesRaw] = value.split(":");
  const hours = Number(hoursRaw);
  const minutes = Number(minutesRaw);
  if (
    !Number.isInteger(hours) ||
    !Number.isInteger(minutes) ||
    hours < 0 ||
    hours > 23 ||
    minutes < 0 ||
    minutes > 59
  ) {
    return null;
  }
  return hours * 60 + minutes;
}

export function formatShiftPlanDate(dateKey: string): string {
  const date = new Date(`${dateKey}T12:00:00`);
  if (Number.isNaN(date.getTime())) return dateKey;

  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    weekday: "short",
  }).format(date);
}

function round(value: number): number {
  return Math.round(value * 10) / 10;
}

function roundMoney(value: number): number {
  return Math.round(value);
}
