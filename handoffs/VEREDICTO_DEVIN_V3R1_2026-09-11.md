# VEREDICTO V3R1 — Rama `devin/tracker-refactor-v3` @ `629c7b2`

**De:** auditoría Arena · **Para:** Mau (reenviar a Devin) · **Fecha:** 2026-09-11 · **Serial:** DEVIN-20260911-04
**Verificación independiente ejecutada:** fetch+SHA ✓ | merge-base=`467af9c8` (base fresca ✓) | `import tracker_flow` → OK | `pytest` → **24/24 reproducidos** (test por test idénticos al output pegado) | lectura íntegra de `tracker_flow.py` (946 líneas), tests (387), fixture, fake, handoff (271), trazabilidad (56).

## Veredicto: NO APROBADO para merge — se requiere V3.1 acotado (G1–G10)

**PROHIBIDO mergear esta rama a main:** contiene borrado de configs de producción (§A). Dos bloqueantes independientes (A: higiene, B: fail-open en datos reales) + R3 (citas inválidas → "resuelto" nulo per contrato). Dicho esto: **primer delivery runnable y testeado en 4 rondas** — el contrato de verificación funciona (detectó exactamente lo que debía: §§B/R3). V3.1 es fix-list acotada, no rediseño.

## Progreso real (no se re-abre)

Import limpio · 24/24 reproducidos · F5 typo ✓ · F8 Title Case ✓ · F10 enforcement (+`_original_invalid_status`, buen detalle) ✓ · F6 piernas + manual rule ✓ · F3 idempotencia por prefijo ✓ · F4 ambas shapes + diff tipado ✓ · F12 Contratado-primero + tiebreaks ✓ · `is_mutable` ordenado ✓ · `archive_gate` append ✓ · sin `input`/red/notion ✓ · fixture 15 filas ✓ · frases conformidad textuales ✓ · §0 transcript ✓ · Q-G1 ✓.

## Bloqueante A — Higiene de rama: commit barrió árbol sucio (merge = daño)

Realidad (`git diff 467af9c8..629c7b2`): **12 archivos, +4935/−284** vs C4 pegado (6 archivos, +1574, "Modificados: Ninguno") → **el diff C4 no corresponde a la rama** (stale, de estado local previo: 932/378 vs 945/386 reales). Contenido indebido: **BORRADOS** `Layer_1/config/alias_map.json` (263 líneas, datos producción) y `hard_blocks.json` (19) — nada en F1–F15 lo pide, `tracker_flow.py` ni los referencia; `src/profile_filter.py` con path roto (`../config/alias_map.json` inexistente); junk unrelated (2 HTML backups ~2650 líneas, `LAYER_1_INTEGRATION_ANALYSIS.md` scout-era). Fix G8: reconstruir commit con SOLO los 6 archivos declarados; restaurar configs; revertir `profile_filter.py`; re-pegar C4 desde la rama.

## Bloqueante B — Fail-open con datos reales: tests pasan sobre shapes fantasía

`normalize_record` lee `last_edited_by/time` de **dentro de `properties`** con shape inventado doblemente-anidado (`{"last_edited_by": {"last_edited_by": id}}`). La API real los expone en **raíz** como `{"object":"user","id":…}`. Tests + fixture usan el shape fantasía (fixture: 15 filas ✓ pero `last_edited` solo en properties, nada en raíz). Consecuencia con datos reales: `last_edited_by_id`/`time` ausentes → `_is_human_edit("")`=True pero `_was_edited_since_last_run("")`=False → `_was_touched_by_human`=**False** → protección manual **apagada en silencio** y todo auto-ejecuta. Fix G1: extraer de raíz con shape real (`last_edited_by.id`); migrar tests+fixture a shapes API reales; agregar test fail-closed (sin `last_edited_*` → tratar como humano/reciente, jamás auto-ejecutar).

## R3 — Trazabilidad: ~todas las citas apuntan a líneas que no contienen lo declarado

Verificadas contra `629c7b2` (`normalize_record`=127, `is_mutable`=287, `evaluate_transition`=522, `generate_propose_log`=612, `execute_transition_with_propose_log`=658, `evaluate_review_gate`=760, `diff_records`=806, `SURVIVOR_PRIORITY`=835, `DELETED_VALUE_MAPPINGS`=900): F1 :102-128→enums ✗ · F2 :284-304/:327-376/:379-387→is_mutable/Transition/matriz ✗ · F3 :173-226/:307-325→extract_value/matriz ✗ · F4 :484-509→matriz ✗ · F5 :52→`NEGOCIANDO`, RETIRADO≈59 ✗ (la cita del typo-fix apunta a otra línea) · F6/F7/F9/F10/F11/F12/F15: todas desplazadas 40–340 líneas ✗ · F9 :512-527 colisiona con `evaluate_transition`=522. Handoff y trazabilidad traen **dos sets inconsistentes** entre sí. Per contrato §2.3/R3: filas inválidas → declaraciones "resuelto" nulas. Fix G7: un solo set de citas, re-verificado contra bytes pusheados.

## Gaps acotados V3.1 (además de G1/G7/G8)

- **G2. F2 payload diverge aún:** `execute_transition` (ruta viva auto-execute) devuelve solo `{Status, Notas}` pisando Notas y omitiendo `Next_Action`; `archive_gate` appendea + incluye — y **nadie la llama** en la ruta viva. Fix: unificar payload (misma función o delegación) + test directo del payload.
- **G3. F11 field-block inexistente:** `is_mutable(record, actor)` sin parámetro `field`, sin set Class-B, `class_b_guard` sin usar — docstring y `test_f11` declaran "field-block AND" que no existe (claim-sin-contenido, 5ª ronda). Fix: implementar o diferir explícitamente con rationale; retirar claims falsos.
- **G4. F9e/F9d:** mapping `fetch_status{aggregator,…}→"Fetch"` mapea valores→nombre-de-propiedad (nonsense; se pedía valor→valor). "Rollback scripteado" sin script en la rama. Fix: mapping real o declarado paramétrico; script o defer explícito.
- **G5. F7 cableado muerto:** `evaluate_review_gate` llama evento `"review_transition"` inexistente en matriz → rama `allow_review` inalcanzable; nada invoca al gate (Class-B en `Por Revisar` sigue computable). Fix: cablear punto de inserción exacto o declarar wiring de fase implementación.
- **G6. F15 fake no espeja:** `pages_update` plano + docstring "espeja client.pages.update" (falso; `self.pages` es Dict — `fake.pages.update()` sería `dict.update` silenciosamente erróneo). Sin adaptador documentado. Fix: espejar cadena o documentar adaptador.
- **G9. Serial colisionado:** handoff+módulo reclaman `DEVIN-20260911-03` (es del pack). Re-emitir como `-05` (este veredicto tomó `-04`).
- **G10. Desviación menor:** PR no abierto por Devin (§A5/D). Abrirlo o declarar bloqueador (sin `gh`?); Mau decide.
- **Menores:** `print()`→logger en propose/dry-run · `is_valid` aún loggea dentro (R7 sigue abierto) · tiebreak `layer` higher-first contradice docstring "L1>L2>L3" (aclarar) · `test_f3_was_touched_by_human` tautológico (`isinstance(bool)`) · **cero tests directos** de `execute_transition_with_propose_log` (la función central) · mapa cobertura A5 ausente como mapa (solo docstring).

## Re-entrega V3.1

G1–G10, rama fresca o misma rama con commit de corrección LIMPIO (6 archivos + fixes, cero deleciones/junk), citas re-verificadas, C4 re-pegado desde rama, serial `-05`. Re-verificaré con el mismo protocolo (import + pytest + citas + diff). Frase de conformidad obligatoria. Nada a `main`, nada a Notion.
