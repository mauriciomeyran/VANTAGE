# HANDOFF CLAUDE — Lado Notion del saneamiento (post-auditoría arena.ia 2026-08-13)

> **Para:** sesión de Claude Desktop con Notion MCP, en la Mac del operador.
> **Instrucción previa:** abrir sesión con el protocolo `vantage-session-open` (Ledger → Health → Pending → Snapshot → READY). Si el operador aún no pegó los gap reports del Terminal, pídelos antes de arrancar la misión — son tu evidencia de entrada formal.

---

## S1 (IDs)

- **Documento fuente:** `AUDIT_SANEAMIENTO_ESTRUCTURAL.md` (repo root). Toda recomendación cita sus IDs canónicos; no lo contradigas sin evidencia nueva.
- **Ledger:** fila nueva `Status: OPEN` vía `vantage-session-open`.
- **Notion IDs operativos:**
  - SCRIPT LIBRARY (data source): `ea914544-338f-485e-ac1b-7f137a5c9cee`
  - SKILL LIBRARY (data source): `2f1938be-fc42-83c8-8972-07300201136d`
  - VANTAGE Tracker: DB `596938be-fc42-836b-aea7-814a1491bd47` · Col `442938be-fc42-828f-b72e-076818d65a5b`
  - ARCHIVO TRACKER (data source): `674696fd-94b6-464a-ac1f-64b0cc917e15`
  - Change Log (página): `390938be-fc42-80e7-b429-d7d730339353` · Archivo Changelog: `39d938be-fc42-801c-94f6-f11bfe803633`
  - Kernel y demás fundacionales: resolver vía `Layer_1/data/resolver_registry_v2.json` (no hardcodear).
- **Evidencia local ya verificada en sandbox (2026-08-13):** `verify_versions.py --new-scripts` en vivo → **86/86 assets documentados en Glosario, 0 gaps**; `skills/` vs `index.json` → **25/25 en sync**. No re-verifiques estos dos — están cerrados.

## S2 (Pendientes Sesión — la misión, en orden)

### M1 — Consumir el gap report vivo de SCRIPT LIBRARY (input: output del Terminal)

Usa la skill **`vantage-sync-script-library`** al pie de la letra (incluye el prerrequisito: confirmar que `EXCLUDED_DIR_NAMES` en `verify_versions.py` incluye `.venv` y `venv` — ya verificado en la auditoría).

- **Por cada fila `SIN REGISTRAR EN NOTION`:** clasificar según la tabla de la skill. Los 6 zombies Tier A de la auditoría (`backfill_next_action_select.py`, `toggle_changelog_archive.py`, `backfill_archive_fingerprint.py`, `patch_vsync_doc.py`, `patch_new_scripts.py`, `extract_score_distribution.py`) **no se registran** — si el operador ya ejecutó el Tier A del Terminal, estarán fuera del scan (80 assets); su remediación es marcar sus filas existentes.
- **Por cada huérfano `EN NOTION COMO 'Activo' PERO NO EN DISCO`:** aplicar la tabla de clasificación (mismatch de nombre vs. ausencia real). Casos esperados ya documentados: `apply_hyperlinks.py` → proponer `update` de título a `apply_hyperlinks_notion.py` (mismo script renombrado); `auto_archive.py`, `vsync_doc_fast.py`, `vantage-assign.sh` → proponer `Estado=Deprecado`, `Acción=Archivar` (nunca eliminar filas — regla de oro de la skill).
- **Fila de los 6 Tier A:** si siguen en `Estado=Activo`, proponer `Deprecado`/`Archivar` en el mismo batch. Esta es la **remediación documental acoplada** que la auditoría exige (regla de acoplamiento, Directiva 2).
- DRY RUN → `APROBAR_WRITE` → Write-Back Verification (fetch de confirmación, nunca "ya se escribió" de palabra).

### M2 — Corrupción de auto-link `http://` (batch separado, solo con aprobación explícita)

Las ~70 filas con `Script`/`Ruta` corrompidos (`health_http://check.py`) degradan el matching del gap report. La skill `vantage-sync-script-library` declara este batch **fuera de su alcance** — es operación aparte:

- Presentar DRY RUN propio: tabla `Fila | valor actual corrupto | valor limpio propuesto` para las filas afectadas.
- Al escribir: texto plano, verificar que el valor propuesto no contenga `http://` antes de confirmar.
- Es ~70 updates — ofrecer por lotes si el operador prefiere. Sin `APROBAR_WRITE` explícito, no se toca.

### M3 — Consumir el gap report vivo de SKILL LIBRARY

Mismo procedimiento con la skill correspondiente y el output de `--skills`. Contexto local ya verificado: 25 `.skill` en disco, 25/25 en `index.json`. Solo altas de skills realmente nuevos; huérfanos → marcar inactivo, nunca borrar.

### M4 — PATCH documental KERNEL:GATE-DECISION-007 §09.7 (Entregable 1 de la auditoría)

Vía **`vantage-documentacion-transversal-propuesta`** (DRY RUN → `APROBAR_WRITE`). Contenido: añadir *inline* al bloque existente `### 09.7 KERNEL:GATE-DECISION-007` (título "Marcado Manual de Archivado"):

- Referencia a la skill de housekeeping `vantage-housekeeping-archive` (propuesta de la auditoría, Entregable 1) como consolidación del ciclo vigente.
- Referencia al reporte read-only `status_report.py --archive-queue` como desfricción del escaneo visual.

**Restricciones duras (Regla de Cierre de la auditoría):** sin heading nuevo, sin `NN.N.N`, sin ID canónico nuevo, sin retitular el bloque. Matriz Tipográfica Congelada (KERNEL:DOCUMENTATION-001): solo `## NN` / `### NN.N`. Validar con PATCH-QUALITY-001.

### M5 — PATCH KERNEL:ARCHITECTURE-L4 §04.4 (dos correcciones inline)

1. En el "riesgo conocido" de delete-all/create-all, la referencia a `vsync_doc_fast.py` está **colgante** (archivo deprecado en `Archive/Legacy_Scripts/`) — reformular citando solo `vsync_doc.py` (activo) y anotando que la variante fast quedó en Archive.
2. Corregir "(actualmente 12)" → "(actualmente 25)" en el párrafo de Skills Distribution (verificado en disco).

Mismo régimen: inline, sin IDs nuevos.

### M6 — Resolver el ID colgante `KERNEL:SKILL-ANNOUNCE-CONVENTION` (hallazgo nuevo de la auditoría)

Citado por Manual §skills y por las 25 skills, sin bloque de definición en ningún fundacional ni entrada en el registry. **Opción A (recomendada por la auditoría):** reanclar las referencias al nodo existente del Manual que describe la convención — sin alta de ID, sin Census. **Opción B:** alta formal `### NN.N KERNEL:SKILL-ANNOUNCE-CONVENTION` — solo si el operador la elige; dispara CENSUS-SYNC Regla 1 (KERNEL:DOCUMENTATION-008) → requiere `generate_census.py` antes de cerrar.

### M7 — Cierre documental del batch

- Entrada en Change Log tipo `[AUDIT]`: Tier A/B2/C ejecutados (según lo que el operador corrió en Terminal), remediación Script/Skill Library, PATCHs M4–M6, y **cierre del pendiente v9.17.1** ("decidir eliminación o conservación de auto_archive.py" → **CONSERVAR como referencia histórica**, KERNEL:EVOLUTION §17 "Linaje Histórico — Preservado, No Operacional").
- Gate absoluto de cierre (vantage-session-close paso 4): pedir al operador el output local de `verify_versions.py --sync` con `[VEREDICTO FINAL] PASS`.
- Si hubo alta de IDs (solo si M6 fue Opción B): Census regenerado antes del Changelog (KERNEL:DOCUMENTATION-008).

### M8 — OPCIONAL y separado: reparación del esquema del ARCHIVO TRACKER (Fase 3 del Entregable 1)

Solo si el operador decide reactivar el Archivo Tracker como destino. One-shot bajo contrato v9.14.2: backup de esquema, dry-run por default, write-back verification, APROBAR_WRITE por grupo de propiedades (eliminar `Next_Action 1` corrupta, deduplicar `Fetch`/`Fuente`/`VM_Scope`/`Status`, crear `Score_Method`). **No bloquear M1–M7 por esto** — es decisión independiente.

## S3 (Heredados — no resolver en esta sesión, reportar como están)

- GitHub issues #3 y #4 (`gate()` sin Score; terminalidad incompleta/rama REJECTED inalcanzable) — ya mapeados en `ISSUE_PROPOSALS.md`.
- Ticket Bug Tracker "Dedup Caso 5 — Next_Action=Archivar no se ejecuta automáticamente": si sigue Abierto, proponer re-etiquetar/cerrar citando v9.17.1 (pendiente de esa entrada, nunca ejecutado).
- `cross_tracker_match.py` — `query_archive_tracker()` placeholder sin implementar (gap declarado en `vantage-tidy-opportunities-tracker`): sugerencia de ticket Bug Tracker Nivel 2 (KERNEL:GATE-DECISION-009: sugerencia + confirmación, nunca ticket automático sin fuente dura).
- Duplicados v9.14.2 (x3) en Archivo Changelog: disparar **`vantage-tidy-changelog`** (mover, nunca borrar).
- Fix del Hallazgo F2 (`graph_layer.py` debe leer de `Layer_1/data/`, no de los stubs de `scripts/`) — ticket de código con tests; prerequisito para retirar los stubs (Tier C4, gated).

## S4 (Última Acción — estado verificado)

Auditoría 2026-08-13 (commit `e385253`): grafo de dependencias completo; 6 zombies verificados; `auto_archive.py` con decadencia triple (root `.env`, filtro `rich_text` vs campo `select`, destino con esquema corrupto); `--new-scripts` en vivo 86/86; skills 25/25. **Nada escrito en Notion desde la auditoría** — cualquier hallazgo tuyo que contradiga el documento debe declararse como evidencia nueva, no como corrección silenciosa.

## S5 (Contexto/Tier)

- Versión VANTAGE: última entrada del Change Log activo v9.20.2 (verificar al abrir; `vversions --sync` propaga al resto de fundacionales).
- Origen de este handoff: la auditoría corrió en sandbox sin MCP Notion — este handoff es la mitad de escritura que completa el saneamiento.
- Reglas duras: DRY RUN + variante válida de `APROBAR_WRITE` (nunca "Ok"/"Go"/"yes") antes de toda escritura; Write-Back Verification con fetch real; nunca borrar filas ni entradas (mover/marcar); estados de Script Library solo `{Activo, En desarrollo, Deprecado}`; nunca escribir Class B por MCP (guard `class_b_guard.py`, KERNEL:GATE-DECISION-003); Matriz Tipográfica Congelada + Regla de Bloque Único; KERNEL:CENSUS-SYNC Regla 4 (resumen de cierre sin que el operador lo pida).

**ANNOUNCE:** `HANDOFF RECEIVED — VANTAGE SANEAMIENTO NOTION SIDE`
