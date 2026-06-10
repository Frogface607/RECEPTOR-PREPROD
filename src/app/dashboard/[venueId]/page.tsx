import { notFound, redirect } from "next/navigation";
import { DashboardHeader } from "@/components/dashboard/dashboard-header";
import { KpiGrid } from "@/components/dashboard/kpi-grid";
import { RevenueChart } from "@/components/dashboard/revenue-chart";
import { DishesChart } from "@/components/dashboard/dishes-chart";
import { CategoriesChart } from "@/components/dashboard/categories-chart";
import { ShiftsTable } from "@/components/dashboard/shifts-table";
import { DailyBriefCard } from "@/components/dashboard/daily-brief-card";
import {
  parsePeriodSearchParams,
  PERIOD_LABELS_RU,
} from "@/lib/venues/period";
import { getDashboardClient } from "@/lib/iiko/config";
import { getVenueAccess } from "@/lib/auth/venue-access";
import { buildDailyBrief } from "@/lib/brief/daily-brief";

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

  // Sandbox fixtures or real Cloud, decided by env/credentials.
  // Flipping USE_MOCK_IIKO=false + pasting apiLogin is the only change needed.
  const client = getDashboardClient(venue);
  const [summary, dishes, categories, shifts, brief] = await Promise.all([
    client.getRevenueSummary(period),
    client.getDishStatistics(period, 10),
    client.getCategoryStatistics(period),
    client.getShifts(period),
    buildDailyBrief(client, period.type),
  ]);

  const periodLabel = PERIOD_LABELS_RU[period.type];

  return (
    <>
      <DashboardHeader venue={venue} period={period.type} />

      <main className="flex-1 px-4 py-7 sm:px-6 lg:px-10 lg:py-10">
        {/* key={period.type} re-triggers the entrance animation on each
            period switch — the dashboard feels alive during exploration. */}
        <div key={period.type} className="contents">
          <div className="reveal reveal-1 mb-7">
            <p className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
              Сводка · {periodLabel}
            </p>
            <h2 className="mt-2 text-balance text-2xl font-medium leading-tight tracking-[-0.02em] sm:text-3xl">
              Операционная картина зала
            </h2>
            <p className="mt-2 max-w-xl text-[14px] leading-relaxed text-muted-foreground">
              Выручка, категории, блюда, смены и brief владельца за выбранный
              период.
            </p>
          </div>

          <div className="reveal reveal-2">
            <KpiGrid
              revenue={summary.revenue}
              averageCheck={summary.averageCheck}
              itemsSold={summary.itemsSold}
              uniqueDishes={summary.uniqueDishes}
              periodLabel={periodLabel}
            />
          </div>

          <div className="reveal reveal-3 mt-6">
            <DailyBriefCard brief={brief} venueId={venueId} />
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
