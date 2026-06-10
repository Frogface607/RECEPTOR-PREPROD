import { describe, expect, test } from "vitest";
import { TOOLS } from "./catalog";
import {
  TOOL_STRATEGY,
  TOOL_WORKFLOWS,
  getToolStrategy,
  getWorkflowTools,
} from "./strategy";

describe("tool strategy", () => {
  test("has strategy metadata for every catalog tool", () => {
    const ids = new Set(TOOLS.map((tool) => tool.id));
    expect(Object.keys(TOOL_STRATEGY).sort()).toEqual([...ids].sort());
  });

  test("each workflow points only to existing tools", () => {
    const ids = new Set(TOOLS.map((tool) => tool.id));
    for (const workflow of TOOL_WORKFLOWS) {
      expect(workflow.toolIds.length).toBeGreaterThan(0);
      for (const toolId of workflow.toolIds) {
        expect(ids.has(toolId)).toBe(true);
      }
    }
  });

  test("workflow resolver preserves configured order", () => {
    const workflow = TOOL_WORKFLOWS[0];
    const tools = getWorkflowTools(workflow);
    expect(tools.map((tool) => tool.id)).toEqual(workflow.toolIds);
  });

  test("core tools include money and tech-card scenarios", () => {
    expect(getToolStrategy("food-cost").role).toBe("core");
    expect(getToolStrategy("menu-audit").role).toBe("core");
    expect(getToolStrategy("haccp-generator").role).toBe("core");
  });

  test("risky advisory tools are marked with caution", () => {
    expect(getToolStrategy("sanpin-check").role).toBe("caution");
    expect(getToolStrategy("ad-legal-check").role).toBe("caution");
  });
});
