"use client";

import { useState, useTransition } from "react";
import { CheckCircle2, Loader2, Plus, Send } from "lucide-react";
import { createTeamTaskAction } from "@/app/team/actions";
import { Button } from "@/components/ui/button";
import type { SurvivalTaskDraft } from "@/lib/survival-score";
import type { TeamRoleId, TeamTask } from "@/lib/team/team-os";

type TaskState = Record<number, "idle" | "saved" | "error">;

const ROLE_LABEL: Record<TeamRoleId, string> = {
  owner: "владелец",
  operations_manager: "операционный",
  venue_manager: "управляющий",
  chef: "шеф",
  line_cook: "повар",
  service: "зал",
  marketing: "маркетинг",
};

const PRIORITY_LABEL: Record<TeamTask["priority"], string> = {
  high: "важно",
  medium: "средне",
  low: "низко",
};

export function SurvivalTaskActions({
  venueId,
  drafts,
}: {
  venueId: string;
  drafts: SurvivalTaskDraft[];
}) {
  const [states, setStates] = useState<TaskState>({});
  const [message, setMessage] = useState("");
  const [isPending, startTransition] = useTransition();

  function createTask(draft: SurvivalTaskDraft, index: number) {
    setMessage("");
    startTransition(async () => {
      const result = await createTeamTaskAction({
        venueId,
        title: draft.title,
        priority: draft.priority,
        audienceType: "role",
        audienceRole: draft.roleId,
        dueLabel: draft.dueLabel,
      });

      if (result.ok) {
        setStates((current) => ({ ...current, [index]: "saved" }));
        setMessage(result.message);
      } else {
        setStates((current) => ({ ...current, [index]: "error" }));
        setMessage(result.error);
      }
    });
  }

  if (drafts.length === 0) return null;

  return (
    <div className="space-y-2.5">
      {drafts.map((draft, index) => {
        const state = states[index] ?? "idle";
        const saved = state === "saved";
        return (
          <div
            key={`${draft.roleId}-${index}-${draft.title}`}
            className="rounded-lg bg-background/35 px-3 py-2"
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-md border border-brand/35 bg-brand/10 px-2 py-0.5 text-[10px] uppercase tracking-[0.12em] text-brand">
                    {ROLE_LABEL[draft.roleId]}
                  </span>
                  <span className="text-[11px] text-muted-foreground">
                    {PRIORITY_LABEL[draft.priority]} · {draft.dueLabel}
                  </span>
                </div>
                <p className="mt-2 text-[13px] leading-relaxed text-foreground/85">
                  {draft.title}
                </p>
              </div>

              <Button
                type="button"
                variant={saved ? "secondary" : "outline"}
                size="sm"
                disabled={isPending || saved}
                onClick={() => createTask(draft, index)}
                className="shrink-0"
              >
                {saved ? (
                  <>
                    <CheckCircle2 className="size-3.5" />
                    создано
                  </>
                ) : isPending ? (
                  <>
                    <Loader2 className="size-3.5 animate-spin" />
                    пишу
                  </>
                ) : (
                  <>
                    <Plus className="size-3.5" /> в задачи
                  </>
                )}
              </Button>
            </div>
          </div>
        );
      })}

      {message ? (
        <p className="flex items-center gap-2 text-[12px] leading-relaxed text-muted-foreground">
          <Send className="size-3.5 text-brand" />
          {message}
        </p>
      ) : null}
    </div>
  );
}
