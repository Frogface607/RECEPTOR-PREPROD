"use server";

import { z } from "zod";
import { getServerSupabase } from "@/lib/db/server";
import { getCurrentUser } from "@/lib/auth/session";
import { encryptSecret } from "@/lib/db/encryption";
import { CloudIikoClient } from "@/lib/iiko/cloud-client";
import { RmsIikoClient } from "@/lib/iiko/rms-client";
import { buildTeamOnboardingSeed } from "@/lib/team/team-onboarding-seed";
import { normalizeVenueProfile } from "@/lib/venues/intelligence";
import { normalizeContextAnswers } from "@/lib/venues/context-questionnaire";

const VenueInput = z.object({
  name: z.string().min(1).max(120),
  type: z.enum(["restaurant", "cafe", "coffee", "bar", "chain", "other"]),
  city: z.string().max(120).optional().default(""),
  intelligenceProfile: z.unknown().optional(),
  contextAnswers: z.unknown().optional(),
  channel: z.enum(["cloud", "rms"]).optional().default("cloud"),
  apiLogin: z.string().trim().optional().default(""),
  organizationId: z.string().optional().default(""),
  rmsHost: z.string().trim().optional().default(""),
  rmsLogin: z.string().trim().optional().default(""),
  rmsPassword: z.string().optional().default(""),
});

export type OnboardingResult =
  | { ok: true; mode: "saved" | "sandbox"; venueId: string }
  | { ok: false; error: string };

export type IikoOrganizationOption = {
  id: string;
  name: string;
};

export type ProbeIikoResult =
  | { ok: true; organizations: IikoOrganizationOption[] }
  | { ok: false; error: string };

const ProbeInput = z.object({
  apiLogin: z.string().trim().min(1, "iiko API ключ обязателен"),
});

const ProbeRmsInput = z.object({
  host: z.string().trim().min(1, "Адрес iiko RMS обязателен"),
  login: z.string().trim().min(1, "Логин iiko RMS обязателен"),
  password: z.string().min(1, "Пароль iiko RMS обязателен"),
});

type ServerSupabaseClient = NonNullable<
  Awaited<ReturnType<typeof getServerSupabase>>
>;

function isMissingTeamOnboardingTable(message: string): boolean {
  return /venue_memberships|team_tasks|team_announcements|team_learning_standards|relation .* does not exist|column .* does not exist/i.test(
    message,
  );
}

async function insertOptionalTeamRows(
  supabase: ServerSupabaseClient,
  table: string,
  rows: object | object[],
): Promise<string | null> {
  const { error } = await supabase.from(table).insert(rows);
  if (error && !isMissingTeamOnboardingTable(error.message)) {
    return error.message;
  }
  return null;
}

async function seedOnboardingTeamWorkspace(
  supabase: ServerSupabaseClient,
  input: {
    venueId: string;
    venueName: string;
    venueType: z.infer<typeof VenueInput>["type"];
    ownerUserId: string;
    ownerEmail: string | null;
  },
): Promise<string | null> {
  const seed = buildTeamOnboardingSeed({
    venueId: input.venueId,
    venueName: input.venueName,
    venueType: input.venueType,
    ownerUserId: input.ownerUserId,
    ownerEmail: input.ownerEmail,
    createdAt: new Date().toISOString(),
  });

  const ownerError = await insertOptionalTeamRows(
    supabase,
    "venue_memberships",
    seed.ownerMembership,
  );
  if (ownerError) return ownerError;

  const taskError = await insertOptionalTeamRows(
    supabase,
    "team_tasks",
    seed.tasks,
  );
  if (taskError) return taskError;

  const announcementError = await insertOptionalTeamRows(
    supabase,
    "team_announcements",
    seed.announcement,
  );
  if (announcementError) return announcementError;

  if (seed.learningStandards.length > 0) {
    const { error } = await supabase
      .from("team_learning_standards")
      .upsert(seed.learningStandards, {
        onConflict: "venue_id,role,module_id",
      });
    if (error && !isMissingTeamOnboardingTable(error.message)) {
      return error.message;
    }
  }

  return null;
}

export async function probeIikoOrganizationsAction(
  raw: unknown,
): Promise<ProbeIikoResult> {
  const parsed = ProbeInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Введите iiko API ключ." };
  }

  try {
    const probe = new CloudIikoClient({
      apiLogin: parsed.data.apiLogin,
      organizationId: "",
      today: new Date().toISOString().slice(0, 10),
    });
    const organizations = await probe.listOrganizations();
    if (organizations.length === 0) {
      return {
        ok: false,
        error: "iiko не вернул ни одной организации для этого API ключа.",
      };
    }
    return { ok: true, organizations };
  } catch (err) {
    return {
      ok: false,
      error: err instanceof Error ? err.message : "Не удалось проверить iiko.",
    };
  }
}

export async function probeRmsOrganizationsAction(
  raw: unknown,
): Promise<ProbeIikoResult> {
  const parsed = ProbeRmsInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Введите host, логин и пароль iiko RMS." };
  }

  try {
    const probe = new RmsIikoClient({
      host: parsed.data.host,
      login: parsed.data.login,
      password: parsed.data.password,
      today: new Date().toISOString().slice(0, 10),
    });
    const organizations = await probe.listOrganizations();
    return { ok: true, organizations };
  } catch (err) {
    return {
      ok: false,
      error:
        err instanceof Error ? err.message : "Не удалось проверить iiko RMS.",
    };
  }
}

/**
 * Persist the onboarding venue.
 *
 * - Real mode (Supabase configured + logged in): validate iiko Cloud,
 *   insert into `venues` + encrypted `iiko_credentials`, return the new id.
 * - Sandbox mode: nothing to persist — return the sandbox venue id so the
 *   wizard still completes in development.
 *
 * Wrapped defensively: a DB hiccup never blocks the user from reaching the
 * dashboard during a sandbox run.
 */
export async function createVenueAction(
  raw: unknown,
): Promise<OnboardingResult> {
  const parsed = VenueInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Проверьте поля заведения." };
  }

  const user = await getCurrentUser();
  const supabase = await getServerSupabase();

  // Local sandbox mode: skip persistence, proceed.
  if (!supabase) {
    return { ok: true, mode: "sandbox", venueId: "dev-venue" };
  }
  if (!user) {
    return { ok: false, error: "Нужно войти, чтобы подключить заведение." };
  }
  if (user.isDemo) {
    return {
      ok: false,
      error:
        "Тестовый кабинет показывает интерфейс, но не сохраняет подключение iiko. Войдите через обычный email и пароль, затем повторите подключение.",
    };
  }
  if (parsed.data.channel === "cloud") {
    if (!parsed.data.apiLogin) {
      return { ok: false, error: "Введите iiko API ключ." };
    }
    if (!parsed.data.organizationId) {
      return { ok: false, error: "Выберите организацию iiko." };
    }
  } else if (
    !parsed.data.rmsHost ||
    !parsed.data.rmsLogin ||
    !parsed.data.rmsPassword
  ) {
    return { ok: false, error: "Введите host, логин и пароль iiko RMS." };
  }

  try {
    let organization: IikoOrganizationOption | null = null;

    if (parsed.data.channel === "cloud") {
      const probe = await probeIikoOrganizationsAction({
        apiLogin: parsed.data.apiLogin,
      });
      if (!probe.ok) return probe;
      organization =
        probe.organizations.find(
          (org) => org.id === parsed.data.organizationId,
        ) ?? null;
      if (!organization) {
        return {
          ok: false,
          error: "Выбранная организация iiko недоступна для этого apiLogin.",
        };
      }
    } else {
      const probe = await probeRmsOrganizationsAction({
        host: parsed.data.rmsHost,
        login: parsed.data.rmsLogin,
        password: parsed.data.rmsPassword,
      });
      if (!probe.ok) return probe;
      organization = probe.organizations[0] ?? {
        id: "default",
        name: parsed.data.rmsHost,
      };
    }

    const venueInsert = {
      owner_user_id: user.id,
      name: parsed.data.name,
      type: parsed.data.type,
      city: parsed.data.city || null,
      intelligence_profile: normalizeVenueProfile(
        parsed.data.intelligenceProfile,
      ),
      context_profile: normalizeContextAnswers(parsed.data.contextAnswers),
    };

    let insertResult = await supabase
      .from("venues")
      .insert(venueInsert)
      .select("id")
      .single();

    if (
      insertResult.error &&
      /(intelligence_profile|context_profile)/i.test(insertResult.error.message)
    ) {
      const fallbackInsert = {
        owner_user_id: venueInsert.owner_user_id,
        name: venueInsert.name,
        type: venueInsert.type,
        city: venueInsert.city,
      };
      insertResult = await supabase
        .from("venues")
        .insert(fallbackInsert)
        .select("id")
        .single();
    }

    const { data, error } = insertResult;

    if (error || !data) {
      return { ok: false, error: error?.message ?? "Не удалось сохранить." };
    }

    const credentialPlaintext =
      parsed.data.channel === "rms"
        ? JSON.stringify({
            host: parsed.data.rmsHost,
            login: parsed.data.rmsLogin,
            password: parsed.data.rmsPassword,
          })
        : parsed.data.apiLogin;
    const encrypted = encryptSecret(credentialPlaintext);
    const { error: credsError } = await supabase
      .from("iiko_credentials")
      .insert({
        venue_id: data.id,
        channel: parsed.data.channel,
        creds_encrypted: encrypted.ciphertext,
        iv: encrypted.iv,
        iiko_org_id: organization?.id ?? null,
        iiko_org_name: organization?.name || null,
        last_validated_at: new Date().toISOString(),
        status: "active",
      });

    if (credsError) {
      return {
        ok: false,
        error: credsError.message,
      };
    }

    const teamSeedError = await seedOnboardingTeamWorkspace(supabase, {
      venueId: data.id as string,
      venueName: parsed.data.name,
      venueType: parsed.data.type,
      ownerUserId: user.id,
      ownerEmail: user.email || null,
    });
    if (teamSeedError) return { ok: false, error: teamSeedError };

    return { ok: true, mode: "saved", venueId: data.id as string };
  } catch (err) {
    return {
      ok: false,
      error: err instanceof Error ? err.message : "Ошибка сохранения.",
    };
  }
}
