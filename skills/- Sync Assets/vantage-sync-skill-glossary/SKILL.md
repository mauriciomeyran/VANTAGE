---
name: vantage-sync-skill-glossary
description: "Sincroniza el Glosario de Skills (Manual apéndice 23) contra el árbol de disco activo de archivos .skill, usando el gap report LOCAL de verify_versions.py --new-skills (no --skills, que compara contra Notion) y el drift report de --skills-drift (contenido modificado en un .skill ya documentado). Usar cuando el operador pida \"sincronizar Skill Glossary\" o similar, o cuando --new-skills reporte gap mayor a 0, o cuando --skills-drift reporte drift sin reconciliar. No usar para Skill Library (Notion, ver vantage-sync-skill-library), Script Glossary (vantage-sync-script-glossary) ni CENSUS_SPEC (vantage-sync-census-spec) — es exclusivo del glosario narrativo de skills en el Manual."
---

# VANTAGE — Skill Glossary Sync

Mantiene el apéndice 23 del Manual (`MANUAL:SKILL-GLOSSARY-*`) sincronizado contra el árbol activo de archivos `.skill`, usando `verify_versions.py --new-skills` (altas/bajas) y `verify_versions.py --skills-drift` (contenido modificado in-place) como fuentes de gap detection.

## Spec source

- Estructura de secciones: Manual.md apéndice 23 (23.1 Pipeline CV y Ciclo de Sesión / 23.2 Sincronización y Mantenimiento Documental / 23.3 Auditoría y Continuidad / 23.4 Estilos de Escritura y Generación / 23.5 Gaps Abiertos — ver índice real vía ID Census, no asumir subsecciones que no existan).
- A diferencia del apéndice 22 (scripts), el apéndice 23 no tiene matriz de estados dual documentada aún — tratar cualquier skill nueva como alta directa a la subsección temática correcta, salvo que el operador confirme que existe un estado equivalente a DOCUMENTADO pendiente de definir.
- Ruta de verdad: mismo `SCRIPT_GLOSSARY_PATH = PROJECT_ROOT / "Documentación" / "ACTIVE" / "Manual.md"` que usa Script Glossary (documento único, apéndice distinto — no hay constante separada, `--new-skills` reusa la misma ruta con extensión `.skill` y label propio).
- Requiere flag `--new-skills` en `verify_versions.py` (parche local aplicado — extiende `render_new_scripts_gap_report` con parámetro `label`, reusa lógica existente de `--new-scripts` sin tocar comportamiento previo).
- Requiere flag `--skills-drift` en `verify_versions.py` (parche local — ver KERNEL:DOCUMENTATION-009-adyacente; baseline de hashes por archivo en `skill_hash_baseline.json`, mismo patrón arquitectónico que `--length`/`length_baseline.json`). Read-only salvo `--update-skill-baseline`.
- Directorio fuente: `/mnt/skills/user/[skill-name]/SKILL.md` (árbol activo de disco).

## Por qué existen dos gap reports separados (no confundir)

- `--new-skills`: compara **presencia por nombre** — detecta `.skill` en disco sin entrada en el apéndice 23 (alta) o entrada en el apéndice sin `.skill` correspondiente (huérfano documental).
- `--skills-drift`: compara **hash de contenido** contra el último baseline confirmado — detecta un `.skill` cuyo nombre ya está documentado en el apéndice 23, pero cuyo contenido cambió desde el último sync (ej. una skill existente que el operador actualizó). Esto es invisible a `--new-skills`, que solo mira nombres.
- Ambos se corren en la misma sesión de sync — un gap = 0 en `--new-skills` NO implica que el apéndice 23 esté al día; puede haber drift sin reconciliar.

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
- Para una entrada existente con drift confirmado: mismo shape, actualización in-place de la entrada ya publicada (no se crea una segunda entrada ni se duplica el bloque).

## Flujo de ejecución

1. Correr `verify_versions.py --new-skills` (gap LOCAL contra Manual.md, altas/bajas por nombre) **y** `verify_versions.py --skills-drift` (gap LOCAL de contenido contra baseline) — capturar ambos reportes completos antes de revisar (no resumir antes de revisarlos).
2. Si `--new-skills` gap = 0 **y** `--skills-drift` reporta `PASS` (sin drift): reportar y salir — no-op, no tocar el Manual.
3. Altas (`--new-skills` gap > 0): para cada `.skill` sin entrada en apéndice 23, redactar el bloque según el shape único (ver contrato arriba), clasificando la subsección 23.1–23.4 correcta.
4. Actualizaciones (`--skills-drift` con drift sin reconciliar): para cada `.skill` marcado `⚠️ CONTENIDO MODIFICADO`, releer el `SKILL.md` actual completo desde disco y redactar la entrada actualizada según el mismo shape — comparar contra la entrada vigente en el apéndice para identificar qué cambió (no reescribir a ciegas si el cambio es cosmético y no afecta la prosa del glosario).
5. Generar DRY RUN: contenido completo de cada entrada nueva o actualizada, en la subsección correcta — nunca como adendum al final del apéndice.
6. Presentar DRY RUN al operador.
7. `APROBAR_WRITE` → escribir en Manual.md vía Notion MCP (`update_content`, diff mínimo — nunca `replace_content` sobre el apéndice completo).
8. Write-Back Verification: re-fetch de la subsección modificada, comparar contra el DRY RUN aprobado.
9. Si la skill también carece de fila en Skill Library (Notion) o su fila tiene body desactualizado: señalar el gap y ofrecer invocar `vantage-sync-skill-library` — este skill no escribe ahí directamente (separación de dominios, ver `no_aplica_a`).
10. Tras Write-Back Verification exitosa de altas y/o actualizaciones, correr `verify_versions.py --skills-drift --update-skill-baseline` para regrabar el hash de cada `.skill` reconciliado — sin este paso, el próximo `--skills-drift` seguirá reportando el mismo drift ya resuelto.
11. Changelog entry solo si el volumen del lote lo amerita (criterio operador) — el enriquecimiento de glosario por sí solo no es alta de ID canónico, salvo que se haya creado un nuevo `MANUAL:SKILL-GLOSSARY-*` ID de subsección.

## No aplica a

- `SKILL LIBRARY` (base Notion, inventario de archivos) — ver `vantage-sync-skill-library`.
- `SCRIPT GLOSSARY` (apéndice 22, shapes técnicos con flags) — ver `vantage-sync-script-glossary`.
- `CENSUS_SPEC` (estructura interna de `generate_census.py`) — ver `vantage-sync-census-spec`.

## Reglas de oro

- Documentar discrepancias, no arreglarlas sin instrucción explícita.
- Diff mínimo — nunca reescribir una subsección completa para agregar o actualizar una entrada.
- Si una skill no encaja limpiamente en 23.1–23.4, no forzarla — listar en 23.5 y preguntar al operador.
- Nunca correr `--update-skill-baseline` antes de la Write-Back Verification — el baseline solo se regrabra sobre drift ya reconciliado y confirmado en el documento live, nunca de forma preventiva.
