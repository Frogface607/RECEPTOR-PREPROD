"use client";

import { useState, useTransition } from "react";
import Link from "next/link";
import {
  BookOpenCheck,
  CheckCircle2,
  HelpCircle,
  Lightbulb,
  ListChecks,
  Loader2,
  MessageSquareText,
  Plus,
  Send,
  Tags,
  UserRound,
  UsersRound,
} from "lucide-react";
import { createTeamTaskAction } from "@/app/team/actions";
import { Button } from "@/components/ui/button";
import type { SurvivalTaskDraft } from "@/lib/survival-score";
import { buildTeamHref } from "@/lib/team/team-links";
import { learningModuleHref } from "@/lib/team/team-learning";
import {
  taskContextBriefFromContext,
  taskChecklistHintFromContext,
  type TeamRoleId,
  type TeamTask,
} from "@/lib/team/team-os";

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
  const learning = draft.learningModuleTitle
    ? ` Стандарт: ${draft.learningModuleTitle}.`
    : "";
  const checklist = draft.learningChecklistTitle
    ? ` Чеклист: ${draft.learningChecklistTitle}.`
    : "";
  return `${message} Контур: ${sourceLabel(draft)}.${impact}${learning}${checklist} Адресат: ${audiencePrefix(draft).toLowerCase()} ${audienceLabel(draft)}.`;
}

export function SurvivalTaskActions({
  venueId,
  drafts,
}: {
  venueId: string;
  drafts: SurvivalTaskDraft[];
}) {
  const [states, setStates] = useState<TaskState>({});
  const [taskIds, setTaskIds] = useState<Record<number, string>>({});
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
        learningModuleId: draft.learningModuleId,
        learningModuleTitle: draft.learningModuleTitle,
        dedupeOpenTask: true,
      });

      if (result.ok) {
        setStates((current) => ({ ...current, [index]: "saved" }));
        const taskId = result.taskId;
        if (taskId) {
          setTaskIds((current) => ({ ...current, [index]: taskId }));
        }
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
        const savedTaskId = taskIds[index];
        const savedTaskHref = savedTaskId
          ? buildTeamHref({
              venueId,
              hash: "#team-actions",
              params: { focusTaskId: savedTaskId },
            })
          : null;
        const AudienceIcon = draft.audienceMemberName ? UserRound : UsersRound;
        const contextBrief = taskContextBriefFromContext(draft.contextNote);
        const checklistTitle =
          draft.learningChecklistTitle ??
          taskChecklistHintFromContext(draft.contextNote);
        const learningHref = draft.learningModuleId
          ? learningModuleHref(draft.learningModuleId, checklistTitle)
          : null;
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
                  {draft.learningModuleTitle ? (
                    <span className="inline-flex items-center gap-1.5 rounded-md border border-sky-400/25 bg-sky-400/10 px-2 py-0.5 text-[10px] uppercase tracking-[0.12em] text-sky-200">
                      <BookOpenCheck className="size-3" />
                      стандарт
                    </span>
                  ) : null}
                </div>
                <p className="mt-2 text-[13px] leading-relaxed text-foreground/85">
                  {draft.title}
                </p>
                {contextBrief.fieldFact ? (
                  <p className="mt-1 flex items-start gap-2 text-[11px] leading-relaxed text-foreground/75">
                    <MessageSquareText className="mt-0.5 size-3.5 shrink-0 text-brand" />
                    <span>{contextBrief.fieldFact}</span>
                  </p>
                ) : null}
                {contextBrief.question ? (
                  <p className="mt-1 flex items-start gap-2 text-[11px] leading-relaxed text-foreground/80">
                    <HelpCircle className="mt-0.5 size-3.5 shrink-0 text-brand" />
                    <span>{contextBrief.question}</span>
                  </p>
                ) : null}
                {contextBrief.check ? (
                  <p className="mt-1 flex items-start gap-2 text-[11px] leading-relaxed text-muted-foreground">
                    <ListChecks className="mt-0.5 size-3.5 shrink-0 text-brand" />
                    <span>{contextBrief.check}</span>
                  </p>
                ) : null}
                {contextBrief.reason ? (
                  <p className="mt-1 flex items-start gap-2 text-[11px] leading-relaxed text-amber-100/90">
                    <Lightbulb className="mt-0.5 size-3.5 shrink-0 text-amber-200" />
                    <span>{contextBrief.reason}</span>
                  </p>
                ) : null}
                {draft.learningModuleTitle ? (
                  <p className="mt-1 flex items-start gap-2 text-[11px] leading-relaxed text-sky-100/90">
                    <BookOpenCheck className="mt-0.5 size-3.5 shrink-0 text-sky-200" />
                    <span>
                      Команде поможет: {draft.learningModuleTitle}
                      {checklistTitle ? `. Чеклист: ${checklistTitle}` : ""}
                      {learningHref ? (
                        <>
                          {" "}
                          <Link
                            href={learningHref}
                            className="font-medium text-sky-100 underline-offset-4 hover:underline"
                          >
                            {checklistTitle ? "Открыть чеклист" : "Открыть"}
                          </Link>
                        </>
                      ) : null}
                    </span>
                  </p>
                ) : null}
                <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
                  Создастся в Team OS как задача для{" "}
                  {audiencePrefix(draft).toLowerCase()} {audienceLabel(draft)}
                  {draft.contextNote
                    ? " с первым комментарием от Receptor."
                    : "."}
                </p>
              </div>

              <div className="flex shrink-0 flex-col gap-2 sm:items-end">
                <Button
                  type="button"
                  variant={saved ? "secondary" : "outline"}
                  size="sm"
                  disabled={isPending || saved}
                  onClick={() => createTask(draft, index)}
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
                {savedTaskHref ? (
                  <Link
                    href={savedTaskHref}
                    className="text-[11px] font-medium text-brand underline-offset-4 hover:underline"
                  >
                    Открыть в Team OS
                  </Link>
                ) : null}
              </div>
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
