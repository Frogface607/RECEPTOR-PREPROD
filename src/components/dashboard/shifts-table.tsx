import { formatRubles, formatInteger } from "@/lib/format";
import type { ShiftStat } from "@/lib/iiko/models";

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "short",
    weekday: "short",
  });
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function ShiftsTable({ shifts }: { shifts: ShiftStat[] }) {
  const sorted = [...shifts].sort((a, b) =>
    a.openTime < b.openTime ? 1 : -1,
  );
  const totalRevenue = shifts.reduce((s, x) => s + x.revenue, 0);
  const totalItems = shifts.reduce((s, x) => s + x.items, 0);

  return (
    <div className="rounded-2xl border border-border/60 bg-card/60 p-6">
      <div className="flex items-baseline justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.2em] text-brand">
            Смены
          </p>
          <h3 className="mt-1 text-[18px] font-medium tracking-[-0.01em]">
            Продажи по кассовым сменам
          </h3>
        </div>
        <div className="text-right">
          <p className="numeric font-display text-[20px] tracking-[-0.01em] text-foreground">
            {formatRubles(totalRevenue)}
          </p>
          <p className="text-[10px] uppercase tracking-widest text-muted-foreground">
            {formatInteger(totalItems)} позиций
          </p>
        </div>
      </div>

      <div className="mt-6 overflow-x-auto">
        <table className="w-full text-left text-[14px]">
          <thead>
            <tr className="border-b border-border/50 text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
              <th className="py-3 pr-6 font-normal">Дата</th>
              <th className="py-3 pr-6 font-normal">Сотрудник</th>
              <th className="py-3 pr-6 font-normal">Открытие → закрытие</th>
              <th className="py-3 pr-6 font-normal text-right">Позиций</th>
              <th className="py-3 pr-0 font-normal text-right">Выручка</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/30">
            {sorted.map((s) => (
              <tr
                key={s.shiftId}
                className="transition-colors hover:bg-card/95"
              >
                <td className="py-4 pr-6 text-foreground">
                  {formatDate(s.openTime)}
                </td>
                <td className="py-4 pr-6 text-foreground">{s.employee}</td>
                <td className="py-4 pr-6 font-mono text-[12px] text-muted-foreground">
                  {formatTime(s.openTime)}
                  {s.closeTime ? ` → ${formatTime(s.closeTime)}` : " · открыта"}
                </td>
                <td className="numeric py-4 pr-6 text-right font-mono text-foreground">
                  {formatInteger(s.items)}
                </td>
                <td className="numeric py-4 pr-0 text-right font-mono text-foreground">
                  {formatRubles(s.revenue)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
