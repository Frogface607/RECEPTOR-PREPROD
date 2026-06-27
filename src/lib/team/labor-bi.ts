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
      };
    });
  }

  return [
    {
      name: shift.employee,
      startedAt: shift.openTime,
      endedAt: shift.closeTime,
    },
  ];
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
