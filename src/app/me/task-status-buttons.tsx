"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, Loader2, Play } from "lucide-react";
import {
  updateOwnTaskStatusAction,
  type OwnTaskStatusResult,
} from "./actions";
import type { TeamTask } from "@/lib/team/team-os";

const TASK_STATUS_EVENT = "receptor:task-status-updated";

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
  const [currentStatus, setCurrentStatus] =
    useState<TeamTask["status"]>(task.status);
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const onTaskStatus = (event: Event) => {
      const detail = (event as CustomEvent<{
        taskId?: string;
        status?: TeamTask["status"];
      }>).detail;

      if (detail?.taskId === task.id && detail.status) {
        setCurrentStatus(detail.status);
      }
    };

    window.addEventListener(TASK_STATUS_EVENT, onTaskStatus);
    return () => window.removeEventListener(TASK_STATUS_EVENT, onTaskStatus);
  }, [task.id]);

  const nextAction = NEXT_ACTIONS[currentStatus];

  if (!nextAction) return null;

  return (
    <div className="mt-4">
      <button
        type="button"
        disabled={pending}
        onClick={async () => {
          setMessage(null);
          setPending(true);
          try {
            const result = await updateOwnTaskStatusAction({
              taskId: task.id,
              status: nextAction.status,
            });
            setMessage(resultText(result));
            if (result.ok) {
              setCurrentStatus(nextAction.status);
              window.dispatchEvent(
                new CustomEvent(TASK_STATUS_EVENT, {
                  detail: { taskId: task.id, status: nextAction.status },
                }),
              );
              router.refresh();
            }
          } finally {
            setPending(false);
          }
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
