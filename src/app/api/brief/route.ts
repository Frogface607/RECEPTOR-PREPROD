import { NextResponse } from "next/server";
import { getVenueAccess } from "@/lib/auth/venue-access";
import { buildDailyBrief, renderDailyBriefText } from "@/lib/brief/daily-brief";
import { getDashboardClient } from "@/lib/iiko/config";
import { parsePeriodSearchParams } from "@/lib/venues/period";

export const runtime = "nodejs";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const venueId = url.searchParams.get("venueId") ?? "";
  const format = url.searchParams.get("format") ?? "json";

  if (format !== "json" && format !== "text") {
    return NextResponse.json(
      { error: "format must be json or text" },
      { status: 400 },
    );
  }

  const access = await getVenueAccess(venueId);
  if (!access.ok) {
    return NextResponse.json(
      { error: access.error },
      { status: access.status },
    );
  }

  const period = parsePeriodSearchParams(Object.fromEntries(url.searchParams));
  const client = getDashboardClient(access.venue);
  const brief = await buildDailyBrief(client, period.type);

  if (format === "text") {
    return new NextResponse(
      renderDailyBriefText(brief, { venueName: access.venue.name }),
      {
        status: 200,
        headers: {
          "Content-Type": "text/plain; charset=utf-8",
          "Cache-Control": "no-store",
        },
      },
    );
  }

  return NextResponse.json(
    {
      venue: {
        id: access.venue.id,
        name: access.venue.name,
        city: access.venue.city,
        type: access.venue.type,
      },
      brief,
      text: renderDailyBriefText(brief, { venueName: access.venue.name }),
    },
    {
      headers: {
        "Cache-Control": "no-store",
      },
    },
  );
}
