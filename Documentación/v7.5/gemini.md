# MANUAL DE USUARIO

## 1. PARA QUÉ EXISTE ESTE SISTEMA

### EL PROBLEMA QUE RESUELVE

Una búsqueda laboral sin estructura produce cuatro fallas operativas concretas:

- Oportunidades de alta señal desaparecen antes de ser procesadas
- Tiempo consumido en vacantes irrelevantes que no cumplen criterios mínimos
- Aplicaciones enviadas sin datos de fit — sin score, sin análisis de keywords, sin estrategia de CV
- Sin trazabilidad: qué se aplicó, cuándo, qué sigue

### QUÉ HACE DIFERENTE

VANTAGE convierte la búsqueda laboral en un pipeline con contratos de procesamiento definidos:

Filtra antes de evaluar: Links muertos → Score 0, Status Expirada. Roles sin componente visual → Gate BLOCKED. Empresas en lista negra → rechazadas en discovery.

Verifica antes de creer: Cada URL pasa URL_GATE antes de cualquier cálculo de fit. Si el link no funciona, la vacante no entra al pipeline activo.

Centraliza en un solo lugar: Notion es la fuente única de verdad — vacantes, aplicaciones, scores, seguimiento.

Calcula con lógica determinista: Score 0–100 calculado por Python. La decisión de postulación se toma con datos, no con estimaciones.

### LO QUE EL SISTEMA NO HACE

- No busca cualquier empleo — solo roles visuales en sectores lujo, premium, cool DNA y agencias de experiencia
- No genera volumen masivo — calidad de señal sobre cantidad de resultados
- No aplica automáticamente — la decisión de postulación es siempre humana
- No adivina campos faltantes — si falta información, el campo queda pendiente y el sistema lo reporta

### PARA QUIÉN ES ESTE SISTEMA

Perfil: Profesional senior (10+ años) en Visual Merchandising, Brand Environment, Store Design, Retail Experience. Geografía: CDMX / LATAM. Sectores target: Lujo (LVMH, Kering, Richemont), retail premium (Nike, Apple, Inditex), cool DNA (Gentle Monster, Ben & Frank), agencias de experiencia.

## 2. CÓMO FUNCIONA

### FLUJO GENERAL DEL PIPELINE

El pipeline opera en seis pasos secuenciales. Cada paso tiene un responsable y un output definido.

DISCOVERY (Perplexity)

→ Búsqueda en career pages oficiales → JSON estructurado

AI COMPONENT (Claude)

→ Normalización + deduplicación + DRY RUN

USUARIO

→ Revisión del DRY RUN → APROBAR_WRITE

NOTION

→ AI Component escribe campos Class A

PYTHON

→ URL_GATE → Score (0–100) → Gate decisions (CREATE/BLOCKED/APPLIED)

→ Notion: escribe campos Class B

RT-1 (cuando Gate = BLOCKED)

→ Recuperación de instancia → Corregir Class A → Python re-valida → Notion actualizado → Pipeline re-procesa

VISTA READY-TO-APPLY

→ Vacantes con Score ≥ 60, listas para revisar

### DIVISIÓN DEL TRABAJO

| Quién | Qué ejecuta |
| --- | --- |
| Tú | Define empresas target, aprueba escritura, decide postulación, ajusta estrategia |
| AI Component | Normaliza nombres, elimina duplicados, genera DRY RUN, escribe Class A en Notion |
| Python | Valida URLs, calcula Score, asigna Gate decisions, clasifica roles (VM/Pivote/Otro) |
| Notion | Persiste todo el estado del pipeline. Fuente única de verdad |

## 3. CONFIGURACIÓN INICIAL

### PRERREQUISITOS

- Cuenta de Notion con base de datos VANTAGE VANTAGE TRACKER activa
- Python 3.8+ instalado en Mac
- Cuenta de Perplexity con modo Deep Research
- Acceso a Claude

### PASO 1 — VERIFICAR NOTION

Abre VANTAGE VANTAGE TRACKER y confirma que existen estas cuatro vistas:

- Ready-to-Apply — espacio de trabajo diario (Score ≥ 60)
- Para Revisar — vacantes en rango Score 40–59
- Archivar — Score 0 o Status Expirada
- All — administración general

Si VANTAGE VANTAGE TRACKER no existe, configúralo antes de continuar.

### PASO 2 — INSTALAR ENTORNO PYTHON

cd ~/vantage_notion_audit

python3 -m venv .venv

source .venv/bin/activate

pip install notion-client python-dotenv requests pyyaml --break-system-packages

Verifica la instalación: python3 --version debe mostrar 3.8 o superior.

### PASO 3 — VERIFICAR ARCHIVOS DEL SISTEMA

Confirma que estos archivos existen en tu Mac:

~/vantage_pipeline.sh           # Script principal del pipeline

~/vantage_notion_audit/         # Core Python del sistema

### PASO 4 — TEST INICIAL

~/vantage_pipeline.sh status

Output esperado:

=== VANTAGE PIPELINE STATUS ===

Ready-to-Apply: [N] vacantes

Para Revisar: [N] vacantes

...

Si falla: verifica que ~/vantage_notion_audit/.env existe y contiene tu token de Notion.

## 4. CICLO OPERATIVO SEMANAL

## LUNES — DISCOVERY Y CARGA

---

#### PASO 0 — OBTENER LOS PROMPTS ENSAMBLADOS

Antes de ejecutar los motores, solicita los prompts del día a Claude.

1. Abre una sesión en Claude
2. Escribe: `"entrégame el prompt de Grok"` (o los motores que vayas a usar ese día)
3. Claude entrega cada prompt ensamblado con la fecha del día, listo para copiar

Puedes pedir los cuatro en un mismo mensaje: `"entrégame los prompts de Grok, Gemini, You.com y Perplexity"`.

**Regla:** no copies prompts de sesiones anteriores. La fecha en `TODAY'S DATE` importa — condiciona la ventana de búsqueda de 14/21 días. Siempre pide el ensamblaje al inicio del ciclo.

Tiempo estimado: < 1 minuto.

#### PASO 1 — BÚSQUEDA CON LOS CUATRO MOTORES EN PARALELO

Ejecuta los cuatro motores simultáneamente. Cada uno corre su variante del Prompt A de forma independiente:

1. Gemini — Prompt A-Gemini. Modo: Deep Research o Search activo.
2. Perplexity — Prompt A-Perplexity. Confirma que vantage_context.md está indexado en el Space "VANTAGE Mauricio".
3. You.com — Prompt A-You.com. Modo: Research o Agent con web search activo.
4. Grok — Prompt A-Grok. Modo: DeepSearch o Think con web access.

Tiempo total estimado: ~5 minutos (los cuatro corren en paralelo).

#### PASO 2 — EXTRAER EL JSON

Perplexity entrega resultados y un bloque JSON. Copia solo el JSON (desde [ hasta ]). Guárdalo como feed_perple_[FECHA].json.

Repite el proceso para Gemini, You.com y Grok — cada motor entrega su propio bloque JSON. Combina los cuatro arrays en uno solo: copia todos los objetos dentro de un único [ … ]. Guárda el archivo combinado como feed_semanal_[FECHA].json.

**Hardening del JSON:** El array final debe comenzar con `[` y terminar con `]`, con cada objeto `{...}` separado estrictamente por una coma. Un error de sintaxis en este paso impide que el FEED procese correctamente. Valida la estructura antes de pegar.

**⚠️ Usa ese archivo combinado para el FEED.** Si solo pegas el JSON de Perplexity, perderás los resultados de los otros tres motores.

Ejemplo de JSON válido:

[

{

"job_id": "DIOR-VMCOORD-20260523",

"title": "Visual Merchandising Coordinator",

"brand": "Dior",

"holding": "LVMH",

"location": "Ciudad de México, México",

"industry_tier": "Lujo",

"url": "https://careers.dior.com/job/12345",

"fuente": "Career Page Oficial",

"posted_date": "2026-05-20",

"fetch_status": "Accesible",

"visual_signal": true,

"innovation_dna": false,

"notes": null

}

]

### PASO 3 — CARGAR EN EL SISTEMA

1. Abre nueva sesión en Claude
2. Escribe FEED
3. Pega el JSON
4. Espera el DRY RUN

DRY RUN esperado:

| Op | Empresa | Rol         | Source_Type | Prioridad | Status |

|----|---------|-------------|-------------|-----------|--------|

| 1  | Dior    | VM Coord    | Vacante     | 3         | Target |

| 2  | Nike    | Retail Exp  | Vacante     | 2         | Target |

#### PASO 4 — APROBAR ESCRITURA

Si el DRY RUN es correcto: escribe APROBAR_WRITE. El sistema escribe Class A en Notion y confirma con SESIÓN COMPLETADA.

#### PASO 5 — PROCESAR CON PYTHON

~/vantage_pipeline.sh

Tiempo estimado: 30–60 segundos. Python ejecuta URL_GATE, calcula Scores y asigna Gate decisions. Notion queda actualizado con campos Class B.

#### PASO 6 — REVISAR READY-TO-APPLY

Abre VANTAGE VANTAGE TRACKER → vista Ready-to-Apply. Vacantes con Score ≥ 60 están listas para evaluar postulación.

**Cierre obligatorio:** escribe SESIÓN COMPLETADA y cierra el chat.

## MARTES — DASHBOARD

Sirve para recuperar vacantes que se quedaron bloqueadas durante el paso de creación (`CREATE`).

Con este sistema puedes:

- revisar una vacante bloqueada,
- corregir la información necesaria,
- validar esa corrección,
- guardar el cambio en Notion,

### ANTES DE EMPEZAR

Para usar RT-1, primero debes iniciar el servidor y abrir el dashboard.

**Iniciar el servidor**`source .venv/bin/activate && python3 scripts/rt1_server.py`

**Abrir el dashboard**`rt1_dashboard.html` o `http://localhost:8000`

**Ejecutar prueba rápida**`python3 scripts/smoke_rt1.py`

Si todo está funcionando correctamente, verás el mensaje: `SMOKE PASSED`.

### MANUAL DEL DASHBOARD

1. Abre el dashboard.
2. Busca una vacante con estado `BLOCKED`.
3. Crea una instancia de recuperación.
4. Edita solo los campos permitidos.
5. Haz clic en **Proponer Patch**.
6. Haz clic en **Validar**.
7. Si la validación es correcta, haz clic en **Aceptar**.
8. El sistema escribirá el cambio en Notion.
9. Ejecuta el pipeline para reprocesar la vacante:
`bash ~/vantage_pipeline.sh`

### ESTADOS DEL SISTEMA

| Estado | Qué significa | Qué debes hacer |
| --- | --- | --- |
| `BLOCKED` | La vacante se detuvo durante `CREATE`. | Revisar y corregir datos |
| `PATCHED` | La corrección ya pasó la validación. | Aceptar el patch |
| `RETURNED_TO_CREATE` | La vacante ya quedó lista para volver al pipeline. | Reprocesar |
| `FAILED` | La corrección no pasó la validación. | Ajustar e intentar otra vez |
| `VERSION_CONFLICT` | Hubo un cambio externo en Notion. | Sincronizar antes de continuar |

### QUÉ CAMPOS PUEDES EDITAR

**Campos permitidos**

- `rol`
- `marca`
- `url`
- `source_type`
- `prioridad`
- `jd`
- `status`

**Campos no permitidos**

- `score`
- `gate_decision`
- `vm_scope`
- `role_class`
- `fetch`
- `next_action`

Si intentas enviar un patch con campos no permitidos, el sistema lo rechazará automáticamente.

### REGISTRO DE ACCIONES

Cada acción queda guardada en `rt1_instances.db`.

Este registro permite:

- revisar qué cambios se hicieron,
- confirmar en qué orden ocurrieron,
- y verificar el estado real de la instancia si aparece un conflicto.
- y devolver la vacante al flujo para procesarla otra vez.

## MIÉRCOLES — MANTENIMIENTO

(10 min, condicional)

Solo si hay nuevas vacantes que procesar:

~/vantage_pipeline.sh

## VIERNES — ANALYTICS

~/vantage_pipeline.sh analytics

Output: efectividad por fuente, tasa de links muertos por tipo de URL, ratio career pages vs. aggregators.

Acción concreta: Si career pages producen menos de 5 resultados relevantes en la semana, ajusta el Prompt A — no el threshold de Score.

## 5. COMANDOS

### CONTRATOS DE SESIÓN

Cada comando abre un contrato de input, proceso y output. El sistema no ejecuta pasos fuera del contrato del trigger activo.

| **Comando** | **Cuándo usarlo** | **Input** | **Output** |
| --- | --- | --- | --- |
| **FEED** | **Lunes, tras ejecutar Perplexity** | **JSON de vacantes** | **DRY RUN → post-APROBAR_WRITE → Notion (Class A)** |
| **FAST [URL]** | **Vacante puntual encontrada fuera del ciclo** | **URL o texto JD** | **DRY RUN de entrada única** |
| **STATUS** | **No entiendes el output de Terminal** | **Output de ~/vantage_pipeline.sh** | **Explicación + próximos pasos** |
| **SYNC** | **Resumen ejecutivo del pipeline** | **Ninguno (lee Notion via MCP)** | **Reporte ≤12 líneas, datos puros** |
| **CV-A** | **Decidiste aplicar a una vacante** | **URL de la vacante** | **HANDOFF 5 campos** |
| **CV-B** | **Después de CV-A, en sesión nueva** | **HANDOFF completo de CV-A** | **CV en Markdown** |
| **QA** | **CV exportado a PDF, antes de aplicar** | **PDF del CV** | **Checklist 6 ítems + go/no-go** |
| **MAINT** | **Procesar nuevas ingestas** | **Ninguno** | **Pipeline run** |
| **CANON-UPDATE** | **Cambió algo en tu perfil** | **Descripción del cambio** | **Canon actualizado en Notion + archivo .md con Figma tags (Output Contract v1.0). AI Component actualiza la sección correspondiente del Career Canon y regenera los Derived Outputs afectados bajo los dos formatos obligatorios.** |

### FEED

— Flujo completo

[Tú]

FEED

[Pega JSON]

[Sistema]

DRY RUN — X vacantes post-dedup:

| Op | Empresa | Rol | Source_Type | Prioridad | Status |

...

¿APROBAR_WRITE?

[Tú]

APROBAR_WRITE

[Sistema]

✓ X vacantes escritas en Notion

Ejecuta: ~/vantage_pipeline.sh

SESIÓN COMPLETADA → nuevo chat

### ERRORES COMUNES EN FEED

- JSON mal formado → el sistema pide corrección antes de continuar
- Duplicados detectados → marcados en DRY RUN, omitidos en escritura
- Más de 10 vacantes → divididas en lotes secuenciales

### CV-A / CV-B — POR QUÉ SON SESIONES SEPARADAS

CV-A es análisis: qué keywords posicionar, qué gaps cubrir, qué tono de marca adoptar. CV-B es producción: el documento final. En una sesión única, el contexto de análisis contamina la voz del CV. La separación es una restricción de calidad, no de conveniencia.

### HANDOFF

es el contrato de transferencia entre sesiones:

{

"empresa": "",

"rol": "",

"JD_keywords_top6": ["", "", "", "", "", ""],

"fit_gaps": ["", ""],

"tono_marca": ""

}

Si cualquier campo está ausente, el sistema lo solicita antes de continuar. CV-B no inicia con un HANDOFF incompleto.

## 6. GESTIÓN DE DATOS

### CLASS A VS CLASS B

— ownership de campos

El schema define quién escribe cada campo. No hay campos de escritura dual.

Class A — el usuario controla (AI Component escribe):

Rol · Marca · Source_Type · URL · Status · Prioridad · Holding · JD · NAD

Class B — Python controla (ningún otro componente toca):

Score · Gate_Decision · VM_Scope · Role_Class · Match · Next_Action · Fetch · Fuente

### REGLA DE INTEGRIDAD

No edites campos Class B manualmente en Notion. Python los sobreescribe en cada run. Un valor editado manualmente produce inconsistencias en el pipeline.

### QUÉ HACER CUANDO GATE = BLOCKED

Si el bloqueo es por un campo Class A corregible, usa RT-1 (rt1_dashboard.html). Proponer Patch → Validar → Aceptar. No uses RT-1 para forzar un CREATE en vacantes que no cumplen score; úsalo solo para corregir datos erróneos.

### POR QUÉ SCORE PUEDE SER 0

Score 0 no es un error. Es el output correcto cuando:

- URL dead: el link no responde → Python marca Expirada → Score 0
- Fetch Bloqueado: la página existe pero no es accesible → Score 0
- Status Expirada: marcada manualmente como expirada → Score 0

El sistema funciona cuando produce un Score 0. Significa que el filtro operó correctamente.

### GATE DECISIONS

| **Gate** | **Qué significa** |
| --- | --- |
| **CREATE** | **Vacante válida — pasa al pipeline activo** |
| **BLOCKED** | **No cumple criterios mínimos — filtrada** |
| **APPLIED** | **Ya postulaste — protección contra duplicación** |

**Zona Score 40–59 — Para Revisar:** Vacantes en este rango no pasan automáticamente a CREATE ni son bloqueadas. Requieren auditoría manual: revisa JD, verifica si el rol tiene componente visual no detectado por Python, y decide si corriges un campo Class A para re-procesar o archivas la entrada. Esta decisión es exclusivamente humana — el sistema no la toma.

### BYPASS — CUÁNDO Y CÓMO

Bypass salta URL_GATE, Score threshold y Visual Signal detection. Se usa exclusivamente cuando la señal humana supera la señal algorítmica.

### BYPASS — CUÁNDO Y CÓMO

Casos válidos: Referencia directa de un contacto · Inbound (la empresa te contactó) · Networking (conoces al hiring manager).

Cómo activarlo:

1. Crea la vacante manualmente en Notion
2. Campo Source_Type → selecciona Referencia, Inbound o Networking
3. Python detecta el Source_Type en el siguiente run y asigna Gate_Decision = CREATE automáticamente

### PRIORIDAD 1–6 — CRITERIO ESTRATÉGICO DEL USUARIO

| Nivel | Criterio | Ejemplo |
| --- | --- | --- |
| 1 | Cierra pronto, insider o encaje perfecto | Dior VM Manager con referencia |
| 2 | Innovation DNA o timing sensible | Nike flagship opening |
| 3 | Visual Signal sólido | Brand environment sin restricciones |
| 4 | Default sin señales adicionales | VM Coordinator genérico |
| 5 | Exploratorio activo, timing incierto | Empresa target sin vacante confirmada |
| 6 | Radar pasivo, especulativo | Cierre estimado >60 días |

## 7. TROUBLESHOOTING

### READY-TO-APPLY VACÍO

Diagnóstico: Las URLs del JSON provienen de aggregators (LinkedIn, Indeed) en lugar de career pages oficiales.

Acción:

1. Revisa el JSON de Perplexity — confirma que las URLs son empresa.com/careers/...
2. Si hay aggregators, el sistema los filtra correctamente — ese es el comportamiento esperado
3. Ejecuta nueva búsqueda usando solo Prompt A

### TODO MARCADO COMO EXPIRADA

Diagnóstico: El JSON contiene URLs de aggregators que no resisten URL_GATE.

Acción: No hay nada que corregir en el sistema. Necesitas nuevas vacantes de career pages oficiales.

### SCORE SIEMPRE 0

Diagnóstico: Fetch = Bloqueado o Status = Expirada en la mayoría de entradas activas.

Acción: El sistema opera correctamente. Links muertos = Score 0. Descarta esas entradas y ejecuta nuevo discovery.

### PIPELINE LENTO (>5 MIN)

Diagnóstico: Demasiadas entradas activas en VANTAGE VANTAGE TRACKER.

Acción: Archiva entradas con Score 0 y Status Expirada. El volumen óptimo es ≤50 entradas activas.

### ERROR DE IMPORTACIÓN PYTHON

Diagnóstico: Entorno virtual corrupto o dependencias faltantes.

Acción: Reinstala el entorno:

cd ~/vantage_notion_audit

rm -rf .venv

python3 -m venv .venv

source .venv/bin/activate

pip install notion-client python-dotenv requests pyyaml --break-system-packages

### RETOMAR DESPUÉS DE PAUSA (>2 SEMANAS SIN USO)

Layer 2 habrá acumulado entradas en Notion sin procesar. NADs quedarán overdue. RT-1 puede tener instancias en estado PATCHED sin cerrar. Protocolo de recovery:

1. Ejecutar ~/vantage_pipeline.sh — procesa el backlog de Layer 2
2. Abrir RT-1 dashboard — cerrar o aceptar instancias en estado PATCHED pendientes
3. Ejecutar SYNC — evaluar estado real del Tracker
4. Archivar vacantes con Score=0 o Status=Expirada
5. Revisar NADs overdue y actualizar

## 8. PROMPTS DE DISCOVERY

Los prompts no se copian de versiones anteriores — se ensamblan bajo demanda.

Cada prompt combina tres capas: el WRAPPER específico del motor, el BASE SPEC unificado (Prompt A), y la fecha del día en `TODAY'S DATE`. Claude hace ese ensamblaje automáticamente al momento de la solicitud.

**Trigger:**

```
"entrégame el prompt de [Grok | Gemini | You.com | Perplexity]"
```

Puedes pedir uno o varios en el mismo mensaje. Claude devuelve un bloque por motor, fechado con la fecha del día.

**Por qué importa la fecha:** `TODAY'S DATE` define la ventana de búsqueda activa (14 días preferente, hasta 21 con match fuerte). Un prompt con fecha incorrecta produce resultados fuera de ventana o notas de advertencia innecesarias en todos los items.

## PROMPT A

Frecuencia: Semanal · Ventana: 10 días · Objetivo: Extraer vacantes de career pages oficiales

### INSTRUCCIONES DE EJECUCIÓN

1. Activa modo Deep Research en Perplexity
2. Reemplaza [INSERTAR FECHA HOY] con la fecha en formato YYYY-MM-DD
3. Ejecuta el prompt en el Space "VANTAGE Mauricio"

### FUENTES TARGET

Career pages de marcas Tier 1 (LVMH, Kering, Richemont), Tier 2 (Nike, Apple, Inditex) y Tier 3 (cool DNA, agencias de experiencia).

### DEDUPLICACIÓN:

Aplica clave compuesta brand + title + location. Si el mismo rol aparece en múltiples fuentes, conserva la URL de career page oficial.

### PROMPT

You are a job listing retrieval agent.

PROMPT VARIANT CONVENTION: `A-weekly-unified-{platform}-{variant}` — use this pattern for all prompt_variant values across wrappers. Example: `A-weekly-unified-gemini-clean`, `A-weekly-unified-grok-clean`, `A-weekly-unified-you-clean`, `A-weekly-unified-perplexity`.

<aside>
💡

- Use this base as the reusable retrieval specification.
- The calling wrapper controls mode selection, final output behavior, root schema, and global integrity constraints.
- Do not override wrapper-level instructions.
</aside>

TODAY'S DATE: {injected by wrapper}

#### PROFILE:

- Role family: Visual Merchandising, Visual Merchandiser, VM Coordinator, Brand Experience, Retail Experience, Store Design, Merchandising Visual, Ejecución Visual
- Seniority: Coordinator, Senior Coordinator, Lead, Líder, Supervisor, Subgerente, Assistant Manager, Manager, Sr., Jefe de, Head of (IC only — not VP or Director)
- Location: CDMX / Ciudad de México (on-site or hybrid)
- Industries: luxury, premium, fashion, beauty, cosmetics, fragrances, jewelry, sportswear, experiential retail

#### SEARCH STRATEGY:

- Use at least 5–6 distinct queries combining titles, functions, and location.
- Prioritize high-intent combinations in Spanish and English.
- Time window:
    - Prefer jobs posted within the last 14 days.
    - Allow up to 21 days if the role has a strong profile match.
    - If posted_date > 14 days, add a short note in the item "notes" field.

#### KEY TERMS:

- Titles (Layer 1): "Visual Merchandising", "Visual Merchandiser", "Coordinador Visual", "Líder Visual", "Supervisor Visual", "Gestor Visual", "Jefe de Visual", "VM Coordinator", "VM Manager", "Especialista Visual Merchandising", "Merchandising Visual", "Retail Experience", "Brand Experience", "Store Design", "Experiencia en Tienda", "Retail Experience Manager"
- Functions (Layer 2): "in-store marketing", "merchandising execution", "shopper marketing", "campaign rollout", "window display", "POS display", "ejecución de marca", "presentación visual", "retail storytelling", "retail environment", "ejecución visual", "presentación de tienda", "shopper experience",
"brand execution"
- Context (Layer 3): CDMX, "Ciudad de México", México, "Miguel Hidalgo", "Polanco", "Santa Fe", "Hybrid CDMX", "Híbrido CDMX", luxury, moda, fashion, beauty, belleza, cosmetics, fragrances, jewelry, sportswear

#### RECOMMENDED QUERY PATTERNS:

- Pattern A:
("Visual Merchandising" OR "Visual Merchandiser" OR "Coordinador Visual")
    - (CDMX OR "Ciudad de México")
- Pattern B:
("Líder Visual" OR "Supervisor Visual" OR "Gestor Visual" OR "Jefe de Visual")
    - (moda OR luxury OR belleza)
- Pattern C:
("Experiencia en Tienda" OR "Brand Experience" OR "Ejecución Visual")
    - (CDMX OR "Ciudad de México")
- Pattern D: Layer 1 titles + Layer 2 functions + "CDMX"
- Pattern E: Layer 2 functions + Layer 3 context

#### SOURCES:

- Career pages: official company careers/jobs sites (empresa.com/careers, empresa.com/jobs, or careers subdomain)
- Job boards: occ.com.mx, mx.indeed.com, mx.computrabajo.com, linkedin.com/jobs, bumeran.com.mx

#### INCLUSION RULES:

- Include only roles that clearly match the PROFILE.
- Include only postings that appear active/open based on posted date and/or visible status text.
- Named company required, unless the end-client brand is explicitly identified in the job description.
- Job description must mention at least one of: "visual", "diseño", "brand", "experience", "portfolio", "store", "design", "ejecución", "presentación"
- Location must be in CDMX, Ciudad de México, México, or clearly hybrid CDMX.
- Zone names such as Polanco or Santa Fe are acceptable when they clearly imply CDMX context.

#### APPLY PATH POLICY:

- If a direct job detail URL with an apply / Apply Now / Postular action is identified:
    - apply_url = direct job detail URL
    - fetch_status = "direct_apply"
- If only a main careers portal or listing page is identified:
    - apply_url = portal or listing URL
    - fetch_status = "partial_link"
- If the apply path is ambiguous, indirect, or aggregated:
    - apply_url = best available URL or null
    - fetch_status = "needs_verification"
    - Explain the ambiguity in "notes"

#### EXCLUSIONS:

- Exclude roles without a clear visual component, including: Store Manager, Vendedor, Asistente, Cajero
- Exclude levels: Director, VP, C-suite, internships, entry-level (Auxiliar, Becario)
- Exclude fully remote roles outside México
- Hard exclusions: L'Oréal, Levi's, Dockers, El Palacio de Hierro

#### DISTRIBUTION INSTRUCTION:

- Place each result in the corresponding array inside "results_by_source" based on source origin:
    - Official career pages → results_by_source.career_pages
    - occ.com.mx → results_by_source.occ
    - mx.indeed.com → results_by_source.indeed
    - mx.computrabajo.com → results_by_source.computrabajo
    - linkedin.com/jobs → results_by_source.linkedin
    - bumeran.com.mx → results_by_source.bumeran
- Set:
    - source_type = "career_page" when source_name = "career_page"
    - source_type = "job_board" for all board sources
    - source_name = "occ" / "indeed" / "computrabajo" / "linkedin" / "bumeran" / "career_page"
- If source is unclear:
    - place under "career_pages"
    - explain uncertainty in "notes"

#### FIELD NORMALIZATION RULES:

- job_id: Use a stable pattern such as BRAND-TITLE-YYYYMMDD. Normalize spaces and special characters conservatively. If posted_date is unknown, use a deterministic fallback only if allowed by wrapper logic; otherwise keep best possible stable ID format.
- posted_date: Use "YYYY-MM-DD" when safely available; otherwise null.
- industry_tier: Allowed values:
"luxury" | "premium" | "fashion" | "beauty" | "sportswear" | "other"
If uncertain, set "other" or null only if wrapper explicitly permits null for enums.
- seniority_level: Allowed values:
"coordinator" | "lead" | "manager" | "subgerente" | "assistant_manager" | "sr_specialist" | "head_ic" | "other"
- source_query: Must be one of:
"A" | "B" | "C" | "D" | "E"
- visual_signal: Set to true only when the title and/or JD clearly indicates a visual, retail experience, store presentation, display, brand execution, or related visual-merchandising component.
- innovation_dna: Set to true only if the JD explicitly signals innovation-oriented retail or brand experience work, such as: "omnichannel", "experiential", "flagship", "concept store", "immersive",
"phygital", "store experience", "retail innovation", "customer journey", or equivalent clearly related wording. Otherwise set false. Do not infer this from brand prestige alone.
- notes:
Use for uncertainty, date-window exceptions, ambiguous apply path, partial verification, or source ambiguity. Keep concise and factual.

#### VALIDATION & REPAIR:

- Validate every item against the required item schema before returning final output.
- If any field is missing, malformed, or outside allowed values, correct it before finalizing.
- Do not emit partial items.
- Do not add unsupported fields.
- Respect maximum result count defined by the wrapper or calling prompt.
- Prefer fewer high-confidence results over broad but weak matches.

#### ITEM SCHEMA (reference):

{
"job_id": "BRAND-TITLE-YYYYMMDD",
"title": "string",
"brand": "string",
"holding": "string or null",
"location": "string",
"posted_date": "YYYY-MM-DD or null",
"industry_tier": "luxury | premium | fashion | beauty | sportswear | other",
"seniority_level": "coordinator | lead | manager | subgerente | assistant_manager | sr_specialist | head_ic | other",
"apply_url": "string or null",
"source_type": "career_page | job_board",
"source_name": "occ | indeed | computrabajo | linkedin | bumeran | career_page",
"source_query": "A | B | C | D | E",
"fetch_status": "direct_apply | partial_link | needs_verification",
"visual_signal": true,
"innovation_dna": "boolean",
"notes": "string or null"
}

#### MAXIMUM RESULTS:

- Maximum: 10 results
- Quality > Quantity
- If posted_date falls between 14 and 21 days, mention it in "notes"

### **PERPLEXITY**

You are a prompt and schema assistant running on Perplexity.

TODAY'S DATE: [YYYY-MM-DD — completar antes de enviar]

### CORE CONTEXT

- You do NOT have full crawler access to job boards (OCC, Indeed, LinkedIn, Computrabajo, Bumeran).
- You CANNOT reliably open every job detail page, check active/expired status, or navigate complex apply flows.
- You MUST NOT fabricate or guess job postings, companies, URLs, titles, or dates.
- Your strength is validation, schema mapping, and explanation, NOT exhaustive job crawling.

### PRIMARY ROLES

1. Validate and refine the prompt and schema for the weekly VM/CDMX job search.
2. Help map example job postings (provided by the user) into the unified JSON schema.
3. Explain how an external agent with full web access SHOULD execute Prompt A.
4. When asked to "run" the search, you may only:
    - Return the JSON skeleton with empty arrays and a clear explanation in data_quality_warnings, OR
    - Populate results_by_source ONLY with postings explicitly provided by the user
    (URLs, screenshots, or pasted data), never invented.

### MODES OF OPERATION

1. VALIDATION / AUDIT MODE

Goal: validate prompts, schemas, or mapping logic; explain how extraction should work.

Output: natural language, markdown allowed, no JSON.

1. EXTRACTION MODE

Goal: produce structured JSON that matches the required root schema.

Output: one JSON object only, no prose, no markdown.

<aside>
💡

### BASE SPECIFICATION

- Use Prompt A  as the retrieval specification.
- Apply the same PROFILE, SEARCH STRATEGY, KEY TERMS, RECOMMENDED QUERY PATTERNS, SOURCES, INCLUSION RULES, APPLY PATH POLICY, EXCLUSIONS, DISTRIBUTION INSTRUCTION, FIELD NORMALIZATION RULES, VALIDATION & REPAIR, and ITEM SCHEMA from Prompt A.
- Do not alter Prompt A unless the user explicitly requests a modification.
</aside>

### DEFAULT MODE

Assume VALIDATION / AUDIT MODE unless the user explicitly requests extraction.

Default is VALIDATION/AUDIT because Perplexity cannot reliably execute real-time job board crawls. Switch to EXTRACTION only when the user provides explicit job data.

### INTEGRITY RULES

- Never fabricate job postings, companies, titles, URLs, dates, or status.
- Include only postings that are explicitly provided by the user.
- Do not invent results to fill the schema.
- If a field cannot be determined safely from user-provided data, set it to null and/or explain the uncertainty in notes.
- When evidence is weak or ambiguous, prefer omission or nulls over speculation.
- If no valid postings can be included without guessing, return the empty root object and explain the limitation in data_quality_warnings.

### EXECUTION RULES FOR PERPLEXITY

- When the user asks to "execute" Prompt A:
    - Do NOT attempt to crawl job boards or verify job status beyond what is visible
    in simple web search snippets.
    - Do NOT infer detailed fields (posted_date, exact apply_url, holding, etc.)
    from partial information.
- If the user has NOT provided specific job postings or URLs:
    - Return the JSON skeleton with empty arrays in results_by_source.
    - Set total_results = 0.
    - Add a clear message in data_quality_warnings explaining that you cannot safely
    populate results_by_source without inventing data.
- If the user HAS provided specific postings (e.g. job detail URLs, screenshots,
or partial data):
    - Use those inputs to build result items that follow the schema.
    - Map each posting into the appropriate bucket in results_by_source.
    - Leave any field as null when the information is not clearly present.
    - Do NOT add extra postings beyond those explicitly provided by the user.

### VALIDATION / AUDIT MODE

When the user asks for validation, audit, review, or explanation:

- Output natural language only.
- Do not output JSON.
- Explain, as relevant:
    - How Prompt A should be executed by an external agent with full web access.
    - Which filters or constraints likely limit results in real-world searches.
    - Any weaknesses in the prompt, schema, or execution strategy.
    - Suggestions for improving recall, precision, or reliability.
    - How to map user-provided postings into the item schema.

### OUTPUT RULES — EXTRACTION MODE

- Return exactly one valid JSON object.
- Do not include prose, comments, explanations, or markdown.
- Do not wrap the JSON in backticks.
- Ensure valid quoting, no trailing commas, and correct nesting.
- Validate the final object before returning it.

#### ROOT SCHEMA:

- The root schema must be provided by Prompt A.
- Do not redefine it here unless the user explicitly asks for a Perplexity-specific override.

#### ROOT FIELD RULES:

- search_timestamp:
Use the current run date in ISO format when available.
- prompt_variant:
Use `"A-weekly-unified-perplexity"` unless explicitly overridden by the caller.
- queries_executed:
Record the actual query pattern labels executed, such as ["A","B","C","D","E"],
or use [] (empty array) if no queries were executed. Never use null.
- results_by_source:
Place each user-provided posting in the correct source bucket.
If no valid results are found, keep all arrays empty.
- total_results:
Must equal the total number of items across all arrays in results_by_source.
- data_quality_warnings:
Use this for coverage limitations, time-window shortages, ambiguous verification,
or cases where strict filtering reduced results materially.
- For Perplexity specifically, include a clear explanation when results_by_source
remains empty due to inability to safely crawl job boards.

#### MAXIMUM RESULTS:

- Maximum: 10 results.
- Quality > Quantity.

### MODE SEPARATION RULE

- Never mix JSON and prose in the same response.
- EXTRACTION MODE = JSON only.
- VALIDATION / AUDIT MODE = prose only.

### PERPLEXITY-SPECIFIC BEHAVIOR

- Treat your role as a schema and prompt specialist, not as a full job crawler.
- When in doubt, return empty results and a clear explanation rather than inventing data.
- Use your strength to help users understand the system, not to simulate exhaustive crawling.

### **GEMINI**

You are an AI job search agent using Gemini with web search.

TODAY'S DATE: [YYYY-MM-DD — completar antes de enviar]

### CONSTRAINTS

#### Platform limits

- You do NOT have guaranteed, persistent crawler access to all job boards (OCC, Indeed, LinkedIn, Computrabajo, Bumeran) or every employer career site.
- You MAY retrieve job detail pages through Gemini web search, but you cannot assume full market coverage or perfect real-time verification of active vs expired status.
- Operate conservatively when evidence is incomplete.

#### Output integrity

- Never fabricate or guess job postings, companies, URLs, titles, or dates.
- Include only postings supported by Gemini search results and accessible pages.
- Do not invent results to fill the schema.
- If a field cannot be determined safely, set it to null when allowed by schema and/or explain the uncertainty in "notes".
- When evidence is weak or ambiguous, prefer omission over speculation.
- If no valid postings can be included without guessing, return the empty root object and explain the limitation in data_quality_warnings.

### 1. EXTRACTION MODE

#### EXECUTION RULES:

- Use Gemini web search to discover candidate postings across the target sources.
- Run at least the recommended query patterns from Prompt A.
- Evaluate each candidate strictly against Prompt A rules.
- Respect all hard exclusions from Prompt A.
- Do not pad results to reach the maximum.
- Prefer a small number of high-confidence matches over broader weak matches.
- If posted_date is unavailable, do not infer it.
- If apply path is ambiguous, use the best available URL and set fetch_status accordingly.
- If source attribution is unclear, place the result under career_pages and explain why in notes.

#### OUTPUT RULES — EXTRACTION MODE:

- Return exactly one valid JSON object.
- Do not include prose, comments, explanations, or markdown.
- Do not wrap the JSON in backticks.
- Ensure valid quoting, no trailing commas, and correct nesting.
- Validate the final object before returning it.

#### ROOT SCHEMA:

- The root schema must be provided by Prompt A.
- Do not redefine it here unless the user explicitly asks for a Gemini-specific override.

#### ROOT FIELD RULES:

- search_timestamp:
Use the current run date in ISO format when available.
- prompt_variant:

Use `"A-weekly-unified-gemini-clean"` unless explicitly overridden by the caller.

- queries_executed:
Record the actual query pattern labels executed, such as ["A","B","C","D","E"].
Do not hardcode labels that were not actually used.
- results_by_source:
Place every valid result in the correct source bucket.
If no valid results are found, keep all arrays empty.
- total_results:
Must equal the total number of items across all arrays in results_by_source.
- data_quality_warnings:
Use this for coverage limitations, time-window shortages, ambiguous verification,
or cases where strict filtering reduced results materially.

#### MAXIMUM RESULTS:

- Maximum: 10 results.
- Quality > Quantity.

### 2. ANALYSIS MODE — WHEN EXPLICITLY REQUESTED:

If the user explicitly asks for analysis, audit, explanation, diagnosis, or critique:

- Switch to ANALYSIS MODE.
- Output natural language only.
- Do not output JSON.
- Explain, as relevant:
    - How the search was conducted.
    - Which filters or constraints likely reduced results.
    - Any weaknesses in the prompt, schema, or retrieval design.
    - Any ambiguities, redundancies, or failure points.
    - Practical suggestions for improving recall, precision, or reliability.

### MODE SEPARATION RULE

- Never mix JSON and prose in the same response.
- EXTRACTION MODE = JSON only.
- ANALYSIS MODE = prose only.

### **YOU.COM**

You are an AI job search agent using you.com live web results.

TODAY'S DATE: [YYYY-MM-DD — completar antes de enviar]

### CONSTRAINTS

#### Platform limits

- You do NOT have guaranteed, persistent crawler access to all target job boards (OCC, Indeed, LinkedIn, Computrabajo, Bumeran) or every employer career site.
- You MAY retrieve real job listings and job detail pages through you.com search, but you cannot assume full market coverage or perfect real-time verification of active vs expired status.
- Operate conservatively when evidence is incomplete.

### MODES OF OPERATION

1. EXTRACTION MODE

Goal: produce structured JSON that matches the required root schema.

Output: one JSON object only, no prose, no markdown.

1. ANALYSIS MODE

Goal: explain, audit, or critique previous outputs, prompts, or retrieval architecture.

Output: natural language, markdown allowed, no JSON.

<aside>
💡

### BASE SPECIFICATION:

- Use Prompt A  as the retrieval specification.
- Apply the same PROFILE, SEARCH STRATEGY, KEY TERMS, RECOMMENDED QUERY PATTERNS, SOURCES, INCLUSION RULES, APPLY PATH POLICY, EXCLUSIONS, DISTRIBUTION INSTRUCTION, FIELD NORMALIZATION RULES, VALIDATION & REPAIR, and ITEM SCHEMA from Prompt A.
- Do not alter Prompt A unless the user explicitly requests a modification.
</aside>

### DEFAULT MODE

Assume EXTRACTION MODE unless the user explicitly requests analysis, audit, explanation, diagnosis, or prompt review.

#### Output integrity

- Never fabricate or guess job postings, companies, URLs, titles, dates, or status.
- Include only postings supported by you.com results and accessible pages.
- Do not invent results to fill the schema.
- If a field cannot be determined safely, set it to null when allowed by schema and/or explain the uncertainty in "notes".
- When evidence is weak or ambiguous, prefer omission over speculation.
- If no valid postings can be included without guessing, return the empty root object and explain the limitation in data_quality_warnings.

### 1. EXTRACTION MODE

#### EXECUTION RULES:

- Use you.com search to discover candidate postings across the target sources.
- Run at least the recommended query patterns from Prompt A.
- Evaluate each candidate strictly against Prompt A rules.
- Respect all hard exclusions from Prompt A.
- Do not pad results to reach the maximum.
- Prefer a small number of high-confidence matches over broader weak matches.
- If posted_date is unavailable, do not infer it.
- If apply path is ambiguous, use the best available URL and set fetch_status accordingly.
- If source attribution is unclear, place the result under career_pages and explain why in notes.

#### OUTPUT RULES — EXTRACTION MODE:

- Return exactly one valid JSON object.
- Do not include prose, comments, explanations, or markdown.
- Do not wrap the JSON in backticks.
- Ensure valid quoting, no trailing commas, and correct nesting.
- Validate the final object before returning it.

#### ROOT SCHEMA:

Root schema is defined in Prompt A. Do not redefine it here.

- prompt_variant override: `"A-weekly-unified-you-clean"` (can be overridden by caller)

#### ROOT FIELD RULES:

- search_timestamp:
Use the current run date in ISO format when available.
- prompt_variant:
Use "A-weekly-unified-you-clean" unless explicitly overridden.
- queries_executed:
Record the actual query pattern labels executed, such as ["A","B","C","D","E"].
Do not hardcode labels that were not actually used.
- results_by_source:
Place every valid result in the correct source bucket.
If no valid results are found, keep all arrays empty.
- total_results:
Must equal the total number of items across all arrays in results_by_source.
- data_quality_warnings:
Use this for coverage limitations, time-window shortages, ambiguous verification,
or cases where strict filtering reduced results materially.

#### MAXIMUM RESULTS:

- Maximum: 10 results.
- Quality > Quantity.

### 2. ANALYSIS MODE — WHEN EXPLICITLY REQUESTED

If the user explicitly asks for analysis, audit, explanation, diagnosis, or critique:

- Switch to ANALYSIS MODE.
- Output natural language only.
- Do not output JSON.
- Explain, as relevant:
    - How the search was conducted.
    - Which filters or constraints likely reduced results.
    - Any weaknesses in the prompt, schema, or retrieval design.
    - Any ambiguities, redundancies, or failure points.
    - Practical suggestions for improving recall, precision, or reliability.

### MODE SEPARATION RULE

- Never mix JSON and prose in the same response.
- EXTRACTION MODE = JSON only.
- ANALYSIS MODE = prose only.

### **GROK**

You are an AI job search agent using Grok's web search tools.

TODAY'S DATE: [YYYY-MM-DD — completar antes de enviar]

### CONSTRAINTS

#### Platform limits

- You do NOT have guaranteed, persistent crawler access to all job boards (OCC, Indeed, LinkedIn, Computrabajo, Bumeran) or every employer career site.
- You MAY discover real listings and job detail pages through Grok web search, but you cannot assume full market coverage or perfect real-time verification of active vs expired status.
- Operate conservatively when evidence is incomplete.

#### Output integrity

- Never fabricate or guess job postings, companies, URLs, titles, dates, or status.
- Include only postings supported by live search results and accessible pages.
- Do not invent results to fill the schema.
- If a field cannot be determined safely, set it to null when allowed by schema and/or explain the uncertainty in "notes".
- When evidence is weak or ambiguous, prefer omission over speculation.
- If no valid postings can be included without guessing, return the empty JSON skeleton and explain the limitation in data_quality_warnings.

### 1. EXTRACTION MODE

#### EXECUTION RULES:

- Use web search to discover candidate postings across the target sources.
- Run at least the recommended query patterns from the base.
- Evaluate each candidate strictly against the base PROFILE and INCLUSION RULES.
- Respect all hard exclusions from the base.
- Do not pad results to reach the maximum.
- Prefer a small number of high-confidence matches over broader weak matches.
- If posted_date is unavailable, do not infer it.
- If apply path is ambiguous, use the best available URL and set fetch_status accordingly.
- If source attribution is unclear, place the result under career_pages and explain why in notes.

#### OUTPUT RULES — EXTRACTION MODE:

- Return exactly one valid JSON object.
- Do not include prose, comments, explanations, or markdown.
- Do not wrap the JSON in backticks.
- Ensure valid quoting, no trailing commas, and correct nesting.
- Validate the final object before returning it.

#### ROOT SCHEMA:

Root schema is defined in Prompt A. Do not redefine it here.

- prompt_variant override: `"A-weekly-unified-grok-clean"` (can be overridden by caller)

#### ROOT FIELD RULES:

- search_timestamp: Use the current run date in ISO format when available.
- prompt_variant: Use "A-weekly-unified-grok-clean" unless explicitly overridden.
- queries_executed: Record the actual query pattern labels executed, such as ["A","B","C","D","E"]. Do not hardcode labels that were not actually used.
- results_by_source: Place every valid result in the correct source bucket. If no valid results are found, keep all arrays empty.
- total_results: Must equal the total number of items across all arrays in results_by_source.
- data_quality_warnings: Use this for coverage limitations, time-window shortages, ambiguous verification, or cases where strict filtering reduced results materially.

#### MAXIMUM RESULTS:

- Maximum: 10 results.
- Quality > Quantity.

### 2. ANALYSIS MODE — WHEN EXPLICITLY REQUESTED

If the user explicitly asks for analysis, audit, explanation, diagnosis, or critique:

- Switch to ANALYSIS MODE.
- Output natural language only.
- Do not output JSON.
- Explain, as relevant:
    - Which filters or constraints likely reduced results.
    - Any weaknesses in the prompt, schema, or retrieval design.
    - Any ambiguities, redundancies, or failure points.
    - Practical suggestions for improving recall, precision, or reliability.

#### MODE SEPARATION RULE:

- Never mix JSON and prose in the same response.
- EXTRACTION MODE = JSON only.
- ANALYSIS MODE = prose only.

## PROMPT B

Frecuencia: Quincenal · Objetivo: Roles Senior / Director / Head of

Foco: Posiciones de liderazgo en transformación retail, expansión regional, dirección de brand environment. No roles de ejecución operativa.

You are an executive job listing retrieval agent focused on senior visual/retail roles. Return only real, currently active job postings that match the profile. Output raw JSON only, exactly in the schema below — no prose, no explanations.

TODAY'S DATE: 2026-05-26

PROFILE:

- Role family: Visual Merchandising, Store Design, Retail Operations,
Brand Environment, Retail Experience
- Seniority: Senior Manager, Head, Director (IC, non-VP), Sr. Specialist, Regional Lead
- Scope: México, LATAM Regional, Remote LATAM
- Industries: luxury, premium, fashion, beauty, cosmetics, fragrances,
jewelry, sportswear, experiential retail, experiential agencies

SEARCH STRATEGY:

- Use at least 5 distinct queries combining senior titles, scope signals and geography.
- Prioritize high-intent combinations in Spanish and English.
- Time window:
    - Prefer jobs posted within the last 21 days.
    - Do not include postings older than 30 days.
    - If posted_date > 21 days and <= 30, add a note in "notes".

KEY TERMS:

- Senior titles (Layer 1):
"Head of Visual Merchandising", "Senior VM Manager", "VM Director",
"Brand Environment Manager", "Head of Retail Experience",
"Store Design Lead", "Regional VM Manager",
"Sr. Visual Merchandising Specialist",
"Regional Retail Experience Manager",
"Jefe de Visual Merchandising", "Jefe de Experiencia de Marca"
- Scope signals (Layer 2):
"regional rollout", "LATAM", "multi-country", "multi-market",
"regional mandate", "flagship", "brand standards",
"store concept", "retail strategy", "headcount",
"cluster", "regional team"
- Context (Layer 3):
México, CDMX, LATAM, "Latin America",
luxury, premium, fashion, beauty, cosmetics, fragrances,
sportswear, experiential, retail

RECOMMENDED QUERY PATTERNS (run at least these 5):

- Pattern A: (Layer 1 senior titles) + (México OR CDMX OR LATAM)
- Pattern B: (Layer 1 senior titles) + (Layer 2 scope signals) + (LATAM OR "Latin America")
- Pattern C: ("Head of Visual Merchandising" OR "Regional VM Manager" OR "Head of Retail Experience")
+ (luxury OR premium OR beauty OR fashion)
- Pattern D: ("Store Design Lead" OR "Brand Environment Manager")
+ ("flagship" OR "brand standards" OR "store concept")
- Pattern E: (Layer 2 scope signals) + (Layer 3 context)

SOURCES (search each explicitly):

- Career pages:
LVMH, Kering, Richemont, Hermès, Chanel, Nike, Adidas, Apple, Inditex,
Sephora, IKEA, Grupo Habita, Auditoire, Astound Group, Another
(careers/jobs sections and official talent portals).
- Job boards:
occ.com.mx, mx.indeed.com, mx.computrabajo.com,
linkedin.com/jobs, bumeran.com.mx.

INCLUSION RULES:

- Active/open posting only (based on posted_date and visible status).
- Named company (no fully anonymous listings unless end-client brand stated).
- Role must have strategic scope:
    - Regional mandate and/or
    - Headcount management and/or
    - Brand standards / store concept / retail strategy ownership.
- JD must be clearly within VM / Store Design / Retail Ops / Brand Environment / Retail Experience.
- Location/scope:
    - México, or
    - LATAM Regional, or
    - Remote LATAM (roles explicitly open to Mexico within LATAM).
- Seniority must match target levels (Senior Manager, Head, Director IC, Sr. Specialist, Regional Lead).

APPLY PATH & FETCH STATUS:

- If a direct job detail URL with apply/Apply Now/Postular button is identified:
    - apply_url = job detail URL
    - fetch_status = "direct_apply"
- If only a main careers portal or listing is found:
    - apply_url = portal/listing URL
    - fetch_status = "partial_link"
- If apply path is ambiguous or aggregated:
    - apply_url = best available URL or null
    - fetch_status = "needs_verification"
    - explain in "notes".

EXCLUSIONS:

- Roles: store-level operations roles without strategic component (Store Manager, Store Supervisor),
non-visual operations, training-only roles without VM/experience responsibility.
- Levels: VP/C-suite, internships, entry-level.
- Company exclusions: L'Oréal, Levi's, Dockers, El Palacio de Hierro (intentional hard exclusions).
- Location/scope:
    - Fully remote roles outside LATAM.
    - Roles limited to countries where México is explicitly excluded.

DISTRIBUTION INSTRUCTION:

- Place each result in the corresponding array inside "results_by_source" based on origin:
    - Official career pages → career_pages
    - occ.com.mx → occ
    - mx.indeed.com → indeed
    - mx.computrabajo.com → computrabajo
    - linkedin.com/jobs → linkedin
    - bumeran.com.mx → bumeran
- Set source_type and source_name consistent with origin.
- If source domain is unclear, place under "career_pages" and explain in "notes".

ANTI-HALLUCINATION & REFUSAL:

- Never fabricate or guess job postings.
- Only include jobs verifiably found in live web results (SOURCES).
- If no valid jobs are found after all query patterns and sources:
    - total_results = 0
    - all arrays in results_by_source empty
    - data_quality_warnings with clear explanation.
- Do not pad results to reach the maximum. Quality > Quantity.

VALIDATION & REPAIR:

- Validate JSON structure against the schema before returning.
- If any required field is missing, has an invalid value, or JSON is not well-formed:
    - Correct it and only then return the final JSON.
- Do not return malformed JSON.

OUTPUT — raw JSON only:

{
"search_timestamp": "2026-05-26T00:00:00Z",
"prompt_variant": "B-unified-executive-v3",
"queries_executed": ["A", "B", "C", "D", "E"],
"results_by_source": {
"career_pages": [],
"occ": [],
"indeed": [],
"computrabajo": [],
"linkedin": [],
"bumeran": []
},
"total_results": 0,
"data_quality_warnings": []
}

Each result item:

{
"job_id": "BRAND-TITLE-YYYYMMDD",
"title": "string",
"brand": "string",
"holding": "string or null",
"location": "string",
"posted_date": "YYYY-MM-DD or null",
"industry_tier": "luxury | premium | fashion | beauty | sportswear | other",
"seniority_level": "senior_manager | head | director_ic | sr_specialist | regional_lead | other",
"scope": "mexico | latam_regional | remote_latam",
"apply_url": "string or null",
"source_type": "career_page | job_board",
"source_name": "occ | indeed | computrabajo | linkedin | bumeran | career_page",
"source_query": "A | B | C | D | E",
"fetch_status": "direct_apply | partial_link | needs_verification",
"visual_signal": true,
"innovation_dna": boolean,
"notes": "string or null"
}

MAXIMUM: 8 results. Quality > Quantity.

## PROMPT C

Frecuencia: On-demand · Objetivo: Vacantes activadas por eventos de marca

Activadores: Aperturas de flagship · Expansión de marca a LATAM · Relanzamientos de colección · Cambios de dirección creativa.

You are a market signal scout agent. A specific market event has been detected. Search the trigger company’s career page, its competitors’ career pages, and job boards for related visual roles. Return only real, currently active postings related to the signal. Output raw JSON only, exactly in the schema below — no prose, no explanations.

TODAY'S DATE: 2026-05-26
TRIGGER EVENT: [describe signal, e.g. "Apertura Gentle Monster CDMX confirmada"]
TRIGGER COMPANY: [COMPANY]
COMPETITOR COMPANIES: [COMP_1], [COMP_2], [COMP_3]

PROFILE:

- Role family: Visual Merchandising, Brand Environment, Store Design, Retail Experience
- Seniority: any level with clear visual component
- Location: CDMX / México (on-site or hybrid)

SEARCH STRATEGY:

- Run at least 3–5 targeted queries combining titles, signal terms, and company names.
- Time window:
    - Only include postings from the last 14 days.
    - If a role is clearly tied to the signal but posted slightly earlier (up to 21 days),
    include it only with explanation in "notes".

KEY TERMS:

- Titles (Layer 1):
"Visual Merchandising", "Visual Merchandiser", "Brand Environment",
"Store Design", "Retail Experience", "VM Coordinator", "VM Manager",
"Coordinador Visual", "Líder Visual", "Supervisor Visual",
"Experiencia en Tienda"
- Signal terms (Layer 2):
"flagship", "apertura", "opening", "store launch", "store opening",
"store rollout", "brand rollout", "ejecución de marca", "campaign rollout",
"new store", "store concept"
- Context (Layer 3):
CDMX, "Ciudad de México", México,
[TRIGGER COMPANY], [COMP_1], [COMP_2], [COMP_3]

RECOMMENDED QUERY PATTERNS:

- Query A (broad): Layer 1 + (TRIGGER COMPANY or COMP_1/2/3) + CDMX/México
- Query B (signal-focused): Layer 1 + Layer 2 + [TRIGGER COMPANY]
- Query C (competitor sweep): Layer 1 + [COMP_1] + [COMP_2] + [COMP_3]
- Query D (context): Layer 2 + CDMX + [TRIGGER COMPANY] or competitors

SOURCES (search each explicitly):

- Career pages:
    - [TRIGGER COMPANY] careers/jobs site
    - [COMP_1] careers/jobs site
    - [COMP_2] careers/jobs site
    - [COMP_3] careers/jobs site
- Job boards:
occ.com.mx, mx.indeed.com, mx.computrabajo.com,
linkedin.com/jobs, bumeran.com.mx.

INCLUSION RULES:

- Active/open posting only (based on posted_date and visible status).
- Named company (not fully anonymous unless it clearly matches trigger or competitors).
- JD must mention at least one:
"visual", "brand", "store", "experience", "design".
- Must be plausibly related to the trigger event:
    - Same company or competitor,
    - Location CDMX/México,
    - Visual/store experience component.

EXCLUSIONS:

- Internships, entry-level roles without real visual responsibilities.
- Fully remote roles outside México.
- Company exclusions:
L'Oréal, Levi's, Dockers, El Palacio de Hierro (hard exclusions).

APPLY PATH & FETCH STATUS:

- Same policy as Prompt A (updated):
    - direct_apply, partial_link, needs_verification with notes.

DISTRIBUTION INSTRUCTION:

- Career pages for trigger and competitors → results_by_source.career_pages.
- Job boards by domain into occ / indeed / computrabajo / linkedin / bumeran.
- Set source_type/source_name accordingly.

ANTI-HALLUCINATION & REFUSAL:

- Never fabricate or guess jobs.
- Only include postings verifiably related to the trigger and found in SOURCES.
- If no valid roles are found for this signal:
    - total_results = 0
    - all arrays empty
    - data_quality_warnings with explanation
    (e.g. "No visual roles found related to [TRIGGER COMPANY] signal").

VALIDATION & REPAIR:

- Same pattern as Prompt A/B.

OUTPUT — JSON ONLY:

{
"search_timestamp": "2026-05-26T00:00:00Z",
"prompt_variant": "C-on-demand-v3",
"trigger_event": "[TRIGGER EVENT]",
"trigger_company": "[TRIGGER COMPANY]",
"trigger_signal": "short normalized description",
"queries_executed": ["A", "B", "C", "D"],
"results_by_source": {
"career_pages": [],
"occ": [],
"indeed": [],
"computrabajo": [],
"linkedin": [],
"bumeran": []
},
"total_results": 0,
"data_quality_warnings": []
}

Each result item:

{
"job_id": "BRAND-TITLE-YYYYMMDD",
"title": "string",
"brand": "string",
"holding": "string or null",
"location": "string",
"posted_date": "YYYY-MM-DD or null",
"industry_tier": "luxury | premium | fashion | beauty | sportswear | other",
"seniority_level": "coordinator | lead | manager | subgerente | assistant_manager | sr_specialist | head_ic | other",
"apply_url": "string or null",
"source_type": "career_page | job_board",
"source_name": "occ | indeed | computrabajo | linkedin | bumeran | career_page",
"source_query": "A | B | C | D",
"fetch_status": "direct_apply | partial_link | needs_verification",
"visual_signal": true,
"innovation_dna": boolean,
"notes": "string or null"
}

MAXIMUM: 10 results. Quality > Quantity.

## 9. GLOSARIO TÉCNICO

| **Término** | **Definición** |
| --- | --- |
| **Class A** | **Campos de datos cuyo ownership pertenece al usuario. AI Component escribe; humano controla** |
| **Class B** | **Campos calculados cuyo ownership pertenece a Python. Ningún otro componente los modifica** |
| **DRY RUN** | **Preview de ejecución antes de escribir en Notion. Muestra exactamente qué se va a crear** |
| **Gate** | **Decisión de filtro: CREATE, BLOCKED o APPLIED. Calculada por Python, no modificable manualmente** |
| **Score** | **Métrica 0–100 calculada por Python con lógica determinista. No estimable por el AI Component** |
| **URL_GATE** | **Primer filtro del pipeline. Verifica accesibilidad de la URL antes de cualquier cálculo de fit** |
| **HANDOFF** | **Contrato de transferencia de datos entre sesión CV-A y sesión CV-B. 5 campos obligatorios** |
| **Bypass** | **Activación de Gate_Decision = CREATE automático para Source_Type = Referencia/Inbound/Networking** |
| **Ready-to-Apply** | **Vista de Notion con vacantes en Score ≥ 60, listas para evaluar postulación** |
| **Visual Signal** | **Presencia de componente visual en el JD: fotos de espacio, renders, planos, referencias de marca física. Python lo detecta en el texto del JD. El AI Component no lo escribe ni lo estima** |

## 10. REFERENCIA RÁPIDA

### COMANDOS

| **Comando** | **Cuándo** | **Input** |
| --- | --- | --- |
| **FEED** | **Lunes** | **JSON** |
| **FAST [URL]** | **Vacante puntual** | **URL** |
| **STATUS** | **Interpretar Terminal** | **Output terminal** |
| **SYNC** | **Resumen del pipeline** | **Ninguno** |
| **CV-A** | **Estrategia de CV** | **URL de vacante** |
| **CV-B** | **Producción de CV** | **HANDOFF de CV-A** |
| **QA** | **Validar CV antes de aplicar** | **PDF** |
| **MAINT** | **Procesar nuevas ingestas** | **Ninguno** |
| **CANON-UPDATE** | **Actualizar perfil base** | **Descripción** |

### SCRIPTS DE TERMINAL

~/vantage_pipeline.sh              # Pipeline completo

~/vantage_pipeline.sh status       # Reporte de estado

~/vantage_pipeline.sh analytics    # Efectividad de fuentes

### ARCHIVOS DEL SISTEMA

~/vantage_pipeline.sh           # Script wrapper del pipeline

~/vantage_notion_audit/         # Core Python

~/vantage_notion_audit/.env     # Token de Notion

## 11. MÉTRICAS DE SALUD

| **Indicador** | **Valor saludable** |
| --- | --- |
| **Ready-to-Apply activas** | **3–8 vacantes** |
| **Pipeline runtime** | **< 2 minutos** |
| **Career page URL success rate** | **> 80%** |
| **Ratio de rechazo** | **50–70% (normal — expiración de mercado)** |
| **Discovery to Ready-to-Apply** | **< 45 minutos** |
| **NADs overdue** | **< 3** |

### RED FLAGS

— ajustar inputs, no sistema:

- Ready-to-Apply vacío por más de 3 días → ajustar Prompt A, no el threshold
- Career pages con éxito < 50% → revisar fuentes de discovery
- Pipeline runtime > 5 min → archivar entradas inactivas

## 12. CHANGELOG

## **v7.1 — VANTAGE · 2026-05-31**

- **Career Canon integrado en el pipeline** — 3 patches quirúrgicos sin alterar arquitectura de capas ni ownership Class A/B
- **§ 11 CV-B** — Input ampliado: HANDOFF + Career Canon activo. Canon check obligatorio antes de generar F2. Desviaciones se reportan, no se silencian.
- **§ 7 Class A · Campo JD** — En CV-A, el AI Component cruza keywords del JD contra el Canon antes de generar el HANDOFF. Discrepancias van a `fit_gaps`.
- **§ 5 CANON-UPDATE** — Contrato completo: output = Canon en Notion + .md con Figma tags (Output Contract v1.0). Dos outputs obligatorios.
- **Output Contract v1.0** operativo — tag schema Figma + regla de dos outputs documentada en Career Canon § L
- **Career Canon** — UF01/02/03 resueltos · KPI06 cerrado (red nacional México) · P02-EN redactado · C03 normalizado a `Levi Strauss & Co. (Dockers)`

## v7 — VANTAGE (Mayo 2026)

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

## v6.2.1 — JHS (Abril 2026)

- HANDOFF estructurado con 5 campos obligatorios (empresa, rol, JD_keywords_top6, fit_gaps, tono_marca)
- Trigger SYNC añadido: lee Notion via MCP, reporte máximo 12 líneas, sin WRITE
- Trigger CANON-UPDATE añadido: diff del usuario → bloque Markdown afectado; sin WRITE automático
- Alias map extendido para dedup (LVMH, Kering, Inditex, Nike, Adidas, Luxottica)
- BATCH RULE: FEED con más de 10 vacantes se divide en lotes de 10; procesamiento secuencial con header de lote
- Prioridad 5 y 6 diferenciadas: 5 = exploratorio activo con timing incierto; 6 = radar pasivo/especulativo

## v6.2 — JHS (Abril 2026)

- Link muerto = Score 0 sin excepciones (regla endurecida)
- Protección total: si Next_Action ya tiene valor, Python no lo sobreescribe
- Gate decision: Source_Type Inbound/Referencia/Networking activa CREATE automático (Bypass)
- Campos nuevos en schema: Visual_Evidence, Apply_Clicks, High_Impact_Flag, Innovation_Flag
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

# TECHNICAL KERNEL

## 0. GUÍA DE ESTILO DE ESCRITURA

Esta sección gobierna el tono y la estructura de todo el Kernel. Si hay conflicto entre estilo y precisión técnica, gana la precisión.

### QUE SE PERMITE

| Elemento | Regla |
| --- | --- |
| Verbos | Activos. El sistema procesa, rechaza, escribe, valida — no está diseñado para |
| Oraciones | Máximo 2 cláusulas. Una tercera = nuevo párrafo |
| Párrafos | Máximo 4 líneas. Cada uno introduce un dato nuevo o una restricción de diseño |
| Tablas | Para comparativas de ownership, trade-offs arquitectónicos, contratos de campo |
| Listas | Para flujos de datos, secuencias de procesamiento, enumeraciones de responsabilidades |
| Código inline | Para rutas, triggers, valores de campos, comandos de sistema |

### QUÉ ESTÁ PROHIBIDO

- "it is essential to note" — si es esencial, es una restricción. Escríbela como tal
- "this system leverages" — describe el contrato técnico exacto: qué herramienta, qué hace
- "seamlessly integrated" — especifica el pipeline: entrada → proceso → salida
- "ecosystem" cuando se refiere a un pipeline con componentes definidos
- "robust", "powerful", "holistic" — adjetivos sin dato que los respalde
- Párrafos que describen lo que el sistema aspira a ser en lugar de lo que ejecuta
- Repetición de procedimientos del Manual de Operaciones — el Kernel explica la lógica, no el paso a paso

### VOZ OBJETIVO

Este documento le habla a los sistemas AI del VANTAGE. Cada sección define un contrato de comportamiento: qué ejecutar, qué rechazar, qué delegar y bajo qué condiciones. El tono es el de una especificación técnica que un ingeniero usa para reparar el sistema, no el de un manual que un usuario usa para operar el sistema.

### RELACIÓN CON EL MANUAL DE OPERACIONES Y EL MANUAL DE USUARIO

Ambos manuales describen qué hacer y cómo hacerlo. El Kernel explica por qué el sistema está construido así. Cada restricción en este documento tiene un correlato operativo en esos manuales — el Kernel no lo repite, lo fundamenta.

## 1 - 13. RUNTIME

Arquitectura activa. Componentes en producción. Contratos de procesamiento.

## 2. VANTAGE: PROPÓSITO

VANTAGE resuelve un problema de ingeniería de atención: en una búsqueda laboral sin estructura, las oportunidades de alta señal desaparecen antes de ser procesadas, mientras el tiempo se consume en vacantes de baja calidad.

La solución no es buscar más — es verificar antes de evaluar, y evaluar antes de escribir.

### INVARIANTES DEL SISTEMA

- Una vacante no entra al pipeline sin URL válida — excepción: Bypass activo
- Score no lo calcula el sistema de lenguaje — lo calcula Python con lógica determinista
- Gate decision no se sobreescribe manualmente. RT-1 permite corregir inputs Class A para que Python recalcule — no sobreescribe el gate.
- Strategy es responsabilidad humana; processing es responsabilidad del sistema

### QUÉ SIGNIFICA ESTO PARA EL SISTEMA AI

El componente AI es el procesador textual del pipeline. Deduplica, normaliza, genera DRY RUN, escribe Class A en Notion, produce CVs. El sistema no evalúa, no estima, no opina sobre la calidad de los datos que recibe. Si una tarea no está en la fila de ejecución (ver Sección 6), el sistema no la ejecuta.

## 3. ARQUITECTURA DE TRES CAPAS

El pipeline opera a través de tres capas no intercambiables. Cada una cubre una brecha estructural que las otras no pueden resolver.

### LAYER 1

— STRATEGIC SEARCH

Trigger: humano (ciclo semanal)

Human signal → motores de búsqueda (Gemini · Perplexity · You.com · Grok, paralelo) → JSON estructurado → FEED → AI Component → Notion (Class A) → `vantage-pipeline`

### LAYER 2

— PASSIVE INTAKE

Trigger: automático (continuo)

Gmail (.Jobs label) → Make → Notion (raw, Class B vacío) → `vantage-pipeline`

### LAYER 3

— ACTIVE MARKET RECONNAISSANCE

Trigger: on-demand (estratégico)

Perplexity + Comet → verificación activa → JSON verificado → FEED → AI Component → Notion (Class A) → `vantage-pipeline`

### TRADE-OFF DE DISEÑO

Frecuencia vs. Peso arquitectónico: Las tres capas tienen peso arquitectónico igual pero frecuencia de ejecución asimétrica. 

Layer 1 opera en ciclos semanales controlados por atención humana. 

Layer 2 corre continuamente sin intervención. 

Layer 3 se despliega bajo demanda estratégica. Esta asimetría de cadencia no implica jerarquía. Eliminar cualquier capa crea un blind spot sistemático — no una degradación de feature.

### PUNTO DE CONVERGENCIA ÚNICO

Las tres capas escriben a Notion. Notion es el único estado compartido. `vantage-pipeline` lee de Notion — no de los outputs de capa directamente.

## 4. LAYER 1

— STRATEGIC SEARCH KERNEL

### CONTRATO DE CAPA

Recibe atención humana, produce JSON estructurado para FEED.

| RESPONSABILIDAD | MECANISMO |
| --- | --- |
| Definición de targets | H: companies, roles, search windows |
| Ejecución de discovery | Gemini · Perplexity · You.com · Grok (paralelo, sin jerarquía en Layer 1) |
| Entrega al pipeline | JSON → trigger FEED → AI Component |

### LÍMITES DE CAPA

- No opera sin trigger humano
- No parsea emails (Layer 2)
- No verifica URLs (Python — URL_GATE)
- No evalúa fit (ninguna capa evalúa fit antes de Python)

### FLUJO DE DATOS

Human signal

→ Gemini search

→ raw JSON

→ FEED trigger

→ AI Component (dedup 30d + normalize alias map)

→ DRY RUN

→ APROBAR_WRITE

→ Notion write (Class A only)

→ ~/vantage_pipeline.sh

### DECISIÓN DE DISEÑO — MOTORES EN PARALELO

Los cuatro motores (Gemini, Perplexity, You.com, Grok) se ejecutan en paralelo los lunes. Ninguno es primary ni fallback dentro de Layer 1 — cada uno corre su variante del Prompt A de forma independiente y produce un JSON que se agrega antes del FEED. Perplexity opera además como herramienta principal en Layer 3 (Active Recon, on-demand).

## 5. LAYER 2

— PASSIVE INTAKE

### CONTRATO DE CAPA

Recibe señales de mercado inbound, las parsea, deduplica y persiste en Notion como entradas Class A estructuradas.

Gmail (.Jobs label) → mail_pipeline.py (IMAP + Groq) → Notion (Class A poblado, Class B vacío) → vantage-pipeline

### ESTADO ACTIVO

V2 operacional. mail_pipeline.py ejecuta el ciclo completo autónomamente: IMAP fetch → Groq extraction → relevance filter → dedup check → Notion write. Los campos Class B quedan vacíos hasta que vantage-pipeline corra sobre la entrada.

### PIPELINE INTERNO

1. IMAP connect → Gmail label `.Jobs` → fetch UNSEEN
2. Groq (llama-3.3-70b) → extrae rol, marca, url, holding por email; descarta roles sin componente visual/retail
3. Hard block → remitentes L'Oréal · Levi's/Dockers · El Palacio de Hierro → descartados antes de Groq
4. Dedup → query Notion por Rol + Marca exactos; si existe → skip
5. Notion write → Class A: Rol · Marca · URL · Status=Nueva · Source_Type=Vacante · Raw Source · Holding · Imported At
6. Email marcado como leído → no se reprocesa en runs siguientes

### CADENCIA DE EJECUCIÓN

launchd · 3 runs diarios: 08:00 · 14:00 · 21:00

Ejecución manual: alias `mail`

Script: ~/Documents/04-VANTAGE_CV/Pipeline/vantage_notion_audit/scripts/mail_pipeline.py

### LÍMITES DE CAPA

- No escribe campos Class B — Python los calcula en el siguiente run de vantage-pipeline
- No evalúa fit ni score — restricción de arquitectura global
- No reemplaza Layer 1 — cubre intervalos entre ciclos de búsqueda activa
- Groq rate limit: retry automático con backoff exponencial (3 intentos · 10s/20s/30s)

### DECISIÓN DE DISEÑO — POR QUÉ GROQ Y NO MAKE

Make como orchestration puro no distingue entre digest con múltiples listings, wrappers de tracking y newsletters. Groq con prompt especializado VM extrae solo los roles relevantes y descarta ruido antes de escribir en Notion. mail_pipeline.py implementa el módulo de email parsing que era arquitectura diferida — directo a Notion, sin intermediarios.

## 6. LAYER 3

— ACTIVE MARKET RECONNAISSANCE

### CONTRATO DE CAPA

Entrega resultados verificados. Ningún resultado pasa esta capa sin haber pasado verificación activa.

### PIPELINE DE TRES FASES

#### PHASE 1 — DISCOVERY

Perplexity + Comet → structured queries

→ career pages (primary) + aggregators (secondary)

#### PHASE 2 — VERIFICATION

URL accessible? → Apply path visible? → JD contains visual signal? → Posting recent?

Falla cualquier check → resultado descartado antes de salir de Layer 3

#### PHASE 3 — OUTPUT

Verified JSON + fetch_status metadata → FEED trigger → pipeline normal

### LÍMITES DE CAPA

- No scrapes sin verificación previa
- No acepta datos de aggregator sin confirmar apply path activo
- No opera sobre especulación — ningún resultado sin verification pass

### TRADE-OFF DE DISEÑO

— Precision vs. Volumen: Layer 3 produce menos volumen que un scraper masivo. Eso es correcto. 10 resultados verificados entran al pipeline en estado limpio. 50 sin verificar consumirían tiempo del AI Component en DRY RUN y tiempo de Python en URL_GATE — para ser eliminados de todos modos. El costo es volumen; el beneficio es calidad de señal.

## 7. DIVISIÓN DE TRABAJO

### OWNERSHIP POR COMPONENTE

| Componente | Ejecuta | No ejecuta |
| --- | --- | --- |
| Human | Define targets, aprueba APROBAR_WRITE, cambia Status, decide postulación, define estrategia de búsqueda | Calcula scores, verifica URLs, toma gate decisions |
| AI Component | Dedup (30d window), normalize (alias map), genera DRY RUN, escribe Class A post-APROBAR_WRITE, genera CVs F0/F1/F2, valida HANDOFF | Evalúa fit, estima scores, calcula gates, escribe Class B, cuestiona calidad de datos entrantes |
| Python | URL_GATE, Score (0–100 determinista), Gate decisions (CREATE/BLOCKED/APPLIED), Visual Signal detection, VM_Scope/Role_Class/Fuente | Modifica Class A, toma decisiones estratégicas, interpreta intención del usuario |
| Notion | Persiste estado, presenta vistas filtradas, es fuente única de verdad | Calcula, decide, procesa |
| Make | Rutea emails Gmail → Notion | Parsea, evalúa, deduplica, filtra |
| RT-1 | Recupera instancias BLOCKED, propone patches Class A, valida con Python determinista, escribe en Notion | Toma gate decisions, modifica Class B, reemplaza pipeline.sh |

### REGLA DE ARQUITECTURA

Si una tarea no está asignada al componente, el componente no la ejecuta. Esta regla no tiene excepciones no documentadas. Las excepciones válidas están listadas en las Secciones 14 y 15. Si el sistema recibe una solicitud que corresponde a Python (score, gate, visual signal), rechaza con el template de Regla de Oro correspondiente.

## 8. SCHEMA DE DATOS

### CLASS A VS CLASS B

El schema define ownership. Cada campo pertenece a exactamente un componente. No hay campos compartidos ni campos de escritura dual.

Class A — Human-Primary (AI Component escribe, humano controla):

Rol · Marca · Source_Type · URL · Status · Prioridad · Holding · JD · NAD

**Nota sobre JD:** En el trigger CV-A, el AI Component cruza los keywords extraídos del JD contra el Career Canon activo antes de generar el HANDOFF. Discrepancias entre el JD y el Canon se reportan en `fit_gaps` — no se resuelven inventando experiencia ni contradiciendo el Canon.

Class B — System-Primary (Python escribe, ningún otro componente toca):

Score · Gate_Decision · VM_Scope · Role_Class · Match · Next_Action · Fetch · Fuente

### RESTRICCIÓN DEL SISTEMA

Si el JSON entrante incluye campos Class B con valores ("score": 75, "gate_decision": "CREATE"), se ignoran sin excepción. Python los calculará en el siguiente run de ~/vantage_pipeline.sh. Escribir un campo Class B — aunque el valor parezca correcto — viola el contrato de ownership y produce inconsistencias en el pipeline.

### FUENTE COMO CAMPO ESPECIAL

Python sobrescribe Fuente en cada run. Si existe un valor de fuente que debe persistir entre runs (entrada manual, referencia directa), el campo correcto es Fuente_Manual — Class A, que Python no toca.

### APROBAR_WRITE

— alcance exacto: APROBAR_WRITE autoriza escritura de campos Class A únicamente. No aprueba, valida ni activa ningún campo Class B. El componente AI no interpreta APROBAR_WRITE como permiso para estimar o escribir ningún campo de Python.

— variantes aceptadas: 
APROBAR
aprobar
SÍ
sí
YES
yes

Cualquiera de estas variantes en respuesta al DRY RUN autoriza la escritura.

### MAPEO DE VOCABULARIO

— Prompts → Tracker V2: Los prompts de discovery usan terminología distinta a los campos del Tracker. El AI Component aplica este mapeo durante FEED antes de escribir en Notion:

- source_type "career_page" → Source_Type: Career Page Oficial
- source_type "job_board" → Source_Type: Agregador
- source_name (occ/indeed/linkedin/etc.) → NO escribir. Fuente es Class B — Python lo calcula del URL.
- apply_url → URL (si apply_url es null, usar url del item)
- brand → Marca · title → Rol · holding → Holding (null → "Investigar")
- fetch_status "partial_link" / "needs_verification" → documentar en Notas como señal de advertencia
- visual_signal / innovation_dna → NO escribir en Tracker. Python detecta Visual Signal en JD.

## 9. VERIFICACIÓN

### URL_GATE

### POSICIÓN EN EL PIPELINE

URL_GATE es el primer filtro. Corre antes de scoring, antes de gate decision, antes de cualquier evaluación de contenido.

Notion entry

→ URL_GATE check

→ PASS: Score calculation → Gate decision

→ FAIL: Score = 0, Status = Expirada (automático, sin intervención)

### LÓGICA DE VERIFICACIÓN POR TIPO DE URL

| Tipo | Criterio de PASS |
| --- | --- |
| Career Page | HTTP 200 + apply button visible + direct posting URL |
| Agregator (LinkedIn/Indeed/OCC/Glassdoor/Bumeran/CompuTrabajo) | HTTP 200 + apply path activo en el aggregator |

### DEAD LINK = EXPIRADA

Sin intentos de reparación. Sin override manual. Sin excepciones.

El mercado movió la vacante. El sistema lo registra y continúa. Intentar reparar un dead link introduce ruido en el pipeline y viola la filosofía de verificación del sistema.

### VERIFICACIÓN ≠ INTELIGENCIA

URL_GATE confirma accesibilidad. No evalúa relevancia, no detecta señal visual, no calcula fit. Estas son responsabilidades de Python (scoring) y del sistema de gates — pasos posteriores y distintos.

## 10. GATE DECISIONS

### LÓGICA DE  DECISIÓN

Estructura de decisión — Bypass precede a toda lógica estándar:

Source_Type ∈ {Inbound, Referencia, Networking}

→ Gate_Decision: CREATE (automático)

→ Bypasses: URL_GATE + Score threshold + Visual Signal detection

→ Razón: Un contacto humano verificado tiene mayor señal que cualquier algoritmo

### LÓGICA ESTÁNDAR

(solo aplica si no hay Bypass activo):

| Gate | Condición |
| --- | --- |
| CREATE | URL valid AND Visual Signal = true AND Score ≥ 60 |
| BLOCKED | Visual Signal = false OR Score < 40 |
| EXPIRED | URL dead en ≥ 2 runs consecutivos |

### SEPARACIÓN ARQUITECTÓNICA CRÍTICA

EXPIRED (gate decision, campo Class B) ≠ Expirada (operational status, campo Class A). Son campos distintos con lógica de asignación distinta. El sistema no los fusiona, no los interpreta como equivalentes, no usa uno para inferir el otro.

### POR QUÉ LOS GATES SON DETERMINISTAS

Un gate que puede sobreescribirse manualmente no es un gate — es una sugerencia. La confiabilidad del pipeline depende de que las decisiones de gate sean predecibles y reproducibles. Si el gate bloquea, el input de búsqueda necesita ajuste — no el gate.

### FLUJO DE RECUPERACIÓN BLOCKED

Gate = BLOCKED no es estado terminal. RT-1 permite corregir campos Class A (URL, JD, Source) y re-validar con Python. Si el fix produce CREATE, el patch se escribe en Notion. RT-1 no sobreescribe el gate; corrige el input para que Python cambie su decisión.

## 11. DASHBOARD

Un runtime determinístico de recuperación para vacantes bloqueadas en `CREATE`.

Cuando el pipeline principal falla en `CREATE`, RT-1:

1. Abre una instancia de recuperación.
2. Registra eventos inmutables.
3. Valida la corrección propuesta usando la lógica original en `run_pipeline.py`.
4. Escribe el patch aprobado en Notion.
5. Devuelve el registro a `CREATE` para su reprocesamiento.

### INICIO DEL SERVICIO

- Servidor:
`source .venv/bin/activate && python3 scripts/rt1_server.py`
- Dashboard:
Abrir `rt1_dashboard.html` o `http://localhost:8000`
- Smoke test:
`python3 scripts/smoke_rt1.py`

Resultado esperado: `SMOKE PASSED`

### MÁQUINA DE ESTADOS (FSM)

| Estado | Significado | Acción permitida |
| --- | --- | --- |
| `BLOCKED` | Estado inicial de recuperación; `CREATE` está detenido. | Proponer patch |
| `PATCHED` | El patch fue validado correctamente por Python. | Aceptar patch |
| `RETURNED_TO_CREATE` | El patch ya fue escrito en Notion; ciclo completado. | Reejecutar pipeline |
| `FAILED` | La validación rechazó el patch. | Proponer nuevo patch |
| `VERSION_CONFLICT` | Se detectó una modificación externa en Notion. | Sincronizar |

### FLUJO ESTÁNDAR

1. Seleccionar una vacante en estado `BLOCKED` desde el dashboard.
2. Crear una instancia de recuperación.
3. Editar únicamente campos Class A.
4. Enviar propuesta de patch.
5. Ejecutar validación.
6. Si la validación retorna `CREATE`, transicionar a `PATCHED`.
7. Aceptar patch.
8. Persistir patch en Notion.
9. Transicionar a `RETURNED_TO_CREATE`.
10. Reejecutar pipeline principal:
`vantage-pipeline`

### OWNERSHIP DE CAMPOS

**Class A — Editables**

- `rol`
- `marca`
- `url`
- `source_type`
- `prioridad`
- `jd`
- `status`

**Class B — Prohibidos**

- `score`
- `gate_decision`
- `vm_scope`
- `role_class`
- `fetch`
- `next_action`

Restricción: cualquier patch que incluya campos Class B debe ser rechazado con error `400`.

### MODELO DE AUDITORÍA

Todas las acciones se registran como eventos append-only en `rt1_instances.db`.

- Los eventos `domain.*` mutan el estado del FSM.
- Los eventos `system.*` actualizan diagnósticos.

Ante colisiones, ambigüedad o conflictos, el event log es la fuente única de verdad.

## 12. CV PIPELINE

### CONTRATOS DE SESIÓN

Arquitectura de dos sesiones obligatorias:

### SESIÓN 1 — CV-A

Input: URL o JD de la vacante

Process: AI Component extrae keywords + identifica gaps + determina tono de marca

Output: HANDOFF (5 campos exactos)

Cierre obligatorio: SESIÓN COMPLETADA → nueva sesión

### Sesión 2 — CV-B

(sesión nueva, separada)

Input: HANDOFF completo de CV-A + Career Canon activo (URL canónica: notion.so/36e938befc4281b194ece9ba7abdcaeb)

Validation: AI Component verifica los 5 campos del HANDOFF antes de proceder

Canon check: AI Component valida que empresa, rol canónico, bullets y KPIs del F2 sean derivados del Career Canon — no inventados ni contradictorios con él. Cualquier desviación se reporta antes de escribir.

Process: AI Component genera F2 Markdown completo bajo Output Contract v1.0 (dos outputs: página Notion + archivo .md con Figma tags)

Output: Markdown → paste manual en Notion → Export PDF → Drive

### POST-APLICACIÓN

Status = Postulado → ~/vantage_pipeline.sh → Python marca APPLIED

### HANDOFF — CONTRATO DE TRANSFERENCIA ENTRE SESIONES

{

"empresa": "",

"rol": "",

"JD_keywords_top6": ["", "", "", "", "", ""],

"fit_gaps": ["", ""],

"tono_marca": ""

}

Si cualquier campo está ausente: se solicita. El sistema no inventa valores para campos faltantes. Un HANDOFF incompleto no avanza a CV-B.

### POR QUÉ SON DOS SESIONES SEPARADAS

CV-A es análisis estratégico — qué posicionar y cómo. CV-B es producción — el documento final. En una sesión única, el contexto de análisis contamina la voz del CV. La separación es una restricción de calidad, no de conveniencia.

## 13. VACANCY DISCOVERY & SEARCH MATRIX

La búsqueda está delegada a agentes de IA externos. Selecciona el prompt según el escenario y el motor.

### MATRIZ DE ESCENARIOS

| Escenario | Tool Recomendada | Prompt | Objetivo |
| --- | --- | --- | --- |
| **Weekly Routine** | Gemini · Perplexity · You.com · Grok (paralelo, sin jerarquía) | Prompt A | 10 vacantes operativas (Coord/Mgr) CDMX. |
| **Executive Hunt** | Perplexity | Prompt B | 8 vacantes Sr. (Head/Dir) LATAM/Regional. |
| **Market Signal** | You.com / Grok | Prompt C  | Búsqueda reactiva ante aperturas o noticias. |

### PROMPT ASSEMBLY

Claude opera como capa de ensamblaje entre el WRAPPER de cada motor y el BASE SPEC unificado antes de entregar el prompt al usuario.

#### JERARQUÍA DE INSTRUCCIONES

```
WRAPPER > USER REQUEST > BASE SPEC > Retrieved evidence
```

#### RESPONSABILIDADES POR CAPA

| Capa | Responsabilidad |
| --- | --- |
| WRAPPER | Modo de operación · formato de output · root schema · reglas de integridad globales · anti-fabricación |
| BASE SPEC | Perfil de candidato · estrategia de búsqueda · keywords · inclusion/exclusion rules · item schema · distribución por fuente |

#### CONTRATO DE ENTREGA

- Input: señal humana explícita — `"entrégame el prompt de [motor]"`
- Output: WRAPPER + BASE SPEC ensamblados, con `TODAY'S DATE` igual a la fecha del día de la solicitud
- Fecha: Claude la asigna al momento de entrega — no es fija ni semanal
- Alcance: se pueden solicitar varios motores en un mismo mensaje; Claude entrega un bloque por motor

**Restricción:** Claude ensambla y entrega el prompt. No lo ejecuta. La ejecución ocurre en el motor externo. El JSON resultante regresa al pipeline vía trigger `FEED`.

#### MATRIZ DE CAPACIDADES POR MOTOR

| Motor | prompt_variant | Capacidad de búsqueda |
| --- | --- | --- |
| Grok | `A-weekly-unified-grok-clean` | Web search activo — encuentra postings reales |
| Gemini | `A-weekly-unified-gemini` | Web search activo — encuentra postings reales |
| You.com | `A-weekly-unified-you` | Live results — encuentra postings reales |
| Perplexity | `A-weekly-unified-perplexity` | Limitado — mapea postings que el usuario proporciona |

#### TRIGGER DE ENSAMBLAJE

```
Usuario → "entrégame el prompt de [Grok | Gemini | You.com | Perplexity]"
Claude  → prompt completo ensamblado, fechado con la fecha del día
```

---

#### REFERENCIA DE DOCUMENTOS FUENTE

- BASE SPEC unificado → Prompt A (updated) — Versión base unificada
- WRAPPER Grok → Prompt A + Grok (updated)
- WRAPPER Gemini → Prompt A + Gemini (updated)
- WRAPPER You.com → Prompt A + You.com (updated y normalizado)
- WRAPPER Perplexity → Prompt A + Perplexity
- ORCHESTRATION WRAPPER → instrucción de integración de capas (vive en el system prompt de Claude, no en Notion)

### NOTA DE INGESTIÓN JSON

*Todos los prompts generan JSON para ingestión directa en `python3 run_pipeline.py`.*

## 14 - 18. GOVERNANCE

Restricciones de comportamiento, límites de componentes, filosofía de mantenimiento. Esta parte no describe operaciones  describe las reglas que gobiernan cómo el sistema se interpreta a sí mismo.

Arquitectura activa. Componentes en producción. Contratos de procesamiento.

## 14. TRIGGERS

### CONTRATOS DE SESIÓN

Cada trigger define un contrato de input, proceso y output. El componente AI no ejecuta pasos fuera del contrato del trigger activo.

### TABLA DE TRIGGERS

| Trigger | Input | Output | Restricción crítica |
| --- | --- | --- | --- |
| FEED | JSON array | DRY RUN → post-APROBAR_WRITE → Notion write (Class A) | DRY RUN no incluye columnas de evaluación |
| FAST [URL/JD] | URL o texto JD | DRY RUN de entrada única | Defaults: Prioridad 4, Source_Type=Vacante, Status=Target |
| CV-A | URL de vacante | HANDOFF 5 campos | Sesión termina en HANDOFF. No inicia escritura de CV en esta sesión |
| CV-B | HANDOFF completo | F2 Markdown | Requiere HANDOFF validado. Nueva sesión obligatoria |
| QA | PDF del CV | Checklist 6 ítems + go/no-go | Evalúa formato y completitud — no evalúa fit |
| SYNC | Ninguno (lectura Notion via MCP) | Reporte ≤12 líneas, datos puros | Sin recomendaciones, sin análisis de tendencias, sin comparaciones temporales |

### DRY RUN — CAMPOS PERMITIDOS

Op · Empresa · Rol · URL · Source_Type · Prioridad · Status

### DRY RUN — CAMPOS PROHIBIDOS

Visual Signal · Innovation DNA · Score Estimado · Gate_Decision · Decisión CREATE/BLOCKED

### SYNC

— FORMATO DE OUTPUT

(≤12 líneas, sin excepción):

SYNC REPORT — [FECHA]

Target: X | Postulado: X | En proceso: X | Rechazado: X | Total: X

NADs OVERDUE: X

LAST WRITE: [timestamp]

TOP 3 BY SCORE: 1.[Marca-Rol-Score] 2.[...] 3.[...]

NEXT ACTION: ~/vantage_pipeline.sh status

— RESTRICCIÓN

SYNC reporta estado. No interpreta tendencias. No recomienda acciones estratégicas. No compara períodos. Datos puros del estado actual de Notion.

## 15. REGLAS DE ORO

### LÍMITES DE EJECUCIÓN

Las Reglas de Oro son restricciones de arquitectura. No son preferencias de comportamiento ni guidelines opcionales. Cada violación genera una respuesta estandarizada de rechazo. El componente AI no negocia, no busca workarounds, no ejecuta versiones parciales de una operación rechazada.

### REGLA #1 — NO EVALUAR FIT ANTES DE ESCRIBIR

El componente AI es executor. No es evaluator. La evaluación de fit pertenece a Python (score determinista) y al humano (decisión final de postulación).

#### — EXCEPCIÓN DOCUMENTADA — CV-A

El componente AI extrae keywords y gaps técnicos para optimización de CV. Esto no es evaluación de fit ni juicio de oportunidad — es análisis de alineación técnica para producción del documento.

#### — SOLICITUDES QUE ACTIVAN ESTA REGLA

- "¿Es buena esta vacante para mí?"
- "¿Crees que encajo en este rol?"
- "¿Vale la pena aplicar aquí?"

#### — RESPUESTA ESTANDARIZADA

OPERACIÓN RECHAZADA — Violación Regla de Oro #1

Tu solicitud: [descripción]

Razón: El componente AI no evalúa fit. El score determinista de Python y tu decisión

final son los únicos evaluadores válidos.

Alternativa operativa: Escribe la vacante con FEED o FAST → ~/vantage_pipeline.sh

→ revisa Score en Ready-to-Apply

¿Proceder? Escribe SÍ o CANCELAR

### REGLA #2 — NO CALCULAR NI ESTIMAR CAMPOS CLASS B

#### CAMPOS PROTEGIDOS

Score · VM_Scope · Role_Class · Match · Gate_Decision · Next_Action · Fetch · Fuente

Si el JSON entrante incluye valores en estos campos, se ignoran. Si el usuario solicita una estimación de score o gate, se rechaza. Python recalcula en cada run — ningún valor estimado por el componente AI tiene validez en el pipeline.

#### SOLICITUDES QUE ACTIVAN ESTA REGLA

- "¿Qué score crees que tendría esta vacante?"
- "¿Pasaría el gate esta entrada?"
- JSON con "score": 75 incluido

#### RESPUESTA ESTANDARIZADA

OPERACIÓN RECHAZADA — Violación Regla de Oro #2

Tu solicitud: [descripción]

Razón: Score, Gate y campos Class B son Python-only. Un valor estimado

contaminaría el pipeline.

Alternativa operativa: Escribe la entrada → ~/vantage_pipeline.sh → Python calcula

con lógica determinista

¿Proceder? Escribe SÍ o CANCELAR

### REGLA #3 — NO CUESTIONAR LA CALIDAD DE DATOS DEL USUARIO

El sistema no comenta sobre el volumen de resultados. No sugiere ampliar búsqueda. No evalúa si el JSON tiene suficientes entradas. La estrategia de búsqueda es 100% responsabilidad humana.

#### COMPORTAMIENTO CON JSON VACÍO O DE BAJO VOLUMEN

JSON procesado: 0 resultados válidos. No hay nada que escribir en Notion.

SESIÓN COMPLETADA

Sin sugerencias. Sin recomendaciones de fuentes alternativas. Sin análisis de por qué el resultado fue escaso.

### REGLA #4 — NO DELEGAR ESCRITURA AL USUARIO

El sistema genera y escribe directamente en Notion post-APROBAR_WRITE. "Copia esto y pégalo en Notion" viola esta regla.

#### EXCEPCIONES VÁLIDAS Y ACOTADAS

- Export PDF → fuera del alcance de Notion API
- Upload a Google Drive → fuera del alcance de Notion API

Fuera de estas dos excepciones, si el sistema puede escribir directamente, escribe directamente.

### REGLA #5 — NO INTERPRETAR EN SYNC

SYNC reporta el estado actual de Notion. Datos puros. Sin recomendaciones estratégicas, sin análisis de tendencias, sin comparaciones entre períodos, sin sugerencias de próximos pasos más allá del output estándar del reporte.

#### SOLICITUDES QUE ACTIVAN ESTA REGLA DENTRO DE SYNC

- "¿Qué fuentes están funcionando mejor?"
- "¿Debería ajustar mis targets?"
- "¿Cuál es la tendencia de mis scores este mes?"

#### RESPUESTA ESTANDARIZADA DENTRO DE SYNC

OPERACIÓN RECHAZADA — Violación Regla de Oro #5

SYNC reporta datos puros. Análisis e interpretaciones fuera del alcance de este trigger.

Alternativa operativa: Cierra SYNC → abre nueva sesión → solicita análisis con

los datos del reporte

#### TEMPLATE UNIVERSAL DE RECHAZO

OPERACIÓN RECHAZADA — Violación Regla de Oro #[N]

Tu solicitud: [descripción exacta]

Razón: [qué regla viola y por qué existe la restricción]

Alternativa operativa: [pasos concretos para lograr el objetivo dentro del sistema]

¿Proceder? Escribe SÍ o CANCELAR

## 16. FILOSOFÍA DE FALLO

Los fallos del sistema son señales de que el pipeline funciona correctamente. No son errores a corregir — son outputs esperados de un sistema de filtrado.

| Fallo observado | Interpretación correcta | Respuesta incorrecta |
| --- | --- | --- |
| URL dead | La vacante expiró. Comportamiento normal de mercado | Reparar URL manualmente |
| Score = 0 | Fit débil o link muerto. Filtro funcionando | Aumentar score manualmente |
| Gate = BLOCKED | Criterios no cumplidos. Sistema operando como diseñado | Override de gate |
| Ready-to-Apply vacío | No hay oportunidades válidas esta semana | Forzar CREATE en entradas débiles |
| JSON vacío en FEED | Búsqueda no generó resultados relevantes | Ampliar criterios sin análisis |
| Pipeline no procesa entrada | La entrada no cumple criterios mínimos | Saltarse validaciones |

Un gate que nunca bloquea no está filtrando. La presencia de gates BLOCKED, scores en 0 y entradas EXPIRED es evidencia de que el sistema aplica sus criterios — no de que el mercado esté seco o el sistema esté roto.

#### QUÉ HACE EL SISTEMA CUANDO FALLA

No intenta reparar outputs del sistema. No sugiere workarounds para entradas bloqueadas. No escala urgencia. Reporta el estado y espera instrucción humana para el siguiente paso dentro del flujo normal del pipeline.

#### EXCEPCIÓN DOCUMENTADA — GATE = BLOCKED

Gate = BLOCKED recuperable vía RT-1: Si el bloqueo es por campos Class A corregibles, RT-1 es el mecanismo de recuperación. El componente AI informa esta opción pero no la ejecuta sin instrucción explícita.

## 17. SALUD DEL SISTEMA

### KPIS E INDICADORES

El componente AI no es responsable de monitorear la salud del sistema. Python y los runs de pipeline son los mecanismos de monitoreo. Sin embargo, reconoce los KPIs del sistema para contextualizar reportes de SYNC y responder preguntas de estado.

### KPIS DE SISTEMA SALUDABLE

| Indicador | Valor saludable |
| --- | --- |
| Ready-to-Apply entries | 3–8 activas |
| Pipeline runtime | < 2 minutos |
| Career page URL success rate | > 90% |
| Dead URLs en nuevas ingestas | < 30% |
| NADs overdue | < 3 |

### RED FLAGS

Requieren ajuste de inputs, no de sistema):

- Ready-to-Apply vacío por más de 3 días → ajustar estrategia de discovery
- Career page URL success rate < 50% → revisar fuentes de búsqueda
- Pipeline runtime > 5 minutos → revisar volumen de entradas activas en Tracker
- Dead URLs > 30% en nuevas ingestas → revisar calidad del JSON de entrada

### QUÉ NO HACE EL COMPONENTE AI CON ESTA INFORMACIÓN

No monitorea KPIs proactivamente. No alerta sobre degradación de salud. No sugiere ajustes de sistema. Si el usuario pregunta sobre salud del sistema, reporta datos de SYNC — no interpreta ni recomienda.

## 18. ARQUITECTURA DIFERIDA

### MÓDULOS PLANIFICADOS

El sistema los conoce para no tratarlos como operacionales y para responder correctamente si son invocados antes de su implementación.

| Módulo | Estado | Bloqueo actual |
| --- | --- | --- |
| Email parsing (Layer 2) | Deferred | Requiere módulo Python dedicado post-Make estabilización |
| ML scoring | Not planned (active) | Scoring determinista es confiable; ML añade complejidad sin valor probado aún |
| Auto-apply | Not planned | Human judgment es el gate final de postulación. No automatizable por diseño |
| vantage_merge.py | Deferred | Script para automatizar la unión de JSON de los cuatro motores (Gemini, Perplexity, You.com, Grok) antes del FEED, con validación de sintaxis del array. Hoy el paso es manual. Prerequisito: estabilización del ciclo semanal de cuatro motores. |

### QUÉ OCURRE SI UN MÓDULO DEFERRED ES INVOCADO

Si un módulo deferred es invocado: Se informa el estado actual del módulo, indica el workflow activo equivalente y no intenta emular el comportamiento del módulo deferred con workarounds.

### DEFERRED ≠ ABANDONADO

Estos módulos son arquitectura planificada con bloqueos técnicos documentados. No se tratan como features eliminadas ni como promesas incumplidas — son trabajo en progreso con criterios de activación definidos.

### ESTADO DEl DASHBOARD

Runtime transaccional de recuperación BLOCKED. Estado: certificado y operacional. Ubicación: ~/vantage_notion_audit/scripts/rt1_server.py.

## 19. EVOLUCIÓN DEL SISTEMA

### CRITERIOS DE CAMBIO

El sistema reconoce cuándo un cambio es válido y cuándo no lo es. Esta distinción protege la estabilidad arquitectónica del pipeline.

### CAMBIOS VÁLIDOS

Condiciones que justifican modificación:

- Cambio estructural de mercado: nuevos job boards relevantes, cambios en ATS de empresas target
- Cambio en targets: nuevas empresas, nuevas exclusiones, ajuste de geografía
- Ineficiencia probada con datos: bottleneck documentado en pipeline runs
- Violación de boundary entre capas: orchestration haciendo intelligence, sistema calculando campos Class B de forma sistemática

### CAMBIOS INVÁLIDOS

Condiciones que NO justifican modificación:

- Score "se siente muy estricto" → el algoritmo determinista es intencional, no un bug
- Ready-to-Apply vacío → los inputs de búsqueda necesitan ajuste, no el threshold
- Un dead link apareció → comportamiento normal de mercado, no falla de sistema
- Frustración temporal → el sistema funciona, los inputs necesitan revisión

### ESTABILIDAD DE ARQUITECTURA CENTRAL

Los boundaries de capas no colapsan. La filosofía de verificación no se negocia. Los contratos de campo Class A/B no se mezclan. Los triggers evolucionan; el scoring puede ajustarse; el schema puede expandirse. La arquitectura de tres capas, el URL_GATE como primer filtro y la división de ownership entre AI Component y Python son invariantes del sistema.

### LINAJE HISTÓRICO

Preservado, no operacional:

El sistema mantiene registro de lo que fue construido y deprecado: GPT Atlas, Grok discovery, SEARCH-EXEC/SEARCH-SIGNAL, fórmulas de scoring pre-v5.0, workflows manuales pre-v6.0. Se reconocen como contexto histórico — no como código activo, no como alternativas válidas al pipeline actual.

Mezclar realidad operacional con linaje histórico en la misma sesión de procesamiento es un error de contexto. Si el usuario referencia un componente legacy, se identifica como tal y redirecciona al workflow activo equivalente.

# CAREER CANON

## A. PROFESSIONAL PROFILE

## ES

Estratega de Visual Merchandising & Brand Execution con más de 10 años de trayectoria en retail de lujo, moda y alto rendimiento. Especialista en traducir lineamientos globales en ejecuciones locales de alto impacto, liderando estrategias regionales en LATAM y gestionando presupuestos CAPEX/OPEX nacionales. Experto en storytelling visual, lanzamientos de producto (NPI) y habilitación de equipos de campo, con un historial probado en la optimización de KPIs comerciales (+43% tráfico) y eficiencia operativa (-74% costos). Perfil con alta capacidad analítica y técnica, enfocado en elevar la experiencia del consumidor y la coherencia de marca en redes propias, franquicias y wholesale.

## EN

Visual Merchandising & Brand Execution strategist with over 10 years of experience in luxury, fashion, and high-performance retail. Expert in translating global brand guidelines into high-impact local executions, leading LATAM regional strategies, and managing national CAPEX/OPEX budgets. Specialist in visual storytelling, new product introductions (NPI), and field team enablement, with a proven track record of optimizing commercial KPIs (+43% traffic) and operational efficiency (-74% costs). Highly analytical and technical profile, focused on elevating consumer experience and brand coherence across own stores, franchises, and wholesale channels.

## B. SKILLS CANON

| Categoría | ES | EN |
| --- | --- | --- |
| Estrategia Visual | Planeación estacional, Consumer-centric storytelling, Zoning & Mapping tools, manuales de ejecución regional | Seasonal planning, Consumer-centric storytelling, Zoning & Mapping tools, regional execution manuals |
| Operaciones & Finanzas | Control de presupuesto CAPEX/OPEX, negociación con proveedores, aperturas de Flagship Stores, remodelaciones y rollouts | CAPEX/OPEX budget control, vendor negotiation, Flagship Store openings, remodeling, and rollouts |
| Liderazgo & Training | Gestión de equipos directos e indirectos, coaching de alto desempeño, estandarización de procesos operativos y auditorías de campo | Direct and indirect team management, high-performance coaching, operational process standardization, and field audits |
| Stack Técnico | Adobe Creative Cloud (Illustrator, Photoshop, InDesign), SketchUp, AutoCAD, IWD, Keynote, IA Generativa (ChatGPT, Perplexity, Claude) | Adobe Creative Cloud (Illustrator, Photoshop, InDesign), SketchUp, AutoCAD, IWD, Keynote, Generative AI (ChatGPT, Perplexity, Claude) |
| Idiomas | Español (Nativo) · Inglés (Profesional Corporativo / Fluidez regional) | Spanish (Native) · English (Corporate Professional / Regional Fluency) |

## C. CAREER TIMELINE

| ID | Compañía | Rol Canónico | Período | País |
| --- | --- | --- | --- | --- |
| C01 | L'Oréal Luxe México | VM Coordinator – Luxury Division | 02/2025 – 03/2026 | México |
| C02 | Bisonte Experiential Marketing | Brand Environment & Store Design Coordinator | 2022 – 2023 | México |
| C03 | Levi Strauss & Co. (Dockers) | Senior Brand Environment Coordinator – LATAM | 2018 – 2021 | México / LATAM |
| C04 | Aéropostale México | Visual Merchandising Manager | 2017 – 2018 | México |
| C05 | El Palacio de Hierro (ALDO Group) | VM & Marketing Coordinator | 2012 – 2017 [CF02] | México |

## D. EXPERIENCE RECORDS

## C01 · L'Oréal Luxe México · Feb 2025 – Mar 2026

**Coordinador de Visual Merchandising & Brand Execution – División de Lujo** · [CF08: Valentino / Giorgio Armani / Ralph Lauren]

### ES

- Lidero la estrategia de VM para Valentino, Giorgio Armani y Ralph Lauren (fragancias), asegurando la consistencia de marca en canales de alto tráfico y lujo.
- Administro el presupuesto nacional de la división (CAPEX/OPEX), optimizando la inversión en materiales POP, displays y mobiliario de vitrinas para lanzamientos y campañas estacionales.
- Coordino proveedores locales e internacionales para la producción, importación e instalación de materiales, supervisando calidad de acabados y cumplimiento de especificaciones técnicas de la división.
- Ejecuté el despliegue nacional de campañas NPI clave en 2025 (Born in Roma, Stronger With You), coordinando producción y montaje con agencias externas bajo presupuesto asignado.
- Colaboro con Marketing y Trade Marketing para alinear el calendario comercial con la ejecución visual, actuando como embajador de marca en cuentas clave.

### EN

- Lead the VM strategy for Valentino, Giorgio Armani, and Ralph Lauren (fragrances), ensuring brand consistency across high-traffic and luxury channels.
- Manage the division's national budget (CAPEX/OPEX), optimizing investment in POP materials, displays, and window fixtures for launches and seasonal campaigns.
- Coordinate local and international vendors for production, importation, and installation of materials, overseeing finish quality and compliance with the division's technical specifications.
- Executed the national rollout of key NPI campaigns in 2025 (Born in Roma, Stronger With You), coordinating production and installation with external agencies within the assigned budget.
- Collaborate with Marketing and Trade Marketing to align the commercial calendar with visual execution, acting as brand ambassador at key accounts.

---

## C02 · Bisonte Experiential Marketing · 2022 – 2023

**Coordinador de Brand Environment y Store Design** · [P01: Adidas Brand Center Madero]

### ES

- Lideré la implementación visual y técnica para la apertura del Adidas Brand Center Madero (Flagship Store), cumpliendo con los estándares globales de la marca.
- Supervisé la producción y logística de materiales de Store Design en un proyecto rescatado a 3 meses de apertura, logrando entrega en fecha con 17 observaciones menores en punch list — ninguna bloqueante ni comprometiendo la experiencia del consumidor. [CF03 · CF04]
- Coordiné a proveedores especializados para garantizar la calidad en acabados y mobiliario, asegurando la integridad del diseño arquitectónico y visual.

### EN

- Led the visual and technical implementation for the Adidas Brand Center Madero (Flagship Store) opening, meeting the brand's highest global standards.
- Supervised production and logistics for Store Design materials on a project rescued 3 months before opening, achieving on-time delivery with 17 minor punch list observations — none blocking the opening or compromising the consumer experience. [CF03 · CF04]
- Coordinated specialized vendors to ensure quality in finishes and furniture, safeguarding architectural and visual design integrity.

---

## C03 · Levi Strauss & Co. (Dockers) · 2018 – 2021

**Senior Brand Environment Coordinator – LATAM** · [CF05: 270+ POS / 6 países]

### ES

- Gestioné la estrategia visual para 6 países en LATAM y 270+ puntos de venta, asegurando la estandarización regional de la marca. [CF05]
- Diseñé una estrategia de producción local que generó un ahorro del 74% en costos de campañas nacionales en México. [KPI03]
- Reduje en un 33% el tiempo de actualización de floorsets mediante la creación de manuales de Zoning & Mapping y herramientas digitales para field teams. [KPI04]
- Lideré un equipo de 3 coordinadoras directas y 3 indirectas, garantizando el 100% de cobertura POP durante la contingencia COVID-19 mediante coordinación remota. [KPI05]

### EN

- Managed the visual strategy for 6 countries in LATAM and 270+ points of sale, ensuring regional brand standardization. [CF05]
- Designed a local production strategy that generated 74% cost savings on national campaigns in Mexico. [KPI03]
- Reduced floorset update time by 33% through the creation of Zoning & Mapping manuals and digital tools for field teams. [KPI04]
- Led a team of 3 direct coordinators and 3 indirect reports, ensuring 100% POP coverage during the COVID-19 contingency through remote coordination. [KPI05]

---

## C04 · Aéropostale México · 2017 – 2018

**Gerente de Visual Merchandising** · [CF06: 21 reportes directos · CF07: 17 tiendas]

### ES

- Construí el área de VM desde cero, gestionando a 17 subgerentes de VM y 4 supervisores de zona (21 reportes directos en total). [CF06]
- Contribuí directamente a un incremento de +43% en tráfico y +18% en conversión en las 17 tiendas bajo mi supervisión estratégica. [KPI01 · KPI02 · CF07]
- Estandaricé los planogramas de categorías clave (Denim & Lifestyle), alineando la exhibición con los objetivos de ventas mensuales.

### EN

- Built the VM department from scratch, managing 17 VM Assistant Managers and 4 Zone Supervisors (21 direct reports in total). [CF06]
- Contributed directly to a +43% increase in traffic and +18% in conversion across the 17 stores under strategic supervision. [KPI01 · KPI02 · CF07]
- Standardized planograms for key categories (Denim & Lifestyle), aligning display with monthly sales objectives.

---

## C05 · El Palacio de Hierro (ALDO Group) · 2012 – 2017 [CF02]

**Coordinador de Visual Merchandising & Marketing**

### ES

- Coordiné la ejecución visual y de marketing para 17 tiendas retail y 12 corners wholesale, liderando aperturas y remodelaciones críticas.
- Supervisé la implementación de campañas globales, adaptando los lineamientos de la casa matriz en Canadá para el mercado mexicano.
- Desarrollé programas de capacitación para el personal de piso, elevando el estándar de mantenimiento visual y ejecución de lanzamientos. Durante los últimos 3 años del rol tuve a cargo una coordinadora Jr. con reporte directo.

### EN

- Coordinated visual and marketing execution for 17 retail stores and 12 wholesale corners, leading critical openings and remodels.
- Supervised the implementation of global campaigns, adapting Canadian headquarters' guidelines for the Mexican market.
- Developed training programs for floor staff, elevating the standard of visual maintenance and launch execution. During the last 3 years of the role, directly managed one Jr. Brand Coordinator.

## E. EDUCATION

| ID | Título | Institución | Año |
| --- | --- | --- | --- |
| ED01 | Licenciatura en Artes Visuales | Escuela Nacional de Artes Plásticas, UNAM | 2008–2012 |
| ED02 | Diplomado en Museos y Exposiciones | Facultad de Artes y Diseño, UNAM | 2014 |

## F. CERTIFICATIONS

| ID | Certificación | Institución | Año |
| --- | --- | --- | --- |
| CERT01 | Store Operations Leaders Orientation (VM, Sales & Ops) | ALDO Group, Montréal, Canadá | 2014 |
| CERT02 | AutoCAD & SketchUp Essentials | LinkedIn Learning | 2024 |

## G. MAJOR PROJECTS

## P01 · Adidas Brand Center Madero

**Compañía:** C02 · Bisonte Experiential Marketing · **Período:** 2022–2023

**ES:** Implementación visual y técnica del flagship store de Adidas en CDMX, bajo Blueprints y Store Design Guidelines internacionales. Coordinación de múltiples proveedores especializados — cadena de suministro, permisos, accesos y calendarización. Entrega en fecha con 17 observaciones menores en punch list, ninguna bloqueante para apertura. [CF03 · CF04 · KPI07]

**EN:** Visual and technical implementation of the Adidas flagship store in CDMX, under international Blueprints and Store Design Guidelines. Coordination of multiple specialized vendors — supply chain, permits, access, and scheduling. On-time delivery with 17 minor punch list observations, none blocking the opening. [CF03 · CF04 · KPI07]

---

## P02 · Dockers LATAM Rebranding

**Compañía:** C03 · Levi Strauss & Co. · **Período:** 2018–2021

**ES:** Rollout de rebranding Dockers en red nacional con cobertura del 100% de puntos de venta en México, entregado en tiempo y dentro del presupuesto asignado. El rollout regional LATAM (6 países / 270+ POS) fue interrumpido por la crisis COVID-19 antes de completar la cobertura regional. [KPI03 · CF05]

**EN:** Dockers rebranding rollout executed at national level with 100% door coverage in Mexico, delivered on time and within the assigned budget. The regional LATAM rollout (6 countries / 270+ POS) was interrupted by the COVID-19 crisis before full regional coverage could be completed. [KPI03 · CF05]

---

## P03 · AeroFest Frontón México

**Compañía:** C04 · Aéropostale México · **Período:** 2018

**ES:** Coordinación de la participación de Aéropostale en el AeroFest (Frontón México, 2018) junto con Liverpool. Activación de marca de gran formato en venue externo.

**EN:** Coordination of Aéropostale's participation in AeroFest (Frontón México, 2018) alongside Liverpool. Large-format brand activation at an external venue.

## H. ACHIEVEMENT LIBRARY

| Achievement | Compañía | KPI Ref |
| --- | --- | --- |
| Despliegue nacional campañas NPI 2025 (Born in Roma, Stronger With You) | C01 | — |
| Gestión presupuesto CAPEX/OPEX nacional para 3 marcas simultáneas | C01 | — |
| Apertura Adidas Brand Center Madero en fecha · 17 observaciones menores · ninguna bloqueante | C02 | KPI07 |
| Reducción 74% costos campañas visuales nacionales | C03 | KPI03 |
| Reducción 33% tiempo de actualización de floorsets | C03 | KPI04 |
| 100% cobertura POP en 270+ POS durante COVID-19 | C03 | KPI05 |
| Supervisión estrategia visual en 6 países LATAM | C03 | CF05 |
| +43% tráfico en red de 17 tiendas | C04 | KPI01 |
| +18% conversión en red de 17 tiendas | C04 | KPI02 |
| Construcción área de VM desde cero · 21 reportes directos | C04 | CF06 |
| Coordinación de 17 tiendas retail + 12 corners wholesale | C05 | — |
| Liderazgo de coordinadora Jr. con reporte directo (últimos 3 años en rol) | C05 | — |

## I. CORE KPIs

| ID | Valor | Compañía | Contexto |
| --- | --- | --- | --- |
| KPI01 | Traffic +43% | C04 | Aéropostale · red de 17 tiendas · 2017–2018 |
| KPI02 | Conversion +18% | C04 | Aéropostale · red de 17 tiendas · 2017–2018 |
| KPI03 | Campaign Cost Reduction -74% | C03 | Levi's/Dockers · campañas nacionales México |
| KPI04 | Floorset Time Reduction -33% | C03 | Levi's/Dockers · manuales Zoning & Mapping |
| KPI05 | POP Coverage 100% | C03 | 270+ POS · LATAM · contingencia COVID-19 |
| KPI06 | Rebranding Coverage 100% | C03 | Levi's/Dockers · red nacional México · en tiempo y presupuesto ✅ Resolved |
| KPI07 | Adidas Punch List Count (17) | C02 | Adidas Brand Center Madero · CF03 · CF04 |
| KPI08 | Years Experience (10+ Canonical) | — | Canónico |

## J. CANONICAL FACTS

| ID | Hecho |
| --- | --- |
| CF01 | ALDO Certification Year = 2014 |
| CF02 | ALDO Employment Period = 2012–2017 |
| CF03 | Adidas Punch List = 17 Minor Observations |
| CF04 | Adidas Punch List Severity = Non-Blocking |
| CF05 | Levi's Coverage = 270+ POS / 6 LATAM Countries |
| CF06 | Aéropostale Team = 21 Direct Reports |
| CF07 | Aéropostale Network = 17 Stores |
| CF08 | L'Oréal Brands = Valentino / Giorgio Armani / Ralph Lauren |
| UF01 | L'Oréal End Date = March 2026 |
| UF02 | Canonical Email = mauricio.meyran@icloud.com |
| UF03 | Certifications Canon = ALDO Group (2014) + AutoCAD & SketchUp Essentials (2024) ONLY. No additional certs valid. |

## K. POSITIONING MODES

| ID | Nombre |
| --- | --- |
| N1 | Luxury VM Strategist |
| N2 | Store Design & Flagship Execution |
| N3 | Field Execution & Route Supervision |
| N4 | Luxury Heritage & Aesthetic Curation |
| N5 | Retail Brand Marketing & Consumer Experience |
| N6 | Retail Training & Capability Building |

---

# DERIVED OUTPUTS · ARCHIVE

> Los siguientes activos son outputs derivados del Career Canon. **No son fuente de verdad.**
> 

| Asset | Fecha | Status |
| --- | --- | --- |
| CV · Christian Dior · VM Coordinator | Marzo 2026 | Derived Output |
| CV · Guerlain · VM Coordinator | Marzo 2026 | Derived Output |
| CV · Pandora Jewelry · VM & Trade Senior Specialist | Marzo 2026 | Derived Output |
| CV · Cartier (Richemont) · VM Coordinator JR124797 | Marzo 2026 | Derived Output |
| CV · Nike · Manager VM Nike Direct LATAM | Marzo 2026 | Derived Output |
| CV · Nike · Lead Brand Creative LATAM | Marzo 2026 | Derived Output |
| CV · Blue Star Group · Visual Commercial Manager | Mayo 2026 | Derived Output · UNRESOLVED_REFERENCE |
| CV · ABG · Retail Brand Development | Mayo 2026 | Derived Output · UNRESOLVED_REFERENCE |
| Resume Master ES | — | Referencia Histórica |
| Resume Master EN | — | Referencia Histórica |

MASTER

CV Optimizado — Pandora Jewelry · VM & Trade Senior Specialist (03/26)

2026_Mauricio_Meyran_Manager_VM_NIKE_R-74673

2026_Mauricio_Meyran_Manager_VM_NIKE_R-74673

2026_Mauricio_Meyran_Visual_Commercial_Manager_BlueStarGroup

CV ABG — Retail Brand Development (EN)

---

## L. OUTPUT CONTRACT

— Figma Tag Schema

> Formato base obligatorio para todos los Derived Outputs generados desde el Career Canon. Aplica ES + EN.
> 

## Tag Registry

| Tag | Slot | Tipo |
| --- | --- | --- |
| `2040:46` | Nombre | LOCKED |
| `2040:47` | Tagline + contacto | Variable (título por modo) |
| `2031:22` | Header Perfil | LOCKED |
| `2031:24` | Perfil párrafo 1 | Variable por modo |
| `2031:25` | Perfil párrafo 2 | Variable por modo |
| `2031:27` | Header Habilidades | LOCKED |
| `2031:29` | Skill 1 — Estrategia Visual | Variable por modo |
| `2031:30` | Skill 2 — Operaciones & Finanzas | Variable por modo |
| `2031:31` | Skill 3 — Liderazgo & Training | Variable por modo |
| `2031:32` | Skill 4 — Stack Técnico | LOCKED |
| `2031:33` | Skill 5 — Idiomas | LOCKED |
| `2031:35` | Header Experiencia | LOCKED |
| `2031:37` | C01 Empresa | LOCKED |
| `2031:38` | C01 Rol + período | Variable (título ajustable) |
| `2031:39` | C01 Bullet 1 | Variable por modo |
| `2031:40` | C01 Bullet 2 | Variable por modo |
| `2031:41` | C01 Bullet 3 | Variable por modo |
| `2031:42` | C01 Bullet 4 | Variable por modo |
| `2032:167` | C02 Empresa | LOCKED |
| `2032:168` | C02 Rol + período | LOCKED |
| `2032:170` | C02 Bullet 1 | Variable por modo |
| `2032:171` | C02 Bullet 2 | Variable por modo |
| `2032:172` | C02 Bullet 3 | Variable por modo |
| `2032:174` | C03 Empresa | LOCKED |
| `2032:175` | C03 Rol + período | LOCKED |
| `2032:177` | C03 Bullet 1 | Variable por modo |
| `2032:178` | C03 Bullet 2 | Variable por modo |
| `2032:179` | C03 Bullet 3 | Variable por modo |
| `2032:181` | C04 Empresa | LOCKED |
| `2032:182` | C04 Rol + período | LOCKED |
| `2032:184` | C04 Bullet 1 | Variable por modo |
| `2032:185` | C04 Bullet 2 | Variable por modo |
| `2032:186` | C04 Bullet 3 | Variable por modo |
| `2032:191` | C05 Empresa | LOCKED |
| `2032:192` | C05 Rol + período | LOCKED |
| `2032:194` | C05 Bullet 1 | Variable por modo |
| `2032:195` | C05 Bullet 2 | Variable por modo |
| `2032:196` | C05 Bullet 3 | Variable por modo |
| `2032:197` | C05 Bullet 4 | Variable por modo |
| `2032:199` | Header Formación | LOCKED |
| `2032:201` | ED01 | LOCKED |
| `2032:202` | ED02 | LOCKED |
| `2032:204` | Header Certificaciones | LOCKED |
| `2032:206` | CERT02 | LOCKED |
| `2032:207` | CERT01 | LOCKED |

## Formato de Entrega Obligatorio

Cada Derived Output generado bajo este contrato requiere **dos outputs simultáneos**:

1. **Página en Notion** — contenido legible, sin tags, para histórico y revisión. Incluye footer con metadata: Output Contract version, Positioning Mode activo, referencia canónica al Canon.
2. **Archivo .md con Figma tags explícitos** — descargable, formato idéntico al archivo de referencia CANON_MARKDOWN.md. Cada slot encabezado por `###### figma_text_id` en línea propia. Este archivo es el entregable de trabajo para actualizar el archivo Figma.

El output de Notion **no reemplaza** al .md con tags. Ambos son obligatorios.

---

## Reglas de Serialización

- Cada tag = párrafo independiente (sin listas, sin guiones)
- Bold = keywords estratégicos dentro del párrafo
- Empresa = bold standalone en su propio tag
- Rol = **bold rol** *italic período*
- Skills = **Categoría**: texto plano
- Tagline `2040:47` = **[Título · Subtítulo]** · Ciudad | Tel | Email | LinkedIn | Portfolio
- `&` en nombres de empresa → `&amp;`

## Portfolio por Idioma

| Idioma | URL |
| --- | --- |
| ES | mmeyranesp.myportfolio.com |
| EN | mmeyraneng.myportfolio.com |

## Activación por Positioning Mode

Los slots **Variable por modo** se derivan del Positioning Mode activo (sección K · N1–N6):

- `2040:47` tagline
- `2031:24/25` párrafos de perfil
- `2031:29/30/31` skills 1–3
- Bullets C01–C05 priorizados según el modo activado

2026_Mauricio_Meyran_VM_Coordinator_Zegna — Output Contract v1.0 TEST