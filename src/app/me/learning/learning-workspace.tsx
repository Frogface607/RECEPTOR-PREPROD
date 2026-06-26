"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  BookOpenCheck,
  CheckCircle2,
  Circle,
  ListChecks,
  RotateCcw,
  Trophy,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  calculateLearningScore,
  type TeamLearningItem,
  type TeamLearningScore,
} from "@/lib/team/team-learning";

type StoredProgress = {
  bestPercentage: number;
  lastPercentage: number;
  correct: number;
  total: number;
  passed: boolean;
  answers: number[];
  completedAt: string;
};

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

function progressLabel(item: TeamLearningItem, progress?: StoredProgress): string {
  if (!progress) return "не пройдено";
  if (progress.bestPercentage >= item.passPercentage) return "сдано";
  return "повторить";
}

function progressClass(item: TeamLearningItem, progress?: StoredProgress): string {
  if (!progress) return "border-border bg-muted/35 text-muted-foreground";
  if (progress.bestPercentage >= item.passPercentage) {
    return "border-brand/30 bg-brand/10 text-brand";
  }
  return "border-amber-400/30 bg-amber-400/10 text-amber-200";
}

export function LearningWorkspace({
  items,
  initialModuleId,
  memberName,
  roleTitle,
  venueName,
}: {
  items: TeamLearningItem[];
  initialModuleId: string;
  memberName: string;
  roleTitle: string;
  venueName: string;
}) {
  const [activeItemId, setActiveItemId] = useState(initialModuleId);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [submittedScore, setSubmittedScore] =
    useState<TeamLearningScore | null>(null);
  const [progress, setProgress] = useState<ProgressMap>({});

  useEffect(() => {
    setProgress(loadProgress());
  }, []);

  const activeItem = useMemo(
    () => items.find((item) => item.id === activeItemId) ?? items[0],
    [activeItemId, items],
  );

  useEffect(() => {
    if (!activeItem) return;
    const nextUrl = `/me/learning?module=${encodeURIComponent(activeItem.id)}`;
    window.history.replaceState(null, "", nextUrl);
    setAnswers({});
    setSubmittedScore(null);
  }, [activeItem?.id, activeItem]);

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

  function selectAnswer(questionIndex: number, answerIndex: number) {
    if (submittedScore) return;
    setAnswers((current) => ({
      ...current,
      [questionIndex]: answerIndex,
    }));
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
        bestPercentage: Math.max(previous?.bestPercentage ?? 0, score.percentage),
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
  }

  function resetQuiz() {
    setAnswers({});
    setSubmittedScore(null);
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

  return (
    <section className="mx-auto grid max-w-7xl gap-6 px-6 py-8 lg:grid-cols-[0.34fr_0.66fr]">
      <aside className="space-y-4">
        <div className="rounded-lg border border-border/60 bg-card/50 p-5">
          <p className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
            Прогресс роли
          </p>
          <div className="mt-4 grid grid-cols-3 gap-2">
            <Metric label="модули" value={`${completedCount}/${items.length}`} />
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
                  onClick={() => setActiveItemId(item.id)}
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
                    {(itemProgress?.bestPercentage ?? 0) >= item.passPercentage ? (
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

          <div className="mt-6 grid gap-4">
            {activeItem.sections.map((section) => (
              <section
                key={section.title}
                className="rounded-lg border border-border/45 bg-background/35 p-4"
              >
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
            ))}
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
                Завершить проверку
                <ArrowRight className="size-4" />
              </button>
            </div>
          </div>
        </article>
      </div>
    </section>
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
