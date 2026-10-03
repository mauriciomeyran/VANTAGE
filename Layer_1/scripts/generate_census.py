import ast
import os
import re
import sys
import time
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

try:
    from notion_utils import _notion_version
except ImportError:
    def _notion_version() -> str:
        return os.environ.get("NOTION_VERSION", "2025-09-03")

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
    "Notion-Version": _notion_version(),
    "Content-Type": "application/json",
}

# Change Log y Changelog Archivo quedan fuera del Census por diseño (son
# bitácoras cronológicas de versiones, no documentos con secciones canónicas
# direccionables en CENSUS_SPEC).
EXCLUDED_FROM_CENSUS_BY_DESIGN = ("Change Log", "Changelog Archivo")
CHANGELOG_PAGE_ID = "390938be-fc42-80e7-b429-d7d730339353"

VALID_PREFIXES = ("KERNEL:", "MANUAL:", "CANON:", "CAREER_CANON:", "SP:", "ALIASES:", "BRIEF:", "CHARTER:")

DOCUMENTS = {
    "System Prompt": "37b938be-fc42-8001-9b9b-fcf81130d274",
    "Manual":        "372938be-fc42-8050-9a67-e40857d7806e",
    "Kernel":        "377938be-fc42-805e-a408-c9ae518d4fe7",
    "Career Canon":  "377938be-fc42-8089-93f2-f52dbd2dec6c",
    "Aliases":       "37c938be-fc42-80d4-b9ae-f5969830331b",
    "Navigation Brief": "3a3938be-fc42-8008-9e90-ec435c01f50d",
    "Project Charter": "f87938be-fc42-8263-a305-819877d2245f",
}

DOC_PRIORITY = {
    "Kernel":        1,
    "System Prompt": 2,
    "Manual":        3,
    "Career Canon":  4,
    "Aliases":       5,
    "Navigation Brief": 6,
    "Project Charter": 7,
}

# ─── LISTADO CANÓNICO DE IDs ──────────────────────────────────────────────────

CENSUS_SPEC = [
    {
        "name": "PROJECT CHARTER",
        "rows": [
            {"id": "CHARTER:PURPOSE", "seccion": "01", "nombre": "Propósito del Proyecto"},
            {"id": "CHARTER:DECISIONS", "seccion": "02", "nombre": "Registro de Decisiones"},
            {"id": "CHARTER:DECISIONS-001", "seccion": "2.1", "nombre": "Separación Class A / Class B"},
            {"id": "CHARTER:DECISIONS-002", "seccion": "2.2", "nombre": "Aéropostale removido de Hard Blocks"},
            {"id": "CHARTER:DECISIONS-003", "seccion": "2.3", "nombre": "Serial Authority v2 — operador como Prioridad 0"},
            {"id": "CHARTER:DECISIONS-004", "seccion": "2.4", "nombre": "Retiro de layer_1_run.py / consolidate_duplicates.py (G6)"},
            {"id": "CHARTER:DECISIONS-005", "seccion": "2.5", "nombre": "Cierre E2E de Runtime/Lazy Loader — Graph declarado SUSPENDED"},
            {"id": "CHARTER:DECISIONS-006", "seccion": "2.6", "nombre": "Detección de fabricación en auditoría externa"},
            {"id": "CHARTER:DECISIONS-007", "seccion": "2.7", "nombre": "Dedup_Flag migrado de select a checkbox"},
            {"id": "CHARTER:DECISIONS-008", "seccion": "2.8", "nombre": "Reconciliación v10 — modelo de tracks paralelos"},
            {"id": "CHARTER:DECISIONS-009", "seccion": "2.9", "nombre": "Blueprint de reescritura KERNEL/MANUAL v10 — adopción híbrida"},
            {"id": "CHARTER:DECISIONS-010", "seccion": "2.10", "nombre": "Creación de este Charter"},
            {"id": "CHARTER:DECISIONS-011", "seccion": "2.11", "nombre": "CLAUDE/MAIN declarado gatekeeper exclusivo del Charter"},
            {"id": "CHARTER:FAILURES", "seccion": "03", "nombre": "Registro de Fallos"},
            {"id": "CHARTER:FAILURES-001", "seccion": "3.1", "nombre": "Reaparición de Hard Blocks ya corregidos"},
            {"id": "CHARTER:FAILURES-002", "seccion": "3.2", "nombre": "Patrón de reporte optimista (ticket RT-1)"},
            {"id": "CHARTER:FAILURES-003", "seccion": "3.3", "nombre": "Cédula de Reconciliación fabricada"},
            {"id": "CHARTER:FAILURES-004", "seccion": "3.4", "nombre": "Loop de auto-rechazo QA↔CV-B"},
            {"id": "CHARTER:FAILURES-005", "seccion": "3.5", "nombre": "Documentación que describe código ya retirado"},
            {"id": "CHARTER:NON-NEGOTIABLES", "seccion": "04", "nombre": "Principios No Negociables"},
            {"id": "CHARTER:NON-NEGOTIABLES-001", "seccion": "4.1", "nombre": "Python es dueño exclusivo de los campos Class B"},
            {"id": "CHARTER:NON-NEGOTIABLES-002", "seccion": "4.2", "nombre": "APROBAR_WRITE obligatorio antes de cualquier escritura"},
            {"id": "CHARTER:NON-NEGOTIABLES-003", "seccion": "4.3", "nombre": "Ningún reporte de éxito se acepta sin re-fetch/verificación"},
            {"id": "CHARTER:NON-NEGOTIABLES-004", "seccion": "4.4", "nombre": "Serial de handoff del operador se adopta en el mismo turno"},
            {"id": "CHARTER:NON-NEGOTIABLES-005", "seccion": "4.5", "nombre": "Todo diagnóstico externo se trata como hipótesis"},
            {"id": "CHARTER:NON-NEGOTIABLES-006", "seccion": "4.6", "nombre": "Ningún agente delegado resuelve discrepancias por su cuenta"},
            {"id": "CHARTER:NON-NEGOTIABLES-007", "seccion": "4.7", "nombre": "tracker_flow.is_mutable() única fuente de verdad de mutabilidad"},
            {"id": "CHARTER:NON-NEGOTIABLES-008", "seccion": "4.8", "nombre": "Graph/Backlinks son artefactos derivados, nunca capa de autoridad"},
            {"id": "CHARTER:NON-NEGOTIABLES-009", "seccion": "4.9", "nombre": "VM_Scope es binario (Alto/Bajo)"},
            {"id": "CHARTER:NON-NEGOTIABLES-010", "seccion": "4.10", "nombre": "Hard Blocks reales se consultan siempre en la fuente"},
            {"id": "CHARTER:MILESTONES", "seccion": "05", "nombre": "Hitos y Milestones"},
            {"id": "CHARTER:MILESTONES-001", "seccion": "5.1", "nombre": "Hito 1 — Track Beta (código) cerrado"},
            {"id": "CHARTER:MILESTONES-002", "seccion": "5.2", "nombre": "Hito 2 — T2.1 KERNEL v10 en paralelo a Track Beta"},
            {"id": "CHARTER:MILESTONES-003", "seccion": "5.3", "nombre": "Hito 3 — MANUAL v10 en paralelo a KERNEL v10"},
            {"id": "CHARTER:MILESTONES-004", "seccion": "5.4", "nombre": "Hito 4 — Fase 3 sync + verificación cruzada"},
            {"id": "CHARTER:MILESTONES-005", "seccion": "5.5", "nombre": "Hito 5 — Charter actualizado en cada decisión estructural"},
            {"id": "CHARTER:CONTINUITY", "seccion": "06", "nombre": "Continuidad Operativa"},
            {"id": "CHARTER:STATUS", "seccion": "07", "nombre": "Estatus del Proyecto"},
        ],
    },
    {
        "name": "KERNEL",
        "rows": [
            {"id": "KERNEL:PURPOSE", "seccion": "01", "nombre": "Propósito del Sistema"},
            {"id": "KERNEL:INVARIANTS", "seccion": "02", "nombre": "KERNEL:INVARIANTS"},
            {"id": "KERNEL:INV-LIST", "seccion": "02.1", "nombre": "KERNEL:INV LIST"},
            {"id": "KERNEL:FAIL", "seccion": "02.2", "nombre": "KERNEL:FAIL"},
            {"id": "KERNEL:FAIL-BEHAVIOR", "seccion": "02.3", "nombre": "KERNEL:FAIL BEHAVIOR"},
            {"id": "KERNEL:FAIL-DASHBOARD", "seccion": "02.4", "nombre": "KERNEL:FAIL DASHBOARD"},
            {"id": "KERNEL:ACTORS", "seccion": "03", "nombre": "KERNEL:ACTORS"},
            {"id": "KERNEL:ACT-SPLIT", "seccion": "03.2", "nombre": "KERNEL:ACT SPLIT"},
            {"id": "KERNEL:ACT-AI", "seccion": "03.3", "nombre": "KERNEL:ACT AI"},
            {"id": "KERNEL:ACT-PY", "seccion": "03.4", "nombre": "KERNEL:ACT PY"},
            {"id": "KERNEL:ARCHITECTURE", "seccion": "04", "nombre": "Arquitectura de Cuatro Capas"},
            {"id": "KERNEL:ARC-L0", "seccion": "04.1", "nombre": "KERNEL:ARC L0"},
            {"id": "KERNEL:ARC-L1", "seccion": "04.2", "nombre": "KERNEL:ARC L1"},
            {"id": "KERNEL:ARC-L2", "seccion": "04.3", "nombre": "KERNEL:ARC L2"},
            {"id": "KERNEL:ARC-L3", "seccion": "04.4", "nombre": "KERNEL:ARC L3"},
            {"id": "KERNEL:ARC-L4", "seccion": "04.5", "nombre": "KERNEL:ARC L4"},
            {"id": "KERNEL:ARC-DASH", "seccion": "04.6", "nombre": "KERNEL:ARC DASH"},
            {"id": "KERNEL:SCHEMA", "seccion": "05", "nombre": "Modelo de Datos y Ownership"},
            {"id": "KERNEL:SCH-DEDUP-GUARD", "seccion": "05.1", "nombre": "KERNEL:SCH DEDUP GUARD"},
            {"id": "KERNEL:SCH-RESTRICTIONS", "seccion": "05.2", "nombre": "KERNEL:SCH RESTRICTIONS"},
            {"id": "KERNEL:SCH-FUENTE", "seccion": "05.3", "nombre": "KERNEL:SCH FUENTE"},
            {"id": "KERNEL:SCH-ENTITY", "seccion": "05.4", "nombre": "KERNEL:SCH ENTITY"},
            {"id": "KERNEL:SCH-RESOLUTION", "seccion": "05.5", "nombre": "KERNEL:SCH RESOLUTION"},
            {"id": "KERNEL:SCH-APPROVE", "seccion": "05.6", "nombre": "KERNEL:SCH APPROVE"},
            {"id": "KERNEL:SCH-AUDIT", "seccion": "05.7", "nombre": "KERNEL:SCH AUDIT"},
            {"id": "KERNEL:SCH-NEXTACTION", "seccion": "05.8", "nombre": "KERNEL:SCH NEXTACTION"},
            {"id": "KERNEL:SCH-WRITERS", "seccion": "05.9", "nombre": "KERNEL:SCH WRITERS"},
            {"id": "KERNEL:SCH-TRACKER", "seccion": "05.10", "nombre": "KERNEL:SCH TRACKER"},
            {"id": "KERNEL:SCH-PRIORITY", "seccion": "05.11", "nombre": "KERNEL:SCH PRIORITY"},
            {"id": "KERNEL:GATE", "seccion": "06", "nombre": "KERNEL:GATE"},
            {"id": "KERNEL:GATE-BYPASS", "seccion": "06.1", "nombre": "KERNEL:GATE BYPASS"},
            {"id": "KERNEL:GATE-LOGIC", "seccion": "06.2", "nombre": "KERNEL:GATE LOGIC"},
            {"id": "KERNEL:GATE-REVIEW", "seccion": "06.3", "nombre": "KERNEL:GATE REVIEW"},
            {"id": "KERNEL:GATE-DETERMINISM", "seccion": "06.4", "nombre": "KERNEL:GATE DETERMINISM"},
            {"id": "KERNEL:GATE-BLOCKED", "seccion": "06.5", "nombre": "KERNEL:GATE BLOCKED"},
            {"id": "KERNEL:GATE-REJECTED", "seccion": "06.6", "nombre": "KERNEL:GATE REJECTED"},
            {"id": "KERNEL:GATE-DEDUP-MARK", "seccion": "06.7", "nombre": "KERNEL:GATE DEDUP MARK"},
            {"id": "KERNEL:GATE-LAYERS", "seccion": "06.8", "nombre": "KERNEL:GATE LAYERS"},
            {"id": "KERNEL:GATE-ESCALATION", "seccion": "06.9", "nombre": "KERNEL:GATE ESCALATION"},
            {"id": "KERNEL:GATE-TERMINAL", "seccion": "06.10", "nombre": "KERNEL:GATE TERMINAL"},
            {"id": "KERNEL:GATE-MATRIX-NOTE", "seccion": "06.11", "nombre": "KERNEL:GATE MATRIX NOTE"},
            {"id": "KERNEL:GATE-MUTABILITY", "seccion": "06.12", "nombre": "KERNEL:GATE MUTABILITY"},
            {"id": "KERNEL:GATE-AUDIT-LIVE", "seccion": "06.13", "nombre": "KERNEL:GATE AUDIT LIVE"},
            {"id": "KERNEL:TRIGGERS", "seccion": "07", "nombre": "Contratos de Ejecución del AI Component"},
            {"id": "KERNEL:TRG-FEED", "seccion": "07.1", "nombre": "KERNEL:TRG FEED"},
            {"id": "KERNEL:TRG-VL1", "seccion": "07.2", "nombre": "KERNEL:TRG VL1"},
            {"id": "KERNEL:TRG-QA", "seccion": "07.3", "nombre": "KERNEL:TRG QA"},
            {"id": "KERNEL:TRG-DRYRUN", "seccion": "07.4", "nombre": "KERNEL:TRG DRYRUN"},
            {"id": "KERNEL:TRG-SYNC", "seccion": "07.5", "nombre": "KERNEL:TRG SYNC"},
            {"id": "KERNEL:TRG-TOP3", "seccion": "07.6", "nombre": "KERNEL:TRG TOP3"},
            {"id": "KERNEL:TRG-NEXTACTION", "seccion": "07.7", "nombre": "KERNEL:TRG NEXTACTION"},
            {"id": "KERNEL:TRG-FEEDMIG", "seccion": "07.8", "nombre": "KERNEL:TRG FEEDMIG"},
            {"id": "KERNEL:TRG-STATUS", "seccion": "07.9", "nombre": "KERNEL:TRG STATUS"},
            {"id": "KERNEL:FLOW", "seccion": "08", "nombre": "KERNEL:FLOW"},
            {"id": "KERNEL:FLOW-WRITE", "seccion": "08.2", "nombre": "KERNEL:FLOW WRITE"},
            {"id": "KERNEL:FLOW-CTX-SCOPE", "seccion": "08.3", "nombre": "KERNEL:FLOW CTX SCOPE"},
            {"id": "KERNEL:FLOW-CTX-ROUTE", "seccion": "08.4", "nombre": "KERNEL:FLOW CTX ROUTE"},
            {"id": "KERNEL:CVP", "seccion": "09", "nombre": "KERNEL:CVP"},
            {"id": "KERNEL:CVP-CVA", "seccion": "09.1", "nombre": "KERNEL:CVP CVA"},
            {"id": "KERNEL:CVP-CVB", "seccion": "09.2", "nombre": "KERNEL:CVP CVB"},
            {"id": "KERNEL:CVP-BATCH", "seccion": "09.3", "nombre": "KERNEL:CVP BATCH"},
            {"id": "KERNEL:CANON-UPDATE", "seccion": "10", "nombre": "Actualización del Canon"},
            {"id": "KERNEL:CVR", "seccion": "11", "nombre": "KERNEL:CVR"},
            {"id": "KERNEL:CVR-NOFIT", "seccion": "11.1", "nombre": "KERNEL:CVR NOFIT"},
            {"id": "KERNEL:CVR-NOCLASSB", "seccion": "11.2", "nombre": "KERNEL:CVR NOCLASSB"},
            {"id": "KERNEL:CVR-NODATAQ", "seccion": "11.3", "nombre": "KERNEL:CVR NODATAQ"},
            {"id": "KERNEL:CVR-NOHANDOFF", "seccion": "11.4", "nombre": "KERNEL:CVR NOHANDOFF"},
            {"id": "KERNEL:CVR-NOSYNC", "seccion": "11.5", "nombre": "KERNEL:CVR NOSYNC"},
            {"id": "KERNEL:CVR-GATE-INV", "seccion": "11.6", "nombre": "KERNEL:CVR GATE INV"},
            {"id": "KERNEL:NAMING", "seccion": "12", "nombre": "KERNEL:NAMING"},
            {"id": "KERNEL:NAM-ID-CONTRACT", "seccion": "12.1", "nombre": "KERNEL:NAM ID CONTRACT"},
            {"id": "KERNEL:NAM-ID-MIGRATION", "seccion": "12.2", "nombre": "KERNEL:NAM ID MIGRATION"},
            {"id": "KERNEL:NAM-DOC-CONTRACT", "seccion": "12.3", "nombre": "KERNEL:NAM DOC CONTRACT"},
            {"id": "KERNEL:NAM-OUTPUT", "seccion": "12.4", "nombre": "KERNEL:NAM OUTPUT"},
            {"id": "KERNEL:NAM-ID-GRAMMAR", "seccion": "12.5", "nombre": "KERNEL:NAM ID GRAMMAR"},
            {"id": "KERNEL:LINK", "seccion": "13", "nombre": "KERNEL:LINK"},
            {"id": "KERNEL:LINK-SYSTEM", "seccion": "13.1", "nombre": "KERNEL:LINK SYSTEM"},
            {"id": "KERNEL:LINK-RULE", "seccion": "13.2", "nombre": "KERNEL:LINK RULE"},
            {"id": "KERNEL:OPS", "seccion": "14", "nombre": "KERNEL:OPS"},
            {"id": "KERNEL:OPS-BOOT", "seccion": "14.1", "nombre": "KERNEL:OPS BOOT"},
            {"id": "KERNEL:OPS-HEALTH", "seccion": "14.2", "nombre": "KERNEL:OPS HEALTH"},
            {"id": "KERNEL:OPS-VERSIONS", "seccion": "14.3", "nombre": "KERNEL:OPS VERSIONS"},
            {"id": "KERNEL:OPS-CENSUS", "seccion": "14.4", "nombre": "KERNEL:OPS CENSUS"},
            {"id": "KERNEL:OPS-LEDGER", "seccion": "14.5", "nombre": "KERNEL:OPS LEDGER"},
            {"id": "KERNEL:OPS-IMPACT", "seccion": "14.6", "nombre": "KERNEL:OPS IMPACT"},
            {"id": "KERNEL:OPS-EXTCFG", "seccion": "14.7", "nombre": "KERNEL:OPS EXTCFG"},
            {"id": "KERNEL:OPS-GEMINI", "seccion": "14.8", "nombre": "KERNEL:OPS GEMINI"},
            {"id": "KERNEL:OPS-SANDBOX", "seccion": "14.9", "nombre": "KERNEL:OPS SANDBOX"},
            {"id": "KERNEL:OPS-ANNOUNCE", "seccion": "14.10", "nombre": "KERNEL:OPS ANNOUNCE"},
            {"id": "KERNEL:OPS-GATES", "seccion": "14.11", "nombre": "KERNEL:OPS GATES"},
            {"id": "KERNEL:OPS-SERIAL", "seccion": "14.12", "nombre": "KERNEL:OPS SERIAL"},
            {"id": "KERNEL:EVOLUTION", "seccion": "15", "nombre": "Evolución del Sistema"},
            {"id": "KERNEL:EVO-POLICY", "seccion": "15.1", "nombre": "KERNEL:EVO POLICY"},
            {"id": "KERNEL:EVO-CHANGELOG", "seccion": "15.2", "nombre": "KERNEL:EVO CHANGELOG"},
            {"id": "KERNEL:EXCEPTIONS", "seccion": "16", "nombre": "KERNEL:EXCEPTIONS"},
            {"id": "KERNEL:PURPOSE-001", "seccion": "01.1", "nombre": "Objetivo Principal"},
            {"id": "KERNEL:FAIL-PHILOSOPHY", "seccion": "02", "nombre": "Filosofía de Fallo"},
            {"id": "KERNEL:FAIL-PHILOSOPHY-001", "seccion": "02.1", "nombre": "Fail-Fast vs Fail-Safe"},
            {"id": "KERNEL:FAIL-PHILOSOPHY-002", "seccion": "02.2", "nombre": "Recovery Strategies"},
            {"id": "KERNEL:DOCUMENTATION", "seccion": "03", "nombre": "Documentación y Gobernanza (L0)"},
            {"id": "KERNEL:DOCUMENTATION-001", "seccion": "03.1", "nombre": "Canonical Document ID Contract"},
            {"id": "KERNEL:DOCUMENTATION-002", "seccion": "03.2", "nombre": "Nomenclatura de IDs Canónicos"},
            {"id": "KERNEL:DOCUMENTATION-003", "seccion": "03.3", "nombre": "L0 — VANTAGE Runtime"},
            {"id": "KERNEL:DOCUMENTATION-004", "seccion": "03.4", "nombre": "Kernel vs Manual"},
            {"id": "KERNEL:DOCUMENTATION-005", "seccion": "03.5", "nombre": "Convención de Anuncio de Skills"},
            {"id": "KERNEL:DOCUMENTATION-006", "seccion": "03.6", "nombre": "Health Check"},
            {"id": "KERNEL:DOCUMENTATION-007", "seccion": "03.7", "nombre": "Verificación de Versión"},
            {"id": "KERNEL:DOCUMENTATION-008", "seccion": "03.8", "nombre": "ID Census"},
            {"id": "KERNEL:DOCUMENTATION-009", "seccion": "03.9", "nombre": "Session Ledger"},
            {"id": "KERNEL:DOCUMENTATION-010", "seccion": "03.10", "nombre": "Documentación Transversal"},
            {"id": "KERNEL:DOCUMENTATION-011", "seccion": "03.11", "nombre": "Impact Assessment Contract"},
            {"id": "KERNEL:DOCUMENTATION-012", "seccion": "03.12", "nombre": "External Configuration Contract"},
            {"id": "KERNEL:DOCUMENTATION-013", "seccion": "03.13", "nombre": "Sistema de Cross-Reference Hyperlinks"},
            {"id": "KERNEL:DOCUMENTATION-014", "seccion": "03.14", "nombre": "Change Log"},
            {"id": "KERNEL:DOCUMENTATION-015", "seccion": "03.15", "nombre": "Cross-Reference Hyperlinks"},
            {"id": "KERNEL:DOCUMENTATION-016", "seccion": "03.16", "nombre": "Notebook Gemini"},
            {"id": "KERNEL:DOCUMENTATION-017", "seccion": "03.17", "nombre": "Sandbox"},
            {"id": "KERNEL:DOC-CONTRACT", "seccion": "03.18", "nombre": "Contrato de Prefijos Documentales del Lazy Loader"},
            {"id": "KERNEL:HANDOFF-SERIAL", "seccion": "03.19", "nombre": "Contrato de Serial Global de Handoff"},
            {"id": "KERNEL:ARCHITECTURE-L1", "seccion": "04.1", "nombre": "L1 — Active Search"},
            {"id": "KERNEL:ARCHITECTURE-L2", "seccion": "04.2", "nombre": "L2 — Strategic Search"},
            {"id": "KERNEL:ARCHITECTURE-L3", "seccion": "04.3", "nombre": "L3 — Passive Intake"},
            {"id": "KERNEL:ARCHITECTURE-L4", "lookup_ids": ["KERNEL:ARCHITECTURE-004", "KERNEL:ARCHITECTURE-L4"], "seccion": "04.4", "nombre": "L4 — Version Control & Infrastructure"},
            {"id": "KERNEL:OWNERSHIP", "seccion": "05", "nombre": "División de Responsabilidades AI/Python"},
            {"id": "KERNEL:OWNERSHIP-001", "seccion": "05.1", "nombre": "AI Component"},
            {"id": "KERNEL:OWNERSHIP-002", "seccion": "05.2", "nombre": "Python Component"},
            {"id": "KERNEL:DASHBOARD-CHECKLIST-ARCH", "seccion": "06", "nombre": "Dashboard Checklist Architecture"},
            {"id": "KERNEL:SCHEMA-001", "seccion": "07.1", "nombre": "Schema — Class A Fields"},
            {"id": "KERNEL:SCHEMA-002", "seccion": "07.2", "nombre": "Schema — Class B Fields"},
            {"id": "KERNEL:SCHEMA-003", "seccion": "07.3", "nombre": "Schema — Field Validation Rules"},
            {"id": "KERNEL:SCHEMA-004", "seccion": "07.4", "nombre": "Schema — Class A vs Class B"},
            {"id": "KERNEL:SCHEMA-005", "seccion": "07.5", "nombre": "Schema — Field Types"},
            {"id": "KERNEL:SCHEMA-006", "seccion": "07.6", "nombre": "Schema — Validation Rules"},
            {"id": "KERNEL:SCHEMA-007", "seccion": "07.7", "nombre": "Schema — Mutability Rules"},
            {"id": "KERNEL:SCHEMA-008", "seccion": "07.8", "nombre": "Valores Operativos — Next_Action (Tracker de Vacantes)"},
            {"id": "KERNEL:SCHEMA-009", "seccion": "07.9", "nombre": "Schema — Subsección 009"},
            {"id": "KERNEL:TRACKER-SCHEMA", "seccion": "08", "nombre": "Schema del Tracker de Vacantes"},
            {"id": "KERNEL:TRACKER-SCHEMA-001", "seccion": "08.1", "nombre": "Tracker Schema — Campos Principales"},
            {"id": "KERNEL:TRACKER-SCHEMA-002", "seccion": "08.2", "nombre": "Tracker Schema — Campos Derivados"},
            {"id": "KERNEL:GATE-DECISION", "seccion": "09", "nombre": "Lógica de Gate Decision"},
            {"id": "KERNEL:GATE-DECISION-001", "seccion": "09.1", "nombre": "Gate Decision — Overview"},
            {"id": "KERNEL:GATE-DECISION-002", "seccion": "09.2", "nombre": "Lógica Estándar"},
            {"id": "KERNEL:GATE-DECISION-003", "seccion": "09.3", "nombre": "Resolución de REVIEW_NEEDED"},
            {"id": "KERNEL:GATE-DECISION-004", "seccion": "09.4", "nombre": "Por Qué los Gates Son Deterministas"},
            {"id": "KERNEL:GATE-DECISION-005", "seccion": "09.5", "nombre": "Flujo de Recuperación BLOCKED"},
            {"id": "KERNEL:GATE-DECISION-006", "seccion": "09.6", "nombre": "REJECTED (Post-Aplicación)"},
            {"id": "KERNEL:GATE-DECISION-007", "seccion": "09.7", "nombre": "Ejecución Automática de Archivado"},
            {"id": "KERNEL:GATE-DECISION-008", "seccion": "09.8", "nombre": "Capas de Evaluación de Gate: Técnica vs. Negocio"},
            {"id": "KERNEL:GATE-DECISION-009", "seccion": "09.9", "nombre": "Escalamiento de Pendientes a Tickets"},
            {"id": "KERNEL:GATE-DECISION-010", "seccion": "09.10", "nombre": "Gate Decision — Technical Review"},
            {"id": "KERNEL:GATE-DECISION-011", "seccion": "09.11", "nombre": "Gate Decision — Business Review"},
            {"id": "KERNEL:DEDUP-LAYER-UPGRADE", "seccion": "09.12", "nombre": "Dedup Layer Upgrade"},
            {"id": "KERNEL:GATE-DECISION-013", "seccion": "09.13", "nombre": "Gate Decision — Subsección 013"},
            {"id": "KERNEL:CV-GOLDEN-RULES", "seccion": "10", "nombre": "Golden Rules — Límites de Ejecución"},
            {"id": "KERNEL:CV-GOLDEN-RULES-001", "seccion": "10.1", "nombre": "Regla de Oro #1"},
            {"id": "KERNEL:CV-GOLDEN-RULES-002", "seccion": "10.2", "nombre": "Regla de Oro #2"},
            {"id": "KERNEL:CV-GOLDEN-RULES-003", "seccion": "10.3", "nombre": "Regla de Oro #3"},
            {"id": "KERNEL:CV-GOLDEN-RULES-004", "seccion": "10.4", "nombre": "Regla de Oro #4"},
            {"id": "KERNEL:CV-GOLDEN-RULES-005", "seccion": "10.5", "nombre": "Regla de Oro #5"},
            {"id": "KERNEL:CV-GOLDEN-RULES-006", "seccion": "10.6", "nombre": "Regla de Oro #6 — Invarianza de la Decisión de Gate"},
            {"id": "KERNEL:TRIGGER-001", "seccion": "11.1", "nombre": "Trigger — Discovery Request"},
            {"id": "KERNEL:TRIGGER-002", "seccion": "11.2", "nombre": "Trigger — CV Optimization"},
            {"id": "KERNEL:TRIGGER-003", "seccion": "11.3", "nombre": "Trigger — Recovery Request"},
            {"id": "KERNEL:TRIGGER-004", "seccion": "11.4", "nombre": "Trigger — Documentation Update"},
            {"id": "KERNEL:TRIGGER-005", "seccion": "11.5", "nombre": "Trigger — Schema Validation"},
            {"id": "KERNEL:TRIGGER-006", "seccion": "11.6", "nombre": "Trigger — Gate Decision"},
            {"id": "KERNEL:TRIGGER-007", "seccion": "11.7", "nombre": "Trigger — Archiving"},
            {"id": "KERNEL:TRIGGER-008", "seccion": "11.8", "nombre": "Trigger — Health Check"},
            {"id": "KERNEL:TRIGGER-009", "seccion": "11.9", "nombre": "Trigger — Version Check"},
            {"id": "KERNEL:CV-PIPELINE", "seccion": "12", "nombre": "Pipeline de CV"},
            {"id": "KERNEL:CV-PIPELINE-003", "seccion": "12.3", "nombre": "CV-C"},
            {"id": "KERNEL:CV-PIPELINE-001", "seccion": "12.1", "nombre": "CV-A"},
            {"id": "KERNEL:CV-PIPELINE-002", "seccion": "12.2", "nombre": "CV-B"},
            {"id": "KERNEL:NAMING-CONVENTION", "seccion": "14", "nombre": "Convención de Nombres"},
            {"id": "KERNEL:CONTEXT-INFRASTRUCTURE", "seccion": "15", "nombre": "Context Infrastructure"},
            {"id": "KERNEL:CONTEXT-INFRASTRUCTURE-001", "seccion": "15.1", "nombre": "Context Infrastructure — Data Sources"},
            {"id": "KERNEL:CONTEXT-INFRASTRUCTURE-002", "seccion": "15.2", "nombre": "Context Infrastructure — Integration Points"},
            {"id": "KERNEL:DATA-FLOW", "seccion": "16", "nombre": "Flujo de Datos"},
            {"id": "KERNEL:DATA-FLOW-001", "seccion": "16.1", "nombre": "Flujo de Datos — Subsección 001"},
        ],
    },
    {
        "name": "MANUAL",
        "rows": [
            {"id": "MANUAL:OBJECTIVE", "seccion": "01", "nombre": "Objetivo"},
            {"id": "MANUAL:HOW-IT-WORKS", "seccion": "02", "nombre": "¿Cómo funciona?"},
            {"id": "MANUAL:FAILURE-PHILOSOPHY", "seccion": "03", "nombre": "Filosofía de Fallo para Operadores"},
            {"id": "MANUAL:SETUP", "seccion": "04", "nombre": "Setup"},
            {"id": "MANUAL:COLD-START", "seccion": "05", "nombre": "Arranque Frío"},
            {"id": "MANUAL:SESSION-CYCLE", "seccion": "06", "nombre": "Ciclo de Sesión"},
            {"id": "MANUAL:CHECKLIST", "seccion": "07", "nombre": "El Checklist"},
            {"id": "MANUAL:WEEKLY-FLOW", "seccion": "08", "nombre": "Flujo Semanal de Operación"},
            {"id": "MANUAL:WEEKLY-FLOW-001", "seccion": "8.1", "nombre": "Lunes — Búsqueda Activa"},
            {"id": "MANUAL:WEEKLY-FLOW-002", "seccion": "8.2", "nombre": "Dashboard — recuperación antes de CV Optimization"},
            {"id": "MANUAL:WEEKLY-FLOW-003", "seccion": "8.3", "nombre": "Miércoles — Figma"},
            {"id": "MANUAL:WEEKLY-FLOW-004", "seccion": "08.4", "nombre": "Jueves"},
            {"id": "MANUAL:WEEKLY-FLOW-005", "seccion": "08.5", "nombre": "Viernes"},
            {"id": "MANUAL:RUNTIME", "seccion": "09", "nombre": "VANTAGE Runtime (Consulta Operativa)"},
            {"id": "MANUAL:RUNTIME-001", "seccion": "9.1", "nombre": "¿Qué es el Runtime?"},
            {"id": "MANUAL:RUNTIME-002", "seccion": "9.2", "nombre": "Comandos Principales"},
            {"id": "MANUAL:RUNTIME-003", "seccion": "9.3", "nombre": "Cuándo Correr Sync"},
            {"id": "MANUAL:RUNTIME-004", "seccion": "9.4", "nombre": "Runtime Build"},
            {"id": "MANUAL:RUNTIME-005", "seccion": "9.5", "nombre": "Notebook Gemini — Triaje de Consultas Documentales"},
            {"id": "MANUAL:DATA-MANAGEMENT", "seccion": "10", "nombre": "Gestión de Datos"},
            {"id": "MANUAL:DATA-MANAGEMENT-001", "seccion": "10.1", "nombre": "Gestión de Datos — Subsección 001"},
            {"id": "MANUAL:MONITOR", "lookup_ids": ["MANUAL:HEALTHCHECK", "MANUAL:MONITOR"], "seccion": "11", "nombre": "Health Check"},
            {"id": "MANUAL:TROUBLESHOOTING", "seccion": "12", "nombre": "Troubleshooting"},
            {"id": "MANUAL:FIGMA-SYNC-DIAGNOSTIC", "seccion": "12.1", "nombre": "Matriz de Errores — Figma Sync"},
            {"id": "MANUAL:PROMPTS-WRAPPERS", "seccion": "13", "nombre": "Prompts & Wrappers"},
            {"id": "MANUAL:LAZY-LOAD", "seccion": "14", "nombre": "Lazy Load"},
            {"id": "MANUAL:PATCH-QUALITY", "seccion": "15", "nombre": "Criterio de Calidad para Parches Documentales"},
            {"id": "MANUAL:GOLDEN-RULES", "seccion": "16", "nombre": "Reglas de Oro para Operadores"},
            {"id": "MANUAL:SLA", "seccion": "17", "nombre": "SLA de Latencia Post-Ingesta"},
            {"id": "MANUAL:CV-GOLDEN-RULES-INDEX", "seccion": "18", "nombre": "Reglas de Oro CV — Referencia Operativa"},
            {"id": "MANUAL:POSITIONING-CRITERIA", "seccion": "19", "nombre": "Positioning Modes (N1–N4) — Criterio de Selección"},
            {"id": "MANUAL:GOLDEN-SKELETON-REF", "seccion": "20", "nombre": "Figma Sync & Golden Skeleton"},
            {"id": "MANUAL:FIGMA-SYNC-001", "seccion": "20.1", "nombre": "Arquitectura del Ecosistema"},
            {"id": "MANUAL:FIGMA-SYNC-002", "seccion": "20.2", "nombre": "Contrato de Bloque"},
            {"id": "MANUAL:FIGMA-SYNC-003", "seccion": "20.3", "nombre": "Flujo de Inyección"},
            {"id": "MANUAL:FIGMA-SYNC-004", "seccion": "20.4", "nombre": "Sanitización de Contenido"},
            {"id": "MANUAL:FIGMA-SYNC-005", "seccion": "20.5", "nombre": "Regla de Reemplazo Total"},
            {"id": "MANUAL:SCHEMA-FIELD-REF", "seccion": "21", "nombre": "Schema Class A/B — Referencia de Campos"},
            {"id": "MANUAL:SCRIPT-GLOSSARY", "seccion": "22", "nombre": "Script Glossary"},
            {"id": "MANUAL:SCRIPT-GLOSSARY-CV-PREP", "seccion": "22.2", "nombre": "CV Pipeline — Preparación Mecánica (Miércoles)"},
            {"id": "MANUAL:SCRIPT-GLOSSARY-L1", "seccion": "22.1", "nombre": "Script Glossary — L1"},
            {"id": "MANUAL:SCRIPT-GLOSSARY-L1-MODULES", "seccion": "22.1a", "nombre": "Script Glossary — L1 Modules"},
            {"id": "MANUAL:SCRIPT-GLOSSARY-L1-TOOLS", "seccion": "22.1b", "nombre": "Script Glossary — L1 Tools"},
            {"id": "MANUAL:SCRIPT-GLOSSARY-L4", "seccion": "22.3", "nombre": "Script Glossary — L4"},
            {"id": "MANUAL:SCRIPT-GLOSSARY-DASHBOARD", "seccion": "22.4", "nombre": "Script Glossary — Dashboard"},
            {"id": "MANUAL:SCRIPT-GLOSSARY-DASHBOARD-MODULES", "seccion": "22.4a", "nombre": "Script Glossary — Dashboard Modules"},
            {"id": "MANUAL:SCRIPT-GLOSSARY-RAYCAST", "seccion": "22.5", "nombre": "Script Glossary — Raycast"},
            {"id": "MANUAL:SCRIPT-GLOSSARY-XREF", "seccion": "22.6", "nombre": "Script Glossary — Cross-Reference"},
            {"id": "MANUAL:SKILL-GLOSSARY", "seccion": "23", "nombre": "Glosario de Skills — Referencia Operativa en Humano"},
            {"id": "MANUAL:SKILL-GLOSSARY-CORE", "seccion": "23.1", "nombre": "Pipeline CV y Ciclo de Sesión"},
            {"id": "MANUAL:SKILL-GLOSSARY-HOUSEKEEPING", "seccion": "23.2", "nombre": "Sincronización y Mantenimiento Documental"},
            {"id": "MANUAL:SKILL-GLOSSARY-AUDIT", "seccion": "23.3", "nombre": "Auditoría y Continuidad"},
            {"id": "MANUAL:SKILL-GLOSSARY-STYLE", "seccion": "23.4", "nombre": "Estilos de Escritura y Generación"},
            {"id": "MANUAL:SKILL-GLOSSARY-XREF", "seccion": "23.5", "nombre": "Gaps Abiertos"},
        ],
    },
    {
        "name": "CAREER CANON",
        "rows": [
            {"id": "CANON:PROFILE", "seccion": "01", "nombre": "Professional Profile Canon"},
            {"id": "CANON:PROFILE-001", "seccion": "01.1", "nombre": "Professional Profile — ES"},
            {"id": "CANON:PROFILE-002", "seccion": "01.2", "nombre": "Professional Profile — EN"},
            {"id": "CANON:SKILLS", "seccion": "02", "nombre": "Skills Canon"},
            {"id": "CANON:EXPERIENCE", "seccion": "03", "nombre": "Experience Records"},
            {"id": "CANON:EXPERIENCE-001", "seccion": "03.1", "nombre": "C01 L'Oréal Luxe"},
            {"id": "CANON:EXPERIENCE-002", "seccion": "03.2", "nombre": "C02 Bisonte Experiential"},
            {"id": "CANON:EXPERIENCE-003", "seccion": "03.3", "nombre": "C03 Levi Strauss (Dockers)"},
            {"id": "CANON:EXPERIENCE-004", "seccion": "03.4", "nombre": "C04 Aéropostale"},
            {"id": "CANON:EXPERIENCE-005", "seccion": "03.5", "nombre": "C05 El Palacio de Hierro (ALDO)"},
            {"id": "CANON:CAREER-TIMELINE", "seccion": "04", "nombre": "Career Timeline (reintegrada v9.11.0)"},
            {"id": "CANON:ACHIEVEMENTS", "seccion": "05", "nombre": "Achievement Library"},
            {"id": "CANON:KPIS", "seccion": "06", "nombre": "Core KPIs (reintegrada v9.11.0)"},
            {"id": "CANON:KPI-001", "seccion": "06.1", "nombre": "KPI01 — Traffic +43% (Aéropostale)"},
            {"id": "CANON:KPI-002", "seccion": "06.2", "nombre": "KPI02 — Conversion +18% (Aéropostale)"},
            {"id": "CANON:KPI-003", "seccion": "06.3", "nombre": "KPI03 — Campaign Cost Reduction -74% (Levi's/Dockers)"},
            {"id": "CANON:KPI-004", "seccion": "06.4", "nombre": "KPI04 — Floorset Time Reduction -33% (Levi's/Dockers)"},
            {"id": "CANON:KPI-005", "seccion": "06.5", "nombre": "KPI05 — POP Coverage 100% (COVID-19 LATAM)"},
            {"id": "CANON:KPI-006", "seccion": "06.6", "nombre": "KPI06 — Rebranding Coverage 100% (Levi's/Dockers)"},
            {"id": "CANON:KPI-007", "seccion": "06.7", "nombre": "KPI07 — Adidas Punch List Count (17)"},
            {"id": "CANON:KPI-008", "seccion": "06.8", "nombre": "KPI08 — Years Experience (10+ Canonical)"},
            {"id": "CANON:FACTS", "seccion": "07", "nombre": "Canonical Facts"},
            {"id": "CANON:FACT-001", "seccion": "07.1", "nombre": "Fact — ALDO Certification Year"},
            {"id": "CANON:FACT-002", "seccion": "07.2", "nombre": "Fact — ALDO Employment Period"},
            {"id": "CANON:FACT-003", "seccion": "07.3", "nombre": "Fact — Adidas Punch List Count"},
            {"id": "CANON:FACT-004", "seccion": "07.4", "nombre": "Fact — Adidas Punch List Severity"},
            {"id": "CANON:FACT-005", "seccion": "07.5", "nombre": "Fact — Levi's Coverage"},
            {"id": "CANON:FACT-006", "seccion": "07.6", "nombre": "Fact — Aéropostale Team Size"},
            {"id": "CANON:FACT-007", "seccion": "07.7", "nombre": "Fact — Aéropostale Network Size"},
            {"id": "CANON:FACT-008", "seccion": "07.8", "nombre": "Fact — L'Oréal Brands"},
            {"id": "CANON:UF-001", "seccion": "07.9", "nombre": "Unique Factor — L'Oréal End Date"},
            {"id": "CANON:UF-002", "seccion": "07.10", "nombre": "Unique Factor — Canonical Email"},
            {"id": "CANON:UF-003", "seccion": "07.11", "nombre": "Unique Factor — Certifications Canon"},
            {"id": "CANON:UF-004", "seccion": "07.12", "nombre": "Unique Factor — Contact Block"},
            {"id": "CANON:UF-005", "seccion": "07.13", "nombre": "Unique Factor — LinkedIn URL"},
            {"id": "CANON:UF-006", "seccion": "07.14", "nombre": "Unique Factor — Portfolio URLs"},
            {"id": "CANON:EDUCATION", "seccion": "08", "nombre": "Education (reintegrada v9.11.0)"},
            {"id": "CANON:EDUCATION-001", "seccion": "08.1", "nombre": "ED01 — Licenciatura en Artes Visuales"},
            {"id": "CANON:EDUCATION-002", "seccion": "08.2", "nombre": "ED02 — Diplomado en Museos y Exposiciones"},
            {"id": "CANON:CERTIFICATIONS", "seccion": "09", "nombre": "Certifications (reintegrada v9.11.0)"},
            {"id": "CANON:CERTIFICATION-001", "seccion": "09.1", "nombre": "CERT01 — Store Operations Leaders Orientation"},
            {"id": "CANON:CERTIFICATION-002", "seccion": "09.2", "nombre": "CERT02 — AutoCAD & SketchUp Essentials"},
            {"id": "CANON:MAJOR-PROJECTS", "seccion": "10", "nombre": "Major Projects (reintegrada v9.11.0)"},
            {"id": "CANON:MAJOR-PROJECT-001", "seccion": "10.1", "nombre": "P01 — Adidas Brand Center Madero"},
            {"id": "CANON:MAJOR-PROJECT-002", "seccion": "10.2", "nombre": "P02 — Dockers LATAM Rebranding"},
            {"id": "CANON:MAJOR-PROJECT-003", "seccion": "10.3", "nombre": "P03 — AeroFest Frontón México"},
            {"id": "CANON:POSITIONING", "seccion": "11", "nombre": "Positioning Modes N1–N4"},
            {"id": "CANON:POSITIONING-001", "seccion": "11.1", "nombre": "Positioning N1 — Luxury Brand Execution"},
            {"id": "CANON:POSITIONING-002", "seccion": "11.2", "nombre": "Positioning N2 — Store Design & Flagship Execution"},
            {"id": "CANON:POSITIONING-003", "seccion": "11.3", "nombre": "Positioning N3 — Regional Brand Execution & Rollout"},
            {"id": "CANON:POSITIONING-004", "seccion": "11.4", "nombre": "Positioning N4 — Commercial VM & Field Leadership"},
            {"id": "CANON:POSITIONING-005", "seccion": "11.5", "nombre": "Mitigación de Riesgos"},
            {"id": "CANON:OUTPUT-CONTRACT", "seccion": "12", "nombre": "Output Contract Framework"},
            {"id": "CANON:OUTPUT-CONTRACT-001", "seccion": "12.1", "nombre": "Output Contract — Golden Skeleton"},
            {"id": "CANON:OUTPUT-CONTRACT-002", "seccion": "12.2", "nombre": "Output Contract — Figma Tags / Registry SSOT"},
            {"id": "CANON:OUTPUT-CONTRACT-003", "seccion": "12.3", "nombre": "Output Contract — Tag Registry / Formato de Entrega"},
            {"id": "CANON:OUTPUT-CONTRACT-004", "seccion": "12.4", "nombre": "Output Contract — Positioning Modes (Aplicación)"},
            {"id": "CANON:OUTPUT-CONTRACT-005", "seccion": "12.5", "nombre": "Output Contract — Positioning Modes (Aplicación en Output)"},
            {"id": "CANON:DERIVED-OUTPUTS-ARCHIVE", "seccion": "13", "nombre": "Derived Outputs Archive (reintegrada v9.11.0)"},
        ],
    },
    {
        "name": "NAVIGATION BRIEF",
        "rows": [
            {"id": "BRIEF:PURPOSE-SCOPE", "lookup_ids": ["BRIEF:PURPOSE-SCOPE", "BRIEF:SCOPE", "BRIEF:001"], "seccion": "01", "nombre": "Propósito y Alcance"},
            {"id": "BRIEF:PURPOSE-SCOPE-001", "seccion": "01.1", "nombre": "Propósito"},
            {"id": "BRIEF:PURPOSE-SCOPE-002", "seccion": "01.2", "nombre": "Alcance"},
            {"id": "BRIEF:PURPOSE-SCOPE-003", "seccion": "01.3", "nombre": "Fuera de Alcance"},
            {"id": "BRIEF:AUTHORITY-MATRIX", "lookup_ids": ["BRIEF:AUTHORITY-MATRIX", "BRIEF:002"], "seccion": "02", "nombre": "Matriz de Autoridad Documental"},
            {"id": "BRIEF:ECOSYSTEM", "lookup_ids": ["BRIEF:ECOSYSTEM", "BRIEF:003"], "seccion": "03", "nombre": "Ecosistema Documental"},
            {"id": "BRIEF:NAV-CONTRACTS", "lookup_ids": ["BRIEF:NAV-CONTRACTS", "BRIEF:004"], "seccion": "04", "nombre": "Contratos de navegación"},
            {"id": "BRIEF:CONSULTATION-001", "seccion": "04.1", "nombre": "Consulta Arquitectónica"},
            {"id": "BRIEF:CONSULTATION-002", "seccion": "04.2", "nombre": "Consulta Operativa"},
            {"id": "BRIEF:CONSULTATION-003", "seccion": "04.3", "nombre": "Consulta Profesional"},
            {"id": "BRIEF:CONSULTATION-004", "seccion": "04.4", "nombre": "Consulta Documental"},
            {"id": "BRIEF:CONSULTATION-005", "seccion": "04.5", "nombre": "Consulta de IDs"},
            {"id": "BRIEF:CONSULTATION-006", "seccion": "04.6", "nombre": "Consulta Histórica"},
            {"id": "BRIEF:DOMAIN-ARCHITECTURE", "lookup_ids": ["BRIEF:DOMAIN-ARCHITECTURE", "BRIEF:005"], "seccion": "05", "nombre": "Dominios"},
            {"id": "BRIEF:HOUSEKEEPING-001", "seccion": "05.1", "nombre": "Housekeeping"},
            {"id": "BRIEF:CORE-ASSETS-001", "seccion": "05.2", "nombre": "Core Assets"},
            {"id": "BRIEF:DISCOVERY-001", "seccion": "05.3", "nombre": "Discovery"},
            {"id": "BRIEF:GATE-LOGIC-001", "seccion": "05.4", "nombre": "Gate Logic"},
            {"id": "BRIEF:CV-PIPELINE-001", "seccion": "05.5", "nombre": "CV Pipeline"},
            {"id": "BRIEF:VERIFICATION-DEPTH", "lookup_ids": ["BRIEF:VERIFICATION-DEPTH", "BRIEF:006"], "seccion": "06", "nombre": "Contratos de verificación"},
            {"id": "BRIEF:CROSS-DEPENDENCIES", "lookup_ids": ["BRIEF:CROSS-DEPENDENCIES", "BRIEF:007"], "seccion": "07", "nombre": "Dependencias entre documentos"},
            {"id": "BRIEF:CROSS-DEPENDENCIES-001", "seccion": "07.1", "nombre": "Impact Assessment Contract"},
            {"id": "BRIEF:CROSS-DEPENDENCIES-002", "seccion": "07.2", "nombre": "Mandatory Change Reporting"},
            {"id": "BRIEF:CROSS-DEPENDENCIES-003", "seccion": "07.3", "nombre": "Closure Gate"},
            {"id": "BRIEF:MAINTENANCE-CONTRACT", "lookup_ids": ["BRIEF:MAINTENANCE-CONTRACT", "BRIEF:008"], "seccion": "08", "nombre": "Contrato de Mantenimiento"},
            {"id": "BRIEF:AUTHORITY-001", "seccion": "08.1", "nombre": "Autoridad"},
            {"id": "BRIEF:DECISION-TREE", "lookup_ids": ["BRIEF:DECISION-TREE", "BRIEF:009"], "seccion": "09", "nombre": "Árbol de Decisiones"},
            {"id": "BRIEF:NAV-PRINCIPLES", "lookup_ids": ["BRIEF:NAV-PRINCIPLES", "BRIEF:010"], "seccion": "10", "nombre": "Principios de Navegación"},
            {"id": "BRIEF:EXPECTED-OUTCOME", "lookup_ids": ["BRIEF:EXPECTED-OUTCOME", "BRIEF:011"], "seccion": "11", "nombre": "Resultado Esperado"},
        ],
    },
    {
        "name": "SYSTEM PROMPT",
        "rows": [
            {"id": "SP:BOOTLOADER", "seccion": "01", "nombre": "Operating Specification — Bootstrap de Sesión"},
            {"id": "SP:BOOTLOADER-001", "seccion": "01.1", "nombre": "Consumo de Skills por Familia de Agente"},
            {"id": "SP:BOOTLOADER-002", "seccion": "01.2", "nombre": "Bootstrap de Sesión — Subsección 002"},
            {"id": "SP:SKILL-VERSION-PIN", "seccion": "01.3", "nombre": "Skill Version Pin"},
            {"id": "SP:BOOTLOADER-004", "seccion": "01.4", "nombre": "Agente Principal y Gatekeeper del Charter"},
            {"id": "SP:SYNC-RULE", "seccion": "02", "nombre": "Sincronización Inicial y Verificación de Versión"},
            {"id": "SP:DIGITAL-ID-CARD", "lookup_ids": ["SP:DIGITAL-ID-CARD-001", "SP:DIGITAL-ID-CARD"], "seccion": "03", "nombre": "Cédula Digital — rutas de operación y UUIDs"},
            {"id": "SP:CONTEXT-INFRASTRUCTURE", "seccion": "04", "nombre": "Referencia — Context Infrastructure (KERNEL:CONTEXT-INFRASTRUCTURE)"},
            {"id": "SP:DATA-FLOW", "seccion": "05", "nombre": "Referencia — Consultar en Technical Kernel (KERNEL:DATA-FLOW)"},
            {"id": "SP:TRIGGERS", "seccion": "06", "nombre": "Triggers operativos de VANTAGE"},
            {"id": "SP:CV-GOLDEN-RULES-REF", "seccion": "07", "nombre": "Referencia — Consultar en Technical Kernel (KERNEL:CV-GOLDEN-RULES)"},
            {"id": "SP:SCHEMA", "seccion": "08", "nombre": "Schema — Trackers (Class A/B)"},
            {"id": "SP:MCP-ROUTING-NOTES", "seccion": "09", "nombre": "Notas Operativas de Ruteo MCP/Terminal (ex duplicado SP:CONSISTENCY)"},
            {"id": "SP:CONSISTENCY", "seccion": "10", "nombre": "Regla de Consistencia Documental"},
            {"id": "SP:CONSISTENCY-002", "seccion": "10.1", "nombre": "Triaje vía Notebook Gemini"},
            {"id": "SP:VERSION-CHECK-TOOL", "seccion": "11", "nombre": "Herramienta de Verificación de Versión de Bajo Costo"},
        ],
    },
    {
        "name": "ALIASES",
        "rows": [
            {"id": "ALIASES:SESSION-CYCLE", "seccion": "01", "nombre": "Session Cycle"},
            {"id": "ALIASES:L0-RUNTIME", "seccion": "02", "nombre": "L0 · VANTAGE Runtime"},
            {"id": "ALIASES:L1L2-DISCOVERY", "seccion": "03", "nombre": "L1/L2 · Discovery (Lunes)"},
            {"id": "ALIASES:L3-PASSIVE-INTAKE", "seccion": "04", "nombre": "L3 · Passive Intake"},
            {"id": "ALIASES:L4-VERSION-CONTROL", "seccion": "05", "nombre": "L4 · Version Control & Documentación"},
            {"id": "ALIASES:DASHBOARD", "seccion": "06", "nombre": "Dashboard (Martes — Recuperación)"},
            {"id": "ALIASES:CV-PIPELINE", "seccion": "07", "nombre": "CV Pipeline (Miércoles)"},
            {"id": "ALIASES:DEDUP", "seccion": "08", "nombre": "Dedup & Oportunidades"},
        ],
    },
]

# NOTA (A7 cerrado): "Change Log" y "Changelog Archivo" quedan fuera del Census
# por diseño (no se indexan en DOCUMENTS ni participan como prefijos en
# VALID_PREFIXES). Las filas CANON: viven en su propia sección "CAREER CANON".

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


SECTION_HEADING_PREFIX_RE = re.compile(r"^[\w.]+\s*(?:[—-]\s*)?")
SECTION_HEADING_CAPTURE_RE = re.compile(r"^([\w.]+)\s*(?:[—-]\s*)?")
LEADING_NUMBER_SECTION_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+")


def extract_live_section(plain: str) -> str | None:
    stripped = plain.strip("` \n")
    m = SECTION_HEADING_CAPTURE_RE.match(stripped)
    if m:
        return f"{m.group(1)}"
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
    is_table_row = btype == "table_row"
    return (
        (stripped == id_str and not is_table_row)
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

    if btype in text_types:
        rich_text = block[btype].get("rich_text", [])
        plain = "".join(s.get("plain_text", "") for s in rich_text).strip()
        for id_str in extract_ids_from_rich_text(rich_text):
            is_def = is_definition_block(plain, id_str, btype)
            seccion = extract_live_section(plain) if is_def else None

            found.append((id_str, is_def, seccion, plain))

    elif btype == "code":
        rich_text = block["code"].get("rich_text", [])
        plain = "".join(s.get("plain_text", "") for s in rich_text).strip()
        for line in plain.splitlines():
            for id_str in extract_ids_from_rich_text([{"plain_text": line}]):
                is_def = line.strip().strip("`") == id_str
                found.append((id_str, is_def, None, line.strip()))

    elif btype == "table_row":
        cells = block["table_row"].get("cells", [])
        for cell in cells:
            cell_plain = "".join(s.get("plain_text", "") for s in cell).strip()
            for id_str in extract_ids_from_rich_text(cell):
                is_def = cell_plain.strip("` \n") == id_str or f"ID: {id_str}" in cell_plain
                found.append((id_str, is_def, None, cell_plain))

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

            for id_str, is_def, seccion, plain in extract_ids_from_block(block):
                link_index.setdefault(id_str, []).append({
                    "doc":     doc_name,
                    "link":    link,
                    "is_def":  is_def,
                    "seccion": seccion,
                    "plain":   plain,
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

def known_ids_from_spec(spec: list | None = None) -> set:
    known = set()
    for section in (spec if spec is not None else CENSUS_SPEC):
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


def infer_section_from_id(id_str: str) -> tuple:
    prefix = id_str.split(":")[0] if ":" in id_str else ""
    section_map = {
        "KERNEL": "KERNEL",
        "MANUAL": "MANUAL",
        "CANON": "CAREER CANON",
        "CAREER_CANON": "CAREER CANON",
        "SP": "SYSTEM PROMPT",
        "ALIASES": "ALIASES",
        "BRIEF": "NAVIGATION BRIEF",
        "CHARTER": "PROJECT CHARTER",
    }
    section_name = section_map.get(prefix, "UNKNOWN")
    seccion = ""
    parts = id_str.split(":")
    body = parts[1] if len(parts) > 1 else id_str
    if "-" in body:
        subparts = body.split("-")
        if subparts[-1].isdigit():
            seccion = subparts[-1]
            nombre = f"Subsección {seccion} de {id_str}"
        else:
            nombre = id_str.replace("-", " ")
    else:
        nombre = id_str
    return section_name, seccion, nombre


def _spec_from_source(content: str) -> list | None:
    """Parsea el CENSUS_SPEC del código fuente (por AST, sin ejecutarlo)."""
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"✗ El archivo no es Python válido: {e}")
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "CENSUS_SPEC" for t in node.targets):
            try:
                return ast.literal_eval(node.value)
            except Exception as e:
                print(f"✗ CENSUS_SPEC no es un literal evaluable: {e}")
                return None
    return None


def load_spec_from_file(path: Path) -> list | None:
    """Carga el CENSUS_SPEC desde disco (para reflejar un auto-fix recién aplicado)."""
    try:
        return _spec_from_source(Path(path).read_text(encoding="utf-8"))
    except OSError as e:
        print(f"✗ No se pudo leer {path}: {e}")
        return None


def _find_rows_bounds(content: str, section_name: str) -> tuple[int, int] | None:
    """Devuelve (inicio, fin) del literal de la lista 'rows' de una sección.

    Balancea corchetes ignorando los que aparecen dentro de strings, para no
    confundirse con listas anidadas como lookup_ids.
    """
    name_idx = content.find(f'"name": "{section_name}"')
    if name_idx == -1:
        return None
    rows_idx = content.find('"rows": [', name_idx)
    if rows_idx == -1:
        return None
    open_idx = content.index("[", rows_idx)
    depth = 0
    in_str = None
    i = open_idx
    while i < len(content):
        ch = content[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == in_str:
                in_str = None
        elif ch in "\"'":
            in_str = ch
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return open_idx, i + 1
        i += 1
    return None


def _orphan_rows_text(items: list, indent: str) -> str:
    """Genera las filas de CENSUS_SPEC para una lista de (id, seccion, nombre)."""
    return "\n".join(
        f'{indent}{{"id": "{id_str}", "seccion": "{seccion}", "nombre": "{nombre}"}},'
        for id_str, seccion, nombre in items
    )


def generate_census_spec_additions(orphans: dict) -> str:
    """Genera el código Python (solo muestra) para agregar IDs huérfanos al CENSUS_SPEC."""
    if not orphans:
        return "# No hay IDs huérfanos para agregar\n"

    by_section = {}
    for id_str in orphans:
        section_name, seccion, nombre = infer_section_from_id(id_str)
        by_section.setdefault(section_name, []).append((id_str, seccion, nombre))

    additions = ["# IDs huérfanos detectados — insertar DENTRO de la sección indicada", ""]
    for section_name, items in sorted(by_section.items()):
        if section_name == "UNKNOWN":
            continue
        additions.append(f"# {section_name}")
        additions.append(_orphan_rows_text(items, indent="            "))
        additions.append("")
    unknown = by_section.get("UNKNOWN", [])
    if unknown:
        additions.append("# Sin sección reconocida en el spec (requieren revisión manual):")
        for id_str, _, _ in unknown:
            additions.append(f"#   {id_str}")
        additions.append("")
    return "\n".join(additions)


def insert_orphan_rows(content: str, orphans: dict) -> tuple[str, list, list]:
    """Inserta cada huérfano DENTRO de la sección que le corresponde del CENSUS_SPEC.

    Retorna (contenido_nuevo, ids_insertados, ids_sin_seccion).
    """
    by_section = {}
    unknown = []
    for id_str in orphans:
        section_name, seccion, nombre = infer_section_from_id(id_str)
        if section_name == "UNKNOWN":
            unknown.append(id_str)
            continue
        by_section.setdefault(section_name, []).append((id_str, seccion, nombre))

    edits = []
    inserted = []
    for section_name, items in by_section.items():
        bounds = _find_rows_bounds(content, section_name)
        if bounds is None:
            unknown.extend(id_str for id_str, _, _ in items)
            continue
        open_idx, close_idx = bounds

        # Indentación: la de la última fila existente antes del cierre
        last_open = content.rfind("{", open_idx, close_idx)
        if last_open != -1:
            line_start = content.rfind("\n", 0, last_open) + 1
            indent = content[line_start:last_open] if not content[line_start:last_open].strip() else " " * 12
        else:
            indent = " " * 12

        close_line_start = content.rfind("\n", 0, close_idx) + 1
        rows_text = _orphan_rows_text(items, indent) + "\n"
        edits.append((close_line_start, rows_text))
        inserted.extend(id_str for id_str, _, _ in items)

    # Aplicar de abajo hacia arriba para no desplazar los índices previos
    new_content = content
    for pos, text in sorted(edits, key=lambda e: e[0], reverse=True):
        new_content = new_content[:pos] + text + new_content[pos:]

    return new_content, inserted, unknown


def auto_fix_orphans(orphans: dict) -> bool:
    """Pregunta al usuario si quiere agregar IDs huérfanos al CENSUS_SPEC."""
    if not orphans:
        print("✓ No hay IDs huérfanos para corregir.")
        return False
    
    print("\n" + "=" * 52)
    print("  DETECCIÓN DE IDS HUÉRFANOS")
    print("=" * 52)
    print(f"  Se detectaron {len(orphans)} IDs huérfanos fuera del CENSUS_SPEC:")
    print()
    
    for id_str, entry in orphans.items():
        section_name, seccion, nombre = infer_section_from_id(id_str)
        print(f"  - {id_str}")
        print(f"    Documento: {entry['doc']}")
        print(f"    Sección inferida: {section_name} -> {seccion}")
        print(f"    Nombre inferido: {nombre}")
        print()
    
    print("=" * 52)
    print("  ¿Deseas agregar estos IDs al CENSUS_SPEC?")
    print("  [Y/y] = Sí, agregar al archivo generate_census.py")
    print("  [N/n] = No, solo mostrar el código generado")
    print("  [C/c] = Cancelar, no hacer nada")
    print("=" * 52)
    
    response = input("  Tu elección: ").strip().lower()
    
    if response in ['c']:
        print("✓ Cancelado. No se realizaron cambios.")
        return False
    
    additions_code = generate_census_spec_additions(orphans)
    
    if response in ['n']:
        print("\n--- Código generado (no aplicado) ---")
        print(additions_code)
        print("--- Fin del código ---")
        return False
    
    if response in ['y']:
        script_path = Path(__file__).resolve()
        current_content = script_path.read_text(encoding="utf-8")

        # Idempotencia: no reinsertar IDs que ya están en el spec
        current_spec = _spec_from_source(current_content)
        if current_spec is None:
            print("✗ No se pudo parsear el CENSUS_SPEC actual. Archivo sin cambios.")
            return False
        already_known = known_ids_from_spec(current_spec)
        new_orphans = {k: v for k, v in orphans.items() if k not in already_known}
        skipped_existing = len(orphans) - len(new_orphans)
        if skipped_existing:
            print(f"  · {skipped_existing} ID(s) ya estaban en CENSUS_SPEC (se omiten).")
        if not new_orphans:
            print("✓ Nada que agregar: todos los huérfanos ya están en el spec.")
            return False

        new_content, inserted, unknown = insert_orphan_rows(current_content, new_orphans)

        if not inserted:
            print("✗ No se insertó ningún ID: no se encontró la sección destino en CENSUS_SPEC.")
            print("  Usa [N/n] para revisar el código generado. Archivo sin cambios.")
            return False

        # Validación previa a la escritura: sintaxis + los IDs deben quedar DENTRO del spec
        new_spec = _spec_from_source(new_content)
        if new_spec is None:
            print("✗ Validación falló (CENSUS_SPEC ilegible tras el cambio). Archivo sin cambios.")
            return False
        new_known = known_ids_from_spec(new_spec)
        missing = [id_str for id_str in inserted if id_str not in new_known]
        if missing:
            print(f"✗ Validación falló: {missing[:3]} no quedaron dentro de CENSUS_SPEC. Archivo sin cambios.")
            return False

        script_path.write_text(new_content, encoding="utf-8")
        print(f"✓ {len(inserted)} ID(s) agregados DENTRO de CENSUS_SPEC en {script_path}")
        if unknown:
            print(f"  ⚠ {len(unknown)} ID(s) sin sección reconocida (no insertados): {', '.join(unknown[:5])}")
        return True

    print("✗ Respuesta no reconocida. Cancelado.")
    return False

# ─── PARSER NATIVO Y CONVERSOR DE MARKDOWN A NOTION API BLOCKS ────────────────

def parse_markdown_table_cell(cell_str: str) -> list:
    """Parsea el contenido de una celda Markdown generando objetos rich_text válidos para la API de Notion.
    
    Soporta:
    - Enlaces con formato [`LABEL`](URL) o [LABEL](URL)
    - Fragmentos en inline code `CODE`
    - Texto plano sin formato
    """
    cell_str = cell_str.strip()
    if not cell_str:
        return [{"type": "text", "text": {"content": ""}}]

    link_pattern = re.compile(r"\[`?([^`\]]+)`?\]\(\s*(\S+?)\s*\)")
    rich_text = []
    last_idx = 0

    for match in link_pattern.finditer(cell_str):
        start, end = match.span()
        label, url = match.group(1), match.group(2)

        if start > last_idx:
            pre_text = cell_str[last_idx:start]
            rich_text.append({"type": "text", "text": {"content": pre_text}})

        rich_text.append({
            "type": "text",
            "text": {
                "content": label,
                "link": {"url": url}
            },
            "annotations": {
                "code": True
            }
        })
        last_idx = end

    if last_idx < len(cell_str):
        post_text = cell_str[last_idx:]
        code_pattern = re.compile(r"`([^`]+)`")
        code_last_idx = 0
        
        for code_match in code_pattern.finditer(post_text):
            c_start, c_end = code_match.span()
            c_label = code_match.group(1)

            if c_start > code_last_idx:
                rich_text.append({
                    "type": "text",
                    "text": {"content": post_text[code_last_idx:c_start]}
                })

            rich_text.append({
                "type": "text",
                "text": {"content": c_label},
                "annotations": {"code": True}
            })
            code_last_idx = c_end

        if code_last_idx < len(post_text):
            rich_text.append({
                "type": "text",
                "text": {"content": post_text[code_last_idx:]}
            })

    return rich_text if rich_text else [{"type": "text", "text": {"content": cell_str}}]


TABLE_SEPARATOR_RE = re.compile(r"^\s*\|[\s:\-|]+\|\s*$")


def markdown_table_to_notion_blocks(table_lines: list, max_rows_per_table: int = 98) -> list:
    """Convierte un bloque de lIneas de tabla Markdown a una lista de bloques 'table' de Notion,
    dividiendo tablas de mas de 98 filas para respetar el limite de 100 de la API (header + 98 filas = 99 bloques).
    """
    if not table_lines:
        return []

    header_line = table_lines[0]
    headers = [c.strip() for c in header_line.strip().strip('|').split('|')]
    column_count = len(headers)

    # Filtrar SOLO la línea separadora (|---|---|) y quedarse con filas de datos.
    # Antes se descartaba cualquier fila que contuviera '---' en alguna celda,
    # perdiendo filas legítimas (p. ej. URLs con '---').
    row_lines = [
        line for line in table_lines[1:]
        if line.strip().startswith('|') and not TABLE_SEPARATOR_RE.match(line)
    ]

    header_cells = [parse_markdown_table_cell(h) for h in headers]
    data_rows = []
    for row in row_lines:
        raw_cells = [c.strip() for c in row.strip().strip('|').split('|')]
        while len(raw_cells) < column_count:
            raw_cells.append("")
        raw_cells = raw_cells[:column_count]
        cells = [parse_markdown_table_cell(c) for c in raw_cells]
        data_rows.append({
            "object": "block",
            "type": "table_row",
            "table_row": {"cells": cells}
        })

    table_blocks = []
    for i in range(0, len(data_rows), max_rows_per_table):
        chunk = data_rows[i:i + max_rows_per_table]
        children = [{
            "object": "block",
            "type": "table_row",
            "table_row": {"cells": header_cells}
        }] + chunk

        table_blocks.append({
            "object": "block",
            "type": "table",
            "table": {
                "table_width": column_count,
                "has_column_header": True,
                "has_row_header": False,
                "children": children
            }
        })

    return table_blocks


def markdown_to_notion_blocks(markdown: str) -> list:
    """Convierte sintaxis Markdown completa a bloques nativos de Notion AST estructurados."""
    blocks = []
    lines = markdown.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        if line.startswith('## '):
            text = line[3:].strip()
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                }
            })
            i += 1
        elif line.startswith('### '):
            text = line[4:].strip()
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                }
            })
            i += 1
        elif line.startswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].startswith('|'):
                table_lines.append(lines[i])
                i += 1
            
            t_blocks = markdown_table_to_notion_blocks(table_lines)
            blocks.extend(t_blocks)
        elif line.strip() == '---':
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })
            i += 1
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": line.strip()}}]
                }
            })
            i += 1

    return blocks


def fetch_all_children(block_id: str) -> list | None:
    """Lista TODOS los bloques hijos de una página, paginando con start_cursor.

    La versión anterior leía solo la primera página (100 bloques): en páginas
    más grandes dejaba bloques viejos sin borrar (duplicados tras el re-render).
    Retorna None si la lectura falla, para que el llamador aborte sin escribir.
    """
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    results = []
    cursor = None
    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        try:
            response = requests.get(url, headers=HEADERS, params=params)
        except Exception as e:
            print(f"✗ Error de red leyendo bloques de {block_id[:8]}: {e}")
            return None
        if response.status_code != 200:
            print(f"✗ Error al obtener bloques actuales: {response.status_code} {response.text[:120]}")
            return None
        data = response.json()
        results.extend(data.get("results", []))
        if not data.get("has_more"):
            return results
        cursor = data.get("next_cursor")
        if not cursor:
            return results


def _delete_block(block_id: str, retries: int = 3) -> bool:
    """Borra un bloque verificando el status HTTP, con backoff ante 429."""
    url = f"https://api.notion.com/v1/blocks/{block_id}"
    for attempt in range(1, retries + 1):
        try:
            r = requests.delete(url, headers=HEADERS)
        except Exception as e:
            print(f"  ⚠ Fallo de red borrando bloque {block_id[:8]}: {e}")
            time.sleep(RETRY_BACKOFF_SECONDS * attempt)
            continue
        if r.status_code == 200:
            return True
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 2))
            time.sleep(wait)
            continue
        print(f"  ⚠ No se pudo borrar bloque {block_id[:8]}: HTTP {r.status_code} {r.text[:100]}")
        return False
    return False


def update_notion_census_page(page_id: str, markdown_content: str) -> bool:
    """Publica el census en Notion con orden seguro: APPEND primero, DELETE después.

    El patrón anterior (borrar todo y luego escribir) dejaba la página VACÍA si
    el append fallaba, y no verificaba los DELETE. Ahora:
      1. Se leen y paginan TODOS los bloques actuales.
      2. Se agregan los bloques nuevos por lotes; si un lote falla se deshace lo
         agregado y se aborta SIN tocar los bloques viejos.
      3. Solo si el paso 2 terminó OK se borran los viejos, verificando status.
    """
    blocks = markdown_to_notion_blocks(markdown_content)

    if not blocks:
        print("✗ Payload vacío: se aborta para no dejar la página sin contenido.")
        return False

    current_blocks = fetch_all_children(page_id)
    if current_blocks is None:
        return False

    append_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    created_ids = []

    for i in range(0, len(blocks), 100):
        batch = blocks[i:i+100]
        response = None
        try:
            response = requests.patch(append_url, headers=HEADERS, json={"children": batch})
        except Exception as e:
            print(f"✗ Error de red agregando bloques (lote {i//100 + 1}): {e}")
        if response is None or response.status_code != 200:
            status = "sin respuesta" if response is None else f"{response.status_code}: {response.text[:150]}"
            print(f"✗ Error al agregar bloques (lote {i//100 + 1}): {status}")
            for bid in created_ids:
                _delete_block(bid)
            print("  ↩ Se deshizo lo agregado; los bloques originales NO se tocaron.")
            return False
        created_ids.extend(
            b.get("id") for b in response.json().get("results", []) if b.get("id")
        )

    deleted = 0
    failed = 0
    for block in current_blocks:
        if _delete_block(block["id"]):
            deleted += 1
        else:
            failed += 1

    if failed:
        print(f"✗ Contenido publicado pero {failed} bloque(s) viejos no se pudieron borrar "
              f"(quedan duplicados en la página). Reintentar o limpiar manualmente.")
        return False

    print(f"✓ Página de Notion actualizada exitosamente (nuevos: {len(blocks)}, reemplazados: {deleted})")
    return True


def get_page_version(page_id: str) -> str:
    """Extrae la propiedad 'Versión' de una página Notion."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": _notion_version(),
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return f"Error HTTP {response.status_code}"

        properties = response.json().get("properties", {})
        prop = properties.get("Versión") or properties.get("Version") or properties.get("Versión ")
        if not prop:
            return "Sin Propiedad"

        p_type = prop.get("type")
        if p_type == "rich_text":
            texts = prop.get("rich_text", [])
            return texts[0].get("plain_text", "N/A") if texts else "N/A"
        elif p_type == "select":
            return prop.get("select", {}).get("name", "N/A")
        elif p_type == "title":
            texts = prop.get("title", [])
            return texts[0].get("plain_text", "N/A") if texts else "N/A"
        return "Tipo no Soportado"
    except Exception as e:
        return f"Error: {str(e)}"


def update_page_version(page_id: str, version: str, prop_name: str = "Versión") -> bool:
    """Actualiza la propiedad de versión de una página Notion."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": _notion_version(),
        "Content-Type": "application/json"
    }
    payload = {
        "properties": {
            prop_name: {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": version
                        }
                    }
                ]
            }
        }
    }
    try:
        response = requests.patch(url, headers=headers, json=payload)
        return response.status_code == 200
    except Exception:
        return False


def sync_page_version_from_changelog(page_id: str, changelog_id: str) -> bool:
    """Sincroniza la versión de una página con la versión del CHANGELOG."""
    # Obtener versión maestra del CHANGELOG
    master_version = get_page_version(changelog_id)
    if "Error" in master_version or master_version in ["N/A", "Sin Propiedad"]:
        print(f"  ✗ Fallo al leer versión maestro de CHANGELOG: {master_version}")
        return False

    print(f"  ✓ Versión maestro del CHANGELOG: {master_version}")

    # Obtener versión actual de la página
    current_version = get_page_version(page_id)
    print(f"  Versión actual de la página: {current_version}")

    # Si ya están sincronizadas, no hacer nada
    if current_version == master_version:
        print("  ✓ La versión ya está sincronizada")
        return True

    # Actualizar versión
    print(f"  → Actualizando versión a {master_version}...")
    prop_name = "Versión " if page_id == "36e938befc4281d6bf40dfe7dee782a5" else "Versión"  # VANTAGE tiene "Versión " con espacio
    write_ok = update_page_version(page_id, master_version, prop_name=prop_name)
    if not write_ok:
        print("  ✗ Fallo al actualizar versión")
        return False

    # Verificar post-escritura
    confirmed_version = get_page_version(page_id)
    if confirmed_version == master_version:
        print(f"  ✓ Versión sincronizada exitosamente: {confirmed_version}")
        return True
    else:
        print(f"  ✗ Verificación falló: esperado {master_version}, releído {confirmed_version}")
        return False


def sync_to_notion(page_id: str, markdown_content: str, auto_confirm: bool = False, sync_version: bool = True) -> bool | None:
    """Sincroniza el census a Notion.

    Retorna True si se publicó OK, False si hubo un error real y None si el
    usuario canceló (cancelar no es un fallo: el entry point no debe marcar
    exit code 1 en ese caso).
    """
    print("\n" + "=" * 52)
    print("  SINCRONIZACIÓN A NOTION")
    print("=" * 52)
    print(f"  Página ID: {page_id}")
    print(f"  Tamaño del contenido: {len(markdown_content)} caracteres")
    print()

    if auto_confirm:
        print("  Auto-confirmado via --yes")
        print("=" * 52)
        content_ok = update_notion_census_page(page_id, markdown_content)
    else:
        print("  ¿Deseas actualizar la página de Notion con el census actual?")
        print("  [Y/y] = Sí, actualizar Notion")
        print("  [N/n] = No, cancelar")
        print("=" * 52)

        response = input("  Tu elección: ").strip().lower()
        if response in ['y']:
            content_ok = update_notion_census_page(page_id, markdown_content)
        else:
            print("✓ Cancelado. No se actualizó Notion.")
            return None

    if not content_ok:
        print("✗ Error al actualizar contenido")
        return False

    # Sincronizar versión con CHANGELOG si se solicita
    if sync_version:
        print("\n" + "=" * 52)
        print("  SINCRONIZACIÓN DE VERSIÓN")
        print("=" * 52)
        changelog_id = (DOCUMENTS.get("Change Log") or CHANGELOG_PAGE_ID).replace("-", "")
        if not changelog_id:
            print("  ✗ No se pudo resolver ID del CHANGELOG")
            return False

        page_id_clean = page_id.replace("-", "")
        version_ok = sync_page_version_from_changelog(page_id_clean, changelog_id)
        return version_ok

    return True

# ─── RENDER ────────────────────────────────────────────────────────────────────

def render_markdown(link_index: dict, orphans: dict, spec: list | None = None) -> tuple:
    lines = []
    unresolved = []
    hardcoded_fallbacks = []

    for i, section in enumerate(spec if spec is not None else CENSUS_SPEC):
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
                cell = f"[`{display_id}`]({link})"
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
            lines.append(f"| `{id_str}` | {entry['doc']} | [link]({entry['link']}) |")
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
            print(f"      plain={e.get('plain')!r}")
    print("\n" + "#" * 52)


if __name__ == "__main__":
    debug_ids = []
    auto_fix_orphans_flag = False
    sync_to_notion_flag = False
    auto_confirm_flag = False
    sync_version_flag = True
    notion_page_id = "394938befc4281e6a381e3869e60d89d"
    
    if "--debug-id" in sys.argv:
        idx = sys.argv.index("--debug-id")
        # Solo IDs: cualquier flag posterior (p. ej. --sync-to-notion) no es un ID
        debug_ids = [a for a in sys.argv[idx + 1:] if not a.startswith("--")]
        if not debug_ids:
            print("[ERROR] --debug-id requiere al menos un ID después, ej.:")
            print("  python3 generate_census.py --debug-id KERNEL:GATE-DECISION-001 KERNEL:GATE-DECISION-004")
            sys.exit(1)

    if "--auto-fix-orphans" in sys.argv:
        auto_fix_orphans_flag = True

    if "--sync-to-notion" in sys.argv:
        sync_to_notion_flag = True
        idx = sys.argv.index("--sync-to-notion")
        if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith("--"):
            notion_page_id = sys.argv[idx + 1]

    if "--yes" in sys.argv:
        auto_confirm_flag = True

    if "--no-sync-version" in sys.argv:
        sync_version_flag = False

    print("\nV-ID-CENSUS Generator v3.1")
    print(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 52)

    link_index, incomplete_docs = build_link_index()

    if debug_ids:
        print_debug_ids(link_index, debug_ids)
        sys.exit(0)

    known_ids = known_ids_from_spec()
    orphans = find_orphan_ids(link_index, known_ids)
    md, unresolved, hardcoded_fallbacks = render_markdown(link_index, orphans)

    # Ruta relativa al script (antes hardcodeada a una ruta absoluta del operador → no portable)
    output = script_dir.parent / "data" / "V_ID_CENSUS_PRODUCTION.md"
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
    print(f"  IDs con Sección hardcodeada (sin heading 'N' detectable en vivo): {len(hardcoded_fallbacks)}")
    if hardcoded_fallbacks:
        print("  ⚠ Revisar manualmente si el número/letra en CENSUS_SPEC sigue vigente:")
        for uid in hardcoded_fallbacks:
            print(f"    - {uid}")
    print("=" * 52)
    
    exit_code = 0

    if auto_fix_orphans_flag:
        if auto_fix_orphans(orphans):
            print("\nRegenerando census con IDs actualizados...")
            # Recargar el spec DESDE DISCO: el de memoria no refleja el auto-fix
            updated_spec = load_spec_from_file(Path(__file__).resolve()) or CENSUS_SPEC
            known_ids = known_ids_from_spec(updated_spec)
            orphans = find_orphan_ids(link_index, known_ids)
            md, unresolved, hardcoded_fallbacks = render_markdown(link_index, orphans, updated_spec)
            output.write_text(md, encoding="utf-8")
            print("✓ Census regenerado.")
    
    if sync_to_notion_flag:
        # None = el usuario canceló (no es fallo); False = error real
        if sync_to_notion(notion_page_id, md, auto_confirm_flag, sync_version_flag) is False:
            exit_code = 1

    if incomplete_docs:
        print("\n  ⚠️  ADVERTENCIA: CENSUS INCOMPLETO")
        print("  Los siguientes documentos NO se indexaron completos")
        for entry in incomplete_docs:
            print(f"    - {entry['doc']}: {entry['error']}")
        exit_code = 1

    print(f"\nExportado a: {output.resolve()}")
    sys.exit(exit_code)
