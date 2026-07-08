# V | MANUAL

> ##
| # | Sección | Tipo | Propósito |
| --- | --- | --- | --- |
| 1 | OBJETIVO DE VANTAGE | CONTEXTO | Propósito, problema resuelto y diferenciadores |
| 2 | CÓMO FUNCIONA | CONTEXTO | Arquitectura general y responsabilidades |
| 3 | SETUP | OPERACIÓN | Instalación y configuración inicial |
| 4 | FLUJO PUNTA A PUNTA | OPERACIÓN | Ciclo semanal completo |
| 5 | VANTAGE RUNTIME | OPERACIÓN | Comandos de consulta y observabilidad |
| 6 | GESTIÓN DE DATOS | OPERACIÓN | Blocks, deduplicación y reglas |
| 7 | TROUBLESHOOTING | REFERENCIA | Problemas comunes y soluciones |
| 8 | PROMPTS & WRAPPERS | REFERENCIA | Biblioteca de prompts |
| 9 | CHEAT SHEETS | REFERENCIA | Resúmenes rápidos |
| 10 | HEALTH CHECK | REFERENCIA | Checklist de mantenimiento |
| 11 | CHANGELOG | REFERENCIA | Historial de versiones |
| 12
 | REGLAS DE ORO PARA OPERADORES     | REFERENCIA | Reglas operativas derivadas del Kernel |
| 13 | FILOSOFÍA DE FALLO PARA OPERADORES         | REFERENCIA | Cómo interpretar fallos del sistema |
| 14 | SLA DE LATENCIA POST-INGESTA       | REFERENCIA | Alcance del SLA post-ingesta |
## 1. OBJETIVO DE VANTAGE · ID: MANUAL:OBJETIVO-001
### El Problema que Resuelve
Una búsqueda laboral sin estructura produce cuatro fallas operativas concretas:
- Oportunidades de alta señal desaparecen antes de ser procesadas
- Tiempo consumido en vacantes irrelevantes que no cumplen criterios mínimos
- Aplicaciones enviadas sin datos de fit — sin score, sin análisis de keywords, sin estrategia de CV
- Sin trazabilidad: qué se aplicó, cuándo, qué sigue
### Qué Hace Diferente
VANTAGE convierte la búsqueda laboral en un pipeline con contratos de procesamiento definidos.
Filtra antes de evaluar: Links muertos → Score 0, Status Expirada. Roles sin componente visual → Gate BLOCKED. Empresas en lista negra → rechazadas en discovery.
Verifica antes de creer: Cada URL pasa URL_GATE antes de cualquier cálculo de fit. Si el link no funciona, la vacante no entra al pipeline activo.
Centraliza en un solo lugar: Notion es la fuente única de verdad — vacantes, aplicaciones, scores, seguimiento.
Calcula con lógica determinista: Score 0–100 calculado por Python. La decisión de postulación se toma con datos, no con estimaciones.
### Impacto del Sistema (KPIs)
Evidencia de posicionamiento (Positioning Modes N1–N4) verificada:
### Lo que el Sistema No Hace
- No busca cualquier empleo — solo roles visuales en sectores lujo, premium, cool DNA y agencias de experiencia
- No genera volumen masivo — calidad de señal sobre cantidad de resultados
- No aplica automáticamente — la decisión de postulación es siempre humana
- No adivina campos faltantes — si falta información, el campo queda pendiente y el sistema lo reporta
### Para Quién Es Este Sistema
Perfil: Profesional senior (10+ años) en Visual Merchandising, Brand Environment, Store Design, Retail Experience. Geografía: CDMX / LATAM. Sectores target: Lujo (LVMH, Kering, Richemont), retail premium (Nike, Apple, Inditex), cool DNA (Gentle Monster, Ben & Frank), agencias de experiencia.
> Las empresas excluidas permanentemente (Hard Blocks) están documentadas en §6 — Gestión de Datos.
## 2. CÓMO FUNCIONA · ID: MANUAL:FUNCIONAMIENTO-001
### Flujo General del Pipeline
El pipeline opera secuencialmente. Cada paso tiene un responsable y un output definido.
### División del Trabajo
### Lógica de Filtrado: Soft vs Hard Blocks
El sistema aplica dos capas de exclusión para garantizar la calidad de la señal:
- Hard Blocks (Permanentes): Empresas o roles que nunca entrarán al sistema (ej. L'Oréal, Levi's). Se filtran en el origen y no son recuperables. Ver §6.
- Soft Blocks (Contextuales): Vacantes bloqueadas por inconsistencias en datos Class A (URL rota, JD parcial) o score insuficiente. Son recuperables mediante el Dashboard (RT-1) corrigiendo el input.
## 3. SETUP · ID: MANUAL:SETUP-001
### Paso 3 — Configuración de Claude (Bootstrap)
Ya no es necesario realizar copy-paste manual del System Prompt maestro en cada actualización. 
1. Copia el STATIC BOOTLOADER v1.0 (disponible en la Cédula Digital) y pégalo en Settings → Project → Project Instructions en la UI de Claude.
1. Inicia un nuevo chat. El Agente Vantage realizará un fetch automático de la gobernanza activa desde Notion.
1. Confirma que el Agente responde con "VANTAGE v8.9.4: SISTEMA SINCRONIZADO" antes de enviar peticiones.
Nota: Este setup es de una sola vez por proyecto.
### Prerrequisitos
- Cuenta de Notion con base de datos VANTAGE TRACKER activa
- Python 3.8+ instalado en Mac
- Acceso a Claude
- Cuenta de Perplexity con modo Deep Research activo
- Acceso a Gemini con modo Deep Research o Search activo
- Acceso a You.com con modo Research o Agent activo
- Acceso a Grok con modo DeepSearch o Think activo
### Paso 1 — Verificar Notion
Abre VANTAGE TRACKER y confirma que existen estas cuatro vistas:
- Ready-to-Apply — espacio de trabajo diario (Score ≥ 60)
- Para Revisar — vacantes en rango Score 40–59
- Archivar — Score 0 o Status Expirada
- All — administración general
Si VANTAGE TRACKER no existe, configúralo antes de continuar.
### Paso 2 — Instalar Entorno Python
```bash
cd ~/Documents/04-VANTAGE_CV/LAYER_1
source .venv/bin/activate
# (el entorno ya existe; solo actívalo)
```
Verifica la instalación: python3 --version debe mostrar 3.8 o superior.
### Paso 3 — Verificar Archivos del Sistema
Confirma que estos archivos existen en tu Mac:
### Permisos de Ejecución
Si reinstalas o mueves archivos, verificar permisos:
```bash
chmod +x $LAYER_1_DIR/layer_1_pipeline.sh
chmod +x $LAYER_1_DIR/wrappers/layer_1_wrapper.sh
chmod +x $LAYER_3_DIR/wrappers/layer_3_mail.sh
chmod +x $DASHBOARD_DIR/wrappers/dashboard_start.sh
```
### Paso 4 — Test Inicial
```bash
~/vantage_pipeline.sh status
```
Output esperado:
```plain text
=== VANTAGE PIPELINE STATUS ===
Ready-to-Apply: [N] vacantes
Para Revisar: [N] vacantes
…
```
Si falla: verifica que ~/vantage_notion_audit/.env existe y contiene tu token de Notion.
### Paso 5 — Verificar VANTAGE Runtime
El Runtime es el motor de lectura del sistema. Antes de operar, se debe verificar que el Entity Index esté cargado:
```bash
python vantage.py status
```
Resultado esperado: Status: READY (4,200+ blocks indexed).
### Paso 6 — Verificar Sync Documental (vsync_doc)
```bash
cd ~/Documents/04-VANTAGE_CV/Layer_4/scripts
source ../../Layer_1/.venv/bin/activate
python vsync_doc.py --dry-run
```
Output esperado: 6 documentos listados con diff por documento, sin errores.
Si falla: verificar que layer_1.env exista y que el token no tenga n embebido.
## 4. FLUJO PUNTA A PUNTA · ID: MANUAL:FLUJO-001
Contenido: V-Checklist y flujos de operación diaria. Ver §3 Setup para prerrequisitos.
### ID: MANUAL:VCHECKLIST-001
CHECKLIST INTERACTIVO
El V-Checklist (V-CHECKLIST · Vantage Weekly) es la interfaz operativa del ciclo semanal descrito en §4. Es un archivo HTML autocontenido con progreso persistente (localStorage), modo claro/oscuro y navegación por día.
Resumen de tareas por día:
Ubicación: archivo local Checklist.html (abre en navegador).
Reset: botón "⟓ Reset semana" en el header para iniciar un nuevo ciclo.
El progreso NO persiste entre sesiones distintas del navegador si se limpia el localStorage.
LUNES
El lunes es el ciclo de búsqueda activa completo. Se dispara manualmente y cubre las dos capas de búsqueda humana.
El ciclo comienza con los prompts de búsqueda, los cuales no se copian de versiones anteriores — se ensamblan bajo demanda a través de Perplexity Desktop: cada prompt combina dos capas: el Prompt Base (perfil, reglas de exclusión, etc.) + el Prompt Wrapper que contiene la fecha del día TODAY'S DATE, el modo de búsqueda, etc.)
Abre Perplexity Desktop y dale la instrucción
```plain text

Lee PROMPT LIBRARY vía MCP. <https://dub.sh/app.notion>

Recupera:

- BASE SPEC L1
- Wrapper Career Sites
- Wrapper LinkedIn
- Wrapper Aggregators

Concatena cada wrapper con BASE SPEC.

Sustituye TODAY'S DATE por la fecha actual.

Entrega los tres prompts completos listos para ejecutar.

No expliques el proceso.
No describas la arquitectura.
Entrega únicamente los prompts finales.

Recupera:

- BASE SPEC L2
- Wrapper Gemini
- Wrapper Grok
- Wrapper you.com

Concatena cada wrapper con BASE SPEC.

Sustituye TODAY'S DATE por la fecha actual.

Entrega los tres prompts completos listos para ejecutar.

No expliques el proceso.
No describas la arquitectura.
Entrega únicamente los prompts finales.
```
Puedes pedir uno o varios en el mismo mensaje; Perplexity lee Prompt Bases y Prompt Wrappers desde PROMPT LIBRARY vía MCP a Notion, los concatena en un bloque de instrucciones y fecha automáticamente, y devuelve un bloque por wrapper listo para ejecutar.
Por qué importa la fecha: TODAY'S DATE define la ventana de búsqueda activa (14 días preferente, hasta 21 con match fuerte). Un prompt con fecha incorrecta produce resultados fuera de ventana o advertencias innecesarias en todos los ítems.
Nota sobre Score 0: Si el URL_GATE detecta un link roto o inaccesible, la vacante recibe automáticamente Score 0 y Status "Archivar". Ver §6 para lógica de descarte.
∆ L1 — ACTIVE RECON
Los Prompts de L1 siempre necesitarán ser concatenados usando el Prompt de alguno de los siguientes Wrappers: Career Sites (Tier 1 → LVMH, Kering, Richemont; Tier 2 → Nike, Apple, Inditex; Tier 3 → cool DNA, agencias de experiencia), LinkedIn o Job Boards (OCC, CompuTrabajo, Indeed, Bumeran). Algunas de las opciones con las que solicitarlos a Perplexity:
```plain text

"Entrégame los prompts de L1"
"Entrégame los prompts de Career Sites"
"Entrégame el prompt de LinkedIn"
"Entrégame el prompt de Aggregators"
```
En Comet Desktop usando Perplexity con el control del navegador activado ejecutarás cada bloque en una pestaña diferente.
Cada ejecución produce un JSON independiente.
Compila los JSONs; los usarás en el paso 3.
∆ L2 — STRATEGIC SEARCH
Regresa a Perplexity Desktop y solicita en esta ocasión los prompts de L2: Prompt A, Prompt B o Prompt C.
En el caso del Prompt A siempre necesitará ser concatenado con alguno de los siguientes Wrappers: Gemini, Grok o you.com. Los Prompts B y C pueden de manera independiente. Algunas de las opciones con las que solicitarlos a Perplexity:
```plain text

"Entrégame el prompt de Gemini"
"Entrégame el prompt de Grok"
"Entrégame el prompt de you.com"
"Entrégame el prompt B"
"Entrégame el prompt C"
```
Ejecutarás cada bloque de instrucciones en su motor de búsqueda correspondiente usando Deep Research siempre que te sea posible.
Los Prompt B y C pueden ser utilizados en cualquiera de los tres motores de búsqueda.
Cada ejecución produce un JSON independiente.
Compila los JSONs; los usarás en el siguiente paso.
∆ PERPLEXITY: CONSOLIDATION & DEDUP
En preparación para entrar al Pipeline es necesario consolidar la información recopilada.
Regresarás a Perplexity Desktop y usando como base el Prompt E pegarás los JSONs de L1 + L2.
Perplexity aplicará dedup con clave compuesta brand+title+location siguiendo una jerarquía L1 > L2: de las vacantes duplicadas persistirán las instancias de L1, tomando de L2 la información que pueda complementar sus propiedades para Class A.
Perplexity entregará como respuesta un Plain Array consolidado (JSON plano sin capas anidadas), listo para Python.
Guardarás el resultado en:
```plain text

~/Documents/04-VANTAGE_CV/Layer_1/Feeds/YYYY-MM-DD_consolidated.json
```
vantage_merge.py DEPRECATED.
Nota: vantage_merge.py está deprecado. El flujo correcto es JSONs L1+L2 → Perplexity (Prompt E) → Plain Array → feed_processor.py. Jerarquía dedup L1 > L2 (ver KERNEL:CV-PIPELINE).
L3 — PASSIVE INTAKE
L3 lee los correos no leídos de Gmail que tengan asignado el label .Jobs., extrae vacantes con Groq y las escribe directamente en el Tracker. El ciclo es autónomo y corre en background vía launchd tres veces al día (08:00 · 14:00 · 21:00).
Ejecutarás manualmente si el equipo estuvo apagado en los horarios indicados o necesitas procesar backlog de Gmail antes del siguiente ciclo automático.
Ejecutarás la app LAYER 3.app desde /Applications o usando Terminal ingresando alguno de los siguientes comandos:
```bash
vl3
```
Para este momento, los siguientes filtros ya habrán sido aplicados sin consumir cuota:
Hard‑blocked (L'Oréal · Levi's/Dockers · El Palacio de Hierro)
Asuntos de agradecimiento
Newsletters
Confirmaciones de cuenta
Límites por ejecución: procesa máximo 5 correos por run (configurable en GROQ_MAX_EMAILS_PER_RUN). Si hay backlog, el script reporta cuántos quedan.
Si L3 falla: verifica que LAYER_3/config/layer_3.env existe y contiene las credenciales de Gmail, Groq y Notion. El venv hereda de LAYER_1/.venv — si Layer 1 funciona, L3 tiene el entorno listo.
∆ PIPELINE
Abre la Terminal y procesa el JSON consolidado de L1+L2:
```bash
~/vantage_pipeline.sh feed ~/Documents/04-VANTAGE_CV/Feeds/YYYY-MM-DD_consolidated.json
```
¿Qué ocurre aquí?
El script vantage_pipeline.sh actúa como wrapper: activa el entorno virtual (.venv), valida la estructura y dispara feed_processor.py para normalizar campos, aplicar dedup cross‑layer (ventana 30 días) y presentarte el DRY RUN antes de escribir en Notion.
APROBAR ESCRITURA
Revisa el DRY RUN en terminal.
El output muestra una las propiedades Class A de cada instancia a crear.
Las entradas duplicadas aparecen como SKIP.
Las que requieren revisión aparecen como REVIEW_NEEDED.
Confirma con y (yes) para escribir en Notion. Cualquier otra tecla cancela sin escribir.
Los registros con status REVIEW_NEEDED que se escriben en Notion, los resuelves en el Dashboard.
PROCESAR CON PYTHON
Para este punto las propiedades Class A de cada instancia nueva se habrán poblado por L1, L2 o L3.
Para poblar las propiedades Class B de todas las instancias pendientes en el Tracker, ejecutarás la app LAYER 1.app desde /Applications o usando Terminal:
```bash
~/vantage_pipeline.sh
```
READY‑TO‑APPLY
Abre la vista Ready-to-Apply en Notion. Vacantes con Score ≥ 60 están listas para CV Optimization en preparación para tu postulación.
∆ L4 — VERSION CONTROL & INFRASTRUCTURE
L4 sincroniza el repositorio git del sistema automáticamente en background. No requiere intervención manual en el ciclo semanal normal.
Automático: launchd corre vgit a las 09:00 · 15:00 · 21:00. Si hay cambios en el repo, hace commit con timestamp + push a origin/main. Sin cambios → silencio total.
Manual: ejecutar vgit desde Terminal en cualquier momento para forzar un sync inmediato.
Verificar último run: cat /tmp/vantage_l4_gitsync.log
Archivos: Layer_4/scripts/git_sync.py · Layer_4/wrappers/git_sync_wrapper.sh · ~/Library/LaunchAgents/com.vantage.gitsync.plist
MARTES
Qué Hacer Cuando Gate = BLOCKED
Si el bloqueo es por un campo Class A corregible, usa RT‑1 (rt1_dashboard.html): Proponer Patch → Validar → Aceptar. No uses RT‑1 para forzar un CREATE en vacantes que no cumplen score — úsalo solo para corregir datos erróneos.
Dashboard & Solve Conflicts
Resuelve los registros pendientes del ciclo del lunes: REVIEW_NEEDED · BLOCKED recuperables · NADs overdue.
Abrir el Dashboard
Ejecuta en terminal:
```bash
vd
```
El wrapper dashboard_start.sh arranca el servidor Flask en http://127.0.0.1:8000, ejecuta un smoke test automático y abre dashboard.html en el navegador. Output esperado en terminal: SMOKE PASSED — abriendo dashboard. Si el smoke falla, emite notificación sonora de error (Basso) y no abre la UI.
Partes del Dashboard
Sidebar (columna izquierda): estado de la instancia activa — instance_id, payload actual de la vacante (campos Class A como aparecen en Notion), capabilities disponibles en el estado actual (can_patch · can_validate · can_accept · can_archive) y Audit Log en tiempo real con cada evento registrado.
Panel principal (área derecha): cuatro secciones — Selector de vacante (dropdown con todas las vacantes en Gate = BLOCKED, botón Crear instancia), máquina de estados FSM (visualiza el estado actual: BLOCKED → PATCHED → RETURNED_TO_CREATE), panel de patch (formulario con campos Class A editables: URL · JD · Source_Type · Prioridad), y área de resultado de validación (PASS verde o FAIL rojo con motivo).
Botones: Crear instancia · Proponer Patch · Validar · Aceptar Patch · Archivar · Sincronizar.
Secuencia — vacante BLOCKED recuperable
Selecciona la vacante del dropdown (muestra Marca · Rol · Score · VM_Scope).
Crear instancia — abre una instancia RT‑1 en estado BLOCKED y carga el payload desde Notion. Audit Log registra domain.instance.created.
Edita los campos incorrectos en el panel de patch — solo Class A (URL · JD · Source_Type · Prioridad). Los campos Class B no son editables.
Proponer Patch — almacena la corrección. Audit Log registra domain.patch.proposed.
Validar — el backend ejecuta run_pipeline.py con el patch y verifica si el resultado sería CREATE. Si pasa: estado → PATCHED, resultado verde. Si falla: estado permanece BLOCKED, resultado rojo con motivo.
Aceptar Patch — escribe los campos Class A corregidos en Notion. Estado → RETURNED_TO_CREATE. Audit Log registra domain.patch.accepted.
Corre el pipeline para que Python recalcule:
```bash
~/vantage_pipeline.sh
```
Secuencia — vacante no recuperable
Usa el botón Archivar. El Dashboard escribe Next_Action = Archivar en Notion y cierra la instancia en estado FAILED. No pasa por el pipeline.
REVIEW_NEEDED — resolución directa
Las entradas con este status son escritas en Notion por feed_processor.py cuando no pudieron procesarse completamente: la URL era parcial o ambigua, la marca no resolvía contra el alias map, o el sistema detectó un semi‑duplicate cross‑layer que requiere revisión humana. Mientras el status permanezca en REVIEW_NEEDED, sus campos Class B (Score, Gate_Decision, VM_Scope, Role_Class) quedan bloqueados — Python no los calcula.
Contrato de resolución — 4 pasos obligatorios:
Abre la entrada en Notion e identifica el problema indicado en el campo Notas (ej. "URL parcial", "alias no resuelto: Nike México", "semi‑duplicate").
Corrige el campo problemático directamente en Notion: reemplaza la URL parcial con la URL completa, o ajusta el nombre de la marca al valor que exista en el alias map.
Cambia Status → Target. Este es el único valor que Python reconoce como señal de resolución. Cualquier otro valor (incluyendo dejar REVIEW_NEEDED) mantiene el bloqueo en el siguiente run.
Corre el pipeline:
```bash
~/vantage_pipeline.sh
```
Python detecta Status = Target en entradas que tenían Gate vacío o REVIEW_NEEDED y procesa sus campos Class B normalmente — calcula Score, Gate_Decision y el resto.
Por qué Target y no otro valor: Target es el estado operativo estándar de una vacante en espera de procesamiento. Usarlo como señal de resolución mantiene el contrato de estados consistente — no requiere un valor nuevo ni lógica adicional en Python.
Estas entradas no pasan por RT‑1. RT‑1 es para vacantes con Gate = BLOCKED que ya tienen campos Class B calculados y necesitan corrección de inputs Class A.
MIÉRCOLES — CV Optimization
Optimización de CV para vacantes priorizadas en Ready-to-Apply. Claude opera activamente en este ciclo — es el único día donde el AI Component tiene rol principal. L3 sigue corriendo en sus horarios habituales.
Cómo llegan las vacantes a Claude
Abre Ready-to-Apply en Notion y elige la vacante a trabajar. Copia la URL del campo URL (career page oficial) o el texto del JD. Abre una nueva sesión de Claude y dispara:
```plain text
CV-A [URL de la vacante]
```
o pega el texto del JD directamente. Claude no accede al Tracker de forma autónoma — el trigger debe ser explícito.
CV‑A / CV‑B — Por Qué Son Sesiones Separadas
CV‑A es análisis: qué keywords posicionar, qué gaps cubrir, qué tono de marca adoptar. CV‑B es producción: el documento final. En una sesión única, el contexto de análisis contamina la voz del CV. La separación es una restricción de calidad, no de conveniencia.
Sesión 1 — CV‑A (análisis estratégico)
Claude extrae los 6 keywords de posicionamiento del JD, identifica los gaps entre los requisitos del rol y CANON:EXPERIENCE-001, determina el Positioning Mode aplicable (CANON:POSITIONING-001: N1 Luxury Brand Execution · N2 Store Design & Flagship · N3 Regional Brand Execution · N4 Commercial VM & Field Leadership) y define el tono de marca del CV.
Output de la sesión — el HANDOFF, 5 campos obligatorios:
```json

{
  "empresa": "",
  "rol": "",
  "JD_keywords_top6": ["", "", "", "", "", ""],
  "fit_gaps": ["", ""],
  "tono_marca": ""
}
```
La sesión termina aquí. No se escribe ningún CV en CV‑A.
HANDOFF — Contrato de Transferencia
CV‑B no inicia con un HANDOFF incompleto. Si cualquier campo está ausente, el sistema lo solicita antes de continuar.
```json

{
  "empresa": "",
  "rol": "",
  "JD_keywords_top6": ["", "", "", "", "", ""],
  "fit_gaps": ["", ""],
  "tono_marca": ""
}
```
Sesión 2 — CV‑B (producción del CV)
PROTOCOL UPDATE - SKELETON‑FIRST:
CV‑B ya no tiene permiso creativo sobre la estructura. El proceso es de inyección en slots.
Usar Golden Skeleton como base.
Vaciar info del Canon en slots existentes sin alterar IDs.
Abre una sesión nueva de Claude. Pega el HANDOFF completo y dispara:
```plain text
CV-B [pega el HANDOFF]
```
Claude verifica los 5 campos, cruza el HANDOFF contra CANON:OUTPUT-CONTRACT-001 para validar que bullets y KPIs sean derivados canónicos (no inventados), aplica el Positioning Mode definido en CV‑A y genera el CV bajo CANON:OUTPUT-CONTRACT-001.
El output tiene tres partes obligatorias y secuenciales:
Markdown con Figma tags — Claude entrega el archivo .md completo en la misma sesión. Cada slot va encabezado por su tag (###### figma_text_id). El operador lo revisa y autoriza antes de cualquier escritura en Notion.
Autorización explícita del operador — Claude espera confirmación antes de continuar. Sin autorización, no escribe nada.
Documentar la URL del Markdown
Regla de orden: El Markdown nunca se escribe en Notion si el operador no ha autorizado explícitamente. El orden cronológico de experiencia es invariante: C01 → C02 → C03 → C04 → C05. No se reordena por vacante ni por Positioning Mode.
Escritura en Notion (dos destinos):
Página en DERIVED OUTPUTS · ARCHIVE del Career Canon — con footer de Positioning Mode activo y fecha.
Bloque # MARKDOWN CANON ALIGNED en la página de la vacante en el Tracker — el Markdown completo con Figma tags, dentro de un bloque de código markdown.
Qué hace el usuario con el output
Con el .md autorizado en mano, el flujo hacia Figma es directo — el plugin hace el trabajo pesado:
Abre Figma Desktop y el archivo del CV.
Plugins → Development → VANTAGE CV Sync.
Copia el contenido completo del .md de CV‑B y pégalo en el área de texto del plugin.
Haz clic en Inyectar a Nodos Nativos.
Verifica la notificación: VANTAGE Sync: X nodos actualizados vía Registry V2 (ID crudo).
Revisa el lienzo visualmente y exporta: frame del CV → Export → PDF.
Si el plugin reporta Keys sin resolver, ver §5.5. Para instalar el plugin por primera vez, ver §5.5.
Sesión 3 — QA (validación antes de aplicar)
```plain text
QA [adjunta el PDF exportado]
```
Claude revisa formato y completitud con checklist de 6 ítems y entrega go/no‑go. QA no evalúa fit — evalúa que el documento esté correcto como entregable.
Cierre del ciclo de postulación
Si QA aprueba, cambia Status a Postulado en Notion y corre:
```bash
~/vantage_pipeline.sh
```
Python detecta el Status y asigna Gate_Decision = APPLIED. La vacante sale de Ready‑to‑Apply automáticamente.
JUEVES — Segunda Pasada (Condicional)
Ejecuta solo si hay nuevas vacantes que procesar — 10 minutos máximo:
```bash
~/vantage_pipeline.sh
```
Script: ~/vantage_pipeline.sh
VIERNES — Analytics
```bash
~/vantage_pipeline.sh analytics
```
Output: efectividad por fuente, tasa de links muertos por tipo de URL, ratio career pages vs. aggregators.
Acción concreta: si career pages producen menos de 5 resultados relevantes en la semana, ajusta el Prompt A — no el threshold de Score.
## 5. VANTAGE RUNTIME (Consulta Operativa) · ID: MANUAL:VANTAGE-RUNTIME-001
5.1 ¿Qué es el Runtime?
Es la herramienta de observabilidad del sistema. Permite interrogar a Notion y extraer contexto semántico sin salir de la terminal.
5.2 Comandos Principales
5.3 Cuándo correr sync
Correr sync después de:
Cualquier ciclo L1/L2 que haya escrito entradas nuevas en Notion
Después de resolver entradas REVIEW_NEEDED en el Tracker
Si status muestra "warning": "entity_index_stale" (index > 24h)
Si status muestra orphan_candidates > 0 de forma persistente
No es necesario para cambios de Status, Score, Gate_Decision en páginas individuales — esos se leen en vivo vía resolve/context.
5.4 Runtime Build — Cuándo y Para Qué
El Runtime Build regenera los tres artefactos de lectura del sistema: entity_index_v2.json, graph_v2.json y backlinks_v2.json. Se corre desde Layer_1/scripts/ con el venv activo.
Cuándo correrlo:
- Después de cualquier migración de namespaces o cambio en resolver_registry_v2.json
- Si graph_v2.json muestra self-loops inesperados (síntoma de colisión de namespace)
- Si entity_index_v2.json contiene IDs con prefix incorrecto
- Como parte del cierre formal de un release que afecte la capa de Runtime
El Build es determinísta: el mismo Registry + el mismo estado de Notion producen los mismos artefactos. Si el resultado varía entre runs sin cambios en los inputs, es una señal de problema en el Registry — no en el Build.
5.5 ARRANQUE FRÍO — Checklist de Reactivación
Usar cuando el sistema no ha sido operado por más de 5 días.
```plain text

1. Verificar entorno
      cd ~/Documents/04-VANTAGE_CV/LAYER_1/scripts
      source ../.venv/bin/activate
      python3 --version  # debe ser 3.8+

2. Verificar token Notion
      cat ../.env | grep NOTION_TOKEN  # debe estar presente y no expirado
      # Si expirado: regenerar en Notion → Settings → API → New token

3. Status del Runtime
      python3 vantage.py status
      # Revisar: total_entities, hash_coverage, index_age_hours, warning

4. Sincronizar Entity Index
      python3 vantage.py sync
      # Esperar: status: "ok", entities_after >= entities_before

5. Verificar Tracker en Notion
      Abrir VANTAGE TRACKER → vista "All"
      Buscar entradas con Status = REVIEW_NEEDED
      Resolver cada una: corregir campo → Status: Target → correr pipeline

6. Verificar L3 (layer_3_mail.py)
      Correr vl3 manualmente una vez
      Verificar heartbeat: `cat ~/.vantage/l3_heartbeat.json`
      Si falla: verificar `layer_3.env` (IMAP credentials, GROQ_API_KEY)

7. Smoke test final
      python3 vantage.py ask "show active roles"
      python3 vantage.py ask "find candidates"
      # Confirmar que la lista refleja el estado actual de Notion
```
### 5.5 Figma Sync — Uso Operativo
Ver flujo completo de inyección en §4 (Miércoles — "Qué hace el usuario con el output"). Instalación del plugin (una sola vez):
Figma Desktop → Plugins → Development → Import plugin from manifest... → navega a ~/Documents/03\ Projects/VANTAGE/Figma Sync/ → selecciona manifest.json. El plugin queda disponible permanentemente.
El plugin no modifica Notion ni el Tracker. Opera exclusivamente sobre el lienzo Figma activo.
### Gate Decisions
### Comandos de Mantenimiento del Tracker
Estos comandos operan sobre el estado del Tracker y están disponibles como subcomandos de vl1. Cada uno tiene un alcance preciso y un modo de operación por defecto.
- vl1 status
Genera un reporte de estado del Tracker en tiempo real: distribución por Gate_Decision, conteo de entradas activas (CREATE + APPLIED), entradas BLOCKED, aplicaciones de los últimos 7 días y NADs vencidas. Es el punto de partida del ciclo semanal — corre antes de cualquier otra operación para tener visibilidad del estado actual.
- vl1 analytics
Analiza la efectividad de las fuentes de discovery: qué canales producen más entradas CREATE, qué ratio de URLs funcionales tienen, cuál es el score promedio por fuente, y qué método de búsqueda (SEARCH‑WEEK, SEARCH‑EXEC, Manual) tiene mayor tasa de éxito. Corre los viernes como parte del cierre semanal.
- vl1 batch
Modo de operación por defecto: read‑only. Muestra la distribución por Status y el conteo de entradas que serían afectadas por la operación batch configurada en el script. Para ejecutar escritura, pasar el flag --execute explícitamente:
```bash
vl1 batch --execute
```
Sin --execute, el comando nunca escribe en Notion. Esta protección es permanente — no se puede desactivar sin modificar el flag.
- vl1 recovery
Verifica la consistencia de los datos en el Tracker: detecta entradas sin Score, sin VM_Scope o sin Gate_Decision. También gestiona checkpoints del pipeline — si un run anterior falló a mitad, recovery carga el último checkpoint y permite retomar desde el paso fallado. Corre cuando el pipeline reporta inconsistencias o tras un fallo inesperado.
- vl1 profile
Gestiona la configuración del perfil activo del sistema: keywords VM y de pivote, pesos de scoring, empresas target por tier y foco geográfico. Permite actualizar el perfil sin editar código — los cambios se persisten en config/profile_config.yaml. Opción 7 ("Salir sin cambios") es el exit seguro; cualquier cambio guardado requiere propagación manual a layer_1_run.py.
- vl1 backfill
Backfill de campos Class A faltantes en entradas existentes: layer, hash y Prioridad. Opera con preview obligatorio antes de escribir — muestra exactamente qué entradas serán modificadas y por qué razón se infirió el layer. Acepta --dry-run para preview sin confirmación:
```bash
vl1 backfill --dry-run
```
Sin --dry-run, solicita confirmación explícita (s) antes de cualquier escritura.
### Empresas Excluidas Permanentemente (Hard Blocks)
- L'Oréal (todas las divisiones)
- Levi Strauss & Co. (Levi's, Dockers)
- El Palacio de Hierro
- Roles store‑level sin gestión estratégica.
## 6. GESTIÓN DE DATOS · ID: MANUAL:GESTION-DATOS-001
> Hard Blocks permanentes: L'Oréal (todas las divisiones) · Levi Strauss & Co. (Levi's, Dockers) · El Palacio de Hierro · Roles store‑level sin gestión estratégica.
> Soft Blocks: recuperables vía RT‑1 (Dashboard, Martes §4).
> Dedup: ventana 30 días, clave brand+title+location, jerarquía L1>L2>L3.
## 7. TROUBLESHOOTING · ID: MANUAL:TROUBLESHOOTING-001
### Problemas Comunes y Soluciones
Pipeline no corre:
- Verificar .env en ~/vantage_notion_audit/
- Confirmar token Notion no expirado (regenerar en Notion → Settings → API → New token)
- Verificar entorno Python activo: source Layer_1/.venv/bin/activate && python --version
- Confirmar permisos de ejecución: ls -la ~/vantage_pipeline.sh (debe tener x)
Entity Index desactualizado:
- Desde v8.7.6: health_check.py detecta índices >24h y dispara vantage.py sync automáticamente en cada corrida de start — no requiere acción manual en el flujo normal.
- Síntoma de que el auto-sync falló: health_check.py reporta ✗ index — auto-sync falló o auto-sync timeout en vez del ✓ esperado.
- Solución manual (solo si el auto-sync falló): python vantage.py sync desde Layer_1/scripts
- Verificar resultado: vantage.py status debe mostrar entities_after >= entities_before
- Si persiste: verificar token Notion y conectividad a internet
L3 no procesa correos:
- Verificar layer_3.env existe en Layer_3/config/
- Confirmar credenciales: IMAP (Gmail), GROQ_API_KEY
- Ejecutar manualmente: vl3 (debe procesar hasta 5 correos)
- Revisar heartbeat: cat ~/.vantage/l3_heartbeat.json (última ejecución exitosa)
- Si falla autenticación IMAP: regenerar app password de Gmail
Figma plugin no resuelve IDs:
- Verificar registry_seed.json actualizado desde lienzo Figma
- Confirmar que code.js tiene Registry V2 embebido (variable REGISTRY al inicio)
- Comparar IDs en .md generado por CV-B vs IDs reales en capas Figma
- Si hay mismatch: regenerar registry_seed.json desde Developer Console de Figma
- Reinstalar plugin si persiste: Plugins → Development → Import plugin from manifest
Dashboard no abre:
- Verificar Flask corriendo: lsof -i :8000 (debe mostrar proceso Python)
- Ejecutar smoke test: vd debe imprimir "SMOKE PASSED — abriendo dashboard"
- Si falla smoke test: revisar dashboard_start.sh permisos (chmod +x)
- Verificar puerto 8000 libre: killall -9 Python si hay proceso zombie
- Si error de importación: confirmar .venv activo y dependencias instaladas
REVIEW_NEEDED no se resuelve tras corregir:
- Confirmar que cambiaste Status → Target en Notion (no otro valor)
- Verificar que corrección se guardó (refrescar página Notion)
- Ejecutar pipeline: ~/vantage_pipeline.sh
- Si persiste: verificar en terminal qué campo sigue bloqueando (Python imprime razón)
- Revisar logs en ~/.vantage/logs/ para diagnóstico detallado
vl1 batch modifica entradas sin --execute:
- Bug crítico: reportar inmediatamente
- Workaround: verificar siempre con vl1 batch (sin flag) antes de ejecutar
- Confirmar que script tiene guard if not args.execute: return al inicio
vsync_doc.py falla con error "blocks.children.list() returned None":
- Bug conocido de notion-client 3.x
- Solución: vsync_doc.py usa safe_list() con httpx directo (3 reintentos)
- Si persiste: verificar que page_id sea válido y token tenga permisos de lectura
- Alternativa temporal: sync manual vía MCP Notion
Score = 0 en vacante que parece relevante:
- Verificar que URL esté activa (no 404/403)
- Confirmar que JD contenga keywords VM (Python busca términos específicos)
- Revisar VM_Scope asignado (debe ser Core/Adjacent, no Off-Target)
- Si todo está correcto: revisar pesos de scoring en profile_config.yaml
- No modificar Score manualmente (campo Class B, Python lo recalcula)
Gate = BLOCKED recuperable pero RT-1 no lo detecta:
- Confirmar que entrada aparece en dropdown del Dashboard
- Verificar que Gate_Decision = BLOCKED (no EXPIRED ni vacío)
- Si no aparece: refrescar cache de Runtime (vantage.py sync)
- Si aparece pero validación falla: revisar logs de run_pipeline.py en Dashboard
### Referencias a documentación adicional:
- Filosofía de fallo: KERNEL:FAIL-PHILOSOPHY
- Reglas de Oro: KERNEL:CV-GOLDEN-RULES
- Schema de datos: pendiente (ver Bug Tracker 390938be-fc42-81c1-9fc7-d0763295cd04)
- Gate Decisions: pendiente (ver Bug Tracker 390938be-fc42-81c1-9fc7-d0763295cd04)
## 8. PROMPTS & WRAPPERS · ID: MANUAL:PROMPTS-WRAPPERS-001
Se consultan vía MCP desde la PROMPT LIBRARY en Notion.
## 9. CHEAT SHEETS · ID: MANUAL:CHEATSHEETS-001
### Cómo la IA lee el KERNEL y el CAREER CANON (Lazy Load)
La extracción de reglas y contratos lógicos (Lazy Load) opera con la siguiente prioridad:
Prioridad A — Terminal (canónico): lazy_loader.py ejecuta Server‑Side Lazy Load. Parsea bloques hijos de la Notion API y devuelve únicamente el payload del ID solicitado. Consumo: ~150 tokens por llamada.
Prioridad B — MCP Notion: Reservado exclusivamente para escrituras (APROBAR_WRITE) y modificaciones estructurales de páginas. No se usa para lectura de reglas o contratos.
Consulte las tablas de comandos para Terminal y Scripts en la sección completa.
## 10. HEALTH CHECK · ID: MANUAL:HEALTHCHECK-001
manual-healthcheck-001
### Red Flags — Ajustar Inputs, No Sistema
- Ready-to-Apply vacío por más de 3 días → ajustar Prompt A (ver §8 — Prompts de Discovery), no el threshold
- Career pages con éxito < 50% → revisar fuentes de discovery
- Pipeline runtime > 5 min → archivar entradas inactivas
Qué es: script de arranque, lectura estricta (cero escritura salvo la excepción documentada abajo). Corre automáticamente al invocar el alias start (activa venv + carga env + ejecuta el script). También puede correrse manualmente:
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
Comportamiento del auto-sync (desde v8.7.9):
Si algún índice supera 24 horas sin actualizarse, health_check.py dispara automáticamente python3 vantage.py sync (housekeeping de rutina — no requiere aprobación del operador, no es remediación de un fallo, ver KERNEL:FAIL-PHILOSOPHY). El sync se dispara una sola vez por corrida, solo si al menos un índice cruzó el umbral — no re-sincroniza índices ya frescos, y no corre si todos están dentro del umbral.
Cómo leer el output:
- ✓ verde — check pasó.
- ! amarillo — advertencia, no bloquea (ej. índice stale antes del auto-sync, tickets pendientes).
- ✗ rojo — fallo real, contribuye al exit code final.
- Línea final Sistema OK (exit 0) vs. Sistema con issues: [lista] (exit 1).
Si el auto-sync falla: aparece ✗ index — auto-sync falló o auto-sync timeout. Esto sí es un fallo real (Golden Rules) — el script no reintenta. Acción manual:
```bash
python3 vantage.py sync
```
desde Layer_1/scripts, y verificar con vantage.py status que entities_after >= entities_before.
Tickets pendientes: se listan explícitamente solo CRÍTICO y ALTO; MEDIO/BAJO/Sin Prioridad aparecen solo como conteo — ver Notion para detalle.
Sync manual sigue disponible para forzar fuera de umbral, o si has realizado cambios masivos en el Tracker o el Canon y no quieres esperar a la siguiente corrida de start:
```bash
python3 vantage.py sync
```
La resolución de entidades depende de resolver_registry_v2.json. Este archivo no debe editarse manualmente sin verificar colisiones de hash.
Desde v2.4.0 (Runtime Contract Migration), resolver_registry_v2.json es la fuente enforced — no solo declarada — de namespace ownership. Cada tipo de entidad tiene su entity_prefix definido aquí; ningún componente del sistema puede hardcodear ni inferir un prefix. Una edición manual que asigne un prefix incorrecto producirá colisiones de namespace en el siguiente Runtime Build, lo que se manifestará como self-loops en graph_v2.json. Antes de editar: verificar el prefix activo por tipo de entidad y correr Runtime Build para confirmar que no hay colisiones.
```bash
cd $LAYER_1_DIR && source .venv/bin/activate && python3 scripts/consolidate_duplicates.py (alias: vdedup)
cd $LAYER_1_DIR && source .venv/bin/activate && python3 scripts/dedup_opportunities.py (alias: vopport)
```
## 11. CHANGELOG · ID: MANUAL:CHANGELOG-001
Registro canónico de cambios: V-CHANGELOG 390938be-fc42-80e7-b429-d7d730339353
## 12. REGLAS DE ORO PARA OPERADORES · ID: MANUAL:REGLAS-DE-ORO-001
Base: KERNEL:CV-GOLDEN-RULES.
## 13. FILOSOFÍA DE FALLO PARA OPERADORES · ID: MANUAL:FALLO-001
Base: KERNEL:FAIL-PHILOSOPHY.
Un "fallo" del sistema (URL muerta, Score = 0, Gate = BLOCKED, Ready-to-Apply vacío, JSON vacío en FEED) no es un bug — es el filtro operando correctamente. No intentes "arreglar" estos resultados manualmente ni le pidas a Claude que los fuerce.
Qué hacer en su lugar:
- URL dead → la vacante expiró, normal del mercado. No repares manualmente.
- Score = 0 → fit débil o link muerto. No subas el score a mano.
- Gate = BLOCKED → criterios no cumplidos. Si es recuperable, usa RT‑1 (Martes, §4).
- Ready-to-Apply vacío → no hay oportunidades válidas esta semana. No fuerces CREATE.
- JSON vacío en FEED → búsqueda sin resultados relevantes. No amplíes criterios sin análisis.
Ante cualquiera de estos, el sistema reporta el estado y espera tu instrucción dentro del flujo normal del pipeline.
---
## 14. SLA DE LATENCIA POST-INGESTA · ID: MANUAL:SLA-001
manual-sla-001
> Nota: El SLA "< 45 minutos" cubre únicamente el segmento Score calculado → Ready-to-Apply (Discovery → Ready-to-Apply en nomenclatura anterior). El segmento Trigger → Score depende del ciclo de ejecución de ~/vantage_pipeline.sh — no tiene SLA fijo salvo ejecución manual explícita de layer_1_run.py.
## ESTADO: v8.8.0 | ACTUALIZADO: 2026-07-04
---
### [DT-015] Normalización de IDs legacy a esquema [PREFIX]:[KEY]
- Fecha: 2026-07-05
- Alcance: MANUAL (BLOQUE 1).
- Acciones:
- Validación de coherencia con KERNEL:DOC-CONTRACT: PASS.
- Búsqueda de líneas sueltas (manual-healthcheck-001, manual-sla-001): No encontradas.
- Búsqueda de UUIDs legacy (390938be-fc42-81c1-9fc7-d0763295cd04): No localizados.
- Resultado: El MANUAL ya cumple con el esquema canónico. Sin cambios requeridos.
- Notas: 
- Los IDs 390938be-fc42-81c1-9fc7-d0763295cd04 podrían haber sido eliminados en versiones previas o nunca existieron en el documento.
---
### [DT-015] Normalización de IDs legacy a esquema [PREFIX]:[KEY]
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
