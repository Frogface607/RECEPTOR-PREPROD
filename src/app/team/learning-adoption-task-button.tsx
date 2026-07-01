"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { CheckCircle2, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { TeamLearningAdoptionTaskDraft } from "@/lib/team/team-learning-adoption";
import { createTeamTaskAction } from "./actions";

export function LearningAdoptionTaskButton({
  venueId,
  draft,
  existingTask,
}: {
  venueId: string;
  draft: TeamLearningAdoptionTaskDraft;
  existingTask: boolean;
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [message, setMessage] = useState<string | null>(null);
  const [tone, setTone] = useState<"success" | "error">("success");

  if (existingTask) {
    return (
      <p className="inline-flex items-center gap-1.5 text-[11px] font-medium text-brand">
        <CheckCircle2 className="size-3.5" />
        Задача уже есть
      </p>
    );
  }

  return (
    <div className="flex flex-col items-start gap-1.5">
      <Button
        type="button"
        variant="outline"
        size="sm"
        disabled={pending}
        onClick={() => {
          setMessage(null);
          startTransition(async () => {
            const result = await createTeamTaskAction({
              venueId,
              title: draft.title,
              source: "manager",
              priority: draft.priority,
              audienceType: draft.audienceType,
              audienceMemberId: draft.audienceMemberId,
              dueLabel: draft.dueLabel,
              contextNote: draft.contextNote,
              sourceLabel: "Обучение",
              impactLabel: "внедрение стандарта",
              learningModuleId: draft.moduleId ?? undefined,
              learningModuleTitle: draft.moduleTitle,
              learningChecklistTitle: draft.checklistTitle,
              dedupeOpenTask: true,
            });

            setTone(result.ok ? "success" : "error");
            setMessage(result.ok ? result.message : result.error);
            if (result.ok) router.refresh();
          });
        }}
      >
        <Plus className="size-3.5" />
        {pending ? "Создаем" : "Назначить факт"}
      </Button>
      {message ? (
        <p
          className={
            "max-w-[240px] text-[11px] leading-snug " +
            (tone === "success" ? "text-brand" : "text-destructive")
          }
        >
          {message}
        </p>
      ) : null}
    </div>
  );
}
