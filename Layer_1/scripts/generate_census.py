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

VALID_PREFIXES = ("KERNEL:", "MANUAL:", "CANON:", "CAREER_CANON:", "SP:", "ALIASES:", "CHANGELOG:", "CHANGELOG_ARCHIVO:", "BRIEF:")

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
            {"id": "KERNEL:DOCUMENTATION", "seccion": "03", "nombre": "Documentación y Gobernanza (L0)"},
            {"id": "KERNEL:DOCUMENTATION-001", "seccion": "03.1", "nombre": "Canonical Document ID Contract"},
            {"id": "KERNEL:DOCUMENTATION-002", "seccion": "03.2", "nombre": "Nomenclatura de IDs Canónicos"},
            {"id": "KERNEL:DOCUMENTATION-003", "seccion": "03.3", "nombre": "L0 — VANTAGE Runtime"},
            {"id": "KERNEL:DOCUMENTATION-004", "seccion": "03.4", "nombre": "Kernel vs Manual"},
            {"id": "KERNEL:DOCUMENTATION-005", "seccion": "03.5", "nombre": "Convención de Anuncio de Skills"},
            {"id": "KERNEL:DOCUMENTATION-006", "seccion": "03.6", "nombre": "Diffs y Write-Back Verification"},
            {"id": "KERNEL:DOCUMENTATION-007", "seccion": "03.7", "nombre": "Version-Check Tool (verify_versions.py)"},
            {"id": "KERNEL:DOCUMENTATION-008", "seccion": "03.8", "nombre": "Sincronización de Versiones"},
            {"id": "KERNEL:DOCUMENTATION-009", "seccion": "03.9", "nombre": "Census Sync"},
            {"id": "KERNEL:DOCUMENTATION-010", "seccion": "03.10", "nombre": "Documentación Transversal"},
            {"id": "KERNEL:DOCUMENTATION-011", "seccion": "03.11", "nombre": "Gate Decision Documentation"},
            {"id": "KERNEL:DOCUMENTATION-012", "seccion": "03.12", "nombre": "Notebook Gemini — Auditor Documental Externo"},
            {"id": "KERNEL:DOCUMENTATION-013", "seccion": "03.13", "nombre": "Protocolo Sandbox — Economía de Tokens Máxima"},
            {"id": "KERNEL:ARCHITECTURE", "seccion": "04", "nombre": "Arquitectura de Cuatro Capas"},
            {"id": "KERNEL:ARCHITECTURE-L1", "seccion": "04.1", "nombre": "L1 — Active Search"},
            {"id": "KERNEL:ARCHITECTURE-L2", "seccion": "04.2", "nombre": "L2 — Strategic Search"},
            {"id": "KERNEL:ARCHITECTURE-L3", "seccion": "04.3", "nombre": "L3 — Passive Intake"},
            {"id": "KERNEL:ARCHITECTURE-L4", "lookup_ids": ["KERNEL:ARCHITECTURE-004", "KERNEL:ARHITECTURE-L4", "KERNEL:ARCHITECTURE-L4"], "seccion": "04.4", "nombre": "L4 — Version Control & Infrastructure"},
            {"id": "KERNEL:DASHBOARD-CHECKLIST-ARCH", "seccion": "06", "nombre": "Dashboard Checklist Architecture"},
            {"id": "KERNEL:OWNERSHIP", "seccion": "05", "nombre": "División de Responsabilidades AI/Python"},
            {"id": "KERNEL:OWNERSHIP-001", "seccion": "05.1", "nombre": "AI Component"},
            {"id": "KERNEL:OWNERSHIP-002", "seccion": "05.2", "nombre": "Python Component"},
            {"id": "KERNEL:PURPOSE", "seccion": "01", "nombre": "Propósito del Sistema"},
            {"id": "KERNEL:PURPOSE-001", "seccion": "01.1", "nombre": "Objetivo Principal"},
            {"id": "KERNEL:SCHEMA", "seccion": "07", "nombre": "Modelo de Datos y Ownership"},
            {"id": "KERNEL:SCHEMA-001", "seccion": "07.1", "nombre": "Schema — Class A Fields"},
            {"id": "KERNEL:SCHEMA-002", "seccion": "07.2", "nombre": "Schema — Class B Fields"},
            {"id": "KERNEL:SCHEMA-003", "seccion": "07.3", "nombre": "Schema — Field Validation Rules"},
            {"id": "KERNEL:SCHEMA-004", "seccion": "07.4", "nombre": "Schema — Class A vs Class B"},
            {"id": "KERNEL:SCHEMA-005", "seccion": "07.5", "nombre": "Schema — Field Types"},
            {"id": "KERNEL:SCHEMA-006", "seccion": "07.6", "nombre": "Schema — Validation Rules"},
            {"id": "KERNEL:SCHEMA-007", "seccion": "07.7", "nombre": "Schema — Mutability Rules"},
            {"id": "KERNEL:SCHEMA-008", "seccion": "07.8", "nombre": "Valores Operativos — Next_Action (Tracker de Vacantes)"},
            {"id": "KERNEL:TRACKER-SCHEMA", "seccion": "08", "nombre": "Schema del Tracker de Vacantes"},
            {"id": "KERNEL:TRACKER-SCHEMA-001", "seccion": "08.1", "nombre": "Tracker Schema — Campos Principales"},
            {"id": "KERNEL:TRACKER-SCHEMA-002", "seccion": "08.2", "nombre": "Tracker Schema — Campos Derivados"},
            {"id": "KERNEL:FAIL-PHILOSOPHY", "seccion": "02", "nombre": "Filosofía de Fallo"},
            {"id": "KERNEL:FAIL-PHILOSOPHY-001", "seccion": "02.1", "nombre": "Fail-Fast vs Fail-Safe"},
            {"id": "KERNEL:FAIL-PHILOSOPHY-002", "seccion": "02.2", "nombre": "Recovery Strategies"},
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
            {"id": "KERNEL:CV-GOLDEN-RULES", "seccion": "10", "nombre": "Golden Rules — Límites de Ejecución"},
            {"id": "KERNEL:CV-GOLDEN-RULES-001", "seccion": "10.1", "nombre": "Regla de Oro #1"},
            {"id": "KERNEL:CV-GOLDEN-RULES-002", "seccion": "10.2", "nombre": "Regla de Oro #2"},
            {"id": "KERNEL:CV-GOLDEN-RULES-003", "seccion": "10.3", "nombre": "Regla de Oro #3"},
            {"id": "KERNEL:CV-GOLDEN-RULES-004", "seccion": "10.4", "nombre": "Regla de Oro #4"},
            {"id": "KERNEL:CV-GOLDEN-RULES-005", "seccion": "10.5", "nombre": "Regla de Oro #5"},
                {"id": "KERNEL:CV-GOLDEN-RULES-006", "seccion": "10.6", "nombre": "Regla de Oro #6 — Invarianza de la Decisión de Gate"},
            {"id": "KERNEL:TRIGGERS", "seccion": "11", "nombre": "Contratos de Ejecución del AI Component"},
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
            {"id": "KERNEL:CV-PIPELINE-001", "seccion": "12.1", "nombre": "CV-A"},
            {"id": "KERNEL:CV-PIPELINE-002", "seccion": "12.2", "nombre": "CV-B"},
            {"id": "KERNEL:CANON-UPDATE", "seccion": "13", "nombre": "Actualización del Canon"},
            {"id": "KERNEL:NAMING-CONVENTION", "seccion": "14", "nombre": "Convención de Nombres"},
            {"id": "KERNEL:CONTEXT-INFRASTRUCTURE", "seccion": "15", "nombre": "Context Infrastructure"},
            {"id": "KERNEL:CONTEXT-INFRASTRUCTURE-001", "seccion": "15.1", "nombre": "Context Infrastructure — Data Sources"},
            {"id": "KERNEL:CONTEXT-INFRASTRUCTURE-002", "seccion": "15.2", "nombre": "Context Infrastructure — Integration Points"},
            {"id": "KERNEL:DATA-FLOW", "seccion": "16", "nombre": "Flujo de Datos"},
            {"id": "KERNEL:EVOLUTION", "seccion": "17", "nombre": "Evolución del Sistema"},
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
            {"id": "MANUAL:WEEKLY-FLOW-006", "seccion": "08.6", "nombre": "Cadence Matrix — Weekly Rhythm"},
            {"id": "MANUAL:RUNTIME", "seccion": "09", "nombre": "VANTAGE Runtime (Consulta Operativa)"},
            {"id": "MANUAL:RUNTIME-001", "seccion": "9.1", "nombre": "¿Qué es el Runtime?"},
            {"id": "MANUAL:RUNTIME-002", "seccion": "9.2", "nombre": "Comandos Principales"},
            {"id": "MANUAL:RUNTIME-003", "seccion": "9.3", "nombre": "Cuándo Correr Sync"},
            {"id": "MANUAL:RUNTIME-004", "seccion": "9.4", "nombre": "Runtime Build"},
            {"id": "MANUAL:RUNTIME-005", "seccion": "9.5", "nombre": "Notebook Gemini — Triaje de Consultas Documentales"},
            {"id": "MANUAL:DATA-MANAGEMENT", "seccion": "10", "nombre": "Gestión de Datos"},
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
            {"id": "MANUAL:WEEKLY-FLOW-006", "seccion": "08.6", "nombre": "Cadence Matrix — Weekly Rhythm"},
            {"id": "MANUAL:GOLDEN-SKELETON-REF", "seccion": "20", "nombre": "Figma Sync & Golden Skeleton"},
            {"id": "MANUAL:FIGMA-SYNC-001", "seccion": "20.1", "nombre": "Arquitectura del Ecosistema"},
            {"id": "MANUAL:FIGMA-SYNC-002", "seccion": "20.2", "nombre": "Contrato de Bloque"},
            {"id": "MANUAL:FIGMA-SYNC-003", "seccion": "20.3", "nombre": "Flujo de Inyección"},
            {"id": "MANUAL:FIGMA-SYNC-004", "seccion": "20.4", "nombre": "Sanitización de Contenido"},
            {"id": "MANUAL:FIGMA-SYNC-005", "seccion": "20.5", "nombre": "Regla de Reemplazo Total"},
            {"id": "MANUAL:SCHEMA-FIELD-REF", "seccion": "21", "nombre": "Schema Class A/B — Referencia de Campos"},
            {"id": "MANUAL:SCRIPT-GLOSSARY", "seccion": "22", "nombre": "Script Glossary"},
            {"id": "MANUAL:SCRIPT-GLOSSARY-DASHBOARD", "seccion": "22.4", "nombre": "Script Glossary — Dashboard"},
            {"id": "MANUAL:SCRIPT-GLOSSARY-DASHBOARD-MODULES", "seccion": "22.4a", "nombre": "Script Glossary — Dashboard Modules"},
            {"id": "MANUAL:SCRIPT-GLOSSARY-L1", "seccion": "22.1", "nombre": "Script Glossary — L1"},
            {"id": "MANUAL:SCRIPT-GLOSSARY-CV-PREP", "seccion": "22.2", "nombre": "CV Pipeline — Preparación Mecánica (Miércoles)"},
            {"id": "MANUAL:SCRIPT-GLOSSARY-L1-MODULES", "seccion": "22.1a", "nombre": "Script Glossary — L1 Modules"},
            {"id": "MANUAL:SCRIPT-GLOSSARY-L1-TOOLS", "seccion": "22.1b", "nombre": "Script Glossary — L1 Tools"},
            {"id": "MANUAL:SCRIPT-GLOSSARY-L4", "seccion": "22.3", "nombre": "Script Glossary — L4"},
            {"id": "MANUAL:SCRIPT-GLOSSARY-RAYCAST", "seccion": "22.5", "nombre": "Script Glossary — Raycast"},
            {"id": "MANUAL:SCRIPT-GLOSSARY-XREF", "seccion": "22.6", "nombre": "Script Glossary — Cross-Reference"},
            {"id": "MANUAL:SKILL-GLOSSARY", "seccion": "23", "nombre": "Glosario de Skills — Referencia Operativa en Humano"},
            {"id": "MANUAL:SKILL-GLOSSARY-CORE", "seccion": "23.1", "nombre": "Pipeline CV y Ciclo de Sesión"},
            {"id": "MANUAL:SKILL-GLOSSARY-HOUSEKEEPING", "seccion": "23.2", "nombre": "Sincronización y Mantenimiento Documental"},
            {"id": "MANUAL:SKILL-GLOSSARY-AUDIT", "seccion": "23.3", "nombre": "Auditoría y Continuidad"},
            {"id": "MANUAL:SKILL-GLOSSARY-STYLE", "seccion": "23.4", "nombre": "Estilos de Escritura y Generación"},
            {"id": "MANUAL:SKILL-GLOSSARY-XREF", "seccion": "23.5", "nombre": "Gaps Abiertos"},            
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
            {"id": "BRIEF:PURPOSE-SCOPE", "lookup_ids": ["BRIEF:PURPOSE-SCOPE", "BRIEF:SCOPE", "BRIEF:001"], "seccion": "00", "nombre": "Propósito y Alcance"},
            {"id": "BRIEF:AUTHORITY-MATRIX", "lookup_ids": ["BRIEF:AUTHORITY-MATRIX", "BRIEF:002"], "seccion": "01", "nombre": "Matriz de Autoridad Documental"},
            {"id": "BRIEF:ECOSYSTEM", "lookup_ids": ["BRIEF:ECOSYSTEM", "BRIEF:003"], "seccion": "02", "nombre": "Ecosistema Documental"},
            {"id": "BRIEF:NAV-CONTRACTS", "lookup_ids": ["BRIEF:NAV-CONTRACTS", "BRIEF:004"], "seccion": "03", "nombre": "Contratos de navegación"},
            {"id": "BRIEF:DOMAIN-ARCHITECTURE", "lookup_ids": ["BRIEF:DOMAIN-ARCHITECTURE", "BRIEF:005"], "seccion": "04", "nombre": "Dominios"},
            {"id": "BRIEF:VERIFICATION-DEPTH", "lookup_ids": ["BRIEF:VERIFICATION-DEPTH", "BRIEF:006"], "seccion": "05", "nombre": "Contratos de verificación"},
            {"id": "BRIEF:CROSS-DEPENDENCIES", "lookup_ids": ["BRIEF:CROSS-DEPENDENCIES", "BRIEF:007"], "seccion": "06", "nombre": "Dependencias entre documentos"},
            {"id": "BRIEF:MAINTENANCE-CONTRACT", "lookup_ids": ["BRIEF:MAINTENANCE-CONTRACT", "BRIEF:008"], "seccion": "07", "nombre": "Contrato de Mantenimiento"},
            {"id": "BRIEF:DECISION-TREE", "lookup_ids": ["BRIEF:DECISION-TREE", "BRIEF:009"], "seccion": "08", "nombre": "Árbol de Decisiones"},
            {"id": "BRIEF:NAV-PRINCIPLES", "lookup_ids": ["BRIEF:NAV-PRINCIPLES", "BRIEF:010"], "seccion": "09", "nombre": "Principios de Navegación"},
            {"id": "BRIEF:EXPECTED-OUTCOME", "lookup_ids": ["BRIEF:EXPECTED-OUTCOME", "BRIEF:011"], "seccion": "10", "nombre": "Resultado Esperado"},
            {"id": "BRIEF:AUTHORITY-001", "seccion": "08.1", "nombre": "Autoridad"},
            {"id": "BRIEF:CONSULTATION-001", "seccion": "04.1", "nombre": "Consulta Arquitectónica"},
            {"id": "BRIEF:CONSULTATION-002", "seccion": "04.2", "nombre": "Consulta Operativa"},
            {"id": "BRIEF:CONSULTATION-003", "seccion": "04.3", "nombre": "Consulta Profesional"},
            {"id": "BRIEF:CONSULTATION-004", "seccion": "04.4", "nombre": "Consulta Documental"},
            {"id": "BRIEF:CONSULTATION-005", "seccion": "04.5", "nombre": "Consulta de IDs"},
            {"id": "BRIEF:CONSULTATION-006", "seccion": "04.6", "nombre": "Consulta Histórica"},
            {"id": "BRIEF:CROSS-DEPENDENCIES-001", "seccion": "07.1", "nombre": "Impact Assessment Contract"},
            {"id": "BRIEF:CROSS-DEPENDENCIES-002", "seccion": "07.2", "nombre": "Mandatory Change Reporting"},
            {"id": "BRIEF:CROSS-DEPENDENCIES-003", "seccion": "07.3", "nombre": "Closure Gate"},
            {"id": "BRIEF:HOUSEKEEPING-001", "seccion": "05.1", "nombre": "Housekeeping"},
            {"id": "BRIEF:CORE-ASSETS-001", "seccion": "05.2", "nombre": "Core Assets"},
            {"id": "BRIEF:DISCOVERY-001", "seccion": "05.3", "nombre": "Discovery"},
            {"id": "BRIEF:GATE-LOGIC-001", "seccion": "05.4", "nombre": "Gate Logic"},
            {"id": "BRIEF:CV-PIPELINE-001", "seccion": "05.5", "nombre": "CV Pipeline"},
            {"id": "BRIEF:PURPOSE-SCOPE-001", "seccion": "01.1", "nombre": "Propósito"},
            {"id": "BRIEF:PURPOSE-SCOPE-002", "seccion": "01.2", "nombre": "Alcance"},
            {"id": "BRIEF:PURPOSE-SCOPE-003", "seccion": "01.3", "nombre": "Fuera de Alcance"},
        ],
    },
    {
        "name": "SYSTEM PROMPT",
        "rows": [
            {"id": "SP:BOOTLOADER", "seccion": "01", "nombre": "Operating Specification — Bootstrap de Sesión"},
            {"id": "SP:BOOTLOADER-001", "seccion": "01.1", "nombre": "Consumo de Skills por Familia de Agente"},
            {"id": "SP:SYNC-RULE", "seccion": "02", "nombre": "Sincronización Inicial y Verificación de Versión"},
            {"id": "SP:CONTEXT-INFRASTRUCTURE", "seccion": "04", "nombre": "Referencia — Context Infrastructure (KERNEL:CONTEXT-INFRASTRUCTURE)"},
            {
                "id": "SP:DIGITAL-ID-CARD",
                "lookup_ids": ["SP:DIGITAL-ID-CARD-001", "SP:DIGITAL-ID-CARD"],
                "seccion": "03",
                "nombre": "Cédula Digital — rutas de operación y UUIDs"
            },
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


def infer_section_from_id(id_str: str) -> tuple:
    """Infiere la sección y nombre a partir del ID huérfano."""
    prefix = id_str.split(":")[0] if ":" in id_str else ""
    
    # Mapeo de prefijos a secciones del CENSUS_SPEC
    section_map = {
        "KERNEL": "KERNEL",
        "MANUAL": "MANUAL",
        "CANON": "CANON",
        "CAREER_CANON": "CAREER_CANON",
        "SP": "SP",
        "ALIASES": "ALIASES",
        "CHANGELOG": "CHANGELOG",
        "CHANGELOG_ARCHIVO": "CHANGELOG_ARCHIVO",
        "BRIEF": "BRIEF",
    }
    
    section_name = section_map.get(prefix, "UNKNOWN")
    
    # Inferir sección numérica basado en el patrón del ID
    seccion = ""
    nombre = ""
    
    if "-" in id_str:
        parts = id_str.split("-")
        if len(parts) > 1:
            # IDs con sufijo numérico
            base = parts[0]
            suffix = parts[1]
            
            # Intentar inferir sección numérica
            if suffix.isdigit():
                seccion = f"{seccion}.{suffix}" if seccion else suffix
            
            # Generar nombre descriptivo
            if prefix == "KERNEL":
                nombre = f"Subsección {suffix} de {base}"
            elif prefix == "MANUAL":
                nombre = f"Subsección {suffix} de {base}"
            else:
                nombre = f"{base} — {suffix}"
    else:
        # IDs sin sufijo numérico (encabezados principales)
        if prefix == "KERNEL":
            nombre = f"Sección principal de {id_str}"
        elif prefix == "MANUAL":
            nombre = f"Sección principal de {id_str}"
        else:
            nombre = id_str
    
    return section_name, seccion, nombre


def generate_census_spec_additions(orphans: dict) -> str:
    """Genera el código Python para agregar IDs huérfanos al CENSUS_SPEC."""
    if not orphans:
        return "# No hay IDs huérfanos para agregar\n"
    
    additions = []
    additions.append("# IDs huérfanos detectados - agregar a CENSUS_SPEC")
    additions.append("# Generado automáticamente por generate_census.py --auto-fix-orphans")
    additions.append("")
    
    # Agrupar por sección
    by_section = {}
    for id_str, entry in orphans.items():
        section_name, seccion, nombre = infer_section_from_id(id_str)
        if section_name not in by_section:
            by_section[section_name] = []
        by_section[section_name].append({
            "id": id_str,
            "seccion": seccion,
            "nombre": nombre,
            "entry": entry
        })
    
    for section_name, items in sorted(by_section.items()):
        if section_name == "UNKNOWN":
            continue
        additions.append(f"# {section_name}")
        for item in items:
            additions.append(f'{{"id": "{item["id"]}", "seccion": "{item["seccion"]}", "nombre": "{item["nombre"]}"}},')
        additions.append("")
    
    return "\n".join(additions)


def find_census_spec_end(content: str) -> int | None:
    """Encuentra el índice del ']' que cierra CENSUS_SPEC balanceando profundidad,
    inmune a corchetes anidados (ej. campos tipo 'lookup_ids': [...])."""
    start_marker = "CENSUS_SPEC = ["
    start = content.find(start_marker)
    if start == -1:
        return None
    bracket_start = start + len(start_marker) - 1
    depth = 0
    for i in range(bracket_start, len(content)):
        ch = content[i]
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return i + 1
    return None


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
    
    # Generar el código para agregar
    additions_code = generate_census_spec_additions(orphans)
    
    if response in ['n']:
        print("\n--- Código generado (no aplicado) ---")
        print(additions_code)
        print("--- Fin del código ---")
        return False
    
    if response in ['y']:
        # Leer el archivo actual
        script_path = Path(__file__).resolve()
        current_content = script_path.read_text(encoding="utf-8")
        
        # Encontrar el final real del CENSUS_SPEC (balanceo de corchetes, no regex)
        census_spec_end = find_census_spec_end(current_content)
        
        if census_spec_end is not None:
            new_content = current_content[:census_spec_end] + "\n    # Auto-generated orphan IDs\n" + additions_code + current_content[census_spec_end:]
            
            script_path.write_text(new_content, encoding="utf-8")
            print(f"✓ IDs agregados a {script_path}")
            print("  Revisa el archivo para verificar la inserción y ajustar secciones si es necesario.")
            return True
        else:
            print("✗ Error: No se pudo encontrar el cierre real de CENSUS_SPEC en el archivo.")
            return False
    
    print("✗ Respuesta no reconocida. Cancelado.")
    return False


def update_notion_census_page(page_id: str, markdown_content: str) -> bool:
    """Actualiza la página de Notion especificada con el contenido del census."""
    try:
        # Convertir el markdown a bloques de Notion
        blocks = markdown_to_notion_blocks(markdown_content)
        
        # Primero obtener los bloques actuales para reemplazar
        url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code != 200:
            print(f"✗ Error al obtener bloques actuales: {response.status_code}")
            return False
        
        current_blocks = response.json().get("results", [])
        
        # Si hay bloques, eliminarlos todos
        if current_blocks:
            for block in current_blocks:
                delete_url = f"https://api.notion.com/v1/blocks/{block['id']}"
                requests.delete(delete_url, headers=HEADERS)
        
        # Agregar los nuevos bloques
        append_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        
        # Notion API tiene límite de 100 bloques por request
        for i in range(0, len(blocks), 100):
            batch = blocks[i:i+100]
            payload = {"children": batch}
            
            response = requests.patch(append_url, headers=HEADERS, json=payload)
            
            if response.status_code != 200:
                print(f"✗ Error al agregar bloques (batch {i//100 + 1}): {response.status_code}")
                print(f"  Response: {response.text}")
                return False
        
        print(f"✓ Página de Notion actualizada exitosamente")
        return True
        
    except Exception as e:
        print(f"✗ Error al actualizar Notion: {e}")
        return False


def markdown_to_notion_blocks(markdown: str) -> list:
    """Convierte contenido markdown a bloques de Notion."""
    blocks = []
    lines = markdown.split('\n')
    
    for line in lines:
        if not line.strip():
            continue
            
        # Encabezados
        if line.startswith('## '):
            text = line[3:].strip()
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                }
            })
        elif line.startswith('### '):
            text = line[4:].strip()
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                }
            })
        # Tablas (simplificado - Notion no soporta tablas nativamente en API)
        elif line.startswith('|'):
            # Para tablas, convertirlas a texto con formato
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": line}}]
                }
            })
        # Separadores
        elif line.strip() == '---':
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })
        # Texto normal
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": line}}]
                }
            })
    
    return blocks


def sync_to_notion(page_id: str, markdown_content: str) -> bool:
    """Sincroniza el census a Notion con confirmación del usuario."""
    print("\n" + "=" * 52)
    print("  SINCRONIZACIÓN A NOTION")
    print("=" * 52)
    print(f"  Página ID: {page_id}")
    print(f"  Tamaño del contenido: {len(markdown_content)} caracteres")
    print()
    print("  ¿Deseas actualizar la página de Notion con el census actual?")
    print("  [Y/y] = Sí, actualizar Notion")
    print("  [N/n] = No, cancelar")
    print("=" * 52)
    
    response = input("  Tu elección: ").strip().lower()
    
    if response in ['y']:
        return update_notion_census_page(page_id, markdown_content)
    else:
        print("✓ Cancelado. No se actualizó Notion.")
        return False

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
            print(f"      plain={e.get('plain')!r}")
    print("\n" + "#" * 52)


if __name__ == "__main__":
    debug_ids = []
    auto_fix_orphans_flag = False
    sync_to_notion_flag = False
    notion_page_id = "394938befc4281e6a381e3869e60d89d"  # ID default proporcionado
    
    if "--debug-id" in sys.argv:
        idx = sys.argv.index("--debug-id")
        debug_ids = sys.argv[idx + 1:]
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

    print(f"\nV-ID-CENSUS Generator v3.1")
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
    print(f"  IDs con Sección hardcodeada (sin heading 'N' detectable en vivo): {len(hardcoded_fallbacks)}")
    if hardcoded_fallbacks:
        print("  ⚠ Revisar manualmente si el número/letra en CENSUS_SPEC sigue vigente:")
        for uid in hardcoded_fallbacks:
            print(f"    - {uid}")
    print("=" * 52)
    
    # Auto-fix orphans si se solicita
    if auto_fix_orphans_flag:
        if auto_fix_orphans(orphans):
            # Si se agregaron IDs, regenerar el census
            print("\nRegenerando census con IDs actualizados...")
            known_ids = known_ids_from_spec()
            orphans = find_orphan_ids(link_index, known_ids)
            md, unresolved, hardcoded_fallbacks = render_markdown(link_index, orphans)
            output.write_text(md, encoding="utf-8")
            print("✓ Census regenerado.")
    
    # Sync a Notion si se solicita
    if sync_to_notion_flag:
        sync_to_notion(notion_page_id, md)

    if incomplete_docs:
        print("\n  ⚠️  ADVERTENCIA: CENSUS INCOMPLETO")
        print("  Los siguientes documentos NO se indexaron completos")
        for entry in incomplete_docs:
            print(f"    - {entry['doc']}: {entry['error']}")

    print(f"\nExportado a: {output.resolve()}")
