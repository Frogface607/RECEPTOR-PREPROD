import type { TeamLaborIikoBlocker } from "./team-labor-readiness";
import type { TeamRoleId } from "./team-os";

export type IikoStaffImportCandidate = {
  name: string;
  roleId: TeamRoleId;
  shiftLabel: string;
  shifts: number;
  hours: number;
  sales: number;
};

export function normalizeIikoStaffName(value: string): string {
  return cleanIikoStaffName(value).toLocaleLowerCase("ru-RU");
}

function cleanIikoStaffName(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

function formatCandidateHours(value: number): string {
  return `${value.toLocaleString("ru-RU", { maximumFractionDigits: 1 })} ч`;
}

export function buildIikoStaffImportCandidates(
  blockers: TeamLaborIikoBlocker[],
  options: { limit?: number } = {},
): IikoStaffImportCandidate[] {
  const limit = Math.max(options.limit ?? 8, 1);
  const bestByName = new Map<string, TeamLaborIikoBlocker & { name: string }>();

  for (const blocker of blockers) {
    if (blocker.action !== "add-member") continue;
    const name = cleanIikoStaffName(blocker.name);
    const normalizedName = normalizeIikoStaffName(name);
    if (!name || !normalizedName) continue;

    const existing = bestByName.get(normalizedName);
    if (
      !existing ||
      blocker.sales > existing.sales ||
      (blocker.sales === existing.sales && blocker.shifts > existing.shifts)
    ) {
      bestByName.set(normalizedName, {
        ...blocker,
        name: existing?.name ?? name,
        roleId: blocker.roleId ?? existing?.roleId,
      });
    } else if (!existing.roleId && blocker.roleId) {
      bestByName.set(normalizedName, { ...existing, roleId: blocker.roleId });
    }
  }

  return [...bestByName.values()]
    .sort((a, b) => b.sales - a.sales || b.shifts - a.shifts)
    .map((blocker) => ({
      name: blocker.name,
      roleId: blocker.roleId ?? "service",
      shiftLabel: `${blocker.shifts.toLocaleString("ru-RU")} смен · ${formatCandidateHours(blocker.hours)}`,
      shifts: blocker.shifts,
      hours: blocker.hours,
      sales: blocker.sales,
    }))
    .slice(0, limit);
}
