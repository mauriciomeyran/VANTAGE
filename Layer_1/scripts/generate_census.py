import os
import re
import sys
import time
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────

script_dir = Path(__file__).resolve().parent
dotenv_path = script_dir.parent / "config" / "layer_1.env"

if not dotenv_path.exists():
    print(f"[ERROR] No se encontró layer_1.env en {dotenv_path}")
    sys.exit(1)

load_dotenv(dotenv_path=dotenv_path)
NOTION_TOKEN = os.getenv("NOTION_TOKEN") or os.getenv("NOTION_API_KEY")

if not NOTION_TOKEN:
    print("[ERROR] Ni NOTION_TOKEN ni NOTION_API_KEY definidos en layer_1.env")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

VALID_PREFIXES = ("KERNEL:", "MANUAL:", "CANON:", "CAREER_CANON:", "SP:", "ALIASES:", "CHANGELOG:")

DOCUMENTS = {
    "System Prompt": "37b938be-fc42-8001-9b9b-fcf81130d274",
    "Manual":        "372938be-fc42-8050-9a67-e40857d7806e",
    "Kernel":        "377938be-fc42-805e-a408-c9ae518d4fe7",
    "Career Canon":  "377938be-fc42-8089-93f2-f52dbd2dec6c",
    "Aliases":       "37c938be-fc42-80d4-b9ae-f5969830331b",
    "Change Log":    "390938be-fc42-80e7-b429-d7d730339353",
}

# Prioridad de documento al resolver el "mejor" bloque para un ID
# (menor número = mayor prioridad)
DOC_PRIORITY = {
    "Kernel":        1,
    "System Prompt": 2,
    "Manual":        3,
    "Career Canon":  4,
    "Aliases":       5,
    "Change Log":    6,
}

# ─── LISTADO CANÓNICO DE IDs (fuente: generate_census.py) ─────────────────────

CENSUS_SPEC = [
    {
        "name": "KERNEL",
        "rows": [
            {"id": "KERNEL:ARCHITECTURE-L0-BOOTSTRAP", "seccion": "§3 L0-B", "nombre": "Bootstrap Protocol / Dynamic Governance Layer"},
            {"id": "KERNEL:AUDIENCE-SCOPE", "seccion": "(encabezado)", "nombre": "Declaración de Audiencia y Alcance"},
            {"id": "KERNEL:PURPOSE", "seccion": "§1", "nombre": "Propósito del Sistema"},
            {"id": "KERNEL:ARCHITECTURE", "seccion": "§2", "nombre": "Arquitectura de Cuatro Capas"},
            {"id": "KERNEL:ARCHITECTURE-L0", "seccion": "§2.1", "nombre": "L0 — VANTAGE Runtime"},
            {"id": "KERNEL:SKILL-ANNOUNCE-CONVENTION", "seccion": "§2.1 (dentro de L0)", "nombre": "Convención de Anuncio de Skills (X-ING.../X-ED)"},
            {"id": "KERNEL:ARCHITECTURE-L0-BOOTSTRAP", "seccion": "§2.2", "nombre": "L0-Bootstrap — Dynamic Governance Layer"},
            {"id": "KERNEL:ARCHITECTURE-L1", "seccion": "§2.3", "nombre": "L1 — Active Recon"},
            {"id": "KERNEL:ARCHITECTURE-L2", "seccion": "§2.4", "nombre": "L2 — Strategic Search"},
            {"id": "KERNEL:ARCHITECTURE-L3", "seccion": "§2.5", "nombre": "L3 — Passive Intake"},
            # typo histórico + forma correcta como lookup_ids para máxima cobertura
            {"id": "KERNEL:ARHITECTURE-L4", "lookup_ids": ["KERNEL:ARHITECTURE-L4", "KERNEL:ARCHITECTURE-L4"], "seccion": "§2.6", "nombre": "L4 — Version Control & Infrastructure"},
            {"id": "KERNEL:DASHBOARD-CHECKLIST-ARCH", "seccion": "§3", "nombre": "Arquitectura Dashboard/Checklist"},
            {"id": "KERNEL:SCHEMA", "seccion": "§4", "nombre": "Class A vs Class B (Schema)"},
            {"id": "KERNEL:SCHEMA-001", "seccion": "§4.1", "nombre": "Class A vs Class B — definición de ownership"},
            {"id": "KERNEL:SCHEMA-002", "seccion": "§4.2", "nombre": "Restricción del Sistema"},
            {"id": "KERNEL:SCHEMA-003", "seccion": "§4.3", "nombre": "Fuente como Campo Especial"},
            {"id": "KERNEL:SCHEMA-004", "seccion": "§4.4", "nombre": "Entity Format"},
            {"id": "KERNEL:SCHEMA-005", "seccion": "§4.5", "nombre": "Contrato de Resolución: 4 Pasos"},
            {"id": "KERNEL:SCHEMA-006", "seccion": "§4.6", "nombre": "APROBAR_WRITE: Alcance"},
            {"id": "KERNEL:SCHEMA-007", "seccion": "§4.7", "nombre": "Acceptance Audit"},
            {"id": "KERNEL:TRACKER-SCHEMA", "seccion": "§5", "nombre": "Alcance y niveles de prioridad — Bug/Tasks Tracker"},
            {"id": "KERNEL:TRACKER-SCHEMA-001", "seccion": "§5.1", "nombre": "Alcance del Tracker"},
            {"id": "KERNEL:TRACKER-SCHEMA-002", "seccion": "§5.2", "nombre": "Niveles de Prioridad"},
            {"id": "KERNEL:HEALTH-CHECK", "seccion": "§6", "nombre": "Contrato de health_check.py"},
            {"id": "KERNEL:HEALTH-CHECK-001", "seccion": "§6.1", "nombre": "Entity Index Auto-Sync"},
            {"id": "KERNEL:HEALTH-CHECK-002", "seccion": "§6.2", "nombre": "Reporte de Tickets"},
            {"id": "KERNEL:OWNERSHIP", "seccion": "§7", "nombre": "Responsabilidades AI vs Python"},
            {"id": "KERNEL:OWNERSHIP-001", "seccion": "§7.1", "nombre": "AI Component"},
            {"id": "KERNEL:OWNERSHIP-002", "seccion": "§7.2", "nombre": "Python Component"},
            {"id": "KERNEL:TRIGGERS", "seccion": "§8", "nombre": "Contratos detallados de Triggers"},
            {"id": "KERNEL:TRIGGER-001", "seccion": "§8.1", "nombre": "FEED — Procesamiento por Lotes"},
            {"id": "KERNEL:TRIGGER-002", "seccion": "§8.2", "nombre": "VL1 — Comandos de mantenimiento del Tracker"},
            {"id": "KERNEL:TRIGGER-003", "seccion": "§8.3", "nombre": "QA — Checklist Canónico de 6 ítems"},
            {"id": "KERNEL:TRIGGER-004", "seccion": "§8.4", "nombre": "DRY RUN"},
            {"id": "KERNEL:TRIGGER-005", "seccion": "§8.5", "nombre": "SYNC"},
            {"id": "KERNEL:TRIGGER-006", "seccion": "§8.6", "nombre": "TOP 3 BY SCORE"},
            {"id": "KERNEL:TRIGGER-007", "seccion": "§8.7", "nombre": "NEXT ACTION"},
            {"id": "KERNEL:TRIGGER-008", "seccion": "§8.8", "nombre": "FEED (sin trigger CV-A)"},
            {"id": "KERNEL:TRIGGER-009", "seccion": "§8.9", "nombre": "STATUS"},
            {"id": "KERNEL:GATE-DECISION", "seccion": "§9", "nombre": "Lógica de gates"},
            {"id": "KERNEL:GATE-DECISION-001", "seccion": "§9.1", "nombre": "Lógica de Bypass"},
            {"id": "KERNEL:GATE-DECISION-002", "seccion": "§9.2", "nombre": "Lógica Estándar"},
            {"id": "KERNEL:GATE-DECISION-003", "seccion": "§9.3", "nombre": "Resolución de REVIEW_NEEDED"},
            {"id": "KERNEL:GATE-DECISION-004", "seccion": "§9.4", "nombre": "Por Qué los Gates Son Deterministas"},
            {"id": "KERNEL:GATE-DECISION-005", "seccion": "§9.5", "nombre": "Flujo de Recuperación BLOCKED"},
            {"id": "KERNEL:GATE-DECISION-006", "seccion": "§9.6", "nombre": "REJECTED (Post-Aplicación)"},
            {"id": "KERNEL:GATE-DECISION-007", "seccion": "§9.7", "nombre": "Ejecución Automática de Archivado"},
            {"id": "KERNEL:GATE-DECISION-008", "seccion": "§9.8", "nombre": "Capas de Evaluación de Gate: Técnica vs. Negocio"},
            {"id": "KERNEL:NAMING-CONVENTION", "seccion": "§10", "nombre": "Convención de Nombres de Outputs"},
            {"id": "KERNEL:CV-GOLDEN-RULES", "seccion": "§11", "nombre": "Reglas de Oro CV"},
            {"id": "KERNEL:CV-GOLDEN-RULES-001", "seccion": "§11.1", "nombre": "No Evaluar Fit Antes de Escribir"},
            {"id": "KERNEL:CV-GOLDEN-RULES-002", "seccion": "§11.2", "nombre": "No Calcular ni Estimar Campos Class B"},
            {"id": "KERNEL:CV-GOLDEN-RULES-003", "seccion": "§11.3", "nombre": "No Cuestionar la Calidad de Datos del Usuario"},
            {"id": "KERNEL:CV-GOLDEN-RULES-004", "seccion": "§11.4", "nombre": "No Delegar Escritura al Usuario"},
            {"id": "KERNEL:CV-GOLDEN-RULES-005", "seccion": "§11.5", "nombre": "No Interpretar en SYNC"},
            {"id": "KERNEL:CV-PIPELINE", "seccion": "§12", "nombre": "Flujo CV-A → CV-B"},
            {"id": "KERNEL:CANON-UPDATE", "seccion": "§13", "nombre": "Actualización del Canon"},
            {"id": "KERNEL:FAIL-PHILOSOPHY", "seccion": "§14", "nombre": "Filosofía de Fallo"},
            {"id": "KERNEL:SCOPE", "seccion": "§15", "nombre": "Scope y economía de contexto (Terminal vs MCP)"},
            {"id": "KERNEL:DATA-FLOW", "seccion": "§16", "nombre": "Flujo de Datos y Escritura"},
            {"id": "KERNEL:ROUTING", "seccion": "§17", "nombre": "Rutas de carga MCP / lazy_loader"},
            {"id": "KERNEL:EVOLUTION", "seccion": "§18", "nombre": "Evolución del sistema, deuda técnica, criterios de cambio"},
            {"id": "KERNEL:DOC-CONTRACT", "seccion": "§22 (TOC dice §21)", "nombre": "Contrato de IDs de Documento"},
            {"id": "KERNEL:NORM", "seccion": "§19", "nombre": "Normalización Documental (Legacy IDs)"},
            {"id": "KERNEL:CENSUS-SYNC", "seccion": "§20", "nombre": "Sincronización obligatoria del ID Census"},
            {"id": "KERNEL:SESSION-LEDGER", "seccion": "§21", "nombre": "Session Ledger — registro de apertura/cierre de sesión"},
            {"id": "KERNEL:DOCUMENTATION-TRANSVERSAL-001", "seccion": "§22", "nombre": "Documentación Transversal — Contrato de Integridad Documental"},
            {"id": "KERNEL:VERSION-CHECK-TOOL", "seccion": "(anexo, post-§21)", "nombre": "Herramienta de bajo costo para verificar versión de los 7 documentos fundacionales (verify_versions.py)"},
        ],
    },
    {
        "name": "SYSTEM PROMPT",
        "rows": [
            {"id": "SP:CEDULA-DIGITAL", "seccion": "§2", "nombre": "Cédula Digital — rutas de operación y UUIDs"},
            {"id": "KERNEL:SCOPE", "seccion": "§3 (referencia)", "nombre": "[Referencia a KERNEL:SCOPE — no sección propia del SP]"},
            {"id": "KERNEL:DATA-FLOW", "seccion": "§4 (referencia)", "nombre": "[Referencia a KERNEL:DATA-FLOW — no sección propia del SP]"},
            {"id": "SP:TRIGGERS", "seccion": "§5", "nombre": "Triggers operativos de VANTAGE"},
            {"id": "KERNEL:CV-GOLDEN-RULES", "seccion": "§6 (referencia)", "nombre": "[Referencia a KERNEL:CV-GOLDEN-RULES — no sección propia del SP]"},
            {"id": "SP:SCHEMA", "seccion": "§7", "nombre": "Schema — Trackers (Class A/B)"},
            {"id": "KERNEL:ROUTING", "seccion": "§8 (referencia)", "nombre": "[Referencia a KERNEL:ROUTING — no sección propia del SP]"},
            {"id": "SP:ID-CONNECTORS-001", "seccion": "§9", "nombre": "ID Connectors — esquema PREFIX:NOMBRE-SECCION"},
            {"id": "SP:BOOTSTRAP-001", "seccion": "(encabezado)", "nombre": "Operating Specification — Bootstrap de Sesión"},
            {"id": "SP:SYNC-RULE", "seccion": "§1", "nombre": "Sincronización Inicial y Verificación de Versión"},
            {"id": "SP:CONSISTENCY", "seccion": "§10", "nombre": "Regla de Consistencia Documental"},
            {"id": "SP:VERSION-CHECK-TOOL", "seccion": "§11", "nombre": "Herramienta de Verificación de Versión de Bajo Costo"},
        ],
    },
    {
        "name": "MANUAL",
        "rows": [
            {"id": "MANUAL:OBJETIVO-001", "seccion": "§1", "nombre": "Objetivo de VANTAGE"},
            {"id": "MANUAL:FUNCIONAMIENTO-001", "seccion": "§2", "nombre": "Cómo Funciona"},
            {"id": "MANUAL:SETUP-001", "seccion": "§3", "nombre": "Setup"},
            {"id": "MANUAL:FLUJO-001", "seccion": "§4", "nombre": "Flujo Punta a Punta"},
            {"id": "MANUAL:VCHECKLIST-001", "seccion": "§4.1", "nombre": "El Checklist — V-Checklist semanal"},
            {"id": "MANUAL:DASHBOARD-001", "seccion": "§4.2", "nombre": "Dashboard — recuperación antes de CV Optimization"},
            {"id": "MANUAL:VANTAGE-RUNTIME-001", "seccion": "§5", "nombre": "VANTAGE Runtime (Consulta Operativa)"},
            {"id": "MANUAL:GESTION-DATOS-001", "seccion": "§6", "nombre": "Gestión de Datos"},
            {"id": "MANUAL:TROUBLESHOOTING-001", "seccion": "§7", "nombre": "Troubleshooting"},
            {"id": "MANUAL:PROMPTS-WRAPPERS-001", "seccion": "§8", "nombre": "Prompts & Wrappers"},
            {"id": "MANUAL:CHEATSHEETS-001", "seccion": "§9", "nombre": "Cheat Sheets"},
            {"id": "MANUAL:HEALTHCHECK-001", "seccion": "§10", "nombre": "Health Check"},
            {"id": "MANUAL:REGLAS-DE-ORO-001", "seccion": "§12", "nombre": "Reglas de Oro para Operadores"},
            {"id": "MANUAL:FALLO-001", "seccion": "§13", "nombre": "Filosofía de Fallo para Operadores"},
            {"id": "MANUAL:SLA-001", "seccion": "§14", "nombre": "SLA de Latencia Post-Ingesta"},
            {"id": "MANUAL:SESSION-CYCLE-001", "seccion": "§5.6", "nombre": "Ciclo de Sesión — Open/Close"},
            {"id": "MANUAL:PATCH-QUALITY-001", "seccion": "§9", "nombre": "Criterio de Calidad para Parches Documentales"},
            {"id": "MANUAL:CV-GOLDEN-RULES-INDEX", "seccion": "§18", "nombre": "Reglas de Oro CV — Referencia Operativa"},
            {"id": "MANUAL:POSITIONING-CRITERIA", "seccion": "§19", "nombre": "Positioning Modes (N1–N4) — Criterio de Selección"},
            {"id": "MANUAL:GOLDEN-SKELETON-REF", "seccion": "§20", "nombre": "Golden Skeleton — Qué es y Dónde Vive"},
            {"id": "MANUAL:SCHEMA-FIELD-REF", "seccion": "§21", "nombre": "Schema Class A/B — Referencia de Campos"},
        ],
    },
    {
        "name": "CAREER CANON",
        "rows": [
            {"id": "CAREER_CANON:AUDIENCE-SCOPE", "lookup_ids": ["CAREER_CANON:AUDIENCE-SCOPE", "CANON:AUDIENCE-SCOPE"], "seccion": "(encabezado)", "nombre": "Declaración de Audiencia y Alcance del Canon Runtime"},
            {"id": "CANON:PROFILE-001", "seccion": "§A", "nombre": "Professional Profile Canon"},
            {"id": "CANON:SKILLS-001", "seccion": "§B", "nombre": "Skills Canon"},
            {"id": "CANON:EXPERIENCE-001", "seccion": "§D", "nombre": "Experience Records"},
            {
                "id": "CANON:EXPERIENCE-C01 … C05",
                "lookup_ids": [
                    "CANON:EXPERIENCE-C01",
                    "CANON:EXPERIENCE-C02",
                    "CANON:EXPERIENCE-C03",
                    "CANON:EXPERIENCE-C04",
                    "CANON:EXPERIENCE-C05",
                ],
                "seccion": "§D.1–D.5",
                "nombre": "C01 L'Oréal Luxe · C02 Bisonte Experiential · C03 Levi Strauss (Dockers) · C04 Aéropostale · C05 El Palacio de Hierro (ALDO)",
            },
            {"id": "CANON:ACHIEVEMENTS-001", "seccion": "§H", "nombre": "Achievement Library"},
            {"id": "CANON:KPIS-001", "seccion": "§I", "nombre": "Core KPIs"},
            {
                "id": "CANON:KPI-001 … KPI-008",
                "lookup_ids": [
                    "CANON:KPI-001", "CANON:KPI-002", "CANON:KPI-003", "CANON:KPI-004",
                    "CANON:KPI-005", "CANON:KPI-006", "CANON:KPI-007", "CANON:KPI-008",
                ],
                "seccion": "§I.1–I.8",
                "nombre": "KPI01 Traffic +43% · KPI02 Conversion +18% · KPI03 Campaign Cost -74% · KPI04 Floorset Time -33% · KPI05 POP Coverage 100% · KPI06 Rebranding Coverage 100% · KPI07 Adidas Punch List (17) · KPI08 Years Experience (10+)",
            },
            {"id": "CANON:FACTS-001", "seccion": "§J", "nombre": "Canonical Facts"},
            {
                "id": "CANON:FACT-001 … FACT-008",
                "lookup_ids": [
                    "CANON:FACT-001", "CANON:FACT-002", "CANON:FACT-003", "CANON:FACT-004",
                    "CANON:FACT-005", "CANON:FACT-006", "CANON:FACT-007", "CANON:FACT-008",
                ],
                "seccion": "§J.1–J.8",
                "nombre": "CF01 ALDO Cert. Year 2014 · CF02 ALDO Periodo 2012–2017 · CF03 Adidas Punch List 17 · CF04 Adidas Punch List Non-Blocking · CF05 Levi's 270+ POS/6 países · CF06 Aéropostale 21 Direct Reports · CF07 Aéropostale 17 Stores · CF08 L'Oréal Marcas",
            },
            {
                "id": "CANON:UF-001 … UF-003",
                "lookup_ids": ["CANON:UF-001", "CANON:UF-002", "CANON:UF-003"],
                "seccion": "§J.9–J.11",
                "nombre": "UF01 L'Oréal End Date · UF02 Canonical Email · UF03 Certifications Canon",
            },
            {"id": "CANON:POSITIONING-001", "seccion": "§K", "nombre": "Positioning Modes N1–N4"},
            {
                "id": "CANON:POSITIONING-N1 … N4",
                "lookup_ids": [
                    "CANON:POSITIONING-N1", "CANON:POSITIONING-N2",
                    "CANON:POSITIONING-N3", "CANON:POSITIONING-N4",
                ],
                "seccion": "§K.1–K.4",
                "nombre": "N1 Luxury Brand Execution · N2 Store Design & Flagship · N3 Regional Brand Execution & Rollout · N4 Commercial VM & Field Leadership",
            },
            {"id": "CANON:OUTPUT-CONTRACT-001", "seccion": "§L", "nombre": "Output Contract"},
            {"id": "CANON:OUTPUT-CONTRACT-SKELETON-001", "seccion": "§L.1", "nombre": "Golden Skeleton (Reference)"},
            {"id": "CANON:OUTPUT-CONTRACT-TAGREGISTRY-001", "seccion": "§L.3", "nombre": "Tag Registry (doble ID junto con CANON:TAG-REGISTRY, ver nota)"},
            {"id": "CANON:FIGMA-TAG-SCHEMA", "seccion": "§L.2", "nombre": "Figma Tag Schema"},
            {"id": "CANON:POSITIONING-MODE", "seccion": "§L.3.1", "nombre": "Activación por Positioning Mode"},
            {"id": "CANON:TAG-REGISTRY", "seccion": "§L.3", "nombre": "Tag Registry (doble ID junto con CANON:OUTPUT-CONTRACT-TAGREGISTRY-001, ver nota)"},
        ],
    },
]

# ─── CAPA DE RED (engine de generator.py con rate-limit de generate_census.py) ─

def fetch_blocks(block_id: str) -> list:
    """Obtiene todos los bloques de un nivel con paginación y manejo de rate-limit."""
    blocks = []
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    cursor = None

    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor

        r = requests.get(url, headers=HEADERS, params=params)

        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 2))
            print(f"  [429] Rate limit. Esperando {wait}s...")
            time.sleep(wait)
            continue

        if r.status_code != 200:
            print(f"  [ERROR {r.status_code}] bloque {block_id}: {r.text[:120]}")
            break

        data = r.json()
        blocks.extend(data.get("results", []))

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    return blocks


def fetch_blocks_recursive(block_id: str) -> list:
    """Barre recursivamente todos los bloques hijos (engine de generator.py)."""
    result = []
    for block in fetch_blocks(block_id):
        result.append(block)
        if block.get("has_children") and block["type"] not in ("child_page", "child_database"):
            result.extend(fetch_blocks_recursive(block["id"]))
    return result

# ─── EXTRACCIÓN DE IDs (engine de generator.py, expandido a más block types) ──

def extract_ids_from_rich_text(rich_text: list) -> list:
    """Extrae todos los tokens que empiecen con un prefijo válido."""
    ids = []
    for segment in rich_text:
        text = segment.get("plain_text", "").strip()
        for token in text.split():
            clean = token.strip(".,;:()[]{}<>`'\"""''")
            if clean.startswith(VALID_PREFIXES):
                ids.append(clean)
    return ids


# Patrón canónico de encabezado de sección: "§N — PREFIX:KEY", "§N.M — PREFIX:KEY",
# admite guión largo (—) o corto (-) como separador, y espacio opcional.
# Ej: "§22 — KERNEL:DOCUMENTATION-TRANSVERSAL-001", "§2.6 - KERNEL:ARHITECTURE-L4"
SECTION_HEADING_PREFIX_RE = re.compile(r"^§[\w.]+\s*[—-]\s*")


def is_definition_block(plain: str, id_str: str, btype: str) -> bool:
    """
    Determina si el bloque ES la definición del ID (heading o texto que arranca
    con el ID), vs. una mención de pasada.

    Reconoce DOS nomenclaturas válidas de heading, ambas presentes en los
    documentos fundacionales:
      (a) Heading = ID puro, ej. "### KERNEL:ARCHITECTURE-L0"
      (b) Heading = "§N — ID" (sección numerada), ej. "## §22 — KERNEL:DOC-CONTRACT"
    La versión anterior de esta función solo cubría (a); (b) es el formato de
    TODOS los headings de sección de primer nivel del Kernel, lo que hacía que
    ninguna sección nueva pudiera detectarse como huérfana (ver DT — Census
    Sync, corrida 2026-07-16).
    """
    stripped = plain.strip("` \n")
    heading_body = SECTION_HEADING_PREFIX_RE.sub("", stripped)
    is_heading = btype in {"heading_1", "heading_2", "heading_3"}
    return (
        stripped == id_str
        or stripped == f"ID: {id_str}"
        or f"ID: {id_str}" in plain
        or (is_heading and plain.lstrip("` ").startswith(id_str))          # nomenclatura (a)
        or (is_heading and heading_body.startswith(id_str))                # nomenclatura (b)
    )


def extract_ids_from_block(block: dict) -> list:
    """
    Devuelve lista de (id_str, is_definition) para cada ID encontrado en el bloque.
    Cubre: headings, párrafos, listas, callouts, quotes, toggles, code, table_row.
    """
    btype = block["type"]
    found = []

    text_types = {
        "paragraph", "bulleted_list_item", "numbered_list_item",
        "callout", "quote", "toggle",
        "heading_1", "heading_2", "heading_3",
    }

    if btype in text_types:
        rich_text = block[btype].get("rich_text", [])
        plain = "".join(s.get("plain_text", "") for s in rich_text).strip()
        for id_str in extract_ids_from_rich_text(rich_text):
            found.append((id_str, is_definition_block(plain, id_str, btype)))

    elif btype == "code":
        rich_text = block["code"].get("rich_text", [])
        plain = "".join(s.get("plain_text", "") for s in rich_text).strip()
        for line in plain.splitlines():
            for id_str in extract_ids_from_rich_text([{"plain_text": line}]):
                is_def = line.strip().strip("`") == id_str
                found.append((id_str, is_def))

    elif btype == "table_row":
        cells = block["table_row"].get("cells", [])
        for cell in cells:
            cell_plain = "".join(s.get("plain_text", "") for s in cell).strip()
            for id_str in extract_ids_from_rich_text(cell):
                is_def = cell_plain.strip("` \n") == id_str or f"ID: {id_str}" in cell_plain
                found.append((id_str, is_def))

    return found

# ─── CONSTRUCCIÓN DEL ÍNDICE ───────────────────────────────────────────────────

def build_link_index() -> dict:
    """
    Barre todos los documentos y construye un índice:
      id_str -> list of { doc, link, is_def }
    """
    link_index = {}

    for doc_name, page_id in DOCUMENTS.items():
        print(f"Indexando: {doc_name}...")
        blocks = fetch_blocks_recursive(page_id)
        page_id_clean = page_id.replace("-", "")

        for block in blocks:
            block_id_clean = block["id"].replace("-", "")
            link = f"https://app.notion.com/p/{page_id_clean}#{block_id_clean}"

            for id_str, is_def in extract_ids_from_block(block):
                link_index.setdefault(id_str, []).append({
                    "doc":    doc_name,
                    "link":   link,
                    "is_def": is_def,
                })

    return link_index


def pick_best_link(entries: list) -> dict | None:
    """
    Selecciona el mejor candidato priorizando:
      1. Bloques de definición (is_def=True) sobre menciones
      2. Documento de mayor prioridad (menor número en DOC_PRIORITY)
    """
    if not entries:
        return None

    defs = [e for e in entries if e["is_def"]]
    pool = defs if defs else entries

    return min(pool, key=lambda e: (DOC_PRIORITY.get(e["doc"], 999), e["link"]))


def resolve_link(row: dict, link_index: dict) -> str | None:
    """Resuelve el mejor link para una fila del CENSUS_SPEC."""
    lookup_ids = row.get("lookup_ids") or [row["id"]]
    candidates = []
    for lid in lookup_ids:
        candidates.extend(link_index.get(lid, []))
    best = pick_best_link(candidates)
    return best["link"] if best else None

# ─── DETECCIÓN DE HUÉRFANOS (KERNEL:CENSUS-SYNC, Regla 2) ─────────────────────

def known_ids_from_spec() -> set:
    """
    Aplana CENSUS_SPEC a un set de todos los IDs "conocidos" (tanto el
    id declarado como cualquier lookup_id asociado), para poder comparar
    contra lo que realmente se encontró en los documentos.
    """
    known = set()
    for section in CENSUS_SPEC:
        for row in section["rows"]:
            known.add(row["id"])
            for lid in row.get("lookup_ids", []):
                known.add(lid)
    return known


# IDs retirados formalmente (ver Change Log) que persisten como texto
# narrativo/histórico dentro de la propia entrada de retiro. No son
# definiciones activas — el heading/sección real ya no existe — pero el
# extractor los marca is_def=True al toparse con el patrón `PREFIX:CLAVE`
# dentro de esa entrada histórica. Confirmado ruido documentado (v9.2.0),
# no requieren alta en CENSUS_SPEC ni acción recurrente.
KNOWN_RETIRED_NOISE = {
    "MANUAL:DASHBOARD-CHECKLIST-001",  # retirado v9.1.6, dividido en
                                        # MANUAL:VCHECKLIST-001 + MANUAL:DASHBOARD-001
}


def find_orphan_ids(link_index: dict, known_ids: set) -> dict:
    """
    Detecta IDs encontrados en los documentos (con al menos un bloque de
    definición, is_def=True) que NO están declarados en CENSUS_SPEC.

    Solo se consideran definiciones, no menciones sueltas, para evitar
    falsos positivos de cross-references (ej. "ver KERNEL:X en el Kernel").

    IDs retirados y documentados en KNOWN_RETIRED_NOISE se excluyen incluso
    si el extractor los marca is_def=True, porque la "definición" detectada
    es en realidad la narración histórica de su propio retiro (ver Change
    Log), no una sección viva sin dar de alta.

    Devuelve: id_str -> mejor entry (doc, link) para reportarlo, ordenado
    por prefijo y nombre para lectura consistente.
    """
    orphans = {}
    for id_str, entries in link_index.items():
        if id_str in known_ids:
            continue
        if id_str in KNOWN_RETIRED_NOISE:
            continue
        def_entries = [e for e in entries if e["is_def"]]
        if not def_entries:
            continue  # solo mención de pasada, no es una definición nueva
        orphans[id_str] = pick_best_link(def_entries)

    return dict(sorted(orphans.items()))

# ─── RENDER ────────────────────────────────────────────────────────────────────

def render_markdown(link_index: dict, orphans: dict) -> tuple:
    """
    Genera el Markdown en el formato "bonito" curado por el operador en
    Notion: un subtítulo `##` por documento, tabla de 3 columnas
    (ID · Sección · Nombre — sin columna de estatus), separador `---`
    entre documentos. Este formato es una vista de auditoría/espejo del
    CENSUS_SPEC; la fuente de verdad para lectura humana sigue siendo la
    página de Notion (394938be), curada a mano por el operador.
    """
    lines = []
    unresolved = []

    for i, section in enumerate(CENSUS_SPEC):
        if i > 0:
            lines.append("---")
            lines.append("")
        lines += [f"## {section['name']}", "", "| ID | Sección | Nombre |", "|---|---|---|"]
        for row in section["rows"]:
            link = resolve_link(row, link_index)
            display_id = row["id"]
            seccion = row.get("seccion", "")
            nombre = row.get("nombre", "")
            if link:
                cell = f"[`{display_id}`]( {link} )"
            else:
                cell = f"`{display_id}`"
                unresolved.append(display_id)
            lines.append(f"| {cell} | {seccion} | {nombre} |")
        lines.append("")

    # Sección de huérfanos — siempre se imprime, incluso vacía, para que
    # quede explícito en el artefacto que la detección corrió (Regla 2:
    # "no ignorar silenciosamente IDs nuevos").
    lines.append("---")
    lines.append("")
    lines += ["## IDs Huérfanos (fuera de CENSUS_SPEC)", ""]
    if orphans:
        lines += ["| ID | Documento | Link |", "|---|---|---|"]
        for id_str, entry in orphans.items():
            lines.append(f"| `{id_str}` | {entry['doc']} | [link]( {entry['link']} ) |")
    else:
        lines.append("_Ninguno detectado en esta corrida._")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n", unresolved

# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\nV-ID-CENSUS Generator v3.0")
    print(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 52)

    link_index = build_link_index()
    known_ids = known_ids_from_spec()
    orphans = find_orphan_ids(link_index, known_ids)
    md, unresolved = render_markdown(link_index, orphans)

    output = Path("V_ID_CENSUS_PRODUCTION.md")
    output.write_text(md, encoding="utf-8")

    total = sum(len(s["rows"]) for s in CENSUS_SPEC)
    print("\n" + "=" * 52)
    print(f"  IDs en spec:          {total}")
    print(f"  IDs resueltos:        {total - len(unresolved)}")
    print(f"  IDs SIN link:         {len(unresolved)}")
    if unresolved:
        print("  Sin resolver:")
        for uid in unresolved:
            print(f"    - {uid}")
    print("-" * 52)
    print(f"  IDs huérfanos (en docs, fuera de spec): {len(orphans)}")
    if orphans:
        print("  ⚠ Huérfanos detectados — agregar a CENSUS_SPEC o confirmar que son ruido:")
        for uid, entry in orphans.items():
            print(f"    - {uid}  ({entry['doc']})")
    print("=" * 52)
    print(f"\nExportado a: {output.resolve()}")
