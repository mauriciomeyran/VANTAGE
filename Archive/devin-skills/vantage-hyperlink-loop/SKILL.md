---
name: vantage-hyperlink-loop
description: Ciclo de integridad Navigation/Cross-Reference (Census -> Hyperlinks -> Sync).
---
VANTAGE: NAVIGATION LOOP

0. ANNOUNCE: REGENERATING NAVIGATION LOOP...
0.5. TIER-GATE: Si hay baja disponibilidad de tokens, activar **MODO DEGRADADO**.

1. CENSUS GATE (`vcensus`):
   Ejecutar `vcensus` en la raíz del repo. 
   **Audit stritcto:** Pegar resumen. 
   **STOP si:** `IDs SIN LINK`, `UNRESOLVED`, o `BROKEN`. 
   **Orphans:** Decidir `CENSUS_SPEC` o ignorar.

2. PERMISOS & HYPERLINKS (`vhyperlinks`):
   - **Unlock:** Ejecutar `vunlock` en terminal.
   - **Dry-Run:** `vhyperlinks`. 
   - **Apply:** `vhyperlinks --apply`.
   - **Lock:** Ejecutar `vlock` en terminal.

3. NOTION SYNC (`vdoc`):
   Ejecutar: `vdoc local`.
   **Validación:** Verificar vínculos clickeables en Notion (KERNEL/PIPELINE/TRACKER).

4. VERSION SYNC (`vversions`):
   Ejecutar: `vversions --sync`.
   **Gate Final:** Debe retornar `[VEREDICTO FINAL] PASS`.

REGLAS DE ORO:
- **No Auto-Link:** Prohibido linkear el V-ID en su propio encabezado.
- **Fail-Fast:** Sin Terminal = Modo Degradado inmediato. 
- **Task Logging:** Registrar `[TASK]` para normalización si `vcensus` detecta inconsistencias.

REPORT FORMAT:
```
NAVIGATION LOOP REPORT
Census: [IDs / Broken / Unresolved / Orphans]
Hyperlinks: [Links / Docs Modificados]
Sync: [Notion OK / Version PASS]
Status: NAVIGATION LOOP FINISHED
```
