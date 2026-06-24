/**
 * Venue access guard for dashboard surfaces.
 *
 * Demo mode is intentionally narrow: the synthetic demo user can only open
 * known in-code demo venues. Real mode resolves venues through Supabase under
 * the current user's session, so RLS and owner_user_id both apply.
 */

import { getCurrentUser, type SessionUser } from "./session";
import { getServerSupabase } from "@/lib/db/server";
import { decryptSecret } from "@/lib/db/encryption";
import { getVenue, type ResolvedVenue } from "@/lib/venues/get-venue";
import { normalizeVenueProfile } from "@/lib/venues/intelligence";
import { normalizeContextAnswers } from "@/lib/venues/context-questionnaire";

type VenueAccessOk = {
  ok: true;
  user: SessionUser;
  venue: ResolvedVenue;
};

type VenueAccessError = {
  ok: false;
  status: 401 | 404;
  error: "unauthorized" | "venue not found";
};

export type VenueAccess = VenueAccessOk | VenueAccessError;

type DbVenue = {
  id: string;
  name: string;
  city: string | null;
  type: ResolvedVenue["type"] | null;
  timezone: string | null;
  intelligence_profile?: unknown | null;
  context_profile?: unknown | null;
};

type DbIikoCredential = {
  channel: ResolvedVenue["iiko"]["channel"] | null;
  iiko_org_id: string | null;
  creds_encrypted: string;
  iv: string;
};

type RmsCredentialsPayload = {
  host?: string;
  login?: string;
  password?: string;
};

function parseRmsCredentials(value: string): RmsCredentialsPayload {
  try {
    const parsed = JSON.parse(value) as RmsCredentialsPayload;
    return {
      host: typeof parsed.host === "string" ? parsed.host : "",
      login: typeof parsed.login === "string" ? parsed.login : "",
      password: typeof parsed.password === "string" ? parsed.password : "",
    };
  } catch {
    return {};
  }
}

function safeDecryptCredential(credential: DbIikoCredential): string {
  try {
    return decryptSecret({
      ciphertext: credential.creds_encrypted,
      iv: credential.iv,
    });
  } catch (error) {
    console.error("[venue-access] Failed to decrypt iiko credentials", {
      channel: credential.channel,
      error: error instanceof Error ? error.message : String(error),
    });
    return "";
  }
}

function toResolvedVenue(
  venue: DbVenue,
  credential?: DbIikoCredential | null,
): ResolvedVenue {
  const decrypted = credential ? safeDecryptCredential(credential) : "";
  const rms = credential?.channel === "rms" ? parseRmsCredentials(decrypted) : {};

  return {
    id: venue.id,
    name: venue.name,
    city: venue.city ?? "",
    type: venue.type ?? "other",
    timezone: venue.timezone ?? "Asia/Irkutsk",
    intelligence: normalizeVenueProfile(venue.intelligence_profile),
    context: normalizeContextAnswers(venue.context_profile),
    iiko: {
      channel: credential?.channel ?? "cloud",
      organizationId: credential?.iiko_org_id ?? venue.id,
      apiLogin: credential?.channel === "cloud" ? decrypted : undefined,
      rmsHost: rms.host,
      rmsLogin: rms.login,
      rmsPassword: rms.password,
    },
  };
}

export async function getVenueAccess(venueId: string): Promise<VenueAccess> {
  const user = await getCurrentUser();
  if (!user) {
    return { ok: false, status: 401, error: "unauthorized" };
  }

  if (user.isDemo) {
    const venue = getVenue(venueId);
    if (!venue) {
      return { ok: false, status: 404, error: "venue not found" };
    }
    return { ok: true, user, venue };
  }

  const supabase = await getServerSupabase();
  if (!supabase) {
    return { ok: false, status: 401, error: "unauthorized" };
  }

  let venueResult = await supabase
    .from("venues")
    .select("id,name,city,type,timezone,intelligence_profile,context_profile")
    .eq("id", venueId)
    .eq("owner_user_id", user.id)
    .maybeSingle<DbVenue>();

  if (
    venueResult.error &&
    /(intelligence_profile|context_profile)/i.test(venueResult.error.message)
  ) {
    venueResult = await supabase
      .from("venues")
      .select("id,name,city,type,timezone")
      .eq("id", venueId)
      .eq("owner_user_id", user.id)
      .maybeSingle<DbVenue>();
  }

  const { data: venue } = venueResult;

  if (!venue) {
    return { ok: false, status: 404, error: "venue not found" };
  }

  const { data: credential } = await supabase
    .from("iiko_credentials")
    .select("channel,iiko_org_id,creds_encrypted,iv")
    .eq("venue_id", venue.id)
    .eq("status", "active")
    .maybeSingle<DbIikoCredential>();

  return { ok: true, user, venue: toResolvedVenue(venue, credential) };
}
