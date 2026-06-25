import { Brain, Target, TriangleAlert } from "lucide-react";
import type { VenueIntelligenceProfile } from "@/lib/venues/intelligence";
import {
  calculateContextCompletion,
  type VenueContextAnswers,
} from "@/lib/venues/context-questionnaire";

export function VenueIntelligenceCard({
  profile,
  context,
}: {
  profile: VenueIntelligenceProfile;
  context?: VenueContextAnswers;
}) {
  const contextCompletion = calculateContextCompletion(context ?? {});

  return (
    <section className="rounded-xl border border-border/60 bg-card/50 p-5 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-border/60 bg-background/45 text-brand">
            <Brain className="size-5" />
          </div>
          <div>
            <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              Профиль заведения
            </p>
            <h2 className="mt-2 text-xl font-medium leading-tight tracking-[-0.01em] text-foreground">
              Receptor учитывает контекст бизнеса
            </h2>
            <p className="mt-2 max-w-2xl text-[14px] leading-relaxed text-muted-foreground">
              {profile.positioning}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="rounded-lg border border-border/60 bg-background/45 px-2.5 py-1 text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
            {profile.researchStatus === "researched"
              ? "Deep Research"
              : profile.researchStatus === "manual"
                ? "Настроено вручную"
                : "Демо-профиль"}
          </span>
          <span className="rounded-lg border border-brand/30 bg-brand/10 px-2.5 py-1 text-[11px] uppercase tracking-[0.14em] text-brand">
            Context {contextCompletion.requiredPercentage}%
          </span>
        </div>
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-3">
        <InsightColumn
          icon={Target}
          title="Цели владельца"
          items={profile.ownerGoals}
        />
        <InsightColumn
          icon={TriangleAlert}
          title="Риски"
          items={profile.operatingRisks}
        />
        <InsightColumn
          icon={Brain}
          title="Фокус AI-помощника"
          items={profile.recommendedFocus}
        />
      </div>
    </section>
  );
}

function InsightColumn({
  icon: Icon,
  title,
  items,
}: {
  icon: typeof Brain;
  title: string;
  items: string[];
}) {
  return (
    <div>
      <div className="mb-3 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
        <Icon className="size-3.5 text-brand" />
        {title}
      </div>
      <ul className="space-y-2.5 text-[13px] leading-relaxed text-foreground/85">
        {items.slice(0, 4).map((item) => (
          <li key={item} className="rounded-lg bg-background/35 px-3 py-2">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
