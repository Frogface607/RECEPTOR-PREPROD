import { NextResponse } from "next/server";
import { z } from "zod";
import { getToolById } from "@/lib/tools/catalog";
import { runToolMock, validateToolInput } from "@/lib/tools/mock-runner";
import { runToolWithClaude, isAiConfigured } from "@/lib/tools/ai-runner";

export const runtime = "nodejs";

const BodySchema = z.object({
  toolId: z.string().min(1),
  values: z.record(z.string(), z.string()),
});

export async function POST(request: Request) {
  let raw: unknown;
  try {
    raw = await request.json();
  } catch {
    return NextResponse.json({ error: "expected JSON body" }, { status: 400 });
  }

  const parsed = BodySchema.safeParse(raw);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "invalid body", issues: parsed.error.issues },
      { status: 400 },
    );
  }

  const { toolId, values } = parsed.data;
  const tool = getToolById(toolId);
  if (!tool) {
    return NextResponse.json({ error: "tool not found" }, { status: 404 });
  }

  const validation = validateToolInput(tool, values);
  if (!validation.ok) {
    return NextResponse.json(
      { error: "missing required fields", missing: validation.missing },
      { status: 422 },
    );
  }

  // Real Claude when configured; deterministic mock otherwise. Same response
  // shape either way, so the UI is agnostic to which backend ran.
  try {
    const markdown = isAiConfigured()
      ? await runToolWithClaude(tool, values)
      : runToolMock(toolId, values);

    return NextResponse.json(
      { markdown, backend: isAiConfigured() ? "claude" : "mock" },
      { status: 200, headers: { "Cache-Control": "no-store" } },
    );
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "run failed" },
      { status: 500 },
    );
  }
}
