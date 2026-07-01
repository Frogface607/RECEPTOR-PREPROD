"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  CheckCircle2,
  Circle,
  ListPlus,
  Loader2,
  Mic2,
  SendHorizontal,
} from "lucide-react";
import { submitFieldNoteAction, type OwnTaskStatusResult } from "./actions";
import {
  FIELD_NOTE_CLOSED_LOOP_COPY,
  FIELD_NOTE_MEMORY_LINK_COPY,
  FIELD_NOTE_MEMORY_PROMPTS,
  FIELD_NOTE_SAVED_MEMORY_COPY,
  FIELD_NOTE_TEMPLATES,
  fieldNoteReadinessHint,
  getFieldNoteReadiness,
  hasMeaningfulFieldNoteBody,
  isFieldNoteClosedLearningAdoptionMessage,
} from "@/lib/team/field-note-input";

type SpeechRecognitionAlternativeLike = {
  transcript: string;
};

type SpeechRecognitionResultLike = {
  isFinal: boolean;
  readonly length: number;
  [index: number]: SpeechRecognitionAlternativeLike;
};

type SpeechRecognitionResultListLike = {
  readonly length: number;
  [index: number]: SpeechRecognitionResultLike;
};

type SpeechRecognitionResultEventLike = Event & {
  resultIndex: number;
  results: SpeechRecognitionResultListLike;
};

type SpeechRecognitionErrorEventLike = Event & {
  error?: string;
};

type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: SpeechRecognitionResultEventLike) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEventLike) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

type SpeechRecognitionConstructorLike = new () => SpeechRecognitionLike;

type SpeechWindow = Window & {
  SpeechRecognition?: SpeechRecognitionConstructorLike;
  webkitSpeechRecognition?: SpeechRecognitionConstructorLike;
};

function resultText(result: OwnTaskStatusResult): string {
  return result.ok ? result.message : result.error;
}

export function FieldNoteForm() {
  const router = useRouter();
  const [body, setBody] = useState("");
  const [pending, setPending] = useState(false);
  const [listening, setListening] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [savedToMemory, setSavedToMemory] = useState(false);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);

  const readiness = getFieldNoteReadiness(body);
  const readinessHint = fieldNoteReadinessHint(readiness);
  const canSubmit = hasMeaningfulFieldNoteBody(body) && !pending;
  const closedLearningLoop = isFieldNoteClosedLearningAdoptionMessage(message);
  const savedMemoryCopy = closedLearningLoop
    ? FIELD_NOTE_CLOSED_LOOP_COPY
    : FIELD_NOTE_SAVED_MEMORY_COPY;

  useEffect(() => {
    const url = new URL(window.location.href);
    const handoffTemplate = url.searchParams.get("fieldNoteTemplate")?.trim();
    if (!handoffTemplate) return;

    const frame = window.requestAnimationFrame(() => {
      setBody((current) =>
        current.trim() ? current : handoffTemplate.slice(0, 1500),
      );
      setMessage(
        "Шаблон из обучения добавлен. Допишите реальные факты смены вместо многоточий.",
      );
    });
    url.searchParams.delete("fieldNoteTemplate");
    window.history.replaceState(
      null,
      "",
      `${url.pathname}${url.search}${url.hash}`,
    );
    return () => window.cancelAnimationFrame(frame);
  }, []);

  useEffect(() => {
    return () => {
      recognitionRef.current?.stop();
      recognitionRef.current = null;
    };
  }, []);

  function addTemplate(text: string) {
    setMessage(null);
    setSavedToMemory(false);
    setBody((current) => {
      const value = current.trimEnd();
      return value ? `${value}\n${text}` : text;
    });
  }

  function appendTranscript(value: string) {
    const transcript = value.trim();
    if (!transcript) return;

    setSavedToMemory(false);
    setBody((current) => {
      const trimmed = current.trimEnd();
      return trimmed ? `${trimmed} ${transcript}` : transcript;
    });
  }

  function stopDictation() {
    recognitionRef.current?.stop();
    recognitionRef.current = null;
    setListening(false);
  }

  function startDictation() {
    if (listening) {
      stopDictation();
      return;
    }

    const speechWindow = window as SpeechWindow;
    const Recognition =
      speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;

    if (!Recognition) {
      setMessage(
        "Диктовка недоступна в этом браузере. Можно написать текстом.",
      );
      return;
    }

    const recognition = new Recognition();
    recognition.lang = "ru-RU";
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      let transcript = "";
      for (
        let index = event.resultIndex;
        index < event.results.length;
        index += 1
      ) {
        const result = event.results[index];
        if (result?.isFinal) transcript += ` ${result[0]?.transcript ?? ""}`;
      }
      appendTranscript(transcript);
    };
    recognition.onerror = (event) => {
      const detail = event.error ? ` (${event.error})` : "";
      setMessage(
        `Не удалось распознать голос${detail}. Можно сохранить текстом.`,
      );
      setListening(false);
    };
    recognition.onend = () => {
      setListening(false);
      recognitionRef.current = null;
    };

    recognitionRef.current = recognition;
    setMessage(null);
    setListening(true);
    try {
      recognition.start();
    } catch {
      recognitionRef.current = null;
      setListening(false);
      setMessage("Не удалось включить диктовку. Можно сохранить текстом.");
    }
  }

  return (
    <form
      id="shift-summary"
      className="scroll-mt-24 rounded-lg border border-border/60 bg-card/50 p-5"
      onSubmit={async (event) => {
        event.preventDefault();
        if (!canSubmit) return;

        setPending(true);
        setMessage(null);
        setSavedToMemory(false);
        try {
          const result = await submitFieldNoteAction({ body });
          setMessage(resultText(result));
          if (result.ok) {
            setSavedToMemory(true);
            setBody("");
            router.refresh();
          }
        } finally {
          setPending(false);
        }
      }}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Mic2 className="size-4 text-brand" />
            <h2 className="text-xl font-medium">Итог смены</h2>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            За 90 секунд: что случилось, почему это важно, что проверить утром
            и что сказать на брифе.
          </p>
          <div className="mt-3 max-w-xl rounded-lg border border-brand/25 bg-brand/10 p-3">
            <p className="text-[10px] uppercase tracking-[0.16em] text-brand">
              {FIELD_NOTE_MEMORY_LINK_COPY.label}
            </p>
            <p className="mt-1 text-sm font-medium text-foreground">
              {FIELD_NOTE_MEMORY_LINK_COPY.title}
            </p>
            <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
              {FIELD_NOTE_MEMORY_LINK_COPY.detail}
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={startDictation}
          className={`inline-flex h-9 shrink-0 items-center gap-2 rounded-lg border px-3 text-xs font-medium transition-colors ${
            listening
              ? "border-brand/45 bg-brand/15 text-brand"
              : "border-border/60 bg-background/40 text-muted-foreground hover:border-brand/40 hover:text-foreground"
          }`}
        >
          <Mic2 className="size-3.5" />
          {listening ? "Остановить" : "Надиктовать"}
        </button>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {FIELD_NOTE_TEMPLATES.map((template) => (
          <button
            key={template.label}
            type="button"
            onClick={() => addTemplate(template.text)}
            className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-border/55 bg-background/40 px-2.5 text-[12px] text-muted-foreground transition-colors hover:border-brand/40 hover:text-foreground"
          >
            <ListPlus className="size-3.5 text-brand" />
            {template.label}
          </button>
        ))}
      </div>

      <div className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        {FIELD_NOTE_MEMORY_PROMPTS.map((prompt) => (
          <div
            key={prompt.label}
            className="rounded-lg border border-border/50 bg-background/30 p-3"
          >
            <p className="text-[10px] uppercase tracking-[0.16em] text-brand">
              {prompt.label}
            </p>
            <p className="mt-1 text-[12px] leading-relaxed text-foreground/85">
              {prompt.hint}
            </p>
            <p className="mt-1 line-clamp-2 text-[11px] leading-relaxed text-muted-foreground">
              {prompt.example}
            </p>
          </div>
        ))}
      </div>

      <textarea
        value={body}
        onChange={(event) => {
          setSavedToMemory(false);
          setBody(event.target.value);
        }}
        rows={4}
        maxLength={1500}
        placeholder="Например: из-за ливня отменили три брони, к 21:00 закончилась мята, гости спрашивали безалкогольные коктейли. Утром проверить стоп-лист и дать залу замену для брифа..."
        className="mt-4 min-h-28 w-full resize-y rounded-lg border border-border/60 bg-background/45 px-3 py-3 text-sm leading-relaxed text-foreground outline-none transition-colors placeholder:text-muted-foreground/65 focus:border-brand/45"
      />

      <div className="mt-3 flex flex-wrap gap-2">
        {[
          { label: "Факт", done: readiness.hasFact },
          { label: "Контекст", done: readiness.hasContext },
          { label: "Когда/сколько", done: readiness.hasScale },
          { label: "Что проверить", done: readiness.hasAction },
        ].map((item) => (
          <span
            key={item.label}
            className={`inline-flex h-7 items-center gap-1.5 rounded-lg border px-2.5 text-[11px] ${
              item.done
                ? "border-brand/35 bg-brand/10 text-brand"
                : "border-border/55 bg-background/35 text-muted-foreground"
            }`}
          >
            {item.done ? (
              <CheckCircle2 className="size-3.5" />
            ) : (
              <Circle className="size-3.5" />
            )}
            {item.label}
          </span>
        ))}
      </div>

      <p
        className={`mt-3 rounded-lg border px-3 py-2 text-[12px] leading-relaxed ${
          readiness.score === 3
            ? "border-brand/35 bg-brand/10 text-brand"
            : "border-border/55 bg-background/30 text-muted-foreground"
        }`}
      >
        {readinessHint}
      </p>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
          {body.trim().length}/1500
        </p>
        <button
          type="submit"
          disabled={!canSubmit}
          className="inline-flex h-9 items-center gap-2 rounded-lg bg-brand px-3 text-xs font-medium text-primary-foreground transition-colors hover:bg-brand-hover disabled:cursor-not-allowed disabled:opacity-50"
        >
          {pending ? (
            <Loader2 className="size-3.5 animate-spin" />
          ) : (
            <SendHorizontal className="size-3.5" />
          )}
          {FIELD_NOTE_MEMORY_LINK_COPY.action}
        </button>
      </div>

      {message ? (
        <p className="mt-3 text-[12px] leading-relaxed text-muted-foreground">
          {message}
        </p>
      ) : null}

      {savedToMemory ? (
        <div className="mt-3 rounded-lg border border-brand/35 bg-brand/10 p-3">
          <div className="flex items-start gap-2">
            <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-brand" />
            <div>
              {closedLearningLoop ? (
                <p className="mb-1 text-[10px] uppercase tracking-[0.16em] text-brand">
                  Петля закрыта
                </p>
              ) : null}
              <p className="text-sm font-medium text-foreground">
                {savedMemoryCopy.title}
              </p>
              <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
                {savedMemoryCopy.detail}
              </p>
            </div>
          </div>
        </div>
      ) : null}
    </form>
  );
}
