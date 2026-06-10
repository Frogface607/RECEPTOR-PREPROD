"use client";

import { useState } from "react";
import { Loader2, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { PeriodType } from "@/lib/iiko/models";

type SendState =
  | { status: "idle" }
  | { status: "sending" }
  | { status: "sent" }
  | { status: "error"; message: string };

export function SendBriefButton({
  venueId,
  period,
}: {
  venueId: string;
  period: PeriodType;
}) {
  const [state, setState] = useState<SendState>({ status: "idle" });

  const sendBrief = async () => {
    if (state.status === "sending") return;
    setState({ status: "sending" });

    try {
      const response = await fetch("/api/brief/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ venueId, period }),
      });
      const data = (await response.json().catch(() => null)) as {
        error?: string;
      } | null;

      if (!response.ok) {
        setState({
          status: "error",
          message: data?.error ?? `HTTP ${response.status}`,
        });
        return;
      }

      setState({ status: "sent" });
    } catch (err) {
      setState({
        status: "error",
        message: err instanceof Error ? err.message : "network error",
      });
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={sendBrief}
        disabled={state.status === "sending"}
        className="bg-background/50"
      >
        {state.status === "sending" ? (
          <Loader2 className="size-3.5 animate-spin" />
        ) : (
          <Send className="size-3.5" />
        )}
        Отправить
      </Button>

      {state.status === "sent" ? (
        <span className="text-[12px] text-brand">Ушло в Telegram</span>
      ) : null}

      {state.status === "error" ? (
        <span className="max-w-[280px] text-[12px] text-destructive">
          {state.message}
        </span>
      ) : null}
    </div>
  );
}
