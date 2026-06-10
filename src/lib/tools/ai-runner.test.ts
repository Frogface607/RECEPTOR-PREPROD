import { describe, expect, test, beforeEach, afterEach } from "vitest";
import { getConfiguredAiBackend, isAiConfigured } from "./ai-runner";

const ORIGINAL_ANTHROPIC = process.env.ANTHROPIC_API_KEY;
const ORIGINAL_OPENAI = process.env.OPENAI_API_KEY;

afterEach(() => {
  if (ORIGINAL_ANTHROPIC === undefined) delete process.env.ANTHROPIC_API_KEY;
  else process.env.ANTHROPIC_API_KEY = ORIGINAL_ANTHROPIC;

  if (ORIGINAL_OPENAI === undefined) delete process.env.OPENAI_API_KEY;
  else process.env.OPENAI_API_KEY = ORIGINAL_OPENAI;
});

describe("isAiConfigured", () => {
  beforeEach(() => {
    delete process.env.ANTHROPIC_API_KEY;
    delete process.env.OPENAI_API_KEY;
  });

  test("false when AI keys are unset", () => {
    expect(isAiConfigured()).toBe(false);
    expect(getConfiguredAiBackend()).toBeNull();
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
    expect(getConfiguredAiBackend()).toBe("claude");
  });

  test("true for a real-looking OpenAI key", () => {
    process.env.OPENAI_API_KEY = "sk-proj-abc123";
    expect(isAiConfigured()).toBe(true);
    expect(getConfiguredAiBackend()).toBe("openai");
  });

  test("prefers OpenAI when both providers are configured", () => {
    process.env.OPENAI_API_KEY = "sk-proj-abc123";
    process.env.ANTHROPIC_API_KEY = "sk-ant-api03-abc123";
    expect(getConfiguredAiBackend()).toBe("openai");
  });
});
