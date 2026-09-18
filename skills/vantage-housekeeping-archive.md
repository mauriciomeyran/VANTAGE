---
name: vantage-housekeeping-archive
description: "Housekeeping de archivado del VANTAGE Tracker: detecta candidatos (Dedup_Flag, Status=Expirada, Next_Action Archivar/Post-Mortem), delega el marcado Archivar=True + documentación de razón determinista en Notas a vantage-tidy-opportunities-tracker (única vía de escritura, DRY RUN + APROBAR_WRITE) y entrega reporte de cola de archivo con IDs de página para localización visual del operador. No mueve páginas ni escribe en el Archivo Tracker. VANTAGE-ALIGNED: Integra KERNEL requirements (DOCUMENTATION-005, DOCUMENTATION-010, DOCUMENTATION-012, DOCUMENTATION-008, FAIL-PHILOSOPHY) y maximiza token economy via sandbox protocol."
---

## Convención de anuncio (KERNEL:DOCUMENTATION-005)

- Apertura: `ARCHIVING HOUSEKEEPING...`
- Cierre: `ARCHIVE HOUSEKEEPING COMPLETE`

## Alineación con KERNEL — Economía de Tokens Máxima

**KERNEL:DOCUMENTATION-010** — Protocolo de 6 fases (Fase 0 Detección → Fase 1 Marcado → Fase 2 Reporte)

**KERNEL:DOCUMENTATION-005** — Convención de Anuncio de Skills

**KERNEL:DOCUMENTATION-012** — Contrato de Cero Inferencia Silenciosa: toda afirmación técnica requiere ancla exacta (PREFIX:KEY)

**KERNEL:DOCUMENTATION-008** — Census Compliance: no crea/modifica IDs canónicos, no requiere CENSUS-SYNC

**KERNEL:FAIL-PHILOSOPHY** — No sugerir workarounds, solo reportar estado y esperar instrucción humana

## Protocolo Sandbox — Economía de Tokens Máxima

**Regla fundamental:** Todos los procesos internos corren en sandbox sin renderizar al operador. Solo se output:
1. `ARCHIVING HOUSEKEEPING...` (inicio)
2. `ARCHIVE REPORT` + resultados de detección/marcado (resultado final)
3. `ARCHIVE HOUSEKEEPING COMPLETE` (cierre)

**Procesos silenciosos (sandbox interno):**
- Detección de candidatos (Fase 0)
- Validación de guards obligatorios
- Delegación a vantage-tidy-opportunities-tracker
- Generación de reporte de cola de archivo

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

## Checklist de Validación Pre-Cierre (sandbox interno)

[Proceso interno] Antes de declarar el cierre, verificar:
- [ ] Todos los candidatos fueron evaluados contra guards obligatorios (KERNEL:GATE-DECISION-010)
- [ ] Ningún Gate_Decision=APPLIED fue incluido en el batch
- [ ] Todos los marcados tienen DRY RUN + APROBAR_WRITE previo
- [ ] Delegación a vantage-tidy-opportunities-tracker se ejecutó correctamente
- [ ] Reporte de cola de archivo incluye IDs de página para localización
- [ ] Ningún Class B fue escrito por esta vía (confirmación explícita)
- [ ] Protocolo sandbox respetado (solo 3 outputs visibles)
- [ ] Convención de anuncio aplicada (KERNEL:DOCUMENTATION-005)

Si algún punto falla, detener y reportar el gap — no declarar `ARCHIVE HOUSEKEEPING COMPLETE` a medias.

## Fuentes verificadas

KERNEL:GATE-DECISION-007 §09.7 (texto vigente post-v9.17.1); skill `vantage-tidy-opportunities-tracker` (procedimiento y guards); auditoría arena.ia 2026-08-13 — `AUDIT_SANEAMIENTO_ESTRUCTURAL.md`, Entregable 1 (Fases 0–4, diseño original).
