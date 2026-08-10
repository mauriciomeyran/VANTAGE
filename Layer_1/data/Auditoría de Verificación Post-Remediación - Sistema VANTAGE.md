# Auditoría de Verificación Post-Remediación — Sistema VANTAGE

**Fecha:** 2026-08-10
**Auditor:** Auditor técnico de estados y pipelines (sesión Arena)
**Objeto:** Verificación de las 4 fases de remediación (H1–H4) derivadas de la auditoría inicial de conformidad/drift
**Reporte base:** `Auditoria_Conformidad_Drift_VANTAGE_2026-08-10.md` (en repo; el nombre `Auditoria-de-Conformidad-y-Drift-Sistema-VANTAGE.md` citado en la tarea no existe en el repo — ver §0)

---

## 0. Localización de la remediación y método de verificación

**Hallazgo de localización (crítico para interpretar todo lo demás):**
- La remediación **no está en el checkout de esta sesión**. El branch de sesión `arena/019fea1d-vantage` está en `3d696b9` (2026-08-09, pre-remediación; `git status` limpio).
- La remediación vive en **`main` = commit `d7dc924`** ("auto-sync: 2026-08-10 07:40 (2 archivo(s))", parent `5e721e2a…`). Diff `3d696b9..d7dc924`: **20 archivos, +1334/−195 líneas**.
- Toda la verificación de código/tests/Kernel se hizo **leyendo los objetos git de `d7dc924`** (`git show d7dc924:<path>`), sin checkout ni modificación. Ejecuté la suite de tests extraída de `d7dc924` en `/tmp` (venv aislado).

**Contenido de la remediación (`d7dc924`):**

| Fase | Artefacto | Tipo |
| --- | --- | --- |
| H1 | `Layer_1/scripts/layer_1_run.py` (gate() con Score), `test_gate_logic.py` (+bandas), `Manual.md`, `Checklist.html`, `Change Log.md` v9.18.0, `Layer_1/data/h1_*.md` (4) | Código + tests + docs + reportes |
| H2 | `layer_1_run.py` (Fase 3/3.6 skip terminal + REJECTED desbloqueado), `test_gate_logic.py` (+4 tests), `Change Log.md` v9.19.0, `Layer_1/data/h2_*.md` (2) | Código + tests + docs |
| H3 | `Kernel.md` (09.11 fila 4 corregida), `Change Log.md` v9.17.2, investigación root-cause | Documental |
| H4 | `Kernel.md` (09.7 → "Marcado Manual de Archivado"), `Change Log.md` v9.17.1 | Documental |
| (no audit) | `ISSUE_PROPOSALS.md` (177 líneas, issues H1–H4 listos para GitHub), Kernel 12.2/CV-B lote único (v9.17.0), skills CV-A/CV-B/QA | — |

**Verificación ejecutada (evidencia reproducible):**
- Suite completa extraída de `d7dc924` → `/tmp/venv/bin/python -m pytest tests/` → **86/86 PASS** (test_gate_logic 45, test_dedup 16, test_scoring 25). Coherente con los claims "41/41" (H1) y "45/45" (H2) de los artefactos.
- Simulación del `gate()` remediado sobre las 81 filas del snapshot (`Layer_1/data/tracker_audit_rows.csv`) → ver H1.
- Grep de observabilidad en el diff completo → ver §3.

**Restricciones (declaradas):**
- No se modificó nada (ni código, ni Kernel, ni datos).
- **No existe snapshot post-remediación del Tracker en el repo**: `Layer_1/cache/notion_cache.json` es idéntico en ambos commits (snapshot 2026-06-15, 81 filas). Las afirmaciones "Tracker vivo: 9 filas CREATE→REVIEW_NEEDED / 8 filas CREATE / 0 filas Postulado+CREATE" citan una consulta viva del 2026-08-10 (dataset de **17 filas**) que **no fue persistida** → no verificable desde el repo. Todo lo relativo al estado vivo se marca como "no verificado".

---

## 1. Verificación por hallazgo

### 🔴 H1 — CRÍTICO · `gate()` no usa Score → **RESUELTO (código + tests + docs), con drift residual documental**

**Veredicto: RESUELTO en la capa principal (`layer_1_run.py`); drift residual en Kernel, runner Dashboard y semántica de borde.**

**Evidencia de resolución:**
- Código (`d7dc924:Layer_1/scripts/layer_1_run.py`): `def gate(fetch, vm_scope, role_class, source_type, score=None, ...)` (L457). Nueva lógica (L463–483): exclusiones/alias → Bypass Inbound/Referencia/Networking → `scope_ok` (fetch ∈ {Accesible, Parcial} + VM_Scope=Alto o Pivote+señal VM) como guard duro → **bandas de Score: ≥60 → CREATE, 40–59 → REVIEW_NEEDED, <40 → BLOCKED, Score=None → REVIEW_NEEDED** (golden rule "no pérdida silenciosa").
- Tests (`d7dc924:Layer_1/tests/test_gate_logic.py`): clase `TestGateScoreBand` con 10 tests de bandas (60/75/59/40/39/0/None/scope-fail/fetch-Bloqueado/bypass) + `test_excluded_role_blocked_before_score_check`. **Los ejecuté: 45/45 PASS.**
- Documentación: `Manual.md` (L116–122) ahora lista READY-TO-APPLY (Score≥60, Gate=CREATE), REVIEW_NEEDED (40–59), BLOCKED (<40); `Checklist.html` task #17 actualizado; `Change Log.md` v9.18.0.
- Aplicación viva (no verificable): artefactos `h1_impact_report.md` / `h1_completion_summary.md` reportan dataset vivo de 17 filas → 9 CREATE→REVIEW_NEEDED, 8 CREATE (Score≥60), Ready-to-Apply=8.

**Simulación sobre el snapshot de junio (81 filas, datos pre-remediación):**

| | Actual (snapshot) | Predicción gate() remediado | Delta |
| --- | --- | --- | --- |
| CREATE | 36 | 12 | −24 |
| REVIEW_NEEDED | 0 | 28 | +28 |
| BLOCKED | 38 | 41 | +3* |
| APPLIED | 7 | 7 | 0 (protegidas por gate_logic) |

*Los +3 BLOCKED son artefacto de simulación pura (aplicé `gate()` a filas sin modelar Status); en el pipeline real las filas con Status terminal son protegidas por `gate_logic()` antes de `gate()`. El delta real sobre datos junio: **28 filas CREATE con Score 40–59 pasarían a REVIEW_NEEDED** (todas Vacante; las 2 Inbound con Score<60 quedan CREATE por bypass, correcto). El run vivo solo movió 9 porque el dataset vivo tenía 17 filas con gate — los números son coherentes entre sí.

**Drift residual (documental, ver §2):**
- Kernel 09.11 fila 3 y 09.8 **no fueron actualizados** y ahora contradicen el código (detalle en §2-N1/N2).
- `Dashboard/scripts/layer_1_run_dash.py` **no fue actualizado** → mantiene `gate()` sin Score y "PROTECCIÓN TOTAL" (ver §2-N3).
- Quirk retenido: `JD_Quality="JD Completo"` + `gate()=BLOCKED` → `Next_Action="Optimizar"` (L1031–1040) — ver §2-N5.
- Vocabulario: Kernel 09.2 dice "Para Revisar"; código/schema escriben `REVIEW_NEEDED` — mismatch pre-existente ahora materializado en filas.

---

### 🟠 H2 — ALTO · Terminalidad incompleta; rama REJECTED inalcanzable → **RESUELTO (código + tests), con residuos**

**Veredicto: RESUELTO en `layer_1_run.py`; residuos en APPLIED (sigue inalcanzable), en tests (solo unit) y en runner Dashboard.**

**Evidencia de resolución:**
- Fase 3 (Scoring) `d7dc924:layer_1_run.py:758–765` y Fase 3.6 (Prioridad) `:934–941`: skip de registros terminales vía `gate_logic(entry)` **antes** de recalcular — implementa el invariante de KERNEL:GATE-DECISION-010 ("un registro terminal no puede ser sobreescrito por recálculo de Score/Gate").
- Fase 4 `:1009–1016`: `if protected != "REJECTED": continue` → Status="Rechazado" ya **no** hace continue; `evaluate_rejection_status()` es alcanzable y escribe `Gate_Decision=REJECTED` + `Next_Action=Post-Mortem` (transición APPLIED→REJECTED de 09.11 fila 11 ahora ejecutable). La escritura es idempotente en runs sucesivos.
- Tests: clase `TestTerminalProtectionScoring` (4 tests de `gate_logic()` para Postulado/Rechazado/Archivar/Expirada). **Ejecutados: 45/45 PASS** (suite total 86/86).
- Changelog v9.19.0 documenta el fix.

**Residuos:**
1. **`Status=Postulado → Gate_Decision=APPLIED` sigue siendo inalcanzable en Python.** El fix desbloqueó solo REJECTED; para Postulado, `gate_logic()` retorna "APPLIED" ≠ "REJECTED" → `continue` → `evaluate_application_status()` nunca se ejecuta. El Kernel documenta "Post-aplicación: Status = Postulado → Python marca APPLIED" (KERNEL:CV-PIPELINE-002) y 09.11 fila 10 — **sin implementación** (las 7 filas APPLIED del snapshot junio fueron escritas por otra vía). Esto es pre-existente, pero la remediación lo dejó explícitamente a medias.
2. Los 4 tests de `TestTerminalProtectionScoring` solo prueban `gate_logic()` (helper); **no hay test de integración** que verifique que Fase 3/3.6 efectivamente skip-ean (el claim "4 tests de protección contra recálculo" es optimista).
3. `layer_1_run_dash.py` mantiene PROTECCIÓN TOTAL (no solo terminal) — ver §2-N3.
4. Claim "0 filas Postulado+CREATE residual (no presentes en dataset actual)" no verificable (sin snapshot); en el snapshot junio había 6 filas Postulado+CREATE.

---

### 🟠 H3 — ALTO · Dedup implementado ≠ documentado (`REJECTED_DUPLICATE` vs `Posible duplicado`) → **RESUELTO (documental) + root-cause documentado; fix de código pendiente**

**Veredicto: RESUELTO a nivel contrato (Kernel 09.11 fila 4 corregida); el gap de cobertura de dedup sigue abierto (ticket).**

**Evidencia de resolución:**
- `Kernel.md` (d7dc924) 09.11 fila 4 corregida: `REJECTED_DUPLICATE / Dedup_Flag=True / Next_Action=Descartar` → **"Dedup match (hash/URL/brand+title) contra VANTAGE TRACKER activo, ventana 30d → REVIEW_NEEDED | Status=REVIEW_NEEDED en el registro entrante; Dedup_Flag='Posible duplicado' (select) en el registro existente coincidente"** — ahora coincide con `feed_processor.py` (no se tocó código: ya implementaba esto).
- Changelog v9.17.2 documenta la investigación root-cause de los 7 registros "Visual Merchandising Coordinator": **la mayoría resultaron falsos positivos** (empleadores distintos, título genérico coincidente); el único caso real (par YELLO Marketing Group, hash `89a50e5e…`) se debió a que `NotionSchema.load()` (feed_processor.py:319) limita el scope de dedup al **VANTAGE TRACKER activo, sin visibilidad sobre el ARCHIVO TRACKER**. Se abrió Bug Tracker `3b8938be-fc42-8100-aa85-cbfe3c3e27f6` (ALTO, dedup no cubre Archivo Tracker).

**Drift residual:**
- **Código sin cambio**: el dedup sigue sin cubrir el Archivo Tracker (pendiente del ticket).
- El snapshot junio muestra además el par `Manager, Retail Development` @ Authentic Brands Group (Inbound Score=70 vs Vacante Score=50) y `Supervisor Visual Merchandising` ×2 que **no se mencionan** en la investigación de v9.17.2 (solo se cubrieron las 7 filas Coordinator + par YELLO). Son datos de junio (pre-remediación), pero la investigación no los declara.

---

### 🟡 H4 — ALTO · GATE-DECISION-007 documenta archivado automático abandonado → **RESUELTO (documental)**

**Veredicto: RESUELTO. Kernel alineado con la decisión operativa vigente.**

**Evidencia de resolución:**
- `Kernel.md` (d7dc924) 09.7 retitulado **"Marcado Manual de Archivado"**: elimina "archivado automático vía auto_archive.py", documenta la decisión del operador (2026-08-01), el mecanismo vigente (skill `vantage-tidy-opportunities-tracker`: marca `Archivar=True` tras DRY RUN + APROBAR_WRITE, sin mover/copiar páginas) y el archivado manual por el operador. Coincide con la skill y con `Archive/Legacy_Scripts/auto_archive.py` (deprecado).
- Changelog v9.17.1 documenta el drift como "puramente documental — no requirió cambio de código".

**Residuo:** el ticket "Dedup Caso 5 — Next_Action=Archivar no se ejecuta automáticamente" en Bug Tracker queda como pendiente manual de re-etiqueta/cierre (declarado en el propio changelog). No verificable en vivo.

---

## 2. Nuevos drifts introducidos (o no cerrados) por la remediación

### N1 — Kernel 09.11 fila 3 contradice el nuevo `gate()` (drift creado por H1)
- `Kernel.md` (d7dc924) 09.11 fila 3 sigue: `[ENTRY] URL muerta OR Score < 60 → BLOCKED | Gate_Decision=BLOCKED`. El `gate()` remediado devuelve **REVIEW_NEEDED para Score 40–59** (y BLOCKED solo para <40 o fallo de scope/fetch). La fila 3 debió reescribirse junto con la fila 4. Consecuencia: dos filas de la misma matriz se contradicen entre sí (fila 2: ≥60→READY; fila 3: <60→BLOCKED) y ninguna describe la banda 40–59.

### N2 — Kernel 09.8 queda obsoleto
- `Kernel.md` 09.8: "gate() (capa técnica, **CREATE/BLOCKED puro**)". El `gate()` remediado retorna tres valores (CREATE/REVIEW_NEEDED/BLOCKED). La descripción de 09.8 y la distinción "técnica vs negocio" ya no reflejan la implementación.

### N3 — `Dashboard/scripts/layer_1_run_dash.py` sin portar (divergencia amplificada)
- No cambió en `d7dc924`. Sigue con: `gate()` **sin parámetro Score** (CREATE/BLOCKED puro), "PROTECCIÓN TOTAL" (`if current_action: continue`, L807) y default `Archivar`. Si el operador corre el pipeline vía Dashboard, **H1 y H2 regresan**: filas con Score<60 pueden quedar CREATE y filas con cualquier Next_Action poblado quedan congeladas. Dos runners, dos semánticas de gate (problema H5 de la auditoría original, ahora con un `gate()` distinto en cada lado).

### N4 — `backfill_next_action_select.py` intacto (H8 sin tocar)
- Sigue con `gate()` legacy sin Score/bypass, `Rechazado→"Ninguna"` y default `"Ninguna"` (contra Post-Mortem/Investigar de v9.14.5) y **sin `gate_logic()`** (viola el "pipeline ordinario y backfill" de 010). Si se re-ejecuta con `--execute` sobre los 4 Next_Action libre-texto del snapshot, los sobreescribe con valores obsoletos.

### N5 — Quirk retenido: `JD_Quality="JD Completo"` + `gate()=BLOCKED` → `Next_Action="Optimizar"`
- `d7dc924:layer_1_run.py:1031–1040`: en la rama JD Completo, el `else` (BLOCKED) asigna `next_action="Optimizar"`. Un registro BLOCKED (Score<40 o scope/fetch fallido) marcado como "Optimizar" (CV-A ready) es contradictorio con SCHEMA-008 y con la vista operativa. Pre-existente, pero la remediación reescribió esta rama sin corregirlo (pudo distinguir BLOCKED → Reparar URL / Investigar).

### N6 — Aplicación viva no verificable + claims internos inconsistentes
- Sin snapshot post-remediación en el repo (cache idéntico 2026-06-15). Los artefactos H1 difieren entre sí: `h1_completion_summary.md` dice "9 filas (Score 40–50)" mientras `h1_impact_report.md` dice "todas con Score=40" (la lista manual incluye 1 fila con Score=50 — la del Oniverse). El claim de "41/41 tests" vs "45/45" es coherente con el archivo final (45 tests), pero el summary dice "9 tests nuevos de Score Band" y la clase trae 10–11.
- **Numeración de issues inconsistente entre artefactos**: H1→Issue #1 (completion summary) pero changelog v9.17.2 menciona "issue #3 (H1)"; H2→Issue #2 y H3→Issue #2 (colisión). Los links de GitHub no son verificables desde la sandbox.

### N7 — Kernel no documenta la golden rule `Score=None → REVIEW_NEEDED`
- El código (L479–481) y los tests la implementan; ni 09.2 ni 09.10 ni 09.11 la mencionan. Un evaluador futuro no sabrá por qué una fila sin Score cae en REVIEW_NEEDED.

### N8 — Vocabulario "Para Revisar" vs `REVIEW_NEEDED`
- Kernel 09.2 usa "40–59 Para Revisar"; el código y el schema escriben `REVIEW_NEEDED`. Ahora que el valor se escribe de verdad (antes solo existía como opción de schema), el mismatch Kernel↔datos se vuelve observable en filas reales.

---

## 3. Observabilidad (H9 de la auditoría original) — **NO RESUELTO**

- **Grep del diff completo `3d696b9..d7dc924` por `last_gate|gate_history|audit_log|observab|log_run|last_run|timestamp`: 0 resultados.** La remediación no añadió ningún campo ni log de transiciones al Tracker ni al pipeline.
- Único aporte de observabilidad: el contador `REVIEW_NEEDED (Score 40-59): {review_count}` en stdout de Fase 4 (`layer_1_run.py:1167`) — informativo, no persistido.
- `Score_Method` (escrito por Fase 3 desde antes) **sigue ausente del Kernel** (0 ocurrencias en `d7dc924:Kernel.md`) — el campo se llena solo en filas post-migración y no se puede confirmar su llenado en vivo (sin snapshot).
- Los artefactos `h1_*.md` / `h2_*.md` son **reportes estáticos de la remediación**, no observabilidad en runtime: no se regeneran por el pipeline, no auditan transiciones futuras.
- **No hay campo de timestamp por transición** (Manual L34 lo declara explícitamente); el hueco de trazabilidad de la auditoría original persiste intacto.

**Conclusión H9:** no implementada; nada que verificar "que se esté llenando" más allá de `Score_Method` (pre-existente, sin documentar).

---

## 4. Matriz de conformidad post-remediación

| Área | Pregunta | Evidencia | Veredicto | Severidad residual |
| --- | --- | --- | --- | --- |
| H1 — Guard Score | ¿`gate()` respeta el umbral del Kernel? | `layer_1_run.py:457–483` (bandas ≥60/40–59/<40/None); 10 tests de banda PASS (ejecutados 45/45); Manual/Checklist/changelog v9.18.0 actualizados | ✅ RESUELTO (capa principal) | 🟠 MEDIO (Kernel fila 3/09.8 sin sync; dash runner sin portar) |
| H2 — Terminalidad | ¿Se protegen Score/Prioridad en terminales y se ejecuta REJECTED? | Skip gate_logic() en Fase 3 (L758–765) y 3.6 (L934–941); `protected != "REJECTED"` (L1015); 4 tests PASS; changelog v9.19.0 | ✅ RESUELTO | 🟠 MEDIO (APPLIED inalcanzable; tests solo unit; dash runner) |
| H3 — Dedup | ¿Kernel = implementación? | Kernel 09.11 fila 4 reescrita a REVIEW_NEEDED+'Posible duplicado' (coincide con feed_processor); root-cause YELLO documentado + ticket | ✅ RESUELTO (documental) | 🟠 MEDIO (dedup no cubre Archivo Tracker — ticket abierto) |
| H4 — Archivado | ¿09.7 refleja la decisión vigente? | Kernel 09.7 "Marcado Manual de Archivado", coincide con skill y con auto_archive.py deprecado | ✅ RESUELTO (documental) | 🟡 BAJO (re-etiqueta ticket "Dedup Caso 5" manual) |
| Observabilidad (H9) | ¿Nuevos campos/logs de transición? | 0 adiciones en el diff; solo contador stdout; Score_Method sin documentar | ❌ NO RESUELTO | 🔴 ALTO (trazabilidad de transiciones sigue ausente) |
| Consistencia Kernel↔código | ¿Sin contradicciones nuevas? | N1 (fila 3), N2 (09.8), N7 (None→REVIEW_NEEDED), N8 (vocabulario) | ❌ PARCIAL — 4 puntos de drift documental nuevos | 🟠 MEDIO |
| Paridad de runners | ¿Todos los ejecutables usan la misma gate? | `layer_1_run_dash.py` sin cambio (sin Score, PROTECCIÓN TOTAL) | ❌ NO — divergencia amplificada | 🟠 MEDIO–🔴 ALTO |
| Evidencia de aplicación | ¿La aplicación al Tracker vivo es verificable? | Sin snapshot post-remediación; claims "9+8 filas" sobre consulta viva no persistida | ⚠️ NO VERIFICABLE | 🟡 BAJO (riesgo de auditoría futura) |

---

## 5. Dictamen y siguientes pasos

### Dictamen por eje

- **H1: ✅ Resuelto con deuda documental.** La corrección central es sólida: firma con `score`, guard duro de scope/fetch primero, bandas 40–59→REVIEW_NEEDED, golden rule para Score=None, 45/45 tests (verificados por ejecución), Manual y Checklist sincronizados. La deuda: Kernel 09.11 fila 3 y 09.8 quedaron contradictorios, y el runner Dashboard no se portó — si alguien corre el pipeline desde el Dashboard, el drift H1 reaparece.
- **H2: ✅ Resuelto con residuos.** La protección de Score/Prioridad en terminales es correcta y REJECTED+Post-Mortem ahora es ejecutable. Residuos: la transición hermana `Postulado→APPLIED` (documentada en CV-PIPELINE-002) sigue sin implementación; los tests no cubren la integración de Fase 3/3.6.
- **H3: ✅ Resuelto a nivel contrato; fix de código diferido.** El Kernel ya describe el mecanismo real y la causa raíz (scope sin ARCHIVO TRACKER) está documentada con ticket. Falta el fix de cobertura (depende del ticket).
- **H4: ✅ Resuelto.** Cambio documental limpio y verificado (Kernel 09.7 ↔ skill ↔ archivo deprecado).
- **Observabilidad: ❌ No resuelto.** Ningún campo/log nuevo; la trazabilidad de transiciones sigue siendo el hueco estructural más importante para futuras auditorías.

**Juicio global:** la remediación H1–H4 es **técnicamente correcta, testeada y coherente con sus propios artefactos**; el riesgo principal no está en lo implementado, sino en lo que quedó **fuera de sync**: (a) el Kernel no fue actualizado en dos puntos que ahora contradicen el código, (b) el runner Dashboard y el backfill quedaron con la lógica vieja, (c) la aplicación viva no quedó evidenciada con un snapshot. El sistema funciona, pero quedó en un estado de **doble semántica de gate según qué pipeline corra**.

### Siguientes pasos (5 acciones concretas)

1. **Sync documental del Kernel (H1):** actualizar 09.11 fila 3 (bandas: ≥60 READY · 40–59 REVIEW_NEEDED · <40 BLOCKED; URL muerta → Score=0/BLOCKED) y 09.8 (gate() es trifásico), documentar `Score=None → REVIEW_NEEDED` y el vocabulario `REVIEW_NEEDED` vs "Para Revisar"; luego `vversions --sync` (los propios changelogs declaran este pendiente).
2. **Portar el fix a `Dashboard/scripts/layer_1_run_dash.py`** (mismo `gate()` con score, skip terminal en Fase 3/3.6, default Investigar) **o deprecar el runner** — eliminar la doble semántica (resuelve H5 + el regreso silencioso de H1/H2).
3. **Cerrar el ciclo APPLIED:** decidir e implementar (o documentar como manual) la transición `Status=Postulado → Gate_Decision=APPLIED` de CV-PIPELINE-002/09.11 fila 10; corregir el quirk `JD Completo + BLOCKED → Optimizar` (L1040) para que BLOCKED nunca reciba Optimizar.
4. **Implementar H9 (observabilidad):** campo Class B `Last_Gate_At` (timestamp del último write de Fase 4) o `Gate_History`, log estructurado por run con diff de transiciones, y alta de `Score_Method` en KERNEL:SCHEMA-001/CV-GOLDEN-RULES-002.
5. **Evidenciar el estado del Tracker:** persistir un snapshot post-remediación (CSV/JSON con timestamp, p. ej. `Layer_1/data/tracker_snapshot_2026-08-10.csv`) antes/después del próximo run, para que los claims "9 filas → REVIEW_NEEDED / 0 Postulado+CREATE" sean auditables; re-verificar en vivo los valores libre-texto de Next_Action y los duplicados no cubiertos por v9.17.2.

---

## Anexo A — Evidencia de ejecución (reproducible)

```bash
# Extracción de la remediación desde git (sin tocar el checkout)
git show d7dc924:Layer_1/scripts/layer_1_run.py > /tmp/rem/scripts/layer_1_run.py   # + resto de .py
git show d7dc924:Layer_1/tests/test_gate_logic.py  > /tmp/rem/tests/test_gate_logic.py
git show d7dc924:Layer_1/config/alias_map.json    > /tmp/rem/config/alias_map.json

# Suite completa sobre el código remediado
cd /tmp/rem && /tmp/venv/bin/python -m pytest tests/ -q
# → 86 passed  (test_gate_logic 45 · test_dedup 16 · test_scoring 25)
```

## Anexo B — Puntos no verificados (explícitos)

| Ítem | Estado |
| --- | --- |
| Aplicación viva "9 filas CREATE→REVIEW_NEEDED, 8 CREATE, 0 Postulado+CREATE" (dataset 17 filas, 2026-08-10) | No verificable — no se persistió snapshot; cache del repo es del 2026-06-15 |
| Estado del schema vivo (opciones de Gate_Decision/Next_Action/Prioridad a 2026-08-10) | No verificable sin token; se usó `schema_full.json` (07-11): Gate_Decision ya incluye REVIEW_NEEDED ✓ (opción válida para el write nuevo) |
| Cierre de issues GitHub / Task Tracker (pendientes manuales declarados en los artefactos H1/H2) | No verificable desde la sandbox |
| Conducta del AI Component y escrituras MCP | Sin logs de sesión en el repo |
| Dataset vivo de 17 filas vs 81 del snapshot junio | Diferencia explicable (limpieza/archivado entre 06-15 y 08-10), pero sin fuente intermedia no reconstruible |

---

*Fin del reporte de verificación. Ningún archivo del sistema fue modificado durante esta auditoría; toda la evidencia de la remediación fue leída del commit `d7dc924` (main) mediante objetos git.*