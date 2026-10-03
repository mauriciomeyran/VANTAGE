# CENSUS_SPEC — resolución del drift KERNEL v10.3

**Fecha:** 2026-10-03 · **Rama:** `arena/01a103c4-vantage` · **Estado:** aplicado en repo (sin escritura a Notion)
**Alcance:** `Layer_1/scripts/generate_census.py`, `Layer_1/scripts/reorder_census_spec.py`, `Layer_1/data/V_ID_CENSUS_PRODUCTION.md`, `tests/test_generate_census.py`

## 1. Síntoma reportado

Corrida `vcensus` del 2026-10-03 15:51 → `385 IDs en spec / 341 resueltos / 44 SIN link / 0 huérfanos / 40 con sección hardcodeada`.

Los 44 "sin link" y los 40 "hardcodeada" son **el mismo problema**: 84 filas del bloque KERNEL del `CENSUS_SPEC` que ya no existen en el KERNEL vivo.

## 2. Causa raíz

El KERNEL fue re-keyed a la gramática v10.3 (`KERNEL:NAM-ID-GRAMMAR` §12.5: slug semántico, **prohibido el relleno numérico `-001`**). El `CENSUS_SPEC` conservó el listado legacy v9 al final de su bloque KERNEL (líneas 213–296 de `generate_census.py`): `DOCUMENTATION-nnn`, `SCHEMA-00n`, `GATE-DECISION-nnn`, `TRIGGER-00n`, `CV-GOLDEN-RULES-nnn`, `CV-PIPELINE-nnn`, `OWNERSHIP-*`, `DATA-FLOW-*`, etc.

Esas 84 filas no son "falsos negativos del matcher" (no es un bug de extracción): **los IDs no existen en los documentos vivos**.

| KERNEL vivo (espejo `Documentación/ACTIVE/Kernel.md`) | CENSUS_SPEC (antes) |
|---|---|
| 97 headings con ID canónico | 181 filas = 97 vivas + **84 legacy** |
| — | 0 headings vivos ausentes del spec (huérfanos = 0) |

De las 84 filas legacy:

- **44** no aparecen en ningún documento → son los "IDs SIN link" de cada corrida.
- **40** sobreviven solo como **cita en prosa** dentro de MANUAL, System Prompt, Career Canon, Aliases y Charter. El census las "resolvía" enlazando al párrafo que las menciona (sin heading) → de ahí el warning "sección hardcodeada sin verificar". Es decir: el reporte estaba señalando **citas colgantes reales en los documentos**, no un defecto del census.

Dato adicional de calidad del bloque legacy: sus `nombre` no coinciden ni con el KERNEL v9 ni con el v10.3. Ejemplo: `KERNEL:TRIGGER-001` figura como *"Trigger — Discovery Request"* cuando el v9 y el v10.3 dicen **FEED** / `KERNEL:TRG-FEED`; `KERNEL:SCHEMA-003` figura como *"Schema — Field Validation Rules"* cuando el contenido real es *"Fuente como Campo Especial"*. Dos de sus filas (`FAIL-PHILOSOPHY-001 Fail-Fast vs Fail-Safe`, `FAIL-PHILOSOPHY-002 Recovery Strategies`) describen secciones que **nunca existieron** en ninguna versión. Es un bloque escrito a mano, con drift propio — retirarlo no pierde información.

Alineación de gobernanza: `CHARTER:DECISIONS-012` (re-key v10.3 con *"puente de alias de vigencia un ciclo de release... Descartado: mantener numeración legacy con alias permanente"*), en HOLD, y el ticket abierto *"[CHARTER] Actualizar citas KERNEL del Charter por re-key v10.3"*. El Census es documento derivado: su fuente de verdad son los IDs reales de los otros documentos.

## 3. Fix aplicado

1. `Layer_1/scripts/reorder_census_spec.py` — nuevo flag **opt-in `--drop-dead`**: retira filas cuyo ID (o cualquiera de sus `lookup_ids`) no tiene **ninguna** definición en el documento espejo, y las lista antes de escribir. Sin el flag el comportamiento es idéntico al anterior.
2. `Layer_1/scripts/generate_census.py` — retiradas las **84 filas** del bloque KERNEL legacy (385 → **301** filas). Diff: 84 líneas, todas dentro de `CENSUS_SPEC`. `py_compile` OK.
3. `Layer_1/scripts/generate_census.py` — `KNOWN_RETIRED_NOISE` ampliado con 8 keys legacy más (`KERNEL:CV-GOLDEN-RULES`, `-001`..`-006`, `KERNEL:GATE-DECISION-010`): aparecen como *celda suelta* en tablas índice del MANUAL y el matcher las tomaría por definiciones nuevas al retirarlas del spec (habrían aparecido como 8 huérfanos falsos, invitando a re-insertarlas).
4. `Layer_1/scripts/generate_census.py` — `extract_live_section()` normaliza el número a la forma canónica del spec (`1.` → `01`, `2.1` intacto). Antes el markdown publicado guardaba `1.` mientras el spec guardaba `01`: las dos representaciones divergían en cada corrida viva (es la razón por la que el test md↔spec llevaba tiempo en rojo).
5. `Layer_1/data/V_ID_CENSUS_PRODUCTION.md` — regenerado con `--md-file` (conserva los links de Notion ya resueltos; quedan 301 filas).
6. `tests/test_generate_census.py` — expectativas stale actualizadas (294 → 301 en dos asserts; la inversión `CV-PIPELINE 12.3→12.1` desaparece; queda solo la de §22 del MANUAL) y 3 tests nuevos/ampliados: anclaje vivo de cada fila, `--drop-dead`, normalización de sección.

Comandos ejecutados (offline, sin red):

```bash
python3 Layer_1/scripts/reorder_census_spec.py --dry-run --drop-dead        # reporte previo
python3 Layer_1/scripts/reorder_census_spec.py --drop-dead \
    --md-file Layer_1/data/V_ID_CENSUS_PRODUCTION.md                        # aplica
python3 -m py_compile Layer_1/scripts/generate_census.py
```

## 4. Verificación

Simulación del pipeline de resolución del census (mismos helpers de `generate_census.py` contra los 9 espejos de `Documentación/ACTIVE/`) — reproduce bit a bit el reporte del operador antes del fix, y queda limpia después:

| | Antes | Después |
|---|---|---|
| IDs en spec | 385 | **301** |
| Resueltos con sección viva | 301 | **301** |
| Resueltos solo por mención (hardcoded) | 40 | **0** |
| Sin link | 44 | **0** |
| Huérfanos | 0 | **0** |

`tests/test_generate_census.py`: de **23 passed / 3 failed** a **28 passed**.
(Los 16 fallos de `tests/test_layer4_*` son pre-existentes y ajenos a este cambio — verificados también con el árbol sin modificar.)

## 5. Pendiente — corrida viva (tu máquina)

1. `vcensus --sync-to-notion --yes` → debería reportar **301 / 301 / 0 / 0**. El markdown commiteado ya coincide con lo que renderiza la corrida viva, así que el diff esperado en `V_ID_CENSUS_PRODUCTION.md` es **nulo** (si aparece alguno, es señal de que Notion cambió desde el último sync del espejo).
2. Regenerar `Layer_1/data/V_ID_CENSUS_PRODUCTION.pdf` (quedó con las 84 filas viejas).
3. Cerrar el ticket de citas (abajo): 40 keys legacy siguen citados en 72 ubicaciones de MANUAL / System Prompt / Career Canon / Aliases / Charter (una más — Manual.md:1368 — termina en ":" y solo la resuelve el tokenizador del census).

## 6. Mapa legacy → v10.3 (solo los 40 retirados que están citados)

Destino propuesto con evidencia (título idéntico o contenido equivalente ya verificado contra el Kernel vivo). Los 44 restantes no están citados en ningún documento y no requieren mapa.

| Key legacy | Ubicaciones de la cita | Destino v10.3 | Evidencia |
|---|---|---|---|
| `KERNEL:FAIL-PHILOSOPHY` | Manual.md:97 | `02 KERNEL:INVARIANTS` + `02.2/02.3/02.4 INV-FAIL-*` | contenido = naturaleza/comportamiento del fallo |
| `KERNEL:DOCUMENTATION-001` | Manual.md:282, 811 | `12.1 KERNEL:NAM-ID-CONTRACT` | título idéntico |
| `KERNEL:DOCUMENTATION-004` | Manual.md:259 | `14.1 KERNEL:OPS-BOOT` | *L0-Bootstrap — Dynamic Governance Layer* |
| `KERNEL:DOCUMENTATION-005` | Manual.md:1368 | `14.10 KERNEL:OPS-ANNOUNCE` | *Convención de Anuncio de Skills* |
| `KERNEL:DOCUMENTATION-007` | System Prompt.md:240 | `14.3 KERNEL:OPS-VERSIONS` | *Verificación de Versión* |
| `KERNEL:DOCUMENTATION-009` | System Prompt.md:23 | `14.5 KERNEL:OPS-LEDGER` | *Session Ledger* |
| `KERNEL:DOCUMENTATION-010` | System Prompt.md:233 | `14.11 KERNEL:OPS-DOCPROTOCOL` | *Documentación Transversal* |
| `KERNEL:DOCUMENTATION-012` | Manual.md:603, System Prompt.md:236 | `14.7 KERNEL:OPS-EXTCONFIG` | *External Configuration Contract* |
| `KERNEL:HANDOFF-SERIAL` | System Prompt.md:52, Aliases.md:58 | `14.12 KERNEL:OPS-SERIAL` | título idéntico |
| `KERNEL:ARCHITECTURE-L4` | Manual.md:389, 697, 699, 865, 1314 · System Prompt.md:27 | `04.5 KERNEL:ARC-L4` | título idéntico |
| `KERNEL:SCHEMA-001` | Manual.md:773, 886 | `05.1 KERNEL:SCH-OWNERSHIP` | v9 07.1 *Class A vs Class B* |
| `KERNEL:SCHEMA-002` | Manual.md:313, 316 | `05.2 KERNEL:SCH-INGEST` | v9 07.2 *Restricción del Sistema* |
| `KERNEL:SCHEMA-003` | Manual.md:893 | `05.3 KERNEL:SCH-SOURCE` | *Fuente como Campo Especial* |
| `KERNEL:SCHEMA-008` | Manual.md:892, 988, 1118 · System Prompt.md:195 | `05.8 KERNEL:SCH-NEXTACTION-VALUES` | título idéntico |
| `KERNEL:GATE-DECISION` | Manual.md:785 | `06 KERNEL:GATE` | nodo raíz |
| `KERNEL:GATE-DECISION-002` | Manual.md:894 | `06.2 KERNEL:GATE-LOGIC` | *Lógica Estándar* |
| `KERNEL:GATE-DECISION-003` | Manual.md:1158 | `06.3 KERNEL:GATE-REVIEW` | *Resolución de REVIEW_NEEDED* |
| `KERNEL:GATE-DECISION-005` | Manual.md:318 | `06.5 KERNEL:GATE-BLOCKED` | *Flujo de Recuperación BLOCKED* |
| `KERNEL:GATE-DECISION-007` | Manual.md:1338 | `06.7 KERNEL:GATE-ARCHIVE-MARK` | archivado manual / `auto_archive.py` deprecado |
| `KERNEL:GATE-DECISION-009` | Manual.md:283, 286 | `06.9 KERNEL:GATE-ESCALATION` | *Escalamiento de Pendientes a Tickets* |
| `KERNEL:GATE-DECISION-010` | Manual.md:317, 1155 | `06.10 KERNEL:GATE-TERMINAL` | Terminal State Protection (`gate_logic.py`) |
| `KERNEL:GATE-DECISION-011` | Manual.md:318, 321, 1286 | `06.11 KERNEL:GATE-TRANSITIONS` | *Matriz de Transición de Estados* |
| `KERNEL:DEDUP-LAYER-UPGRADE` | Manual.md:609, 918 · PROJECT_CHARTER.md:356 | `06.12 KERNEL:GATE-MUTABILITY` | *Guard de Mutación en Existentes* |
| `KERNEL:GATE-DECISION-013` | Manual.md:614, 967, 1341 | `06.13 KERNEL:GATE-ARCHIVE-AUDIT` | *Auditoría de Archivado en Tiempo Real* |
| `KERNEL:CV-GOLDEN-RULES` | Manual.md:319, 783, 822, 830, 840 · System Prompt.md:187 | `11 KERNEL:CVR` | *CV Golden Rules* |
| `KERNEL:CV-GOLDEN-RULES-001..006` | Manual.md:833–838 (índice §18) · PROJECT_CHARTER.md:351 (solo `-002`) | `11.1–11.6 CVR-NOFIT / NOCLASSB / NODATAQUALITY / NODELEGATE / NOSYNC / GATE-INVARIANCE` | los títulos del índice §18 coinciden 1:1 con los headings vivos |
| `KERNEL:TRIGGER-001` | Manual.md:316 | `07.1 KERNEL:TRG-FEED` | FEED |
| `KERNEL:TRIGGER-002` | Manual.md:554, 1046 | `07.2 KERNEL:TRG-VL1` | VL1 + `priority_logic.py` |
| `KERNEL:TRIGGER-003` | Manual.md:514 | `07.3 KERNEL:TRG-QA` | QA (checklist 7 ítems) |
| `KERNEL:CV-PIPELINE-001` | Manual.md:467, 852 · Career Canon.md:618 | `09.1 KERNEL:CVP-CVA` | el algoritmo N1–N4 vive en 09.1 |
| `KERNEL:CV-PIPELINE-003` | Manual.md:463, 927 | `09.3 KERNEL:CVP-BATCH` | batch/scaffold mecánico |
| `KERNEL:CONTEXT-INFRASTRUCTURE` | System Prompt.md:168 | `08.3 KERNEL:FLOW-CONTEXT-ECONOMY` / `08.4 FLOW-CONTEXT-ROUTING` | *revisar* cuál aplica por contexto |
| `KERNEL:CONTEXT-INFRASTRUCTURE-002` | Manual.md:798 | `08.4 KERNEL:FLOW-CONTEXT-ROUTING` | integration points → routing |
| `KERNEL:DATA-FLOW` | Manual.md:1298 · System Prompt.md:172 | `08 KERNEL:FLOW` | título idéntico |
| `KERNEL:DATA-FLOW-001` | Manual.md:537, 968 | `08.2 KERNEL:FLOW-WRITE-RISK` | *Contrato de Niveles de Riesgo de Escritura — Terminal* |

Relacionado: el Charter ya trata `KERNEL:GATE-DECISION-012` como referencia huérfana no operativa (no está en el spec; su reemplazo vigente es `KERNEL:DEDUP-LAYER-UPGRADE` en la nota del propio Charter → ahora `06.12 GATE-MUTABILITY`).

## 7. Anexo A — las 84 filas retiradas

44 sin ninguna cita (retiro directo, sin efecto en documentos):

```
KERNEL:PURPOSE-001, KERNEL:FAIL-PHILOSOPHY-001, KERNEL:FAIL-PHILOSOPHY-002,
KERNEL:DOCUMENTATION, KERNEL:DOCUMENTATION-002, KERNEL:DOCUMENTATION-003,
KERNEL:DOCUMENTATION-006, KERNEL:DOCUMENTATION-008, KERNEL:DOCUMENTATION-011,
KERNEL:DOCUMENTATION-013, KERNEL:DOCUMENTATION-014, KERNEL:DOCUMENTATION-015,
KERNEL:DOCUMENTATION-016, KERNEL:DOCUMENTATION-017, KERNEL:DOC-CONTRACT,
KERNEL:ARCHITECTURE-L1, KERNEL:ARCHITECTURE-L2, KERNEL:ARCHITECTURE-L3,
KERNEL:OWNERSHIP, KERNEL:OWNERSHIP-001, KERNEL:OWNERSHIP-002,
KERNEL:DASHBOARD-CHECKLIST-ARCH, KERNEL:SCHEMA-004, KERNEL:SCHEMA-005,
KERNEL:SCHEMA-006, KERNEL:SCHEMA-007, KERNEL:SCHEMA-009,
KERNEL:TRACKER-SCHEMA, KERNEL:TRACKER-SCHEMA-001, KERNEL:TRACKER-SCHEMA-002,
KERNEL:GATE-DECISION-001, KERNEL:GATE-DECISION-004, KERNEL:GATE-DECISION-006,
KERNEL:GATE-DECISION-008, KERNEL:TRIGGER-004, KERNEL:TRIGGER-005,
KERNEL:TRIGGER-006, KERNEL:TRIGGER-007, KERNEL:TRIGGER-008, KERNEL:TRIGGER-009,
KERNEL:CV-PIPELINE, KERNEL:CV-PIPELINE-002, KERNEL:NAMING-CONVENTION,
KERNEL:CONTEXT-INFRASTRUCTURE-001
```

(Nota: varios de ellos tienen equivalente vivo — p. ej. `ARCHITECTURE-L1/L2/L3` → `ARC-L1/L2/L3`, `OWNERSHIP-001/-002` → `ACT-AI/ACT-PY`, `DOC-CONTRACT` → `NAM-DOC-CONTRACT`, `GATE-DECISION-006` → `GATE-REJECTED` — y ya están en el spec con su key v10.3; no se pierden.)

Los otros 40 están en la tabla de §6 (citados en 72 ubicaciones).

## 8. Anexo B — backup y reversión

- Backup pre-fix: `/tmp/census/generate_census.py.bak` y `/tmp/census/V_ID_CENSUS_PRODUCTION.md.bak` (temporales, no versionados).
- Reversión: `git revert` del commit de esta rama.
- Herramienta idempotente: volver a correr `reorder_census_spec.py --drop-dead` sobre el spec ya limpio reporta `0` retiradas (no hay filas muertas).
