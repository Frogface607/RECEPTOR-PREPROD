import { getCurrentUser } from "@/lib/auth/session";
import { getServerSupabase } from "@/lib/db/server";
import type {
  MenuItemMapping,
  MenuItemMappingStatus,
  MenuItemMappingType,
} from "@/lib/menu-item-mapping";

type DbMenuItemMapping = {
  id: string;
  venue_id: string;
  dish_key: string;
  dish_name: string;
  dish_group: string | null;
  iiko_product_id: string | null;
  iiko_product_name: string | null;
  iiko_article: string | null;
  tech_card_id: string | null;
  mapping_type: string;
  status: string;
  confidence: number | null;
  note: string | null;
};

const MAPPING_TYPES = new Set<MenuItemMappingType>([
  "manual",
  "auto",
  "imported",
]);
const MAPPING_STATUSES = new Set<MenuItemMappingStatus>([
  "active",
  "ignored",
  "needs_review",
]);

export async function listMenuItemMappings(
  venueId: string,
): Promise<MenuItemMapping[]> {
  const user = await getCurrentUser();
  if (!user || user.isDemo) return [];

  const supabase = await getServerSupabase();
  if (!supabase) return [];

  const { data, error } = await supabase
    .from("menu_item_mappings")
    .select(
      "id,venue_id,dish_key,dish_name,dish_group,iiko_product_id,iiko_product_name,iiko_article,tech_card_id,mapping_type,status,confidence,note",
    )
    .eq("venue_id", venueId)
    .order("dish_name", { ascending: true })
    .returns<DbMenuItemMapping[]>();

  if (error) {
    if (/menu_item_mappings|relation .* does not exist/i.test(error.message)) {
      return [];
    }
    console.error("[menu-item-mapping] Failed to load mappings", {
      venueId,
      error: error.message,
    });
    return [];
  }

  return (data ?? []).map(toMenuItemMapping);
}

function toMenuItemMapping(row: DbMenuItemMapping): MenuItemMapping {
  const mappingType = MAPPING_TYPES.has(row.mapping_type as MenuItemMappingType)
    ? (row.mapping_type as MenuItemMappingType)
    : "manual";
  const status = MAPPING_STATUSES.has(row.status as MenuItemMappingStatus)
    ? (row.status as MenuItemMappingStatus)
    : "needs_review";

  return {
    id: row.id,
    venueId: row.venue_id,
    dishKey: row.dish_key,
    dishName: row.dish_name,
    dishGroup: row.dish_group ?? "",
    iikoProductId: row.iiko_product_id ?? undefined,
    iikoProductName: row.iiko_product_name ?? undefined,
    iikoArticle: row.iiko_article ?? undefined,
    techCardId: row.tech_card_id ?? undefined,
    mappingType,
    status,
    confidence: row.confidence ?? 1,
    note: row.note ?? "",
  };
}
