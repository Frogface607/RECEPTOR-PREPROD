import type {
  TeamShiftPlanItem,
  TeamShiftPlanSummary,
} from "./team-shift-plan";
import type { TeamShiftRoster } from "./team-shift-roster";
import type { StaffMember } from "./team-os";

export type TeamShiftPlanVarianceStatus =
  | "matched"
  | "day_off_worked"
  | "unplanned_actual"
  | "missed_plan"
  | "over_hours"
  | "under_hours"
  | "missing_rate";

export type TeamShiftPlanVarianceTone = "ready" | "watch" | "risk" | "setup";

export type TeamShiftPlanVarianceIssue = {
  id: string;
  member: StaffMember;
  roleTitle: string;
  dateKey: string;
  dateLabel: string;
  status: Exclude<TeamShiftPlanVarianceStatus, "matched">;
  tone: TeamShiftPlanVarianceTone;
  plannedShifts: number;
  actualShifts: number;
  plannedHours: number;
  actualHours: number;
  hoursDelta: number;
  plannedLaborCost: number;
  actualLaborCost: number;
  laborDelta: number;
  revenue: number;
};

export type TeamShiftPlanVarianceSummary = {
  plannedShifts: number;
  actualShifts: number;
  coveredActualShifts: number;
  planCoveragePct: number;
  plannedHours: number;
  actualHours: number;
  hoursDelta: number;
  plannedLaborCost: number;
  actualLaborCost: number;
  laborDelta: number;
  unplannedActualShifts: number;
  missedPlanShifts: number;
  dayOffWorkedShifts: number;
  hourVarianceShifts: number;
  missingRateShifts: number;
  issues: TeamShiftPlanVarianceIssue[];
};

export function buildTeamShiftPlanVariance(input: {
  plan: TeamShiftPlanSummary;
  roster: TeamShiftRoster;
  hourTolerance?: number;
}): TeamShiftPlanVarianceSummary {
  const hourTolerance = input.hourTolerance ?? 1;
  const rosterRowsByMember = new Map(
    input.roster.rows.map((row) => [row.member.id, row]),
  );
  const planRowsByMember = new Map(
    input.plan.rows.map((row) => [row.member.id, row]),
  );
  const memberIds = new Set<string>([
    ...rosterRowsByMember.keys(),
    ...planRowsByMember.keys(),
  ]);
  const issues: TeamShiftPlanVarianceIssue[] = [];
  let coveredActualShifts = 0;
  let unplannedActualShifts = 0;
  let missedPlanShifts = 0;
  let dayOffWorkedShifts = 0;
  let hourVarianceShifts = 0;
  let missingRateShifts = 0;

  memberIds.forEach((memberId) => {
    const rosterRow = rosterRowsByMember.get(memberId);
    const planRow = planRowsByMember.get(memberId);
    const member = rosterRow?.member ?? planRow?.member;
    if (!member) return;

    const actualCellsByDate = new Map(
      (rosterRow?.cells ?? []).map((cell) => [cell.dateKey, cell]),
    );
    const planItemsByDate = new Map(
      (planRow?.items ?? []).map((item) => [item.plan.shiftDate, item]),
    );
    const dateKeys = new Set<string>([
      ...actualCellsByDate.keys(),
      ...planItemsByDate.keys(),
    ]);

    dateKeys.forEach((dateKey) => {
      const actual = actualCellsByDate.get(dateKey);
      const planned = planItemsByDate.get(dateKey);
      const plannedShifts = planned && !planned.plan.isDayOff ? 1 : 0;
      const actualShifts = actual?.shifts ?? 0;
      const plannedHours = planned?.hours ?? 0;
      const actualHours = actual?.hours ?? 0;
      const hoursDelta = round(actualHours - plannedHours);
      const plannedLaborCost = planned?.laborCost ?? 0;
      const actualLaborCost = actual?.laborCost ?? 0;
      const laborDelta = roundMoney(actualLaborCost - plannedLaborCost);
      const missingRate =
        Boolean(planned?.missingRate) || actual?.status === "missing_rate";
      const status = resolveStatus({
        planned,
        plannedShifts,
        actualShifts,
        hoursDelta,
        missingRate,
        hourTolerance,
      });

      if (plannedShifts > 0 && actualShifts > 0) {
        coveredActualShifts += actualShifts;
      }
      if (actualShifts > 0 && missingRate) missingRateShifts += actualShifts;

      if (status === "matched") return;

      if (status === "unplanned_actual") unplannedActualShifts += actualShifts;
      if (status === "missed_plan") missedPlanShifts += plannedShifts;
      if (status === "day_off_worked") dayOffWorkedShifts += actualShifts;
      if (status === "over_hours" || status === "under_hours") {
        hourVarianceShifts += Math.max(plannedShifts, actualShifts);
      }

      issues.push({
        id: `${member.id}-${dateKey}-${status}`,
        member,
        roleTitle: rosterRow?.roleTitle ?? planRow?.roleTitle ?? "",
        dateKey,
        dateLabel: formatVarianceDate(dateKey),
        status,
        tone: statusTone(status),
        plannedShifts,
        actualShifts,
        plannedHours,
        actualHours,
        hoursDelta,
        plannedLaborCost,
        actualLaborCost,
        laborDelta,
        revenue: actual?.revenue ?? 0,
      });
    });
  });

  return {
    plannedShifts: input.plan.plannedShifts,
    actualShifts: input.roster.totalShifts,
    coveredActualShifts,
    planCoveragePct: planCoveragePct({
      actualShifts: input.roster.totalShifts,
      plannedShifts: input.plan.plannedShifts,
      coveredActualShifts,
    }),
    plannedHours: input.plan.hours,
    actualHours: input.roster.totalHours,
    hoursDelta: round(input.roster.totalHours - input.plan.hours),
    plannedLaborCost: input.plan.laborCost,
    actualLaborCost: input.roster.totalLaborCost,
    laborDelta: roundMoney(input.roster.totalLaborCost - input.plan.laborCost),
    unplannedActualShifts,
    missedPlanShifts,
    dayOffWorkedShifts,
    hourVarianceShifts,
    missingRateShifts,
    issues: issues.sort(sortIssues).slice(0, 8),
  };
}

function resolveStatus(input: {
  planned: TeamShiftPlanItem | undefined;
  plannedShifts: number;
  actualShifts: number;
  hoursDelta: number;
  missingRate: boolean;
  hourTolerance: number;
}): TeamShiftPlanVarianceStatus {
  if (input.planned?.plan.isDayOff && input.actualShifts > 0) {
    return "day_off_worked";
  }
  if (input.actualShifts > 0 && input.plannedShifts === 0) {
    return "unplanned_actual";
  }
  if (input.plannedShifts > 0 && input.actualShifts === 0) {
    return "missed_plan";
  }
  if (
    input.missingRate &&
    (input.plannedShifts > 0 || input.actualShifts > 0)
  ) {
    return "missing_rate";
  }
  if (input.hoursDelta > input.hourTolerance) return "over_hours";
  if (input.hoursDelta < -input.hourTolerance) return "under_hours";
  return "matched";
}

function statusTone(
  status: Exclude<TeamShiftPlanVarianceStatus, "matched">,
): TeamShiftPlanVarianceTone {
  if (status === "day_off_worked" || status === "missed_plan") return "risk";
  if (status === "missing_rate" || status === "unplanned_actual") {
    return "setup";
  }
  return "watch";
}

function sortIssues(
  a: TeamShiftPlanVarianceIssue,
  b: TeamShiftPlanVarianceIssue,
): number {
  return (
    toneWeight(b.tone) - toneWeight(a.tone) ||
    statusWeight(b.status) - statusWeight(a.status) ||
    Math.abs(b.laborDelta) - Math.abs(a.laborDelta) ||
    Math.abs(b.hoursDelta) - Math.abs(a.hoursDelta) ||
    a.dateKey.localeCompare(b.dateKey) ||
    a.member.name.localeCompare(b.member.name, "ru")
  );
}

function toneWeight(tone: TeamShiftPlanVarianceTone): number {
  if (tone === "risk") return 3;
  if (tone === "setup") return 2;
  if (tone === "watch") return 1;
  return 0;
}

function statusWeight(
  status: Exclude<TeamShiftPlanVarianceStatus, "matched">,
): number {
  if (status === "day_off_worked") return 6;
  if (status === "missed_plan") return 5;
  if (status === "unplanned_actual") return 4;
  if (status === "missing_rate") return 3;
  if (status === "over_hours") return 2;
  return 1;
}

function planCoveragePct(input: {
  actualShifts: number;
  plannedShifts: number;
  coveredActualShifts: number;
}): number {
  if (input.actualShifts > 0) {
    return Math.round((input.coveredActualShifts / input.actualShifts) * 100);
  }
  return input.plannedShifts > 0 ? 0 : 100;
}

function formatVarianceDate(dateKey: string): string {
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
