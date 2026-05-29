import { notFound } from "next/navigation";
import { DashboardHeader } from "@/components/dashboard/dashboard-header";
import { KpiGrid } from "@/components/dashboard/kpi-grid";
import { RevenueChart } from "@/components/dashboard/revenue-chart";
import { DishesChart } from "@/components/dashboard/dishes-chart";
import { CategoriesChart } from "@/components/dashboard/categories-chart";
import { ShiftsTable } from "@/components/dashboard/shifts-table";
import { getVenue } from "@/lib/venues/get-venue";
import {
  parsePeriodSearchParams,
  PERIOD_LABELS_RU,
} from "@/lib/venues/period";
import { getIikoClient } from "@/lib/iiko/client";

/**
 * Dashboard "today" anchor.
 * Phase 0–3: deterministic 2026-05-29 for stable demos and screenshots.
 * Phase 4+: read from the server clock once real iiko credentials land.
 */
const ANCHOR = "2026-05-29";

export default async function DashboardPage({
  params,
  searchParams,
}: {
  params: Promise<{ venueId: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const [{ venueId }, sp] = await Promise.all([params, searchParams]);
  const venue = getVenue(venueId);
  if (!venue) notFound();

  const period = parsePeriodSearchParams(sp);

  const client = getIikoClient({
    channel: "cloud",
    apiLogin: "",
    organizationId: venue.iiko.organizationId,
    today: ANCHOR,
  });

  const [summary, dishes, categories, shifts] = await Promise.all([
    client.getRevenueSummary(period),
    client.getDishStatistics(period, 10),
    client.getCategoryStatistics(period),
    client.getShifts(period),
  ]);

  const periodLabel = PERIOD_LABELS_RU[period.type];

  return (
    <>
      <DashboardHeader venue={venue} period={period.type} />

      <main className="flex-1 px-6 py-8 lg:px-10 lg:py-10">
        <div className="mb-7">
          <p className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
            Сводка · {periodLabel}
          </p>
          <h2 className="mt-2 text-balance text-3xl font-medium leading-tight tracking-[-0.02em]">
            Что{" "}
            <span className="font-display italic text-brand">
              Receptor видит
            </span>{" "}
            в зале сегодня
          </h2>
        </div>

        <KpiGrid
          revenue={summary.revenue}
          averageCheck={summary.averageCheck}
          itemsSold={summary.itemsSold}
          uniqueDishes={summary.uniqueDishes}
          periodLabel={periodLabel}
        />

        <div className="mt-10 grid gap-6 lg:grid-cols-5">
          <div className="lg:col-span-3">
            <RevenueChart points={summary.points} />
          </div>
          <div className="lg:col-span-2">
            <CategoriesChart categories={categories} />
          </div>
        </div>

        <div className="mt-6">
          <DishesChart dishes={dishes} />
        </div>

        <div className="mt-6">
          <ShiftsTable shifts={shifts} />
        </div>

        <p className="mt-12 text-center text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
          Receptor v2 · USE_MOCK_IIKO=true · anchor {ANCHOR}
        </p>
      </main>
    </>
  );
}
