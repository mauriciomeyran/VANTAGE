# RADIOGRAFÍA E2E — Pipeline "VANTAGE Tracker" (Layer 1)

**Fecha:** 2026-09-11 · **Auditor:** agente Arena (auditoría técnica senior, solo lectura de código + mirrors documentales del repo)
**Rama auditada:** `main` @ `467af9c` (sesión `arena/01a08e60-vantage`)
**Alcance:** ingesta → scoring → gate → cleanup → estados terminales del Tracker de vacantes (Notion data source `442938be-fc42-828f-b72e-076818d65a5b`).

## Declaración de acceso (qué se leyó y qué NO)

| Fuente requerida | Estado |
|---|---|
| `Layer_1/scripts/layer_1_run.py` | ✅ leído completo (1336 líneas) |
| `Layer_1/scripts/feed_processor.py` | ✅ leído completo (1422 líneas) |
| `Layer_1/scripts/profile_fit.py` | ✅ leído completo (149 líneas) |
| `Layer_1/scripts/dedup_opportunities.py` | ✅ leído completo (376 líneas) |
| `Layer_1/scripts/generate_census.py` | ✅ leído completo (1038 líneas) |
| `Layer_1/scripts/verify_versions.py` | ✅ leído completo (1001 líneas) |
| `Layer_1/scripts/allocate_vantage_serial.py` | ✅ leído completo (110 líneas) |
| `config/alias_map.json` | ⚠️ **no existe en `config/`** — el real vive en `Layer_1/config/alias_map.json` (✅ leído). `config/` solo contiene `layer_2.env.example` |
| `Figma Sync/registry_seed.json` | ✅ leído (68 nodos) — **fuera de scope del Tracker**: solo mapea tags de CV para Figma Sync, ningún script del pipeline Tracker lo importa |
| Archivos extra leídos (necesarios para el mapa real) | `gate_logic.py` (59 líneas), `priority_logic.py` (176), `backfill_class_a.py` (355), `class_b_guard.py` (137), `consolidate_duplicates.py` (509), `batch_operations.py` (90), `Dashboard/scripts/layer_1_run_dash.py`, `Dashboard/scripts/dashboard_notion.py` (parcial), `Layer_1/config/hard_blocks.json`, `profile_config.yaml`, tests `test_profile_fit.py` / `test_gate_logic.py` / `test_scoring.py` |
| Notion Changelog (`390938be-…`) y ARCHIVO (`077938be…`) en vivo | ❌ **INCOMPLETO — sin acceso Notion en este entorno** (no hay `NOTION_TOKEN`; no existe `.env`). Sustituido por mirrors del repo: `Documentación/ACTIVE/Change Log.md` (164 líneas, últimas ~10 entradas) y `Documentación/ACTIVE/Changelog Archivo.md` (1950 líneas, histórico v9.13→v9.21.x). Todo hallazgo marcado "Changelog" refiere a estos mirrors, no al vivo |
| TRACKER DB schema vivo (`data_source_id 442938be-…`) | ❌ **INCOMPLETO — sin acceso Notion**. Superficie de opciones reconstruida por evidencia convergente: literales en código + `KERNEL:SCHEMA-001/008` + `MANUAL:SCHEMA-FIELD-REF` + skill `vantage-tidy-opportunities-tracker`. Cada valor indica su fuente; lo no confirmado en ≥2 fuentes se marca **inferencia** |

**Convención de citas:** `archivo:línea` (líneas aproximadas ±5 por docstrings largos; cada cita incluye ancla de función/fase para localización exacta).

---

## 1. Mapa de flujo de dependencias E2E

### 1.0 Topología real (no la documentada)

El Kernel describe UN pipeline (`KERNEL:GATE-DECISION-011`, matriz de transición). El repo contiene **cuatro escritores Python independientes sobre el mismo Tracker**, más un quinto manual (skill tidy), sin coordinador común:

| # | Escritor | Trigger | Qué escribe sobre Status | Gate que respeta |
|---|---|---|---|---|
| W1 | `layer_1_run.py` (orquestador "oficial" v8.0/v8.1) | `~/vantage_pipeline.sh` semanal, manual | 3 rutas → `Expirada` (Fase 2, 3.5, 3.5.1) + 1 ruta → `Target` (Fase 2 agregadores, **código muerto** — ver §3.3) | `gate_logic()` parcial + whitelists ad-hoc por fase |
| W2 | `feed_processor.py` (ingesta FEED/FAST) | manual por lote | `Target` (CLEAN) / `REVIEW_NEEDED` (problemático); nunca archiva (BLOCKED = no escribe) | N/A (crea, no muta; mutación de existentes vía `should_mutate_existing_page` → `should_annotate_existing`) |
| W3 | `Dashboard/scripts/layer_1_run_dash.py` (fork v7.6 "Dashboard") | vía Dashboard/RT-1 | `Expirada` (2 rutas propias, con payload **divergente**: incluye `Gate_Decision=BLOCKED`, que W1 no escribe al archivar) | `gate_logic()` importado (H2 backport), resto lógica v7.x |
| W4 | `consolidate_duplicates.py` (sin llamadores en pipeline) | manual, sin wiring | No toca `Status`: **mueve página al ARCHIVO TRACKER (copia con pérdida) + `archived=True` (trash de Notion)** | **ninguno** — ni `gate_logic`, ni `_PROTECTED_STATUSES` |
| W5 | `batch_operations.py` (`vl1 batch --execute`) | manual | flip masivo `Target` → `Exploratorio` | ninguno |

Evidencia W3-fork: `Dashboard/scripts/layer_1_run_dash.py:1-27` (docstring "v7.6 (Dashboard)", pasos 0/0.5/1/2+ distintos de v8.0, aún escribe `Match` y `Fuente` que v8.0 eliminó — `layer_1_run.py:14-22`). Evidencia payload divergente: `layer_1_run_dash.py:593-595` y `:746-748` escriben `{Status:Expirada, Next_Action:Archivar, Gate_Decision:BLOCKED}` vs W1 `layer_1_run.py:783-785,940-941,1006-1007` que escriben `{Status:Expirada, Next_Action:Archivar}` **sin Gate_Decision** (queda stale, ver §4.5). Evidencia W4: `consolidate_duplicates.py:338-368` (`_move_to_archivo`: copia 11 props y trunca — pierde `VM_Scope, Next_Action, Fetch, Prioridad, NAD, Holding, JD_Quality, Dedup_Flag…` — luego `archived=True`); sin callers (`grep` §"consolidate writes": solo menciones en comentarios de `layer_1_run.py:104` y `layer_1_run_dash.py:92`).
**Inferencia sin confirmar:** si W3 sigue ejecutándose en producción (el Kernel lo cita como escritor vigente de `Next_Action` en `KERNEL:SCHEMA-008`), cada run de W1 y W3 se pisan mutuamente sin lock ni `Last_Gate_Run` distinguible (W3 ni siquiera escribe `Last_Gate_Run` — `layer_1_run_dash.py:910-911` escribe solo Gate+Action).

### 1.1 Fase por fase de W1 (`layer_1_run.py:main`)

Orden real de ejecución y dependencias (nota: la numeración salta 1→2→3→3.5→3.5.1→3.6→4→5→6; no existe "Fase 0 NAD" como fase — NAD es Fase 3.5.1; el brief la nombra distinto al código):

**F1 — Clasificación (`layer_1_run.py:~610-690`).**
- Lee: `URL`, `Source_Type␣` (**con trailing space** — nombre real del schema según `class_b_guard.py:37` comment), `Rol`, `VM_Scope`, `Role_Class`, `Marca`.
- Escribe: `Source_Type␣=Vacante` si vacío (**Class A auto-rellenado**, sin chequear edición manual — ver §4.2); `VM_Scope`/`Role_Class` recalculados vía `get_vm_scope`/`get_role_class` (`layer_1_run.py:344-370`: matching por substring sobre el título; título <3 chars → `Bajo`/`Otro`).
- Protección: **NINGUNA**. No consulta `gate_logic()` ni listas de terminales. Recalcula clasificación hasta en `Contratado`/`Rechazado`/`Expirada`. (Divergencia con `KERNEL:GATE-DECISION-010`: "un registro terminal no puede ser sobreescrito por recálculo de Score/Gate" — F1 no toca Score/Gate, pero sí toca Class B derivado en terminales; el invariante no la menciona porque el H2 FIX solo parcheó Fases 3/3.6/4 — Changelog v9.19.0.)
- Si input vacío/malformado: `Rol` vacío → `Bajo`/`Otro` (default silencioso, alimenta F3.5 `no_profile_fit` → **una fila sin título es archivada por misfit** aunque sea `Target` manual).
- Re-query: sí (`items = query_all_items` al inicio).

**F2 — URL Gate + Fetch (`layer_1_run.py:~692-830`).**
- Lee: `URL`, `Source_Type␣`, `Status`, `Fetch`, `JD`, `Marca`, `Rol`, `Notas` (para append).
- Escribe (ruta éxito): `Fetch=Accesible` si no lo era (fix del Bug Tracker `3aa938be…` — antes el éxito nunca escribía y `gate()` bloqueaba por default; `layer_1_run.py:805-827`).
- Escribe (ruta fracaso sitio directo): `{Fetch:Bloqueado, Status:Expirada, Next_Action:Archivar}` + append en `Notas` (`:771-800`). **Ruta 1 de 3 hacia Expirada.**
- Escribe (ruta fracaso agregador): **código muerto** — `{Fetch:Accesible, Status:Target, Next_Action:Reparar URL}` (`:737-770`) es inalcanzable porque `validate_url_pre_ingestion` retorna `True` en TODAS las ramas de agregador (`:262-275`). Ver §3.3. El Kernel (`KERNEL:GATE-DECISION-002`, fix v9.21.40) documenta este comportamiento muerto como vigente.
- Skips: `Source_Type ∈ {Inbound, Referencia, Networking}` (bypass, Gate en F4); filas sin URL; `Status ∈ {Expirada, Rechazado, Archivar, Contratado}` (`:717`); `Status=Target AND len(JD)>100` (guard `KERNEL:GATE-DECISION-010`, `:720-722`).
- **Hueco crítico:** `Postulado, Postulando, En proceso, Negociando, Sin respuesta` **NO se saltan**. Una postulación viva sin JD>100 con URL caída (lo normal post-cierre de vacante) → `Expirada` + `Fetch=Bloqueado`, destruyendo estado de aplicación. Sin retry, sin gracia, sin contador de fallos consecutivos: un solo `HEAD` con timeout 12s decide (`:236-340`). Las filas con JD>100 se salvan por el bypass `JD_ALREADY_EXISTS` (`:250-254`) — la protección real de postulaciones en F2 es **tener JD largo**, no el Status.
- Si input malformado: URL sin esquema → se prependea `https://` (`normalize_url`, `:221-234`); URL con tracking params en URL final → `TRACKING_URL` → archiva (`:290-293` — una URL válida de career page con `utm_` archiva la fila); dominios `jobs.nike.com/workable/greenhouse/lever` → whitelist ciega (`:282-288`).
- Asume corrido antes: F1 (Source_Type poblado; si F1 no corrió, `source_type = … or "Vacante"` — default silencioso `:708`).
- Re-query: sí.

**F3 — Scoring v6.4 (`layer_1_run.py:~832-900`).**
- Lee: `Rol, Marca, JD, Contacto, Score, Source_Type␣, Status, Next_Action`.
- Escribe: `Score` (0-100, `calculate_score_v6` `:372-470`: base 40 + hasta 9 bonos) + `Score_Method ∈ {DETERMINISTIC, BYPASS}`. Bypass (Inbound/Referencia/Networking): conserva score existente o 0 (`:865-873`).
- Protección: `gate_logic(entry)` — solo `Status ∈ {Postulado, Rechazado, Expirada}` o `Next_Action ∈ {Archivar, Expirada}` (`gate_logic.py:16-22`). **Todo lo demás se recalcula**, incl. `Contratado, Postulando, En proceso, Negociando, Sin respuesta, Target`.
- Trampa latente: el `try/except` alrededor de `update_props["Score_Method"]=` (`:880-886`) no puede fallar (asignación a dict); si `Score_Method` no existiera en el schema vivo, el `pages.update` entero falla y **el Score tampoco se escribe** (outer `except` → log + skip). **Inferencia:** en prod la prop existe (el pipeline corre), pero el blindaje es ficticio.
- Si input vacío: scoring no requiere nada — fila vacía → 40 (base). `Score=None` no ocurre post-F3 (siempre escribe número), pero F4/`gate()` sí contempla `None` (H1: `None → REVIEW_NEEDED`, `:505-516`) para filas que F3 skipeó (terminales/protegidas con Score vacío legacy).
- Asume: F2 (el "+40 base" presupone haber pasado URL_GATE, pero F3 no lee `Fetch` — una fila con `Fetch=Bloqueado` no-expirada igual recibe score).
- Re-query: sí. **Último re-query hasta F4** — F3.5/3.5.1/3.6 operan sobre snapshot stale (ver §1.2).

**F3.5 — Limpieza por fit (`layer_1_run.py:~902-960`).**
- Lee: `Rol, Marca, Status, Source_Type␣, VM_Scope, Role_Class, Score` (stale, ver §1.2), `Notas`.
- Escribe: `{Status:Expirada, Next_Action:Archivar}` + append `Notas`. **Ruta 2 de 3 hacia Expirada.**
- Condición: `profile_misfit_reasons(...)` no vacío + `should_auto_cleanup(status, reasons)` (`profile_fit.py:100-131`): reasons = `exclude:<label>` (25 regexes de rol, `:9-33`) | `hard_block_alias` | (`Vacante` + `Bajo`+`Otro` → `no_profile_fit`) | (pivote sin señal VM → `pivot_without_vm`) | (`Bajo` + score<45 → `low_score:N`).
- Protección: `status ∈ _PROTECTED_STATUSES ∪ _TERMINAL_STATUSES` → no cleanup. `_PROTECTED_STATUSES = {Postulado, En proceso, Negociando, Sin respuesta, Contratado, Postulando}` (`profile_fit.py:29-34`) — **sin `Target`**. **BUG CONOCIDO CONFIRMADO** (ver §3.1). `_TERMINAL_STATUSES = {Expirada, Rechazado, Archivar, Retirado}`.
- Divergencia de umbrales: `low_score` corta en **<45**, pero las bandas de `gate()` son <40 BLOCKED / 40-59 REVIEW (`:505-522`). Una fila `Bajo`-scope con score 40-44: F4 la marcaría `REVIEW_NEEDED/Investigar`, pero F3.5 (que corre antes) la archiva. El intervalo 40-44 es REVIEW-solo-en-teoría para `Vacante/Bajo`.
- Asume: F3 (usa `Score` — pero stale del run anterior).

**F3.5.1 — Expiración por NAD (`layer_1_run.py:~962-1030`).**
- Lee: `Status, NAD, Notas, Marca, Rol`.
- Escribe: `{Status:Expirada, Next_Action:Archivar}` + append `Notas`. **Ruta 3 de 3 hacia Expirada.**
- Skip: `Status ∈ {Expirada, Archivar, Postulado, Rechazado}` (`:973`) — **falta `Contratado, Postulando, En proceso, Negociando, Sin respuesta`** (¡una fila `Negociando` con NAD pasado se archiva!) y falta `Retirado`. Es la whitelist más corta de las 7 existentes (ver §3.1 tabla).
- NAD malformado (`ValueError` en parse): `continue` silencioso (`:1028-1030`) — NAD con formato no-`%Y-%m-%d` se ignora sin log. NAD vacío → skip. NAD == hoy → no vence (`< today` estricto). Sin chequeo de edición manual reciente.
- Asume: nada (lee snapshot stale de F3 — ver §1.2 doble-nota).

**F3.6 — Prioridad (`layer_1_run.py:~1032-1095` + `priority_logic.py`).**
- Lee: `Prioridad, Status, Next_Action` (+ page object entero: `JD` para deadlines regex, `Source_Type␣`, `item["created_time"]` raíz, `Score`).
- Escribe: `Prioridad ∈ {1 BAJO, 2 MEDIO, 3 ALTO, 4 CRÍTICO}` (`priority_logic.py:44-79` matriz Urgencia×Importancia; Urgencia: deadline-en-JD o Source_Type∈{Inbound…} → CRÍTICO, si no antigüedad ≤3d ALTO / 4-14d MEDIO / >14d BAJO; Importancia: bucket de Score con `==40 → Base`).
- Protección: `gate_logic()` (igual que F3 — **no** cubre Contratado/Postulando/En proceso/Negociando/Sin respuesta).
- **Sobrescribe Class A sin miramientos:** `Prioridad` es Class A Human-Primary (`KERNEL:SCHEMA-001`, `class_b_guard.py:36-40`) pero F3.6 la pisa cada run si difiere, sin chequear edición manual. Contraste: `backfill_class_a.py` (el otro escritor) solo rellena vacíos (`backfill_class_a.py:collect_backfill_rows`: `needs_prioridad` = select None) — dos escritores, semánticas opuestas sobre el mismo campo.
- Rarezas: `Score==40 → "Base"` pero `score<=60 → "Media"` (`priority_logic.py:34-42`) — 40 cae en Base por el `==` primero (documentado como intencional: 40 = sin bonos); score>100 o negativo → `"Base"` (fallback). `created_time` ausente → Urgencia MEDIO (`sin_fecha_creacion`) — fue el bug v9.20.2 (leía `props` en vez de raíz; fix en `priority_logic.py:143-160`).
- Asume: F3 (Score) — stale por un run.

**F4 — Gate Logic (`layer_1_run.py:~1097-1230`).**
- Lee: `Rol, Marca, Fetch, VM_Scope, Role_Class, Source_Type␣, Status, Gate_Decision, Next_Action, Score, JD_Quality, Notas` (no escribe Notas).
- Escribe: `{Gate_Decision, Next_Action, Last_Gate_Run=now}` **en TODA fila no-skipeada/no-protegida, aunque nada haya cambiado** (`:1196-1225` — `Last_Gate_Run` siempre es nuevo → write amplification + churn de `last_edited_time` en cada run, lo que **invalida `last_edited_time` como señal de "edición manual reciente"** para cualquier refactor futuro).
- Skip: `Status ∈ {Expirada, Archivar}` (`:1117`); luego `gate_logic()` (Postulado/Rechazado/Expirada + Archivar/Expirada actions) con excepción REJECTED-para-transición (`:1129-1137`, H2/KERNEL:GATE-DECISION-006).
- Ramas (orden): `Rechazado → REJECTED/Post-Mortem` (`:1146-1149`, v9.14.5); aplicación (`Postulado/En proceso/Negociando/Sin respuesta → APPLIED` + `Follow-up/Interview prep`, `:524-545`); `JD_Quality=="JD Completo"` → Optimizar/Investigar (`:1154-1167`, H1: REVIEW no optimiza); si no `gate(...)` → CREATE→`Re-check` / REVIEW_NEEDED→`Investigar` / Bloqueado→`Reparar URL` / Parcial→`Verificar JD` / else→`Investigar` (catch-all no destructivo desde v9.14.5, `:1168-1194`).
- **`Contratado` cae al `gate()` genérico** (no está en `evaluate_application_status`, no lo protege `gate_logic`, no lo skipea F4): una fila Contratado puede salir con `Gate_Decision=CREATE + Re-check` o `BLOCKED + Investigar`. Ver §4.4.
- `gate()` (`:483-523`): `is_role_excluded(rol)` o alias hard_block → BLOCKED (ineludible salvo bypass); bypass → CREATE; Vacante: `fetch∈{Accesible,Parcial}` + (`Alto` | pivote-con-señal) si no → BLOCKED; luego bandas por score (H1).
- Asume: F1-F3.6 (lee Fetch/Score/VM_Scope/Role_Class frescos — **re-query sí**, `:1100`).
- Chequeo H9 Postulado-sin-APPLIED (`:1142-1143`): **código muerto** (ver §3.3).

**F5 — Patrones (`:~1232-1258` + `analyze_outcome_patterns :540-600`).** Solo lectura (5º full-scan del run). Buckets `f"Score {score}"` por valor exacto (no por banda — granularidad inútil con N pequeño). Sin escrituras. `timing_patterns` se calcula y se descarta (nunca se imprime/retorna exponible — solo `rejection/score` se usan).

**F6 — Dedup audit (`:~1260-1310` → subprocess `dedup_opportunities.py`).** Escribe `Dedup_Flag=Posible duplicado` (Class B) con su propia lista de terminales (`is_terminal_state`: `Status∈{Postulado,Rechazado}` + actions — **sin Expirada-status, sin En proceso/Negociando/Sin respuesta/Postulando/Contratado/Retirado/Archivar**). Fuzzy: empresa ≥0.85 (SequenceMatcher, tras strip de " group"/" ag") + Jaccard de keywords de rol ≥0.7 sobre el conjunto fijo `{visual, merchandising, coordinator, manager}` — **roles sin ninguna de esas 4 palabras jamás matchean** (`dedup_opportunities.py:are_duplicates`). Marca TODOS los elegibles del grupo (sin survivor canónico). Ventana 60d default, filtro en memoria por `created_time`. Reglas anti-FP: 1 (electrónica). Métricas a `dedup_metrics.json` (repo-root-relative — actually cwd-relative, se escribe donde se invoque).

### 1.2 Dependencias temporales y el snapshot stale F3→F3.6

Re-queries por run: F1→sí, F2→sí, F3→sí, **F3.5→NO, F3.5.1→NO, F3.6→NO**, F4→sí, F5→sí (dentro de `analyze_outcome_patterns`). Consecuencias verificadas en código:

1. **F3.5 usa el Score del run anterior** (F3 acaba de escribir el nuevo pero `items` es el snapshot pre-F3). Convergencia eventual al siguiente run; dentro del run, decisiones `low_score` con dato de hace una semana.
2. **Doble nota de archivo en el mismo run:** F3.5 archiva (Status→Expirada + nota#1); F3.5.1 itera el MISMO snapshot con Status pre-F3.5 → si NAD vencido, vuelve a escribir `{Expirada, Archivar}` + **nota#2 appendida** sobre la nota#1. Ambas escrituras "pegan" porque Notion no valida transiciones. Evidencia: F3.5 `:905-960` y F3.5.1 `:962-1030` comparten `items` sin re-query intermedio; skip de F3.5.1 (`:973`) no puede ver el Expirada recién escrito.
3. **F3.6 recalcula Prioridad de filas recién archivadas** (Status stale pre-F3.5) — write desperdiciado + churn; F4 (fresco) ya las skipea.
4. **F3.6 usa Score stale** para el bucket de Importancia (off-by-one-run).

### 1.3 Ingesta (W2 `feed_processor.py`) — contrato de entrada

`sanitize_input → normalize_envelope (+GAP-01 warn) → coerce_types → per-record process_record → dryrun.md → confirmación interactiva → write_to_notion → archive_dryrun_notion`.
- `process_record` (`:855-990`): orden de gates: hard-block marca (3 marcas veto) → alias hard_block → `is_role_excluded` → alias sin resolver → `dedup_cross_layer` (rechazo histórico + hash + URL + brand+title 30d) → `dedup_by_content_fingerprint` (rotación jk Indeed) → `run_url_gate` → título vacío. Dispositions: BLOCKED (no se escribe — pérdida silenciosa salvo dryrun), REVIEW_NEEDED (se escribe con `Status=REVIEW_NEEDED`), CLEAN (se escribe `Status=Target`).
- `build_notion_properties` (`:1070-1115`): escribe `Rol/Marca/Status/hash/layer/fetch_status/Fuente/location/holding/URL/Source_Type?/Notas`. **Divergencia de nombre:** chequea `"Source_Type" in schema.properties` (sin espacio, `:1099`) mientras W1 lee `"Source_Type "` (con espacio) y `class_b_guard` documenta el trailing space como real — **inferencia:** en el schema vivo la prop tiene espacio ⇒ el chequeo falla ⇒ FEED nunca escribe Source_Type ⇒ F1 lo defaulta a `Vacante`. Consecuencia: `Inbound/Referencia/Networking` solo pueden nacer manuales.
- `Holding`: solo se escribe si el alias lo trae (`:1089-1091`); alias sin resolver → REVIEW_NEEDED con holding vacío. El placeholder `"Investigar"` en Holding **no** lo escribe Python — viene del mapeo documentado del trigger FEED del AI Component (`KERNEL:SCHEMA-007`: `holding → Holding (null → "Investigar")`). El ruido es institucional, no bug de código.
- `Prioridad`: intencionalmente NO escrita al ingresar ("sin default — backfill es responsable", `:1103-1104`; desde F3.6 la escribe W1).
- REVIEW_NEEDED "bloquea Class B": **documentado pero NO implementado en W1.** El contrato GAP-03 (`feed_processor.py:843-862`, `MANUAL:WEEKLY-FLOW-002`, troubleshooting "REVIEW_NEEDED No Se Resuelve") afirma que Python no calcula Class B mientras `Status=REVIEW_NEEDED`. En `layer_1_run.py` **no existe ningún chequeo de `Status==REVIEW_NEEDED`**: F1 la reclasifica, F2 la valida URL (sin URL → skip; con URL mala → Expirada), F3 le calcula Score, F3.5 **puede archivarla** (`should_auto_cleanup("REVIEW_NEEDED",…)` → True si hay reasons — el test `test_profile_fit.py:TestShouldAnnotateExisting` confirma que REVIEW_NEEDED es "anotable"), F4 la re-gatea. La única parte real del "bloqueo" es que FEED la crea sin Class B y nadie la marca como resuelta salvo el operador cambiando a `Target`. Veredicto: **contrato fictional en el lado lector** (hallazgo mayor, ver §4.6).

### 1.4 Variables de entorno y archivos de config (W1+W2)

`NOTION_TOKEN` (requerido, `.env` en `Layer_1/` o raíz — `layer_1_run.py:~600-615`), `NOTION_DB_OPPORTUNITIES`, `NOTION_ARCHIVE_PAGE_ID` (W2, `:60-62`), `ENABLE_DEDUP_AUDIT` (default true), `DEDUP_WINDOW_DAYS` (default 60), `NOTION_ARCHIVE_DATA_SOURCE_ID` (default hardcodeado `674696fd-…` en dedup). Archivos: `Layer_1/config/alias_map.json` (40 alias; consumido con `lru_cache` en `profile_fit._alias_data` y directo en W2), `hard_blocks.json` (solo referencia — **ningún script lo importa**; el veto real está hardcodeado en `feed_processor.py:HARD_BLOCKED_BRANDS` + `hard_block` en alias_map + scoring ignora hard_blocks; drift doc comable), `profile_config.yaml` (**ningún script lo importa** — config huérfana; los keywords viven duplicados en `layer_1_run.get_vm_scope/get_role_class/calculate_score_v6`).

---

## 2. Opciones binarias / bifurcaciones de diseño

Cada bifurcación: condición exacta → ramas → default silenciosa → diseño explícito vs side-effect acumulativo. (Orden de ejecución.)

| # | Sitio | Condición exacta | Rama default silenciosa | Diseño o side-effect |
|---|---|---|---|---|
| B1 | F1 `Source_Type` vacío → `Vacante` | `if not st:` (`:~635`) | **Vacante** (asume tipo más restrictivo) | Side-effect: parches de robustez; el schema permite vacío pero ningún gate lo contempla (`gate()` else-final → BLOCKED) |
| B2 | F1 `Rol` corto/vacío | `len<3` (`:344-370`) | `VM_Scope=Bajo, Role_Class=Otro` → alimenta `no_profile_fit` en F3.5 | Side-effect: default "seguro" que se volvió destructivo al agregarse F3.5 después |
| B3 | F2 bypass `Source_Type ∈ {Inbound, Referencia, Networking}` | (`:712-715`) | Bypass total de URL+Fetch (Fetch queda stale/vacío; `gate()` los aprueba de todos modos) | Diseño explícito (`KERNEL:GATE-DECISION-001`) |
| B4 | F2 skip `Status ∈ {Expirada, Rechazado, Archivar, Contratado}` | (`:717`) | Todo lo demás se re-valida en red cada run | Side-effect: lista crecida por parches (falta En proceso/Negociando/Sin respuesta/Postulando — ver §3.1) |
| B5 | F2 guard `Target + JD>100` | (`:720-722`, KERNEL:GATE-DECISION-010) | Resto de Target sin JD largo → validación viva | Diseño explícito pero estrecho (protege 1 status de 6 manuales) |
| B6 | `validate()`: JD>100 → válido sin red | (`:250-254`) | Sin JD → HEAD/GET real | Diseño explícito (v7.5) |
| B7 | `validate()`: agregador → siempre True | (`:259-275`, FIX v9.21.36) | Agregador jamás archiva (ni siquiera con 404 real) | Parche reactivo que **mató** la rama F2-agregador (B8) — side-effect entre dos fixes del mismo release |
| B8 | F2 `is_agregador_fail` → Target+Reparar URL | (`:737`) | — (inaccesible) | **Código muerto** creado por B7; Kernel lo documenta como vivo (v9.21.40) |
| B9 | F3 `gate_logic() is not None` → skip | (`:846-850`, H2) | Solo 3 statuses + 2 actions protegidos; resto recalcula | Parche H2 (v9.19.0) sobre invariante Kernel; cobertura parcial por diseño del mapa (no del parche) |
| B10 | F3 bypass scoring conserva score/0 | (`:865-873`) | Score 0 para bypass nuevos (banda <40, pero `gate()` los aprueba igual) | Diseño explícito; incoherencia documentada en Kernel (bypass salta threshold) |
| B11 | F3.5 `should_auto_cleanup` | (`profile_fit.py:128-131`) | **Archiva todo status no-listado con reasons** (Target, REVIEW_NEEDED, Exploratorio, vacío, typos, valores futuros) | Side-effect mayor: blacklist-en-vez-de-whitelist; cada status nuevo nace desprotegido |
| B12 | F3.5 reasons `elif` encadenados | (`profile_fit.py:117-123`) | `no_profile_fit` enmascara `low_score` (solo primer match reportado; nota cita `reasons[0]`) | Diseño (nota determinista) con pérdida de información |
| B13 | F3.5.1 skip 4 statuses + NAD parse | (`:973`, `:1028-1030`) | NAD malformado → skip silencioso; status no-listado + NAD pasado → archiva | Side-effect: whitelist más corta del sistema + swallow de `ValueError` |
| B14 | F3.6 `gate_logic()` skip + overwrite Prioridad | (`:1055-1073`) | Prioridad manual pisada si difiere | Side-effect: campo Class A con escritor System sin protocolo de precedencia (contradice `KERNEL:SCHEMA-001` ownership) |
| B15 | F4 skip `{Expirada, Archivar}` + `gate_logic` | (`:1117-1137`) | Resto entra a ramas incl. Contratado/Postulando | Side-effect acumulativo (listas parciales en 3 capas: skip, mapa, `evaluate_*`) |
| B16 | F4 H9 Postulado-sin-APPLIED | (`:1142-1143`) | — (inaccesible, `continue` previo) | **Código muerto** (parche de observabilidad insertado después del guard que lo precede) |
| B17 | F4 `gate()` score None → REVIEW_NEEDED | (`:513-516`, H1) | Dato faltante → revisión, nunca pérdida | Diseño explícito (golden rule v9.18.0) |
| B18 | F4 catch-all → `Investigar` | (`:1192-1194`, v9.14.5) | Nada cae a Archivar por default en F4 | Diseño explícito (rediseño 9Q con operador) — **pero** F3.5/F3.5.1/F2 sí archivan por default; el "no destructivo" solo rige F4 |
| B19 | F4 JD_Quality==Completo → Optimizar | (`:1154-1167`, v9.14.6) | Sin JD_Quality → camino normal | Diseño explícito; `JD_Quality` no lo escribe ningún script del pipeline (**inferencia:** lo escribe CV-A/manual; ningún `pages.update` en Layer_1/Dashboard lo setea — verificado por grep) |
| B20 | W2 `process_record`: orden hard→alias→rol→dedup→url→título | (`:875-990`) | Primera causa gana; BLOCKED = descarte silencioso (solo dryrun.md lo registra) | Diseño con pérdida: BLOCKED no deja rastro en Notion (sin fila, sin log persistente fuera del .md local) |
| B21 | W2 dedup hit → REVIEW_NEEDED (escribe duplicado!) | (`:949-975`) | El duplicado entra como fila nueva REVIEW_NEEDED + flag en existente | Diseño explícito pero contraintuitivo: "dedup" no deduplica, marca |
| B22 | F6 fuzzy thresholds + keyword-set fijo | (`dedup_opportunities.py:are_duplicates`) | Roles sin {visual,merchandising,coordinator,manager} → jamás duplicados | Side-effect: heurística de MVP fosilizada |
| B23 | F6 marca TODO el grupo elegible | (`dedup_opportunities.py:~330-350`) | Sin survivor canónico; el original también queda flaggeado | Diseño (v9.21.0); resuelve vía tidy-manual |
| B24 | `resolve_alias` substring-match | (`feed_processor.py:resolve_alias`, `profile_fit.resolve_alias_flags`) | `alias_key in key or key in alias_key` — match parcial (ej. "armani" matchea "giorgio armani beauty" y viceversa) | Side-effect: puede colisionar (ej. "dior" ⊂ …; "coach" ⊂ "coaching" — **inferencia de riesgo**, no observado) |
| B25 | `query_all_items` dedup defensivo + MAX 250 | (`:90-200`) | Duplicados de paginación descartados con log; >250 filas → **trunca el run** | Parche (auditoría 2026-07-29) con techo silencioso: el Tracker creciendo past 250 deja de procesarse completo sin error |

---

## 3. Parches evidentes sobre errores de diseño

### 3.1 BUG CONOCIDO — VALIDADO ✅ (con ampliación)

**Claim:** `profile_fit.py::_PROTECTED_STATUSES` no incluye `Target`; F3.5 auto-archiva `Target` manuales con misfit; guard `KERNEL:GATE-DECISION-010` solo cubre F2.

**Veredicto: CONFIRMADO línea por línea.**
- `_PROTECTED_STATUSES` = `{Postulado, En proceso, Negociando, Sin respuesta, Contratado, Postulando}` — `profile_fit.py:29-34`. `Target` ausente; `REVIEW_NEEDED`, `Exploratorio`, `""` ausentes por diseño (test lo consagra: `test_profile_fit.py:TestShouldAnnotateExisting::test_operational_statuses_are_annotatable`).
- F3.5: `if not should_auto_cleanup(status, reasons): continue` → else escribe `{Expirada, Archivar}` — `layer_1_run.py:905-960`. `should_auto_cleanup` retorna `bool(reasons)` para cualquier status no listado (`profile_fit.py:128-131`).
- Guard Target+JD solo en F2 (`layer_1_run.py:720-722`); F3.5/F3.5.1 no lo consultan.
- El patrón pedido ("¿cuántas otras fases tienen el mismo hueco?"): **7 listas de protección ad-hoc, todas distintas, ninguna completa.** Tabla de cobertura real (status manuales/operativos como filas):

| Status | F1 clasif | F2 URL | F3 Score | F3.5 misfit | F3.5.1 NAD | F3.6 Prior | F4 Gate | F6 dedup-flag | W4 consol. |
|---|---|---|---|---|---|---|---|---|---|
| Target | ✗ recalc | ~ solo si JD>100 | ✗ recalc | ✗ **archiva** | ✗ archiva | ✗ overwrite | ✗ re-gatea | ✗ flaggea | ✗ trash |
| REVIEW_NEEDED | ✗ | ✗ (puede expirar) | ✗ | ✗ **archiva** | ✗ archiva | ✗ | ✗ | ✗ | ✗ |
| Exploratorio | ✗ | ✗ | ✗ | ✗ archiva | ✗ archiva | ✗ | ✗ | ✗ | ✗ |
| Postulando | ✗ | ✗ puede expirar | ✗ recalc | ✓ (D-003) | ✗ **archiva** | ✗ recalc | ✗ re-gatea | ✗ flaggea | ✗ trash |
| Postulado | ✗ | ✗ puede expirar* | ✓ gate_logic | ✓ | ✓ skip | ✓ gate_logic | ✓ APPLIED† | ✓ skip | ✗ trash |
| En proceso | ✗ | ✗ puede expirar* | ✗ recalc‡ | ✓ | ✗ **archiva** | ✗ recalc‡ | ~ APPLIED (no protegido, re-derivado) | ✗ flaggea | ✗ trash |
| Negociando | ✗ | ✗ puede expirar* | ✗ recalc‡ | ✓ | ✗ **archiva** | ✗ recalc‡ | ~ APPLIED (re-derivado) | ✗ flaggea | ✗ trash |
| Sin respuesta | ✗ | ✗ puede expirar* | ✗ recalc‡ | ✓ | ✗ **archiva** | ✗ recalc‡ | ~ APPLIED (re-derivado) | ✗ flaggea | ✗ trash |
| Contratado | ✗ | ✓ skip | ✗ recalc‡ | ✓ | ✗ **archiva** | ✗ recalc‡ | ✗ **re-gatea (puede →CREATE/BLOCKED)** | ✗ flaggea | ✗ trash |
| Rechazado | ✗ | ✓ skip | ✓ | ✓ terminal | ✓ skip | ✓ | ~ REJECTED (excepción H2) | ✓ skip | ✗ trash |
| Expirada | ✗ | ✓ skip | ✓ | ✓ terminal | ✓ skip | ✓ | ✓ skip | ✗ flaggea! | ✗ trash |
| Retirado | ✗ | ✗ puede expirar | ✗ recalc | ✓ terminal | ✗ archiva | ✗ recalc | ✗ re-gatea | ✗ flaggea | ✗ trash |

\* salvo bypass JD>100 (protección incidental, no por status). † vía `continue` aunque H9 pretenda observar (muerto). ‡ recalc de Score/Prioridad en postulaciones vivas contradice el espíritu de GATE-DECISION-010 pero no su letra (el mapa no los lista).
**Conclusión del patrón:** el hueco no es "una whitelist incompleta" sino **arquitectura de listas paralelas sin fuente única**: `STATUS_TERMINAL_MAP` (3) + skip-F2 (4) + skip-F3.5.1 (4 distintos) + skip-F4 (2) + `_PROTECTED∪_TERMINAL` (10) + `evaluate_application_status` (4) + `is_terminal_state` dedup (2+2) + `consolidate` map (11, otro vocabulario). Cada fix (D-001, D-003, H2) parchó UNA lista. **Ningún fix unificó.**

### 3.2 Tabla de parches reactivos (firmas `FIX/H/KERNEL/D/GAP` en código + Changelog mirror)

| Versión/firma | Sitio | Síntoma que resolvió | ¿Causa raíz o síntoma? |
|---|---|---|---|
| FIX v8.2 (query `data_sources`) | `layer_1_run.py:90-200`, `feed_processor.query_notion_db` | Loop infinito paginación multi-source | Causa raíz del loop; pero dejó MAX_PAGES/MAX 250 como techos silenciosos nuevos |
| Auditoría paginación 2026-07-29 (sin versión) | `query_all_items` dedup defensivo | 38 líneas para 10 IDs (empate sort key) | Síntoma (el docstring admite: "NO se descarta omisiones… pendiente chequeo aparte") |
| FIX v7.5.1 (computrabajo) | `AGREGADOR_DOMAINS` | Dominio no matcheado | Síntoma (lista manual, sin test) |
| FIX v9.21.36 agregador→True | `validate():259-275` | 6 Indeed accesibles archivadas por error | Síntoma; **creó B7→B8 (mató rama F2 + divergencia Kernel)** |
| FIX v9.21.36 rama F2 agregador | `layer_1_run.py:737-770` | (mismo) | **Muerto al nacer** por el anterior; Kernel v9.21.40 lo documenta como vivo |
| FIX BUG CRÍTICO `3aa938be…` (Fetch éxito) | `layer_1_run.py:805-827` | Éxito nunca escribía Fetch → BLOCKED por default | Causa raíz de ese bug puntual |
| H1 (v9.18.0, GATE-002/011) | `gate():505-522` | `gate()` ignoraba Score (31/36 CREATE con Score<60) | Causa raíz del drift Score↔Gate; dejó `low_score<45` vs bandas<40 desalineados (F3.5) |
| H2 (v9.19.0, GATE-010) | F3 `:846-850`, F3.6 `:1055-1060`, F4 `:1129-1137` | Recálculo sobre terminales; transición APPLIED→REJECTED muerta | Parcial: cubrió 3 fases, dejó F1/F2/F3.5/F3.5.1/F6/W4 fuera |
| H9 (Observabilidad A) | `:1142-1143` + `Last_Gate_Run` `:1196-1203` | Postulado-sin-APPLIED invisible | **La detección es código muerto** (B16); el timestamp sí vive (y causa write-churn §1.1-F4) |
| D-001 (v9.19.1) | `gate_logic.py:20` + Kernel 09.10 | Expirada solo protegida vía Next_Action | Causa raíz de ese gap; patrón "agregar al mapa" sin revisar las otras 6 listas |
| D-003 (v9.19.1) | `profile_fit.py:40` | Postulando desprotegido en cleanup | Parcial: solo F3.5/dedup-ingesta; F2/F3/F3.5.1/F3.6/F4/F6 siguen tocándolo |
| D-004 (v9.19.1) | `gate_logic.py:39,47` | Terminales silenciosos | Observabilidad real (sí funciona) |
| D-002/GAP-03 (v9.19.2) | `class_b_guard.py` + `dashboard_notion.write_patch_to_notion` | MCP/RT-1 escribía Class B sin guard | Causa raíz de la asimetría (fail-closed); **pero** `feed_processor` (vía Python) y W1 siguen sin guard simétrico — el guard solo cubre la vía Dashboard |
| GAP-01 (L0 flag) | `feed_processor.py:114-143` | Mezcla L1/L2 sin consolidar | Solo warning impreso; continúa igual (observabilidad sin enforcement) |
| GAP-02 (FAST len) | `feed_processor.py:1288-1303` | FAST con N≠1 | Enforcement real (`sys.exit`) |
| v9.14.5 rediseño Next_Action | F4 ramas + Kernel 07.8/09.10 | Catch-all Archivar destructivo; Rechazado→Ninguna | Causa raíz **solo en F4**; F2/F3.5/F3.5.1 conservan defaults destructivos (B18) |
| v9.14.2/3 migración select | schema + escrituras `{select:…}` | Next_Action rich_text→select | Causa raíz; dejó drift doc (v9.13.11 decía rich_text) corregido en v9.14.5 |
| v9.20.1 `txt()` rich_text concat | `layer_1_run.txt`, `priority_logic.txt` | Solo primer chunk leído | Causa raíz en W1; **no portado al fork W3** (`layer_1_run_dash.py:txt` sigue `rich_text[0]`) ni a `dedup_opportunities.get_plain_text` (sigue `[0]`) |
| v9.20.2 `created_time` raíz | `priority_logic.py:143-160` | Urgencia siempre MEDIO | Causa raíz; precedente documentado en Kernel 11.2 |
| v9.21.0 dedup auto (F6) | `layer_1_run.py:1260-1310` | Duplicados post-ingesta manual | Feature con guard propio débil (B-tabla: dedup-flaggea Expirada/En proceso/…) |
| v9.21.21 `generate_archive_notes` | `layer_1_run.py:474-481` + 3 call sites | Archivos sin trazabilidad | Causa raíz (append-only); vulnerable a doble-nota por snapshot stale (§1.2.2) |
| H3/v9.17.2 fila dedup Kernel | doc | Fila 09.11 documentaba un mecanismo inexistente (`REJECTED_DUPLICATE/Descartar`) | Corrección doc→código (precedente: docs describen mecanismos fantasma; este se corrigió, B8/H9 no) |
| `--skills/--new-skills` rewrite (v9.21.30) | `verify_versions.py` | Escaneaba `.skill` literales inexistentes | Causa raíz (fuera del Tracker, pero mismo patrón: asumir forma sin verificar) |

### 3.3 Código muerto verificado (3 casos, todos con evidencia de inalcanzabilidad)

1. **Rama F2 agregador-retry** (`layer_1_run.py:737-770`): requiere `not is_valid and reason.startswith("AGREGADOR_RETRY_")`; `validate()` retorna `True` en las 3 salidas agregador (`:262-275`). Inalcanzable. El Kernel 09.2/09.11 la documenta como comportamiento vigente (fix v9.21.40) — **el doc describe código muerto.**
2. **Chequeo H9 Postulado-sin-APPLIED** (`:1142-1143`): requiere `status==Postulado` tras el `continue` de `gate_logic→APPLIED` (`:1129-1137`). Inalcanzable.
3. **`is_agregador` intra-try** (`:300-302`, `return True, "AGREGADOR_VALID"`): el early-return agregador (`:262`) lo precede incondicionalmente. Inalcanzable. (Cosmético, pero confirma acumulación sin limpieza.)

### 3.4 ¿Acumulación equivalente al caso vantage-cv-b v9.16→v10.0.0?

**Sí — y peor en un eje.** El precedent (Changelog mirror v9.21.30: "CV-B v9.17.0→v10.0.0 refactor completo…; QA…; …reconciliado drift real en 5 skills") muestra el tratamiento del sistema ante 3+ parches reactivos: refactor consolidado con modelo unificado. Layer 1 acumula **≥12 parches reactivos sobre el mismo invariante** ("no tocar lo protegido / no perder trabajo del operador") sin modelo unificado de terminalidad: H2, D-001, D-003, H9, v9.14.5, v9.19.x, v9.21.36/40, Bug-3aa938be, GAP-01/02/03. Cada uno cerró UN síntoma en UNA fase. La tabla §3.1 demuestra que el invariante sigue violado en ≥10 celdas. **Recomendación de auditoría: mismo tratamiento (refactor con fuente única de verdad para transiciones de Status), no otro parche de lista.**

---

## 4. Callejones sin salida para el operador

(Escenarios verificados contra código; "Mau" = operador manual diario en Notion.)

### 4.1 `Status=Target` manual → archivado silencioso (CONFIRMADO)
F3.5 archiva `Target` con misfit (`:905-960` + `profile_fit.py:128-131`); F3.5.1 archiva `Target` con NAD pasado (`:962-1030`); F2 archiva `Target` sin JD>100 con URL muerta (`:692-830`). La nota `[ARCHIVO]` sí queda (trazabilidad), pero la decisión es irreversible por pipeline (ninguna fase saca de Expirada; solo edición manual + limpieza de `Next_Action`/`Gate_Decision` a null, per Kernel 09.10 RT-1 — procedimiento que el operador casual desconoce).

### 4.2 Class A pisada por Python sin chequeo de edición (CONFIRMADO, 3 campos)
- **`Prioridad`** (Class A): F3.6 overwrite incondicional (`:1063-1093`). Edición manual de Mau dura hasta el próximo run. Peor: como F4 reescribe `Last_Gate_Run` en todo, `last_edited_time` no distingue autoría — **ni siquiera hay forma de detectar el pisotón**.
- **`Status`** (Class A): 3 rutas a Expirada + (muerta) a Target. Sin recency-check en ninguna.
- **`Source_Type␣`** (Class A): F1 defaulta vacío→Vacante (`:~635`). Si Mau deja vacío a propósito (pendiente de clasificar), el sistema lo clasifica por él.
- `Notas` (Class A): append-only — no se pierde, pero crece sin cota y puede duplicarse (§1.2.2). `Holding`/`layer`/`hash`/`JD`/`NAD`/`URL`/`Rol`/`Marca`: W1 no los toca (solo W2-ingesta/backfill los pueblan) — a salvo del run semanal.

### 4.3 Valores de Status/Next_Action fuera de toda lista → huérfanos (CONFIRMADO)
Comportamiento por defecto ante valor desconocido (typo, valor nuevo del schema, inglés/español alterno):
- `Status` desconocido: pasa TODOS los skips/guards (ninguna lista lo contiene) → F3.5 lo archiva si hay reasons (B11: default = archivar); F4 lo re-gatea por `gate()` genérico. **No rompe, no avisa: se procesa como operativo.** Peor caso: typo en `Postulado` (ej. "Postulada") → pierde toda protección → archivable.
- `Next_Action` desconocido: `gate_logic` retorna None (no está en `TERMINAL_ACTIONS`) → recalculable → F4 lo sobrescribe. Edición manual de Next_Action (aunque sea Class B, Mau podría escribirlo) se pierde salvo `Archivar/Expirada`.
- `Gate_Decision` manual: F4 lo sobrescribe siempre (no hay rama "respetar manual"). `KERNEL:GATE-DECISION-004` ("un gate sobreescribible no es gate") lo prohíbe por diseño — coherente, pero implica que Mau **nunca** puede forzar un Gate ni siquiera transitoriamente.

### 4.4 Combinaciones imposibles / no cubiertas (schema permite, código no anticipa)
1. `Contratado` + cualquier cosa (§1.1-F4, §3.1): el estado terminal más importante del sistema (¡contratado!) no está en `STATUS_TERMINAL_MAP`, ni en `evaluate_application_status`, ni en skips de F3/F3.5.1/F3.6/F4. Resultado: Score/Prioridad recalculados, Gate re-derivado (posible CREATE), NAD-vencido → **Expirada**. Una fila Contratado con NAD viejo es archivada como fracasada.
2. `Postulando` + NAD vencido / URL muerta / score bajo: D-003 solo lo cubre en F3.5. F3.5.1 lo archiva, F2 lo expira, F4 lo re-gatea (puede →BLOCKED/Investigar mientras Mau está a mitad de aplicar).
3. `Status=Archivar` (opción select) vs checkbox `Archivar=True` vs `Next_Action=Archivar`: **triple overload del mismo nombre** (Status-opción en skips `:717,973,1117` y `_TERMINAL_STATUSES`; checkbox en tidy skill `:99` `"Archivar": {"checkbox": true}` + Kernel 09.7 "marca Archivar = True"; Next_Action-opción en `TERMINAL_ACTIONS`). Mau marca el checkbox esperando archivar; ninguna fase de W1 lee el checkbox → **nada pasa** (el checkbox solo lo consume la skill manual tidy). Inversamente, W1 escribe `Status=Archivar`… nunca: W1 solo escribe Expirada/Target — `Status=Archivar` no tiene productor en W1/W2 (¿manual? ¿legacy?). Estado escribible por schema, sin productor ni consumidor claros = huérfano bilateral.
4. `Fetch=Parcial`: producido por… nadie en W1 (W1 solo escribe Accesible/Bloqueado). Consumido en F4 (`→Verificar JD`) y `gate()` (acepta Parcial como ok). **Inferencia:** valor legacy o manual; si Mau lo setea manualmente, F2 lo pisa a Accesible en el éxito (`:815`) — edición perdida.
5. `Score_Method`, `JD_Quality`, `Dedup_Flag`, `Fuente`, `Match`: `Fuente`/`Match` eliminados de W1 v8.0 pero `Match` sigue en `CLASS_B_FIELDS` y `Fuente` la escribe W3-fork y W2-FEED (`_resolve_fuente_from_source_type`) — writers divergentes por campo.
6. `Repetida` (Kernel 07.1 la lista como valor operativo de Status): **cero referencias en código** — valor documentado fantasma. `RAW` (Manual weekly-flow: "Status=RAW"): cero referencias — fantasma. `Nueva` (mapa de `consolidate_duplicates.py:250`): solo ahí — fantasma unilateral. `Descartar`/`REJECTED_DUPLICATE`/`Ninguna`: fantasmas ya corregidos (H3/v9.14.5) — precedente de que esto se repite.
7. `En proceso/Negociando/Sin respuesta` + `Next_Action=Archivar` manual: `gate_logic` protege (action terminal) → F4 skip → pero F3.5.1/F2 no miran Next_Action → archivan igual. Protección por acción solo existe en F3/F3.6/F4.

### 4.5 Derivas y pérdidas silenciosas adicionales
- **Gate stale post-archivo:** F3.5/F3.5.1 escriben Status/Next_Action pero no Gate_Decision → filas `Expirada + Gate=CREATE` (W3 sí escribe BLOCKED — divergencia W1/W3). Filtros por CREATE incluyen expiradas.
- **F5 descarta `timing_patterns`** (calcula días applied→rejected y lo tira) — señal pedida por nadie, computada siempre.
- **W4 (consolidate) puede trashear postulaciones vivas:** `choose_primary` prefiere `Target(7) > … > Sin respuesta(4) > Expirada(2)` — un duplicado `Sin respuesta` pierde contra un `Target` y va a `_move_to_archivo` (copia lossy + trash). Sin guards, sin wiring al pipeline (daño solo si alguien lo corre manual — pero existe, es ejecutable, y nothing lo marca deprecated).

### 4.6 El contrato REVIEW_NEEDED→Target es fictional del lado lector (CONFIRMADO)
Manual + GAP-03 + troubleshooting afirman: "mientras REVIEW_NEEDED, Class B bloqueado; Status→Target = única señal de resolución". Código: **cero chequeos de `Status==REVIEW_NEEDED` en W1**; peor aún, `Target` (la "señal de resolución") es el status MENOS protegido (§3.1: archivable en F2/F3.5/F3.5.1, recalculable en F1/F3/F3.6/F4). El flujo documentado "corrige → Target → run → Class B calculado" funciona por accidente (Target es procesable), no por contrato; y la fila recién "resuelta" puede ser archivada en el mismo run por misfit. La frase del Manual "Cualquier otro valor mantiene el bloqueo" es falsa: ningún valor bloquea nada en W1.

---

## 5. Auditoría de normalización de opciones (reconstruida sin schema vivo)

> Base: literales de código (fuente primaria) + Kernel 07.1/07.8 + Manual + tidy skill. La columna "schema vivo" queda **pendiente de verificación por Claude vía Notion MCP** (ver contrato Devin §5).

### 5.1 Inventario por propiedad (evidencia convergente)

| Propiedad (tipo inferido) | Opciones con evidencia | Fuente |
|---|---|---|
| `Status` (select) | Target, Postulado, Postulando, En proceso, Negociando, Sin respuesta, Contratado, Rechazado, Expirada, Archivar, Retirado, REVIEW_NEEDED, Exploratorio, Repetida†, RAW†, Nueva† | código (todas salvo †) + Kernel 07.1 (`Repetida`) + Manual weekly (`RAW`) + consolidate (`Nueva`) |
| `Next_Action` (select, migrado v9.14.2) | Optimizar, Archivar, Investigar, Post-Mortem, Expirada, Follow-up, Interview prep, Re-check, Reparar URL, Verificar JD | Kernel 07.8 tabla (10) + F4 ramas (coinciden) |
| `Gate_Decision` (select) | CREATE, BLOCKED, REVIEW_NEEDED, APPLIED, REJECTED (+ EXPIRADA solo como valor interno de `gate_logic`, nunca escrito — `EXPIRADA` ≠ `Expirada`) | código |
| `Fetch` (select) | Accesible, Bloqueado, Parcial† (consumido, sin productor en W1) | código |
| `VM_Scope` (select) | Alto, Bajo | código |
| `Role_Class` (select) | VM, Pivote, Otro | código |
| `Source_Type␣` (select, trailing space) | Vacante, Inbound, Referencia, Networking | código |
| `Prioridad` (select) | 1 BAJO, 2 MEDIO, 3 ALTO, 4 CRÍTICO | código (mismo vocabulario en Bug/Tasks Trackers — `verify_versions.py:get_priority_tickets`) |
| `Holding` (rich_text/select? — **inferencia:** texto libre con convención) | LVMH, Kering, Inditex, … + `"Investigar"` (placeholder institucional, Kernel 07.7) + vacío | alias_map + Kernel 07.7 |
| `Dedup_Flag` (select) | Posible duplicado | código (4 escritores: W2-ingesta, F6, consolidate, `dedup_cross_layer`) |
| `Score_Method` (select) | DETERMINISTIC, BYPASS | código |
| `JD_Quality` (select) | JD Completo (+ otros no visibles en código) | código (1 literal) |
| `layer` (select) | L1, L2, L3 | código |
| `Fuente` (select) | Career Page Oficial, Agregador, LinkedIn, Gemini, + legacy {Indeed, OCC, …} en backfill | W2 `:1030-1066` + backfill `MAIL_FUENTES` |
| `Archivar` (checkbox — **inferencia robusta**) | true/false | tidy skill `:99` + Kernel 09.7 (convive con Status=Archivar y Next_Action=Archivar) |

### 5.2 Inconsistencias verificadas

1. **Idioma mezclado ES/EN (sistemático):** `Target` (EN) vs `Postulado/Expirada` (ES) en Status; `Follow-up/Interview prep/Re-check` (EN) vs `Reparar URL/Verificar JD` (ES) en Next_Action; `CREATE/BLOCKED` (EN técnico) en Gate; `Alto/Bajo` (ES) en VM_Scope; `Accesible/Bloqueado/Parcial` (ES) en Fetch. Criterio propuesto (contrato Devin §4): ES operativo + EN solo para terminología técnica fijada (Status/Score/Gate_Decision como nombres de campo, no como valores).
2. **Casing mezclado:** `REVIEW_NEEDED` (SCREAMING) como Status y como Gate_Decision vs `Target/Postulado` (Title) en Status; `Post-Mortem` (Title-hífen) vs `Follow-up` (Title-hífen-minúscula) vs `Interview prep` (sentence) vs `Re-check` en Next_Action; `JD Completo` (Title) vs `BYPASS/DETERMINISTIC` (SCREAMING) en métodos.
3. **Duplicidad semántica entre propiedades:**
   - `"Investigar"` = Next_Action legítimo (default no-destructivo F4, Kernel 07.8) **Y** placeholder-ruido en Holding (Kernel 07.7 `null → "Investigar"`). CONFIRMADO por diseño documentado. Queries/filtros por texto "Investigar" mezclan señal con ruido.
   - `"Archivar"` × 3 (Status-opción, Next_Action-opción, checkbox) — §4.4.3. CONFIRMADO.
   - `"Expirada"` = Status-opción **Y** Next_Action-opción (miembro de `TERMINAL_ACTIONS` sin productor conocido en W1 — `grep` no muestra escritura de `Next_Action=Expirada` en ningún writer; **inferencia:** legacy/manual). CONFIRMADO por código (`gate_logic.py:16`).
   - `"REVIEW_NEEDED"` = Status (W2) **Y** Gate_Decision (F4) — mismo string, dos semánticas (estado de ingesta vs banda de score 40-59). CONFIRMADO.
   - `"Bloqueado"` = Fetch-opción **Y** concepto Gate (`BLOCKED`) — CONFIRMADO (menor: distinto idioma/casing evita colisión técnica, pero confunde operador).
4. **Propiedades sin señal utilizable (criterio: ¿alguna decisión del pipeline la lee?):**
   - **`Holding`: NO aporta señal.** Ninguna fase de W1/W3 la lee (verificado: `Holding` solo aparece en `class_b_guard` lista, `feed_processor` schema/write, alias_map). Con el dato del brief (87.5% en "Investigar"/vacío — **no verificable sin Notion; se toma como dato aportado**) es costo de escritura sin lector. Contraste pedido: `Last_Gate_Run` SÍ es señal legítima (marca frescura del gate por fila; escrita siempre en F4) aunque hoy nadie la lea programáticamente — su lector es el operador/auditoría, y habilita futuros guards de recency. Criterio explícito: *una propiedad sirve si ≥1 decisión (humana o Python, presente o del refactor) la consume; Holding no tiene ninguna; Last_Gate_Run tiene lector humano + rol en el refactor.*
   - `Match`: eliminada de W1 v8.0, aún en `CLASS_B_FIELDS` y escrita por W3-fork — zombi inter-writer.
   - `Fuente`: escrita por 3 (W2, W3, nadie-en-W1) y leída por… `backfill.infer_fetch_status` y poco más — señal débil, writers divergentes.
   - `fetch_status` (W2, `aggregator/career_page`) vs `Fetch` (W1, `Accesible/Bloqueado`): **dos propiedades distintas con nombre casi idéntico y vocabularios disjuntos** — CONFIRMADO (`feed_processor.py:NotionSchema.fetch_status_prop` vs `Fetch` en W1). Si ambas existen en el schema vivo, es duplicidad estructural.
   - `fetch_status` valores `aggregator/career_page/filled?` (W2) vs código que chequea `== "aggregator"` en `run_url_gate` — `filled` cae al path career_page (default silencioso).
5. **Nombres de propiedad inconsistentes:** `Source_Type␣` con trailing space (trampa documentada en `class_b_guard.py:37` y causante probable del skip silencioso en W2 `:1099`); `Rol/Marca/Notas` (ES) vs `Score/Status/URL/JD/NAD` (EN/short); `Apply Date/Rej Date/Interview_Date` (mezcla espacio/guión); `URL Notion` vs `URL`.

### 5.3 Pendiente de verificación contra schema vivo (para Claude/MCP, no Devin)
Lista mínima: opciones completas de Status, Next_Action, Gate_Decision, Fetch, JD_Quality, Fuente, Prioridad, layer, Dedup_Flag, Score_Method, Role_Class, VM_Scope, Source_Type␣ (confirmar trailing space), tipo real de Holding/Marca (select vs rich_text/texto — `NotionSchema.brand_type` lo tolera ambos, `:365-378`), existencia del checkbox `Archivar`, existencia de `fetch_status` vs `Fetch`, existencia de `Score_Method`/`Last_Gate_Run`/`Positioning_Mode`/`Fuente_Manual` (mencionados en Kernel 07.1/07.3, sin productor en código auditado).

---

## Apéndice A. Lecturas lineales sugeridas para Devin (orden)
1. `Layer_1/scripts/layer_1_run.py` F2+F3.5+F3.5.1+F4 (el corazón destructivo) 2. `profile_fit.py` completo 3. `gate_logic.py` completo 4. `feed_processor.py:process_record` + `build_notion_properties` 5. `priority_logic.py` 6. `dedup_opportunities.py:is_terminal_state/are_duplicates` 7. `Dashboard/scripts/layer_1_run_dash.py` (divergencias) 8. `consolidate_duplicates.py:choose_primary/_move_to_archivo` 9. `Documentación/ACTIVE/Kernel.md` §§07/09/11.2 10. `Documentación/ACTIVE/Changelog Archivo.md` entradas v9.14.5, v9.17.2(H3), v9.18.0(H1), v9.19.0(H2), v9.19.1(D-001/003/004), v9.19.2(D-002), v9.20.1/2, v9.21.0, v9.21.21, v9.21.36/40, v9.21.30(CV-B v10).

## Apéndice B. Glosario de firmas de parche
H1/H2/H9 = hallazgos auditoría arena+Claude 2026-08-10 (Issues #1/#2); D-001..004 = fixes Devin coordinados v9.19.1/2; GAP-01/02/03 = gaps estructurales FEED; FIX vX = fix de release; KERNEL:GATE-DECISION-0XX = anclas normativas (09.1–09.13 + 09.12-duplicado: nótese que `KERNEL:DEDUP-LAYER-UPGRADE` ocupa el slot 09.12 con ID no secuencial — drift de numeración menor).
