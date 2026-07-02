import { SANDBOX_VENUE as SANDBOX_ORG } from "@/lib/mock/sandbox-fixtures";
import {
  DEMO_RESTAURANT_INTELLIGENCE,
  type VenueIntelligenceProfile,
} from "./intelligence";
import {
  DEMO_CONTEXT_ANSWERS,
  type VenueContextAnswers,
} from "./context-questionnaire";

export type ResolvedVenue = {
  id: string;
  name: string;
  city: string;
  type: "restaurant" | "cafe" | "coffee" | "bar" | "chain" | "other";
  timezone: string;
  intelligence: VenueIntelligenceProfile;
  context: VenueContextAnswers;
  iiko: {
    channel: "cloud" | "rms";
    organizationId: string;
    apiLogin?: string;
    rmsHost?: string;
    rmsLogin?: string;
    rmsPassword?: string;
  };
};

const SANDBOX_VENUE: ResolvedVenue = {
  id: "dev-venue",
  name: SANDBOX_ORG.name,
  city: "Город",
  type: "restaurant",
  timezone: SANDBOX_ORG.timezone ?? "Europe/Moscow",
  intelligence: DEMO_RESTAURANT_INTELLIGENCE,
  context: DEMO_CONTEXT_ANSWERS,
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
