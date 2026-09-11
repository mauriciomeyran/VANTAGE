# CONTRATO DE SESIÓN — Refactor completo del pipeline VANTAGE Tracker (Devin)

**Para:** Devin (agente de ingeniería autónomo) · **De:** Mauricio Meyrán (operador) vía auditoría Arena 2026-09-11
**Repo:** `mauriciomeyran/VANTAGE` · **Base:** `main` @ `467af9c` · **Documento hermano (lectura obligatoria primera):** `handoffs/AUDITORIA_TRACKER_E2E_2026-09-11.md` (radiografía con evidencia `archivo:línea` de cada afirmación aquí contenida)
**Naturaleza del encargo:** PLAN DE IMPLEMENTACIÓN/DESPLIEGUE + código del pipeline refactorizado. **Devin NO escribe en el Notion de producción bajo ninguna circunstancia** (sin token, sin MCP de escritura, sin scripts con credenciales reales). El despliegue (migración de schema y datos) lo ejecuta Claude vía Notion MCP, bajo aprobación explícita de Mau paso a paso, con dry run obligatorio antes de cada escritura (protocolo APROBAR_WRITE vigente, `KERNEL:SCHEMA-006`).

---

## 1. Objetivo y prohibición de parches incrementales

Diseñar y construir el reemplazo completo del pipeline Tracker (ingesta → scoring → gate → cleanup → terminales), desde cero, gobernado por **un solo mapa de flujo lógico** (§2). Queda explícitamente prohibido:
- Agregar entradas a whitelists/blacklists existentes (`STATUS_TERMINAL_MAP`, `_PROTECTED_STATUSES`, skips ad-hoc por fase, `is_terminal_state`, etc.).
- Agregar fases numeradas (`3.5.2`, `3.7`…) o scripts writers nuevos sobre el mismo Tracker.
- "Sincronizar" el fork `Dashboard/scripts/layer_1_run_dash.py` con `layer_1_run.py`: el fork se **retira** (decisión arquitectónica, §6.5), no se iguala.
- Cualquier cambio que deje dos escritores Python con semántica divergente sobre el mismo campo.

Criterio de aceptación global: **cada transición de `Status` tiene exactamente un gate responsable, exactamente una lista de protección, y respeta ediciones manuales recientes como señal de máxima prioridad** (§2.3). Si el diseño final necesita una tabla tipo "cobertura por fase × status" con más de una columna de protección, el diseño está mal: vuelve a §2.

## 2. El mapa de flujo lógico único (entregable central)

### 2.1 Fuente única de verdad para transiciones
- Un solo módulo (nombre sugerido `tracker_flow.py`, ubicación `Layer_1/scripts/`) que contenga: (a) el enum/constantes de TODOS los estados y acciones válidos (cerrado: lo no listado se rechaza, nunca se procesa como operativo — invierte el default actual B11); (b) la matriz de transición permitida `(estado_origen, evento) → estado_destino` (reemplaza `KERNEL:GATE-DECISION-011` como ejecutable; el doc se actualiza para reflejar el código, no al revés); (c) el predicado único `is_mutable(record, actor)` que TODOS los writers (pipeline, ingesta, dedup, tidy-automatizable) consultan antes de escribir.
- Las 3+ rutas actuales hacia `Expirada` (F2 URL, F3.5 misfit, F3.5.1 NAD) se consolidan en **un solo gate de archivo** con una sola firma de decisión `(razón, evidencia, actor, timestamp)` y una sola escritura atómica `{Status, Next_Action, Gate_Decision, Notas+=…}`. La nota determinista `generate_archive_notes()` se conserva como formato (es el único mecanismo de trazabilidad que funciona) pero se emite una sola vez por transición (cierra la doble-nota §1.2.2 de la radiografía).
- Orden total de evaluación documentado y testeado: protección-manual → terminalidad → elegibilidad → cómputo. `gate()` (técnico) y `gate_logic()` (negocio) se fusionan o se ordenan con precedencia explícita testeada — hoy coexisten sin contrato (`KERNEL:GATE-DECISION-008` describe la dualidad pero nada la enforcea).

### 2.2 Estados y valores: diseño desde errores históricos, no desde cero ingenuo
Antes de proponer el vocabulario, Devin DEBE leer y citar en el diseño (qué decisión histórica respeta y por qué):
- `Documentación/ACTIVE/Changelog Archivo.md`: v9.14.5 (catch-all destructivo eliminado — no reintroducir defaults destructivos), v9.17.2/H3 (mecanismos fantasma documentados — todo estado debe tener productor Y consumidor en código), v9.18.0/H1 (Score ignorado por gate — bandas como contrato testeado), v9.19.0/H2 (terminales recalculados — protección como predicado único, no por fase), v9.19.1 (D-001/D-003: listas paralelas — la lección es unificar, no extender), v9.19.2/D-002 (asimetría MCP — el guard debe cubrir TODAS las vías de escritura, no una), v9.20.1/2 (forma del objeto Notion — ningún acceso a schema sin verificación contra schema real), v9.21.0 (dedup sin survivor — definir survivor canónico o no auto-marcar), v9.21.36/40 (fix que mató a otro fix — prohibido merges de ramas de decisión sin test de alcanzabilidad; cada rama `if` nueva requiere test que la ejecuta), v9.21.30 (precedente vantage-cv-b v9.16→v10.0.0: refactor consolidado ante ≥3 parches — este encargo es su equivalente Tracker).
- `Documentación/ACTIVE/Kernel.md` §§07/09/11.2 y `MANUAL:WEEKLY-FLOW-002` (contrato REVIEW_NEEDED→Target): el refactor decide explícitamente — **o** implementa de verdad el bloqueo Class-B-mientras-REVIEW_NEEDED (hoy fictional, radiografía §4.6) **o** lo elimina del contrato y diseña el flujo real (Target-procesable). Lo prohibido es mantenerlo documentado-sin-implementar.
- Decisiones ya tomadas que NO se reabren: `auto_archive.py` permanece deprecado (decisión operador 2026-08-01, `KERNEL:GATE-DECISION-007`); `APROBAR_WRITE` como única autorización de escritura; `HO-######` seriales para handoffs; `Aéropostale` NO es hard block.

### 2.3 Ediciones manuales recientes = máxima prioridad (requisito duro)
- El diseño incluye un mecanismo real de precedencia manual: propuesta base (Devin puede superarla justificando) — `last_edited_time` + `last_edited_by` (¿humano vs integración?) como señal; toda fila tocada por humano dentro de la ventana (sugerido: desde el último run exitoso) queda inmune a mutación destructiva en el run siguiente, y su `Next_Action` sugerido se marca `Re-check`/revisión en vez de ejecutarse.
- Restricción conocida (radiografía §1.1-F4): hoy el pipeline reescribe `Last_Gate_Run` en TODAS las filas cada run, destruyendo la señal `last_edited_time`. El refactor DEBE dejar de tocar filas sin cambios materiales (writes condicionados a diff real) — es prerrequisito del mecanismo manual-first, no optimización opcional.
- Lo que nunca puede hacer el pipeline sin confirmación interactiva: cambiar `Status` de una fila tocada-por-humano, sobrescribir `Prioridad`/`Next_Action` manuales, archivar postulaciones vivas (`Postulando/Postulado/En proceso/Negociando/Sin respuesta/Contratado`) por causas automáticas (URL/NAD/score) — como máximo, proponer con evidencia y esperar.

### 2.4 Reglas de bifurcación (antídoto a §2 de la radiografía)
- Conjunto cerrado de estados/acciones: valor desconocido → `REVIEW` explícita + log WARN, jamás procesamiento-como-operativo (invierte B11/B13/B15) y jamás excepción silenciosa.
- Cada `if/elif/else` con efecto destructivo lleva: comentario `DECISION:` (qué invariante implementa + qué entrada de Changelog lo motiva), rama `else` explícita (prohibido `else` implícito por omisión en decisiones de archivo), y test de alcanzabilidad de CADA rama (antídoto a B8/B16/código muerto).
- Prohibidos defaults silenciosos con efecto de escritura (B1/B2/B25): default que escribe debe loggearse como decisión (`[DEFAULT] campo=X razón=Y`), y los techos de paginación/MAX deben fallar ruidosamente (exit≠0 + mensaje), no truncar.

## 3. Lectura obligatoria del histórico de errores (antes de diseñar)

Devin debe acreditar lectura (citando ID de entrada + lección aplicada en el diseño) de:
1. La radiografía hermana completa (`handoffs/AUDITORIA_TRACKER_E2E_2026-09-11.md`), §§1–5 + Apéndices.
2. `Documentación/ACTIVE/Changelog Archivo.md` (foco: entradas listadas en §2.2; resto en diagonal para no repetir decisiones revertidas).
3. `Documentación/ACTIVE/Change Log.md` (estado reciente).
4. `Documentación/ACTIVE/Kernel.md` §§05, 07, 09, 11.2, 14 (ownership, schema, gates, triggers, naming).
5. Código: `layer_1_run.py` (F2/F3.5/F3.5.1/F4), `profile_fit.py`, `gate_logic.py`, `feed_processor.py` (`process_record`, `build_notion_properties`), `priority_logic.py`, `dedup_opportunities.py`, `consolidate_duplicates.py`, `batch_operations.py`, `class_b_guard.py`, `Dashboard/scripts/layer_1_run_dash.py` (solo para documentar divergencias a retirar).
6. **Incompleto conocido:** schema vivo de Notion + Changelog/ARCHIVO vivos no estaban accesibles en la auditoría (sin token). Donde la radiografía dice "inferencia" o "pendiente de verificación", Devin NO asume: diseña paramétrico (vocabulario final como config validada contra schema en despliegue) y lista cada supuesto en §7 como pregunta abierta. **No bloquear por ello.**

## 4. Plan de normalización de opciones del Tracker (entregable incluido)

Devin entrega, como parte del plan de despliegue, la tabla de normalización propuesta con mapeo `valor_actual → valor_normalizado` por propiedad, siguiendo:
- **Idioma:** español operativo en VALORES (el corpus de Mau es 100% ES); inglés reservado a terminología técnica ya fijada como NOMBRES de campo/propiedad (`Status/Score/Gate_Decision`), nunca como valores nuevos. `Target` → equivalente ES (propuesta: `Objetivo`; Devin justifica alternativa si la hay — es el valor más visible del operador, cambio sensible). `Follow-up/Interview prep/Re-check` → ES. `CREATE/BLOCKED/APPLIED/REJECTED/REVIEW_NEEDED` (Gate_Decision, técnico, consumido por filtros/automatizaciones): se mantienen EN por ser terminología fijada, documentando la excepción.
- **Casing:** una sola convención por tipo de propiedad (propuesta: Title Case en selects operativos ES; SCREAMING solo en Gate_Decision). `Interview prep` vs `Post-Mortem` vs `Re-check` se unifican.
- **Anti-duplicidad:** ningún string-value vive en dos propiedades con distinta semántica. Casos obligatorios: `Investigar` (sale de Holding — Holding vacío = vacío, el placeholder documentado en `KERNEL:SCHEMA-007` se deroga); `Archivar` ×3 → un solo mecanismo (propuesta: `Next_Action=Archivar` como señal + checkbox `Archivar` como ejecución manual; `Status=Archivar` se elimina del vocabulario); `Expirada` como Next_Action (sin productor — eliminar o dar productor); `REVIEW_NEEDED` en dos propiedades (renombrar uno: propuesta `Gate_Decision=REVIEW` vs `Status=Por revisar`); `fetch_status` vs `Fetch` (fusionar en una sola propiedad con un vocabulario); `Source_Type␣` trailing space (renombrar a `Source_Type` limpio con migración).
- **Poda:** valores fantasma sin productor ni consumidor (`Repetida`, `RAW`, `Nueva`, `Match` como campo, `fetch_status=filled`, `Fuente` legacy) se eliminan del schema con migración explícita fila-por-fila (a dónde va cada fila afectada). `Holding`: sin lectores en el pipeline — Devin decide (con justificación y cita al criterio de la radiografía §5.2.4): eliminarla, convertirla en select curado desde alias_map, o mantenerla como texto libre documentando quién la consume. Lo prohibido: mantenerla como hoy (escritura sin lector + 87.5% ruido).
- Cada rename/eliminación incluye: conteo de filas afectadas (estimable en despliegue por Claude), reversibilidad (export JSON pre-migración obligatorio, §6.3), y actualización del doc normativo correspondiente (Kernel 07.1/07.8, Manual, tidy skill).

## 5. Límites de ejecución (lo que Devin NO hace)

- **Cero escritura a Notion de producción.** Ni lectura con token real (no lo tiene ni lo pide). Todo desarrollo contra fixtures: Devin construye un fixture JSON del Tracker (anonimizable, ≥15 filas que cubran TODAS las ramas: cada Status × cada Gate × casos borde de la radiografía §4) + un Notion fake (stub de `Client`) para tests. Los tests deben correr con `pytest` sin red ni credenciales.
- **Cero `input()` en rutas de pipeline** (precedente: `vl1 batch` read-only-by-default; FEED interactivo se mantiene fuera del run semanal).
- **Cero secretos en repo** (`.env` nunca commiteado; ejemplo en `config/*.example` si añade variables).
- **Cero alteraciones a datos de valor:** el refactor no toca Datos — pero el PLAN debe garantizar (§6.3): vacantes activas preservadas 1:1 ( IDs estables — la migración es update-in-place por `page_id`, jamás delete+create), histórico ARCHIVO intacto (ninguna escritura al ARCHIVO TRACKER salvo las ya existentes y documentadas), y export pre-migración completo en JSON versionado.

## 6. Entregables de la sesión (definición de hecho)

1. **`tracker_flow.py` (o nombre justificado)** — mapa ejecutable único (§2.1) + enums cerrados + `is_mutable` + gate de archivo consolidado. Cobertura de tests ≥90% en este módulo; test de alcanzabilidad por rama destructiva; test de regresión por cada celda ✗/✗ de la tabla §3.1 de la radiografía (cada celda debe tener un test nombrado `test_<status>_<fase>_respeta_…`).
2. **Orquestador refactorizado** (reemplazo de `layer_1_run.py`, mismo punto de entrada/CLI compatible + `--dry-run` real end-to-end + `--apply` explícito para escritura, default dry-run): fases lineales, un solo re-query inicial + writes con diff (no tocar filas sin cambio material), summary idéntico-en-espíritu al actual. `feed_processor.py` adaptado al vocabulario normalizado (o reescrito si es más limpio — decisión de Devin, justificada). `dedup` fusionado en UN mecanismo (ingesta+fuzzy post-hoc unificados, con survivor canónico y guard `is_mutable`); `consolidate_duplicates.py` retirado o reescrito bajo el mismo guard (prohibido trash físico sin confirmación). `batch_operations.py` retirado o convertido a migración versionada de un solo uso (no tool recurrente).
3. **Retiro del fork Dashboard** (`layer_1_run_dash.py`): plan de convergencia RT-1/Dashboard al orquestador único (el Dashboard consume el pipeline, no lo duplica). Si RT-1 necesita endpoints, se definen como API sobre el orquestador, no como pipeline paralelo. `class_b_guard` se generaliza a TODAS las vías (cierra D-002 del todo) o se documenta por qué una vía queda exenta.
4. **Plan de normalización** (§4) como tabla ejecutable + scripts de migración idempotentes (dry-run primero, por propiedad, reanudables, con conteo pre/post).
5. **Plan de implementación/despliegue** (documento): orden de pasos, cada paso con (comando exacto para Claude/MCP o script, validación post-paso, rollback), export pre-migración, ventana de congelamiento de escritura manual durante la migración, y checklist de verificación post-despliegue (incl. re-correr la matriz §3.1 de la radiografía contra el sistema nuevo: todas las celdas deben ser ✓/~/diseño-explícito-documentado).
6. **Docsync**: actualización propuesta (diffs, no escritura directa — la aplica Claude) para Kernel §§07/09, Manual affected, tidy skill, y entrada de Changelog lista para pegar (formato vigente Tipo/Alcance/Contexto/Cambios/IDs/Write-Back/Pendiente).
7. **Preguntas abiertas** (§7): lo no resoluble sin Mau/schema vivo, sin bloquear entregables 1–6.

## 7. Protocolo de ambigüedad (sesión sin Mau presente)

- Devin NO se detiene por dudas: decide con el criterio de este contrato + histórico, implementa, y registra cada decisión dudosa en `PREGUNTAS_ABIERTAS.md` (entregable 7) con formato: `Q-n: pregunta | decisión tomada | alternativas descartadas + por qué | qué dato la cerraría (schema vivo / Mau / …) | impacto si se revierte (alto/medio/bajo)`.
- Prohibido preguntar en tiempo real (Mau no está). Prohibido asumir schema vivo: lo marcado "inferencia" en la radiografía se trata como desconocido-paramétrico.
- Estimación de esfuerzo: una sola sesión. Si algo no cabe, se entrega 1+2+4+5 completos y 3+6 como diseño detallado (no código), declarado en el handoff.

## 8. Handoff de cierre (formato)

Al cerrar, Devin emite handoff serializado compatible con el sistema (`HO-######` si tiene acceso al mecanismo; si no, `DEVIN-YYYYMMDD-NN` + nota) con: qué se entregó (paths), qué quedó abierto (→ §7), conteo de tests (pass/fail), y la frase explícita de conformidad: "Ninguna escritura a Notion de producción fue realizada ni intentada en esta sesión." Sin esta frase, el handoff se considera incompleto.
