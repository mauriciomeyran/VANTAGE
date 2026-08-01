---
name: vantage-tidy-opportunities-tracker
description: Identifica duplicados y vacantes expiradas en el VANTAGE Tracker (Opportunities DB) y marca Archivar = True en el registro original — sin crear copias ni tocar el Archivo Tracker. Usa los mecanismos de fingerprint y protección de estado terminal ya implementados en el pipeline Python y documentados en el Kernel. Requiere Dry Run y APROBAR_WRITE antes de cualquier escritura.
---

## Convención de anuncio (KERNEL:SKILL-ANNOUNCE-CONVENTION)

- Apertura: `TIDYING OPPORTUNITIES...`
- Cierre: `OPPORTUNITIES TIDIED`

## Alcance de esta skill (léase primero)

Esta skill **solo marca la casilla `Archivar = True`** en el registro original del VANTAGE Tracker. No crea copias, no toca el Archivo Tracker, no mueve ni archiva físicamente ninguna página (`archived: true` a nivel Notion). Es el mismo modelo que `vantage-tidy-bug-task-tracker`: marcar para que el operador localice visualmente qué mandar a su archivo, cuando él decida hacerlo manualmente.

Decisión del operador (2026-08-01): se abandona el enfoque de mover/copiar automáticamente vía `auto_archive.py` o vía creación de páginas en el Archivo Tracker. Motivo: menor fricción, menos tokens, y evita depender de que el esquema del Archivo Tracker esté alineado 1:1 con el Tracker principal (hallazgo de esta misma fecha: el Archivo Tracker tiene propiedades duplicadas/corruptas — `Next_Action 1` con opciones de Bug/Task Tracker en vez de las propias, `Fetch`/`Fuente`/`VM_Scope`/`Status` duplicadas con tipos inconsistentes, y falta `Score_Method` — sin resolver a la fecha). Esta skill ya no depende de ese esquema para nada.

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

El campo `Dedup_Flag` (select, valor único "Posible duplicado") es la señal primaria de duplicado que esta skill usa para proponer candidatos de marcado.

## Estado real de los datos (snapshot verificado 2026-07-19, no inferido)

Del VANTAGE Tracker vivo (76 registros totales en esa fecha): 36 tenían `Next_Action="Archivar"`, pero solo 2 tenían `Dedup_Flag="Posible duplicado"` — 34 de 36 registros marcados para archivar eran páginas "zombis" sin ejecución. Esta skill trata esos 34 (y cualquier equivalente futuro) como candidatos legítimos de marcado manual — no asume que ningún script externo los resolverá.

También confirmado en esa fecha: 27 registros con `Status=Expirada` tenían `Gate_Decision` vacío — `Gate_Decision=EXPIRED` existe en el schema pero no se usa en la práctica. No inventar lógica que dependa de ese valor estando poblado; tratar `Status=Expirada` (Class A) como la señal real y suficiente de expiración.

## Segunda vía de `Status=Expirada` — motor de fit de perfil (`profile_fit.py`, confirmado)

`Status=Expirada` también se asigna por **misfit de perfil**, vía motor de reglas determinista en `layer_1_run.py` Fase 3.5, aplicable solo a `source_type == "Vacante"` (Inbound/Networking/Referencia exentos):

- **Exclusión por título de rol** (`is_role_excluded()`), con excepción para señal VM explícita (`has_vm_title_signal()`).
- **Hard-block por marca** (`resolve_alias_flags()`, vía `config/alias_map.json`).
- **Combinación de scope/score bajo**: `VM_Scope=Bajo` + `Role_Class=Otro`, o `Role_Class=Pivote` + `VM_Scope=Bajo` sin señal VM en el título, o `VM_Scope=Bajo` + `Score<45`.

`should_auto_cleanup()` nunca aplica este auto-marcado si `Status` ya está en `_PROTECTED_STATUSES` (`Postulado`, `En proceso`, `Negociando`, `Sin respuesta`, `Contratado`) o `_TERMINAL_STATUSES` (`Expirada`, `Rechazado`, `Archivar`, `Retirado`). Esta skill hereda la misma protección.

## Protección de estado terminal — PROTECCIÓN TOTAL (KERNEL:GATE-DECISION-006 + gate_logic.py)

Registros con `Next_Action` ya poblado quedan protegidos y no reciben re-evaluación retroactiva sin limpieza manual explícita del campo. En código (`gate_logic.py`), los valores permanentemente inmutables son `Next_Action ∈ {"Archivar", "Expirada"}`.

Golden Rule de esta skill: **verificar `Next_Action` y `Gate_Decision` antes de proponer cualquier marcado.** Si `Gate_Decision=APPLIED` (aplicación activa), excluir del batch sin importar qué digan `Next_Action`/`Dedup_Flag` — reportar aparte como "aplicación activa, requiere revisión manual". Esto aplica incluso si el registro ya califica por duplicado o expiración.

## Resolución de REVIEW_NEEDED (KERNEL:GATE-DECISION-003)

El único valor de `Status` que libera un registro bloqueado para reprocesamiento de Class B es exactamente `"Target"`. Fuera del alcance de escritura de esta skill — solo referencia.

## Procedimiento

1. Fetch del VANTAGE Tracker (Col. real).
2. **Para dedup**: identificar registros con `Dedup_Flag="Posible duplicado"`, o correr `dedup_opportunities.py` como auditoría batch si se pide revisión general del tracker completo.
3. **Para expiración**: identificar registros con `Status=Expirada` (señal real y suficiente hoy).
4. **Antes de proponer cualquier candidato**: verificar `Gate_Decision`. Si es `APPLIED`, excluir del batch y reportarlo aparte como "aplicación activa, requiere revisión manual" — sin importar `Next_Action`/`Dedup_Flag`/`Status`.
5. **Si un candidato ya tiene `Archivar=True`**: omitirlo del Dry Run (ya está marcado, nada que hacer).
6. **Si no hay candidatos**: informar "sin candidatos de marcado en esta corrida" y terminar — no generar Dry Run vacío.
7. Presentar **Dry Run**: tabla con columnas `Vacante | Marca | Criterio (Dedup_Flag / Status=Expirada) | Evidencia (hash/fingerprint) | Gate_Decision`.
8. Esperar variante válida de `APROBAR_WRITE`.
9. **Ejecutar marcado** — para cada candidato aprobado, `notion-update-page` con payload mínimo:
   ```json
   {"properties": {"Archivar": {"checkbox": true}}}
   ```
10. **Verificación**: fetch de confirmación por cada página para validar que `Archivar == true`.

## Gaps que siguen abiertos (no resueltos por código ni Kernel, fuera del alcance de esta skill)

- `cross_tracker_match.py` (cruce Inbound↔Público vía `Marca+Rol`) sigue **incompleto** — `query_archive_tracker()` es un placeholder sin implementar. Esta skill no asume que ese cruce funciona.
- El archivado físico (mover a Archivo Tracker o `archived:true` en Notion) queda **fuera de alcance de esta skill** por decisión explícita del operador — es responsabilidad manual posterior, apoyada por la casilla `Archivar` como marcador visual.
- Esquema del Archivo Tracker (propiedades duplicadas/corruptas, `Score_Method` faltante) — sigue sin resolver, pero ya no bloquea esta skill porque esta skill no escribe ahí.

## Reglas de oro

- Nunca sobreescribir `Next_Action` — esta skill no lo toca, solo lee.
- Nunca marcar `Archivar=True` sin Dry Run + `APROBAR_WRITE`.
- Nunca marcar un registro con `Gate_Decision=APPLIED` — reportar aparte, sin excepción.
- Nunca asumir expiración por antigüedad — solo actuar sobre `Status=Expirada` ya asignado.
- Nunca escribir `Dedup_Flag`, `Gate_Decision`, `Next_Action`, `Score`, `VM_Scope`, `Role_Class`, `Match`, `Fetch`, `Fuente`, `JD_Quality` — todos son Class B, Python-only (KERNEL:CV-GOLDEN-RULES-002). Esta skill solo escribe `Archivar` (Class A, checkbox).
- **Sin reversión automática**: corrección manual (desmarcar `Archivar` en el original).

## Cierre de sesión (KERNEL:CENSUS-SYNC, Regla 4)

Post-`APROBAR_WRITE`, reportar sin que el operador lo pida:
- Total de registros marcados, por criterio (Dedup_Flag / Status=Expirada).
- Total de registros excluidos por `Gate_Decision=APPLIED` (aplicación activa, requieren revisión manual).
- Confirmación de que ningún registro con `Next_Action` ya poblado fue reevaluado.

---

## Fuentes verificadas (sesión 2026-07-19, vigentes salvo lo indicado en "Alcance de esta skill")

Jerarquía de 3 mecanismos de dedup: confirmada por lectura directa de `feed_processor.py` (líneas 201-450) y `dedup_opportunities.py`. Estado real de datos (34/36 huérfanos de archivado, 27/27 `Expirada` sin `Gate_Decision=EXPIRED`): confirmado por análisis directo del CSV exportado del VANTAGE Tracker (76 filas). Motor de misfit de perfil: confirmado por lectura directa de `profile_fit.py`. PROTECCIÓN TOTAL: confirmada en código vigente de `layer_1_run.py` (línea 735-738, v8.0).

Nota de simplificación (2026-08-01): esta skill ya no depende de `auto_archive.py` ni del esquema del Archivo Tracker — decisión explícita del operador para reducir fricción y costo de tokens, calcando el modelo de `vantage-tidy-bug-task-tracker`.
