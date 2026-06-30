"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import {
  ArrowRight,
  BookOpenCheck,
  CheckCircle2,
  Circle,
  ListChecks,
  MessageSquareText,
  RotateCcw,
  Target,
  Trophy,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  calculateLearningScore,
  learningModuleHref,
  type TeamLearningItem,
  type TeamLearningScore,
} from "@/lib/team/team-learning";
import {
  buildTeamLearningAdmission,
  type TeamLearningAdmission,
} from "@/lib/team/team-learning-admission";
import { buildTeamLearningShiftCard } from "@/lib/team/team-learning-shift-card";
import type { TeamLearningProgressSnapshot } from "@/lib/team/team-learning-progress";
import { saveLearningProgressAction } from "./actions";

type StoredProgress = TeamLearningProgressSnapshot;

type ProgressMap = Record<string, StoredProgress>;

const STORAGE_KEY = "receptor-learning-progress:v1";

function loadProgress(): ProgressMap {
  if (typeof window === "undefined") return {};

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as ProgressMap;
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function saveProgress(progress: ProgressMap) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
  } catch {
    // Local progress is helpful, but the lesson must remain usable without it.
  }
}

function mergeProgress(
  primary: ProgressMap,
  secondary: ProgressMap,
): ProgressMap {
  const merged: ProgressMap = { ...secondary };

  for (const [moduleId, progress] of Object.entries(primary)) {
    const current = merged[moduleId];
    if (!current || progress.bestPercentage >= current.bestPercentage) {
      merged[moduleId] = progress;
    }
  }

  return merged;
}

function formatProgressDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "сегодня";

  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function progressLabel(
  item: TeamLearningItem,
  progress?: StoredProgress,
): string {
  if (!progress) return "не пройдено";
  if (progress.bestPercentage >= item.passPercentage) return "сдано";
  return "повторить";
}

function progressClass(
  item: TeamLearningItem,
  progress?: StoredProgress,
): string {
  if (!progress) return "border-border bg-muted/35 text-muted-foreground";
  if (progress.bestPercentage >= item.passPercentage) {
    return "border-brand/30 bg-brand/10 text-brand";
  }
  return "border-amber-400/30 bg-amber-400/10 text-amber-200";
}

function normalizedTitle(value: string | null | undefined): string {
  return value?.trim().toLocaleLowerCase("ru-RU") ?? "";
}

export function LearningWorkspace({
  items,
  initialModuleId,
  initialChecklistTitle,
  initialProgress,
  memberName,
  roleTitle,
  venueId,
  venueName,
}: {
  items: TeamLearningItem[];
  initialModuleId: string;
  initialChecklistTitle?: string;
  initialProgress: ProgressMap;
  memberName: string;
  roleTitle: string;
  venueId: string;
  venueName: string;
}) {
  const [pending, startTransition] = useTransition();
  const [activeItemId, setActiveItemId] = useState(initialModuleId);
  const [activeChecklistTitle, setActiveChecklistTitle] = useState(
    initialChecklistTitle?.trim() ?? "",
  );
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [submittedScore, setSubmittedScore] =
    useState<TeamLearningScore | null>(null);
  const [progress, setProgress] = useState<ProgressMap>(() =>
    mergeProgress(initialProgress, loadProgress()),
  );
  const [saveMessage, setSaveMessage] = useState<string>("");

  const activeItem = useMemo(
    () => items.find((item) => item.id === activeItemId) ?? items[0],
    [activeItemId, items],
  );
  const activeItemUrlId = activeItem?.id;

  useEffect(() => {
    if (!activeItemUrlId) return;
    const nextUrl = learningModuleHref(activeItemUrlId, activeChecklistTitle);
    window.history.replaceState(null, "", nextUrl);
  }, [activeItemUrlId, activeChecklistTitle]);

  const answeredCount = activeItem
    ? activeItem.quiz.filter((_, index) => answers[index] !== undefined).length
    : 0;
  const allAnswered = activeItem
    ? answeredCount === activeItem.quiz.length && activeItem.quiz.length > 0
    : false;
  const completedCount = items.filter(
    (item) => (progress[item.id]?.bestPercentage ?? 0) >= item.passPercentage,
  ).length;
  const averageScore =
    items.length > 0
      ? Math.round(
          items.reduce(
            (sum, item) => sum + (progress[item.id]?.bestPercentage ?? 0),
            0,
          ) / items.length,
        )
      : 0;
  const admission = useMemo(
    () => buildTeamLearningAdmission({ items, progress }),
    [items, progress],
  );
  const shiftCard = useMemo(
    () =>
      activeItem
        ? buildTeamLearningShiftCard(activeItem, activeChecklistTitle)
        : null,
    [activeItem, activeChecklistTitle],
  );

  function selectAnswer(questionIndex: number, answerIndex: number) {
    if (submittedScore) return;
    setAnswers((current) => ({
      ...current,
      [questionIndex]: answerIndex,
    }));
  }

  function selectModule(moduleId: string) {
    setActiveItemId(moduleId);
    setActiveChecklistTitle("");
    setAnswers({});
    setSubmittedScore(null);
    setSaveMessage("");
  }

  function submitQuiz() {
    if (!activeItem || !allAnswered) return;

    const selectedAnswers = activeItem.quiz.map(
      (_, index) => answers[index] ?? -1,
    );
    const score = calculateLearningScore(activeItem, selectedAnswers);
    const previous = progress[activeItem.id];
    const nextProgress: ProgressMap = {
      ...progress,
      [activeItem.id]: {
        bestPercentage: Math.max(
          previous?.bestPercentage ?? 0,
          score.percentage,
        ),
        lastPercentage: score.percentage,
        correct: score.correct,
        total: score.total,
        passed:
          score.passed ||
          (previous?.bestPercentage ?? 0) >= activeItem.passPercentage,
        answers: selectedAnswers,
        completedAt: new Date().toISOString(),
      },
    };

    setSubmittedScore(score);
    setProgress(nextProgress);
    saveProgress(nextProgress);
    setSaveMessage("");

    startTransition(async () => {
      const result = await saveLearningProgressAction({
        venueId,
        moduleId: activeItem.id,
        answers: selectedAnswers,
      });

      if (!result.ok) {
        setSaveMessage(`Локально сохранено. Сервер: ${result.error}`);
        return;
      }

      const serverProgress: ProgressMap = {
        ...nextProgress,
        [activeItem.id]: result.progress,
      };
      setProgress(serverProgress);
      saveProgress(serverProgress);
      setSaveMessage(result.message);
    });
  }

  function resetQuiz() {
    setAnswers({});
    setSubmittedScore(null);
    setSaveMessage("");
  }

  if (!activeItem) {
    return (
      <section className="mx-auto max-w-7xl px-6 py-10">
        <div className="rounded-lg border border-border/60 bg-card/50 p-6 text-sm text-muted-foreground">
          Для этой роли пока нет материалов.
        </div>
      </section>
    );
  }

  const activeProgress = progress[activeItem.id];
  const activeChecklistNormalized = normalizedTitle(activeChecklistTitle);
  const checklistExists =
    activeChecklistNormalized.length > 0 &&
    activeItem.sections.some(
      (section) => normalizedTitle(section.title) === activeChecklistNormalized,
    );

  return (
    <section className="mx-auto max-w-7xl px-6 py-8">
      <LearningAdmissionPanel
        admission={admission}
        memberName={memberName}
        roleTitle={roleTitle}
        onOpenNext={(moduleId) => selectModule(moduleId)}
      />

      <div className="mt-6 grid gap-6 lg:grid-cols-[0.34fr_0.66fr]">
        <aside className="space-y-4">
        <div className="rounded-lg border border-border/60 bg-card/50 p-5">
          <p className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
            Прогресс роли
          </p>
          <div className="mt-4 grid grid-cols-3 gap-2">
            <Metric
              label="модули"
              value={`${completedCount}/${items.length}`}
            />
            <Metric label="средний" value={`${averageScore}%`} />
            <Metric label="роль" value={roleTitle} compact />
          </div>
          <p className="mt-4 text-[12px] leading-relaxed text-muted-foreground">
            {memberName} · {venueName}
          </p>
        </div>

        <div className="rounded-lg border border-border/60 bg-card/50 p-3">
          <div className="mb-2 flex items-center gap-2 px-2 py-1">
            <BookOpenCheck className="size-4 text-brand" />
            <p className="text-sm font-medium">Материалы</p>
          </div>
          <div className="grid gap-2">
            {items.map((item) => {
              const itemProgress = progress[item.id];
              const active = item.id === activeItem.id;

              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => selectModule(item.id)}
                  className={cn(
                    "rounded-lg border p-3 text-left transition-colors",
                    active
                      ? "border-brand/45 bg-brand/10"
                      : "border-border/55 bg-background/30 hover:bg-card/70",
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="line-clamp-2 text-sm font-medium leading-snug">
                        {item.title}
                      </p>
                      <p className="mt-1 text-[12px] text-muted-foreground">
                        {item.timeLabel} · {item.quiz.length} вопроса
                      </p>
                    </div>
                    {(itemProgress?.bestPercentage ?? 0) >=
                    item.passPercentage ? (
                      <CheckCircle2 className="size-4 shrink-0 text-brand" />
                    ) : (
                      <Circle className="size-4 shrink-0 text-muted-foreground" />
                    )}
                  </div>
                  <Badge
                    variant="outline"
                    className={cn("mt-3", progressClass(item, itemProgress))}
                  >
                    {progressLabel(item, itemProgress)}
                  </Badge>
                </button>
              );
            })}
          </div>
        </div>
        </aside>

        <div className="space-y-6">
        <article className="rounded-lg border border-border/60 bg-card/50 p-5">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline" className="border-brand/30 text-brand">
                  {activeItem.timeLabel}
                </Badge>
                <Badge
                  variant="outline"
                  className={progressClass(activeItem, activeProgress)}
                >
                  {progressLabel(activeItem, activeProgress)}
                </Badge>
              </div>
              <h2 className="mt-4 text-2xl font-medium leading-tight">
                {activeItem.title}
              </h2>
              <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">
                {activeItem.description}
              </p>
              {checklistExists ? (
                <div className="mt-3 inline-flex items-center gap-2 rounded-md border border-brand/30 bg-brand/10 px-3 py-1.5 text-[12px] leading-relaxed text-brand">
                  <ListChecks className="size-3.5" />
                  <span>Фокус смены: {activeChecklistTitle}</span>
                </div>
              ) : null}
            </div>
            {activeProgress ? (
              <div className="rounded-lg border border-border/60 bg-background/35 p-3 text-right">
                <p className="numeric text-2xl font-medium">
                  {activeProgress.bestPercentage}%
                </p>
                <p className="mt-1 text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                  лучший балл
                </p>
              </div>
            ) : null}
          </div>

          {shiftCard ? (
            <div className="mt-5 rounded-lg border border-brand/25 bg-brand/[0.06] p-4">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="text-[10px] uppercase tracking-[0.16em] text-brand">
                    Практика на сегодня
                  </p>
                  <h3 className="mt-1 text-sm font-medium text-foreground">
                    {shiftCard.title}
                  </h3>
                </div>
                <Badge
                  variant="outline"
                  className="w-fit border-brand/30 text-brand"
                >
                  в смену
                </Badge>
              </div>
              <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">
                {shiftCard.reason}
              </p>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <div className="rounded-lg border border-border/45 bg-background/35 p-3">
                  <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                    <Target className="size-3.5 text-brand" />
                    Действие
                  </div>
                  <p className="mt-2 text-sm leading-relaxed text-foreground/85">
                    {shiftCard.action}
                  </p>
                </div>
                <div className="rounded-lg border border-border/45 bg-background/35 p-3">
                  <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                    <MessageSquareText className="size-3.5 text-brand" />
                    В память ресторана
                  </div>
                  <p className="mt-2 text-sm leading-relaxed text-foreground/85">
                    {shiftCard.fieldNote}
                  </p>
                </div>
              </div>
            </div>
          ) : null}

          <div className="mt-6 grid gap-4">
            {activeItem.sections.map((section) => {
              const focused =
                activeChecklistNormalized.length > 0 &&
                normalizedTitle(section.title) === activeChecklistNormalized;

              return (
                <section
                  key={section.title}
                  className={cn(
                    "rounded-lg border p-4 transition-colors",
                    focused
                      ? "border-brand/45 bg-brand/10"
                      : "border-border/45 bg-background/35",
                  )}
                >
                  {focused ? (
                    <div className="mb-3 inline-flex items-center gap-2 rounded-md border border-brand/30 bg-background/35 px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-brand">
                      <ListChecks className="size-3" />
                      Чеклист из задачи
                    </div>
                  ) : null}
                  <h3 className="text-sm font-medium">{section.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    {section.body}
                  </p>
                  {section.bullets?.length ? (
                    <ul className="mt-3 grid gap-2">
                      {section.bullets.map((bullet) => (
                        <li
                          key={bullet}
                          className="flex gap-3 text-sm leading-relaxed text-foreground/85"
                        >
                          <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-brand" />
                          <span>{bullet}</span>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </section>
              );
            })}
          </div>
        </article>

        <article className="rounded-lg border border-border/60 bg-card/50 p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <ListChecks className="size-5 text-brand" />
                <h2 className="text-xl font-medium">Проверка</h2>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                Ответь на вопросы. Проходной балл: {activeItem.passPercentage}%.
              </p>
            </div>
            <span className="rounded-md border border-border/50 bg-background/45 px-2.5 py-1 text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
              {answeredCount}/{activeItem.quiz.length}
            </span>
          </div>

          <div className="mt-5 grid gap-4">
            {activeItem.quiz.map((question, questionIndex) => {
              const selectedAnswer = answers[questionIndex];
              const showResult = submittedScore !== null;
              const answeredCorrectly =
                selectedAnswer === question.correctIndex;

              return (
                <div
                  key={question.id}
                  className="rounded-lg border border-border/45 bg-background/35 p-4"
                >
                  <p className="text-sm font-medium leading-relaxed">
                    {questionIndex + 1}. {question.prompt}
                  </p>
                  <div className="mt-3 grid gap-2">
                    {question.options.map((option, answerIndex) => {
                      const selected = selectedAnswer === answerIndex;
                      const correct = question.correctIndex === answerIndex;
                      const highlighted = showResult && (selected || correct);

                      return (
                        <button
                          key={option}
                          type="button"
                          onClick={() =>
                            selectAnswer(questionIndex, answerIndex)
                          }
                          aria-pressed={selected}
                          className={cn(
                            "flex items-center justify-between gap-3 rounded-lg border px-3 py-2 text-left text-sm transition-colors",
                            selected
                              ? "border-brand/45 bg-brand/10"
                              : "border-border/55 bg-card/35 hover:bg-card/70",
                            highlighted &&
                              correct &&
                              "border-brand/50 bg-brand/10 text-foreground",
                            highlighted &&
                              selected &&
                              !correct &&
                              "border-destructive/40 bg-destructive/10",
                          )}
                        >
                          <span>{option}</span>
                          {selected ? (
                            <CheckCircle2 className="size-4 shrink-0 text-brand" />
                          ) : (
                            <Circle className="size-4 shrink-0 text-muted-foreground" />
                          )}
                        </button>
                      );
                    })}
                  </div>
                  {showResult ? (
                    <div
                      className={cn(
                        "mt-3 rounded-lg border p-3 text-sm leading-relaxed",
                        answeredCorrectly
                          ? "border-brand/30 bg-brand/10 text-brand"
                          : "border-amber-400/25 bg-amber-400/10 text-amber-100",
                      )}
                    >
                      {answeredCorrectly ? "Верно. " : "Разберем. "}
                      {question.explanation}
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>

          <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            {submittedScore ? (
              <div className="flex items-center gap-3 rounded-lg border border-border/60 bg-background/35 p-3">
                {submittedScore.passed ? (
                  <Trophy className="size-5 text-brand" />
                ) : (
                  <RotateCcw className="size-5 text-amber-200" />
                )}
                <div>
                  <p className="text-sm font-medium">
                    {submittedScore.percentage}% · {submittedScore.correct} из{" "}
                    {submittedScore.total}
                  </p>
                  <p className="mt-1 text-[12px] text-muted-foreground">
                    {submittedScore.passed
                      ? "Стандарт подтвержден."
                      : "Нужно повторить материал и пересдать."}
                    {activeProgress?.completedAt
                      ? ` Последняя попытка: ${formatProgressDate(
                          activeProgress.completedAt,
                        )}.`
                      : ""}
                  </p>
                  {saveMessage ? (
                    <p className="mt-1 text-[12px] text-muted-foreground">
                      {saveMessage}
                    </p>
                  ) : null}
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                Выбери ответы на все вопросы, затем заверши проверку.
              </p>
            )}

            <div className="flex flex-wrap gap-2">
              {submittedScore ? (
                <button
                  type="button"
                  onClick={resetQuiz}
                  className="inline-flex h-10 items-center gap-2 rounded-lg border border-border/60 bg-card/50 px-4 text-sm text-foreground transition-colors hover:border-brand/40"
                >
                  <RotateCcw className="size-4" />
                  Пройти еще раз
                </button>
              ) : null}
              <button
                type="button"
                onClick={submitQuiz}
                disabled={!allAnswered || submittedScore !== null}
                className="inline-flex h-10 items-center gap-2 rounded-lg bg-brand px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-brand-hover disabled:pointer-events-none disabled:opacity-50"
              >
                {pending ? "Сохраняем" : "Завершить проверку"}
                <ArrowRight className="size-4" />
              </button>
            </div>
          </div>
        </article>
        </div>
      </div>
    </section>
  );
}

function LearningAdmissionPanel({
  admission,
  memberName,
  roleTitle,
  onOpenNext,
}: {
  admission: TeamLearningAdmission;
  memberName: string;
  roleTitle: string;
  onOpenNext: (moduleId: string) => void;
}) {
  const ready = admission.status === "admitted";
  const nextItem = admission.nextItem;

  return (
    <div className="rounded-lg border border-border/60 bg-card/45 p-5">
      <div className="grid gap-4 lg:grid-cols-[1fr_0.58fr]">
        <div>
          <p className="text-[11px] uppercase tracking-[0.18em] text-brand">
            Допуск к смене
          </p>
          <h2 className="mt-3 text-xl font-medium leading-tight">
            {admission.title}
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
            {admission.detail}
          </p>
          <p className="mt-3 text-[12px] leading-relaxed text-muted-foreground">
            {memberName} · {roleTitle}
          </p>
        </div>

        <div className="rounded-lg border border-brand/25 bg-brand/[0.05] p-4">
          <div className="grid grid-cols-3 gap-2">
            <Metric
              label="обязательные"
              value={`${admission.requiredCompleted}/${admission.requiredCount}`}
            />
            <Metric
              label="все"
              value={`${admission.completedCount}/${admission.totalCount}`}
            />
            <Metric label="средний" value={`${admission.averageBest}%`} />
          </div>
          {nextItem ? (
            <button
              type="button"
              onClick={() => onOpenNext(nextItem.id)}
              className="mt-4 inline-flex h-9 w-full items-center justify-center rounded-lg bg-brand px-3 text-sm font-medium text-primary-foreground transition-colors hover:bg-brand-hover"
            >
              {ready ? "Продолжить обучение" : "Открыть следующий стандарт"}
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  compact = false,
}: {
  label: string;
  value: string;
  compact?: boolean;
}) {
  return (
    <div className="rounded-lg border border-border/50 bg-background/35 p-3">
      <p
        className={cn(
          "font-medium text-foreground",
          compact ? "truncate text-sm" : "numeric text-2xl",
        )}
      >
        {value}
      </p>
      <p className="mt-1 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </p>
    </div>
  );
}
