#!/usr/bin/env python3
"""
verify_versions.py — VANTAGE Write-Back Verification (TCK-04)

Verifica la propiedad "Versión" de los 6 documentos fundacionales + Changelog
+ Census, sin traer el body completo de cada página (a diferencia de un
fetch vía MCP). Usa pages.retrieve() — solo metadata/propiedades.

Uso:
    cd ~/Documents/03 Projects/VANTAGE/Layer_1/scripts
    source ../.venv/bin/activate
    python3 verify_versions.py

Requiere layer_1.env con NOTION_TOKEN. Reutiliza el mismo patrón que el
resto de los scripts de Layer_1 (requests directo, sin dependencia del
SDK notion-client, para minimizar puntos de fallo).

Salida esperada: tabla de 7 filas, documento | versión | fecha actualización.
Si algún documento no coincide con el resto (drift), se marca con ⚠️.
"""

import os
import sys
import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

NOTION_VERSION = "2025-09-03"
API_BASE = "https://api.notion.com/v1"

# Los 7 documentos de gobernanza VANTAGE (6 fundacionales + Changelog).
# El Census (394938be) se incluye también porque participa en el mismo
# ciclo de normalización de versión, aunque no sea "fundacional" per KERNEL:SYNC-RULE.
DOCUMENTS = [
    ("KERNEL",        "377938be-fc42-805e-a408-c9ae518d4fe7"),
    ("MANUAL",        "372938be-fc42-8050-9a67-e40857d7806e"),
    ("CAREER CANON",  "377938be-fc42-8089-93f2-f52dbd2dec6c"),
    ("SYSTEM PROMPT", "37b938be-fc42-8001-9b9b-fcf81130d274"),
    ("ALIASES",       "37c938be-fc42-80d4-b9ae-f5969830331b"),
    ("CHANGELOG",     "390938be-fc42-80e7-b429-d7d730339353"),
    ("ID CENSUS",     "394938be-fc42-81e6-a381-e3869e60d89d"),
]

VERSION_PROPERTY_NAME = "Versión"
DATE_PROPERTY_NAME = "Fecha de actualización"

# La propiedad "Versión" en el ID CENSUS no siempre estuvo poblada
# consistentemente en el histórico — si aparece vacía, se reporta como tal,
# no se asume error del script.


def load_token() -> str:
    """Carga NOTION_TOKEN desde layer_1.env (mismo patrón que otros scripts)."""
    env_candidates = [
        os.path.join(os.path.dirname(__file__), "..", "layer_1.env"),
        os.path.join(os.path.dirname(__file__), "layer_1.env"),
        os.path.expanduser("~/Documents/03 Projects/VANTAGE/Layer_1/layer_1.env"),
    ]
    for path in env_candidates:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("NOTION_TOKEN="):
                        token = line.split("=", 1)[1].strip().strip('"').strip("'")
                        # Guard contra el bug histórico de \n embebido (ver Changelog v8.6)
                        token = token.replace("\\n", "").strip()
                        if token:
                            return token
    # Fallback: variable de entorno ya exportada en la shell
    token = os.environ.get("NOTION_TOKEN", "").strip()
    if token:
        return token
    print("ERROR: NOTION_TOKEN no encontrado en layer_1.env ni en el entorno.")
    print("Verifica la ruta de layer_1.env o exporta NOTION_TOKEN manualmente.")
    sys.exit(1)


def fetch_page_properties(page_id: str, token: str) -> dict:
    """pages.retrieve() — solo propiedades, sin bloques de contenido."""
    url = f"{API_BASE}/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json().get("properties", {})


def extract_rich_text_or_select(prop: dict) -> str:
    """Extrae valor legible de una propiedad, sin importar el tipo (rich_text,
    select, title, etc.) — la propiedad Versión ha existido como distintos
    tipos a lo largo del historial del sistema."""
    if not prop:
        return "(vacío)"
    ptype = prop.get("type")
    if ptype == "rich_text":
        parts = prop.get("rich_text", [])
        return "".join(p.get("plain_text", "") for p in parts) or "(vacío)"
    if ptype == "title":
        parts = prop.get("title", [])
        return "".join(p.get("plain_text", "") for p in parts) or "(vacío)"
    if ptype == "select":
        sel = prop.get("select")
        return sel.get("name", "(vacío)") if sel else "(vacío)"
    if ptype == "date":
        d = prop.get("date")
        return d.get("start", "(vacío)") if d else "(vacío)"
    return f"(tipo no manejado: {ptype})"


def main():
    token = load_token()
    results = []
    errors = []

    for name, page_id in DOCUMENTS:
        try:
            props = fetch_page_properties(page_id, token)
            version = extract_rich_text_or_select(props.get(VERSION_PROPERTY_NAME, {}))
            date = extract_rich_text_or_select(props.get(DATE_PROPERTY_NAME, {}))
            results.append((name, version, date))
        except requests.exceptions.RequestException as e:
            errors.append((name, str(e)))
            results.append((name, "ERROR", "—"))

    # --- Reporte ---
    print("=" * 60)
    print("VANTAGE — VERIFICACIÓN DE VERSIÓN (verify_versions.py)")
    print("=" * 60)
    print(f"{'Documento':<15} {'Versión':<12} {'Actualizado'}")
    print("-" * 60)

    versions_seen = set()
    for name, version, date in results:
        marker = ""
        if version not in ("ERROR", "(vacío)"):
            versions_seen.add(version)
        print(f"{name:<15} {version:<12} {date}")

    print("-" * 60)

    if len(versions_seen) > 1:
        print(f"⚠️  WRITE-BACK MISMATCH — {len(versions_seen)} versiones distintas detectadas: {sorted(versions_seen)}")
        print("    No se puede confirmar Regla de Versión Única (SP:SYNC-RULE) hasta resolver.")
        exit_code = 1
    elif len(versions_seen) == 1:
        print(f"✅ Todos los documentos coinciden en versión: {versions_seen.pop()}")
        exit_code = 0
    else:
        print("⚠️  No se pudo determinar versión de ningún documento — revisar errores abajo.")
        exit_code = 1

    if errors:
        print()
        print("Errores de conexión:")
        for name, err in errors:
            print(f"  - {name}: {err}")
        exit_code = 1

    print("=" * 60)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
