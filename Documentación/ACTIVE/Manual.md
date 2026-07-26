# V | MANUAL

Archivos: Layer_4/scripts/git_sync.py · Layer_4/wrappers/git_sync_wrapper.sh · ~/Library/LaunchAgents/com.vantage.gitsync.plist
Extensión reciente — Skills Distribution: vgit/git_sync.py además detecta cambios en /skills/ (archivos .skill nuevos o modificados) y, como parte del mismo commit+push, regenera index.json. No es un flujo separado de mantenimiento — es el mismo mecanismo de auto-sync ya descrito arriba, extendido a un directorio adicional. Esto es lo que permite que Claude Desktop (MCP filesystem local sobre /skills/) y Devin Desktop (vía GitHub Pages en main) lean siempre la misma versión sin paso de sincronización manual entre ambos consumidores.
vdoc — Document Layer Sync
Sincroniza los 6 documentos fundacionales (Kernel · System Prompt · Career Canon · Manual · Aliases · Change Log) entre Notion y ACTIVE/ en disco, y al terminar encadena un git_sync automático para que el commit quede reflejado en GitHub sin un paso adicional.
Tres direcciones posibles:
- vdoc auto — compara la fecha de modificación de cada documento (local vs. Notion) y sincroniza en el sentido que corresponda, documento por documento. Es el modo por defecto y el más seguro para uso diario: nunca sobreescribe algo más reciente con algo más viejo.
- vdoc notion — fuerza Notion → local para los 6 documentos, sin comparar fechas. Úsalo solo si sabes que Notion tiene la versión correcta y quieres descartar cualquier cambio local.
- vdoc local — fuerza local → Notion para los 6 documentos, sin comparar fechas. Úsalo solo si editaste los .md directamente en disco (offline) y quieres que Notion adopte esa versión.
Como notion y local sobreescriben sin comparar fechas, ambos son operaciones forzadas: antes de ejecutar nada, vdoc te muestra automáticamente un preview (equivalente a --dry-run) de lo que va a hacer, y te pide confirmación explícita en terminal (s para continuar, cualquier otra tecla cancela). Si por alguna razón corres el comando sin una terminal interactiva disponible, el script no asume que confirmaste — cancela por seguridad y no escribe nada. vdoc auto nunca pide esta confirmación porque nunca sobreescribe algo más reciente.
Modificador dry — se combina con cualquiera de los tres comandos anteriores y con cualquier documento específico, en cualquier orden, y siempre gana: nunca escribe en Notion, en disco ni hace commit, sin importar qué más hayas escrito en la misma línea.
- vdoc dry — preview de auto (equivalente a vdoc auto dry)
- vdoc notion dry — preview de lo que haría vdoc notion, sin ejecutar la escritura forzada
- vdoc local dry — preview de lo que haría vdoc local
- vdoc kernel dry — preview de solo Kernel en modo auto
Recomendación operativa: corre siempre la variante dry primero cuando no estés seguro de qué dirección va a ganar — te cuesta segundos y evita sorpresas, especialmente antes de un notion o local forzado.
Sync quirúrgico por documento — cualquiera de los 6 nombres puede pasarse solo o combinado con dirección/dry: vdoc kernel · vdoc system_prompt · vdoc career_canon · vdoc manual · vdoc aliases · vdoc change_log. Sin dirección explícita, cada uno corre en modo auto (gana el más reciente) solo para ese documento — los otros 5 no se tocan. Se puede combinar con notion/local (ej. vdoc notion kernel fuerza solo Kernel Notion→local) y con dry (ej. vdoc kernel dry).
Archivos: Layer_4/scripts/vsync_doc.py (motor de sync) · Layer_4/scripts/vdoc.py (wrapper de comandos, el que invocas por alias) · reutiliza .venv de Layer_1.
Ver también §12 — Troubleshooting, entrada “vsync_doc.py falla con error blocks.children.list() returned None”.
---
## 08.2 MANUAL:DASHBOARD-001
## Martes — Recuperación y Dashboard
Antes de avanzar al miércoles, este es el momento de resolver lo que quedó bloqueado el lunes: REVIEW_NEEDED · BLOCKED recuperables · NADs vencidas. Las vacantes que recuperes aquí son las que estarán disponibles en Ready-to-Apply para trabajar mañana.
Si el bloqueo es por un campo Class A corregible, usa el Dashboard: Proponer Patch → Validar → Aceptar. No uses el Dashboard para forzar un CREATE en vacantes que no cumplen score — úsalo solo para corregir datos erróneos. (Recuerda de §2: un Gate BLOCKED no es un error del sistema a “saltarse”, es una vacante cuyos datos de entrada tienen un problema identificable y corregible.)
Es una sola herramienta (dashboard.html + dashboard_server.py :8000), no hay pestañas ni vistas separadas. La pantalla es un panel de recuperación de vacantes bloqueadas, con una tira de estado del pipeline (L1 → RT-1 → Notion → Mail) como indicador visual — no una vista de navegación distinta. Comparte la infraestructura visual (vantage-tokens.css, vantage-theme.js) con el Checklist, descrita en §7.
Archivos: Dashboard/dashboard.html · Dashboard/scripts/dashboard_server.py.
Abrir el Dashboard: ejecuta en terminal:
```bash
vd
```
El wrapper dashboard_start.sh arranca el servidor Flask en http://127.0.0.1:8000 (accesible también vía Tailscale desde otros dispositivos), ejecuta un smoke test automático y abre dashboard.html en el navegador. Output esperado en terminal: SMOKE PASSED — abriendo dashboard. Si el smoke falla, emite notificación sonora de error (Basso) y no abre la UI. El indicador “BACKEND OK/OFFLINE” en la esquina superior confirma la conexión en vivo.
Partes del Dashboard:
- Sidebar (columna izquierda): estado de la instancia activa — instance_id, payload actual de la vacante (campos Class A como aparecen en Notion), capabilities disponibles en el estado actual (can_patch · can_validate · can_accept · can_archive) y Audit Log en tiempo real con cada evento registrado.
- Panel principal (área derecha): cuatro secciones — selector de vacante (dropdown con todas las vacantes en Gate = BLOCKED, botón Crear instancia), máquina de estados FSM (visualiza el estado actual: BLOCKED → PATCHED → RETURNED_TO_CREATE), panel de patch (formulario con campos Class A editables: URL · JD · Source_Type · Prioridad), y área de resultado de validación (PASS verde o FAIL rojo con motivo).
Botones: Crear instancia · Proponer Patch · Validar · Aceptar Patch · Archivar · Sincronizar.
Secuencia — vacante BLOCKED recuperable:
1. Selecciona la vacante del dropdown (muestra Marca · Rol · Score · VM_Scope).
1. Crear instancia — abre una instancia en estado BLOCKED y carga el payload desde Notion. Audit Log registra domain.instance.created.
1. Edita los campos incorrectos en el panel de patch — solo Class A (URL · JD · Source_Type · Prioridad). Los campos Class B no son editables.
1. Proponer Patch — almacena la corrección. Audit Log registra domain.patch.proposed.
1. Validar — el backend ejecuta run_pipeline.py con el patch y verifica si el resultado sería CREATE. Si pasa: estado → PATCHED, resultado verde. Si falla: estado permanece BLOCKED, resultado rojo con motivo.
1. Aceptar Patch — escribe los campos Class A corregidos en Notion. Estado → RETURNED_TO_CREATE. Audit Log registra domain.patch.accepted.
1. Corre el pipeline para que Python recalcule:
```bash
~/vantage_pipeline.sh
```
Secuencia — vacante no recuperable: usa el botón Archivar. El Dashboard escribe Next_Action = Archivar en Notion y cierra la instancia en estado FAILED. No pasa por el pipeline.
Las entradas con este status son escritas en Notion por feed_processor.py cuando no pudieron procesarse completamente: la URL era parcial o ambigua, la marca no resolvía contra el alias map, o el sistema detectó un semi-duplicate cross-layer que requiere revisión humana. Mientras el status permanezca en REVIEW_NEEDED, sus campos Class B (Score, Gate_Decision, VM_Scope, Role_Class) quedan bloqueados — Python no los calcula.
Contrato de resolución — 4 pasos obligatorios:
1. Abre la entrada en Notion e identifica el problema indicado en el campo Notas (ej. “URL parcial”, “alias no resuelto: Nike México”, “semi-duplicate”).
1. Corrige el campo problemático directamente en Notion: reemplaza la URL parcial con la URL completa, o ajusta el nombre de la marca al valor que exista en el alias map.
1. Cambia Status → Target. Este es el único valor que Python reconoce como señal de resolución. Cualquier otro valor (incluyendo dejar REVIEW_NEEDED) mantiene el bloqueo en el siguiente run.
1. Corre el pipeline:
```bash
~/vantage_pipeline.sh
```
Python detecta Status = Target en entradas que tenían Gate vacío o REVIEW_NEEDED y procesa sus campos Class B normalmente — calcula Score, Gate_Decision y el resto.
Por qué Target y no otro valor: Target es el estado operativo estándar de una vacante en espera de procesamiento. Usarlo como señal de resolución mantiene el contrato de estados consistente — no requiere un valor nuevo ni lógica adicional en Python.
Nota importante: estas entradas no pasan por el Dashboard. El Dashboard es para vacantes con Gate = BLOCKED que ya tienen campos Class B calculados y necesitan corrección de inputs Class A. REVIEW_NEEDED es un estado previo — todavía no llegó a tener Gate calculado.
---
### 8.3 MIÉRCOLES — CV Optimization
Optimización de CV para vacantes priorizadas en Ready-to-Apply. Claude opera activamente en este ciclo — es el único día donde el AI Component tiene rol principal. L3 sigue corriendo en sus horarios habituales, en background.
Abre Ready-to-Apply en Notion y elige la vacante a trabajar. Copia la URL del campo URL (career page oficial) o el texto del JD. Abre una nueva sesión de Claude (recuerda: esto significa pasar primero por el Ciclo de Sesión de §6 si aún no lo has hecho hoy) y dispara:
```plain text
CV-A [URL de la vacante]
```
o pega el texto del JD directamente. Claude no accede al Tracker de forma autónoma — el trigger debe ser explícito.
CV-A es análisis: qué keywords posicionar, qué gaps cubrir, qué tono de marca adoptar. CV-B es producción: el documento final. En una sesión única, el contexto de análisis contamina la voz del CV. La separación es una restricción de calidad, no de conveniencia.
Claude extrae los 6 keywords de posicionamiento del JD, identifica los gaps entre los requisitos del rol y el perfil de experiencia canónico del Career Canon, determina el Positioning Mode aplicable — hay cuatro posibles, definidos en el Career Canon:
- N1 Luxury Brand Execution
- N2 Store Design & Flagship
- N3 Regional Brand Execution
- N4 Commercial VM & Field Leadership
Además, define el tono de marca del CV y detecta el idioma del JD (ES/EN) para el output.
Output de la sesión — el HANDOFF, 6 campos obligatorios:
```json
{
  "empresa": "",
  "rol": "",
  "JD_keywords_top6": ["", "", "", "", "", ""],
  "fit_gaps": ["", ""],
  "tono_marca": "",
  "idioma": ""
}
```
La sesión termina aquí. No se escribe ningún CV en CV-A.
HANDOFF — Contrato de Transferencia: CV-B no inicia con un HANDOFF incompleto. Si cualquier campo está ausente, el sistema lo solicita antes de continuar.
PROTOCOL UPDATE — SKELETON-FIRST: CV-B ya no tiene permiso creativo sobre la estructura. El proceso es de inyección en slots: se usa el Golden Skeleton como base, y se vacía la información del Career Canon en los slots existentes sin alterar sus IDs.
Abre una sesión nueva de Claude. Pega el HANDOFF completo y dispara:
```plain text
CV-B [pega el HANDOFF]
```
Claude verifica los 6 campos, cruza el HANDOFF contra el contrato de output del Career Canon para validar que bullets y KPIs sean derivados canónicos (no inventados), aplica el Positioning Mode definido en CV-A, usa el campo idioma del HANDOFF para seleccionar la versión ES o EN de cada sección del Career Canon (no se generan CVs bilingües ni se mezclan idiomas dentro de un mismo output) y genera el CV bajo ese mismo contrato de output.
El output tiene tres partes obligatorias y secuenciales:
1. Markdown con Figma tags — Claude entrega el archivo .md completo en la misma sesión. Cada slot va encabezado por su tag (###### figma_text_id). El operador lo revisa y autoriza antes de cualquier escritura en Notion.
1. Autorización explícita del operador — Claude espera confirmación antes de continuar. Sin autorización, no escribe nada.
1. Documentar la URL del Markdown.
Regla de orden: el Markdown nunca se escribe en Notion si el operador no ha autorizado explícitamente. El orden cronológico de experiencia es invariante: C01 → C02 → C03 → C04 → C05. No se reordena por vacante ni por Positioning Mode.
Escritura en Notion (dos destinos):
- Página en DERIVED OUTPUTS · ARCHIVE del Career Canon — con footer de Positioning Mode activo y fecha.
- Bloque # MARKDOWN CANON ALIGNED en la página de la vacante en el Tracker — el Markdown completo con Figma tags, dentro de un bloque de código markdown.
Con el .md autorizado en mano, el flujo hacia Figma es directo — el plugin hace el trabajo pesado.
Instalación del plugin (una sola vez, si aún no lo tienes instalado): Figma Desktop → Plugins → Development → Import plugin from manifest… → navega a ~/Documents/03 Projects/VANTAGE/Figma Sync/ → selecciona manifest.json. El plugin queda disponible permanentemente. Es importante saber que el plugin no modifica Notion ni el Tracker — opera exclusivamente sobre el lienzo Figma activo.
Uso operativo, cada Miércoles:
1. Abre Figma Desktop y el archivo del CV.
1. Plugins → Development → VANTAGE CV Sync.
1. Copia el contenido completo del .md de CV-B y pégalo en el área de texto del plugin.
1. Haz clic en Inyectar a Nodos Nativos.
1. Verifica la notificación: VANTAGE Sync: X nodos actualizados vía Registry V2 (ID crudo).
1. Revisa el lienzo visualmente y exporta: frame del CV → Export → PDF.
Si el plugin reporta Keys sin resolver, revisa la entrada correspondiente en §12 — Troubleshooting (“Figma plugin no resuelve IDs”).
```plain text
QA [adjunta el PDF exportado]
```
Claude revisa formato y completitud con checklist de 6 ítems y entrega go/no-go. QA no evalúa fit — evalúa que el documento esté correcto como entregable.
Si QA aprueba, cambia Status a Postulado en Notion y corre:
```bash
~/vantage_pipeline.sh
```
Python detecta el Status y asigna Gate_Decision = APPLIED. La vacante sale de Ready-to-Apply automáticamente.
---
### 8.4 JUEVES — Segunda Pasada (Condicional)
Ejecuta solo si hay nuevas vacantes que procesar — 10 minutos máximo:
```bash
~/vantage_pipeline.sh
```
Script: ~/vantage_pipeline.sh. Este día no tiene un procedimiento distinto al ya descrito en el Lunes (§8.1) — es simplemente una repetición ligera del paso de procesamiento, para no dejar acumular vacantes hasta la siguiente semana si el Lunes no alcanzó a cubrir todo el backlog.
---
### 8.5 VIERNES — Analytics
```bash
~/vantage_pipeline.sh analytics
```
Output: efectividad por fuente, tasa de links muertos por tipo de URL, ratio career pages vs. aggregators.
Acción concreta: si career pages producen menos de 5 resultados relevantes en la semana, ajusta el Prompt A (ver §13 — Prompts & Wrappers) — no el threshold de Score. (Recuerda §3, Filosofía de Fallo: el Score bajo no es el problema a corregir, el input de búsqueda sí lo es.)
Con esto se cierra el ciclo semanal. La siguiente vez que abras Claude para trabajar en VANTAGE, el ciclo completo empieza de nuevo desde §6 — Ciclo de Sesión.
---
## 09 MANUAL:VANTAGE-RUNTIME-001
## VANTAGE Runtime (Consulta Operativa)
Ya viste varios de estos comandos en acción durante el flujo semanal (§8) — esta sección los reúne como catálogo de referencia completo, junto con el detalle de cuándo y por qué correr cada uno.
### 9.1 ¿Qué es el Runtime?
Es la herramienta de observabilidad del sistema. Permite interrogar a Notion y extraer contexto semántico sin salir de la terminal.
Version Check Tool (vversions) y Census (vcensus) —ya documentados como comandos en §9.2 y en uso durante el Ciclo de Sesión (§6)— pertenecen a esta misma capa: interrogan a Notion para darte visibilidad (versión documental, salud del Census), nunca escriben datos de negocio del pipeline de vacantes. Si alguna vez te preguntas por qué vversions vive junto a vantage.py status en vez de junto a vl1, es por esto: los dos son observación, no procesamiento de vacantes.
### 9.2 Comandos Principales — Mantenimiento del Tracker
Estos comandos operan sobre el estado del Tracker y están disponibles como subcomandos de vl1. Cada uno tiene un alcance preciso y un modo de operación por defecto.
- vl1 tracker — genera un reporte de estado del Tracker en tiempo real: distribución por Gate_Decision, conteo de entradas activas (CREATE + APPLIED), entradas BLOCKED, aplicaciones de los últimos 7 días y NADs vencidas. Es el punto de partida del ciclo semanal — corre antes de cualquier otra operación para tener visibilidad del estado actual (esto es lo que produce el output que viste en el Test Inicial de Setup, §4, Paso 5).
- vl1 analytics — analiza la efectividad de las fuentes de discovery: qué canales producen más entradas CREATE, qué ratio de URLs funcionales tienen, cuál es el score promedio por fuente, y qué método de búsqueda (SEARCH-WEEK, SEARCH-EXEC, Manual) tiene mayor tasa de éxito. Corre los viernes como parte del cierre semanal (§8.5).
- vl1 batch — modo de operación por defecto: read-only. Muestra la distribución por Status y el conteo de entradas que serían afectadas por la operación batch configurada en el script. Para ejecutar escritura, pasar el flag -execute explícitamente:
```bash
vl1 batch --execute
```
Sin --execute, el comando nunca escribe en Notion. Esta protección es permanente — no se puede desactivar sin modificar el flag.
- vl1 recovery — verifica la consistencia de los datos en el Tracker: detecta entradas sin Score, sin VM_Scope o sin Gate_Decision. También gestiona checkpoints del pipeline — si un run anterior falló a mitad, recovery carga el último checkpoint y permite retomar desde el paso fallado. Corre cuando el pipeline reporta inconsistencias o tras un fallo inesperado.
- vl1 profile — gestiona la configuración del perfil activo del sistema: keywords VM y de pivote, pesos de scoring, empresas target por tier y foco geográfico. Permite actualizar el perfil sin editar código — los cambios se persisten en config/profile_config.yaml. Opción 7 (“Salir sin cambios”) es el exit seguro; cualquier cambio guardado requiere propagación manual a layer_1_run.py.
- vl1 backfill — backfill de campos Class A faltantes en entradas existentes: layer, hash y Prioridad. Opera con preview obligatorio antes de escribir — muestra exactamente qué entradas serán modificadas y por qué razón se infirió el layer. Acepta -dry-run para preview sin confirmación:
```bash
vl1 backfill --dry-run
```
Sin --dry-run, solicita confirmación explícita (s) antes de cualquier escritura.
vversions — alias corto de verify_versions.py, el motor de verificación y sincronización de versión de los 7 documentos fundacionales ([KERNEL:VERSION-CHECK-TOOL](https://app.notion.com/p/377938befc42805ea408c9ae518d4fe7#380a32a5525b4d5d8cd44516fb1b74d4)). No es un comando del Tracker de vacantes como los vl1 * de arriba — es infraestructura documental, y su uso está integrado al Ciclo de Sesión completo en §6, no como comando suelto. Acepta tres flags: --bootstrap (dump de apertura), --check (lectura de versión, read-only) y --sync (única escritura, propagación en lote).
vcensus — alias corto de generate_census.py. Regenera el V-ID-CENSUS y reporta IDs huérfanos detectados en los documentos fuente. Se corre en el paso 1 del Cierre de Sesión (§6) si algún ID cambió de estado durante la sesión — ver también §11, "El V-ID-Census", para el detalle completo de cuándo es obligatorio.
### 9.3 Cuándo correr sync
Correr vantage.py sync después de:
- Cualquier ciclo L1/L2 que haya escrito entradas nuevas en Notion.
- Después de resolver entradas REVIEW_NEEDED en el Tracker (ver §8.2).
- Si status muestra "warning": "entity_index_stale" (index > 24h).
- Si status muestra orphan_candidates > 0 de forma persistente.
No es necesario para cambios de Status, Score, Gate_Decision en páginas individuales — esos se leen en vivo vía resolve/context.
### 9.4 Runtime Build — Cuándo y Para Qué
El Runtime Build regenera los tres artefactos de lectura del sistema: entity_index_v2.json, graph_v2.json y backlinks_v2.json. Se corre desde Layer_1/scripts/ con el venv activo.
Cuándo correrlo:
- Después de cualquier migración de namespaces o cambio en resolver_registry_v2.json.
- Si graph_v2.json muestra self-loops inesperados (síntoma de colisión de namespace).
- Si entity_index_v2.json contiene IDs con prefix incorrecto.
- Como parte del cierre formal de un release que afecte la capa de Runtime.
El Build es determinista: el mismo Registry + el mismo estado de Notion producen los mismos artefactos. Si el resultado varía entre runs sin cambios en los inputs, es una señal de problema en el Registry — no en el Build.
Sobre resolver_registry_v2.json: desde v2.4.0 (Runtime Contract Migration), este archivo es la fuente enforced — no solo declarada — de namespace ownership. Cada tipo de entidad tiene su entity_prefix definido aquí; ningún componente del sistema puede hardcodear ni inferir un prefix. Una edición manual que asigne un prefix incorrecto producirá colisiones de namespace en el siguiente Runtime Build, lo que se manifestará como self-loops en graph_v2.json. Antes de editar: verificar el prefix activo por tipo de entidad y correr Runtime Build para confirmar que no hay colisiones.
Comandos relacionados de deduplicación y oportunidades:
```bash
cd $LAYER_1_DIR && source .venv/bin/activate && python3 scripts/consolidate_duplicates.py  # alias: vdedup
cd $LAYER_1_DIR && source .venv/bin/activate && python3 scripts/dedup_opportunities.py    # alias: vopport
```
---
## 10 MANUAL:DATA-MANAGEMENT-001
## Gestión de Datos
Esta sección consolida en un solo lugar todo lo relacionado con exclusiones y deduplicación de vacantes — conceptos que se mencionan a lo largo de §1, §2 y §8, y que aquí tienen su definición completa y única.
### Hard Blocks — Empresas Excluidas Permanentemente
Estas empresas o tipos de rol nunca entrarán al sistema. Se filtran en el origen (antes de que la vacante exista como registro en Notion) y no son recuperables bajo ninguna circunstancia, ni siquiera vía Dashboard:
- L’Oréal (todas las divisiones)
- Levi Strauss & Co. (Levi’s, Dockers)
- El Palacio de Hierro
- Roles store-level sin gestión estratégica
### Soft Blocks — Bloqueos Recuperables
A diferencia de los Hard Blocks, estas vacantes sí pueden recuperarse: fueron bloqueadas por inconsistencias en datos Class A (URL rota, JD parcial) o por score insuficiente, no por pertenecer a una empresa vetada. Se recuperan corrigiendo el input incorrecto a través del Dashboard — el procedimiento completo está en §8.2 (Martes).
### Deduplicación
- Ventana: 30 días. Una vacante que ya existe en el Tracker no se vuelve a crear si aparece de nuevo dentro de esta ventana.
- Clave compuesta: brand + title + location.
- Jerarquía entre capas: L1 > L2 > L3. Cuando dos capas detectan la misma vacante, persiste la instancia de la capa de mayor jerarquía, pero se toman de la capa de menor jerarquía los datos que puedan complementar sus propiedades Class A (esto es exactamente lo que ocurre en el paso de Consolidation & Dedup del Lunes, §8.1).
---
## 11 MANUAL:HEALTHCHECK-001
## Health Check
### Red Flags — Ajustar Inputs, No Sistema
- Ready-to-Apply vacío por más de 3 días → ajustar Prompt A (ver §13 — Prompts & Wrappers), no el threshold. (Ver también §3 — Filosofía de Fallo.)
- Career pages con éxito < 50% → revisar fuentes de discovery.
- Pipeline runtime > 5 min → archivar entradas inactivas.
### Qué es y qué lee
Es un script de arranque, de lectura estricta (cero escritura salvo la excepción documentada abajo). Corre automáticamente al invocar el alias start (activa venv + carga env + ejecuta el script). También puede correrse manualmente:
```bash
cd Layer_1/scripts && python3 health_check.py
```
Qué lee, en este orden:
1. Versión del sistema — propiedad Versión de V-CHANGELOG vía Notion.
1. Entorno (.env) — verifica que NOTION_TOKEN y demás vars requeridas existan.
1. Git — git status --porcelain; reporta si hay archivos sin commitear.
1. Último commit (vgit) — git log -1 para timestamp de referencia.
1. Notion reachable — fetch mínimo a V-SYSTEM-PROMPT para confirmar conectividad y token válido.
1. Docs fundacionales — confirma que los 6 documentos existen localmente en ACTIVE/.
1. Último vdoc sync — cuál de los 6 docs locales tiene el mtime más reciente, y hace cuánto.
1. Antigüedad de índices (index_age) — ver detalle abajo. Única sección con capacidad de escritura (auto-sync condicional).
1. Tickets pendientes — Bug Tracker y Task Tracker, agrupados por prioridad.
Índices monitoreados: graph_v2.json y entity_index_v2.json, ambos en Layer_1/scripts/.
Comportamiento del auto-sync (desde v8.7.9): si algún índice supera 24 horas sin actualizarse, health_check.py dispara automáticamente python3 vantage.py sync (housekeeping de rutina — no requiere aprobación del operador, no es remediación de un fallo, según la misma lógica de §3 — Filosofía de Fallo: esto no es un error, es mantenimiento normal). El sync se dispara una sola vez por corrida, solo si al menos un índice cruzó el umbral — no re-sincroniza índices ya frescos, y no corre si todos están dentro del umbral.
Cómo leer el output:
- ✓ verde — check pasó.
- ! amarillo — advertencia, no bloquea (ej. índice stale antes del auto-sync, tickets pendientes).
- ✗ rojo — fallo real, contribuye al exit code final.
- Línea final Sistema OK (exit 0) vs. Sistema con issues: [lista] (exit 1).
Si el auto-sync falla: aparece ✗ index — auto-sync falló o auto-sync timeout. Esto sí es un fallo real — el script no reintenta. Acción manual:
```bash
python3 vantage.py sync
```
desde Layer_1/scripts, y verificar con vantage.py status que entities_after >= entities_before.
Tickets pendientes: se listan explícitamente solo CRÍTICO y ALTO; MEDIO/BAJO/Sin Prioridad aparecen solo como conteo — ver Notion para detalle.
Sync manual sigue disponible para forzar fuera de umbral, o si has realizado cambios masivos en el Tracker o el Canon y no quieres esperar a la siguiente corrida de start:
```bash
python3 vantage.py sync
```
### El V-ID-Census
Qué es: el V-ID-CENSUS es tu mapa de navegación — te dice en qué documento y en qué bloque exacto vive cada ID del sistema, con link directo. Pero es un mapa, no el territorio: si el Kernel cambia y el Census no se actualiza, el mapa miente. Este es el mismo Census que se verifica y actualiza durante el Ciclo de Sesión (§6).
Cuándo se regenera (obligatorio, no opcional):
- Antes de marcar cualquier ticket como cerrado, si ese ticket cambió el estado de un ID (de pendiente a resuelto, o creó uno nuevo).
- Si no tienes Terminal a la mano en ese momento, el ticket se queda en Blocked-Census — no se cierra en falso, se marca como bloqueado hasta que puedas correr el script.
Cómo corre:
```bash
source ~/Documents/03 Projects/VANTAGE/Layer_1/.venv/bin/activate
cd ~/Documents/03 Projects/VANTAGE/Layer_1/scripts
python3 generate_census.py
```
El script también detecta IDs que existen en los documentos pero no en su lista de seguimiento (“huérfanos”) y te los señala — ya no se cuelan en silencio. Y para cada ID resuelto genera el link exacto al bloque en Notion, no solo al documento.
Orden con Changelog: primero Census actualizado, después la entrada de Changelog. Nunca al revés (esto es exactamente el paso 2 del Cierre de Sesión, §6).
Al cerrar sesión: si hubo cambios a documentación o bases de datos, se te presenta automáticamente un resumen de lo que quedó hecho vs. pendiente — sin que tengas que pedirlo.
Aviso en arranque: health_check.py (alias start) reporta la antigüedad del Census en cada corrida — ! census — Nd sin regenerar si pasó el umbral de 7 días. Es solo un recordatorio visual, no dispara nada automáticamente; sigue siendo tu responsabilidad correr generate_census.py cuando cierres un ticket que cambió estado de un ID.
### Aplicación de Hipervínculos Cross-Reference
Con el Census ya resolviendo cada ID a su bloque real, el siguiente paso es convertir esas menciones en links clickeables dentro de los propios documentos — eso lo hace apply_hyperlinks.py, no generate_census.py (el Census resuelve, el script de hipervínculos escribe).
Cuándo correrlo: después de cualquier alta/baja/rename de ID canónico, o tras una migración de formato de heading — en ambos casos el MAPPING interno del script puede quedar desactualizado.
Cómo corre:
```bash
python3 apply_hyperlinks.py --root "Documentación/ACTIVE"
```
Sin --apply, solo reporta cuántos hipervínculos propuestos hay por documento (dry-run, no escribe nada). Revisa el diff generado; si se ve correcto, vuelve a correr agregando --apply.
Si el dry-run reporta 0 en los 6 documentos, no hay nada pendiente — no hace falta --apply.
### Skills de Mantenimiento del Tracker (VANTAGE)
Con el Census y su ciclo de regeneración ya cubiertos arriba, esta es la contraparte operativa del lado de Bug/Task Tracker y Changelog: cinco skills que Claude ejecuta bajo invocación explícita del operador, cada una con su propio contrato de Dry Run + APROBAR_WRITE cuando corresponde.
- vantage-create-bug-task — crea un ticket nuevo en Bug Tracker (defecto reactivo) o Task Tracker (trabajo/decisión pendiente). Úsala en cualquier momento de la sesión en que detectes o reportes uno de los dos.
- vantage-tidy-bug-task-tracker — archiva tickets ya resueltos (confirmación directa del operador, o detección indirecta vía Change Log). Requiere Dry Run + APROBAR_WRITE antes de archivar.
- vantage-tidy-opportunities-tracker — identifica duplicados y vacantes expiradas en el Tracker de vacantes para archivado, usando los mecanismos de fingerprint y protección de estado terminal ya implementados en feed_processor.py (ver §10 — Gestión de Datos). Requiere Dry Run + APROBAR_WRITE.
- vantage-tidy-changelog — mantiene el Change Log con las últimas 10 entradas visibles, moviendo el exceso al Archivo Changelog histórico. Úsala cuando el Change Log activo supera 10 entradas o para housekeeping documental puntual.
- vantage-present-handoff — genera el snapshot de contexto de sesión para continuidad en un chat nuevo. Es independiente y se puede invocar en cualquier momento; no requiere que la sesión esté cerrando (ver también §6 — Ciclo de Sesión, Cierre, donde vantage-session-close la invoca automáticamente como parte de su secuencia normal).
Cada una declara su propio verbo de apertura/cierre ([KERNEL:SKILL-ANNOUNCE-CONVENTION](https://app.notion.com/p/377938befc42805ea408c9ae518d4fe7#39e938befc4281db9f8eee98d8f90185)) — nunca el lenguaje de Bootstrap ni de Session Ledger.
---
## 12 MANUAL:TROUBLESHOOTING-001
## Troubleshooting
### Problemas Comunes y Soluciones
Pipeline no corre:
- Verificar .env en ~/vantage_notion_audit/.
- Confirmar token Notion no expirado (regenerar en Notion → Settings → API → New token).
- Verificar entorno Python activo: source Layer_1/.venv/bin/activate && python --version.
- Confirmar permisos de ejecución: ls -la ~/vantage_pipeline.sh (debe tener x).
Entity Index desactualizado:
- Desde v8.7.6: health_check.py detecta índices >24h y dispara vantage.py sync automáticamente en cada corrida de start — no requiere acción manual en el flujo normal.
- Síntoma de que el auto-sync falló: health_check.py reporta ✗ index — auto-sync falló o auto-sync timeout en vez del ✓ esperado.
- Solución manual (solo si el auto-sync falló): python vantage.py sync desde Layer_1/scripts.
- Verificar resultado: vantage.py status debe mostrar entities_after >= entities_before.
- Si persiste: verificar token Notion y conectividad a internet.
L3 no procesa correos:
- Verificar layer_3.env existe en Layer_3/config/.
- Confirmar credenciales: IMAP (Gmail), GROQ_API_KEY.
- Ejecutar manualmente: vl3 (debe procesar hasta 5 correos).
- Revisar heartbeat: cat ~/.vantage/l3_heartbeat.json (última ejecución exitosa).
- Si falla autenticación IMAP: regenerar app password de Gmail.
Figma plugin no resuelve IDs:
- Verificar registry_seed.json actualizado desde lienzo Figma.
- Confirmar que code.js tiene Registry V2 embebido (variable REGISTRY al inicio).
- Comparar IDs en .md generado por CV-B vs IDs reales en capas Figma.
- Si hay mismatch: regenerar registry_seed.json desde Developer Console de Figma.
- Reinstalar plugin si persiste: Plugins → Development → Import plugin from manifest.
Dashboard no abre:
- Verificar Flask corriendo: lsof -i :8000 (debe mostrar proceso Python).
- Ejecutar smoke test: vd debe imprimir “SMOKE PASSED — abriendo dashboard”.
- Si falla smoke test: revisar dashboard_start.sh permisos (chmod +x).
- Verificar puerto 8000 libre: killall -9 Python si hay proceso zombie.
- Si error de importación: confirmar .venv activo y dependencias instaladas.
REVIEW_NEEDED no se resuelve tras corregir:
- Confirmar que cambiaste Status → Target en Notion (no otro valor).
- Verificar que corrección se guardó (refrescar página Notion).
- Ejecutar pipeline: ~/vantage_pipeline.sh.
- Si persiste: verificar en terminal qué campo sigue bloqueando (Python imprime razón).
- Revisar logs en ~/.vantage/logs/ para diagnóstico detallado.
vl1 batch modifica entradas sin --execute:
- Bug crítico: reportar inmediatamente.
- Workaround: verificar siempre con vl1 batch (sin flag) antes de ejecutar.
- Confirmar que script tiene guard if not args.execute: return al inicio.
vsync_doc.py falla con error “blocks.children.list() returned None”:
- Bug conocido de notion-client 3.x.
- Solución: vsync_doc.py usa safe_list() con httpx directo (3 reintentos).
- Si persiste: verificar que page_id sea válido y token tenga permisos de lectura.
- Alternativa temporal: sync manual vía MCP Notion.
Score = 0 en vacante que parece relevante:
- Verificar que URL esté activa (no 404/403).
- Confirmar que JD contenga keywords VM (Python busca términos específicos).
- Revisar VM_Scope asignado (debe ser Core/Adjacent, no Off-Target).
- Si todo está correcto: revisar pesos de scoring en profile_config.yaml.
- No modificar Score manualmente (campo Class B, Python lo recalcula).
Gate = BLOCKED recuperable pero el Dashboard no lo detecta:
- Confirmar que entrada aparece en dropdown del Dashboard.
- Verificar que Gate_Decision = BLOCKED (no EXPIRED ni vacío).
- Si no aparece: refrescar cache de Runtime (vantage.py sync).
- Si aparece pero validación falla: revisar logs de run_pipeline.py en Dashboard.
### Referencias a documentación adicional
- Filosofía de fallo: [KERNEL:FAIL-PHILOSOPHY](V | KERNEL) (ver también §3 de este Manual).
- Reglas de Oro: [KERNEL:CV-GOLDEN-RULES](https://app.notion.com/p/377938befc42805ea408c9ae518d4fe7#39e938befc428148a288d1c640c6f64d) (ver también §18 de este Manual).
- Schema de datos: [KERNEL:SCHEMA](https://app.notion.com/p/377938befc42805ea408c9ae518d4fe7#39e938befc42812dbc97e075758ba0ee).
- Gate Decisions: [KERNEL:GATE-DECISION](https://app.notion.com/p/377938befc42805ea408c9ae518d4fe7#39e938befc42810d9f3af9b12751d7e1) (ver también §2 de este Manual).
---
## 13 MANUAL:PROMPTS-WRAPPERS-001
## Prompts & Wrappers
Se consultan vía MCP desde la PROMPT LIBRARY en Notion. Este es el catálogo que Perplexity Desktop lee cada Lunes (§8.1) para ensamblar los prompts de L1 y L2: los Prompt Bases (BASE SPEC L1, BASE SPEC L2) y los Wrappers correspondientes (Career Sites, LinkedIn, Aggregators, Gemini, Grok, you.com, Prompt A/B/C, Prompt E de consolidación).
---
## 14 MANUAL:CHEATSHEETS-001
## Cheat Sheets
### Cómo la IA lee el KERNEL y el CAREER CANON (Lazy Load)
La extracción de reglas y contratos lógicos (Lazy Load) opera con la siguiente prioridad:
Prioridad A — Terminal (canónico): lazy_loader.py ejecuta Server-Side Lazy Load. Parsea bloques hijos de la Notion API y devuelve únicamente el payload del ID solicitado. Consumo: ~150 tokens por llamada.
Prioridad B — MCP Notion: reservado exclusivamente para escrituras (APROBAR_WRITE) y modificaciones estructurales de páginas. No se usa para lectura de reglas o contratos.
---
## 15 MANUAL:PATCH-QUALITY-001
## Criterio de Calidad para Parches Documentales
Todo parche a los 6 documentos fundacionales debe cumplir estos cinco criterios antes de aplicarse — si falla alguno, se reescribe antes de solicitar APROBAR_WRITE:
1. Invisibilidad estructural — no crea secciones nuevas si el contenido cabe en una existente.
1. Continuidad de voz — mismo registro y nivel técnico del bloque que lo rodea.
1. Progresión narrativa intacta — el lector no debe notar un salto temático al leer de corrido.
1. Diff mínimo — se edita solo el texto indispensable, nunca el bloque completo si un párrafo basta.
1. Coherencia transversal — no puede contradecir ni duplicar una definición ya existente en Kernel, System Prompt, Career Canon o Aliases.
Un parche que pasa estos cinco filtros no se distingue, seis meses después, del texto que rodeaba su punto de inserción original.
---
## 16 MANUAL:GOLDEN-RULES-001
## Reglas de Oro para Operadores
Base: [KERNEL:CV-GOLDEN-RULES](https://app.notion.com/p/377938befc42805ea408c9ae518d4fe7#39e938befc428148a288d1c640c6f64d).
> El contenido detallado de estas reglas vive en el Kernel del sistema y no está reproducido en este Manual más allá de esta referencia. Ver lista de huecos detectados al final de este documento.
---
## 17 MANUAL:SLA-001
## SLA de Latencia Post-Ingesta
> Nota: el SLA “< 45 minutos” cubre únicamente el segmento Score calculado → Ready-to-Apply (Discovery → Ready-to-Apply en nomenclatura anterior). El segmento Trigger → Score depende del ciclo de ejecución de ~/vantage_pipeline.sh (ver §8.1, Lunes) — no tiene SLA fijo salvo ejecución manual explícita de layer_1_run.py.
## 18 MANUAL:CV-GOLDEN-RULES-INDEX
## Reglas de Oro CV — Referencia Operativa
Las Reglas de Oro ([KERNEL:CV-GOLDEN-RULES](https://app.notion.com/p/377938befc42805ea408c9ae518d4fe7#39e938befc428148a288d1c640c6f64d)) son restricciones de arquitectura, no preferencias. Viven íntegras en el Kernel — esta sección es un índice de navegación, no una copia.
| ID | Regla | Qué bloquea |
| --- | --- | --- |
| KERNEL:CV-GOLDEN-RULES-001 | No Evaluar Fit Antes de Escribir | Preguntas de "¿me conviene esta vacante?" — el fit lo decide Score (Python) + el operador |
| KERNEL:CV-GOLDEN-RULES-002 | No Calcular ni Estimar Campos Class B | Estimar Score, Gate_Decision, VM_Scope, etc. — son Python-only |
| KERNEL:CV-GOLDEN-RULES-003 | No Cuestionar la Calidad de Datos del Usuario | Comentarios sobre volumen/calidad del JSON de búsqueda — estrategia es 100% humana |
| KERNEL:CV-GOLDEN-RULES-004 | No Delegar Escritura al Usuario | "Copia esto y pégalo en Notion" — el sistema escribe directo, salvo export PDF/Drive |
| KERNEL:CV-GOLDEN-RULES-005 | No Interpretar en SYNC | SYNC reporta datos puros, sin análisis ni recomendaciones |
Toda violación produce el Template Universal de Rechazo (ver Kernel): OPERACIÓN RECHAZADA → razón → alternativa operativa → confirmación SÍ/CANCELAR.
Para el detalle completo de cada regla (ejemplos de solicitudes que la activan, redacción exacta de la respuesta estandarizada), consultar directamente [KERNEL:CV-GOLDEN-RULES](https://app.notion.com/p/377938befc42805ea408c9ae518d4fe7#39e938befc428148a288d1c640c6f64d) en el Kernel — fuente única, no se replica aquí para evitar drift entre documentos.
## 19 MANUAL:POSITIONING-CRITERIA
## Positioning Modes (N1–N4) — Criterio de Selección
[CANON:POSITIONING-001](https://app.notion.com/p/377938befc42808993f2f52dbd2dec6c#39a938befc42811ba92acf1dc1467702) define 4 modos de posicionamiento para CV-B. Esta sección resuelve el gap operativo: con qué criterio elegir uno.
| Modo | ID | Ancla canónica | Cuándo aplica |
| --- | --- | --- | --- |
| N1 | CANON:POSITIONING-N1 | C01 · 3 marcas lujo · CAPEX/OPEX · NPI | JD enfatiza gestión multi-marca de lujo, presupuesto, lanzamientos de producto |
| N2 | CANON:POSITIONING-N2 | C02 · Adidas Brand Center · KPI07 · blueprints | JD enfatiza Store Design, Flagship, construcción/remodelación física |
| N3 | CANON:POSITIONING-N3 | C03 · 270+ POS · 6 países · KPI03–06 · CF05 | JD enfatiza rollout regional multi-país, estandarización, eficiencia operativa |
| N4 | CANON:POSITIONING-N4 | C04/C05 · +43% tráfico · +18% conversión · 21 reportes | JD enfatiza liderazgo de campo comercial, KPIs de tráfico/conversión, gestión de equipos directos |
Regla de desempate (JDs híbridos) — ver [CANON:POSITIONING-001](https://app.notion.com/p/377938befc42808993f2f52dbd2dec6c#39a938befc42811ba92acf1dc1467702) para el texto completo: (1) más keywords mapeados al ancla, (2) empate → mayor seniority (N2>N1, N4>N3 con presupuesto regional explícito), (3) empate persistente → escalar a decisión humana vía fit_gaps.
## 20 MANUAL:GOLDEN-SKELETON-REF
## Golden Skeleton — Qué es y Dónde Vive
El "Golden Skeleton" ([CANON:OUTPUT-CONTRACT-001](https://app.notion.com/p/377938befc42808993f2f52dbd2dec6c#39a938befc428110a5effba7515cd721)) es la secuencia fija de bloques ###### figma_text_id que todo CV-B debe replicar exactamente — mismo conteo, mismo orden, solo cambia el contenido textual.
- SSOT de IDs de nodo Figma: registry_seed.json en 04-Vantage_CV/Figma Sync/.
- Slots clave: 2055:9 (Nombre), 2055:10 (Tagline), 2043:51 (Perfil), 2043:56-60 (Skills), 2043:64+ (Experiencia).
- Regla de invariancia: si el Skeleton cambia en Figma, registry_seed.json se actualiza antes del siguiente CV-B — nunca al revés.
- Detalle completo del protocolo (immutability, slot integrity, null-fill rule) vive en [CANON:OUTPUT-CONTRACT-001](https://app.notion.com/p/377938befc42808993f2f52dbd2dec6c#39a938befc428110a5effba7515cd721) — no se replica aquí.
## 21 MANUAL:SCHEMA-FIELD-REF
## Schema Class A/B — Referencia de Campos
[KERNEL:SCHEMA-001](https://app.notion.com/p/377938befc42805ea408c9ae518d4fe7#39e938befc4281faa81ac25589b3c67f) define ownership exclusivo por campo. Esta tabla es índice de consulta rápida — el contrato completo (reglas de excepción, mapeo de vocabulario) vive en el Kernel.
Class A — Human-Primary (operador/feed_processor escriben):
Rol · Marca · Source_Type · URL · Status · Prioridad · Holding · JD · NAD · layer · hash
Class B — System-Primary (Python únicamente, ningún otro componente escribe):
Score · Gate_Decision · VM_Scope · Role_Class · Match · Next_Action · Fetch · Fuente
Excepción documentada: Fuente_Manual (Class A) existe para valores de fuente que deben persistir entre runs — Fuente (Class B) se sobreescribe en cada corrida ([KERNEL:SCHEMA-003](https://app.notion.com/p/377938befc42805ea408c9ae518d4fe7#39e938befc42817eb1dad96ac1ccc2b0)).
Pesos de Score/VM_Scope: viven en profile_config.yaml, propiedad de Python — el Manual no reproduce los valores numéricos porque son deuda de implementación, no contrato documental (ver [KERNEL:GATE-DECISION-002](https://app.notion.com/p/377938befc42805ea408c9ae518d4fe7#39e938befc42815a9d52ccf7394c183a)). Un operador que necesite ajustar pesos debe editar ese archivo directamente, no este documento.
