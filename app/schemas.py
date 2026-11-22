"""Pydantic-модели анкеты кандидата и запроса на проверку.

Схема повторяет JSON анкеты, которую присылает заказчик:
``positionName``, ``department``, ``education[]``, ``experience[]`` и т.д.

В Python имена полей записаны в snake_case, во входном JSON — в camelCase.
Поддерживаются оба варианта записи, лишние поля не отбрасываются
(``extra="allow"``), чтобы расширение анкеты не ломало приём данных.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _as_text(value: Any) -> str:
    """Приводит значение к строке и схлопывает повторные пробелы."""
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.split())
    return str(value).strip()


def _as_int(value: Any) -> int | None:
    """Мягко приводит значение к целому числу; пустая строка → None."""
    if value is None or isinstance(value, bool):
        return int(value) if isinstance(value, bool) else None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _as_bool(value: Any) -> bool:
    """Приводит значение к bool, понимая строки вида "true"/"да"."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes", "y", "да"}


class _BaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class PrevNameEntry(BaseModel):
    """Запись о предыдущем имени."""

    surname: str | None = Field(default=None, alias="lastNameBeforeChange")
    firstname: str | None = Field(default=None, alias="firstNameBeforeChange")
    patronymic: str | None = Field(default=None, alias="midNameBeforeChange")
    changed: str | None = Field(default=None)
    reason: str | None = None
    
    @field_validator("surname", "firstname", "patronymic", mode="before")
    @classmethod
    def _validate_text(cls, value: Any) -> str:
        return _as_text(value)


class EducationEntry(_BaseModel):
    """Запись об образовании."""

    education_type: str = Field(default="", alias="educationType")
    institution_name: str = Field(default="", alias="institutionName")
    begin_year: int | None = Field(default=None, alias="beginYear")
    end_year: int | None = Field(default=None, alias="endYear")
    specialty: str = Field(default="")

    @field_validator("begin_year", "end_year", mode="before")
    @classmethod
    def _validate_year(cls, value: Any) -> int | None:
        return _as_int(value)

    @field_validator(
        "education_type", "institution_name", "specialty", mode="before"
    )
    @classmethod
    def _validate_text(cls, value: Any) -> str:
        return _as_text(value)


class ExperienceEntry(_BaseModel):
    """Запись об опыте работы."""

    begin_date: str = Field(default="", alias="beginDate")
    end_date: str = Field(default="", alias="endDate")
    current_job: bool = Field(default=False, alias="currentJob")
    name: str = Field(default="")
    address: str = Field(default="")
    activity_type: str = Field(default="", alias="activityType")
    position: str = Field(default="")
    possibility_contact_employer: bool = Field(
        default=True, alias="possibilityContactEmployer"
    )
    reason: str = Field(default="")

    @field_validator("current_job", "possibility_contact_employer", mode="before")
    @classmethod
    def _validate_bool(cls, value: Any) -> bool:
        return _as_bool(value)

    @field_validator(
        "begin_date", "name", "address", "activity_type", "position", mode="before"
    )
    @classmethod
    def _validate_text(cls, value: Any) -> str:
        return _as_text(value)

class OrganizationEntry(_BaseModel):
    """Запись о организации."""

    view: str = Field(alias="activity")
    organization: str = Field(alias="name")
    inn: str | None


class CandidateProfile(_BaseModel):
    """Анкета кандидата в том виде, в котором она приходит в JSON."""

    position_name: str = Field(default="", alias="positionName")
    department: str = Field(default="")
    last_name: str = Field(default="", alias="lastName")
    first_name: str = Field(default="", alias="firstName")
    has_name_changed: bool = Field(default=False, alias="hasNameChanged")
    birthday: str = Field(default="")
    birthplace: str = Field(default="")
    citizen: str = Field(default="")
    has_additional_citizenship: bool = Field(
        default=False, alias="hasAdditionalCitizenship"
    )
    marital_status: str = Field(default="", alias="maritalStatus")
    reg_address: str = Field(default="", alias="regAddress")
    valid_address: str = Field(default="", alias="validAddress")
    contact_phone: str = Field(default="", alias="contactPhone")
    email: str = Field(default="")
    has_inn: bool = Field(default=False, alias="hasInn")
    inn: str = Field(default="")
    has_snils: bool = Field(default=False, alias="hasSnils")
    snils: str = Field(default="")
    passport_serial: str = Field(default="", alias="passportSerial")
    passport_number: str = Field(default="", alias="passportNumber")
    passport_issue_date: str = Field(default="", alias="passportIssueDate")
    passport_issued_by: str = Field(default="", alias="passportIssuedBy")
    education: list[EducationEntry] = Field(default_factory=list)
    has_job: bool = Field(default=False, alias="hasJob")
    experience: list[ExperienceEntry] = Field(default_factory=list)
    nameWasChanged: list[PrevNameEntry] = Field(default_factory=list)
    organizations: list[OrganizationEntry] = Field(default_factory=list)

    @field_validator(
        "position_name",
        "department",
        "last_name",
        "first_name",
        "birthday",
        "birthplace",
        "citizen",
        "marital_status",
        "reg_address",
        "valid_address",
        "contact_phone",
        "email",
        "inn",
        "snils",
        "passport_serial",
        "passport_number",
        "passport_issue_date",
        "passport_issued_by",
        mode="before",
    )
    @classmethod
    def _validate_text(cls, value: Any) -> str:
        return _as_text(value)

    @field_validator(
        "has_name_changed",
        "has_additional_citizenship",
        "has_inn",
        "has_snils",
        "has_job",
        mode="before",
    )
    @classmethod
    def _validate_bool(cls, value: Any) -> bool:
        return _as_bool(value)

    @field_validator("education", "experience", mode="before")
    @classmethod
    def _validate_list(cls, value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, dict):
            return [value]
        if isinstance(value, list):
            return value
        return []

    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name]
        return " ".join(part for part in parts if part).strip()


class ScreeningRequest(_BaseModel):
    """Тело запроса на проверку анкеты.

    ``candidate`` — анкета по схеме заказчика. Соответствие должности
    оценивается только по названию должности и подразделению из анкеты.
    """

    candidate: CandidateProfile
