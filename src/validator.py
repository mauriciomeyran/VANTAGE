"""PromptA-v1.0 schema validation and hard-rule enforcement."""

from __future__ import annotations

import json
import re
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_AUDIT_TYPES = frozenset(
    {"DNS", "HTTP", "Timeout", "Filled", "Expired", "Redirect", "Cloudflare", "DEDUP", "GATE", "PROFILE_FILTER", "NOTION_SYNC", "ANALYTICS"}
)

HARD_TITLE_EXCLUSIONS: tuple[str, ...] = (
    "Store Manager",
    "Director",
    "VP",
    "C-Level",
    "Assistant",
    "Asistente",
    "Auxiliar",
    "Jr.",
    "Internship",
    "Intern",
    "Entry Level",
    "Pasantía",
    "Sales Advisor",
    "Vendedor",
    "Asesor Comercial",
)

BLOCKED_COMPANY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"l['’]?or[eé]al\s+(cosmetics|luxury|division|group|holding)?", re.IGNORECASE),
    re.compile(r"levi['’]?s", re.IGNORECASE),
    re.compile(r"\bdockers\b", re.IGNORECASE),
    re.compile(r"(el\s+)?palacio\s+de\s+hierro", re.IGNORECASE),
    re.compile(r"l'or[eé]al\s+m[eé]xico", re.IGNORECASE),
    re.compile(r"loreal\s+(mexico|m[eé]xico)", re.IGNORECASE),
)

CDMX_HINTS: tuple[str, ...] = (
    "cdmx",
    "ciudad de mexico",
    "ciudad de méxico",
    "mexico city",
    "méxico city",
    "cd. de mexico",
    "cd. de méxico",
    "benito juarez",
    "benito juárez",
    "polanco",
    "cuauhtemoc",
    "cuauhtémoc",
    "miguel hidalgo",
    "coyoacan",
    "coyoacán",
    "alvaro obregon",
    "álvaro obregón",
)

MEXICO_HINTS: tuple[str, ...] = (
    "mexico",
    "méxico",
    "mx",
    *CDMX_HINTS,
)


class JobItem(BaseModel):
    """Single extracted vacancy (PromptA item)."""

    model_config = ConfigDict(extra="allow")

    job_id: str
    title: str
    brand: str
    holding: str | None = None
    location: str
    posted_date: str | None = None
    industry_tier: str | None = None
    seniority_level: str | None = None
    apply_url: str
    source_type: str
    source_name: str
    source_query: str | None = None
    fetch_status: str
    error_log: str | None = None
    visual_signal: bool = False
    innovation_dna: bool = False
    notes: str | None = None
    jd: str | None = None
    prompt_version: str
    layer: str = "L1"
    source_bucket: str | None = None

    @field_validator("posted_date")
    @classmethod
    def _iso_date(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        date.fromisoformat(value)
        return value


class AuditLogEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    source: str | None = None
    url: str | None = None
    message: str
    http_status: int | None = None

    @field_validator("type")
    @classmethod
    def _allowed_type(cls, value: str) -> str:
        if value not in ALLOWED_AUDIT_TYPES:
            raise ValueError(
                f"audit type '{value}' is not allowed; use one of {sorted(ALLOWED_AUDIT_TYPES)}"
            )
        return value


class DataQualityWarning(BaseModel):
    model_config = ConfigDict(extra="allow")

    code: str
    severity: Literal["info", "low", "medium", "high"] = "medium"
    cause: str | None = None
    impact: str | None = None
    message: str
    recommendation: str | None = None
    origin_layer: str = "L1"
    origin_wrapper: str | None = None


class PromptAPayload(BaseModel):
    """Kernel PromptA-v1.0 output envelope."""

    model_config = ConfigDict(extra="allow")

    prompt_variant: str
    prompt_version: str
    today_date: str
    items: list[JobItem] = Field(default_factory=list)
    audit_log: list[AuditLogEntry] = Field(default_factory=list)
    data_quality_warnings: list[DataQualityWarning] = Field(default_factory=list)
    reroute_candidates: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("today_date")
    @classmethod
    def _today_iso(cls, value: str) -> str:
        date.fromisoformat(value)
        return value


def title_is_hard_excluded(title: str) -> str | None:
    """Return the matching exclusion token if the full title is blocked."""
    normalized = title.lower().strip()
    for token in HARD_TITLE_EXCLUSIONS:
        # Handle punctuation in tokens like "Jr." by using lookarounds
        pattern = r'(?<!\w)' + re.escape(token.lower()) + r'(?!\w)'
        if re.search(pattern, normalized):
            return token
    return None


def company_is_blocked(brand: str, holding: str | None = None) -> str | None:
    haystack = f"{brand} {holding or ''}"
    for pattern in BLOCKED_COMPANY_PATTERNS:
        if pattern.search(haystack):
            return pattern.pattern
    return None


def location_is_allowed(location: str, notes: str | None = None) -> bool:
    blob = f"{location} {notes or ''}".lower()
    remote_pattern = r'\b(remote|remoto)\b'
    remote = re.search(remote_pattern, blob) is not None
    if remote:
        return any(hint in blob for hint in MEXICO_HINTS)
    return any(hint in blob for hint in CDMX_HINTS)


def empty_payload(
    *,
    prompt_variant: str,
    prompt_version: str,
    today_date: str,
    audit: list[AuditLogEntry] | None = None,
    warnings: list[DataQualityWarning] | None = None,
) -> PromptAPayload:
    return PromptAPayload(
        prompt_variant=prompt_variant,
        prompt_version=prompt_version,
        today_date=today_date,
        items=[],
        audit_log=audit or [],
        data_quality_warnings=warnings or [],
        reroute_candidates=[],
    )


def extract_json_object(raw: str) -> dict[str, Any]:
    """Parse JSON from an LLM/agent string that may include fences."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        parsed: Any = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise
        parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("PromptA output must be a JSON object")
    return parsed


def _normalize_envelope(data: dict[str, Any], *, fallback_version: str, fallback_variant: str, today: str) -> dict[str, Any]:
    items = data.get("items")
    if items is None and isinstance(data.get("consolidated_results"), list):
        items = data["consolidated_results"]
    if items is None:
        items = []
    return {
        "prompt_variant": data.get("prompt_variant") or fallback_variant,
        "prompt_version": data.get("prompt_version") or fallback_version,
        "today_date": data.get("today_date") or today,
        "items": items,
        "audit_log": data.get("audit_log") or [],
        "data_quality_warnings": data.get("data_quality_warnings") or [],
        "reroute_candidates": data.get("reroute_candidates")
        or data.get("reroute_candidates_history")
        or [],
    }


def apply_hard_rules(payload: PromptAPayload, *, wrapper_name: str) -> PromptAPayload:
    """Drop items that violate hard exclusions without relaxing the rules."""
    kept: list[JobItem] = []
    warnings = list(payload.data_quality_warnings)
    reroutes = list(payload.reroute_candidates)

    for item in payload.items:
        excluded = title_is_hard_excluded(item.title)
        if excluded:
            reroutes.append(
                {
                    "title": item.title,
                    "brand": item.brand,
                    "url_detectada": item.apply_url,
                    "wrapper_destino_sugerido": "not_applicable_excluded_title",
                    "confidence": "high",
                    "motivo": f"Title contains excluded term '{excluded}'",
                }
            )
            continue
        blocked = company_is_blocked(item.brand, item.holding)
        if blocked:
            warnings.append(
                DataQualityWarning(
                    code="HARD_BLOCK_EMPLOYER",
                    severity="high",
                    cause="Blocked employer",
                    impact="Item omitted",
                    message=f"Omitted vacancy from blocked employer: {item.brand}",
                    origin_wrapper=wrapper_name,
                )
            )
            continue
        if not location_is_allowed(item.location, item.notes):
            warnings.append(
                DataQualityWarning(
                    code="GEO_FILTER",
                    severity="medium",
                    cause="Location outside CDMX / remote Mexico",
                    impact="Item omitted",
                    message=f"Omitted '{item.title}' at {item.location}",
                    origin_wrapper=wrapper_name,
                )
            )
            continue
        kept.append(item)

    return payload.model_copy(
        update={"items": kept, "data_quality_warnings": warnings, "reroute_candidates": reroutes}
    )


def validate_raw(
    raw: str | dict[str, Any],
    *,
    prompt_variant: str,
    prompt_version: str,
    today_date: str,
    wrapper_name: str,
) -> PromptAPayload:
    data = raw if isinstance(raw, dict) else extract_json_object(raw)
    envelope = _normalize_envelope(
        data,
        fallback_version=prompt_version,
        fallback_variant=prompt_variant,
        today=today_date,
    )
    payload = PromptAPayload.model_validate(envelope)
    return apply_hard_rules(payload, wrapper_name=wrapper_name)
