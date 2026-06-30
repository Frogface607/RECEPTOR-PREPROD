import {
  AlertTriangle,
  ArrowRight,
  BookOpenCheck,
  CheckCircle2,
  ClipboardList,
  GaugeCircle,
  HelpCircle,
  MessageSquareText,
  SearchCheck,
} from "lucide-react";
import Link from "next/link";
import type {
  OwnerProfitReadinessAction,
  OwnerReview,
  OwnerReviewAction,
  OwnerReviewActionTarget,
  OwnerReviewConfidence,
  OwnerReviewRole,
  OwnerReviewTone,
} from "@/lib/owner-review";
import { buildOwnerMorningReviewRows } from "@/lib/owner-morning-review";
import { buildTeamHref, type TeamPeriodParams } from "@/lib/team/team-links";
import type { TeamTask } from "@/lib/team/team-os";
import type { TeamTaskQueueSummary } from "@/lib/team/team-task-queue";
import { LinkButton } from "@/components/ui/link-button";

const TONE_CLASS: Record<OwnerReviewTone, string> = {
  risk: "border-destructive/35 bg-destructive/8 text-destructive",
  watch: "border-amber-500/35 bg-amber-500/10 text-amber-300",
  good: "border-brand/35 bg-brand/10 text-brand",
};

const ROLE_LABEL: Record<OwnerReviewRole, string> = {
  owner: "владелец",
  manager: "управляющий",
  chef: "кухня",
  service: "зал",
};

const CONFIDENCE_LABEL: Record<OwnerReviewConfidence, string> = {
  high: "уверенно",
  medium: "нужно проверить",
  low: "данных мало",
};

const TASK_STATUS_LABEL: Record<TeamTask["status"], string> = {
  new: "новая",
  accepted: "принята",
  in_progress: "в работе",
  done: "сделана",
  verified: "проверена",
};

function actionContour(action: OwnerReviewAction): string {
  return action.sourceLabel ?? "контур";
}

function ToneIcon({ tone }: { tone: OwnerReviewTone }) {
  if (tone === "risk") return <AlertTriangle className="size-4" />;
  if (tone === "watch") return <SearchCheck className="size-4" />;
  return <CheckCircle2 className="size-4" />;
}

function targetHref(
  target: OwnerReviewActionTarget,
  venueId: string,
  teamPeriodParams?: TeamPeriodParams,
): string {
  const encodedVenueId = encodeURIComponent(venueId);

  if (target === "iiko-settings") return "/settings#iiko";
  if (target === "labor-member") {
    return buildTeamHref({
      venueId,
      hash: "#team-actions",
      periodParams: teamPeriodParams,
    });
  }
  if (target === "labor-rate") {
    return buildTeamHref({
      venueId,
      hash: "#labor-rates",
      periodParams: teamPeriodParams,
    });
  }
  if (target === "shift-coverage") {
    return buildTeamHref({
      venueId,
      hash: "#shift-coverage",
      periodParams: teamPeriodParams,
    });
  }
  if (target === "shift-diagnostics") {
    return buildTeamHref({
      venueId,
      hash: "#iiko-shift-diagnostics",
      periodParams: teamPeriodParams,
    });
  }
  if (target === "shift-plan") {
    return buildTeamHref({
      venueId,
      hash: "#shift-plan",
      periodParams: teamPeriodParams,
    });
  }
  if (target === "shift-plan-variance") {
    return buildTeamHref({
      venueId,
      hash: "#shift-plan-variance",
      periodParams: teamPeriodParams,
    });
  }
  if (target === "team-learning") {
    return buildTeamHref({
      venueId,
      hash: "#learning-progress",
      periodParams: teamPeriodParams,
    });
  }
  if (target === "team-actions") {
    return buildTeamHref({
      venueId,
      hash: "#team-actions",
      periodParams: teamPeriodParams,
    });
  }
  if (target === "team-journal") {
    return buildTeamHref({
      venueId,
      hash: "#team-journal",
      periodParams: teamPeriodParams,
    });
  }
  if (target === "margin-diagnostics") {
    return `/settings#iiko-diagnostics-${encodedVenueId}`;
  }
  return "#margin-mapping-workspace";
}

function actionHref(
  action: OwnerReviewAction,
  venueId: string,
  teamPeriodParams?: TeamPeriodParams,
): string {
  if (action.existingTaskId) {
    return buildTeamHref({
      venueId,
      hash: "#team-actions",
      periodParams: teamPeriodParams,
      params: { focusTaskId: action.existingTaskId },
    });
  }

  if (
    (action.target === "labor-member" || action.target === "labor-rate") &&
    action.memberId
  ) {
    const encodedMemberId = encodeURIComponent(action.memberId);
    return buildTeamHref({
      venueId,
      hash: `#labor-member-${encodedMemberId}`,
      periodParams: teamPeriodParams,
      params: {
        memberId: action.memberId,
        focusMemberId: action.memberId,
      },
    });
  }

  if (action.target === "labor-member" && action.memberName) {
    return buildTeamHref({
      venueId,
      hash: "#team-actions",
      periodParams: teamPeriodParams,
      params: { prefillMemberName: action.memberName },
    });
  }

  return targetHref(action.target, venueId, teamPeriodParams);
}

function readinessHref(
  action: OwnerProfitReadinessAction,
  venueId: string,
  teamPeriodParams?: TeamPeriodParams,
): string {
  return targetHref(action.target, venueId, teamPeriodParams);
}

function teamTaskQueueHref(
  venueId: string,
  taskId: string | undefined,
  teamPeriodParams?: TeamPeriodParams,
): string {
  if (!taskId) {
    return buildTeamHref({
      venueId,
      hash: "#team-actions",
      periodParams: teamPeriodParams,
    });
  }

  return buildTeamHref({
    venueId,
    hash: "#team-actions",
    periodParams: teamPeriodParams,
    params: { focusTaskId: taskId },
  });
}

function actionCta(action: OwnerReviewAction): string {
  if (action.existingTaskId) return "Открыть задачу";
  if (action.target === "margin-risk") return "Разобрать";
  if (action.target === "iiko-settings") return "Открыть iiko";
  if (action.target === "labor-member" && action.memberId) return "Открыть";
  if (action.target === "labor-member") return "Добавить";
  if (action.target === "labor-rate") return "Ставка";
  if (action.target === "shift-coverage") return "Смены";
  if (action.target === "shift-diagnostics") return "Смена";
  if (action.target === "shift-plan") return "План";
  if (action.target === "shift-plan-variance") return "План/факт";
  if (action.target === "team-learning") return "Обучение";
  if (action.target === "team-journal") return "Журнал";
  if (action.target === "team-actions") return "Team OS";
  if (action.target === "margin-diagnostics") {
    return action.learningChecklistTitle === "Если в техкарте нет цен ингредиентов"
      ? "Цены техкарт"
      : "Цены RMS";
  }
  return "Связать";
}

function primaryAction(review: OwnerReview): OwnerReviewAction | null {
  return review.actions[0] ?? null;
}

export function OwnerCommandPanel({
  venueId,
  review,
  teamTaskQueue,
  teamPeriodParams,
}: {
  venueId: string;
  review: OwnerReview;
  teamTaskQueue?: TeamTaskQueueSummary;
  teamPeriodParams?: TeamPeriodParams;
}) {
  const mainAction = primaryAction(review);
  const proof = review.evidence.slice(0, 4);
  const morningReview = buildOwnerMorningReviewRows({ review, mainAction });
  const nextTeamTask = teamTaskQueue?.openTasks[0]?.task;
  const secondaryActions = review.actions.slice(
    mainAction ? 1 : 0,
    mainAction ? 3 : 2,
  );
  const teamActionsHref = buildTeamHref({
    venueId,
    hash: "#team-actions",
    periodParams: teamPeriodParams,
  });
  const shiftMemoryHref = buildTeamHref({
    venueId,
    hash: "#shift-summary",
    periodParams: teamPeriodParams,
  });
  const teamLearningHref = buildTeamHref({
    venueId,
    hash: "#learning-progress",
    periodParams: teamPeriodParams,
  });

  return (
    <section className="rounded-xl border border-brand/30 bg-card/70 p-5 shadow-[0_18px_80px_rgba(0,0,0,0.22)] sm:p-6">
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(360px,0.8fr)]">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-2 rounded-full border border-brand/35 bg-brand/10 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-brand">
              <GaugeCircle className="size-3.5" />
              Утро владельца
            </span>
            <span
              className={
                "rounded-full border px-3 py-1 text-[11px] uppercase tracking-[0.14em] " +
                TONE_CLASS[review.readiness.tone]
              }
            >
              {review.readiness.score}% · {review.readiness.title}
            </span>
            <span className="rounded-full border border-border/55 bg-background/45 px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
              {CONFIDENCE_LABEL[review.confidence]}
            </span>
          </div>

          <h2 className="mt-5 max-w-4xl text-balance text-3xl font-medium leading-[1.05] tracking-[-0.02em] text-foreground sm:text-4xl">
            {review.verdict}
          </h2>
          <p className="mt-4 max-w-3xl text-[15px] leading-relaxed text-muted-foreground">
            {review.summary}
          </p>

          <div className="mt-5 divide-y divide-border/45 border-y border-border/45">
            {morningReview.map((row) => (
              <div
                key={row.label}
                className="grid gap-2 py-3 sm:grid-cols-[120px_minmax(0,0.8fr)_minmax(0,1.2fr)] sm:items-start"
              >
                <div className="flex items-center gap-2">
                  <span
                    className={
                      "inline-flex size-6 items-center justify-center rounded-md border " +
                      TONE_CLASS[row.tone]
                    }
                  >
                    <ToneIcon tone={row.tone} />
                  </span>
                  <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                    {row.label}
                  </p>
                </div>
                <p className="min-w-0 text-sm font-medium leading-relaxed text-foreground">
                  {row.value}
                </p>
                <p className="min-w-0 text-[13px] leading-relaxed text-muted-foreground">
                  {row.detail}
                </p>
              </div>
            ))}
          </div>

          <div className="mt-5 flex flex-wrap gap-3">
            {mainAction ? (
              <LinkButton
                href={actionHref(mainAction, venueId, teamPeriodParams)}
              >
                {actionCta(mainAction)}
                <ArrowRight className="size-4" />
              </LinkButton>
            ) : review.readiness.action ? (
              <LinkButton
                href={readinessHref(
                  review.readiness.action,
                  venueId,
                  teamPeriodParams,
                )}
              >
                {review.readiness.action.label}
                <ArrowRight className="size-4" />
              </LinkButton>
            ) : null}
            {review.operationalPulse ? (
              <LinkButton
                href={readinessHref(
                  review.operationalPulse.action,
                  venueId,
                  teamPeriodParams,
                )}
                variant="outline"
              >
                Открыть контур
                <ArrowRight className="size-4" />
              </LinkButton>
            ) : null}
          </div>

          <div className="mt-5 grid gap-2 md:grid-cols-3">
            <Link
              href={teamActionsHref}
              className="group rounded-lg border border-border/50 bg-background/30 p-3 transition-colors hover:border-brand/45 hover:bg-brand/10"
            >
              <span className="flex items-center gap-2 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                <ClipboardList className="size-3.5 text-brand" />
                До смены
              </span>
              <span className="mt-2 block text-sm font-medium text-foreground">
                Фокус, задачи и бриф
              </span>
            </Link>
            <Link
              href={shiftMemoryHref}
              className="group rounded-lg border border-brand/30 bg-brand/10 p-3 transition-colors hover:border-brand/55 hover:bg-brand/15"
            >
              <span className="flex items-center gap-2 text-[10px] uppercase tracking-[0.16em] text-brand">
                <MessageSquareText className="size-3.5" />
                После смены
              </span>
              <span className="mt-2 block text-sm font-medium text-foreground">
                Итог с поля в память
              </span>
            </Link>
            <Link
              href={teamLearningHref}
              className="group rounded-lg border border-border/50 bg-background/30 p-3 transition-colors hover:border-brand/45 hover:bg-brand/10"
            >
              <span className="flex items-center gap-2 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                <BookOpenCheck className="size-3.5 text-brand" />
                Обучение
              </span>
              <span className="mt-2 block text-sm font-medium text-foreground">
                Закрыть пробел команды
              </span>
            </Link>
          </div>

          {proof.length > 0 ? (
            <details className="mt-4 rounded-lg border border-border/45 bg-background/25 px-3 py-2">
              <summary className="cursor-pointer select-none text-[11px] uppercase tracking-[0.16em] text-muted-foreground transition-colors hover:text-foreground">
                Что учтено в разборе · {proof.length}
              </summary>
              <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
                {proof.map((item) => (
                  <div
                    key={item.label}
                    className="rounded-lg border border-border/45 bg-card/35 p-3"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                        {item.label}
                      </p>
                      <span
                        className={
                          "inline-flex size-6 items-center justify-center rounded-md border " +
                          TONE_CLASS[item.tone]
                        }
                      >
                        <ToneIcon tone={item.tone} />
                      </span>
                    </div>
                    <p className="mt-3 truncate text-xl font-medium text-foreground">
                      {item.value}
                    </p>
                    <p className="mt-1 line-clamp-2 text-[12px] leading-relaxed text-muted-foreground">
                      {item.detail}
                    </p>
                  </div>
                ))}
              </div>
            </details>
          ) : null}
        </div>

        <div className="rounded-lg border border-border/55 bg-background/35 p-4">
          <div className="mb-4 flex items-start justify-between gap-3">
            <div>
              <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                Что сделать сейчас
              </p>
              <h3 className="mt-2 text-lg font-medium text-foreground">
                {mainAction
                  ? "Один следующий шаг"
                  : nextTeamTask
                    ? "Задача в Team OS"
                    : "Контур спокойный"}
              </h3>
            </div>
            <ClipboardList className="size-5 text-brand" />
          </div>

          {mainAction ? (
            <div className="rounded-lg border border-brand/30 bg-brand/10 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={
                    "inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-[10px] uppercase tracking-[0.12em] " +
                    TONE_CLASS[mainAction.tone]
                  }
                >
                  <ToneIcon tone={mainAction.tone} />
                  {ROLE_LABEL[mainAction.role]}
                </span>
                {mainAction.sourceLabel ? (
                  <span className="rounded-md border border-brand/30 bg-background/35 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-brand">
                    {actionContour(mainAction)}
                  </span>
                ) : null}
                {mainAction.impactLabel ? (
                  <span className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-amber-200">
                    {mainAction.impactLabel}
                  </span>
                ) : null}
                {mainAction.learningModuleTitle ? (
                  <span className="rounded-md border border-sky-400/30 bg-sky-400/10 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-sky-200">
                    стандарт
                  </span>
                ) : null}
                {mainAction.existingTaskId ? (
                  <span className="rounded-md border border-border/45 bg-background/50 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                    Team OS
                    {mainAction.existingTaskStatus
                      ? `: ${TASK_STATUS_LABEL[mainAction.existingTaskStatus]}`
                      : ""}
                  </span>
                ) : null}
              </div>
              <h4 className="mt-3 text-base font-medium leading-snug text-foreground">
                {mainAction.title}
              </h4>
              <p className="mt-2 line-clamp-3 text-[13px] leading-relaxed text-muted-foreground">
                {mainAction.detail}
              </p>
              {mainAction.briefingQuestion ? (
                <p className="mt-2 flex items-start gap-2 text-[12px] leading-relaxed text-foreground/85">
                  <HelpCircle className="mt-0.5 size-3.5 shrink-0 text-brand" />
                  <span>{mainAction.briefingQuestion}</span>
                </p>
              ) : null}
              {mainAction.learningModuleTitle ? (
                <p className="mt-2 line-clamp-1 text-[12px] leading-relaxed text-sky-100/85">
                  Стандарт команды: {mainAction.learningModuleTitle}
                  {mainAction.learningChecklistTitle
                    ? `. Чеклист: ${mainAction.learningChecklistTitle}`
                    : ""}
                </p>
              ) : null}
              <LinkButton
                href={actionHref(mainAction, venueId, teamPeriodParams)}
                className="mt-4 h-9 px-3 text-[13px]"
              >
                {actionCta(mainAction)}
                <ArrowRight className="size-3.5" />
              </LinkButton>
            </div>
          ) : nextTeamTask ? (
            <div className="rounded-lg border border-brand/30 bg-brand/10 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-md border border-brand/25 bg-background/35 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-brand">
                  следующая задача
                </span>
                {nextTeamTask.sourceLabel ? (
                  <span className="rounded-md border border-border/45 bg-card/50 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                    {nextTeamTask.sourceLabel}
                  </span>
                ) : null}
                {nextTeamTask.impactLabel ? (
                  <span className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-amber-200">
                    {nextTeamTask.impactLabel}
                  </span>
                ) : null}
                <span className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                  {nextTeamTask.dueLabel}
                </span>
              </div>
              <h4 className="mt-3 text-base font-medium leading-snug text-foreground">
                {nextTeamTask.title}
              </h4>
              <LinkButton
                href={teamTaskQueueHref(
                  venueId,
                  nextTeamTask.id,
                  teamPeriodParams,
                )}
                className="mt-4 h-9 px-3 text-[13px]"
              >
                Открыть задачу
                <ArrowRight className="size-3.5" />
              </LinkButton>
            </div>
          ) : (
            <div className="rounded-lg border border-brand/25 bg-brand/10 p-3 text-[13px] leading-relaxed text-foreground/85">
              Критичных действий нет. Дальше можно смотреть детали по марже, ФОТ
              и сменам ниже.
            </div>
          )}

          {teamTaskQueue ? (
            <div className="mt-4 rounded-lg border border-border/45 bg-card/35 p-3">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                    Командная очередь
                  </p>
                  <p className="mt-1 text-sm font-medium text-foreground">
                    {teamTaskQueue.openCount > 0
                      ? `${teamTaskQueue.openCount} открыто · ${teamTaskQueue.urgentOpenCount} срочно · ${teamTaskQueue.inProgressCount} в работе`
                      : "Открытых задач нет"}
                  </p>
                </div>
                <LinkButton
                  href={teamTaskQueueHref(
                    venueId,
                    nextTeamTask?.id,
                    teamPeriodParams,
                  )}
                  variant="outline"
                  className="h-8 shrink-0 px-3 text-[12px]"
                >
                  {nextTeamTask ? "Открыть задачу" : "Открыть Team OS"}
                  <ArrowRight className="size-3.5" />
                </LinkButton>
              </div>

              {!nextTeamTask ? (
                <p className="mt-3 text-[12px] leading-relaxed text-muted-foreground">
                  Если владелец создаст действие из рекомендаций, оно появится в
                  Team OS и будет видно здесь.
                </p>
              ) : null}
              {teamTaskQueue.openContours.length > 0 ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {teamTaskQueue.openContours.slice(0, 4).map((contour) => (
                    <span
                      key={contour.label}
                      className="rounded-md border border-border/45 bg-background/35 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-muted-foreground"
                    >
                      {contour.label}: {contour.count}
                    </span>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}

          {secondaryActions.length > 0 ? (
            <div className="mt-4 space-y-2">
              <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                Следом
              </p>
              {secondaryActions.map((action) => (
                <div
                  key={`${action.target}-${action.title}`}
                  className="grid gap-3 rounded-lg border border-border/45 bg-card/35 p-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center"
                >
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      {action.sourceLabel ? (
                        <span className="rounded-md border border-brand/30 bg-brand/10 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-brand">
                          {actionContour(action)}
                        </span>
                      ) : null}
                      {action.impactLabel ? (
                        <span className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-amber-200">
                          {action.impactLabel}
                        </span>
                      ) : null}
                      {action.learningModuleTitle ? (
                        <span className="rounded-md border border-sky-400/30 bg-sky-400/10 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-sky-200">
                          стандарт
                        </span>
                      ) : null}
                      <p className="text-[13px] font-medium text-foreground">
                        {action.title}
                      </p>
                    </div>
                    <p className="mt-1 line-clamp-1 text-[12px] leading-relaxed text-muted-foreground">
                      {action.detail}
                    </p>
                    {action.briefingQuestion ? (
                      <p className="mt-1 flex items-start gap-2 text-[12px] leading-relaxed text-foreground/85">
                        <HelpCircle className="mt-0.5 size-3.5 shrink-0 text-brand" />
                        <span>{action.briefingQuestion}</span>
                      </p>
                    ) : null}
                  </div>
                  <LinkButton
                    href={actionHref(action, venueId, teamPeriodParams)}
                    variant="outline"
                    className="h-8 shrink-0 px-3 text-[12px]"
                  >
                    {actionCta(action)}
                    <ArrowRight className="size-3.5" />
                  </LinkButton>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
