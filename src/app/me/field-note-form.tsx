"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ListPlus, Loader2, Mic2, SendHorizontal } from "lucide-react";
import { submitFieldNoteAction, type OwnTaskStatusResult } from "./actions";
import {
  FIELD_NOTE_TEMPLATES,
  hasMeaningfulFieldNoteBody,
} from "@/lib/team/field-note-input";

function resultText(result: OwnTaskStatusResult): string {
  return result.ok ? result.message : result.error;
}

export function FieldNoteForm() {
  const router = useRouter();
  const [body, setBody] = useState("");
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const canSubmit = hasMeaningfulFieldNoteBody(body) && !pending;

  function addTemplate(text: string) {
    setMessage(null);
    setBody((current) => {
      const value = current.trimEnd();
      return value ? `${value}\n${text}` : text;
    });
  }

  return (
    <form
      className="rounded-lg border border-border/60 bg-card/50 p-5"
      onSubmit={async (event) => {
        event.preventDefault();
        if (!canSubmit) return;

        setPending(true);
        setMessage(null);
        try {
          const result = await submitFieldNoteAction({ body });
          setMessage(resultText(result));
          if (result.ok) {
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
            <h2 className="text-xl font-medium">Что было на смене</h2>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            Гости, стоп-лист, конфликт, событие, команда, продажи. Коротко и по
            делу.
          </p>
        </div>
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

      <textarea
        value={body}
        onChange={(event) => setBody(event.target.value)}
        rows={4}
        maxLength={1500}
        placeholder="Например: гости спрашивали безалкогольный коктейль, к 21:00 закончилась мята, кухня задержала два стола..."
        className="mt-4 min-h-28 w-full resize-y rounded-lg border border-border/60 bg-background/45 px-3 py-3 text-sm leading-relaxed text-foreground outline-none transition-colors placeholder:text-muted-foreground/65 focus:border-brand/45"
      />

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
          Сохранить
        </button>
      </div>

      {message ? (
        <p className="mt-3 text-[12px] leading-relaxed text-muted-foreground">
          {message}
        </p>
      ) : null}
    </form>
  );
}
