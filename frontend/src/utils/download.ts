import type { HistoryEntry } from "../types";
import { fileTimestamp } from "./format";

function downloadBlob(
  content: BlobPart,
  filename: string,
  type: string,
): void {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export function downloadJson(data: unknown, filename: string): void {
  downloadBlob(
    JSON.stringify(data, null, 2),
    filename,
    "application/json;charset=utf-8",
  );
}

function csvCell(value: unknown): string {
  const text = value === null || value === undefined ? "" : String(value);
  return `"${text.replace(/"/g, '""')}"`;
}

export function downloadHistoryCsv(entries: HistoryEntry[]): void {
  const header = [
    "Время",
    "Кандидат",
    "Должность",
    "Вердикт",
    "Оценка",
    "Критичных",
    "Средних",
    "Незначительных",
  ];

  const rows = entries.map((entry) => [
    entry.createdAt,
    entry.candidate,
    entry.position,
    entry.verdictLabel,
    entry.score ?? "",
    entry.high,
    entry.medium,
    entry.low,
  ]);

  const csv = [header, ...rows]
    .map((row) => row.map(csvCell).join(";"))
    .join("\r\n");

  // BOM нужен, чтобы Excel корректно открыл кириллицу.
  downloadBlob(
    `\uFEFF${csv}`,
    `candidate_history_${fileTimestamp()}.csv`,
    "text/csv;charset=utf-8",
  );
}
