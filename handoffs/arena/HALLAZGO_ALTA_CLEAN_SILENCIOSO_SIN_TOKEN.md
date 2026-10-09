# HALLAZGO ALTA SEVERIDAD — CLEAN silencioso sin NOTION_TOKEN en dry-run de ingesta

**Autor:** ARENA/DEFAULT · **Fecha:** 2026-10-09 · **Contrato:** CS-ARENA-L1-01 (cierre, por instrucción de CLAUDE/MAIN HO-000094 en nombre del operador)
**Severidad:** ALTA
**Estado:** Reportado. Propuesta NO implementada (requiere decisión del operador).

## Hallazgo (redacción acordada con CLAUDE/MAIN)

HALLAZGO ALTA SEVERIDAD: `layer_1_orchestrator.py:1186-1210` — sin `NOTION_TOKEN`, el dry-run de ingesta asigna `disposition="CLEAN"` a todos los registros sin pasar por `process_record` (donde viven Hard Blocks y reglas de rol, `feed_processor.py:1004`). El resumen final no distingue "evaluado y limpio" de "no evaluado". Cualquier dry-run sin credenciales reales produce falsos negativos silenciosos. Propuesta (sin implementar): que el resumen declare explícitamente "N registros NO EVALUADOS (sin token)" en vez de "N limpio" cuando falte `NOTION_TOKEN`.

## Evidencia de soporte (reproducida en sandbox, 2026-10-09)

- Warning único, fácil de pasar por alto: `layer_1_orchestrator.py:1187` → `"Sin NOTION_TOKEN — dry-run de ingesta limitado (sin schema/dedup live)"`.
- Fallback con disposition hardcodeada: `layer_1_orchestrator.py:1191-1205` (construye `ProcessedRecord(..., disposition="CLEAN", ...)` en :1199 sin llamar a `process_record`).
- Reglas que se omiten: hard block por JSON (`feed_processor.py:984` → `blocked_employer_term`, `hard_block_gate.py:62-65`), hard block por alias (`feed_processor.py:993-1001`), reglas de rol (`feed_processor.py:1004-1011` → `profile_fit.py:18-45`), URL gate y dedup.
- Demostración empírica: mismo feed `CS-L1-RUNTIME-02_workday_chanel_2026-10-06.json`:
  - Dry-run sin token (orquestador): `10 limpio · 0 BLOCKED · 0 REVIEW_NEEDED` — incluye "Makeup Marketing Coordinator" como CLEAN.
  - Ruta completa con `process_record` (reproducción offline, dedup/URL mockeados, regla de rol intacta): `{'CLEAN': 9, 'BLOCKED': 1}` — BLOCKED = "Makeup Marketing Coordinator | exclude role: marketing_coordinator", idéntico a `feeds/2026-10-08_dryrun.md` (corrida del operador con token).
- Riesgo agravado: un dry-run sin token sobre un feed con empleadores Hard Block (p. ej. L'Oréal, Levi's, El Palacio de Hierro) los mostraría como CLEAN en el resumen y en el archivo `feeds/<fecha>_dryrun.md`, que es el artefacto que se revisa/archiva.

## Propuesta (sin implementar)

1. En la rama sin token de `run_ingestion` (`layer_1_orchestrator.py:1191-1205`), usar una disposition distintiva (p. ej. `NOT_EVALUATED` o mantener CLEAN con `notes="NO EVALUADO (sin NOTION_TOKEN)"`).
2. Que `print_dryrun_summary` / `write_dryrun_file` declaren en el resumen: "N registros NO EVALUADOS (sin token)" en vez de "N limpio" cuando falte `NOTION_TOKEN`.
3. Test pytest que conmute la presencia/ausencia de token (cliente mock) y verifique que el resumen distingue ambos casos.
