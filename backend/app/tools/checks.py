"""Детерминированные (без LLM) проверки анкеты кандидата.

Здесь ищутся объективные противоречия: несогласованные даты, флаги
документов, невозможный возраст начала карьеры, пересечения периодов
обучения и т.п. Смысловые противоречия, требующие рассуждения, ищет
LLM-агент (``app/agents/contradiction_agent.py``).
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from app.schema.schemas import CandidateProfile
from app.tools.utils import (
    age_on,
    career_span_years,
    earliest_experience_start,
    parse_date,
)

SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}
SEVERITY_LABELS = {
    "high": "Критично",
    "medium": "Средне",
    "low": "Незначительно",
}

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")


def make_item(
    severity: str,
    title: str,
    description: str,
    fields: list[str] | None = None,
    source: str = "rule",
) -> dict[str, Any]:
    """Собирает одну находку проверки в едином формате."""
    if severity not in SEVERITY_RANK:
        severity = "medium"
    return {
        "severity": severity,
        "title": title,
        "description": description,
        "fields": fields or [],
        "source": source,
    }


def sort_findings(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Сортирует находки по убыванию важности."""
    return sorted(items, key=lambda item: SEVERITY_RANK.get(item.get("severity"), 3))


def _digits(value: str | None) -> str:
    return re.sub(r"\D", "", value or "")


def _check_identity(
    candidate: CandidateProfile,
    birth: date | None,
    age: int | None,
    today: date,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    if not candidate.position_name:
        items.append(
            make_item(
                "medium",
                "position_missing",
                "Не указана целевая должность",
                "Поле positionName пустое, поэтому соответствие опыта "
                "должности невозможно оценить корректно.",
                ["positionName"],
            )
        )
    if not candidate.full_name:
        items.append(
            make_item(
                "medium",
                "name_missing",
                "Не указаны фамилия и имя",
                "Поля lastName и firstName пустые — анкета не идентифицирует "
                "кандидата.",
                ["lastName", "firstName"],
            )
        )
    if not candidate.department:
        items.append(
            make_item(
                "low",
                "department_missing",
                "Не указано подразделение",
                "Поле department пустое — неясно, в какое подразделение "
                "рассматривается кандидат.",
                ["department"],
            )
        )

    if not candidate.birthday:
        items.append(
            make_item(
                "low",
                "birthday_missing",
                "Не указана дата рождения",
                "Без даты рождения нельзя проверить правдоподобность периодов "
                "обучения и начала карьеры.",
                ["birthday"],
            )
        )
    elif birth is None:
        items.append(
            make_item(
                "medium",
                "birthday_invalid",
                "Дата рождения не распознана",
                f"Значение birthday={candidate.birthday!r} не удалось "
                "разобрать как дату.",
                ["birthday"],
            )
        )
    elif age is not None and age < 14:
        items.append(
            make_item(
                "high",
                "age_too_low",
                "Невозможный возраст кандидата",
                f"По дате рождения кандидату {age} лет. Трудоустройство "
                "в таком возрасте невозможно.",
                ["birthday"],
            )
        )
    elif age is not None and age < 18:
        items.append(
            make_item(
                "medium",
                "candidate_minor",
                "Кандидат несовершеннолетний",
                f"По дате рождения кандидату {age} лет. Требуется проверка "
                "правовых ограничений на трудоустройство.",
                ["birthday"],
            )
        )

    return items


def _check_contacts(candidate: CandidateProfile) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    if not candidate.email:
        items.append(
            make_item(
                "low",
                "email_missing",
                "Не указан e-mail",
                "Поле email пустое — связаться с кандидатом по электронной "
                "почте нельзя.",
                ["email"],
            )
        )
    elif not _EMAIL_RE.match(candidate.email):
        items.append(
            make_item(
                "low",
                "email_invalid",
                "Некорректный e-mail",
                f"Значение email={candidate.email!r} не похоже на адрес "
                "электронной почты.",
                ["email"],
            )
        )

    if not candidate.contact_phone:
        items.append(
            make_item(
                "low",
                "phone_missing",
                "Не указан телефон",
                "Поле contactPhone пустое.",
                ["contactPhone"],
            )
        )
    elif len(_digits(candidate.contact_phone)) < 10:
        items.append(
            make_item(
                "low",
                "phone_invalid",
                "Некорректный телефон",
                f"В contactPhone={candidate.contact_phone!r} меньше 10 цифр.",
                ["contactPhone"],
            )
        )

    return items


def _check_documents(candidate: CandidateProfile) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    inn_digits = _digits(candidate.inn)
    if candidate.has_inn and not inn_digits:
        items.append(
            make_item(
                "medium",
                "inn_flag_without_value",
                "ИНН отмечен, но не заполнен",
                "hasInn=true, при этом поле inn пустое.",
                ["hasInn", "inn"],
            )
        )
    if not candidate.has_inn and inn_digits:
        items.append(
            make_item(
                "medium",
                "inn_value_without_flag",
                "ИНН заполнен, но не отмечен",
                "Поле inn заполнено, при этом hasInn=false.",
                ["hasInn", "inn"],
            )
        )
    if inn_digits and len(inn_digits) not in (10, 12):
        items.append(
            make_item(
                "low",
                "inn_invalid_length",
                "Некорректная длина ИНН",
                f"В ИНН {len(inn_digits)} цифр, ожидается 10 или 12.",
                ["inn"],
            )
        )

    snils_digits = _digits(candidate.snils)
    if candidate.has_snils and not snils_digits:
        items.append(
            make_item(
                "medium",
                "snils_flag_without_value",
                "СНИЛС отмечен, но не заполнен",
                "hasSnils=true, при этом поле snils пустое.",
                ["hasSnils", "snils"],
            )
        )
    if not candidate.has_snils and snils_digits:
        items.append(
            make_item(
                "medium",
                "snils_value_without_flag",
                "СНИЛС заполнен, но не отмечен",
                "Поле snils заполнено, при этом hasSnils=false.",
                ["hasSnils", "snils"],
            )
        )
    if snils_digits and len(snils_digits) != 11:
        items.append(
            make_item(
                "low",
                "snils_invalid_length",
                "Некорректная длина СНИЛС",
                f"В СНИЛС {len(snils_digits)} цифр, ожидается 11.",
                ["snils"],
            )
        )

    if candidate.has_additional_citizenship and not candidate.citizen:
        items.append(
            make_item(
                "low",
                "citizenship_missing",
                "Не указано гражданство",
                "hasAdditionalCitizenship=true, но поле citizen пустое.",
                ["hasAdditionalCitizenship", "citizen"],
            )
        )

    return items


def _check_passport(
    candidate: CandidateProfile, birth: date | None, today: date
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    serial = candidate.passport_serial
    number = candidate.passport_number
    issue_date = parse_date(candidate.passport_issue_date)

    if bool(serial) != bool(number):
        items.append(
            make_item(
                "low",
                "passport_incomplete",
                "Паспортные данные заполнены частично",
                "Указана только серия или только номер паспорта.",
                ["passportSerial", "passportNumber"],
            )
        )
    if (serial or number) and not candidate.passport_issue_date:
        items.append(
            make_item(
                "low",
                "passport_issue_date_missing",
                "Не указана дата выдачи паспорта",
                "Серия и номер паспорта заполнены, а passportIssueDate пустая.",
                ["passportIssueDate"],
            )
        )
    if candidate.passport_issue_date and issue_date is None:
        items.append(
            make_item(
                "low",
                "passport_issue_date_invalid",
                "Дата выдачи паспорта не распознана",
                f"Значение passportIssueDate="
                f"{candidate.passport_issue_date!r} не является датой.",
                ["passportIssueDate"],
            )
        )
    elif issue_date is not None:
        if issue_date > today:
            items.append(
                make_item(
                    "high",
                    "passport_issue_date_future",
                    "Дата выдачи паспорта в будущем",
                    f"passportIssueDate={issue_date.isoformat()} позже текущей даты.",
                    ["passportIssueDate"],
                )
            )
        if birth is not None:
            age_at_issue = age_on(birth, issue_date)
            if age_at_issue < 14:
                items.append(
                    make_item(
                        "high",
                        "passport_issued_too_early",
                        "Паспорт выдан слишком рано",
                        f"На дату выдачи паспорта кандидату было "
                        f"{age_at_issue} лет, паспорт РФ выдаётся с 14 лет.",
                        ["passportIssueDate", "birthday"],
                    )
                )

    return items


def _check_education(
    candidate: CandidateProfile, birth: date | None, today: date
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    education = candidate.education

    if not education:
        items.append(
            make_item(
                "low",
                "education_missing",
                "Образование не указано",
                "Раздел education пуст.",
                ["education"],
            )
        )
        return items

    intervals: list[tuple[int, int]] = []
    for index, item in enumerate(education):
        prefix = f"education[{index}]"
        begin = item.begin_year
        end = item.end_year

        if not item.institution_name:
            items.append(
                make_item(
                    "low",
                    f"education_{index}_institution_missing",
                    "Не указано учебное заведение",
                    f"В записи {prefix} пустое поле institutionName.",
                    [f"{prefix}.institutionName"],
                )
            )
        if not item.specialty:
            items.append(
                make_item(
                    "low",
                    f"education_{index}_specialty_missing",
                    "Не указана специальность",
                    f"В записи {prefix} пустое поле specialty.",
                    [f"{prefix}.specialty"],
                )
            )

        if begin is not None and end is not None and end < begin:
            items.append(
                make_item(
                    "high",
                    f"education_{index}_dates_reversed",
                    "Годы обучения противоречат друг другу",
                    f"В записи {prefix} год окончания ({end}) раньше года "
                    f"начала ({begin}).",
                    [f"{prefix}.beginYear", f"{prefix}.endYear"],
                )
            )

        if begin is not None:
            if begin > today.year:
                items.append(
                    make_item(
                        "high",
                        f"education_{index}_begin_future",
                        "Обучение начинается в будущем",
                        f"В записи {prefix} beginYear={begin} больше "
                        f"текущего года ({today.year}).",
                        [f"{prefix}.beginYear"],
                    )
                )
            if birth is not None:
                age_at_start = begin - birth.year
                if age_at_start < 10:
                    items.append(
                        make_item(
                            "high",
                            f"education_{index}_too_early",
                            "Обучение началось в слишком раннем возрасте",
                            f"В записи {prefix} обучение начинается в "
                            f"{begin} году, кандидат родился в "
                            f"{birth.year} году (возраст {age_at_start}).",
                            [f"{prefix}.beginYear", "birthday"],
                        )
                    )

        if end is not None and end > today.year:
            items.append(
                make_item(
                    "low",
                    f"education_{index}_end_future",
                    "Дата окончания обучения в будущем",
                    f"В записи {prefix} endYear={end} больше текущего года "
                    f"({today.year}) — обучение ещё не завершено.",
                    [f"{prefix}.endYear"],
                )
            )

        if begin is not None and end is not None and end >= begin:
            intervals.append((begin, end))

    for first in range(len(intervals)):
        for second in range(first + 1, len(intervals)):
            start_a, end_a = intervals[first]
            start_b, end_b = intervals[second]
            if start_a < end_b and start_b < end_a:
                items.append(
                    make_item(
                        "low",
                        "education_periods_overlap",
                        "Периоды обучения пересекаются",
                        f"Периоды {start_a}–{end_a} и {start_b}–{end_b} "
                        "пересекаются по времени. Если это не второе "
                        "образование параллельно, данные противоречивы.",
                        ["education"],
                    )
                )

    return items


def _check_experience(
    candidate: CandidateProfile,
    birth: date | None,
    age: int | None,
    today: date,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    experience = candidate.experience

    if not experience:
        items.append(
            make_item(
                "medium",
                "experience_missing",
                "Опыт работы не указан",
                "Раздел experience пуст — соответствие опыта должности оценить нельзя.",
                ["experience"],
            )
        )
        return items

    current_flags = [item.current_job for item in experience]

    if candidate.has_job and not any(current_flags):
        items.append(
            make_item(
                "medium",
                "has_job_without_current",
                "Флаг занятости противоречит опыту",
                "hasJob=true, но ни одна запись experience не помечена как "
                "текущее место работы (currentJob=true).",
                ["hasJob", "experience"],
            )
        )
    if not candidate.has_job and any(current_flags):
        items.append(
            make_item(
                "medium",
                "current_job_without_has_job",
                "Флаг занятости противоречит опыту",
                "Есть запись с currentJob=true, но hasJob=false.",
                ["hasJob", "experience"],
            )
        )

    for index, item in enumerate(experience):
        prefix = f"experience[{index}]"
        begin = parse_date(item.begin_date)

        if not item.name:
            items.append(
                make_item(
                    "low",
                    f"experience_{index}_name_missing",
                    "Не указана организация",
                    f"В записи {prefix} пустое поле name.",
                    [f"{prefix}.name"],
                )
            )
        if not item.position:
            items.append(
                make_item(
                    "low",
                    f"experience_{index}_position_missing",
                    "Не указана должность",
                    f"В записи {prefix} пустое поле position — нельзя оценить "
                    "соответствие опыта целевой должности.",
                    [f"{prefix}.position"],
                )
            )

        if item.current_job and not item.begin_date:
            items.append(
                make_item(
                    "medium",
                    f"experience_{index}_current_without_date",
                    "Текущее место работы без даты начала",
                    f"В записи {prefix} currentJob=true, но beginDate пустая.",
                    [f"{prefix}.beginDate"],
                )
            )

        if item.begin_date and begin is None:
            items.append(
                make_item(
                    "medium",
                    f"experience_{index}_date_invalid",
                    "Дата начала работы не распознана",
                    f"Значение beginDate={item.begin_date!r} в записи "
                    f"{prefix} не является датой.",
                    [f"{prefix}.beginDate"],
                )
            )
        elif begin is not None:
            if begin > today:
                items.append(
                    make_item(
                        "high",
                        f"experience_{index}_begin_future",
                        "Работа начинается в будущем",
                        f"В записи {prefix} beginDate={begin.isoformat()} "
                        "позже текущей даты.",
                        [f"{prefix}.beginDate"],
                    )
                )
            if birth is not None:
                age_at_start = age_on(birth, begin)
                if age_at_start < 14:
                    items.append(
                        make_item(
                            "high",
                            f"experience_{index}_too_early",
                            "Работа началась в слишком раннем возрасте",
                            f"В записи {prefix} работа начинается "
                            f"{begin.isoformat()}, кандидату было "
                            f"{age_at_start} лет.",
                            [f"{prefix}.beginDate", "birthday"],
                        )
                    )

    start = earliest_experience_start(experience)
    if start is not None and age is not None:
        span = career_span_years(experience, today)
        max_plausible = max(age - 14, 0)
        if span > max_plausible + 1:
            items.append(
                make_item(
                    "high",
                    "career_longer_than_life",
                    "Стаж не соответствует возрасту",
                    f"Интервал карьеры {span} лет при возрасте {age} лет. "
                    f"Максимально возможный стаж — около {max_plausible} лет.",
                    ["experience", "birthday"],
                )
            )

    return items


def run_rule_checks(
    candidate: CandidateProfile, today: date | None = None
) -> list[dict[str, Any]]:
    """Выполняет все детерминированные проверки анкеты."""
    today = today or date.today()
    birth = parse_date(candidate.birthday)
    age = age_on(birth, today) if birth else None

    items: list[dict[str, Any]] = []
    items.extend(_check_identity(candidate, birth, age, today))
    items.extend(_check_contacts(candidate))
    items.extend(_check_documents(candidate))
    items.extend(_check_passport(candidate, birth, today))
    items.extend(_check_education(candidate, birth, today))
    items.extend(_check_experience(candidate, birth, age, today))
    return items
