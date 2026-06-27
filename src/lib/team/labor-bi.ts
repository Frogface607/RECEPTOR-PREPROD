import type { ShiftStat } from "@/lib/iiko/models";
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
  shiftsBreakdown: LaborShiftSummary[];
  employees: LaborEmployeeSummary[];
};

export type LaborInsightTone = "risk" | "watch" | "good" | "setup";

export type LaborInsight = {
  tone: LaborInsightTone;
  title: string;
  detail: string;
  action: string;
};

export type LaborInsightOptions = {
  targetLaborCostPct?: number;
  minimumRevenuePerLaborHour?: number;
};

export function buildLaborBi(input: {
  shifts: LaborShiftInput[];
  staff?: StaffMember[];
  rates?: LaborRate[];
}): LaborBiSummary {
  const staffById = new Map((input.staff ?? []).map((member) => [member.id, member]));
  const employeeTotals = new Map<string, MutableEmployeeSummary>();

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
    missingRates: shiftsBreakdown.reduce((total, shift) => total + shift.missingRates, 0),
    shiftsBreakdown,
    employees,
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
    insights.push({
      tone: "setup",
      title: "Не все ставки заведены",
      detail: `${labor.missingRates} ${plural(labor.missingRates, "сотрудник", "сотрудника", "сотрудников")} без ставки мешают точно считать ФОТ.`,
      action: "Заполните ставки в Team OS и вернитесь к этому периоду.",
    });
  }

  if (labor.laborCost === 0 && labor.staffShifts > 0) {
    insights.push({
      tone: "setup",
      title: "ФОТ сейчас считается как 0 ₽",
      detail: "Смены есть, но по ним нет ни почасовой ставки, ни фикса за смену, ни процента от продаж.",
      action: "Задайте хотя бы один тип ставки для сотрудников на смене.",
    });
  }

  if (labor.laborCostPct !== null && labor.laborCostPct > targetLaborCostPct) {
    insights.push({
      tone: "risk",
      title: "ФОТ выше целевой нормы",
      detail: `Сейчас ${formatPct(labor.laborCostPct)} от выручки при ориентире ${formatPct(targetLaborCostPct)}.`,
      action: "Проверьте состав смены, часы и фактическую загрузку зала.",
    });
  }

  const expensiveShift = labor.shiftsBreakdown
    .filter((shift) => shift.laborCostPct !== null && shift.laborCostPct > targetLaborCostPct)
    .sort((a, b) => (b.laborCostPct ?? 0) - (a.laborCostPct ?? 0))[0];
  if (expensiveShift) {
    insights.push({
      tone: "watch",
      title: `Дорогая смена: ${formatShiftDate(expensiveShift.openTime)}`,
      detail: `ФОТ смены ${formatPct(expensiveShift.laborCostPct)} при выручке ${formatMoney(expensiveShift.revenue)}.`,
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
      action: "Проверьте слабые часы, лишние руки на смене и продажи официантов.",
    });
  }

  if (insights.length === 0) {
    insights.push({
      tone: "good",
      title: "ФОТ выглядит управляемо",
      detail: `ФОТ ${formatPct(labor.laborCostPct)} от выручки, ${formatMoney(labor.revenuePerLaborHour)} на человеко-час.`,
      action: "Сравните с маржинальностью блюд и держите этот уровень как базу.",
    });
  }

  return insights.slice(0, 3);
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
      const member = worker.memberId ? staffById.get(worker.memberId) : undefined;
      return {
        ...worker,
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
      name: shift.employee,
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
  return [...staffById.values()].find(
    (member) => normalizeName(member.name) === normalizedName,
  );
}

function normalizeName(value: string): string {
  return value.trim().toLowerCase().replace(/\s+/g, " ");
}

function resolveRate(worker: LaborShiftWorker, rates: LaborRate[]): LaborRate | null {
  if (worker.hourlyRate || worker.shiftPay || worker.revenueBonusPct) return worker;
  return (
    (worker.memberId
      ? rates.find((rate) => rate.memberId === worker.memberId)
      : undefined) ??
    (worker.roleId ? rates.find((rate) => rate.roleId === worker.roleId) : undefined) ??
    null
  );
}

function resolveHours(worker: LaborShiftWorker, shift: LaborShiftInput): number {
  if (typeof worker.hours === "number" && Number.isFinite(worker.hours)) {
    return Math.max(worker.hours, 0);
  }

  const startedAt = worker.startedAt ?? shift.openTime;
  const endedAt = worker.endedAt ?? shift.closeTime;
  if (!endedAt) return 0;

  const started = Date.parse(startedAt);
  const ended = Date.parse(endedAt);
  if (!Number.isFinite(started) || !Number.isFinite(ended) || ended <= started) {
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

  return roundMoney(hours * hourlyRate + shiftPay + sales * (revenueBonusPct / 100));
}

function isMissingRate(worker: LaborShiftWorker, rate: LaborRate | null): boolean {
  return !worker.hourlyRate && !worker.shiftPay && !worker.revenueBonusPct && !rate;
}

function upsertEmployee(
  map: Map<string, MutableEmployeeSummary>,
  worker: LaborShiftWorker,
  delta: Pick<MutableEmployeeSummary, "hours" | "sales" | "laborCost" | "missingRate">,
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

function finalizeEmployee(employee: MutableEmployeeSummary): LaborEmployeeSummary {
  return {
    ...employee,
    hours: round(employee.hours),
    sales: roundMoney(employee.sales),
    laborCost: roundMoney(employee.laborCost),
    revenuePerHour: ratio(employee.sales, employee.hours),
    laborCostPct: pct(employee.laborCost, employee.sales),
  };
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
