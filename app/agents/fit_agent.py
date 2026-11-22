"""LLM-агент оценки соответствия опыта кандидата целевой должности."""

from __future__ import annotations

from datetime import date
from typing import Any

from app.llm import chat_json
from app.prompts import FIT_EVALUATION
from app.schemas import CandidateProfile
from app.utils import career_span_years, describe_candidate

_ALLOWED_VERDICTS = {"suitable", "partially_suitable", "not_suitable"}
_ALLOWED_CONFIDENCE = {"high", "medium", "low"}

_DEFAULT_FIT: dict[str, Any] = {
    "verdict": "unknown",
    "score": None,
    "summary": "Оценка соответствия должности недоступна.",
    "strengths": [],
    "gaps": [],
    "matched_requirements": [],
    "unmatched_requirements": [],
    "relevant_experience_years": None,
    "required_experience_years": None,
    "confidence": "low",
}


def _as_text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        text = str(item).strip()
        if text:
            result.append(text)
    return result


def _as_score(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        score = int(float(value))
    except (TypeError, ValueError):
        return None
    return max(0, min(100, score))


def _as_years(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return round(float(value), 1)
    except (TypeError, ValueError):
        return None


def evaluate_fit(
    candidate: CandidateProfile,
    today: date | None = None,
) -> dict[str, Any]:
    """Оценивает соответствие профиля кандидата должности через LLM."""
    today = today or date.today()

    prompt = FIT_EVALUATION.format(
        candidate_summary=describe_candidate(candidate, today),
    )

    data = chat_json(prompt)

    verdict = str(data.get("verdict") or "").strip().lower()
    if verdict not in _ALLOWED_VERDICTS:
        verdict = "unknown"

    confidence = str(data.get("confidence") or "").strip().lower()
    if confidence not in _ALLOWED_CONFIDENCE:
        confidence = "low"

    relevant = _as_years(data.get("relevant_experience_years"))
    if relevant is None:
        relevant = career_span_years(candidate.experience, today)

    return {
        "verdict": verdict,
        "score": _as_score(data.get("score")),
        "summary": str(data.get("summary") or "").strip()
        or _DEFAULT_FIT["summary"],
        "strengths": _as_text_list(data.get("strengths")),
        "gaps": _as_text_list(data.get("gaps")),
        "matched_requirements": _as_text_list(
            data.get("matched_requirements")
        ),
        "unmatched_requirements": _as_text_list(
            data.get("unmatched_requirements")
        ),
        "relevant_experience_years": relevant,
        "required_experience_years": _as_years(
            data.get("required_experience_years")
        ),
        "confidence": confidence,
    }


def default_fit() -> dict[str, Any]:
    """Заготовка результата, если LLM-оценка не удалась."""
    return dict(_DEFAULT_FIT)
