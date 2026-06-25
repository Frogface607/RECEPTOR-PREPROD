import { notFound, redirect } from "next/navigation";
import { DashboardHeader } from "@/components/dashboard/dashboard-header";
import { KpiGrid } from "@/components/dashboard/kpi-grid";
import { RevenueChart } from "@/components/dashboard/revenue-chart";
import { DishesChart } from "@/components/dashboard/dishes-chart";
import { CategoriesChart } from "@/components/dashboard/categories-chart";
import { ShiftsTable } from "@/components/dashboard/shifts-table";
import { DataQualityStrip } from "@/components/dashboard/data-quality-strip";
import { DailyBriefCard } from "@/components/dashboard/daily-brief-card";
import { OwnerCockpitCard } from "@/components/dashboard/owner-cockpit-card";
import { VenueIntelligenceCard } from "@/components/dashboard/venue-intelligence-card";
import { MenuEngineeringCard } from "@/components/dashboard/menu-engineering-card";
import { SurvivalBriefCard } from "@/components/dashboard/survival-brief-card";
import { AlertTriangle } from "lucide-react";
import {
  formatPeriodLabel,
  parsePeriodSearchParams,
} from "@/lib/venues/period";
import {
  DEMO_ANCHOR,
  getDashboardClient,
  resolveIikoClientConfig,
} from "@/lib/iiko/config";
import { buildRevenueDataQuality } from "@/lib/iiko/data-quality";
import { MockIikoClient } from "@/lib/iiko/mock-client";
import { getVenueAccess } from "@/lib/auth/venue-access";
import { buildDailyBrief } from "@/lib/brief/daily-brief";
import type { IikoClient } from "@/lib/iiko/types";
import type {
  CategoryStat,
  DishStat,
  RevenueSummary,
  ShiftStat,
} from "@/lib/iiko/models";
import type { DailyBrief } from "@/lib/brief/daily-brief";

type DashboardData = {
  summary: RevenueSummary;
  dishes: DishStat[];
  categories: CategoryStat[];
  shifts: ShiftStat[];
  brief: DailyBrief;
};

async function loadDashboardData(
  client: IikoClient,
  period: Parameters<IikoClient["getRevenueSummary"]>[0],
): Promise<DashboardData> {
  const [summary, dishes, categories, shifts, brief] = await Promise.all([
    client.getRevenueSummary(period),
    client.getDishStatistics(period, 10),
    client.getCategoryStatistics(period),
    client.getShifts(period),
    buildDailyBrief(client, period),
  ]);

  return { summary, dishes, categories, shifts, brief };
}

function dashboardDataErrorMessage(error: unknown): string {
  const message = error instanceof Error ? error.message : String(error);
  if (/iiko RMS|RMS auth|OLAP-запрос|reports\/olap|resto\/api/i.test(message)) {
    return "iiko RMS не отдал BI-данные по этому запросу. Проверьте период и права OLAP reports для логина.";
  }
  if (/olap.*not allowed|right .*olap.*not allowed/i.test(message)) {
    return "Нет права на api/v2/reports/olap. Попросите iiko включить OLAP reports для этого API login.";
  }
  if (/401/i.test(message)) {
    return "iiko отклонил live-запрос. Проверьте права API login.";
  }
  return "Live-данные iiko недоступны. Временно показываем demo.";
}

export default async function DashboardPage({
  params,
  searchParams,
}: {
  params: Promise<{ venueId: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const [{ venueId }, sp] = await Promise.all([params, searchParams]);
  const access = await getVenueAccess(venueId);
  if (!access.ok) {
    if (access.status === 401) {
      redirect(`/auth?next=/dashboard/${encodeURIComponent(venueId)}`);
    }
    notFound();
  }
  const { venue } = access;

  const period = parsePeriodSearchParams(sp);

  const runtimeToday = new Date().toISOString().slice(0, 10);
  const iikoConfig = resolveIikoClientConfig(
    venue,
    process.env,
    runtimeToday,
  );
  const intendedDataMode = iikoConfig.mode === "real" ? "live" : "mock";
  let dataMode: "live" | "mock" = intendedDataMode;
  let dataError: string | null = null;
  let dashboardData: DashboardData;

  try {
    dashboardData = await loadDashboardData(getDashboardClient(venue), period);
  } catch (error) {
    if (intendedDataMode !== "live") throw error;

    dataMode = "mock";
    dataError = dashboardDataErrorMessage(error);
    dashboardData = await loadDashboardData(
      new MockIikoClient({ today: DEMO_ANCHOR }),
      period,
    );
  }

  const { summary, dishes, categories, shifts, brief } = dashboardData;
  const periodLabel = formatPeriodLabel(period);
  const quality = buildRevenueDataQuality(period, summary, {
    today: dataMode === "mock" ? DEMO_ANCHOR : runtimeToday,
    dataMode,
  });

  return (
    <>
      <DashboardHeader venue={venue} period={period} />

      <main className="flex-1 px-4 py-7 sm:px-6 lg:px-10 lg:py-10">
        {/* key={periodLabel} re-triggers the entrance animation on each
            period switch — the dashboard feels alive during exploration. */}
        <div key={periodLabel} className="contents">
          <div className="reveal reveal-1 mb-7">
            <p className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
              Owner Cockpit · {periodLabel}
            </p>
            <h2 className="mt-2 text-balance text-2xl font-medium leading-tight tracking-[-0.02em] sm:text-3xl">
              Утренний управленческий экран
            </h2>
            <p className="mt-2 max-w-xl text-[14px] leading-relaxed text-muted-foreground">
              Сначала решение владельца: что происходит, где риск и что сделать
              сегодня. Графики ниже — детализация.
            </p>
          </div>

          {dataError ? (
            <div className="reveal reveal-2 mb-6 rounded-xl border border-amber-500/25 bg-amber-500/10 p-4 text-sm text-foreground/90">
              <div className="flex items-start gap-3">
                <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-300" />
                <div>
                  <p className="font-medium text-foreground">
                    iiko подключен. BI ждёт права.
                  </p>
                  <p className="mt-1 leading-relaxed text-muted-foreground">
                    {dataError}
                  </p>
                </div>
              </div>
            </div>
          ) : null}

          <div className="reveal reveal-2">
            <OwnerCockpitCard
              venue={venue}
              brief={brief}
              periodLabel={periodLabel}
              dataMode={dataMode}
            />
          </div>

          <div className="reveal reveal-2 mt-6">
            <KpiGrid
              revenue={summary.revenue}
              revenueDeltaPct={
                brief.revenue.comparisonAvailable
                  ? brief.revenue.deltaPct
                  : undefined
              }
              averageCheck={summary.averageCheck}
              itemsSold={summary.itemsSold}
              uniqueDishes={summary.uniqueDishes}
              periodLabel={periodLabel}
            />
          </div>

          <div className="reveal reveal-2 mt-6">
            <DataQualityStrip quality={quality} />
          </div>

          <div className="reveal reveal-3 mt-6">
            <DailyBriefCard brief={brief} venueId={venueId} />
          </div>

          <div className="reveal reveal-3 mt-6">
            <SurvivalBriefCard
              venueId={venueId}
              brief={brief}
              dishes={dishes}
              categories={categories}
              dataQuality={quality}
            />
          </div>

          <div className="reveal reveal-3 mt-6">
            <VenueIntelligenceCard
              profile={venue.intelligence}
              context={venue.context}
            />
          </div>

          <div className="reveal reveal-4 mt-6">
            <MenuEngineeringCard dishes={dishes} />
          </div>

          <div className="reveal reveal-4 mt-10 grid gap-6 lg:grid-cols-5">
            <div className="lg:col-span-3">
              <RevenueChart points={summary.points} />
            </div>
            <div className="lg:col-span-2">
              <CategoriesChart categories={categories} />
            </div>
          </div>

          <div className="reveal reveal-5 mt-6">
            <DishesChart dishes={dishes} />
          </div>

          <div className="reveal reveal-5 mt-6">
            <ShiftsTable shifts={shifts} />
          </div>
        </div>

      </main>
    </>
  );
}
