# V | CHANGELOG

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
[v9.4.4] — 2026-07-16
Auditoría cruzada Bug Tracker / Tasks Tracker vs sus archivos.
Confirmados y archivados: 3 bugs (verify_, vantage-session-close.md,
Fuente/Fetch/VM_Scope) + 3 tasks (generate_ export, KERNEL:BOOTSTRAP-001,
dup §16/§17 Manual). Detectado ID incorrecto en SP:CEDULA-DIGITAL para
ARCHIVO BUG TRACKER (674696fd... apuntaba a ARCHIVO TRACKER/vacantes;
ID correcto: 9ef938be-fc42-831b-a2d6-874bd22b7990). Pendiente:
archivar (soft-delete) las 6 filas originales en trackers activos;
corregir ID en SP:CEDULA-DIGITAL.
### v9.4.3 — 2026-07-16
Bug Fix #19 (Dedup) + Housekeeping Layer_2 + Tickets Infraestructura Git
Dedup Strategy — Bug #19 (CRÍTICO)
- Archivo: Layer_1/scripts/feed_processor.py
- Línea: 232
- Cambio: Agregado "jk" a tracking_prefixes en función normalize_url()
- Justificación: URLs de Indeed rotan el parámetro jk en cada repost, generando hashes distintos para el mismo job
- Impacto: Now filters volatile Indeed tracking parameters alongside standard tracking params (utm_, gclid, etc.)
- Evidencia: Caso GILSA documentado en Notion (6 páginas para el mismo puesto con 3 jk distintos)
- Testing: py_compile exitoso
- Backward compatibility: No afecta URLs sin parámetro jk (filtro es inclusivo, no exclusivo)
Architecture Documentation — Layer_2 Cleanup
- Archivo: Layer_1/VANTAGE_ARCHITECTURE.md
- Cambios:
- Eliminada referencia a layer_2_mail.py del inventario de scripts
- Actualizada tabla "Envelope Types por Layer" (solo L1 y L3)
- Actualizado campo layer en Class A Schema (solo L1/L3)
- Justificación: Layer_2 fue eliminado en v9.3.9 según Changelog
- Impacto: Documentación ahora alineada con arquitectura actual
- Cross-reference: Changelog v9.3.9 — "Layer_2 ha sido eliminado"
Ticket #9 — Manual §16/§17 (Fantasma)
- ID Ticket: 39e938befc42817dab02f90716f3548b
- Estado: Cerrado como "Completado" con nota de obsolescencia
- Diagnóstico: Problema resuelto en v9.4.1 (reestructuración de índices §16-§19→§18-§21)
- Acción: Actualizado campo "Notas" con evidencia del Changelog
- Cross-reference: Changelog v9.4.1 — "Reestructuración de índices en documentos fundacionales"
Bug #43 — Rich-text Truncamiento (Verificado)
- Archivo: Layer_1/scripts/verify_versions.py
- Línea: 306
- Estado: Verificado como resuelto en v9.3.7
- Pattern: name = "".join(t.get("plain_text", "") for t in texts) if texts else None
- Justificación: Concatena todos los rich-text runs para evitar truncamiento cuando Notion detecta links en títulos
Bug #44 — Manifest Handling (Verificado)
- Archivo: Layer_4/scripts/vsync_doc.py
- Líneas: 62-68
- Estado: Verificado como resuelto
- Pattern: _load_manifest() retorna {} si archivo no existe (no lanza error)
- Justificación: Evita falso CONFLICT cuando .vsync_manifest.json está ausente
Bucket Plan Update
- ID: 39f938befc4280e6a505f432b95755eb
- Campo: "Notas"
- Contenido: Resumen de sesión con items resueltos
- Estado: Actualizado y verificado por re-fetch
Git Infrastructure Tickets Created
- Tickets #46-A y #46-B creados en Tasks Tracker (aaaaef55-a1ce-45f7-9c8b-1c1def2c18e8)
- #46-A: Git Infrastructure — Branch Protection, Feature Branches, PR Workflow (ALTO)
- #46-B: Git Commit Quality — Commits Grandes, Mensajes Genéricos, Tags/Versionado (MEDIO)
- Origen: Split híbrido del hallazgo #46 de auditoría Devin 2026-07-16
- Estado: Creados y verificados por re-fetch tras incidente MCP
Version Verification
- Comando: python3 scripts/verify_versions.py --check
- Resultado: Todos los documentos fundacionales en v9.4.2 ✓
- Estado: Sistema sincronizado
1. Layer_2 References — Eliminadas referencias obsoletas en documentación de arquitectura
1. Ticket Fantasma — Eliminado ticket CRÍTICO que consumía atención innecesaria
1. Dedup GILSA Case — Resuelto caso documentado de 6 páginas duplicadas para mismo puesto
| Métrica | Valor |
| --- | --- |
| Líneas de código modificadas | 1 |
| Documentos actualizados | 1 |
| Tickets cerrados | 1 fantasma |
| Tickets creados | 2 (infraestructura git) |
| Bugs resueltos | 1 crítico |
| Deuda técnica eliminada | 2 items |
### v9.4.2 — 2026-07-16
Manual — Nuevos IDs de sección (§18–§21)
- Alta de 4 IDs faltantes en MANUAL, detectados como huérfanos por generate_census.py tras la renumeración de secciones (§16→§18, §17→§19, §18→§20, §19→§21):
- MANUAL:CV-GOLDEN-RULES-INDEX (§18)
- MANUAL:POSITIONING-CRITERIA (§19)
- MANUAL:GOLDEN-SKELETON-REF (§20)
- MANUAL:SCHEMA-FIELD-REF (§21)
- CENSUS_SPEC actualizado en generate_census.py (Layer_1/scripts/) — 116 IDs en spec, 0 huérfanos.
- ID CENSUS regenerado y cargado manualmente a Notion.
## v9.4.1 - 2026-07-16
### Changed
- Reestructuración de índices en documentos fundacionales (§16-§19 desplazados a §18-§21).
- Normalización del mensaje de éxito en §4 Paso 3 (eliminación de hardcodeo de versión).
- Corrección de referencias cruzadas en módulo de Troubleshooting (apuntando a §18).
### Fixed
- Eliminación de ambigüedad en mapeo de nodos tras migración de secciones.
### v9.4.0 Batch Quick Wins — GROQ key purgada del historial de git, schema Fuente/Fetch/VM_Scope a select, KERNEL:BOOTSTRAP-001 corregido, VERSION_EXEMPT cerrado como obsoleto
- Fecha: 2026-07-16
- Alcance: repositorio git (github.com/mauriciomeyran/VANTAGE), VANTAGE TRACKER (schema), KERNEL (KERNEL:ARCHITECTURE-L0-BOOTSTRAP), Bug Tracker (2 tickets), Tasks Tracker (2 tickets).
- Contexto: auditoría cruzada de 8 pendientes clasificados como Quick Wins (<5 iteraciones) contra el código real (verify_versions.py, generate_census.py, subidos por el operador) y el historial de git (clonado y verificado independientemente), en vez de asumir el contenido de los tickets al pie de la letra.
- Cambio 1 — Seguridad (CRÍTICO, hallazgo original de auditoría Devin 2026-07-06): la GROQ API key (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) seguía expuesta en el historial de git dentro de layer_1_blueprint.json, pese a haber sido borrada del working tree. Ejecutado git filter-repo --replace-text sobre el historial completo (130 commits reescritos) + force-push a origin/main y al tag v2.4.0. Verificado en dos rondas independientes (grep del operador + re-clon limpio desde el remoto reescrito por el AI Component): 0 coincidencias del string en todo el historial. La key ya había sido rotada en Groq el mismo día de la auditoría original — el riesgo real era de higiene, no de credencial activa expuesta.
- Cambio 2 — VANTAGE TRACKER (schema): Fuente, Fetch y VM_Scope convertidos de text a select vía notion-update-data-source (ALTER COLUMN SET SELECT), con las opciones reales detectadas en producción (Fuente: Agregador/Career Page Oficial/Indeed/Other/Computrabajo/LinkedIn · Fetch: Accesible/Bloqueado · VM_Scope: Alto/Bajo). Corrige además una premisa incorrecta del bug original ("VM_Scope siempre Alto" — falso, había registros en ambos valores; no era un bug de escritura).
- Cambio 3 — KERNEL:ARCHITECTURE-L0-BOOTSTRAP: referencia rota KERNEL:BOOTSTRAP-001 (citada como ID a fetchear en el Bootstrap Protocol, pero nunca definida en ningún documento) corregida a SP:BOOTSTRAP-001 (System Prompt), que sí cumple esa función. Nota editorial de "hueco detectado" removida — el hueco era una referencia mal apuntada heredada de la reestructuración v9.3.0, no una definición faltante que requiriera alta de ID nuevo.
- Cambio 4 — generate_census.py (local, no fundacional): confirmado por el operador el fix de la línea 512 — output = Path(__file__).resolve().parent / "V_ID_CENSUS_PRODUCTION.md", reemplazando un path relativo puro que resolvía contra el cwd de invocación en vez de la ubicación del script.
- Cambio 5 — Bug Tracker: ticket "verify_versions.py — VERSION_EXEMPT no hace match con nombre real de fila Ledger" cerrado como obsoleto. Verificado contra el historial completo de git: VERSION_EXEMPT = {"LEDGER"} pertenecía a una arquitectura anterior del script (lectura desde una VERSION MANIFEST DB en Notion), purgada en la sesión 2026-07-15. El script v3.0 actual no tiene ese mecanismo — no requería desarrollo, era un ticket fantasma de una arquitectura ya reemplazada.
- Cambio 6 — pendiente descartado: "commitear notion_backup.py" no correspondía a ningún archivo existente en el repo ni referenciado en ningún script — se determinó que era el mismo ítem ya trackeado como #10 ("backup Notion") del Plan de trabajo post-auditoría V2 (Devin), sin script propio todavía escrito. Fusionado ahí, sin acción propia.
- Ningún ID canónico (KERNEL:*, MANUAL:*, SP:*, CANON:*) fue creado ni retirado — Cambio 3 es corrección de una referencia existente, no alta de ID nuevo. Census no requiere regeneración (KERNEL:CENSUS-SYNC Regla 1 no se dispara).
- Pendiente identificado: Task "Restaurar color de anotación en IDs y referencias intradocumentales de Kernel y Manual" reclasificada de Quick Win a bucket 6-10 iteraciones tras confirmar el scope real (~37 headers entre ambos documentos, requiere fetch a nivel de bloque previo). .vsync_manifest.json (Layer_4) pendiente de decisión operador: gitignore explícito vs. versionado — recomendación dada, no ejecutada aún.
- Versión actualizada: 9.4.0 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en su versión previa hasta que el operador corra verify_versions.py --sync.
### v9.3.9 — 2026-07-08 (Fecha en la que se escribió esta entrada pero no se había publicado hasta hoy en changelog) A continuación el avance del plan de trabajo tras la auditoría V2 (Devin). Cambio mayor dado el alcance (83% del plan de trabajo implementado)
Contenido: Resumen estructurado por bloques (1-5) con los cambios principales
Puntos clave incluidos:
- Bloque 1: GROQ key, data_source_id, Source_Type, feedback loop
- Bloque 2: .gitignore, scripts deprecados, Layer 2 eliminado
- Bloque 3: backup, sync, heartbeat, logging, idempotencia
- Bloque 4: tests (42/42), rate limits, GROQ tier gratuito
- Bloque 5: outcomes, Dashboard UX rediseñado
- Pendientes: tasks #16, #17 y items en espera de datos
- Commit reference: 5cec93a
### v9.3.8 SP:CEDULA-DIGITAL — alta de ARCHIVO SCRIPT LIBRARY
- Fecha: 2026-07-16
- Alcance: SYSTEM PROMPT (SP:CEDULA-DIGITAL).
- Cambio: agregado ID de ARCHIVO SCRIPT LIBRARY (data_source 39f938be-fc42-80ec-8f2e-000b16d736e2) al listado de rutas/UUIDs de la Cédula Digital — pendiente identificado en v9.3.7, ahora cerrado.
- Ningún ID canónico (KERNEL:, MANUAL:, CANON:*) fue creado, retirado ni cambió de estado. Census no requiere regeneración.
- Versión actualizada: 9.3.8 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en su versión previa hasta que el operador corra verify_versions.py --sync.
### v9.3.7 SCRIPT LIBRARY — fix bug de truncamiento de título, gap report auditado (18 altas + 1 corrección + 17 migradas a ARCHIVO SCRIPT LIBRARY)
- Fecha: 2026-07-16
- Alcance: Layer_1/scripts/verify_versions.py (local, no fundacional), SCRIPT LIBRARY (data_source ea914544-338f-485e-ac1b-7f137a5c9cee), ARCHIVO SCRIPT LIBRARY (database nueva, creada por el operador en esta sesión, data_source 39f938be-fc42-80ec-8f2e-000b16d736e2).
- Contexto: handoff de sesión anterior dejó 17 gaps confirmados manualmente entre disco y SCRIPT LIBRARY, pendientes de alta vía DRY RUN, con una segunda verificación cruzada requerida contra el output de verify_versions.py --scripts antes de confiar en él. El primer output real (--scripts) no coincidió con el handoff: reportó 58 gaps y 43 filas huérfanas con nombres truncados en _ (ej. agent_, dashboard_, git_sync_).
- Bug encontrado — get_script_library_titles(): Notion parte el título de una fila en múltiples rich-text runs cuando autodetecta un link dentro del nombre (ej. "patch_cheat_sheet.py" → runs ["patch_cheat_", "sheet.py"]). El código leía solo texts[0], truncando el nombre en el primer run.
- Fix aplicado: name = "".join(t.get("plain_text","") for t in texts) — concatena todos los runs. Verificado con py_compile y con una query real a la API confirmando el shape multi-run. Re-run post-fix coincidió exactamente con el handoff: 18 gaps (17 + el propio verify_versions.py), 42 registrados y vigentes, 17 filas 'Activo' huérfanas con nombres completos.
- Hallazgo colateral resuelto: las 17 filas huérfanas no eran mismatch de nombre — los 17 scripts existen físicamente en Archive/Legacy_Scripts/ (confirmado por ls del operador), fuera del árbol activo por diseño, pero con Estado desactualizado en Notion (seguían marcadas Activo).
- Cambio 1 — SCRIPT LIBRARY: 18 altas nuevas (8 scripts sueltos: feedback_loop.py, generate_census.py, health_check.py, health_check_patch.py, notion_backup.py, patch_vsync_doc.py, runtime_identity.py, verify_versions.py — Estado Activo; 10 wrappers Raycast vantage-*.sh — Estado En desarrollo, sin validar aún por el operador, Capa heredada del script que invocan). Corrección de título: layer_1_run.py (Dashboard) → layer_1_run_dash.py (mismatch entre título Notion y filename real en disco).
- Cambio 2 — ARCHIVO SCRIPT LIBRARY: database creada por el operador con solo la propiedad Nombre. Schema replicado vía ADD COLUMN (Ruta, Capa, Estado, Acción, Dependencias, Descripción, mismas opciones de select que SCRIPT LIBRARY) con aprobación explícita del operador antes del DDL. 17 páginas creadas con Estado=Deprecado / Acción=Archivar, copiando Ruta/Capa/Dependencias/Descripción de las filas originales. Las 17 filas originales en SCRIPT LIBRARY fueron archivadas (soft-delete vía API nativa PATCH /pages/{id} con archived:true — no expuesto por el MCP de Notion, ejecutado vía Terminal/httpx directo).
- Pendiente identificado: agregar el ID de ARCHIVO SCRIPT LIBRARY a SP:CEDULA-DIGITAL (no ejecutado en esta entrada por priorización de tokens). notion_backup.py sigue sin resolver si debe commitearse a git (confirmado: .gitignore de VANTAGE root, Layer_1 y Layer_3 están vacíos, por lo que su ausencia del repo es omisión, no exclusión deliberada).
- Ningún ID canónico (KERNEL:, MANUAL:, SP:, CANON:) fue creado, retirado ni cambió de estado — SCRIPT LIBRARY no es documento fundacional, no dispara KERNEL:CENSUS-SYNC ni SP:SYNC-RULE.
- Versión actualizada: 9.3.7 (solo esta página — CHANGELOG). El resto de los fundacionales permanece en su versión previa hasta que el operador corra verify_versions.py --sync.
### v9.3.6 SYSTEM PROMPT — SP:BOOTSTRAP-001, blindaje contra notion-search en sincronización de bootstrap
- Fecha: 2026-07-16
- Alcance: SYSTEM PROMPT (SP:BOOTSTRAP-001). Solo este documento recibe el bump en esta entrada — el operador hará el sync manual de versión hacia el resto de los fundacionales.
- Contexto: el operador reportó confusión recurrente entre sesiones — el agente mencionaba intentar "Google Drive" al recuperar SYSTEM PROMPT/ID CENSUS pese a que el contrato de sesión siempre especificó Notion MCP. Auditoría de la herramienta notion-search confirmó la causa técnica: su descripción indexa, además del workspace de Notion, otras fuentes conectadas (Google Drive, Slack, GitHub, Jira, Teams, SharePoint, OneDrive, Linear) y puede devolver resultados híbridos no correspondientes a los documentos fundacionales reales.
- Cambio — SP:BOOTSTRAP-001: nueva subsección "Conector único autorizado". Establece que toda recuperación de documentos fundacionales debe hacerse exclusivamente vía notion-fetch por Page ID/URL directo. Prohíbe explícitamente notion-search como ruta de sincronización de bootstrap (solo permitido si el operador lo pide para exploración puntual). Prohíbe explícitamente Google Drive u otro conector como fuente de documentos fundacionales.
- Ningún ID canónico (KERNEL:, MANUAL:, CANON:*) fue creado ni retirado. Census no requiere regeneración (KERNEL:CENSUS-SYNC Regla 1 no se dispara — cambio de contenido bajo SP:BOOTSTRAP-001, ID ya existente).
- Pendiente identificado: sync manual pendiente por el operador — SYSTEM PROMPT queda en v9.3.6 mientras el resto de los fundacionales (Kernel, Manual, Career Canon, Aliases, Census) permanecen en v9.3.5 hasta que el operador corra la normalización (verify_versions.py --sync o equivalente manual). Discrepancia esperada y temporal, no reportar como error en la próxima sesión hasta confirmar que el sync se completó.
- Versión actualizada: 9.3.6 (solo SYSTEM PROMPT).
### v9.3.5 Corrección de SKILL.md open/close — alineación con verify_versions.py real (--bootstrap/--check/--sync)
- Fecha: 2026-07-16
- Alcance: vantage-session-open/SKILL.md, vantage-session-close/SKILL.md (locales, no fundacionales — no disparan KERNEL:CENSUS-SYNC).
- Contexto: v9.3.2 ya había detectado y corregido el mismo tipo de drift en MANUAL:SESSION-CYCLE-001 y KERNEL:VERSION-CHECK-TOOL, dejando explícitamente pendiente (nota al cierre de esa entrada) que los SKILL.md instalados aún no reflejaban el contrato nuevo. Esta sesión cierra ese pendiente.
- Cambio 1 — vantage-session-open/SKILL.md: reescritura completa del cuerpo. Eliminados los pasos que hacían query MCP directo a Session Ledger (collection://8d736032...) y fetch MCP de System Prompt + ID Census — ambos prohibidos desde v9.3.2 (Terminal es requisito obligatorio, sin fallback). Reemplazado por protocolo de 6 pasos basado exclusivamente en los outputs de --bootstrap y --check pegados por el operador. Descripción del frontmatter también optimizada con disparadores léxicos explícitos ("abrir sesión", "VANTAGE OPEN", etc.), siguiendo criterio de skill-creator.
- Cambio 2 — vantage-session-close/SKILL.md: correcciones puntuales (ya estaba mayormente alineado). Conteo de documentos corregido de 6 a 7 (incluye Census) en el paso VERIFY. Aclarado explícitamente que las escrituras de SYNC MANIFEST y LEDGER son housekeeping exento de APROBAR_WRITE, consistente con KERNEL:VERSION-CHECK-TOOL. Descripción del frontmatter optimizada con disparadores léxicos ("cerrar sesión", "VANTAGE CLOSE", etc.).
- Verificación: lectura del código real de verify_versions.py (provisto por el operador) contra el texto de ambos SKILL.md — confirmado que el Manual (v9.3.4) ya era la fuente correcta; los SKILL.md eran los desactualizados. Cambios no verificados aún por re-fetch en disco — los archivos corregidos se generaron en sandbox y quedan pendientes de reemplazo manual por el operador en /mnt/skills/user/.
- Ningún ID canónico (MANUAL:, KERNEL:, SP:*) fue creado, retirado ni cambió de estado. Census no requiere regeneración (KERNEL:CENSUS-SYNC Regla 1 no se dispara — cambio es de contenido de skill local, no de canon).
- Pendiente identificado: confirmar que el operador reemplazó físicamente ambos archivos en disco antes de cerrar esta sesión — de lo contrario el drift persiste en producción aunque el Changelog lo documente como resuelto (mismo patrón de riesgo que v9.1.1/v9.2.6, ya señalado en entradas anteriores).
- Versión actualizada: 9.3.5.
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

