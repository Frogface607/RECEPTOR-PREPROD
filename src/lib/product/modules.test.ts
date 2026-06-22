import { describe, expect, test } from "vitest";
import {
  getProductModule,
  getPilotCommandState,
  listModulesByPhase,
  listPilotCommandStates,
  listPilotBundleModules,
  PILOT_BUNDLE_MODULE_IDS,
  resolvePilotReadinessState,
} from "./modules";

describe("restaurant OS modules", () => {
  test("keeps the pilot bundle focused", () => {
    const modules = listPilotBundleModules();

    expect(modules.map((module) => module.id)).toEqual(PILOT_BUNDLE_MODULE_IDS);
    expect(modules[0]?.id).toBe("owner_cockpit");
    expect(modules.some((module) => module.id === "context_engine")).toBe(true);
  });

  test("lists modules by product phase", () => {
    const pilotModules = listModulesByPhase("pilot");
    const saasModules = listModulesByPhase("saas");

    expect(pilotModules.map((module) => module.id)).toContain("owner_cockpit");
    expect(saasModules.map((module) => module.id)).toContain("team_os");
  });

  test("throws for unknown module ids", () => {
    expect(() => getProductModule("bad" as never)).toThrow("Unknown product module");
  });

  test("models the pilot command states in launch order", () => {
    const states = listPilotCommandStates();

    expect(states.map((state) => state.id)).toEqual([
      "mock",
      "waiting_key",
      "connected",
      "error",
    ]);
    expect(getPilotCommandState("waiting_key").primaryAction).toBe(
      "Request apiLogin",
    );
  });

  test("resolves the current Mikhno pilot state while the key is missing", () => {
    expect(
      resolvePilotReadinessState({
        liveTargetSelected: true,
        targetHasIikoKey: false,
      }),
    ).toBe("waiting_key");

    expect(resolvePilotReadinessState({ iikoConnected: true })).toBe(
      "connected",
    );
    expect(resolvePilotReadinessState({ hasConnectionError: true })).toBe(
      "error",
    );
  });
});
