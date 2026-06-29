export function normalizeTaskLabel(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const normalized = value.replace(/\s+/g, " ").trim();
  if (!normalized) return null;
  return normalized.length > 80
    ? `${normalized.slice(0, 77).trim()}...`
    : normalized;
}

export function normalizeTaskSourceLabel(value: unknown): string | null {
  return normalizeTaskLabel(value);
}

export function normalizeTaskImpactLabel(value: unknown): string | null {
  return normalizeTaskLabel(value);
}
