#!/usr/bin/env python3
"""
VANTAGE Cross-Tracker Match — Regla de cruce Marca+Rol

Detecta cuando un registro Inbound ya cerrado (ej. Zegna, JOB_ID=ZEGNA-VMLATAM-20260527, 
Rechazado) corresponde al mismo puesto que una vacante pública recién capturada por el pipeline.

Esta regla de cruce entre Tracker activo y Archive Tracker ayuda a identificar:
- Reposiciones de puestos previamente cerrados
- Oportunidades que deben ser reconsideradas
- Cambios en el estado de contratación de una marca
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Import Notion client following the same pattern as feed_processor.py
import sys as _sys
_scripts_dir = str(Path(__file__).resolve().parent)
_saved_path = _sys.path[:]
_saved_nc = _sys.modules.pop("notion_utils", None)
_sys.path = [p for p in _sys.path if p not in (_scripts_dir, ".", "")]
try:
    from notion_client import Client
finally:
    _sys.path = _saved_path
    if _saved_nc is not None:
        _sys.modules["notion_utils"] = _saved_nc

_LAYER_1_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_LAYER_1_ROOT / ".env", override=True)

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DB_ID = os.environ["NOTION_DB_OPPORTUNITIES"]
NOTION_ARCHIVE_PAGE_ID = os.environ["NOTION_ARCHIVE_PAGE_ID"]


@dataclass
class TrackerRecord:
    """Representa un registro de Tracker (activo o archivado)."""
    page_id: str
    title: str
    brand: str
    location: str
    status: str
    source_type: str
    job_id: str
    url: str
    is_archived: bool
    created_time: str


def _extract_text_prop(page: dict, prop_name: str) -> str:
    """Extrae texto plano de una propiedad Notion (title/rich_text/select/url)."""
    field = page.get("properties", {}).get(prop_name, {})
    ftype = field.get("type")
    
    if ftype == "rich_text":
        return "".join(t.get("plain_text", "") for t in field.get("rich_text", []))
    if ftype == "title":
        return "".join(t.get("plain_text", "") for t in field.get("title", []))
    if ftype == "select":
        return (field.get("select") or {}).get("name", "")
    if ftype == "url":
        return field.get("url") or ""
    return ""


def _normalize_brand_text(text: str) -> str:
    """Normaliza texto de marca para comparación."""
    if not text:
        return ""
    return text.strip().lower().replace("’", "'").replace("‘", "'")


def _normalize_title_text(text: str) -> str:
    """Normaliza texto de título para comparación."""
    if not text:
        return ""
    return text.strip().lower()


def compute_marca_rol_key(record: TrackerRecord) -> str:
    """
    Calcula la clave de cruce Marca+Rol.
    
    Esta clave se usa para identificar si dos registros corresponden al mismo puesto,
    independientemente de su estado (activo vs archivado) o fuente (Inbound vs Vacante).
    """
    brand_norm = _normalize_brand_text(record.brand)
    title_norm = _normalize_title_text(record.title)
    return f"{brand_norm}|{title_norm}"


def query_active_tracker(notion: Client) -> list[TrackerRecord]:
    """
    Consulta el Tracker activo para obtener vacantes recientes.
    
    Filtra por:
    - Source_Type = Vacante (públicas)
    - Creadas en el último mes
    """
    records = []
    
    try:
        # Usar data_source API
        response = notion.request(
            path="data_sources/442938befc42828fb72e076818d65a5b/query",
            method="POST",
            body={
                "filter": {
                    "and": [
                        {
                            "property": "Source_Type ",
                            "select": {"equals": "Vacante"}
                        },
                        {
                            "timestamp": "created_time",
                            "created_time": {"past_month": {}}
                        }
                    ]
                }
            }
        )
        
        for page in response.get("results", []):
            record = TrackerRecord(
                page_id=page["id"],
                title=_extract_text_prop(page, "title") or _extract_text_prop(page, "Rol") or "",
                brand=_extract_text_prop(page, "brand") or _extract_text_prop(page, "Marca") or "",
                location=_extract_text_prop(page, "location") or "",
                status=_extract_text_prop(page, "Status") or "",
                source_type=_extract_text_prop(page, "Source_Type ") or "",
                job_id=_extract_text_prop(page, "JOB_ID") or "",
                url=_extract_text_prop(page, "apply_url") or _extract_text_prop(page, "URL") or "",
                is_archived=False,
                created_time=page.get("created_time", ""),
            )
            records.append(record)
            
    except Exception as exc:
        print(f"❌ Error consultando Tracker activo: {exc}")
    
    return records


def query_archive_tracker(notion: Client) -> list[TrackerRecord]:
    """
    Consulta el Archive Tracker para obtener registros Inbound cerrados.
    
    Filtra por:
    - Source_Type = Inbound
    - Status = Rechazado o similares (cerrados)
    """
    records = []
    
    try:
        # Archive Tracker está organizado como páginas hijas bajo NOTION_ARCHIVE_PAGE_ID
        # Necesitamos iterar sobre las páginas mensuales y luego sobre sus contenidos
        
        # Por simplicidad, este es un placeholder - la implementación real dependerá
        # de la estructura específica del Archive Tracker
        print("⚠️  Archive Tracker query no implementado completamente")
        print("⚠️  Se requiere estructura específica del Archive Tracker")
        
    except Exception as exc:
        print(f"❌ Error consultando Archive Tracker: {exc}")
    
    return records


def find_cross_tracker_matches(
    active_records: list[TrackerRecord],
    archived_records: list[TrackerRecord],
) -> list[dict]:
    """
    Encuentra matches entre Tracker activo y Archive Tracker usando la regla Marca+Rol.
    
    Retorna una lista de matches donde:
    - El registro archivado es Inbound cerrado (Rechazado, etc.)
    - El registro activo es una vacante pública reciente
    - Ambos tienen la misma Marca+Rol (mismo puesto)
    """
    matches = []
    
    # Crear índice de archived records por Marca+Rol
    archived_index = {}
    for archived in archived_records:
        key = compute_marca_rol_key(archived)
        if key not in archived_index:
            archived_index[key] = []
        archived_index[key].append(archived)
    
    # Buscar matches en active records
    for active in active_records:
        key = compute_marca_rol_key(active)
        
        if key in archived_index:
            for archived in archived_index[key]:
                # Verificar que el archived sea Inbound cerrado
                if archived.source_type == "Inbound" and archived.status in ["Rechazado", "Cerrado", "Cancelado"]:
                    match = {
                        "active_record": active,
                        "archived_record": archived,
                        "match_reason": f"Marca+Rol match: {active.brand} - {active.title}",
                        "recommendation": "Reconsiderar - posición previamente cerrada ahora está disponible"
                    }
                    matches.append(match)
    
    return matches


def format_match_report(matches: list[dict]) -> str:
    """Genera un reporte legible de los matches encontrados."""
    if not matches:
        return "✅ No se encontraron matches entre Tracker activo y Archive Tracker"
    
    lines = [
        f"📋 Se encontraron {len(matches)} match(es) entre Tracker activo y Archive Tracker:",
        "",
    ]
    
    for i, match in enumerate(matches, 1):
        active = match["active_record"]
        archived = match["archived_record"]
        
        lines.append(f"Match #{i}:")
        lines.append(f"  {match['match_reason']}")
        lines.append(f"  📌 Vacante Activa:")
        lines.append(f"     - Título: {active.title}")
        lines.append(f"     - Marca: {active.brand}")
        lines.append(f"     - Ubicación: {active.location}")
        lines.append(f"     - URL: {active.url}")
        lines.append(f"     - Creada: {active.created_time}")
        lines.append(f"  📁 Registro Archivado:")
        lines.append(f"     - Título: {archived.title}")
        lines.append(f"     - Marca: {archived.brand}")
        lines.append(f"     - Status: {archived.status}")
        lines.append(f"     - JOB_ID: {archived.job_id}")
        lines.append(f"     - Source: {archived.source_type}")
        lines.append(f"  💡 Recomendación: {match['recommendation']}")
        lines.append("")
    
    return "\n".join(lines)


def main() -> None:
    import argparse
    
    parser = argparse.ArgumentParser(description="VANTAGE Cross-Tracker Match")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Modo dry-run (default): solo reporta matches sin acciones"
    )
    args = parser.parse_args()
    
    print("🔍 VANTAGE Cross-Tracker Match — Regla Marca+Rol")
    print("=" * 60)
    
    # Inicializar cliente Notion
    notion = Client(auth=NOTION_TOKEN)
    
    # Consultar Tracker activo
    print("📊 Consultando Tracker activo (vacantes recientes)...")
    active_records = query_active_tracker(notion)
    print(f"   ✅ {len(active_records)} registros activos encontrados")
    
    # Consultar Archive Tracker
    print("📁 Consultando Archive Tracker (Inbound cerrados)...")
    archived_records = query_archive_tracker(notion)
    print(f"   ✅ {len(archived_records)} registros archivados encontrados")
    
    # Buscar matches
    print("🔎 Buscando matches por Marca+Rol...")
    matches = find_cross_tracker_matches(active_records, archived_records)
    
    # Generar reporte
    print("\n" + "=" * 60)
    report = format_match_report(matches)
    print(report)
    
    if matches and not args.dry_run:
        print("\n⚠️  Modo ejecución: Se podrían crear alertas o actualizar registros")
        print("⚠️  Esta funcionalidad está pendiente de implementación")


if __name__ == "__main__":
    main()