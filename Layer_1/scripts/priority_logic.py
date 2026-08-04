#!/usr/bin/env python3
"""
priority_logic.py — Lógica de Prioridad (Class A) compartida.

Extraído de backfill_class_a.py para romper el import circular con
layer_1_run.py (backfill_class_a.py importa is_agregador de layer_1_run.py;
layer_1_run.py necesita infer_prioridad de aquí). Ningún módulo del pipeline
debe importar layer_1_run.py ni backfill_class_a.py desde este archivo.

Consumido por:
  - layer_1_run.py   (Fase 3.6 — escritura primaria en el run semanal)
  - backfill_class_a.py (catch-up de registros legacy / huecos)
"""

from __future__ import annotations

import re
from datetime import date


def txt(prop: dict | None) -> str:
    if not prop:
        return ""
    t = prop.get("type")
    if t == "url":
        return prop.get("url") or ""
    if t == "rich_text" and prop.get("rich_text"):
        return prop["rich_text"][0]["plain_text"]
    if t == "select" and prop.get("select"):
        return prop["select"]["name"]
    if t == "title" and prop.get("title"):
        return prop["title"][0]["plain_text"]
    return ""


def get_importancia_bucket(score: int) -> str:
    """
    Determina el bucket de Importancia basado en Score.

    Score=40 es BASE SCORE (sin bonificaciones) = "Sin evaluar"
    Score != 40 tiene al menos un bono activado = valor calculado real
    """
    if score == 40:
        return "Base"
    elif score <= 60:
        return "Media"
    elif score <= 80:
        return "Alta"
    elif score <= 100:
        return "Muy Alta"
    else:
        return "Base"  # fallback defensivo


def apply_importancia_matrix(urgencia: str, importancia_bucket: str) -> str:
    """
    Matriz Urgencia x Importancia -> Prioridad final.

             | Base    | Media   | Alta     | Muy Alta
    CRÍTICO  | 4 CRÍTICO| 4 CRÍTICO| 4 CRÍTICO| 4 CRÍTICO
    ALTO     | 2 MEDIO | 3 ALTO  | 4 CRÍTICO| 4 CRÍTICO
    MEDIO    | 1 BAJO  | 2 MEDIO | 3 ALTO   | 4 CRÍTICO
    BAJO     | 1 BAJO  | 1 BAJO  | 2 MEDIO  | 3 ALTO
    """
    matrix = {
        ("CRÍTICO", "Base"):     "4 CRÍTICO",
        ("CRÍTICO", "Media"):    "4 CRÍTICO",
        ("CRÍTICO", "Alta"):     "4 CRÍTICO",
        ("CRÍTICO", "Muy Alta"): "4 CRÍTICO",
        ("ALTO",    "Base"):     "2 MEDIO",
        ("ALTO",    "Media"):    "3 ALTO",
        ("ALTO",    "Alta"):     "4 CRÍTICO",
        ("ALTO",    "Muy Alta"): "4 CRÍTICO",
        ("MEDIO",   "Base"):     "1 BAJO",
        ("MEDIO",   "Media"):    "2 MEDIO",
        ("MEDIO",   "Alta"):     "3 ALTO",
        ("MEDIO",   "Muy Alta"): "4 CRÍTICO",
        ("BAJO",    "Base"):     "1 BAJO",
        ("BAJO",    "Media"):    "1 BAJO",
        ("BAJO",    "Alta"):     "2 MEDIO",
        ("BAJO",    "Muy Alta"): "3 ALTO",
    }
    return matrix.get((urgencia, importancia_bucket), "1 BAJO")  # fallback defensivo


def infer_prioridad(props: dict, today: date) -> tuple[str, str]:
    """
    Infiere Prioridad usando matriz Urgencia x Importancia.

    Pasos:
    1. Calcular Urgencia (deadline + antigüedad + Source_Type)
    2. Calcular Importancia (bucket de Score)
    3. Aplicar matriz Urgencia x Importancia

    Retorna: (valor_prioridad, razón)
    Valores válidos: "1 BAJO", "2 MEDIO", "3 ALTO", "4 CRÍTICO"

    NOTA — sin cambios de lógica respecto al backfill_class_a.py verificado
    en vivo el 2026-08-03. El Criterio 1 (Source_Type en {Inbound,
    Referencia, Networking} -> Urgencia=CRÍTICO sin chequeo de antigüedad)
    se traslada intacto. Pendiente de decisión operador — no tocado en
    este patch.
    """
    jd_text = txt(props.get("JD")).lower()

    deadline_patterns = [
        r"apply by\s+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        r"deadline\s*[:]\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        r"fecha\s+límite\s*[:]\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        r"deadline\s*:\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
    ]

    deadline_near = False
    for pattern in deadline_patterns:
        match = re.search(pattern, jd_text)
        if match:
            try:
                date_str = match.group(1)
                parts = re.findall(r"\d+", date_str)
                if len(parts) >= 3:
                    day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                    if year < 100:
                        year += 2000
                    deadline_date = date(year, month, day)
                    days_until = (deadline_date - today).days
                    if days_until <= 5:
                        deadline_near = True
                        break
            except (ValueError, IndexError):
                continue

    source_type = txt(props.get("Source_Type "))

    if deadline_near or source_type in {"Inbound", "Referencia", "Networking"}:
        urgencia = "CRÍTICO"
        urgencia_reason = "deadline_jd" if deadline_near else f"source_type_{source_type}"
    else:
        created_time = props.get("created_time")
        if created_time:
            try:
                created_date = date.fromisoformat(created_time.replace("Z", "+00:00").split("T")[0])
                days_old = (today - created_date).days
            except (ValueError, AttributeError):
                urgencia = "MEDIO"
                urgencia_reason = "fecha_invalida"
            else:
                if days_old <= 3:
                    urgencia = "ALTO"
                    urgencia_reason = f"creado_{days_old}_dias"
                elif 4 <= days_old <= 14:
                    urgencia = "MEDIO"
                    urgencia_reason = f"creado_{days_old}_dias"
                else:
                    urgencia = "BAJO"
                    urgencia_reason = f"creado_{days_old}_dias"
        else:
            urgencia = "MEDIO"
            urgencia_reason = "sin_fecha_creacion"

    score = props.get("Score", 40)
    if isinstance(score, dict):
        score = score.get("number", 40)
    try:
        score_int = int(score)
    except (ValueError, TypeError):
        score_int = 40

    importancia_bucket = get_importancia_bucket(score_int)
    prioridad_final = apply_importancia_matrix(urgencia, importancia_bucket)
    prioridad_reason = f"{urgencia_reason}_{importancia_bucket}"

    return prioridad_final, prioridad_reason
