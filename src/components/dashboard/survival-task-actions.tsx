"use client";

import { useState, useTransition } from "react";
import {
  CheckCircle2,
  Loader2,
  Plus,
  Send,
  Tags,
  UserRound,
  UsersRound,
} from "lucide-react";
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

function audienceLabel(draft: SurvivalTaskDraft): string {
  return draft.audienceMemberName ?? ROLE_LABEL[draft.roleId];
}

function audiencePrefix(draft: SurvivalTaskDraft): string {
  return draft.audienceMemberName ? "Сотрудник" : "Роль";
}

function sourceLabel(draft: SurvivalTaskDraft): string {
  return draft.sourceLabel ?? "Разбор владельца";
}

function createdMessage(draft: SurvivalTaskDraft, message: string): string {
  const impact = draft.impactLabel ? ` Вес: ${draft.impactLabel}.` : "";
  return `${message} Контур: ${sourceLabel(draft)}.${impact} Адресат: ${audiencePrefix(draft).toLowerCase()} ${audienceLabel(draft)}.`;
}

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
        dedupeOpenTask: true,
      });

      if (result.ok) {
        setStates((current) => ({ ...current, [index]: "saved" }));
        setMessage(createdMessage(draft, result.message));
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
        const AudienceIcon = draft.audienceMemberName ? UserRound : UsersRound;
        return (
          <div
            key={`${draft.roleId}-${index}-${draft.title}`}
            className="rounded-lg bg-background/35 px-3 py-2"
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="inline-flex items-center gap-1.5 rounded-md border border-brand/35 bg-brand/10 px-2 py-0.5 text-[10px] uppercase tracking-[0.12em] text-brand">
                    <Tags className="size-3" />
                    {sourceLabel(draft)}
                  </span>
                  <span className="inline-flex items-center gap-1.5 rounded-md border border-border/45 bg-background/45 px-2 py-0.5 text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                    <AudienceIcon className="size-3" />
                    {audiencePrefix(draft)}: {audienceLabel(draft)}
                  </span>
                  <span className="text-[11px] text-muted-foreground">
                    {PRIORITY_LABEL[draft.priority]} · {draft.dueLabel}
                  </span>
                  {draft.impactLabel ? (
                    <span className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] uppercase tracking-[0.12em] text-amber-200">
                      {draft.impactLabel}
                    </span>
                  ) : null}
                </div>
                <p className="mt-2 text-[13px] leading-relaxed text-foreground/85">
                  {draft.title}
                </p>
                <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
                  Создастся в Team OS как задача для{" "}
                  {audiencePrefix(draft).toLowerCase()} {audienceLabel(draft)}
                  {draft.contextNote ? " с первым комментарием от Receptor." : "."}
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
