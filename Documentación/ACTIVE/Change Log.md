# V | CHANGELOG

### v9.3.4 Manual §6 — Fail-Fast, nota de versión en vdoc notion, purga de VERSION MANIFEST (Manual + Aliases)
- Fecha: 2026-07-15
- Alcance: MANUAL (§6 — "Qué hacer si algo no cuadra", §8.1 vdoc notion, §6 Cierre paso 3), ALIASES (Session Lifecycle, fila --sync).
- Contexto: sesión anterior (inconclusa por límite de mensajes) auditó dos payloads de patches propuestos por un modelo colaborador externo contra el Manual real (fetch en vivo, no memoria). De 6 patches propuestos entre ambos payloads, 3 resultaron obsoletos o mal anclados (old_str inexistente en el documento real) y fueron descartados; 3 se aplicaron con old_str verificado.
- Cambio 1 — MANUAL §6 "Qué hacer si algo no cuadra": reescrito a Fail-Fast explícito — "Terminal no está disponible → Operación detenida (Fail-Fast). No existe bypass automatizado vía MCP para este chequeo... con el fin de proteger la cuota de la API de Notion y evitar el desperdicio de tokens de contexto." Reemplaza redacción anterior que mencionaba el mismo principio con lenguaje menos directo. Write-back verificado por re-fetch (TCK-04).
- Cambio 2 — MANUAL §8.1 (vdoc notion): añadida "Nota obligatoria de Versión" — exige correr verify_versions.py --sync antes de vdoc notion si la descarga ocurre inmediatamente después de un cierre de sesión con incremento de versión, para evitar que los archivos Markdown locales nazcan con metadata de versión desalineada del Changelog maestro.
- Cambio 3 — MANUAL §6 Cierre paso 3: corregida la descripción de --sync, que decía inyectar la versión "directamente en el VERSION MANIFEST (DB)". Texto real del comportamiento del script: --sync ejecuta pages.retrieve + seis pages.patch secuenciales, una por documento fundacional restante, actualizando la propiedad "Versión" de cada página en Notion. La abstracción VERSION MANIFEST (DB) nunca reflejó el comportamiento real del script y quedó purgada de la prosa.
- Cambio 4 — ALIASES, Session Lifecycle, fila --sync: misma corrección aplicada en esta sesión (v9.3.3 dejó esta fila desalineada respecto al Manual ya corregido — discrepancia detectada por SP:CONSISTENCY y resuelta hoy). Write-back verificado por re-fetch.
- Hallazgo de proceso: durante la auditoría cruzada se confirmó que un modelo colaborador externo (sin acceso directo al Manual real, solo a un volcado de texto estático previo) generó 2 de los 3 patches de un primer payload y 2 de 3 de un segundo payload ancladas en texto ya obsoleto — no por alucinación, sino por trabajar sobre una versión desactualizada del documento (v9.3.1/anterior al rewrite de v9.3.2). Ningún patch se aplicó sin verificación de old_str contra el fetch en vivo.
- Ningún ID canónico (MANUAL:, KERNEL:, SP:*) fue creado ni retirado — los 4 cambios son reescritura de contenido bajo IDs ya existentes. Census no requiere regeneración (KERNEL:CENSUS-SYNC Regla 1 no se dispara).
- Resultado: MANUAL y ALIASES alineados entre sí y con el comportamiento real de verify_versions.py --sync. 0 discrepancias abiertas conocidas entre Manual/Aliases/script.
- Versión actualizada: 9.3.4.
### v9.3.3 Fix verify_versions.py + generate_census.py — discrepancia CENSUS resuelta, 4 huérfanos históricos incorporados
- Fecha: 2026-07-15
- Alcance: Layer_1/scripts/verify_versions.py, Layer_1/scripts/generate_census.py (ambos locales, no fundacionales — no disparan KERNEL:CENSUS-SYNC Regla 1 por sí mismos, ver Cambio 3).
- Contexto: sesión anterior (handoff) dejó verify_versions.py con basura de texto, rutas y flag --bootstrap corregidos, pero el operador reportó al correrlo en Terminal que seguía fallando: ENV_PATH y REGISTRY_NAME no resolvían contra la estructura real de disco ni contra el schema real de resolver_registry_v2.json (namespace real: "document_registry", no "DOCUMENTS"/"SYSTEM" como asumía el script; CENSUS ausente por completo de ese archivo).
- Cambio 1 — verify_versions.py: ENV_PATH corregido a Layer_1/config/layer_1.env; búsqueda de resolver_registry_v2.json extendida a Layer_1/data/; load_document_uuids() reescrito para leer del namespace real "document_registry"; CENSUS_FALLBACK_ID agregado como constante fija (394938be-fc42-81e6-a381-e3869e60d89d) ya que CENSUS no vive en el registro. Verificado en producción por el operador: --bootstrap, --check y --sync corridos limpio, CENSUS normalizado de v9.3.1 a v9.3.2.
- Cambio 2 — generate_census.py: auditoría cruzada contra CENSUS_SPEC reveló que DT-016 (v9.2.9) documentó "4 IDs huérfanos incorporados al CENSUS_SPEC" (KERNEL:VERSION-CHECK-TOOL, SP:VERSION-CHECK-TOOL, MANUAL:SESSION-CYCLE-001, MANUAL:PATCH-QUALITY-001) pero el write real nunca se aplicó al script — un Changelog documentando un write que no persistió (mismo patrón que v9.1.1/v9.2.6). Los 4 IDs fueron dados de alta ahora, con verificación real vía re-run (112/112 resueltos, 0 huérfanos, 0 sin-link).
- Cambio 3 — generate_census.py: MANUAL:CHANGELOG-001 retirado de CENSUS_SPEC (el operador eliminó esa sección del Manual — contenido redundante frente al Changelog centralizado). CAREER_CANON:AUDIENCE-SCOPE recibió lookup_ids alterno ["CANON:AUDIENCE-SCOPE"] — el heading real en Career Canon nunca tuvo el prefijo CAREER_CANON, causando "sin link" en cada corrida previa.
- Página ID CENSUS (394938be): actualizada manualmente por el operador en Notion con el output fresco (112/112, 0 huérfanos) — no verificado vía fetch por instrucción explícita del operador.
- Ningún ID canónico de MANUAL/KERNEL/SP fue creado ni retirado en esta entrada — los 4 altas y 1 baja son exclusivamente del namespace local CENSUS_SPEC (script), reflejando estado ya existente en los documentos reales.
- Versión actualizada: 9.3.3.
### v9.3.2 Optimización verify_versions.py — flags --bootstrap/--check/--sync, Terminal obligatorio en Session Cycle
- Fecha: 2026-07-15
- Alcance: MANUAL (MANUAL:SESSION-CYCLE-001, §6 — reescritura completa de Apertura y Cierre), KERNEL (KERNEL:VERSION-CHECK-TOOL — reescritura completa).
- Contexto: el operador optimizó verify_versions.py (antes un solo modo de verificación) para operar con tres flags de responsabilidad exclusiva: --bootstrap (read-only, genera dump de contexto de apertura con última fila del Session Ledger + última entrada de Changelog + pendientes CRÍTICO/ALTO, reemplazando la lectura que antes hacía el AI Component vía MCP), --check (read-only, comportamiento ya documentado, tabla de 7 documentos), y --sync (único modo con escritura — inyecta la versión target del Changelog al VERSION MANIFEST DB 02331706-d2f5-43d1-8166-ed53b690dbd7, housekeeping exento de APROBAR_WRITE por el mismo tratamiento que KERNEL:HEALTH-CHECK-001 y KERNEL:SESSION-LEDGER).
- Cambio 1 — MANUAL:SESSION-CYCLE-001: nueva subsección "Un cambio de fondo: el operador corre Terminal primero, Claude ya no improvisa la verificación", explicando el giro de diseño. Apertura reescrita a 5 pasos que incorporan --bootstrap + --check como payload de entrada al invocar /vantage-session-open (antes: Claude hacía fetch/lectura propia del Ledger y Changelog). Cierre reescrito a 4 pasos que incorporan --sync como paso obligatorio antes de invocar /vantage-session-close. Se elimina la rama de fallback "Terminal no disponible → fetch MCP directo" — Terminal pasa a ser requisito obligatorio, sin downgrade de eficiencia. Ejemplo de output de --check actualizado de versión hardcodeada (9.2.8, obsoleta) a formato genérico X.X.X para evitar que el ejemplo vuelva a quedar desactualizado.
- Cambio 2 — KERNEL:VERSION-CHECK-TOOL: documentado el contrato completo de los tres flags (--bootstrap, --check, --sync), incluyendo el DB ID del VERSION MANIFEST como destino de escritura de --sync y su exención explícita de APROBAR_WRITE. Regla operativa actualizada: se retira la instrucción de "preguntar primero al operador si puede correr el script" — el contrato ahora asume Terminal como prerrequisito no negociable, sin rama de pregunta ni fallback.
- Decisiones congeladas por el operador durante esta sesión (ver hilo): (1) --sync escribe en VERSION MANIFEST y está exento de APROBAR_WRITE por ser housekeeping automático de script local, análogo a Session Ledger/Health Check; (2) se elimina por completo la rama de fallback MCP directo cuando Terminal no está disponible — el pipeline no avanza sin Terminal; (3) el downgrade path "preguntar primero" queda derogado — el operador corre Terminal primero de forma incondicional e inyecta los resultados en el prompt de apertura/cierre.
- Ningún ID canónico (MANUAL:, KERNEL:) fue creado, retirado ni cambió de estado — ambas secciones son reescritura de contenido bajo IDs ya existentes. Census no requiere regeneración (KERNEL:CENSUS-SYNC Regla 1 no se dispara).
- Pendiente identificado, fuera de esta entrada: V | ALIASES (sección "Session Lifecycle") describe el flujo Open/Close en su forma anterior a esta optimización — no refleja --bootstrap/--sync ni el requisito de Terminal obligatorio. Requiere actualización de contenido en sesión futura (no bloquea esta entrada: Aliases recibe el bump de versión de esta sesión por SP:SYNC-RULE, pero su contenido queda desactualizado respecto al nuevo contrato).
- Resultado: MANUAL y KERNEL alineados al nuevo contrato de verify_versions.py. 0 huerfanos, 0 IDs afectados.
- Versión actualizada: 9.3.2.
### v9.3.1 Manual §16-19 — Reglas de Oro CV, Positioning Modes, Golden Skeleton, Schema Class A/B (referencia por ID) + alta de ARCHIVO TASK TRACKER en Cédula Digital
- Fecha: 2026-07-14
- Alcance: MANUAL (§16-19, nuevas), SYSTEM PROMPT (SP:CEDULA-DIGITAL), TASKS TRACKER / ARCHIVO TASK TRACKER.
- Cambios:
- MANUAL §16: índice de navegación hacia KERNEL:CV-GOLDEN-RULES (5 reglas + template de rechazo) — sin duplicar el contrato completo, solo tabla de qué activa cada regla.
- MANUAL §17: criterio de selección Positioning Modes N1–N4 (CANON:POSITIONING-001), con ancla canónica y cuándo aplica cada modo + regla de desempate para JDs híbridos.
- MANUAL §18: qué es y dónde vive el Golden Skeleton (CANON:OUTPUT-CONTRACT-SKELETON-001) — slots clave, SSOT registry_seed.json, regla de invariancia.
- MANUAL §19: tabla de referencia Class A/B (KERNEL:SCHEMA-001) + nota de que los pesos de Score/VM_Scope viven en profile_config.yaml, no en el Manual.
- Ningún ID canónico (MANUAL:, KERNEL:, CANON:*) fue creado ni cambió de estado — las 4 secciones son contenido de referencia nuevo, no redefinición. Census no requiere regeneración (KERNEL:CENSUS-SYNC Regla 1 no se dispara).
- SP:CEDULA-DIGITAL: alta de ARCHIVO TASK TRACKER (DB c2698a3e-50c8-4d92-a2a1-756d9aaed2d2 / COL c470ead7-465b-4375-9469-c48534559657) — base de datos existente, no documentada previamente en la Cédula.
- Tasks Tracker: 3 tickets ALTO (huecos de la reestructuración V-MANUAL v9.3.0 — DT-017) marcados Hecho y movidos a ARCHIVO TASK TRACKER.
- Resultado: Manual con 4 secciones nuevas de referencia, 0 huérfanos, 0 huecos ALTO pendientes de la reestructuración anterior (quedan 2 MEDIO + 1 BAJO, ver Tasks Tracker).
- Versión actualizada: 9.3.1.
### v9.3.0 Reestructuración narrativa de V-MANUAL (journey-based) + deprecación de §CHANGELOG duplicado
- Fecha: 2026-07-14
- Alcance: MANUAL (reordenamiento completo de §1–§17).
- Cambios:
- Contenido promovido desde V-MANUAL (PROPOSAL) (39d938be-fc42-8054-8b3a-ce1c87c85fc6), vía escritura manual del operador.
- Reorganización siguiendo el journey real del operador: Objetivo → Cómo Funciona → Filosofía de Fallo (adelantada desde §13 a §3) → Setup → Arranque Frío → Ciclo de Sesión (MANUAL:SESSION-CYCLE-001, adelantado desde §5.6 a §6) → Checklist → Flujo Semanal → Runtime → Gestión de Datos → Health Check → Troubleshooting → Prompts & Wrappers → Cheat Sheets → Criterio de Calidad → Reglas de Oro → SLA.
- Ningún ID (MANUAL:*) fue creado, retirado ni renumerado en su clave — solo reubicados en el documento. Census no requiere regeneración (sin cambio de estado de IDs).
- DEPRECADO: sección Changelog duplicada dentro de V-MANUAL (antes §11, luego §18 en el proposal). El registro canónico de versiones vive únicamente en V-CHANGELOG — mantener una copia secundaria en el Manual generaba drift documental (precedente: confusión "Cheat Sheet" vs Aliases, v9.1.9). No se promovió al Manual restructurado.
- Fusiones de contenido disperso sin ID propio: "Gate Decisions" (dentro de §2), "Antes de Lunes" (dentro de §6), comandos vl1 (dentro de §9.2) — ver tabla de mapeo completa en el proposal fuente.
- Resultado: V-MANUAL reestructurado, mismo set de 16 IDs, 0 huérfanos nuevos.
- Pendiente (fuera de esta entrada): 11 huecos detectados durante la reestructuración (referencias a Kernel/Career Canon no desarrolladas en el Manual) — ver Tasks Tracker.
- Versión actualizada: 9.3.0.
### v9.2.9 Integración de Session Lifecycle al Manual y Aliases
- Fecha: 2026-07-14
- Alcance: MANUAL (§4, §5.6, §9), ALIASES (nueva sección Session Lifecycle), V-ID-CENSUS.
- Cambios:
- MANUAL §4: nueva introducción "Antes de Lunes — El Ciclo de la Sesión Misma", ancla el ciclo /vantage-session-open → /vantage-session-close antes del ciclo semanal.
- MANUAL §5.6 (nuevo): MANUAL:SESSION-CYCLE-001 — detalle narrativo completo de apertura/cierre de sesión, con ejemplos de output y tabla de troubleshooting.
- MANUAL §9: MANUAL:PATCH-QUALITY-001 — Criterio de Calidad para Parches Documentales (5 filtros: invisibilidad estructural, continuidad de voz, progresión narrativa, diff mínimo, coherencia transversal).
- ALIASES: nueva sección "Session Lifecycle" — /vantage-session-open, /vantage-session-close, verify_versions.py --check.
- V-ID-CENSUS: 4 IDs huérfanos incorporados al CENSUS_SPEC (KERNEL:VERSION-CHECK-TOOL, SP:VERSION-CHECK-TOOL, MANUAL:SESSION-CYCLE-001, MANUAL:PATCH-QUALITY-001).
- Resultado: Census 109/109 resueltos, 0 huérfanos.
- Versión actualizada: 9.2.9.
### v9.2.8 — 2026-07-14
- V | SESSION LEDGER creada en Notion (38324240-c686-47d0-8082-cee5e4409f88), bajo V | ARCHIVEROS
- VERSION MANIFEST y SESSION LEDGER registrados en SP:CEDULA-DIGITAL (write verificado)
- vantage-session-open/SKILL.md y vantage-session-close/SKILL.md reescritos y guardados en disco (20/22 líneas, referencian verify_versions.py --check/-sync real y el Ledger ID real)
### v9.2.7 — 2026-07-14
SPRINT 1 - CIERRE
Tickets Completados
- [TCK-04] - CE-01/CE-02 - Write-Back Verification
- Añadido Write-Back Verification a SKILL-CLOSE (§1 y §3.5)
- Nuevo comportamiento: Re-fetch después de cada write + detección de WRITE-BACK MISMATCH
- Dogfooded exitosamente. Detectó mismatch real de ALIASES (v9.2.5 vs v9.2.6) y permitió su corrección
Artefactos creados
- Creación de Layer_1/scripts/verify_versions.py
- Script de validación de versiones de los 7 documentos fundacionales
- Ejecutado en producción. Resultado: 7/7 documentos en v9.2.6
- Canonización de KERNEL:VERSION-CHECK-TOOL
- Documento kernel creado para documentar la herramienta de verificación de versiones.
- Creación de ARCHIVO CHANGELOG
- Archivo histórico creado por el operador
- Migración de todas las entradas pre-v9.1.0 desde V-CHANGELOG.
Verificación
- Verificación ejecutada con verify_versions.py post-cambios: 7/7 @ v9.2.7
- No se modificaron campos Class B. Solo canon updates + housekeeping.
Notas
- Sprint 0: CERRADO
- Sprint 1: CERRADO (tras esta entrada)
### v9.2.6 — 2026-07-14
[FEATURE] TCK-04 — Write-Back Verification implementado en vantage-session-close.md.
- Contexto: SKILL-CLOSE carecía de verificación transaccional post-escritura.
Un Changelog documentando un write no era evidencia de que el write
hubiera persistido (precedente: v9.1.1, repetido con el Census el
2026-07-13/14).
- Cambio — vantage-session-close.md (Skills/):
· Nuevo §3.5 "Write-Back Verification": re-fetch de solo lectura de la
propiedad Versión de los 6 fundacionales + Changelog inmediatamente
después de escribir, comparando contra el valor esperado. Si hay
mismatch, FAIL — WRITE-BACK MISMATCH, no avanza a §4 sin resolución
(KERNEL:FAIL-PHILOSOPHY: reportar, no reintentar automático).
· §1 (Inventory): cada Notion write reportado se re-fetchea y confirma
antes de incluirse en "COMPLETADO ESTA SESIÓN" (paso 5).
- Verificación: patches aplicados y confirmados vía cat -evt + comparación
Python UTF-8 explícita (dos rondas — el primer grep dio falso negativo
por problema de locale/encoding, resuelto forzando lectura UTF-8).
- Census: regenerado antes de este Changelog (109/109, 0 huérfanos) — sin
impacto en IDs, cambio de skill local, no de canon.
- Versión: v9.2.5 → v9.2.6. Los 6 documentos fundacionales normalizados
a v9.2.6 en la misma operación (SP:SYNC-RULE — Regla de Versión Única).
Pendiente que sigue abierto: TCK-05 (CRÍTICO — mitigación interina Class B
Guard, GAP-03).
## v9.2.5 - 2026-07-14
[FEATURE] generate_census.py — reformateo del output a estructura curada por el operador.
- Contexto: el .md generado usaba tabla de 1 sola columna (ID) sin agrupamiento visual claro. El operador reformeteó a mano la página de Notion del Census (394938be) con una estructura de lectura preferida: subtítulo ## por documento, tabla de 3 columnas (ID · Sección · Nombre), separador --- entre bloques, sin columna de estatus. Decisión del operador: el formato bonito es la fuente autoritativa; el script se adapta a él, no al revés.
- Cambio — CENSUS_SPEC: las 109 filas recibieron los campos seccion y nombre, poblados vía auditoría cruzada TOC-vs-body de los 4 documentos fundacionales (KERNEL, SYSTEM PROMPT, MANUAL, CAREER CANON), ejecutada por Perplexity/Sonnet 5 bajo contrato de sesión con gates DRY RUN + APROBAR_WRITE, verificada por Claude antes de la inyección.
- Cambio — render_markdown(): reescrito para producir subtítulo ## por documento + tabla de 3 columnas + separador ---, en vez de la tabla plana de 1 columna anterior.
- Verificación: py_compile sin errores. Corrida en producción del operador (2026-07-14 02:24): 109/109 IDs resueltos, 0 sin link, 0 huérfanos. Formato de salida confirmado visualmente contra el .md real — coincide con la estructura objetivo.
- Versión: v9.2.4 → v9.2.5. Los 6 documentos fundacionales normalizados a v9.2.5.
---
## v9.2.4 - 2026-07-13
[FIX] generate_census.py — falso positivo de huérfano retirado filtrado (MANUAL:DASHBOARD-CHECKLIST-001).
- Contexto: el generador reportaba MANUAL:DASHBOARD-CHECKLIST-001 como huérfano en cada corrida desde v9.1.6. El ID fue retirado formalmente esa versión (dividido en MANUAL:VCHECKLIST-001 + MANUAL:DASHBOARD-001), pero su nombre persiste como texto narrativo dentro de la propia entrada del Change Log que documenta el retiro. find_orphan_ids() marcaba esa mención como is_def=True (definición nueva) en vez de reconocerla como narración histórica de un retiro ya cerrado — mismo tipo de falso positivo que v9.2.0 ya había calificado como "ruido documentado, no requiere acción", pero sin mecanismo de código para suprimirlo en corridas futuras.
- Cambio — generate_census.py (Layer_1/scripts/): nueva constante KNOWN_RETIRED_NOISE (set de IDs retirados y documentados). find_orphan_ids() excluye estos IDs antes de evaluar is_def, sin tocar la lógica de detección de huérfanos reales.
- Verificación: py_compile sin errores. Re-run del operador en producción (2026-07-13 01:59): 109/109 IDs en spec resueltos, 0 sin link, 0 huérfanos (antes: 1 huérfano constante).
- Versión: v9.2.3 → v9.2.4. Los 6 documentos fundacionales normalizados a v9.2.4 en la misma operación (ver SP:SYNC-RULE — Regla de Versión Única).
---
> El histórico completo del CHANGELOG lo podrás encontrar en ARCHIVO CHANGELOG, en esta pagina de consulta continua solo encontrarás las últimas diez entradas para garantizar la operación y referencia del sistema.

