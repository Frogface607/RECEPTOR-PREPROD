/**
 * Venue resolver — stubbed for Phase 2.
 *
 * Phase 3 swaps the implementation to read from Supabase
 * (`venues` table joined with `iiko_credentials`). The signature stays the same.
 */

import { EDISON_VENUE } from "@/lib/mock/edison-fixtures";

export type ResolvedVenue = {
  id: string;
  name: string;
  city: string;
  type: "restaurant" | "cafe" | "coffee" | "bar" | "chain" | "other";
  timezone: string;
  iiko: {
    channel: "cloud" | "rms";
    organizationId: string;
  };
};

const DEMO_VENUE: ResolvedVenue = {
  id: "edison-demo",
  name: EDISON_VENUE.name,
  city: "Иркутск",
  type: "bar",
  timezone: EDISON_VENUE.timezone ?? "Asia/Irkutsk",
  iiko: {
    channel: "cloud",
    organizationId: EDISON_VENUE.id,
  },
};

const KNOWN_VENUES: Record<string, ResolvedVenue> = {
  "edison-demo": DEMO_VENUE,
};

export function getVenue(id: string): ResolvedVenue | null {
  return KNOWN_VENUES[id] ?? null;
}

export function listKnownVenues(): ResolvedVenue[] {
  return Object.values(KNOWN_VENUES);
}
