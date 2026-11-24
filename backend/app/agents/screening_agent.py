"""Оркестратор проверки анкеты: правила + LLM-противоречия + соответствие."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.agents.contradiction_agent import analyze_contradictions
from app.agents.fit_agent import default_fit, evaluate_fit
from app.tools.checks import run_rule_checks, sort_findings
from app.models.llm import LLMError, get_model
from app.schema.schemas import CandidateProfile
from app.tools.utils import (
    age_on,
    career_span_years,
    earliest_experience_start,
    parse_date,
)

_VERDICT_TEXT = {
    "suitable": "опыт и профиль соответствуют целевой должности",
    "partially_suitable": "опыт соответствует должности частично",
    "not_suitable": "опыт не соответствует целевой должности",
    "unknown": "соответствие должности не оценено",
}


def _severity_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"high": 0, "medium": 0, "low": 0}
    for item in items:
        severity = item.get("severity")
        if severity in counts:
            counts[severity] += 1
    return counts


def _build_recommendation(fit: dict[str, Any], counts: dict[str, int]) -> str:
    verdict = fit.get("verdict", "unknown")
    parts = [f"Вердикт по соответствию: {_VERDICT_TEXT.get(verdict, verdict)}."]

    if counts["high"]:
        parts.append(
            f"Найдено критичных противоречий: {counts['high']}. "
            "Анкету нельзя использовать без ручной проверки и уточнений "
            "у кандидата."
        )
    elif counts["medium"]:
        parts.append(
            f"Найдено противоречий средней важности: {counts['medium']}. "
            "Рекомендуется уточнить данные у кандидата перед решением."
        )
    else:
        parts.append("Критичных внутренних противоречий не выявлено.")

    if verdict == "not_suitable":
        parts.append("Кандидата не рекомендуется рассматривать на эту должность.")
    elif verdict == "suitable" and not counts["high"]:
        parts.append("Кандидата рекомендуется передать нанимающему менеджеру.")
    elif verdict == "partially_suitable":
        parts.append(
            "Кандидата можно рассмотреть при условии закрытия отмеченных пробелов."
        )

    return " ".join(parts)


def _candidate_facts(candidate: CandidateProfile, today: date) -> dict[str, Any]:
    birth = parse_date(candidate.birthday)
    career_start = earliest_experience_start(candidate.experience)
    return {
        "full_name": candidate.full_name,
        "position_name": candidate.position_name,
        "department": candidate.department,
        "age": age_on(birth, today) if birth else None,
        "career_start": career_start.isoformat() if career_start else None,
        "career_span_years": career_span_years(candidate.experience, today),
        "has_job": candidate.has_job,
        "education_count": len(candidate.education),
        "experience_count": len(candidate.experience),
    }


def screen_candidate(candidate: CandidateProfile) -> dict[str, Any]:
    """Полный цикл проверки анкеты и формирования отчёта."""
    today = date.today()
    errors: list[dict[str, str]] = []

    rule_items = run_rule_checks(candidate, today)

    llm_result: dict[str, Any] = {"items": [], "summary": ""}
    try:
        llm_result = analyze_contradictions(candidate, rule_items, today)
    except LLMError as exc:
        errors.append({"stage": "contradictions", "message": str(exc)})

    all_items = sort_findings(rule_items + list(llm_result.get("items") or []))
    counts = _severity_counts(all_items)

    try:
        fit = evaluate_fit(candidate, today)
    except LLMError as exc:
        errors.append({"stage": "fit", "message": str(exc)})
        fit = default_fit()

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "model": get_model(),
        "candidate": _candidate_facts(candidate, today),
        "contradictions": {
            "has_contradictions": bool(all_items),
            "counts": counts,
            "items": all_items,
            "summary": llm_result.get("summary", ""),
        },
        "fit": fit,
        "recommendation": _build_recommendation(fit, counts),
        "analysis_errors": errors,
    }
