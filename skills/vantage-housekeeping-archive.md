---
name: vantage-housekeeping-archive
description: "Housekeeping de archivado del VANTAGE Tracker: detecta candidatos (Dedup_Flag, Status=Expirada, Next_Action Archivar/Post-Mortem), delega el marcado Archivar=True a vantage-tidy-opportunities-tracker (única vía de escritura, DRY RUN + APROBAR_WRITE) y entrega reporte de cola de archivo con IDs de página para localización visual del operador. No mueve páginas ni escribe en el Archivo Tracker."
---

## Convención de anuncio (KERNEL:SKILL-ANNOUNCE-CONVENTION)

- Apertura: `ARCHIVING HOUSEKEEPING...`
- Cierre: `ARCHIVE HOUSEKEPT`

## Alcance (léase primero)

Consolida el ciclo completo de archivado vigente (KERNEL:GATE-DECISION-007 §09.7 — Marcado Manual de Archivado): **detección → marcado → reporte**. La decisión del operador (2026-08-01) sigue vigente: no se mueven ni copian páginas automáticamente, y el Archivo Tracker no se toca (esquema con propiedades duplicadas/corruptas sin resolver — ver `vantage-tidy-opportunities-tracker`). `auto_archive.py` permanece deprecado en `Archive/Legacy_Scripts/` como referencia histórica (KERNEL:EVOLUTION §17).

## Fase 0 — Detección (lectura, sin escritura)

Señales de candidato, en orden de fuerza:

1. `Dedup_Flag = "Posible duplicado"` — señal primaria de duplicado.
2. `Status = "Expirada"` — señal real y suficiente de expiración. `Gate_Decision=EXPIRED` existe en schema pero **no se puebla en la práctica** — no depender de ese valor (verificado 2026-07-19).
3. `Next_Action ∈ {Archivar, Post-Mortem}` (KERNEL:SCHEMA-008 §07.8; KERNEL:GATE-DECISION-006).

Guards obligatorios antes de proponer cualquier candidato (KERNEL:GATE-DECISION-010 + `gate_logic.py`):

- `Gate_Decision = APPLIED` → exclusión absoluta; reportar aparte como "aplicación activa, requiere revisión manual".
- Orden de evaluación: `STATUS_TERMINAL_MAP` → `TERMINAL_ACTIONS`.
- Nunca sobreescribir `Next_Action` ni ningún campo Class B (KERNEL:CV-GOLDEN-RULES-002).

## Fase 1 — Marcado (única vía de escritura)

Delegar 1:1 a la skill **`vantage-tidy-opportunities-tracker`**: payload mínimo `{"properties": {"Archivar": {"checkbox": true}}}`, Dry Run con tabla (`Vacante | Marca | Criterio | Evidencia | Gate_Decision`) → variante válida de `APROBAR_WRITE` → write-back verification por página.

Esta skill no duplica ese procedimiento — lo invoca como sub-skill (mismo patrón con que KERNEL:GATE-DECISION-009 escala a `vantage-create-bug-task`).

## Fase 2 — Reporte de cola de archivo (read-only, desfricción)

Objetivo: eliminar el escaneo visual del Tracker. En orden de preferencia:

- `status_report.py --archive-queue` — vista de registros con `Archivar=True` agrupados por criterio con IDs de página (flag **PENDIENTE de implementación** — ticket de código abierto en el batch de saneamiento; hasta que exista, usar la alternativa manual).
- Alternativa vigente: fetch del Tracker filtrado por `Archivar=True` y presentar tabla `Marca | Rol | Criterio | Page ID` para localización directa en Notion.

## Reglas de oro

- Nunca mover páginas físicamente (`archived: true`) — decisión del operador.
- Nunca escribir en el Archivo Tracker.
- Nunca marcar sin Dry Run + `APROBAR_WRITE`.
- Nunca incluir `Gate_Decision=APPLIED` en el batch.
- Nunca asumir expiración por antigüedad — solo `Status=Expirada` ya asignado por Python.
- Sin reversión automática: desmarcar `Archivar` es corrección manual del operador.

## Cierre de sesión (KERNEL:CENSUS-SYNC, Regla 4)

Reportar sin que el operador lo pida: total de candidatos detectados, marcados y excluidos por APPLIED, y confirmación de que ningún Class B fue escrito por esta vía.

## Fuentes verificadas

KERNEL:GATE-DECISION-007 §09.7 (texto vigente post-v9.17.1); skill `vantage-tidy-opportunities-tracker` (procedimiento y guards); auditoría arena.ia 2026-08-13 — `AUDIT_SANEAMIENTO_ESTRUCTURAL.md`, Entregable 1 (Fases 0–4, diseño original).
