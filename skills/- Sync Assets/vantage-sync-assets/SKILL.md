---
name: vantage-sync-assets
description: Orquesta la sincronización de los seis dominios de assets de VANTAGE (Script Library + Script Glossary + Skill Library + Skill Glossary + Census Spec + Hyperlinks) en un solo punto de entrada. Usar cuando el operador pida "sincronizar assets", "sync assets", "sincronizar libraries y glosarios", o cuando quiera ejecutar todas las syncs de scripts y skills en orden determinista. Soporta modo selectivo con flags (--scripts-only, --skills-only, --libraries-only, --glossaries-only, --census-only, --hyperlinks-only). Esta skill no reimplementa lógica de clasificación, shapes o schema de las skills hijas; solo secuencia y reporta. No aplica a Bug/Task Tracker ni escritura fuera de los seis dominios definidos.
---

# VANTAGE — Assets Sync Meta-Skill

Orquesta de forma determinista la sincronización de los seis dominios de assets (Script Library + Script Glossary + Skill Library + Skill Glossary + Census Spec + Hyperlinks), reutilizando las skills hijas sin duplicar lógica.

## Convención de anuncio (KERNEL:DOCUMENTATION-005)

- Apertura: `SYNCING ASSETS...`
- Por dominio: reutilizar la apertura/cierre de la hija correspondiente
- Cierre global: `ASSETS SYNCED`

## Skills hijas dependientes

Esta skill orquesta las siguientes skills en orden fijo:

1. `vantage-sync-script-library` → SCRIPT LIBRARY (Notion, `ea914544-338f-485e-ac1b-7f137a5c9cee`)
2. `vantage-sync-skill-library` → SKILL LIBRARY (Notion, `2f1938be-fc42-83c8-8972-07300201136d`)
3. `vantage-sync-script-glossary` → Script Glossary (Manual.md apéndice 22)
4. `vantage-sync-skill-glossary` → Skill Glossary (Manual.md apéndice 23)
5. `vantage-sync-census-spec` → Census Spec (CENSUS_SPEC interno de `generate_census.py`)
6. `vantage-hyperlink-loop` → Hyperlinks (Ciclo de integridad Navigation/Cross-Reference)

## Trigger / Activación

Activar cuando el operador diga cualquiera de:
- `sincronizar assets`
- `sync assets`
- `sincronizar libraries y glosarios`
- `SYNC ASSETS`
- o cuando entregue un gap report combinado / pida "todo lo de scripts y skills"

También activable en modo selectivo:
- `sync assets --scripts-only`
- `sync assets --skills-only`
- `sync assets --libraries-only`
- `sync assets --glossaries-only`
- `sync assets --census-only`
- `sync assets --hyperlinks-only`

## Contrato de entrada

```yaml
scope: all | scripts | skills | libraries | glossaries | census | hyperlinks   # default: all
force_refresh_gaps: true | false                         # default: true
skip_zero_gap: true                                      # no invocar hija si gap = 0
dry_run_matrix: false                                    # modo planificación (vea sección específica)
```

## Flujo de ejecución propuesto (orden fijo)

1. **Apertura**: `SYNCING ASSETS...`
2. **Clasificar alcance** según flags o según dominios con gaps detectados
3. **Presentar mapa de gaps unificado** al operador (tabla resumen, vea formato abajo)
4. **Ejecutar en este orden estricto** (solo los dominios con gap > 0):

   A. **Libraries primero** (fuente de verdad de inventario)
      1. `vantage-sync-script-library`
      2. `vantage-sync-skill-library`

   B. **Glossaries después** (narrativa que referencia el inventario)
      3. `vantage-sync-script-glossary`
      4. `vantage-sync-skill-glossary`

   C. **Census Spec** (actualización de estructura interna basada en docs)
      5. `vantage-sync-census-spec`

   D. **Hyperlinks** (integridad de navegación/cross-reference)
      6. `vantage-hyperlink-loop`

5. **Cada hija mantiene su propio Dry Run + APROBAR_WRITE independiente**.
   La meta-skill NO agrupa los APROBAR_WRITE; solo secuencia y reporta.
6. **Al final de cada hija**: capturar resumen (altas / correcciones / huérfanos pendientes).
7. **Cierre unificado**: `ASSETS SYNCED` + tabla resumen consolidada.

### Validación de gap reports

Cada hija valida su propio gap report internamente (≤ 5 min de antigüedad). La meta-skill NO coordina el timing de los reports — cada hija corre su `verify_versions.py` correspondiente según su contrato. Esto evita estados inconsistentes si el árbol de disco cambia entre los 6 reports.

### Manejo de error en hija interrumpida

- **Si una hija se detiene por ambigüedad** (huérfano mismatch, shape no claro, etc.): la meta-skill pausa y espera resolución antes de continuar al siguiente dominio.
- **Si el operador aborta la hija actual**: la meta-skill pregunta si desea continuar con los dominios restantes o abortar todo.
- **Si una hija falla por error inesperado** (no ambigüedad): la meta-skill captura el error y pregunta al operador si continuar con los dominios restantes o abortar todo.

### Skip de dominios con cero gap

Si `skip_zero_gap: true` (default) y una hija reporta gap = 0, esa hija se invoca pero termina inmediatamente con un "ya en sync" según su contrato interno. La meta-skill reporta este skip en la tabla final.

## Modo Dry Run Matrix

Si `dry_run_matrix: true`, la meta-skill presenta un plan de ejecución sin ejecutar nada:

```
ASSETS SYNC PLAN
┌─────────────────────┬──────────┬────────────────┐
│ Dominio              │ Gap      │ Acción          │
├─────────────────────┼──────────┼────────────────┤
│ Script Library       │    3     │ Ejecutar (DRY)  │
│ Skill Library        │    0     │ Skip            │
│ Script Glossary      │    2     │ Ejecutar (DRY)  │
│ Skill Glossary       │    0     │ Skip            │
│ Census Spec          │    1     │ Ejecutar (DRY)  │
│ Hyperlinks           │    0     │ Skip            │
└─────────────────────┴──────────┴────────────────┘
```

El operador puede entonces aprobar el plan antes de ejecutar las hijas reales.

## Entregable final (resumen consolidado)

```
ASSETS SYNCED
┌────────────────────────────┬────────┬────────────┬────────────────────┐
│ Dominio                    │ Altas  │ Correcciones│ Huérfanos pendientes│
├────────────────────────────┼────────┼────────────┼────────────────────┤
│ Script Library             │   n    │     n      │         n          │
│ Skill Library              │   n    │     n      │         n          │
│ Script Glossary (ap. 22)   │   n    │     n      │         n          │
│ Skill Glossary (ap. 23)    │   n    │     n      │         n          │
│ Census Spec                │   n    │     n      │         n          │
│ Hyperlinks                 │   n    │     n      │         n          │
└────────────────────────────┴────────┴────────────┴────────────────────┘
```

## Bootstrap de la meta-skill

La primera vez que se active `vantage-sync-assets`, es probable que ella misma no esté registrada en Skill Library/Glossary. En ese caso:

1. Ejecutar las 6 hijas normalmente
2. Al final, si la meta-skill carece de registro, ofrecer ejecutar `vantage-sync-skill-library` + `vantage-sync-skill-glossary` para autorregistrarse
3. Esto es un ciclo de una sola vez; posteriores syncs no lo requieren

Este ciclo es aceptable porque es un paso de bootstrap manual que no afecta la operación normal del sistema.

## Reglas de oro

- **Nunca reimplementar** la lógica de clasificación, shapes, schema o auto-link cleaning de las hijas.
- **Nunca fusionar** los APROBAR_WRITE. Cada dominio conserva su propio gate.
- Si una hija se detiene por ambigüedad, la meta-skill pausa y espera resolución antes de continuar al siguiente dominio.
- Si el operador cancela una hija, la meta-skill pregunta si desea continuar con los dominios restantes o abortar todo.
- Zero-gap en un dominio = skip silencioso de esa hija (reportar "ya en sync").
- La meta-skill no escribe Changelog ni Session Ledger por sí misma; eso sigue siendo responsabilidad de las hijas o del operador.
- La meta-skill no valida gaps report — cada hija valida su propio reporte según su contrato.

## No aplica a

- Bug/Task Tracker
- Cualquier escritura fuera de los seis dominios definidos (Script Library, Script Glossary, Skill Library, Skill Glossary, Census Spec, Hyperlinks)

## Fuentes verificadas

Contratos de las seis skills hijas confirmados por lectura directa de sus archivos .md (sesión 2026-08-13):
- `vantage-sync-script-library.md` (schema SCRIPT LIBRARY, bug auto-link `http://`, convención APROBAR_WRITE)
- `vantage-sync-script-glossary.md` (3 shapes A/B/C, estructura apéndice 22, separación de dominios)
- `vantage-sync-skill-library.md` (schema SKILL LIBRARY, protección auto-link en `Descripción`, extracción de frontmatter)
- `vantage-sync-skill-glossary.md` (shape único narrativo, estructura apéndice 23, flag `--new-skills`)
- `vantage-sync-census-spec.md` (CENSUS_SPEC interno de `generate_census.py`, Contrato de Cero Inferencia)
- `vantage-hyperlink-loop.md` (Ciclo de integridad Navigation/Cross-Reference, Census Gate → Permisos & Hyperlinks → Notion Sync → Version Sync)

Orden de ejecución (Libraries → Glossaries → Census Spec → Hyperlinks) basado en dependencia semántica: el inventario (Notion) es fuente de verdad, el glosario (Manual) es narrativa que referencia ese inventario, Census Spec actualiza estructura interna basada en docs, y Hyperlinks asegura integridad de navegación/cross-reference.
