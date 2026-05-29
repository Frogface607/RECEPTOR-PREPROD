"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { Send, Sparkles, X, Wrench } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  type ChatEvent,
  type ChatMessage,
  SUGGESTED_PROMPTS,
} from "./chat-types";

function genId() {
  return Math.random().toString(36).slice(2, 9);
}

export function ChatDrawer({
  venueId,
  venueName,
}: {
  venueId: string;
  venueName: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const search = useSearchParams();

  const isOpen = search?.get("chat") === "1";
  const setOpen = useCallback(
    (open: boolean) => {
      const sp = new URLSearchParams(search?.toString() ?? "");
      if (open) sp.set("chat", "1");
      else sp.delete("chat");
      router.replace(`${pathname}?${sp.toString()}`, { scroll: false });
    },
    [router, pathname, search],
  );

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || busy) return;

      const userMsg: ChatMessage = {
        role: "user",
        id: genId(),
        text: trimmed,
      };
      const assistantId = genId();
      const assistantMsg: ChatMessage = {
        role: "assistant",
        id: assistantId,
        text: "",
        toolCalls: [],
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setInput("");
      setBusy(true);

      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ venueId, message: trimmed }),
        });

        if (!res.body) throw new Error("no stream body");
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        for (;;) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          let nlIdx;
          while ((nlIdx = buffer.indexOf("\n")) >= 0) {
            const raw = buffer.slice(0, nlIdx).trim();
            buffer = buffer.slice(nlIdx + 1);
            if (!raw) continue;
            const event = JSON.parse(raw) as ChatEvent;

            setMessages((prev) =>
              prev.map((m) => {
                if (m.id !== assistantId || m.role !== "assistant") return m;
                if (event.type === "tool") {
                  return {
                    ...m,
                    toolCalls: [
                      ...m.toolCalls,
                      { tool: event.tool, input: event.input },
                    ],
                  };
                }
                if (event.type === "text") {
                  return { ...m, text: event.text };
                }
                if (event.type === "done") {
                  return { ...m, isStreaming: false };
                }
                if (event.type === "error") {
                  return {
                    ...m,
                    text: `Ошибка: ${event.message}`,
                    isStreaming: false,
                  };
                }
                return m;
              }),
            );
          }
        }
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId && m.role === "assistant"
              ? {
                  ...m,
                  text: `Ошибка сети: ${
                    err instanceof Error ? err.message : "unknown"
                  }`,
                  isStreaming: false,
                }
              : m,
          ),
        );
      } finally {
        setBusy(false);
      }
    },
    [busy, venueId],
  );

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    void send(input);
  };

  const hasConversation = messages.length > 0;

  return (
    <Sheet open={isOpen} onOpenChange={setOpen}>
      <SheetContent
        side="right"
        className="flex w-full flex-col gap-0 border-l border-border/60 bg-background p-0 sm:max-w-[480px]"
      >
        <SheetHeader className="border-b border-border/40 px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-lg bg-brand/15 text-brand">
              <Sparkles className="size-4" />
            </div>
            <div className="flex flex-1 flex-col">
              <SheetTitle className="text-[15px] font-medium tracking-tight">
                Receptor
              </SheetTitle>
              <span className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
                {venueName} · live data
              </span>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              aria-label="Закрыть чат"
            >
              <X className="size-4" />
            </button>
          </div>
        </SheetHeader>

        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto px-5 py-6 space-y-6"
        >
          {!hasConversation ? (
            <EmptyState onPick={send} />
          ) : (
            messages.map((m) => <MessageBubble key={m.id} message={m} />)
          )}
        </div>

        <form
          onSubmit={handleSubmit}
          className="border-t border-border/40 bg-background px-5 py-4"
        >
          <div className="flex items-end gap-2 rounded-xl border border-border/60 bg-card/80 p-2 focus-within:border-brand/50">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void send(input);
                }
              }}
              rows={1}
              placeholder="Спроси про выручку, блюда, смены…"
              disabled={busy}
              className="min-h-[36px] max-h-32 flex-1 resize-none bg-transparent px-2 py-1.5 text-sm text-foreground placeholder:text-muted-foreground/70 focus:outline-none disabled:opacity-60"
            />
            <button
              type="submit"
              disabled={busy || !input.trim()}
              className="inline-flex items-center justify-center rounded-lg bg-brand p-2 text-primary-foreground transition-colors hover:bg-brand-hover disabled:opacity-40"
              aria-label="Отправить"
            >
              <Send className="size-4" />
            </button>
          </div>
          <p className="mt-2 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            Enter — отправить · Shift+Enter — новая строка
          </p>
        </form>
      </SheetContent>
    </Sheet>
  );
}

function EmptyState({ onPick }: { onPick: (text: string) => void }) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
          Что я умею
        </p>
        <h3 className="mt-2 font-display text-[28px] italic leading-tight text-foreground">
          Спроси по-человечески — отвечу цифрами.
        </h3>
        <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">
          Receptor читает выручку, блюда, смены и категории прямо из iiko и
          отвечает на конкретный вопрос. Без отчётов, без «выгрузить-открыть».
        </p>
      </div>

      <div>
        <p className="mb-3 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
          Попробуй
        </p>
        <div className="flex flex-col gap-2">
          {SUGGESTED_PROMPTS.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => onPick(p)}
              className="group rounded-lg border border-border/60 bg-card/60 px-3.5 py-3 text-left text-sm text-foreground/85 transition-colors hover:border-brand/40 hover:bg-card hover:text-foreground"
            >
              {p}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-xl bg-muted px-3.5 py-2.5 text-[14px] text-foreground">
          {message.text}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-[11px] uppercase tracking-[0.18em] text-brand">
        Receptor
      </p>
      {message.toolCalls.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {message.toolCalls.map((tc, i) => (
            <span
              key={`${tc.tool}-${i}`}
              className="inline-flex items-center gap-1.5 rounded-md border border-border/60 bg-card/60 px-2 py-1 font-mono text-[10px] text-muted-foreground"
            >
              <Wrench className="size-3" />
              {tc.tool}
            </span>
          ))}
        </div>
      ) : null}
      {message.text ? (
        <div className="whitespace-pre-wrap text-[14px] leading-relaxed text-foreground/90">
          {message.text}
        </div>
      ) : null}
      {message.isStreaming ? (
        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <span className="size-1.5 animate-pulse rounded-full bg-brand" />
          собираю данные…
        </div>
      ) : null}
    </div>
  );
}
