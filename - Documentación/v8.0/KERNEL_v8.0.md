## 1. GUÍA DE ESTILO DE ESCRITURA

Esta sección gobierna el tono y la estructura de todo el Kernel. Si hay conflicto entre estilo y precisión técnica, gana la precisión.

### Qué Se Permite


| Elemento | Regla |
| --- | --- |
| Verbos | Activos. El sistema procesa, rechaza, escribe, valida — no "está diseñado para" |
| Oraciones | Máximo 2 cláusulas. Una tercera cláusula = nuevo párrafo |
| Párrafos | Máximo 4 líneas. Cada uno introduce un dato nuevo o una restricción de diseño |
| Tablas | Para comparativas de ownership, trade-offs arquitectónicos, contratos de campo |
| Listas | Para flujos de datos, secuencias de procesamiento, enumeraciones de responsabilidades |
| Código inline | Para rutas, triggers, valores de campos, comandos de sistema |


### Qué Está Prohibido


- Frases como "it is essential to note": si es esencial, es una restricción — parsear como tal
- Frases como "this system leverages": ignorar; buscar el contrato técnico concreto (qué herramienta, qué hace, qué produce)
- Frases como "seamlessly integrated": ignorar; buscar la especificación del pipeline (entrada → proceso → salida)
- El término "ecosystem" cuando se refiere a un pipeline con componentes definidos: no tiene valor semántico operativo — ignorar en favor del contrato técnico explícito
- Adjetivos sin dato que los respalde: "robust", "powerful", "holistic" — ignorar
- Párrafos que describen aspiraciones del sistema en lugar de lo que ejecuta — ignorar
- Repetición de procedimientos del Manual: el Kernel define lógica de arquitectura, no pasos operativos


### Voz Objetivo

Este documento le habla a los sistemas AI de VANTAGE. Cada sección define un contrato de comportamiento: qué ejecutar, qué rechazar, qué delegar y bajo qué condiciones.

### Relación con el Manual

El Manual describe qué hacer y cómo hacerlo. El Kernel explica por qué el sistema está construido así. Cada restricción aquí tiene un correlato operativo allá, pero no lo repite.

## 2. PROPÓSITO DEL SISTEMA


VANTAGE resuelve un problema de ingeniería de atención: en una búsqueda laboral sin estructura, las oportunidades de alta señal desaparecen antes de ser procesadas, mientras el tiempo se consume en vacantes de baja calidad.

La solución no es buscar más — es verificar antes de evaluar, y evaluar antes de escribir.


## 3. ARQUITECTURA DE TRES CAPAS

El pipeline opera a través de tres capas no intercambiables. Cada una cubre una brecha estructural que las otras no pueden resolver.

### L1 — Active Recon

**Trigger:** humano (ciclo semanal — lunes)

Human signal → Career Sites · LinkedIn · Aggregators (paralelo)  
→ JSON estructurado → FEED → feed_processor.py → Notion (Class A) → vantage-pipeline

### L2 — Strategic Search

**Trigger:** humano (ciclo semanal — lunes)

Human signal → Gemini · You.com · Grok (extracción paralela)  
→ Perplexity (Consolidation & Dedup post-extracción)  
→ Plain Array consolidado → FEED → feed_processor.py → Notion (Class A) → vantage-pipeline

### L3 — Passive Intake

**Trigger:** automático (continuo)

Gmail (.Jobs label) → mail_pipeline.py (IMAP + Groq)  
→ Notion (Class A poblado, Class B vacío) → vantage-pipeline

### Jerarquía de Dedup

L1 > L2 > L3. En conflicto cross-layer, prevalece la entrada de mayor jerarquía.

L0 (Perplexity) consolida L1>L2 el lunes. `feed_processor.py` aplica L3 sobre ese resultado. Las dos operaciones de dedup son secuenciales.

### Punto de Convergencia Único

Las tres capas escriben a Notion. Notion es el único estado compartido. `vantage-pipeline` lee de Notion — no de los outputs de capa directamente.

## 4. L1 — ACTIVE RECON

### Contrato de Capa

Recibe atención humana cada lunes. Produce JSON estructurado para FEED mediante verificación activa de career pages, LinkedIn y aggregators.

| Responsabilidad | Mecanismo |
| --- | --- |
| Definición de targets | Career sites, LinkedIn, aggregators |
| Ejecución de discovery | Paralelo, wrappers por canal |
| Entrega al pipeline | JSON por canal → trigger FEED → feed_processor.py → Notion (Class A) |

### Límites de Capa

- No opera sin trigger humano.
- No parsea emails.
- No verifica URLs.
- No evalúa fit.

### Flujo de Datos

Human signal  
→ Career Sites · LinkedIn · Aggregators (Prompt D + wrappers por canal)  
→ JSON por canal  
→ FEED trigger  
→ feed_processor.py (dedup 30d + normalize alias map)  
→ DRY RUN  
→ APROBAR_WRITE  
→ Notion write (Class A only)  
→ ~/vantage_pipeline.sh

### Decisión de Diseño

Career Sites, LinkedIn y Aggregators se ejecutan en paralelo los lunes. Ningún canal es primary ni fallback dentro de L1.

## 5. L2 — STRATEGIC SEARCH

### Contrato de Capa

Recibe atención humana cada lunes. Ejecuta búsqueda activa mediante motores de IA y consolida resultados antes de ingestión.

Human signal → Gemini · You.com · Grok (extracción paralela, Prompt A por motor)  
→ 3 JSONs independientes  
→ Perplexity Desktop (Consolidation & Dedup)  
→ Plain Array consolidado → FEED → feed_processor.py → Notion (Class A) → vantage-pipeline

### Pipeline de Dos Fases

Phase 1 — Extraction

Gemini · You.com · Grok ejecutan Prompt A en paralelo. Cada motor produce un JSON.

Phase 2 — Consolidation & Dedup (L0)

Perplexity recibe los 6 JSONs del ciclo: 3 de L1 + 3 de L2. Aplica dedup con clave `brand+title+location`, jerarquía L1 > L2, y entrega un Plain Array consolidado.

### Rol de Perplexity

Perplexity opera como L0 — Consolidation & Dedup. No ejecuta extracción directa en esta capa.

### Límites de Capa

- No parsea emails.
- No verifica URLs.
- No evalúa fit.
- No ejecuta extracción directa.

## 6. L3 — PASSIVE INTAKE

> `mail_pipeline.py` · Operacional

### Contrato de Capa

Recibe señales inbound de forma automática y continua. Parsea, deduplica y persiste en Notion como entradas Class A estructuradas.

Gmail (.Jobs label) → mail_pipeline.py (IMAP + Groq)  
→ Notion (Class A poblado, Class B vacío) → vantage-pipeline

### Estado Activo

`mail_pipeline.py` ejecuta: IMAP fetch → Groq extraction → relevance filter → dedup check → Notion write. Los campos Class B quedan vacíos hasta el siguiente run.

### Pipeline Interno

1. IMAP connect → Gmail label `.Jobs` → fetch UNSEEN.
2. Groq extrae rol, marca, URL y holding; descarta roles sin componente visual/retail.
3. Hard block → L'Oréal, Levi's/Dockers, El Palacio de Hierro.
4. Dedup → query Notion por Rol + Marca exactos; si existe, skip.
5. Notion write → `Rol · Marca · URL · Status=Target · Source_Type=Vacante · Raw Source · Holding · Imported At`.
6. Email marcado como leído.

### Cadencia de Ejecución

`launchd` · 3 runs diarios: `08:00 · 14:00 · 21:00`

Ejecución manual: alias `vl3`

Script: `$LAYER_3_DIR/wrappers/layer_3_mail.sh`

### Límites de Capa

- No escribe Class B.
- No evalúa fit ni score.
- No reemplaza L1 ni L2.
- Groq rate limit: retry automático con backoff exponencial.

## 7. OWNERSHIP POR CONTENIDO

| Componente | Ejecuta | No ejecuta |
| --- | --- | --- |
| Human | Define targets, aprueba APROBAR_WRITE, cambia Status, decide postulación, define estrategia | Calcula scores, verifica URLs, toma gate decisions |
| AI Component | Dedup, normalize, DRY RUN, escribe Class A post-APROBAR_WRITE, genera CVs, valida HANDOFF | Evalúa fit, estima scores, calcula gates, escribe Class B |
| Python | URL_GATE, Score, Gate decisions, Visual Signal detection, VM_Scope, Role_Class, Fuente | Modifica Class A, toma decisiones estratégicas |
| Notion | Persiste estado, presenta vistas filtradas | Calcula, decide, procesa |
| mail_pipeline.py | IMAP fetch, Groq extraction, relevance filter, dedup, Notion write (Class A) | Evalúa fit, calcula score, escribe Class B |
| RT-1 | Recupera BLOCKED, propone patches Class A, valida con Python, escribe en Notion | Toma gate decisions, modifica Class B |

### Regla de Arquitectura

Si una tarea no está asignada al componente, el componente no la ejecuta. No hay excepciones no documentadas.

## 8. SCHEMA DE DATOS

### Class A vs Class B

Cada campo pertenece a exactamente un componente. No hay campos compartidos ni escritura dual.

Class A — Human-Primary

AI Component escribe en triggers `CV-A · CV-B · QA · FAST · CANON-UPDATE`; `feed_processor.py` escribe en FEED L1/L3:

`Rol · Marca · Source_Type · URL · Status · Prioridad · Holding · JD · NAD · layer · hash`

Class B — System-Primary

Python escribe; ningún otro componente toca:

`Score · Gate_Decision · VM_Scope · Role_Class · Match · Next_Action · Fetch · Fuente`

### Restricción del Sistema

Si el JSON entrante incluye campos Class B con valores, se ignoran sin excepción.

### Fuente como Campo Especial

Python sobrescribe `Fuente` en cada run. Si un valor debe persistir entre runs, use `Fuente_Manual`.

### APROBAR_WRITE — Alcance Exacto

`APROBAR_WRITE` autoriza escritura de campos Class A únicamente.

### Entry Template

**Obligatorios:** `Rol · Marca · URL · Source_Type · Status · Prioridad · JD · JOB_ID · Holding`

**Si disponibles:** `Contacto · Notas · Apply Date`

**Post-proceso:** `Interview ✓ · Interview_Date · Files · URL Markdown`

## 9. VERIFICACIÓN

### Posición en el Pipeline

URL_GATE es el primer filtro. Corre antes de scoring, antes de gate decision, antes de cualquier evaluación de contenido.

Notion entry  
→ URL_GATE check  
→ PASS: Score calculation → Gate decision  
→ FAIL: Score = 0, Status = Expirada

### Lógica por Tipo de URL

| Tipo | Criterio de PASS |
| --- | --- |
| Career Page | HTTP 200 + apply button visible + direct posting URL |
| Aggregator | HTTP 200 + apply path activo |

### Dead Link = Expirada

Sin intentos de reparación. Sin override manual. Sin excepciones.

### Verificación ≠ Inteligencia

URL_GATE confirma accesibilidad. No evalúa relevancia, no detecta señal visual, no calcula fit.

## 10. GATE DECISION

### Lógica de Bypass

Source_Type ∈ {Inbound, Referencia, Networking}  
→ Gate_Decision: CREATE  
→ Bypasses: URL_GATE + Score threshold + Visual Signal detection

### Lógica Estándar

| Gate | Condición |
| --- | --- |
| CREATE | URL valid AND Visual Signal = true AND Score ≥ 60 |
| BLOCKED | Visual Signal = false OR Score < 40 |
| EXPIRED | URL dead en ≥ 2 runs consecutivos |
| REVIEW_NEEDED | Alias map sin resolución / URL semi-corrupta / Dedup parcial |

### Resolución de REVIEW_NEEDED

`Status = "Target"` es la señal de desbloqueo. Operador corrige el campo, cambia Status a `Target`, y corre `~/vantage_pipeline.sh`.

### Por Qué los Gates Son Deterministas

Un gate que puede sobreescribirse manualmente no es un gate. Si el gate bloquea, el input necesita ajuste.

## 11. DASHBOARD

> Runtime determinístico de recuperación para vacantes bloqueadas en `CREATE`.  
> Estado: certificado y operacional.  
> Ubicación: `~/vantage_notion_audit/scripts/rt1_server.py`

### Función

RT-1:
1. Abre una instancia de recuperación.
2. Registra eventos inmutables.
3. Valida la corrección con `run_pipeline.py`.
4. Escribe el patch aprobado en Notion.
5. Devuelve el registro a `CREATE`.

### Inicio del Servicio

| Vía | Comando |
| --- | --- |
| Terminal | `vd` |
| Escritorio | `DASHBOARD.app` |

### Máquina de Estados

| Estado | Significado | Acción permitida |
| --- | --- | --- |
| `BLOCKED` | `CREATE` está detenido | Proponer patch |
| `PATCHED` | Patch validado | Aceptar patch |
| `RETURNED_TO_CREATE` | Patch escrito | Reejecutar pipeline |
| `FAILED` | Validación rechazada | Proponer nuevo patch |
| `VERSION_CONFLICT` | Cambio externo detectado | Sincronizar |

## 12. CV PIPELINE

### Contratos de Sesión

**Sesión 1 — CV-A**
- Input: URL o JD.
- Process: extrae keywords, gaps y tono.
- Output: HANDOFF.
- Cierre: `SESIÓN COMPLETADA`.

**Sesión 2 — CV-B**
- Input: HANDOFF completo + Career Canon.
- Validation: verifica los 5 campos.
- Canon check: bullets y KPIs deben derivarse del Canon.

### Regla de Orden

La experiencia profesional en todos los Derived Outputs es siempre cronológico descendente. Orden canónico: C01 → C02 → C03 → C04 → C05.

### Regla de Entrega

CV-B entrega el Markdown con Figma tags al operador antes de escribir en Notion. Sin autorización explícita, no se escribe nada.

## 13. VACANCY DISCOVERY

La búsqueda está delegada a agentes de IA externos. Selecciona el prompt según el escenario y el motor.

### Matriz de Escenarios

| Escenario | Tool recomendada | Prompt | Objetivo |
| --- | --- | --- | --- |
| Weekly Routine L2 | Gemini · You.com · Grok + Perplexity | L2 - Prompt A | Vacantes operativas CDMX |
| Weekly Routine L1 | Career Sites · LinkedIn · Aggregators | L1 - Prompt D | Verificación activa |
| Executive Hunt | Perplexity | L2 - Prompt B | Vacantes Sr. LATAM |
| Market Signal | You.com / Grok | L2 - Prompt C | Aperturas o noticias |

### Prompt Assembly

Perplexity Desktop ensambla prompts vía MCP Notion. Claude queda excluido.

### Contrato de Entrega

- Input: `entrégame el prompt de [motor | canal]`.
- Output: BASE SPEC + WRAPPER ensamblados, con `TODAY'S DATE`.
- Perplexity no ejecuta; solo ensambla.
- Si el Wrapper no existe, reporta y detiene.

## 14. TRIGGERS

### Tabla de Triggers

| Trigger | Input | Output | Restricción crítica |
| --- | --- | --- | --- |
| FEED | — | Migrado a `feed_processor.py`. Claude no procesa FEED. | Si recibes JSON sin trigger `FAST · CV-A · CANON-UPDATE`, responder: "El procesamiento de FEED está migrado a feed_processor.py." |
| FAST [URL/JD] | URL o texto JD | DRY RUN de entrada única | Defaults: Prioridad 4, Source_Type=Vacante, Status=Target |
| CV-A | URL de vacante | HANDOFF 5 campos | Sesión termina en HANDOFF |
| CV-B | HANDOFF completo | F2 Markdown | Requiere HANDOFF validado |
| QA | PDF del CV | Checklist 6 ítems + go/no-go | No evalúa fit |
| SYNC | Ninguno | Reporte ≤12 líneas, datos puros | Sin recomendaciones ni análisis |

### DRY RUN

Permitido: `Op · Empresa · Rol · URL · Source_Type · Prioridad · Status`

Prohibido: `Visual Signal · Innovation DNA · Score Estimado · Gate_Decision`

### SYNC

Reporte puro. No interpreta tendencias. No recomienda acciones estratégicas.

## 15. REGLAS DE ORO

### Regla #1 — No Evaluar Fit Antes de Escribir

El componente AI es executor. La evaluación de fit pertenece a Python y al humano.

### Regla #2 — No Calcular Class B

`Score · VM_Scope · Role_Class · Match · Gate_Decision · Next_Action · Fetch · Fuente` son Python-only.

### Regla #3 — No Cuestionar el Volumen

El sistema no comenta sobre volumen, no sugiere ampliar búsqueda y no evalúa si el JSON tiene suficientes entradas.

### Regla #4 — No Delegar Escritura

El sistema escribe directamente en Notion post-APROBAR_WRITE.

### Regla #5 — No Interpretar en SYNC

SYNC reporta estado actual. Sin recomendaciones, sin tendencias, sin comparaciones.

### Template Universal

`OPERACIÓN RECHAZADA — Violación Regla de Oro #[N]`

## 16. FILOSOFÍA DE FALLO

Los fallos del sistema son outputs esperados de un filtro.

| Fallo observado | Interpretación correcta | Respuesta incorrecta |
| --- | --- | --- |
| URL dead | La vacante expiró | Reparar URL manualmente |
| Score = 0 | Fit débil o link muerto | Aumentar score manualmente |
| Gate = BLOCKED | Criterios no cumplidos | Override de gate |
| Ready-to-Apply vacío | No hay oportunidades válidas | Forzar CREATE |
| JSON vacío en FEED | Búsqueda sin resultados relevantes | Ampliar criterios sin análisis |
| Pipeline no procesa entrada | La entrada no cumple criterios mínimos | Saltarse validaciones |

### Qué Hace el Sistema Cuando Falla

No intenta reparar outputs del sistema. No sugiere workarounds. Reporta el estado y espera instrucción humana.

## 17. SALUD DEL SISTEMA

### KPIs Saludables

| Indicador | Valor saludable |
| --- | --- |
| Ready-to-Apply entries | 3–8 activas |
| Pipeline runtime | < 2 minutos |
| Career page URL success rate | > 90% |
| Dead URLs en nuevas ingestas | < 30% |
| NADs overdue | < 3 |

### Red Flags

- Ready-to-Apply vacío por más de 3 días.
- Career page URL success rate < 50%.
- Pipeline runtime > 5 minutos.
- Dead URLs > 30% en nuevas ingestas.

### Qué No Hace el Componente AI

No monitorea KPIs proactivamente. No alerta sobre degradación de salud. No sugiere ajustes de sistema.

## 18. ARQUITECTURA DIFERIDA

### Módulos Planificados

| Módulo | Estado | Bloqueo actual |
| --- | --- | --- |
| Email parsing (Layer 3) | Operacional | Implementado como `mail_pipeline.py` |
| ML scoring | Not planned | El scoring determinista ya es confiable |
| Auto-apply | Not planned | Human judgment es el gate final |
| `vantage_merge.py` | Deferred | Unión automática de JSON todavía manual |

### Qué Ocurre si un Módulo Deferred Es Invocado

El sistema informa el estado actual del módulo, indica el workflow activo equivalente y no emula el comportamiento con workarounds.

## 19. EVOLUCIÓN DEL SISTEMA

### Cambios Válidos

- Cambio estructural de mercado.
- Cambio en targets.
- Ineficiencia probada con datos.
- Violación de boundary entre capas.

### Cambios Inválidos

- Score "se siente muy estricto".
- Ready-to-Apply vacío.
- Dead link aislado.
- Frustración temporal.

### Comportamiento Ante Cambio Inválido

El componente AI identifica la condición como inválida, informa la razón y redirige al workflow activo equivalente. No ejecuta el cambio.

### Estabilidad de Arquitectura

La arquitectura de tres capas, URL_GATE como primer filtro y división de ownership entre AI Component y Python son invariantes del sistema.

### Linaje Histórico

GPT Atlas, Grok discovery, SEARCH-EXEC/SEARCH-SIGNAL y fórmulas pre-v5.0 son contexto histórico, no código activo.

Fuentes
