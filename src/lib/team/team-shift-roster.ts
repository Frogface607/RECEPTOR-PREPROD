import type { LaborBiSummary, LaborShiftInput } from "./labor-bi";
import {
  buildMemberLaborProfile,
  buildMemberShiftSchedule,
  type MemberLaborProfileStatus,
} from "./member-shift-schedule";
import { getTeamRole, type StaffMember } from "./team-os";

export type TeamShiftRosterCellStatus = "ready" | "missing_rate" | "no_shift";

export type TeamShiftRosterDay = {
  dateKey: string;
  label: string;
};

export type TeamShiftRosterCell = {
  dateKey: string;
  status: TeamShiftRosterCellStatus;
  shifts: number;
  hours: number;
  revenue: number;
  items: number;
  laborCost: number;
  timeLabels: string[];
};

export type TeamShiftRosterRowStatus = "ready" | "missing_rate" | "no_shifts";

export type TeamShiftRosterRow = {
  member: StaffMember;
  roleTitle: string;
  status: TeamShiftRosterRowStatus;
  cells: TeamShiftRosterCell[];
  shifts: number;
  hours: number;
  revenue: number;
  items: number;
  laborCost: number;
  laborCostPct: number | null;
  revenuePerHour: number | null;
};

export type TeamShiftRoster = {
  days: TeamShiftRosterDay[];
  rows: TeamShiftRosterRow[];
  rowsWithShifts: number;
  rowsMissingRates: number;
  totalShifts: number;
  totalHours: number;
  totalRevenue: number;
  totalLaborCost: number;
};

export function buildTeamShiftRoster(input: {
  staff: StaffMember[];
  shifts: LaborShiftInput[];
  labor: LaborBiSummary | null;
}): TeamShiftRoster {
  const days = buildRosterDays(input.shifts);
  const rows = input.staff
    .filter((member) => member.status !== "paused")
    .map((member) => buildRosterRow({ ...input, member, days }))
    .sort(
      (a, b) =>
        statusWeight(b.status) - statusWeight(a.status) ||
        b.revenue - a.revenue ||
        a.member.name.localeCompare(b.member.name, "ru"),
    );

  return {
    days,
    rows,
    rowsWithShifts: rows.filter((row) => row.shifts > 0).length,
    rowsMissingRates: rows.filter((row) => row.status === "missing_rate")
      .length,
    totalShifts: rows.reduce((sum, row) => sum + row.shifts, 0),
    totalHours: round(rows.reduce((sum, row) => sum + row.hours, 0)),
    totalRevenue: roundMoney(rows.reduce((sum, row) => sum + row.revenue, 0)),
    totalLaborCost: roundMoney(
      rows.reduce((sum, row) => sum + row.laborCost, 0),
    ),
  };
}

function buildRosterRow(input: {
  member: StaffMember;
  staff: StaffMember[];
  shifts: LaborShiftInput[];
  labor: LaborBiSummary | null;
  days: TeamShiftRosterDay[];
}): TeamShiftRosterRow {
  const schedule = buildMemberShiftSchedule({
    member: input.member,
    shifts: input.shifts,
  });
  const profile = buildMemberLaborProfile({
    member: input.member,
    labor: input.labor,
  });
  const rowStatus = rosterRowStatus(profile.status);
  const cells = input.days.map((day) =>
    buildRosterCell({
      dateKey: day.dateKey,
      status: rowStatus,
      member: input.member,
      shifts: schedule.filter((shift) => shift.dateKey === day.dateKey),
    }),
  );
  const laborCost = roundMoney(
    cells.reduce((sum, cell) => sum + cell.laborCost, 0),
  );
  const revenue = roundMoney(
    cells.reduce((sum, cell) => sum + cell.revenue, 0),
  );
  const hours = round(cells.reduce((sum, cell) => sum + cell.hours, 0));

  return {
    member: input.member,
    roleTitle: getTeamRole(input.member.roleId).title,
    status: rowStatus,
    cells,
    shifts: cells.reduce((sum, cell) => sum + cell.shifts, 0),
    hours,
    revenue,
    items: cells.reduce((sum, cell) => sum + cell.items, 0),
    laborCost,
    laborCostPct: pct(laborCost, revenue),
    revenuePerHour: ratio(revenue, hours),
  };
}

function buildRosterCell(input: {
  dateKey: string;
  status: TeamShiftRosterRowStatus;
  member: StaffMember;
  shifts: ReturnType<typeof buildMemberShiftSchedule>;
}): TeamShiftRosterCell {
  if (input.shifts.length === 0) {
    return {
      dateKey: input.dateKey,
      status: "no_shift",
      shifts: 0,
      hours: 0,
      revenue: 0,
      items: 0,
      laborCost: 0,
      timeLabels: [],
    };
  }

  const revenue = roundMoney(
    input.shifts.reduce((sum, shift) => sum + shift.revenue, 0),
  );
  const hours = round(
    input.shifts.reduce((sum, shift) => sum + shift.hours, 0),
  );
  const laborCost =
    input.status === "missing_rate"
      ? 0
      : roundMoney(
          hours * (input.member.hourlyRate ?? 0) +
            input.shifts.length * (input.member.shiftPay ?? 0) +
            revenue * ((input.member.revenueBonusPct ?? 0) / 100),
        );

  return {
    dateKey: input.dateKey,
    status: input.status === "missing_rate" ? "missing_rate" : "ready",
    shifts: input.shifts.length,
    hours,
    revenue,
    items: input.shifts.reduce((sum, shift) => sum + shift.items, 0),
    laborCost,
    timeLabels: input.shifts.map((shift) => shift.timeLabel),
  };
}

function buildRosterDays(shifts: LaborShiftInput[]): TeamShiftRosterDay[] {
  const dateKeys = [
    ...new Set(shifts.map((shift) => shift.openTime.slice(0, 10))),
  ].sort((a, b) => a.localeCompare(b));

  return dateKeys.map((dateKey) => ({
    dateKey,
    label: formatRosterDay(dateKey),
  }));
}

function rosterRowStatus(
  status: MemberLaborProfileStatus,
): TeamShiftRosterRowStatus {
  if (status === "missing_rate") return "missing_rate";
  if (status === "no_shifts") return "no_shifts";
  return "ready";
}

function statusWeight(status: TeamShiftRosterRowStatus): number {
  if (status === "missing_rate") return 2;
  if (status === "ready") return 1;
  return 0;
}

function formatRosterDay(dateKey: string): string {
  const date = new Date(`${dateKey}T12:00:00`);
  if (Number.isNaN(date.getTime())) return dateKey.slice(5);

  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    weekday: "short",
  }).format(date);
}

function pct(part: number, total: number): number | null {
  if (total <= 0) return null;
  return round((part / total) * 100);
}

function ratio(part: number, total: number): number | null {
  if (total <= 0) return null;
  return roundMoney(part / total);
}

function round(value: number): number {
  return Math.round(value * 10) / 10;
}

function roundMoney(value: number): number {
  return Math.round(value);
}
