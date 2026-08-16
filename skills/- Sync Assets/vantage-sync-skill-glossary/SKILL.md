---
name: vantage-sync-skill-glossary
description: "Sincroniza el Glosario de Skills (Manual apéndice 23) contra el árbol de disco activo de archivos .skill, usando el gap report LOCAL de verify_versions.py --new-skills (no --skills, que compara contra Notion). Usar cuando el operador pida \"sincronizar Skill Glossary\" o similar, o cuando --new-skills reporte gap mayor a 0 entre árbol activo y Manual.md apéndice 23. No usar para Skill Library (Notion, ver vantage-sync-skill-library), Script Glossary (vantage-sync-script-glossary) ni CENSUS_SPEC (vantage-sync-census-spec) — es exclusivo del glosario narrativo de skills en el Manual."
---

# VANTAGE — Skill Glossary Sync

Mantiene el apéndice 23 del Manual (`MANUAL:SKILL-GLOSSARY-*`) sincronizado contra el árbol activo de archivos `.skill`, usando `verify_versions.py --skills` como fuente de gap detection.

## Spec source

- Estructura de secciones: Manual.md apéndice 23 (23.1 Pipeline CV y Ciclo de Sesión / 23.2 Sincronización y Mantenimiento Documental / 23.3 Auditoría y Continuidad / 23.4 Estilos de Escritura y Generación / 23.5 Gaps Abiertos — ver índice real vía ID Census, no asumir subsecciones que no existan).
- A diferencia del apéndice 22 (scripts), el apéndice 23 no tiene matriz de estados dual documentada aún — tratar cualquier skill nueva como alta directa a la subsección temática correcta, salvo que el operador confirme que existe un estado equivalente a DOCUMENTADO pendiente de definir.
- Ruta de verdad: mismo `SCRIPT_GLOSSARY_PATH = PROJECT_ROOT / "Documentación" / "ACTIVE" / "Manual.md"` que usa Script Glossary (documento único, apéndice distinto — no hay constante separada, `--new-skills` reusa la misma ruta con extensión `.skill` y label propio).
- Requiere flag `--new-skills` en `verify_versions.py` (parche local aplicado — extiende `render_new_scripts_gap_report` con parámetro `label`, reusa lógica existente de `--new-scripts` sin tocar comportamiento previo).
- Directorio fuente: `/mnt/skills/user/[skill-name]/SKILL.md` (árbol activo de disco).

## Contrato de entrada — shape único (glosario narrativo, no técnico)

A diferencia de Script Glossary (3 shapes técnicos con flags/tokens), el apéndice 23 es referencia humana en prosa. Cada entrada nueva sigue este shape:

```
<nombre-skill>Qué hace: <resumen funcional en una línea, tono directo>
Cuándo se activa: <trigger operativo — frase o contexto del operador que lo dispara>
Por qué te sirve saberlo: <impacto operativo — qué resuelve o qué evita>
```

- `Depende de:` — línea opcional, solo si la skill requiere otra skill como prerequisito (ej. vantage-cv-b depende de HANDOFF de vantage-cv-a).
- No inventar campos fuera de este contrato — mantiene voz y densidad consistente con el resto del apéndice 23.
- Clasificar la subsección temática correcta (23.1–23.4) según el propósito dominante de la skill; si no encaja claramente en ninguna, es candidata a listarse en 23.5 (Gaps Abiertos) hasta que el operador confirme dónde vive.

## Flujo de ejecución

1. Correr `verify_versions.py --new-skills` (gap LOCAL contra Manual.md — no confundir con `--skills`, que compara contra Notion Skill Library), capturar el gap report completo (no resumir antes de revisarlo).
2. Si gap = 0: reportar y salir — no-op, no tocar el Manual.
3. Si gap > 0: para cada `.skill` sin entrada en apéndice 23, redactar el bloque según el shape único (ver contrato arriba), clasificando la subsección 23.1–23.4 correcta.
4. Generar DRY RUN: contenido completo de cada entrada nueva, en la subsección correcta — nunca como adendum al final del apéndice.
5. Presentar DRY RUN al operador.
6. `APROBAR_WRITE` → escribir en Manual.md vía Notion MCP (`update_content`, diff mínimo — nunca `replace_content` sobre el apéndice completo).
7. Write-Back Verification: re-fetch de la subsección modificada, comparar contra el DRY RUN aprobado.
8. Si la skill también carece de fila en Skill Library (Notion): señalar el gap y ofrecer invocar `vantage-sync-skill-library` — este skill no escribe ahí directamente (separación de dominios, ver `no_aplica_a`).
9. Changelog entry solo si el volumen del lote lo amerita (criterio operador) — el enriquecimiento de glosario por sí solo no es alta de ID canónico, salvo que se haya creado un nuevo `MANUAL:SKILL-GLOSSARY-*` ID de subsección.

## No aplica a

- `SKILL LIBRARY` (base Notion, inventario de archivos) — ver `vantage-sync-skill-library`.
- `SCRIPT GLOSSARY` (apéndice 22, shapes técnicos con flags) — ver `vantage-sync-script-glossary`.
- `CENSUS_SPEC` (estructura interna de `generate_census.py`) — ver `vantage-sync-census-spec`.

## Reglas de oro

- Documentar discrepancias, no arreglarlas sin instrucción explícita.
- Diff mínimo — nunca reescribir una subsección completa para agregar una entrada.
- Si una skill no encaja limpiamente en 23.1–23.4, no forzarla — listar en 23.5 y preguntar al operador.