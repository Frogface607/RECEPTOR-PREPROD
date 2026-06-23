import { describe, expect, test } from "vitest";
import {
  FOUNDATION_MODULE_IDS,
  getProductModule,
  listFoundationModules,
  listProductModules,
} from "./modules";

describe("restaurant OS modules", () => {
  test("keeps the foundation bundle focused", () => {
    const modules = listFoundationModules();

    expect(modules.map((module) => module.id)).toEqual(FOUNDATION_MODULE_IDS);
    expect(modules[0]?.id).toBe("owner_cockpit");
    expect(modules.some((module) => module.id === "context_engine")).toBe(true);
  });

  test("lists product modules in display order", () => {
    const modules = listProductModules();

    expect(modules.map((module) => module.id)).toEqual([
      "owner_cockpit",
      "context_engine",
      "menu_os",
      "team_os",
      "integration_pack",
      "guest_os",
      "delivery_os",
      "marketing_os",
    ]);
  });

  test("throws for unknown module ids", () => {
    expect(() => getProductModule("bad" as never)).toThrow("Unknown product module");
  });
});
