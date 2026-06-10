"use client";

import { useMemo, useRef, useState, type ReactNode } from "react";
import {
  ArrowDownToLine,
  Building2,
  Copy,
  Download,
  FileText,
  Upload,
  Loader2,
  Plus,
  Printer,
  RotateCcw,
  Save,
  Sparkles,
  Trash2,
} from "lucide-react";
import {
  calculateTechCard,
  createTechCardLaunchPack,
  createTechCardMarkdown,
  evaluateTechCardQuality,
  formatRub,
  parseTechCardExportDocument,
  serializeTechCard,
  type TechCardQualityReport,
  type TechCardIngredient,
  type TechCardInput,
  type TechCardLaunchPack,
} from "@/lib/tools/tech-card";
import {
  DEFAULT_VENUE_INTELLIGENCE,
  type VenueIntelligenceProfile,
} from "@/lib/venues/intelligence";

type SavedTechCard = {
  id: string;
  savedAt: string;
  input: TechCardInput;
};

type DraftRunState =
  | { status: "idle" }
  | { status: "running" }
  | { status: "done"; provider: string; note: string }
  | { status: "error"; message: string };

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
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [input, setInput] = useState<TechCardInput>(() => emptyInput());
  const [venueProfile, setVenueProfile] = useState<VenueIntelligenceProfile>(
    DEFAULT_VENUE_INTELLIGENCE,
  );
  const [draftIdea, setDraftIdea] = useState("");
  const [draftRun, setDraftRun] = useState<DraftRunState>({ status: "idle" });
  const [fileMessage, setFileMessage] = useState("");
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
  const [launchCopied, setLaunchCopied] = useState(false);

  const calculation = useMemo(() => calculateTechCard(input), [input]);
  const quality = useMemo(
    () => evaluateTechCardQuality(input, calculation),
    [input, calculation],
  );
  const launchPack = useMemo(
    () => createTechCardLaunchPack(input, calculation, quality, venueProfile),
    [input, calculation, quality, venueProfile],
  );
  const markdown = useMemo(
    () => createTechCardMarkdown(input, calculation, venueProfile),
    [input, calculation, venueProfile],
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

  const copyLaunchPack = async () => {
    await navigator.clipboard.writeText(launchPack.markdown);
    setLaunchCopied(true);
    setTimeout(() => setLaunchCopied(false), 1600);
  };

  const printPdf = () => {
    window.print();
  };

  const exportJson = () => {
    const json = serializeTechCard(input, venueProfile);
    const blob = new Blob([json], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const safeName =
      input.dishName.trim().replace(/[^\p{L}\p{N}]+/gu, "-").replace(/^-|-$/g, "") ||
      "tech-card";
    link.href = url;
    link.download = `receptor-${safeName}.json`;
    link.click();
    URL.revokeObjectURL(url);
    setFileMessage("JSON-файл техкарты скачан.");
  };

  const importJson = async (file: File | null) => {
    if (!file) return;
    try {
      const text = await file.text();
      const document = parseTechCardExportDocument(text);
      setInput(document.input);
      if (document.venueProfile) setVenueProfile(document.venueProfile);
      setDraftIdea(document.input.dishName);
      setFileMessage("Техкарта импортирована из JSON.");
    } catch (err) {
      setFileMessage(
        err instanceof Error ? err.message : "Не удалось импортировать JSON.",
      );
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const reset = () => {
    setInput(emptyInput());
    setDraftIdea("");
    setCopied(false);
  };

  const generateDraft = async () => {
    const idea = draftIdea.trim() || input.dishName.trim();
    if (!idea || draftRun.status === "running") return;

    setDraftRun({ status: "running" });
    try {
      const response = await fetch("/api/tools/tech-card-draft", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          idea,
          category: input.category,
          portions: input.portions,
          targetFoodCostPercent: input.targetFoodCostPercent,
          venueProfile,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        setDraftRun({
          status: "error",
          message: data.error ?? `HTTP ${response.status}`,
        });
        return;
      }
      setInput(data.input);
      setDraftIdea(data.input.dishName || idea);
      setDraftRun({
        status: "done",
        provider: data.provider ?? "fallback",
        note: data.note ?? "Черновик готов.",
      });
    } catch (err) {
      setDraftRun({
        status: "error",
        message: err instanceof Error ? err.message : "network error",
      });
    }
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
              <ActionButton onClick={exportJson} icon={<Download className="size-4" />}>
                JSON
              </ActionButton>
              <ActionButton
                onClick={() => fileInputRef.current?.click()}
                icon={<Upload className="size-4" />}
              >
                Импорт
              </ActionButton>
              <ActionButton onClick={printPdf} icon={<Printer className="size-4" />}>
                PDF
              </ActionButton>
              <ActionButton onClick={reset} icon={<RotateCcw className="size-4" />}>
                Очистить
              </ActionButton>
            </div>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/json,.json"
            className="hidden"
            onChange={(event) => {
              void importJson(event.target.files?.[0] ?? null);
            }}
          />
          {fileMessage ? (
            <p className="mt-4 rounded-lg border border-border/50 bg-background/35 px-3 py-2 text-[12px] leading-relaxed text-muted-foreground">
              {fileMessage}
            </p>
          ) : null}

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

          <DraftGeneratorPanel
            idea={draftIdea}
            state={draftRun}
            onIdeaChange={setDraftIdea}
            onGenerate={generateDraft}
          />

          <VenueProfileStrip
            profile={venueProfile}
            onChange={setVenueProfile}
          />

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
            <QualityPreflight report={quality} />
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

          <LaunchPackPanel
            pack={launchPack}
            copied={launchCopied}
            onCopy={copyLaunchPack}
          />

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

      <PrintableTechCard input={input} venueProfile={venueProfile} />
    </div>
  );
}

function DraftGeneratorPanel({
  idea,
  state,
  onIdeaChange,
  onGenerate,
}: {
  idea: string;
  state: DraftRunState;
  onIdeaChange: (value: string) => void;
  onGenerate: () => void;
}) {
  return (
    <section className="mt-6 rounded-xl border border-[color:var(--ai)]/25 bg-[color:var(--ai)]/[0.05] p-4">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 text-[color:var(--ai)]">
            <Sparkles className="size-4" />
            <p className="text-[11px] uppercase tracking-[0.18em]">
              AI-черновик
            </p>
          </div>
          <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">
            Введите идею блюда. Receptor набросает ингредиенты, граммовки,
            КБЖУ, цену и технологию с учётом профиля заведения.
          </p>
        </div>
        <div className="flex w-full flex-col gap-2 lg:w-[420px]">
          <div className="flex flex-col gap-2 sm:flex-row">
            <input
              value={idea}
              onChange={(event) => onIdeaChange(event.target.value)}
              placeholder="Например: цезарь с креветками в премиальной подаче"
              className="h-10 min-w-0 flex-1 rounded-lg border border-border/60 bg-background/55 px-3.5 text-sm text-foreground placeholder:text-muted-foreground/55 focus:border-brand/50 focus:outline-none"
            />
            <button
              type="button"
              onClick={onGenerate}
              disabled={!idea.trim() || state.status === "running"}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-brand px-4 text-[13px] font-medium text-primary-foreground transition hover:bg-brand-hover disabled:opacity-45"
            >
              {state.status === "running" ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Собираю
                </>
              ) : (
                <>
                  <Sparkles className="size-4" />
                  Заполнить
                </>
              )}
            </button>
          </div>
          {state.status === "done" ? (
            <p className="text-[12px] leading-relaxed text-muted-foreground">
              {state.provider === "openai" ? "OpenAI" : "Receptor fallback"}:{" "}
              {state.note}
            </p>
          ) : state.status === "error" ? (
            <p className="text-[12px] leading-relaxed text-destructive">
              Ошибка: {state.message}
            </p>
          ) : null}
        </div>
      </div>
    </section>
  );
}

function VenueProfileStrip({
  profile,
  onChange,
}: {
  profile: VenueIntelligenceProfile;
  onChange: (profile: VenueIntelligenceProfile) => void;
}) {
  const update = (patch: Partial<VenueIntelligenceProfile>) => {
    onChange({ ...profile, ...patch });
  };

  return (
    <section className="mt-6 rounded-xl border border-brand/25 bg-brand/[0.045] p-4">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg border border-brand/30 bg-brand/10 text-brand">
          <Building2 className="size-4" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-[11px] uppercase tracking-[0.18em] text-brand">
            Профиль заведения
          </p>
          <p className="mt-1 text-[13px] leading-relaxed text-muted-foreground">
            Техкарта сохраняет контекст концепции. Позже Copilot сможет
            автособирать блюда и меню именно под этот профиль.
          </p>
        </div>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <label className="grid gap-1.5">
          <span className="text-[12px] font-medium text-foreground">Формат</span>
          <input
            value={profile.format}
            onChange={(event) => update({ format: event.target.value })}
            className="h-9 rounded-lg border border-border/60 bg-background/55 px-3 text-[13px] outline-none focus:border-brand/50"
          />
        </label>
        <label className="grid gap-1.5">
          <span className="text-[12px] font-medium text-foreground">
            Цель владельца
          </span>
          <input
            value={profile.ownerGoals[0] ?? ""}
            onChange={(event) =>
              update({
                ownerGoals: [
                  event.target.value,
                  ...profile.ownerGoals.slice(1),
                ].filter(Boolean),
              })
            }
            className="h-9 rounded-lg border border-border/60 bg-background/55 px-3 text-[13px] outline-none focus:border-brand/50"
          />
        </label>
      </div>
      <label className="mt-3 grid gap-1.5">
        <span className="text-[12px] font-medium text-foreground">
          Позиционирование
        </span>
        <textarea
          value={profile.positioning}
          onChange={(event) => update({ positioning: event.target.value })}
          rows={2}
          className="min-h-[70px] rounded-lg border border-border/60 bg-background/55 px-3 py-2 text-[13px] leading-relaxed outline-none focus:border-brand/50"
        />
      </label>
    </section>
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

function LaunchPackPanel({
  pack,
  copied,
  onCopy,
}: {
  pack: TechCardLaunchPack;
  copied: boolean;
  onCopy: () => void;
}) {
  return (
    <section className="rounded-xl border border-border/60 bg-card/35 p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-[color:var(--ai)]">
            <Sparkles className="size-4" />
            <p className="text-[11px] uppercase tracking-[0.18em]">
              Launch Pack
            </p>
          </div>
          <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">
            Материалы, чтобы блюдо не просто появилось в меню, а продавалось
            залом.
          </p>
        </div>
        <button
          type="button"
          onClick={onCopy}
          className="inline-flex h-8 shrink-0 items-center gap-2 rounded-lg border border-border/60 bg-background/40 px-3 text-[12px] text-muted-foreground transition-colors hover:bg-card hover:text-foreground"
        >
          <Copy className="size-3.5" />
          {copied ? "Скопировано" : "Copy"}
        </button>
      </div>

      <div className="mt-5 space-y-4">
        <div>
          <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
            Описание для меню
          </p>
          <p className="mt-2 text-[13px] leading-relaxed text-foreground/85">
            {pack.menuDescription}
          </p>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
            Скрипт официанта
          </p>
          <p className="mt-2 text-[13px] leading-relaxed text-foreground/85">
            {pack.waiterPitch}
          </p>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
            Upsell
          </p>
          <ul className="mt-2 space-y-1.5 text-[12px] leading-relaxed text-muted-foreground">
            {pack.upsellIdeas.map((idea) => (
              <li key={idea}>• {idea}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

function QualityPreflight({ report }: { report: TechCardQualityReport }) {
  const statusClass =
    report.status === "ok"
      ? "border-brand/35 bg-brand/10 text-brand"
      : report.status === "critical"
        ? "border-destructive/35 bg-destructive/10 text-destructive"
        : "border-[color:var(--pro)]/35 bg-[color:var(--pro)]/10 text-[color:var(--pro)]";
  const label =
    report.status === "ok"
      ? "Готово"
      : report.status === "critical"
        ? "Блокеры"
        : "Проверить";

  return (
    <div className="mt-5 rounded-xl border border-border/55 bg-background/35 p-4">
      <div className="flex items-center justify-between gap-3">
        <span
          className={
            "rounded-full border px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] " +
            statusClass
          }
        >
          {label}
        </span>
        <div className="text-right">
          <p className="text-2xl font-medium tracking-[-0.02em] text-foreground">
            {report.score}
          </p>
          <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
            score
          </p>
        </div>
      </div>

      {report.issues.length > 0 ? (
        <div className="mt-4 space-y-2">
          {report.issues.slice(0, 5).map((issue) => (
            <div
              key={`${issue.severity}-${issue.title}`}
              className="rounded-lg border border-border/45 bg-card/35 p-3"
            >
              <p
                className={
                  "text-[13px] font-medium " +
                  (issue.severity === "critical"
                    ? "text-destructive"
                    : "text-foreground")
                }
              >
                {issue.title}
              </p>
              <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
                {issue.description}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-4 text-[13px] leading-relaxed text-muted-foreground">
          Блокеров нет. Техкарту можно печатать или готовить к iiko-маппингу.
        </p>
      )}

      <div className="mt-4 border-t border-border/40 pt-3">
        <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
          Следующие действия
        </p>
        <ul className="mt-2 space-y-1.5 text-[12px] leading-relaxed text-muted-foreground">
          {report.nextActions.map((action) => (
            <li key={action}>• {action}</li>
          ))}
        </ul>
      </div>
    </div>
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

function PrintableTechCard({
  input,
  venueProfile,
}: {
  input: TechCardInput;
  venueProfile: VenueIntelligenceProfile;
}) {
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

        <div className="mt-5 border border-neutral-300 p-3 text-xs">
          <p className="font-semibold uppercase tracking-[0.12em] text-neutral-500">
            Контекст заведения
          </p>
          <p className="mt-2 leading-relaxed">
            {venueProfile.format}. {venueProfile.positioning}
          </p>
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
