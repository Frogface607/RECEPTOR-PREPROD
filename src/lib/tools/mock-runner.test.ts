import { describe, expect, test } from "vitest";
import { runToolMock, validateToolInput } from "./mock-runner";
import { TOOLS, getToolById } from "./catalog";

describe("validateToolInput", () => {
  test("passes when all required fields are filled", () => {
    const tool = getToolById("recipe-generator")!;
    const res = validateToolInput(tool, { dish: "Том Ям", style: "" });
    expect(res.ok).toBe(true);
  });

  test("fails listing missing required fields", () => {
    const tool = getToolById("recipe-generator")!;
    const res = validateToolInput(tool, { dish: "  ", style: "x" });
    expect(res.ok).toBe(false);
    if (!res.ok) {
      expect(res.missing).toContain("dish");
    }
  });

  test("optional fields may be empty", () => {
    const tool = getToolById("dish-idea")!;
    const res = validateToolInput(tool, { context: "Итальянская", constraints: "" });
    expect(res.ok).toBe(true);
  });
});

describe("runToolMock — contract for every tool", () => {
  test("returns non-empty markdown for all 27 tools", () => {
    for (const tool of TOOLS) {
      const values: Record<string, string> = {};
      for (const f of tool.fields) values[f.id] = f.required ? "Образец ввода" : "";
      const md = runToolMock(tool.id, values);
      expect(md.length).toBeGreaterThan(50);
    }
  });

  test("output contains the tool name as an h1 heading", () => {
    for (const tool of TOOLS) {
      const values: Record<string, string> = {};
      for (const f of tool.fields) values[f.id] = f.required ? "x" : "";
      const md = runToolMock(tool.id, values);
      expect(md).toContain(`# ${tool.name}`);
    }
  });

  test("output echoes a provided required input value", () => {
    for (const tool of TOOLS) {
      const firstRequired = tool.fields.find((f) => f.required)!;
      const values: Record<string, string> = {};
      for (const f of tool.fields) values[f.id] = "";
      values[firstRequired.id] = "Маркер сорок два";
      const md = runToolMock(tool.id, values);
      expect(md).toContain("Маркер сорок два");
    }
  });

  test("is deterministic — same input yields identical output", () => {
    const a = runToolMock("food-cost", { ingredients: "Лосось 200г", target_margin: "300" });
    const b = runToolMock("food-cost", { ingredients: "Лосось 200г", target_margin: "300" });
    expect(a).toBe(b);
  });

  test("labels the output as a demo preview while on mock", () => {
    const md = runToolMock("review-response", { review: "Долго ждали" });
    expect(md.toLowerCase()).toMatch(/демо|preview|пример/);
  });

  test("throws on unknown tool id", () => {
    expect(() => runToolMock("nope", {})).toThrow(/unknown tool|не найден/i);
  });

  test("throws when a required field is missing", () => {
    expect(() => runToolMock("recipe-generator", { dish: "", style: "" })).toThrow(
      /required|обязател/i,
    );
  });
});
