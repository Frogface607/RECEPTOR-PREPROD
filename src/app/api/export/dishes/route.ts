import { NextResponse } from "next/server";
import { getDashboardClient } from "@/lib/iiko/config";
import {
  parsePeriodSearchParams,
  PERIOD_LABELS_RU,
} from "@/lib/venues/period";
import { toCsv, type CsvColumn } from "@/lib/export/csv";
import type { DishStat } from "@/lib/iiko/models";
import { getVenueAccess } from "@/lib/auth/venue-access";

const COLUMNS: CsvColumn<DishStat>[] = [
  { header: "Блюдо", value: (d) => d.dishName },
  { header: "Группа", value: (d) => d.dishGroup },
  { header: "Количество", value: (d) => d.dishAmountInt },
  { header: "Сумма (₽)", value: (d) => d.dishSumInt },
];

export async function GET(request: Request) {
  const url = new URL(request.url);
  const venueId = url.searchParams.get("venueId") ?? "";
  const access = await getVenueAccess(venueId);
  if (!access.ok) {
    return NextResponse.json(
      { error: access.error },
      { status: access.status },
    );
  }
  const { venue } = access;

  const period = parsePeriodSearchParams(
    Object.fromEntries(url.searchParams),
  );
  const client = getDashboardClient(venue);

  const dishes = await client.getDishStatistics(period, 100);
  const body = toCsv(dishes, COLUMNS);

  const periodTag =
    period.type === "CUSTOM"
      ? `${period.from}_${period.to}`
      : period.type.toLowerCase();
  const filename = `receptor_${venueId}_dishes_${periodTag}.csv`;

  return new NextResponse(body, {
    status: 200,
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="${filename}"`,
      "X-Receptor-Period": PERIOD_LABELS_RU[period.type],
    },
  });
}
