import { NextResponse } from "next/server";
import { z } from "zod";
import { getToolById } from "@/lib/tools/catalog";
import { validateToolInput } from "@/lib/tools/mock-runner";
import { executeTool } from "@/lib/tools/execute";

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

  // OpenAI/Claude when configured; otherwise (or on any model failure) the
  // deterministic mock. executeTool guarantees a usable result so the demo
  // never shows a red API error.
  try {
    const result = await executeTool(tool, values);
    return NextResponse.json(result, {
      status: 200,
      headers: { "Cache-Control": "no-store" },
    });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "run failed" },
      { status: 500 },
    );
  }
}
