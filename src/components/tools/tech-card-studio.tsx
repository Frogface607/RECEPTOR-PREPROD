"use client";

import { useMemo, useState, type ReactNode } from "react";
import {
  ArrowDownToLine,
  Copy,
  FileText,
  Plus,
  Printer,
  RotateCcw,
  Save,
  Trash2,
} from "lucide-react";
import {
  calculateTechCard,
  createTechCardMarkdown,
  formatRub,
  type TechCardIngredient,
  type TechCardInput,
} from "@/lib/tools/tech-card";

type SavedTechCard = {
  id: string;
  savedAt: string;
  input: TechCardInput;
};

const STORAGE_KEY = "receptor.tech-card-studio.history";

function newId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function emptyIngredient(): TechCardIngredient {
  return {
    id: newId(),
    name: "",
    unit: "g",
    grossQty: 0,
    netQty: 0,
    pricePerKg: 0,
    proteinPer100g: 0,
    fatPer100g: 0,
    carbsPer100g: 0,
    kcalPer100g: 0,
    article: "",
  };
}

function emptyInput(): TechCardInput {
  return {
    dishName: "",
    category: "",
    portions: 1,
    outputWeight: 0,
    targetFoodCostPercent: 30,
    process: "",
    ingredients: [emptyIngredient(), emptyIngredient(), emptyIngredient()],
  };
}

function numberValue(value: string): number {
  if (!value.trim()) return 0;
  return Number(value.replace(",", "."));
}

export function TechCardStudio() {
  const [input, setInput] = useState<TechCardInput>(() => emptyInput());
  const [history, setHistory] = useState<SavedTechCard[]>(() => {
    if (typeof window === "undefined") return [];
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      return raw ? (JSON.parse(raw) as SavedTechCard[]) : [];
    } catch {
      return [];
    }
  });
  const [copied, setCopied] = useState(false);

  const calculation = useMemo(() => calculateTechCard(input), [input]);
  const markdown = useMemo(
    () => createTechCardMarkdown(input, calculation),
    [input, calculation],
  );

  const updateInput = <K extends keyof TechCardInput>(
    field: K,
    value: TechCardInput[K],
  ) => {
    setInput((current) => ({ ...current, [field]: value }));
  };

  const updateIngredient = <K extends keyof TechCardIngredient>(
    id: string,
    field: K,
    value: TechCardIngredient[K],
  ) => {
    setInput((current) => ({
      ...current,
      ingredients: current.ingredients.map((ingredient) =>
        ingredient.id === id ? { ...ingredient, [field]: value } : ingredient,
      ),
    }));
  };

  const addIngredient = () => {
    setInput((current) => ({
      ...current,
      ingredients: [...current.ingredients, emptyIngredient()],
    }));
  };

  const removeIngredient = (id: string) => {
    setInput((current) => ({
      ...current,
      ingredients:
        current.ingredients.length > 1
          ? current.ingredients.filter((ingredient) => ingredient.id !== id)
          : current.ingredients,
    }));
  };

  const saveVersion = () => {
    const next = [
      {
        id: newId(),
        savedAt: new Date().toISOString(),
        input,
      },
      ...history,
    ].slice(0, 12);
    setHistory(next);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  };

  const copyMarkdown = async () => {
    await navigator.clipboard.writeText(markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  const printPdf = () => {
    window.print();
  };

  const reset = () => {
    setInput(emptyInput());
    setCopied(false);
  };

  return (
    <div className="space-y-8">
      <div className="print:hidden grid gap-4 lg:grid-cols-4">
        <SummaryCard label="Себестоимость" value={formatRub(calculation.totalCost)} />
        <SummaryCard label="Порция" value={formatRub(calculation.costPerPortion)} />
        <SummaryCard label="Цена при фудкосте" value={formatRub(calculation.recommendedPrice)} />
        <SummaryCard label="iiko артикулы" value={`${calculation.mappingCoveragePercent}%`} />
      </div>

      <div className="print:hidden grid min-w-0 gap-6 xl:grid-cols-[minmax(0,1.25fr)_minmax(340px,0.75fr)]">
        <section className="min-w-0 rounded-xl border border-border/60 bg-card/35 p-5 sm:p-6">
          <div className="flex flex-col gap-4 border-b border-border/40 pb-5 lg:flex-row lg:items-start lg:justify-between">
            <div className="min-w-0">
              <p className="text-[11px] uppercase tracking-[0.18em] text-brand">
                Tech Card Studio
              </p>
              <h2 className="mt-2 text-2xl font-medium tracking-[-0.02em]">
                Технологическая карта
              </h2>
              <p className="mt-2 max-w-2xl text-[13px] leading-relaxed text-muted-foreground">
                Считаем рабочую основу: брутто/нетто, потери, себестоимость,
                КБЖУ, фудкост и артикулы iiko. Дальше этот слой станет PDF,
                историей и экспортом в iiko.
              </p>
            </div>
            <div className="flex max-w-full flex-wrap gap-2 lg:justify-end">
              <ActionButton onClick={saveVersion} icon={<Save className="size-4" />}>
                Сохранить
              </ActionButton>
              <ActionButton onClick={copyMarkdown} icon={<Copy className="size-4" />}>
                {copied ? "Скопировано" : "Markdown"}
              </ActionButton>
              <ActionButton onClick={printPdf} icon={<Printer className="size-4" />}>
                PDF
              </ActionButton>
              <ActionButton onClick={reset} icon={<RotateCcw className="size-4" />}>
                Очистить
              </ActionButton>
            </div>
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-4">
            <Field
              label="Блюдо"
              value={input.dishName}
              placeholder="Название блюда"
              onChange={(value) => updateInput("dishName", value)}
              className="lg:col-span-2"
            />
            <Field
              label="Категория"
              value={input.category}
              placeholder="Горячее, закуски, соус"
              onChange={(value) => updateInput("category", value)}
            />
            <NumberField
              label="Порций"
              value={input.portions}
              onChange={(value) => updateInput("portions", value)}
            />
            <NumberField
              label="Выход, г"
              value={input.outputWeight}
              onChange={(value) => updateInput("outputWeight", value)}
            />
            <NumberField
              label="Фудкост, %"
              value={input.targetFoodCostPercent}
              onChange={(value) => updateInput("targetFoodCostPercent", value)}
            />
          </div>

          <div className="mt-7 overflow-x-auto rounded-xl border border-border/55">
            <table className="numeric min-w-[1040px] w-full text-left text-[12px]">
              <thead className="bg-background/60 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                <tr>
                  <th className="px-3 py-3 font-normal">Ингредиент</th>
                  <th className="px-3 py-3 font-normal">Ед.</th>
                  <th className="px-3 py-3 font-normal">Брутто</th>
                  <th className="px-3 py-3 font-normal">Нетто</th>
                  <th className="px-3 py-3 font-normal">Цена</th>
                  <th className="px-3 py-3 font-normal">Б</th>
                  <th className="px-3 py-3 font-normal">Ж</th>
                  <th className="px-3 py-3 font-normal">У</th>
                  <th className="px-3 py-3 font-normal">Ккал</th>
                  <th className="px-3 py-3 font-normal">Артикул</th>
                  <th className="px-3 py-3 font-normal">Итог</th>
                  <th className="px-3 py-3 font-normal" />
                </tr>
              </thead>
              <tbody>
                {calculation.ingredients.map((ingredient) => (
                  <tr key={ingredient.id} className="border-t border-border/35">
                    <td className="px-3 py-2">
                      <input
                        value={ingredient.name}
                        onChange={(event) =>
                          updateIngredient(ingredient.id, "name", event.target.value)
                        }
                        placeholder="Ингредиент"
                        className="h-9 w-full min-w-[180px] rounded-lg border border-border/50 bg-background/50 px-3 text-[12px] outline-none focus:border-brand/50"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <select
                        value={ingredient.unit}
                        onChange={(event) =>
                          updateIngredient(
                            ingredient.id,
                            "unit",
                            event.target.value as TechCardIngredient["unit"],
                          )
                        }
                        className="h-9 w-[72px] rounded-lg border border-border/50 bg-background/50 px-2 text-[12px] outline-none focus:border-brand/50"
                      >
                        <option value="g">г</option>
                        <option value="ml">мл</option>
                        <option value="pcs">шт</option>
                      </select>
                    </td>
                    <NumericCell
                      value={ingredient.grossQty}
                      onChange={(value) =>
                        updateIngredient(ingredient.id, "grossQty", value)
                      }
                    />
                    <NumericCell
                      value={ingredient.netQty}
                      onChange={(value) =>
                        updateIngredient(ingredient.id, "netQty", value)
                      }
                    />
                    <NumericCell
                      value={ingredient.pricePerKg}
                      onChange={(value) =>
                        updateIngredient(ingredient.id, "pricePerKg", value)
                      }
                    />
                    <NumericCell
                      value={ingredient.proteinPer100g}
                      onChange={(value) =>
                        updateIngredient(ingredient.id, "proteinPer100g", value)
                      }
                    />
                    <NumericCell
                      value={ingredient.fatPer100g}
                      onChange={(value) =>
                        updateIngredient(ingredient.id, "fatPer100g", value)
                      }
                    />
                    <NumericCell
                      value={ingredient.carbsPer100g}
                      onChange={(value) =>
                        updateIngredient(ingredient.id, "carbsPer100g", value)
                      }
                    />
                    <NumericCell
                      value={ingredient.kcalPer100g}
                      onChange={(value) =>
                        updateIngredient(ingredient.id, "kcalPer100g", value)
                      }
                    />
                    <td className="px-3 py-2">
                      <input
                        value={ingredient.article ?? ""}
                        onChange={(event) =>
                          updateIngredient(ingredient.id, "article", event.target.value)
                        }
                        placeholder="iiko"
                        className="h-9 w-[90px] rounded-lg border border-border/50 bg-background/50 px-3 text-[12px] outline-none focus:border-brand/50"
                      />
                    </td>
                    <td className="px-3 py-2 text-right text-[12px] text-foreground">
                      <div>{formatRub(ingredient.cost)}</div>
                      <div className="text-muted-foreground">{ingredient.lossPercent}%</div>
                    </td>
                    <td className="px-3 py-2 text-right">
                      <button
                        type="button"
                        onClick={() => removeIngredient(ingredient.id)}
                        className="inline-flex size-8 items-center justify-center rounded-lg border border-border/50 text-muted-foreground transition hover:border-destructive/40 hover:text-destructive"
                        aria-label="Удалить ингредиент"
                      >
                        <Trash2 className="size-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <button
            type="button"
            onClick={addIngredient}
            className="mt-4 inline-flex h-10 items-center gap-2 rounded-lg border border-border/60 bg-background/45 px-4 text-[13px] text-foreground transition hover:border-brand/50"
          >
            <Plus className="size-4" />
            Добавить ингредиент
          </button>

          <div className="mt-6">
            <label className="text-[13px] font-medium text-foreground">
              Технология приготовления
            </label>
            <textarea
              value={input.process}
              onChange={(event) => updateInput("process", event.target.value)}
              placeholder="Опишите подготовку, приготовление, подачу, условия хранения и контрольные точки."
              rows={7}
              className="mt-2 min-h-[160px] w-full resize-y rounded-lg border border-border/60 bg-background/55 px-3.5 py-3 text-sm leading-relaxed text-foreground placeholder:text-muted-foreground/55 focus:border-brand/50 focus:outline-none"
            />
          </div>
        </section>

        <aside className="min-w-0 space-y-6">
          <section className="rounded-xl border border-border/60 bg-card/35 p-5">
            <div className="flex items-center gap-2 text-brand">
              <FileText className="size-4" />
              <p className="text-[11px] uppercase tracking-[0.18em]">
                Контроль качества
              </p>
            </div>
            <div className="mt-5 space-y-3">
              <QualityRow
                label="Выход"
                value={
                  calculation.yieldDelta === 0
                    ? "совпадает"
                    : `${calculation.yieldDelta > 0 ? "+" : ""}${calculation.yieldDelta} г`
                }
              />
              <QualityRow
                label="Нетто / брутто"
                value={`${calculation.totalNetWeight} / ${calculation.totalGrossWeight} г`}
              />
              <QualityRow
                label="КБЖУ на 100 г"
                value={`${calculation.kcalPer100g} / ${calculation.proteinPer100g} / ${calculation.fatPer100g} / ${calculation.carbsPer100g}`}
              />
              <QualityRow
                label="Артикулы iiko"
                value={`${calculation.mappingCoveragePercent}%`}
              />
            </div>
          </section>

          <section className="rounded-xl border border-border/60 bg-card/35 p-5">
            <div className="flex items-center justify-between gap-3">
              <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                История версий
              </p>
              <ArrowDownToLine className="size-4 text-muted-foreground" />
            </div>
            <div className="mt-4 space-y-2">
              {history.length === 0 ? (
                <p className="rounded-lg border border-border/50 bg-background/35 p-4 text-[13px] leading-relaxed text-muted-foreground">
                  Сохранённые версии появятся здесь. Пока история локальная в
                  браузере; позже перенесём в Supabase.
                </p>
              ) : (
                history.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setInput(item.input)}
                    className="block w-full rounded-lg border border-border/50 bg-background/35 p-3 text-left transition hover:border-brand/45"
                  >
                    <p className="text-[13px] font-medium text-foreground">
                      {item.input.dishName || "Без названия"}
                    </p>
                    <p className="mt-1 text-[11px] text-muted-foreground">
                      {new Date(item.savedAt).toLocaleString("ru-RU")}
                    </p>
                  </button>
                ))
              )}
            </div>
          </section>
        </aside>
      </div>

      <PrintableTechCard input={input} />
    </div>
  );
}

function SummaryCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border/60 bg-card/35 p-5">
      <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </p>
      <p className="mt-2 text-2xl font-medium tracking-[-0.02em] text-foreground">
        {value}
      </p>
    </div>
  );
}

function ActionButton({
  children,
  icon,
  onClick,
}: {
  children: ReactNode;
  icon: ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex h-9 items-center gap-2 rounded-lg border border-border/60 bg-background/45 px-3 text-[12px] text-foreground transition hover:border-brand/50"
    >
      {icon}
      {children}
    </button>
  );
}

function Field({
  label,
  value,
  placeholder,
  onChange,
  className = "",
}: {
  label: string;
  value: string;
  placeholder: string;
  onChange: (value: string) => void;
  className?: string;
}) {
  return (
    <label className={`flex flex-col gap-2 ${className}`}>
      <span className="text-[13px] font-medium text-foreground">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="h-10 rounded-lg border border-border/60 bg-background/55 px-3.5 text-sm text-foreground placeholder:text-muted-foreground/55 focus:border-brand/50 focus:outline-none"
      />
    </label>
  );
}

function NumberField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="flex flex-col gap-2">
      <span className="text-[13px] font-medium text-foreground">{label}</span>
      <input
        value={value || ""}
        inputMode="decimal"
        onChange={(event) => onChange(numberValue(event.target.value))}
        className="h-10 rounded-lg border border-border/60 bg-background/55 px-3.5 text-sm text-foreground placeholder:text-muted-foreground/55 focus:border-brand/50 focus:outline-none"
      />
    </label>
  );
}

function NumericCell({
  value,
  onChange,
}: {
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <td className="px-3 py-2">
      <input
        value={value || ""}
        inputMode="decimal"
        onChange={(event) => onChange(numberValue(event.target.value))}
        className="h-9 w-[74px] rounded-lg border border-border/50 bg-background/50 px-2 text-right text-[12px] outline-none focus:border-brand/50"
      />
    </td>
  );
}

function QualityRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border border-border/45 bg-background/35 px-3 py-2.5">
      <span className="text-[12px] text-muted-foreground">{label}</span>
      <span className="text-right text-[13px] font-medium text-foreground">
        {value}
      </span>
    </div>
  );
}

function PrintableTechCard({ input }: { input: TechCardInput }) {
  const calculation = calculateTechCard(input);

  return (
    <section className="hidden print:block">
      <div className="mx-auto max-w-[760px] bg-white p-8 text-black">
        <p className="text-[11px] uppercase tracking-[0.18em] text-neutral-500">
          RECEPTOR · Технологическая карта
        </p>
        <h1 className="mt-3 text-3xl font-semibold">
          {input.dishName || "Новое блюдо"}
        </h1>
        <div className="mt-5 grid grid-cols-4 gap-3 text-sm">
          <PrintMetric label="Категория" value={input.category || "-"} />
          <PrintMetric label="Порций" value={String(input.portions || 1)} />
          <PrintMetric label="Выход" value={`${input.outputWeight || 0} г`} />
          <PrintMetric label="Себестоимость" value={formatRub(calculation.totalCost)} />
        </div>

        <table className="mt-8 w-full border-collapse text-left text-xs">
          <thead>
            <tr>
              <PrintTh>Ингредиент</PrintTh>
              <PrintTh>Брутто</PrintTh>
              <PrintTh>Нетто</PrintTh>
              <PrintTh>Потери</PrintTh>
              <PrintTh>Стоимость</PrintTh>
              <PrintTh>Артикул</PrintTh>
            </tr>
          </thead>
          <tbody>
            {calculation.ingredients.map((ingredient) => (
              <tr key={ingredient.id}>
                <PrintTd>{ingredient.name || "-"}</PrintTd>
                <PrintTd>{ingredient.grossQty} {ingredient.unit}</PrintTd>
                <PrintTd>{ingredient.netQty} {ingredient.unit}</PrintTd>
                <PrintTd>{ingredient.lossPercent}%</PrintTd>
                <PrintTd>{formatRub(ingredient.cost)}</PrintTd>
                <PrintTd>{ingredient.article || "-"}</PrintTd>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="mt-7 grid grid-cols-2 gap-4 text-sm">
          <PrintMetric
            label="Цена при целевом фудкосте"
            value={formatRub(calculation.recommendedPrice)}
          />
          <PrintMetric
            label="КБЖУ на 100 г"
            value={`${calculation.kcalPer100g} ккал / Б ${calculation.proteinPer100g} / Ж ${calculation.fatPer100g} / У ${calculation.carbsPer100g}`}
          />
        </div>

        <div className="mt-8">
          <h2 className="text-sm font-semibold uppercase tracking-[0.12em]">
            Технология
          </h2>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed">
            {input.process || "Технология приготовления не заполнена."}
          </p>
        </div>
      </div>
    </section>
  );
}

function PrintMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-neutral-300 p-3">
      <p className="text-[10px] uppercase tracking-[0.12em] text-neutral-500">
        {label}
      </p>
      <p className="mt-1 font-semibold">{value}</p>
    </div>
  );
}

function PrintTh({ children }: { children: ReactNode }) {
  return (
    <th className="border border-neutral-300 bg-neutral-100 px-2 py-2 font-semibold">
      {children}
    </th>
  );
}

function PrintTd({ children }: { children: ReactNode }) {
  return <td className="border border-neutral-300 px-2 py-2">{children}</td>;
}
