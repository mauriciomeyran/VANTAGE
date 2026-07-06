# V | CHANGELOG

---
### v8.9.7 — 2026-07-05
[ARCH] Bootstrap Layer — VANTAGE Bootloader v1.0 desplegado en UI de Claude — Estrategia de deploy del System Prompt migrada de copy-paste manual a bootstrap dinámico de una sola vez. STATIC BOOTLOADER v1.0 instalado en Settings → Project Instructions de Claude. Ante el primer mensaje de cada sesión, el agente hace fetch automático de SYSTEM PROMPT (37b938be) e ID CENSUS (394938be) antes de procesar cualquier petición del operador. El contenido de Notion sobreescribe cualquier instrucción estática previa (anti-drift de versiones). Confirmación de sincronización: "VANTAGE v[X]: SISTEMA SINCRONIZADO". Si el bootstrap falla: MODO DEGRADADO — no se procesan triggers operativos. Documentado en: KERNEL:ARCHITECTURE-L0-BOOTSTRAP (contrato técnico completo) · MANUAL §3 Paso 3 (instrucciones operativas para el operador) · System Prompt: KERNEL:BOOTSTRAP-001 referenciado en Cédula Digital.
---
### v8.9.6 — 2026-07-05
[FIX] SYSTEM PROMPT §5 — KERNEL:CV-GOLDEN-RULES DEF duplicada eliminada — Colisión real detectada via generate_census.py (DEF duplicada entre System Prompt y Kernel). Contenido de reglas retirado del SP; sección reducida a enrutador puro: → Ver KERNEL:CV-GOLDEN-RULES en Technical Kernel. Kernel permanece como única DEF autorizada. Colisiones reales del sistema: 71 (falsos positivos) → 1 (real) → 0.
---
### v8.9.5 — 2026-07-05
Enriquecimiento de V-ID-CENSUS
- Generado script Python generate_census_hyperlinks.py que produce tabla completa con IDs como hipervínculos directos a cada sección.
- Output: Markdown listo para pegar en Notion (IDs clicables + links directos).
- Actualizado V-ID-CENSUS con la tabla enriquecida.
- Integración ligera al Master Index.
Beneficio: Navegación directa desde el Census a cualquier sección de los documentos fundacionales.
### v8.9.4 — 2026-07-05
[DT-015] Normalización de IDs legacy a esquema [PREFIX]:[KEY] — CIERRE
- Fecha: 2026-07-05
- Alcance: MANUAL (BLOQUE 1), CAREER CANON (BLOQUE 2), KERNEL (BLOQUE 3).
- Resultados:
- BLOQUE 1 (MANUAL): Validación de coherencia con KERNEL:DOC-CONTRACT (PASS). Líneas sueltas (manual-healthcheck-001, manual-sla-001) y UUIDs legacy (390938be-fc42-81c1-9fc7-d0763295cd04) no localizados. Versión: 8.8.1.
- BLOQUE 2 (CAREER CANON): Migración de prefijos (CAREER_CANON:AUDIENCE-SCOPE → CANON:AUDIENCE-SCOPE, TRACKER:ARCHIVO_VANTAGE → CANON:ARCHIVO-VANTAGE). Anclaje de IDs huérfanos en §L (CANON:FIGMA-TAG-SCHEMA, CANON:POSITIONING-MODE, CANON:TAG-REGISTRY). Versión: 8.7.5.
- BLOQUE 3 (KERNEL): Reemplazo de stub KERNEL:NORM por sección operativa. Versión: 8.9.2.
- Notas:
- Todas las entradas individuales ya registradas en el Changelog.
- Versión final del sistema: v8.9.4.
### v8.9.3 — 2026-07-05
[DT-015] Normalización de IDs legacy a esquema [PREFIX]:[KEY]
- Fecha: 2026-07-05
- Alcance: KERNEL (BLOQUE 3).
- Cambios:
- Reemplazo de stub KERNEL:NORM por sección operativa real:
- Esquema: [PREFIX]:[KEY].
- Alcance: Todos los documentos fundacionales.
- Excepciones: UUIDs en metadatos/URLs.
- Gobernanza: APROBAR_WRITE + entrada en Changelog.
- Notas: 
- La sección ahora es ejecutable y alineada con KERNEL:DOC-CONTRACT.
- Versión actualizada: 8.9.2.
[DT-015] Normalización de IDs legacy a esquema [PREFIX]:[KEY]
- Fecha: 2026-07-05
- Alcance: MANUAL (BLOQUE 1).
- Acciones:
- Validación de coherencia con KERNEL:DOC-CONTRACT: PASS.
- Búsqueda de líneas sueltas (manual-healthcheck-001, manual-sla-001): No encontradas.
- Búsqueda de UUIDs legacy (390938be-fc42-81c1-9fc7-d0763295cd04): No localizados.
- Resultado: El MANUAL ya cumple con el esquema canónico. Sin cambios requeridos.
- Notas: 
- Los IDs 390938be-fc42-81c1-9fc7-d0763295cd04 podrían haber sido eliminados en versiones previas o nunca existieron en el documento.
[DT-015] Normalización de IDs legacy a esquema [PREFIX]:[KEY]
- Fecha: 2026-07-05
- Alcance: CAREER CANON (BLOQUE 2).
- Cambios:
- Migración de prefijos: CAREER_CANON:AUDIENCE-SCOPE → CANON:AUDIENCE-SCOPE, TRACKER:ARCHIVO_VANTAGE → CANON:ARCHIVO-VANTAGE.
- Anclaje de IDs huérfanos en §L:
- Figma Tag Schema → CANON:FIGMA-TAG-SCHEMA.
- Activación por Positioning Mode → CANON:POSITIONING-MODE.
- Tag Registry → CANON:TAG-REGISTRY (conversión a heading ##).
- Second pass: 26 ocurrencias revisadas (sin cambios adicionales requeridos).
- Notas: 
- Las referencias CF01–CF08, KPI01–KPI08, UF01–UF03 y N1–N4 ya cumplen con el esquema canónico.
- Versión actualizada: 8.7.5.
### v8.9.2 — VANTAGE · 2026-07-05
- [AUDIT] Graph Topology Audit — 3 documentos fundacionales auditados (KERNEL, SYSTEM PROMPT, MANUAL) — Auditoría topológica completa sobre el grafo de IDs de la suite documental. Producidos tres tiers de output: Master Index Dataset (inventario completo de IDs), Diagnóstico de Integridad (enlaces rotos, stubs válidos, redundancias) y Plan de Refactorización (bloqueantes priorizados). Hallazgos: 8 enlaces rotos, 6 IDs redundantes, 10 headings con UUID-prefijo violando DOC-CONTRACT, 2 referencias UUID raw en texto narrativo, 2 kebabs mal formados en Namespace A.
- [FIX] KERNEL — KERNEL:NORM stub creado — Sección KERNEL:NORM inexistente a pesar de estar listada en el TOC como §12. Creada con stub explícito y referencia a KERNEL:DOC-CONTRACT (DT-015). Enlace roto resuelto.
- [FIX] KERNEL §8 — KERNEL:PIPELINE → KERNEL:CV-PIPELINE — Typo en §Reglas operativas de CV-PIPELINE que producía referencia rota. Corregido a ID canónico.
- [FIX] KERNEL §8 — CAREER_CANON:OUTPUT-CONTRACT → CANON:OUTPUT-CONTRACT-001 — Prefijo no autorizado (CAREER_CANON) reemplazado por prefijo canónico (CANON) con ID completo. Alineado con KERNEL:DOC-CONTRACT.
- [ARCH] KERNEL — Secciones KERNEL:SCOPE, KERNEL:DATA-FLOW, KERNEL:ROUTING creadas — Las tres secciones existían únicamente en el System Prompt con prefijo KERNEL: pero sin contraparte real en el KERNEL. Migradas al KERNEL con contenido íntegro extraído del SP. SP actualizado a enrutador puro con referencias → Ver KERNEL:CLAVE. Decisión arquitectónica: Opción B (contenido vive en KERNEL, SP enruta).
- [FIX] MANUAL §5–§14 — Migración UUID-prefijo → MANUAL:CLAVE — 10 headings de secciones §5 a §14 usaban el UUID de la página como prefijo de ID (372938be-...:MANUAL-CLAVE), violando KERNEL:DOC-CONTRACT. Migrados al esquema canónico MANUAL:CLAVE. Contribuye al cierre de DT-015.
- [FIX] MANUAL §4 — Referencias UUID raw eliminadas (×2) — Dos referencias [ID: 377938be-fc42-8089-93f2-f52dbd2dec6c] en texto narrativo de CV-A y CV-B reemplazadas por CANON:EXPERIENCE-001 y CANON:OUTPUT-CONTRACT-001 respectivamente.
- [FIX] MANUAL §4 — Kebabs mal formados corregidos (×2) — canon-positioning-001 y canon-output-contract-001 (Namespace B en contexto de Namespace A) corregidos a CANON:POSITIONING-001 y CANON:OUTPUT-CONTRACT-001.
- [MAINT] MANUAL §8–§13 — IDs kebab redundantes eliminados (×6) — Líneas sueltas manual-prompts-wrappers-001, manual-cheatsheets-001, manual-healthcheck-001, manual-reglas-de-oro-001, manual-fallo-001, manual-sla-001 eliminadas. Duplicaban el ID ya presente en el heading de cada sección sin aportar navegación.
- Pendiente: DT-015 — 26 ocurrencias de IDs legacy restantes. Ejecutable vía trigger NORM [DOC:CLAVE] bajo autorización del operador.
### v8.9.1 — VANTAGE · 2026-07-05
- [REFACTOR] runtime_identity.py — Extract Runtime Identity Contract (DT-014 cerrado) — Módulo nuevo en Layer_1/scripts/. Encapsula el contrato de entity_prefix que vivía inline en generate_entity_index_v2.py. Exporta cuatro funciones con contrato explícito: load_prefix_map(registry_path) (carga mapa completo source_db → prefix desde resolver_registry_v2.json), get_entity_prefix(source_db, registry_path) (prefijo canónico; falla explícita si no está registrado — invariante v2.4.0/v8.8.0), get_authorized_prefixes(registry_path) (frozenset consumible por lazy_loader), generate_entity_id(entity_prefix, page_id, hash_value) (formato canónico PREFIX:H_xxx / PREFIX:U_xxx). SSOT: resolver_registry_v2.json — ningún componente hardcodea prefijos.
- [PATCH] generate_entity_index_v2.py — Consume runtime_identity — _load_entity_prefixes() y generate_entity_id() inline eliminadas. Reemplazadas por from runtime_identity import load_prefix_map, generate_entity_id. Cero cambios de comportamiento — únicamente eliminación de duplicación.
- [PATCH] lazy_loader.py v2 — AUTHORIZED_PREFIXES descentralizada — Constante hardcodeada eliminada. Reemplazada por _get_authorized_prefixes() que carga desde resolver_registry_v2.json vía runtime_identity.get_authorized_prefixes(). Fallback estático (frozenset({"KERNEL", "MANUAL", "CANON", "TRACKER"})) activo si el módulo no está disponible (compatibilidad en entornos sin Runtime Build completo).
### v8.9.0 — VANTAGE · 2026-07-04
Change_Log_v8.9.0
- [ARCH] Canonical Document ID Contract (DOC:CLAVE) formalizado — Unificación de todas las referencias de identidad bajo el formato estricto [PREFIX]:[KEY] (ej. KERNEL:ARCHITECTURE). Este contrato elimina la dependencia de UUIDs hardcodeados en prompts y anchors de texto plano ("flat-anchors"), permitiendo una resolución O(1) vía resolver_registry_v2.json. Invariantes: Prefijos en mayúsculas, Keys en Kebab-case, prohibición de IDs numéricos/UUIDs en capa de aplicación.
- [DOC] V-KERNEL §11 — Inyección de Contrato de Identidad — Inserción de la especificación técnica completa en el Kernel. Define: (1) Formato Canónico, (2) Registro de Prefijos Autorizados (KERNEL, MANUAL, CANON, TRACKER), (3) Protocolo de Resolución. El Índice Maestro del Kernel fue actualizado para incluir esta sección.
- [DEBT] DT-015: Plan de Migración de IDs Legacy — Identificación y mapeo de 26 ocurrencias de IDs antiguos para migración masiva. La ejecución queda vinculada a la resolución de DT-014 (Refactor de entity_prefix en módulo explícito).
- [AUDIT] Integrity Audit: PASS WITH FINDINGS (C1/M1) — Auditoría de sincronización post-actualización. Kernel y Manual preservan integridad estructural. Se confirman "gaps" de contenido (tablas vacías) en Career Canon (§B Skills y §H Achievements) derivados del bug de roundtrip de vsync_doc.py. No compromete el Kernel ni el Runtime actual.
### v8.8.0 — VANTAGE · 2026-07-04
Change_Log_v8.8.0
- [FIX] generate_entity_index_v2.py — Runtime Contract Migration: entity_id Namespace — generate_entity_id() tenía prefijo TRACKER hardcodeado. Todas las entidades recibían el mismo namespace sin consultar resolver_registry_v2.json, produciendo IDs idénticos entre entidades ARCHIVO y TRACKER en colisión de hash. graph_layer.py expresaba esas colisiones correctamente como self-loops en graph_v2.json. Fix: entity_prefix ahora se carga desde resolver_registry_v2.json en runtime. Self-loops eliminados.
- [ARCH] Architectural Invariants formalizados — resolver_registry_v2.json pasa de fuente declarada a fuente enforced como único punto de verdad para namespace ownership. Contratos explicitados: entity_id = identidad canónica · page_id = página física Notion · múltiples page_id pueden resolver al mismo entity_id · graph_layer.py nunca infiere namespaces · Runtime Build consume el Registry sin redefinir el contrato.
- [GOV] Artifact Migration — El contrato público del Runtime no cambió. Entidades ARCHIVO ahora generan ARCHIVO:H_xxx en artefactos generados (antes TRACKER:H_xxx por defecto de implementación). Registros Notion (page_id) no afectados. La migración ocurre únicamente al ejecutar Runtime Build — un pull del repositorio por sí solo no modifica ningún artefacto generado.
- [DEBT] DT-014 registrado — Extract Runtime Identity Contract: encapsular lógica de entity_prefix en módulo explícito. Prioridad: MEDIO. Fuera de scope de este release.
- Acceptance Audit: PASS WITH ARCHITECTURAL FINDING — FINDING: entity_id duplicados en scope ARCHIVO — mismo canonical_id, múltiples page_id históricos, no colisiones criptográficas, Resolver Layer y Query Layer no afectados. Clasificado como condición de calidad de datos históricos. No bloquea release.
- Git: commit 372e72f · tag v2.4.0 · rama main
# V | CHANGELOG

Change_Log_001
### v8.7.9 — VANTAGE · 2026-07-04
Change_Log_v8.7.9
- [FEAT] health_check.py — Entity Index auto-sync condicional — Si graph_v2.json o entity_index_v2.json superan 24h sin actualizar (INDEX_STALE_THRESHOLD_HOURS), el script dispara python3 vantage.py sync automáticamente — una vez por corrida, solo si se cruza el umbral. Clasificado como housekeeping de rutina, no remediación de fallo (ver KERNEL:FAIL-PHILOSOPHY): un índice stale no es un fallo del sistema, es mantenimiento esperado de infraestructura de lectura, equivalente en naturaleza al sync automático ya existente de L3 (Gmail) y L4 (git) vía launchd. Si el auto-sync falla (returncode ≠ 0, timeout, o vantage.py no encontrado), el script reporta y NO reintenta — a partir de ahí aplica Golden Rules estándar.
- [FIX] health_check.py — output de auto-sync ilegíble corregido — El reporte del resultado del sync mostraba fragmentos crudos de JSON (ej. })) en vez de un resumen legible. Agregada _summarize_sync_output(): parsea el stdout de vantage.py sync buscando el último bloque {...} válido y extrae status/entities_before/entities_after; si no hay JSON parseable, cae a la última línea de texto no vacía. Verificado con 3 casos de prueba (JSON válido, texto plano, stdout vacío).
- [DOC] Nueva sección KERNEL:HEALTH-CHECK — Documenta el contrato completo de health_check.py: los 9 checks ejecutados en orden fijo, la única excepción de escritura autorizada (auto-sync de Entity Index) con su justificación explícita frente a Golden Rules, y el criterio de agrupación de tickets por prioridad.
- [DOC] Manual §10.1 reescrita — De "Mantenimiento del Entity Index" (3 líneas) a sección human-facing completa: qué es y cómo correr health_check.py, qué lee en cada uno de sus 9 checks, índices monitoreados, comportamiento del auto-sync, cómo interpretar el output (✓/!/✗), y qué hacer si el auto-sync falla. §5.3 y §7 (Troubleshooting) actualizados para reflejar que el monitoreo de staleness del índice ya no requiere acción manual del operador en el flujo normal — el comando manual vantage.py sync queda como fallback documentado.
- [GOV] Governance — Versionado del Changelog — Identificado que la propiedad Versión de la página V-CHANGELOG no se actualizaba en cada entrada nueva, quedando desalineada con el ESTADO reportado en el cuerpo del documento (propiedad mostraba 8.7.6 mientras el cuerpo ya reflejaba v8.7.8). Corregido en esta sesión: propiedad Versión actualizada a 8.7.9. Nota agregada al System Prompt (KERNEL:AUDIENCE-SCOPE / §1) para que toda actualización futura del Changelog incluya la actualización de la propiedad Versión como paso obligatorio del mismo write — los números de versión en los demás documentos fundacionales deben ser reflejo del Changelog, no texto fijo mantenido por separado.
- [BUG] push_local_to_notion() destruye tablas — confirmado Resuelto en Bug Tracker en sesión anterior; verificado sin reapertura.
### v8.7.8 — VANTAGE · 2026-07-03
Change_Log_v8.7.8
- [GOV] System Prompt — Hardening de límites de interpretación (experimental) — Se reforzó el System Prompt para separar explícitamente contrato operativo, implementación interna, navegación lógica del Kernel y límites de interpretación del modelo. Motivo: se observaron inferencias arquitectónicas espontáneas no solicitadas (auditorías del Kernel, rutas lógicas interpretadas como estructura física) sin evidencia obtenida vía mecanismos oficiales de consulta. Sin evidencia de corrupción real en Source of Truth, Terminal, MCP o lazy_loader.py. Validación pendiente — requiere observar comportamiento en próximas sesiones/cuentas antes de confirmar cierre. Bug Tracker: 392938be-fc42-8111-bc97-f2a53f8b09d1.
### v8.7.7 — VANTAGE · 2026-07-03
Change_Log_v8.7.7
- [FIX] V-ALIASES — Corrupción de tablas Markdown restaurada — Página V | ALIASES presentaba 7 tablas fragmentadas en bloques de 1 fila (separador | --- | repetido por fila en lugar de único por tabla), causando renderizado roto en Notion. Reconstruida vía replace_content con las 7 tablas consolidadas como bloques únicos (header-row + N filas). Verificado post-write: 7 <table> nativas correctas.
- [BUG] Layer 4 — push_local_to_notion() no parsea tablas Markdown — Causa raíz identificada: el parser de vsync_doc.py (roundtrip local→notion) carece de rama elif l.startswith("|"); cualquier línea de tabla cae en el branch genérico de paragraph, destruyendo la estructura tabular al hacer push. No es la causa de la corrupción de V-ALIASES (esa se originó en escritura MCP directa fuera de este script), pero representa riesgo activo en cualquier vdoc local/vdoc auto futuro sobre documentos con tablas. Bug Tracker: 392938be-fc42-810c-b6e6-fc381e6af9b5.
- [PATCH] vsync_doc.py — _try_parse_table() agregado — Nueva función detecta bloques |...| consecutivos con separador válido y los reconstruye como bloque table nativo (table_width, has_column_header, table_row children), en lugar de fragmentarlos en párrafos. Verificado: fetch post-parche sano (17 bloques, --doc aliases --direction notion --dry-run sin errores). Pendiente: roundtrip real --direction local para confirmar cierre. Riesgo conocido no resuelto: tablas >100 filas podrían exceder el límite de children por request de la API de Notion. Backup pre-parche: vsync_doc.py.bak-{timestamp}.
### v8.7.6 — VANTAGE · 2026-07-03
Change_Log_v8.7.6
- [GOV] Normalización Terminológica L0 — Auditoría de Gobernanza y Mitigación de Drift Documental — Sesión de refinamiento estructural sobre la suite documental de VANTAGE. Objetivo: Eliminación de ambigüedades terminológicas y corrección de desajustes entre índices y cuerpo documental sin alterar lógica operativa ni especificaciones técnicas.
- V-MASTER-INDEX (Nuevo): Creación de página centralizadora de gobernanza. Impacto: Mapeo de los 6 documentos fundacionales y red de conectores bajo esquema KERNEL:.
- V-SYSTEM PROMPT (37b938be-fc42-8001-9b9b-fcf81130d274):
- Índice ligero integrado en cabecera (apunta a V-MASTER-INDEX).
- Normalización absoluta de IDs (KERNEL:CLAVE).
- Corrección transversal: "siete documentos" → "6 documentos fundacionales".
- V-KERNEL (377938be-fc42-805e-a408-c9ae518d4fe7):
- Índice reajustado a 10 capítulos reales (mitigación de secciones huérfanas como KERNEL:EVOLUTION).
- Normalización L0: "AI Component" / "componente AI" → "componente de IA" (homogéneo en KERNEL:ARCHITECTURE y KERNEL:OWNERSHIP).
- Remoción de referencia de acoplamiento directo "Claude" → "componente de IA" en KERNEL:CV-PIPELINE.
- V-MANUAL (372938be-fc42-8050-9a67-e40857d7806e):
- Índice expandido de 11 a 14 secciones (añadidas: §12 REGLAS DE ORO, §13 FILOSOFÍA DE FALLO, §14 SLA DE LATENCIA).
- Normalización L0: "componente AI" → "componente de IA" + estandarización de "VANTAGE Runtime".
- Homologación tipográfica: disparadores del pipeline en mayúsculas (CV-A, CV-B, Handoff).
- V-CAREER CANON (377938be-fc42-8089-93f2-f52dbd2dec6c):
- Índice sincronizado con esqueleto real.
- Normalización L0: "componente AI" → "componente de IA" + capitalización de términos clave (Career Canon, Handoff, CV-B).
- Homologación de "Visual Merchandising" como rol/título conceptual.
- Unificación de referencias a Figma Sync y Registry en OUTPUT CONTRACT.
- V-ALIASES & CHANGE LOG (37c938be-fc42-80d4-b9ae-f5969830331b):
- Índice ajustado para explicitar bloque de Lazy Loader.
- Normalización L0: formateo inline de lazy_loader.py + capitalización de "Kernel" como nombre propio.
- Auditoría visual: listado explícito de aliases activos (vload, vtrig, etc.).
- Criterios de aceptación verificados:
| Criterio | Estado | Observaciones |
| --- | --- | --- |
| Disipación de ambigüedades | ✅ Validado | Vocabulario alineado al System Prompt. |
| Coherencia estructural de índices | ✅ Validado | Eliminados gaps de secciones huérfanas. |
| Cero impacto funcional | ✅ Validado | Variables de entorno, flags y código intactos. |
| Control de Drift Documental | ✅ Validado | Preparado para escalamiento sin colisiones. |
### v8.7.5 — VANTAGE · 2026-07-03
Contexto: Estabilización post-Evento de Mutilación y alineación SSOT.
Change_Log_v8.7.5
---
- [FIX] Layer 4 Hardening — Exportación estructural Notion → ACTIVE (vsync_doc.py) — Corregido el recorrido recursivo de bloques hijos durante la exportación documental. Se agregó soporte para exportación de bloques table y table_row, preservando la estructura de los documentos fundacionales (Technical Kernel, System Prompt, Career Canon, Manual, Aliases y Change Log) durante la sincronización Notion → ACTIVE. Causa raíz: el exportador no procesaba correctamente bloques hijos de tipo tabla, provocando pérdida estructural en los archivos Markdown generados desde Notion.
- [FIX] Wrapper documental (vdoc.py) — Ampliado el soporte de sincronización quirúrgica incorporando los documentos aliases y change_log, alineando el wrapper con las capacidades existentes de vsync_doc.py. Actualizada la ayuda (--help) para reflejar los nuevos comandos soportados.
- [AUDIT] Layer 4 Hardening — Auditoría técnica concluida. Se descartó corrupción documental causada por Devin, Git, lazy_loader.py o vdoc.py. La causa raíz quedó localizada exclusivamente en el proceso de exportación Notion → Markdown de vsync_doc.py. Layer 4 se considera estabilizado y operativo.
---
- [PLAN] Governance Hardening v8.6.0 — Definido el plan de fortalecimiento de gobernanza documental compuesto por quince iniciativas (GH-001 a GH-015), orientadas a formalizar contratos documentales, normalizar terminología, reforzar la definición de responsabilidades, consolidar la autoridad editorial de Notion como SSOT y eliminar ambigüedades detectadas durante la auditoría técnica. Esta versión únicamente establece el plan de trabajo; no introduce cambios arquitectónicos ni funcionales.
---
- [DOC] Cierre de auditoría documental — Finalizada la validación de integridad de los documentos fundacionales. Se confirmó la preservación de la estructura documental durante la sincronización Notion → ACTIVE tras la corrección del exportador. Los ajustes editoriales identificados pasan al proyecto independiente Governance Hardening v8.6.0 y no bloquean la operación normal del sistema.
### v8.7.4 — VANTAGE · 2026-07-01
Change_Log_v8.7.4
- [AUDIT] Auditoría editorial v8.7.4 — Bloque 1 + Bloque 3 aplicados vía MCP directo (autorización operador, override Golden Rule Terminal-first). Correcciones de referencias cruzadas rotas en Kernel, Manual, Aliases, Career Canon (sin creación de contenido nuevo). Detalle completo: Bug Tracker.
### v8.7.3 — VANTAGE · 2026-06-30
Change_Log_v8.7.3
- [FIX] vdoc [doc] (atajos kernel/manual/etc) sobreescribía local sin comparar fecha — Los 5 atajos por documento (kernel, system_prompt, career_canon, manual, cheat_sheet) en vdoc.py tenían --direction hardcoded a "notion", ignorando la lógica de comparación de timestamps (mtime local vs last_edited_time Notion) que sí existe en vsync_doc.py --direction auto. Resultado: ediciones locales hechas entre syncs se perdían si se corría el atajo en vez de vdoc auto explícito. Fix: vdoc.py línea 49 cambiada de --direction notion a --direction auto. Componente: Python. Bug Tracker: 38f938be-fc42-818f-b76e-cf083642e617.
### v8.7.2 — VANTAGE · 2026-06-28
Change_Log_v8.7.2
- [DOC] Source_Type trailing space — source_analytics.py y gate_logic.py — Ambos scripts leían props.get("Source_Type") sin trailing space; el campo real en Notion es "Source_Type ". Fix aplicado Jun 26. Bug Tracker: 38b938be-fc42-817f-9ae0-f28dc7e268f9.
- [DOC] Fuente no asignada en Paso 0.5 — Source_Type sin trailing space — layer_1_run.py línea ~618. Fix aplicado Jun 26. Bug Tracker: 38b938be-fc42-81a7-9593-f6ea8af18da2.
- [DOC] Source_Type vacío — backfill 9 registros — 9 registros corregidos vía script puntual. Bug Tracker: 38b938be-fc42-8117-9d3f-cb2903f49415.
- [DOC] Next_Action type mismatch — rich_text en layer_1_run.py — Fix 2 correcto: revertido a rich_text. Líneas: 591, 745, 892. Bug Tracker: 38b938be-fc42-81fa-b1be-e60f909107fc.
- [MAINT] Scripts one-shot deprecados en Script Library — patch_kernel.py, patch_manual.py, patch_career_canon.py, patch_cheat_sheet.py, fx4_legacy_check.py marcados como Deprecado / Archivar.
### v8.7.1 — VANTAGE · 2026-06-28
Change_Log_v8.7.1
- [PATCH] Auditoría editorial v8.7 — 4 documentos fundacionales corregidos — 16 hallazgos aplicados vía scripts de patch atómicos (patch_kernel.py · patch_manual.py · patch_career_canon.py · patch_cheat_sheet.py). Kernel: GAP-03 duplicado eliminado, §4.6/§4.7 reordenados, 17 headers [ID: UUID] normalizados a [ID:UUID], lista §4.5 numeración corregida. Manual: 4 prefijos KERNEL-* corregidos a MANUAL-* en ÍNDICE, IDs RUNTIME-* con notas de resolución, stubs §4 CICLO SEMANAL y §6 GESTIÓN DE DATOS insertados, header SLA con ID asignado. Career Canon: título duplicado eliminado, versión 8,5→8.7, fecha normalizada a ISO 8601, tag <aside> HTML eliminado, §B SKILLS CANON y §H ACHIEVEMENT LIBRARY marcadas [PENDING DATA]. Cheat Sheet: header # ## crítico corregido a ##, stub §1 ALIASES & COMANDOS RÁPIDOS insertado con tabla canónica, header CHANGELOG normalizado.
### v8.7 — VANTAGE · 2026-06-27
Change_Log_v8.7
- [ARCH] Figma Sync integrado como CV Output Layer — Carpeta Figma Sync/ establecida al mismo nivel jerárquico que L1–L4 dentro de 04-Vantage_CV/. Contiene los 4 componentes del plugin Figma: manifest.json · code.js · ui.html · registry_seed.json. No es capa de búsqueda ni de infraestructura de datos — es la capa de materialización del CV en Figma.
- [NEW] registry_seed.json — SSOT de nodos Figma — JSON canónico que mapea tokens semánticos (ej. HEADER_NAME, EXP_L_OR_AL_LUXE_M_XICO_BULLET_1) a IDs crudos de nodo Figma (ej. "2:4"). 52 tokens mapeados cubriendo header, perfil, habilidades, experiencia C01–C05, formación y certificaciones. Fuente única de verdad para toda operación de inyección sobre el lienzo.
- [REFACTOR] code.js — Registry V2 / Resolver Layer V1 — Motor del plugin refactorizado. Deprecado: findAll() con búsqueda O(n) por nombre de capa [VANTAGE] KEY_NAME. Activo: getNodeById(rawId) con resolución O(1). Resolver dual: KEY semántica → REGISTRY → ID crudo; ID crudo directo (flujo Markdown figma_text_id) → uso directo sin lookup. Notify actualizado para confirmar modo Registry V2 y reportar keys sin resolver.
### v8.5.4 — VANTAGE · 2026-06-23
Change_Log_v8.5.4
- [FIX] Campo jd agregado al pipeline L1/L2 — bug resuelto en consolidación — jd estaba ausente del ITEM SCHEMA de Prompt A y de la capa de escritura de feed_processor.py, impidiendo que el texto del JD llegara al Tracker. Tres patches quirúrgicos aplicados: (1) Prompt A — "jd": "string or null" agregado al ITEM SCHEMA como último campo, con instrucción de poblar cuando fetch_status = direct_apply; (2) feed_processor.py — jd_prop agregado a NotionSchema; JD escrito en build_notion_properties() via rich_text_value(rec["jd"][:2000]); (3) Kernel §4 — mapeo jd → JD documentado en tabla de vocabulario; nota operativa sobre comportamiento cuando el campo llega null (fetch_status ≠ direct_apply). Wrappers L1/L2 heredan el contrato de Prompt A sin cambios individuales.
### v8.6 — VANTAGE · 2026-06-23
Change_Log_v8.6
- [ARCH] Normalización de capa documental — cierre formal de auditoría externa (3 agentes independientes). Todos los pendientes resueltos en sesión 2026-06-22.
- [ARCH] Convención ACTIVE/ establecida — paths versionados (.../v8.5/) reemplazados por directorio agnóstico de versión. Al pasar a v8.7: copiar archivos a ACTIVE/, cero cambios de código.
- [NEW] vsync_doc.py migrado a Layer_4/scripts/ — alias vdoc [dry|notion|local]. Sync bidireccional Notion ↔ ACTIVE/ para los 5 docs fundacionales + auto-commit GitHub al terminar vdoc notion.
- [FIX] Bugs resueltos en vsync_doc.py: layer_1.env token con \n embebido · _rich_text() con None · _block_to_md() en callout con icon: null · safe_list() reemplaza blocks.children.list() (bug silencioso de notion-client 3.x).
- [ARCH] Sistema normalizado a v8.6 en todos los documentos fundacionales.
### v8.5.3 — VANTAGE · 2026-06-23
Change_Log_v8.5.3
- [NEW] vsync_doc.py — Sync bidireccional Notion ↔ .md (BUG-005 cerrado) — Script independiente en Layer_1/scripts/. Sincroniza 5 páginas fundacionales (KERNEL · SYSTEM PROMPT · CAREER CANON · MANUAL · CHEAT SHEET) contra sus .md locales en - Documentación/v8.5/. Flags: --direction {notion|local|auto} (auto: gana timestamp más reciente; notion: default pre-sesión; local: para edits offline) · --dry-run (inspección sin escritura) · --doc {key} (sync quirúrgico por documento). Output --json disponible para integración futura con vstatus. Alias: vsync-doc. Bug Tracker: 388938be-fc42-8198-a954-db353d22a1cc.
### v8.5.2 — VANTAGE · 2026-06-21
Change_Log_v8.5.2
- [FIX] notion_utils.py — rewrite completo de Client — notion_utils.py no exportaba clase Client. Reescrito con namespaces client.data_sources.query(data_source_id=...), client.pages.update(page_id=..., properties=...), client.pages.retrieve(), client.pages.create(), client.databases.retrieve(), client.databases.query(). Drop-in compatible con notion-client 3.x. Throttle, retry, cache y metrics del módulo original preservados. Afectaba: status_report.py, source_analytics.py, batch_operations.py, pipeline_recovery.py, backfill_class_a.py.
- [FIX] NOTION_VERSION corregida — Versión 2025-09-03 (futura, inválida) reemplazada por 2022-06-28 (estable). Causaba invalid_request_url en todas las llamadas a la API.
- [FIX] DB IDs corregidos en scripts — status_report.py usaba COL ID (442938be) en lugar del DB ID (596938be). source_analytics.py, batch_operations.py y pipeline_recovery.py usaban ID desconocido (4e542b37). Todos corregidos a 596938be-fc42-836b-aea7-814a1491bd47 (VANTAGE TRACKER DB).
- [FIX] pyyaml instalado — profile_evolution.py fallaba con ModuleNotFoundError: yaml. Instalado en .venv.
- [FIX] layer_1_pipeline.sh — argumento backfill — @ pasaba backfill como argumento posicional a backfill_class_a.py. Corregido a{@:2} para pasar solo flags (--dry-run).
- [FIX] batch_operations.py — escritura destructiva sin guardia — El script ejecutaba batch Target → Exploratorio sin flag de protección. Reescrito con flag --execute obligatorio. Sin el flag: solo reporte. Con --execute: escritura. Eliminado input() interactivo. Alias vl1 batch ahora es read-only por defecto.
### v8.5.1 — VANTAGE · 2026-06-21
Change_Log_v8.5.1
- v8.5.1 (Patch OA-01): Migración de MCP Client-Side Lazy Load a Server-Side Lazy Load vía Terminal (lazy_loader.py). Reducción drástica de Input Tokens al aislar payloads de IDs embebidos desde Python antes de inyectarlos al contexto del LLM.
### v8.5 — VANTAGE · 2026-06-20
Change_Log_v8.5
- [ARCH] Patrón "Thin Client, Thick Server" & MCP Lazy Loading — Cobertura completa (SP + KERNEL + CAREER CANON + MANUAL) — Refactorización arquitectónica mayor en dos capas. Capa 1 — Cirugía de bloques en V | KERNEL: fusión estructural de identificadores de anclaje. Antes: párrafo con ID + bloque heading_2 separado (API retornaba 2 objetos; bloques huérfanos). Después: ## [ID: {KERNEL_MASTER}:{ruta}] TÍTULO — ID y encabezado como un solo objeto. Un read_block extrae el encabezado + todos sus hijos en una sola llamada limpia. Gap de resolución en Notion API eliminado. Capa 2 — Compresión del System Prompt (Enrutador MCP): SP despojado de texto descriptivo y convertido en modelo imperativo estructurado. Directiva Economía de Contexto implementada (respuestas ultra-concisas, solo carga útil). Patrón Lazy Loading centralizado: SP ya no almacena flujos completos; posee un índice de enrutamiento que construye cadenas de búsqueda exactas ([ID: {KERNEL_MASTER}:{ruta}]) para cargar módulos específicos (schema-001, cv-pipeline-001) únicamente cuando el trigger activo lo requiere. Impacto operativo: ~50% reducción del footprint del SP (token-efficiency). Zero hallucination por carga quirúrgica de solo la regla necesaria. KERNEL en Notion escala infinitamente sin añadir tokens al prompt base. Career Canon (377938be-fc42-8089-93f2-f52dbd2dec6c): misma cirugía de bloques aplicada. Todos los IDs de anclaje de secciones (:canon-profile-001, :canon-skills-001, :canon-experience-001, :canon-achievements-001, :canon-kpis-001, :canon-facts-001, :canon-positioning-001, :canon-output-contract-001, :canon-coverage-gate-001, y los IDs de experiencias C01–C05, KPI01–KPI08, CF01–UF03, positioning N1–N4) fusionados con sus encabezados. Un read_block sobre cualquier sección del Canon ahora retorna el bloque completo con su payload en una sola llamada, habilitando la carga diferida del perfil completo del operador sin cargar el documento entero al contexto. Manual de Usuario (372938be-
- L4 — Version Control & Infrastructure — Nueva capa documental. git_sync.py + git_sync_wrapper.sh + com.vantage.gitsync.plist instalados en Layer_4/scripts/ y Layer_4/wrappers/. Detecta cambios en el repo, hace add -A + commit con timestamp + push a origin/main. Atomic: sin cambios → silencio total. Con cambios → notificación Hero. Error → notificación Basso. launchd corre a las 09:00, 15:00, 21:00. Alias: vgit. Reutiliza .venv de Layer_1. Repo: github.com/mauriciomeyran/jhs-pipeline.
- Nomenclatura de capas actualizada — L1 Active Recon · L2 Strategic Search · L3 Passive Intake · L4 Version Control & Infrastructure. L4 no es una capa de búsqueda — es infraestructura documental del sistema. — _write_heartbeat(total_created, total_failed) agregada en layer_3_mail.py. Escribe ~/.vantage/l3_heartbeat.json al final de cada run con campos last_run (ISO-8601 UTC), total_created, total_failed. Directorio ~/.vantage/ se crea automáticamente. Imports con alias privados (_json, _pl, _dt) para evitar colisiones. Bug Tracker: 382938be-fc42-81b3-98c1-e513eab798fc.
- M-06 cerrado — find_candidates pre-filter — _handle_find_candidates() en agent_api.py (~l.150) ahora incluye score >= 60 como condición de filtro. Elimina el riesgo de que el endpoint devuelva entidades por debajo del umbral Gate=CREATE. Umbral alineado con Kernel §5. Bug Tracker: 382938be-fc42-810c-9e94-eaa6f416a68f.
- M-01 confirmado operativo — vantage.py status produce index_age_hours: 36.5 + "warning": "entity_index_stale" correctamente. No requirió cambios.
- Nomenclatura mail_pipeline.py corregida — Nombre conceptual desactualizado en Kernel §2 (arquitectura L3) y §3 (ownership table) alineado con nombre real en disco: layer_3_mail.py (Layer_3/scripts/). Origen del alias: renaming pre-v8.0 (layer_2_mail.py → layer_3_mail.py) no propagado a la documentación del Kernel. Manual §4 corregido: LAYER 2.app → LAYER 3.app. Manual §5.4 Arranque Frío actualizado con nombre real + verificación de heartbeat (cat ~/.vantage/l3_heartbeat.json).
### v8.4 — VANTAGE · 2026-06-16
Change_Log_v8.4
- vantage.py sync implementado — Nuevo comando CLI + módulo. Regenera entity_index_v2.json desde Notion en vivo (atomic write: .tmp → os.replace), invalida cache de query_layer con force_reload=True, ejecuta status() al terminar. Resultado en producción: 465 entidades, 100% hash coverage, 0 orphans, 4.3s. Conflicto notion_client local vs SDK PyPI resuelto vía pop(sys.modules) + filtro sys.path + restauración en finally. Implementado con Perplexity Pro + Claude Sonnet 4.6 Thinking + FileSystem MCP.
- resolver_registry_v2.json corregido — Campos status y resolution_contract.live_resolution actualizados de DESIGN_ONLY / NO IMPLEMENTADO a estado operativo real. Resolver Layer verificado en vivo desde 2026-06-15. Pendiente documentado en Runtime Doc §5.7 cerrado.
- vacante_purge_trash_only.py depreciado — Workaround de emergencia para un run puntual. Script canónico: vacante_purge.py (copia + trash, atómico). Renombrado a _DEPRECATED_vacante_purge_trash_only.py. Pendiente de eliminación tras auditoría.
- Archivos .bak generados — vantage.py.bak, vantage.py.bak_20260616_035426 creados por Perplexity durante implementación de sync. Pendiente: mover a Layer_1/backups/ o eliminar.
- VANTAGE Runtime V1 documentado — Documentación formal en V | RUNTIME DOCUMENTATION y V | RUNTIME ROADMAP. Patches de Runtime en Kernel y Manual pendientes de inserción (bloqueados hasta resolver los 4 pendientes del Roadmap §7.2).
- SP actualizado a v8.4 — vantage.py sync agregado al scope y tabla de triggers (§7). Tokens de aprobación ampliados: Ok, Go, YEP.
### v8.3 — VANTAGE · 2026-06-15
Change_Log_v8.3
- Sistema de IDs duales desplegado — Structural ID (<!-- ID: [page_id:node_id] -->) + Visible ID (ID: [page_id:node_id]) implementados en los tres documentos fundacionales: Kernel, Manual de Usuario y System Prompt. Los IDs son los nodos de conexión para el cableado de Runtime.
- VANTAGE Runtime V1 construido — Stack completo operativo: entity_index_v2.py → resolver_layer_v1.py → query_layer.py → context_layer.py → agent_api.py → notion_client.py (hardened: cache, retry, throttle, metrics). 465 entidades indexadas, 100% hash coverage, 0 orphans. Verificado en vivo el 2026-06-15.
- vantage.py entrypoint único — CLI + módulo Python. Comandos: status, ask, resolve, context, query.
- Registry V2 — entity_index_v2.json, graph_v2.json, backlinks_v2.json, resolver_registry_v2.json generados. Graph Layer con 13 edges archived_from (no ejercitado en vivo al 2026-06-15).
- backfill_hash.py v1.2 completado — 100% hash coverage en VANTAGE_TRACKER y ARCHIVO_TRACKER. Prerequisito para generación del Entity Index.
### v8.2 — VANTAGE · 2026-06-14
Change_Log_v8.2
- Kernel optimizado para token efficiency — Refactor completo del Technical Kernel: schemas, workflows y checklists consolidados. Arquitectura token-efficient: SP contiene únicamente contratos operativos activos; lógica completa vive en el Kernel.
- Career Canon integrado — Career Canon v8.2 con métricas verificadas, node markers Figma (###### figma_text_id), bold metrics con escaped parentheses. Output Contract v1.0 operativo.
- SP v8.2 — Contratos operativos únicamente. Referencias cruzadas al Kernel para schemas y lógica completa. Ownership Matrix Class A/B consolidada.
### v8.0 — VANTAGE · 2026-06-09
- Renaming de capas — Arquitectura renaming completo: Layer 3 (Active Market Reconnaissance) → L1 — Active Recon (Career Sites · LinkedIn · Aggregators) | Layer 1 (Strategic Search) → L2 — Strategic Search (Gemini · You.com · Grok) | Layer 2 (Passive Intake) → L3 — Passive Intake (layer_3_mail.py). Jerarquía dedup: L1 > L2 > L3.
- Perplexity — nuevo rol canónico — Removido de motores de extracción (no opera en Extraction Mode en job boards/career sites). Rol: Consolidation & Dedup — paso post-extracción del ciclo del lunes. Sigue siendo motor de ensamblaje de prompts (sin cambio).
- Ciclo semanal actualizado (Manual §4) — Lunes: ①L1 Active Recon ②L2 Strategic Search ③Consolidation&Dedup (Perplexity) ④feed_processor.py. Martes: Dashboard & Solve Conflicts. Miércoles: CV Optimization.
- Kernel §3/§4/§5/§6/§13 actualizados — Naming canónico L1/L2/L3 propagado en tabla de arquitectura, contratos de capa, flujos de datos y Search Matrix.
- Manual §8 actualizado — Referencias Layer 1/3 → L1/L2 en callouts de prompts y wrappers. Perplexity: rol correcto documentado.
- 
- Canonización L0 — Perplexity renombrado a L0 - Consolidation & Dedup. No es una capa independiente — es el paso del pipeline del lunes entre extracción y FEED. Recibe 6 JSONs: L1 (Career Sites · LinkedIn · Aggregators) + L2 (Gemini · You.com · Grok). Jerarquía de dedup L1 > L2 aplicada en este paso. L3 no pasa por L0.
- Naming wrappers L1 — Wrappers Career Sites · LinkedIn · Aggregators corregidos: Layer 3 → L1, referencias a Perplexity/Comet eliminadas. Responsabilidades canónicas: Career Sites = career pages oficiales + ATS únicamente; LinkedIn = LinkedIn Jobs únicamente; Aggregators = job boards LATAM (OCC · Indeed · Computrabajo · Bumeran).
- Naming L2 - Prompt A — Renombrado de “LAYER 1 - Prompt A” a “L2 - Prompt A”. Categoría LAYER 2 confirmada.
- Kernel §3/§4/§5/§13 actualizados — L0 propagado en arquitectura, flujos de datos, pipeline de fases y search matrix.
- Manual §4/§8 actualizados — PASO ③ LUNES y callout Perplexity reflejan rol L0 canónico.
- Revisión editorial completa — pasada única sobre Kernel y Manual. Sin cambios de arquitectura ni contratos.
- Kernel — §1: prohibiciones reformuladas en voz de IA operadora. §2: redundancia de “no evalúa” eliminada (referencia cruzada a §7/§15). §3: nota de implementación de jerarquía dedup agregada. §4: “Cierre obligatorio” removido (pertenece al Manual). §5: “Rol de Perplexity” consolidado como referencia cruzada. §7: columna AI Component clarificada (calidad estratégica vs. errores de formato). §8: visual_signal/innovation_dna con instrucción de ignorar sin comentar. §10: mini-ejemplo EXPIRED vs. Expirada agregado. §11: scripts/archivos reemplazados por referencia cruzada al Manual §10. §13: segunda instancia de BOUNDARY consolidada. §14: input de FEED clarificado como N/A. §15: comportamiento con JSON vacío post-DRY RUN documentado. §19: comportamiento ante solicitud de cambio inválido especificado.
- Manual — §1: plain text → prosa Notion. Hard Blocks movidos a §6. §2: plain text → tablas Notion; celda Python dividida en Scoring/Gates y FEED. §3: plain text narrativo → prosa Notion. §4: callout ⚠️ movido antes de PASO ①; pasos bold → H3; L3 reescrito como subsec. colapsable. §5: [Sistema] = feed_processor.py aclarado. §6: nota de timing Bypass agregada. §7: diagnósticos reformulados en voz del operador. §8: Prompts B y C URL directa → mention-page. §9: NAD y RT-1 agregados al glosario. §11: referencia a §8 en Red Flags.
### v7.5 — VANTAGE · 2026-06-06
- Migración FEED a Python — feed_processor.py asume ownership completo del ciclo FEED (Layer 1 y Layer 3). Claude queda excluido de esta operación.
- BOUNDARY v7.5 — Kernel recibe bloque de boundary al inicio del Technical Kernel. JSON de vacantes sin trigger CV-A · FAST [URL] · CANON-UPDATE → responde: “El procesamiento de FEED está migrado a feed_processor.py.”
- Confirmación interactiva — feed_processor.py presenta DRY RUN en terminal + _dryrun.md; escritura requiere s del operador.
- REVIEW_NEEDED — nuevo status de vacantes. Python lo asigna cuando alias no resuelve, URL falla parcialmente o hay semi-duplicado. Vacantes con este status se escriben en Notion y se revisan en Dashboard antes del siguiente ciclo.
- Campos layer y hash agregados a Class A — layer (L1/L3) y hash (dedup cross-layer) escritos por feed_processor.py en cada entrada.
- Dedup cross-layer — feed_processor.py computa hash diferenciado por tipo de URL y consulta Notion con ventana de 30 días antes de escribir.
- Archivo DRY RUN archivado mensualmente — estructura: ARCHIVO → YYYY-MM MONTH → DRY RUN · YYYY-MM-DD · Layer L{1|3}.
- Manual §4 (LUNES) y §4 (MARTES Layer 3) actualizados — PASOS 3 y 4 apuntan a layer_1_pipeline.sh feed + confirmación s.
- Callout v7.5 — warning amarillo en Manual §4: Claude no participa en ciclo FEED.
### v7.4 — VANTAGE · 2026-06-06
- Migración de ensamblaje de prompts — responsabilidad transferida de Claude a Perplexity Desktop (vía MCP Notion). Claude queda excluido de esta operación.
- Layer 1 — Perplexity lee Prompt A + Wrapper del motor, concatena y completa TODAY'S DATE. Trigger: "entrégame el prompt de [motor]".
- Layer 3 — Perplexity lee Prompt D + Wrapper del canal, concatena y completa TODAY'S DATE. Trigger: "entrégame el prompt de [Career Sites | LinkedIn]".
- Contrato de ejecución documentado — Wrapper ausente en PROMPT LIBRARY = reportar y detener, no inferir. Prompt A y D no se ejecutan sin Wrapper.
- Manual §8 actualizado — responsable, triggers Layer 1 y Layer 3, regla de no reutilizar sesiones anteriores.
- Manual §4 (LUNES) actualizado — instrucciones operativas apuntan a Perplexity Desktop.
- Kernel §13 actualizado — contrato de ensamblaje, alcance por capa, trigger unificado.
### v7.2 — VANTAGE · 2026-06-01
- Layer 2 — layer_3_mail.py operacional (antes llamado mail_pipeline.py) — Reemplaza arquitectura Make → Notion raw por pipeline autónomo Gmail → Groq → Notion con Class A poblado
- Parsing con LLM — Groq (llama-3.3-70b) extrae rol, marca, url, holding directamente del cuerpo del email; solo roles VM/retail pasan
- Dedup nativo en Layer 2 — query Notion por Rol + Marca antes de cada write; duplicados descartados sin write
- Hard blocks en sender check — L’Oréal · Levi’s/Dockers · El Palacio de Hierro filtrados antes de Groq
- Cadencia automática — launchd · 3 runs diarios 08:00 · 14:00 · 21:00 · alias mail para run manual
- §18 Arquitectura Diferida actualizada — Email parsing (Layer 2) pasa de Deferred a Operacional
### v7.1 — VANTAGE · 2026-05-31
- Career Canon integrado en el pipeline — 3 patches quirúrgicos sin alterar arquitectura de capas ni ownership Class A/B
- § 11 CV-B — Input ampliado: HANDOFF + Career Canon activo. Canon check obligatorio antes de generar F2. Desviaciones se reportan, no se silencian.
- § 7 Class A · Campo JD — En CV-A, el AI Component cruza keywords del JD contra el Canon antes de generar el HANDOFF. Discrepancias van a fit_gaps.
- § 5 CANON-UPDATE — Contrato completo: output = Canon en Notion + .md con Figma tags (Output Contract v1.0). Dos outputs obligatorios.
- Output Contract v1.0 operativo — tag schema Figma + regla de dos outputs documentada en Career Canon § L
- Career Canon — UF01/02/03 resueltos · KPI06 cerrado (red nacional México) · P02-EN redactado · C03 normalizado a Levi Strauss & Co. (Dockers)
## v7 — VANTAGE · Mayo 2026
- Renombrado de JHS → VANTAGE
- Arquitectura de tres capas (Layer 1 / Layer 2 / Layer 3) documentada formalmente
- Layer 1 — Strategic Search: cuatro motores en paralelo (Gemini, Perplexity, You.com, Grok); ninguno es primary ni fallback
- Layer 2 — Passive Intake: Gmail → Make → Notion (raw, Class B vacío); Make como orchestration puro, sin parsing
- Layer 3 — Active Market Reconnaissance: verificación activa obligatoria antes de salir de capa
- RT-1 Dashboard certificado como operacional: recuperación de vacantes BLOCKED, FSM de 5 estados, event log append-only
- Sección Dashboard añadida al Manual de Usuario con flujo paso a paso y tabla de estados
- Source_Type expandido: Inbound, Referencia, Networking activan Bypass automático
- Separación arquitectónica documentada: EXPIRED (Class B) ≠ Expirada (Class A)
- Comando CANON-UPDATE: genera dos outputs obligatorios (página Notion + archivo .md con Figma tags) bajo Output Contract v1.0
- Indicador de salud Career page URL success rate ajustado a > 80% (Manual) / > 90% (Kernel)
- Triggers: SYNC restringido a datos puros ≤12 líneas; QA evalúa formato y completitud, no fit
- Scripts renombrados: ~/jhs_pipeline.sh → ~/vantage_pipeline.sh; ~/jhs_notion_audit/ → ~/vantage_notion_audit/
- Manual de Usuario reestructurado a 12 secciones; Sección 4 expandida con ciclo semanal de cuatro motores
- Sección ARCHIVADAS separada del documento principal
## v6.2.1 — JHS · Abril 2026
- HANDOFF estructurado con 5 campos obligatorios (empresa, rol, JD_keywords_top6, fit_gaps, tono_marca)
- Trigger SYNC añadido: lee Notion via MCP, reporte máximo 12 líneas, sin WRITE
- Trigger CANON-UPDATE añadido: diff del usuario → bloque Markdown afectado; sin WRITE automático
- Alias map extendido para dedup (LVMH, Kering, Inditex, Nike, Adidas, Luxottica)
- BATCH RULE: FEED con más de 10 vacantes se divide en lotes de 10; procesamiento secuencial con header de lote
- Prioridad 5 y 6 diferenciadas: 5 = exploratorio activo con timing incierto; 6 = radar pasivo/especulativo
## v6.2 — JHS · Abril 2026
- Link muerto = Score 0 sin excepciones (regla endurecida)
- Protección total: si Next_Action ya tiene valor, Python no lo sobreescribe
- Gate decision: Source_Type Inbound/Referencia/Networking activa CREATE automático (Bypass)
## v6.1 — JHS
- Scoring realista: Score ≥ 60 = Ready-to-Apply (umbral consolidado)
- Vista Ready-to-Apply como espacio de trabajo diario principal
## v6.0 — JHS
- URL_GATE pre-scoring: verificación de accesibilidad antes de cualquier cálculo de fit
- Limpieza masiva de entradas legacy
- Score 0 automático para links muertos
## v5.0 — JHS
- Arquitectura híbrida Python + Claude introducida
- Python asume ownership de campos Class B (Score, Gate, VM_Scope, Role_Class)
- Separación formal entre AI Component (texto) y Python (cálculo determinista)
## v4.x — JHS
- Sistema manual Claude-only
- Sin pipeline Python; procesamiento y evaluación en sesión de chat
---
ESTADO: v8.9.6 | ACTUALIZADO: 2026-07-05
---
