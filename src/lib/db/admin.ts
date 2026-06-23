import { createClient } from "@supabase/supabase-js";
import {
  isSupabaseAdminConfigured,
  supabaseServiceRoleKey,
  supabaseUrl,
} from "./env";

export function getSupabaseAdmin() {
  if (!isSupabaseAdminConfigured()) return null;

  return createClient(supabaseUrl(), supabaseServiceRoleKey(), {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  });
}
