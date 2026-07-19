# V | CHANGELOG

---
### v9.5.8 — KERNEL:SKILL-ANNOUNCE-CONVENTION · 2026-07-19
Tipo: [DOC]
Descripción:
Actualización de la tabla "Implementación actual" en KERNEL:SKILL-ANNOUNCE-CONVENTION para incluir 5 nuevos skills:
- vantage-create-bug-task (TICKETING.../TICKET CREADO o TICKETS CREADOS si es batch)
- vantage-present-handoff (HANDING OFF.../HANDOFF ENTREGADO)
- vantage-tidy-changelog (LOGGING CHANGES.../CHANGELOG ACTUALIZADO)
- vantage-tidy-bug-task-tracker (SWEEPING TICKETS.../TICKETS AL DÍA)
- vantage-tidy-opportunities-tracker (DEDUPING TRACKER.../TRACKER SINCRONIZADO)
Contexto:
- Regla de mantenimiento: Según KERNEL:SKILL-ANNOUNCE-CONVENTION, cualquier cambio en la convención debe listar el Kernel y cada .skill afectado en el mismo alcance.
- Consistencia: Todos los skills siguen el formato X-ING.../X-ED (o equivalente), alineado con la filosofía de evitar ambigüedad de alcance (ver Changelog v9.5.0–v9.5.1).
Criterios de aceptación:
| # | Criterio | Estado |
| --- | --- | --- |
| 1 | Texto en KERNEL:SKILL-ANNOUNCE-CONVENTION actualizado con los 9 skills. | ✅ |
| 2 | Mensajes de inicio/cierre de los nuevos skills coinciden con lo declarado en sus archivos .skill. | ⏳ Pendiente validación |
| 3 | Entrada en Changelog registrada con formato canónico. | ⏳ Pendiente aplicación |
Archivos afectados:
- V | KERNEL (sección KERNEL:SKILL-ANNOUNCE-CONVENTION)
- [V | CHANGELOG](https://app.notion.com/p/390938befc4280e7b429d7d730339353) (esta entrada)
- Archivos .skill de los 5 nuevos skills (validación pendiente).
### v9.5.7 — 2026-07-19
Alcance: Cierre de Fase C de la auditoría de skills VANTAGE (R-06b, R-13, R-15, R-08b) + formalización de tag canónico en Kernel.
Kernel: KERNEL:CENSUS-SYNC §20, Regla 1 — formalizado el tag literal [CENSUS-SYNC-R1] como referencia canónica que cualquier skill debe citar textualmente al referenciar esta obligación, en vez de paráfrasis libres por skill (cierra R-13).
Infraestructura (Layer_1/, local): resolver_registry_v2.json — nueva entrada CHANGELOG_ARCHIVE en document_registry, resolviendo al UUID del Archivo Changelog. generate_census.py y normalize_heading_ids.py — VALID_PREFIXES extendida con CHANGELOG_ARCHIVE: en ambos scripts, cerrando el gap donde el Registry reconocía el alias pero el resto del pipeline lo hubiera rechazado como prefijo inválido (cierra R-06b).
Skills (vantage-tidy-changelog, vantage-tidy-bug-task-tracker, vantage-tidy-opportunities-tracker, vantage-create-bug-task): migración de los 2 UUIDs hardcodeados del Changelog a notación CHANGELOG:/CHANGELOG_ARCHIVE: en vantage-tidy-changelog (R-06b); tag [CENSUS-SYNC-R1] citado en vez de string libre en vantage-create-bug-task y vantage-tidy-bug-task-tracker (R-13); referencias posicionales ("Skill N") reemplazadas por nombres reales de archivo en los 5 skills — incluye una corrección de contenido real: la obligación de Regla 1 de CENSUS-SYNC se atribuía incorrectamente a vantage-tidy-changelog en vez de vantage-create-bug-task (R-15); manejo explícito de fallo parcial en operaciones multi-paso (append+edición en vantage-tidy-changelog, crear-copia+marcar-original en vantage-tidy-opportunities-tracker) — estado intermedio documentado como recuperable, sin reintentar el paso ya exitoso (R-08b).
Write-Back Verification: re-fetch de Kernel tras la escritura de §20 — sin mismatch, tag y línea de referencia cruzada confirmados verbatim.
Census: regenerado en Terminal por el operador — 120/120 IDs resueltos, 0 huérfanos, 0 sin link.
IDs afectados: ninguna alta de ID canónico nuevo — [CENSUS-SYNC-R1] es un tag de referencia cruzada dentro de Regla 1 existente, no un ID PREFIX:CLAVE nuevo del DOC-CONTRACT; el Census no lo indexa como entidad, comportamiento confirmado correcto en la regeneración de esta entrada.
Discrepancia detectada (SP:CONSISTENCY): al inicio de esta sesión, SYSTEM PROMPT e ID CENSUS reportaban v9.5.5 vía notion-fetch, un paso atrás de la versión real del Changelog (v9.5.6, ya escrita en la entrada anterior a esta). Causa no diagnosticada en esta sesión — posible verify_versions.py --sync no corrido tras v9.5.6, o drift de caché de fetch. Pendiente investigar antes de asumir que el próximo --sync corrige automáticamente el origen del drift, no solo el síntoma.
Pendiente (fuera de esta entrada): R-12b — actualizar KERNEL:SKILL-ANNOUNCE-CONVENTION §3 para incluir los 5 skills de housekeeping en la tabla "Implementación actual"; Fase D — patch a KERNEL:GATE-DECISION-003 punto 6 (DRY RUN debe reconstruirse, ya no vive en contexto activo); diagnóstico de la causa raíz del drift de versión SP/Census vs. Changelog señalado arriba.
Versión actualizada: 9.5.7 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.5.5/v9.5.6 (discrepancia ya señalada arriba) hasta que el operador corra verify_versions.py --sync.
---
### v9.5.6 — 2026-07-18
Alcance: Segunda vuelta de fixes técnicos ejecutados por Devin: Auto-Archivado (Bug Crítico, CERRADO), JD Null Audit (Bug Medio, causa raíz identificada, requiere task nuevo), Normalize URL (verificación de regresión, sin cambios).
Contexto: Continuidad de v9.5.5. El operador dio el prompt final a Devin con 3 objetivos, corrigiéndolo previamente para usar la condición real de Gate (KERNEL:GATE-DECISION-007) en vez de una condición inventada, separar dry-run de execute con gate de aprobación explícita, y evitar reimplementar el fix de Normalize URL ya resuelto en v9.5.3.
Cambios:
- Auto-Archivado (Bug Tracker, CERRADO): Devin confirmó uso correcto de NOTION_TOKEN desde el entorno (auto_archive.py línea 39). Dry-run confirmó los mismos 2 candidatos ya validados en v9.5.4 (Promotwist SC y Zegna, mismos Page IDs), sin candidatos nuevos ni inesperados. Aprobación explícita del operador (APROBAR_WRITE) antes de execute. Ejecución real: página mensual 2026-07 JULY creada, ambos registros archivados sin errores.
- JD Null Audit (Bug Medio, hallazgo estructural — NO cerrado): Devin descartó la ruta asumida en el prompt (Layer_2/wrappers/) y confirmó vía find que no existe un directorio de código Layer_2 separado — aclaración del operador: Layer 2 es una capa metodológica, no de código (búsquedas vía Perplexity+Comet en LinkedIn/Aggregators/Career Sites), y comparte el mismo núcleo operativo que Layer 1 (los scripts en Layer_1/scripts/). Esto es consistente con el schema real de Notion — tanto Bug Tracker como Tasks Tracker ya tenían "Layer 2" como opción de select en Componente antes de esta sesión, y el Tracker de vacantes tiene un campo layer con opciones L1/L2/L3. Causa raíz real: layer_1_run.py (validate_url_pre_ingestion()) y feed_processor.py (_first_nonempty()) solo consumen el campo JD ya vacío — el problema está en los prompts/flujos de discovery (A-Gemini, A-Grok, A-You.com para L1; Perplexity+Comet para L2), que no extraen el JD del HTML/resultado.
- Normalize URL (verificación de regresión, sin cambios de código): confirmado que el fix de v9.5.3 sigue vigente en feed_processor.py línea 238 — implementación real es path = parsed.path.rstrip("/").lower() or "/" (más completa que la descripción original de v9.5.3, que solo mencionaba .lower(); se deja constancia aquí para que el registro histórico sea exacto). 7/7 tests de regresión pasan, verificado contra datos reales de Notion (Electrónica Confidencial, hashes idénticos), sin duplicados fantasma detectados.
Task nuevo (Tasks Tracker): "Auditar scripts de discovery upstream (you.com/Grok/LinkedIn) — job_description llega NULL en algunos registros" (3a1938be-fc42-8172-bcbc-cd8e8cf2ec81), Componente: Layer 1, Next_Action: Definir, Prioridad: MEDIO, Status: Pendiente.
Write-Back Verification: Task nuevo confirmado por respuesta de la API de creación, sin mismatch. No se tocó ningún documento fundacional en esta entrada más allá de este Changelog.
IDs afectados: ninguno nuevo en los fundacionales — el hallazgo de Layer 2 como capa metodológica (no de código) queda documentado aquí pero no dispara alta en Kernel; queda como candidato a documentación transversal si el operador decide formalizarlo en KERNEL:ARCHITECTURE. Census no requiere regeneración.
Pendiente (fuera de esta entrada): ejecutar el task nuevo de auditoría de discovery upstream; decisión del operador sobre si formalizar la distinción L1/L2 (metodología, mismo núcleo de código) en el Kernel vía vantage-documentacion-transversal; pendientes heredados de v9.5.4 (cross_tracker_match.py Caso 3, decisión sobre Dedup_Flag en SCHEMA-001).
Versión actualizada: 9.5.6 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.5.5 hasta que el operador corra verify_versions.py --sync.
---
### v9.5.5 — 2026-07-18
Alcance: Fix de generate_census.py (Layer_1/scripts/, no fundacional) — alta en spec de 2 IDs huérfanos detectados en Kernel §9 y corrección de 1 ID mal declarado en spec (Bootstrap).
Contexto: Continuidad de v9.5.4. El re-run de vcensus tras el alta de KERNEL:GATE-DECISION-007/-008 (documentada en v9.5.4) reportó ambos IDs como huérfanos — existían en el Kernel real pero no en CENSUS_SPEC del script, confirmando que la Regla 2 de KERNEL:CENSUS-SYNC seguía pendiente de cierre. En el mismo diagnóstico se detectó un segundo defecto no relacionado: CENSUS_SPEC declaraba KERNEL:BOOTSTRAP-001, un ID que nunca existió con ese nombre exacto en el Kernel — el ID real es KERNEL:ARCHITECTURE-L0-BOOTSTRAP (§3), verificado por fetch en vivo antes de tocar el script.
Cambios:
- generate_census.py: agregadas al CENSUS_SPEC las filas KERNEL:GATE-DECISION-007 (§9.7 — Ejecución Automática de Archivado) y KERNEL:GATE-DECISION-008 (§9.8 — Capas de Evaluación de Gate: Técnica vs. Negocio), con nombres tomados verbatim del Kernel.
- generate_census.py: corregida la fila KERNEL:BOOTSTRAP-001 → KERNEL:ARCHITECTURE-L0-BOOTSTRAP (§3 L0-B), alineando el spec al ID real ya escrito en el Kernel — consistente con KERNEL:CENSUS-SYNC ("el Census audita a los documentos fuente, no al revés").
- Re-run de vcensus confirmado por el operador en Terminal: 120/120 IDs resueltos, 0 huérfanos, 0 sin link.
Write-Back Verification: no aplica a escritura en Notion — el fix es local (Layer_1/scripts/generate_census.py, fuera del alcance de sync bidireccional de vdoc). Verificación fue el propio output de vcensus en Terminal, confirmado por el operador en corridas sucesivas (detección de huérfanos → alta en spec → 0 huérfanos → detección de mismatch Bootstrap → corrección → 120/120 limpio).
IDs afectados: ninguno nuevo en Notion — los 2 IDs (KERNEL:GATE-DECISION-007/-008) ya habían sido dados de alta en el Kernel real en v9.5.4; esta entrada cierra su reflejo pendiente en el Census (KERNEL:CENSUS-SYNC Regla 2). KERNEL:ARCHITECTURE-L0-BOOTSTRAP tampoco es alta — ya existía en el Kernel desde v9.5.0.
Pendiente (fuera de esta entrada): los pendientes heredados de v9.5.4 (execute de auto_archive.py para Promotwist/Zegna; cross_tracker_match.py Caso 3; decisión sobre Dedup_Flag en SCHEMA-001) siguen abiertos, no tocados en esta sesión.
Versión actualizada: 9.5.5 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.5.3 hasta que el operador corra verify_versions.py --sync.
---
### v9.5.4 — 2026-07-18
Alcance: Cierre del ticket de Dedup (Bug Tracker 39b938befc4281efa1ccdd5d763bfdbf, pendiente solo execute), cierre del ticket de Suite de Tests Unitarios (Tasks Tracker 3a1938befc4281ca8ebcddf246425981 → Hecho), alta de 2 IDs nuevos en Kernel §9 (KERNEL:GATE-DECISION-007, KERNEL:GATE-DECISION-008).
Contexto: Continuidad de la sesión v9.5.3. Devin ejecutó los 2 prompts pendientes (Dedup completo + Suite de tests). Ambas respuestas fueron auditadas cruzando el ticket original y el código real antes de aceptarlas — no se dieron por buenas de palabra.
Cambios:
- Dedup (Bug Tracker, sigue Abierto — pendiente solo execute): Devin implementó y verificó los 4 frentes del prompt final: (1) auto_archive.py — dry-run confirmó 2 candidatos legítimos: Promotwist (control positivo) y Zegna (397938be-fc42-8124-8b10-def44d530da8, Next_Action='Archivar' y Dedup_Flag='Posible duplicado' verificados en vivo en Notion — corresponde al registro CSV público REVIEW_NEEDED, no al Inbound real ya cerrado). Confirmado sin cruce de lógica con cross_tracker_match.py (grep). (2) content_fingerprint()/dedup_by_content_fingerprint() resuelve Caso 4b (GILSA) — 3/3 tests pasando. (3) cross_tracker_match.py diseñado para Caso 3 (Zegna, cruce Inbound↔público) — pendiente implementación completa. (4) verify_dedup_fix.py confirmó contra Notion real que Casos 1 y 2 ya funcionaban sin cambios adicionales.
- Suite de Tests Unitarios (Tasks Tracker, CERRADO): 77 tests (16 dedup + 36 gate logic + 25 scoring), auditoría de código real confirmó nombres de función no inferidos (gate_logic(), evaluate_gate(), gate() en layer_1_run.py, calculate_score_v6(), get_score_band()). GILSA confirmado validando content_fingerprint() (línea 214 de test_dedup.py), no normalize_url() — README corregido tras señalamiento explícito.
- Kernel §9 (KERNEL:GATE-DECISION) — 2 altas: KERNEL:GATE-DECISION-007 (mecanismo de ejecución automática de archivado vía auto_archive.py, condición Next_Action='Archivar' + Dedup_Flag='Posible duplicado') y KERNEL:GATE-DECISION-008 (distinción arquitectónica confirmada: gate() capa técnica vs. gate_logic() capa de negocio/workflow — no son duplicación). Ambos anclan conocimiento que hasta esta sesión solo existía en chat/Censo.
Hallazgo pendiente de decisión del operador (no ejecutado en esta entrada): Dedup_Flag aparece en la lista de campos Class B protegidos de KERNEL:CV-GOLDEN-RULES-002, pero no en la lista canónica Class B de KERNEL:SCHEMA-001 — inconsistencia pre-existente, no causada por esta sesión, señalada por SP:CONSISTENCY.
Write-Back Verification: re-fetch de Kernel tras la escritura de §9 — sin mismatch, ambas secciones confirmadas verbatim.
IDs afectados: alta de KERNEL:GATE-DECISION-007 y KERNEL:GATE-DECISION-008 — dispara KERNEL:CENSUS-SYNC Regla 1, Census requiere regeneración antes de dar por cerrados los tickets asociados a estos IDs.
Pendiente (fuera de esta entrada): aprobar execute de auto_archive.py para los 2 candidatos confirmados (Promotwist, Zegna); dar de alta implementación completa de cross_tracker_match.py (Caso 3) como task separado; decisión del operador sobre el hallazgo de Dedup_Flag en SCHEMA-001; re-run de generate_census.py para reflejar los 2 IDs nuevos.
Versión actualizada: 9.5.4 (Kernel y Changelog). El resto de los fundacionales (Manual, Career Canon, System Prompt, Aliases, Census) permanece en v9.5.3 hasta que el operador corra verify_versions.py --sync.
---
### v9.5.3 — 2026-07-18
Alcance: 3 quick wins del handoff SESSION-2026-07-17-B: fix --bootstrap (SP:SYNC-RULE/KERNEL:CENSUS-SYNC, Census como 7º fundacional) y 2 fixes de dedup en feed_processor.py.
Contexto: SESSION-2026-07-18-A (Ledger). Auditoría de 3 quick wins (<5 iteraciones) propuestos en el handoff de la sesión anterior, verificados contra el código real (verify_versions.py, feed_processor.py, subidos por el operador) antes de tocar nada.
Cambios:
- Quick win #1 — Bug Tracker (registrado y Resuelto): get_priority_tickets() en verify_versions.py (Layer_1/scripts/, local) filtraba tickets ALTO/CRÍTICO solo por Prioridad, sin excluir Status terminal — causaba falsos positivos en el dump de --bootstrap (caso confirmado: ticket ya Resuelto seguía apareciendo). Fix: agregado filtro and con does_not_equal por Status, diferenciado por tracker vía dict closed_statuses_by_label (Bug: Resuelto · Task: Hecho/Completado — labels reales confirmados en main()). Verificado en producción: dump bajó de 10 a 8 tickets tras el patch, coincidiendo con el handoff.
- Quick win #2 — SP:SYNC-RULE + KERNEL:CENSUS-SYNC (Task, resuelto sin ticket formal — aclaración documental): discrepancia de conteo de documentos fundacionales (5/6/7) entre SP:SYNC-RULE (6), SP:VERSION-CHECK-TOOL (7) y el propio canon del operador ("Census NO es fundacional"). Resuelto por decisión explícita del operador: ID CENSUS pasa a ser el séptimo documento fundacional, sujeto a la misma Regla de Versión Única que los otros seis. Patch en SP:SYNC-RULE (bootstrap universal sigue recuperando solo SP+Census; la verificación de versión de los 7 fundacionales es un paso distinto, vinculado a vantage-session-open) y en KERNEL (KERNEL:CENSUS-SYNC §20, KERNEL:ARCHITECTURE-L4, KERNEL:VERSION-CHECK-TOOL §23 — este último corregido para reflejar el comportamiento real del código: DOC_KEYS en verify_versions.py ya incluía CENSUS y --sync ya ejecutaba 7 patches, no 6; la discrepancia era puramente documental, no de código).
- Quick win #3 — Bug Tracker (ticket original actualizado, NO cerrado): ticket 39b938be-fc42-81ef-a1cc-dd5d763bfdbf ("Dedup no detecta registros duplicados del Tracker", 5 casos documentados) recibía atención parcial — se mantiene Abierto. Dos de cinco causas resueltas en feed_processor.py: (a) normalize_url() no aplicaba .lower() al path (solo a netloc), rompiendo dedup entre URLs idénticas con distinta capitalización de path (Caso 1, Electrónica Confidencial) — fix de una línea, verificado en producción (MATCH: True); (b) dedup_cross_layer() filtraba title vía equals case-sensitive de la API de Notion, fallando en republicación cross-portal con distinta capitalización de título (Caso 2, Vinos La Naval) — fix: el filtro de Notion ya solo usa brand (ya canonizado por resolve_alias()) + ventana temporal; title se compara en Python normalizado post-fetch, con extracción robusta a runs multi-rich_text. Verificado en aislamiento con datos sintéticos (4 casos: match case-insensitive, espacios extra, no-falso-positivo, extracción multi-run) — no verificado aún contra Notion real, pendiente confirmación con caso vivo. Sin tocar: Caso 3 (falta cruce Inbound↔público, Zegna), Caso 4b (jk rotativo de Indeed, requiere fingerprint de contenido), y el bug transversal de Caso 5 (Next_Action=Archivar nunca se ejecuta automáticamente — probablemente el de mayor impacto acumulado, sigue enteramente abierto).
Write-Back Verification: re-fetch de SP, Kernel y del ticket de dedup tras cada escritura — sin mismatch en ninguno.
IDs afectados: ninguno nuevo — los tres cambios son reescritura de contenido bajo IDs ya existentes (SP:SYNC-RULE, KERNEL:CENSUS-SYNC, KERNEL:ARCHITECTURE-L4, KERNEL:VERSION-CHECK-TOOL) y patches de código local (no fundacional). Census no requiere regeneración.
Pendiente (fuera de esta entrada): verificar en producción real el fix de dedup cross-portal (Caso 2) con un caso vivo de republicación; los 7 tickets ALTO restantes del handoff (System Prompt inferencias, Git Infrastructure, hyperlinks cruzados en Kernel/Manual, inventario de referencias cruzadas, RT-1/STATIC BOOTLOADER, tests unitarios) permanecen abiertos, no tocados en esta sesión; Caso 3/4b/5 del ticket de dedup.
Versión actualizada: 9.5.3 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.5.2 hasta que el operador corra verify_versions.py --sync.
---
### v9.5.2 — 2026-07-18
Alcance: KERNEL §3 (alta de KERNEL:SKILL-ANNOUNCE-CONVENTION), Tasks Tracker + ARCHIVO TASK TRACKER (cierre de ticket Ledger huérfano), Bug Tracker (registro de bug nuevo: --bootstrap sin filtro de Status).
Cambios:
- KERNEL: nuevo nodo KERNEL:SKILL-ANNOUNCE-CONVENTION en §3, verificado por re-fetch sin mismatch (sesión 2026-07-17-B).
- Tasks Tracker: ticket "Revisar skill vantage-session-open — Ledger huérfano" cerrado (Status: Hecho), copia migrada a ARCHIVO TASK TRACKER (3a1938be-fc42-810d-ae99-f2666a61e565).
- Archivado real (API archived:true) del ticket original (3a0938be-fc42-813c-92de-cb9e9c86e1da) sigue PENDIENTE — falló por token inválido (401), resolver NOTION_TOKEN contra Layer_1/config/layer_1.env antes de reintentar.
- Bug Tracker (pendiente, no ejecutado en esta sesión): registrar bug "verify_versions.py --bootstrap no filtra Status resuelto/hecho" — detectado, no escrito aún.
Write-Back Verification: pendiente de confirmar en esta misma sesión tras el write.
IDs afectados: alta de KERNEL:SKILL-ANNOUNCE-CONVENTION.
Pendiente (fuera de esta entrada): cerrar Ledger de SESSION-2026-07-17-B (en curso); resolver NOTION_TOKEN antes de reintentar archivado; registrar bug de --bootstrap sin filtro Status.
Versión actualizada: 9.5.2 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.5.1 hasta que el operador corra verify_versions.py --sync.
---
### v9.5.1 — 2026-07-18
Alcance: Skills locales (fuera de Notion, no fundacionales — no dispara KERNEL:CENSUS-SYNC): vantage-session-open, vantage-session-close, vantage-documentacion-transversal, prompt-master, tailored-resume-generator.
Contexto: continuidad del trabajo de v9.5.0. Se detectó que el fix de convención de anuncio (X-ING → X-ED) diseñado y validado en la sesión de Notion previa (2026-07-18) nunca había persistido en el filesystem real del operador — los archivos montados seguían con artefactos de mojibake ([span_x]) y, en el caso de vantage-session-open/vantage-session-close, con un UUID de Session Ledger divergente (8d736032-eef9-4e6e-a05a-df8b8079ebff) del canónico (38324240-c686-47d0-8082-cee5e4409f88) — causa probable de que las filas del Ledger quedaran huérfanas sin cerrar.
Cambios:
- vantage-session-open: agregado paso 0 SESSION-OPENING... / cierre SESSION-OPENED: VANTAGE READY; UUID de Session Ledger corregido al canónico; artefactos de mojibake eliminados.
- vantage-session-close: agregado paso 0 CLOSING SESSION... / cierre SESSION CLOSED -> nuevo chat.; mismo fix de UUID y mojibake.
- vantage-documentacion-transversal: agregado anuncio BEGINNING DOCUMENTATION... / DOCUMENTATION FINISHED.
- prompt-master: agregado anuncio PROMPTING... / PROMPT FINISHED, con nota explícita de que va fuera del bloque de prompt copiable.
- tailored-resume-generator: sin cambios — ya traía el anuncio correcto.
Incidente de proceso (honestidad estructural): en esta misma sesión, antes de leer el handoff completo de la sesión de Notion, Claude entregó una primera versión de estos skills con un fix incompleto (solo limpieza de mojibake) presentado como definitivo. Se generó un Contrato de Sesión documentando la falla y reglas de refuerzo (R1–R5) para prevenir recurrencia — no se escribe a Notion, vive como artefacto de sesión entregado al operador.
Write-Back Verification: no aplica — cambios son locales, fuera de Notion.
IDs afectados: ninguno. Census no requiere regeneración.
Pendiente (fuera de esta entrada): dar de alta KERNEL:SKILL-ANNOUNCE-CONVENTION en el Kernel (nodo junto a KERNEL:ARCHITECTURE-L0-BOOTSTRAP) para formalizar la convención de anuncio como regla transversal — no ejecutado, pendiente de decisión del operador sobre alcance. Confirmar en sesión real que el operador subió los 5 .skill corregidos y que el ciclo open→close cierra la fila del Ledger sin quedar huérfana.
Versión actualizada: 9.5.1 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en v9.5.0 hasta que el operador corra verify_versions.py --sync.
---
### v9.5.0 — 2026-07-17
Alcance: KERNEL:ARCHITECTURE-L0-BOOTSTRAP (§3) — convención de estado del Bootstrap y distinción de alcance frente al Session Ledger.
Contexto: el operador identificó un patrón de riesgo de 5 sesiones consecutivas sin fila nueva en Session Ledger al invocar /vantage-session-open. Diagnosticado en esta sesión: el Bootstrap universal (Project Instructions, copy fuente en SP:BOOTSTRAP-001) cierra con "VANTAGE: SISTEMA SINCRONIZADO" — casi idéntico al cierre real del skill vantage-session-open ("VANTAGE READY") — lo que hacía que el bootstrap universal (que corre en cada mensaje inicial de cualquier conversación del proyecto) se autodeclarara "sesión sincronizada" sin que el operador ni el modelo distinguieran ese cierre de la apertura formal del skill, que es la única que escribe al Ledger.
Cambios:
- KERNEL:ARCHITECTURE-L0-BOOTSTRAP (§3): agregada convención de estado X-ING → X-ED — el Bootstrap declara BOOTLOADING... al inicio y BOOTLOADED: DOCUMENTOS CARGADOS al cierre, nunca lenguaje de cierre de sesión formal. Agregado párrafo explícito de distinción de alcance: el Bootstrap es carga de contexto universal (cada mensaje inicial), el Session Ledger (KERNEL:SESSION-LEDGER, §21) es opt-in exclusivo del skill vantage-session-open. Diagrama de flujo actualizado con ambos estados y nota de Ledger condicional.
- SP:BOOTSTRAP-001 (System Prompt): copy operativo real corregido por el operador directamente en Project Instructions (fuera del alcance de escritura de este componente) — mismo cambio de convención de estado, mas la línea explícita de que el Bootstrap no escribe en Session Ledger.
Write-Back Verification: re-fetch de Kernel tras la escritura — sin mismatch.
IDs afectados: ninguno — ambos patches documentan contenido bajo IDs ya existentes (KERNEL:ARCHITECTURE-L0-BOOTSTRAP, SP:BOOTSTRAP-001). Census no requiere regeneración.
Pendiente (fuera de esta entrada): Task Tracker — "Revisar skill vantage-session-open — no ha abierto fila en Session Ledger en 5 sesiones continuas" permanece abierto hasta que el operador confirme, en una sesión real con el nuevo copy activo, que la distinción BOOTLOADED vs SESSION-OPENED resuelve el patrón de confusión. No cerrar el ticket solo con este Changelog.
Versión actualizada: 9.5.0 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en su versión previa hasta que el operador corra verify_versions.py --sync.
---
### v9.4.9 — 2026-07-17
Alcance: Esquema base de Bug/Tasks Tracker en SP (SP:SCHEMA) + regla de no-inferencia sobre mecanismos del sistema (SP:CONSISTENCY) + narrativa L0 ampliada en Kernel (KERNEL:ARCHITECTURE-L0) y Manual (§9.1, MANUAL:VANTAGE-RUNTIME-001) para incluir Version Check Tool/Census como parte de la capa L0.
Cambios:
- SP:SCHEMA (§7): agregado bloque "Esquema base" para Bug Tracker y Tasks Tracker (campos, tipos, opciones de select) como referencia estática para creación directa de páginas vía notion-create-pages sin fetch previo del data source. Nota explícita: Notion es la fuente de verdad, este bloque es caché de lectura que debe actualizarse en la misma sesión si el schema real cambia.
- SP:CONSISTENCY (§10): nuevo punto 5 — antes de escribir en un documento fundacional una afirmación sobre CÓMO funciona un mecanismo del sistema (skill, script, proceso), confirmar con el operador o la fuente real, nunca inferir por nombre o intención aparente. Originado por una corrección del operador en esta misma sesión: una primera redacción de SP:SCHEMA atribuyó erróneamente a vantage-documentacion-transversal un rol de monitoreo activo que el skill no tiene (es un skill de creación de contenido bajo demanda, no un proceso de vigilancia). Corregido en la misma sesión antes de este Changelog — no se registró como bug porque se resolvió de inmediato.
- KERNEL:ARCHITECTURE-L0: agregado párrafo + línea de diagrama declarando que Version Check Tool (vversions) y Census (vcensus) pertenecen a L0 (observabilidad ReadOnly), ya confirmado por el operador en sesión previa pero nunca escrito en el Kernel.
- MANUAL §9.1 (MANUAL:VANTAGE-RUNTIME-001): extendida la definición de Runtime con la misma pertenencia de vversions/vcensus a L0, sin duplicar el detalle operativo ya documentado en §9.2 y §6.
- V | ALIASES: reescritura completa a las 8 familias (Session Cycle → L0 Runtime → L1/L2 → Pipeline → L3 → L4 → Dashboard → CV → Dedup), aprobada en sesión previa (chat 71ea0fc5) pero nunca escrita — confirmado por fetch al inicio de esta sesión que el documento seguía en su estructura anterior de 9 secciones. Ejecutada ahora junto con alta de alias nuevo vsource (source ~/.zshrc, familia L0 Runtime) solicitado por el operador.
Write-Back Verification: re-fetch de SP y Kernel tras cada escritura — sin mismatch. Manual no re-verificado por fetch en esta entrada (patch aplicado vía update_content sin error reportado). ALIASES re-fetcheado post-escritura — 8 familias confirmadas, sin mismatch.
IDs afectados: ninguno — los cuatro patches documentan contenido bajo IDs ya existentes (SP:SCHEMA, SP:CONSISTENCY, KERNEL:ARCHITECTURE-L0, MANUAL:VANTAGE-RUNTIME-001). Census no requiere regeneración.
Pendiente (fuera de esta entrada): ninguno identificado — handoff de sesión anterior (chat 71ea0fc5) cerrado con esta entrada.
Versión actualizada: 9.4.9 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en su versión previa hasta que el operador corra verify_versions.py --sync.
---
### v9.4.8 — 2026-07-17
Alcance: Convención de nombres de alias de Terminal (Kernel §23, Manual §9.2, Aliases). Corrige drift entre alias reales en .zshrc (vversion, vcensus) y el contrato ya documentado en Kernel/Manual, y cierra el hueco de gramática que mezclaba subcomando posicional (vl1 tracker) con flags de guión (vversions --sync) sin regla explícita.
Cambios:
- Diagnosticado en Terminal (log del operador): vversion/vcensus existían como alias en .zshrc pero con comillas dobladas mal formadas (=''...'' en vez de '...'), causando ejecución silenciosa sin error ni output. Causa raíz identificada, fix entregado al operador para aplicar localmente (no fundacional — vive en .zshrc, fuera de Notion).
- KERNEL §23 (KERNEL:VERSION-CHECK-TOOL): agregado párrafo "Alias de invocación" declarando vversions (plural) como nombre corto canónico de verify_versions.py, con los tres flags sin modo default. Agregada subsección "Convención de nombres de alias (Terminal)" al cierre de la sección: v<dominio>[ <subcomando>] — subcomando posicional para modos mutuamente excluyentes, flags con guión para variaciones sobre un mismo motor; un alias nunca coexiste con un nombre casi-idéntico de un script renombrado.
- MANUAL §9.2 (MANUAL:VANTAGE-RUNTIME-001): catalogadas vversions y vcensus junto a los vl1 * ya documentados, con referencia cruzada a §6 (Ciclo de Sesión) y §11 (V-ID-Census) para no duplicar su contrato operativo completo.
- ALIASES (V | ALIASES, sesión previa a este Changelog): agregadas filas vversions y vcensus a la tabla Session Lifecycle (antes ausentes pese a que verify_versions.py --bootstrap/--check/--sync ya estaba documentado ahí sin alias corto asociado); nota de convención de nombres al pie de la sección.
Write-Back Verification: re-fetch de Kernel y Manual tras cada escritura — sin mismatch en ninguno de los dos.
IDs afectados: ninguno — los tres patches documentan un alias y una convención de nombres ya vigentes en el contrato, no dan de alta, retiran ni cambian de estado ningún ID canónico. Census no requiere regeneración (KERNEL:CENSUS-SYNC Regla 1 no se dispara).
Pendiente (fuera de esta entrada): aplicar el fix de comillas en .zshrc (local, operador) y retirar los alias huérfanos vpipeline/vpipeline-status propuestos en sesión previa y descartados por ser redundantes con vl1.
Versión actualizada: 9.4.8 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en su versión previa hasta que el operador corra verify_versions.py --sync.
---
### v9.4.7 — 2026-07-16
Alcance: Corrección de bugs en tooling local (generate_census.py, normalize_heading_ids.py — ambos en Layer_1/scripts/, no fundacionales) + cierre del pendiente de deeplink dejado abierto por v9.4.6.
Cambios:
- generate_census.py: corregido is_definition_block() — la condición de heading solo reconocía la nomenclatura "ID puro" (### PREFIX:KEY), no la nomenclatura real usada en TODOS los headings de sección top-level del Kernel (§N — PREFIX:KEY). Esto hacía que ninguna sección nueva pudiera detectarse como huérfana, sin importar cuántas veces se regenerara el Census. Agregado reconocimiento de ambas nomenclaturas vía regex §[\w.]+\s*[—-]\s*.
- Re-run de generate_census.py en Terminal: 117/117 IDs resueltos, 0 huérfanos, 0 sin link — confirma que KERNEL:DOCUMENTATION-TRANSVERSAL-001 (alta documentada en v9.4.6) ya se detecta correctamente, con deeplink de bloque real, reemplazando el placeholder de página usado como honesto en la entrada anterior.
- Census (394938be) regenerado y subido manualmente a Notion por el operador con el output fresco.
- Ambos scripts: corregida ruta de resolución de layer_1.env tras el traslado de ambos archivos de Layer_1/ a Layer_1/scripts/. La fórmula inicial (script_dir.parent.parent) sobre-corrigió, apuntando a VANTAGE/config/ en vez de Layer_1/config/ (ubicación real, confirmada vía find). Corregida a script_dir.parent.
- normalize_heading_ids.py (script nuevo, complemento de auditoría de generate_census.py): la primera versión usaba una heurística de clasificación de headings distinta e inconsistente con is_definition_block(), generando falsos positivos masivos (47 hallazgos, la mayoría patrones "ID: PREFIX:KEY" ya válidos y reconocidos por el Census). Corregido para usar exactamente la misma lógica de reconocimiento. Excluido explícitamente Change Log del barrido — sus headings narran historia y mencionan IDs de pasada, nunca los definen; normalizarlos arriesgaba corromper texto histórico (confirmado con un caso real de sugerencia de fix que mutilaba una entrada de v9.4.0).
- normalize_heading_ids.py: agregado retry con backoff (5 intentos, 2–10s) y timeout ampliado (30s → 60s) en fetch_blocks_recursive() — la primera corrida contra el Kernel completo (documento más grande) truncaba con ReadTimeoutError sin reintentar.
- Re-run de normalize_heading_ids.py (modo dry-run, sin escritura): 8 hallazgos reales, todos en Career Canon — mismo patrón en los 8 ("TÍTULO PREFIX:KEY", ID pegado al final sin separador): CANON:PROFILE-001, CANON:SKILLS-001, CANON:EXPERIENCE-001, CANON:ACHIEVEMENTS-001, CANON:KPIS-001, CANON:FACTS-001, CANON:POSITIONING-001, CANON:OUTPUT-CONTRACT-001. No aplicados aún.
Pendiente (no ejecutado en esta sesión):
- Aplicar (o corregir a mano) los 8 headings mal formados de Career Canon detectados por normalize_heading_ids.py. Impacto es cosmético/consistencia — estos 8 IDs ya resuelven bien vía fallback en el Census; además --apply reescribe rich_text plano y perdería cualquier anotación de estilo del heading original.
- Cerrar el ticket de Tasks Tracker sobre el timeout de normalize_heading_ids.py (ya resuelto por esta entrada) — pendiente de marcarlo Hecho.
IDs afectados: ninguno nuevo — KERNEL:DOCUMENTATION-TRANSVERSAL-001 ya fue dado de alta en v9.4.6; esta entrada resuelve su deeplink pendiente, no crea ni retira IDs.
Versión actualizada: 9.4.7 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en su versión previa hasta que el operador corra verify_versions.py --sync.
---
### v9.4.6 — 2026-07-16
Alcance: Alta de KERNEL:DOCUMENTATION-TRANSVERSAL-001 (Kernel §22) + cross-referencia en Manual §6 + fila nueva en Census. Cierra el pendiente dejado abierto por v9.4.5.
Cambios:
- KERNEL: nueva sección §22 — KERNEL:DOCUMENTATION-TRANSVERSAL-001, insertada entre KERNEL:SESSION-LEDGER (§21) y KERNEL:VERSION-CHECK-TOOL (renumerado de §22 a §23). Contrato de seis fases (Mapeo → DRY RUN → Inyección → Write-Back → Changelog/versión → Binary Gate), hereda los 5 filtros de MANUAL:PATCH-QUALITY-001 sin redefinirlos.
- MANUAL §6 ("Qué hacer si algo no cuadra"): nuevo bullet cruzando al ID nuevo, distinguiendo el caso "cambio sin reflejo documental" del drift de versión ya cubierto en esa misma lista.
- CENSUS: fila nueva bajo KERNEL para KERNEL:DOCUMENTATION-TRANSVERSAL-001 (§22); renumerada la fila de KERNEL:VERSION-CHECK-TOOL de "(anexo, post-§21)" a §23 para reflejar la inserción. Deeplink de bloque del ID nuevo queda pendiente de resolución exacta vía generate_census.py (Regla 2) — se registró con link a nivel de página como placeholder honesto, no aproximado como si fuera el anchor exacto.
Write-Back Verification: re-fetch de Kernel, Manual y Census tras cada escritura — sin mismatch en ninguno de los tres.
Disparo KERNEL:CENSUS-SYNC Regla 1: aplicado — alta de ID nuevo reflejada en Census en la misma sesión, antes de este Changelog.
Pendiente (no ejecutado en esta sesión):
- Re-run de generate_census.py en Terminal para resolver el deeplink de bloque exacto del ID nuevo (placeholder de página en uso mientras tanto).
- Instalación del SKILL.md corregido en la ruta local real (pendiente heredado de v9.4.5).
- Verificación de discrepancia entre esta sesión y el último Session Ledger cerrado (pendiente heredado de v9.4.5).
IDs afectados: alta de KERNEL:DOCUMENTATION-TRANSVERSAL-001.
### v9.4.5 — 2026-07-16
Alcance: Revisión y refinamiento del skill vantage-documentacion-transversal (trabajo local, sin escritura a Notion en esta sesión).
Cambios:
- Corrección de cita KERNEL:PATCH-QUALITY-001 → MANUAL:PATCH-QUALITY-001 en el skill.
- Reescritura del protocolo del skill: principio "nodo natural, no adendum"; gate de dos etapas (propuesta de nodo/IDs → autorización → DRY RUN de parches → APROBAR_WRITE → inyección → Write-Back → Changelog/versión → Binary Gate).
- Evaluación y descarte de propuesta externa de "sistema dual de IDs" (no existe en SP:ID-CONNECTORS-001; confundía UUID de Census con el de Changelog).
- Adopción parcial de checklist de validación pre-cierre y de gestión de parches pendientes vía Tasks Tracker (d2a65ca1-6a35-465d-bcff-b0d82dddd549).
- Agregado ejemplo práctico único (auto-referencial): la propia creación de este skill como caso guía.
Pendiente (no ejecutado en esta sesión):
- Alta de KERNEL:DOCUMENTATION-TRANSVERSAL-001 en el Technical Kernel real (nodo junto a KERNEL:CENSUS-SYNC/KERNEL:SESSION-LEDGER).
- Instalación del SKILL.md corregido en la ruta local real (/mnt/skills/user/).
- Verificación de discrepancia entre esta sesión y el último Session Ledger cerrado.
IDs afectados: ninguno en Notion todavía (pendiente KERNEL:DOCUMENTATION-TRANSVERSAL-001).
---
> El histórico completo del CHANGELOG lo podrás encontrar en ARCHIVO CHANGELOG, en esta pagina de consulta continua solo encontrarás las últimas diez entradas para garantizar la operación y referencia del sistema.

