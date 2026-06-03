import { describe, expect, test } from "vitest";
import {
  CATEGORIES,
  TOOLS,
  getToolsByCategory,
  getFreeTools,
  getToolById,
  type ToolCategoryId,
} from "./catalog";

describe("CATEGORIES", () => {
  test("has the 6 v1 categories in stable order", () => {
    expect(CATEGORIES.map((c) => c.id)).toEqual([
      "chef",
      "waiter",
      "marketing",
      "management",
      "hr",
      "legal",
    ]);
  });

  test("every category has a name and icon", () => {
    for (const c of CATEGORIES) {
      expect(c.name.length).toBeGreaterThan(0);
      expect(c.icon.length).toBeGreaterThan(0);
    }
  });
});

describe("TOOLS catalog integrity", () => {
  test("contains exactly 27 tools", () => {
    expect(TOOLS).toHaveLength(27);
  });

  test("all tool ids are unique", () => {
    const ids = TOOLS.map((t) => t.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  test("every tool references an existing category", () => {
    const validCats = new Set(CATEGORIES.map((c) => c.id));
    for (const t of TOOLS) {
      expect(validCats.has(t.category)).toBe(true);
    }
  });

  test("every tool has name, description, icon", () => {
    for (const t of TOOLS) {
      expect(t.name.length).toBeGreaterThan(0);
      expect(t.description.length).toBeGreaterThan(0);
      expect(t.icon.length).toBeGreaterThan(0);
    }
  });

  test("every tool has at least one field", () => {
    for (const t of TOOLS) {
      expect(t.fields.length).toBeGreaterThanOrEqual(1);
    }
  });

  test("every field has a unique id within its tool", () => {
    for (const t of TOOLS) {
      const ids = t.fields.map((f) => f.id);
      expect(new Set(ids).size).toBe(ids.length);
    }
  });

  test("at least one field per tool is required", () => {
    for (const t of TOOLS) {
      expect(t.fields.some((f) => f.required)).toBe(true);
    }
  });

  test("buildPrompt produces a non-empty string from field values", () => {
    for (const t of TOOLS) {
      const values: Record<string, string> = {};
      for (const f of t.fields) values[f.id] = "тест";
      const prompt = t.buildPrompt(values);
      expect(typeof prompt).toBe("string");
      expect(prompt.length).toBeGreaterThan(10);
    }
  });

  test("buildPrompt reflects provided input (first required field appears)", () => {
    for (const t of TOOLS) {
      const firstRequired = t.fields.find((f) => f.required)!;
      const values: Record<string, string> = {};
      for (const f of t.fields) values[f.id] = "";
      values[firstRequired.id] = "УникальныйМаркер42";
      const prompt = t.buildPrompt(values);
      expect(prompt).toContain("УникальныйМаркер42");
    }
  });
});

describe("helpers", () => {
  test("getToolsByCategory returns only that category's tools", () => {
    for (const c of CATEGORIES) {
      const tools = getToolsByCategory(c.id as ToolCategoryId);
      expect(tools.every((t) => t.category === c.id)).toBe(true);
    }
  });

  test("getToolsByCategory partitions the whole catalog", () => {
    const total = CATEGORIES.reduce(
      (sum, c) => sum + getToolsByCategory(c.id as ToolCategoryId).length,
      0,
    );
    expect(total).toBe(TOOLS.length);
  });

  test("chef is the richest category", () => {
    const chef = getToolsByCategory("chef");
    expect(chef.length).toBeGreaterThanOrEqual(5);
  });

  test("getFreeTools returns only free tools and there is a healthy mix", () => {
    const free = getFreeTools();
    expect(free.every((t) => t.free)).toBe(true);
    expect(free.length).toBeGreaterThan(0);
    expect(free.length).toBeLessThan(TOOLS.length);
  });

  test("getToolById finds a known tool", () => {
    const t = getToolById("recipe-generator");
    expect(t?.name).toBe("Генератор рецептов");
  });

  test("getToolById returns undefined for unknown id", () => {
    expect(getToolById("does-not-exist")).toBeUndefined();
  });
});
