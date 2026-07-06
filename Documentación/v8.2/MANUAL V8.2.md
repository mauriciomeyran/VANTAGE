<aside>
💡

# **DECLARACIÓN DE AUDIENCIA**

**MANUAL DE USUARIO** — escrito para el **operador humano**. Describe configuración inicial, ciclo operativo semanal, comandos y flujos de uso. Leer el Kernel no es prerrequisito para operar el sistema.

**Regla de separación:** El Manual responde *cómo*. El Kernel responde *por qué*. Nunca se mezclan.

</aside>

| **Sección** | **Contenido** | **Porción** |
| --- | --- | --- |
| 1 | OBJETIVO DE VANTAGE | CONTEXTO |
| 2 | COMO FUNCIONA | CONTEXTO |
| 3 | SETUP | OPERACIÓN |
| 4 | FLUJO PUNTA A PUNTA | OPERACIÓN |
| 5 | TERMINAL | OPERACIÓN |
| 6 | TRACKER | OPERACIÓN |
| 7 | TROUBLESHOOTING | OPERACIÓN |
| 8 | PROMPTS & WRAPPERS | REFERENCIA |
| 9 | CHEAT SHEETS | REFERENCIA |
| 10 | HEALTH CHECK | REFERENCIA |
| 11 | CHANGELOG | REFERENCIA |

## 1. OBJETIVO DE VANTAGE

### El Problema que Resuelve

Una búsqueda laboral sin estructura produce cuatro fallas operativas concretas:

- Oportunidades de alta señal desaparecen antes de ser procesadas
- Tiempo consumido en vacantes irrelevantes que no cumplen criterios mínimos
- Aplicaciones enviadas sin datos de fit — sin score, sin análisis de keywords, sin estrategia de CV
- Sin trazabilidad: qué se aplicó, cuándo, qué sigue

### Qué Hace Diferente

VANTAGE convierte la búsqueda laboral en un pipeline con contratos de procesamiento definidos.

**Filtra antes de evaluar:** Links muertos → Score 0, Status Expirada. Roles sin componente visual → Gate BLOCKED. Empresas en lista negra → rechazadas en discovery.

**Verifica antes de creer:** Cada URL pasa URL_GATE antes de cualquier cálculo de fit. Si el link no funciona, la vacante no entra al pipeline activo.

**Centraliza en un solo lugar:** Notion es la fuente única de verdad — vacantes, aplicaciones, scores, seguimiento.

**Calcula con lógica determinista:** Score 0–100 calculado por Python. La decisión de postulación se toma con datos, no con estimaciones.

### Lo que el Sistema No Hace

- No busca cualquier empleo — solo roles visuales en sectores lujo, premium, cool DNA y agencias de experiencia
- No genera volumen masivo — calidad de señal sobre cantidad de resultados
- No aplica automáticamente — la decisión de postulación es siempre humana
- No adivina campos faltantes — si falta información, el campo queda pendiente y el sistema lo reporta

### Para Quién Es Este Sistema

Perfil: Profesional senior (10+ años) en Visual Merchandising, Brand Environment, Store Design, Retail Experience. Geografía: CDMX / LATAM. Sectores target: Lujo (LVMH, Kering, Richemont), retail premium (Nike, Apple, Inditex), cool DNA (Gentle Monster, Ben & Frank), agencias de experiencia.

> Las empresas excluidas permanentemente (Hard Blocks) están documentadas en §6 — Gestión de Datos.
> 

## 2. CÓMO FUNCIONA

### Flujo General del Pipeline

El pipeline opera ecuencialmente. Cada paso tiene un responsable y un output definido.

!GPT.png

### División del Trabajo

| **Quién** | **Qué ejecuta** |
| --- | --- |
| Tú | Define empresas target, aprueba escritura, decide postulación, ajusta estrategia |
| AI Component | CV-A · CV-B · QA-contenido · CANON-UPDATE · FAST |
| Python — Scoring & Gates | Valida URLs, calcula Score, asigna Gate decisions, clasifica roles (VM/Pivote/Otro) |
| Python — FEED Processing | Dedup + normalización L1/L3 · DRY RUN · escritura Class A L1/L3 (`feed_processor.py`) |
| Notion | Persiste todo el estado del pipeline. Fuente única de verdad |

## 3. SETUP

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

cd ~/Documents/04-VANTAGE_CV/LAYER_1

source .venv/bin/activate

```jsx

(el entorno ya existe; solo actívalo)

Verifica la instalación: `python3 --version` debe mostrar 3.8 o superior.

### Paso 3 — Verificar Archivos del Sistema

Confirma que estos archivos existen en tu Mac:

| Ruta | Descripción |
| --- | --- |
| `~/vantage_pipeline.sh` → `LAYER_1/wrappers/layer_1_pipeline.sh` | Pipeline principal · alias: `vl1` |
| `~/Documents/04-VANTAGE_CV/LAYER_1/` | Core Python LAYER_1 |
| `~/Documents/04-VANTAGE_CV/LAYER_3/wrappers/layer_3_mail.sh` | LAYER_3 Gmail → Groq → Notion · alias: `vl3` |
| `~/Documents/04-VANTAGE_CV/LAYER_3/config/layer_3.env` | Credenciales Gmail · Groq · Notion |
| `~/Documents/04-VANTAGE_CV/DASHBOARD/wrappers/dashboard_start.sh` | Dashboard backend + UI · alias: `vd` |

### Permisos de Ejecución
Si reinstalás o movés archivos, verificar permisos:
```

chmod +x $LAYER_1_DIR/layer_1_pipeline.sh

chmod +x $LAYER_1_DIR/wrappers/layer_1_wrapper.sh

chmod +x $LAYER_3_DIR/wrappers/layer_3_mail.sh

chmod +x $DASHBOARD_DIR/wrappers/dashboard_start.sh

```

### Paso 4 — Test Inicial

```

~/vantage_pipeline.sh status

```jsx

Output esperado:

```

=== VANTAGE PIPELINE STATUS ===

Ready-to-Apply: [N] vacantes

Para Revisar: [N] vacantes

...

```jsx

Si falla: verifica que `~/vantage_notion_audit/.env` existe y contiene tu token de Notion.
```

## 4. FLUJO PUNTA A PUNTA

### LUNES

El lunes es el ciclo de búsqueda activa completo. Se dispara manualmente y cubre las dos capas de búsqueda humana. 

El ciclo comienza con los prompts de búsqueda, los cuales no se copian de versiones anteriores — se ensamblan bajo demanda a través de Perplexity Desktop: cada prompt combina dos capas: el Prompt Base (perfil, reglas de exclusión, etc.) + el Prompt Wrapper que contiene la fecha del día`(TODAY'S DATE)`, el modo de busqueda, etc.)

- [ ]  Abre Perplexity Desktop y dale la instrucción

```
"Entrégame el prompt de [...]"
```

Puedes pedir uno o varios en el mismo mensaje, Perplexity lee *Prompt Bases* y *Prompt Wrappers* desde PROMPT LIBRARY vía MCP a Notion, los concatena en un bloque de instrucciones y fecha automáticamente Devuelve un bloque por wrapper listo para ejecutar.>

**Por qué importa la fecha:** `TODAY'S DATE` define la ventana de búsqueda activa (14 días preferente, hasta 21 con match fuerte). Un prompt con fecha incorrecta produce resultados fuera de ventana o advertencias innecesarias en todos los ítems.

---

> **Nota sobre Score 0:** Si el URL_GATE detecta un link roto o inaccesible, la vacante recibe automáticamente Score 0 y Status "Archivar". Ver §6 para lógica de descarte.
> 

#### ① L1 — ACTIVE RECON

Los Prompts de L1 siempre necesitarán de ser concatenados usando el Prompt de alguno de los siguientes Wrappers: Career Sites (Career pages de marcas Tier 1: LVMH, Kering, Richemont, Tier 2: Nike, Apple, Inditex y Tier 3: cool DNA, agencias de experiencia), LinkedIn o Job Boards (OCC, CompuTrabajo, Indeed, Bumeran). Aquí algunas de las opciones con las que solicitarlos a Perplexity:

```
"Entrégame los prompts de L1"
"Entrégame el prompts de Career Sites"
"Entrégame el prompt de LinkedIn"
"Entrégame el prompt de Aggregators"
```

- [ ]  En Comet Desktop usando Perplexity con el control del navegador activado ejecutarás cada bloque en una pestaña diferente.
- [ ]  Cada ejecución produce un JSON independiente.
- [ ]  Compila los JSONs, los usarás enn el paso 3.

---

#### ② L2 — STRATEGIC SEARCH

Regresa a Perplexity Desktop y solicita en esta ocasión los prompts de L2: Prompt A, Prompt B o Prompt C. 

En el caso del Prompt A siempre necesitará ser concatenado con alguno de los siguientes Wrappers: Gemini, Grok o you.com. Los Prompts B y C pueden de manera independiente.

Aquí algunas de las opciones con las que solicitarlos a Perplexity:

```
"Entrégame el prompts de Gemini"
"Entrégame el prompt de Grok"
"Entrégame el prompt de you.com"
"Entrégame en prompt B"
"Entrégame en prompt C"
```

- [ ]  Ejecutarás cada bloque de instrucciones su motor de búsqueda correspondiente usando Deep Research siempre que te sea posible.
- [ ]  Los Prompt B y C pueden ser utilizados en cualquiera de los tres motores de búsqueda.
- [ ]  Cada ejecución produce un JSON independiente.
- [ ]  Compila los JSONs, los usarás en el siguiente paso

---

#### ③ PERPLEXITY: CONSOLIDATION & DEDUP (L0)

En preparación para entrar al Pipeline es necesario consolidar la información recopilada.

- [ ]  Regresarás a Perplexity Desktop y usando como base el Prompt E pegarás los JSONs de L1 + L2.
- [ ]  Perplexity aplicará dedup con clave compuesta `brand+title+location` siguiendo una jerarquía L1 > L2: de las vacantes duplicadas persistirán las instancias de L1, tomando de L2 la información que pueda complementar sus propiedades para Class A.
- [ ]  Perplexity entregará como respuesta un **Plain Array consolidado (**JSON plano sin capas anidadas), listo para Python.
- [ ]  Guardarás el resultado en:

```
~/Documents/04-VANTAGE_CV/Layer_1/Feeds/YYYY-MM-DD_consolidated.json
```

> ⚠️ **`vantage_merge.py` — DEPRECATED (v8.0):** Este script existió como utilidad de consolidación local pero fue reemplazado por el paso de Consolidation & Dedup de **Perplexity (L0)** vía Prompt E. No debe usarse porque no implementa la jerarquía de dedup `L1 > L2` — al unir los JSONs sin esa lógica, instancias de L2 pueden prevalecer sobre las de L1, introduciendo duplicados de menor calidad en el Tracker. El paso correcto es siempre: JSONs de L1 + L2 → Perplexity (Prompt E) → Plain Array consolidado → `feed_processor.py`.
> 

---

<aside>

#### L3 — PASSIVE INTAKE

L3 lee los correos no leídos de Gmail que tengan asignado el label `.Jobs.`, extrae vacantes con Groq y las escribe directamente en el Tracker. El ciclo es autónomo y corre en background vía launchd tres veces al día (08:00 · 14:00 · 21:00). 

- [ ]  Ejecutarás manualmente **si** el equipo estuvo apagado en los horarios indicados o necesitas procesar backlog de Gmail antes del siguiente ciclo automático.
- [ ]  Ejecutarás la app `LAYER 2.app` desde `/Applications` o usando Terminal ingresando alguno de los siguientes comandos:

```
vl3
```

Para este momento, los siguientes filtros ya habrán sido aplicados sin consumir cuota:

- Hard-blocked (L’Oréal · Levi’s/Dockers · El Palacio de Hierro)
- Asuntos de agradecimiento
- Newsletters
- Confirmaciones de cuenta

**Límites por ejecución:** procesa máximo 5 correos por run (configurable en `GROQ_MAX_EMAILS_PER_RUN`). Si hay backlog, el script reporta cuántos quedan.

- [ ]  Si L3 falla: verifica que `LAYER_3/config/layer_3.env` existe y contiene las credenciales de Gmail, Groq y Notion. El venv hereda de `LAYER_1/.venv` — si Layer 1 funciona, L3 tiene el entorno listo.
</aside>

#### ④ PIPELINE

Abre la Terminal y procesa el JSON consolidado de L1+L2:

```bash
~/vantage_pipeline.sh feed ~/Documents/04-VANTAGE_CV/Feeds/YYYY-MM-DD_consolidated.json
```

**¿Qué ocurre aquí?**

El script `vantage_pipeline.sh` actúa como wrapper: activa el entorno virtual (`.venv`), valida la estructura y dispara `feed_processor.py` para normalizar campos, aplicar dedup cross-layer (ventana 30 días) y presentarte el **DRY RUN** antes de escribir en Notion.

#### APROBAR ESCRITURA

- [ ]  Revisa el DRY RUN en terminal.
- [ ]  El output muestra una las propiedades Class A de cada instancia a crear.
- [ ]  Las entradas duplicadas aparecen como `SKIP.`
- [ ]  Las que requieren revisión aparecen como `REVIEW_NEEDED`.

<aside>

Confirma con `y` (yes) para escribir en Notion.

Cualquier otra tecla cancela sin escribir.

</aside>

Los registros con status `REVIEW_NEEDED` que se escriben en Notion, los resuelves en el Dashboard.

#### PROCESAR CON PYTHON

- [ ]  Para este punto las propiedades Class A de cada instancia nueva se habrán poblado por L1, L2 o L3.
- [ ]  Para poblar las propiedades Class B de todas las instancias pendientes en el Tracker, ejecutarás la app `LAYER 1.app` desde `/Applications` o usando Terminal:

```
~/vantage_pipeline.sh
```

### READY-TO-APPLY

Abre la vista Ready-to-Apply en Notion. Vacantes con Score ≥ 60 están listas para *CV Optimization* en preparación para tu postulación.

### MARTES

### Qué Hacer Cuando Gate = BLOCKED

Si el bloqueo es por un campo Class A corregible, usa RT-1 (`rt1_dashboard.html`): Proponer Patch → Validar → Aceptar. No uses RT-1 para forzar un CREATE en vacantes que no cumplen score — úsalo solo para corregir datos erróneos.

Dashboard & Solve Conflicts

Resuelve los registros pendientes del ciclo del lunes: `REVIEW_NEEDED` · `BLOCKED` recuperables · NADs overdue.

---

### Abrir el Dashboard

Ejecuta en terminal:

```
vd
```

El wrapper `dashboard_start.sh` arranca el servidor Flask en `http://127.0.0.1:8000`, ejecuta un smoke test automático y abre `dashboard.html` en el navegador. Output esperado en terminal: `SMOKE PASSED — abriendo dashboard`. Si el smoke falla, emite notificación sonora de error (Basso) y no abre la UI.

---

### Partes del Dashboard

**Sidebar (columna izquierda):** estado de la instancia activa — `instance_id`, payload actual de la vacante (campos Class A como aparecen en Notion), capabilities disponibles en el estado actual (`can_patch` · `can_validate` · `can_accept` · `can_archive`) y Audit Log en tiempo real con cada evento registrado.

**Panel principal (área derecha):** cuatro secciones — Selector de vacante (dropdown con todas las vacantes en `Gate = BLOCKED`, botón Crear instancia), máquina de estados FSM (visualiza el estado actual: `BLOCKED → PATCHED → RETURNED_TO_CREATE`), panel de patch (formulario con campos Class A editables: `URL · JD · Source_Type · Prioridad`), y área de resultado de validación (PASS verde o FAIL rojo con motivo).

**Botones:** Crear instancia · Proponer Patch · Validar · Aceptar Patch · Archivar · Sincronizar.

---

### Secuencia — vacante BLOCKED recuperable

1. Selecciona la vacante del dropdown (muestra Marca · Rol · Score · VM_Scope).
2. **Crear instancia** — abre una instancia RT-1 en estado `BLOCKED` y carga el payload desde Notion. Audit Log registra `domain.instance.created`.
3. Edita los campos incorrectos en el panel de patch — solo Class A (`URL · JD · Source_Type · Prioridad`). Los campos Class B no son editables.
4. **Proponer Patch** — almacena la corrección. Audit Log registra `domain.patch.proposed`.
5. **Validar** — el backend ejecuta `run_pipeline.py` con el patch y verifica si el resultado sería `CREATE`. Si pasa: estado → `PATCHED`, resultado verde. Si falla: estado permanece `BLOCKED`, resultado rojo con motivo.
6. **Aceptar Patch** — escribe los campos Class A corregidos en Notion. Estado → `RETURNED_TO_CREATE`. Audit Log registra `domain.patch.accepted`.
7. Corre el pipeline para que Python recalcule: `~/vantage_pipeline.sh`

---

### Secuencia — vacante no recuperable

Usa el botón **Archivar**. El Dashboard escribe `Next_Action = Archivar` en Notion y cierra la instancia en estado `FAILED`. No pasa por el pipeline.

---

### REVIEW_NEEDED — resolución directa

Las entradas con este status son escritas en Notion por `feed_processor.py` cuando no pudieron procesarse completamente: la URL era parcial o ambigua, la marca no resolvía contra el alias map, o el sistema detectó un semi-duplicado cross-layer que requiere revisión humana. Mientras el status permanezca en `REVIEW_NEEDED`, sus campos Class B (`Score`, `Gate_Decision`, `VM_Scope`, `Role_Class`) quedan **bloqueados** — Python no los calcula.

**Contrato de resolución — 4 pasos obligatorios:**

1. Abre la entrada en Notion e identifica el problema indicado en el campo `Notas` (ej. “URL parcial”, “alias no resuelto: Nike México”, “semi-duplicate”).
2. Corrige el campo problemático directamente en Notion: reemplaza la URL parcial con la URL completa, o ajusta el nombre de la marca al valor que exista en el alias map.
3. Cambia `Status` → **`Target`**. Este es el **único valor** que Python reconoce como señal de resolución. Cualquier otro valor (incluyendo dejar `REVIEW_NEEDED`) mantiene el bloqueo en el siguiente run.
4. Corre el pipeline:

```
~/vantage_pipeline.sh
```

Python detecta `Status = Target` en entradas que tenían `Gate` vacío o `REVIEW_NEEDED` y procesa sus campos Class B normalmente — calcula Score, Gate_Decision y el resto.

> **Por qué `Target` y no otro valor:** `Target` es el estado operativo estándar de una vacante en espera de procesamiento. Usarlo como señal de resolución mantiene el contrato de estados consistente — no requiere un valor nuevo ni lógica adicional en Python.
> 

Estas entradas no pasan por RT-1. RT-1 es para vacantes con `Gate = BLOCKED` que ya tienen campos Class B calculados y necesitan corrección de inputs Class A.

### MIÉRCOLES

— CV Optimization

Optimización de CV para vacantes priorizadas en Ready-to-Apply. Claude opera activamente en este ciclo — es el único día donde el AI Component tiene rol principal.

L3 sigue corriendo en sus horarios habituales.

---

### Cómo llegan las vacantes a Claude

Abre Ready-to-Apply en Notion y elige la vacante a trabajar. Copia la URL del campo `URL` (career page oficial) o el texto del JD. Abre una nueva sesión de Claude y dispara:

```
CV-A [URL de la vacante]
```

o pega el texto del JD directamente. Claude no accede al Tracker de forma autónoma — el trigger debe ser explícito.

---

### CV-A / CV-B — Por Qué Son Sesiones Separadas

CV-A es análisis: qué keywords posicionar, qué gaps cubrir, qué tono de marca adoptar. CV-B es producción: el documento final. En una sesión única, el contexto de análisis contamina la voz del CV. La separación es una restricción de calidad, no de conveniencia.

### Sesión 1 — CV-A (análisis estratégico)

Claude extrae los 6 keywords de posicionamiento del JD, identifica los gaps entre los requisitos del rol y el Career Canon activo, determina el Positioning Mode aplicable (N1 Luxury Brand Execution · N2 Store Design & Flagship · N3 Regional Brand Execution · N4 Commercial VM & Field Leadership) y define el tono de marca del CV.

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

La sesión termina aquí. No se escribe ningún CV en CV-A.

---

### HANDOFF — Contrato de Transferencia

CV-B no inicia con un HANDOFF incompleto. Si cualquier campo está ausente, el sistema lo solicita antes de continuar.

```json
{
  "empresa": "",
  "rol": "",
  "JD_keywords_top6": ["", "", "", "", "", ""],
  "fit_gaps": ["", ""],
  "tono_marca": ""
}
```

### Sesión 2 — CV-B (producción del CV)

<aside>
⚙️

**PROTOCOL UPDATE - SKELETON-FIRST:**

CV-B ya no tiene permiso creativo sobre la estructura. El proceso es de **inyección en slots**.

- Usar **Golden Skeleton** (Smart Bamboo FINAL) como base.
- Vaciar info del Canon en slots existentes sin alterar IDs.
</aside>

Abre una sesión nueva de Claude. Pega el HANDOFF completo y dispara:

```
CV-B [pega el HANDOFF]
```

Claude verifica los 5 campos, cruza el HANDOFF contra el Career Canon activo para validar que bullets y KPIs sean derivados canónicos (no inventados), aplica el Positioning Mode definido en CV-A y genera el CV bajo Output Contract v1.0.

El output tiene **tres partes obligatorias y secuenciales**:

1. **Markdown con Figma tags** — Claude entrega el archivo `.md` completo en la misma sesión. Cada slot va encabezado por su tag (`###### figma_text_id`). El operador lo revisa y autoriza antes de cualquier escritura en Notion.
2. **Autorización explícita del operador** — Claude espera confirmación antes de continuar. Sin autorización, no escribe nada en Notion.

---

### Documentar la URL del Markdown

**Regla de orden:** El Markdown nunca se escribe en Notion si el operador no ha autorizado explícitamente. El orden cronológico de experiencia es invariante: C01 → C02 → C03 → C04 → C05. No se reordena por vacante ni por Positioning Mode.

**Escritura en Notion (dos destinos):**

- Página en `DERIVED OUTPUTS · ARCHIVE` del Career Canon — con footer de Positioning Mode activo y fecha.
- Bloque `# MARKDOWN CANON ALIGNED` en la página de la vacante en el Tracker — el Markdown completo con Figma tags, dentro de un bloque de código `plain text`.

---

### Qué hace el usuario con el output

Copia el contenido del .md con Figma tags. Abre `CANON_MARKDOWN.md` en tu editor (o directo en Figma via plugin). Reemplaza los slots variables con los valores entregados por Claude. Exporta el CV a PDF desde Figma.

---

### Sesión 3 — QA (validación antes de aplicar)

```
QA [adjunta el PDF exportado]
```

Claude revisa formato y completitud con checklist de 6 ítems y entrega go/no-go. QA no evalúa fit — evalúa que el documento esté correcto como entregable.

---

### Cierre del ciclo de postulación

Si QA aprueba, cambia Status a `Postulado` en Notion y corre:

```
~/vantage_pipeline.sh
```

Python detecta el Status y asigna `Gate_Decision = APPLIED`. La vacante sale de Ready-to-Apply automáticamente.

### JUEVES

— Segunda Pasada (Condicional)

Ejecuta solo si hay nuevas vacantes que procesar — 10 minutos máximo:

```
~/vantage_pipeline.sh
```

> Script: `~/vantage_pipeline.sh`
> 

### VIERNES

— Analytics

```
~/vantage_pipeline.sh analytics
```

Output: efectividad por fuente, tasa de links muertos por tipo de URL, ratio career pages vs. aggregators.

**Acción concreta:** si career pages producen menos de 5 resultados relevantes en la semana, ajusta el Prompt A — no el threshold de Score.

## 5. TRIGGERS

Cada comando define un contrato de entrada, proceso y salida. Para mantener claridad operativa, esta sección separa los comandos por entorno: **Claude y Terminal.**

### CLAUDE

| **Comando** | **Cuándo usarlo** | **Input** | **Output** |
| --- | --- | --- | --- |
| **STATUS** | No entiendes el output de Terminal | Output de `~/vantage_pipeline.sh` | Explicación + próximos pasos |
| **SYNC** | Resumen ejecutivo del pipeline | Ninguno (lee Notion vía MCP) | Reporte ≤ 12 líneas, datos puros |
| **CV-A** | Decidiste aplicar a una vacante | URL de la vacante | HANDOFF 5 campos |
| **CV-B** | Después de CV-A, en sesión nueva | HANDOFF completo de CV-A | CV en Markdown |
| **QA** | CV exportado a PDF, antes de aplicar | PDF del CV | Checklist 6 ítems + go/no-go |
| **CANON-UPDATE** | Cambió algo en tu perfil | Descripción del cambio | Canon actualizado en Notion + archivo `.md` con Figma tags (Output Contract v1.0) |

### TERMINAL

| **Comando** | **Cuándo usarlo** | **Input** | **Output** |
| --- | --- | --- | --- |
| **FEED** | Lunes o martes, tras ejecutar los motores | JSON de vacantes | DRY RUN → confirmación `s` → Notion (Class A) |
| **FAST [URL]** | Vacante puntual encontrada fuera del ciclo | URL o texto JD | DRY RUN de entrada única |
| **MAINT** | Procesar nuevas ingestas | Ninguno | Pipeline run |
| **mail** | Run manual de Layer 2 | Ninguno | Procesamiento inmediato de backlog Gmail |

### FEED — Flujo Completo

Este intercambio ocurre en **terminal** vía `feed_processor.py` — no en una sesión de chat con Claude. `[Sistema]` en el ejemplo de abajo es `feed_processor.py`.

```
[Tú]
~/vantage_pipeline.sh feed
[Pega JSON cuando el script lo solicite]

[Sistema]
DRY RUN — X vacantes post-dedup:
| Op | Empresa | Rol | Source_Type | Prioridad | Status |
...
¿Confirmar escritura? [s/N]

[Tú]
s

[Sistema]
✓ X vacantes escritas en Notion
Pipeline continuará en el siguiente run.
```

### ERRORES COMUNES EN FEED

- JSON mal formado → el sistema solicita corrección antes de continuar.
- Duplicados detectados → marcados en DRY RUN, omitidos en escritura.
- Más de 10 vacantes → divididas en lotes secuenciales de 10.
- Más de una URL en FAST → el modo  --fast  acepta exactamente 1 vacante. Si el array contiene más de un ítem, el sistema rechaza la operación con un error explícito e indica el comando correcto para FEED. Para procesar dos o más vacantes puntuales, usa FEED sin  --fast .

---

## 6. TRACKER

#### Por Qué Score Puede Ser 0

Score 0 no es un error. Es el output correcto en estos tres casos:

- **URL dead** — el link no responde → Python marca `Expirada` → Score 0.
- **Fetch Bloqueado** — la página existe pero no es accesible → Score 0.
- **Status Expirada** — marcada manualmente como expirada → Score 0.

El sistema funciona correctamente cuando produce un Score 0. Significa que el filtro operó como se esperaba.

---

#### Gate Decisions

| **Gate / Status** | **Qué significa** | **Quién resuelve** |
| --- | --- | --- |
| **CREATE** | Vacante válida — pasa al pipeline activo | Python |
| **BLOCKED** | No cumple criterios mínimos — filtrada | RT-1 (si campos Class A son corregibles) |
| **APPLIED** | Ya postulaste — protección contra duplicación | N/A |
| **REVIEW_NEEDED** | Alias no resuelve, URL parcial o semi-duplicado. `feed_processor.py` escribe la entrada; el operador resuelve antes del siguiente ciclo | Operador (Dashboard) |
| **EXPIRED** | URL dead en ≥ 2 runs consecutivos — campo Class B | Python (automático) |

**Zona Score 40–59 — Para Revisar:** las vacantes en este rango no pasan automáticamente a CREATE ni son bloqueadas. Requieren auditoría manual: revisa el JD, verifica si el rol tiene componente visual no detectado por Python, y decide si corriges un campo Class A para reprocesar o archivas la entrada. Esta decisión es exclusivamente humana — el sistema no la toma.

---

#### Bypass — Cuándo y Cómo

Bypass omite URL_GATE, Score threshold y Visual Signal detection. Se usa exclusivamente cuando la señal humana supera la señal algorítmica.

**Casos válidos:** referencia directa de un contacto · Inbound (la empresa te contactó) · Networking (conoces al hiring manager).

**Tres campos relacionados con el origen — no son intercambiables:**

| Campo | Clase | Quién escribe | Propósito | ¿Python lo sobreescribe? |
| --- | --- | --- | --- | --- |
| `Source_Type` | Class A | Tú o `feed_processor.py` | Activa la lógica de Bypass cuando vale `Referencia`, `Inbound` o `Networking`. Para vacantes normales, `feed_processor.py` lo asigna como `Vacante`. Si tú lo escribes manualmente, Python lo respeta — no lo sobreescribe. | No |
| `Fuente_Manual` | Class A | Solo tú | Etiqueta de origen humano persistente. Úsalo para guardar contexto que Python no puede inferir: “Carlos de Zegna me lo pasó”, “salió en newsletter de Retail Insider”. Python nunca toca este campo. | No |
| `Fuente` | Class B | Solo Python | Python lo calcula del URL en cada run y siempre prevalece. Si escribes algo aquí manualmente, desaparece en el siguiente `~/vantage_pipeline.sh`. | Sí — siempre |

> **Regla práctica:** Para activar Bypass → `Source_Type`. Para dejar una nota de dónde salió la vacante → `Fuente_Manual`. Nunca escribas en `Fuente`.
> 

Para activarlo:

1. Crea la vacante manualmente en Notion.
2. En el campo Source_Type, selecciona `Referencia`, `Inbound` o `Networking`.
3. Python detecta el Source_Type en el siguiente run y asigna `Gate_Decision = CREATE` automáticamente. El cambio no es visible en Notion hasta que corra el siguiente `~/vantage_pipeline.sh`.

---

#### Empresas Excluidas Permanentemente (Hard Blocks)

Estas empresas no entran al sistema bajo ningún `Source_Type`, incluyendo Referencia, Inbound o Networking.

- L’Oréal (todas las divisiones: Luxe, Paris, Maybelline, Lancôme, etc.)
- Levi Strauss & Co. (Levi’s, Dockers)
- El Palacio de Hierro (todas las unidades)
- Roles store-level sin gestión de presupuesto, proveedores o multi-tienda

---

#### Prioridad 1–6 — Criterio Estratégico del Usuario

| **Nivel** | **Criterio** | **Ejemplo** |
| --- | --- | --- |
| 1 | Cierra pronto, insider o encaje perfecto | Dior VM Manager con referencia |
| 2 | Innovation DNA o timing sensible | Nike flagship opening |
| 3 | Visual Signal sólido | Brand environment sin restricciones |
| 4 | Default sin señales adicionales | VM Coordinator genérico |
| 5 | Exploratorio activo, timing incierto | Empresa target sin vacante confirmada |
| 6 | Radar pasivo, especulativo | Cierre estimado > 60 días |

---

#### CLASS A VS CLASS B (Ownership Matrix)

Cada campo (propiedad) del Tracker (Schema) ya tiene definido quién escribe en él, a eso le llamamos Ownership. Un campo pertenece a alguna de las siguientes dos clases, nunca a las dos al mismo tiempo:

**Class A (Human-Only / Discovery)**

| **Propiedad** | **Descripción** |
| --- | --- |
| Marca / Brand | Nombre de la empresa o cliente final. |
| Rol / Title | Nombre de la posición. |
| URL | Link a la vacante (Career Page / Job Board). |
| JD | Job Description (texto completo o link). |
| Source_Type | Origen: L1, L2, L3, Referencia, Inbound. |
| Prioridad | Nivel de interés (1-6). |
| NAD | Next Action Date (Fecha de seguimiento). |
| Layer | L1, L2 o L3. |

**Class B (Python-Only / Calculated)**

| **Propiedad** | **Descripción** |
| --- | --- |
| Score | Puntaje 0-100 calculado por Python. |
| Gate | Decisión: CREATE, BLOCKED, APPLIED. |
| VM_Scope | Nivel de fit visual detectado. |
| Role_Class | Clasificación: VM, Pivote, Otro. |
| Next_Action | Acción operativa sugerida. |
| Status_Detail | Motivo de Gate o Score. |

<aside>

Regla de Integridad: no edites campos Class B manualmente en Notion. Python los sobreescribe en cada run. Un valor editado manualmente produce inconsistencias en el pipeline.

</aside>

---

#### DEFINICIÓN DE SEÑAL VISUAL (Visual Signal)

Se considera una **Señal Visual Positiva** cuando el JD o el ecosistema de la marca presentan:

- Mención explícita de *Store Front*, *Lighting Design* o *Materials*.
- Requerimientos de diseño de espacios físicos o *Flagship* management.
- Necesidad de interpretación de planos, renders o visuales 3D.
- Referencias a *Spatial Design* o *Art Installation* dentro de retail.

---

### Ejemplo de HANDOFF (Contrato CV-A → CV-B)

Este es el bloque de datos que Claude genera en la sesión CV-A y consume en la sesión CV-B para garantizar consistencia estratégica.

<copyable label="Handoff Data" editable="false">

{

"empresa": "Gentle Monster",

"rol": "Retail Experience Coordinator",

"JD_keywords_top6": ["Store Front", "Spatial Design", "Art Installation", "Luxury Retail", "Visual Merchandising", "Lighting"],

"fit_gaps": ["No experience in Seoul market", "Direct reports count unspecified"],

"tono_marca": "Avant-garde, minimalist, futuristic, artistic"

}

</copyable>

| **Nivel** | **Criterio** | **Ejemplo** |
| --- | --- | --- |
| 1 | Cierra pronto, insider o encaje perfecto | Dior VM Manager con referencia |
| 2 | Innovation DNA o timing sensible | Nike flagship opening |
| 3 | Visual Signal sólido | Brand environment sin restricciones |
| 4 | Default sin señales adicionales | VM Coordinator genérico |
| 5 | Exploratorio activo, timing incierto | Empresa target sin vacante confirmada |
| 6 | Radar pasivo, especulativo | Cierre estimado > 60 días |

## 7. TROUBLESHOOTING

### Ready-to-Apply Vacío

**Diagnóstico:** las URLs del JSON provienen de aggregators (LinkedIn, Indeed) en lugar de career pages oficiales.

**Acción:**

1. Revisa el JSON de los motores — confirma que las URLs son `empresa.com/careers/...`.
2. Si hay aggregators, el sistema los filtra correctamente — ese es el comportamiento esperado.
3. Ejecuta nueva búsqueda usando solo Prompt A.

---

### Todo Marcado Como Expirada

**Diagnóstico:** el JSON contiene URLs de aggregators que no resisten URL_GATE.

**Acción:** esto es el comportamiento esperado. URL_GATE filtró correctamente. No hay nada que corregir en el sistema — necesitas nuevas vacantes de career pages oficiales.

---

### Score Siempre 0

**Diagnóstico:** `Fetch = Bloqueado` o `Status = Expirada` en la mayoría de entradas activas.

**Acción:** esto es el comportamiento esperado del sistema. Score 0 significa que URL_GATE filtró correctamente — no hay nada roto. Descarta esas entradas y ejecuta nuevo discovery.

---

### Pipeline Lento (> 5 min)

**Diagnóstico:** demasiadas entradas activas en VANTAGE TRACKER.

**Acción:** archiva entradas con `Score 0` y `Status = Expirada`. El volumen óptimo es ≤ 50 entradas activas.

---

### Error de Importación Python

**Diagnóstico:** entorno virtual corrupto o dependencias faltantes.

**Acción:** reinstala el entorno:

```bash
cd ~/Documents/04-VANTAGE_CV/LAYER_1
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install notion-client python-dotenv requests pyyaml --break-system-packages
```

---

### Retomar Después de una Pausa (> 2 Semanas sin Uso)

L3 continuó corriendo si el Mac estuvo encendido (08:00 · 14:00 · 21:00). Las entradas de Gmail `.Jobs` se procesaron automáticamente. Si el Mac estuvo apagado durante la pausa, ejecuta `vl3` para procesar el backlog pendiente.

Los NADs quedarán overdue. RT-1 puede tener instancias en estado `PATCHED` sin cerrar. Protocolo de recovery:

1. Ejecuta `~/vantage_pipeline.sh` — procesa el backlog de L3.
2. Abre RT-1 Dashboard — cierra o acepta instancias en estado `PATCHED` pendientes.
3. Ejecuta `SYNC` — evalúa el estado real del Tracker.
4. Archiva vacantes con `Score = 0` o `Status = Expirada`.
5. Revisa los NADs overdue y actualiza.

## 8. PROMPTS & WRAPPERS

<aside>
💡

### PROMPT A

- [ ]  Capa: L2
- [ ]  Ver en Prompt Library
- [ ]  Prompt A
</aside>

<aside>
💡

### PROMPT B

- [ ]  Capa: L2
- [ ]  Ver en Prompt Library
- [ ]  Prompt B
</aside>

<aside>
💡

### PROMPT C

- [ ]  Capa: L2
- [ ]  Ver en Prompt Library
- [ ]  Prompt C 
</aside>

<aside>
💡

### PROMPT D

- [ ]  Capa: L1
- [ ]  Ver en Prompt Library
- [ ]  Prompt D
</aside>

<aside>
💡

### PROMPT E

- [ ]  Ver en Prompt Library
- [ ]  Default mode: VALIDATION
- [ ]  Deduplica con clave brand+title+location (jerarquía L1 > L2)
- [ ]  Entrega Plain Array para FEED
- [ ]  Prompt E
</aside>

<aside>
💡

### WRAPPER CAREER SITES

- [ ]  Capa: L1
- [ ]  Ver en Prompt Library
- [ ]  Canal: Career Sites
- [ ]  Default mode: EXTRACTION
- [ ]  L1 - Wrapper Career Sites 
</aside>

<aside>
💡

### WRAPPER LINKEDIN

- [ ]  Capa: L1
- [ ]  Ver en Prompt Library
- [ ]  Canal: LinkedIn
- [ ]  Default mode: EXTRACTION
- [ ]  L1 - Wrapper LinkedIn 
</aside>

<aside>
💡

### WRAPPER AGGREGATORS

- [ ]  Capa: L1
- [ ]  Ver en Prompt Library
- [ ]  Canal: Aggregators
- [ ]  Default mode: EXTRACTION
- [ ]  L1 - Wrapper Aggregators
</aside>

<aside>
💡

### WRAPPER GEMINI

- [ ]  Capa: L2
- [ ]  Ver en Prompt Library
- [ ]  Motor: Gemini
- [ ]  Default mode: EXTRACTION
- [ ]  L2 - Wrapper Gemini
</aside>

<aside>
💡

### WRAPPER GROK

- [ ]  Capa: L2
- [ ]  Ver en Prompt Library
- [ ]  Motor: Grok
- [ ]  Default mode: EXTRACTION
- [ ]  L2 - Wrapper Grok
</aside>

<aside>
💡

### WRAPPER YOU.COM

- [ ]  Capa: L2
- [ ]  Ver en Prompt Library
- [ ]  Motor: You.com
- [ ]  Default mode: EXTRACTION
- [ ]  L2 - Wrapper you.com
</aside>

## 9. CHEAT SHEETS

### NOTION

| **Término** | **Definición** |
| --- | --- |
| Class A | Campos de datos que se escriben a través de L1, L2 o L3 |
| Class B | Campos calculados cuyo ownership pertenece a Python. Ningún otro componente los modifica |
| DRY RUN | Preview de ejecución antes de escribir en Notion. Muestra exactamente qué se va a crear |
| Gate | Decisión de filtro: CREATE, BLOCKED o APPLIED. Calculada por Python, no modificable manualmente |
| Score | Métrica 0–100 calculada por Python con lógica determinista. No estimable por el AI Component |
| URL_GATE | Primer filtro del pipeline. Verifica accesibilidad de la URL antes de cualquier cálculo de fit |
| HANDOFF | Contrato de transferencia de datos entre sesión CV-A y sesión CV-B. 5 campos obligatorios |
| Bypass | Activación de Gate_Decision = CREATE automático para Source_Type = Referencia/Inbound/Networking |
| Ready-to-Apply | Vista de Notion con vacantes en Score ≥ 60, listas para evaluar postulación |
| Visual Signal | Presencia de componente visual en el JD: fotos de espacio, renders, planos, referencias de marca física. Python lo detecta en el texto del JD. El AI Component no lo escribe ni lo estima |
| REVIEW_NEEDED | Status asignado por Python cuando alias no resuelve, URL falla parcialmente o hay semi-duplicado. Operador resuelve antes del siguiente ciclo |
| NAD | Next Action Date. Campo Class A que registra la fecha del próximo paso operativo de una vacante. Si queda overdue (fecha pasada), aparece como alerta en SYNC y en el Dashboard |
| DASHBOARD | Dashboard de recuperación de vacantes con Gate = BLOCKED. Permite corregir campos Class A y re-validar con Python sin sobreescribir el gate manualmente. Acceso: alias `vd` o `DASHBOARD.app` |

### CLAUDE

| **Comando** | **Cuándo** | **Input** |
| --- | --- | --- |
| **STATUS** | **Interpretar Terminal** | **Output terminal** |
| **SYNC** | **Resumen del pipeline** | **Ninguno** |
| **CV-A** | **Estrategia de CV** | **URL de vacante** |
| **CV-B** | **Producción de CV** | **HANDOFF de CV-A** |
| **QA** | **Validar CV antes de aplicar** | **PDF** |
| **CANON-UPDATE** | **Actualizar perfil base** | **Descripción** |

### TERMINAL

| **Comando** | **Cuándo** | **Input** |
| --- | --- | --- |
| **FEED** | **Lunes** | **JSON** |
| **FAST [URL]** | **Vacante puntual** | **URL** |
| **MAINT** | **Procesar nuevas ingestas** | **Ninguno** |
| **mail** | **Run manual Layer 2** | **Ninguno** |

### SCRIPTS

```bash
~/vantage_pipeline.sh                                               # LAYER_1 pipeline completo       (alias: vl1)
~/vantage_pipeline.sh status                                        # reporte de estado               (alias: vl1status)
~/vantage_pipeline.sh analytics                                     # efectividad de fuentes          (alias: vl1analytics)
~/vantage_pipeline.sh batch                                         # operaciones batch               (alias: vl1batch)
~/vantage_pipeline.sh recovery                                      # recuperación de pipeline        (alias: vl1recovery)
~/vantage_pipeline.sh profile                                       # evolución de perfil             (alias: vl1profile)
~/Documents/04-VANTAGE_CV/LAYER_3/wrappers/layer_3_mail.sh         # L3 Gmail → Groq → Notion       (alias: vl3)
~/Documents/04-VANTAGE_CV/DASHBOARD/wrappers/dashboard_start.sh    # DASHBOARD Flask + UI           (alias: vd)
```

### ARCHIVOS

```bash
~/vantage_pipeline.sh                                         # symlink → LAYER_1/wrappers/layer_1_wrapper.sh
~/Documents/04-VANTAGE_CV/LAYER_1/                            # Core Python LAYER_1
~/Documents/04-VANTAGE_CV/LAYER_1/config/layer_1.env          # Token de Notion
~/Documents/04-VANTAGE_CV/LAYER_3/config/layer_3.env          # Gmail · Groq · Notion (L3)
~/Documents/04-VANTAGE_CV/DASHBOARD/                          # DASHBOARD Flask
```

## 10. HEALTH CHECK

| **Indicador** | **Valor saludable** |
| --- | --- |
| Ready-to-Apply activas | 3–8 vacantes |
| Pipeline runtime | < 2 minutos |
| Career page URL success rate | > 80% |
| Ratio de rechazo | 50–70% (normal — expiración de mercado) |
| Discovery to Ready-to-Apply | < 45 minutos |
| NADs overdue | < 3 |

### Red Flags — Ajustar Inputs, No Sistema

- Ready-to-Apply vacío por más de 3 días → ajustar Prompt A (ver §8 — Prompts de Discovery), no el threshold
- Career pages con éxito < 50% → revisar fuentes de discovery
- Pipeline runtime > 5 min → archivar entradas inactivas

## 11. CHANGELOG

## v8.0 — VANTAGE · 2026-06-09

- **Renaming de capas** — Arquitectura renaming completo: Layer 3 (Active Market Reconnaissance) → **L1 — Active Recon** (Career Sites · LinkedIn · Aggregators) | Layer 1 (Strategic Search) → **L2 — Strategic Search** (Gemini · You.com · Grok) | Layer 2 (Passive Intake) → **L3 — Passive Intake** (mail_pipeline.py). Jerarquía dedup: L1 > L2 > L3.
- **Perplexity — nuevo rol canónico** — Removido de motores de extracción (no opera en Extraction Mode en job boards/career sites). Rol: **Consolidation & Dedup** — paso post-extracción del ciclo del lunes. Sigue siendo motor de ensamblaje de prompts (sin cambio).
- **Ciclo semanal actualizado (Manual §4)** — Lunes: ①L1 Active Recon ②L2 Strategic Search ③Consolidation&Dedup (Perplexity) ④feed_processor.py. Martes: Dashboard & Solve Conflicts. Miércoles: CV Optimization.
- **Kernel §3/§4/§5/§6/§13 actualizados** — Naming canónico L1/L2/L3 propagado en tabla de arquitectura, contratos de capa, flujos de datos y Search Matrix.
- **Manual §8 actualizado** — Referencias Layer 1/3 → L1/L2 en callouts de prompts y wrappers. Perplexity: rol correcto documentado.
- 
- **Canonización L0** — Perplexity renombrado a L0 - Consolidation & Dedup. No es una capa independiente — es el paso del pipeline del lunes entre extracción y FEED. Recibe 6 JSONs: L1 (Career Sites · LinkedIn · Aggregators) + L2 (Gemini · You.com · Grok). Jerarquía de dedup L1 > L2 aplicada en este paso. L3 no pasa por L0.
- **Naming wrappers L1** — Wrappers Career Sites · LinkedIn · Aggregators corregidos: Layer 3 → L1, referencias a Perplexity/Comet eliminadas. Responsabilidades canónicas: Career Sites = career pages oficiales + ATS únicamente; LinkedIn = LinkedIn Jobs únicamente; Aggregators = job boards LATAM (OCC · Indeed · Computrabajo · Bumeran).
- **Naming L2 - Prompt A** — Renombrado de “LAYER 1 - Prompt A” a “L2 - Prompt A”. Categoría LAYER 2 confirmada.
- **Kernel §3/§4/§5/§13 actualizados** — L0 propagado en arquitectura, flujos de datos, pipeline de fases y search matrix.
- **Manual §4/§8 actualizados** — PASO ③ LUNES y callout Perplexity reflejan rol L0 canónico.
- **Revisión editorial completa** — pasada única sobre Kernel y Manual. Sin cambios de arquitectura ni contratos.
- **Kernel** — §1: prohibiciones reformuladas en voz de IA operadora. §2: redundancia de "no evalúa" eliminada (referencia cruzada a §7/§15). §3: nota de implementación de jerarquía dedup agregada. §4: "Cierre obligatorio" removido (pertenece al Manual). §5: "Rol de Perplexity" consolidado como referencia cruzada. §7: columna AI Component clarificada (calidad estratégica vs. errores de formato). §8: visual_signal/innovation_dna con instrucción de ignorar sin comentar. §10: mini-ejemplo EXPIRED vs. Expirada agregado. §11: scripts/archivos reemplazados por referencia cruzada al Manual §10. §13: segunda instancia de BOUNDARY consolidada. §14: input de FEED clarificado como N/A. §15: comportamiento con JSON vacío post-DRY RUN documentado. §19: comportamiento ante solicitud de cambio inválido especificado.
- **Manual** — §1: plain text → prosa Notion. Hard Blocks movidos a §6. §2: plain text → tablas Notion; celda Python dividida en Scoring/Gates y FEED. §3: plain text narrativo → prosa Notion. §4: callout ⚠️ movido antes de PASO ①; pasos bold → H3; L3 reescrito como subsec. colapsable. §5: [Sistema] = feed_processor.py aclarado. §6: nota de timing Bypass agregada. §7: diagnósticos reformulados en voz del operador. §8: Prompts B y C URL directa → mention-page. §9: NAD y RT-1 agregados al glosario. §11: referencia a §8 en Red Flags.

## v7.5 — VANTAGE · 2026-06-06

- **Migración FEED a Python** — `feed_processor.py` asume ownership completo del ciclo FEED (Layer 1 y Layer 3). Claude queda excluido de esta operación.
- **BOUNDARY v7.5** — Kernel recibe bloque de boundary al inicio del Technical Kernel. JSON de vacantes sin trigger CV-A · FAST [URL] · CANON-UPDATE → responde: "El procesamiento de FEED está migrado a feed_processor.py."
- **Confirmación interactiva** — `feed_processor.py` presenta DRY RUN en terminal + `_dryrun.md`; escritura requiere `s` del operador.
- **REVIEW_NEEDED** — nuevo status de vacantes. Python lo asigna cuando alias no resuelve, URL falla parcialmente o hay semi-duplicado. Vacantes con este status se escriben en Notion y se revisan en Dashboard antes del siguiente ciclo.
- **Campos `layer` y `hash` agregados a Class A** — `layer` (L1/L3) y `hash` (dedup cross-layer) escritos por `feed_processor.py` en cada entrada.
- **Dedup cross-layer** — `feed_processor.py` computa hash diferenciado por tipo de URL y consulta Notion con ventana de 30 días antes de escribir.
- **Archivo DRY RUN archivado mensualmente** — estructura: `ARCHIVO → YYYY-MM MONTH → DRY RUN · YYYY-MM-DD · Layer L{1|3}`.
- **Manual §4 (LUNES) y §4 (MARTES Layer 3) actualizados** — PASOS 3 y 4 apuntan a `layer_1_pipeline.sh feed` + confirmación `s`.
- **Callout v7.5** — warning amarillo en Manual §4: Claude no participa en ciclo FEED.

## v7.4 — VANTAGE · 2026-06-06

- **Migración de ensamblaje de prompts** — responsabilidad transferida de Claude a Perplexity Desktop (vía MCP Notion). Claude queda excluido de esta operación.
- **Layer 1** — Perplexity lee Prompt A + Wrapper del motor, concatena y completa `TODAY'S DATE`. Trigger: `"entrégame el prompt de [motor]"`.
- **Layer 3** — Perplexity lee Prompt D + Wrapper del canal, concatena y completa `TODAY'S DATE`. Trigger: `"entrégame el prompt de [Career Sites | LinkedIn]"`.
- **Contrato de ejecución documentado** — Wrapper ausente en PROMPT LIBRARY = reportar y detener, no inferir. Prompt A y D no se ejecutan sin Wrapper.
- **Manual §8 actualizado** — responsable, triggers Layer 1 y Layer 3, regla de no reutilizar sesiones anteriores.
- **Manual §4 (LUNES) actualizado** — instrucciones operativas apuntan a Perplexity Desktop.
- **Kernel §13 actualizado** — contrato de ensamblaje, alcance por capa, trigger unificado.

## v7.2 — VANTAGE · 2026-06-01

- **Layer 2 — mail_pipeline.py operacional** — Reemplaza arquitectura Make → Notion raw por pipeline autónomo Gmail → Groq → Notion con Class A poblado
- **Parsing con LLM** — Groq (llama-3.3-70b) extrae rol, marca, url, holding directamente del cuerpo del email; solo roles VM/retail pasan
- **Dedup nativo en Layer 2** — query Notion por Rol + Marca antes de cada write; duplicados descartados sin write
- **Hard blocks en sender check** — L'Oréal · Levi's/Dockers · El Palacio de Hierro filtrados antes de Groq
- **Cadencia automática** — launchd · 3 runs diarios 08:00 · 14:00 · 21:00 · alias `mail` para run manual
- **§18 Arquitectura Diferida actualizada** — Email parsing (Layer 2) pasa de Deferred a Operacional

## v7.1 — VANTAGE · 2026-05-31

- **Career Canon integrado en el pipeline** — 3 patches quirúrgicos sin alterar arquitectura de capas ni ownership Class A/B
- **§ 11 CV-B** — Input ampliado: HANDOFF + Career Canon activo. Canon check obligatorio antes de generar F2. Desviaciones se reportan, no se silencian.
- **§ 7 Class A · Campo JD** — En CV-A, el AI Component cruza keywords del JD contra el Canon antes de generar el HANDOFF. Discrepancias van a `fit_gaps`.
- **§ 5 CANON-UPDATE** — Contrato completo: output = Canon en Notion + .md con Figma tags (Output Contract v1.0). Dos outputs obligatorios.
- **Output Contract v1.0** operativo — tag schema Figma + regla de dos outputs documentada en Career Canon § L
- **Career Canon** — UF01/02/03 resueltos · KPI06 cerrado (red nacional México) · P02-EN redactado · C03 normalizado a `Levi Strauss & Co. (Dockers)`

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
    - Pipeline wrapper reforzado: nunca ejecutar Python directamente, solo ~/jhs_pipeline.sh

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

# === DEDUPLICACIÓN ===

cd $LAYER_1_DIR && source .venv/bin/activate && python3 scripts/consolidate_duplicates.py    (alias: vdedup)

cd $LAYER_1_DIR && source .venv/bin/activate && python3 scripts/dedup_opportunities.py       (alias: vopport)