import { describe, expect, test } from "vitest";
import {
  normalizeTaskImpactLabel,
  normalizeTaskSourceLabel,
} from "./team-task-labels";

describe("team task labels", () => {
  test("normalizes source and impact labels consistently", () => {
    expect(normalizeTaskSourceLabel("  ФОТ   и   маржа  ")).toBe("ФОТ и маржа");
    expect(normalizeTaskImpactLabel("  120 000   ₽  ")).toBe("120 000 ₽");
    expect(normalizeTaskImpactLabel("")).toBeNull();
    expect(normalizeTaskImpactLabel(null)).toBeNull();
  });

  test("keeps long labels compact for task badges", () => {
    const label = normalizeTaskImpactLabel("x".repeat(120));

    expect(label).toHaveLength(80);
    expect(label?.endsWith("...")).toBe(true);
  });
});
