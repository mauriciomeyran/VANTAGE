---
name: vantage-sync-script-glossary
description: "Sincroniza el Script Glossary (Manual apéndice 22) contra el árbol de disco activo, usando el gap report de verify_versions.py --new-scripts. Usar cuando el operador pida \"sincronizar Script Glossary\" o similar, o cuando --new-scripts reporte gap > 0 entre árbol activo y Manual.md apéndice 22. No usar para Script Library (Notion, ver vantage-sync-script-library), CENSUS_SPEC (vantage-sync-census-spec) ni Skill Library (vantage-sync-skill-library) — es exclusivo del glosario narrativo en el Manual."
---

# VANTAGE — Script Glossary Sync

Mantiene el apéndice 22 del Manual (`MANUAL:SCRIPT-GLOSSARY-*`) sincronizado contra el árbol activo de scripts, usando `verify_versions.py --new-scripts` como fuente de gap detection.

## Spec source

- Estructura de secciones: Manual.md apéndice 22 (22.1/22.1a/22.1b/22.3/22.4/22.4a/22.5/22.6 — ver índice real, no asumir subsecciones que no existan).
- Matriz de estados: `MANUAL:SCRIPT-GLOSSARY-XREF` (22.6) — DOCUMENTADO es estado doble (Glosario + Script Library), transición nunca salta directo a DOCUMENTADO sin DRY RUN + `APROBAR_WRITE`.
- Patrón de tabla de transición (referencia de forma, no de contenido): `KERNEL:GATE-DECISION-011`.
- Ruta de verdad: `SCRIPT_GLOSSARY_PATH = PROJECT_ROOT / "Documentación" / "ACTIVE" / "Manual.md"` (confirmado — el glosario vive en el Manual, no en archivo separado).

## Contrato de entrada — 3 shapes según tipo de asset

Antes de redactar cualquier entrada nueva, clasificar el script/módulo detectado en uno de estos 3 shapes. No inventar campos fuera de este contrato — mantiene voz y densidad consistente con el resto del apéndice 22.

### Shape A — Script CLI con flags/args propios

```
<nombre_script.py>Qué hace: <resumen funcional en una línea, tono directo>
Flags:
| Flag | Caso de uso |
| --- | --- |
| <flag> | <escenario operativo concreto en 2ª persona — no descripción de parámetro, sino cuándo usarlo> |
```

- Si el script usa tokens posicionales en vez de flags reales (ej. `vdoc.py dry/notion/local/auto`), sustituir la tabla `Flags` por `Uso (tokens posicionales, no flags tradicionales):` con la misma forma de tabla (columna `Token` en vez de `Flag`).
- Si el script no tiene flags en absoluto (un solo modo de invocación), sustituir por `Uso: <una línea, qué se necesita y qué dispara>`.
- `Caso de uso:` como línea standalone opcional, solo si el "Qué hace" + flags no cubre un escenario operativo relevante que vale la pena nombrar aparte (patrón visto en `get_vantage_digest.sh`, `vprint.py`, `smoke_dashboard.py`).
- `⚠️ Nota real:` o `⚠️ Hallazgo real (no corregido, solo documentado):` — solo si hay discrepancia verificada entre código real y comportamiento esperado/documentado. Nunca inventar un hallazgo para llenar la plantilla; su ausencia es el estado normal.

### Shape B — Módulo sin CLI (se importa, no se ejecuta solo)

```
<nombre_modulo.py>Qué hace: <rol funcional>
Quién lo consume: <script(s) que lo importan>
Por qué existe: <opcional — solo si hay contexto de refactor/extracción que vale la pena preservar>
Por qué te sirve saberlo: <impacto operativo para el operador — qué síntoma explica este módulo si algo falla>
```

### Shape C — Wrapper Raycast (fila de tabla en 22.5, no bloque propio)

```
| <wrapper.sh> | <script real invocado> | <nota operativa — flags reenviados, limitaciones, o "Sin flags."> |
```

## Flujo de ejecución

1. Correr `verify_versions.py --new-scripts`, capturar el gap report completo (no resumir antes de revisarlo).
2. Si gap = 0: reportar y salir — no-op, no tocar el Manual.
3. Si gap > 0: clasificar cada script/módulo nuevo en Shape A/B/C (ver contrato arriba). Nunca asumir Shape A por default — un módulo importado sin CLI documentado como Shape A introduce una tabla de flags vacía o inventada, lo cual viola `MANUAL:PATCH-QUALITY-001` (invisibilidad estructural).
4. Generar DRY RUN: contenido completo de cada entrada nueva, en la subsección 22.x correcta según capa (L1/L3/L4/Dashboard/Raycast) — nunca como adendum al final del apéndice.
5. Presentar DRY RUN al operador.
6. `APROBAR_WRITE` (tokens válidos: `APROBAR_WRITE`, `APROBAR`, `SÍ`, `sí`, `YEP`, `yep`) → escribir en Manual.md vía Notion MCP (`update_content`, nunca `replace_content` sobre el apéndice completo — diff mínimo).
7. Write-Back Verification: re-fetch de la subsección modificada, comparar contra el DRY RUN aprobado.
8. Si el script también carece de fila en Script Library (Notion): señalar el gap y ofrecer invocar `vantage-sync-script-library` — este skill no escribe ahí directamente (separación de dominios, ver `no_aplica_a`).
9. Changelog entry solo si el volumen del lote lo amerita (criterio operador) — el enriquecimiento de glosario por sí solo no es alta de ID canónico, no dispara `KERNEL:CENSUS-SYNC` Regla 1 salvo que se haya creado un nuevo `MANUAL:SCRIPT-GLOSSARY-*` ID de subsección.

## No aplica a

- `CENSUS_SPEC` (estructura interna de `generate_census.py`) — ver `vantage-sync-census-spec`.
- `SCRIPT LIBRARY` (base Notion, property `Descripción` sin flags estructurados) — ver `vantage-sync-script-library`.
- `SKILL LIBRARY` — ver `vantage-sync-skill-library`.

## Reglas de oro

- Documentar discrepancias, no arreglarlas sin instrucción explícita (política heredada de 22.6, hallazgos arena.ia).
- Diff mínimo — nunca reescribir una subsección completa para agregar una entrada.
- Si un script no encaja limpiamente en ninguno de los 3 shapes, detener y preguntar al operador antes de forzarlo en el shape más cercano.
