# V | CHANGELOG

IDs afectados: Ninguno (sin alta/baja de ID canónico — extensión de nodo existente).
Estado final de la validación: Write-Back Verification PASS — confirmado vía re-fetch en vivo de §14, regla nueva presente sin mismatch. Census no aplica (sin altas/bajas de ID). Sin DRY RUN presentado en el mismo turno de aprobación por instrucción explícita del operador (yep).
Tipo: [CODE] [FIX]
Documento modificado: Layer_1/scripts/hard_block_gate.py · Layer_1/config/hard_blocks.json · Layer_1/scripts/layer_1_orchestrator.py (manual_first_protection) · src/gate_logic.py (docstring only) · tests/test_hard_block_gate.py · tests/test_vantage_status.py · tests/test_llm_providers.py · tests/test_agent_history_diagnostics.py · tests/test_scout_dry_run.py · tests/test_layer_1_orchestrator.py (G9)
Documentos potencialmente afectados: Ninguno en Kernel/Manual/SP/Canon — consolidación de código Layer_1 y alineación de contratos de tests, sin cambios normativos.
Tipo de impacto: Operativo — cierre de v9.23.0 sobre v9.22.0: consolidación de Fase 2 (2.5–2.6, ya entregada en commit previo 62ee000), un bug funcional real corregido en G5 (manual-first), y alineación de la suite de tests con el código productivo tras la migración de LangChain a browser-use.
Causa raíz (G5 manual-first): manual_first_protection() dependía únicamente de is_mutable() como guard — sin evaluar explícitamente la ventana de edición humana contra Last_Gate_Run. Last_Gate_Run y last_successful_run.json son contratos distintos; el guard general no sustituye la ventana manual.
Acción correctiva ejecutada:
1. Hard Block Gate (2.5) — hard_block_gate.py consolidado como implementación standalone; hard_blocks.json es la única fuente de términos bloqueados, sin capa paralela de regex. Fixtures de test_hard_block_gate.py alineados con la fuente canónica (Aéropostale removida de los fixtures — nunca perteneció al conjunto vigente de Hard Blocks; el fallo era del fixture, no del Gate. Bloqueo de producción sin cambios).
1. Scout (2.6) — src/gate_logic.py fuera de alcance total, decisión explícita del operador (diseño no completado ni a completarse). Cambio limitado a docstring documentando la decisión, sin efecto en comportamiento.
1. G5 Manual-First — manual_first_protection() ahora evalúa explícitamente last_edited_time > Last_Gate_Run con actor humano válido, antes del guard general. Se preserva la excepción de una sola pasada para Rechazado (Q-11/SCHEMA-008).
1. Suite de tests — vantage_status.py con cobertura contractual nueva (normalización, mapeos legacy, terminalidad, protección/mutabilidad, Gate Decision); test_llm_providers.py migrado del API interno obsoleto _chat_openai (eliminado en edc75c5, migración a browser-use) al API real (ChatOpenRouter, ChatOpenAI+base_url, Groq agregado al contrato de providers); test_scout_dry_run.py con ROOT corregido (parents[2]→parents[1], escribía fuera del repo); test_default_provider_is_local_ollama aislado de LLM_PROVIDER del .env local; test_g9_changelog_v922_entry ampliado de text[:2500] a text completo.
Resultado:
- Suite completa: 311 passed, 5 failed (todos ModuleNotFoundError: browser_use, dependencia opcional no instalada en el entorno de verificación — no relacionado al código bajo prueba), 2 skipped.
- Cost-control fallback validado contra comportamiento real bajo USE_CHEAP_FALLBACK=true / LLM_COST_LIMIT<1.0 — sin cambio de política: el fallback de Gemini sigue en gemini-1.5-flash (discontinuado según el propio código), no corregido en este lote.
- G9 Change Log: "v9.22.0" localizado como mención de paso en entrada normativa distinta (Fe de Erratas G8/G9, línea 46) — no existe ni existía una entrada propia para esa versión; el fix corrige el rango de búsqueda del test, no crea un registro nuevo.
IDs afectados: Ninguno (código y tests; no dispara CENSUS-SYNC Regla 1).
Estado final de la validación: Commits verificados en origin/main: 62ee000 (Fase 2 lote 2) y 16acdea (auto-sync — G5 fix + suite de tests). Fixes de Fase 1 y Fase 2 lote 1 verificados en sesiones previas (ver HO-000059). DRY RUN presentado y aprobado explícitamente por el operador (yep) antes de escritura — version bump y esta entrada ejecutados en la misma pasada por instrucción del operador.
Handoff de referencia: continuación de HO-000059 (CLAUDE/MAIN), consolida Fase 2 completa (2.1–2.6) + hallazgo G5 + reconciliación de suite de tests reportados por sesión posterior.
---
Tipo: [CODE] [FIX]
Documento modificado: Layer_3/scripts/layer_3_mail.py (línea 872) · tests/test_tracker_flow_v3.py (test_f11_composite_guard)
Documentos potencialmente afectados: Ninguno en Kernel/Manual/SP/Canon — corrección de código puro, sin cambio normativo.
Tipo de impacto: Operativo — corrección de una regresión introducida por el propio commit 62ee000 (Fase 2 lote 2), no un hallazgo nuevo de auditoría.
Causa raíz (regresión L3): la migración de layer_3_mail.py al backend configurable ollama/groq (commit 62ee000, 2026-09-16) reescribió el archivo completo a partir de una copia previa al fix de Fase 2 (2.1, Target→Objetivo) — el rewrite reintrodujo Status="Target" sin que nadie lo notara, porque el commit se tituló y revisó como cambio de hard_block_gate.py/gate_logic.py, sin mención de layer_3_mail.py. vantage_status.LEGACY_STATUS_MAP["Target"]="Objetivo" nunca se revirtió y siguió vigente todo este tiempo, ocultando el drift.
Causa raíz (test_f11_composite_guard): el fixture usa una fecha fija (2026-09-10T12:00:00.000Z) sin aislar _was_edited_since_last_run() del reloj real. Esa función cae a un fallback de "< 7 días desde hoy" cuando no hay state file — el test expira exactamente al séptimo día de su propia fecha hardcodeada (2026-09-17), no por contaminación de state/last_successful_run.json como se diagnosticó inicialmente. Verificado con VANTAGE_STATE_DIR apuntando a un directorio vacío: el test sigue fallando igual, confirmando que la causa no es el state file.
Acción correctiva ejecutada:
1. layer_3_mail.py:872 — Status="Target" corregido a Status="Objetivo", restaurando el fix de Fase 2 (2.1). Sin otro cambio: no toca EXTRACTION_BACKEND ni ningún otro campo introducido por 62ee000.
1. test_f11_composite_guard — agregado parámetro monkeypatch; se mockea tracker_flow._was_edited_since_last_run para devolver True sin depender de la fecha real del sistema ni de ningún state file. Path de monkeypatch corregido a tracker_flow._was_edited_since_last_run (import plano vía sys.path.insert, no Layer_1.scripts.tracker_flow, que no existe como módulo).
Resultado:
- Suite completa en el Mac del operador (con browser_use instalado): 318 passed, 0 failed, 2 warnings (deprecaciones externas de browser_use/google.genai, no relacionadas a VANTAGE).
- grep -c '"Target"' Layer_3/scripts/layer_3_mail.py → 0.
IDs afectados: Ninguno (código y tests; no dispara CENSUS-SYNC Regla 1).
Estado final de la validación: DRY RUN presentado y aprobado explícitamente por el operador (yep) antes de cada escritura, en turnos separados. Verificado py_compile + pytest tras cada fix, antes y después de aplicar en el Mac del operador.
---
> El histórico completo del CHANGELOG lo podrás encontrar en ARCHIVO CHANGELOG, en esta pagina de consulta continua solo encontrarás las últimas diez entradas para garantizar la operación y referencia del sistema.
Tipo: [CODE] [OPS] [DOC]
Alcance:
- [CODE]:
- Dual Backend en layer_3_mail.py: Implementado EXTRACTION_BACKEND (ollama | groq). Default cambiado a Ollama local (qwen2.5:3b). Groq (_call_groq) como fallback/alternativo intacto (validación de GROQ_API_KEY condicional al backend activo). GROQ_MODEL normalizado a openai/gpt-oss-20b como fuente única de verdad (líneas 36, 331, 817).
- Nuevo Guardrail is_url_valid(): Invocado en main() previo a creación en Notion. Descarta vacantes si la URL está vacía, mal formada o no es substring literal del cuerpo del correo (mitiga alucinaciones de modelos locales).
- Validation Check: Sintaxis de layer_3_mail.py validada (py_compile → SYNTAX OK).
- [OPS]:
- Evaluación E2E de LLMs locales: qwen2.5:0.5b descartado por alucinaciones en prompt/URLs. qwen2.5:3b validado como funcional junto a guardrails de Python.
- Test E2E de Guardrails: Confirmado is_vm_relevant() filtrando descarte por seniority (_TITLE_HARD_EXCLUSIONS) y marcas bloqueadas (_HARD_BLOCK_BRANDS). 3/3 casos de prueba integrales filtrados correctamente.
- Cero ejecuciones en prod: Pendiente corrida real contra inbox (python3 layer_3_mail.py) por cierre de sesión al límite de tokens (90%).
- [DOC]:
- Registro de Deuda Técnica y Gaps: (1) is_url_valid() sin validación de emparejamiento exacto rol-URL en correos multi-vacante. (2) Fallback local/rate-limit Groq pendiente de validación empírica real (vl3). (3) Decisiones pendientes en reasoning_effort ("low"), livelock de inbox y replicación de industrias L1→L3. (4) Reinyector de vacantes omitidas (Converse ×2, GOLDCO) pendiente. (5) OLLAMA_KEEP_ALIVE sin configurar por decisión explícita. (6) Alerta de credenciales en texto plano (layer_3.env) diferida por Mau.
- Estado Handoff HO-000058: Ledger status declarado UNKNOWN por ausencia de vantage-session-open en la sesión SESSION-20260916-1.
IDs afectados: Ninguno (código / refactor Layer 3; no dispara CENSUS-SYNC Regla 1).
Tipo: [FIX]
Documento modificado: Layer_1/scripts/layer_1_orchestrator.py (repo local, 2 hunks quirúrgicos vía str_replace)
Documentos potencialmente afectados: Ninguno en Kernel/Manual/SP/Canon — corrección de código puro, sin cambio de especificación normativa. class_b_guard.py verificado sin necesidad de cambio (Score_Method ya presente en CLASS_B_FIELDS desde antes).
Tipo de impacto: Operativo — cierre de HO-000056 (recibido de GROK-20260914-01), que reportaba Score/VM_Scope/Score_Method/Prioridad vacíos en Notion tras un --apply con 90 errores, más 144 registros duplicados en el tracker (resuelto por el operador vaciando el tracker antes de esta sesión, fuera de esta entrada).
Causa raíz (dos bugs distintos, ambos en layer_1_orchestrator.py):
1. Source_Type con espacio final (línea 1234): write_payload["Source_Type "] (con trailing space) no coincide con el nombre real de la propiedad en el schema del Tracker de Notion ("Source_Type", sin espacio — confirmado vía notion-fetch del data source). Cada PATCH que incluía este campo era rechazado con 400 Bad Request (Source_Type  is not a property that exists.) — arrastrando consigo, en el mismo payload, Score/VM_Scope/Prioridad/Gate_Decision. Root cause de los 90 errores originales reportados por GROK.
1. Aliasing de record como current en el diff (tras fix #1, con Errores: 0 pero campos aún vacíos): record (dict normalizado desde Notion en F0) se muta in-place durante F1.5 (VM_Scope, Role_Class), F3 (Score, Score_Method) y F3.6 (Prioridad), y ese mismo objeto mutado se pasaba como current=record a guarded_pages_update → compute_write_diff en las 3 llamadas del loop. El diff terminaba comparando el valor recién calculado contra sí mismo (60 == 60), nunca contra el valor real que Notion tenía al momento del F0 query — resultado: todo campo calculado por F1.5/F3/F3.6 se descartaba sistemáticamente como "sin cambio", sin excepción ni error visible. Gate_Decision/Next_Action/Last_Gate_Run sobrevivían porque apply_gate_decision() devuelve un dict separado, no muta record.
Acción correctiva ejecutada:
1. Línea 1234: write_payload["Source_Type "] → write_payload["Source_Type"] (patch quirúrgico con guardrail count==1, aplicado vía terminal por el operador, .bak generado).
1. Captura de record_original = dict(record) inmediatamente después de normalize_record(item), antes de cualquier mutación in-place — snapshot inmutable del estado real de Notion al momento del F0 query. Las 3 llamadas a guarded_pages_update (bloque NAD-expirado, bloque URL-Gate-archivado, bloque principal F3-F4) actualizadas de current=record a current=record_original (patch con guardrail count==3, .bak generado).
1. Diagnóstico verificado con evidencia dura en cada paso, no por inferencia de código: (a) traceback real capturado vía terminal del operador confirmando el mensaje exacto de la API de Notion para el bug #1; (b) fetch directo de un registro vía notion-fetch confirmando ausencia total de las 3 properties tras el primer --apply (post-fix #1, aún con bug #2); (c) logging de debug temporal (logger.info con record.get('Score')/'VM_Scope'/'Score_Method', removido tras uso) confirmando que F3 sí calculaba los valores en memoria correctamente, aislando el bug al diff; (d) --dry-run-live antes/después del fix #2 confirmando el cambio de keys=['Gate_Decision', 'Last_Gate_Run', 'Next_Action'] a keys=['Gate_Decision', 'Last_Gate_Run', 'Next_Action', 'Prioridad', 'Role_Class', 'Score', 'Score_Method', 'VM_Scope'].
IDs afectados: Ninguno (sin alta/baja de ID canónico — corrección de código, no de especificación normativa).
Estado final de la validación: Reingesta completa (24/24 registros, 0 fallidos) + --apply de cálculo (29 escrituras, 0 errores, 2 archivados, 5 flagged dedup) verificado con evidencia end-to-end: log de terminal del operador + fetch directo vía API de Notion + screenshot del Tracker con timestamp posterior a la corrida, confirmando Score/VM_Scope/Score_Method/Prioridad/Role_Class poblados correctamente en las 24 filas. Archivos .bak/.bak2/.bak3 (puntos de rollback intermedios) limpiados por el operador tras confirmar el estado final funcional. Sin DRY RUN de Changelog presentado ni aprobación por turno adicional, por instrucción explícita del operador (optimización de tokens, 00:36 CDMX) — version bump y esta entrada ejecutados en una sola pasada.
Handoff de referencia: HO-000056 (recibido de GROK-20260914-01 al inicio de sesión, cerrado con esta entrada).
---
Tipo: [CODE] [FIX]
Documento modificado: Layer_1/scripts/feed_processor.py (3 parches: jd_prop + write de JD, job_board en st_map, comentario Prioridad actualizado)
Documentos potencialmente afectados: Ninguno — código de Layer 1, sin escritura a Kernel/Manual/SP/Canon.
Tipo de impacto: Operativo — cierre de 3 deudas técnicas reportadas en HO-000054 (CLAUDE/MM): (1) JD nunca escrito a Notion, (2) source_type "job_board" sin mapeo, (3) comentario obsoleto sobre Prioridad.
Acción correctiva ejecutada:
1. Feed_processor.py — JD_write: agregado jd_prop en NotionSchema (resuelve propiedad "JD" de la DB) y write en build_notion_properties() con truncado explícito a 1990 chars (margen por discrepancia len() Python vs validación API de Notion). Resolvería 24/24 filas con JD en el reingreso.
1. Feed_processor.py — job_board mapping: agregado "job_board": "Agregador" en st_map de _resolve_fuente_from_source_type(). Resolvería 21/24 filas que venían con Fuente crudo.
1. Feed_processor.py — Prioridad doc drift: reemplazado comentario obsoleto (decía "vl1 backfill es responsable") por referencia correcta a layer_1_orchestrator.py F3.6 (infer_prioridad via priority_logic.py, se ejecuta en cada --apply).
1. Reingesta global v9.21.60: 24/24 registros creados con éxito (0 fallidos), seguida de vl1 apply (2 pasadas de idempotencia: 1ra=29 escrituras + 2 archivados + 5 flagged dedup; 2da=13 escrituras + 9 skips + 2 protegidas manuales + 2 sugerencias revisión, 0 errores).
Resultado:
- JD poblado en las 24 filas del Tracker (truncado a 1990 en casos >2000).
- Fuente canónica resuelta para los 21 registros job_board (antes "job_board" crudo).
- Class B calculada: Score, Prioridad, Gate_Decision, VM_Scope, Role_Class, Next_Action, Dedup_Flag, JD_Quality — todas pobladas (2da pasada del orquestador).
- Idempotencia verificada: 2da pasada idéntica a 1ra en resultado final, solo escrituras menores.
IDs afectados: Ninguno (código, no alta/baja de ID canónico).
Estado final de la validación: pytest 11/11 pasaron (feed_processor + notion). Sin DRY RUN presentado ni APROBAR_WRITE por turno adicional (operador autorizó directamente). 2026-09-14 19:40 CDMX.
---
Tipo: [FIX]
Documento modificado: Layer_1/scripts/layer_1_orchestrator.py (repo, un solo hunk — condición agregada al branch F4 de Last_Gate_Run).
Documentos potencialmente afectados: Ninguno en Notion — corrección de código puro sobre el fix P4 ya reflejado en v9.21.59 (KERNEL:SCHEMA-001 no requiere cambio, la clasificación Class B de Last_Gate_Run ya era correcta).
Tipo de impacto: Operativo — corrección de un bug real introducido por el propio fix P4 de v9.21.59, detectado con evidencia dura antes de tocar producción.
Causa raíz: La implementación original de P4 ataba el write de Last_Gate_Run a if gate_result.get("Gate_Decision"): — condición que es verdadera para casi cualquier fila no protegida en cada corrida (apply_gate_decision() siempre recalcula una decisión salvo PROTECTED/TERMINAL), no una señal de que el gate haya cambiado algo. compute_write_diff() filtra Gate_Decision del payload final cuando el valor no cambió, pero Last_Gate_Run (timestamp fresco cada corrida) nunca coincide con el valor ya guardado — sobrevive el diff siempre. Confirmado con --dry-run-live contra el Tracker real (24 filas): 22/24 proponían escritura de Last_Gate_Run sin ningún cambio real de Gate_Decision — la misma escritura amplificada en cada corrida que el audit E2E 2026-09-11 documentó como problema del script legacy, reintroducida por el propio fix pensado para evitarla.
Acción correctiva ejecutada: Condición adicional en el mismo branch — if gate_result["Gate_Decision"] != record.get("Gate_Decision"): antes de estampar Last_Gate_Run — de forma que el campo solo se toca cuando el Gate_Decision computado difiere del valor ya guardado en el record (transición real), no en cada corrida sobre cada fila no protegida.
IDs afectados: Ninguno.
Estado final de la validación: ast.parse OK. Verificado con --dry-run-live real (no sintético) en dos corridas comparables: antes del fix, 22/24 filas proponían Last_Gate_Run; después, 0/24 — mismo Tracker, mismo summary en el resto de métricas (24 procesadas, 2 protegidos manual, 2 sugerencias, 0 errores), sin regresión. Commit verificado en vivo contra origin/main (1db254d) — texto corregido presente carácter por carácter, sin mismatch. Sin DRY RUN de Changelog presentado ni aprobación por turno adicional, por instrucción explícita del operador (optimización de tokens, 18:27 CDMX) — version bump y esta entrada ejecutados en una sola pasada.
Handoff de referencia: continuación de HO-000052→HO-000053 (P4), corrige la implementación de v9.21.59 antes de que el handoff HO-000053 se emitiera formalmente.

---
Tipo: [FIX] [DOC]
Documento modificado: Layer_1/scripts/class_b_guard.py (repo, CLASS_A_FIELDS + CLASS_B_FIELDS) · Layer_1/scripts/layer_1_orchestrator.py (repo, F3.6 + F4) · V | KERNEL (§07.1 KERNEL:SCHEMA-001 — Match y JD_Quality agregados a Class B)
Documentos potencialmente afectados: Ninguno adicional — Manual/SP/Canon no referencian estos campos directamente.
Tipo de impacto: Normativo + Operativo — cierre de 4 de los 6 pendientes heredados de HO-000052 (verify_versions.py, P1, cerrado en esta misma sesión previo a esta entrada; P2 Prioridad, P3 Positioning_Mode/Match/JD_Quality/Last_Gate_Run).
Acción correctiva ejecutada:
1. P2 — layer_1_orchestrator.py (F3.6): infer_prioridad(item, ...) leía item["properties"]["Score"] sin actualizar tras el recálculo de F3 (record["Score"], no item) — Prioridad colapsaba a "2 MEDIO"/"1 BAJO" sin importar el Score real. Fix: item["properties"]["Score"] se parchea con el Score recién calculado justo antes de la llamada, sin tocar la firma de priority_logic.py (evita romper a backfill_class_a.py, que sí depende del shape crudo de item y no recalcula Score en su propia pasada). Validado con test funcional: Score=40 → "1 BAJO", Score=85 (mismo item) → "4 CRÍTICO".
1. P3a — Positioning_Mode: agregado a CLASS_A_FIELDS en class_b_guard.py. Kernel (SCHEMA-001) ya lo clasificaba Class A correctamente — el guard estaba desalineado, bloqueaba el PATCH completo del Dashboard (dashboard_notion.py::guard_write_payload) con CLASS_B_BLOCKED en cualquier intento de setearlo.
1. P3b — Match y JD_Quality: agregados a la lista Class B de KERNEL:SCHEMA-001 (Notion) para alinear con OWNERSHIP-002 (que ya listaba Match) y con class_b_guard.py (que ya listaba ambos en CLASS_B_FIELDS) — lapsus documental cerrado, sin cambio de código.
1. P3c/P4 — Last_Gate_Run reabierto: huérfano desde el refactor v9.0 (layer_1_orchestrator.py solo lo leía en manual_first_protection(), nunca lo escribía — el único write vivía en layer_1_run.py, archivado). Agregado a CLASS_B_FIELDS en class_b_guard.py + write en F4 (layer_1_orchestrator.py), atado deliberadamente al mismo branch que Gate_Decision (no a cada fila procesada) para no recrear el write amplification que el audit E2E 2026-09-11 documentó en la versión legacy (que stampeaba Last_Gate_Run=now en TODA fila no-skipeada, invalidando last_edited_time como señal de edición humana).
IDs afectados: Ninguno (extensión de listas existentes en class_b_guard.py; extensión de nodo existente KERNEL:SCHEMA-001, sin alta/baja de ID canónico — no dispara CENSUS-SYNC Regla 1).
Estado final de la validación: class_b_guard.py y layer_1_orchestrator.py verificados con ast.parse tras cada cambio + tests funcionales aislados (guard_write_payload/class_b_guard con payloads sintéticos) confirmando que Positioning_Mode/Last_Gate_Run ya no bloquean sus respectivas vías de escritura, sin afectar el bloqueo intacto para actores no-pipeline. KERNEL:SCHEMA-001 verificado por re-fetch en vivo post-escritura, texto verbatim confirmado. Fixes aplicados sobre un clon de origin/main en sandbox — NO sobre el working tree local real del operador, que además contiene un fix de Cursor sin commitear (to_notion_properties() en pages.update(), línea ~1176) y el fix de P2 ya aplicado a mano por el operador vía edit_block. Handoff HO-000053 (siguiente entrada) entrega diffs exactos para aplicación manual sobre el working tree real, sin clonar de cero. Sin DRY RUN presentado ni aprobación por turno adicional para este Changelog, por instrucción explícita del operador (optimización de tokens, 18:01 CDMX) — version bump y esta entrada ejecutados en una sola pasada.
Handoff de referencia: HO-000052 (recibido al inicio de sesión) · HO-000053 (emitido a continuación, para CLAUDE/MP).
---
Tipo: [DOC]
Documento modificado: V | KERNEL (§09.10 KERNEL:GATE-DECISION-010, §07.1 KERNEL:SCHEMA-001) · V | MANUAL (§22.1 MANUAL:SCRIPT-GLOSSARY-L1, entrada layer_1_run.py extendida con layer_1_orchestrator.py)
Documentos potencialmente afectados: Ninguno adicional — System Prompt/Career Canon no referencian estos tres nodos.
Tipo de impacto: Normativo — cierre de 3 de los 9 puntos de Fe de Erratas post-deploy G8/G9 (refactor v9.22.0, Layer_1), consolidados en mapeo de nodos por CLAUDE/MAIN (corrigiendo entrega previa incompleta de CLAUDE/KM en el Nodo 3).
Acción correctiva ejecutada:
1. KERNEL:GATE-DECISION-010 — agregada distinción entre bloqueo de escritura de Class B en el momento de ingesta (real, verificado por test_g8_matrix_live_statuses_protected) y protección persistente contra recálculo posterior (nunca existió — "Por Revisar" no formó parte de STATUS_TERMINAL_MAP ni TERMINAL_ACTIONS).
1. KERNEL:SCHEMA-001 — agregada línea junto a campos Class B: VM_Scope ∈ {Alto, Bajo}, binario, sin valor "Medio" en ningún punto del sistema.
1. MANUAL:SCRIPT-GLOSSARY-L1 — extendida entrada de layer_1_run.py (archivado) con layer_1_orchestrator.py (su reemplazo): documentadas las dos listas vm_terms independientes (línea 123 get_vm_scope vs línea 138 get_role_class, 7 vs 4 términos), alcance vigente ES+EN sin términos de escaparatismo (decisión explícita del operador, evidencia histórica de 8 filas "Escaparatista" documentada sin acción correctiva), y método de curación disponible a futuro no aplicado.
IDs afectados: Ninguno (extensión de nodos existentes, sin alta/baja de ID canónico — no dispara CENSUS-SYNC Regla 1).
Estado final de la validación: Write-Back Verification PASS — confirmado vía re-fetch en vivo de KERNEL post-escritura (Nodos 1 y 2 verbatim, sin mismatch); Manual escrito sin error reportado por la herramienta (mismo patrón y vía que los dos anteriores). APROBAR_WRITE del operador cubrió el lote de 3 nodos en un solo turno. Pendientes de la Fe de Erratas fuera de esta entrada: allowlist test_g3_parity.py (Q-11), suite completa de tests, confirmación de referencias residuales a Source_Type con espacio/"Medio".
---
Tipo: [CODE] [OPS] [DOC]
Alcance:
- [CODE]: suite tracker_flow 30→39 (T0: 6 tests F13/F13b + 3 minors one-shot, bb29edf; T4: fix TypeError choose_survivor capa string Q-H7 L1>L2>L3>N/A + 3 tests; G1 enum GateDecision alineado a vivo REVIEW_NEEDED/EXPIRED). Patch combinado 159 líneas.
Validación: pytest 39 passed reproducido por Arena; bug pre-fix confirmado con TypeError real; md5 base 6a41a7e0…/7e274a6d…. (Fix endpoint data_sources ya registrado en v9.21.56.)
- [OPS]: censo T1 (24 filas; Status 12/12=enum; Target=0; fantasmas=0; Q-H1 Fetch 22/2 resuelto; Next_Action vivo 11 vs enum 9 y Gate_Decision 2/6 registrados como deuda-doc, no bloqueantes) · backup T2 CSV sha256 7da5210c…eb071 24/24 · T5: one-shot --dry-run 0 filas + cross-check MCP n=0 → --apply no-op (tercera corroboración junto al dry-run operador de v9.21.56; Outcome 100% vacío). Cero escrituras a prod en el ciclo.
- [DOC]: actas handoffs/ seriales CLAUDE-20260911-01…06 (veredictos T0–T5, acta CIERRE, brief doc transversal, handoff T6 sidecar vl1s). Propuesta doc transversal pendiente de APROBAR_WRITE; T6 spec entregado (runner thin + case sync + alias, --apply excluido).
IDs afectados: Ninguno (código; no dispara CENSUS-SYNC Regla 1).
Tipo: [FIX] [DOC] [OPS]
Documento modificado: vantage-present-handoff/SKILL.md, vantage-session-open/SKILL.md, vantage-session-close/SKILL.md (repo GitHub, v1.0.0→v1.1.0→v1.2.0 en dos pasadas) · tracker_flow.py (repo, fix de bug real) · Tasks Tracker (Notion, 1 alta) · KERNEL:HANDOFF-SERIAL (Notion, pendiente de edición manual por el operador — markdown entregado, no aplicado por MCP en esta sesión).
Documentos potencialmente afectados: SP:SKILL-VERSION-PIN (tabla en v1.0.0 para los 3 skills de sesión, desalineada contra el repo tras este cambio — pendiente de sync, no ejecutado en esta sesión).
Tipo de impacto: Normativo + Operativo — cierre de una fricción de diseño real detectada esta sesión: instancias receptoras de handoff re-verificaban exhaustivamente estado ya reportado por el operador (incluyendo el propio serial del handoff), consumiendo tokens de forma desproporcionada sin mejorar la fiabilidad, dado que Mau es operador único y transportista único de todo handoff en el sistema.
Causa raíz: El diseño original de vantage-present-handoff/vantage-session-close no distinguía entre "estado no verificado" y "estado declarado por la única fuente de autoridad posible". Sin un campo de evidencia adjunta ni una regla explícita de adopción, cada instancia por defecto trataba todo como no verificado — incluyendo la resolución de serial, que en la práctica depende de vías (MCP allocate_vantage_serial, Terminal allocate_vantage_serial.py next) confirmadas no funcionales en esta sesión.
Acción correctiva ejecutada:
1. S4-EVIDENCE + Regla de Adopción (v1.1.0): los 3 skills de sesión (vantage-present-handoff, vantage-session-close — ambos con sección S4 — y bump de versión en vantage-session-open, que no emite S4) reciben una subsección S4-EVIDENCE obligatoria para afirmaciones verificables (comando exacto + output crudo, sin campo de timestamp propio — el orden queda implícito por ser Mau el único transportista de handoffs) y una Regla de Adopción: la instancia receptora de un handoff con S4-EVIDENCE completo adopta esa evidencia sin re-ejecutar verificación, salvo contradicción explícita del operador o inconsistencia interna de la evidencia misma.
1. Serial Authority v2 (v1.2.0, extensión del mismo patch): la ruta MCP/HTTP para resolución de serial se elimina del diseño (no se degrada a fallback — se retira por no ser funcional en la práctica operativa). vserial vía Terminal se conserva como la única vía canónica para obtener un serial nuevo. Nueva Prioridad 0: serial declarado directamente por el operador en el mismo turno, autoridad máxima, adoptado sin verificación adicional bajo ninguna circunstancia. Si el operador no declara uno, debe obtenerse mediante vserial vía Terminal; si esa ruta no está disponible, declarar HANDOFF_SERIAL_UNAVAILABLE y detener la emisión — nunca inventar ni interpolar por continuidad secuencial con el handoff anterior.
1. Fix real de bug en tracker_flow.py: run_outcome_status_sync() (F13b) llamaba a notion_client.databases.query() — endpoint inexistente en la versión instalada de notion-client contra API version 2025-09-03, donde ese método se movió a client.data_sources.query(). Confirmado mediante introspección directa del cliente (dir(client.databases) → sin query; dir(client.data_sources) → con query). Corregido cuerpo de la función y docstring (parámetro database_id debe recibir el DATA SOURCE ID 442938be-fc42-828f-b72e-076818d65a5b, no el DATABASE ID 596938be-fc42-836b-aea7-814a1491bd47 — no intercambiables). Verificado con py_compile tras el fix.
1. DRY RUN real ejecutado contra producción (Terminal, operador): script standalone reutilizando normalize_record() de tracker_flow.py sobre las 24 filas del Tracker vía data_sources.query() — checked=24, would_sync=0, skipped=24, sin invocar apply_status_sync_writeback en ningún momento. Consistente con verificación independiente previa (sync_status_contratado.py, mismo resultado: 0 filas con Outcome=Contratado pendientes de reconciliar — el campo Outcome simplemente no está poblado en ninguna fila real hoy, no es un bug de query).
1. Investigación de campo Holding: snapshot previo (HO-000042) reportaba 13 filas pendientes de limpieza; verificación directa contra Notion (24 filas totales) encontró 16 filas con Holding no vacío: 13 = Investigar (placeholder), 1 = Genérico (placeholder distinto, tratamiento sin confirmar), 2 = datos reales de holding corporativo (Nike Inc., LVMH) que NO deben tratarse como placeholder. Task creado en Tasks Tracker (3d8938be-fc42-81dc-8ada-c7afec89bec9) documentando el desglose completo y bloqueando ejecución de limpieza hasta que el operador confirme criterio de tratamiento para cada categoría.
1. Verificación de integridad post-migración de schema Status (heredado de HO-000042, cerrado esta sesión con evidencia real): query directa de las 24 filas del Tracker confirmó 0 filas con Status vacío/huérfano tras el rename de opciones (Target→Objetivo, REVIEW_NEEDED→Por Revisar, etc.) — sin pérdida de datos.
IDs afectados: Alta de 1 registro operativo (Tasks Tracker, Holding). Ninguna alta/baja de ID canónico en Kernel/Manual/SP/Canon en esta pasada — el cambio de KERNEL:HANDOFF-SERIAL (Notion) queda como edición manual pendiente del operador, markdown ya entregado en sesión, no ejecutado vía MCP.
Estado final de la validación: Fix de tracker_flow.py verificado con py_compile + DRY RUN real contra Notion producción (evidencia cruda capturada). Patch de los 3 skills de sesión verificado vía git diff en cada pasada, commit confirmado por el operador (vgit, no re-verificado con git log en esta sesión — adoptado por declaración directa del operador bajo la nueva Regla de Adopción que este mismo changelog documenta). Pendiente explícito: sync de SP:SKILL-VERSION-PIN (Notion) a v1.2.0 para los 3 skills de sesión, y aplicación manual del markdown de KERNEL:HANDOFF-SERIAL v2 por el operador. Sin DRY RUN de Changelog presentado ni aprobación por turno adicional, por instrucción explícita del operador (optimización de tokens) — version bump y esta entrada ejecutados en una sola pasada.
---
Tipo: [OPS] [SYNC]
Alcance: script_hash_baseline.json (8 hashes), skill_hash_baseline.json (5 hashes), bodies Notion de vantage-present-handoff / vantage-session-open / vantage-session-close; Script Library + Skill Library altas previas de assets sync.
Contexto: Cierre de content-drift detectado vs baselines locales. Bodies de session skills alineados a disco (v1.1.0 S4-EVIDENCE + Regla de Adopción). Baselines de hash actualizados en clone local (requiere commit/push del operador para persistir en repo remoto).
Cambios:
1. Script content-drift cerrado: allocate_vantage_serial.py, feed_processor.py, layer_1_run.py, layer_3_mail.py, mcp_vantage_serial_server.py, open-figma-template.sh, profile_evolution.py, verify_versions.py.
1. Skill content-drift cerrado en baseline: vantage-cv-a, vantage-cv-b, present-handoff, session-close, session-open (bodies Notion actualizados para las 3 session skills).
1. Version bump CHANGELOG → v9.21.55.
Pendientes: commit/push baselines en repo; bodies completos de vantage-cv-a/cv-b en Notion (archivos >10k, omitidos por tamaño en esta pasada MCP); 10 scripts missing-on-disk del baseline histórico (legacy) sin acción.
IDs afectados: Ninguno.
Estado: APLICADO — baselines locales + bodies session skills + propiedad Versión CHANGELOG.
---
Tipo: [REVERT] [CODE]
Alcance: layer_3_mail.py, layer_3.env
Contexto:
- Revert intencional de la migración v9.21.52 (Groq → Gemini): retorno a Groq como proveedor de LLM.
- Razón del revert: Inestabilidad y errores de esquema/deprecación en el endpoint de Gemini. Se migró a Groq aprovechando el modelo qwen/qwen3.8-27b para garantizar JSON estructurado estricto.
Cambios observados:
1. Variables de configuración restablecidas a nomenclatura GROQ_* (GROQ_API_KEY, GROQ_MODEL, GROQ_MIN_DELAY_SEC).
1. Actualización de modelo activo a qwen/qwen3.8-27b y ajuste del delay entre peticiones a 5.0s para evitar el rate limit por Tokens Per Minute (TPM).
1. Implementación de sanitización ASCII en el cuerpo del correo previo al payload JSON para eliminar errores 400 Bad Request por caracteres de control.
Estado: APLICADO Y VALIDADO EN PRODUCCIÓN — Pipeline ejecutado con éxito en la rama main (🏁 VL3 terminó — no quedan correos pendientes), procesando y deduplicando alertas de empleo en Notion sin errores de red o sintaxis.
IDs afectados: Ninguno (refactor de código de backend/pipeline).
Pendientes:
- Ejecutar commit y push a GitHub (vgit) para sincronizar el estado local verificado con el repositorio remoto.
---
Tipo: [OPS]
Documento modificado: Ninguno en Notion — auditoría de 15 PDFs finales del batch (Beyond, Confidencial GVM, Confidencial Gte.Nacional VM, Eurokor, GDC Inmobiliaria, H&M Junior Retail Designer, IKEA, Inditex, Intimissimi, Juguetron, SARELLY, ServiciosAndrei/Moygo, Tendam, Walmart, ZaraHome).
Documentos potencialmente afectados: Ninguno — trabajo de auditoría de entregables, no de especificación normativa.
Tipo de impacto: Operativo — checklist canónico de 7 ítems (vantage-qa v9.17.0) corrido sobre los 15 PDFs sin HANDOFF de CV-A disponible para ninguno (Ítem 3 = N/A en los 15). Ítem 7 (Anti-cloning) evaluado por comparación cruzada entre los 15 archivos del batch.
Acción ejecutada:
1. Verificación de orden cronológico C01→C05 intacto en los 15.
1. Hard Blocks confirmados PASS en los 15 — L'Oréal/Levi's/Palacio de Hierro presentes solo como historial (C01/C03/C05), ninguna vacante target pertenece a esas marcas.
1. Certificaciones (CERT01/CERT02) y email canónico verificados sin desviación en los 15.
1. Métricas (+43%/+18%/-74%/-33%/17 punch-list/21 reportes/270+ PDV/6 países) verificadas sin inflación ni redondeo.
1. Sin [PENDING DATA] visible en ningún PDF.
1. Anti-cloning: pares con headers de título similares (Beyond/GDC; IKEA/Juguetron) verificados con bullets de Experience reescritos con ángulo distinto — ningún par supera 80% de coincidencia verbatim.
IDs afectados: Ninguno (auditoría de contenido, sin alta/baja de ID canónico).
Estado final de la validación: 15/15 PDFs con veredicto GO. Corrección de conteo aplicada en la misma sesión (reporte inicial erróneo de "14/14" corregido a 15/15 tras verificación directa del conteo de archivos). Sin DRY RUN presentado ni aprobación por turno adicional, por instrucción explícita del operador (optimización de tokens) — version bump y esta entrada ejecutados en una sola pasada.
---
Tipo: [MIGRATION] [CODE]
Alcance: layer_3_mail.py (migración completa Groq → Gemini) + layer_3.env
Contexto:
- Problema de backoff exponencial (12s → 1,217s) en retries de Groq, causando tiempos de espera no viables.
- Cuota insuficiente de Groq incluso tras implementar pre-filtrado y backoff cap.
- Investigación de proveedores alternativos determinó que Gemini Flash-Lite ofrece mejor free tier (15-30 RPM vs ~10 RPM de Groq) y OpenAI-compatibility.
Cambios ejecutados:
1. Migración de proveedor: Reemplazo completo de cliente Groq por cliente Gemini:
- extract_jobs_with_groq() → extract_jobs_with_gemini()
- _groq_throttle() → _gemini_throttle()
- _groq_wait_seconds() → _gemini_wait_seconds()
- GroqFatalError → GeminiFatalError
- Endpoint: https://api.groq.com/openai/v1/chat/completions → https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
- Payload format: OpenAI-style → Gemini native (contents/generationConfig)
1. Configuración renombrada (layer_3.env):
- GROQ_API_KEY → GEMINI_API_KEY (usando key existente en .env principal)
- GROQ_MODEL → GEMINI_MODEL (gemini-3.5-flash-lite)
- GROQ_MIN_DELAY_SEC → GEMINI_MIN_DELAY_SEC (8s, reducido de 12s)
- GROQ_MAX_RETRIES → GEMINI_MAX_RETRIES (3)
- GROQ_MAX_BACKOFF_SEC → GEMINI_MAX_BACKOFF_SEC (20s, reducido de 30s)
- GROQ_MAX_EMAILS_PER_RUN → GEMINI_MAX_EMAILS_PER_RUN (5)
- GROQ_BODY_MAX_CHARS → GEMINI_BODY_MAX_CHARS
1. Pre-filtrado preservado: Función should_skip_groq() → should_skip_gemini() mantiene lógica de filtrado de correos sin indicadores de vacante.
1. VM keywords preservadas: _VM_KEYWORDS expandido con equivalentes españoles (exhibición visual, escaparatismo, coordinador visual, etc.) implementados en sesión previa.
Validación:
- Pipeline ejecutado sin intervención manual en correos de prueba.
- Sin rate limits observados con Gemini (vs persistentes con Groq).
- Latencia mejorada: 8s delay vs 12s anterior.
- Modelo gemini-3.5-flash-lite estable y disponible.
Pendientes post-escritura:
- Ejecutar vversions --sync para propagar cambios a documentos fundacionales.
- Monitorear cuota de Gemini (usos/hora) tras despliegue.
- Considerar backup provider (DeepSeek) como fallback si se requiere mayor throughput.
IDs afectados: Ninguno (migración de proveedor sin alta/baja de ID canónico — no dispara KERNEL:CENSUS-SYNC Regla 1).
---
---
> El histórico completo del CHANGELOG lo podrás encontrar en ARCHIVO CHANGELOG, en esta pagina de consulta continua solo encontrarás las últimas diez entradas para garantizar la operación y referencia del sistema.
