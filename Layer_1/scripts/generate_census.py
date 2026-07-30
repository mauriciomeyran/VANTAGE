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

VALID_PREFIXES = ("KERNEL:", "MANUAL:", "CANON:", "CAREER_CANON:", "SP:", "ALIASES:", "CHANGELOG:", "CHANGELOG_ARCHIVE:", "BRIEF:")

DOCUMENTS = {
    "System Prompt": "37b938be-fc42-8001-9b9b-fcf81130d274",
    "Manual":        "372938be-fc42-8050-9a67-e40857d7806e",
    "Kernel":        "377938be-fc42-805e-a408-c9ae518d4fe7",
    "Career Canon":  "377938be-fc42-8089-93f2-f52dbd2dec6c",
    "Aliases":       "37c938be-fc42-80d4-b9ae-f5969830331b",
    "Change Log":    "390938be-fc42-80e7-b429-d7d730339353",
    "Navigation Brief": "3a3938be-fc42-8008-9e90-ec435c01f50d",
}

DOC_PRIORITY = {
    "Kernel":        1,
    "System Prompt": 2,
    "Manual":        3,
    "Career Canon":  4,
    "Aliases":       5,
    "Change Log":    6,
    "Navigation Brief": 7,
}

# ─── LISTADO CANÓNICO DE IDs ──────────────────────────────────────────────────

CENSUS_SPEC = [
    {
        "name": "KERNEL",
        "rows": [
            {"id": "KERNEL:PURPOSE", "seccion": "§1", "nombre": "Propósito del Sistema"},
            {"id": "KERNEL:FAIL-PHILOSOPHY", "seccion": "§2", "nombre": "Filosofía de Fallo"},
            {"id": "KERNEL:DOCUMENTATION", "seccion": "§3", "nombre": "Documentación (L0)"},
            {"id": "KERNEL:DOCUMENTATION-001", "seccion": "§3.1", "nombre": "Canonical Document ID Contract"},
            {"id": "KERNEL:DOCUMENTATION-002", "seccion": "§3.2", "nombre": "Normalización Documental de IDs Legacy"},
            {"id": "KERNEL:DOCUMENTATION-003", "seccion": "§3.3", "nombre": "L0 — VANTAGE Runtime"},
            {"id": "KERNEL:DOCUMENTATION-004", "seccion": "§3.4", "nombre": "L0-Bootstrap — Dynamic Governance Layer"},
            {"id": "KERNEL:DOCUMENTATION-005", "seccion": "§3.5", "nombre": "Convención de Anuncio de Skills"},
            {"id": "KERNEL:DOCUMENTATION-006", "seccion": "§3.6", "nombre": "Contrato de health_check.py"},
            {"id": "KERNEL:DOCUMENTATION-007", "seccion": "§3.7", "nombre": "Version-Check Tool (verify_versions.py)"},
            {"id": "KERNEL:DOCUMENTATION-008", "seccion": "§3.8", "nombre": "Sincronización Obligatoria del ID Census"},
            {"id": "KERNEL:DOCUMENTATION-009", "seccion": "§3.9", "nombre": "Registro de Continuidad de Sesión"},
            {"id": "KERNEL:DOCUMENTATION-010", "seccion": "§3.10", "nombre": "Documentación Transversal"},
            {"id": "KERNEL:DOCUMENTATION-011", "seccion": "§3.11", "nombre": "Sistema de Cross-Reference Hyperlinks"},
            {"id": "KERNEL:ARCHITECTURE", "seccion": "§4", "nombre": "Arquitectura de Cuatro Capas"},
            {"id": "KERNEL:ARCHITECTURE-L1", "seccion": "§4", "nombre": "L1 — Active Recon"},
            {"id": "KERNEL:ARCHITECTURE-L2", "seccion": "§4", "nombre": "L2 — Strategic Search"},
            {"id": "KERNEL:ARCHITECTURE-L3", "seccion": "§4", "nombre": "L3 — Passive Intake"},
            {"id": "KERNEL:ARCHITECTURE-L4", "lookup_ids": ["KERNEL:ARCHITECTURE-L4", "KERNEL:ARHITECTURE-L4"], "seccion": "§4", "nombre": "L4 — Version Control & Infrastructure"},
            {"id": "KERNEL:OWNERSHIP", "seccion": "§5", "nombre": "División de Responsabilidades AI/Python"},
            {"id": "KERNEL:OWNERSHIP-001", "seccion": "§5.1", "nombre": "AI Component"},
            {"id": "KERNEL:OWNERSHIP-002", "seccion": "§5.2", "nombre": "Python Component"},
            {"id": "KERNEL:DASHBOARD-CHECKLIST-ARCH", "seccion": "§6", "nombre": "Arquitectura Dashboard/Checklist"},
            {"id": "KERNEL:SCHEMA", "seccion": "§7", "nombre": "Modelo de Datos y Ownership"},
            {"id": "KERNEL:SCHEMA-001", "seccion": "§7.1", "nombre": "Schema — Class A Fields"},
            {"id": "KERNEL:SCHEMA-002", "seccion": "§7.2", "nombre": "Schema — Class B Fields"},
            {"id": "KERNEL:SCHEMA-003", "seccion": "§7.3", "nombre": "Schema — Field Validation Rules"},
            {"id": "KERNEL:SCHEMA-004", "seccion": "§7.4", "nombre": "Schema — Relationship Constraints"},
            {"id": "KERNEL:SCHEMA-005", "seccion": "§7.5", "nombre": "Schema — Index Definition"},
            {"id": "KERNEL:SCHEMA-006", "seccion": "§7.6", "nombre": "Schema — Migration Strategy"},
            {"id": "KERNEL:SCHEMA-007", "seccion": "§7.7", "nombre": "Schema — Version Control"},
            {"id": "KERNEL:TRACKER-SCHEMA", "seccion": "§8", "nombre": "Bug Tracker y Tasks Tracker"},
            {"id": "KERNEL:TRACKER-SCHEMA-001", "seccion": "§8.1", "nombre": "Tracker Schema — Bug Tracker"},
            {"id": "KERNEL:TRACKER-SCHEMA-002", "seccion": "§8.2", "nombre": "Tracker Schema — Tasks Tracker"},
            {"id": "KERNEL:GATE-DECISION", "seccion": "§9", "nombre": "Lógica de Gate Decision"},
            {"id": "KERNEL:GATE-DECISION-001", "seccion": "§9.1", "nombre": "Bypass"},
            {"id": "KERNEL:GATE-DECISION-002", "seccion": "§9.2", "nombre": "Lógica Estándar"},
            {"id": "KERNEL:GATE-DECISION-003", "seccion": "§9.3", "nombre": "Resolución de REVIEW_NEEDED"},
            {"id": "KERNEL:GATE-DECISION-004", "seccion": "§9.4", "nombre": "Por Qué los Gates Son Deterministas"},
            {"id": "KERNEL:GATE-DECISION-005", "seccion": "§9.5", "nombre": "Flujo de Recuperación BLOCKED"},
            {"id": "KERNEL:GATE-DECISION-006", "seccion": "§9.6", "nombre": "REJECTED (Post-Aplicación)"},
            {"id": "KERNEL:GATE-DECISION-007", "seccion": "§9.7", "nombre": "Ejecución Automática de Archivado"},
            {"id": "KERNEL:GATE-DECISION-008", "seccion": "§9.8", "nombre": "Capas de Evaluación de Gate: Técnica vs. Negocio"},
            {"id": "KERNEL:GATE-DECISION-009", "seccion": "§9.9", "nombre": "Escalamiento de Pendientes a Tickets"},
            {"id": "KERNEL:GATE-DECISION-010", "seccion": "§9.10", "nombre": "Gate Decision — Technical Review"},
            {"id": "KERNEL:GATE-DECISION-011", "seccion": "§9.11", "nombre": "Gate Decision — Business Review"},
            {"id": "KERNEL:CV-GOLDEN-RULES", "seccion": "§10", "nombre": "Golden Rules — Límites de Ejecución"},
            {"id": "KERNEL:CV-GOLDEN-RULES-001", "seccion": "§10", "nombre": "Regla de Oro #1"},
            {"id": "KERNEL:CV-GOLDEN-RULES-002", "seccion": "§10", "nombre": "Regla de Oro #2"},
            {"id": "KERNEL:CV-GOLDEN-RULES-003", "seccion": "§10", "nombre": "Regla de Oro #3"},
            {"id": "KERNEL:CV-GOLDEN-RULES-004", "seccion": "§10", "nombre": "Regla de Oro #4"},
            {"id": "KERNEL:CV-GOLDEN-RULES-005", "seccion": "§10", "nombre": "Regla de Oro #5"},
            {"id": "KERNEL:TRIGGERS", "seccion": "§11", "nombre": "Contratos de Ejecución del AI Component"},
            {"id": "KERNEL:TRIGGER-001", "seccion": "§11.1", "nombre": "Trigger — Discovery Request"},
            {"id": "KERNEL:TRIGGER-002", "seccion": "§11.2", "nombre": "Trigger — CV Optimization"},
            {"id": "KERNEL:TRIGGER-003", "seccion": "§11.3", "nombre": "Trigger — Recovery Request"},
            {"id": "KERNEL:TRIGGER-004", "seccion": "§11.4", "nombre": "Trigger — Documentation Update"},
            {"id": "KERNEL:TRIGGER-005", "seccion": "§11.5", "nombre": "Trigger — Schema Validation"},
            {"id": "KERNEL:TRIGGER-006", "seccion": "§11.6", "nombre": "Trigger — Gate Decision"},
            {"id": "KERNEL:TRIGGER-007", "seccion": "§11.7", "nombre": "Trigger — Archiving"},
            {"id": "KERNEL:TRIGGER-008", "seccion": "§11.8", "nombre": "Trigger — Health Check"},
            {"id": "KERNEL:TRIGGER-009", "seccion": "§11.9", "nombre": "Trigger — Version Check"},
            {"id": "KERNEL:CV-PIPELINE", "seccion": "§12", "nombre": "Pipeline de CV"},
            {"id": "KERNEL:CANON-UPDATE", "seccion": "§13", "nombre": "Actualización del Canon"},
            {"id": "KERNEL:NAMING-CONVENTION", "seccion": "§14", "nombre": "Convención de Nombres"},
            {"id": "KERNEL:CONTEXT-INFRASTRUCTURE", "seccion": "§16", "nombre": "Context Infrastructure"},
            {"id": "KERNEL:CONTEXT-INFRASTRUCTURE-001", "seccion": "§16.1", "nombre": "Context Infrastructure — Data Sources"},
            {"id": "KERNEL:CONTEXT-INFRASTRUCTURE-002", "seccion": "§16.2", "nombre": "Context Infrastructure — Integration Points"},
            {"id": "KERNEL:DATA-FLOW", "seccion": "§17", "nombre": "Flujo de Datos"},
            {"id": "KERNEL:EVOLUTION", "seccion": "§18", "nombre": "Evolución del Sistema"},
        ],
    },
    {
        "name": "MANUAL",
        "rows": [
            {"id": "MANUAL:OBJECTIVE", "seccion": "§1", "nombre": "Objetivo de VANTAGE"},
            {"id": "MANUAL:HOW-IT-WORKS", "seccion": "§2", "nombre": "Cómo Funciona"},
            {"id": "MANUAL:FAILURE-PHILOSOPHY", "seccion": "§3", "nombre": "Filosofía de Fallo para Operadores"},
            {"id": "MANUAL:SETUP", "seccion": "§4", "nombre": "Setup"},
            {"id": "MANUAL:COLD-START", "seccion": "§5", "nombre": "Arranque Frío — Checklist de Reactivación"},
            {"id": "MANUAL:SESSION-CYCLE", "seccion": "§6", "nombre": "Ciclo de Sesión — Open/Close"},
            {"id": "MANUAL:VCHECKLIST", "seccion": "§7", "nombre": "El Checklist — V-Checklist semanal"},
            {"id": "MANUAL:WEEKLY-FLOW", "seccion": "§8", "nombre": "Flujo Semanal de Operación"},
            {"id": "MANUAL:DASHBOARD-001", "seccion": "§8.2", "nombre": "Dashboard — recuperación antes de CV Optimization"},
            {"id": "MANUAL:VANTAGE-RUNTIME", "seccion": "§9", "nombre": "VANTAGE Runtime (Consulta Operativa)"},
            {"id": "MANUAL:DATA-MANAGEMENT", "seccion": "§10", "nombre": "Gestión de Datos"},
            {"id": "MANUAL:HEALTHCHECK", "seccion": "§11", "nombre": "Health Check"},
            {"id": "MANUAL:TROUBLESHOOTING", "seccion": "§12", "nombre": "Troubleshooting"},
            {"id": "MANUAL:PROMPTS-WRAPPERS", "seccion": "§13", "nombre": "Prompts & Wrappers"},
            {"id": "MANUAL:CHEATSHEETS", "seccion": "§14", "nombre": "Cheat Sheets"},
            {"id": "MANUAL:PATCH-QUALITY", "seccion": "§15", "nombre": "Criterio de Calidad para Parches Documentales"},
            {"id": "MANUAL:GOLDEN-RULES", "seccion": "§16", "nombre": "Reglas de Oro para Operadores"},
            {"id": "MANUAL:SLA", "seccion": "§17", "nombre": "SLA de Latencia Post-Ingesta"},
            {"id": "MANUAL:CV-GOLDEN-RULES-INDEX", "seccion": "§18", "nombre": "Reglas de Oro CV — Referencia Operativa"},
            {"id": "MANUAL:POSITIONING-CRITERIA", "seccion": "§19", "nombre": "Positioning Modes (N1–N4) — Criterio de Selección"},
            {"id": "MANUAL:CADENCE-MATRIX", "seccion": "§20", "nombre": "Cadence Matrix — Weekly Rhythm"},
            {"id": "MANUAL:GOLDEN-SKELETON-REF", "seccion": "§21", "nombre": "Golden Skeleton — Qué es y Dónde Vive"},
            {"id": "MANUAL:SCHEMA-FIELD-REF", "seccion": "§22", "nombre": "Schema Class A/B — Referencia de Campos"},
            {"id": "CANON:PROFILE", "seccion": "§A", "nombre": "Professional Profile Canon"},
            {"id": "CANON:SKILLS", "seccion": "§B", "nombre": "Skills Canon"},
            {"id": "CANON:EXPERIENCE", "seccion": "§D", "nombre": "Experience Records"},
            {"id": "CANON:EXPERIENCE-C01", "seccion": "§D.1", "nombre": "C01 L'Oréal Luxe"},
            {"id": "CANON:EXPERIENCE-C02", "seccion": "§D.2", "nombre": "C02 Bisonte Experiential"},
            {"id": "CANON:EXPERIENCE-C03", "seccion": "§D.3", "nombre": "C03 Levi Strauss (Dockers)"},
            {"id": "CANON:EXPERIENCE-C04", "seccion": "§D.4", "nombre": "C04 Aéropostale"},
            {"id": "CANON:EXPERIENCE-C05", "seccion": "§D.5", "nombre": "C05 El Palacio de Hierro (ALDO)"},
            {"id": "CANON:ACHIEVEMENTS", "seccion": "§H", "nombre": "Achievement Library"},
            {"id": "CANON:KPIS", "seccion": "§I", "nombre": "Core KPIs"},
            {"id": "CANON:KPI-001", "seccion": "§I.1", "nombre": "KPI — Revenue Impact"},
            {"id": "CANON:KPI-002", "seccion": "§I.2", "nombre": "KPI — Cost Optimization"},
            {"id": "CANON:KPI-003", "seccion": "§I.3", "nombre": "KPI — Time to Market"},
            {"id": "CANON:KPI-004", "seccion": "§I.4", "nombre": "KPI — Quality Score"},
            {"id": "CANON:KPI-005", "seccion": "§I.5", "nombre": "KPI — Customer Satisfaction"},
            {"id": "CANON:KPI-006", "seccion": "§I.6", "nombre": "KPI — Team Productivity"},
            {"id": "CANON:KPI-007", "seccion": "§I.7", "nombre": "KPI — Innovation Index"},
            {"id": "CANON:KPI-008", "seccion": "§I.8", "nombre": "KPI — Strategic Alignment"},
            {"id": "CANON:FACTS", "seccion": "§J", "nombre": "Canonical Facts"},
            {"id": "CANON:FACT-001", "seccion": "§J.1", "nombre": "Fact — Industry Experience"},
            {"id": "CANON:FACT-002", "seccion": "§J.2", "nombre": "Fact — Technical Stack"},
            {"id": "CANON:FACT-003", "seccion": "§J.3", "nombre": "Fact — Team Leadership"},
            {"id": "CANON:FACT-004", "seccion": "§J.4", "nombre": "Fact — Project Scale"},
            {"id": "CANON:FACT-005", "seccion": "§J.5", "nombre": "Fact — Geographic Scope"},
            {"id": "CANON:FACT-006", "seccion": "§J.6", "nombre": "Fact — Budget Management"},
            {"id": "CANON:FACT-007", "seccion": "§J.7", "nombre": "Fact — Methodology Expertise"},
            {"id": "CANON:FACT-008", "seccion": "§J.8", "nombre": "Fact — Certifications & Education"},
            {"id": "CANON:POSITIONING", "seccion": "§K", "nombre": "Positioning Modes N1–N4"},
            {"id": "CANON:POSITIONING-N1", "seccion": "§K.1", "nombre": "Positioning N1 — Strategic Leader"},
            {"id": "CANON:POSITIONING-N2", "seccion": "§K.2", "nombre": "Positioning N2 — Technical Expert"},
            {"id": "CANON:POSITIONING-N3", "seccion": "§K.3", "nombre": "Positioning N3 — Delivery Manager"},
            {"id": "CANON:POSITIONING-N4", "seccion": "§K.4", "nombre": "Positioning N4 — Innovation Driver"},
            {"id": "CANON:OUTPUT-CONTRACT", "seccion": "§L", "nombre": "Output Contract Framework"},
            {"id": "CANON:OUTPUT-CONTRACT-001", "seccion": "§L.1", "nombre": "Output Contract — CV Documents"},
            {"id": "CANON:OUTPUT-CONTRACT-002", "seccion": "§L.2", "nombre": "Output Contract — Portfolio Materials"},
            {"id": "CANON:OUTPUT-CONTRACT-003", "seccion": "§L.3", "nombre": "Output Contract — Case Studies"},
            {"id": "CANON:OUTPUT-CONTRACT-004", "seccion": "§L.4", "nombre": "Output Contract — Interview Prep"},
            {"id": "CANON:UF-001", "seccion": "§M.1", "nombre": "Unique Factor — Global Experience"},
            {"id": "CANON:UF-002", "seccion": "§M.2", "nombre": "Unique Factor — Industry Transformation"},
            {"id": "CANON:UF-003", "seccion": "§M.3", "nombre": "Unique Factor — Digital Innovation"},
        ],
    },
    {
        "name": "NAVIGATION BRIEF",
        "rows": [
            {"id": "BRIEF:PURPOSE-SCOPE", "lookup_ids": ["BRIEF:PURPOSE-SCOPE", "BRIEF:SCOPE", "BRIEF:001"], "seccion": "§0", "nombre": "Propósito y Alcance"},
            {"id": "BRIEF:AUTHORITY-MATRIX", "lookup_ids": ["BRIEF:AUTHORITY-MATRIX", "BRIEF:002"], "seccion": "§1", "nombre": "Matriz de Autoridad Documental"},
            {"id": "BRIEF:ECOSYSTEM", "lookup_ids": ["BRIEF:ECOSYSTEM", "BRIEF:003"], "seccion": "§2", "nombre": "Ecosistema Documental"},
            {"id": "BRIEF:NAV-CONTRACTS", "lookup_ids": ["BRIEF:NAV-CONTRACTS", "BRIEF:004"], "seccion": "§3", "nombre": "Contratos de navegación"},
            {"id": "BRIEF:DOMAIN-ARCHITECTURE", "lookup_ids": ["BRIEF:DOMAIN-ARCHITECTURE", "BRIEF:005"], "seccion": "§4", "nombre": "Dominios"},
            {"id": "BRIEF:VERIFICATION-DEPTH", "lookup_ids": ["BRIEF:VERIFICATION-DEPTH", "BRIEF:006"], "seccion": "§5", "nombre": "Contratos de verificación"},
            {"id": "BRIEF:CROSS-DEPENDENCIES", "lookup_ids": ["BRIEF:CROSS-DEPENDENCIES", "BRIEF:007"], "seccion": "§6", "nombre": "Dependencias entre documentos"},
            {"id": "BRIEF:MAINTENANCE-CONTRACT", "lookup_ids": ["BRIEF:MAINTENANCE-CONTRACT", "BRIEF:008"], "seccion": "§7", "nombre": "Contrato de Mantenimiento"},
            {"id": "BRIEF:DECISION-TREE", "lookup_ids": ["BRIEF:DECISION-TREE", "BRIEF:009"], "seccion": "§8", "nombre": "Árbol de Decisiones"},
            {"id": "BRIEF:NAV-PRINCIPLES", "lookup_ids": ["BRIEF:NAV-PRINCIPLES", "BRIEF:010"], "seccion": "§9", "nombre": "Principios de Navegación"},
            {"id": "BRIEF:EXPECTED-OUTCOME", "lookup_ids": ["BRIEF:EXPECTED-OUTCOME", "BRIEF:011"], "seccion": "§10", "nombre": "Resultado Esperado"},
            {"id": "BRIEF:AUTHORITY-001", "seccion": "TBD", "nombre": "TBD"},
            {"id": "BRIEF:CONSULTATION-001", "seccion": "TBD", "nombre": "TBD"},
            {"id": "BRIEF:CROSS-DEPENDENCIES-001", "seccion": "TBD", "nombre": "TBD"},
            {"id": "BRIEF:CROSS-DEPENDENCIES-002", "seccion": "TBD", "nombre": "TBD"},
            {"id": "BRIEF:CROSS-DEPENDENCIES-003", "seccion": "TBD", "nombre": "TBD"},
            {"id": "BRIEF:HOUSEKEEPING-001", "seccion": "TBD", "nombre": "TBD"},
            {"id": "BRIEF:PURPOSE-SCOPE-001", "seccion": "TBD", "nombre": "TBD"},
            {"id": "BRIEF:PURPOSE-SCOPE-002", "seccion": "TBD", "nombre": "TBD"},
            {"id": "BRIEF:PURPOSE-SCOPE-003", "seccion": "TBD", "nombre": "TBD"},
        ],
    },
    {
        "name": "SYSTEM PROMPT",
        "rows": [
            {
                "id": "SP:BOOTSTRAP",
                "lookup_ids": ["SP:BOOTSTRAP-001", "SP:BOOTSTRAP"],
                "seccion": "§1",
                "nombre": "Operating Specification — Bootstrap de Sesión"
            },
            {"id": "SP:SYNC-RULE", "seccion": "§2", "nombre": "Sincronización Inicial y Verificación de Versión"},
            {"id": "SP:CONTEXT-INFRASTRUCTURE-REF", "seccion": "§4", "nombre": "Referencia — Context Infrastructure (KERNEL:CONTEXT-INFRASTRUCTURE)"},
            {
                "id": "SP:DIGITAL-ID-CARD",
                "lookup_ids": ["SP:DIGITAL-ID-CARD-001", "SP:DIGITAL-ID-CARD"],
                "seccion": "§3",
                "nombre": "Cédula Digital — rutas de operación y UUIDs"
            },
            {"id": "SP:DATA-FLOW-REF", "seccion": "§5", "nombre": "Referencia — Consultar en Technical Kernel (KERNEL:DATA-FLOW)"},
            {"id": "SP:TRIGGERS", "seccion": "§6", "nombre": "Triggers operativos de VANTAGE"},
            {"id": "SP:CV-GOLDEN-RULES-REF", "seccion": "§7", "nombre": "Referencia — Consultar en Technical Kernel (KERNEL:CV-GOLDEN-RULES)"},
            {"id": "SP:SCHEMA", "seccion": "§8", "nombre": "Schema — Trackers (Class A/B)"},
            {"id": "SP:MCP-ROUTING-NOTES", "seccion": "§9", "nombre": "Notas Operativas de Ruteo MCP/Terminal (ex duplicado SP:CONSISTENCY)"},
            {"id": "SP:ID-CONNECTORS", "seccion": "§10", "nombre": "ID Connectors — esquema PREFIX:NOMBRE-SECCION"},
            {"id": "SP:CONSISTENCY", "seccion": "§11", "nombre": "Regla de Consistencia Documental"},
            {"id": "SP:VERSION-CHECK-TOOL", "seccion": "§12", "nombre": "Herramienta de Verificación de Versión de Bajo Costo"},
        ],
    },
    {
        "name": "ALIASES",
        "rows": [
            {"id": "ALIASES:SESSION-CYCLE", "seccion": "§1", "nombre": "Session Cycle"},
            {"id": "ALIASES:L0-RUNTIME", "seccion": "§2", "nombre": "L0 · VANTAGE Runtime"},
            {"id": "ALIASES:L1L2-DISCOVERY", "seccion": "§3", "nombre": "L1/L2 · Discovery (Lunes)"},
            {"id": "ALIASES:L3-PASSIVE-INTAKE", "seccion": "§4", "nombre": "L3 · Passive Intake"},
            {"id": "ALIASES:L4-VERSION-CONTROL", "seccion": "§5", "nombre": "L4 · Version Control & Documentación"},
            {"id": "ALIASES:DASHBOARD", "seccion": "§6", "nombre": "Dashboard (Martes — Recuperación)"},
            {"id": "ALIASES:CV-PIPELINE", "seccion": "§7", "nombre": "CV Pipeline (Miércoles)"},
            {"id": "ALIASES:DEDUP", "seccion": "§8", "nombre": "Dedup & Oportunidades"},
        ],
    },
]

# ─── CAPA DE RED ──────────────────────────────────────────────────────────────

class FetchIncompleteError(Exception):
    pass


MAX_RETRIES_PER_PAGE = 3
RETRY_BACKOFF_SECONDS = 2


def fetch_blocks(block_id: str) -> list:
    blocks = []
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    cursor = None

    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor

        last_error = None
        for attempt in range(1, MAX_RETRIES_PER_PAGE + 1):
            r = requests.get(url, headers=HEADERS, params=params)

            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", 2))
                print(f"  [429] Rate limit. Esperando {wait}s... (intento {attempt}/{MAX_RETRIES_PER_PAGE})")
                time.sleep(wait)
                last_error = f"429 tras {attempt} intentos"
                continue

            if r.status_code != 200:
                wait = RETRY_BACKOFF_SECONDS * attempt
                print(
                    f"  [ERROR {r.status_code}] bloque {block_id} "
                    f"(intento {attempt}/{MAX_RETRIES_PER_PAGE}): {r.text[:120]} "
                    f"— reintentando en {wait}s..."
                )
                time.sleep(wait)
                last_error = f"{r.status_code}: {r.text[:200]}"
                continue

            data = r.json()
            blocks.extend(data.get("results", []))
            last_error = None
            break

        if last_error is not None:
            raise FetchIncompleteError(
                f"No se pudo obtener una página completa de {block_id} "
                f"tras {MAX_RETRIES_PER_PAGE} intentos. Último error: {last_error}. "
                f"Bloques indexados antes del fallo: {len(blocks)}."
            )

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    return blocks


def fetch_blocks_recursive(block_id: str) -> list:
    result = []
    for block in fetch_blocks(block_id):
        result.append(block)
        if block.get("has_children") and block["type"] not in ("child_page", "child_database"):
            result.extend(fetch_blocks_recursive(block["id"]))
    return result

# ─── EXTRACCIÓN DE IDs ────────────────────────────────────────────────────────

def extract_ids_from_rich_text(rich_text: list) -> list:
    ids = []
    for segment in rich_text:
        text = segment.get("plain_text", "").strip()
        for token in text.split():
            clean = token.strip(".,;:()[]{}<>`'\"""''")
            if clean.startswith(VALID_PREFIXES):
                ids.append(clean)
    return ids


SECTION_HEADING_PREFIX_RE = re.compile(r"^§[\w.]+\s*(?:[—-]\s*)?")
SECTION_HEADING_CAPTURE_RE = re.compile(r"^§([\w.]+)\s*(?:[—-]\s*)?")
LEADING_NUMBER_SECTION_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+")


def extract_live_section(plain: str) -> str | None:
    stripped = plain.strip("` \n")
    m = SECTION_HEADING_CAPTURE_RE.match(stripped)
    if m:
        return f"§{m.group(1)}"
    m2 = LEADING_NUMBER_SECTION_RE.match(stripped)
    if m2:
        return m2.group(1)
    return None


def is_definition_block(plain: str, id_str: str, btype: str) -> bool:
    stripped = plain.strip("` \n")
    heading_body = SECTION_HEADING_PREFIX_RE.sub("", stripped)
    if heading_body == stripped:
        heading_body = LEADING_NUMBER_SECTION_RE.sub("", stripped)
    is_heading = btype in {"heading_1", "heading_2", "heading_3"}
    return (
        stripped == id_str
        or stripped == f"ID: {id_str}"
        or _contains_id_boundary(plain, f"ID: {id_str}")
        or (is_heading and _starts_with_id_boundary(plain.lstrip("` "), id_str))
        or (is_heading and _starts_with_id_boundary(heading_body, id_str))
    )


def _contains_id_boundary(haystack: str, needle: str) -> bool:
    idx = haystack.find(needle)
    if idx == -1:
        return False
    end = idx + len(needle)
    if end >= len(haystack):
        return True
    nxt = haystack[end]
    return not (nxt.isalnum() or nxt in "-_:")


def _starts_with_id_boundary(text: str, id_str: str) -> bool:
    if not text.startswith(id_str):
        return False
    rest = text[len(id_str):]
    return rest == "" or not (rest[0].isalnum() or rest[0] in "-_:")


def extract_ids_from_block(block: dict) -> list:
    btype = block["type"]
    found = []

    text_types = {
        "paragraph", "bulleted_list_item", "numbered_list_item",
        "callout", "quote", "toggle",
        "heading_1", "heading_2", "heading_3",
    }
    is_heading_type = btype in {"heading_1", "heading_2", "heading_3"}

    if btype in text_types:
        rich_text = block[btype].get("rich_text", [])
        plain = "".join(s.get("plain_text", "") for s in rich_text).strip()
        for id_str in extract_ids_from_rich_text(rich_text):
            is_def = is_definition_block(plain, id_str, btype)
            seccion = extract_live_section(plain) if is_def else None

            found.append((id_str, is_def, seccion))

    elif btype == "code":
        rich_text = block["code"].get("rich_text", [])
        plain = "".join(s.get("plain_text", "") for s in rich_text).strip()
        for line in plain.splitlines():
            for id_str in extract_ids_from_rich_text([{"plain_text": line}]):
                is_def = line.strip().strip("`") == id_str
                found.append((id_str, is_def, None))

    elif btype == "table_row":
        cells = block["table_row"].get("cells", [])
        for cell in cells:
            cell_plain = "".join(s.get("plain_text", "") for s in cell).strip()
            for id_str in extract_ids_from_rich_text(cell):
                is_def = cell_plain.strip("` \n") == id_str or f"ID: {id_str}" in cell_plain
                found.append((id_str, is_def, None))

    return found

# ─── CONSTRUCCIÓN DEL ÍNDICE ───────────────────────────────────────────────────

def build_link_index() -> tuple:
    link_index = {}
    incomplete_docs = []

    for doc_name, page_id in DOCUMENTS.items():
        print(f"Indexando: {doc_name}...")
        try:
            blocks = fetch_blocks_recursive(page_id)
        except FetchIncompleteError as e:
            print(f"  [INCOMPLETO] {doc_name}: {e}")
            incomplete_docs.append({"doc": doc_name, "error": str(e)})
            continue

        page_id_clean = page_id.replace("-", "")

        for block in blocks:
            block_id_clean = block["id"].replace("-", "")
            link = f"https://app.notion.com/p/{page_id_clean}#{block_id_clean}"

            for id_str, is_def, seccion in extract_ids_from_block(block):
                link_index.setdefault(id_str, []).append({
                    "doc":     doc_name,
                    "link":    link,
                    "is_def":  is_def,
                    "seccion": seccion,
                })

    return link_index, incomplete_docs


def pick_best_link(entries: list) -> dict | None:
    if not entries:
        return None

    defs = [e for e in entries if e["is_def"]]
    pool = defs if defs else entries

    with_seccion = [e for e in pool if e.get("seccion")]
    ranked_pool = with_seccion if with_seccion else pool

    return min(ranked_pool, key=lambda e: (DOC_PRIORITY.get(e["doc"], 999), e["link"]))


def resolve_link(row: dict, link_index: dict) -> dict | None:
    lookup_ids = row.get("lookup_ids") or [row["id"]]
    candidates = []
    for lid in lookup_ids:
        candidates.extend(link_index.get(lid, []))
    return pick_best_link(candidates)

# ─── DETECCIÓN DE HUÉRFANOS ───────────────────────────────────────────────────

def known_ids_from_spec() -> set:
    known = set()
    for section in CENSUS_SPEC:
        for row in section["rows"]:
            known.add(row["id"])
            for lid in row.get("lookup_ids", []):
                known.add(lid)
    return known


KNOWN_RETIRED_NOISE = {
    "MANUAL:DASHBOARD-CHECKLIST-001",
}


def find_orphan_ids(link_index: dict, known_ids: set) -> dict:
    orphans = {}
    for id_str, entries in link_index.items():
        if id_str in known_ids or id_str in KNOWN_RETIRED_NOISE:
            continue
        def_entries = [e for e in entries if e["is_def"]]
        if not def_entries:
            continue
        orphans[id_str] = pick_best_link(def_entries)

    return dict(sorted(orphans.items()))

# ─── RENDER ────────────────────────────────────────────────────────────────────

def render_markdown(link_index: dict, orphans: dict) -> tuple:
    lines = []
    unresolved = []
    hardcoded_fallbacks = []

    for i, section in enumerate(CENSUS_SPEC):
        if i > 0:
            lines.append("---")
            lines.append("")
        lines += [f"## {section['name']}", "", "| ID | Sección | Nombre |", "|---|---|---|"]
        for row in section["rows"]:
            best = resolve_link(row, link_index)
            display_id = row["id"]
            link = best["link"] if best else None
            live_seccion = best.get("seccion") if best else None
            nombre = row.get("nombre", "")

            if live_seccion:
                seccion = live_seccion
            else:
                seccion = row.get("seccion", "")
                if link:
                    seccion = f"{seccion} ⚠︎sin verificar en vivo" if seccion else "⚠︎sin verificar en vivo"
                    hardcoded_fallbacks.append(display_id)

            if link:
                cell = f"[`{display_id}`]( {link} )"
            else:
                cell = f"`{display_id}`"
                unresolved.append(display_id)
            lines.append(f"| {cell} | {seccion} | {nombre} |")
        lines.append("")

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

    return "\n".join(lines).rstrip() + "\n", unresolved, hardcoded_fallbacks

# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

def print_debug_ids(link_index: dict, ids_to_debug: list) -> None:
    print("\n" + "#" * 52)
    print("  DEBUG-ID: candidatos crudos en link_index")
    print("#" * 52)
    for id_str in ids_to_debug:
        entries = link_index.get(id_str)
        print(f"\n  {id_str}:")
        if not entries:
            print("    (sin ninguna entrada — el ID nunca fue extraído de ningún bloque)")
            continue
        for e in entries:
            print(f"    - doc={e['doc']!r} is_def={e['is_def']} seccion={e.get('seccion')!r} link={e['link']}")
    print("\n" + "#" * 52)


if __name__ == "__main__":
    debug_ids = []
    if "--debug-id" in sys.argv:
        idx = sys.argv.index("--debug-id")
        debug_ids = sys.argv[idx + 1:]
        if not debug_ids:
            print("[ERROR] --debug-id requiere al menos un ID después, ej.:")
            print("  python3 generate_census.py --debug-id KERNEL:GATE-DECISION-001 KERNEL:GATE-DECISION-004")
            sys.exit(1)

    print(f"\nV-ID-CENSUS Generator v3.0")
    print(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 52)

    link_index, incomplete_docs = build_link_index()

    if debug_ids:
        print_debug_ids(link_index, debug_ids)
        sys.exit(0)

    known_ids = known_ids_from_spec()
    orphans = find_orphan_ids(link_index, known_ids)
    md, unresolved, hardcoded_fallbacks = render_markdown(link_index, orphans)

    output = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/data/V_ID_CENSUS_PRODUCTION.md")
    output.parent.mkdir(parents=True, exist_ok=True)
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
    print("-" * 52)
    print(f"  IDs con Sección hardcodeada (sin heading '§N' detectable en vivo): {len(hardcoded_fallbacks)}")
    if hardcoded_fallbacks:
        print("  ⚠ Revisar manualmente si el número/letra en CENSUS_SPEC sigue vigente:")
        for uid in hardcoded_fallbacks:
            print(f"    - {uid}")
    print("=" * 52)

    if incomplete_docs:
        print("\n  ⚠️  ADVERTENCIA: CENSUS INCOMPLETO")
        print("  Los siguientes documentos NO se indexaron completos")
        for entry in incomplete_docs:
            print(f"    - {entry['doc']}: {entry['error']}")

    print(f"\nExportado a: {output.resolve()}")