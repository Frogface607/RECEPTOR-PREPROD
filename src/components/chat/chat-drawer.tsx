"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { Bot, Database, Send, X, Wrench } from "lucide-react";
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
        showCloseButton={false}
        className="flex w-full flex-col gap-0 border-l border-border/60 bg-background p-0 data-[side=right]:sm:w-[min(100vw,820px)] data-[side=right]:sm:max-w-[820px]"
      >
        <SheetHeader className="border-b border-border/40 px-5 py-4 sm:px-7">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-lg border border-border/60 bg-card/50 text-brand">
              <Bot className="size-5" />
            </div>
            <div className="flex flex-1 flex-col">
              <SheetTitle className="text-[17px] font-medium tracking-[-0.01em]">
                Copilot Receptor
              </SheetTitle>
              <span className="mt-0.5 text-[12px] text-muted-foreground">
                {venueName} · отвечает по выручке, блюдам, сменам и категориям
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
          className="flex-1 space-y-6 overflow-y-auto px-5 py-6 sm:px-7"
        >
          {!hasConversation ? (
            <EmptyState onPick={send} />
          ) : (
            messages.map((m) => <MessageBubble key={m.id} message={m} />)
          )}
        </div>

        <form
          onSubmit={handleSubmit}
          className="border-t border-border/40 bg-background px-5 py-4 sm:px-7"
        >
          <div className="flex items-end gap-3 rounded-xl border border-border/60 bg-card/70 p-3 focus-within:border-brand/50">
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
              placeholder="Например: почему выручка просела на прошлой неделе?"
              disabled={busy}
              className="min-h-[44px] max-h-36 flex-1 resize-none bg-transparent px-1 py-2 text-[15px] leading-relaxed text-foreground placeholder:text-muted-foreground/65 focus:outline-none disabled:opacity-60"
            />
            <button
              type="submit"
              disabled={busy || !input.trim()}
              className="inline-flex size-10 items-center justify-center rounded-lg bg-brand text-primary-foreground transition-colors hover:bg-brand-hover disabled:opacity-40"
              aria-label="Отправить"
            >
              <Send className="size-4" />
            </button>
          </div>
          <p className="mt-2 text-[11px] text-muted-foreground">
            Enter — отправить. Shift+Enter — новая строка.
          </p>
        </form>
      </SheetContent>
    </Sheet>
  );
}

function EmptyState({ onPick }: { onPick: (text: string) => void }) {
  return (
    <div className="flex min-h-full flex-col justify-between gap-8">
      <div className="rounded-xl border border-border/60 bg-card/45 p-5 sm:p-6">
        <div className="flex items-start gap-3">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg border border-border/60 bg-background/45 text-brand">
            <Database className="size-4" />
          </div>
          <div>
            <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              Copilot по данным iiko
            </p>
            <h3 className="mt-2 max-w-xl text-[24px] font-medium leading-tight tracking-[-0.02em] text-foreground sm:text-[30px]">
              Задайте вопрос как управляющему аналитику.
            </h3>
            <p className="mt-3 max-w-xl text-[14px] leading-relaxed text-muted-foreground">
              Receptor читает продажи, блюда, категории и смены, затем отвечает
              нормальным языком: что произошло, почему это важно и что сделать
              сегодня.
            </p>
          </div>
        </div>
      </div>

      <div>
        <p className="mb-3 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
          Быстрые вопросы
        </p>
        <div className="grid gap-2 sm:grid-cols-2">
          {SUGGESTED_PROMPTS.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => onPick(p)}
              className="group rounded-lg border border-border/60 bg-card/55 px-3.5 py-3 text-left text-sm leading-snug text-foreground/85 transition-colors hover:border-brand/40 hover:bg-card hover:text-foreground"
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
        <div className="max-w-[85%] rounded-xl bg-muted px-4 py-3 text-[14px] leading-relaxed text-foreground">
          {message.text}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2 rounded-xl border border-border/50 bg-card/35 p-4">
      <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
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
        <div className="whitespace-pre-wrap text-[15px] leading-relaxed text-foreground/90">
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
