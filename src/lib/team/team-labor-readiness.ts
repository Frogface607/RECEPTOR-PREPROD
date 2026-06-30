import type { StaffMember } from "./team-os";
import type {
  LaborBiSummary,
  LaborBlocker,
  LaborReadinessStatus,
} from "./labor-bi";

export type TeamLaborReadinessStatus = "ready" | "partial" | "blocked";

export type TeamLaborIikoBlocker = LaborBlocker & {
  action: "add-member" | "set-rate";
};

export type TeamLaborReadiness = {
  status: TeamLaborReadinessStatus;
  totalStaff: number;
  activeStaff: number;
  readyStaff: number;
  missingStaff: StaffMember[];
  coveragePct: number;
  source: "team" | "iiko";
  iikoStatus: LaborReadinessStatus | null;
  iikoStaffShifts: number;
  iikoRevenueCoveragePct: number | null;
  iikoUnpricedStaffShifts: number;
  iikoUnpricedRevenue: number;
  iikoBlockers: TeamLaborIikoBlocker[];
};

export type TeamBulkLaborRateTarget = {
  id: string;
  name: string;
  roleId: StaffMember["roleId"];
  shiftLabel: string;
};

export type TeamLaborSetupBlocker = {
  name: string;
  reason: LaborBlocker["reason"];
  action: TeamLaborIikoBlocker["action"];
  shifts: number;
  hours: number;
  revenue: number;
};

export type TeamLaborSetupProgressStatus =
  "ready" | "needs-shifts" | "needs-members" | "needs-rates";

export type TeamLaborSetupProgress = {
  status: TeamLaborSetupProgressStatus;
  tone: "good" | "watch" | "risk";
  title: string;
  detail: string;
  ctaLabel: string | null;
  target: "labor-rates" | null;
  coveragePct: number;
  activeStaff: number;
  readyStaff: number;
  missingStaffCards: number;
  missingRateCards: number;
  bulkRateTargets: TeamBulkLaborRateTarget[];
  setupBlockers: TeamLaborSetupBlocker[];
  unpricedShifts: number;
  unpricedRevenue: number;
};

export function hasLaborRate(member: StaffMember): boolean {
  return Boolean(
    member.hourlyRate || member.shiftPay || member.revenueBonusPct,
  );
}

export function buildBulkLaborRateTargets(
  staff: StaffMember[],
  options: { limit?: number } = {},
): TeamBulkLaborRateTarget[] {
  const limit = Math.max(options.limit ?? 50, 1);

  return staff
    .filter((member) => member.status !== "paused" && !hasLaborRate(member))
    .sort((a, b) => a.name.localeCompare(b.name, "ru-RU"))
    .slice(0, limit)
    .map((member) => ({
      id: member.id,
      name: member.name,
      roleId: member.roleId,
      shiftLabel: member.shiftLabel,
    }));
}

export function buildTeamLaborSetupProgress(
  staff: StaffMember[],
  readiness: TeamLaborReadiness,
): TeamLaborSetupProgress {
  const bulkRateTargets = buildBulkLaborRateTargets(staff);
  const missingStaffCards = readiness.iikoBlockers.filter(
    (blocker) => blocker.reason === "missing-member",
  ).length;
  const missingRateBlockers = readiness.iikoBlockers.filter(
    (blocker) => blocker.reason === "missing-rate",
  ).length;
  const missingRateCards = Math.max(
    bulkRateTargets.length,
    missingRateBlockers,
  );
  const setupBlockers = readiness.iikoBlockers.slice(0, 3).map((blocker) => ({
    name: blocker.name,
    reason: blocker.reason,
    action: blocker.action,
    shifts: blocker.shifts,
    hours: blocker.hours,
    revenue: blocker.sales,
  }));
  const base = {
    coveragePct: readiness.coveragePct,
    activeStaff: readiness.activeStaff,
    readyStaff: readiness.readyStaff,
    missingStaffCards,
    missingRateCards,
    bulkRateTargets,
    setupBlockers,
    unpricedShifts: readiness.iikoUnpricedStaffShifts,
    unpricedRevenue: readiness.iikoUnpricedRevenue,
  };

  if (readiness.iikoStatus === "blocked" && readiness.iikoStaffShifts === 0) {
    return {
      ...base,
      status: "needs-shifts",
      tone: "risk",
      title: "Сначала нужны смены iiko",
      detail:
        "ФОТ нельзя доказать без сотрудников и часов из смен. Проверьте период, права OLAP и выгрузку смен.",
      ctaLabel: null,
      target: null,
    };
  }

  if (missingStaffCards > 0) {
    return {
      ...base,
      status: "needs-members",
      tone: "watch",
      title: `Создать карточки из iiko: ${missingStaffCards}`,
      detail:
        "Смены уже видны, но часть имен еще не связана с Team OS. После импорта ставки можно закрыть пачкой.",
      ctaLabel: "Открыть импорт",
      target: "labor-rates",
    };
  }

  if (missingRateCards > 0) {
    return {
      ...base,
      status: "needs-rates",
      tone: readiness.status === "blocked" ? "risk" : "watch",
      title: `Закрыть ставки ФОТ: ${missingRateCards}`,
      detail:
        "Карточки сотрудников есть. Заполните типовую ставку пачкой, а потом поправьте исключения вручную.",
      ctaLabel: "Закрыть ставки",
      target: "labor-rates",
    };
  }

  if (readiness.status !== "ready") {
    return {
      ...base,
      status: "needs-rates",
      tone: readiness.status === "blocked" ? "risk" : "watch",
      title: "Проверить ставки ФОТ",
      detail:
        "Часть сменной выручки пока без точного ФОТ. Откройте Team OS и проверьте связку сотрудников со сменами.",
      ctaLabel: "Открыть Team OS",
      target: "labor-rates",
    };
  }

  return {
    ...base,
    status: "ready",
    tone: "good",
    title: "ФОТ готов к управленческим выводам",
    detail:
      "Ставки заведены, смены связаны с Team OS. Можно смотреть стоимость команды, график и производительность смен.",
    ctaLabel: null,
    target: null,
  };
}

export function buildTeamLaborReadiness(
  staff: StaffMember[],
  labor?: LaborBiSummary | null,
): TeamLaborReadiness {
  const activeStaff = staff.filter((member) => member.status !== "paused");
  const readyStaff = activeStaff.filter(hasLaborRate);
  const missingStaff = activeStaff.filter((member) => !hasLaborRate(member));
  const teamCoveragePct =
    activeStaff.length > 0
      ? Math.round((readyStaff.length / activeStaff.length) * 100)
      : 0;
  const iikoCoveragePct = labor?.revenueCoveragePct ?? null;
  const useIikoCoverage = typeof iikoCoveragePct === "number";
  const iikoBlockers =
    labor?.topBlockers.map((blocker) => ({
      ...blocker,
      action:
        blocker.reason === "missing-member"
          ? ("add-member" as const)
          : ("set-rate" as const),
    })) ?? [];

  return {
    status:
      labor?.laborReadinessStatus ??
      (activeStaff.length === 0 || readyStaff.length === 0
        ? "blocked"
        : missingStaff.length > 0
          ? "partial"
          : "ready"),
    totalStaff: staff.length,
    activeStaff: activeStaff.length,
    readyStaff: readyStaff.length,
    missingStaff,
    coveragePct: useIikoCoverage ? iikoCoveragePct : teamCoveragePct,
    source: useIikoCoverage ? "iiko" : "team",
    iikoStatus: labor?.laborReadinessStatus ?? null,
    iikoStaffShifts: labor?.staffShifts ?? 0,
    iikoRevenueCoveragePct: iikoCoveragePct,
    iikoUnpricedStaffShifts: labor?.unpricedStaffShifts ?? 0,
    iikoUnpricedRevenue: labor?.unpricedRevenue ?? 0,
    iikoBlockers,
  };
}
