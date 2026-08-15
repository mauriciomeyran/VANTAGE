# CONTRATO DE SESIÓN — MIGRACIÓN DE HEADINGS A FORMATO CANÓNICO VANTAGE
**Versión del contrato:** 1.0 · **Fecha:** 2026-07-25
**Emisor:** Claude (Anthropic), bajo instrucción explícita del operador (Mauricio Meyrán)
**Ejecutor:** [Mistral / Grok / Littlebird — completar antes de despachar]
**Propósito:** ejecutar la escritura real en Notion de la migración de headings aprobada en `DRY_RUN_migracion_headings.md`, documento por documento, con verificación obligatoria y sin margen de interpretación.

---

## 0. LECTURA OBLIGATORIA ANTES DE EMPEZAR

Este contrato es la ÚNICA fuente de instrucciones para esta tarea. No se debe:
- inferir, generalizar, ni "mejorar" ningún heading más allá de lo que este contrato especifica línea por línea;
- tratar ninguna fila de las tablas de este contrato como sugerencia — son literales, carácter por carácter;
- proceder al documento N+1 sin haber completado el GATE del documento N;
- reportar éxito sin haber ejecutado el paso de verificación de la Sección 4.

Si algo en este contrato es ambiguo, contradictorio, o no cubre un caso que aparece en el documento real: **DETENTE y reporta la ambigüedad al operador**, en lugar de decidir por tu cuenta. Una decisión no autorizada, aunque parezca razonable, invalida toda la operación bajo `SP:CONSISTENCY` (protocolo de esta suite).

---

## 1. FORMATO CANÓNICO DE DESTINO

**Heading de sección padre** (siempre 2 líneas consecutivas de heading nivel 2, `##`):
```
## NN PREFIX:KEY
## Título Normalizado en Español
```

**Heading de subsección** (mismo patrón, sufijo decimal SIN padding):
```
## NN.N PREFIX:KEY-NNN
## Título Normalizado en Español
```

**Reglas de padding:**
- Número de sección padre: SIEMPRE 2 dígitos (`01`, `02`, ... `21`).
- Sufijo decimal de subsección: SIN padding (`08.1`, nunca `08.01`).

**Símbolo `§`:** eliminado por completo. No debe aparecer en ningún heading nuevo.

**Regla de idioma:** el ID (`PREFIX:KEY`) va siempre en inglés. El título normalizado (segunda línea) va siempre en español.

**Regla de auto-enlace (NO NEGOCIABLE):** el heading de definición NUNCA se convierte en hipervínculo, ni siquiera si el ID ya tiene una entrada en el mapa de links. Es texto plano, siempre. Esta regla existe independientemente de cualquier otro script o proceso que puedas conocer — ignora cualquier lógica previa que sugiera lo contrario.

**Excluidos de este contrato (NO TOCAR):**
- `KERNEL:AUDIENCE-SCOPE` y `CANON:AUDIENCE-SCOPE` — quedan como heading bare, sin número de sección, sin cambio de forma. Son metadata de audiencia, no secciones de contenido navegable.
- Change Log — es un registro cronológico, no tiene TOC ni headings de sección numerada. No se toca en absoluto.
- Cualquier subsección de Manual §8 marcada en la Sección 3.2 de este contrato como "fuera de alcance" (ej. 8.1, 8.3, 8.4, 8.5) — no tienen ID hoy y este contrato no les asigna uno.

---

## 2. REGLA DE ORO DE EJECUCIÓN — UN DOCUMENTO A LA VEZ

El orden de ejecución es:

1. **ALIASES** (8 secciones — el más pequeño, sirve para validar el proceso)
2. **NAVIGATION BRIEF** (11 secciones)
3. **SYSTEM PROMPT** (12 secciones, incluye 2 correcciones estructurales)
4. **CAREER CANON** (8 secciones + ~30 subsecciones)
5. **KERNEL** (17 secciones + ~34 subsecciones, incluye 1 fusión estructural)
6. **MANUAL** (21 secciones, el más grande)

**No se avanza al documento siguiente sin haber completado el GATE (Sección 4) del documento actual y haber recibido `APROBAR_WRITE` explícito del operador para ese documento específico.** `APROBAR_WRITE` de un documento NO autoriza los siguientes — cada documento requiere su propia aprobación.

---

## 3. TABLAS DE MIGRACIÓN — LITERALES, CARÁCTER POR CARÁCTER

### 3.1 ALIASES (8 secciones)

| # | ID actual | ID nuevo | Heading actual (buscar EXACTO) | Heading nuevo (escribir EXACTO, 2 líneas) |
|---|---|---|---|---|
| 01 | ALIASES:SESSION-CYCLE | *(sin cambio)* | `## §1 ALIASES:SESSION-CYCLE` | `## 01 ALIASES:SESSION-CYCLE` / `## Session Cycle` |
| 02 | ALIASES:L0-RUNTIME | *(sin cambio)* | `## §2 ALIASES:L0-RUNTIME` | `## 02 ALIASES:L0-RUNTIME` / `## L0 · VANTAGE Runtime` |
| 03 | ALIASES:L1L2-DISCOVERY | *(sin cambio)* | `## §3 ALIASES:L1L2-DISCOVERY` | `## 03 ALIASES:L1L2-DISCOVERY` / `## L1/L2 · Discovery (Lunes)` |
| 04 | ALIASES:L3-PASSIVE-INTAKE | *(sin cambio)* | `## §4 ALIASES:L3-PASSIVE-INTAKE` | `## 04 ALIASES:L3-PASSIVE-INTAKE` / `## L3 · Passive Intake` |
| 05 | ALIASES:L4-VERSION-CONTROL | *(sin cambio)* | `## §5 ALIASES:L4-VERSION-CONTROL` | `## 05 ALIASES:L4-VERSION-CONTROL` / `## L4 · Version Control & Documentación` |
| 06 | ALIASES:DASHBOARD | *(sin cambio)* | `## §6 ALIASES:DASHBOARD` | `## 06 ALIASES:DASHBOARD` / `## Dashboard (Martes — Recuperación)` |
| 07 | ALIASES:CV-PIPELINE | *(sin cambio)* | `## §7 ALIASES:CV-PIPELINE` | `## 07 ALIASES:CV-PIPELINE` / `## CV Pipeline (Miércoles)` |
| 08 | *(sin ID — gap confirmado)* | **ALIASES:DEDUP** (nuevo) | `# 8 — Dedup & Oportunidades` | `## 08 ALIASES:DEDUP` / `## Dedup & Oportunidades` |

### 3.2 NAVIGATION BRIEF (11 secciones)

| # | ID | Heading actual | Heading nuevo |
|---|---|---|---|
| 01 | BRIEF:001 | `## §1 BRIEF:001` | `## 01 BRIEF:001` / *(título ya existe en el documento, en español — conservar tal cual está, solo aplicar el nuevo formato de 2 líneas)* |
| 02 | BRIEF:002 | `## §2 BRIEF:002` | `## 02 BRIEF:002` / *(conservar título existente)* |
| 03 | BRIEF:003 | `## §3 BRIEF:003` | `## 03 BRIEF:003` / *(conservar título existente)* |
| 04 | BRIEF:004 | `## §4 BRIEF:004` | `## 04 BRIEF:004` / *(conservar título existente)* |
| 05 | BRIEF:005 | `## §5 BRIEF:005` | `## 05 BRIEF:005` / *(conservar título existente)* |
| 06 | BRIEF:006 | `## §6 BRIEF:006` | `## 06 BRIEF:006` / *(conservar título existente)* |
| 07 | BRIEF:007 | `## §7 BRIEF:007` | `## 07 BRIEF:007` / *(conservar título existente)* |
| 08 | BRIEF:008 | `## §8 BRIEF:008` | `## 08 BRIEF:008` / *(conservar título existente)* |
| 09 | BRIEF:009 | `## §9 BRIEF:009` | `## 09 BRIEF:009` / *(conservar título existente)* |
| 10 | BRIEF:010 | `## §10 BRIEF:010` | `## 10 BRIEF:010` / *(conservar título existente)* |
| 11 | BRIEF:011 | `## §11 BRIEF:011` | `## 11 BRIEF:011` / *(conservar título existente)* |

**Nota de ejecución para Brief:** los títulos de sección de este documento ya están en español y no requieren traducción — solo eliminar el `§`, aplicar padding de 2 dígitos, y separar en 2 líneas si no lo están ya. Confirma el texto exacto del título actual antes de reescribir; no lo cambies.

### 3.3 SYSTEM PROMPT (12 secciones — incluye 2 correcciones estructurales 🔶 APROBADAS)

| # | ID actual | ID nuevo | Heading actual | Heading nuevo |
|---|---|---|---|---|
| 01 | SP:BOOTSTRAP-001 | *(sin cambio)* | `## §1 — SP:BOOTSTRAP-001` | `## 01 SP:BOOTSTRAP-001` / `## Operating Specification` |
| 02 | SP:SYNC-RULE | *(sin cambio)* | `## §2 SP:SYNC-RULE` | `## 02 SP:SYNC-RULE` / `## Sincronización Inicial` |
| 03 | SP:CEDULA-DIGITAL | **SP:DIGITAL-ID-CARD-001** | `## §3 — SP:CEDULA-DIGITAL` | `## 03 SP:DIGITAL-ID-CARD-001` / `## Cédula Digital` |
| 04 | KERNEL:SCOPE *(stub)* | **SP:CONTEXT-INFRASTRUCTURE-REF** | `## §4 KERNEL:SCOPE` | `## 04 SP:CONTEXT-INFRASTRUCTURE-REF` / `## Referencia — Consultar en Technical Kernel` |
| 05 | KERNEL:DATA-FLOW *(stub)* | **SP:DATA-FLOW-REF** | `## §5 KERNEL:DATA-FLOW` | `## 05 SP:DATA-FLOW-REF` / `## Referencia — Consultar en Technical Kernel` |
| 06 | SP:TRIGGERS | *(sin cambio)* | `## §6 SP:TRIGGERS` | `## 06 SP:TRIGGERS` / `## Triggers Operativos de VANTAGE` |
| 07 | KERNEL:CV-GOLDEN-RULES *(stub)* | **SP:CV-GOLDEN-RULES-REF** | `## §7 KERNEL:CV-GOLDEN-RULES` | `## 07 SP:CV-GOLDEN-RULES-REF` / `## Referencia — Consultar en Technical Kernel` |
| 08 | SP:SCHEMA | *(sin cambio)* | `## §8 SP:SCHEMA` | `## 08 SP:SCHEMA` / `## Schema — Trackers (Class A/B)` |
| 09 | SP:CONSISTENCY *(duplicado)* | **SP:MCP-ROUTING-NOTES** | `## §9 SP:CONSISTENCY` | `## 09 SP:MCP-ROUTING-NOTES` / `## Notas Operativas de Ruteo MCP/Terminal` |
| 10 | SP:ID-CONNECTORS | *(sin cambio)* | `## §10 SP:ID-CONNECTORS` | `## 10 SP:ID-CONNECTORS` / `## ID Connectors — Esquema PREFIX:NOMBRE-SECCION` |
| 11 | SP:CONSISTENCY *(el real — verificado por grep, todas las referencias cruzadas del sistema apuntan aquí)* | *(sin cambio)* | `## §11 — SP:CONSISTENCY` | `## 11 SP:CONSISTENCY` / `## Reglas de Consistencia Documental` |
| 12 | SP:VERSION-CHECK-TOOL | *(sin cambio)* | `## §12 SP:VERSION-CHECK-TOOL` | `## 12 SP:VERSION-CHECK-TOOL` / `## Herramienta de Verificación de Versión de Bajo Costo` |

**ADVERTENCIA CRÍTICA para §9 y §11:** estos dos headings comparten hoy el mismo texto (`SP:CONSISTENCY`) pero son secciones de contenido completamente distinto. NO los confundas ni los intercambies. §9 es la nota corta sobre routing MCP/Terminal (Notion SQL bloqueado, etc.). §11 es la regla de 5 pasos sobre reportar discrepancias antes de escribir. Verifica el CONTENIDO de cada bloque antes de decidir cuál es cuál — no te guíes solo por el número de posición, por si el documento cambió de orden entre la redacción de este contrato y tu ejecución.

### 3.4 CAREER CANON (8 secciones + subsecciones)

`CANON:AUDIENCE-SCOPE` — **NO TOCAR**, ver Sección 1 de este contrato (exclusiones).

| # | ID | Heading actual | Heading nuevo |
|---|---|---|---|
| 01 | CANON:PROFILE-001 | `## §1 CANON:PROFILE-001` | `## 01 CANON:PROFILE-001` / `## A. Professional Profile` |
| 02 | CANON:SKILLS-001 | `## §2 CANON:SKILLS-001` | `## 02 CANON:SKILLS-001` / `## B. Skills Canon` |
| 03 | CANON:EXPERIENCE-001 | `## §3 CANON:EXPERIENCE-001` | `## 03 CANON:EXPERIENCE-001` / `## D. Experience Records` |
| 03.1 | CANON:EXPERIENCE-C01 | `## §3.1 CANON:EXPERIENCE-C01` | `## 03.1 CANON:EXPERIENCE-C01` / `## C01 · L'Oréal Luxe México` |
| 03.2 | CANON:EXPERIENCE-C02 | `## §3.2 CANON:EXPERIENCE-C02` | `## 03.2 CANON:EXPERIENCE-C02` / `## C02 · Bisonte Experiential Marketing` |
| 03.3 | CANON:EXPERIENCE-C03 | `## §3.3 CANON:EXPERIENCE-C03` | `## 03.3 CANON:EXPERIENCE-C03` / `## C03 · Levi Strauss & Co. (Dockers)` |
| 03.4 | CANON:EXPERIENCE-C04 | `## §3.4 CANON:EXPERIENCE-C04` | `## 03.4 CANON:EXPERIENCE-C04` / `## C04 · Aéropostale México` |
| 03.5 | CANON:EXPERIENCE-C05 | `## §3.5 CANON:EXPERIENCE-C05` | `## 03.5 CANON:EXPERIENCE-C05` / `## C05 · El Palacio de Hierro (ALDO Group)` |
| 04 | CANON:ACHIEVEMENTS-001 | `## §4 CANON:ACHIEVEMENTS-001` | `## 04 CANON:ACHIEVEMENTS-001` / `## H. Achievement Library` |
| 05 | CANON:KPIS-001 | `## §5 CANON:KPIS-001` | `## 05 CANON:KPIS-001` / `## I. Core KPIs` |
| 05.1–05.8 | CANON:KPI-001..008 | `## §5.N CANON:KPI-00N` | `## 05.N CANON:KPI-00N` *(título sin cambio — ya es corto: "KPI 01", "KPI 02", etc., verificar contra el documento real)* |
| 06 | CANON:FACTS-001 | `## §6 CANON:FACTS-001` | `## 06 CANON:FACTS-001` / `## J. Canonical Facts` |
| 06.1–06.11 | CANON:FACT-001..008, CANON:UF-001..003 | `## §6.N CANON:...` | `## 06.N CANON:...` *(título sin cambio, verificar contra el documento real)* |
| 07 | CANON:POSITIONING-001 | `## §7 CANON:POSITIONING-001` | `## 07 CANON:POSITIONING-001` / `## K. Positioning Modes` |
| 07.1–07.4 | CANON:POSITIONING-N1..N4 | `## §7.N CANON:POSITIONING-NN` | `## 07.N CANON:POSITIONING-NN` *(título sin cambio)* |
| 08 | CANON:OUTPUT-CONTRACT | `## §8 CANON:OUTPUT-CONTRACT` | `## 08 CANON:OUTPUT-CONTRACT` / `## Contrato de Entregable` |
| 08.1 | CANON:OUTPUT-CONTRACT-001 | `## §8.1 CANON:OUTPUT-CONTRACT-001` | `## 08.1 CANON:OUTPUT-CONTRACT-001` / `## Golden Skeleton` |
| 08.2 | CANON:OUTPUT-CONTRACT-002 | `## §8.2 CANON:OUTPUT-CONTRACT-002` | `## 08.2 CANON:OUTPUT-CONTRACT-002` / `## Figma Tags` |
| 08.3 | CANON:OUTPUT-CONTRACT-003 | `## §8.3 CANON:OUTPUT-CONTRACT-003` | `## 08.3 CANON:OUTPUT-CONTRACT-003` / `## Tag Registry` |
| 08.4 | CANON:OUTPUT-CONTRACT-004 | `## §8.4 CANON:OUTPUT-CONTRACT-004` | `## 08.4 CANON:OUTPUT-CONTRACT-004` / `## Positioning Modes (Aplicación en Output)` |

**RECORDATORIO ESPECÍFICO PARA ESTE DOCUMENTO:** este es el documento que originó toda esta migración — su TOC (tabla "Índice del Career Canon") nunca contuvo el ID real, solo el nombre de sección en texto libre (ej. "OUTPUT CONTRACT" en vez de "CANON:OUTPUT-CONTRACT"). Como parte de este GATE, la tabla TOC de Career Canon DEBE actualizarse para incluir el ID real de cada fila en formato clickeable, según el formato de 4 columnas: `# | PREFIX:KEY [clickable] | Heading Normalizado | Portion`. Sin esto, la migración de headings no resuelve el problema original.

### 3.5 KERNEL (17 secciones + ~34 subsecciones — incluye fusión estructural 🔶 APROBADA)

| # | ID actual | ID nuevo | Heading actual | Heading nuevo |
|---|---|---|---|---|
| 01 | KERNEL:PURPOSE | *(sin cambio)* | `## §1 — KERNEL:PURPOSE` | `## 01 KERNEL:PURPOSE` / `## Propósito del Sistema` |
| 02 | KERNEL:FAIL-PHILOSOPHY | *(sin cambio)* | `## §2 — KERNEL:FAIL-PHILOSOPHY` | `## 02 KERNEL:FAIL-PHILOSOPHY` / `## Filosofía de Fallo` |
| 03 | KERNEL:DOCUMENTATION | *(sin cambio)* | `## §3 — KERNEL:DOCUMENTATION (L0)` | `## 03 KERNEL:DOCUMENTATION` / `## Documentación y Gobernanza (L0)` |
| 03.1 | KERNEL:DOCUMENTATION-001 | *(sin cambio)* | `### §3.1 — KERNEL:DOCUMENTATION-001` | `## 03.1 KERNEL:DOCUMENTATION-001` / `## Contrato Canónico de ID de Documento` |
| 03.2 | KERNEL:DOCUMENTATION-002 | *(sin cambio)* | `### §3.2 — KERNEL:DOCUMENTATION-002` | `## 03.2 KERNEL:DOCUMENTATION-002` / `## Normalización Documental de IDs Legacy` |
| 03.3 | KERNEL:DOCUMENTATION-003 | *(sin cambio)* | `### §3.3 — KERNEL:DOCUMENTATION-003` | `## 03.3 KERNEL:DOCUMENTATION-003` / `## L0 — VANTAGE Runtime` |
| 03.4 | KERNEL:DOCUMENTATION-004 | *(sin cambio)* | `### §3.4 — KERNEL:DOCUMENTATION-004` | `## 03.4 KERNEL:DOCUMENTATION-004` / `## L0-Bootstrap — Capa de Gobernanza Dinámica` |
| 03.5 | KERNEL:DOCUMENTATION-005 | *(sin cambio)* | `### §3.5 — KERNEL:DOCUMENTATION-005` | `## 03.5 KERNEL:DOCUMENTATION-005` / `## Convención de Anuncio de Skills` |
| 03.6 | KERNEL:DOCUMENTATION-006 | *(sin cambio)* | `### §3.6 — KERNEL:DOCUMENTATION-006` | `## 03.6 KERNEL:DOCUMENTATION-006` / `## Contrato de health_check.py` |
| 03.7 | KERNEL:DOCUMENTATION-007 | *(sin cambio)* | `### §3.7 — KERNEL:DOCUMENTATION-007` | `## 03.7 KERNEL:DOCUMENTATION-007` / `## Herramienta de Verificación de Versión` |
| 03.8 | KERNEL:DOCUMENTATION-008 | *(sin cambio)* | `### §3.8 — KERNEL:DOCUMENTATION-008` | `## 03.8 KERNEL:DOCUMENTATION-008` / `## Sincronización Obligatoria del ID Census` |
| 03.9 | KERNEL:DOCUMENTATION-009 | *(sin cambio)* | `### §3.9 — KERNEL:DOCUMENTATION-009` | `## 03.9 KERNEL:DOCUMENTATION-009` / `## Session Ledger` |
| 03.10 | KERNEL:DOCUMENTATION-010 | *(sin cambio)* | `### §3.10 — KERNEL:DOCUMENTATION-010` | `## 03.10 KERNEL:DOCUMENTATION-010` / `## Documentación Transversal — Contrato de Integridad` |
| 04 | KERNEL:ARCHITECTURE | *(sin cambio)* | `## §4 — KERNEL:ARCHITECTURE` | `## 04 KERNEL:ARCHITECTURE` / `## Arquitectura de Cuatro Capas` |
| 04.1 | KERNEL:ARCHITECTURE-L1 | *(sin cambio)* | `### KERNEL:ARCHITECTURE-L1 — Active Recon` | `## 04.1 KERNEL:ARCHITECTURE-L1` / `## L1 — Active Recon` |
| 04.2 | KERNEL:ARCHITECTURE-L2 | *(sin cambio)* | `### KERNEL:ARCHITECTURE-L2 — Strategic Search` | `## 04.2 KERNEL:ARCHITECTURE-L2` / `## L2 — Búsqueda Estratégica` |
| 04.3 | KERNEL:ARCHITECTURE-L3 | *(sin cambio)* | `### KERNEL:ARCHITECTURE-L3 — Passive Intake` | `## 04.3 KERNEL:ARCHITECTURE-L3` / `## L3 — Passive Intake` |
| 04.4 | KERNEL:ARCHITECTURE-L4 | *(sin cambio)* | `### KERNEL:ARCHITECTURE-L4 — Version Control...` | `## 04.4 KERNEL:ARCHITECTURE-L4` / `## L4 — Control de Versiones e Infraestructura` |
| 05 | KERNEL:OWNERSHIP | *(sin cambio)* | `## §5 — KERNEL:OWNERSHIP` | `## 05 KERNEL:OWNERSHIP` / `## División de Responsabilidades AI/Python` |
| 05.1 | KERNEL:OWNERSHIP-001 | *(sin cambio)* | `### KERNEL:OWNERSHIP-001 — AI Component` | `## 05.1 KERNEL:OWNERSHIP-001` / `## Componente AI` |
| 05.2 | KERNEL:OWNERSHIP-002 | *(sin cambio)* | `### KERNEL:OWNERSHIP-002 — Python Component` | `## 05.2 KERNEL:OWNERSHIP-002` / `## Componente Python` |
| 06 | KERNEL:DASHBOARD-CHECKLIST-ARCH | *(sin cambio)* | `## §6 — KERNEL:DASHBOARD-CHECKLIST-ARCH` | `## 06 KERNEL:DASHBOARD-CHECKLIST-ARCH` / `## Arquitectura Dashboard/Checklist` |
| 07 | KERNEL:SCHEMA | *(sin cambio)* | `## §7 — KERNEL:SCHEMA` | `## 07 KERNEL:SCHEMA` / `## Modelo de Datos y Ownership` |
| 07.1 | KERNEL:SCHEMA-001 | *(sin cambio)* | `### KERNEL:SCHEMA-001 — Class A vs Class B` | `## 07.1 KERNEL:SCHEMA-001` / `## Class A vs Class B` |
| 07.2 | KERNEL:SCHEMA-002 | *(sin cambio)* | `### KERNEL:SCHEMA-002 — Restricción del Sistema` | `## 07.2 KERNEL:SCHEMA-002` / `## Restricción del Sistema` |
| 07.3 | KERNEL:SCHEMA-003 | *(sin cambio)* | `### KERNEL:SCHEMA-003 — Fuente como Campo Especial` | `## 07.3 KERNEL:SCHEMA-003` / `## Fuente como Campo Especial` |
| 07.4 | KERNEL:SCHEMA-004 | *(sin cambio)* | `### KERNEL:SCHEMA-004 — Entity Format` | `## 07.4 KERNEL:SCHEMA-004` / `## Formato de Entidad` |
| 07.5 | KERNEL:SCHEMA-005 | *(sin cambio)* | `### KERNEL:SCHEMA-005 — Contrato de Resolución: 4 Pasos` | `## 07.5 KERNEL:SCHEMA-005` / `## Contrato de Resolución: 4 Pasos` |
| 07.6 | KERNEL:SCHEMA-006 | *(sin cambio)* | `### KERNEL:SCHEMA-006 — APROBAR_WRITE: Alcance` | `## 07.6 KERNEL:SCHEMA-006` / `## APROBAR_WRITE: Alcance` |
| 07.7 | KERNEL:SCHEMA-007 | *(sin cambio)* | `### KERNEL:SCHEMA-007 — Acceptance Audit` | `## 07.7 KERNEL:SCHEMA-007` / `## Auditoría de Aceptación` |
| 08 | KERNEL:TRACKER-SCHEMA | *(sin cambio)* | `## §8 — KERNEL:TRACKER-SCHEMA` | `## 08 KERNEL:TRACKER-SCHEMA` / `## Bug Tracker y Tasks Tracker` |
| 08.1 | KERNEL:TRACKER-SCHEMA-001 | *(sin cambio)* | `### KERNEL:TRACKER-SCHEMA-001 — Alcance` | `## 08.1 KERNEL:TRACKER-SCHEMA-001` / `## Alcance` |
| 08.2 | KERNEL:TRACKER-SCHEMA-002 | *(sin cambio)* | `### KERNEL:TRACKER-SCHEMA-002 — Niveles de Prioridad` | `## 08.2 KERNEL:TRACKER-SCHEMA-002` / `## Niveles de Prioridad` |
| 09 | KERNEL:GATE-DECISION | *(sin cambio)* | `## §9 — KERNEL:GATE-DECISION` | `## 09 KERNEL:GATE-DECISION` / `## Lógica de Gate Decision` |
| 09.1 | KERNEL:GATE-DECISION-001 | *(sin cambio)* | `### §9.1 — KERNEL:GATE-DECISION-001 — Bypass` | `## 09.1 KERNEL:GATE-DECISION-001` / `## Bypass` |
| 09.2 | KERNEL:GATE-DECISION-002 | *(sin cambio)* | `### §9.2 — ...002 — Lógica Estándar` | `## 09.2 KERNEL:GATE-DECISION-002` / `## Lógica Estándar` |
| 09.3 | KERNEL:GATE-DECISION-003 | *(sin cambio)* | `### §9.3 — ...003 — Resolución de REVIEW_NEEDED` | `## 09.3 KERNEL:GATE-DECISION-003` / `## Resolución de REVIEW_NEEDED` |
| 09.4 | KERNEL:GATE-DECISION-004 | *(sin cambio)* | `### §9.4 — ...004 — Por Qué los Gates Son Deterministas` | `## 09.4 KERNEL:GATE-DECISION-004` / `## Por Qué los Gates Son Deterministas` |
| 09.5 | KERNEL:GATE-DECISION-005 | *(sin cambio)* | `### §9.5 — ...005 — Flujo de Recuperación BLOCKED` | `## 09.5 KERNEL:GATE-DECISION-005` / `## Flujo de Recuperación BLOCKED` |
| 09.6 | KERNEL:GATE-DECISION-006 | *(sin cambio)* | `### §9.6 — ...006 — REJECTED (Post-Aplicación)` | `## 09.6 KERNEL:GATE-DECISION-006` / `## REJECTED (Post-Aplicación)` |
| 09.7 | KERNEL:GATE-DECISION-007 | *(sin cambio)* | `### §9.7 — ...007 — Ejecución Automática de Archivado` | `## 09.7 KERNEL:GATE-DECISION-007` / `## Ejecución Automática de Archivado` |
| 09.8 | KERNEL:GATE-DECISION-008 | *(sin cambio)* | `### §9.8 — ...008 — Capas de Evaluación: Técnica vs. Negocio` | `## 09.8 KERNEL:GATE-DECISION-008` / `## Capas de Evaluación: Técnica vs. Negocio` |
| 09.9 | KERNEL:GATE-DECISION-009 | *(sin cambio)* | `### §9.9 — ...009 — Escalamiento de Pendientes a Tickets` | `## 09.9 KERNEL:GATE-DECISION-009` / `## Escalamiento de Pendientes a Tickets` |
| 10 | KERNEL:CV-GOLDEN-RULES | *(sin cambio)* | `## §10 — KERNEL:CV-GOLDEN-RULES` | `## 10 KERNEL:CV-GOLDEN-RULES` / `## Golden Rules — Límites de Ejecución` |
| 11 | KERNEL:TRIGGERS | *(sin cambio)* | `## §11 — KERNEL:TRIGGERS` | `## 11 KERNEL:TRIGGERS` / `## Contratos de Ejecución del AI Component` |
| 11.1 | KERNEL:TRIGGER-001 | *(sin cambio)* | `### KERNEL:TRIGGER-001 — FEED` | `## 11.1 KERNEL:TRIGGER-001` / `## FEED` |
| 11.2 | KERNEL:TRIGGER-002 | *(sin cambio)* | `### KERNEL:TRIGGER-002 — VL1` | `## 11.2 KERNEL:TRIGGER-002` / `## VL1` |
| 11.3 | KERNEL:TRIGGER-003 | *(sin cambio)* | `### KERNEL:TRIGGER-003 — QA` | `## 11.3 KERNEL:TRIGGER-003` / `## QA` |
| 11.4 | KERNEL:TRIGGER-004 | *(sin cambio)* | `### KERNEL:TRIGGER-004 — DRY RUN` | `## 11.4 KERNEL:TRIGGER-004` / `## DRY RUN` |
| 11.5 | KERNEL:TRIGGER-005 | *(sin cambio)* | `### KERNEL:TRIGGER-005 — SYNC` | `## 11.5 KERNEL:TRIGGER-005` / `## SYNC` |
| 11.6 | KERNEL:TRIGGER-006 | *(sin cambio)* | `### KERNEL:TRIGGER-006 — TOP 3 BY SCORE` | `## 11.6 KERNEL:TRIGGER-006` / `## TOP 3 BY SCORE` |
| 11.7 | KERNEL:TRIGGER-007 | *(sin cambio)* | `### KERNEL:TRIGGER-007 — NEXT ACTION` | `## 11.7 KERNEL:TRIGGER-007` / `## NEXT ACTION` |
| 11.8 | KERNEL:TRIGGER-008 | *(sin cambio)* | `### KERNEL:TRIGGER-008 — FEED (migración)` | `## 11.8 KERNEL:TRIGGER-008` / `## FEED (migración)` |
| 11.9 | KERNEL:TRIGGER-009 | *(sin cambio)* | `### KERNEL:TRIGGER-009 — STATUS` | `## 11.9 KERNEL:TRIGGER-009` / `## STATUS` |
| 12 | KERNEL:CV-PIPELINE | *(sin cambio)* | `## §12 — KERNEL:CV-PIPELINE` | `## 12 KERNEL:CV-PIPELINE` / `## CV Pipeline — Dos Sesiones Obligatorias` |
| 13 | KERNEL:CANON-UPDATE | *(sin cambio)* | `## §13 — KERNEL:CANON-UPDATE` | `## 13 KERNEL:CANON-UPDATE` / `## Trigger de Actualización del Career Canon` |
| 14 | KERNEL:NAMING-CONVENTION | *(sin cambio)* | `## §14 — KERNEL:NAMING-CONVENTION` | `## 14 KERNEL:NAMING-CONVENTION` / `## Convención de Nombres de Outputs` |
| 15 | KERNEL:SCOPE / KERNEL:ROUTING | **KERNEL:CONTEXT-INFRASTRUCTURE** | `## §15 — KERNEL:SCOPE / KERNEL:ROUTING` | `## 15 KERNEL:CONTEXT-INFRASTRUCTURE` / `## Infraestructura de Contexto` |
| 15.1 | KERNEL:SCOPE | **KERNEL:CONTEXT-INFRASTRUCTURE-001** | `### KERNEL:SCOPE — Principio General` | `## 15.1 KERNEL:CONTEXT-INFRASTRUCTURE-001` / `## Scope` |
| 15.2 | KERNEL:ROUTING | **KERNEL:CONTEXT-INFRASTRUCTURE-002** | `### KERNEL:ROUTING — Mecanismo Técnico` | `## 15.2 KERNEL:CONTEXT-INFRASTRUCTURE-002` / `## Routing` |
| 16 | KERNEL:DATA-FLOW | *(sin cambio)* | `## §16 — KERNEL:DATA-FLOW` | `## 16 KERNEL:DATA-FLOW` / `## Flujo de Datos y Escritura` |
| 17 | KERNEL:EVOLUTION | *(sin cambio)* | `## §17 — KERNEL:EVOLUTION` | `## 17 KERNEL:EVOLUTION` / `## Evolución del Sistema` |

**ADVERTENCIA CRÍTICA para §15:** esta es la única fusión estructural real del documento. Antes de escribir, lee el contenido completo de `KERNEL:SCOPE` y `KERNEL:ROUTING` tal como existen hoy. NO los resumas ni los reescribas — solo reorganízalos bajo la nueva jerarquía padre/subsección, preservando el texto de cada uno íntegro dentro de su nueva subsección (15.1 y 15.2 respectivamente).

**IMPORTANTE — referencias cruzadas dentro de Kernel:** el propio Kernel cita `SP:CONSISTENCY` dos veces (con la coletilla "§5", que se refiere al quinto punto de una lista dentro de esa sección, NO a un número de sección distinto). No modifiques esas citas — están correctas y no se ven afectadas por la migración de headings.

### 3.6 MANUAL (21 secciones, la más grande)

| # | ID actual | ID nuevo | Heading actual | Heading nuevo |
|---|---|---|---|---|
| 01 | MANUAL:OBJETIVO-001 | **MANUAL:OBJECTIVE-001** | `## 1. OBJETIVO DE VANTAGE · ID: MANUAL:OBJETIVO-001` | `## 01 MANUAL:OBJECTIVE-001` / `## Objetivo de VANTAGE` |
| 02 | MANUAL:FUNCIONAMIENTO-001 | **MANUAL:HOW-IT-WORKS-001** | `## 2. CÓMO FUNCIONA · ID: MANUAL:FUNCIONAMIENTO-001` | `## 02 MANUAL:HOW-IT-WORKS-001` / `## Cómo Funciona` |
| 03 | MANUAL:FALLO-001 | **MANUAL:FAILURE-PHILOSOPHY-001** | `## 3. FILOSOFÍA DE FALLO... · ID: MANUAL:FALLO-001` | `## 03 MANUAL:FAILURE-PHILOSOPHY-001` / `## Filosofía de Fallo para Operadores` |
| 04 | MANUAL:SETUP-001 | *(sin cambio)* | `## 4. SETUP · ID: MANUAL:SETUP-001` | `## 04 MANUAL:SETUP-001` / `## Setup` |
| 05 | *(sin ID)* | **MANUAL:COLD-START-001** (nuevo — asignado esta sesión) | `## 5. ARRANQUE FRÍO — Checklist de Reactivación` | `## 05 MANUAL:COLD-START-001` / `## Arranque Frío — Checklist de Reactivación` |
| 06 | MANUAL:SESSION-CYCLE-001 | *(sin cambio)* | `## 6. CICLO DE SESIÓN... · ID: MANUAL:SESSION-CYCLE-001` | `## 06 MANUAL:SESSION-CYCLE-001` / `## Ciclo de Sesión — Open/Close` |
| 07 | MANUAL:VCHECKLIST-001 | *(sin cambio)* | `## 7. EL CHECKLIST... · ID: MANUAL:VCHECKLIST-001` | `## 07 MANUAL:VCHECKLIST-001` / `## El Checklist y las Interfaces Compartidas` |
| 08 | MANUAL:FLUJO-001 | **MANUAL:WEEKLY-FLOW-001** | `## 8. FLUJO SEMANAL... · ID: MANUAL:FLUJO-001` | `## 08 MANUAL:WEEKLY-FLOW-001` / `## Flujo Semanal de Operación` |
| — | *(sin ID)* | **FUERA DE ALCANCE — NO TOCAR** | `### 8.1 LUNES — Búsqueda Activa Completa` | *(sin cambio — este contrato no asigna ID a subsecciones de §8 salvo 8.2, ver abajo)* |
| 08.2 | MANUAL:DASHBOARD-001 | *(sin cambio)* | `### 8.2 MARTES... · ID: MANUAL:DASHBOARD-001` | `## 08.2 MANUAL:DASHBOARD-001` / `## Martes — Recuperación y Dashboard` |
| — | *(sin ID)* | **FUERA DE ALCANCE — NO TOCAR** | `### 8.3/8.4/8.5 ...` | *(sin cambio)* |
| 09 | MANUAL:VANTAGE-RUNTIME-001 | *(sin cambio)* | `## 9. VANTAGE RUNTIME... · ID: MANUAL:VANTAGE-RUNTIME-001` | `## 09 MANUAL:VANTAGE-RUNTIME-001` / `## VANTAGE Runtime (Consulta Operativa)` |
| 10 | MANUAL:GESTION-DATOS-001 | **MANUAL:DATA-MANAGEMENT-001** | `## 10. GESTIÓN DE DATOS · ID: MANUAL:GESTION-DATOS-001` | `## 10 MANUAL:DATA-MANAGEMENT-001` / `## Gestión de Datos` |
| 11 | MANUAL:HEALTHCHECK-001 | *(sin cambio)* | `## 11. HEALTH CHECK · ID: MANUAL:HEALTHCHECK-001` | `## 11 MANUAL:HEALTHCHECK-001` / `## Health Check` |
| 12 | MANUAL:TROUBLESHOOTING-001 | *(sin cambio)* | `## 12. TROUBLESHOOTING · ID: MANUAL:TROUBLESHOOTING-001` | `## 12 MANUAL:TROUBLESHOOTING-001` / `## Troubleshooting` |
| 13 | MANUAL:PROMPTS-WRAPPERS-001 | *(sin cambio)* | `## 13. PROMPTS & WRAPPERS · ID: MANUAL:PROMPTS-WRAPPERS-001` | `## 13 MANUAL:PROMPTS-WRAPPERS-001` / `## Prompts & Wrappers` |
| 14 | MANUAL:CHEATSHEETS-001 | *(sin cambio)* | `## 14. CHEAT SHEETS · ID: MANUAL:CHEATSHEETS-001` | `## 14 MANUAL:CHEATSHEETS-001` / `## Cheat Sheets` |
| 15 | MANUAL:PATCH-QUALITY-001 | *(sin cambio)* | `## 15. CRITERIO DE CALIDAD... · ID: MANUAL:PATCH-QUALITY-001` | `## 15 MANUAL:PATCH-QUALITY-001` / `## Criterio de Calidad para Parches Documentales` |
| 16 | MANUAL:REGLAS-DE-ORO-001 | **MANUAL:GOLDEN-RULES-001** | `## 16. REGLAS DE ORO... · ID: MANUAL:REGLAS-DE-ORO-001` | `## 16 MANUAL:GOLDEN-RULES-001` / `## Reglas de Oro para Operadores` |
| 17 | MANUAL:SLA-001 | *(sin cambio)* | `## 17. SLA DE LATENCIA... · ID: MANUAL:SLA-001` | `## 17 MANUAL:SLA-001` / `## SLA de Latencia Post-Ingesta` |
| 18 | MANUAL:CV-GOLDEN-RULES-INDEX | *(sin cambio)* | `## 18. Reglas de Oro CV... ID: MANUAL:CV-GOLDEN-RULES-INDEX` | `## 18 MANUAL:CV-GOLDEN-RULES-INDEX` / `## Reglas de Oro CV — Referencia Operativa` |
| 19 | MANUAL:POSITIONING-CRITERIA | *(sin cambio)* | `## 19. Positioning Modes... ID: MANUAL:POSITIONING-CRITERIA` | `## 19 MANUAL:POSITIONING-CRITERIA` / `## Positioning Modes (N1–N4) — Criterio de Selección` |
| 20 | MANUAL:GOLDEN-SKELETON-REF | *(sin cambio)* | `## 20. Golden Skeleton... ID: MANUAL:GOLDEN-SKELETON-REF` | `## 20 MANUAL:GOLDEN-SKELETON-REF` / `## Golden Skeleton — Qué Es y Dónde Vive` |
| 21 | MANUAL:SCHEMA-FIELD-REF | *(sin cambio)* | `## 21. Schema Class A/B... ID: MANUAL:SCHEMA-FIELD-REF` | `## 21 MANUAL:SCHEMA-FIELD-REF` / `## Schema Class A/B — Referencia de Campos` |

**IMPORTANTE — Manual §18 (Golden Rules):** este documento tiene un bug conocido y sin resolver en su tabla de referencia (`_try_parse_table()` en `vsync_doc.py` no parsea sintaxis markdown `[texto](url)` dentro de celdas, dejándolas como texto plano crudo). Si al llegar a esta sección encuentras una tabla con texto de link roto (corchetes y URL visibles como texto, no como link real), NO lo arregles como parte de esta migración — repórtalo en tu resumen de cierre (Sección 5) y sigue con el resto del documento. Ese bug tiene su propio patch pendiente, separado de este contrato.

---

## 4. GATE DE VERIFICACIÓN — OBLIGATORIO DESPUÉS DE CADA DOCUMENTO

Al terminar de escribir los headings de UN documento, antes de reportar cualquier cosa al operador o pasar al siguiente documento:

1. **Re-fetch obligatorio** del documento completo, vía `notion-fetch` (o el método MCP equivalente disponible). NO uses el resultado reportado por tu propia herramienta de escritura como confirmación — debes leer el documento de vuelta, de forma independiente a la operación de escritura.
2. **Verificación línea por línea:** compara cada heading nuevo, tal como aparece en el re-fetch, contra la columna "Heading nuevo" de la tabla correspondiente en la Sección 3. Confirma:
   - El símbolo `§` no aparece en ningún heading.
   - El padding de 2 dígitos es correcto en todas las secciones padre.
   - El ID está en inglés, el título en español.
   - Ningún heading de definición quedó convertido en hipervínculo.
3. **Conteo de headings:** el número total de headings de nivel 2 (`##`) en el documento después de la migración debe coincidir con el número de filas de la tabla de la Sección 3 para ese documento (más las subsecciones no incluidas en el conteo de filas padre, si aplica). Si el conteo no coincide, DETENTE — algo se perdió o se duplicó.
4. **Redacta un reporte de verificación** con este formato exacto:

```
DOCUMENTO: [nombre]
HEADINGS ESPERADOS: [N]
HEADINGS ENCONTRADOS (re-fetch): [N]
COINCIDENCIA LÍNEA POR LÍNEA: [SÍ / NO — listar discrepancias]
ANCHORS NUEVOS CAPTURADOS: [lista de bloque-IDs para los headings nuevos/renombrados, ver Sección 6]
PROBLEMAS ENCONTRADOS: [ninguno / lista]
```

5. **Envía este reporte al operador y espera `APROBAR_WRITE` explícito antes de continuar al siguiente documento.** No autoinfieras aprobación por ausencia de respuesta ni por el paso del tiempo.

---

## 5. CIERRE DE TAREA

Al completar los 6 documentos (o los que el operador haya autorizado), entrega:

- Los 6 reportes de verificación de la Sección 4 (uno por documento).
- Una lista consolidada de TODOS los anchors nuevos capturados (ver Sección 6) para que puedan integrarse al `MAPPING` de `apply_hyperlinks.py`.
- Cualquier discrepancia, ambigüedad, o decisión que hayas tenido que reportar al operador durante la ejecución (Sección 0).
- Confirmación explícita de si el bug de Manual §18 (tabla de Golden Rules) se detectó o no durante tu paso por ese documento.

**No cierres la tarea con lenguaje de éxito genérico** ("todo se aplicó correctamente", "62/62 aplicados") sin acompañarlo del reporte de verificación línea por línea de la Sección 4. Un reporte de éxito sin este detalle no será aceptado como cierre válido — esto ya ocurrió una vez en este proyecto (Changelog v9.8.1, "Career Canon 1 hipervínculo aplicado" resultó ser falso tras verificación) y es precisamente el fallo que este contrato existe para prevenir.

---

## 6. CAPTURA DE ANCHORS NUEVOS (para 3 IDs sin anchor conocido)

Los siguientes 3 IDs son nuevos o renombrados y su anchor de bloque real en Notion se desconoce hasta que el heading correspondiente se escriba:

- `SP:MCP-ROUTING-NOTES` (System Prompt §9, renombrado)
- `MANUAL:COLD-START-001` (Manual §5, nuevo)
- `ALIASES:DEDUP` (Aliases §8, nuevo)

Inmediatamente después de escribir el heading correspondiente en cada uno de estos 3 casos, captura el anchor de bloque real (vía `notion-fetch` sobre el bloque específico, o el método que tu herramienta MCP provea para obtener el `block_id`) y repórtalo explícitamente en el reporte de verificación de ese documento. Estos 3 anchors son necesarios para completar el `MAPPING` de `apply_hyperlinks.py`, que hoy los tiene marcados como `PENDIENTE_ANCHOR...`.

---

## 7. QUÉ HACER SI ALGO NO COINCIDE CON EL DOCUMENTO REAL

Si al abrir un documento encuentras que:
- un heading citado en la Sección 3 no existe tal como está escrito (texto distinto, posición distinta, o ausente),
- el documento tiene una sección adicional no contemplada en este contrato,
- el conteo de subsecciones no coincide con lo documentado,

**DETENTE en ese documento específico, no intentes adivinar ni "corregir" la tabla de este contrato por tu cuenta, y repórtalo al operador con el texto exacto que encontraste versus el texto que este contrato esperaba.** Esto no es una falla tuya — es exactamente el tipo de discrepancia que `SP:CONSISTENCY` exige reportar antes de proceder.
