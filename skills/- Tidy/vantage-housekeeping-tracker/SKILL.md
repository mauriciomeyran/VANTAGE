---
name: vantage-housekeeping-tracker
description: "Orquesta el housekeeping de trackers (Bug/Task Tracker, VANTAGE Tracker, Change Log) en un solo punto de entrada. Ejecuta en orden lógico: Bug/Task Tracker (prioridad CRÍTICO/ALTO) → VANTAGE Tracker (housekeeping de vacantes) → Change Log (recorte a últimas 10 entradas). VANTAGE-ALIGNED: Integra KERNEL requirements (DOCUMENTATION-005, DOCUMENTATION-010, DOCUMENTATION-012, DOCUMENTATION-008, FAIL-PHILOSOPHY) y maximiza token economy via sandbox protocol."
---

# VANTAGE — Housekeeping Tracker Meta-Skill

Orquesta de forma determinista el housekeeping de trackers (Bug/Task Tracker, VANTAGE Tracker, Change Log), reutilizando las skills hijas sin duplicar lógica.

## Convención de Anuncio (KERNEL:DOCUMENTATION-005)

- Apertura: `HOUSEKEEPING TRACKERS...`
- Por tracker: reutilizar la apertura/cierre de la hija correspondiente
- Cierre global: `TRACKERS HOUSEKEPT`

## Alineación con KERNEL — Economía de Tokens Máxima

**KERNEL:DOCUMENTATION-010** — Protocolo de 6 fases (Bug/Task → VANTAGE → Change Log)

**KERNEL:DOCUMENTATION-005** — Convención de Anuncio de Skills

**KERNEL:DOCUMENTATION-012** — Contrato de Cero Inferencia Silenciosa: toda afirmación técnica requiere ancla exacta (PREFIX:KEY)

**KERNEL:DOCUMENTATION-008** — Census Compliance: no crea/modifica IDs canónicos, no requiere CENSUS-SYNC

**KERNEL:FAIL-PHILOSOPHY** — No sugerir workarounds, solo reportar estado y esperar instrucción humana

## Protocolo Sandbox — Economía de Tokens Máxima

**Regla fundamental:** Todos los procesos internos corren en sandbox sin renderizar al operador. Solo se output:
1. `HOUSEKEEPING TRACKERS...` (inicio)
2. `HOUSEKEEPING REPORT` + resultados de tidy por tracker (resultado final)
3. `TRACKERS HOUSEKEPT` (cierre)

**Procesos silenciosos (sandbox interno):**
- Detección de tickets resueltos en Bug/Task Tracker
- Detección de duplicados/expiradas en VANTAGE Tracker
- Detección de exceso de entradas en Change Log
- Ejecución de skills hijas en orden lógico

## Skills hijas dependientes

Esta skill orquesta las siguientes skills en orden fijo de prioridad:

1. `vantage-tidy-bug-task-tracker` → Bug/Task Tracker (tickets resueltos → Archivar=True)
2. `vantage-tidy-opportunities-tracker` → VANTAGE Tracker (duplicados/expiradas → Archivar=True)
3. `vantage-tidy-changelog` → Change Log (recorte a últimas 10 entradas)

## Trigger / Activación

Activar cuando el operador diga cualquiera de:
- `housekeeping trackers`
- `tidy trackers`
- `limpiar trackers`
- `HOUSEKEEPING TRACKERS`
- o cuando entregue un reporte combinado de housekeeping

También activable en modo selectivo:
- `housekeeping trackers --bug-task-only`
- `housekeeping trackers --opportunities-only`
- `housekeeping trackers --changelog-only`

## Contrato de entrada

```yaml
scope: all | bug-task | opportunities | changelog   # default: all
force_refresh_gaps: true | false                     # default: true
skip_zero_gap: true                                  # no invocar hija si gap = 0
dry_run_matrix: false                                # modo planificación (vea sección específica)
```

## Flujo de ejecución propuesto (orden fijo de prioridad)

1. **Apertura**: `HOUSEKEEPING TRACKERS...`
2. **Clasificar alcance** según flags o según trackers con gaps detectados
3. **Presentar mapa de gaps unificado** al operador (tabla resumen, vea formato abajo)
4. **Ejecutar en este orden estricto** (solo los trackers con gap > 0):

   A. **Bug/Task Tracker primero** (prioridad CRÍTICO/ALTO)
      1. `vantage-tidy-bug-task-tracker`

   B. **VANTAGE Tracker después** (housekeeping de vacantes)
      2. `vantage-tidy-opportunities-tracker`

   C. **Change Log al final** (housekeeping documental)
      3. `vantage-tidy-changelog`

5. **Cada hija mantiene su propio Dry Run + APROBAR_WRITE independiente**.
   La meta-skill NO agrupa los APROBAR_WRITE; solo secuencia y reporta.
6. **Al final de cada hija**: capturar resumen (tickets archivados / duplicados marcados / entradas recortadas).
7. **Cierre unificado**: `TRACKERS HOUSEKEPT` + tabla resumen consolidada.

### Validación de gap reports

Cada hija valida su propio gap report internamente. La meta-skill NO coordina el timing de los reports — cada hija detecta sus propios gaps según su contrato.

### Manejo de error en hija interrumpida

- **Si una hija se detiene por ambigüedad** (ticket sin criterio claro, shape no definido, etc.): la meta-skill pausa y espera resolución antes de continuar al siguiente tracker.
- **Si el operador aborta la hija actual**: la meta-skill pregunta si desea continuar con los trackers restantes o abortar todo.
- **Si una hija falla por error inesperado** (no ambigüedad): la meta-skill captura el error y pregunta al operador si continuar con los trackers restantes o abortar todo.

### Skip de trackers con cero gap

Si `skip_zero_gap: true` (default) y una hija reporta gap = 0, esa hija se invoca pero termina inmediatamente con un "ya en sync" según su contrato interno. La meta-skill reporta este skip en la tabla final.

## Modo Dry Run Matrix

Si `dry_run_matrix: true`, la meta-skill presenta un plan de ejecución sin ejecutar nada:

```
TRACKERS HOUSEKEEPING PLAN
┌─────────────────────┬──────────┬────────────────┐
│ Tracker              │ Gap      │ Acción          │
├─────────────────────┼──────────┼────────────────┤
│ Bug/Task Tracker     │    5     │ Ejecutar (DRY)  │
│ VANTAGE Tracker      │    0     │ Skip            │
│ Change Log           │   12     │ Ejecutar (DRY)  │
└─────────────────────┴──────────┴────────────────┘
```

El operador puede entonces aprobar el plan antes de ejecutar las hijas reales.

## Entregable final (resumen consolidado)

```
TRACKERS HOUSEKEPT
┌────────────────────────────┬────────────┬──────────────────┐
│ Tracker                    │ Archivados│ Recortados       │
├────────────────────────────┼────────────┼──────────────────┤
│ Bug/Task Tracker           │     n      │        -         │
│ VANTAGE Tracker            │     n      │        -         │
│ Change Log                 │     -      │        n         │
└────────────────────────────┴────────────┴──────────────────┘
```

## Reglas de oro

- **Nunca reimplementar** la lógica de clasificación, criterios de archivado o recorte de las hijas.
- **Nunca fusionar** los APROBAR_WRITE. Cada tracker conserva su propio gate.
- Si una hija se detiene por ambigüedad, la meta-skill pausa y espera resolución antes de continuar al siguiente tracker.
- Si el operador cancela una hija, la meta-skill pregunta si desea continuar con los trackers restantes o abortar todo.
- Zero-gap en un tracker = skip silencioso de esa hija (reportar "ya en sync").
- La meta-skill no escribe Changelog ni Session Ledger por sí misma; eso sigue siendo responsabilidad de las hijas o del operador.
- La meta-skill no valida gaps report — cada hija valida su propio reporte según su contrato.

## No aplica a

- `vantage-housekeeping-archive` (archivado específico con sus propios guards)
- Skills de sincronización (vantage-sync-*)
- Skills de documentación transversal
- Cualquier escritura fuera de los tres trackers definidos (Bug/Task, VANTAGE, Change Log)

## Fuentes verificadas

Contratos de las tres skills hijas confirmados por lectura directa de sus archivos .md:
- `vantage-tidy-bug-task-tracker.md` (marcado tickets resueltos como Archivar=True)
- `vantage-tidy-opportunities-tracker.md` (marcado duplicados/expiradas como Archivar=True)
- `vantage-tidy-changelog.md` (recorte Change Log a últimas 10 entradas)

Orden de ejecución (Bug/Task → VANTAGE → Change Log) basado en prioridad operativa: tickets CRÍTICO/ALTO primero, housekeeping de vacantes después, documental al final.
