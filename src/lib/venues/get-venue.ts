import { SANDBOX_VENUE as SANDBOX_ORG } from "@/lib/mock/sandbox-fixtures";

export type ResolvedVenue = {
  id: string;
  name: string;
  city: string;
  type: "restaurant" | "cafe" | "coffee" | "bar" | "chain" | "other";
  timezone: string;
  iiko: {
    channel: "cloud" | "rms";
    organizationId: string;
    apiLogin?: string;
  };
};

const SANDBOX_VENUE: ResolvedVenue = {
  id: "dev-venue",
  name: SANDBOX_ORG.name,
  city: "Sandbox",
  type: "restaurant",
  timezone: SANDBOX_ORG.timezone ?? "Asia/Irkutsk",
  iiko: {
    channel: "cloud",
    organizationId: SANDBOX_ORG.id,
  },
};

const KNOWN_VENUES: Record<string, ResolvedVenue> = {
  "dev-venue": SANDBOX_VENUE,
};

export function getVenue(id: string): ResolvedVenue | null {
  return KNOWN_VENUES[id] ?? null;
}

export function listKnownVenues(): ResolvedVenue[] {
  return [SANDBOX_VENUE];
}
