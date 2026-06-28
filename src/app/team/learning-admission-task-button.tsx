"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { TeamLearningAdmissionTaskDraft } from "@/lib/team/team-learning-role-plan";
import { createTeamTaskAction } from "./actions";

export function LearningAdmissionTaskButton({
  venueId,
  draft,
}: {
  venueId: string;
  draft: TeamLearningAdmissionTaskDraft;
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [message, setMessage] = useState<string | null>(null);
  const [tone, setTone] = useState<"success" | "error">("success");

  return (
    <div className="flex flex-col items-start gap-1.5 sm:items-end">
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
              dedupeOpenTask: true,
            });

            setTone(result.ok ? "success" : "error");
            setMessage(result.ok ? result.message : result.error);
            if (result.ok) router.refresh();
          });
        }}
      >
        <Plus className="size-3.5" />
        {pending ? "Создаем" : "Создать задачу"}
      </Button>
      {message ? (
        <p
          className={
            "max-w-[220px] text-right text-[11px] leading-snug " +
            (tone === "success" ? "text-brand" : "text-destructive")
          }
        >
          {message}
        </p>
      ) : null}
    </div>
  );
}
