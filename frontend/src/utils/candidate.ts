const MAX_FILE_SIZE = 5 * 1024 * 1024;

export function parseCandidate(raw: string): unknown {
  const text = raw.trim();
  if (!text) {
    throw new Error("Загрузите JSON-файл анкеты или вставьте JSON в поле.");
  }

  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch (error) {
    throw new Error(`Некорректный JSON: ${(error as Error).message}`);
  }

  if (data === null || typeof data !== "object" || Array.isArray(data)) {
    throw new Error("Ожидался JSON-объект с данными анкеты.");
  }

  const record = data as Record<string, unknown>;
  const nested = record.candidate;
  if (nested && typeof nested === "object" && !Array.isArray(nested)) {
    return nested;
  }
  return record;
}

export async function readCandidateFile(file: File): Promise<string> {
  if (file.size > MAX_FILE_SIZE) {
    throw new Error("Файл слишком большой: максимум 5 МБ.");
  }

  const buffer = await file.arrayBuffer();
  for (const encoding of ["utf-8", "windows-1251"]) {
    try {
      return new TextDecoder(encoding, { fatal: true }).decode(buffer);
    } catch {
      // Пробуем следующую кодировку.
    }
  }
  throw new Error("Не удалось определить кодировку файла.");
}
