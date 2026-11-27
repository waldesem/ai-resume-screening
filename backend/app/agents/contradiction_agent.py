"""LLM-агент поиска смысловых противоречий в анкете кандидата."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from app.models.llm import chat_json
from app.models.prompts import CONTRADICTION_ANALYSIS
from app.schema.schemas import CandidateProfile
from app.tools.utils import candidate_json, describe_candidate

_ALLOWED_SEVERITIES = {"high", "medium", "low"}


def _normalize_item(raw: Any, index: int) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None

    title = str(raw.get("title") or "").strip()
    description = str(raw.get("description") or "").strip()
    if not title and not description:
        return None

    severity = str(raw.get("severity") or "medium").strip().lower()
    if severity not in _ALLOWED_SEVERITIES:
        severity = "medium"

    fields = raw.get("fields") or []
    if not isinstance(fields, list):
        fields = [str(fields)]

    return {
        "severity": severity,
        "title": title or "Смысловое противоречие",
        "description": description,
        "fields": [str(field) for field in fields if str(field).strip()],
        "source": "llm",
    }


def analyze_contradictions(
    candidate: CandidateProfile,
    rule_findings: list[dict[str, Any]] | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    """Ищет смысловые противоречия, которые не ловятся формальными правилами."""
    today = today or date.today()
    findings = rule_findings or []

    prompt = CONTRADICTION_ANALYSIS.format(
        rule_findings=json.dumps(findings, ensure_ascii=False, indent=2)
        if findings
        else "[]",
        candidate_summary=describe_candidate(candidate, today),
        candidate_json=candidate_json(candidate),
    )

    data = chat_json(prompt)

    items: list[dict[str, Any]] = []
    raw_items = data.get("contradictions") or []
    if isinstance(raw_items, list):
        for index, raw in enumerate(raw_items):
            item = _normalize_item(raw, index)
            if item is not None:
                items.append(item)

    return {
        "items": items,
        "summary": str(data.get("summary") or "").strip(),
    }
