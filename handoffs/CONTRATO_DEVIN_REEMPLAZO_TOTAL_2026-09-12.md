 CONTRATO DE SESIÓN DETERMINÍSTICO — Reemplazo total del orquestador Tracker (Devin)

**Para:** Devin (agente autónomo) · **De:** Mauricio Meyrán (operador) vía auditoría Arena
**Base:** `main`@HEAD al abrir sesión (Devin reporta `git log --oneline -1` primero; todo se
mide contra esa base). **Predecesor:** `CONTRATO_DEVIN_REFACTOR_TRACKER_2026-09-11` (v1):
su ítem §6.1 (core `tracker_flow.py`) está entregado y verificado (39 tests); los ítems
§6.2–§6.6 NO están hechos. Este contrato ordena EXACTAMENTE ese delta. La válvula de
entrega parcial del §7-v1 queda REVOCADA: entrega incompleta = RECHAZADA (§8), no aceptada.

**Lectura obligatoria primera (en orden):** v1 completo + `AUDITORIA_TRACKER_E2E_2026-09-11`
+ `CIERRE_DEPLOY_TRACKER_2026-09-11` + `HANDOFF_T6_VL1S_SIDECAR_2026-09-11` (patrón runner:
proxy read-only, `--dry-run` default, exit codes) + §4-v1 (normalización; Estado HOY:
Status ya renombrado y verificado 0 huérfanos; pendiente Next_Action/Gate_Decision/pruning).

## 1. Objetivo (binario, sin interpretación)

Al cierre: `layer_1_run.py` v7.5 y `Dashboard/scripts/layer_1_run_dash.py` NO existen en el
árbol activo (movidos a `Archive/`, §G7); un orquestador nuevo ejecuta TODAS las fases
(§2) sobre `tracker_flow.py` como único core de decisión; la cadena `vl1` resuelve al
nuevo entry point; cada transición de `Status` tiene exactamente un gate, una protección,
y respeta ediciones manuales recientes como máxima prioridad. Cero escrituras a Notion
prod por Devin (sin token, sin MCP-write, fixtures + fake únicamente).

## 2. Alcance fase por fase (todo obligatorio, nada opcional)

Cada fila = migrar al core nuevo con paridad de comportamiento documentado + tests +
entrada en plan de despliegue. Paridad se prueba con harness paralelo viejo-vs-nuevo
sobre fixtures (§G3); cada divergencia INTENCIONADA lleva justificación + cita a
Changelog/ARCHIVO.

- **F0 NAD + F3.5.1 expiración NAD:** un solo cómputo de expiración (hoy duplicado).
- **F1.5 (clasificación VM_Scope/Role_Class/Source_Type):** reglas idénticas, enums cerrados.
- **F2 URL Gate:** mismo gate + guard manual (Target/Objetivo y ediciones recientes inmunes).
- **F3 Scoring v6.4 + bandas:** fórmula idéntica; bandas como contrato testeado (H1).
- **F3.5 misfit + exclusiones:** whitelist incompleta PROHIBIDA — protección = `is_mutable`
  único; `profile_misfit_reasons`/`should_auto_cleanup`/`is_role_excluded` portados, no pegados.
- **F3.6 Prioridad:** misma matriz Urgencia×Importancia vía `priority_logic.py` (NO tocar su
  bug día/mes `:125` — backlog documentado; portar llamada, no lógica).
- **F4 Gate + Next_Action:** writers vía enums + `DELETED_VALUE_MAPPINGS` (cero strings
  hardcodeados sueltos — ver §G4); `gate()` técnico y `gate_logic()` negocio fusionados u
  ordenados con precedencia testeada.
- **F5 patrones + F6 dedup audit:** survivor canónico (`choose_survivor`, L1>L2>L3>N/A) +
  guard `is_mutable`; `consolidate_duplicates.py` retirado o bajo el mismo guard (prohibido
  trash físico sin confirmación).
- **Ingesta:** `feed_processor.py` adaptado al vocabulario normalizado (alias_map, Holding/Marca
  per §4-v1); `batch_operations.py` retirado o convertido a migración versionada de un uso.
- **Clase B:** `class_b_guard` generalizado a TODAS las vías o exención documentada (D-002).

## 3. Prohibiciones (violar una = gate rojo automático)

Parches a whitelists/blacklists existentes; fases numeradas nuevas sobre lo viejo; writers
nuevos fuera del core; strings hardcodeados de Status/Next_Action/Gate_Decision en writers
(fuera de enums/mappings); `else` destructivo sin comentario `DECISION:` + test de rama;
defaults que escriben sin log `[DEFAULT]`; tocar filas sin diff material; `input()` en
pipeline; secretos en repo; escritura/lectura a Notion prod; REDUCIR ALCANCE sin
autorización escrita del operador en chat (el agente no se auto-recorta).

## 4. Gates de aceptación (todos verdes o RECHAZADO — §8)

- **G0 base:** `git log --oneline -1` + `pytest` suite completa verde ANTES de tocar nada
  (cuenta reportada; base esperada ≥39).
- **G1 invariante:** suite existente verde en TODO momento; cualquier rojo = alto inmediato.
- **G2 cobertura:** ≥90% en módulos nuevos; test `test_<fase>_*` por cada fase §2; test de
  alcanzabilidad por cada rama destructiva nueva (v9.21.36/40).
- **G3 paridad:** harness paralelo viejo-vs-nuevo sobre fixtures (≥15 filas, todas las ramas
  §4 radiografía): diff de decisiones vacío salvo allowlist justificada entrada por entrada.
- **G4 un solo escritor:** `grep -rn` de literales sueltos en writers = 0 (comandos exactos
  en reporte; Arena los re-ejecuta).
- **G5 manual-first:** fixtures con filas tocadas-por-humano → inmunes a mutación destructiva;
  `Next_Action` sugerido = revisión, jamás ejecución silenciosa.
- **G6 retiro:** `git status` muestra EXACTAMENTE: nuevos (orquestador, tests, migraciones,
  plan) + `Archive/` (viejos movidos, cero borrado físico) + pipeline.sh/Raycast apuntando
  al nuevo entry; `vl1` resuelve al orquestador nuevo end-to-end en dry-run.
- **G7 normalización restante:** tabla ejecutable `actual→normalizado` + scripts idempotentes
  (dry-run primero, reanudables, conteo pre/post) para Next_Action/Gate_Decision/pruning §4-v1.
- **G8 despliegue:** documento paso-a-paso (comando exacto Claude/MCP o script, validación,
  rollback), export pre-migración, ventana de congelamiento manual, checklist post (matriz
  radiografía §3.1 toda ✓/~/documentada).
- **G9 docsync:** diffs listos (Kernel §§07/09, Manual, tidy skill) + entrada Changelog formato
  vigente. La aplica Claude, no Devin.
- **G10 handoff:** serial + paths + tests + abiertas (formato `Q-n`, v1-§7) + frase textual:
  "Ninguna escritura a Notion de producción fue realizada ni intentada en esta sesión."

## 5. Protocolo de sesión (sin Mau presente)

Gates en orden G0→G10, reporte por gate (evidencia primero: comandos + outputs crudos, regla
S4 v9.21.56). Prohibido saltar, fusionar o declarar gates "no aplicables" unilateralmente.
Duda → decidir con contrato+histórico, implementar, registrar en abiertas. La sesión termina
SOLO en TODO-VERDE o con descoping explícito escrito del operador. Estimación: una sesión;
si no cabe, se reporta en qué gate se detuvo y QUEDA RECHAZADO-PARCIAL (no aceptado): el
operador decide si continúa, recorta por escrito, o re-emite.

## 6. División de trabajo

Devin: código + tests + planes + diffs (cero Notion). Claude: migraciones/schema vía MCP con
APROBAR_WRITE paso a paso. Arena: re-ejecuta CADA comando de aceptación §4 sobre el diff
entregado; un solo mismatch = gate rojo. Mau: aprueba gates, declara done.