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

export function hasLaborRate(member: StaffMember): boolean {
  return Boolean(member.hourlyRate || member.shiftPay || member.revenueBonusPct);
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
