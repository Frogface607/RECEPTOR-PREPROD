import { getVenueAccess } from "@/lib/auth/venue-access";
import { DEMO_ANCHOR, getDashboardClient } from "@/lib/iiko/config";
import type { Period } from "@/lib/iiko/models";
import { MockIikoClient } from "@/lib/iiko/mock-client";
import {
  buildLaborBi,
  type LaborBiSummary,
  type LaborShiftInput,
} from "@/lib/team/labor-bi";
import type { StaffMember } from "@/lib/team/team-os";

export type TeamLaborLoadResult = {
  laborBi: LaborBiSummary | null;
  shifts: LaborShiftInput[];
  source: "live" | "demo" | "unavailable";
  error: string | null;
};

export function laborLoadErrorMessage(error: unknown): string {
  const message = error instanceof Error ? error.message : String(error);
  if (/401|auth|unauthorized/i.test(message)) {
    return "iiko не дала доступ к сменам. Проверьте права интеграции.";
  }
  if (/OLAP|reports|shifts|смен/i.test(message)) {
    return "iiko не вернула смены за выбранный период. Проверьте период и права OLAP.";
  }
  return "Смены iiko временно недоступны. Показываем только ставки Team OS.";
}

export async function loadTeamLabor(input: {
  venueId: string;
  staff: StaffMember[];
  period: Period;
}): Promise<TeamLaborLoadResult> {
  if (input.venueId === "dev-venue") {
    const shifts = await new MockIikoClient({ today: DEMO_ANCHOR }).getShifts(
      input.period,
    );
    return {
      laborBi: buildLaborBi({ shifts, staff: input.staff }),
      shifts,
      source: "demo",
      error: null,
    };
  }

  const access = await getVenueAccess(input.venueId);
  if (!access.ok) {
    return {
      laborBi: null,
      shifts: [],
      source: "unavailable",
      error: "Нет доступа к заведению для загрузки смен iiko.",
    };
  }

  try {
    const shifts = await getDashboardClient(access.venue).getShifts(
      input.period,
    );
    return {
      laborBi: buildLaborBi({ shifts, staff: input.staff }),
      shifts,
      source: "live",
      error: null,
    };
  } catch (error) {
    console.error("[team] Failed to load iiko labor shifts", {
      venueId: input.venueId,
      error: error instanceof Error ? error.message : String(error),
    });
    return {
      laborBi: null,
      shifts: [],
      source: "unavailable",
      error: laborLoadErrorMessage(error),
    };
  }
}
