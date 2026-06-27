import type {
  LaborBiSummary,
  LaborShiftInput,
  LaborShiftWorker,
} from "./labor-bi";
import type { StaffMember } from "./team-os";

export type MemberShiftScheduleItem = {
  shiftId: string;
  dateKey: string;
  dayLabel: string;
  timeLabel: string;
  revenue: number;
  items: number;
  hours: number;
};

export type MemberLaborProfileStatus = "ready" | "missing_rate" | "no_shifts";

export type MemberLaborProfile = {
  status: MemberLaborProfileStatus;
  shifts: number;
  hours: number;
  sales: number;
  laborCost: number;
  revenuePerHour: number | null;
  laborCostPct: number | null;
  missingRate: boolean;
};

export function buildMemberShiftSchedule(input: {
  member: StaffMember;
  shifts: LaborShiftInput[];
}): MemberShiftScheduleItem[] {
  return input.shifts
    .map((shift) => {
      const worker = matchShiftWorker(shift, input.member);
      if (!worker) return null;

      const workerCount = Math.max(shift.workers?.length ?? 1, 1);
      return {
        shiftId: shift.shiftId,
        dateKey: shift.openTime.slice(0, 10),
        dayLabel: formatScheduleDay(shift.openTime),
        timeLabel: formatShiftTime(
          worker.startedAt ?? shift.openTime,
          worker.endedAt ?? shift.closeTime,
        ),
        revenue: Math.round(worker.sales ?? shift.revenue / workerCount),
        items: shift.items,
        hours: roundHours(resolveWorkerHours(worker, shift)),
      } satisfies MemberShiftScheduleItem;
    })
    .filter((item): item is MemberShiftScheduleItem => item !== null)
    .sort((a, b) => a.dateKey.localeCompare(b.dateKey));
}

export function buildMemberLaborProfile(input: {
  member: StaffMember;
  labor: LaborBiSummary | null;
}): MemberLaborProfile {
  const employee = input.labor?.employees.find(
    (item) =>
      item.memberId === input.member.id ||
      normalizeName(item.name) === normalizeName(input.member.name),
  );

  if (!employee) {
    return {
      status: "no_shifts",
      shifts: 0,
      hours: 0,
      sales: 0,
      laborCost: 0,
      revenuePerHour: null,
      laborCostPct: null,
      missingRate: false,
    };
  }

  return {
    status: employee.missingRate ? "missing_rate" : "ready",
    shifts: employee.shifts,
    hours: employee.hours,
    sales: employee.sales,
    laborCost: employee.laborCost,
    revenuePerHour: employee.revenuePerHour,
    laborCostPct: employee.laborCostPct,
    missingRate: employee.missingRate,
  };
}

function matchShiftWorker(
  shift: LaborShiftInput,
  member: StaffMember,
): LaborShiftWorker | null {
  if (shift.workers?.length) {
    return (
      shift.workers.find((worker) => worker.memberId === member.id) ??
      shift.workers.find(
        (worker) => normalizeName(worker.name) === normalizeName(member.name),
      ) ??
      null
    );
  }

  if (normalizeName(shift.employee) !== normalizeName(member.name)) {
    return null;
  }

  return {
    memberId: member.id,
    name: shift.employee,
    roleId: member.roleId,
    startedAt: shift.openTime,
    endedAt: shift.closeTime,
    hourlyRate: member.hourlyRate,
    shiftPay: member.shiftPay,
    revenueBonusPct: member.revenueBonusPct,
    sales: shift.revenue,
  };
}

function resolveWorkerHours(
  worker: LaborShiftWorker,
  shift: LaborShiftInput,
): number {
  if (typeof worker.hours === "number" && Number.isFinite(worker.hours)) {
    return Math.max(worker.hours, 0);
  }

  const startedAt = worker.startedAt ?? shift.openTime;
  const endedAt = worker.endedAt ?? shift.closeTime;
  if (!endedAt) return 0;

  const started = Date.parse(startedAt);
  const ended = Date.parse(endedAt);
  if (
    !Number.isFinite(started) ||
    !Number.isFinite(ended) ||
    ended <= started
  ) {
    return 0;
  }

  return (ended - started) / 3_600_000;
}

function formatScheduleDay(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value.slice(0, 10);
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    weekday: "short",
  }).format(date);
}

function formatShiftTime(start: string, end?: string): string {
  return `${formatTime(start)} - ${end ? formatTime(end) : "..."}`;
}

function formatTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value.slice(11, 16) || value;
  return new Intl.DateTimeFormat("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function normalizeName(value: string): string {
  return value.trim().toLowerCase().replace(/\s+/g, " ");
}

function roundHours(value: number): number {
  return Math.round(value * 10) / 10;
}
