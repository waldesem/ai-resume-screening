import { ref, watch } from "vue";

import type { HistoryEntry, ScreeningReport } from "../types";
import { formatTimestamp, verdictLabel } from "../utils/format";

const STORAGE_KEY = "AI-resume-screening:history:v1";
const MAX_ENTRIES = 200;

function isHistoryEntry(value: unknown): value is HistoryEntry {
  if (!value || typeof value !== "object") {
    return false;
  }
  const entry = value as Record<string, unknown>;
  return (
    typeof entry.id === "string" &&
    typeof entry.createdAt === "string" &&
    typeof entry.candidate === "string" &&
    typeof entry.position === "string"
  );
}

function loadHistory(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter(isHistoryEntry) : [];
  } catch {
    return [];
  }
}

export function useHistory() {
  const entries = ref<HistoryEntry[]>(loadHistory());

  watch(
    entries,
    (value) => {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
      } catch {
        // Хранилище может быть недоступно или переполнено — не мешаем работе.
      }
    },
    { deep: true },
  );

  function add(report: ScreeningReport): void {
    const candidate = report.candidate ?? {};
    const fit = report.fit ?? {};
    const counts = report.contradictions?.counts ?? {};

    const entry: HistoryEntry = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      createdAt: formatTimestamp(new Date()),
      candidate: candidate.full_name || "—",
      position: candidate.position_name || "—",
      verdict: fit.verdict || "unknown",
      verdictLabel: verdictLabel(fit.verdict),
      score: fit.score ?? null,
      high: counts.high ?? 0,
      medium: counts.medium ?? 0,
      low: counts.low ?? 0,
    };

    entries.value = [entry, ...entries.value].slice(0, MAX_ENTRIES);
  }

  function clear(): void {
    entries.value = [];
  }

  return { entries, add, clear };
}
