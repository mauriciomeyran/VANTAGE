#!/usr/bin/env python3
"""
VANTAGE Auto-Archive — Ejecución automática de archivado

Archiva páginas en VANTAGE TRACKER cuando:
  - Next_Action='Archivar' 
  - Dedup_Flag='Posible duplicado'

Las páginas se mueven a ARCHIVO TRACKER con soft-delete.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import date
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

MONTH_NAMES = [
    "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE",
    "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER",
]


@dataclass
class ArchiveCandidate:
    """Representa una página candidata para archivado."""
    page_id: str
    title: str
    brand: str
    url: str
    next_action: str
    dedup_flag: str
    reason: str


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


def _find_child_page(notion: Client, parent_id: str, title: str) -> dict | None:
    """Busca una página hija por título dentro de una página padre."""
    cursor = None
    while True:
        kwargs: dict[str, Any] = {"page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        resp = notion.blocks.children.list(block_id=parent_id, **kwargs)
        for block in resp.get("results", []):
            if block.get("type") != "child_page":
                continue
            child_title = ""
            child_page = block.get("child_page", {})
            for t in child_page.get("title", []):
                child_title += t if isinstance(t, str) else t.get("plain_text", "")
            if child_title.strip() == title:
                return {"id": block["id"], "title": child_title}
        if resp.get("has_more") and resp.get("next_cursor"):
            cursor = resp["next_cursor"]
        else:
            break
    return None


def _month_page_title(d: date) -> str:
    """Genera título de página mensual de archivo."""
    return f"{d.strftime('%Y-%m')} {MONTH_NAMES[d.month - 1]}"


def query_archive_candidates(
    notion: Client,
    dry_run: bool = True,
) -> list[ArchiveCandidate]:
    """
    Busca páginas en VANTAGE TRACKER con:
    - Next_Action='Archivar'
    - Dedup_Flag='Posible duplicado'
    """
    candidates = []
    
    # First, get the database schema to understand property names
    # VANTAGE uses data_sources API instead of standard databases API
    try:
        print(f"🔍 Consultando data_source ID: 442938befc42828fb72e076818d65a5b")
        ds_info = notion.request(path="data_sources/442938befc42828fb72e076818d65a5b", method="GET", body=None)
        properties = ds_info.get("properties", {})
        print(f"🔍 Total propiedades: {len(properties)}")
    except Exception as exc:
        print(f"❌ Error obteniendo schema de data_source: {exc}")
        return candidates
    
    # Find property names for Next_Action and Dedup_Flag
    next_action_prop = None
    dedup_flag_prop = None
    
    print(f"🔍 Propiedades disponibles en DB: {list(properties.keys())[:10]}...")
    
    for prop_name, prop_def in properties.items():
        # Use exact name matching since we know the schema
        if prop_name == "Next_Action":
            next_action_prop = prop_name
        if prop_name == "Dedup_Flag":
            dedup_flag_prop = prop_name
    
    if not next_action_prop:
        print("⚠️  No se encontró propiedad Next_Action en la DB")
        return candidates
    
    if not dedup_flag_prop:
        print("⚠️  No se encontró propiedad Dedup_Flag en la DB")
        return candidates
    
    print(f"🔍 Buscando candidatos con {next_action_prop}='Archivar' y {dedup_flag_prop}='Posible duplicado'")
    
    # Query for pages matching the criteria
    # Next_Action is rich_text, Dedup_Flag is select
    filter_body = {
        "and": [
            {
                "property": next_action_prop,
                "rich_text": {"equals": "Archivar"}
            },
            {
                "property": dedup_flag_prop,
                "select": {"equals": "Posible duplicado"}
            }
        ]
    }
    
    try:
        response = notion.request(
            path="data_sources/442938befc42828fb72e076818d65a5b/query",
            method="POST",
            body={"filter": filter_body}
        )
        
        results = response.get("results", [])
        print(f"🔍 Resultados encontrados: {len(results)}")
        
        for page in results:
            page_id = page["id"]
            title = _extract_text_prop(page, "title") or _extract_text_prop(page, "Rol") or "Sin título"
            brand = _extract_text_prop(page, "brand") or _extract_text_prop(page, "Marca") or ""
            url = _extract_text_prop(page, "apply_url") or _extract_text_prop(page, "URL") or ""
            next_action = _extract_text_prop(page, next_action_prop)
            dedup_flag = _extract_text_prop(page, dedup_flag_prop)
            
            candidate = ArchiveCandidate(
                page_id=page_id,
                title=title,
                brand=brand,
                url=url,
                next_action=next_action,
                dedup_flag=dedup_flag,
                reason="Auto-archive: Next_Action=Archivar + Dedup_Flag=Posible duplicado"
            )
            candidates.append(candidate)
            
            # Debug: mostrar detalles completos del candidato
            print(f"  🔍 DEBUG - Candidato #{len(candidates)}:")
            print(f"      Page ID: {page_id}")
            print(f"      Next_Action: '{next_action}'")
            print(f"      Dedup_Flag: '{dedup_flag}'")
            print(f"      Título: '{title}'")
            print(f"      Marca: '{brand}'")
            print(f"      Source_Type: '{_extract_text_prop(page, 'Source_Type ')}'")
            print(f"      Status: '{_extract_text_prop(page, 'Status')}'")
            
    except Exception as exc:
        print(f"❌ Error consultando candidatos: {exc}")
    
    return candidates


def archive_page(
    notion: Client,
    candidate: ArchiveCandidate,
    dry_run: bool = True,
) -> bool:
    """
    Mueve una página a ARCHIVO TRACKER.
    
    En modo dry_run, solo reporta la acción sin ejecutarla.
    """
    if dry_run:
        print(f"  [DRY RUN] Archivar: {candidate.title[:50]} @ {candidate.brand}")
        print(f"            URL: {candidate.url[:80]}")
        print(f"            Page ID: {candidate.page_id[:8]}...")
        return True
    
    # Implementación real de archivado
    # 1. Obtener o crear página mensual en ARCHIVO TRACKER
    today = date.today()
    month_title = _month_page_title(today)
    
    month_page = _find_child_page(notion, NOTION_ARCHIVE_PAGE_ID, month_title)
    if not month_page:
        try:
            created = notion.pages.create(
                parent={"database_id": NOTION_ARCHIVE_PAGE_ID},
                properties={"title": {"title": [{"text": {"content": month_title}}]}},
            )
            month_page_id = created["id"]
            print(f"  📁 Creada página mensual: {month_title}")
        except Exception as exc:
            print(f"  ❌ Error creando página mensual: {exc}")
            return False
    else:
        month_page_id = month_page["id"]
    
    # 2. Mover la página al archivo (cambiar parent)
    try:
        notion.pages.update(
            page_id=candidate.page_id,
            parent={"page_id": month_page_id},
        )
        print(f"  ✅ Archivado: {candidate.title[:50]} @ {candidate.brand}")
        return True
    except Exception as exc:
        print(f"  ❌ Error archivando página: {exc}")
        return False


def main() -> None:
    import argparse
    
    parser = argparse.ArgumentParser(description="VANTAGE Auto-Archive")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Modo dry-run (default): solo reporta acciones sin ejecutar"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Ejecuta el archivado real (desactiva dry-run)"
    )
    args = parser.parse_args()
    
    dry_run = args.dry_run and not args.execute
    
    if dry_run:
        print("🔍 MODO DRY RUN — No se realizarán cambios reales")
    else:
        print("⚠️  MODO EJECUCIÓN — Se realizarán cambios reales en Notion")
    
    # Inicializar cliente Notion
    notion = Client(auth=NOTION_TOKEN)
    
    # Buscar candidatos
    candidates = query_archive_candidates(notion, dry_run=dry_run)
    
    if not candidates:
        print("✅ No se encontraron candidatos para archivar")
        return
    
    print(f"\n📋 Found {len(candidates)} candidate(s) for archiving:\n")
    
    # Archivar candidatos
    success_count = 0
    fail_count = 0
    
    for candidate in candidates:
        if archive_page(notion, candidate, dry_run=dry_run):
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\n📊 Resumen:")
    print(f"  ✅ Exitosos: {success_count}")
    print(f"  ❌ Fallidos: {fail_count}")
    print(f"  📋 Total: {len(candidates)}")
    
    if dry_run:
        print("\n💡 Para ejecutar el archivado real, usa --execute")


if __name__ == "__main__":
    main()