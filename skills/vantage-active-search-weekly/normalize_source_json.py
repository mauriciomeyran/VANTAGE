#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VANTAGE — Active Search Weekly (L1: LinkedIn + Career Sites + Aggregators)
Skill helper: normaliza el JSON de salida de cada fuente al schema canónico del
consolidador. Usado después de que un agente navega/extare los resultados crudos.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Exclusiones Prompt A (fuente: KERNEL + Prompt A) ──────────────────────────

EXCLUDED_TITLES = [
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
]

BLOCKED_COMPANIES = [
    "l'oréal",
    "levi's",
    "levis",
    "dockers",
    "el palacio de hierro",
    "palacio de hierro",
]

ACCEPTED_SENIORITIES = [
    "Coordinator",
    "Senior Coordinator",
    "Lead",
    "Supervisor",
    "Líder",
    "Subgerente",
    "Assistant Manager",
    "Manager",
    "Sr.",
    "Jefe",
    "Head",
]

ACCEPTED_INDUSTRIES = [
    "luxury",
    "premium",
    "fashion",
    "beauty",
    "cosmetics",
    "fragrances",
    "jewelry",
    "sportswear",
    "experiential retail",
    "retail experience",
    "brand experience",
    "visual merchandising",
    "store design",
]

ACCEPTED_LOCATION_KEYWORDS = [
    "ciudad de méxico",
    "cdmx",
    "área metropolitana de ciudad de méxico",
    "Área metropolitana de Ciudad de México",
    "cuauhtémoc",
    "miguel hidalgo",
    "benito juárez",
    "coyoacán",
    "almada",
    "ocidente",
    "polyanco",
    "san benito",
    "san Ángel",
    "del valle",
    "nápoles",
    "doctores",
    "tabacalera",
    "centro histórico",
    "colonia doct",
    "narvarte",
    "sección xiii",
    "viaducto",
    "portales",
    "san pedro de los pinos",
    "tláhuac",
    "iztapalapa",
    "tlaxpana",
    "pepenom stress",
]

# Colonias de EdoMex que comúnmente se confunden con CDMX:
EXCLUDED_LOCATION_KEYWORDS = [
    "naucalpan",
    "ecatepec",
    "tlalnepantla",
    "nezahualcóyotl",
    "ateljtlán",
    "tlajomulco",
    "atizapán",
    "tianguistenco",
    "texcoco",
    "chimalhuacán",
    "nextlalpan",
    "cuautitlán",
    "tepotzotlán",
    "huixquilucan",
    "jilotzingo",
    "acolo",
    "teotihuacán",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    if not text:
        return ""
    return (
        text.strip()
        .lower()
        .replace("’", "'")
        .replace("‘", "'")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
        .replace(" Área metropolitana", "")
    )


def is_excluded_title(title: str) -> str | None:
    """Devuelve el término excluido que matcheó, o None."""
    if not title:
        return None
    norm = _normalize(title)
    for term in EXCLUDED_TITLES:
        if term.lower() in norm:
            return term
    return None


def is_blocked_company(company: str) -> str | None:
    """Devuelve el término bloqueado que matcheó, o None."""
    if not company:
        return None
    norm = _normalize(company)
    for blocked in BLOCKED_COMPANIES:
        if blocked in norm:
            return blocked
    return None


def is_cdmx_location(location: str) -> bool:
    """Heurística: la ubicación es CDMX o Área Metropolitana de CDMX?"""
    if not location:
        return False
    norm = _normalize(location)
    for kw in ACCEPTED_LOCATION_KEYWORDS:
        if kw in norm:
            for excl in EXCLUDED_LOCATION_KEYWORDS:
                if excl in norm:
                    return False
            return True
    # Si dice explícitamente "Ciudad de México" (con o sin acento)
    if "ciudad de méxico" in norm or "ciudad de mexico" in norm:
        return True
    return False


def is_accepted_industry(industry_text: str) -> bool:
    """Heurística simple: el texto de industria menciona alguno aceptado."""
    if not industry_text:
        return False
    norm = _normalize(industry_text)
    for kw in ACCEPTED_INDUSTRIES:
        if kw in norm:
            return True
    return False


def is_accepted_seniority(seniority: str) -> bool:
    """Solo chequeado si el title no tiene senioridad explícita — fallback."""
    if not seniority:
        return False
    norm = _normalize(seniority)
    for s in ACCEPTED_SENIORITIES:
        if s.lower() in norm:
            return True
    return False


# ── Normalización de un job crudo → registro canónico ────────────────────────

def normalize_job(raw: dict, source: str) -> dict:
    """Convierte un job extraído por un agente a schema canónico del consolidador.

    El agente debe entregar un dict con al menos keys: title, company, location,
    apply_url. Las demás son opcionales.
    """
    title = raw.get("title", "") or ""
    company = raw.get("company", "") or ""
    location = raw.get("location", "") or ""
    apply_url = raw.get("apply_url", "") or ""
    posted_date = raw.get("posted_date", "") or ""
    job_id = raw.get("job_id", "") or ""
    platform_signals = raw.get("platform_signals", "") or ""
    jd = raw.get("jd", "") or ""
    source_type = raw.get("source_type", source)
    notes = raw.get("notes", "") or ""
    seniority = raw.get("seniority", "")
    work_mode = raw.get("work_mode", "")
    industry = raw.get("industry", "")

    # Limpieza de title (LinkedIn suelta title + ubicación + empresa en el mismo textContent)
    title = title.split("\n")[0].split("|")[0].split("·")[0].split("—")[0].strip()
    title = re.sub(r"\s+\[.*?\]\s*$", "", title)  # [CDMX] al final
    title = title.strip()

    # Exclusiones
    excluded_term = is_excluded_title(title)
    blocked_brand = is_blocked_company(company)

    excluded = bool(excluded_term or blocked_brand)
    rejection_reason = []
    if excluded_term:
        rejection_reason.append(f"excluded_title:{excluded_term}")
    if blocked_brand:
        rejection_reason.append(f"blocked_company:{blocked_brand}")

    # Location
    cdmx_ok = is_cdmx_location(location)

    rejection = excluded or not cdmx_ok
    status = "rejected" if rejection else "candidate"

    return {
        "title": title,
        "company": company,
        "location": location,
        "apply_url": apply_url,
        "posted_date": posted_date,
        "job_id": job_id,
        "platform_signals": platform_signals,
        "jd": jd,
        "source_type": source_type,
        "source": source,
        "seniority": seniority,
        "work_mode": work_mode,
        "industry": industry,
        "cdmx_location": cdmx_ok,
        "excluded_term": excluded_term,
        "blocked_company": blocked_brand,
        "rejection_reason": " · ".join(rejection_reason) if rejection_reason else "",
        "status": status,  # candidate | rejected
    }


# ── Construir JSON de fuente ──────────────────────────────────────────────────

def build_source_json(
    source: str,
    jobs_raw: list[dict],
    rejected_raw: list[dict],
    not_evaluated_raw: list[dict],
    audit_log: list[dict],
    search_summary: dict | None = None,
    search_metadata: dict | None = None,
    prompt_variant: str | None = None,
    prompt_version: str | None = None,
) -> dict:
    """Construye el JSON completo de salida para una fuente.

    Args:
        source: "linkedin" | "career_sites" | "aggregators"
        jobs_raw: lista de jobs candidatos (ya validados por el agente como positivos).
        rejected_raw: lista de jobs rechazados por exclusiones.
        not_evaluated_raw: lista de jobs que no se pudieron evaluar (bloqueos, etc.).
        audit_log: lista de eventos de auditoría.
        search_summary: metadata de la búsqueda.
        search_metadata: metadata de la búsqueda (promedio de edad, etc.).
        prompt_variant: variant del prompt (default: generado por fuente).
        prompt_version: version del prompt (default: generado por fuente).
    """
    variant_map = {
        "linkedin": "A-weekly-unified-linkedin",
        "career_sites": "A-weekly-unified-careersites",
        "aggregators": "A-weekly-unified-aggregators",
    }
    version_map = {
        "linkedin": "PromptA-v1.0+linkedin",
        "career_sites": "PromptA-v1.0+careersites",
        "aggregators": "PromptA-v1.0+aggregators",
    }

    variant = prompt_variant or variant_map.get(source, f"A-weekly-unified-{source}")
    version = prompt_version or version_map.get(source, f"PromptA-v1.0+{source}")

    jobs = [normalize_job(j, source) for j in jobs_raw]
    rejected = [normalize_job(j, source) for j in rejected_raw]

    # not_evaluated se deja como está (no se aplica normalizer)
    not_evaluated = not_evaluated_raw or []

    # Separar candidatos de rechazados
    candidates = [j for j in jobs if j["status"] == "candidate"]
    rechazados = [j for j in jobs if j["status"] == "rejected"]

    # Agregar rejected_raw a los rechazados
    rechazados.extend([normalize_job(j, source) for j in rejected_raw])

    return {
        "prompt_variant": variant,
        "prompt_version": version,
        "generated_at": _now_iso(),
        "candidate": "Mauricio Meyrán",
        "search_summary": search_summary or {
            "source": source,
            "candidates_count": len(candidates),
            "rejected_count": len(rechazados),
        },
        "audit_log": audit_log or [],
        "jobs": candidates,
        "rejected_jobs": rechazados,
        "not_evaluated": {
            "reason": "Sin evaluar — ver audit_log",
            "items": not_evaluated,
        },
        "search_metadata": search_metadata or {},
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="VANTAGE — Normaliza JSON de búsqueda de fuente L1 al schema canónico."
    )
    parser.add_argument(
        "--source",
        required=True,
        choices=["linkedin", "career_sites", "aggregators"],
        help="Fuente que se normaliza.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Ruta al JSON crudo del agente (con jobs, rejected_jobs, not_evaluated, audit_log).",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Ruta donde escribir el JSON normalizado (ej: Layer_1/feeds/2026-09-05_linkedin.json).",
    )
    parser.add_argument(
        "--prompt-variant",
        default=None,
        help="Prompt variant override (default: generado por fuente).",
    )
    parser.add_argument(
        "--prompt-version",
        default=None,
        help="Prompt version override (default: generado por fuente).",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Archivo de entrada no encontrado: {input_path}")
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        raw_data = json.load(f)

    # Extraer secciones del JSON crudo del agente
    jobs_raw = raw_data.get("jobs", [])
    rejected_raw = raw_data.get("rejected_jobs", [])
    not_evaluated_raw = raw_data.get("not_evaluated", {}).get("items", [])
    audit_log = raw_data.get("audit_log", [])
    search_summary = raw_data.get("search_summary", {})
    search_metadata = raw_data.get("search_metadata", {})

    output = build_source_json(
        source=args.source,
        jobs_raw=jobs_raw,
        rejected_raw=rejected_raw,
        not_evaluated_raw=not_evaluated_raw,
        audit_log=audit_log,
        search_summary=search_summary,
        search_metadata=search_metadata,
        prompt_variant=args.prompt_variant,
        prompt_version=args.prompt_version,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ JSON normalizado escrito: {output_path}")
    print(f"   Fuente: {args.source}")
    print(f"   Candidatos: {len(output['jobs'])}")
    print(f"   Rechazados: {len(output['rejected_jobs'])}")
    print(f"   No evaluados: {len(output['not_evaluated']['items'])}")
    print(f"   Audit events: {len(output['audit_log'])}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Cancelado por usuario")
        sys.exit(1)
