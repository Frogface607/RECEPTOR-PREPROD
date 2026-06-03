import { describe, expect, test, beforeEach, afterEach } from "vitest";
import { isAiConfigured } from "./ai-runner";

const ORIGINAL = process.env.ANTHROPIC_API_KEY;

afterEach(() => {
  if (ORIGINAL === undefined) delete process.env.ANTHROPIC_API_KEY;
  else process.env.ANTHROPIC_API_KEY = ORIGINAL;
});

describe("isAiConfigured", () => {
  beforeEach(() => {
    delete process.env.ANTHROPIC_API_KEY;
  });

  test("false when ANTHROPIC_API_KEY is unset", () => {
    expect(isAiConfigured()).toBe(false);
  });

  test("false when key is empty or whitespace", () => {
    process.env.ANTHROPIC_API_KEY = "   ";
    expect(isAiConfigured()).toBe(false);
  });

  test("false for an obvious placeholder value", () => {
    process.env.ANTHROPIC_API_KEY = "your-key-here";
    expect(isAiConfigured()).toBe(false);
  });

  test("true for a real-looking sk-ant key", () => {
    process.env.ANTHROPIC_API_KEY = "sk-ant-api03-abc123";
    expect(isAiConfigured()).toBe(true);
  });
});
