# V | MANUAL

Objetivo
- Oportunidades de alta señal desaparecen antes de ser procesadas.
- Tiempo consumido en vacantes irrelevantes que no cumplen criterios mínimos.
- Sin trazabilidad: qué se aplicó, cuándo, qué sigue.
- Convierte la búsqueda laboral en un pipeline con contratos de procesamiento definidos.
- Filtra antes de evaluar: 
- Links muertos → Score 0, Status Expirada. 
- Empresas en lista negra → rechazadas en Discovery. 
- Verifica antes de creer: 
- Si el link no funciona, la vacante no entra al pipeline activo. 
- Centraliza en un solo lugar:
- Notion es la fuente única de verdad — vacantes, aplicaciones, scores, seguimiento
- Calcula con lógica determinista:
- Throughput semanal — vacantes nuevas ingresadas por ciclo de feed_processor.py.
- Tasa de Gate CREATE — % de vacantes con Gate_Decision=CREATE sobre el total procesado.
- Tasa de recuperación RT-1 — % de vacantes BLOCKED que alcanzan PATCHED → CREATE vía Dashboard.
- No busca cualquier empleo — solo roles visuales en sectores lujo, premium, cool DNA y agencias de experiencia.
- No genera volumen masivo — calidad de señal sobre cantidad de resultados.
- No adivina campos faltantes — si falta información, el campo queda pendiente y el sistema lo reporta.
- Perfil Senior en:
- Visual Merchandising
- Brand Environment
- Store Design
- Retail Experience.
- Geografía:
- CDMX
- LATAM.
- Sectores target:
- Lujo (LVMH, Kering, Richemont), 
- Retail Premium (Nike, Apple, Inditex)
- L1 - Active Recon: Búsqueda activa vía prompts ejecutados en motores de búsqueda (Perplexity, Comet).
- L3 - Passive Intake: Lectura automática de correos etiquetados en Gmail.
- L4 - Documentation: mantiene sincronizados en background el repositorio de código (git) y los documentos fundacionales del sistema entre Notion y disco local.
El sistema evalúa cada vacante nueva en tres pasos, siempre en este orden:
El sistema aplica dos capas de exclusión para garantizar la calidad de la señal — ambas se explican con su lista completa y mecánica de recuperación en MANUAL:DATA-MANAGEMENT, pero conviene entender la diferencia conceptual desde ahora, porque ambos términos aparecen constantemente en el flujo semanal:
Base KERNEL:FAIL-PHILOSOPHY
- Python 3.8+ instalado en Mac.
- Acceso a Claude.
- Cuenta de Perplexity con modo Deep Research activo.
- Acceso a Gemini con modo Deep Research o Search activo.
- Acceso a You.com con modo Research o Agent activo.
Verificar Notion
1. Las instrucciones activas deben residir exclusivamente en las Project Instructions de la plataforma. Encontrarás la referencia documental en SP:BOOTLOADER. Este es el proceso para su configuración:
1. Inicia un nuevo chat. El Agente  realizará un fetch automático del Bootloader  desde Notion.
Nota: este setup de Claude es de una sola vez por proyecto — no se repite en cada sesión de trabajo. Lo que sí se repite en cada sesión es el Ciclo de Sesión completo, explicado en MANUAL:SESSION-CYCLE.
Verificar Archivos del Sistema y Permisos de Ejecución
```bash
chmod +x $LAYER_1_DIR/layer_1_pipeline.sh
chmod +x $LAYER_1_DIR/wrappers/layer_1_wrapper.sh
chmod +x $LAYER_3_DIR/wrappers/layer_3_mail.sh
chmod +x $DASHBOARD_DIR/wrappers/dashboard_start.sh
```
Test Inicial del Pipeline
Output esperado:
```plain text
=== VANTAGE PIPELINE STATUS ===
Ready-to-Apply: [N] vacantes
REVIEW_NEEDED: [N] vacantes
…
```
1. cd ... — te posiciona en Layer_1/scripts, donde viven vantage.py y todos los scripts del runtime.
1. cat ../.env | grep NOTION_TOKEN — verifica que el token de Notion esté presente en el .env; no valida si está vigente, solo que la variable existe.
1. cat ~/.vantage/l3_heartbeat.json — confirma que L3 corrió y dejó su heartbeat; si el archivo no existe o el timestamp es viejo, L3 falló silenciosamente.
1. python3 vantage.py ask "find candidates" — mismo smoke test, distinto intent; mismo resultado esperado (falla) por la misma causa.
Ciclo de Sesión
### ¿Cuándo se dispara esto?¿por qué es distinto del ciclo semanal?
Este ciclo se dispara con dos comandos:
No necesitas invocarlo tú manualmente cada vez que se te ocurra — pero sí necesitas recordar que es el primer paso obligatorio: si acabas de abrir Claude para trabajar en VANTAGE hoy, el primer paso siempre es este ciclo, antes de tocar Tracker, Dashboard o cualquier trigger de CV descrito en MANUAL:WEEKLY-FLOW.
- notion-search sobre el data source del Ledger (collection://38324240-c686-47d0-8082-cee5e4409f88)
- notion-fetch de la fila más reciente devuelta
- Comprimido: Una línea: [COMPRIMIDO] resumen + "expandir en próxima sesión".
- Comprimido: Si no hay output, marcar SYNC PENDIENTE en Ledger.
- Drift de versión detectado y SÍ es el documento que ibas a tocar → se resuelve el drift primero, antes de aplicar cualquier parche nuevo — de lo contrario terminarías escribiendo sobre una base que ya no coincide con lo que las otras piezas del sistema esperan.
- Un cambio de código, schema o flujo operativo quedó sin reflejo en la documentación → esto no es parte del drift de versión que acabas de revisar arriba, es el caso que cubre KERNEL:DOCUMENTATION-001: el contrato que detecta contenido operativo nuevo sin ancla en Kernel, Manual, Canon o System Prompt, ya sea porque tú lo pides explícitamente ("documentación transversal", "parche orgánico") o porque el sistema lo señala como recordatorio no-bloqueante a media tarea, sin detener lo que estabas haciendo.
- Un pendiente detectado durante la sesión necesita convertirse en ticket (o no) → esto lo gobierna KERNEL:GATE-DECISION-009 (3 niveles de escalamiento). En resumen: esfuerzo bajo y sin bloqueo confirmado se queda en pending_summary del Ledger
El Checklist
Esto importa porque el Dashboard (que verás en detalle MANUAL:WEEKLY-FLOW-002) usa exactamente esta misma infraestructura visual — no son dos sistemas de interfaz distintos, son la misma base compartida.
- No copies/pegues código de un HTML al otro para “igualar” un color o componente — edita vantage-tokens.css o vantage-theme.js, que ambos ya leen. Editar directo en el HTML reintroduce el mismo drift que se corrigió.
El ciclo comienza con los prompts de búsqueda, los cuales no se copian de versiones anteriores — se materializan bajo demanda ejecutando el Weekly Prompt Assembler:
### ¿Cómo uso los archivos generados?
- Regresarás a Perplexity Desktop y, usando como base el Prompt E, pegarás los JSONs de L1 + L2.
- Perplexity aplicará dedup con clave compuesta brand+title+location siguiendo una jerarquía L1 > L2 (de las vacantes duplicadas persistirán las instancias de L1, tomando de L2 la información que pueda complementar sus propiedades para Class A).
- Guardarás el resultado en:
### ¿Como corre L3?
- Extrae vacantes con Groq y las escribe directamente en el Tracker. 
- Ejecuta manualmente para procesar backlog de Gmail antes del siguiente ciclo automático. 
- Hard-blocked (L’Oréal · Levi’s/Dockers · El Palacio de Hierro — ver lista completa en MANUAL:DATA-MANAGEMENT)
- Asuntos de agradecimiento
- Newsletters
- Confirmaciones de cuenta.
- Procesa máximo 10 correos por run (configurable en GROQ_MAX_EMAILS_PER_RUN).
- Si hay backlog, el script reporta cuántos quedan.
Abre la Terminal y procesa el JSON consolidado de L1+L2:
- Dispara: El script vantage_pipeline.sh actúa como wrapper: activa el entorno virtual (.venv), valida la estructura y dispara feed_processor.py para normaliar campos, aplicar dedup cross-layer (ventana 30 días — ver MANUAL:DATA-MANAGEMENT) y presentarte el DRY RUN antes de escribir en Notion.
- Aprobar escritura: revisa el DRY RUN en terminal. El output muestra las propiedades Class A de cada instancia a crear. Las entradas duplicadas aparecen como SKIP. Las que requieren revisión aparecen como REVIEW_NEEDED. Confirma con y (yes) para escribir en Notion. Cualquier otra tecla cancela sin escribir.
- Los registros con status REVIEW_NEEDED que se escriben en Notion se resuelven al día siguiente en el Dashboard MANUAL:WEEKLY-FLOW-002
- Procesar con Python: Para este punto las propiedades Class A de cada instancia nueva se habrán poblado por L1, L2 o L3. 
- Para poblar las propiedades Class B de todas las instancias pendientes en el Tracker, ejecutarás la app LAYER 1.app desde /Applications o usando Terminal:
- Vacantes con Score ≥ 60 están listas para CV Optimization en preparación para tu postulación — esto es lo que trabajarás el Miércoles MANUAL:WEEKLY-FLOW-003.
- El repositorio git del sistema (vgit)
- Los 6 documentos fundacionales entre Notion y el disco local (vdoc). 
Son dos herramientas separadas que se combinan: vdoc mueve contenido documental Notion ↔︎ ACTIVE/, y al terminar dispara automáticamente un git_sync — por eso casi nunca necesitas correr vgit a mano después de un vdoc.
### ¿Qué es vgit?
- Ejecuta vgit desde Terminal en cualquier momento para enviar un sync inmediato — útil si hiciste cambios locales fuera del ciclo automático y no quieres esperar al siguiente horario.
- Verificar último run: cat /tmp/vantage_l4_gitsync.log — cada corrida (automática o manual) queda registrada ahí con timestamp, exit code y el output completo del sync, así puedes auditar qué pasó sin depender de las notificaciones del sistema.
- Si el repo no existe o está corrupto, vgit ya no lo confunde con “sin cambios” — reporta el error explícitamente y la notificación del wrapper se ve roja (❌), no verde.
- Archivos: 
- Layer_4/scripts/git_sync.py 
- Layer_4/wrappers/git_sync_wrapper.sh 
- ~/Library/LaunchAgents/com.vantage.gitsync.plist
Como notion y local sobreescriben sin comparar fechas, ambos son operaciones forzadas: antes de ejecutar nada, vdoc te muestra automáticamente un preview (equivalente a --dry-run) de lo que va a hacer, y te pide confirmación explícita en terminal (s para continuar, cualquier otra tecla cancela).
Si por alguna razón corres el comando sin una terminal interactiva disponible, el script no asume que confirmaste — cancela por seguridad y no escribe nada. vdoc auto nunca pide esta confirmación porque nunca sobreescribe algo más reciente.
- vdoc local dry — preview de lo que haría vdoc local
- vdoc kernel dry — preview de solo Kernel en modo auto
### ¿Que es sync?
Martes
Abrir el Dashboard: ejecuta en terminal:
El wrapper dashboard_start.sh arranca el servidor Flask en http://127.0.0.1:8000 (accesible también vía Tailscale desde otros dispositivos), ejecuta un smoke test automático y abre dashboard.html en el navegador. Output esperado en terminal: SMOKE PASSED — abriendo dashboard. Si el smoke falla, emite notificación sonora de error (Basso) y no abre la UI. El indicador “BACKEND OK/OFFLINE” en la esquina superior confirma la conexión en vivo.
1. Selecciona la vacante del dropdown (muestra Marca · Rol · Score · VM_Scope).
1. Crear instancia — abre una instancia en estado BLOCKED y carga el payload desde Notion. Audit Log registra domain.instance.created.
1. Edita los campos incorrectos en el panel de patch — solo Class A (URL · JD · Source_Type · Prioridad). Los campos Class B no son editables.
1. Proponer Patch — almacena la corrección. Audit Log registra domain.patch.proposed.
Las entradas con este status son escritas en Notion por feed_processor.py cuando no pudieron procesarse completamente: la URL era parcial o ambigua, la marca no resolvía contra el alias map, o el sistema detectó un semi-duplicate cross-layer que requiere revisión humana. Mientras el status permanezca en REVIEW_NEEDED, sus campos Class B (Score, Gate_Decision, VM_Scope, Role_Class) quedan bloqueados — Python no los calcula.
Contrato de resolución — 4 pasos obligatorios:
1. Corrige el campo problemático directamente en Notion: reemplaza la URL parcial con la URL completa, o ajusta el nombre de la marca al valor que exista en el alias map.
1. Corre el pipeline:
Python detecta Status = Target en entradas que tenían Gate vacío o REVIEW_NEEDED y procesa sus campos Class B normalmente — calcula Score, Gate_Decision y el resto.
Nota importante: estas entradas no pasan por el Dashboard. El Dashboard es para vacantes con Gate = BLOCKED que ya tienen campos Class B calculados y necesitan corrección de inputs Class A. REVIEW_NEEDED es un estado previo — todavía no llegó a tener Gate calculado.
- Determina el Positioning Mode aplicable mediante el Algoritmo de Selección N1–N4 (KERNEL:CV-PIPELINE-001) — hay cuatro modos posibles, definidos en el Career Canon:
- N1 Luxury Brand Execution
La sesión termina aquí. No se escribe ningún CV en CV-A.
Abre una sesión nueva de Claude. Pega el HANDOFF completo y dispara:
1. Autorización explícita del operador — Claude espera confirmación antes de continuar. Sin autorización, no escribe nada.
1. Documentar la URL del Markdown.
Regla de orden: el Markdown nunca se escribe en Notion si el operador no ha autorizado explícitamente. El orden cronológico de experiencia es invariante: C01 → C02 → C03 → C04 → C05. No se reordena por vacante ni por Positioning Mode.
- Bloque # MARKDOWN CANON ALIGNED en la página de la vacante en el Tracker — el Markdown completo con Figma tags, dentro de un bloque de código markdown.
CV-B ya no tiene permiso creativo sobre la estructura. El proceso es de inyección en slots vía plugin — arquitectura, contrato de bloque, flujo de inyección, sanitización y diagnóstico de errores viven en MANUAL:FIGMA-SYNC-003 (§20, Flujo de Inyección) y subsecciones adyacentes 20.1–20.5. Con el .md autorizado en mano:
1. Plugins → Development → VANTAGE CV Sync.
Si el plugin reporta "Keys sin resolver" o "0 nodos actualizados", ver MANUAL:FIGMA-SYNC-DIAGNOSTIC (§12).
Claude revisa formato y completitud con checklist de 6 ítems y entrega go/no-go. QA no evalúa fit — evalúa que el documento esté correcto como entregable.
```bash
~/vantage_pipeline.sh analytics
```
Output: efectividad por fuente, tasa de links muertos por tipo de URL, ratio career pages vs. aggregators.
Complementa la narrativa día-por-día con una vista de:
- Trigger → resultado desacoplada del calendario.
- Las entradas del Tracker reflejadas en la columna “Resultado” son siempre campos Class B
Nota operativa: los días de semana en 8.1–8.5 son metadato de cadencia del operador, no guard conditions de ningún gate. Una vacante con Score ≥ 60 puede alcanzar READY_TO_APPLY el mismo día de su ingesta, sin esperar al ciclo siguiente. → Ver KERNEL:GATE-DECISION-011 para vista completa de transiciones.
Runtime
Sin --execute, el comando nunca escribe en Notion. Esta protección es permanente — no se puede desactivar sin modificar el flag.
Sin --dry-run, solicita confirmación explícita (s) antes de cualquier escritura.
Estos dos últimos alimentan a vantage-sync-script-library y vantage-sync-skill-library respectivamente. El modo --check fue eliminado en Kernel v9.6.2.
- Si status muestra orphan_candidates > 0 de forma persistente.
El Runtime Build regenera los tres artefactos de lectura del sistema: entity_index_v2.json, graph_v2.json y backlinks_v2.json. Se corre desde Layer_1/scripts/ con el venv activo.
### 9.5 MANUAL:RUNTIME-005
Notebook Gemini — Triaje de Consultas Documentales
Esta sección consolida en un solo lugar todo lo relacionado con exclusiones y deduplicación de vacantes — conceptos que se mencionan a lo largo de MANUAL:OBJECTIVE, MANUAL:HOW-IT-WORKS y MANUAL:WEEKLY-FLOW, y que aquí tienen su definición completa y única.
Estas empresas o tipos de rol nunca entrarán al sistema. Se filtran en el origen (antes de que la vacante exista como registro en Notion) y no son recuperables bajo ninguna circunstancia, ni siquiera vía Dashboard:
### Dedup
- Jerarquí»¶ entre capas: L1 > L2 > L3. Cuando dos capas detectan la misma vacante, persiste la instancia de la capa de mayor jerarquí»¶, pero se toman de la capa de menor jerarquí»¶ los datos que puedan complementar sus propiedades Class A (esto es exactamente lo que ocurre en el paso de Consolidation & Dedup del Lunes, MANUAL:WEEKLY-FLOW-001).
- Resolució¶¶¶n de flags: los registros marcados Dedup_Flag='Posible duplicado' por la auditorí»¶ post-ingesta son candidatos a archivado; su resolució¶¶¶n opera ví­a vantage-tidy-opportunities-tracker (DRY RUN + APROBAR_WRITE), no hay archivado automá¶¶tico.
Health Check
### ¿Qué es y qué lee?
Es un script de arranque, de lectura estricta (cero escritura salvo la excepción documentada abajo). Corre automáticamente al invocar el alias start (activa venv + carga env + ejecuta el script). También puede correrse manualmente:
1. Último commit (vgit) — git log -1 para timestamp de referencia.
1. Último vdoc sync — cuál de los 6 docs locales tiene el mtime más reciente, y hace cuánto.
- ✓ verde — check pasó.
- ! amarillo — advertencia, no bloquea (ej. índice stale antes del auto-sync, tickets pendientes).
- ✗ rojo — fallo real, contribuye al exit code final.
- Línea final Sistema OK (exit 0) vs. Sistema con issues: [lista] (exit 1).
- Si no tienes Terminal a la mano en ese momento, el ticket se queda en Blocked-Census — no se cierra en falso, se marca como bloqueado hasta que puedas correr el script.
- Primero Census actualizado
- Después la entrada de Changelog. 
### Aplicación de Hipervínculos Cross-Reference
- vantage-tidy-bug-task-tracker — archiva tickets ya resueltos (confirmación directa del operador, o detección indirecta vía Change Log). Requiere Dry Run + APROBAR_WRITE antes de archivar.
- vantage-tidy-opportunities-tracker — identifica duplicados y vacantes expiradas en el Tracker de vacantes para archivado, usando los mecanismos de fingerprint y protección de estado terminal ya implementados en feed_processor.py (ver MANUAL:DATA-MANAGEMENT). Requiere Dry Run + APROBAR_WRITE.
- vantage-tidy-changelog — mantiene el Change Log con las últimas 10 entradas visibles, moviendo el exceso al Archivo Changelog histórico. Úsala cuando el Change Log activo supera 10 entradas o para housekeeping documental puntual.
- vantage-present-handoff — genera el snapshot de contexto de sesión para continuidad en un chat nuevo. Es independiente y se puede invocar en cualquier momento; no requiere que la sesión esté cerrando (ver también MANUAL:SESSION-CYCLE, Cierre, donde vantage-session-close la invoca automáticamente como parte de su secuencia normal).
- Verificar .env en ~/vantage_notion_audit/.
- Verificar entorno Python activo: source Layer_1/.venv/bin/activate && python --version.
- Confirmar permisos de ejecución: ls -la ~/vantage_pipeline.sh (debe tener x).
- Desde v8.7.6: health_check.py detecta índices >24h y dispara vantage.py sync automáticamente en cada corrida de start — no requiere acción manual en el flujo normal.
- Solución manual (solo si el auto-sync falló): python vantage.py sync desde Layer_1/scripts.
- Verificar resultado: vantage.py status debe mostrar entities_after >= entities_before.
- Si persiste: verificar token Notion y conectividad a internet.
- Si falla autenticación IMAP: regenerar app password de Gmail.
Checklist de situaciones:
- Revisar VM_Scope asignado (debe ser Core/Adjacent, no Off-Target).
- Si todo está correcto: revisar pesos de scoring en profile_config.yaml.
- Si no aparece: refrescar cache de Runtime (vantage.py sync).
Prioridad A — Terminal (canónico): lazy_loader.py ejecuta Server-Side Lazy Load. Parsea bloques hijos de la Notion API y devuelve únicamente el payload del ID solicitado. Consumo: ~150 tokens por llamada.
Prioridad B — MCP Notion: reservado exclusivamente para escrituras (APROBAR_WRITE) y modificaciones estructurales de páginas. No se usa para lectura de reglas o contratos.
Calidad de Parches
Todo parche a los 6 documentos fundacionales debe cumplir estos seis criterios antes de aplicarse — si falla alguno, se reescribe antes de solicitar APROBAR_WRITE:
1. Coherencia transversal — no puede contradecir ni duplicar una definición ya existente en Kernel, System Prompt, Career Canon o Aliases.
1. Concreción de títulos — el título descriptivo de cualquier nodo debe ser ilustrativo y concreto (una palabra o frase corta que nombra el contenido), no una construcción semántica compuesta o explicativa. Ejemplo de dirección: preferir el nombre directo del tema sobre una paráfrasis de su función.
Un parche que pasa estos seis filtros no se distingue, seis meses después, del texto que rodeaba su punto de inserción original.
Reglas de Oro
Base: KERNEL:CV-GOLDEN-RULES.
SLA de Latencia
Reglas de Oro CV
Las Reglas de Oro (KERNEL:CV-GOLDEN-RULES) son restricciones de arquitectura, no preferencias. Viven íntegras en el Kernel — esta sección es un índice de navegación, no una copia.
CANON:POSITIONING define 4 modos de posicionamiento para CV-B. Esta sección resuelve el gap operativo: con qué criterio elegir uno.
Contrato de Bloque
Cada slot del .md debe seguir el patrón estricto marcado en el Golden Skeleton: encabezado ###### figma_text_id(KEY) seguido del contenido con negrita donde aplique. Sin esa cabecera exacta (nivel de heading correcto seguido del KEY entre paréntesis), el bloque no se detecta — el síntoma es "0 nodos actualizados" sin error explícito.
Cuatro fases, en orden:
1. Detección — ui.html revisa si el texto contiene figma_text_id; si no, intenta JSON.parse.
1. Parsing — regex extrae cada bloque, detecta KEYs duplicadas (detiene el envío si las hay) y sanitiza contenido.
1. Escritura — reemplazo total del texto del nodo (node.characters), con negrita quirúrgica por rango si aplica.
Sanitización de Contenido
Regla de Reemplazo Total
La inyección es node.characters = item.text — reemplazo total, no merge ni append. Cualquier edición manual hecha directamente en Figma sobre esos nodos se sobrescribe sin aviso ni backup en el siguiente sync. La única fuente de verdad post-sync es el .md pegado, no el estado previo del lienzo.
KERNEL:SCHEMA-001 define ownership exclusivo por campo. Esta tabla es índice de consulta rápida — el contrato completo (reglas de excepción, mapeo de vocabulario) vive en el Kernel.
Rol · Marca · Source_Type · URL · Status · Positioning_Mode · Prioridad · Holding · JD · NAD · layer · hash
Score · Gate_Decision · VM_Scope · Role_Class · Match · Next_Action · Fetch · Fuente
Next_Action: select (10 valores operativos). Ver KERNEL:SCHEMA-008.
Pesos de Score/VM_Scope: viven en profile_config.yaml, propiedad de Python — el Manual no reproduce los valores numéricos porque son deuda de implementación, no contrato documental (ver KERNEL:GATE-DECISION-002). Un operador que necesite ajustar pesos debe editar ese archivo directamente, no este documento.
Procedimiento de sanity check para validar que ningún documento fundacional haya sufrido pérdida silenciosa de contenido tras operaciones de sincronización, edición masiva o fallo en scripts de inyección.
1. Ejecución básica de verificación (read-only):
Casos de uso clave:
layer_1_run.py
feed_processor.pyQué hace: Ingiere un JSON de feed (L1/L2/L3) y crea/actualiza registros en el Tracker. Hardening PR #10: (1) _extract_text_prop consolidado como helper único a nivel de módulo (title / rich_text / select / url, firma con default) — elimina las dos copias anidadas que causaban NameError en _check_historical_rejected_status y TypeError en el fingerprint path con location_prop seteado; (2) guard should_mutate_existing_page() aplica el predicado de Status compartido (profile_fit.should_annotate_existing) antes de escribir Dedup_Flag o upgrade de layer sobre un registro existente (ver KERNEL:GATE-DECISION-007 y MANUAL:DATA-MANAGEMENT § Dedup); (3) comentario GAP-03 actualizado: este write path es Class A por construcción vía NotionSchema, el guard para actores no-Python vive en dashboard_notion.py (class_b_guard) — FX-1 cerrado.
Flags:
| Flag | Caso de uso |
| --- | --- |
| --file <ruta> (requerido) | El Markdown exportado desde Notion que quieres convertir. |
| --out <ruta> | Default es /tmp/archivo_changelog_toggled.md — especifica otra ruta si quieres conservarlo fuera de /tmp. |
| --dry-run | Ver las primeras 80 líneas convertidas sin escribir el archivo completo. |
| --apply | ⚠️ No tiene efecto real — el archivo se escribe siempre que --dry-run esté ausente; este flag es vestigial. |
generate_entity_index_v2.pyQué hace: Reconstruye el índice de entidades (entity_index_v2.json), el grafo de relaciones y los backlinks — la base de datos interna que usa vantage.py ask/query.
Flags:
apply_hyperlinks_notion.pyQué hace: Aplica el sistema de cross-reference hyperlinks entre documentos fundacionales (PATCH de bloques en Notion).
Flags:
Flags:
cross_tracker_match.pyQué hace: Busca coincidencias entre el Tracker activo y el Archivo Tracker por regla marca+rol.
dedup_opportunities.py
Flags:
Variables de entorno (tuning silencioso):
backfill_class_a.pyQué hace: Backfill de campos Class A (layer, hash, Prioridad) en registros existentes del Tracker. Contiene su propio hack de parsing local para leer propiedades top-level del objeto Notion (mismo patrón de riesgo que created_time en priority_logic.py, ver KERNEL:TRIGGER-002) — depende de la estructura de chunks del objeto recibido, no de un parser compartido. Fix PR #10: infer_layer() retornaba "L3" para Notas con "layer: l2" — corregido a "L2" (un backfill ya no puede escribir mal la procedencia de un registro L2); branch L1/L2/L3 + default cubierto por test.
backfill_next_action_select.pyQué hace: Migra el campo Next_Action de texto libre a select tipado. — MOVIDO a Archive/Legacy_Scripts/ (saneamiento v9.21.x)
Flags:
verify_versions.py (alias vversions)Qué hace: Herramienta central de verificación — versión de los 9 fundacionales, gap-report de scripts/skills, e integridad de longitud documental.
Flags:
clean_script_library_links.pyQué hace: Limpia valores de URL corruptos (http:// mal formados) en Script Library.
Flags:
Uso: Sin flags CLI propios — se corre directo, solo requiere NOTION_TOKEN/NOTION_API_KEY en el entorno. — MOVIDO a Archive/Legacy_Scripts/ (saneamiento v9.21.x)
notion_utils.pyQué hace: Cliente HTTP compartido para todas las llamadas a Notion — caché, rate limiting, reintentos. No se invoca directo salvo para diagnóstico.
Uso: Sin flags — se corre directo (via vantage-health.sh en Raycast). Exit code 0 = sano, 1 = issues encontrados (no fallo fatal).
feedback_loop.pyQué hace: Calcula métricas de efectividad y conversión sobre el Tracker.
Flags:
Uso: Sin flags CLI — se corre directo. Requiere NOTION_TOKEN.
Caso de uso: Cuando el resumen simple no te dice si el problema es concentración en un rango específico (ej. muchas vacantes atoradas en 55-60) — el detalle por bucket sí lo muestra.
Uso: Sin flags CLI — se corre directo. Requiere NOTION_TOKEN.
⚠️ Hallazgo real (no corregido, solo documentado): vprint.sh invoca python3 .../VANTAGE/vprint.py — ruta incompleta, le falta Layer_1/scripts/. El script real vive en Layer_1/scripts/vprint.py, no en la raíz de VANTAGE. Si el wrapper falla con "No such file or directory", esta es la causa.
---
Módulos Compartidos (sin CLI propia — se importan, no se ejecutan solos)
> Estos 7 no son "scripts" en el sentido operativo — son librerías internas que otros scripts importan. --new-scripts los detecta igual porque no distingue tipo de archivo; se documentan aquí por completitud, sin tabla de flags porque no tienen ninguno.
Por qué te sirve saberlo: si un registro se queda "atorado" sin actualizar pese a nueva información, este es el módulo que decide si eso es correcto (protección de terminalidad) o un bug.
priority_logic.pyQué hace: Lógica de Prioridad (Class A) compartida — extraída de backfill_class_a.py para romper un import circular con layer_1_run.py.
Quién lo consume: pipeline principal, scripts de cleanup, y feed_processor.py (guard de anotación en dedup).
Por qué te sirve saberlo: si vantage.py ask devuelve relaciones incorrectas o desactualizadas entre entidades, corre vantage.py sync para regenerar los JSON que este módulo lee — no es un bug del módulo en sí.
vantage_id_rules.pyQué hace: Módulo único de reglas de detección DEF/REF/heading/boundary para todo el ecosistema de IDs PREFIX:KEY — consolida lógica que antes vivía duplicada (y desincronizada) en 4 scripts distintos (generate_census.py, generate_id_inventory.py, apply_hyperlinks_notion.py, normalize_heading_ids.py).
### 22.1b MANUAL:SCRIPT-GLOSSARY-L1-TOOLS
Utilidades y Herramientas de Sesión
agent_api.pyQué hace: Capa de consulta en lenguaje natural sobre el índice de entidades — es el motor real detrás de vantage.py ask.
Uso: python3 agent_api.py "texto de consulta" — un solo argumento posicional, entre comillas.
Caso de uso: Ejemplos reales soportados: 'show active roles', 'show archived history', 'show bugs', 'find candidates', 'compare TRACKER:H_xxx TRACKER:H_yyy'.
clean_caches.py (y su wrapper Raycast clean-caches-raycast.sh)Qué hace: Limpieza de cachés de aplicaciones en Mac (Chrome, Safari, Firefox, Edge, y otras) — no toca sesión/login ni LocalStorage, solo caché regenerable. Reporta espacio liberado por ruta.
Uso: Sin flags — se corre directo.
Caso de uso: Tu Mac se siente lento o con poco espacio y quieres liberar caché de navegadores sin riesgo de cerrar sesiones activas.
pipeline_recovery.pyQué hace: Manejo de fallos y "resume operations" del pipeline — guarda checkpoints (save_checkpoint) para poder retomar una corrida de L1 que se interrumpió a medias.
Uso: Requiere NOTION_TOKEN.
Caso de uso: Si layer_1_run.py se cae a la mitad de un batch grande (ej. por rate limit de Notion), este módulo es el que permite retomar desde el checkpoint en vez de reprocesar todo desde cero.
profile_evolution.pyQué hace: Maneja cambios en la configuración/perfil del sistema (config/profile_config.yaml) — crea config default si no existe, actualiza progresión de perfil.
Uso: python3 profile_evolution.py — sin flags, interactivo, requiere pyyaml instalado.
Caso de uso: Cuando cambia tu rol objetivo o etapa de carrera (ej. de "Coordinador" a "Dirección") y quieres que el sistema actualice su configuración de perfil de forma guiada en vez de editar el YAML a mano.
weekly_prompt_assembler.pyQué hace: Arma los prompts semanales para los motores externos (L2) — trae Prompt A + Wrappers + Prompt E desde Notion, sustituye la fecha del día, concatena (A + Wrapper) y escribe archivos .md listos para pegar en Gemini/Grok/Perplexity/You.com.
Uso: Sin flags — se corre directo, genera archivos con fecha en el nombre (Prompt_{motor}_{fecha}.md).
Caso de uso: Es el primer paso de tu ciclo semanal de L2 — antes de ir a copiar/pegar prompts a mano en cada motor externo, esto te los pre-arma con la fecha correcta ya sustituida.
patch_vsync_doc.pyQué hace: Patcher de un solo uso (ya ejecutado) que separó la entrada cheat_sheet de vsync_doc.py en dos entradas independientes (aliases y change_log) — mismo patrón que patch_new_scripts.py (backup automático + validación de sintaxis antes de escribir).
Uso: python3 patch_vsync_doc.py — sin flags. Es idempotente por diseño de patcher (aunque no verifiqué si tiene el mismo guard explícito).
Nota operativa: Como es un patcher de una sola aplicación histórica (ya corrido, ver ALIASES/CHANGE_LOG separados en tu vsync_doc.py actual), no debería necesitar correrse de nuevo. patch_vsync_doc.py y patch_new_scripts.py fueron MOVIDOS a Archive/Legacy_Scripts/ (saneamiento v9.21.x) — --new-scripts ya no debería detectarlos como pendientes.
⚠️ Hallazgo real — extract_score_distribution.py: este script parece ser un borrador abandonado, no una herramienta funcional. El propio código trae comentarios como "Simulación: voy a asumir que necesito procesar los datos reales" y "Por ahora, voy a mostrar el formato de análisis esperado" — usa datos de muestra hardcodeados (sample_data), no consulta Notion. extract_score_distribution.py parece ser una versión temprana/incompleta de extract_scores.py (que sí funciona). Documentado como hallazgo, no corregido — decide tú si vale la pena eliminarlo del árbol para que deje de aparecer en cada gap report. — MOVIDO a Archive/Legacy_Scripts/ (saneamiento v9.21.x)
---
### 22.3 MANUAL:SCRIPT-GLOSSARY-L4
Layer 4 — Version Control & Sync Documental
vdoc.pyQué hace: Wrapper de orquestación — decide dirección de sync (Notion↔local) y dispara vsync_doc.py + git_sync.py.
Uso (tokens posicionales, no flags tradicionales):
| Token | Caso de uso |
| --- | --- |
| dry | Preview de lo que haría en modo auto, sin escribir nada. Úsalo antes de cualquier sync si no estás seguro de qué documento cambió más recientemente. |
| notion | Fuerzas Notion→local (pide confirmación). Úsalo si sabes que editaste en Notion y el local está desactualizado. |
| local | Fuerzas local→Notion (PATCH puntual). ⚠️ Nota real: pese a que el resto del sistema pide confirmación para direcciones forzadas, local tiene una excepción temporal en el código y NO pide confirmación — ejecuta directo. |
| auto | Deja que el script decida por hash cuál lado está más reciente. |
| <documento> (ej. kernel, brief) | Restringe el sync a un solo documento en vez de los 7. |
vsync_doc.pyQué hace: Motor real de sincronización documento-por-documento (invocado por vdoc.py, no directo normalmente).
Flags:
| Flag | Caso de uso |
| --- | --- |
| --direction {notion,auto,local} | Igual lógica que los tokens de vdoc.py, pero si necesitas invocar el motor directo (debugging). |
| --dry-run | Preview sin aplicar ni auto-commit. |
| --doc {kernel,system_prompt,career_canon,manual,aliases,change_log,brief} | Nota real: maneja 7 documentos, incluyendo brief — aunque la documentación textual del Manual describe un catálogo de 6. |
git_sync.pyQué hace: Genera commit y push del árbol VANTAGE hacia GitHub.
Flags:
| Flag | Caso de uso |
| --- | --- |
| --dry | Antes de un push automático, revisa qué archivos entrarían al commit sin ejecutar nada. |
vsum.pyQué hace: Genera resúmenes de archivos Markdown/texto vía Groq o Gemini.
Flags:
| Flag | Caso de uso |
| --- | --- |
| file (posicional, requerido) | Ruta al archivo local a resumir. ⚠️ Nota real: pese a lo que sugiere cualquier doc sobre "Claude Share URLs", el código solo acepta rutas de archivo local — una URL fallará. |
| -o/--output <ruta> | Si quieres guardar el resumen en vez de verlo en pantalla — útil para encadenar con otro proceso. |
| -m/--model {groq,gemini} | Si Groq está teniendo rate limits, cambia manualmente a Gemini con este flag en vez de esperar el fallback automático. |
| --notion | ⚠️ Flag vestigial — se parsea pero no tiene ningún efecto en el código actual. No lo uses esperando que cree una página en Notion. |
---
### 22.4 MANUAL:SCRIPT-GLOSSARY-DASHBOARD
Dashboard — Servidor Local de Visualización
dashboard_start.sh → dashboard_server.pyQué hace: Levanta el servidor local del Dashboard, corre smoke test, abre el navegador.
Uso: Sin flags — un solo comando hace todo el ciclo (start → healthcheck → smoke test → abrir browser). Si el smoke test falla, no abre el navegador y te avisa por notificación de sistema.
layer_1_run_dash.pyQué hace: Variante de layer_1_run.py adaptada para ser invocada desde el Dashboard web en vez de Terminal.
Uso: Sin flags CLI propios — se invoca vía las rutas HTTP del Dashboard, no directo.
---
### 22.4a MANUAL:SCRIPT-GLOSSARY-DASHBOARD-MODULES
Módulos Internos del Dashboard (sin CLI — arquitectura, no scripts ejecutables)
> Al igual que los módulos de 22.1a, estos 5 no tienen flags porque no se ejecutan como scripts sueltos — son la arquitectura interna del servidor Flask del Dashboard. Documentados por su rol, no por CLI.
| Módulo | Rol |
| --- | --- |
| dashboard_config.py | Carga config/dashboard.env, expone NOTION_TOKEN, DATABASE_ID (desde NOTION_DB_OPPORTUNITIES) y DB_PATH (SQLite local del Dashboard) al resto de módulos. |
| dashboard_db.py | Capa de acceso a la base SQLite local (dashboard_instances.db) — inicialización de schema y operaciones CRUD internas del Dashboard (no confundir con el Tracker de Notion). |
| dashboard_notion.py | Cliente Notion del Dashboard — reutiliza NOTION_TOKEN/DATABASE_ID de dashboard_config.py, importa txt() de layer_1_run.py para parseo de propiedades. |
| dashboard_routes.py | Rutas HTTP Flask (jsonify/request) — endpoints del Dashboard, consume dashboard_notion.py para las queries reales (ej. query_blocked_vacancies, write_patch_to_notion). |
| dashboard_validation.py | Reutiliza validación core del pipeline (validate_url_pre_ingestion, calculate_score_v6, get_vm_scope, get_role_class, gate) directamente de layer_1_run.py — garantiza que el Dashboard aplique exactamente la misma lógica de scoring/gate que el pipeline CLI, no una copia paralela. |
smoke_dashboard.pyQué hace: Smoke test del servidor Dashboard corriendo en http://127.0.0.1:8000 — verifica /health y /blocked-vacancies, imprime SMOKE PASSED/SMOKE FAILED.
Uso: Sin flags — requiere que el Dashboard ya esté corriendo localmente (lo invoca dashboard_start.sh como parte de su ciclo de arranque).
Caso de uso: Si el Dashboard se ve raro tras un cambio de código, corre esto antes de asumir que es un bug visual — confirma si el backend responde correctamente primero.
---
### 22.5 MANUAL:SCRIPT-GLOSSARY-RAYCAST
Raycast — Atajos de Un Click
> Estos scripts son wrappers delgados — su único trabajo es invocar el script real de la capa correspondiente con notificaciones de sistema (sonido de éxito/error). No tienen flags propios más allá de lo que reenvían.
| Wrapper Raycast | Invoca | Nota operativa |
| --- | --- | --- |
| vantage-health.sh | health_check.py | Sin flags. |
| vantage-vl1.sh → layer_1_wrapper.sh | layer_1_pipeline.sh | Si no le pasas argumentos, auto-detecta el feed JSON más reciente en Layer_1/feeds/. |
| vantage-vl3.sh → layer_3_mail.sh | layer_3_mail.py | Sin flags — valida que exista .venv y config/layer_3.env antes de correr. |
| vantage-dedup.sh / vantage-opport-dedup.sh | dedup_opportunities.py (sin args) | ⚠️ No expone --clear — para limpiar un flag puntual necesitas Terminal directo. |
| vantage-vgit.sh → git_sync_wrapper.sh | git_sync.py | Reenvía "$@" — sí puedes pasarle --dry vía Raycast si tu atajo lo permite. Loguea cada corrida en /tmp/vantage_l4_gitsync.log. |
| vantage-vdoc-dry.sh | vdoc.py dry | Atajo directo al modo preview. |
| vantage-vdoc-notion.sh | vdoc.py notion | Atajo directo al modo forzado Notion→local (pide confirmación). |
| vantage-vd.sh | vdoc.py (modo según config del atajo) | Revisa el contenido del script si necesitas saber qué dirección dispara por default. |
| vantage-census.sh | generate_census.py | Sin --debug-id expuesto — census completo únicamente. |
| vantage-versions-bootstrap.sh | verify_versions.py --bootstrap |  |
| vantage-versions-sync.sh | verify_versions.py --sync |  |
| vantage-versions-scripts-gap.sh | verify_versions.py --scripts |  |
| vantage-hyperlinks-dry.sh | apply_hyperlinks_notion.py --all (sin --apply) |  |
| vantage-hyperlinks-apply.sh | apply_hyperlinks_notion.py --all --apply | ⚠️ Escritura real de un solo click — sin gate de confirmación adicional del lado Raycast. |
| vantage-status.sh | status_report.py | Sin flags. |
| vantage-sync.sh | (revisar contenido — probablemente alias de vdoc.py auto o vsync_doc.py) | Pendiente de confirmación directa si se usa activamente. |
| clean-caches-raycast.sh | clean_caches.sh | Limpieza de cachés de apps (Chrome, Figma, Notion, etc.) — no toca sesión/login, solo caché regenerable. |
---
### 22.6 MANUAL:SCRIPT-GLOSSARY-XREF
Matriz de Transición de Estados — Ciclo de Vida del Script
Vista tabular consolidada, mismo patrón que [KERNEL:GATE-DECISION-011] (Matriz de Transición de vacantes) — aplicada aquí al ciclo de vida de un script dentro del sistema de documentación (disco → Glosario → Script Library). Referencia canónica para el skill vantage-sync-script-glossary (punto E) y para verify_versions.py --new-scripts (punto D) — no reemplaza la descripción en prosa de cada script, la complementa con indexación de estados.
| Estado Origen | Evento / Trigger | Guard / Regla | Estado Destino | Componente | Efecto |
| --- | --- | --- | --- | --- | --- |
| [ENTRY] | Commit de archivo .py/.sh nuevo en árbol activo (Layer_1/3/4, Dashboard, Raycast) | No excluido por EXCLUDED_DIR_NAMES/EXCLUDED_FILE_PREFIXES | NO_DOCUMENTADO | Filesystem (git) | Ninguno — script existe, cero registro |
| NO_DOCUMENTADO | Operador corre vversions --new-scripts | Nombre de archivo ausente en SCRIPT_GLOSSARY_PATH (local, sin Notion) | DETECTADO | Python (local, read-only) | Exit code 1 — reporte en stdout, sin escritura |
| DETECTADO | Claude invoca vantage-sync-script-glossary | Lectura del script fuente (grep de flags/env vars) + DRY RUN de ambas entradas propuestas | PROPUESTO | Claude (AI Component) | Ninguno aún — solo preview, sin escritura |
| PROPUESTO | Operador confirma APROBAR_WRITE | Escritura dual atómica: entrada en Glosario (Notion, página Manual) + fila en Script Library (Notion DB) | DOCUMENTADO | Claude + Notion MCP | Página Manual actualizada; fila Script Library creada; write-back verification en ambos |
| PROPUESTO | Operador rechaza o no confirma | Sin APROBAR_WRITE | DETECTADO | Humano | Sin cambio — permanece pendiente para próxima corrida |
| DOCUMENTADO | Edición posterior del script (nuevo flag agregado) | Diff entre flags reales (grep) y flags documentados en Glosario | DESACTUALIZADO | Python + Claude (detección manual o futura extensión de --new-scripts) | Marcado ⚠️ en Glosario — no auto-corregido, requiere revisión igual que hallazgos de auditoría (ver lista al final de esta sección) |
| DOCUMENTADO | Script renombrado con prefijo DEPRECATED_ o movido a carpeta excluida | EXCLUDED_FILE_PREFIXES / EXCLUDED_DIR_NAMES aplica en el próximo scan_committed_assets() | HUÉRFANO_GLOSARIO | Filesystem (git) + Python (detección pasiva) | Ninguno automático — entrada en Glosario/Script Library queda obsoleta, sin flag de alerta hasta auditoría manual |
| DOCUMENTADO (Script Library) | Fila marcada "Activo" en Notion sin archivo correspondiente en disco | vversions --scripts (ya existente, vía Notion) | HUÉRFANO_NOTION | Python (read-only) + Notion | Reportado en gap report — remediación manual, mismo patrón que hoy |
Reglas de mantenimiento derivadas de la matriz:
- Todo script nuevo agregado al árbol activo transita [ENTRY] → NO_DOCUMENTADO → DETECTADO → PROPUESTO → DOCUMENTADO — nunca salta directo a DOCUMENTADO sin pasar por DRY RUN + APROBAR_WRITE (mismo invariante que [KERNEL:DATA-FLOW]).
- El estado DOCUMENTADO es doble — requiere presencia simultánea en Glosario y Script Library. Un script en solo uno de los dos no es DOCUMENTADO, es un estado intermedio no listado arriba porque hoy no debería poder ocurrir (la escritura de vantage-sync-script-glossary es atómica en ambos destinos).
- DESACTUALIZADO y HUÉRFANO_* no tienen remediación automática por diseño — son señales para auditoría del operador, igual que los hallazgos ⚠️ ya documentados en este Glosario. Documentar la discrepancia, no "arreglarla" sin instrucción explícita.
- Esta matriz es la fuente de verdad para el diseño del skill vantage-sync-script-glossary — cualquier cambio a su lógica de transición pasa por vantage-documentacion-transversal-propuesta sobre este nodo (MANUAL:SCRIPT-GLOSSARY-XREF), no por edición directa del skill.
Hallazgos de discrepancia activos (heredados de auditoría arena.ia, verificados contra código fuente):
1. layer_1_pipeline.sh batch no reenvía -execute a batch_operations.py — siempre corre en modo definido por el propio script.
1. vdoc.py local no pide confirmación pese a que el resto de direcciones forzadas sí (excepción temporal marcada en el propio código).
1. vsync_doc.py --doc maneja 7 documentos (incluye brief), no 6.
1. dedup_opportunities.py --clear requiere posición fija en sys.argv, no es un flag argparse real.
1. vsum.py --notion se parsea pero no tiene efecto — vestigial.
1. cross_tracker_match.py --dry-run no puede desactivarse — default True sin opuesto.
1. GROQ_MAX_EMAILS_PER_RUN: Manual/Aliases citan valores distintos entre sí; código usa 10. — RESUELTO (v9.21.x, saneamiento estructural): Manual §12 alineado a 10 correos.
---
## 23 MANUAL:SKILL-GLOSSARY
Glosario de Skills — Referencia Operativa en Humano
> Propósito: Traducir cada skill de Claude (/mnt/skills/user/) a lenguaje operativo — qué hace, qué la dispara, si requiere gate de escritura, y su convención de anuncio. Contraparte de MANUAL:SCRIPT-GLOSSARY (§22), aplicada a skills en vez de scripts. La Skill Library (Notion DB) es su índice corto y estructurado; se referencian entre sí.
---
### 23.1 MANUAL:SKILL-GLOSSARY-CORE
Pipeline CV y Ciclo de Sesión
| Skill | Propósito | Trigger | Gate | Anuncio |
| --- | --- | --- | --- | --- |
| vantage-session-open | Bootstrap de sesión (Ledger→Contexto) | Inicio de sesión / invocación explícita | ❌ (housekeeping, exento de APROBAR_WRITE) | SESSION-OPENING… / SESSION-OPENED |
| vantage-session-close | Cierre de sesión (Changelog+Ledger+Sync) | Fin de sesión / invocación explícita | ✅ | CLOSING SESSION… / SESSION CLOSED |
| vantage-cv-a | Analiza JD/URL, produce HANDOFF con Positioning Mode | CV-A [URL/JD] | ❌ | No especificado (gap, ver 23.5) |
| vantage-cv-b | Construye CV final con Figma Tags desde HANDOFF | CV-B [HANDOFF] | ✅ | No especificado (gap, ver 23.5) |
| vantage-qa | Audita PDF de CV final, veredicto GO/NO-GO | QA [PDF] | ❌ | No especificado (gap, ver 23.5) |
| vantage-present-handoff | Handoff compacto de sesión para continuidad | Fin de sesión / cambio de chat | ❌ | HANDING OFF… / HANDOFF DELIVERED |
---
### 23.2 MANUAL:SKILL-GLOSSARY-HOUSEKEEPING
Sincronización y Mantenimiento Documental
| Skill | Propósito | Trigger | Gate | Anuncio |
| --- | --- | --- | --- | --- |
| vantage-sync-script-library | Sincroniza Script Library Notion vs disco | "sincronizar Script Library" / gap report | ✅ | SYNCING SCRIPT LIBRARY… / SCRIPT LIBRARY SYNCED |
| vantage-sync-skill-library | Sincroniza Skill Library Notion vs disco .skill | "sincronizar Skill Library" / gap report | ✅ | SYNCING SKILL LIBRARY… / SKILL LIBRARY SYNCED |
| vantage-sync-assets | Orquesta las 6 sync de Libraries/Glossaries/Census/Hyperlinks en orden fijo | "sync assets" / "sincronizar assets" | ✅ | SYNCING ASSETS… / ASSETS SYNCED |
| vantage-sync-script-glossary | Sincroniza apéndice §22 vs disco | "sincronizar Script Glossary" / gap --new-scripts | ✅ | No especificado (gap, ver 23.5) |
| vantage-sync-census-spec | Da de alta IDs huérfanos en CENSUS_SPEC | "sincronizar Census Spec" / huérfanos en vcensus | ✅ | SYNCING CENSUS SPEC… / CENSUS SPEC SYNCED |
| vantage-hyperlink-loop | Ciclo Census→Hyperlinks→Sync | Housekeeping de navegación / invocación explícita | ✅ | REGENERATING NAVIGATION LOOP… / NAVIGATION LOOP FINISHED |
| vantage-housekeeping-tracker | Orquesta housekeeping de trackers (Bug/Task → VANTAGE Tracker → Change Log) en orden fijo | "housekeeping trackers" / "tidy trackers" | ✅ | HOUSEKEEPING TRACKERS… / TRACKERS HOUSEKEPT |
| vantage-housekeeping-archive | Consolida detección→marcado→verificación de candidatos a archivar (Dedup_Flag/Next_Action) en un solo procedimiento, absorbiendo el ciclo antes cubierto por escaneo visual (ver KERNEL:GATE-DECISION-007) | "housekeeping archive" / candidatos detectados vía Dedup_Flag/Next_Action | ✅ | ARCHIVING HOUSEKEEPING… / ARCHIVE HOUSEKEPT |
| vantage-create-bug-task | Crea ticket en Bug/Task Tracker | Reporte de defecto o tarea pendiente | ✅ | LOGGING TICKET… / TICKET LOGGED |
| vantage-tidy-bug-task-tracker | Marca tickets resueltos como Archivar=True | Resolución directa o vía Change Log | ✅ | TIDYING TRACKER… / TRACKER TIDIED |
| vantage-tidy-opportunities-tracker | Marca duplicados/expiradas en VANTAGE Tracker | Housekeeping de vacantes | ✅ | TIDYING OPPORTUNITIES… / OPPORTUNITIES TIDIED |
| vantage-tidy-changelog | Recorta Change Log a últimas 10 entradas | Exceso >10 entradas / housekeeping | ✅ | TIDYING CHANGELOG… / CHANGELOG TIDIED |
| vantage-documentacion-transversal-propuesta | Mapea nodos fundacionales afectados, sin escribir | "propuesta de documentación transversal" / gap estructural | ❌ | BEGINNING DOCUMENTATION MAPPING… / cierre no especificado (gap, ver 23.5) |
| vantage-documentacion-transversal-implementacion | Ejecuta escritura de documentación ya autorizada | Post-APROBAR_WRITE de propuesta | ✅ | RESUMING DOCUMENTATION — IMPLEMENTATION PHASE… / DOCUMENTATION FINISHED |
---
### 23.3 MANUAL:SKILL-GLOSSARY-AUDIT
Auditoría y Continuidad
| Skill | Propósito | Trigger | Gate | Anuncio |
| --- | --- | --- | --- | --- |
| vantage-audit-navigation-brief | [DEPRECATED] Funcionalidad integrada en vantage-documentacion-transversal-propuesta | N/A — usar vantage-documentacion-transversal-propuesta | ❌ (solo lectura, nunca escribe Notion) | No aplica (deprecada) |
| extract-learnings | [DEPRECATED] Actividad post-mortem esporádica, no skill operativa recurrente | Post-fumble evitable o creación de skill nueva | ❌ | No aplica (housekeeping interno) |
| vantage-skill-updater | Evalúa compliance de skills contra KERNEL requirements, propone actualizaciones | "actualizar skills con requisitos VANTAGE" / "evaluar compliance de skills" | ✅ | BEGINNING SKILL EVALUATION… / SKILL EVALUATION COMPLETE |
---
### 23.4 MANUAL:SKILL-GLOSSARY-STYLE
Estilos de Escritura y Generación (activación por invocación explícita, no por trigger operativo)
| Skill | Propósito | Trigger |
| --- | --- | --- |
| critico-pensante-style | Reflexivo/analítico, cuestiona contradicciones | Invocación exacta por nombre |
| retail-auditor-style | Auditoría sistemática de VM/retail multi-tienda | Invocación exacta por nombre |
| socio-estrategico-style | Directo/eficiente para VM, sin rodeos | Invocación exacta por nombre |
| corporate-communication-style | Cartas de recomendación formales | Invocación exacta por nombre |
| prompt-master | Genera prompts optimizados para otras IAs | Pedido explícito de prompt para IA/Cursor/Midjourney/etc. |
| tailored-resume-generator | Genera CVs adaptados a una vacante específica | Solicitud de CV a medida + JD |
---
### 23.5 MANUAL:SKILL-GLOSSARY-XREF
Gaps Abiertos (hallazgos, no corregidos en esta pasada)
- Capa null en 24/25 filas de Skill Library (Notion) — campo definido en schema, prácticamente sin uso.
- Anuncio no especificado en 5 skills operativas que deberían tenerlo por KERNEL:DOCUMENTATION-005:
vantage-cv-a, vantage-cv-b, vantage-qa, vantage-sync-script-glossary, y el cierre de vantage-documentacion-transversal-propuesta.
