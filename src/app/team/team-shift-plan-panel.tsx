"use client";

import {
  useMemo,
  useState,
  useTransition,
  type FormEvent,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import {
  AlertTriangle,
  CalendarPlus,
  CheckCircle2,
  Clock3,
  Save,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatInteger, formatRubles } from "@/lib/format";
import type { StaffMember } from "@/lib/team/team-os";
import {
  buildTeamShiftPlanSummary,
  type TeamShiftPlan,
  type TeamShiftPlanItem,
} from "@/lib/team/team-shift-plan";
import { saveTeamShiftPlanAction, type TeamActionResult } from "./actions";

type Message = {
  tone: "success" | "error";
  text: string;
};

const FIELD_CLASS =
  "w-full rounded-lg border border-border/55 bg-background/45 px-3 py-2 text-sm text-foreground outline-none transition focus:border-brand/50 focus:ring-2 focus:ring-brand/15";

export function TeamShiftPlanPanel({
  venueId,
  staff,
  plans,
}: {
  venueId: string;
  staff: StaffMember[];
  plans: TeamShiftPlan[];
}) {
  const router = useRouter();
  const activeStaff = useMemo(
    () => staff.filter((member) => member.status !== "paused"),
    [staff],
  );
  const summary = useMemo(
    () => buildTeamShiftPlanSummary({ staff, plans }),
    [staff, plans],
  );
  const planItems = useMemo(
    () =>
      summary.rows
        .flatMap((row) =>
          row.items.map((item) => ({
            ...item,
            member: row.member,
            roleTitle: row.roleTitle,
          })),
        )
        .sort((a, b) => a.plan.shiftDate.localeCompare(b.plan.shiftDate))
        .slice(0, 8),
    [summary],
  );

  const [memberId, setMemberId] = useState(activeStaff[0]?.id ?? "");
  const [shiftDate, setShiftDate] = useState(nextDateValue());
  const [shiftStart, setShiftStart] = useState("12:00");
  const [shiftEnd, setShiftEnd] = useState("23:00");
  const [isDayOff, setIsDayOff] = useState(false);
  const [note, setNote] = useState("");
  const [message, setMessage] = useState<Message | null>(null);
  const [pending, startTransition] = useTransition();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    savePlan();
  }

  function savePlan() {
    setMessage(null);

    startTransition(async () => {
      const result = await saveTeamShiftPlanAction({
        venueId,
        memberId,
        shiftDate,
        shiftStart,
        shiftEnd,
        isDayOff,
        note,
      });
      setMessage(resultToMessage(result));
      if (result.ok && result.mode === "saved") {
        router.refresh();
      }
    });
  }

  return (
    <section
      id="shift-plan"
      className="scroll-mt-24 border-b border-border/40"
    >
      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="rounded-lg border border-border/60 bg-card/50 p-5">
          <div className="grid gap-5 xl:grid-cols-[0.58fr_1.42fr]">
            <div>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.22em] text-brand">
                    План смен
                  </p>
                  <h2 className="mt-3 text-2xl font-medium">
                    Состав и ФОТ до начала дня
                  </h2>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    Запланируйте людей, часы и выходные. Receptor сразу считает
                    прогноз ФОТ и показывает, где нет ставки.
                  </p>
                </div>
                <CalendarPlus className="size-6 shrink-0 text-brand" />
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3">
                <PlanMetric
                  label="Смен"
                  value={formatInteger(summary.plannedShifts)}
                />
                <PlanMetric label="Часов" value={formatHours(summary.hours)} />
                <PlanMetric
                  label="ФОТ план"
                  value={formatRubles(summary.laborCost)}
                />
                <PlanMetric
                  label="Без ставки"
                  value={formatInteger(summary.missingRateShifts)}
                />
              </div>

              {summary.missingRateShifts > 0 ? (
                <div className="mt-4 flex gap-3 rounded-lg border border-amber-400/25 bg-amber-400/10 p-3">
                  <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-200" />
                  <p className="text-xs leading-relaxed text-muted-foreground">
                    Есть смены без ставки. ФОТ будет занижен, пока не заполнены
                    ₽/час или ₽/смена в карточке сотрудника.
                  </p>
                </div>
              ) : (
                <div className="mt-4 flex gap-3 rounded-lg border border-brand/25 bg-brand/10 p-3">
                  <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-brand" />
                  <p className="text-xs leading-relaxed text-muted-foreground">
                    План можно сравнивать с фактическими сменами из iiko.
                  </p>
                </div>
              )}
            </div>

            <div className="grid gap-4 lg:grid-cols-[0.92fr_1.08fr]">
              <form
                onSubmit={handleSubmit}
                className="rounded-lg border border-border/45 bg-background/35 p-4"
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                      Добавить
                    </p>
                    <h3 className="mt-1 text-lg font-medium">Смена или выходной</h3>
                  </div>
                  <Clock3 className="size-5 text-muted-foreground" />
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <FieldLabel label="Сотрудник">
                    <select
                      className={FIELD_CLASS}
                      value={memberId}
                      onChange={(event) => setMemberId(event.target.value)}
                      required
                    >
                      {activeStaff.map((member) => (
                        <option key={member.id} value={member.id}>
                          {member.name}
                        </option>
                      ))}
                    </select>
                  </FieldLabel>
                  <FieldLabel label="Дата">
                    <input
                      className={FIELD_CLASS}
                      type="date"
                      value={shiftDate}
                      onChange={(event) => setShiftDate(event.target.value)}
                      required
                    />
                  </FieldLabel>
                  <FieldLabel label="Начало">
                    <input
                      className={FIELD_CLASS}
                      type="time"
                      value={shiftStart}
                      onChange={(event) => setShiftStart(event.target.value)}
                      disabled={isDayOff}
                    />
                  </FieldLabel>
                  <FieldLabel label="Конец">
                    <input
                      className={FIELD_CLASS}
                      type="time"
                      value={shiftEnd}
                      onChange={(event) => setShiftEnd(event.target.value)}
                      disabled={isDayOff}
                    />
                  </FieldLabel>
                </div>

                <label className="mt-4 flex items-center gap-2 rounded-lg border border-border/45 bg-card/35 px-3 py-2 text-sm text-muted-foreground">
                  <input
                    type="checkbox"
                    checked={isDayOff}
                    onChange={(event) => setIsDayOff(event.target.checked)}
                    className="size-4 accent-brand"
                  />
                  Выходной
                </label>

                <FieldLabel label="Заметка">
                  <input
                    className={FIELD_CLASS}
                    value={note}
                    onChange={(event) => setNote(event.target.value)}
                    placeholder="зал, кухня, банкет"
                  />
                </FieldLabel>

                <Button
                  type="button"
                  className="mt-4 w-full"
                  disabled={pending || activeStaff.length === 0}
                  onClick={savePlan}
                >
                  <Save className="size-4" />
                  Сохранить план
                </Button>

                {message ? (
                  <p
                    className={
                      "mt-3 text-sm " +
                      (message.tone === "success"
                        ? "text-brand"
                        : "text-destructive")
                    }
                  >
                    {message.text}
                  </p>
                ) : null}
              </form>

              <div className="rounded-lg border border-border/45 bg-background/35 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                      Ближайший план
                    </p>
                    <h3 className="mt-1 text-lg font-medium">Кто выходит</h3>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {summary.dayOffs} выходных
                  </p>
                </div>

                <div className="mt-4 grid gap-2">
                  {planItems.length > 0 ? (
                    planItems.map((item) => (
                      <PlanItemRow
                        key={`${item.plan.memberId}-${item.plan.shiftDate}`}
                        item={item}
                      />
                    ))
                  ) : (
                    <p className="rounded-lg border border-border/45 bg-card/35 p-4 text-sm text-muted-foreground">
                      План пока пустой. Добавьте первую смену, чтобы увидеть
                      прогноз ФОТ.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function PlanMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border/45 bg-background/35 p-3">
      <p className="numeric text-lg font-medium text-foreground">{value}</p>
      <p className="mt-1 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </p>
    </div>
  );
}

function PlanItemRow({
  item,
}: {
  item: TeamShiftPlanItem & { member: StaffMember; roleTitle: string };
}) {
  return (
    <div className="grid gap-2 rounded-lg border border-border/45 bg-card/35 p-3 sm:grid-cols-[1fr_auto] sm:items-center">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <p className="truncate text-sm font-medium">{item.member.name}</p>
          <span
            className={
              "rounded-md border px-2 py-0.5 text-[10px] uppercase tracking-[0.12em] " +
              (item.plan.isDayOff
                ? "border-border/60 text-muted-foreground"
                : item.missingRate
                  ? "border-amber-400/35 text-amber-200"
                  : "border-brand/30 text-brand")
            }
          >
            {item.plan.isDayOff
              ? "выходной"
              : item.missingRate
                ? "нет ставки"
                : "в плане"}
          </span>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          {item.dateLabel} · {item.timeLabel} · {item.roleTitle}
        </p>
        {item.plan.note ? (
          <p className="mt-1 text-xs text-muted-foreground">{item.plan.note}</p>
        ) : null}
      </div>
      <div className="text-left sm:text-right">
        <p className="numeric text-sm font-medium text-foreground">
          {formatRubles(item.laborCost)}
        </p>
        <p className="mt-1 text-[11px] text-muted-foreground">
          {formatHours(item.hours)}
        </p>
      </div>
    </div>
  );
}

function FieldLabel({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </span>
      {children}
    </label>
  );
}

function formatHours(value: number): string {
  return `${value.toLocaleString("ru-RU", { maximumFractionDigits: 1 })} ч`;
}

function resultToMessage(result: TeamActionResult): Message {
  if (!result.ok) return { tone: "error", text: result.error };
  return { tone: "success", text: result.message };
}

function nextDateValue(): string {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  return date.toISOString().slice(0, 10);
}
