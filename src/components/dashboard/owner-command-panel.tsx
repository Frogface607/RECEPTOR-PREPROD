import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ClipboardList,
  GaugeCircle,
  ListChecks,
  SearchCheck,
} from "lucide-react";
import type {
  OwnerProfitReadinessAction,
  OwnerReview,
  OwnerReviewAction,
  OwnerReviewActionTarget,
  OwnerReviewConfidence,
  OwnerReviewRole,
  OwnerReviewTone,
} from "@/lib/owner-review";
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

function actionContour(action: OwnerReviewAction): string {
  return action.sourceLabel ?? "контур";
}

function ToneIcon({ tone }: { tone: OwnerReviewTone }) {
  if (tone === "risk") return <AlertTriangle className="size-4" />;
  if (tone === "watch") return <SearchCheck className="size-4" />;
  return <CheckCircle2 className="size-4" />;
}

function targetHref(target: OwnerReviewActionTarget, venueId: string): string {
  const encodedVenueId = encodeURIComponent(venueId);

  if (target === "iiko-settings") return "/settings#iiko";
  if (target === "labor-member") {
    return `/team?role=venue_manager&venueId=${encodedVenueId}#team-actions`;
  }
  if (target === "labor-rate") {
    return `/team?role=venue_manager&venueId=${encodedVenueId}#labor-rates`;
  }
  if (target === "shift-coverage") {
    return `/team?role=venue_manager&venueId=${encodedVenueId}#shift-coverage`;
  }
  if (target === "shift-diagnostics") {
    return `/team?role=venue_manager&venueId=${encodedVenueId}#iiko-shift-diagnostics`;
  }
  if (target === "shift-plan") {
    return `/team?role=venue_manager&venueId=${encodedVenueId}#shift-plan`;
  }
  if (target === "shift-plan-variance") {
    return `/team?role=venue_manager&venueId=${encodedVenueId}#shift-plan-variance`;
  }
  if (target === "team-learning") {
    return `/team?role=venue_manager&venueId=${encodedVenueId}#learning-progress`;
  }
  if (target === "team-actions") {
    return `/team?role=venue_manager&venueId=${encodedVenueId}#team-actions`;
  }
  if (target === "team-journal") {
    return `/team?role=venue_manager&venueId=${encodedVenueId}#team-journal`;
  }
  if (target === "margin-diagnostics") {
    return `/settings#iiko-diagnostics-${encodedVenueId}`;
  }
  return "#margin-mapping-workspace";
}

function actionHref(action: OwnerReviewAction, venueId: string): string {
  const encodedVenueId = encodeURIComponent(venueId);

  if (action.existingTaskId) {
    const encodedTaskId = encodeURIComponent(action.existingTaskId);
    return `/team?role=venue_manager&venueId=${encodedVenueId}&focusTaskId=${encodedTaskId}#team-task-${encodedTaskId}`;
  }

  if (
    (action.target === "labor-member" || action.target === "labor-rate") &&
    action.memberId
  ) {
    const encodedMemberId = encodeURIComponent(action.memberId);
    return `/team?role=venue_manager&venueId=${encodedVenueId}&memberId=${encodedMemberId}&focusMemberId=${encodedMemberId}#labor-member-${encodedMemberId}`;
  }

  if (action.target === "labor-member" && action.memberName) {
    return `/team?role=venue_manager&venueId=${encodedVenueId}&prefillMemberName=${encodeURIComponent(action.memberName)}#team-actions`;
  }

  return targetHref(action.target, venueId);
}

function readinessHref(
  action: OwnerProfitReadinessAction,
  venueId: string,
): string {
  return targetHref(action.target, venueId);
}

function actionCta(action: OwnerReviewAction): string {
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
  if (action.target === "margin-diagnostics") return "RMS";
  return "Связать";
}

function primaryAction(review: OwnerReview): OwnerReviewAction | null {
  return review.actions[0] ?? null;
}

export function OwnerCommandPanel({
  venueId,
  review,
}: {
  venueId: string;
  review: OwnerReview;
}) {
  const mainAction = primaryAction(review);
  const proof = review.evidence.slice(0, 4);

  return (
    <section className="rounded-xl border border-brand/30 bg-card/70 p-5 shadow-[0_18px_80px_rgba(0,0,0,0.22)] sm:p-6">
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(360px,0.8fr)]">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-2 rounded-full border border-brand/35 bg-brand/10 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-brand">
              <GaugeCircle className="size-3.5" />
              Сводка владельца
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

          <div className="mt-5 flex flex-wrap gap-3">
            {mainAction ? (
              <LinkButton href={actionHref(mainAction, venueId)}>
                {actionCta(mainAction)}
                <ArrowRight className="size-4" />
              </LinkButton>
            ) : review.readiness.action ? (
              <LinkButton
                href={readinessHref(review.readiness.action, venueId)}
              >
                {review.readiness.action.label}
                <ArrowRight className="size-4" />
              </LinkButton>
            ) : null}
            {review.operationalPulse ? (
              <LinkButton
                href={readinessHref(review.operationalPulse.action, venueId)}
                variant="outline"
              >
                Открыть контур
                <ArrowRight className="size-4" />
              </LinkButton>
            ) : null}
          </div>

          <div className="mt-6 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
            {proof.map((item) => (
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
                <p className="mt-1 line-clamp-2 text-[12px] leading-relaxed text-muted-foreground">
                  {item.detail}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-border/55 bg-background/35 p-4">
          <div className="mb-4 flex items-start justify-between gap-3">
            <div>
              <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                Что сделать сейчас
              </p>
              <h3 className="mt-2 text-lg font-medium text-foreground">
                Первые управленческие шаги
              </h3>
            </div>
            <ClipboardList className="size-5 text-brand" />
          </div>

          {review.actions.length > 0 ? (
            <div className="space-y-2.5">
              {review.actions.slice(0, 3).map((action) => (
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
                      {action.existingTaskId ? (
                        <span className="rounded-md border border-border/45 bg-background/50 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                          уже в Team OS
                        </span>
                      ) : null}
                      <p className="text-[13px] font-medium text-foreground">
                        {action.title}
                      </p>
                    </div>
                    <p className="mt-2 line-clamp-2 text-[12px] leading-relaxed text-muted-foreground">
                      {action.detail}
                    </p>
                  </div>
                  <LinkButton
                    href={actionHref(action, venueId)}
                    variant="outline"
                    className="h-8 shrink-0 px-3 text-[12px]"
                  >
                    {actionCta(action)}
                    <ArrowRight className="size-3.5" />
                  </LinkButton>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-lg border border-brand/25 bg-brand/10 p-3 text-[13px] leading-relaxed text-foreground/85">
              Критичных действий нет. Дальше можно смотреть детали по марже, ФОТ
              и сменам ниже.
            </div>
          )}

          {review.operationalPulse ? (
            <div className="mt-4 rounded-lg border border-border/45 bg-card/35 p-3">
              <div className="flex items-start gap-3">
                <span
                  className={
                    "mt-0.5 inline-flex size-8 items-center justify-center rounded-md border " +
                    TONE_CLASS[review.operationalPulse.tone]
                  }
                >
                  <ListChecks className="size-4" />
                </span>
                <div className="min-w-0">
                  <p className="text-[13px] font-medium text-foreground">
                    {review.operationalPulse.title}
                  </p>
                  <p className="mt-1 line-clamp-2 text-[12px] leading-relaxed text-muted-foreground">
                    {review.operationalPulse.detail}
                  </p>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
