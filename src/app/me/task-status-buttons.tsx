"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, Loader2, Play } from "lucide-react";
import {
  updateOwnTaskStatusAction,
  type OwnTaskStatusResult,
} from "./actions";
import type { TeamTask } from "@/lib/team/team-os";

const NEXT_ACTIONS: Partial<
  Record<TeamTask["status"], { status: "accepted" | "in_progress" | "done"; label: string }>
> = {
  new: { status: "accepted", label: "Принять" },
  accepted: { status: "in_progress", label: "В работу" },
  in_progress: { status: "done", label: "Готово" },
};

function resultText(result: OwnTaskStatusResult): string {
  return result.ok ? result.message : result.error;
}

export function TaskStatusButtons({ task }: { task: TeamTask }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [message, setMessage] = useState<string | null>(null);
  const nextAction = NEXT_ACTIONS[task.status];

  if (!nextAction) return null;

  return (
    <div className="mt-4">
      <button
        type="button"
        disabled={pending}
        onClick={() => {
          setMessage(null);
          startTransition(async () => {
            const result = await updateOwnTaskStatusAction({
              taskId: task.id,
              status: nextAction.status,
            });
            setMessage(resultText(result));
            if (result.ok) router.refresh();
          });
        }}
        className="inline-flex h-9 items-center gap-2 rounded-lg border border-border/60 bg-background/60 px-3 text-xs font-medium text-foreground transition-colors hover:border-brand/40 disabled:opacity-50"
      >
        {pending ? (
          <Loader2 className="size-3.5 animate-spin" />
        ) : nextAction.status === "done" ? (
          <CheckCircle2 className="size-3.5 text-brand" />
        ) : (
          <Play className="size-3.5 text-brand" />
        )}
        {nextAction.label}
      </button>
      {message ? (
        <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">
          {message}
        </p>
      ) : null}
    </div>
  );
}
