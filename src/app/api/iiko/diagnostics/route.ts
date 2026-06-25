import { NextResponse } from "next/server";
import { getVenueAccess } from "@/lib/auth/venue-access";
import { runIikoDiagnostics } from "@/lib/iiko/diagnostics";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

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

  try {
    const report = await runIikoDiagnostics(access.venue, process.env);

    return NextResponse.json(
      {
        venue: {
          id: access.venue.id,
          name: access.venue.name,
        },
        report,
      },
      {
        headers: {
          "Cache-Control": "no-store",
        },
      },
    );
  } catch (error) {
    console.error("[iiko-diagnostics] Unexpected failure", {
      venueId: access.venue.id,
      error: error instanceof Error ? error.message : String(error),
    });

    return NextResponse.json(
      { error: "Не удалось проверить iiko. Попробуйте еще раз." },
      { status: 500 },
    );
  }
}
