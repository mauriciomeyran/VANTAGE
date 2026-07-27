---
name: vantage-tidy-opportunities-tracker
description: Identifica duplicados y vacantes expiradas en el VANTAGE Tracker (Opportunities DB) para archivado, usando los mecanismos de fingerprint y protección de estado terminal ya implementados en el pipeline Python y documentados en el Kernel. Requiere Dry Run y APROBAR_WRITE antes de cualquier escritura.
---

## Convención de anuncio (KERNEL:SKILL-ANNOUNCE-CONVENTION)

- Apertura: `TIDYING OPPORTUNITIES...`
- Cierre: `OPPORTUNITIES TIDIED`

## IDs confirmados

- VANTAGE Tracker (DB): `596938be-fc42-836b-aea7-814a1491bd47`
- VANTAGE Tracker (Col.): `442938be-fc42-828f-b72e-076818d65a5b`

## Mecanismos de dedup — jerarquía real de 3, verificados en `feed_processor.py`

1. **`compute_dedup_hash()`** — primario, condicional por `fetch_status`:
   - `career_page` → `sha256("url:" + URL normalizada)`
   - `aggregator` → `sha256("agg:" + brand|title|location)`
   - `job_id` real (no genérico) → `sha256("job_id:" + job_id)`
   - fallback → `sha256("fallback:" + brand|title|location)`
2. **`dedup_by_content_fingerprint()`** — fallback específico para rotación de `jk` de Indeed (caso de referencia: GILSA, 3 `jk` distintos, mismo puesto). Mismo `brand|title|location`, ventana de 30 días (28+) o 7 días.
3. **`dedup_opportunities.py`** — auditoría batch **separada** del pipeline de ingesta, fuzzy matching (`SequenceMatcher`, umbral empresa 0.85, umbral rol 0.7 sobre keywords fijas). Solo diagnóstico — no escribe ni marca nada por sí sola.

El campo `Dedup_Flag` (select, valor único "Posible duplicado") es el que, en combinación con `Next_Action="Archivar"`, dispara el archivado automático vía `auto_archive.py` — este es `KERNEL:GATE-DECISION-007`, documentado con su origen: bug transversal en Bug Tracker (`39b938befc4281efa1ccdd5d763bfdbf`) donde ambos campos quedaban marcados sin que el paso de ejecución corriera nunca ("páginas zombis").

## Hueco de seguridad confirmado en `auto_archive.py` (Bug Tracker, jul-19, ALTO, abierto)

**`auto_archive.py` NO verifica `Gate_Decision` antes de archivar** — solo evalúa `Next_Action='Archivar'` AND `Dedup_Flag='Posible duplicado'`. Un registro con `Gate_Decision=APPLIED` (aplicación activa) podría archivarse si esos dos campos calzan, sin ninguna protección cruzada. Esto **corrige una afirmación anterior de esta skill**: "PROTECCIÓN TOTAL" (`Next_Action` ya poblado bloquea reevaluación de *gate*) es un mecanismo distinto y no cubre el paso de *archivado físico* — son dos protecciones separadas, y la segunda tiene este hueco real, sin corregir a la fecha.

**Consecuencia operativa para esta skill**: antes de incluir cualquier candidato en el Dry Run, verificar explícitamente `Gate_Decision` del registro. Si es `APPLIED`, excluirlo del batch de archivado y reportarlo aparte como "requiere revisión manual — aplicación activa", incluso si `Next_Action='Archivar'` y `Dedup_Flag='Posible duplicado'` ya calzan. Esta skill no depende de que `auto_archive.py` se corrija — aplica el check ella misma.

## Estado real de los datos (snapshot verificado, no inferido)

Del VANTAGE Tracker vivo (76 registros totales): 36 tienen `Next_Action="Archivar"`, pero solo 2 tienen `Dedup_Flag="Posible duplicado"` — es decir, **34 de 36 registros marcados para archivar nunca serán tocados por `auto_archive.py`** porque no cumplen la condición compuesta completa. Son páginas "zombis" acumuladas, exactamente el patrón transversal documentado en el Bug Tracker. Esta skill debe tratar esos 34 como candidatos legítimos de limpieza manual (vía Dry Run), no asumir que el script los resolverá solo.

También confirmado: **27 registros con `Status=Expirada` tienen `Gate_Decision` vacío** — `Gate_Decision=EXPIRED` existe en el schema pero no se usa en la práctica hoy. No inventar lógica que dependa de ese valor estando poblado; tratar `Status=Expirada` (Class A) como la señal real y suficiente de expiración.

## Segunda vía de `Status=Expirada` — motor de fit de perfil (`profile_fit.py`, confirmado)

`Status=Expirada` no solo se asigna por URL dead — también se asigna por **misfit de perfil**, vía un motor de reglas determinista que corre en `layer_1_run.py` Fase 3.5, aplicable solo a `source_type == "Vacante"` (Inbound/Networking/Referencia quedan exentos):

- **Exclusión por título de rol** (`is_role_excluded()`): ~24 patrones regex (vendedor, sales, planner, store manager, graphic designer, merchandising coordinator sin señal VM, etc.), con excepción explícita para títulos que sí llevan señal VM (`has_vm_title_signal()` — "visual", "merchandis", "brand environment", "retail design", etc.) para no descartar falsos positivos como "Visual Merchandising Coordinator".
- **Hard-block por marca** (`resolve_alias_flags()`, vía `config/alias_map.json`, no leído directamente pero confirmado su propósito).
- **Combinación de scope/score bajo**: `VM_Scope=Bajo` + `Role_Class=Otro`, o `Role_Class=Pivote` + `VM_Scope=Bajo` sin señal VM en el título, o `VM_Scope=Bajo` + `Score<45`.

**Tercera capa de protección, distinta y adicional a PROTECCIÓN TOTAL**: `should_auto_cleanup()` nunca aplica este auto-marcado si `Status` ya está en `_PROTECTED_STATUSES` (`Postulado`, `En proceso`, `Negociando`, `Sin respuesta`, `Contratado`) o `_TERMINAL_STATUSES` (`Expirada`, `Rechazado`, `Archivar`, `Retirado`) — irrelevante de si hay razones de misfit detectadas. Esta skill hereda esa misma protección: si un registro ya tiene uno de esos Status, no se reevalúa por misfit de perfil bajo ningún criterio.

## Limitación real de MCP (ver `vantage-tidy-bug-task-tracker` — misma limitación aplica aquí)

El archivado real (`archived:true`) no está expuesto por MCP. Esta skill, igual que `vantage-tidy-bug-task-tracker`, solo puede completar vía MCP: crear la copia en Archivo Tracker + marcar el original. El paso de Terminal para archivado real usa el mismo patrón de comando que `vantage-tidy-bug-task-tracker`:

```bash
curl -X PATCH "https://api.notion.com/v1/pages/{PAGE_ID}" \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{"archived": true}'
```

Generarlo como parte del reporte final con los `{PAGE_ID}` reales de esta ejecución, no ejecutarlo.

Este patron usa el endpoint estandar de paginas de la API de Notion (archived: true via PATCH) — no ha sido confirmado contra un comando ejecutado end-to-end en esta skill especifica; tratarlo como plantilla de referencia, misma advertencia que aplica en vantage-tidy-bug-task-tracker.

## Expiración — vía Kernel (KERNEL:GATE-DECISION-003, punto 6) — matizado por datos vivos

`Gate_Decision=EXPIRED` (Class B) **≠** `Status=Expirada` (Class A). Son campos distintos, con lógica de asignación distinta, que coexisten sin fusionarse:
- `Status=Expirada` — Class A, puede asignarse manualmente por el operador o por URL_GATE en el primer run.
- `Gate_Decision=EXPIRED` — Class B, asignado por Python **tras ≥2 runs con URL dead**. No es inferencia por antigüedad genérica; es un criterio determinista real ligado a fallos repetidos de accesibilidad de URL.

Un registro puede tener uno sin el otro en un momento dado — no es error, es el diseño documentado.

## Protección de estado terminal — PROTECCIÓN TOTAL (KERNEL:GATE-DECISION-006 + gate_logic.py)

El Kernel documenta el mecanismo real, más amplio de lo que el código por sí solo sugiere: **registros con `Next_Action` ya poblado quedan protegidos ("PROTECCIÓN TOTAL") y no reciben re-evaluación retroactiva** (ej. REJECTED) sin limpieza manual explícita del campo. En código (`gate_logic.py`), los dos valores que quedan permanentemente inmutables una vez seteados son `Next_Action ∈ {"Archivar", "Expirada"}` — ninguna lógica de gate posterior los sobreescribe, sin importar `Gate_Decision` o `Status` entrante.

Esta es la Golden Rule real de esta skill: **antes de tocar cualquier entrada, verificar `Next_Action` primero.** Si ya está poblado (y con mayor razón si es `"Archivar"` o `"Expirada"`), no se re-evalúa, no se recalcula, no se archiva de nuevo — se respeta como decisión ya tomada.

## Resolución de REVIEW_NEEDED (KERNEL:GATE-DECISION-003)

El único valor de `Status` que libera un registro bloqueado para reprocesamiento de campos Class B es exactamente `"Target"`. Flujo: operador corrige el campo problemático (indicado en Notas) → cambia Status→`Target` → corre `~/vantage_pipeline.sh` → `layer_1_run.py` reprocesa Class B (URL_GATE → Score → Gate_Decision → VM_Scope → Role_Class).

## Procedimiento

1. Fetch del VANTAGE Tracker (Col. real).
2. **Para dedup**: aplicar `compute_dedup_hash()`/`dedup_by_content_fingerprint()` sobre entradas nuevas, o correr `dedup_opportunities.py` como auditoría batch si se pide revisión general del tracker completo.
3. **Para expiración**: identificar entradas con `Status=Expirada` (Class A, señal real y suficiente hoy — `Gate_Decision=EXPIRED` está presente en el schema pero sin uso operativo confirmado; no depender de él estando poblado).
4. **Antes de tocar cualquier entrada**: verificar `Next_Action` Y `Gate_Decision`. Si `Next_Action` ya está poblado, es terminal — PROTECCIÓN TOTAL aplica a nivel de reevaluación de gate. Si además `Gate_Decision=APPLIED`, excluir del batch de archivado sin importar qué diga `Next_Action`/`Dedup_Flag` — reportar aparte como "aplicación activa, requiere revisión manual".
5. **Si no hay candidatos** (ningún `Dedup_Flag` activo, ningún `Status=Expirada` sin protección): informar "sin candidatos de archivado en esta corrida" y terminar — no generar Dry Run vacío.
6. Dry Run: tabla con columnas Vacante | Marca | Criterio (Dedup_Flag/Status=Expirada) | Evidencia (hash/fingerprint) | Gate_Decision (columna presente para cuando este campo tenga uso operativo real — hoy aparecera sistematicamente vacia, ver seccion de Expiracion) — misma estructura en cada corrida.
7. Esperar variante válida de `APROBAR_WRITE`.
8. Ejecutar: crear copia en Archivo Tracker (`4ec34e1b-5286-48c9-afbd-d57c6eb76053`) vía `notion-create-pages`, luego `notion-update-page` sobre el original para marcar su Status. El archivado real (fuera de vista activa) requiere Terminal — generar el comando de referencia (ver arriba) en el reporte final si el operador lo quiere completado. **Manejo de fallo parcial:** si la copia en Archivo Tracker se crea pero la actualización de Status en el original falla, el registro queda duplicado (original activo sin marcar + copia en Archivo) — reportarlo explícitamente en el reporte de cierre, no darlo como resuelto; reintentar solo la actualización del Status, sin repetir la creación de la copia. Si la creación de la copia falla, no tocar el original — abortar y reportar sin cambios.
9. Fetch de verificación post-escritura sobre ambas páginas.

## Gaps que siguen abiertos (no resueltos por código ni Kernel, requieren decisión del operador si se activan)

- `cross_tracker_match.py` (cruce Inbound↔Público vía `Marca+Rol`) está **incompleto** — `query_archive_tracker()` es un placeholder sin implementar (consistente con Changelog v9.5.3/v9.5.4). Esta skill no debe asumir que ese cruce funciona hasta que se complete.
- Inconsistencia de schema sin resolver: `Dedup_Flag` aparece en la lista de campos protegidos de `KERNEL:CV-GOLDEN-RULES-002` pero su ownership de escritura exacto frente a `KERNEL:SCHEMA-001` (Class B) debe tratarse como Python-only por default — no escribir `Dedup_Flag` desde el AI Component bajo ninguna circunstancia.
- `auto_archive.py` no comparte lógica con el motor de cruce Marca+Rol — no decide cuál registro es el duplicado, solo ejecuta una decisión ya tomada por Python. Esta skill tampoco debe decidir cuál es el duplicado; solo ejecuta sobre flags ya calculados.

## Reglas de oro

- Nunca sobreescribir `Next_Action` si ya está poblado — PROTECCIÓN TOTAL es la regla rectora de esta skill.
- Nunca archivar sin Dry Run + `APROBAR_WRITE`.
- Nunca asumir expiración por antigüedad — solo actuar sobre `Gate_Decision=EXPIRED` o `Status=Expirada` ya calculados/asignados.
- Nunca escribir `Dedup_Flag`, `Gate_Decision`, `Next_Action`, `Score`, `VM_Scope`, `Role_Class`, `Match`, `Fetch`, `Fuente`, `JD_Quality` desde el AI Component — todos son Class B, Python-only (KERNEL:CV-GOLDEN-RULES-002).
- **No existe mecanismo de reversión en esta skill.** El Dry Run es la única salvaguarda antes de escribir; una vez archivado, restaurar es manual en Notion.

## Cierre de sesión standalone (KERNEL:CENSUS-SYNC, Regla 4)

Toda ejecución que resulte en archivado real (post-`APROBAR_WRITE`) cierra con resumen automático: cuántas entradas se archivaron, por qué criterio (Dedup_Flag / Gate_Decision=EXPIRED / Status=Expirada), y confirmación de que ninguna entrada con `Next_Action` protegido fue tocada. Se presenta sin que el operador lo pida.

---

## Fuentes verificadas (sesión 2026-07-19)

Jerarquía de 3 mecanismos de dedup (`compute_dedup_hash`, `dedup_by_content_fingerprint`, `dedup_opportunities.py`): confirmada por lectura directa de `feed_processor.py` (líneas 201-450) y `dedup_opportunities.py`. Hueco de `Gate_Decision` no verificado en `auto_archive.py`: confirmado por lectura directa del script y por entrada propia del Bug Tracker vivo (fila jul-19, Notion CSV) — hallazgo del mismo día de esta sesión. Estado real de datos (34/36 huérfanos de archivado automático, 27/27 `Expirada` sin `Gate_Decision=EXPIRED`): confirmado por análisis directo del CSV exportado del VANTAGE Tracker (76 filas), no estimado. Motor de misfit de perfil (`is_role_excluded`, `resolve_alias_flags`, `should_auto_cleanup`): confirmado por lectura directa de `profile_fit.py`. PROTECCIÓN TOTAL como "cualquier `Next_Action` poblado": confirmada en código vigente de `layer_1_run.py` (línea 735-738, v8.0) — más amplia que la definición previa basada solo en `gate_logic.py`, que puede ser una versión anterior o script de auditoría aparte. Limitación de MCP para archivado real: misma fuente que `vantage-tidy-bug-task-tracker`.
