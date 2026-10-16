# Auditorías del subsistema

Aquí van los informes del skill **bug-hunter** (`scan_report.json` / `.html` / `.md`) y sus
versiones en texto. La razón de que vivan dentro del subsistema y no en `handoffs/` de la raíz
es que auditan **este** código: así viajan en el mismo commit que lo que describen y se
encuentran al lado.

## Convención de nombres

```
auditorias/
  AUDITORIA_<subsistema>_<AAAA-MM-DD>[_rN].md      informe legible
  AUDITORIA_<subsistema>_<AAAA-MM-DD>[_rN].json    scan_report.json del skill
  AUDITORIA_<subsistema>_<AAAA-MM-DD>[_rN].html    versión HTML (si el skill la genera)
```

- `<subsistema>` en minúsculas (`busqueda` para este).
- `_rN` solo si hay más de una pasada el mismo día (`_r2`).
- En la cabecera del informe, anotar el **commit base** auditado: es lo que permite saber si
  un hallazgo sigue vivo o ya se corrigió. Las dos pasadas de este subsistema se hicieron
  sobre `5f6acf5` y `2f7b923`.

## Pasadas registradas

| Fecha | Commit base | Resultado |
| --- | --- | --- |
| 2026-10-15 | `5f6acf5` | 18 hallazgos (9 CONFIRMED / 5 POTENTIAL / 4 INFO). Entrega inline, sin archivo |
| 2026-10-15 | `2f7b923` | Verificación de los 18 + 9 nuevos (BH2-001…BH2-009) |

Los triajes están resumidos en
[`../handoffs/BUSQUEDA_TORRENTS_MULTIMOTOR_2026-10-14.md`](../handoffs/BUSQUEDA_TORRENTS_MULTIMOTOR_2026-10-14.md),
secciones 5 y 6.

## Nota para el skill

Si el skill escribe el informe, la ruta a usar es esta carpeta con el nombre de la tabla de
arriba. Si no puede escribir en disco (modo sólo lectura), la entrega inline se archiva aquí a
mano después, con el mismo nombre.
