# V | MANUAL

## 01 MANUAL:OBJECTIVE
Objetivo
### ¿Qué problema que resuelve?
Una búsqueda laboral sin estructura produce cuatro fallas operativas concretas:
- Oportunidades de alta señal desaparecen antes de ser procesadas.
- Tiempo consumido en vacantes irrelevantes que no cumplen criterios mínimos.
- Aplicaciones enviadas sin datos de fit — sin score, sin análisis de keywords, sin estrategia de CV.
- Sin trazabilidad: qué se aplicó, cuándo, qué sigue.
### ¿Qué hace diferente?
- Convierte la búsqueda laboral en un pipeline con contratos de procesamiento definidos.
- Filtra antes de evaluar: 
- Links muertos → Score 0, Status Expirada. 
- Roles sin componente visual → Gate BLOCKED. 
- Empresas en lista negra → rechazadas en Discovery. 
> Las empresas excluidas permanentemente (Hard Blocks) y las reglas de deduplicación están documentadas de forma completa en MANUAL:DATA-MANAGEMENT
- Verifica antes de creer: 
- Cada URL pasa un chequeo de enlace (lo que el sistema llama internamente “URL_GATE”) antes de cualquier cálculo de fit.
- Si el link no funciona, la vacante no entra al pipeline activo. 
> El mecanismo completo de este chequeo y los pasos que le siguen están explicados en MANUAL:HOW-IT-WORKS.
- Centraliza en un solo lugar:
- Notion es la fuente única de verdad — vacantes, aplicaciones, scores, seguimiento
- Calcula con lógica determinista:
- Score 0–100 calculado por Python.
- La decisión de postulación se toma con datos, no con estimaciones.
### ¿Cuáles son los KPIs del sistema?
Métricas calculables directamente desde el Tracker, sin requerir instrumentación adicional:
- Throughput semanal — vacantes nuevas ingresadas por ciclo de feed_processor.py.
- Tasa de Gate CREATE — % de vacantes con Gate_Decision=CREATE sobre el total procesado.
- Tasa de recuperación RT-1 — % de vacantes BLOCKED que alcanzan PATCHED → CREATE vía Dashboard.
- Distribución por Positioning Mode — vacantes activas por N1–N4 (campo Positioning_Mode).
- Score promedio de vacantes CREATE — calidad promedio del pipeline activo.
Nota: el sistema no mantiene checkpoints de tiempo entre estados (ej. tiempo de ingesta a READY_TO_APPLY) — cualquier métrica de latencia queda fuera de esta lista hasta que exista un campo de timestamp dedicado.
### ¿Qué no hace el sistema?
- No busca cualquier empleo — solo roles visuales en sectores lujo, premium, cool DNA y agencias de experiencia.
- No genera volumen masivo — calidad de señal sobre cantidad de resultados.
- No aplica automáticamente — la decisión de postulación es siempre humana.
- No adivina campos faltantes — si falta información, el campo queda pendiente y el sistema lo reporta.
### ¿Qué tipo de vacantes busca?
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
- Cool DNA (Gentle Monster, Ben & Frank)
- Agencias de experiencia.
---
## 02 MANUAL:HOW-IT-WORKS
¿Cómo funciona?
### El Pipeline
- El Pipeline opera secuencialmente.
- Cada paso tiene un responsable (una capa del sistema: L1, L2, L3, Python, o el operador humano) y un output definido antes de pasar al siguiente paso.
> El detalle operativo día por día de este flujo está en MANUAL:WEEKLY-FLOW aquí se explica la lógica que sostiene ese flujo.
### Layers
El sistema se organiza en capas con responsabilidades separadas:
- L1 - Active Recon: Búsqueda activa vía prompts ejecutados en motores de búsqueda (Perplexity, Comet).
- L2 - Strategic Search: Búsqueda activa complementaria vía Gemini, Grok, you.com.
- L3 - Passive Intake: Lectura automática de correos etiquetados en Gmail.
- L4 - Documentation: mantiene sincronizados en background el repositorio de código (git) y los documentos fundacionales del sistema entre Notion y disco local.
### Responsables
- Python (Pipeline / Runtime): normaliza, deduplica, calcula Score y Gate_Decision, y expone comandos de consulta.
- Agente IA (Claude): opera el Ciclo de Sesión (Open/Close), ejecuta CV-A/CV-B en el ciclo semanal (Miércoles), y mantiene documentos fundacionales y trackers vía parches — siempre bajo DRY RUN + APROBAR_WRITE, nunca escribe sin autorización explícita del operador.
- El operador: Decide qué se postula, resuelve bloqueos recuperables vía Dashboard (Proponer Patch → Validar → Aceptar, sobre campos Class A del Tracker), autoriza escrituras y aprueba entregables.
> Este reparto de trabajo se ve en acción completa en MANUAL:WEEKLY-FLOW
### Gate Decisions
Este es uno de los conceptos que más se usa a lo largo de todo el ciclo operativo, así que conviene fijarlo aquí, antes de encontrarlo en Lunes, Martes o Miércoles sin previo aviso.
El sistema evalúa cada vacante nueva en tres pasos, siempre en este orden:
1. Link check — si la URL de la vacante no carga (404, 403, dominio caído, redirección rota), la vacante se archiva automáticamente con Score 0 y Status “Archivar”. No se calcula nada más sobre ella: un link muerto no tiene fit que evaluar. Esto es lo que el sistema llama internamente el “URL_GATE” — el primer filtro que cualquier vacante debe pasar antes de que Python invierta cómputo en analizarla.
1. Score (0–100) — si la URL funciona, Python calcula un puntaje numérico según qué tan bien encaja el rol con el perfil objetivo (Keywords de Visual Merchandising, sSctor, Seniority, Geografía). Este cálculo es determinista: mismos datos de entrada, mismo Score de salida, siempre.
Dónde aterriza, según el Score obtenido:
| SCORE | NEXT ACTION |
| --- | --- |
| 60 o más | READY-TO-APPLY: Tu bandeja de trabajo diaria — de aquí sale todo lo que trabajas en CV Optimization. |
| 40–59 | REVIEW_NEEDED: Zona gris: el sistema no descarta la vacante, pero tampoco la prioriza — la decisión de trabajarla o no es tuya. |
| Menos de 40 | ARCHIVE¹ |
- Excepción a los tres pasos: si la vacante llegó por contacto directo (Inbound, Referencia o Networking), se salta este proceso completo y entra directo como CREATE — un contacto humano pesa más que el algoritmo, porque la señal de calidad ya viene validada por una persona real, no por texto de un JD.
- Este mismo mecanismo de Gate es el que determina si una vacante queda en estado BLOCKED cuando algo en sus datos de entrada (Class A: URL, JD, Source_Type, Prioridad) es inconsistente². 
> 
¹ ¿Por qué esto no es un error que debas corregir? ver MANUAL:FAILURE-PHILOSOPHY.
² Para caso específico y cómo recuperarlo a través del Dashboard ver MANUAL:TUESDAY.**
### Soft vs Hard Blocks
El sistema aplica dos capas de exclusión para garantizar la calidad de la señal — ambas se explican con su lista completa y mecánica de recuperación en MANUAL:DATA-MANAGEMENT, pero conviene entender la diferencia conceptual desde ahora, porque ambos términos aparecen constantemente en el flujo semanal:
- Hard Blocks: Empresas o roles que nunca entrarán al sistema (ej. L’Oréal, Levi’s). Se filtran en el origen, antes de que la vacante exista siquiera como registro en Notion, y no son recuperables bajo ninguna circunstancia.
- Soft Blocks: Vacantes bloqueadas por inconsistencias en datos Class A (URL rota, JD parcial) o por Score insuficiente. A diferencia de los Hard Blocks, estas sí son recuperables — corrigiendo el dato erróneo a través del Dashboard MANUAL:WEEKLY-FLOW-002.
---
## 03 MANUAL:FAILURE-PHILOSOPHY
Filosofía de Fallo para Operadores
Base KERNEL:FAIL-PHILOSOPHY
Antes de entrar a Setup y al ciclo operativo, es necesario internalizar esto, porque vas a encontrarlo constantemente desde el primer Lunes que operes el sistema: Un “fallo” del sistema no es un bug — es el filtro operando correctamente. Los siguientes resultados son señales normales de funcionamiento, no errores que debas reparar manualmente ni forzar a que Claude “arregle”:
| RESULTADO | QUE SIGNIFICA | QUE NO HACER | QUE SI HACER |
| --- | --- | --- | --- |
| URL dead / link roto | La vacante expiró — es normal del mercado laboral, las publicaciones caducan. | No repares manualmente el link ni intentes “revivir” la vacante. | Déjala archivada. Si te parece un error de captura (ej. la URL se guardó mal, no que la vacante haya expirado), eso sí es corregible — ver MANUAL:WEEKLY-FLOW-002, Dashboard. |
| Score = 0 | El fit es débil, o el link estaba muerto (ver MANUAL:HOW-IT-WORKS, Gate Decisions, paso 1). | No subas el score a mano — es un campo Class B, calculado por Python, no editable directamente. | Si sospechas que el cálculo está mal por un dato de entrada erróneo (URL, JD), corrige el dato de entrada, no el resultado — ver MANUAL:WEEKLY-FLOW-002. |
| Gate = BLOCKED | Los criterios Class A no se cumplieron (URL rota, JD parcial, fuente no reconocida). | No lo fuerces a CREATE manualmente en Notion. | Si es recuperable, usa el Dashboard (MANUAL:WEEKLY-FLOW-002) para corregir el dato de origen y dejar que el pipeline recalcule. |
| Ready-to-Apply vacío | No hay oportunidades válidas esta semana — puede pasar, especialmente en semanas de baja actividad del mercado. | No fuerces un CREATE artificial para “llenar” la bandeja. | Espera al siguiente ciclo de discovery (Lunes), o revisa si el Prompt de búsqueda necesita ajuste (ver MANUAL:HEALTHCHECK, Red Flags). |
| JSON vacío en el Feed de discovery | La búsqueda no encontró resultados relevantes esa ejecución. | No amplíes los criterios de búsqueda sin análisis previo — podrías bajar la calidad de la señal general. | Revisa el Viernes de Analytics (MANUAL:WEEKLY-FLOW-005) antes de decidir si el prompt necesita ajuste. |
Ante cualquiera de estos casos, el sistema reporta el estado y espera tu instrucción dentro del flujo normal del PIpeline — no requiere, ni acepta bien, intervenciones manuales que intenten “corregir” el resultado en sí mismo en vez de corregir el dato de entrada que lo produjo.
---
## 04 MANUAL:SETUP
Setup
Esta sección se ejecuta una sola vez, al instalar el sistema por primera vez (o al reinstalarlo desde cero). Si el sistema ya está instalado y solo llevas varios días sin usarlo, lo que necesitas es MANUAL:COLD-START, no este capítulo completo.
### Prerrequisitos
- Cuenta de Notion con base de datos VANTAGE TRACKER activa.
- Python 3.8+ instalado en Mac.
- Acceso a Claude.
- Cuenta de Perplexity con modo Deep Research activo.
- Acceso a Gemini con modo Deep Research o Search activo.
- Acceso a You.com con modo Research o Agent activo.
- Acceso a Grok con modo DeepSearch o Think activo.
### Paso 1
Verificar Notion
- READY-TO-APPLY: Espacio de trabajo diario (Score ≥ 60).
- REVIEW_NEEDED: Vacantes en rango Score 40–59.
- ARCHIVE: Score 0 o Status Expirada.
- ALL: Administración general.
### Paso 2
Instalar Entorno Python
```bash
cd ~/Documents/03 Projects/VANTAGE/Layer_1
source .venv/bin/activate
# (el entorno ya existe; solo actívalo)
```
En Terminal, verifica la instalación, debe mostrar 3.8 o superior.
```bash
python3 --version 
```
### Paso 3 
Bootloader con Claude
Ya no es necesario realizar copy-paste manual del System Prompt maestro en cada actualización, en su lugar:
1. Las instrucciones activas deben residir exclusivamente en las Project Instructions de la plataforma. Encontrarás la referencia documental en SP:BOOTLOADER. Este es el proceso para su configuración:
Settings → Project → Project Instructions en la UI de Claude.
1. Inicia un nuevo chat. El Agente  realizará un fetch automático del Bootloader  desde Notion.
1. El Agente responde con “VANTAGE: SISTEMA SINCRONIZADO” (sin número de versión fijo — ver SP:BOOTLOADER) antes de enviar peticiones.
Nota: este setup de Claude es de una sola vez por proyecto — no se repite en cada sesión de trabajo. Lo que sí se repite en cada sesión es el Ciclo de Sesión completo, explicado en MANUAL:SESSION-CYCLE.
### Paso 4
Verificar Archivos del Sistema y Permisos de Ejecución
Confirma que los archivos del sistema existen en tu Mac en las rutas esperadas (Layer_1, Layer_3, Layer_4, Dashboard). Si reinstalas o mueves archivos, verifica permisos de ejecución:
```bash
chmod +x $LAYER_1_DIR/layer_1_pipeline.sh
chmod +x $LAYER_1_DIR/wrappers/layer_1_wrapper.sh
chmod +x $LAYER_3_DIR/wrappers/layer_3_mail.sh
chmod +x $DASHBOARD_DIR/wrappers/dashboard_start.sh
```
### Paso 5
Test Inicial del Pipeline
```bash
~/vantage_pipeline.sh tracker
```
Output esperado:
```plain text
=== VANTAGE PIPELINE STATUS ===
Ready-to-Apply: [N] vacantes
Para Revisar: [N] vacantes
…
```
Si falla: verifica que ~/vantage_notion_audit/.env existe y contiene tu token de Notion.
### Paso 6
Verificar Runtime
El Runtime (explicado en detalle en MANUAL:RUNTIME) es el motor de lectura del sistema — permite consultar el estado de Notion desde Terminal sin abrir el navegador. Antes de operar, verifica que su índice interno (el “Entity Index”, el catálogo de todas las entidades que el Runtime sabe interpretar) esté cargado:
```bash
python vantage.py status
```
Resultado esperado: Status: READY (4,200+ blocks indexed).
### Paso 7
Verificar Sync Documental
```bash
cd ~/Documents/03 Projects/VANTAGE/Layer_4/scripts
source ../../Layer_1/.venv/bin/activate
python vsync_doc.py --dry-run
```
Output esperado: 6 documentos listados con diff por documento, sin errores.
Si falla: verificar que layer_1.env exista y que el token no tenga un salto de línea (\n) embebido por error de copy-paste.
## 05 MANUAL:COLD-START
Arranque Frío
Usar cuando el sistema no ha sido operado por más de 5 días. A diferencia de MANUAL:SETUP, aquí no estás instalando nada nuevo — estás confirmando que todo lo que ya instalaste sigue funcionando después de un periodo de inactividad, antes de confiar en que el primer comando que corras te va a dar un resultado correcto.
```plain text
cd ~/Documents/03\ Projects/VANTAGE/Layer_1/scripts && \
source ../.venv/bin/activate && \
python3 --version && \
cat ../.env | grep NOTION_TOKEN && \
python3 vantage.py status && \
python3 vantage.py sync && \
vl3 && \
cat ~/.vantage/l3_heartbeat.json && \
python3 vantage.py ask "show active roles" && \
python3 vantage.py ask "find candidates"
```
### Explicación por comando
1. cd ... — te posiciona en Layer_1/scripts, donde viven vantage.py y todos los scripts del runtime.
1. source ../.venv/bin/activate — activa el virtualenv correcto (un nivel arriba de scripts), asegurando que uses las dependencias instaladas del proyecto y no el Python global.
1. python3 --version — confirma que el intérprete activo cumple el mínimo (3.8+); no bloquea el resto si falla, solo informa.
1. cat ../.env | grep NOTION_TOKEN — verifica que el token de Notion esté presente en el .env; no valida si está vigente, solo que la variable existe.
1. python3 vantage.py status — healthcheck de solo lectura: lee entity_index_v2.json y las métricas acumuladas de notion_utils, sin tocar la API.
1. python3 vantage.py sync — regenera entity_index_v2.json, graph_v2.json y backlinks_v2.json consultando Notion en vivo; sí escribe.
1. vl3 — corre layer_3_mail.py una vez, manualmente (asumiendo que vl3 es tu alias configurado para ese script).
1. cat ~/.vantage/l3_heartbeat.json — confirma que L3 corrió y dejó su heartbeat; si el archivo no existe o el timestamp es viejo, L3 falló silenciosamente.
1. python3 vantage.py ask "show active roles" — smoke test end-to-end contra el Tracker real vía resolver_layer_v1 — este es el que hoy falló por el archivo borrado en el commit 29fc7f0; seguirá fallando igual hasta que restauremos ese archivo.
1. python3 vantage.py ask "find candidates"
---
## 21. Schema Class A/B — Referencia de Campos
| CAMPO | TIPO | WRITER |
| --- | --- | --- |
| Next_Action | select | Python |
