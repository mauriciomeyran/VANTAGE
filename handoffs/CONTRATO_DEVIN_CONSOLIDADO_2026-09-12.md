# CONTRATO-HANDOFF CONSOLIDADO — Reemplazo total orquestador Tracker (Devin)

**Para:** instancia Devin vigente (van 2 muertas por tokens) · **De:** Mauricio Meyrán vía Arena
**Documento ÚNICO y suficiente:** todo lo necesario está aquí dentro. Contratos/handoffs/
actas previos = contexto histórico OPCIONAL (§9); en contradicción, MANDA ESTE.
**Base:** rama fresca desde `origin/main` al abrir (reporta SHA; prohibido partir de otra
base). Ramas prohibidas (no leer como fuente, no partir de ellas, no mergear):
`origin/devin/tracker-refactor-v3` (superseded: 961 líneas/27 tests VIEJOS — adoptar eso
es regresión) y `origin/devin/plan-refactor-tracker-v2` (stale, docs). Lección pagada 2 veces.
**Estado heredado:** G0/G1 verdes sobre `35da44d` (re-verificar en TU base, §0 — no heredar
verdes); G2 reclamado 2 veces, 2 veces RECHAZADO (incompleto/sin medir); G3–G10 pendientes.
**Autorizaciones Mau registradas:** (a) implementación completa, cero recorte — solo Mau
descopa por escrito; (b) fallidos ajenos al tracker se ignoran (si aparecen, listar IDs).

## §0 Órdenes primeras (antes de codear)

1. `git log --oneline -1` + `git status --short` + rama fresca desde `origin/main`.
2. INVENTARIO crudo: `git log --oneline -8`; por cada path — existe sí/no + `wc -l` +
   `git log --oneline -3 -- <path>`: `Layer_1/scripts/tracker_flow.py`,
   `tests/test_tracker_flow_v3.py`, `Layer_1/scripts/vl1_sync.py`,
   `tests/test_vl1_sync.py`, `Layer_1/scripts/layer_1_orchestrator.py`,
   `tests/test_layer_1_orchestrator.py`. Sin este reporte nada avanza (resuelve qué
   aterrizó, quién lo escribió, qué adoptas vs creas).
3. Re-corre G0/G1 (§6) en tu base. Esperado: v3-file 39 passed; vl1_sync 3 passed si
   aterrizó (confirmar, no asumir).

## §1 Objetivo (binario)

Al cierre: `layer_1_run.py` v7.5 y `Dashboard/scripts/layer_1_run_dash.py` NO existen en el
árbol activo (movidos a `Archive/`, cero borrado físico); el orquestador nuevo ejecuta TODAS
las fases §2 sobre `tracker_flow.py` como único core; la cadena `vl1` resuelve al nuevo
entry; cada transición de `Status` = exactamente un gate + una protección + ediciones
manuales recientes inmunes. Cero escrituras a Notion prod (fixtures + fake únicamente).

## §2 Alcance fase por fase (todo obligatorio)

- **F0 NAD + F3.5.1:** un solo cómputo de expiración (hoy duplicado).
- **F1.5 clasificación** (VM_Scope/Role_Class/Source_Type): reglas idénticas, enums cerrados.
- **F2 URL Gate:** mismo gate + inmunidad manual (Objetivo/ediciones recientes).
- **F3 Scoring v6.4 + bandas:** fórmula idéntica; bandas = contrato testeado.
- **F3.5 misfit/exclusiones:** protección = `is_mutable` único (cierra whitelist incompleta);
  portar `profile_misfit_reasons`/`should_auto_cleanup`/`is_role_excluded`.
- **F3.6 Prioridad:** misma matriz vía `priority_logic.py`. NO tocar su bug día/mes.
- **F4 Gate + Next_Action:** writers vía enums + mappings (cero strings sueltos); `gate()` y
  `gate_logic()` fusionados u ordenados con precedencia testeada.
- **F5 patrones + F6 dedup:** survivor canónico L1>L2>L3>N/A + guard `is_mutable`;
  `consolidate_duplicates.py` a `Archive/` (trash físico sin confirmación = prohibido).
- **Ingesta `feed_processor.py`:** adaptado a vocabulario §3 (alias_map, Holding/Marca).
- **`batch_operations.py`:** retirado o migración versionada de un uso (incluye case `batch`
  del pipeline.sh + nota glosario — referencia viva confirmada).
- **Clase B:** `class_b_guard` a TODAS las vías Python; MCP = exención documentada con control
  procedural (APROBAR_WRITE + cláusula). No afirmar cierre-en-código de lo procedural.
- **Transversales:** un solo re-query inicial + snapshot; writes SOLO con diff real (filas sin
  cambio no se tocan — prerrequisito de precedencia manual, con test anti-reescritura);
  ventana manual = "desde último run exitoso" (`last_edited_time > Last_Gate_Run` + autor humano).

## §3 Decisiones finales Q-1–Q-10 (cerradas, no reabrir)

- **Q-1 `Source_Type␣`:** RENOMBRAR a limpio con migración (código + lectores/escritores);
  rename del schema vivo vía Claude/MCP ordenado ANTES del cutover (dependencia en plan §6-G8).
- **Q-2 Target→Objetivo:** YA ejecutado y verificado en prod (0 filas Target). Nada que hacer.
- **Q-3 Holding:** curar (select alias_map o vacío); holdings REALES (Nike Inc., LVMH) se
  migran, jamás se vacían; placeholders → vacío. Criterio fino vive en Task `3d8938be`.
- **Q-4 bloqueo Class-B/REVIEW_NEEDED:** NO implementar (aceptado) CONDICIONAL a derogar
  `KERNEL:GATE-DECISION-010` en docsync. Sin derogación, gate rojo.
- **Q-5 ventana manual:** §2-transversales (ventana + conditional writes + test). Inseparables.
- **Q-6 snapshot:** confirmado. **Q-7 bug día/mes:** no tocar. **Q-8 dedup:** unificar +
  Archive + survivor + guard (dependencias = grep tuyo). **Q-9 guard:** §2-Clase B.
- **Q-10 batch:** §2-batch.

## §4 Ground truth inline (no re-censar, no re-fetch para decidir)

Tracker prod: 24 filas. Status 12 (= enum código); Outcome 4, 100% VACÍO (backfill = no-op
verificado triple); Next_Action vivo 11 (EN legacy: Follow-up/Interview prep/Re-check +
Ninguna/Expirada — normalizar per §6-G7); Gate_Decision vivo 6
(REJECTED/CREATE/BLOCKED/APPLIED/EXPIRED/REVIEW_NEEDED); Fetch 2 (Accesible 22/Bloqueado 2);
layer L1=10/L3=12/N/A=2/L2=0; Target=0; valores fantasma=0. Backup: CSV sha256
`7da5210c2bda170c6b590272d0d21f70691a31a74dfaf6b1c4244c1f8b7eb071`, 24/24.
IDs: DATABASE `596938be-fc42-836b-aea7-814a1491bd47` (/databases, API 2022-06-28) vs DATA
SOURCE `442938be-fc42-828f-b72e-076818d65a5b` (data_sources, API 2025-09-03). No intercambiables.
Core verificado: `tracker_flow.py` 1106 líneas (F13 sync + fix layer + enum alineado) +
39 tests + fixtures(≥15)/fake. Runner ref: `vl1_sync.py` (patrón obligatorio para dry-run:
proxy read-only, `--dry-run` default, `--apply` gateado exit 2). One-shot
`sync_status_contratado.py`: verificado no-op → archivar al cierre. Writer vivo HOY:
`layer_1_run.py` v7.5 con strings hardcodeados (lo que se reemplaza).

## §5 Prohibiciones (una violación = gate rojo)

Parches a whitelists; fases numeradas sobre lo viejo; writers fuera del core; literales
sueltos en writers; `else` destructivo sin `DECISION:` + test de rama; defaults que escriben
sin log; tocar filas sin diff; `input()`; secretos; cualquier Notion prod (leer o escribir);
auto-recorte de alcance; re-decidir §3; inventar filenames (orquestador =
`layer_1_orchestrator.py`, tests `tests/test_layer_1_orchestrator.py` — si existen: adoptar +
completar; los 17 tests previos NO cuentan como G2).

## §6 Gates (todos verdes o RECHAZADO)

- **G0/G1:** base + suite tracker verde (re-corridos §0). Cualquier rojo tracker = alto.
- **G2 cobertura (rehacer):** tests `test_<fase>_*` por CADA fila §2; cobertura MEDIDA ≥90%
  en módulos nuevos (pegar tabla coverage — conteo solo no pasa). Reportable en 2 mitades
  (G2a F0–F3.6, G2b resto); cierra con ambas. Push comprobable por mitad (§7).
  Aclaración vinculante 2026-09-12: el ≥90% whole-file se verifica al CIERRE de ambas
  mitades; por mitad se exige tests por fila + push comprobable + reporte honesto.
- **G3 paridad:** harness paralelo viejo-vs-nuevo sobre fixtures (≥15 filas, todas las ramas):
  diff vacío salvo allowlist justificada entrada por entrada.
- **G4 un escritor:** grep literales sueltos en writers = 0 (comandos exactos en reporte).
- **G5 manual-first:** fixtures humano-tocadas inmunes; sugerencia = revisión, jamás ejecución.
- **G6 retiro:** `git status` EXACTO: nuevos (orquestador/tests/migraciones/plan) + `Archive/`
  (viejos movidos) + pipeline.sh/Raycast al nuevo entry; `vl1` corre el nuevo en dry-run.
- **G7 normalización:** tabla `actual→normalizado` + scripts idempotentes (dry-run, reanudables,
  pre/post) para Next_Action/Gate_Decision/pruning + rename `Source_Type␣` (ordenado pre-cutover).
- **G8 despliegue:** paso-a-paso (comando Claude/MCP o script, validación, rollback), export
  pre-migración, congelamiento manual, checklist post (matriz radiografía §3.1).
- **G9 docsync:** diffs (Kernel §§07/09 incl. derogación GATE-DECISION-010, Manual, tidy skill)
  + entrada Changelog formato vigente. Los aplica Claude.
- **G10 handoff:** serial + paths + tests + abiertas formato `Q-n` + frase textual:
  "Ninguna escritura a Notion de producción fue realizada ni intentada en esta sesión."

## §7 Protocolo (anti-muerte-por-tokens, 2 precedentes)

Gates en orden, reporte por gate (evidencia PRIMERO: comandos + outputs crudos; prosa mínima;
lotes chicos — morir redactando = repetir el loop). Push comprobable por gate: SHA local +
`git status --short` vacío + `git log origin/<rama> --oneline -1` == SHA. Archivo "adoptado"
declara path + SHA-origen + autor (prohibido "ya existía" sin procedencia). Prohibido saltar,
fusionar o declarar "no aplicable". Duda → decidir, implementar, registrar en abiertas. Fin
SOLO en todo-verde o descoping escrito de Mau. Si no cabe: reportar gate alcanzado = estado
RECHAZADO-PARCIAL (Mau decide: continúa, recorta por escrito, o re-emite).

## §8 División

Devin: código + tests + planes + diffs (cero Notion). Claude: schema/migraciones vía MCP con
APROBAR_WRITE paso a paso. Arena: re-ejecuta CADA comando §6 sobre el diff; un mismatch =
rojo. Mau: aprueba gates, declara done.

## §9 Contexto opcional (NO requerido)

Contrato v1, handoffs de retomada, actas T0–T6, brief doc transversal, radiografía E2E.
Solo si quieres entender el porqué histórico de algo. Nada de aquí se evalúa.