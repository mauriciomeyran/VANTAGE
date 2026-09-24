# V | CHANGELOG

Fecha: 24-Sep-2026 · 12:19 CDMX (VERIFICADO)
Estado: PASS / CANON ACTUALIZADO
Scope: V | CAREER CANON (377938befc42808993f2f52dbd2dec6c) · Secciones 07 y 12.4
Cambios
- 12.4 CANON:OUTPUT-CONTRACT-004 — INSERT labels de contacto: 8:62 = "LinkedIn", 8:63 = " | Portafolio". El hipervínculo se aplica en Figma, no en el .md.
- 12.4 CANON:OUTPUT-CONTRACT-004 — INSERT regla de labels: nodo solo-etiqueta con hipervínculo en Figma → el .md lleva el label literal, NUNCA la URL cruda.
- 07.12 CANON:UF-004 — INSERT Contact Block: Ubicación Miguel Hidalgo, CDMX · Teléfono +52 56 4383 8125 · Email mauricio.meyran@icloud.com (UF02).
- 07.13 CANON:UF-005 — INSERT LinkedIn URL = https://www.linkedin.com/in/mauriciomeyran.
- 07.14 CANON:UF-006 — INSERT Portfolio URLs = https://mmeyranesp.myportfolio.com (CV ES) · https://mmeyraneng.myportfolio.com (CV EN). Confirmado por operador en sesión.
NO-OP
- 03.1 CANON:EXPERIENCE-001 (C01 rol): sin cambio — el CV-B de referencia trunca el título; el Canon es correcto. Discrepancia documentada.
Identidad: agent.family=MISTRAL · agent.instance=DEFAULT
Fecha: 24-Sep-2026 · 07:05 CDMX
Estado: PASS / DOCUMENTACIÓN ACTUALIZADA
Scope: Runtime VANTAGE · vload · lazy_loader · Entity Index · Resolver · Query · Context · Agent API · Health Check · Graph SUSPENDED
Cambios documentales
- KERNEL:DOCUMENTATION-003 actualizado para separar explícitamente la ruta documental PREFIX:CLAVE → vload → document_registry → Notion de la ruta de entidades Entity Index → Resolver → Notion.
- KERNEL:DOCUMENTATION-003 actualizado para reflejar vload.py como interfaz documental preferente y lazy_loader.py como implementación interna.
- KERNEL:DOCUMENTATION-003 actualizado con vantage.py, last_sync_result.json y el estado arquitectónico Graph SUSPENDED.
- KERNEL:DOCUMENTATION-006 armonizado con el Health Check y el auto-sync condicional del Entity Index.
- MANUAL:RUNTIME-001 armonizado para documentar las dos rutas del Runtime.
- MANUAL:RUNTIME-002 armonizado para separar comandos documentales y operaciones de entidades.
- MANUAL:RUNTIME-003 armonizado con el comportamiento actual de sync, status y last_sync_result.
- MANUAL:RUNTIME-004 armonizado con el estado actual de Entity Index, Graph y Backlinks.
- ALIASES:L0-RUNTIME corregido para reflejar vload.py como interfaz documental y vantage.py como Runtime operacional.
IDs
No se crearon ni eliminaron IDs canónicos. CENSUS-SYNC-R1 no se dispara.
Validación
La documentación se alineó con la validación E2E registrada en v9.22.12: vload 20/20, health_check 14/14, graph 16/16, sync 729→729, hash 100%, orphan candidates 0.
Fecha: 24-Sep-2026 · 06:38 CDMX
Estado: PASS / CERRADO
Scope: Runtime VANTAGE · Lazy Loader · vload · Resolver · Context · Query · Agent API · Health Check
### Validación E2E
Se completó la validación funcional del Runtime/Lazy Loader contra HEAD actual, incluyendo rutas documentales, resolución de entidades, capas operativas y suites de regresión.
Documentary path
- vload --route KERNEL:SCHEMA → PASS
- vload --route MANUAL:RUNTIME-002 → PASS
- vload --list → PASS
- Registry operativo: 11 prefijos disponibles
- Resolución automática de UUID → PASS
P4 — vload regression suite
- tests/test_vload.py localizado en VANTAGE/tests/test_vload.py
- Resultado: 20/20 PASS
- Tiempo: 0.12 s
Health Check
- Corrección aplicada en scripts/health_check.py para normalizar el texto sin corrupción detectada.
- tests/test_health_check.py
- Resultado: 14/14 PASS
- Tiempo: 0.11 s
- El fallo previo era exclusivamente un mismatch de texto entre implementación y expectativa del test.
Graph / Runtime validation
- tests/test_graph_layer.py
- Resultado: 16/16 PASS
- Graph validation permanece SUSPENDED conforme a la decisión arquitectónica vigente: VANTAGE utiliza movimiento mutuamente excluyente TRACKER ↔ ARCHIVO_TRACKER y no relaciones de grafo para archivado.
Resolver / Context / Query / Agent API
- Entity Index → Resolver → Notion → PASS
- resolve TRACKER:* → PASS
- context TRACKER:* → PASS
- ask "show active roles" → PASS
- ask "compare ..." → PASS
### Reconciliación de Entity Index
Se ejecutó python3 scripts/vantage.py sync para resolver la discrepancia observada entre el índice actual y el último resultado histórico de sync.
Resultado:
- entities_before: 729
- entities_after: 729
- Tracker: 36
- ARCHIVO_TRACKER: 693
- Total: 729
- Hash coverage: 100%
- Orphan candidates: 0
- Index age posterior al sync: 0.0 h
- last_sync_result.status: ok
- Graph edges: 0
- Backlinks: 0
La discrepancia previa 863 → 729 queda reconciliada mediante un sync actual exitoso que confirma estabilidad del índice en 729 entidades.
### Resultado final
Runtime / Lazy Loader E2E → PASS
No quedan hallazgos funcionales abiertos dentro del scope auditado.
Evidencia final:
vload 20/20 · health_check 14/14 · graph 16/16 · sync 729→729 · hash 100% · orphans 0
Tipo: [OPS] [DOC] [CODE]
Identidad VANTAGE: agent.family=CLAUDE · agent.instance=KM (P-E, triage) + agent.family=CLAUDE · agent.instance=MAIN (P-C/P-D, HO-000065) + agent.family=GEMINI · agent.instance=GEMINI-2.5-PRO (HO-000065, autor del script).
Documentos modificados: V | SYSTEM PROMPT (§04 SP:CONTEXT-INFRASTRUCTURE) · V | MANUAL (§06 MANUAL:SESSION-CYCLE) · Layer_1/scripts/purge_archivo_duplicates.py · Layer_1/data/entity_index_v2.json · Layer_1/data/graph_v2.json · Layer_1/data/backlinks_v2.json
Documentos pendientes de commit: ninguno — Documentación/ACTIVE/Aliases.md y Brief.md confirmados comiteados en origin/main (commit dcd21d3, verificado por CLAUDE/MP vía git pull independiente el mismo día).
Tipo de impacto: Operativo + Documental + Correctivo.
HO-000064 — cierre de contenido (P-C/P-D/P-E), posterior a la sesión GROK/DEFAULT (ver v9.22.10, anterior en el tiempo pese al número de versión menor — GROK trabajó primero, encontró las páginas de Tracker ya en la papelera, y por eso reportó P-C/D/E como "canceladas". Esta sesión completó el contenido real contra los documentos vivos):
1. P-C — SP:CONTEXT-INFRASTRUCTURE (§04): reemplazada la línea genérica 'Terminal (lazy_loader.py): Ruta preferente...' con: (a) mención explícita de vload como comando preferente para fetches documentales, con lazy_loader.py como base interna; (b) tabla de 2 filas: DOCUMENTOS (Kernel/Manual/SP/Canon) → vload --route PREFIX:CLAVE | ENTIDADES (Tracker/bugs/vacantes) → vantage.py ask/query/resolve. Cierra Riesgo 2 del análisis de adopción (SESSION-20260921-KM3). Página de Tracker encontrada en papelera (trastada por MAIN por links rotos del handoff HO-000064) — trabajo aplicado en Notion vivo confirmado. Verificado independientemente por CLAUDE/MP vía notion-fetch en vivo el mismo día: texto presente byte-exacto.
1. P-D — MANUAL:SESSION-CYCLE (§06): nota aclaratoria: Fail-Fast aplica únicamente a escrituras documentales y a emisión de seriales de handoff (vserial) — no a operaciones de solo lectura, análisis o revisión de código. Confirmado en Notion vivo. Cierra Riesgo 3. Verificado independientemente por CLAUDE/MP el mismo día.
1. P-E — Triage de 216 candidatos de validate_governance.py --check refs contra Notion vivo. Resultado: 0 referencias realmente muertas. Desglose: 167 KERNEL/MANUAL/SP vivos en mirrors locales (el scanner no detecta headings con esa sintaxis); 8 ALIASES vivos en V|ALIASES Notion (01-08 confirmados vía notion-fetch); 48 BRIEF vivos en V|BRIEF Notion (01-11 y todos los sub-IDs confirmados); 1 SP:DIGITAL-ID-CARD-001 vivo como fila de tabla. Diagnóstico raíz: ALIASES y BRIEF no tenían mirror .md en Documentación/ACTIVE/. Fix: stubs generados (Aliases.md 25 líneas, Brief.md 42 líneas), comiteados a origin/main. Cierra Riesgo 4.
Nota infraestructura: páginas Tracker de P-C, P-D y P-E encontradas en la papelera — las trastó CLAUDE/MAIN al no poder fetchearlas por links rotos en el handoff HO-000064. Trabajo aplicado confirmado en documentos vivos; solo el tracking operativo se perdió. No se restauran: esta entrada es el registro oficial.
HO-000065 — GEMINI/GEMINI-2.5-PRO (purga de duplicados ARCHIVO_TRACKER):
1. purge_archivo_duplicates.py: nuevo script de Gemini para purgar duplicados en ARCHIVO_TRACKER. Bug original: usaba client.request() y client.pages.update(archived=True) — métodos inexistentes en el SDK custom de VANTAGE. Fix por CLAUDE/MAIN: reemplazado por _notion_patch(f'/v1/pages/{page_id}', {'archived': True}), la función HTTP real de bajo nivel con auth, headers, throttle y versión correcta. Verificado contra un solo registro antes del apply masivo.
1. Purga aplicada: 134/134 duplicados archivados en ARCHIVO_TRACKER. 827 → 693 registros. 600 hashes únicos mantenidos.
1. generate_entity_index_v2.py re-ejecutado vía ../.venv/bin/python3: 729 entidades (Tracker 36 + Archivo 693), hash coverage 100%, 0 orphan candidates, Graph SUSPENDED confirmado. Artefactos entity_index_v2.json/graph_v2.json/backlinks_v2.json regenerados y comiteados (commit 47ab17c). Entity index ahora usa clave 'metrics' correctamente.
Bug Tracker RT-1: este episodio suma como tercer caso del patrón de reporte optimista (Gemini reportó 'fix aplicado' con bugs de sintaxis aún presentes). Umbral 3er episodio alcanzado: Next_Action RT-1 debe escalar de Monitorear a Patch.
Ver también: entrada anterior [v9.22.10 — GROK/DEFAULT, cierre operativo de HO-000064 P-A/P-B + MIRROR-TRIGGER], trabajo de otra sesión sobre el mismo contrato, ejecutado antes que este.
IDs afectados: Ninguno (no dispara CENSUS-SYNC Regla 1).
Estado: P-C/P-D aplicados en Notion vivo (verificados dos veces, por KM y por CLAUDE/MP independientemente). P-E triage completado (0 muertas). HO-000065 en origin/main (commit 47ab17c). Stubs comiteados (verificado). RT-1 aún Abierto/Monitorear en Bug Tracker — pendiente de escalar a Patch (ver ticket).
Tipo: [CODE] [OPS] [DOC]
Identidad VANTAGE: agent.family=GROK · agent.instance=DEFAULT. Agente de código: DEVIN (parcial, agotó tokens).
Documentos / artefactos modificados:
- Layer_4/scripts/trigger_sync_after_mcp_write.py (no-bloqueante + 8 docs fundacionales)
- Layer_4/scripts/MCP_SYNC_HOOK_README.md (actualizado a 8 docs + estado actual)
- validate_governance.py --check refs (exclusión de /Archive/ ya aplicada por Devin)
- VANTAGE AUDIT TRACKER (página madre reordenada y limpiada de texto histórico parchado)
- P-A y P-B (páginas de item) → Cerrado
- RT-1 (Bug Tracker) → notas actualizadas, permanece en Monitorear
Tipo de impacto: Cierre de contrato + endurecimiento operativo + higiene documental.
Nota de contexto (agregada en el split de esta entrada): esta sesión (GROK/DEFAULT) encontró las páginas de Tracker de P-C/P-D/P-E ya en la papelera al momento de escribir — de ahí que reporte "canceladas / nunca iniciadas" abajo. Trabajo posterior de otra sesión (KM/MAIN/GEMINI, ver entrada v9.22.11, posterior en el tiempo) sí completó P-C/P-D/P-E contra los documentos vivos, verificado independientemente por CLAUDE/MP. Las dos entradas describen agentes y alcance distintos sobre el mismo contrato HO-000064, no una contradicción real.
Alcance de esta sesión:
1. P-A cerrado — sync() escribe last_sync_result.json + status() lo incluye. Verificación byte-exacta previa confirmada. Status → Cerrado.
1. P-B cerrado — skill vantage-session-open con warning de staleness. Sincronizado también a Notion Skill Library (v1.2.0) + tabla SP:SKILL-VERSION-PIN actualizada.
1. MIRROR-TRIGGER cerrado pragmáticamente — commit 405ef8f endurece el trigger (Popen no-bloqueante, Brief + Changelog Archivo añadidos). Limitación del MCP server (fuera del repo) aceptada: invocación manual vía mcp_sync_wrapper.sh <page_id>. notion_write_wrapper.py queda como experimental/stub.
1. -check refs — Devin ya excluyó /Archive/ del alcance. Triage de 224 candidatos: cero referencias muertas reales que ameriten limpieza hoy (nota: cifra de 224 reportada por esta sesión difiere de los 216 de la entrada v9.22.11 — ambas dentro del rango de drift normal entre corridas, no reconciliadas).
1. Audit Tracker — página madre reescrita: estado actual consolidado, reglas operativas vigentes, resumen de cierre HO-000062 + HO-000064. Texto histórico parchado eliminado.
1. RT-1 — notas actualizadas; Next_Action sigue = Monitorear (umbral 3er episodio para Patch) — nota: entrada v9.22.11 declara el umbral ya cumplido por el episodio de Gemini/HO-000065; RT-1 en Notion vivo sigue en Monitorear al día de hoy — pendiente real, ver mensaje de CLAUDE/MP en sesión.
P-C / P-D / P-E del contrato HO-000064: reportados por esta sesión como páginas canceladas / en papelera (nunca iniciadas) — ver nota de contexto arriba: trabajo real de contenido sí se completó por otra sesión el mismo día.
Estado de verificación: origin/main contiene 405ef8f y a64cf56 (exclusión /Archive/). Tracker sin items abiertos (P-A/P-B).
IDs afectados: ninguno en canon/documentación fundacional que dispare CENSUS-SYNC Regla 1.
Estado: WRITE aplicado en Notion (Audit Tracker + Changelog + versión). Código ya en origin/main.
Tipo: [CODE] [OPS] [DOC]
Identidad VANTAGE: agent.family=CLAUDE · agent.instance=KM. Agente de código: DEVIN (2 instancias: local→repo-only).
Documentos modificados: Layer_1/scripts/resolver_layer_v1.py · notion_utils.py · verify_versions.py · clean_script_library_links.py · agent_api.py · lazy_loader.py · generate_entity_index_v2.py · graph_layer.py · status_report.py · generate_census.py · health_check.py · normalize_heading_ids.py · generate_entity_index_v2.py · context_layer.py · Layer_3/scripts/layer_3_mail.py · Layer_1/scripts/vload.py (nuevo) · tools/validate_governance.py (nuevo) · Documentación/ACTIVE/Manual.md · .gitignore · handoffs/AUDITORIA_L0_RUNTIME_LAZYLOADER_2026-09-22.md (nuevo) · VANTAGE AUDIT TRACKER (Notion, 11 páginas de items + 1 página de handoff HO-000001 + 1 página HO-000064)
Documentos potencialmente afectados: SP:CONTEXT-INFRASTRUCTURE (pendiente — P-C del contrato HO-000064) · MANUAL:SESSION-CYCLE (pendiente — P-D del contrato HO-000064)
Tipo de impacto: Correctivo + Arquitectónico + Operativo + Documental.
Alcance — items cerrados bajo HO-000062:
1. P1 — Resolver v3: resolve_entity() usa GET /v1/pages/{page_id} vía notion_utils (cache/throttle/retry); _query_notion() deprecado explícitamente (raise ResolverError) en vez de dead code silencioso; load_index() con dict O(1) en memoria. Cierra F8/§1.2.
1. P3 — Versión API única: notion_utils.notion_version() con default 2025-09-03 (antes 2022-06-28); verifyversions.py y clean_script_library_links.py enrutados a notion_utils._notion_version() con fallback consistente — eliminados los 2 hardcodes activos. 2 pasadas (primera pasada incompleta, segunda aprobada). Cierra F1/F5/F7/F12.
1. P5 — Saneamiento documental (ejecutado directamente por Claude/KM vía MCP Notion): F16 (SP:BOOTSTRAP-001→SP:BOOTLOADER), F17 (3 fixes en Manual), F15 (creación KERNEL:DOC-CONTRACT §03.18), tabla única de triaje MCP-lectura, corrección vcontext en Aliases. F19 (Hermes) resultó falso positivo — ya registrado en Notion vivo; mirror .md desactualizado.
1. P6 — Payload budgets: _handle_show_roles / _handle_show_archived_history / _handle_show_bugs con flag full=False y agregados top-25 por defecto. Cierra §3.3.
1. P8 — Higiene del repo: Scout eliminado del árbol, .m4a de 40MB removido, config/layer_2.env.example removido, raíz limpia. DESVIACIÓN DOCUMENTADA: infra de seriales MCP (mcp_vantage_serial_server.py, tools/claude-desktop-mcp-extension/) eliminada por Devin sin decisión explícita previa — mandato pedía solo reportarla. Resultado técnico aprobado, desviación de protocolo registrada en Notas de Cierre de P8.
1. P2 — Cerrado como no aplicable: una fila archivada en VANTAGE es la misma fila movida de TRACKER a ARCHIVO TRACKER (mutuamente excluyentes, nunca coexisten). No existe ni puede existir archived_from como arista — verificado contra schema real de ARCHIVO TRACKER vía notion-fetch (solo 'hash' y 'Page ID', sin propiedad de origen). Decisión de producto documentada, no un bug pendiente.
1. P2b — Grafo SUSPENDED: build_graph() retorna {status: SUSPENDED, reason: ...}; graph_layer.py loggea warning y propaga estado suspendido; validate_graph_artifacts() pasa explícitamente reconociendo SUSPENDED; status_report.py y agent_api.py reportan el estado en vez de aparentar datos vacíos; Manual.md documentado (22.1b, 9.4). Cierra F2 de raíz.
1. P4 — vload.py (nuevo): resolución automática de UUID desde document_registry de resolver_registry_v2.json — el agente ya no necesita conocer el UUID de memoria para hacer fetches documentales. 20/20 tests en tests/test_vload.py. 4 commits individuales [HO-000062][P4]. Cierra §2.4/§1.1.
1. P7 — validate_governance.py (nuevo en tools/): lint de gobernanza en Terminal (~0 tokens). Modo default: json (duplicados en registry) + parity (huérfanos triggers↔skills) — pueden fallar el lint. Modo --check refs: opt-in explícito, disclaimer de mirror-only, no bloqueante, 223 candidatos como insumo de triage manual. Incidente de fuente documental: Devin #2 leyó AUDITORIA_TRACKER_E2E_2026-09-11.md (documento incorrecto de otro subsistema) en vez del audit L0 correcto — se detuvo por su cuenta al detectar la incongruencia; el documento correcto se subió al repo vía git apply + commit manual del operador antes de continuar. 4 commits individuales [HO-000062][P7]. Cierra §3.2.
Padrón de deuda técnica documentado — Bug Tracker ticket abierto:
- Ticket RT-1 ALTO «Devin narra push/commit que no ocurrió» (2 episodios: P3 primera pasada y P7): Notion Devin narra push/commit que no ocurrió — reporte optimista recurrente. Mitigación vigente: Claude/KM verifica siempre contra repo real (git clone/pull + grep), nunca contra reporte narrado. Umbral tercer episodio → escalar de Monitorear a Patch.
Análisis de adopción punta a punta (Runtime/Lazy Loader):
Realizado post-cierre de HO-000062. Fuentes: vantage.py, lazy_loader.py, vload.py, agent_api.py, resolver_layer_v1.py, graph_layer.py, health_check.py, System Prompt, Kernel, Manual. 5 riesgos y 2 fricciones estructurales identificadas. Fixes de mayor ROI: (1) documentar vload en SP:CONTEXT-INFRASTRUCTURE, (2) tabla 2 filas documental vs. operacional en el mismo nodo — cero código nuevo. Nuevo contrato HO-000064 emitido con items P-A a P-E.
Contrato HO-000064 abierto (pendiente de ejecución en próxima sesión):
- P-A (DEVIN): sync() escribe last_sync_result.json + status() lo incluye
- P-B (DEVIN): vantage-session-open inyecta warning si entity_index_stale
- P-C (CLAUDE/KM): SP:CONTEXT-INFRASTRUCTURE — documentar vload + tabla documental vs. operacional
- P-D (CLAUDE/KM): MANUAL:SESSION-CYCLE — aclarar Fail-Fast aplica solo a escrituras y seriales
- P-E (CLAUDE/KM): triage de 223 candidatos --check refs contra Notion vivo
Estado de verificación: origin/main verificado en b024457 desde clon independiente. VANTAGE AUDIT TRACKER: 9 items Aprobados/Cerrado, 0 abiertos para HO-000062. Handoffs emitidos: HO-000001 x2 (cierre HO-000062 y HO-000063 — contador reiniciado en esa sesión), HO-000064 (contrato nuevo). Nota: GLOBAL_VANTAGE_COUNTER reiniciado produjo dos HO-000001 en el mismo ciclo — próximo serial canónico es HO-000065.
IDs afectados: Ninguno en canon/documentación fundacional (correcciones de código, herramientas nuevas, y páginas operativas en VANTAGE AUDIT TRACKER — no dispara CENSUS-SYNC Regla 1).
Estado: WRITE aplicado en repo (commits verificados vía git pull/clone desde sandbox) y en Notion (VANTAGE AUDIT TRACKER, Bug Tracker). P-C y P-D (cambios documentales en SP y Manual) pendientes de ejecución en próxima sesión bajo HO-000064.
BASELINE Tag Registry verificado contra Figma real (67/67 nodos) {toggle="true"}
Corrige: posición de barra en Rol/Período (vivía en ambos nodos → duplicaba o heredaba bold), footer nunca en .md de Figma (bug blockRegex/EOF), prohibición de nodos vacíos/[PENDING DATA] en entrega final, teléfono sin "1" post-52, "ALDO GROUP"→"ALDO" pin ejecutado, Idiomas en prosa con "e", Tagline 2:5 sin duplicar Contacto.
Tipo: [FIX] [DOC]
Identidad VANTAGE: agent.family=CLAUDE · agent.instance=MAIN.
Documentos modificados: V | CAREER CANON (12.3 CANON:OUTPUT-CONTRACT-003, 12.4 CANON:OUTPUT-CONTRACT-004), skill vantage-qa (ítem 1 del checklist), skill vantage-cv-b (Inmutabilidad de IDs, Estructura Golden Skeleton).
Causa raíz: tres rondas de correcciones consecutivas sobre el mismo CV-B (Adolfo Domínguez) revelaron que la posición de la barra en nodos Rol/Período vivía simultáneamente en ambos nodos en vez de uno solo — causando doble barra o herencia de bold indebida al importar a Figma — y que el footer de metadata, cuando se incluía dentro del .md entregado a Figma, quedaba absorbido por el último bloque del archivo debido a que el blockRegex del plugin (ui.html) extiende cualquier bloque sin un ###### posterior hasta EOF. Verificación adicional confirmó vía MCP Figma (get_metadata + get_screenshot contra el fileKey real) que el patrón corregido (barra al inicio del segundo nodo, footer fuera del .md, sin nodos vacíos) importa limpio: 67/67 nodos reconocidos.
Acción correctiva:
1. Reescrito CANON:OUTPUT-CONTRACT-002 (Golden Skeleton) con placeholders neutros reflejando el patrón corregido — pegado directamente por el operador en Notion.
1. Añadida copia embebida de registry_seed.json dentro de CANON:OUTPUT-CONTRACT-003, como referencia de auditoría cruzada sin salir de Notion (el archivo en /Figma Sync/ sigue siendo la fuente operativa).
1. Reescrito CANON:OUTPUT-CONTRACT-004 (Tag Registry) de v1.0 a v1.1.0 con reglas de serialización mecánicas: posición de barra Rol/Período, formato de Contacto (8:56-8:63), teléfono sin "1" post-52, "ALDO GROUP"→"ALDO", Idiomas en prosa con "e", Tagline 2:5 sin duplicar Contacto, "Flagship Store" capitalizado, Institución sin bold.
1. skill vantage-qa (ítem 1, Invarianza estructural): añadida instrucción de leer CANON:OUTPUT-CONTRACT-002 en vivo antes de evaluar — nunca de memoria ni contra copia local desactualizada; si el Skeleton no está accesible, el ítem se declara FAIL — requiere confirmación humana en vez de asumir estructura.
1. skill vantage-cv-b: corregida referencia a la ubicación del registry_seed.json — ya no asume una única ruta local (04-Vantage_CV/Figma Sync/); ahora acepta Notion (copia embebida en CANON:OUTPUT-CONTRACT-003), Google Drive, o adjunto directo del operador en sesión, leyendo siempre la copia más reciente disponible.
Decisiones confirmadas: "ALDO GROUP"→"ALDO" se ejecutó también vía replace_aldo_notion.py (script del operador) sobre el árbol completo bajo VANTAGE HUB — verificado post-ejecución vía notion-fetch: CANON:EXPERIENCE-005, CANON:CAREER-TIMELINE (ambas filas C05) y CANON:CERTIFICATION-001 confirmados sin "GROUP" remanente. El log del script no mostró líneas de reemplazo individuales porque el Golden Skeleton ya había sido corregido a mano por el operador en una ronda previa — sin discrepancia real, solo ausencia de trabajo pendiente en esa corrida.
Decisiones no duplicadas: no se tocó CANON:POSITIONING (11.x) ni CANON:EXPERIENCE bullets — el cambio fue exclusivamente de formato/serialización de output, no de contenido factual del Canon. No se regeneraron los ~14 CV-B previos del batch de la sesión (Beyond, Confidencial x2, Eurokor, GDC, HM, IKEA, Inditex, Intimissimi, Juguetron, SARELLY, ServiciosAndreiMoygo, Tendam, Walmart, ZaraHome) — quedan con footer embebido y convención de barra antigua; corrección queda pendiente para cuando se re-visiten explícitamente.
Impacto: Corrective, Operativo. Cierra el ciclo BASELINE iniciado la mañana del mismo día — de 3 rondas de corrección iterativa sobre Adolfo Domínguez a un patrón único verificado y documentado en 4 ubicaciones del sistema (Golden Skeleton, registry embebido, Tag Registry v1.1.0, skills QA/CV-B).
Validación: verificación visual directa contra el lienzo Figma real vía MCP (mcp__Figma__get_metadata, mcp__Figma__get_screenshot) sobre fileKey qPyrpGysJs7XxcbubKOo0n — 3 páginas confirmadas limpias (Header/Perfil/Skills/L'Oréal; Bisonte/Dockers/Aéropostale; ALDO/Formación/Cursos). Confirmación adicional del operador tras reimport: 67/67 nodos reconocidos, sin errores de parser.
Estado: WRITE aplicado en Notion (V | CAREER CANON, secciones 12.2/12.3/12.4) y en los archivos de skill entregados al operador (vantage-qa.md, vantage-cv-b.md) para reemplazo manual en el repositorio local. Pin "ALDO GROUP"→"ALDO" cerrado y verificado. Corrección retroactiva a los ~14 CV-B del batch anterior: pendiente, no aplicada en esta sesión.
Tipo: [FIX] [OPS]
Identidad VANTAGE: agent.family=CLAUDE · agent.instance=MAIN.
Documentos modificados: V | CAREER CANON (12.4 CANON:OUTPUT-CONTRACT-004), verify_md.py (nuevo).
Causa raíz: dos bugs distintos de importación a Figma detectados en la misma sesión post-BASELINE v9.22.8. (a) Nodo vacío con characters="" rompe setRangeFontName(0,0,...) en el reset a Regular del plugin (code.js) — "Empty range selected" — tumbando el batch completo (0/67 nodos), detectado en Viva CV-B (2:28, 10:198). (b) Espacio final residual tras bold en nodo de Rol + espacio faltante al inicio del nodo de Período siguiente — mezcla de convenciones de una prueba anterior que quedó parcialmente aplicada en un solo par de nodos (10:164/10:165) de Adolfo Domínguez.
Acción correctiva: Golden Skeleton actualizado con regla explícita de nodo vacío = un espacio, nunca string vacío. Creado verify_md.py — chequeo automatizado (trailing whitespace, bold con espacio final, formato de nodo de Período, nodos vacíos, [PENDING DATA]) obligatorio antes de cualquier entrega de CV-B.
Decisiones confirmadas: el patrón "un espacio en vez de vacío" ya se aplicó y confirmó funcional en Viva CV-B (reimport exitoso). Adolfo Domínguez CV-B corregido (10:164/10:165 normalizado) y confirmado por el operador: reimportado exitosamente a Figma.
Impacto: Corrective, Operativo. Cierra el segundo ciclo de bugs de importación post-BASELINE — de detección manual por el operador a verificación mecánica previa a entrega.
Estado: WRITE pendiente de aplicar por el operador en Notion (Golden Skeleton) y en el repo local (verify_md.py).
Tipo: [FIX] [OPS]
Identidad VANTAGE: agent.family=CLAUDE · agent.instance=KM.
Documentos modificados: Layer_1/scripts/layer_1_orchestrator.py (validate_url()).
Causa raíz: el bypass "JD > 100 caracteres = válido" estaba ubicado después de if not url: return False, "NO_URL", haciéndolo inalcanzable para cualquier vacante sin URL de aplicación (capturas de LinkedIn, apply-por-correo) — se archivaban aunque tuvieran JD completo.
Acción correctiva: reordenado el bypass de JD largo antes del check de URL vacía en validate_url(). Cambio quirúrgico de un solo bloque, sin tocar url_gate.py ni la lógica de agregadores.
Decisiones confirmadas: el bypass de JD largo aplica también cuando no hay URL — la ausencia de URL de aplicación no es por sí sola motivo de archivo si el JD documenta la vacante.
Decisiones no duplicadas: no se modificó el criterio de agregadores ni el gate de NAD/expiración; no se tocó el flujo de Class B origin-independent (v9.22.5), que ya operaba correctamente; no se reabrió la migración de baselines Class_B_Last_Run.
Impacto: Correctivo, Operativo. Detectado al validar en vivo los 4 registros L2 sin baseline de Class B dejados por v9.22.5 (Adolfo Domínguez, Commando Retail, SomosUno, Grupo Axo) — el intento de recomputar Class B sobre ellos exponía que iban a ser archivados incorrectamente por este bug de URL Gate.
Validación: ast.parse OK tras el patch. --dry-run-live antes/después: antes, las 4 filas se archivaban (Archivos: 4, keys=['Next_Action','Notas','Status']); después, Archivos: 0 y las 4 computan Class B completo (Score/Gate_Decision/Prioridad/VM_Scope/Class_B_Last_Run). --apply real ejecutado por el operador: 10 escrituras, 10/10 PATCH 200 OK, 0 archivados, 0 errores. Confirmado en Notion vía notion-fetch directo de las 4 páginas (URL vacía, apply-por-correo o solo screenshot, JD completo en las 4).
Estado: WRITE aplicado. Commit subido a origin/main vía vgit — declaración directa del operador, adoptada bajo Regla de Adopción (Serial Authority v2, v9.21.56), no re-verificado con git log en esta sesión. Cierra el pendiente operativo de first-run Class B sobre los 4 New anunciado en v9.22.5.
IDs afectados: Ninguno (corrección de código, sin alta/baja de ID canónico).
---
Tipo: [DEDUPE] [DOC]
Identidad VANTAGE: agent.family=CHATGPT · agent.instance=DEFAULT (registro original); consolidación editorial agent.family=GROK · agent.instance=DEFAULT.
Documentos modificados: Ninguno en este serial. El trabajo de código, tests, schema y migración Notion quedó documentado de forma canónica en v9.22.5.
Causa raíz del dedupe: dos entradas de changelog (v9.22.5 GROK y v9.22.6 CHATGPT) describían el mismo batch — Class B origin-independent, commit 25b06d8, migración 28/4/6 — con redacción distinta pero sin segundo cambio de sistema.
Acción correctiva: esta entrada se anula como evento operativo. El contenido útil (validación de suite completa Layer 1, control pre-cambio 160/13, confirmación push main) se fusionó en v9.22.5.
Decisiones confirmadas: un serial = un cambio de sistema; la doble documentación del mismo fix no implica dos versiones de producto.
Decisiones no duplicadas: no se revirtió código; no se re-ejecutó migración Notion; no se alteró v9.22.7.
Impacto: Solo documental / higiene de changelog. Sin impacto runtime.
Validación: N/A (dedupe editorial).
Estado: ANULADA como entrada de cambio. Fuente de verdad del fix Class B: v9.22.5. URL Gate y apply de los 4 New: v9.22.7.
IDs afectados: Ninguno.
Tipo: [FIX] [ARCH] [OPS]
Identidad VANTAGE: agent.family=GROK · agent.instance=DEFAULT (implementación Phase 2/3); integración y publicación en main confirmada por operador / agent.family=CHATGPT · agent.instance=DEFAULT.
Documentos modificados: Layer_1/scripts/class_b_guard.py (CLASS_A_FIELDS / CLASS_B_FIELDS); Layer_1/scripts/tracker_flow.py (is_mutable + _DATE_PROPS); Layer_1/scripts/layer_1_orchestrator.py (needs_first_class_b_compute, manual_first_protection, baseline Class_B_Last_Run, snapshot); Layer_1/tests/test_class_b_origin_invariant.py (T1–T15 + regression). Schema Notion Tracker: propiedad Class_B_Last_Run (date) en collection://442938be-fc42-828f-b72e-076818d65a5b.
Causa raíz: la elegibilidad Class B dependía del origen técnico de creación/escritura (feed/API vs MCP/manual vs layer). Registros equivalentes en lifecycle y Class A recibían tratamiento distinto; first-run podía bloquearse solo por last_edited_by humano cuando no existía baseline; Fetch/Fuente estaban mal clasificados; el snapshot podía inventar baseline en filas no evaluadas.
Acción correctiva: baseline canónico Class_B_Last_Run (última evaluación Class B exitosa; semántica distinta de Last_Gate_Run); first-run cuando Class_B_Last_Run ausente y el registro es elegible, independientemente de Origin o editor; ventana de protección manual anclada al baseline (edición humana Class B protege; edición solo Class A permite recomputar); Fetch y Fuente movidos a Class A; snapshot solo persiste filas con evaluación real (_class_b_computed) y nunca se usa como fuente de verdad ni backfill; tests de invariante de origen + regression del gap original L2 feed vs MCP/manual.
Decisiones confirmadas: el origen técnico no determina si Class B se calcula; same lifecycle + same Class A + different origin = same Class B behavior; ausencia de Class_B_Last_Run = primera evaluación pendiente, no “protegido por humano”; Last_Gate_Run sigue siendo solo marker de cambio de Gate; Class_B_Last_Run es el marcador canónico de última evaluación Class B exitosa.
Decisiones no duplicadas: no se utilizó Last_Gate_Run como sustituto de Class_B_Last_Run; no se utilizó Snapshot para crear baselines; no se condicionó la elegibilidad Class B al origen del registro; no se reescribió Score/Gate_Decision/Next_Action/Status en migración; no se tocó Por Revisar ni estados terminales; no se inventaron baselines sin evidencia de evaluación previa; no se modificó el gate de URL/JD (eso es v9.22.7, posterior y distinto).
Migración Notion: 38 registros validados. Baseline establecido en 28 SAFE_TO_MIGRATE (Class_B_Last_Run = Last_Gate_Run solo con evidencia previa de Class B); 4 New L2 sin baseline (MUST_RECOMPUTE vía first-run canónico); 6 Por Revisar MUST_NOT_TOUCH intactos.
Impacto: Correctivo, Arquitectónico, Runtime y Operativo. Cierra la clase de defecto origin-dependent Class B processing y fija semántica persistente baseline Class B vs cambio de Gate.
Validación: test_class_b_origin_invariant.py 18/18 PASS. Suite Layer 1: 178 passed / 13 failed; control contra origin/main pre-cambio: 160 passed / 13 failed → 0 regresiones nuevas atribuibles a Phase 2. git diff --check PASS. Schema check: Class_B_Last_Run date presente. Post-migración: Objetivo/Postulado con baseline; New 0/4 baseline (esperado); Por Revisar 0/6 baseline (protegido). APPLY Notion: solo Class_B_Last_Run en 28 páginas.
Estado: WRITE aplicado. Código en origin/main (commit 25b06d8 — fix: make Class B evaluation origin-independent). Schema + 28 baselines WRITE en Tracker live. First-run de los 4 New L2 (Adolfo Domínguez, Commando Retail, SomosUno, Grupo Axo) quedó pendiente operativo y se cerró en cadena con v9.22.7 (URL Gate), no en este serial.
IDs afectados: Ninguno (corrección de código + schema/baseline; sin alta/baja de ID canónico).
---

Documento modificado: KERNEL, SP
Documentos potencialmente afectados: MANUAL (parcial, pendiente nodo 8), ALIASES (pendiente nodo 9)
Tipo de impacto: Normativo + Operativo
Acción correctiva: Rediseño Discovery L1/L2/L4 — L1 absorbe Gemini bajo ejecución Hermes; L2 se redefine como "Personal Request" (patrón espejo de L3, sin motores externos); jerarquía de dedup invertida a L2>L1>L3; Hermes agregado a matriz de ruteo L4 y a registro de identidad SP:BOOTLOADER-002.
Estado final: PASS parcial — nodos 1–7 y 10 listos para escritura; nodos 8–9 bloqueados en espera de tu input.
---

Documento modificado:
- Layer_1/scripts/dedup_opportunities.py
- Layer_1/scripts/feed_processor.py
Documentos potencialmente afectados (impacto documental, aún no actualizados):
- KERNEL:GATE-DECISION-011 (Matriz de Transición de Estados) — declara
explícitamente "Dedup_Flag='Posible duplicado' (select)" — ROMPE, según
auditoría Notebook Gemini de esta sesión.
- KERNEL:GATE-DECISION-007 (Marcado Manual de Archivado) — asume string
'Posible duplicado' como señal — AMBIGUO.
- MANUAL:DATA-MANAGEMENT (§10, Dedup) — misma asunción de string — AMBIGUO.
Tipo de impacto: Operativo + Runtime
(cambio de tipo de propiedad Notion + lógica de lectura/escritura en 2
scripts productivos; sin cambio de comportamiento funcional del pipeline)
Descripción del cambio:
1. Propiedad "Dedup_Flag" en VANTAGE TRACKER migrada de tipo Select
(única opción: "Posible duplicado") a tipo Checkbox, para alinear con
el patrón ya usado por "Archivar".
1. dedup_opportunities.py: write_dedup_flag() actualizado — lectura vía
dedup_field.get("type") == "checkbox", escritura vía
{"checkbox": True/False} en vez de {"select": {"name": ...}}/None.
1. feed_processor.py: bloque de asignación (líneas ~581-599) actualizado
con el mismo patrón select→checkbox.
1. Verificado en producción: corrida post-fix confirmó marcado correcto
(operador confirma "se marcaron correctamente").
Acción correctiva ejecutada:
- Backups automáticos creados antes de cada edición
(dedup_opportunities.py.bak-, feed_processor.py.bak-).
- Ambos scripts editados vía comando de terminal de una sola pasada,
con assert de verificación de bloque exacto antes de escribir.
Estado final de la validación:
- dedup_opportunities.py: PASS (confirmado por operador en producción)
- feed_processor.py: PENDIENTE — actualizado pero sin corrida de
verificación confirmada en esta sesión (próxima ejecución del
pipeline L1/L3 real validará)
- class_b_guard.py: NO auditado — no se confirmó si valida estructura
interna del payload; riesgo residual si rechaza {"checkbox": ...}
Pendiente (no cerrado en esta sesión):
- Actualizar KERNEL:GATE-DECISION-011, KERNEL:GATE-DECISION-007 y
MANUAL:DATA-MANAGEMENT para reflejar tipo Checkbox (Regla de Versión
Única, SP:SYNC-RULE).
- Verificar class_b_guard.py contra el nuevo payload.
- Confirmar tipo de propiedad ya migrado en Notion (Select→Checkbox) —
prerequisito operativo para que ambos scripts lean valores correctos.
Versión: [pendiente — operador hace bump manual]
════════════════════════════════════════════════════════════
---
Tipo: [REFactor] [OPS]
Identidad VANTAGE: agent.family=CHATGPT · agent.instance=DEFAULT.
Documentos modificados: 29 skills activos fueron migrados de SKILL.md dentro de subdirectorios a archivos planos skills/<skill-name>.md. Se actualizaron compile_skills.py, verify_versions.py, update_triggers_json.py, g9_docsync_verify.py, skill_hash_baseline.json, triggers.json y G9_DOCSYNC_PACKAGE.md.
Decisiones confirmadas: se conserva el contenido byte-for-byte de los 29 skills; el flattening se limita a los skills activos; vantage-active-search-weekly conserva sus assets auxiliares en su directorio; triggers.json mantiene sus 28 registros existentes y solo actualiza referencias de ruta/URL; el baseline se rebaselinizó contra las versiones vigentes de main para los 8 skills cuyo hash histórico estaba desfasado; se conserva la estructura de assets auxiliares fuera del nuevo nivel plano.
Decisiones no duplicadas: no se modificaron los contenidos funcionales de los skills; no se eliminaron assets auxiliares de vantage-active-search-weekly; no se realizó ningún cambio adicional en documentación histórica fuera de las referencias necesarias para el flattening.
Impacto: Estructural, Operativo, Runtime y Navegación. La resolución Git confirmó los 29 movimientos como renames al 100%.
Validación: Flattening validado con 29/29 skills idénticos byte-for-byte a HEAD; 0 archivos SKILL.md; 29 archivos .md planos; baseline verificado; py_compile PASS; git diff --check PASS. Commit 80c4604 creado y push origin main completado correctamente.
Estado: WRITE aplicado. El cambio ya está publicado en main.
---
Tipo: [DOC] [OPS]
Identidad VANTAGE: agent.family=CHATGPT · agent.instance=DEFAULT.
Documentos modificados: Manual y Kernel. Aliases fue revalidado: los cambios de este DRY RUN ya estaban aplicados, por lo que no se reescribió.
Decisiones confirmadas: dedup por auditoría requiere --apply y usa class_b_guard; L3 usa backend configurable ollama/groq, límite GEMINI_MAX_EMAILS_PER_RUN (default 5) y conserva como no leídos los correos con fallo recuperable; B-12 mantiene regenerate_index_json() activo antes de git status en sync(); B-22 no se modificó porque no apareció la cadena previa exacta Aliases=6-7; B-25 queda como decisión documental sin mover ni eliminar archivos.
Decisiones no duplicadas: B-09, H-6 y B-15 ya existían en sus nodos SSOT; H-1 no se modificó porque no apareció una referencia literal aplicable a RT-1.
Impacto: Normativo, Operativo, Runtime y Navegación.
Validación: DRY RUN aprobado con APROBAR_WRITE; patches mínimos por coincidencia exacta; write-back verification PASS para Manual y Kernel. Census no aplica: no se creó ningún ID canónico.
---
diff --git "a/Documentaci\303\263n/ACTIVE/Change Log.md" "b/Documentaci\303\263n/ACTIVE/Change Log.md"
index 0105cc9..e79f299 100644
--- "a/Documentaci\303\263n/ACTIVE/Change Log.md"
+++ "b/Documentaci\303\263n/ACTIVE/Change Log.md"
@@ -258,5 +258,23 @@ Acción correctiva ejecutada: Agregada regla explícita en §14 — "Cada compon
IDs afectados: Ninguno (sin alta/baja de ID canónico — extensión de nodo existente).
Estado final de la validación: Write-Back Verification PASS — confirmado vía re-fetch en vivo de §14, regla nueva presente sin mismatch. Census no aplica (sin altas/bajas de ID). Sin DRY RUN presentado en el mismo turno de aprobación por instrucción explícita del operador (yep).
+Tipo: [CODE] [FIX]
+Documento modificado: Layer_1/scripts/hard_block_gate.py · Layer_1/config/hard_blocks.json · Layer_1/scripts/layer_1_orchestrator.py (manual_first_protection) · src/gate_logic.py (docstring only) · tests/test_hard_block_gate.py · tests/test_vantage_status.py · tests/test_llm_providers.py · tests/test_agent_history_diagnostics.py · tests/test_scout_dry_run.py · tests/test_layer_1_orchestrator.py (G9)
+Documentos potencialmente afectados: Ninguno en Kernel/Manual/SP/Canon — consolidación de código Layer_1 y alineación de contratos de tests, sin cambios normativos.
+Tipo de impacto: Operativo — cierre de v9.23.0 sobre v9.22.0: consolidación de Fase 2 (2.5–2.6, ya entregada en commit previo 62ee000), un bug funcional real corregido en G5 (manual-first), y alineación de la suite de tests con el código productivo tras la migración de LangChain a browser-use.
+Causa raíz (G5 manual-first): manual_first_protection() dependía únicamente de is_mutable() como guard — sin evaluar explícitamente la ventana de edición humana contra Last_Gate_Run. Last_Gate_Run y last_successful_run.json son contratos distintos; el guard general no sustituye la ventana manual.
+Acción correctiva ejecutada:
+1. Hard Block Gate (2.5) — hard_block_gate.py consolidado como implementación standalone; hard_blocks.json es la única fuente de términos bloqueados, sin capa paralela de regex. Fixtures de test_hard_block_gate.py alineados con la fuente canónica (Aéropostale removida de los fixtures — nunca perteneció al conjunto vigente de Hard Blocks; el fallo era del fixture, no del Gate. Bloqueo de producción sin cambios).
+1. Scout (2.6) — src/gate_logic.py fuera de alcance total, decisión explícita del operador (diseño no completado ni a completarse). Cambio limitado a docstring documentando la decisión, sin efecto en comportamiento.
+1. G5 Manual-First — manual_first_protection() ahora evalúa explícitamente last_edited_time > Last_Gate_Run con actor humano válido, antes del guard general. Se preserva la excepción de una sola pasada para Rechazado (Q-11/SCHEMA-008).
+1. Suite de tests — vantage_status.py con cobertura contractual nueva (normalización, mapeos legacy, terminalidad, protección/mutabilidad, Gate Decision); test_llm_providers.py migrado del API interno obsoleto _chat_openai (eliminado en edc75c5, migración a browser-use) al API real (ChatOpenRouter, ChatOpenAI+base_url, Groq agregado al contrato de providers); test_scout_dry_run.py con ROOT corregido (parents[2]→parents[1], escribía fuera del repo); test_default_provider_is_local_ollama aislado de LLM_PROVIDER del .env local; test_g9_changelog_v922_entry ampliado de text[:2500] a text completo.
+Resultado:
+- Suite completa: 311 passed, 5 failed (todos ModuleNotFoundError: browser_use, dependencia opcional no instalada en el entorno de verificación — no relacionado al código bajo prueba), 2 skipped.
+- Cost-control fallback validado contra comportamiento real bajo USE_CHEAP_FALLBACK=true / LLM_COST_LIMIT<1.0 — sin cambio de política: el fallback de Gemini sigue en gemini-1.5-flash (discontinuado según el propio código), no corregido en este lote.
+- G9 Change Log: "v9.22.0" localizado como mención de paso en entrada normativa distinta (Fe de Erratas G8/G9, línea 46) — no existe ni existía una entrada propia para esa versión; el fix corrige el rango de búsqueda del test, no crea un registro nuevo.
+IDs afectados: Ninguno (código y tests; no dispara CENSUS-SYNC Regla 1).
+Estado final de la validación: Commits verificados en origin/main: 62ee000 (Fase 2 lote 2) y 16acdea (auto-sync — G5 fix + suite de tests). Fixes de Fase 1 y Fase 2 lote 1 verificados en sesiones previas (ver HO-000059). DRY RUN presentado y aprobado explícitamente por el operador (yep) antes de escritura — version bump y esta entrada ejecutados en la misma pasada por instrucción del operador.
+Handoff de referencia: continuación de HO-000059 (CLAUDE/MAIN), consolida Fase 2 completa (2.1–2.6) + hallazgo G5 + reconciliación de suite de tests reportados por sesión posterior.
+---
> El histórico completo del CHANGELOG lo podrás encontrar en ARCHIVO CHANGELOG, en esta pagina de consulta continua solo encontrarás las últimas diez entradas para garantizar la operación y referencia del sistema.
---
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
---
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
---
## Sep 18, 26 06.11
Documento modificado: KERNEL, SP, MANUAL  
Tipo de impacto: Normativo + Operativo  
Acción correctiva: Rediseño Discovery L1/L2/L4 — L1 absorbe Gemini bajo ejecución Hermes Desktop; L2 se redefine como "Personal Request" (patrón espejo de L3, sin motores externos); jerarquía de dedup invertida a L2>L1>L3; Hermes agregado a matriz de ruteo L4 y a registro de identidad SP:BOOTLOADER-002; Vassemble actualizado a Hermes Desktop en MANUAL.  
Estado final: PASS — todos los nodos validados y listos para escritura.

