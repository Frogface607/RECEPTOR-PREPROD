import {
  AlertTriangle,
  CheckCircle2,
  ClipboardList,
  ArrowRight,
  GaugeCircle,
  HelpCircle,
  ListChecks,
  MessageSquareText,
  SearchCheck,
  ShieldCheck,
} from "lucide-react";
import Link from "next/link";
import type {
  OwnerReview,
  OwnerReviewAction,
  OwnerReviewConfidence,
  OwnerProfitReadinessAction,
  OwnerReviewRole,
  OwnerReviewTone,
  OwnerReviewActionTarget,
} from "@/lib/owner-review";
import { buildTeamHref, type TeamPeriodParams } from "@/lib/team/team-links";
import { SurvivalTaskActions } from "./survival-task-actions";
import { LinkButton } from "@/components/ui/link-button";

const TONE_CLASS: Record<OwnerReviewTone, string> = {
  risk: "border-destructive/35 bg-destructive/8 text-destructive",
  watch: "border-amber-500/35 bg-amber-500/10 text-amber-300",
  good: "border-brand/35 bg-brand/10 text-brand",
};

const ROLE_LABEL: Record<OwnerReviewRole, string> = {
  owner: "владелец",
  manager: "управляющий",
  chef: "шеф",
  service: "зал",
};

const CONFIDENCE_LABEL: Record<OwnerReviewConfidence, string> = {
  high: "высокая уверенность",
  medium: "средняя уверенность",
  low: "низкая уверенность",
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

  if (target === "iiko-settings") {
    return `/settings#iiko`;
  }

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

  if (target === "margin-risk") {
    return "#margin-mapping-workspace";
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

  if (action.target === "labor-member" && action.memberId) {
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

  if (action.target === "labor-rate" && action.memberId) {
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

  return targetHref(action.target, venueId, teamPeriodParams);
}

function readinessHref(
  action: OwnerProfitReadinessAction,
  venueId: string,
  teamPeriodParams?: TeamPeriodParams,
): string {
  return targetHref(action.target, venueId, teamPeriodParams);
}

function actionCta(action: OwnerReviewAction): string {
  if (action.existingTaskId) return "Открыть задачу";
  if (action.target === "margin-risk") return "Разобрать маржу";
  if (action.target === "iiko-settings") return "Открыть iiko";
  if (action.target === "labor-member" && action.memberId)
    return "Открыть сотрудника";
  if (action.target === "labor-member") return "Добавить";
  if (action.target === "labor-rate") return "Открыть ставку";
  if (action.target === "shift-coverage") return "Открыть смены";
  if (action.target === "shift-diagnostics") return "Разобрать смену";
  if (action.target === "shift-plan") return "Открыть план";
  if (action.target === "shift-plan-variance") return "Открыть план/факт";
  if (action.target === "team-learning") return "Открыть обучение";
  if (action.target === "team-journal") return "Открыть журнал";
  if (action.target === "team-actions") return "Открыть Team OS";
  if (action.target === "margin-diagnostics") return "Проверить RMS";
  return "Связать блюдо";
}

export function OwnerReviewCard({
  venueId,
  review,
  teamPeriodParams,
}: {
  venueId: string;
  review: OwnerReview;
  teamPeriodParams?: TeamPeriodParams;
}) {
  return (
    <section className="rounded-xl border border-brand/25 bg-card/70 p-5 sm:p-6">
      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-2 rounded-full border border-brand/35 bg-brand/10 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-brand">
              <ShieldCheck className="size-3.5" />
              Разбор владельца
            </span>
            <span className="rounded-full border border-border/55 bg-background/45 px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
              {CONFIDENCE_LABEL[review.confidence]}
            </span>
          </div>

          <h2 className="mt-4 max-w-4xl text-balance text-2xl font-medium leading-tight tracking-[-0.02em] text-foreground sm:text-3xl">
            {review.verdict}
          </h2>
          <p className="mt-3 max-w-3xl text-[14px] leading-relaxed text-muted-foreground">
            {review.summary}
          </p>

          <div className="mt-5 rounded-lg border border-border/45 bg-background/35 p-3">
            <div className="flex items-start gap-2">
              <HelpCircle className="mt-0.5 size-4 shrink-0 text-brand" />
              <p className="text-[12px] leading-relaxed text-muted-foreground">
                Уверенность:{" "}
                <span className="text-foreground/85">
                  {review.confidenceReason}
                </span>
                . Каждый вывод ниже — гипотеза для проверки, а не магическое
                утверждение.
              </p>
            </div>
          </div>

          <div className="mt-3 rounded-lg border border-border/45 bg-background/35 p-3">
            <div className="grid gap-3 sm:grid-cols-[auto_minmax(0,1fr)_auto] sm:items-center">
              <span
                className={
                  "inline-flex size-9 items-center justify-center rounded-md border " +
                  TONE_CLASS[review.readiness.tone]
                }
              >
                <GaugeCircle className="size-4" />
              </span>
              <div className="min-w-0">
                <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                  Достоверность прибыли
                </p>
                <p className="mt-1 text-[14px] font-medium text-foreground">
                  {review.readiness.title}
                </p>
              </div>
              <div className="sm:text-right">
                <p className="text-xl font-medium text-foreground">
                  {review.readiness.score}%
                </p>
                <p className="text-[11px] text-muted-foreground">готовность</p>
              </div>
            </div>
            <p className="mt-3 text-[12px] leading-relaxed text-muted-foreground">
              {review.readiness.detail}
            </p>
            {review.readiness.action ? (
              <LinkButton
                href={readinessHref(
                  review.readiness.action,
                  venueId,
                  teamPeriodParams,
                )}
                variant="outline"
                className="mt-3 h-8 px-3 text-[12px]"
              >
                {review.readiness.action.label}
                <ArrowRight className="size-3.5" />
              </LinkButton>
            ) : null}
          </div>

          {review.operationalPulse ? (
            <div className="mt-3 rounded-lg border border-border/45 bg-background/35 p-3">
              <div className="grid gap-3 sm:grid-cols-[auto_minmax(0,1fr)_auto] sm:items-center">
                <span
                  className={
                    "inline-flex size-9 items-center justify-center rounded-md border " +
                    TONE_CLASS[review.operationalPulse.tone]
                  }
                >
                  <ListChecks className="size-4" />
                </span>
                <div className="min-w-0">
                  <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                    Контур управления
                  </p>
                  <p className="mt-1 text-[14px] font-medium text-foreground">
                    {review.operationalPulse.title}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-2 sm:text-right">
                  <div>
                    <p className="text-lg font-medium text-foreground">
                      {review.operationalPulse.openTasks}
                    </p>
                    <p className="text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                      открыто
                    </p>
                  </div>
                  <div>
                    <p className="text-lg font-medium text-foreground">
                      {review.operationalPulse.closedLoops}
                    </p>
                    <p className="text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                      закрыто
                    </p>
                  </div>
                </div>
              </div>
              <p className="mt-3 text-[12px] leading-relaxed text-muted-foreground">
                {review.operationalPulse.detail}
              </p>
              {review.operationalPulse.openTaskContours.length > 0 ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {review.operationalPulse.openTaskContours.map((contour) => (
                    <span
                      key={contour}
                      className="rounded-md border border-brand/30 bg-brand/10 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-brand"
                    >
                      {contour}
                    </span>
                  ))}
                </div>
              ) : null}

              {review.operationalPulse.recentEvents.length > 0 ? (
                <div className="mt-3 divide-y divide-border/35 overflow-hidden rounded-md border border-border/35">
                  {review.operationalPulse.recentEvents.map((event) => (
                    <Link
                      key={`${event.label}-${event.timeLabel}-${event.summary}`}
                      href={targetHref(event.target, venueId, teamPeriodParams)}
                      className="grid gap-2 px-3 py-2 transition-colors hover:bg-card/45 sm:grid-cols-[auto_minmax(0,1fr)_auto_auto] sm:items-center"
                    >
                      <span
                        className={
                          "w-fit rounded-md border px-2 py-1 text-[10px] uppercase tracking-[0.12em] " +
                          TONE_CLASS[event.tone]
                        }
                      >
                        {event.label}
                      </span>
                      <p className="min-w-0 text-[12px] leading-relaxed text-foreground/80">
                        {event.summary}
                      </p>
                      {event.timeLabel ? (
                        <span className="text-[11px] text-muted-foreground">
                          {event.timeLabel}
                        </span>
                      ) : null}
                      <ArrowRight className="hidden size-3.5 text-muted-foreground sm:block" />
                    </Link>
                  ))}
                </div>
              ) : null}

              <LinkButton
                href={readinessHref(
                  review.operationalPulse.action,
                  venueId,
                  teamPeriodParams,
                )}
                variant="outline"
                className="mt-3 h-8 px-3 text-[12px]"
              >
                {review.operationalPulse.action.label}
                <ArrowRight className="size-3.5" />
              </LinkButton>
            </div>
          ) : null}

          <div className="mt-5 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
            {review.evidence.map((item) => (
              <div
                key={item.label}
                className="rounded-lg border border-border/45 bg-background/35 p-3"
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
                <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
                  {item.detail}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-border/55 bg-background/35 p-4">
          {review.actions.length > 0 ? (
            <div className="mb-5 border-b border-border/45 pb-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                    Что сделать первым
                  </p>
                  <h3 className="mt-2 text-lg font-medium">
                    Очередь владельца
                  </h3>
                </div>
                <ClipboardList className="size-5 text-brand" />
              </div>
              <div className="mt-3 space-y-2.5">
                {review.actions.map((action) => (
                  <div
                    key={`${action.target}-${action.title}`}
                    className="grid gap-3 rounded-lg border border-border/45 bg-card/45 p-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center"
                  >
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          className={
                            "inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-[10px] uppercase tracking-[0.12em] " +
                            TONE_CLASS[action.tone]
                          }
                        >
                          <ToneIcon tone={action.tone} />
                          {ROLE_LABEL[action.role]}
                        </span>
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
                            урок
                          </span>
                        ) : null}
                        {action.existingTaskId ? (
                          <span className="rounded-md border border-border/45 bg-background/50 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                            уже в Team OS
                          </span>
                        ) : null}
                        <p className="text-[13px] font-medium text-foreground">
                          {action.title}
                        </p>
                      </div>
                      <p className="mt-2 text-[12px] leading-relaxed text-muted-foreground">
                        {action.detail}
                      </p>
                      {action.learningModuleTitle ? (
                        <p className="mt-1 text-[12px] leading-relaxed text-sky-100/85">
                          Команде поможет: {action.learningModuleTitle}
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
            </div>
          ) : null}

          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                Что проверить
              </p>
              <h3 className="mt-2 text-lg font-medium">
                Гипотезы вместо очевидных советов
              </h3>
            </div>
            <MessageSquareText className="size-5 text-brand" />
          </div>

          <div className="mt-4 space-y-3">
            {review.hypotheses.map((hypothesis) => (
              <div
                key={`${hypothesis.role}-${hypothesis.title}`}
                className="rounded-lg border border-border/45 bg-card/45 p-3"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={
                      "inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-[10px] uppercase tracking-[0.12em] " +
                      TONE_CLASS[hypothesis.tone]
                    }
                  >
                    <ToneIcon tone={hypothesis.tone} />
                    {ROLE_LABEL[hypothesis.role]}
                  </span>
                  <p className="text-[13px] font-medium text-foreground">
                    {hypothesis.title}
                  </p>
                </div>
                <p className="mt-2 text-[12px] leading-relaxed text-muted-foreground">
                  {hypothesis.why}
                </p>
                <p className="mt-2 text-[13px] leading-relaxed text-foreground/85">
                  {hypothesis.check}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-[0.95fr_1.05fr]">
        <div>
          <div className="mb-3 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            <HelpCircle className="size-3.5 text-brand" />
            Вопросы команде
          </div>
          <div className="space-y-2">
            {review.questions.map((question) => (
              <div
                key={`${question.role}-${question.text}`}
                className="rounded-lg bg-background/35 px-3 py-2 text-[13px] leading-relaxed text-foreground/85"
              >
                <span className="mr-2 font-mono text-[10px] uppercase tracking-[0.14em] text-brand">
                  {ROLE_LABEL[question.role]}
                </span>
                {question.text}
              </div>
            ))}
          </div>
        </div>

        <div>
          <div className="mb-3 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            <ClipboardList className="size-3.5 text-brand" />
            Сразу в задачи
          </div>
          <SurvivalTaskActions venueId={venueId} drafts={review.tasks} />
        </div>
      </div>
    </section>
  );
}
