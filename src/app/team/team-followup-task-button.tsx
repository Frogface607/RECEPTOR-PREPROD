"use client";

import { useState, useTransition } from "react";
import { CheckCircle2, Loader2, Plus } from "lucide-react";
import { useRouter } from "next/navigation";
import { createTeamTaskAction } from "./actions";
import { Button } from "@/components/ui/button";
import type { SurvivalTaskDraft } from "@/lib/survival-score";
import { buildFocusedTeamTaskHref } from "@/lib/team/team-links";

export function TeamFollowUpTaskButton({
  venueId,
  draft,
}: {
  venueId: string;
  draft: SurvivalTaskDraft;
}) {
  const router = useRouter();
  const [state, setState] = useState<"idle" | "saved" | "error">("idle");
  const [isPending, startTransition] = useTransition();

  function createTask() {
    setState("idle");
    startTransition(async () => {
      const audienceType = draft.audienceMemberId ? "member" : "role";
      const result = await createTeamTaskAction({
        venueId,
        title: draft.title,
        source: "copilot",
        priority: draft.priority,
        audienceType,
        audienceRole: audienceType === "role" ? draft.roleId : undefined,
        audienceMemberId: draft.audienceMemberId,
        dueLabel: draft.dueLabel,
        impactLabel: draft.impactLabel,
        contextNote: draft.contextNote,
        sourceLabel: draft.sourceLabel,
        learningModuleId: draft.learningModuleId,
        learningModuleTitle: draft.learningModuleTitle,
        learningChecklistTitle: draft.learningChecklistTitle,
        dedupeOpenTask: true,
      });

      if (result.ok) {
        setState("saved");
        if (result.taskId) {
          router.push(
            buildFocusedTeamTaskHref({
              venueId,
              taskId: result.taskId,
              pathname: window.location.pathname,
              currentSearch: window.location.search,
            }),
          );
        }
      } else {
        setState("error");
      }
    });
  }

  const saved = state === "saved";

  return (
    <Button
      type="button"
      variant={
        saved ? "secondary" : state === "error" ? "destructive" : "outline"
      }
      size="sm"
      disabled={isPending || saved}
      onClick={createTask}
      className="h-8 shrink-0 px-2.5 text-[12px]"
    >
      {saved ? (
        <>
          <CheckCircle2 className="size-3.5" />
          поручено
        </>
      ) : isPending ? (
        <>
          <Loader2 className="size-3.5 animate-spin" />
          поручаю
        </>
      ) : (
        <>
          <Plus className="size-3.5" /> Поручить
        </>
      )}
    </Button>
  );
}
