"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, Loader2 } from "lucide-react";
import { markAnnouncementReadAction } from "./actions";

export function AnnouncementReadButton({
  announcementId,
  initialRead,
}: {
  announcementId: string;
  initialRead: boolean;
}) {
  const router = useRouter();
  const [isRead, setIsRead] = useState(initialRead);
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  return (
    <div className="mt-4">
      <button
        type="button"
        disabled={pending || isRead}
        onClick={async () => {
          setMessage(null);
          setPending(true);
          try {
            const result = await markAnnouncementReadAction({ announcementId });
            setMessage(result.ok ? result.message : result.error);
            if (result.ok) {
              setIsRead(true);
              router.refresh();
            }
          } finally {
            setPending(false);
          }
        }}
        className="inline-flex h-9 items-center gap-2 rounded-lg border border-border/60 bg-background/60 px-3 text-xs font-medium text-foreground transition-colors hover:border-brand/40 disabled:opacity-55"
      >
        {pending ? (
          <Loader2 className="size-3.5 animate-spin" />
        ) : (
          <CheckCircle2 className="size-3.5 text-brand" />
        )}
        {isRead ? "Прочитано" : "Понятно"}
      </button>
      {message ? (
        <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">
          {message}
        </p>
      ) : null}
    </div>
  );
}
