import { describe, expect, test } from "vitest";
import {
  FOUNDATION_MODULE_IDS,
  getIntegrationReadinessState,
  getProductModule,
  listFoundationModules,
  listIntegrationReadinessStates,
  listModulesByPhase,
  resolveIntegrationReadinessState,
} from "./modules";

describe("restaurant OS modules", () => {
  test("keeps the foundation bundle focused", () => {
    const modules = listFoundationModules();

    expect(modules.map((module) => module.id)).toEqual(FOUNDATION_MODULE_IDS);
    expect(modules[0]?.id).toBe("owner_cockpit");
    expect(modules.some((module) => module.id === "context_engine")).toBe(true);
  });

  test("lists modules by product phase", () => {
    const coreModules = listModulesByPhase("core");
    const operationsModules = listModulesByPhase("operations");

    expect(coreModules.map((module) => module.id)).toContain("owner_cockpit");
    expect(operationsModules.map((module) => module.id)).toContain("team_os");
  });

  test("throws for unknown module ids", () => {
    expect(() => getProductModule("bad" as never)).toThrow("Unknown product module");
  });

  test("models integration readiness states in setup order", () => {
    const states = listIntegrationReadinessStates();

    expect(states.map((state) => state.id)).toEqual([
      "demo",
      "waiting_credentials",
      "connected",
      "error",
    ]);
    expect(getIntegrationReadinessState("waiting_credentials").primaryAction).toBe(
      "Add iiko credentials",
    );
  });

  test("resolves readiness while live credentials are missing", () => {
    expect(
      resolveIntegrationReadinessState({
        liveVenueSelected: true,
        hasIikoCredentials: false,
      }),
    ).toBe("waiting_credentials");

    expect(resolveIntegrationReadinessState({ iikoConnected: true })).toBe(
      "connected",
    );
    expect(resolveIntegrationReadinessState({ hasConnectionError: true })).toBe(
      "error",
    );
  });
});
