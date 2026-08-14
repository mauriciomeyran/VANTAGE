# V | CHANGELOG

Tipo: [DOC]
Alcance:
- Skill Library (Notion DB, alta de fila)
- Manual (MANUAL:SKILL-GLOSSARY-HOUSEKEEPING §23.2 — fila nueva)
- /mnt/skills/user/vantage-sync-script-library/SKILL.md (local, corrección)
- /mnt/skills/user/vantage-sync-assets/SKILL.md (local, instalación)
Contexto: Propuesta de documentación transversal para vantage-sync-assets, meta-skill que orquesta las 4 skills de sincronización existentes (Script Library, Skill Library, Script Glossary §22, Skill Glossary §23) en orden fijo Libraries→Glossaries. Mapeo inicial (Notebook Gemini) proponía altas de ID nuevas en Kernel (KERNEL:ASSETS-SYNC, extensión de KERNEL:DOCUMENTATION-005/-010, trigger en SP:TRIGGERS) — descartadas tras verificación contra BRIEF:CONSULTATION-002 (catálogo de skills es responsabilidad del Manual, no del Kernel) y contra el contrato ya confirmado de vantage-sync-skill-library (que ya cita KERNEL:DOCUMENTATION-005 correctamente). Auditoría cruzada expuso que vantage-sync-script-library citaba un anchor inexistente (KERNEL:SKILL-ANNOUNCE-CONVENTION) para la misma convención — corregido en este batch.
Cambios:
- Skill Library (Notion) — alta de fila vantage-sync-assets (Estado: Activo, Ruta: /mnt/skills/user/vantage-sync-assets/SKILL.md, Dependencias: las 4 skills hijas).
- MANUAL:SKILL-GLOSSARY-HOUSEKEEPING (23.2) — fila nueva insertada tras vantage-sync-skill-library, antes de vantage-sync-census-spec.
- vantage-sync-script-library/SKILL.md (local) — anchor corregido: KERNEL:SKILL-ANNOUNCE-CONVENTION → KERNEL:DOCUMENTATION-005.
- vantage-sync-assets/SKILL.md (local) — instalado, con nota de alcance frente a L4 (vdoc/vsync_doc.py) añadida en Reglas de oro (metadatos de inventario vs. contenido documental — dominios distintos).
IDs afectados: Ninguno (sin alta/baja de KERNEL:ID/MANUAL:ID canónico — fila de tabla existente + archivo local).
Write-Back Verification: Skill Library re-fetched post-escritura (fila confirmada). Manual re-fetched post-escritura — fila vantage-sync-assets confirmada en posición correcta dentro de §23.2. Archivos locales verificados por lectura directa post-escritura.
Pendiente (fuera de esta entrada):
- vversions --sync para propagar v9.20.5 al resto de los fundacionales.
- Gap heredado sin tocar: campo Capa de Skill Library sigue sin opción aplicable para meta-skills de housekeeping (dejado vacío en la fila nueva, consistente con el gap ya documentado en MANUAL:SKILL-GLOSSARY-XREF 23.5).
---
Tipo: [DOC]
Alcance:
- Manual (MANUAL:SKILL-GLOSSARY §23 y subsecciones 23.1–23.5)
- Navigation Brief (BRIEF:AUTHORITY-MATRIX §02, BRIEF:CONSULTATION-002 §04.2)
- Census Spec (Layer_1/scripts/generate_census.py, local)
Contexto: Alta de §23 MANUAL:SKILL-GLOSSARY — catálogo operativo de las 19 skills de Claude (/mnt/skills/user/), contraparte de MANUAL:SCRIPT-GLOSSARY (§22) aplicada a skills en vez de scripts. Contrato validado contra los 6 filtros de MANUAL:PATCH-QUALITY-001. Escritura verificada en vivo vía notion-fetch en esta sesión (Manual y Brief re-fetched, contenido confirmado byte-exacto contra el patch propuesto).
Cambios:
- MANUAL:SKILL-GLOSSARY (23) — nodo nuevo, glosario de skills en 4 categorías (Core, Housekeeping, Audit, Style) + XREF de gaps abiertos.
- MANUAL:SESSION-CYCLE — bullet nuevo referenciando §23.
- BRIEF:AUTHORITY-MATRIX — fila nueva: Gobernanza de Skills IA → Manual §23.
- BRIEF:CONSULTATION-002 — bullet nuevo: catálogo de skills.
- CENSUS_SPEC (local) — alta de 6 IDs: MANUAL:SKILL-GLOSSARY, -CORE, -HOUSEKEEPING, -AUDIT, -STYLE, -XREF.
IDs afectados: 6 altas (ver Census Spec arriba).
Write-Back Verification: Manual y Navigation Brief re-fetched post-escritura — 4 nodos confirmados en posición correcta. vcensus re-ejecutado post-alta en CENSUS_SPEC: 196/196 IDs resueltos, 0 huérfanos. ID CENSUS (Notion) actualizado por el operador con el nuevo export.
Pendiente (fuera de esta entrada):
- vversions --sync para propagar v9.20.4 al resto de los fundacionales.
- Gaps documentados en MANUAL:SKILL-GLOSSARY-XREF (23.5): anuncio no especificado en 6 skills (vantage-cv-a, vantage-cv-b, vantage-qa, vantage-sync-script-glossary, vantage-audit-navigation-brief, cierre de vantage-documentacion-transversal-propuesta); campo Capa null en 24/25 filas de Skill Library.
---
Tipo: [DOC]
Alcance:
- Kernel (KERNEL:TRIGGER-002, 11.2)
- Manual (MANUAL:SCRIPT-GLOSSARY-L1-MODULES — priority_logic.py; MANUAL:SCRIPT-GLOSSARY-L1 — backfill_class_a.py)
Contexto: Cierre documental del fix de código v9.20.2 (created_time leído desde raíz del objeto Notion, no desde properties; duplicación de txt() sin fix de rich_text en backfill_class_a.py). Este batch deja precedente narrativo en Kernel/Manual para que la próxima función que asuma la forma del objeto Notion sin verificar schema tenga ancla de referencia.
Cambios:
- KERNEL:TRIGGER-002 (11.2) — nota de precedente: created_time vive en raíz del objeto página, no en properties; mismo patrón de riesgo que motivó el fix de txt()/rich_text (v9.20.1).
- MANUAL:SCRIPT-GLOSSARY-L1-MODULES (priority_logic.py) — aclaración: txt() existe duplicada en 3 archivos (layer_1_run.py, priority_logic.py, backfill_class_a.py); consolidación evaluada y descartada por riesgo de import circular.
- MANUAL:SCRIPT-GLOSSARY-L1 (backfill_class_a.py) — nota sobre hack de parsing local para propiedades top-level, con referencia cruzada a KERNEL:TRIGGER-002 (nodo aportado por Gemini, validado).
IDs afectados: Ninguno (extensión de nodos existentes).
Write-Back Verification: 3 parches inyectados y confirmados en sesión previa (KERNEL + MANUAL re-fetched byte-exactos contra v9.20.1 vivo).
Pendiente (fuera de esta entrada):
- vversions --sync para propagar v9.20.3 al resto de los fundacionales.
---
Tipo: [FIX] [CODE]
Alcance:
- Código: Layer_1/scripts/priority_logic.py (infer_prioridad()), Layer_1/scripts/layer_1_run.py (caller Fase 3.6), Layer_1/scripts/backfill_class_a.py (txt())
Contexto: Verificación post-v9.20.1 detectó que infer_prioridad() nunca calculaba Urgencia por antigüedad real: leía props.get("created_time"), pero ese campo vive en la raíz del objeto de página de Notion (item["created_time"]), no dentro de properties. Todas las vacantes caían en el fallback urgencia="MEDIO", razon="sin_fecha_creacion" sin importar su antigüedad real. Auditoría de verificación de ese fix reveló además una tercera copia independiente de txt() en backfill_class_a.py sin el fix de concatenación de rich_text aplicado en v9.20.1 (Bug Tracker 3bb938be-fc42-8186-a551-d19cc3691d86).
Cambios:
- priority_logic.py::infer_prioridad() — firma cambiada de (props, today) a (item, today); lee item.get("created_time") en vez de props.get("created_time").
- layer_1_run.py y backfill_class_a.py — callers actualizados para pasar item completo.
- backfill_class_a.py::txt() — concatena todos los chunks de rich_text/title, igual que las otras dos instancias.
- test_gate_logic.py — 7 tests nuevos (TestPriorityLogicCreatedTime) + 5 tests nuevos (TestBackfillTxtConcatenation).
Validación: Corrida real de vl1 post-fix — 9 cambios de Prioridad reflejando antigüedad real (antes: fallback fijo a MEDIO). Fix de backfill_class_a.py::txt() verificado línea por línea contra el archivo real, no solo por resumen del agente.
IDs afectados: Ninguno (fix de código, sin alta/baja de ID canónico).
Write-Back Verification: Bug Tracker 3bb938be-fc42-8186-a551-d19cc3691d86 — Resuelto, verificado.
Pendiente (fuera de esta entrada):
- Evaluar ticket de Task Tracker para consolidar txt() en módulo compartido (notion_helpers.py) — no viable en este ciclo por hack de imports en backfill_class_a.py (ver Bug Tracker para detalle).
- vversions --sync para propagar v9.20.2 al resto de los fundacionales.
---
Tipo: [FIX] [CODE]
Alcance:
- Código: Layer_1/scripts/layer_1_run.py (txt(), FASE 2 URL Gate línea ~693)
- Kernel (KERNEL:GATE-DECISION-010 §09.10 — referencia de protección de terminalidad)
Contexto:
Operador verificó manualmente 17 vacantes activas (JD completo, accesibles, reciben postulaciones) marcándolas Status=Target, Fetch=Accesible, Gate_Decision=CREATE. Re-ejecución de vl1 revirtió las 17 a Bloqueado/Expirada/Archivar. Causa raíz aislada con evidencia directa de la API (no CSV, no hipótesis): txt() leía únicamente rich_text[0]["plain_text"]; la API de Notion fragmenta contenido largo en múltiples chunks (confirmado: 21 chunks para un JD de ENCANTO MÉXICO, chunk[0] de 60 caracteres frente a ~1750+ reales). Esto rompía JD_ALREADY_EXISTS (len(jd_clean) > 100), forzando la rama de HEAD en vivo contra agregadores con anti-scraping activo (403 reproducido en Indeed/OCC/LVMH), sin protección de terminalidad para Status=Target.
Cambios:
- layer_1_run.py::txt() — concatena todos los chunks de rich_text y title en vez de leer solo [0].
- layer_1_run.py línea ~693 — nueva protección: Status=Target con JD concatenado >100 chars se salta el URL Gate (defensa en profundidad, además del fix de raíz).
- test_gate_logic.py — nueva clase TestRichTextConcatenation, 7 tests, 7/7 passed.
Validación: DRY_RUN sobre las 17 filas afectadas — 0/17 rechazos (antes: 17/17 reversiones erróneas).
IDs afectados: Ninguno (fix de código, sin alta/baja de ID canónico).
Write-Back Verification: Bug Tracker (ticket 3bb938be-fc42-813d-a253-ca2097f33957) creado y verificado en esta sesión.
Pendiente (fuera de esta entrada):
- Corrección manual/batch de las 17 filas ya dañadas en Notion (operación de datos separada, requiere DRY RUN + APROBAR_WRITE aparte).
- vversions --sync para propagar v9.20.1 al resto de los fundacionales.
---
Tipo: [FIX] [CODE] [DOC]
Alcance:
- Código: Layer_1/scripts/layer_1_run.py (validate_url_pre_ingestion)
- Kernel (KERNEL:GATE-DECISION-002 §09.2, KERNEL:GATE-DECISION-011 §09.11)
- Manual (MANUAL:HOW-IT-WORKS §02, MANUAL:SCHEMA-FIELD-REF §21)
- Aliases (ALIASES:L1L2-DISCOVERY §03)
Contexto:
Auditoría del Tracker (CSV export, 42 filas) detectó 19 vacantes con JD vacío pese a Fetch=Accesible y Score determinístico. Causa raíz: validate_url_pre_ingestion() tenía un bypass ciego para dominios agregadores (Computrabajo, Indeed, LinkedIn) — retornaba True sin ejecutar ningún request HTTP (AGREGADOR_VALID), y el flujo de FASE 2 escribía Fetch: Accesible sin verificación real. 13 de las 19 filas resultaron URLs sintéticas no indexadas (patrón [rol]-[marca]-2024 en computrabajo.com), consistente con orígen de agente L2 sin verificar, coladas por el bypass.
Cambios:
- layer_1_run.py::validate_url_pre_ingestion() — bypass ciego reemplazado por HEAD con timeout de 6s: 200 → AGREGADOR_VERIFIED; status ≠ 200 → rechazo (AGREGADOR_STATUS_XXX); timeout/excepción → AGREGADOR_UNVERIFIED (no confirma ni descarta, ya no asume Accesible).
- KERNEL:§09.2 — Paso 1 (URL_GATE) re-especificado: HEAD 6s obligatorio para agregadores en vez de excepción sin verificar.
- KERNEL:§09.11 — fila nueva en la matriz: [ENTRY] Agregador con HEAD fallido/timeout → REVIEW_NEEDED (Fetch=No_Verificado, no Accesible).
- MANUAL:§02 — aclaración en "Gate Decisions", paso 1: el chequeo en agregadores ya no omite verificación, registra honestamente si no pudo confirmarse.
- MANUAL:§21 — nota en campo Fetch: refleja verificación técnica real, incluso en agregadores.
- ALIASES:§03 (vl1) — nota sobre validación activa de URLs de agregadores en Fase 2 de layer_1_run.py.
Validación PATCH-QUALITY-001: ✅ Invisibilidad estructural (inline, sin secciones nuevas) · ✅ Continuidad de voz · ✅ Diff mínimo · ✅ Coherencia transversal (sin contradicción con GATE-DECISION-010/011 existentes).
IDs afectados: Ninguno (sin alta/baja de ID canónico — extensiones de nodos existentes).
Write-Back Verification: KERNEL, MANUAL y ALIASES re-fetched post-escritura — 4/4 bloques confirmados en posición correcta, sin mismatch.
Pendiente (fuera de esta entrada):
- Alta del select-option No_Verificado en el campo Fetch del Tracker de vacantes (Notion, Class B — requiere decisión del operador antes de propagar el reason diferenciado a FASE 2 de escritura).
- Ticket Bug Tracker asociado (creación pendiente de APROBAR_WRITE separado).
- vversions --sync para propagar v9.20.0 al resto de los fundacionales.
---
Tipo: [DOC] [GOVERNANCE] [INFRA]Alcance:
- Kernel (KERNEL:DOCUMENTATION-007)
- Manual (MANUAL:RUNTIME-002)
- System Prompt (SP:VERSION-CHECK-TOOL)
Contexto:
El contrato de Length Check (verificación de integridad estructural) estaba definido en un adendum externo (### 007.3) bajo KERNEL:DOCUMENTATION-007, lo que violaba la Matriz Tipográfica Congelada (KERNEL:DOCUMENTATION-001) al introducir un heading ### no autorizado (NN.N.N). Este batch relocaliza el contrato como contenido *inline* bajo el nodo existente ### 03.7, eliminando el adendum y evitando:
- Creación de un nuevo ID canónico (exime de CENSUS-SYNC Regla 1).
- Violación de la jerarquía de headings (NN.N válido).
- Fragmentación de la documentación transversal.
Cambios:
- KERNEL:§03.7:
- Lista de Modos extendida: añadidos -length (Sanity check read-only) y -update-baseline (write explícito).
- Cuerpo del contrato inyectado inline (propósito, mecanismo, umbrales, archivos asociados, flags).
- Adendum ### 007.3 eliminado (evita colisión de headings).
- Alias actualizado: vversions — acepta --bootstrap, --sync, --scripts, --skills, --length o --update-baseline, sin modo default.
- MANUAL:9.2:
- Bullet de vversions expandido con descripción operativa de -length (exit code 1 si ATENCIÓN REQUERIDA) y -update-baseline (requiere confirmación explícita).
- Sección flotante "HC-03" eliminada (consolidación de contenido).
- SP:§11.3:
- Verificado alineado: Directivas vigentes ya reflejan umbrales (≥5.0%, ≥10 líneas) y bloqueo de -update-baseline no verificado. Sin parche requerido.
Validación PATCH-QUALITY-001:
✅ Matriz Tipográfica (001): Respeta niveles autorizados (### NN.N).
✅ Invisibilidad estructural: Contenido vivo dentro de ### 03.7 sin alterar árbol de navegación.
✅ Continuidad de voz: Tono técnico consistente con el estándar del Kernel.
✅ Diff mínimo: Relocalización limpia (inyección + depuración de adendum).
IDs afectados: Ninguno (sin alta/remoción de IDs canónicos).
Write-Back Verification:
- KERNEL, MANUAL y SP re-fetched post-escritura: 3/3 nodos confirmados en posición correcta.
- KERNEL:§03.7: Modos, cuerpo del contrato y alias verificados.
- MANUAL:9.2: Bullet de vversions expandido y "HC-03" eliminado.
- SP:§11.3: Directivas alineadas (sin cambios requeridos).
Pendientes (fuera de esta entrada):
- vversions --sync para propagar v9.19.6 al resto de los fundacionales.
---
Tipo: [DOC] [GOVERNANCE]Alcance:
- Kernel (KERNEL:DOCUMENTATION-001 §03.1, KERNEL:DOCUMENTATION-007 §03.7, KERNEL:SCHEMA-008 §007.3)
- Manual (MANUAL:SESSION-CYCLE §06, MANUAL:SETUP §11)
- System Prompt (SP:SYNC-RULE §02, SP:DIGITAL-ID-CARD §03)
Contexto:
El documento CHANGELOG_ARCHIVO (ID: 3ba938be-fc42-8011-8947-fb4fa5d1f63f) fue migrado de página a base de datos para centralizar el historial de cambios. Este batch actualiza todas las referencias en el corpus fundacional para reflejar su nuevo estatus como 10° documento fundacional, alineando:
- Contrato de Prefijos Autorizados (KERNEL:§03.1).
- Alcance de vversions (KERNEL:§03.7, §007.3).
- Validación de sesión (MANUAL:§06).
- Verificación de archivos locales (MANUAL:§11).
- Lista de documentos en SP:§02 y ID en SP:§03.
Cambios:
- KERNEL:§03.1: Fila CHANGELOG_ARCHIVO V | CHANGE LOG ARCHIVO añadida a la tabla de Prefijos Autorizados.
- KERNEL:§03.7: 9 → 10 documentos fundacionales.
- KERNEL:§007.3: Lista de documentos actualizada para incluir CHANGELOG_ARCHIVO.
- MANUAL:§06: 9 → 10 documentos fundacionales.
- MANUAL:§11: 6 → 7 documentos en ACTIVE/.
- SP:§02: nueve → diez + ARCHIVO CHANGELOG añadido a la lista.
- SP:§03: ID de ARCHIVO CHANGELOG actualizado de 39d938be-fc42-801c-94f6-f11bfe803633 (página) a 3ba938be-fc42-8011-8947-fb4fa5d1f63f (base de datos).
IDs afectados:
- 3ba938be-fc42-8011-8947-fb4fa5d1f63f (nuevo ID de CHANGELOG_ARCHIVO).
Write-Back Verification:
- KERNEL, MANUAL y SP re-fetched post-escritura: 7/7 nodos confirmados en posición correcta.
- SP:§03: ID de ARCHIVO CHANGELOG verificado como 3ba938be-fc42-8011-8947-fb4fa5d1f63f.
Pendientes (fuera de esta entrada):
- vcensus para regenerar el Census con el nuevo ID.
- vversions --sync para propagar v9.19.5 al resto de los fundacionales.
---
Tipo: [INFRA] [DOC]
Alcance: Integración de "Archivo Changelog" (UUID: 3ba938be-fc42-8011-8947-fb4fa5d1f63f) al flujo de sincronización local y de versión.
Contexto: La página de Notion "Archivo Changelog" cuenta con la propiedad "Versión" y cumple con el contrato de página fundacional. Se integra al registry y a los scripts de sincronización para incluirlo en el ciclo de versionado y check de salud.
Cambios:
- resolver_registry_v2.json — Agregada entrada "CHANGELOG_ARCHIVO": "3ba938be-fc42-8011-8947-fb4fa5d1f63f" en document_registry.
- verify_versions.py — Añadido "CHANGELOG_ARCHIVO" a DOC_KEYS (conteo de fundamentales: 9→10). Agregado fallback ID y lógica de resolución.
- vsync_doc.py — Añadida entrada "change_log_archivo" en diccionario DOCS con mapeo a "Changelog Archivo.md".
- vdoc.py — Añadido "change_log_archivo" al set DOCS.
- health_check.py — Añadida entrada "V-CHANGELOG-ARCHIVO" en DOCS_FUNDACIONALES.
IDs afectados: Ninguno nuevo — integración de documento existente al flujo operativo. 
Tipo: [DATA] [AUDIT]
Alcance: VANTAGE TRACKER (5 páginas: Oniverse, Milano Operadora, Ikea, Confidencial/placeholder, Dior); alias_map.json (local).
Contexto: Cierre de tareas C-003 a C-006 del plan B.md (Devin/Claude), verificadas contra datos vivos del Tracker (35 registros, CSV export + Notion MCP) en vez de asumir el plan original sin verificar. Se detectaron y corrigieron discrepancias entre B.md y el estado real: (1) C-004 asumía que fila 3 y fila 10 del Tracker compartían hash — falso; el duplicado real de fila 3 ya estaba archivado en ARCHIVO TRACKER (39a938befc428102a26ecbc0fe20917c, Archivar=true), por lo que C-004 no requirió escritura. (2) C-003 asumía 4 alias sin resolver — en Notion vivo, Milano Operadora e Ikea ya tenían Marca canónica, solo faltaba limpiar Notas; solo Oniverse requirió write real de Marca. (3) C-006 asumía 17 registros — el Tracker vivo tiene 35.
Cambios:
- alias_map.json (local) — altas: oniverse→Intimissimi, milano operadora→Milano Operadora, ikano retail→Ikea. "Importante empresa del sector" excluido (placeholder genérico, resolución manual).
- Tracker — página Oniverse (3b6938befc42818e9ba8c68dbd300b0b): Marca→Intimissimi, Notas actualizadas.
- Tracker — página Milano Operadora (3b6938befc4281b3a827d1acbf6b983c): Notas actualizadas (Marca ya canónica).
- Tracker — página Ikea (3b6938befc4281619c75d37456a9f79f): Notas actualizadas (Marca ya canónica).
- Tracker — página Confidencial/placeholder (3b6938befc4281f3b054f5785e989fa9): Notas documentando decisión de no-alta.
- Tracker — página Dior (38d938befc42818f8447f0da5369c40b): Notas documentando decisión de mantener URL de búsqueda (C-005, opcional, no ejecutada re-captura).
- C-006: auditoría de 35 registros vs. KERNEL:GATE-DECISION-011 (bandas de Score × Gate_Decision) — 35/35 coherentes, 0 excepciones estructurales. Sin escritura asociada (solo lectura).
IDs afectados: ninguno nuevo. Census no requiere regeneración.
Write-Back Verification: las 5 páginas de Tracker re-consultadas vía query_data_sources post-escritura — Marca/Notas confirmadas en los 5 casos, sin mismatch.
Pendiente (fuera de esta entrada): 2 posibles duplicados no marcados sin resolver (CONFIDENCIAL/Gerente Nacional vs. Confidencial/Gerente; Ikano-Retail vs. Ikea) — requieren decisión del operador; verificación de precedencia Next_Action=Optimizar vs JD_Quality no confirmada por falta de esa columna en la query de auditoría.
Versión actualizada: 9.19.3 (CHANGELOG). Resto de fundacionales permanece en v9.19.2 hasta vversions --sync.
---
Tipo: [DOC]
Alcance: Kernel (KERNEL:GATE-DECISION-003 09.3, KERNEL:GATE-DECISION-010 09.10 Referencias, KERNEL:OWNERSHIP-002 05.2).
Contexto: Cierre del pendiente D-002 dejado abierto en v9.19.1. Verificación línea por línea contra dashboard_notion.py confirmó que class_b_guard.guard_write_payload() está integrado en write_patch_to_notion() como guard previo a client.pages.update(), fail-closed (CLASS_B_BLOCKED) ante campos Class B o desconocidos (strict_unknown=True). Esto cierra GAP-03, documentado desde antes como mitigación interina (whitelist en DRY RUN) sin guard real equivalente al de feed_processor.py.
Cambios:
- KERNEL:GATE-DECISION-003 (09.3) — GAP-03 marcado CERRADO, reemplaza la mención de mitigación interina por la descripción del guard real confirmado.
- KERNEL:GATE-DECISION-010 (09.10, bloque Referencias) — extendida la referencia a dashboard_notion.py para mencionar el guard D-002.
- KERNEL:OWNERSHIP-002 (05.2) — nota añadida sobre la aplicación técnica del invariante "Python recalcula Class B" en la vía RT-1/Dashboard.
IDs afectados: ninguno nuevo — extensión de contenido bajo IDs existentes. Census no requiere regeneración.
Write-Back Verification: Kernel re-fetched tras escritura — los tres bloques confirmados en posición correcta, sin mismatch.
Pendiente (fuera de esta entrada): vversions --sync para propagar v9.19.2 al resto de los fundacionales.
Versión actualizada: 9.19.2 (CHANGELOG). Resto de fundacionales permanece en v9.19.1 hasta vversions --sync.
---
Tipo: [FIX] [CODE]
Alcance: Layer_1/scripts/gate_logic.py (D-001, D-004); Layer_1/scripts/profile_fit.py (D-003); Kernel (KERNEL:GATE-DECISION-010).
Contexto: Implementación coordinada Devin de tres fixes puntuales sobre gate_logic.py y profile_fit.py, verificados por dry-run del pipeline sin cambios lógicos a datos existentes (solo protección/observabilidad). D-002 (class_b_guard como middleware MCP) queda fuera de esta entrada — estado sin confirmar, pendiente de verificación en sesión futura.
Cambios:
- gate_logic.py — D-001: agregado "Expirada": "EXPIRADA" a STATUS_TERMINAL_MAP, alineando protección de terminalidad por Status con KERNEL:GATE-DECISION-010 (antes solo protegida indirectamente vía Next_Action=Expirada en TERMINAL_ACTIONS).
- gate_logic.py — D-004: agregado logging explícito de protección de terminales para observabilidad.
- profile_fit.py — D-003: agregado "Postulando" a _PROTECTED_STATUSES.
- KERNEL:GATE-DECISION-010 (09.10) — Criterio 1 actualizado documentando el fix D-001.
IDs afectados: ninguno nuevo — extensión/corrección de contenido bajo KERNEL:GATE-DECISION-010 ya existente. Census no requiere regeneración.
Write-Back Verification: gate_logic.py y profile_fit.py verificados línea por línea contra el código fuente subido (comentarios # D-001 FIX, # D-003 FIX, # D-004 FIX confirmados). Kernel re-fetched tras escritura — 09.10 Criterio 1 confirmado, referencias cruzadas (GATE-DECISION-005, -006, -008) intactas.
Pendiente (fuera de esta entrada): confirmar estado de D-002 (class_b_guard middleware MCP); C-002 posible duplicado (ya cubierto v9.14.5); C-003 a C-006 sin verificar con evidencia de código/tracker.
Versión actualizada: 9.19.1 (CHANGELOG). Resto de fundacionales permanece en v9.18.0 hasta vversions --sync.
Observaciones del dry-run:
1. Logging de terminales (D-004) funcionando:
- 10 registros con Status=Expirada muestran logging correcto:
```plain text

[gate_logic] PROTECTED: unknown → EXPIRADA (Status=Expirada, Next_Action=Archivar)
```
1. Cambios de prioridad (Fase 3.6):
- 6 cambios por sin_fecha_creacion (comportamiento esperado)
- Ejemplo: Confidencial/Zara/Bershka cambiando de BAJO→MEDIO/ALTO
1. Gate updates:
- 38 actualizaciones de Last_Gate_Run (timestamp normal de última ejecución)
1. Estado estable:
- "ESTADO ESTABLE: Sin cambios necesarios"
- D-001 a D-004 no introducen cambios lógicos a los datos, solo protección/observabilidad
RESUMEN FINAL v8.0:
URL Gate: 0 links muertos eliminados
JD Bypass: 2 vacantes con JD existente
READY-TO-APPLY (>=60): 11
CREATE (Pipeline Activo): 11
REVIEW_NEEDED (Score 40-59): 24
APPLIED (En proceso): 0
REJECTED: 0
BLOCKED: 0
PROTEGIDAS: 0
Total procesado: 45
ESTADO ESTABLE: Sin cambios necesarios
---
Tipo: [FIX] [INFRA]
Contexto: Auditoría de conformidad/drift de VANTAGE (sesión arena.ia + Claude, 2026-08-10, GitHub Issue #2, H2) detectó que Fase 3 (Scoring) y Fase 3.6 (Prioridad) iteraban sobre TODAS las filas sin filtrar terminales, violando KERNEL:GATE-DECISION-010 ("un registro terminal no puede ser sobreescrito por recálculo de Score/Gate"). Solo Fase 4 estaba protegida vía gate_logic(). Adicionalmente, la transición APPLIED→REJECTED (GATE-DECISION-011 fila 11) era código muerto porque gate_logic() retornaba "REJECTED" y el código hacía continue antes de llegar a evaluate_rejection_status().
Cambios:
- layer_1_run.py:743-770 — Fase 3 (Scoring): agregado filtro gate_logic() para skip registros terminales antes de recalcular Score.
- layer_1_run.py:917-945 — Fase 3.6 (Prioridad): agregado filtro gate_logic() para skip registros terminales antes de recalcular Prioridad.
- layer_1_run.py:999-1012 — Fase 4 (Gate): modificado gate_logic() continue para permitir que Status="Rechazado" continue y active evaluate_rejection_status() → REJECTED+Post-Mortem (transición APPLIED→REJECTED).
- test_gate_logic.py — agregada clase TestTerminalProtectionScoring con 4 tests de protección de terminales contra recálculo de Score/Prioridad.
IDs afectados: Tracker 596938befc42836baea7814a1491bd47 — 0 filas Postulado+CREATE residual (no presentes en dataset actual; fix previene futuros casos).
Write-Back Verification: Tests pasando (45/45), protección de terminales extendida a Fase 3/3.6, transición REJECTED+Post-Mortem ahora ejecutable.
Pendiente: avisar en GitHub Issue #2; actualizar Task Tracker (3b8938be-fc42-8166-81c9-ef9002012fac) con Status→Hecho y solución documentada.
Versión actualizada: 9.19.0 (CHANGELOG). Resto de fundacionales permanece en v9.18.0 hasta vversions --sync.
---
Tipo: [FIX] [INFRA]
Contexto: Auditoría de conformidad/drift de VANTAGE (sesión arena.ia + Claude, 2026-08-10, GitHub Issue #1, H1) detectó que gate() decidía solo por fetch + VM_Scope + Role_Class y nunca leía Score, violando el contrato del Kernel que define bandas: ≥60 CREATE · 40-59 Para Revisar · <40 BLOCKED. Evidencia: 31/36 filas CREATE con Score<60 en snapshot, mientras Manual/Checklist filtraban por Score≥60.
Cambios:
- layer_1_run.py:457-483 — gate() implementado con umbral de Score: score≥60 → CREATE, score≥40 → REVIEW_NEEDED, score<40 → BLOCKED. Score=None → REVIEW_NEEDED (golden rule: no pérdida silenciosa por dato faltante).
- test_gate_logic.py — actualizado para reflejar contrato actual de gate_logic() (solo protección de terminales) + 9 tests nuevos de Score Band (TestGateScoreBand).
- Manual.md — actualizado para incluir banda REVIEW_NEEDED (Score 40-59) y BLOCKED (Score<40).
- Checklist.html — actualizado para mencionar vista REVIEW_NEEDED en flujo de trabajo.
IDs afectados: Tracker 596938befc42836baea7814a1491bd47 — 9 filas cambiadas de CREATE→REVIEW_NEEDED (Score 40-50), 8 filas permanecen CREATE (Score≥60). Ready-to-Apply (≥60): 8 filas, alineado con contrato.
Write-Back Verification: Tests pasando (41/41), dry-run confirmado, aplicación exitosa al Tracker vivo.
Pendiente: avisar en GitHub Issue #1; actualizar Task Tracker (3b8938be-fc42-8130-b47a-f0150c2502cd) con Status→Hecho y solución documentada.
Versión actualizada: 9.18.0 (CHANGELOG). Resto de fundacionales permanece en v9.17.1 hasta vversions --sync.
---
Tipo: [DOC] [FIX]
Alcance: Kernel (KERNEL:GATE-DECISION-011).
Contexto: Auditoria de conformidad/drift de VANTAGE (sesion arena.ia + Claude, 2026-08-10, GitHub Issue #2, H3) detecto que KERNEL:GATE-DECISION-011 fila 4 documentaba un mecanismo de dedup inexistente en codigo ni schema (Gate_Decision=REJECTED_DUPLICATE, Dedup_Flag=True, Next_Action=Descartar). El mecanismo real (feed_processor.py) escribe Status=REVIEW_NEEDED sobre el registro entrante y Dedup_Flag='Posible duplicado' sobre el registro existente. En paralelo se investigo la causa raiz de 7 registros "Visual Merchandising Coordinator" (Score=50) reportados como no colapsados por la ventana de 30 dias: la mayoria resultaron falsos positivos (vacantes reales de empleadores distintos con titulo generico coincidente); el unico caso real de dedup fallido (par YELLO Marketing Group, hash identico 89a50e5e1978ec...) se debio a que NotionSchema.load() (feed_processor.py:319) limita el scope de dedup_cross_layer()/dedup_by_content_fingerprint() al VANTAGE TRACKER activo, sin visibilidad sobre ARCHIVO TRACKER.
Cambios:
- KERNEL:GATE-DECISION-011 (09.11) — fila 4 corregida: elimina referencia a REJECTED_DUPLICATE/Dedup_Flag=True/Next_Action=Descartar; documenta el mecanismo real (Status=REVIEW_NEEDED, Dedup_Flag='Posible duplicado').
IDs afectados: ninguno nuevo — correccion de contenido bajo KERNEL:GATE-DECISION-011 ya existente. Census no requiere regeneracion.
Write-Back Verification: Kernel re-fetched tras escritura — fila 4 confirmada en posicion correcta, sin mismatch.
Pendiente (fuera de esta entrada): Bug Tracker — nuevo ticket 3b8938be-fc42-8100-aa85-cbfe3c3e27f6 (dedup no cubre Archivo Tracker, 3 ALTO, [CENSUS-SYNC-R1]); vversions --sync para propagar v9.17.2 al resto de los fundacionales. GitHub: cerrado issue #2 con comentario de resolucion; corregido cierre erroneo de issue #3 (H1, permanece abierto — no relacionado con H3).
Version actualizada: 9.17.2 (CHANGELOG). Resto de fundacionales permanece en v9.17.1 hasta vversions --sync.
---
Tipo: [DOC] [FIX]
Alcance: Kernel (KERNEL:GATE-DECISION-007).
Contexto: Auditoria de conformidad/drift de VANTAGE (sesion arena.ia + Claude, 2026-08-10, GitHub Issue #4, H4) detecto que KERNEL:GATE-DECISION-007 documentaba archivado automatico via auto_archive.py como regla vigente, mientras el script vive deprecado en Archive/Legacy_Scripts/auto_archive.py desde la decision del operador (2026-08-01, documentada en la skill vantage-tidy-opportunities-tracker) de abandonar ese enfoque por marcado manual. El Bug Tracker tenia un ticket abierto ("Dedup Caso 5 — Next_Action=Archivar no se ejecuta automaticamente") como consecuencia directa de este drift documental. Es drift puramente documental — no requirio cambio de codigo.
Cambios:
- KERNEL:GATE-DECISION-007 (09.7) — retitulado de "Ejecucion Automatica de Archivado" a "Marcado Manual de Archivado". Reemplazada la referencia a auto_archive.py como mecanismo activo por la descripcion del flujo vigente: la skill vantage-tidy-opportunities-tracker marca Archivar = True tras DRY RUN + APROBAR_WRITE, sin mover ni copiar paginas; el operador archiva manualmente. Documentada explicitamente la decision del operador (2026-08-01) y la razon (friccion, costo de tokens, desalineacion de esquema con el Archivo Tracker).
IDs afectados: ninguno nuevo — extension/correccion de contenido bajo KERNEL:GATE-DECISION-007 ya existente. Census no requiere regeneracion.
Write-Back Verification: Kernel re-fetched tras escritura — bloque 09.7 confirmado en posicion correcta, sin mismatch.
Pendiente (fuera de esta entrada): re-etiquetar/cerrar ticket "Dedup Caso 5..." en Bug Tracker; decidir eliminacion o conservacion como referencia de auto_archive.py en el repo; avisar en GitHub Issue #4; vversions --sync para propagar v9.17.1 al resto de los fundacionales.
Version actualizada: 9.17.1 (CHANGELOG). Resto de fundacionales permanece en v9.16.0 hasta vversions --sync.
---
Contexto: post-mortem de batch de 13 CV-B procesados en una sola sesión continua — densidad narrativa (perfil/bullets) muy por debajo del estándar de referencia (Zegna), pese a que el Anti-cloning Guard (v9.16.0) eliminó correctamente la duplicación verbatim entre vacantes. Comparación directa contra 6 CV-B generados individualmente (uno por sesión) en el mismo periodo confirmó densidad consistentemente alta sin regla numérica adicional — la causa raíz es degradación de esfuerzo del AI Component bajo procesamiento secuencial de lote, no un gap de contrato documental.
Cambios:
- KERNEL:12.2 — Restricción de Lote (Single-Item Processing): CV-B procesa exactamente UN HANDOFF por invocación; ante un batch, procesa el primero y se detiene a esperar invocación explícita para el siguiente.
- vantage-cv-b.md — mismo guard insertado como restricción operativa previa al Anti-cloning Guard.
IDs afectados: ninguno nuevo — extensión de contenido bajo KERNEL:CV-PIPELINE-002 ya existente. Census no requiere regeneración.
Write-Back Verification: pendiente de re-fetch en este mismo batch.
Versión actualizada: 9.17.0 (CHANGELOG). Resto de fundacionales permanece en v9.16.0 hasta vversions --sync.
---
Contexto: drift detectado en batch de 16 CV-B (mismo Positioning Mode reutilizando
bullets pre-redactados verbatim entre vacantes distintas) + defecto mecánico de
viñetas dobles ("• •") en serialización Figma.
Cambios:
- KERNEL:12.2 — prohibición explícita de reutilizar bullets pre-redactados
verbatim entre vacantes, incluso dentro del mismo Positioning Mode.
- CANON:12.1 — alta de Regla #5, Distinctiveness Rule (Figma Sync Protocol).
- vantage-cv-b.md — Anti-cloning Guard como paso de verificación previo a entrega.
- vantage-qa.md — Ítem #7 del checklist: Diferenciación de Contenido, FAIL
automático si match verbatim >80% en Experience frente a otro entregable del
mismo batch.
- MANUAL:08.3 — advertencia operativa de riesgo Batch-Cloning en el flujo de
inyección Figma.
- Regeneración operativa: 16 CV-B del batch (17 HANDOFFs − 1 duplicado de
contenido) reconstruidos con bullets diferenciados por HANDOFF activo y sin
viñetas dobles.
---
Tipo: [INFRA] [DOC]
Cambios:
- Kernel: Subsección 007.3 integrada en KERNEL:DOCUMENTATION-007 (mecanismo, umbrales 5%/10 líneas, baseline).
- Manual: Subsección HC-03 en MANUAL:HEALTHCHECK (procedimiento de salud de documentos).
- Aliases: Extensión de ALIASES:L4-VERSION-CONTROL con flags --length y --update-baseline.
- System Prompt: Subsección 11.3 en SP:VERSION-CHECK-TOOL (guardarraíl operativo para la IA).
- Navigation Brief: Dependencia LENGTH-BASELINE añadida en CROSS-DEPENDENCIES-001 y matriz de autoridad actualizada.
Notas: Backward Compatibility — las operaciones existentes (--sync, --bootstrap) no se ven afectadas. Requisitos — length_baseline.json se genera automáticamente en la primera ejecución de --length.
Versión actualizada: 9.15.1 (CHANGELOG) · 2026-08-08.
---
> El histórico completo del CHANGELOG lo podrás encontrar en ARCHIVO CHANGELOG, en esta pagina de consulta continua solo encontrarás las últimas diez entradas para garantizar la operación y referencia del sistema.
