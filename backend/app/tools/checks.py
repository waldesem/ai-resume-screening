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
    employment_gaps,
    experience_periods,
    last_employment_end,
    months_between,
    parse_date,
)

SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}
SEVERITY_LABELS = {
    "high": "Критично",
    "medium": "Средне",
    "low": "Незначительно",
}

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
_BUSINESS_PATTERNS = (
    r"\bип\b",
    r"индивидуальн\w* предпринимател",
    r"учредител",
    r"владел",
    r"собственник",
    r"самозанят",
    r"предпринимател",
    r"\bfounder\b",
    r"\bowner\b",
    r"self[- ]employed",
)


def make_item(
    severity: str,
    code: str,
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
        "code": code,
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
        end = parse_date(item.end_date)

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

        if item.end_date and end is None:
            items.append(
                make_item(
                    "low",
                    f"experience_{index}_end_date_invalid",
                    "Дата окончания работы не распознана",
                    f"Значение endDate={item.end_date!r} в записи "
                    f"{prefix} не является датой.",
                    [f"{prefix}.endDate"],
                )
            )
        elif begin is not None and end is not None and end < begin:
            items.append(
                make_item(
                    "high",
                    f"experience_{index}_dates_reversed",
                    "Даты периода работы противоречат друг другу",
                    f"В записи {prefix} дата окончания "
                    f"({end.isoformat()}) раньше даты начала "
                    f"({begin.isoformat()}).",
                    [f"{prefix}.beginDate", f"{prefix}.endDate"],
                )
            )

        if item.current_job and item.end_date:
            items.append(
                make_item(
                    "low",
                    f"experience_{index}_current_with_end",
                    "У текущего места работы указана дата окончания",
                    f"В записи {prefix} currentJob=true, но endDate="
                    f"{item.end_date!r} заполнена.",
                    [f"{prefix}.currentJob", f"{prefix}.endDate"],
                )
            )

    if not candidate.has_job and not candidate.no_job_reason:
        items.append(
            make_item(
                "low",
                "no_job_reason_missing",
                "Не указана причина отсутствия работы",
                "hasJob=false, но поле noJobReason пустое — причина "
                "отсутствия текущего места работы не раскрыта.",
                ["hasJob", "noJobReason"],
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


def _is_business_text(value: str) -> bool:
    """Ищет в тексте признаки собственного бизнеса или самозанятости."""
    lowered = (value or "").lower()
    return any(re.search(pattern, lowered) for pattern in _BUSINESS_PATTERNS)


def _gap_explained_by_education(
    candidate: CandidateProfile, begin: date, end: date
) -> bool:
    """Считает перерыв объяснённым, если он целиком попадает в годы обучения."""
    for item in candidate.education:
        if item.begin_year is None or item.end_year is None:
            continue
        if begin.year >= item.begin_year and end.year <= item.end_year:
            return True
    return False


def _format_months(months: int) -> str:
    """Короткое человекочитаемое представление длительности в месяцах."""
    if months < 12:
        return f"{months} мес."
    years, rest = divmod(months, 12)
    if rest:
        return f"{years} г. {rest} мес."
    return f"{years} г."


def _check_employment_history(
    candidate: CandidateProfile, today: date
) -> list[dict[str, Any]]:
    """Проверяет короткие периоды, перерывы, причины увольнения и бизнес."""
    items: list[dict[str, Any]] = []
    experience = candidate.experience
    periods = experience_periods(experience, today)

    short_periods = [item for item in periods if item["months"] < 6]
    if short_periods:
        severity = "high" if len(short_periods) >= 3 else "medium"
        details = "; ".join(
            f"{item['name'] or 'организация не указана'} "
            f"({item['position'] or 'должность не указана'}) — "
            f"{_format_months(item['months'])}"
            for item in short_periods
        )
        items.append(
            make_item(
                severity,
                "short_tenure",
                "Короткие периоды работы",
                f"Найдено мест работы короче 6 месяцев: "
                f"{len(short_periods)}. {details}. Требуется уточнить причины "
                "увольнения и характер работы (стажировка, проект, сезонная "
                "занятость).",
                ["experience"],
            )
        )

    gaps = [
        gap
        for gap in employment_gaps(experience, today)
        if gap["months"] >= 6
        and not _gap_explained_by_education(candidate, gap["begin"], gap["end"])
    ]
    if gaps:
        severity = "high" if any(gap["months"] >= 12 for gap in gaps) else "medium"
        details = "; ".join(
            f"{gap['begin'].isoformat()}–{gap['end'].isoformat()} "
            f"({_format_months(gap['months'])})"
            for gap in gaps
        )
        items.append(
            make_item(
                severity,
                "employment_gap",
                "Длительные перерывы в работе",
                f"Найдено перерывов более 6 месяцев: {len(gaps)}. {details}. "
                "Перерывы не объяснены обучением по данным анкеты.",
                ["experience", "education"],
            )
        )

    if not candidate.has_job:
        last_end = last_employment_end(experience, today)
        if last_end is not None and last_end < today:
            months = months_between(last_end, today)
            if months >= 6 and not _gap_explained_by_education(
                candidate, last_end, today
            ):
                items.append(
                    make_item(
                        "high" if months >= 12 else "medium",
                        "employment_gap_after_last_job",
                        "Длительный перерыв после последнего места работы",
                        f"После окончания последнего места работы "
                        f"({last_end.isoformat()}) прошло "
                        f"{_format_months(months)}, при этом hasJob=false.",
                        ["experience", "hasJob", "noJobReason"],
                    )
                )

    completed = [
        (index, item)
        for index, item in enumerate(experience)
        if not item.current_job
    ]
    missing_reasons = [
        (index, item) for index, item in completed if not item.reason.strip()
    ]
    if missing_reasons:
        severity = "medium" if len(missing_reasons) >= 2 else "low"
        details = "; ".join(
            f"experience[{index}] — {item.name or 'организация не указана'}"
            for index, item in missing_reasons
        )
        items.append(
            make_item(
                severity,
                "dismissal_reason_missing",
                "Не указаны причины увольнения",
                f"Причина увольнения не заполнена для завершённых мест "
                f"работы: {details}.",
                [f"experience[{index}].reason" for index, _ in missing_reasons],
            )
        )

    reasons = [
        " ".join(item.reason.lower().split())
        for _, item in completed
        if item.reason.strip()
    ]
    repeated = sorted({reason for reason in reasons if reasons.count(reason) >= 2})
    if repeated:
        items.append(
            make_item(
                "low",
                "dismissal_reason_repeated",
                "Причины увольнения повторяются",
                "Одинаковая причина увольнения указана для нескольких мест "
                f"работы: {', '.join(repeated)}. Требуется уточнение реальных "
                "причин ухода.",
                ["experience"],
            )
        )

    business_positions = [
        (index, item)
        for index, item in enumerate(experience)
        if _is_business_text(item.position) or _is_business_text(item.name)
    ]
    if business_positions:
        evidence = "; ".join(
            f"experience[{index}] — {item.position or item.name}"
            for index, item in business_positions
        )
        if candidate.organizations:
            evidence += (
                "; организации кандидата: "
                + "; ".join(
                    item.organization or "название не указано"
                    for item in candidate.organizations
                )
            )
        items.append(
            make_item(
                "medium",
                "own_business",
                "Признаки собственного бизнеса",
                f"В опыте найдены признаки собственного бизнеса: {evidence}. "
                "Требуется проверить конфликт интересов и совместительство.",
                ["experience", "organizations"],
            )
        )

    experience_names = {
        " ".join(item.name.lower().split()) for item in experience if item.name
    }
    unmatched_organizations = [
        item
        for item in candidate.organizations
        if item.organization
        and " ".join(item.organization.lower().split()) not in experience_names
    ]
    if unmatched_organizations:
        items.append(
            make_item(
                "low",
                "organization_not_in_experience",
                "Организации не отражены в опыте работы",
                "В разделе organizations указаны организации, которых нет "
                "среди мест работы: "
                + "; ".join(
                    item.organization for item in unmatched_organizations
                )
                + ". Требуется уточнить роль кандидата в этих организациях.",
                ["organizations", "experience"],
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
    items.extend(_check_employment_history(candidate, today))
    return items
