const MAX_FILE_SIZE = 5 * 1024 * 1024;

export function parseCandidate(raw: string): unknown {
  const text = raw.trim().replace(/^\uFEFF/, "");
  if (!text) {
    throw new Error("Загрузите/перенесите JSON-файл в область загрузки.");
  }

  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch (error) {
    throw new Error(`Некорректный JSON: ${(error as Error).message}`, { cause: error });
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
  const bytes = new Uint8Array(buffer);
  const bomEncoding =
    bytes[0] === 0xff && bytes[1] === 0xfe
      ? "utf-16le"
      : bytes[0] === 0xfe && bytes[1] === 0xff
        ? "utf-16be"
        : null;
  const encodings = bomEncoding
    ? [bomEncoding, "utf-8", "windows-1251"]
    : ["utf-8", "windows-1251"];

  for (const encoding of encodings) {
    try {
      return new TextDecoder(encoding, { fatal: true })
        .decode(buffer)
        .replace(/^\uFEFF/, "");
    } catch {
      // Пробуем следующую кодировку.
    }
  }
  throw new Error("Не удалось определить кодировку файла.");
}
