"use server";

import { z } from "zod";
import { getServerSupabase } from "@/lib/db/server";
import { getCurrentUser } from "@/lib/auth/session";
import { encryptSecret } from "@/lib/db/encryption";
import { CloudIikoClient } from "@/lib/iiko/cloud-client";

const VenueInput = z.object({
  name: z.string().min(1).max(120),
  type: z.enum(["restaurant", "cafe", "coffee", "bar", "chain", "other"]),
  city: z.string().max(120).optional().default(""),
  apiLogin: z.string().trim().optional().default(""),
  organizationId: z.string().optional().default(""),
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
  apiLogin: z.string().trim().min(1, "iiko apiLogin обязателен"),
});

export async function probeIikoOrganizationsAction(
  raw: unknown,
): Promise<ProbeIikoResult> {
  const parsed = ProbeInput.safeParse(raw);
  if (!parsed.success) {
    return { ok: false, error: "Введите iiko apiLogin." };
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
        error: "iiko не вернул ни одной организации для этого apiLogin.",
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

  // Sandbox mode: skip persistence, proceed.
  if (!supabase || user?.isDemo) {
    return { ok: true, mode: "sandbox", venueId: "dev-venue" };
  }
  if (!user) {
    return { ok: false, error: "Нужно войти, чтобы подключить заведение." };
  }
  if (!parsed.data.apiLogin) {
    return { ok: false, error: "Введите iiko apiLogin." };
  }
  if (!parsed.data.organizationId) {
    return { ok: false, error: "Выберите организацию iiko." };
  }

  try {
    const probe = await probeIikoOrganizationsAction({
      apiLogin: parsed.data.apiLogin,
    });
    if (!probe.ok) return probe;
    const organization = probe.organizations.find(
      (org) => org.id === parsed.data.organizationId,
    );
    if (!organization) {
      return { ok: false, error: "Выбранная организация iiko недоступна для этого apiLogin." };
    }

    const { data, error } = await supabase
      .from("venues")
      .insert({
        owner_user_id: user.id,
        name: parsed.data.name,
        type: parsed.data.type,
        city: parsed.data.city || null,
      })
      .select("id")
      .single();

    if (error || !data) {
      return { ok: false, error: error?.message ?? "Не удалось сохранить." };
    }

    const encrypted = encryptSecret(parsed.data.apiLogin);
    const { error: credsError } = await supabase
      .from("iiko_credentials")
      .insert({
        venue_id: data.id,
        channel: "cloud",
        creds_encrypted: encrypted.ciphertext,
        iv: encrypted.iv,
        iiko_org_id: organization.id,
        iiko_org_name: organization.name || null,
        last_validated_at: new Date().toISOString(),
        status: "active",
      });

    if (credsError) {
      return {
        ok: false,
        error: credsError.message,
      };
    }

    return { ok: true, mode: "saved", venueId: data.id as string };
  } catch (err) {
    return {
      ok: false,
      error: err instanceof Error ? err.message : "Ошибка сохранения.",
    };
  }
}
