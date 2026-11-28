import type { ScreeningReport } from "./types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(
  /\/+$/,
  "",
);
const REQUEST_TIMEOUT_MS = 600_000;
const HEALTH_TIMEOUT_MS = 5_000;

export class ApiError extends Error {}

async function readErrorMessage(response: Response): Promise<string> {
  const raw = await response.text().catch(() => "");
  const text = raw.trim();
  if (!text) {
    return `Backend вернул ошибку ${response.status}.`;
  }

  try {
    const data = JSON.parse(text) as { detail?: unknown };
    if (typeof data.detail === "string") {
      return `Backend вернул ошибку ${response.status}: ${data.detail}`;
    }
    if (Array.isArray(data.detail)) {
      const details = data.detail
        .map((item) => {
          const record = item as { loc?: unknown; msg?: unknown };
          const loc = Array.isArray(record.loc) ? record.loc.join(".") : "";
          return [loc, String(record.msg ?? "")].filter(Boolean).join(": ");
        })
        .filter(Boolean)
        .join("; ");
      if (details) {
        return `Backend вернул ошибку ${response.status}: ${details}`;
      }
    }
  } catch {
    // Ответ не JSON — показываем безопасно обрезанный текст.
  }

  const short = text.length > 500 ? `${text.slice(0, 500)}…` : text;
  return `Backend вернул ошибку ${response.status}: ${short}`;
}

export async function screenCandidate(
  candidate: unknown,
): Promise<ScreeningReport> {
  const controller = new AbortController();
  const timer = window.setTimeout(
    () => controller.abort(),
    REQUEST_TIMEOUT_MS,
  );

  const payload = { candidate };

  try {
    const response = await fetch(`${API_BASE_URL}/screening/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new ApiError(await readErrorMessage(response));
    }

    return (await response.json()) as ScreeningReport;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError(
        "Backend не ответил за отведённое время (10 минут). Проверьте, что Ollama и FastAPI работают.",
      );
    }
    throw new ApiError(
      `Не удалось подключиться к backend (${API_BASE_URL || "текущий адрес"}). Проверьте, запущен ли FastAPI.`,
    );
  } finally {
    window.clearTimeout(timer);
  }
}

export async function checkHealth(): Promise<boolean> {
  const controller = new AbortController();
  const timer = window.setTimeout(
    () => controller.abort(),
    HEALTH_TIMEOUT_MS,
  );

  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      signal: controller.signal,
    });
    return response.ok;
  } catch {
    return false;
  } finally {
    window.clearTimeout(timer);
  }
}
