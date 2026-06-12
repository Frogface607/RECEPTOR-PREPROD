import {
  AlertTriangle,
  CircleHelp,
  Flame,
  ShieldCheck,
  Stethoscope,
} from "lucide-react";
import type { DailyBrief } from "@/lib/brief/daily-brief";
import type { CategoryStat, DishStat } from "@/lib/iiko/models";
import {
  buildSurvivalBrief,
  type SurvivalFactor,
  type SurvivalStatus,
} from "@/lib/survival-score";

const STATUS_TONE: Record<SurvivalStatus, string> = {
  critical: "border-destructive/45 bg-destructive/8 text-destructive",
  serious: "border-amber-500/35 bg-amber-500/10 text-amber-300",
  watch: "border-brand/35 bg-brand/10 text-brand",
  stable: "border-emerald-500/35 bg-emerald-500/10 text-emerald-300",
};

const FACTOR_TONE: Record<SurvivalFactor["level"], string> = {
  critical: "border-destructive/35",
  serious: "border-amber-500/30",
  watch: "border-brand/25",
  info: "border-border/50",
};

export function SurvivalBriefCard({
  brief,
  dishes,
  categories,
}: {
  brief: DailyBrief;
  dishes: DishStat[];
  categories: CategoryStat[];
}) {
  const survival = buildSurvivalBrief({
    dailyBrief: brief,
    dishes,
    categories,
  });
  const topFactors = survival.factors.slice(0, 4);

  return (
    <section className="rounded-xl border border-border/60 bg-card/50 p-5 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-border/60 bg-background/45 text-brand">
            <Stethoscope className="size-5" />
          </div>
          <div className="min-w-0">
            <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              Контроль прибыли
            </p>
            <h2 className="mt-2 text-xl font-medium leading-tight tracking-[-0.01em] text-foreground">
              {survival.title}
            </h2>
            <p className="mt-2 max-w-2xl text-[14px] leading-relaxed text-muted-foreground">
              {survival.summary}
            </p>
          </div>
        </div>

        <div
          className={
            "rounded-lg border px-3 py-2 text-right " +
            STATUS_TONE[survival.status]
          }
        >
          <p className="font-mono text-[22px] leading-none">
            {survival.score}
          </p>
          <p className="mt-1 text-[10px] uppercase tracking-[0.14em]">
            риск прибыли
          </p>
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-4">
        {topFactors.map((factor) => (
          <FactorCard key={factor.id} factor={factor} />
        ))}
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <div>
          <div className="mb-3 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            <Flame className="size-3.5 text-brand" />
            Что сделать уже сегодня
          </div>
          <ol className="space-y-2.5 text-[13px] leading-relaxed text-foreground/85">
            {survival.actions.map((action, index) => (
              <li
                key={action}
                className="flex gap-3 rounded-lg bg-background/35 px-3 py-2"
              >
                <span className="font-mono text-[11px] text-brand">
                  {index + 1}
                </span>
                <span>{action}</span>
              </li>
            ))}
          </ol>
        </div>

        <div>
          <div className="mb-3 flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            <CircleHelp className="size-3.5 text-brand" />
            Что спросить у команды
          </div>
          <ul className="space-y-2.5 text-[13px] leading-relaxed text-foreground/85">
            {survival.questions.slice(0, 4).map((question) => (
              <li
                key={`${question.role}-${question.text}`}
                className="rounded-lg bg-background/35 px-3 py-2"
              >
                <span className="mr-2 font-mono text-[10px] uppercase tracking-[0.14em] text-brand">
                  {roleLabel(question.role)}
                </span>
                {question.text}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-6 rounded-lg border border-border/45 bg-background/30 px-3 py-3">
        <div className="flex items-start gap-2">
          <ShieldCheck className="mt-0.5 size-4 shrink-0 text-brand" />
          <p className="text-[12px] leading-relaxed text-muted-foreground">
            Для точной картины прибыли не хватает:{" "}
            <span className="text-foreground/85">
              {survival.missingData.join(", ")}
            </span>
            . Начинаем с A-позиций, потому что они быстрее всего покажут, где
            ресторан зарабатывает, а где просто крутит оборот.
          </p>
        </div>
      </div>
    </section>
  );
}

function FactorCard({ factor }: { factor: SurvivalFactor }) {
  const isBad = factor.level === "critical" || factor.level === "serious";
  return (
    <div
      className={
        "rounded-lg border bg-background/35 p-3 " + FACTOR_TONE[factor.level]
      }
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <AlertTriangle
            className={
              "mt-0.5 size-4 shrink-0 " +
              (isBad ? "text-amber-300" : "text-brand")
            }
          />
          <p className="text-[13px] font-medium text-foreground">
            {factor.title}
          </p>
        </div>
        <span className="shrink-0 rounded-md border border-border/50 bg-card/50 px-2 py-0.5 font-mono text-[11px] text-muted-foreground">
          {factor.metric}
        </span>
      </div>
      <p className="mt-2 text-[12px] leading-relaxed text-muted-foreground">
        {factor.detail}
      </p>
    </div>
  );
}

function roleLabel(role: string): string {
  if (role === "owner") return "владелец";
  if (role === "manager") return "управляющий";
  if (role === "chef") return "шеф";
  return "зал";
}
