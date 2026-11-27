const VERDICT_LABELS: Record<string, string> = {
  suitable: "Соответствует",
  partially_suitable: "Частично соответствует",
  not_suitable: "Не соответствует",
  unknown: "Не оценено",
};

const SEVERITY_LABELS: Record<string, string> = {
  high: "Критично",
  medium: "Средне",
  low: "Незначительно",
};

const CONFIDENCE_LABELS: Record<string, string> = {
  high: "высокая",
  medium: "средняя",
  low: "низкая",
};

export function verdictLabel(verdict?: string | null): string {
  if (!verdict) {
    return "—";
  }
  return VERDICT_LABELS[verdict] ?? verdict;
}

export function verdictClass(
  verdict?: string | null,
): "success" | "warning" | "danger" | "neutral" {
  switch (verdict) {
    case "suitable":
      return "success";
    case "partially_suitable":
      return "warning";
    case "not_suitable":
      return "danger";
    default:
      return "neutral";
  }
}

export function severityLabel(severity?: string | null): string {
  if (!severity) {
    return "—";
  }
  return SEVERITY_LABELS[severity] ?? severity;
}

export function severityClass(
  severity?: string | null,
): "error" | "danger" | "warning" {
  switch (severity) {
    case "high":
      return "error";
    case "medium":
      return "danger";
    default:
      return "warning";
  }
}

export function confidenceLabel(confidence?: string | null): string {
  if (!confidence) {
    return "—";
  }
  return CONFIDENCE_LABELS[confidence] ?? confidence;
}

export function formatYears(value?: number | null): string {
  if (value === null || value === undefined) {
    return "—";
  }

  const absolute = Math.abs(value);
  let suffix = "лет";

  if (Number.isInteger(absolute)) {
    const mod10 = absolute % 10;
    const mod100 = absolute % 100;
    if (mod10 === 1 && mod100 !== 11) {
      suffix = "год";
    } else if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
      suffix = "года";
    }
  } else {
    suffix = "года";
  }

  return `${value} ${suffix}`;
}
