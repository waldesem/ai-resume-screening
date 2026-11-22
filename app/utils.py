"""Вспомогательные функции: разбор дат, расчёт возраста и стажа,
подготовка текстовой сводки анкеты для LLM.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from app.schemas import CandidateProfile, ExperienceEntry

_DATE_FORMATS = (
    "%Y-%m-%d",
    "%d.%m.%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%d/%m/%Y",
    "%Y-%m",
    "%m.%Y",
    "%Y",
)


def parse_date(value: Any) -> date | None:
    """Разбирает дату из строки в распространённых форматах.

    Поддерживаются ``2020-03-01``, ``01.03.2020``, ``2020-03``, ``2020``.
    Возвращает ``None``, если значение пустое или не распознано.
    """
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    text = str(value).strip()
    if not text:
        return None

    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def months_between(start: date, end: date) -> int:
    """Количество полных месяцев между датами (не меньше нуля)."""
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        months -= 1
    return max(months, 0)


def age_on(birthday: date, today: date) -> int:
    """Полных лет на указанную дату."""
    return (
        today.year
        - birthday.year
        - ((today.month, today.day) < (birthday.month, birthday.day))
    )


def earliest_experience_start(
    experience: list[ExperienceEntry],
) -> date | None:
    """Самая ранняя распознанная дата начала работы."""
    starts = [parse_date(item.begin_date) for item in experience]
    valid = [start for start in starts if start is not None]
    return min(valid) if valid else None


def career_span_years(
    experience: list[ExperienceEntry], today: date | None = None
) -> float:
    """Стаж по датам: от самого раннего начала работы до сегодняшнего дня.

    Схема анкеты не содержит дату окончания прошлых мест работы, поэтому
    точную сумму периодов посчитать нельзя — используется общий интервал
    карьеры как верхняя оценка стажа.
    """
    today = today or date.today()
    start = earliest_experience_start(experience)
    if start is None:
        return 0.0
    return round(months_between(start, today) / 12, 1)


def current_job_years(
    experience: list[ExperienceEntry], today: date | None = None
) -> float:
    """Суммарная длительность текущих мест работы (по датам начала)."""
    today = today or date.today()
    total_months = 0
    for item in experience:
        if not item.current_job:
            continue
        start = parse_date(item.begin_date)
        if start is None:
            continue
        total_months += months_between(start, today)
    return round(total_months / 12, 1)


def candidate_json(candidate: CandidateProfile) -> str:
    """Исходная анкета в JSON (camelCase) для передачи в промпт."""
    return json.dumps(
        candidate.model_dump(by_alias=True), ensure_ascii=False, indent=2
    )


def describe_candidate(
    candidate: CandidateProfile, today: date | None = None
) -> str:
    """Человекочитаемая сводка анкеты для промптов LLM."""
    today = today or date.today()
    lines: list[str] = [
        f"Целевая должность: {candidate.position_name or '—'}",
        f"Подразделение: {candidate.department or '—'}",
        f"ФИО: {candidate.full_name or '—'}",
    ]

    birth = parse_date(candidate.birthday)
    if birth:
        lines.append(
            f"Дата рождения: {birth.isoformat()} "
            f"(возраст: {age_on(birth, today)} лет)"
        )
    else:
        lines.append(f"Дата рождения: {candidate.birthday or '—'}")

    lines.append(f"Гражданство: {candidate.citizen or '—'}")

    lines.append("Образование:")
    if candidate.education:
        for item in candidate.education:
            period = f"{item.begin_year or '?'}–{item.end_year or '?'}"
            lines.append(
                f"  - {period}: {item.institution_name or '—'}, "
                f"специальность: {item.specialty or '—'}, "
                f"тип: {item.education_type or '—'}"
            )
    else:
        lines.append("  - не указано")

    lines.append("Опыт работы:")
    if candidate.experience:
        for item in candidate.experience:
            if item.current_job:
                period = f"с {item.begin_date or '?'} по настоящее время"
            elif item.end_date:
                period = f"с {item.begin_date or '?'} по {item.end_date}"
            else:
                period = (
                    f"с {item.begin_date or '?'} "
                    "(дата окончания в анкете не указана)"
                )
            reason = (
                f", причина увольнения: {item.reason}" if item.reason else ""
            )
            lines.append(
                f"  - {period}: {item.name or '—'}, "
                f"должность: {item.position or '—'}, "
                f"сфера: {item.activity_type or '—'}{reason}"
            )
    else:
        lines.append("  - не указан")

    if candidate.organizations:
        lines.append("Организации кандидата (раздел organizations):")
        for item in candidate.organizations:
            lines.append(
                f"  - {item.organization or '—'}, "
                f"вид деятельности: {item.view or '—'}, "
                f"ИНН: {item.inn or '—'}"
            )

    start = earliest_experience_start(candidate.experience)
    if start:
        lines.append(
            f"Начало карьеры по анкете: {start.isoformat()} "
            f"(общий интервал карьеры: "
            f"{career_span_years(candidate.experience, today)} лет)"
        )
    lines.append(
        "Текущее место работы по флагу hasJob: "
        f"{'есть' if candidate.has_job else 'нет'}"
    )
    return "\n".join(lines)
