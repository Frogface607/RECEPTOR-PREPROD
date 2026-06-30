import type { ShiftStat } from "@/lib/iiko/models";
import {
  findStaffMemberByName,
  normalizeTeamMemberName,
} from "./team-member-match";
import type { StaffMember, TeamRoleId } from "./team-os";

export type LaborRate = {
  memberId?: string;
  roleId?: TeamRoleId;
  hourlyRate?: number;
  shiftPay?: number;
  revenueBonusPct?: number;
};

export type LaborShiftWorker = {
  memberId?: string;
  name: string;
  roleId?: TeamRoleId;
  startedAt?: string;
  endedAt?: string;
  hours?: number;
  hourlyRate?: number;
  shiftPay?: number;
  revenueBonusPct?: number;
  sales?: number;
};

export type LaborShiftInput = ShiftStat & {
  workers?: LaborShiftWorker[];
};

export type LaborEmployeeSummary = {
  memberId?: string;
  name: string;
  roleId?: TeamRoleId;
  shifts: number;
  hours: number;
  sales: number;
  laborCost: number;
  revenuePerHour: number | null;
  laborCostPct: number | null;
  missingRate: boolean;
};

export type LaborBlockerReason = "missing-member" | "missing-rate";

export type LaborBlocker = {
  memberId?: string;
  name: string;
  roleId?: TeamRoleId;
  shifts: number;
  hours: number;
  sales: number;
  reason: LaborBlockerReason;
};

export type LaborReadinessStatus = "ready" | "partial" | "blocked";

export type LaborShiftSummary = {
  shiftId: string;
  openTime: string;
  closeTime?: string;
  revenue: number;
  items: number;
  staffCount: number;
  hours: number;
  laborCost: number;
  laborCostPct: number | null;
  revenuePerHour: number | null;
  missingRates: number;
};

export type LaborBiSummary = {
  revenue: number;
  items: number;
  shifts: number;
  staffShifts: number;
  staffHours: number;
  laborCost: number;
  laborCostPct: number | null;
  revenuePerLaborHour: number | null;
  averageStaffPerShift: number;
  missingRates: number;
  pricedStaffShifts: number;
  unpricedStaffShifts: number;
  pricedRevenue: number;
  unpricedRevenue: number;
  revenueCoveragePct: number | null;
  laborReadinessStatus: LaborReadinessStatus;
  shiftsBreakdown: LaborShiftSummary[];
  employees: LaborEmployeeSummary[];
  topBlockers: LaborBlocker[];
};

export type LaborInsightTone = "risk" | "watch" | "good" | "setup";

export type LaborInsight = {
  tone: LaborInsightTone;
  title: string;
  detail: string;
  action: string;
};

export type LaborNextActionKind =
  | "ready"
  | "missing-shifts"
  | "missing-member"
  | "missing-rate"
  | "expensive-labor"
  | "low-productivity";

export type LaborNextAction = {
  kind: LaborNextActionKind;
  title: string;
  detail: string;
  action: string;
  blocker: LaborBlocker | null;
  shift: LaborShiftSummary | null;
  impactLabel?: string;
};

export type LaborInsightOptions = {
  targetLaborCostPct?: number;
  minimumRevenuePerLaborHour?: number;
};

export type LaborShiftDiagnosticKind =
  "missing-rates" | "expensive-labor" | "low-productivity" | "healthy";

export type LaborShiftDiagnostic = LaborShiftSummary & {
  kind: LaborShiftDiagnosticKind;
  tone: LaborInsightTone;
  title: string;
  detail: string;
  action: string;
  laborOverTarget: number | null;
};

export type LaborEmployeeDiagnosticKind =
  "missing-rate" | "expensive-employee" | "low-productivity" | "healthy";

export type LaborEmployeeDiagnostic = LaborEmployeeSummary & {
  kind: LaborEmployeeDiagnosticKind;
  tone: LaborInsightTone;
  title: string;
  detail: string;
  action: string;
  laborOverTarget: number | null;
};

export function buildLaborBi(input: {
  shifts: LaborShiftInput[];
  staff?: StaffMember[];
  rates?: LaborRate[];
}): LaborBiSummary {
  const staffById = new Map(
    (input.staff ?? []).map((member) => [member.id, member]),
  );
  const employeeTotals = new Map<string, MutableEmployeeSummary>();
  let pricedStaffShifts = 0;
  let unpricedStaffShifts = 0;
  let pricedRevenue = 0;
  let unpricedRevenue = 0;

  const shiftsBreakdown = input.shifts.map((shift) => {
    const workers = normalizeWorkers(shift, staffById);
    let shiftHours = 0;
    let shiftLaborCost = 0;
    let missingRates = 0;

    workers.forEach((worker) => {
      const rate = resolveRate(worker, input.rates ?? []);
      const hours = resolveHours(worker, shift);
      const sales = worker.sales ?? splitRevenue(shift.revenue, workers.length);
      const cost = calculateWorkerCost(worker, rate, hours, sales);
      const missingRate = isMissingRate(worker, rate);

      shiftHours += hours;
      shiftLaborCost += cost;
      if (missingRate) missingRates += 1;
      if (missingRate) {
        unpricedStaffShifts += 1;
        unpricedRevenue += sales;
      } else {
        pricedStaffShifts += 1;
        pricedRevenue += sales;
      }

      upsertEmployee(employeeTotals, worker, {
        hours,
        sales,
        laborCost: cost,
        missingRate,
      });
    });

    return {
      shiftId: shift.shiftId,
      openTime: shift.openTime,
      closeTime: shift.closeTime,
      revenue: shift.revenue,
      items: shift.items,
      staffCount: workers.length,
      hours: round(shiftHours),
      laborCost: roundMoney(shiftLaborCost),
      laborCostPct: pct(shiftLaborCost, shift.revenue),
      revenuePerHour: ratio(shift.revenue, shiftHours),
      missingRates,
    } satisfies LaborShiftSummary;
  });

  const revenue = sum(shiftsBreakdown, "revenue");
  const items = sum(shiftsBreakdown, "items");
  const staffHours = sum(shiftsBreakdown, "hours");
  const laborCost = sum(shiftsBreakdown, "laborCost");
  const staffShifts = sum(shiftsBreakdown, "staffCount");
  const employees = [...employeeTotals.values()]
    .map(finalizeEmployee)
    .sort((a, b) => b.laborCost - a.laborCost || b.sales - a.sales);
  const topBlockers = buildLaborBlockers(employees);
  const roundedPricedRevenue = roundMoney(pricedRevenue);
  const roundedUnpricedRevenue = roundMoney(unpricedRevenue);

  return {
    revenue,
    items,
    shifts: input.shifts.length,
    staffShifts,
    staffHours: round(staffHours),
    laborCost: roundMoney(laborCost),
    laborCostPct: pct(laborCost, revenue),
    revenuePerLaborHour: ratio(revenue, staffHours),
    averageStaffPerShift: round(ratio(staffShifts, input.shifts.length) ?? 0),
    missingRates: shiftsBreakdown.reduce(
      (total, shift) => total + shift.missingRates,
      0,
    ),
    pricedStaffShifts,
    unpricedStaffShifts,
    pricedRevenue: roundedPricedRevenue,
    unpricedRevenue: roundedUnpricedRevenue,
    revenueCoveragePct: buildRevenueCoveragePct({
      staffShifts,
      unpricedStaffShifts,
      pricedRevenue: roundedPricedRevenue,
      unpricedRevenue: roundedUnpricedRevenue,
    }),
    laborReadinessStatus: resolveLaborReadinessStatus({
      staffShifts,
      pricedStaffShifts,
      unpricedStaffShifts,
    }),
    shiftsBreakdown,
    employees,
    topBlockers,
  };
}

export function buildLaborInsights(
  labor: LaborBiSummary,
  options: LaborInsightOptions = {},
): LaborInsight[] {
  const targetLaborCostPct = options.targetLaborCostPct ?? 25;
  const minimumRevenuePerLaborHour = options.minimumRevenuePerLaborHour ?? 6000;
  const insights: LaborInsight[] = [];

  if (labor.staffShifts === 0) {
    return [
      {
        tone: "setup",
        title: "Смены пока не найдены",
        detail: "iiko не вернула смены за выбранный период.",
        action: "Проверьте период и права на OLAP смены.",
      },
    ];
  }

  if (labor.missingRates > 0) {
    const blocker = labor.topBlockers[0];
    insights.push({
      tone: "setup",
      title: "Не все ставки заведены",
      detail: blocker
        ? `${labor.missingRates} ${plural(labor.missingRates, "сотрудник", "сотрудника", "сотрудников")} без ставки. Первым закрыть: ${blocker.name}, ${formatMoney(blocker.sales)} выручки в сменах. ${formatLaborCoverageGap(labor)}`
        : `${labor.missingRates} ${plural(labor.missingRates, "сотрудник", "сотрудника", "сотрудников")} без ставки мешают точно считать ФОТ. ${formatLaborCoverageGap(labor)}`,
      action:
        blocker?.reason === "missing-member"
          ? "Добавьте этого сотрудника в команду или выровняйте имя с iiko."
          : "Заполните ставку сотрудника в команде и вернитесь к периоду.",
    });
  }

  if (labor.laborCost === 0 && labor.staffShifts > 0) {
    insights.push({
      tone: "setup",
      title: "ФОТ сейчас считается как 0 ₽",
      detail:
        "Смены есть, но по ним нет ни почасовой ставки, ни фикса за смену, ни процента от продаж.",
      action: "Задайте хотя бы один тип ставки для сотрудников на смене.",
    });
  }

  if (labor.laborCostPct !== null && labor.laborCostPct > targetLaborCostPct) {
    const overTarget = laborCostOverTarget(
      labor.laborCost,
      labor.revenue,
      targetLaborCostPct,
    );
    insights.push({
      tone: "risk",
      title: "ФОТ выше целевой нормы",
      detail: `Сейчас ${formatPct(labor.laborCostPct)} от выручки при ориентире ${formatPct(targetLaborCostPct)}. Управляемый перерасход к цели: ${formatMoney(overTarget)}.`,
      action: "Проверьте состав смены, часы и фактическую загрузку зала.",
    });
  }

  const expensiveShift = labor.shiftsBreakdown
    .filter(
      (shift) =>
        shift.laborCostPct !== null && shift.laborCostPct > targetLaborCostPct,
    )
    .sort((a, b) => expensiveShiftDelta(a, b, targetLaborCostPct))[0];
  if (expensiveShift) {
    const overTarget = laborCostOverTarget(
      expensiveShift.laborCost,
      expensiveShift.revenue,
      targetLaborCostPct,
    );
    insights.push({
      tone: "watch",
      title: `Дорогая смена: ${formatShiftDate(expensiveShift.openTime)}`,
      detail: `ФОТ смены ${formatPct(expensiveShift.laborCostPct)} при выручке ${formatMoney(expensiveShift.revenue)}. Перерасход к цели: ${formatMoney(overTarget)}.`,
      action: "Сравните расписание, посадку и роли на этой смене.",
    });
  }

  if (
    labor.revenuePerLaborHour !== null &&
    labor.revenuePerLaborHour < minimumRevenuePerLaborHour
  ) {
    insights.push({
      tone: "watch",
      title: "Выручка на человеко-час ниже цели",
      detail: `${formatMoney(labor.revenuePerLaborHour)} на час при ориентире ${formatMoney(minimumRevenuePerLaborHour)}.`,
      action:
        "Проверьте слабые часы, лишние руки на смене и продажи официантов.",
    });
  }

  if (insights.length === 0) {
    insights.push({
      tone: "good",
      title: "ФОТ выглядит управляемо",
      detail: `ФОТ ${formatPct(labor.laborCostPct)} от выручки, ${formatMoney(labor.revenuePerLaborHour)} на человеко-час.`,
      action:
        "Сравните с маржинальностью блюд и держите этот уровень как базу.",
    });
  }

  return insights.slice(0, 3);
}

export function buildLaborNextAction(
  labor: LaborBiSummary,
  options: LaborInsightOptions = {},
): LaborNextAction {
  const targetLaborCostPct = options.targetLaborCostPct ?? 25;
  const minimumRevenuePerLaborHour = options.minimumRevenuePerLaborHour ?? 6000;

  if (labor.staffShifts === 0) {
    return {
      kind: "missing-shifts",
      title: "Смены не найдены",
      detail: "iiko не вернула сотрудников за выбранный период.",
      action: "Проверьте период и права на OLAP смены.",
      blocker: null,
      shift: null,
    };
  }

  const blocker = labor.topBlockers[0] ?? null;
  if (blocker?.reason === "missing-member") {
    return {
      kind: "missing-member",
      title: "Добавить сотрудника из iiko",
      detail: `${blocker.name}: ${formatMoney(blocker.sales)} выручки в сменах без карточки сотрудника. ${formatLaborCoverageGap(labor)}`,
      action:
        "Откройте команду, добавьте сотрудника с таким же именем и задайте ставку ФОТ.",
      blocker,
      shift: null,
    };
  }

  if (blocker?.reason === "missing-rate") {
    return {
      kind: "missing-rate",
      title: "Заполнить ставку ФОТ",
      detail: `${blocker.name}: ${formatMoney(blocker.sales)} выручки в сменах без точной стоимости. ${formatLaborCoverageGap(labor)}`,
      action:
        "Откройте карточку сотрудника и заполните почасовую ставку, фикс за смену или процент.",
      blocker,
      shift: null,
    };
  }

  const expensiveShift = labor.shiftsBreakdown
    .filter(
      (shift) =>
        shift.laborCostPct !== null && shift.laborCostPct > targetLaborCostPct,
    )
    .sort((a, b) => expensiveShiftDelta(a, b, targetLaborCostPct))[0];

  if (expensiveShift) {
    const overTarget = laborCostOverTarget(
      expensiveShift.laborCost,
      expensiveShift.revenue,
      targetLaborCostPct,
    );
    return {
      kind: "expensive-labor",
      title: "Разобрать дорогую смену",
      detail: `${formatShiftDate(expensiveShift.openTime)}: ФОТ ${formatPct(expensiveShift.laborCostPct)} при выручке ${formatMoney(expensiveShift.revenue)}; перерасход к цели ${formatMoney(overTarget)}.`,
      action: "Сверьте расписание, роли, часы и загрузку зала на этой смене.",
      blocker: null,
      shift: expensiveShift,
      impactLabel: formatMoney(overTarget),
    };
  }

  const lowProductivityShift = labor.shiftsBreakdown
    .filter(
      (shift) =>
        shift.revenuePerHour !== null &&
        shift.revenuePerHour < minimumRevenuePerLaborHour,
    )
    .sort(
      (a, b) =>
        minimumRevenuePerLaborHour -
          (b.revenuePerHour ?? 0) -
          (minimumRevenuePerLaborHour - (a.revenuePerHour ?? 0)) ||
        b.revenue - a.revenue,
    )[0];

  if (lowProductivityShift) {
    return {
      kind: "low-productivity",
      title: "Разобрать слабую смену",
      detail: `${formatShiftDate(lowProductivityShift.openTime)}: ${formatMoney(lowProductivityShift.revenuePerHour)} на человеко-час при ориентире ${formatMoney(minimumRevenuePerLaborHour)}.`,
      action:
        "Сверьте состав смены, слабые часы, посадку и задачи на средний чек.",
      blocker: null,
      shift: lowProductivityShift,
    };
  }

  return {
    kind: "ready",
    title: "ФОТ можно анализировать",
    detail: `Ставки закрыты: ФОТ ${formatPct(labor.laborCostPct)} от выручки, ${formatMoney(labor.revenuePerLaborHour)} на человеко-час, ${labor.averageStaffPerShift.toLocaleString("ru-RU")} человека на смену.`,
    action:
      "Следующий контроль: сравнить ФОТ с маржей топ-блюд и разобрать смены, где команда стоит дорого к выручке.",
    blocker: null,
    shift: null,
  };
}

export function buildLaborShiftDiagnostics(
  labor: LaborBiSummary,
  options: LaborInsightOptions = {},
): LaborShiftDiagnostic[] {
  const targetLaborCostPct = options.targetLaborCostPct ?? 25;
  const minimumRevenuePerLaborHour = options.minimumRevenuePerLaborHour ?? 6000;

  return labor.shiftsBreakdown
    .map((shift) =>
      decorateShiftDiagnostic(shift, {
        targetLaborCostPct,
        minimumRevenuePerLaborHour,
      }),
    )
    .sort(
      (a, b) =>
        shiftRiskScore(b, {
          targetLaborCostPct,
          minimumRevenuePerLaborHour,
        }) -
          shiftRiskScore(a, {
            targetLaborCostPct,
            minimumRevenuePerLaborHour,
          }) || b.revenue - a.revenue,
    );
}

export function buildLaborEmployeeDiagnostics(
  labor: LaborBiSummary,
  options: LaborInsightOptions = {},
): LaborEmployeeDiagnostic[] {
  const targetLaborCostPct = options.targetLaborCostPct ?? 25;
  const minimumRevenuePerLaborHour = options.minimumRevenuePerLaborHour ?? 6000;

  return labor.employees
    .map((employee) =>
      decorateEmployeeDiagnostic(employee, {
        targetLaborCostPct,
        minimumRevenuePerLaborHour,
      }),
    )
    .sort(
      (a, b) =>
        employeeRiskScore(b, {
          targetLaborCostPct,
          minimumRevenuePerLaborHour,
        }) -
          employeeRiskScore(a, {
            targetLaborCostPct,
            minimumRevenuePerLaborHour,
          }) || b.sales - a.sales,
    );
}

type MutableEmployeeSummary = {
  memberId?: string;
  name: string;
  roleId?: TeamRoleId;
  shifts: number;
  hours: number;
  sales: number;
  laborCost: number;
  missingRate: boolean;
};

function normalizeWorkers(
  shift: LaborShiftInput,
  staffById: Map<string, StaffMember>,
): LaborShiftWorker[] {
  if (shift.workers && shift.workers.length > 0) {
    return shift.workers.map((worker) => {
      const member = worker.memberId
        ? staffById.get(worker.memberId)
        : findStaffMemberByName(staffById.values(), worker.name);
      return {
        ...worker,
        memberId: worker.memberId ?? member?.id,
        name: member?.name ?? worker.name,
        roleId: worker.roleId ?? member?.roleId,
        hourlyRate: worker.hourlyRate ?? member?.hourlyRate,
        shiftPay: worker.shiftPay ?? member?.shiftPay,
        revenueBonusPct: worker.revenueBonusPct ?? member?.revenueBonusPct,
      };
    });
  }

  const member = findStaffByName(staffById, shift.employee);
  return [
    {
      memberId: member?.id,
      name: member?.name ?? shift.employee,
      roleId: member?.roleId,
      startedAt: shift.openTime,
      endedAt: shift.closeTime,
      hourlyRate: member?.hourlyRate,
      shiftPay: member?.shiftPay,
      revenueBonusPct: member?.revenueBonusPct,
    },
  ];
}

function findStaffByName(
  staffById: Map<string, StaffMember>,
  name: string,
): StaffMember | undefined {
  const normalizedName = normalizeName(name);
  if (!normalizedName || normalizedName === "смена") return undefined;
  return findStaffMemberByName(staffById.values(), name);
}

function normalizeName(value: string): string {
  return normalizeTeamMemberName(value);
}

function resolveRate(
  worker: LaborShiftWorker,
  rates: LaborRate[],
): LaborRate | null {
  if (worker.hourlyRate || worker.shiftPay || worker.revenueBonusPct)
    return worker;
  return (
    (worker.memberId
      ? rates.find((rate) => rate.memberId === worker.memberId)
      : undefined) ??
    (worker.roleId
      ? rates.find((rate) => rate.roleId === worker.roleId)
      : undefined) ??
    null
  );
}

function resolveHours(
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

function calculateWorkerCost(
  worker: LaborShiftWorker,
  rate: LaborRate | null,
  hours: number,
  sales: number,
): number {
  const hourlyRate = worker.hourlyRate ?? rate?.hourlyRate ?? 0;
  const shiftPay = worker.shiftPay ?? rate?.shiftPay ?? 0;
  const revenueBonusPct = worker.revenueBonusPct ?? rate?.revenueBonusPct ?? 0;

  return roundMoney(
    hours * hourlyRate + shiftPay + sales * (revenueBonusPct / 100),
  );
}

function isMissingRate(
  worker: LaborShiftWorker,
  rate: LaborRate | null,
): boolean {
  return (
    !worker.hourlyRate && !worker.shiftPay && !worker.revenueBonusPct && !rate
  );
}

function upsertEmployee(
  map: Map<string, MutableEmployeeSummary>,
  worker: LaborShiftWorker,
  delta: Pick<
    MutableEmployeeSummary,
    "hours" | "sales" | "laborCost" | "missingRate"
  >,
): void {
  const key = worker.memberId ?? worker.name;
  const current =
    map.get(key) ??
    ({
      memberId: worker.memberId,
      name: worker.name,
      roleId: worker.roleId,
      shifts: 0,
      hours: 0,
      sales: 0,
      laborCost: 0,
      missingRate: false,
    } satisfies MutableEmployeeSummary);

  current.shifts += 1;
  current.hours += delta.hours;
  current.sales += delta.sales;
  current.laborCost += delta.laborCost;
  current.missingRate = current.missingRate || delta.missingRate;
  map.set(key, current);
}

function finalizeEmployee(
  employee: MutableEmployeeSummary,
): LaborEmployeeSummary {
  return {
    ...employee,
    hours: round(employee.hours),
    sales: roundMoney(employee.sales),
    laborCost: roundMoney(employee.laborCost),
    revenuePerHour: ratio(employee.sales, employee.hours),
    laborCostPct: pct(employee.laborCost, employee.sales),
  };
}

function buildLaborBlockers(employees: LaborEmployeeSummary[]): LaborBlocker[] {
  return employees
    .filter((employee) => employee.missingRate)
    .map((employee) => ({
      memberId: employee.memberId,
      name: employee.name,
      roleId: employee.roleId,
      shifts: employee.shifts,
      hours: employee.hours,
      sales: employee.sales,
      reason: employee.memberId
        ? ("missing-rate" as const)
        : ("missing-member" as const),
    }))
    .sort(
      (a, b) => b.sales - a.sales || b.hours - a.hours || b.shifts - a.shifts,
    )
    .slice(0, 5);
}

function resolveLaborReadinessStatus(input: {
  staffShifts: number;
  pricedStaffShifts: number;
  unpricedStaffShifts: number;
}): LaborReadinessStatus {
  if (input.staffShifts === 0 || input.pricedStaffShifts === 0)
    return "blocked";
  if (input.unpricedStaffShifts > 0) return "partial";
  return "ready";
}

function buildRevenueCoveragePct(input: {
  staffShifts: number;
  unpricedStaffShifts: number;
  pricedRevenue: number;
  unpricedRevenue: number;
}): number | null {
  if (input.staffShifts === 0) return null;

  const assignedRevenue = input.pricedRevenue + input.unpricedRevenue;
  if (assignedRevenue > 0) return pct(input.pricedRevenue, assignedRevenue);

  return input.unpricedStaffShifts === 0 ? 100 : 0;
}

function decorateShiftDiagnostic(
  shift: LaborShiftSummary,
  options: Required<LaborInsightOptions>,
): LaborShiftDiagnostic {
  const laborOverTarget = laborCostOverTarget(
    shift.laborCost,
    shift.revenue,
    options.targetLaborCostPct,
  );

  if (shift.missingRates > 0) {
    return {
      ...shift,
      kind: "missing-rates",
      tone: "setup",
      title: "ФОТ смены не доказан",
      detail: `${shift.missingRates} ${plural(shift.missingRates, "сотрудник", "сотрудника", "сотрудников")} без ставки или карточки сотрудника.`,
      action: "Сначала закройте ставку, потом сравнивайте смену по прибыли.",
      laborOverTarget: null,
    };
  }

  if (
    shift.laborCostPct !== null &&
    shift.laborCostPct > options.targetLaborCostPct
  ) {
    return {
      ...shift,
      kind: "expensive-labor",
      tone: "risk",
      title: "Смена дорогая по ФОТ",
      detail: `ФОТ ${formatPct(shift.laborCostPct)} при выручке ${formatMoney(shift.revenue)}. Перерасход к цели: ${formatMoney(laborOverTarget)}.`,
      action: "Разберите расписание, роли и загрузку зала в этой смене.",
      laborOverTarget,
    };
  }

  if (
    shift.revenuePerHour !== null &&
    shift.revenuePerHour < options.minimumRevenuePerLaborHour
  ) {
    return {
      ...shift,
      kind: "low-productivity",
      tone: "watch",
      title: "Низкая выручка на человеко-час",
      detail: `${formatMoney(shift.revenuePerHour)} на час при ориентире ${formatMoney(options.minimumRevenuePerLaborHour)}.`,
      action: "Проверьте лишние руки, слабые часы и задачи на продажи.",
      laborOverTarget,
    };
  }

  return {
    ...shift,
    kind: "healthy",
    tone: "good",
    title: "Смена выглядит управляемо",
    detail: `ФОТ ${formatPct(shift.laborCostPct)}, ${formatMoney(shift.revenuePerHour)} на человеко-час.`,
    action: "Сравните с маржой блюд и закрепите этот состав как ориентир.",
    laborOverTarget,
  };
}

function decorateEmployeeDiagnostic(
  employee: LaborEmployeeSummary,
  options: Required<LaborInsightOptions>,
): LaborEmployeeDiagnostic {
  const laborOverTarget = laborCostOverTarget(
    employee.laborCost,
    employee.sales,
    options.targetLaborCostPct,
  );

  if (employee.missingRate) {
    return {
      ...employee,
      kind: "missing-rate",
      tone: "setup",
      title: "Сотрудник без ставки ФОТ",
      detail: `${employee.name}: ${formatMoney(employee.sales)} выручки и ${employee.shifts} ${plural(employee.shifts, "смена", "смены", "смен")} без точной стоимости.`,
      action: employee.memberId
        ? "Заполните ставку в карточке сотрудника, чтобы ФОТ и прибыль считались точно."
        : "Создайте карточку сотрудника из iiko и задайте ставку ФОТ.",
      laborOverTarget: null,
    };
  }

  if (
    employee.laborCostPct !== null &&
    employee.laborCostPct > options.targetLaborCostPct
  ) {
    return {
      ...employee,
      kind: "expensive-employee",
      tone: "risk",
      title: "Сотрудник дорогой к выручке",
      detail: `${employee.name}: ФОТ ${formatPct(employee.laborCostPct)} при выручке ${formatMoney(employee.sales)}. Перерасход к цели: ${formatMoney(laborOverTarget)}.`,
      action:
        "Проверьте часы, ставку, роль на смене и нагрузку: высокая выручка не всегда означает прибыль.",
      laborOverTarget,
    };
  }

  if (
    employee.revenuePerHour !== null &&
    employee.revenuePerHour < options.minimumRevenuePerLaborHour
  ) {
    return {
      ...employee,
      kind: "low-productivity",
      tone: "watch",
      title: "Низкая выручка на час сотрудника",
      detail: `${employee.name}: ${formatMoney(employee.revenuePerHour)} на час при ориентире ${formatMoney(options.minimumRevenuePerLaborHour)}.`,
      action:
        "Сравните смены, посадку и задачи на продажи; возможно, человек стоит не в те часы или без фокуса на чек.",
      laborOverTarget,
    };
  }

  return {
    ...employee,
    kind: "healthy",
    tone: "good",
    title: "Сотрудник выглядит управляемо",
    detail: `${employee.name}: ФОТ ${formatPct(employee.laborCostPct)}, ${formatMoney(employee.revenuePerHour)} на час.`,
    action:
      "Держите как рабочий ориентир и сравнивайте с маржинальностью продаж.",
    laborOverTarget,
  };
}

function shiftRiskScore(
  shift: LaborShiftSummary,
  options: Required<LaborInsightOptions>,
): number {
  if (shift.missingRates > 0) return 30_000 + shift.missingRates * 100;

  if (
    shift.laborCostPct !== null &&
    shift.laborCostPct > options.targetLaborCostPct
  ) {
    return (
      20_000 +
      laborCostOverTarget(
        shift.laborCost,
        shift.revenue,
        options.targetLaborCostPct,
      ) /
        10
    );
  }

  if (
    shift.revenuePerHour !== null &&
    shift.revenuePerHour < options.minimumRevenuePerLaborHour
  ) {
    return 10_000 + (options.minimumRevenuePerLaborHour - shift.revenuePerHour);
  }

  return 0;
}

function employeeRiskScore(
  employee: LaborEmployeeSummary,
  options: Required<LaborInsightOptions>,
): number {
  if (employee.missingRate) return 30_000 + employee.sales / 100;

  if (
    employee.laborCostPct !== null &&
    employee.laborCostPct > options.targetLaborCostPct
  ) {
    return (
      20_000 +
      laborCostOverTarget(
        employee.laborCost,
        employee.sales,
        options.targetLaborCostPct,
      ) /
        10 +
      employee.sales / 1_000
    );
  }

  if (
    employee.revenuePerHour !== null &&
    employee.revenuePerHour < options.minimumRevenuePerLaborHour
  ) {
    return (
      10_000 +
      (options.minimumRevenuePerLaborHour - employee.revenuePerHour) +
      employee.sales / 1_000
    );
  }

  return 0;
}

function splitRevenue(revenue: number, workerCount: number): number {
  if (workerCount <= 0) return 0;
  return revenue / workerCount;
}

function pct(part: number, total: number): number | null {
  if (total <= 0) return null;
  return round((part / total) * 100);
}

function ratio(part: number, total: number): number | null {
  if (total <= 0) return null;
  return roundMoney(part / total);
}

function sum<T, K extends keyof T>(items: T[], key: K): number {
  return roundMoney(
    items.reduce((total, item) => {
      const value = item[key];
      return total + (typeof value === "number" ? value : 0);
    }, 0),
  );
}

function round(value: number): number {
  return Math.round(value * 10) / 10;
}

function roundMoney(value: number): number {
  return Math.round(value);
}

function formatPct(value: number | null): string {
  if (value === null) return "—";
  return `${value.toLocaleString("ru-RU", { maximumFractionDigits: 1 })}%`;
}

function formatMoney(value: number | null): string {
  if (value === null) return "—";
  return `${Math.round(value).toLocaleString("ru-RU")} ₽`;
}

function laborCostOverTarget(
  laborCost: number,
  revenue: number,
  targetLaborCostPct: number,
): number {
  if (revenue <= 0 || targetLaborCostPct <= 0) return 0;
  return Math.max(
    0,
    roundMoney(laborCost - revenue * (targetLaborCostPct / 100)),
  );
}

function expensiveShiftDelta(
  left: LaborShiftSummary,
  right: LaborShiftSummary,
  targetLaborCostPct: number,
): number {
  const overspendDelta =
    laborCostOverTarget(right.laborCost, right.revenue, targetLaborCostPct) -
    laborCostOverTarget(left.laborCost, left.revenue, targetLaborCostPct);
  if (overspendDelta !== 0) return overspendDelta;
  return (right.laborCostPct ?? 0) - (left.laborCostPct ?? 0);
}

function formatLaborCoverageGap(labor: LaborBiSummary): string {
  if (labor.revenueCoveragePct === null) {
    return "Покрытие ФОТ по выручке пока не считается.";
  }

  if (labor.unpricedRevenue <= 0) {
    return `ФОТ доказан на ${formatPct(labor.revenueCoveragePct)} выручки периода.`;
  }

  return `ФОТ доказан на ${formatPct(labor.revenueCoveragePct)} выручки периода; ${formatMoney(labor.unpricedRevenue)} остаются без точной стоимости смен.`;
}

function formatShiftDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value.slice(0, 10);
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "short",
  }).format(date);
}

function plural(value: number, one: string, few: string, many: string): string {
  const mod10 = value % 10;
  const mod100 = value % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
  return many;
}
