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