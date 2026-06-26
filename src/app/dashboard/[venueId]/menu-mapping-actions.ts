"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { getCurrentUser } from "@/lib/auth/session";
import { getServerSupabase } from "@/lib/db/server";
import { createDishKey } from "@/lib/menu-item-mapping";

const ProductOptionSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  article: z.string().optional(),
});

const SaveMenuItemMappingInput = z.object({
  venueId: z.string().min(1),
  dishName: z.string().trim().min(1).max(240),
  dishGroup: z.string().trim().max(160).optional(),
  product: ProductOptionSchema,
});

const AutoMappingSchema = z.object({
  dishName: z.string().trim().min(1).max(240),
  dishGroup: z.string().trim().max(160).optional(),
  product: ProductOptionSchema,
});

const SaveAutoMenuItemMappingsInput = z.object({
  venueId: z.string().min(1),
  mappings: z.array(AutoMappingSchema).max(50),
});

export type MenuMappingActionState = {
  ok: boolean;
  message: string;
  mode?: "saved" | "sandbox";
};

export async function saveMenuItemMappingAction(
  formData: FormData,
): Promise<void> {
  await saveMenuItemMappingStateAction({ ok: false, message: "" }, formData);
}

export async function saveMenuItemMappingStateAction(
  _prevState: MenuMappingActionState,
  formData: FormData,
): Promise<MenuMappingActionState> {
  const productRaw = String(formData.get("product") ?? "");
  const parsedProduct = safeParseProductOption(productRaw);
  const parsed = SaveMenuItemMappingInput.safeParse({
    venueId: String(formData.get("venueId") ?? ""),
    dishName: String(formData.get("dishName") ?? ""),
    dishGroup: String(formData.get("dishGroup") ?? ""),
    product: parsedProduct,
  });

  if (!parsed.success) {
    return { ok: false, message: "Выберите блюдо и товар iiko." };
  }

  const user = await getCurrentUser();
  if (!user) return { ok: false, message: "Нужно войти." };

  const { venueId, dishName, dishGroup, product } = parsed.data;
  const supabase = await getServerSupabase();
  if (!supabase || user.isDemo) {
    revalidatePath(`/dashboard/${venueId}`);
    return {
      ok: true,
      mode: "sandbox",
      message: "Demo: связь показана, но сохраняется только в обычном входе.",
    };
  }

  const { error } = await supabase.from("menu_item_mappings").upsert(
    {
      venue_id: venueId,
      dish_key: createDishKey(dishName),
      dish_name: dishName,
      dish_group: dishGroup ?? "",
      iiko_product_id: product.id,
      iiko_product_name: product.name,
      iiko_article: product.article ?? null,
      mapping_type: "manual",
      status: "active",
      confidence: 1,
      created_by: user.id,
      updated_at: new Date().toISOString(),
    },
    { onConflict: "venue_id,dish_key" },
  );

  if (error) {
    if (/menu_item_mappings|relation .* does not exist/i.test(error.message)) {
      return { ok: false, message: "Таблица маппинга еще не применена." };
    }
    console.error("[menu-mapping] Failed to save mapping", {
      venueId,
      dishName,
      error: error.message,
    });
    return { ok: false, message: "Не удалось сохранить связь." };
  }

  revalidatePath(`/dashboard/${venueId}`);
  return { ok: true, mode: "saved", message: "Связь сохранена." };
}

export async function saveAutoMenuItemMappingsStateAction(
  _prevState: MenuMappingActionState,
  formData: FormData,
): Promise<MenuMappingActionState> {
  const parsed = SaveAutoMenuItemMappingsInput.safeParse({
    venueId: String(formData.get("venueId") ?? ""),
    mappings: safeParseJson(String(formData.get("mappings") ?? "")),
  });

  if (!parsed.success || parsed.data.mappings.length === 0) {
    return { ok: false, message: "Нет авто-связей для сохранения." };
  }

  const user = await getCurrentUser();
  if (!user) return { ok: false, message: "Нужно войти." };

  const { venueId, mappings } = parsed.data;
  const supabase = await getServerSupabase();
  if (!supabase || user.isDemo) {
    revalidatePath(`/dashboard/${venueId}`);
    return {
      ok: true,
      mode: "sandbox",
      message: `Demo: найдено авто-связей ${mappings.length}, сохранение доступно в обычном входе.`,
    };
  }

  const { error } = await supabase.from("menu_item_mappings").upsert(
    mappings.map((mapping) => ({
      venue_id: venueId,
      dish_key: createDishKey(mapping.dishName),
      dish_name: mapping.dishName,
      dish_group: mapping.dishGroup ?? "",
      iiko_product_id: mapping.product.id,
      iiko_product_name: mapping.product.name,
      iiko_article: mapping.product.article ?? null,
      mapping_type: "auto",
      status: "active",
      confidence: 0.9,
      created_by: user.id,
      updated_at: new Date().toISOString(),
    })),
    { onConflict: "venue_id,dish_key" },
  );

  if (error) {
    if (/menu_item_mappings|relation .* does not exist/i.test(error.message)) {
      return { ok: false, message: "Таблица маппинга еще не применена." };
    }
    console.error("[menu-mapping] Failed to save auto mappings", {
      venueId,
      count: mappings.length,
      error: error.message,
    });
    return { ok: false, message: "Не удалось сохранить авто-связи." };
  }

  revalidatePath(`/dashboard/${venueId}`);
  return { ok: true, mode: "saved", message: `Авто-связи сохранены: ${mappings.length}.` };
}

function safeParseProductOption(value: string): unknown {
  try {
    return JSON.parse(value) as unknown;
  } catch {
    return null;
  }
}

function safeParseJson(value: string): unknown {
  try {
    return JSON.parse(value) as unknown;
  } catch {
    return null;
  }
}
