import type { StaffMember } from "./team-os";

export type TeamLaborReadinessStatus = "ready" | "partial" | "blocked";

export type TeamLaborReadiness = {
  status: TeamLaborReadinessStatus;
  totalStaff: number;
  activeStaff: number;
  readyStaff: number;
  missingStaff: StaffMember[];
  coveragePct: number;
};

export function hasLaborRate(member: StaffMember): boolean {
  return Boolean(member.hourlyRate || member.shiftPay || member.revenueBonusPct);
}

export function buildTeamLaborReadiness(
  staff: StaffMember[],
): TeamLaborReadiness {
  const activeStaff = staff.filter((member) => member.status !== "paused");
  const readyStaff = activeStaff.filter(hasLaborRate);
  const missingStaff = activeStaff.filter((member) => !hasLaborRate(member));
  const coveragePct =
    activeStaff.length > 0
      ? Math.round((readyStaff.length / activeStaff.length) * 100)
      : 0;

  return {
    status:
      activeStaff.length === 0 || readyStaff.length === 0
        ? "blocked"
        : missingStaff.length > 0
          ? "partial"
          : "ready",
    totalStaff: staff.length,
    activeStaff: activeStaff.length,
    readyStaff: readyStaff.length,
    missingStaff,
    coveragePct,
  };
}
