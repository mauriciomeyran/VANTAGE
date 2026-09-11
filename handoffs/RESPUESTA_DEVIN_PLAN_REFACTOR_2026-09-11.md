# RESPUESTA A DEVIN — Revisión del plan de refactor (2026-09-11)

**De:** Mau (vía auditoría Arena) · **Para:** Devin · **Ref:** `handoff SESSION-20260910-1` (HO-000041), contrato `handoffs/CONTRATO_DEVIN_REFACTOR_TRACKER_2026-09-11.md`, radiografía `handoffs/AUDITORIA_TRACKER_E2E_2026-09-11.md`

---

## Veredicto

**Dirección aprobada, implementación NO aprobada todavía.** El plan entiende el contrato (fuente única, conjunto cerrado, manual-first, retirar el fork), pero contiene errores de diseño que reproducen —o empeoran— fallas documentadas en la radiografía. Ajustar los 10 bloqueantes (B1–B10), agregar las 5 secciones ausentes (A1–A5) y re-presentar el diff del diseño. Sin código hasta el re-review.

Lo que está bien y se mantiene: enums cerrados con REVIEW-ante-desconocido (invierte B11 correctamente); `archive_gate` atómico incluyendo `Gate_Decision` (cierra enrolled stale-gate §4.5, pendiente chequeo schema R3); escrituras condicionadas a diff como prerrequisito §2.3 (implementación mal, B4); retirar-no-igualar el fork; split `REVIEW` vs `Por revisar`; pensamiento de despliegue con export/rollback; frase de conformidad.

---

## BLOQUEANTES (corregir en diseño, antes de cualquier implementación)

### B1. Vocabularios Status ↔ Next_Action confundidos + enum incompleto (plan §1.1, §3.1)
- Tu `NextAction` tiene 6 valores e inventa `OBJETIVO = "Objetivo"`. `Target` **nunca** fue Next_Action. Faltan 5 de los 10 valores confirmados (`KERNEL:SCHEMA-008`, radiografía §5.1): `Optimizar, Investigar, Post-Mortem, Reparar URL, Verificar JD`. `Investigar` es nada menos que el catch-all default de F4 — omitirlo rompe la matriz.
- Tu tabla §3.1 pone `Follow-up, Interview prep, Re-check` bajo la columna **Status**. Son Next_Action. Toda fila con propiedad errónea invalida su migración.
- **Ajuste:** rebasear ambos vocabularios desde el inventario §5.1 de la radiografía (Status: 13 con evidencia; Next_Action: 10). Re-presentar enum + tabla completos. Cada valor: mantener | renombrar | eliminar, con productor+consumidor o justificación de poda.

### B2. Gates de la matriz INVERTIDOS + matriz decorativa (plan §1.1b)
- `gate=lambda r: not is_mutable(r, Actor.PIPELINE)` autoriza `→Expirada` exactamente cuando el registro está **protegido**. Con ese gate, `Contratado` se archiva y lo operativo se salta. Es el bug más grave del plan.
- Además la matriz no se usa: el sketch del orquestador llama a `should_archive()` (indefinido) + `archive_gate()` directo, bypasseando `evaluate_transition`. Dos rutas paralelas = reproduces el problema de "3 rutas hacia Expirada" con 2.
- **Ajuste:** `gate=lambda r, a: is_mutable(r, a)` (nótese: la matriz debe recibir el actor, hoy lo hardcodea a PIPELINE); UN solo punto de entrada (todo archivo pasa por `evaluate_transition → archive_gate`, o la matriz se elimina). Test de regresión obligatorio: `Contratado + url_failed → PROTECTED`.

### B3. `evaluate_flow` reintroduce listas paralelas (plan §1.1, paso 2)
- Su lista terminal `[CONTRATADO, POSTULADO, RECHAZADO]` ≠ `protected_statuses` de `is_mutable` (6 estados). Criterio del contrato §1: más de una columna de protección = diseño mal.
- **Ajuste:** terminalidad desde UNA sola fuente (el enum + un único set `TERMINAL_STATUSES`/`LIVE_APPLICATION_STATUSES` en `tracker_flow.py`). `evaluate_flow` no define listas; solo ordena la evaluación.

### B4. `write_conditional` compara shapes API crudos: siempre difiere, siempre escribe (plan §2.3)
- Un `select` leído es `{"id":…,"type":"select","select":{"id":…,"name":"X","color":…}}` y el de escritura es `{"select":{"name":"X"}}` → `!=` siempre True. Igual para `title`/`rich_text` (annotations, ids, `plain_text` en lectura). Resultado: escribe TODO cada run → `last_edited_time` churn → **destruye la señal manual-first que §2.3 exige** (reproduce F4 actual).
- **Ajuste:** comparar **valores normalizados**, no dicts:
```python
def extract_value(prop):  # acepta shape-lectura Y shape-escritura
    ...
def write_conditional(client, page_id, new_props, current_props):
    diff = {k: v for k, v in new_props.items()
            if extract_value(current_props.get(k)) != extract_value(v)}
    if diff:
        client.pages.update(page_id=page_id, properties=diff)
```
- Test obligatorio: run sin cambios materiales → cero llamadas a `pages.update` (mock cuenta llamadas).

### B5. Diff-conditional ≠ respeto manual (plan §2.2, Fase 4)
- Un `Prioridad` manual difiere del computado → hay diff → se sobrescribe. El diff solo evita churn; la precedencia manual la da `is_mutable`, que tu sketch no consulta en ninguna escritura de Score/Gate/Prioridad.
- **Ajuste:** mostrar el guard en CADA fase: `if is_mutable(...) and diff: write`. Test: fila tocada-por-humano + Prioridad manual ≠ computada → no se escribe + Next_Action sugiere revisión.

### B6. Cómputos actuales sin hogar + staleness intra-run (plan §2.2)
- El sketch cubre Score→Gate→Cleanup→Prioridad. ¿Dónde viven **clasificación** (`VM_Scope`/`Role_Class`), **validación URL + `Fetch`**, **chequeo NAD** y **dedup**? Sin Fetch no hay gate que evaluar; sin clasificación no hay misfit. El contrato §6.2 exige dedup unificado con survivor canónico: ausente.
- "Un solo re-query" sin write-through reproduce §1.2: fases tardías deciden con snapshot viejo.
- **Ajuste:** matriz cómputo↔fase que cubra los 7 cómputos actuales (clasificación, Fetch, Score, Gate/Next_Action, Prioridad, archivo-3-causas, dedup); orden propuesto clasificar → fetch/validar → elegibilidad-archivo → score → gate → prioridad; mirror en memoria actualizado en cada escritura (write-through declarado + testeado).

### B7. Modelo de aprobación contradictorio (plan §1.1b + §2.2)
- Las 3 transiciones declaran `requires_human_approval=True`, pero el sketch archiva directo y el contrato §5 prohíbe `input()` en pipeline. ¿Interactivo o automático? Ambos a la vez no.
- **Ajuste:** modelo explícito recomendado = reglas pre-aprobadas por diseño + auto solo en filas operativas no-tocadas-por-humano + propose-log (fila + evidencia + acción propuesta, sin ejecutar) para filas humanas/postulaciones vivas. `requires_human_approval` debe significar algo ejecutable o eliminarse.

### B8. Decisiones declaradas pero no diseñadas + contradicciones internas
- `Status.ARCHIVAR` "transitorio" (§1.1a) vs "eliminar Status=Archivar" (§3.1). `NextAction.EXPIRADA` en enum vs "eliminar" en tabla. Una decisión por valor.
- "REVIEW-bloqueo-real" declarado en el Changelog-entry pero sin gate en `evaluate_flow`/COMPUTE. Diseñarlo (¿qué cómputos se saltan con `Por revisar`? ¿qué origina la resolución?) o revertir a la opción (b) del contrato §2.2 explícitamente.
- `Last_Gate_Run` en checklist ("solo si hay diff") pero ausente del sketch. Declarar su semántica nueva.

### B9. Despliegue: rename-vía-rewrite rompe vistas + orden peligroso (plan §5.1)
- Reescribir filas `Target→Objetivo` deja la opción vieja huérfana con 0 filas; las vistas/filtros de Notion apuntan a option-ids → filtros rotos silenciosamente. Para renames 1:1 usar **PATCH de schema (mismo option-id, nuevo nombre)**; rewrite por fila solo para merges/splits.
- Orden propuesto (migrar valores paso 4 → desplegar código paso 5) deja código VIEJO corriendo sobre valores nuevos: `Status=Objetivo` es desconocido para el código viejo → lo trata como operativo desprotegido (B11) → archivable por misfit. Cualquier run intermedio destruye trabajo.
- **Ajuste:** (i) nuevo código tolerante-a-ambos-vocabularios primero (alias map viejo→nuevo, solo lectura), (ii) migración, (iii) enforcement + retiro de alias; o ventana atómica con pipeline deshabilitado. Declarar cuál + mecanismo anti-run-intermedio.

### B10. La "matriz" no modela el ciclo de vida (plan §1.1b)
- Tres wildcards `from_status=None →Expirada` + un manual `to_status=None` no es la matriz que pide el contrato §2.1. Falta el lifecycle: ingesta crea (`∅ → Objetivo/Por revisar` por INGESTA), flujo de aplicación (`Objetivo → Postulando → Postulado → En proceso/Negociando/Sin respuesta → Contratado/Rechazado` por HUMANO), archivo (set operativo explícito → Expirada por PIPELINE con causa), y no-transiciones explícitas (terminal × PIPELINE = prohibido).
- **Ajuste:** matriz enumerada origen×evento×actor→destino. `to_status=None` rompe el conjunto cerrado: modelar manual como "cualquier destino dentro del enum" validado por `Status.is_valid`.

---

## ADICIONES REQUERIDAS POR CONTRATO (secciones ausentes del plan)

- **A1. `feed_processor.py`** (§6.2): adaptar o reescribir (decisión justificada). Escribe `Target/REVIEW_NEEDED` → debe escribir vocabulario nuevo + respetar `is_mutable` en existentes.
- **A2. Dedup unificado** (§6.2): UN mecanismo (ingesta + fuzzy post-hoc), survivor canónico definido, guard `is_mutable`. Hoy: cero menciones.
- **A3. Disposición de `consolidate_duplicates.py` y `batch_operations.py`** (§6.2): retirar o reescribir bajo guard. Prohibido dejar `archived=True` físico sin confirmación.
- **A4. `class_b_guard` generalizado** (§6.3): cubrir todas las vías o documentar exención.
- **A5. Fixture + Notion-fake + plan de tests** (§5, §6.1): fixture ≥15 filas cubriendo §4 de la radiografía; tests parametrizados por celda ✗ de la tabla §3.1 (nombrados `test_<status>_<fase>_…`); conteo realista (revisar estimación 30–40 contra celdas ✗ reales).

## RECOMENDADAS (no bloquean, se revisan en el diff)

- **R1.** `last_edited_by == "humano"` no existe en la API (objeto user con id). Mecanismo real: IDs de integración conocidos = bot, resto = humano, desconocido = humano (safe default). Heurística 7-días → state file `state/last_successful_run.json` (hay `state/` en repo). Declarar cómo se resuelven los bot-IDs (¿MCP usa otro token? → pregunta abierta para fase MCP).
- **R2.** `Transition`: `reason_field="Gate_Decision"` → `Notas` (GATE-DECISION-013); `archive_gate` debe devolver shapes API Notion (capa `to_notion_properties`, testeada).
- **R3.** `Gate_Decision=EXPIRADA` escrito + `REVIEW_NEEDED→REVIEW`: requieren opción en schema vivo + auditoría de consumidores (filtros, SYNC, tidy skill, dashboard). Listar como dependencia MCP explícita.
- **R4.** Casing ES sin decidir: `En proceso/Sin respuesta` (sentence) vs Title Case propuesto. Decidir + filas "se mantiene" para TODO valor no tocado; completar tabla por propiedad (Fetch, VM_Scope, Role_Class, Source_Type-valores, Prioridad, layer, Fuente, Score_Method, JD_Quality).
- **R5.** Holding→select: migración de filas `"Investigar"`/vacío → ? (null, no string); crecimiento del select con marcas nuevas (Notion auto-crea options: documentar que "curado" = poblado-vía-alias).
- **R6.** Migraciones: conteos pre/post por propiedad, idempotencia, reanudabilidad; cómo trata el export/restore a páginas `archived=True`.
- **R7.** `Status.is_valid` con side-effect log → mover log al llamador. `--dry-run store_true default True` → único switch `--apply` (dry por default).
- **R8.** Entregar `PREGUNTAS_ABIERTAS.md` en repo (`handoffs/`), no en path local; el "handoff de cierre" overclaimea ("Entregables Completados" — esto es gate de diseño, renombrar a "diseños propuestos").

## Solicitud de re-entrega

Re-presentar: (1) diff del diseño con B1–B10 corregidos, (2) secciones A1–A5, (3) respuestas a R1–R8 (aplicadas o rebutidas con justificación), (4) `PREGUNTAS_ABIERTAS.md` completo inline/en-repo. Mantener la frase de conformidad en cada handoff. Nada de código en Notion ni en `main` hasta el re-review.
