# RE-AUDITORÍA + PLAN DE TRABAJO SECUENCIAL V3 — VANTAGE

**Fecha:** 2026-08-15
**Fuente auditada:** `origin/main` (auto-sync Notion→disco 2026-08-15 02:45) + PRs #5/#6/#7 vía GitHub. **Nota:** los 8 fundacionales adjuntos no se materializaron en el workspace (`/home/user/uploads/` inexistente) — si difieren del ACTIVE actual, el operador debe declarar el delta en la tarea 1; todo lo demás se auditó contra el árbol real.
**Regla de oro:** DRY RUN + variante válida de `APROBAR_WRITE` antes de toda escritura (Notion o disco). Nada se borra — se mueve o se marca.

---

## PARTE A — Resultados de la re-auditoría (estado de verdad v3)

| # | Ítem | Estado | Evidencia verificada |
| --- | --- | --- | --- |
| R1 | F1 disco: Tier A 6/6, B2 2/2, C C1–C3/C6/B5 | ✅ | `Archive/Legacy_Scripts/` con los 6 movidos + `DEPRECATED_*` renombrados; artefactos fuera del árbol en `origin/main` |
| R2 | Conteo de assets activos | ✅ **80** (no 79) | `verify_versions.py --new-scripts` ejecutado en vivo sobre el árbol actual: **80/80 documentados en Glosario, 0 gaps** |
| R3 | M4 — PATCH §09.7 GATE-DECISION-007 | ✅ | Texto "Consolidación prevista: vantage-housekeeping-archive… status_report.py --archive-queue (aún no implementado)" presente inline (PR #6 MERGED) |
| R4 | M6 — re-anchor SKILL-ANNOUNCE-CONVENTION | ✅ | 0 skills citan el ID viejo; convención anclada en KERNEL:DOCUMENTATION-005 §03.5 (PR #5 MERGED) |
| R5 | M5 — P4a: referencia `vsync_doc_fast.py` en §04.4 | ⚠️ **REVERTIDO** | PR #7 (Devin) la reformuló sobre el archivo LOCAL, pero el sync Notion posterior devolvió el texto viejo: L284 actual dice `(vsync_doc.py / vsync_doc_fast.py)` — referencia colgante activa |
| R6 | M5 — P4b: conteo de skills en §04.4 | ⚠️ **STALE** | Dice "(actualmente 25)"; disco = **30** `.skill` (28 activas + 2 deprecadas por v9.20.8) |
| R7 | P1 — Kernel "máx. 10 correos" | ✅ | Kernel L274 ya dice 10 |
| R8 | P2 — Manual vl3 "5 correos" + hallazgo XREF | ❌ | Manual L717 sigue diciendo "hasta 5 correos"; hallazgo GROQ (#7 de XREF, L1231) sigue listado sin resolver |
| R9 | C5 — dedupe v9.14.2 (x3) en Archivo Changelog | ❌ | "migra de rich_text a select con 8 opciones" aparece **3 veces** — sin consolidar |
| R10 | F3 — fix `graph_layer.py` (leer `../data`) | ✅ con deuda | `_DIR` ahora resuelve a `data/` (fix aplicado); **sin tests** en `Layer_1/tests/` |
| R11 | C4 — stubs `graph_v2/backlinks_v2` en `scripts/` | ⚠️ Retirables | Siguen presentes; ya son basura segura (fix R10 hace que nadie los lea) |
| R12 | Tier D — `facial_analyzer.py` / `index.html` raíz | ⚠️ Parcial | `facial_analyzer.py` eliminado ✅; `index.html` raíz sigue (duplicado de `skills/index.html`) |
| R13 | Deprecadas v9.20.8 en disco | ⚠️ | `vantage-audit-navigation-brief` y `extract-learnings` documentadas como deprecadas pero siguen en `skills/` (`.md`+`.skill`) |
| R14 | `vantage-housekeeping-tracker` — 3 copias | ⚠️ Divergentes | `.md` raíz == zip (md5 c89bb6…) pero `skills/vantage-housekeeping-tracker/SKILL.md` (9106 B) difiere (b2da3649…) — dos verdades; además el zip trae entry de directorio vacío y el dir desempaquetado rompe el patrón SSOT |
| R15 | `vantage-housekeeping-archive` | ⚠️ Falta gobernanza | En disco + `index.json` ✅ (30/30 sync); pero: sin línea de anuncio en §03.5, sin fila en glosario Manual 23.x, y fila SKILL LIBRARY (Notion) sin evidencia de alta |
| R16 | Registry drift V4 (doble ID Changelog Archivo) | ⚠️ Sigue | `CHANGELOG_ARCHIVE` y `CHANGELOG_ARCHIVO` ambos presentes; no reportado aún en Change Log |
| R17 | Script Library Notion (filas Tier A, auto-link `http://`, investigación `git_sync.py`) | ❓ Sin evidencia | Ninguna entrada de Change Log la registra → ejecución no verificada; pendiente de confirmación en vivo por Claude |
| R18 | F3 restante | ❌ | `status_report.py --archive-queue` no existe; sys.path hardcodeado sigue en 4 puntos de Dashboard; `.gitignore` sin `*.bak*` |
| R19 | Briefs raíz (4 archivos nuevos: `brief_*_v921*.md`) | ⚠️ Nuevo | Ruido de sesión en la raíz del repo — sin destino documental |
| R20 | Cierre v9.17.1 (auto_archive.py conservar + avisar issue #4) | ❌ | Pendiente explícito sigue listado en Change Log (L394); no hay entrada `[AUDIT]` de cierre del saneamiento |
| R21 | Gobernanza v9.20.8 (meta-skill tracker, deprecaciones, sync-assets) | ✅ | Documentada en Change Log/Manual/Kernel — el ecosistema evolucionó sano en esta veta |

**Lectura:** el F2 avanzó (M4/M6 completos y limpios; M5 revertido por el ciclo de sync; P1 sí, P2 no), el F1 disco está verificado, y el F3 quedó a medias. Todo lo demás (R8–R20) es el alcance del plan v3.

---

## PARTE B — Tabla maestra secuencial v3 (solo lo pendiente)

| # | Fase | Tarea | Responsable | Script / Skill / Atajo | Salida esperada | Gate | Depende de |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | G0 | Declarar delta de los 8 fundacionales adjuntos vs. ACTIVE (si existe) | Operador | diff / pegar en chat | Delta explícito o "sin delta" | — | — |
| 2 | G1 | **P2**: Manual L717 "hasta 5 correos" → 10 + resolver hallazgo GROQ de XREF (L1231) | Claude (MCP) | `vantage-documentacion-transversal-propuesta` | DRY RUN con anclas exactas | APROBAR_WRITE | 1 |
| 3 | G1 | **P4-redo en Notion** (no solo local): §04.4 (a) reformular el riesgo conocido — `vsync_doc_fast.py` solo como variante deprecada en Archive (ancla: frase autocontenida o KERNEL:EVOLUTION §17 "Linaje Histórico"; **NO** citar "conservación histórica en §09.7", no existe); (b) conteo → "30 en disco (28 activas, 2 deprecadas por v9.20.8)" | Claude (MCP) | idem | DRY RUN | APROBAR_WRITE | 1 |
| 4 | G1 | Alta de anuncio de `vantage-housekeeping-archive` en KERNEL:DOCUMENTATION-005 §03.5 (`ARCHIVING HOUSEKEEPING… / ARCHIVE HOUSEKEPT`) | Claude (MCP) | idem | DRY RUN | APROBAR_WRITE | 1 |
| 5 | G1 | Alta de fila `vantage-housekeeping-archive` en glosario de skills del Manual (23.x) | Claude (MCP) | `vantage-documentacion-transversal-propuesta` | DRY RUN | APROBAR_WRITE | 1 |
| 6 | G1 | **C5**: dedupe 3 bloques v9.14.2 en Archivo Changelog (ID vivo `3ba938be…`) + validar v9.14.3 | Claude (MCP) | `vantage-tidy-changelog` | DRY RUN de consolidación (mover, nunca borrar) | APROBAR_WRITE | 2 |
| 7 | G2 | Skill Library: alta/verificación `vantage-housekeeping-archive`; filas Tier A (6 zombies) → `Deprecado`/`Archivar`; huérfanos `extract_score_distribution.py`/`patch_vsync_doc.py` → deprecar | Claude (MCP) | `vantage-sync-skill-library` + `vantage-sync-script-library` | DRY RUN de filas | APROBAR_WRITE | 3 |
| 8 | G2 | **Investigación fila `git_sync.py`** (huérfano reportado): mismatch de título o corrupción `http://` — **PROHIBIDO deprecar** | Claude (MCP) | fetch de fila + gap report vivo | Dictamen de causa + remedio propuesto | APROBAR_WRITE (remedio) | 7 |
| 9 | G2 | Batch auto-link `http://` (~70 filas Script Library) | Claude (MCP) | operación aparte (DRY RUN propio, lotes) | DRY RUN fila→valor limpio | APROBAR_WRITE | 8 |
| 10 | G2 | Registrar drift V4 (doble ID Changelog Archivo) en entrada de cierre — no corregir sin instrucción | Claude (MCP) | texto de la entrada `[AUDIT]` | Mención explícita en DRY RUN del cierre | APROBAR_WRITE | 7 |
| 11 | G3 | Mover a `Archive/Legacy_Scripts/` las 2 skills deprecadas (`vantage-audit-navigation-brief`, `extract-learnings`) o retirarlas — decisión del operador | Operador | `git mv` o `git rm` | Skills fuera del árbol activo + `index.json` regenerado por `vgit` | APROBAR_WRITE | 1 |
| 12 | G3 | Reconciliar `vantage-housekeeping-tracker`: decidir versión canónica (dir 9106 B vs .md/zip 8562 B), regenerar zip sin entry de directorio, eliminar dir desempaquetado | Operador + Claude | verificación contra fila SKILL LIBRARY | 1 sola copia + zip consistente | APROBAR_WRITE | 7 |
| 13 | G3 | Retirar stubs C4 (`graph_v2.json`, `backlinks_v2.json` de `scripts/`) | Operador | `git rm` | Fuera del árbol | APROBAR_WRITE | 14 |
| 14 | G4 | Tests retro para el fix de `graph_layer.py` (R10) | Devin | PR con tests en `Layer_1/tests/` | Tests PASS | PR review | — |
| 15 | G4 | `status_report.py --archive-queue` + tests | Devin | PR | Tests + salida ejemplo | PR review | — |
| 16 | G4 | Hardening Dashboard: 4 refs de sys.path hardcodeado → `LAYER_1_DIR` | Devin | PR | `smoke_dashboard.py` PASS | PR review | — |
| 17 | G4 | `.gitignore`: cubrir `*.bak2`, `*.bak_*` (ampliar a `*.bak*`) | Devin | PR | PR | PR review | — |
| 18 | G3 | C5 docs duplicadas en `scripts/` (`contrato_migracion_headings.md`, `generate_census.md`, `DEDUP_AUDIT_GUIDE.md`): mover a Archive o eliminar — decisión de solapamiento con §22 | Operador | `git mv`/`git rm` | Fuera del árbol | APROBAR_WRITE | 2 |
| 19 | G3 | Tier D restante: `index.html` raíz (duplicado), `Video/`+`Outputs/` en git (210 MB), `inventario_output/`, `.devin/skills` desincronizado, dirs `archive/` de Dashboard/L4, briefs raíz (R19) | Operador | decisiones + `git mv`/`git rm` | Tabla de decisión resuelta | APROBAR_WRITE por ítem | 1 |
| 20 | G5 | Entrada única `[AUDIT]` en Change Log: cierre de TODO el saneamiento (F1 verificado, M4/M6, P1/P2, P4-redo, C5, R13–R19) + cierre pendiente v9.17.1 + aviso issue #4 + drift V4 | Claude (MCP) | draft → APROBAR_WRITE | Entrada versionada | APROBAR_WRITE | 6,7,10,13,18 |
| 21 | G5 | Gate absoluto: `vversions --sync` con `[VEREDICTO FINAL] PASS` | Operador + Claude | Terminal → pegar output | PASS | — | 20 |
| 22 | G5 | Ledger CLOSED + resumen Regla 4 (CENSUS-SYNC) | Claude (MCP) | `vantage-session-close` | Fila Ledger CLOSED | — | 21 |

**Paralelismo:** G3 (Operador, 11–13, 18–19) y G4 (Devin, 14–17) corren en paralelo con G1/G2 (Claude) — dominios disjuntos. Las reviews Grok/Mistral se aplican a los DRY RUN de las tareas 3 y 6.

---

## PARTE C — Contratos de sesión por agente

### §OP — Operador (Terminal)

```bash
# Tarea 13 (C4 stubs — gateada tras tarea 14)
cd "$HOME/Documents/03 Projects/VANTAGE"
git rm Layer_1/scripts/graph_v2.json Layer_1/scripts/backlinks_v2.json

# Tarea 11 (opción mover) — skills deprecadas por v9.20.8
git mv skills/vantage-audit-navigation-brief.md Archive/Legacy_Scripts/
git mv skills/vantage-audit-navigation-brief.skill Archive/Legacy_Scripts/
git mv skills/extract-learnings.md Archive/Legacy_Scripts/
git mv skills/extract-learnings.skill Archive/Legacy_Scripts/
# luego: vgit  (regenera index.json automáticamente al detectar el cambio en /skills/)

# Tarea 12 (tras dictamen de Claude): eliminar el dir desempaquetado divergente
git rm -r skills/vantage-housekeeping-tracker   # solo si el zip/.md quedó como canónico

# Verificación final de disco
cd Layer_1/scripts && source ../.venv/bin/activate
python3 verify_versions.py --new-scripts   # esperado: 0 gaps con el conteo nuevo
```

Reglas: nunca pegar `NOTION_TOKEN` en chat; `APROBAR_WRITE` es exclusivo tuyo.

### §CL — Claude (MCP Notion)

Misiones en orden: tareas **2 → 3 → 4 → 5 → 6** (G1 documental) y **7 → 8 → 9 → 10** (G2 datos), cierre **20 → 22**. Anclas exactas para los DRY RUN:

| Patch | Ancla ANTES → DESPUÉS |
| --- | --- |
| P2 (Manual) | `Ejecutar manualmente: vl3 (debe procesar hasta 5 correos)` → `…(debe procesar hasta 10 correos)`; hallazgo XREF #7 → marcar RESUELTO (v9.21.x saneamiento) |
| P4a (Kernel §04.4) | `push_local_to_notion() (vsync_doc.py / vsync_doc_fast.py) hace delete-all…` → `push_local_to_notion() (vsync_doc.py) hace delete-all… — la variante vsync_doc_fast.py quedó deprecada en Archive/Legacy_Scripts/ (ver KERNEL:EVOLUTION §17, Linaje Histórico) —` |
| P4b (Kernel §04.4) | `(actualmente 25)` → `(30 en disco: 28 activas, 2 deprecadas por v9.20.8)` |
| 03.5 | añadir línea `- vantage-housekeeping-archive — ARCHIVING HOUSEKEEPING… / ARCHIVE HOUSEKEPT` tras la fila de housekeeping-tracker |

**Escritura en Notion, no solo en disco** (lección R5: el auto-sync revierte PATCHs solo-locales). Write-Back Verification con fetch real. C5 usa ID vivo `3ba938be-fc42-8011-8947-fb4fa5d1f63f`. Golden rules de siempre (sin IDs nuevos → sin CENSUS-R1; Matriz `## NN`/`### NN.N`; Bloque Único).

### §DV — Devin (código, PRs a rama del saneamiento)

D1: tests retro `graph_layer.py` (fixture de `data/`) · D2: `--archive-queue` en `status_report.py` · D3: 4 refs sys.path → `LAYER_1_DIR` · D4: `.gitignore` `*.bak*`. Cada PR: tests + comando de corrida + salida. Prohibido tocar `Documentación/ACTIVE/*` y Notion.

### §G1 — Grok (review del DRY RUN de la tarea 6, dedupe v9.14.2)

Criterios: 3 bloques representados (contenido "Consolidado" íntegro, los otros 2 anotados, no vaciados) · orden cronológico · mover ≠ borrar · ID destino `3ba938be…`. Output: tabla criterio→PASS/FAIL con cita del DRY RUN.

### §M1 — Mistral (review del DRY RUN de la tarea 3, PATCHs Kernel)

Criterios PATCH-QUALITY-001: jerarquía `## NN`/`### NN.N` sin `NN.N.N` · inline sin secciones nuevas · anclas literales ANTES/DESPUÉS · cero IDs nuevos · Bloque Único. Output: misma tabla.

---

## PARTE D — IDs de referencia

| Recurso | ID |
| --- | --- |
| SCRIPT / SKILL LIBRARY | `ea914544-338f-485e-ac1b-7f137a5c9cee` / `2f1938be-fc42-83c8-8972-07300201136d` |
| VANTAGE Tracker DB / Col | `596938be-fc42-836b-aea7-814a1491bd47` / `442938be-fc42-828f-b72e-076818d65a5b` |
| ARCHIVO TRACKER (no tocar) | `674696fd-94b6-464a-ac1f-64b0cc917e15` |
| Change Log / Archivo Changelog vivo | `390938be-fc42-80e7-b429-d7d730339353` / **`3ba938be-fc42-8011-8947-fb4fa5d1f63f`** (drift V4 a reportar) |
| Kernel / Manual / Aliases | `377938be-fc42-805e-a408-c9ae518d4fe7` / `372938be-fc42-8050-9a67-e40857d7806e` / `37c938be-fc42-80d4-b9ae-f5969830331b` |
| Fuente de este plan | `handoffs/HANDOFF_MAESTRO_V3.md` (rama `arena/019ffb49-vantage`) · auditoría base `AUDIT_SANEAMIENTO_ESTRUCTURAL.md` |

## Check de cierre global

- [ ] `--new-scripts` → 0 gaps con el conteo post-G3 · `--scripts`/`--skills` → 0 huérfanos críticos sin remediar
- [ ] `vversions --sync` → `[VEREDICTO FINAL] PASS` · Ledger CLOSED
- [ ] Manual dice 10 correos en TODAS sus secciones (L329 ✓, L717 ✗→✓) · XREF #7 resuelto
- [ ] Kernel §04.4: riesgo conocido sin `vsync_doc_fast` como parte activa · conteo 30 (28+2 deprecadas)
- [ ] Kernel §03.5 lista `vantage-housekeeping-archive` · Manual 23.x tiene su fila
- [ ] Archivo Changelog: 1 solo bloque v9.14.2 consolidado · v9.14.3 validado
- [ ] Skill Library: fila housekeeping-archive · filas Tier A en `Deprecado` · `git_sync.py` investigada y NO deprecada · batch `http://` ejecutado
- [ ] `skills/`: 28 activas + tracker reconciliado (1 copia) + deprecadas fuera del árbol · `index.json` en sync
- [ ] Stubs C4 fuera · C5 docs resueltas · Tier D resuelto por ítem · briefs raíz con destino
- [ ] Change Log: entrada `[AUDIT]` única de cierre con v9.17.1 cerrado y drift V4 reportado · git limpio y pusheado

---

## Bitácora de avance

**2026-08-15 (tarde) — verificación de movimiento del remoto:** `origin/main` sin cambios desde 02:45 (sin PRs ni commits nuevos) → ninguna tarea avanzó desde la re-auditoría. **Tarea 1 RESUELTA:** el operador confirmó que el espejo GitHub de `Documentación/ACTIVE/` es la fuente; delta de adjuntos = **sin delta**.

### Tarjeta de ejecución — Tarea 2 (P2, Manual) — lista para pegar en Claude

```
Misión P2 (HANDOFF_MAESTRO_V3, tarea 2): dos correcciones inline en la página
Manual (372938be-fc42-8050-9a67-e40857d7806e), vía
vantage-documentacion-transversal-propuesta, escribiendo en NOTION (no solo disco).
Presentar DRY RUN con estos dos pares exactos:

PAR 1 — sección de diagnóstico L3:
ANTES: "Ejecutar manualmente: vl3 (debe procesar hasta 5 correos)."
DESPUÉS: "Ejecutar manualmente: vl3 (debe procesar hasta 10 correos)."

PAR 2 — lista de hallazgos de discrepancia al final de 22.6 XREF:
ANTES: "GROQ_MAX_EMAILS_PER_RUN: Manual/Aliases citan valores distintos entre sí; código usa 10."
DESPUÉS: "GROQ_MAX_EMAILS_PER_RUN: RESUELTO (saneamiento 2026-08-15) — Manual/Aliases alineados en 10; código usa 10."

Restricciones: inline · sin secciones nuevas · sin IDs nuevos · sin retitular.
Tras APROBAR_WRITE: write-back verification con fetch real de ambos bloques.
```

---

## Bitácora — 2026-08-15 (tarde 2): revisión SRE del DRY RUN de Claude (T2–T6)

Claude entregó DRY RUNs verificados en vivo contra Notion. Revisión del auditor contra el espejo `origin/main` (Manual L1082/L1231/§23.2 verificados byte-exacto):

**Veredictos:**
- **T2 (P2)**: PASS, con **P2c ADICIONAL (ancla que Claude no detectó)** — la nota de discrepancia en la tabla de env-vars §22.1 (L1082) sigue diciendo "Manual y Aliases citan valores distintos (10 vs 5)" y quedaría falsa tras aplicar P2. Ancla: `⚠️ Nota de discrepancia: Manual y Aliases citan valores distintos (10 vs 5) — el código real usa 10 como default; candidato prioritario para el punto B.` → `⚠️ Nota de discrepancia RESUELTA (saneamiento v9.21.x): Manual y Aliases alineados en 10.` — anexar al mismo DRY RUN de T2.
- **T3 (P4-redo)**: PASS. La aclaración de Claude sobre §09.7 es correcta (la frase "conservación histórica" no existe ahí; se cumple por omisión citando KERNEL:EVOLUTION §17). **P4b — decisión del operador**: Opción A (snapshot estático "30 en disco: 28 activas + 2 deprecadas por v9.20.8") o **Opción B recomendada** (referencia viva: "(conteo en skills/index.json — SSOT)") para eliminar el drift recurrente 12→25→30 de raíz. Si se ejecuta T11 antes, el conteo estático cambia a 28 — con Opción B no hay coordinación.
- **T4**: PASS (ancla de fila `vantage-housekeeping-tracker` verificada en §03.5).
- **T5**: PASS condicional — la tabla §23.2 real es `Skill | Propósito | Trigger | Gate | Anuncio` con fila create-bug-task completa (`Reporte de defecto o tarea pendiente | ✅ | LOGGING TICKET… / TICKET LOGGED`); la inserción operativa va entre `vantage-housekeeping-tracker` y `vantage-create-bug-task` (el texto introductorio de Claude decía "antes de tracker" — ignorar esa frase, vale el diff). Exigir ancla byte-exacta al ejecutar.
- **T6 (C5)**: hallazgo en vivo de Claude **más rico que R9** — el texto "Migración Estructural Next_Action SELECT" está triplicado entre versiones: 2× bajo header v9.14.2 (2º auto-marcado "copia 2") + 1× bajo header v9.14.3 (idéntico verbatim). Los bloques "Auditoría L0" (1 en v9.14.2, 1 en v9.14.3) son eventos legítimos distintos — NO tocar.

**Decisión T6 (recomendación del auditor, requiere confirmación del operador):** EXTENDER alcance — consolidar las 3 copias idénticas. Canonical = **v9.14.2** (evidencia: `MIGRATION_NEXT_ACTION_SELECT_V9.14.2.md` en raíz del repo; KERNEL:SCHEMA-008 §07.8 ancla la migración en v9.14.2). Tratamiento: bloque v9.14.2 Consolidado intacto; la copia 2 de v9.14.2 y la copia v9.14.3 "Migración Estructural" se sustituyen por notas de trazabilidad `[DEDUPE v9.21.x]` apuntando al bloque canónico (mover, nunca borrar) — la nota de la copia v9.14.3 registra además el drift de número de versión como hallazgo para la entrada [AUDIT] de T20.

**Reviews externas:** el dictamen SRE de esta bitácora cubre los criterios asignados a Grok (dedupe) y Mistral (PATCH-QUALITY-001) — verificados ancla por ancla. Omitirlos para velocidad, salvo que el operador los quiera como doble check.

**Siguiente acción del operador:** APROBAR_WRITE por tarea (T2+P2c, T3 con Opción A/B, T4, T5) + decisión de alcance T6. Luego G2 (T7–T10, Claude) y Devin (T14–T17) corren en paralelo.

---

## Bitácora — 2026-08-15 (G1 COMPLETA): asignación de siguientes acciones

**G1 cerrada por Claude con write-back verificado en Notion** (T2 3 sub-parches, T3 con Opción B + reintento tras write silencioso, T4, T5, T6 dedupe extendido 3→1 con canonical v9.14.2 y marcador [AUDIT DRIFT] para T20). **Verificación del espejo GitHub pendiente**: el último auto-sync (03:51) es anterior a las escrituras — confirmar en el próximo sync (no bloqueante; la evidencia primaria es el re-fetch de Notion del protocolo). Hallazgo operativo registrado: patrón de write silencioso en T3 → mantener write-back con re-fetch en toda escritura Notion.

**Asignación siguiente (3 tracks en paralelo):**
- **Claude — G2 (T7→T8→T9):** T7 Skill/Script Library (alta housekeeping-archive, filas Tier A → Deprecado/Archivar, huérfanos extract_score_distribution/patch_vsync_doc), T8 investigación fila git_sync.py (PROHIBIDO deprecar), T9 batch auto-link http://. T10 se absorbe en T20 (la entrada [AUDIT] ya incluye drift V4).
- **Devin — G4 (T14–T17, sin dependencias, arranque inmediato):** T14 tests retro graph_layer.py (fix ya en main, solo faltan tests), T15 status_report.py --archive-queue, T16 sys.path Dashboard → LAYER_1_DIR (4 puntos), T17 .gitignore *.bak*. PRs hacia rama del saneamiento desde origin/main; prohibido Documentación/ACTIVE y Notion.
- **Operador — G3 parcial (T11, T18, T19 listas):** T11 skills deprecadas (mover a Archive/Legacy_Scripts — recomendado, nunca borrar), T18 docs duplicadas C5 (mover a Archive), T19 Tier D por ítem (index.html raíz, Video/Outputs, inventario_output, .devin/skills, dirs archive, briefs raíz). **Bloqueadas:** T12 (tracker 3 copias) espera dictamen de T7; T13 (stubs C4) espera merge de T14.

**Secuencia de cierre restante:** T20 (Claude, deps: 6✅, 7, 13, 18) → T21 (sync PASS, Operador) → T22 (Ledger, Claude).

---

## Bitácora — 2026-08-15: dictamen SRE del DRY RUN G2 (Claude T7–T10)

**Respuestas a las 2 preguntas de Claude (resueltas por el auditor con evidencia de repo, no requieren espera del operador):**

1. **Nombres de los 6 Tier A (7b)** — sí están nombrados en el plan (tarjeta T7 de esta bitácora) y verificados en `origin/main` `Archive/Legacy_Scripts/`: `backfill_next_action_select.py`, `toggle_changelog_archive.py`, `backfill_archive_fingerprint.py`, `patch_vsync_doc.py`, `patch_new_scripts.py`, `extract_score_distribution.py`. **Solapamiento**: 2 de esos 6 ya están cubiertos por 7c con row IDs (`patch_vsync_doc.py` 39f938be…, `extract_score_distribution.py` 3b3938be…) — aplicar una sola vez. Quedan 4 filas por localizar por título exacto: `backfill_next_action_select.py`, `toggle_changelog_archive.py`, `backfill_archive_fingerprint.py`, `patch_new_scripts.py` (template 7b).
2. **Método T9 → Opción (c), herramienta determinista existente**: `Layer_1/scripts/clean_script_library_links.py` (verificado en origin/main; dry-run por default, `--apply` para escribir; detecta ambas variantes: anotación de link y `http://` literal; escribe con tipo correcto title/rich_text). Ejecución: **OPERADOR en Terminal** (dry-run → inspección de candidatos → `--apply`), **Claude verifica** después con re-fetch (filas `vprint.py` y `git_sync.py` dup) + gap report. Gate de seguridad: si el dry-run imprime algún residuo tipo `[x.py](x.py)` (mangle del replace literal), STOP y caer al plan CSV de Claude.

**Correcciones al DRY RUN de Claude:**
- **7a**: `Ruta` debe ser el archivo exacto `skills/vantage-housekeeping-archive.skill` (no `skills/vantage-housekeeping-archive/`). `Capa`: NO inventar "L4" — verificar la fila de un skill hermano (`vantage-tidy-opportunities-tracker` o `vantage-tidy-bug-task-tracker`) y replicar su convención.
- **7b/7c**: aprobados con el desglose de nombres del punto 1.
- **T8**: dictamen aprobado — duplicado creado en M1 (2026-08-13), ya Deprecado/Archivar, fila canónica `git_sync.py (L4)` intacta. La limpieza del dup se cubre en T9. Prohibición respetada.
- **T10**: texto aprobado para incluirse en la entrada `[AUDIT]` de T20.

**Siguiente acción (Operador):**
1) Pegar a Claude: `APROBAR_WRITE T7 (7a con Ruta=skills/vantage-housekeeping-archive.skill y Capa espejo de hermanos; 7b con los 6 nombres confirmados por auditor: backfill_next_action_select.py, toggle_changelog_archive.py, backfill_archive_fingerprint.py, patch_vsync_doc.py, patch_new_scripts.py, extract_score_distribution.py — aplicar 7c una sola vez donde se solapa; 7c aprobado), T8 sin escritura adicional, T10 texto aprobado.`
2) Ejecutar T9 en Terminal:
```bash
cd "$HOME/Documents/03 Projects/VANTAGE/Layer_1/scripts"
source ../.venv/bin/activate
python3 clean_script_library_links.py          # DRY RUN — inspeccionar candidatos
# si la salida es limpia (sin residuos "[x.py](x.py)"):
python3 clean_script_library_links.py --apply  # escribe de verdad
```
3) Claude verifica T9 con re-fetch + gap report; después cierra G2.

---

## Bitácora — 2026-08-15: veredicto sobre los 3 nombres faltantes (T7) + plan T9 extendido

**Veredicto T7 (auditor, con evidencia): los 3 nombres NO existen en Script Library y NO deben crearse.**
Cadena de evidencia: (1) son one-shots nacidos y muertos en una sola sesión — `backfill_next_action_select.py` (dry-run v9.14.2 → 0 huérfanos, nunca ejecutado), `backfill_archive_fingerprint.py` (batch GILSA cerrado v9.13.0), `toggle_changelog_archive.py` (formateo toggle ya aplicado); (2) quedaron en estado intermedio "solo Glosario" (XREF: DOCUMENTADO exige Glosario + Script Library); (3) el gap report del cierre F1 listó solo 3 huérfanos, ninguno de estos nombres → no hay filas Activo con esos títulos; (4) están fuera del árbol activo → el scan ya no los ve → la librería no necesita filas para ellos. Crear filas solo para deprecarlas viola la guía de vantage-sync-script-library. **Los candidatos cercanos NO son alias y NO se tocan**: `assign_next_action.py` (flujo legacy, ya archivado con su trío documental) y `backfill_class_a.py` (**ACTIVO** en Layer_1/scripts, vía layer_1_pipeline.sh backfill — tocarlo habría sido un incidente). Claude hizo bien en parar.

**Registro para T20:** "3 one-shots de Tier A nunca registrados en Script Library (solo Glosario §22.1) — sin fila que deprecar; sin alta por estar fuera del árbol activo".

**Pendiente de confirmación en el próximo write-back de Claude:** el 6º nombre `patch_new_scripts.py` no aparece en su tabla (2 confirmados + 3 faltantes = 5) — confirmar si su fila fue deprecada o tampoco existe.

**T9 — plan en 2 pasadas (el hallazgo colateral de Claude es real y verificado):**
`clean_script_library_links.py` SOLO cubre `Script` y `Ruta` (grep de Descripción = 0 hits). El auto-linker también corrompe texto libre (Descripción) — confirmado por la corrupción en vivo de la descripción de patch_vsync_doc.py durante 7c.
- **Pasada 1 (YA, Operador):** correr el script actual (dry-run → --apply) — limpia Script/Ruta de ~70 filas.
- **Devin D5 (nueva micro-tarea):** extender el script al campo `Descripción` (misma detección dual + limpieza), extrayendo función pura `clean_value()` con test unitario. PR.
- **Pasada 2 (tras merge de D5, Operador):** dry-run → --apply cubre Descripción (incluye la descripción de patch_vsync_doc.py corrompida en 7c).
- **Verificación (Claude):** re-fetch de vprint.py, git_sync.py (dup), patch_vsync_doc.py (Descripción) + gap report limpio. Si el auto-linker re-dispara sobre texto plano en Descripción, escalar como comportamiento de plataforma (no re-escribir en loop).

**T5b (nueva, pequeña):** las entradas del Glosario §22.1/22.1b de los 6 movidos siguen sin anotar (verificado en espejo L983/L1003/L1037) — Claude anota inline "— MOVIDO a Archive/Legacy_Scripts/ (saneamiento v9.21.x)" en las 6 (backfill_next_action_select, toggle_changelog_archive, backfill_archive_fingerprint, extract_score_distribution [22.1b hallazgo], patch_vsync_doc [22.1b], patch_new_scripts [22.1b nota]). Sin headings, sin IDs — puede ir en el mismo batch que T20.

**Espejo GitHub:** sigue sin bajar las escrituras de G1 (último auto-sync 03:51, pre-G1) — evidencia primaria = re-fetch de Notion; el espejo se re-verificará en el próximo sync.
