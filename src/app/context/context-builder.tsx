"use client";

import Link from "next/link";
import { useMemo, useState, useTransition } from "react";
import {
  CheckCircle2,
  Clipboard,
  Loader2,
  RotateCcw,
  Save,
  Search,
  Sparkles,
  Trash2,
} from "lucide-react";
import {
  researchVenueContextAction,
  updateVenueContextAction,
} from "./actions";
import {
  calculateContextCompletion,
  DEMO_CONTEXT_ANSWERS,
  formatContextAnswersForPrompt,
  VENUE_CONTEXT_QUESTIONNAIRE,
  type ContextQuestion,
  type ContextSection,
  type VenueContextAnswers,
} from "@/lib/venues/context-questionnaire";
import type { VenueIntelligenceProfile } from "@/lib/venues/intelligence";

type ContextVenueOption = {
  id: string;
  name: string;
  city: string;
};

export function ContextBuilder({
  initialAnswers,
  venueId,
  venueName,
  venues,
  canPersist,
  sandboxMode,
}: {
  initialAnswers: VenueContextAnswers;
  venueId: string;
  venueName: string;
  venues: ContextVenueOption[];
  canPersist: boolean;
  sandboxMode: boolean;
}) {
  const [answers, setAnswers] = useState<VenueContextAnswers>(
    Object.keys(initialAnswers).length ? initialAnswers : DEMO_CONTEXT_ANSWERS,
  );
  const [copied, setCopied] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [researchMessage, setResearchMessage] = useState<string | null>(null);
  const [researchError, setResearchError] = useState<string | null>(null);
  const [researchProfile, setResearchProfile] =
    useState<VenueIntelligenceProfile | null>(null);
  const [researchDiagnostics, setResearchDiagnostics] = useState<string[]>([]);
  const [pending, startTransition] = useTransition();
  const [researchPending, startResearchTransition] = useTransition();

  const completion = useMemo(
    () => calculateContextCompletion(answers),
    [answers],
  );
  const prompt = useMemo(
    () => formatContextAnswersForPrompt(answers),
    [answers],
  );

  const setAnswer = (id: string, value: string | string[]) => {
    setAnswers((current) => ({ ...current, [id]: value }));
    setCopied(false);
    setSaveMessage(null);
    setSaveError(null);
    setResearchMessage(null);
    setResearchError(null);
  };

  const copyPrompt = async () => {
    if (!prompt.trim()) return;
    await navigator.clipboard.writeText(prompt);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  const saveContext = () => {
    setSaveMessage(null);
    setSaveError(null);
    startTransition(async () => {
      const result = await updateVenueContextAction({ venueId, answers });
      if (!result.ok) {
        setSaveError(result.error);
        return;
      }

      setAnswers(result.answers);
      setSaveMessage(
        result.mode === "sandbox"
          ? "Тестовый режим: контекст обновлен локально, без записи."
          : "Контекст сохранен в профиль заведения.",
      );
    });
  };

  const researchContext = () => {
    setResearchMessage(null);
    setResearchError(null);
    setResearchDiagnostics([]);
    startResearchTransition(async () => {
      const result = await researchVenueContextAction({ venueId, answers });
      if (!result.ok) {
        setResearchError(result.error);
        return;
      }

      setAnswers(result.answers);
      setResearchProfile(result.profile);
      setResearchDiagnostics(result.diagnostics);
      setResearchMessage(
        result.mode === "sandbox"
          ? `${result.summary} Профиль показан в тестовом режиме без записи в базу.`
          : `${result.summary} Анкета и профиль заведения сохранены.`,
      );
    });
  };

  return (
    <section className="border-b border-border/40">
      <div className="mx-auto grid max-w-7xl gap-8 px-6 py-12 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="lg:sticky lg:top-24 lg:self-start">
          <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
            Память заведения
          </p>
          <h1 className="mt-4 text-balance text-[clamp(2rem,4vw,3.3rem)] font-medium leading-[1.04]">
            Анкета, которая делает советника ресторанным.
          </h1>
          <p className="mt-5 max-w-xl text-sm leading-relaxed text-muted-foreground">
            Receptor должен знать формат, экономику, команду, системы и красные
            линии клиента до того, как начинает советовать. Анкета и ресерч
            становятся памятью заведения для советника, брифов и задач.
          </p>

          <div className="mt-6 rounded-lg border border-border/60 bg-card/50 p-4">
            <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              Заведение
            </p>
            <h2 className="mt-2 text-lg font-medium">{venueName}</h2>
            {venues.length > 1 ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {venues.map((venue) => (
                  <Link
                    key={venue.id}
                    href={`/context?venueId=${encodeURIComponent(venue.id)}`}
                    className={
                      "rounded-md border px-2.5 py-1 text-xs transition-colors " +
                      (venue.id === venueId
                        ? "border-brand/50 bg-brand/10 text-brand"
                        : "border-border/60 bg-background/50 text-muted-foreground hover:text-foreground")
                    }
                  >
                    {venue.name}
                  </Link>
                ))}
              </div>
            ) : null}
            {!canPersist ? (
              <Link
                href="/onboarding?new=1"
                className="mt-3 inline-block text-xs text-brand underline-offset-4 hover:underline"
              >
                Добавить заведение
              </Link>
            ) : null}
          </div>

          <div className="mt-8 grid grid-cols-2 gap-3">
            <Metric label="Заполнено" value={`${completion.percentage}%`} />
            <Metric
              label="Обязательные"
              value={`${completion.requiredAnswered}/${completion.requiredTotal}`}
            />
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setAnswers(DEMO_CONTEXT_ANSWERS)}
              className="inline-flex h-9 items-center gap-2 rounded-lg border border-border/60 bg-card/50 px-3 text-xs text-foreground transition-colors hover:border-brand/40"
            >
              <RotateCcw className="size-3.5" /> Demo
            </button>
            <button
              type="button"
              onClick={() => setAnswers({})}
              className="inline-flex h-9 items-center gap-2 rounded-lg border border-border/60 bg-card/50 px-3 text-xs text-muted-foreground transition-colors hover:text-foreground"
            >
              <Trash2 className="size-3.5" /> Очистить
            </button>
            <button
              type="button"
              onClick={copyPrompt}
              className="inline-flex h-9 items-center gap-2 rounded-lg bg-brand px-3 text-xs font-medium text-primary-foreground transition-colors hover:bg-brand-hover disabled:opacity-50"
              disabled={!prompt.trim()}
            >
              {copied ? (
                <CheckCircle2 className="size-3.5" />
              ) : (
                <Clipboard className="size-3.5" />
              )}
              {copied ? "Скопировано" : "Скопировать контекст"}
            </button>
            <button
              type="button"
              onClick={saveContext}
              disabled={!canPersist || pending}
              className="inline-flex h-9 items-center gap-2 rounded-lg border border-brand/40 bg-brand/10 px-3 text-xs font-medium text-brand transition-colors hover:bg-brand/15 disabled:opacity-50"
            >
              {pending ? (
                <Loader2 className="size-3.5 animate-spin" />
              ) : (
                <Save className="size-3.5" />
              )}
              Сохранить
            </button>
            <button
              type="button"
              onClick={researchContext}
              disabled={!canPersist || researchPending}
              className="inline-flex h-9 items-center gap-2 rounded-lg border border-border/60 bg-card/50 px-3 text-xs font-medium text-foreground transition-colors hover:border-brand/40 disabled:opacity-50"
            >
              {researchPending ? (
                <Loader2 className="size-3.5 animate-spin" />
              ) : (
                <Search className="size-3.5" />
              )}
              Дополнить ресерчем
            </button>
          </div>

          {saveMessage ? (
            <div className="mt-5 rounded-lg border border-brand/25 bg-brand/10 p-4 text-xs leading-relaxed text-foreground/85">
              {saveMessage}
            </div>
          ) : null}
          {saveError ? (
            <div className="mt-5 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-xs leading-relaxed text-destructive">
              {saveError}
            </div>
          ) : null}
          {researchMessage ? (
            <div className="mt-5 rounded-lg border border-brand/25 bg-brand/10 p-4 text-xs leading-relaxed text-foreground/85">
              {researchMessage}
            </div>
          ) : null}
          {researchError ? (
            <div className="mt-5 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-xs leading-relaxed text-destructive">
              {researchError}
            </div>
          ) : null}
          {sandboxMode ? (
            <div className="mt-5 rounded-lg border border-border/60 bg-card/50 p-4 text-xs leading-relaxed text-muted-foreground">
              Тестовый режим: изменения показываются в интерфейсе без записи в
              базу.
            </div>
          ) : null}

          {completion.missingRequired.length > 0 ? (
            <div className="mt-5 rounded-lg border border-[color:var(--pro)]/30 bg-[color:var(--pro)]/8 p-4 text-xs leading-relaxed text-muted-foreground">
              Не заполнены обязательные поля:{" "}
              {completion.missingRequired.join(", ")}.
            </div>
          ) : (
            <div className="mt-5 rounded-lg border border-brand/25 bg-brand/10 p-4 text-xs leading-relaxed text-foreground/85">
              Базовый контекст готов для советника, ежедневного брифа и задач
              команды.
            </div>
          )}

          <div className="mt-6 rounded-lg border border-border/60 bg-card/50 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-medium">
              <Sparkles className="size-4 text-brand" /> Память для советника
            </div>
            <pre className="max-h-[360px] overflow-auto whitespace-pre-wrap rounded-md bg-background/60 p-3 text-xs leading-relaxed text-muted-foreground">
              {prompt || "Заполните анкету, чтобы собрать контекст."}
            </pre>
          </div>

          {researchProfile ? (
            <ResearchProfileCard
              diagnostics={researchDiagnostics}
              profile={researchProfile}
            />
          ) : null}
        </div>

        <div className="space-y-4">
          {VENUE_CONTEXT_QUESTIONNAIRE.map((section) => (
            <QuestionSection
              key={section.id}
              section={section}
              answers={answers}
              onAnswer={setAnswer}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

function ResearchProfileCard({
  profile,
  diagnostics,
}: {
  profile: VenueIntelligenceProfile;
  diagnostics: string[];
}) {
  const focusItems = [
    ...profile.recommendedFocus.slice(0, 3),
    ...profile.operatingRisks.slice(0, 2),
  ].slice(0, 5);

  return (
    <div className="mt-6 rounded-lg border border-brand/25 bg-brand/[0.04] p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.18em] text-brand">
            Ресерч заведения
          </p>
          <h2 className="mt-2 text-base font-medium">{profile.format}</h2>
        </div>
        <span className="rounded-md border border-brand/30 bg-brand/10 px-2 py-1 text-[10px] uppercase tracking-[0.14em] text-brand">
          {profile.researchStatus}
        </span>
      </div>
      <p className="mt-3 text-sm leading-relaxed text-foreground/85">
        {profile.positioning}
      </p>
      {focusItems.length > 0 ? (
        <ul className="mt-4 space-y-2 text-xs leading-relaxed text-muted-foreground">
          {focusItems.map((item) => (
            <li key={item} className="flex gap-2">
              <span className="mt-2 size-1 shrink-0 rounded-full bg-brand/70" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      ) : null}
      {diagnostics.length > 0 ? (
        <p className="mt-4 border-t border-border/35 pt-3 text-[11px] leading-relaxed text-muted-foreground/75">
          {diagnostics.join(" · ")}
        </p>
      ) : null}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border/60 bg-card/50 p-4">
      <p className="numeric text-3xl font-medium text-brand">{value}</p>
      <p className="mt-1 text-xs text-muted-foreground">{label}</p>
    </div>
  );
}

function QuestionSection({
  section,
  answers,
  onAnswer,
}: {
  section: ContextSection;
  answers: VenueContextAnswers;
  onAnswer: (id: string, value: string | string[]) => void;
}) {
  return (
    <section className="rounded-lg border border-border/60 bg-card/50 p-5">
      <div className="mb-5">
        <h2 className="text-lg font-medium">{section.title}</h2>
        <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
          {section.description}
        </p>
      </div>
      <div className="grid gap-4">
        {section.questions.map((question) => (
          <QuestionControl
            key={question.id}
            question={question}
            value={answers[question.id]}
            onChange={(value) => onAnswer(question.id, value)}
          />
        ))}
      </div>
    </section>
  );
}

function QuestionControl({
  question,
  value,
  onChange,
}: {
  question: ContextQuestion;
  value: string | string[] | undefined;
  onChange: (value: string | string[]) => void;
}) {
  const textValue = Array.isArray(value) ? value.join("\n") : (value ?? "");
  const arrayValue = Array.isArray(value)
    ? value
    : value
      ? value
          .split("\n")
          .map((item) => item.trim())
          .filter(Boolean)
      : [];

  return (
    <label className="grid gap-2">
      <span className="flex items-center gap-2 text-sm font-medium">
        {question.label}
        {question.required ? <span className="text-brand">*</span> : null}
      </span>
      <span className="text-xs leading-relaxed text-muted-foreground">
        {question.prompt}
      </span>

      {question.type === "textarea" ? (
        <textarea
          value={textValue}
          onChange={(event) => onChange(event.target.value)}
          placeholder={question.placeholder}
          rows={4}
          className="input-base min-h-28 resize-y leading-relaxed"
        />
      ) : question.type === "text" ? (
        <input
          value={textValue}
          onChange={(event) => onChange(event.target.value)}
          placeholder={question.placeholder}
          className="input-base"
        />
      ) : question.type === "select" && question.options ? (
        <select
          value={textValue}
          onChange={(event) => onChange(event.target.value)}
          className="input-base"
        >
          <option value="">Выберите</option>
          {question.options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      ) : question.type === "multiselect" && question.options ? (
        <ChipGroup
          options={question.options}
          value={arrayValue}
          onChange={onChange}
        />
      ) : (
        <textarea
          value={arrayValue.join("\n")}
          onChange={(event) =>
            onChange(
              event.target.value
                .split("\n")
                .map((item) => item.trim())
                .filter(Boolean),
            )
          }
          placeholder="Каждый пункт с новой строки"
          rows={3}
          className="input-base min-h-24 resize-y leading-relaxed"
        />
      )}
    </label>
  );
}

function ChipGroup({
  options,
  value,
  onChange,
}: {
  options: string[];
  value: string[];
  onChange: (value: string[]) => void;
}) {
  const toggle = (option: string) => {
    onChange(
      value.includes(option)
        ? value.filter((item) => item !== option)
        : [...value, option],
    );
  };

  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => {
        const active = value.includes(option);
        return (
          <button
            key={option}
            type="button"
            onClick={() => toggle(option)}
            className={
              "rounded-md border px-3 py-1.5 text-xs transition-colors " +
              (active
                ? "border-brand/50 bg-brand/10 text-brand"
                : "border-border/60 bg-background/50 text-muted-foreground hover:text-foreground")
            }
          >
            {option}
          </button>
        );
      })}
    </div>
  );
}
