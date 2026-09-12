# G7 — Tabla de normalización Tracker (actual → normalizado)

**Gate:** G7 · **Fecha:** 2026-09-12 · **Código:** `tracker_flow.NORMALIZATION_TABLE`  
**Script:** `Layer_1/scripts/normalize_tracker_values.py` (dry-run default, `--apply` gateado)  
**Criterio (contrato §4-v1 / consolidado §6-G7):** ES operativo en VALORES; EN solo terminología técnica fijada (`Gate_Decision` SCREAMING). Un literal canónico por semántica (F8). Idempotente.

> Schema vivo (rename props / prune opciones select) = **G8** vía Claude/MCP + `APROBAR_WRITE`.  
> Este entregable es código + tabla + script; **cero writes a Notion prod**.

---

## 1. Next_Action

| actual (prod / legacy) | normalizado (canónico ES) | notas |
|---|---|---|
| `Follow-up` | `Seguimiento` | legacy EN vivo |
| `Interview prep` | `Preparación Entrevista` | legacy EN vivo |
| `Re-check` | `Revisión` | legacy EN vivo |
| `Ninguna` | *(vacío)* | huérfano sin productor |
| `Expirada` | `Archivar` | Next_Action=Expirada legacy (Status.Expirada ≠) |
| `Optimizar` | `Optimizar` | identity |
| `Seguimiento` | `Seguimiento` | identity (canónico) |
| `Preparación Entrevista` | `Preparación Entrevista` | identity |
| `Revisión` | `Revisión` | identity |
| `Investigar` | `Investigar` | identity |
| `Post-Mortem` | `Post-Mortem` | identity |
| `Archivar` | `Archivar` | identity (señal de archivo) |
| `Reparar URL` | `Reparar URL` | identity |
| `Verificar JD` | `Verificar JD` | identity |

**Writers post-G7** (`get_application_next_action`, `apply_gate_decision`): emiten solo canónico ES.  
Enum `NextAction` conserva miembros legacy EN **solo para lectura/migración** hasta prune de opciones en G8.

---

## 2. Gate_Decision

| actual | normalizado | notas |
|---|---|---|
| `CREATE` | `CREATE` | técnico EN fijado |
| `BLOCKED` | `BLOCKED` | |
| `REVIEW_NEEDED` | `REVIEW_NEEDED` | ≠ Status `Por Revisar` |
| `APPLIED` | `APPLIED` | |
| `REJECTED` | `REJECTED` | |
| `EXPIRED` | `EXPIRED` | enum canónico |
| `EXPIRADA` | `EXPIRED` | valor interno `gate_logic` / legacy |

---

## 3. Status (pruning + casing)

| actual | normalizado | notas |
|---|---|---|
| `Target` | `Objetivo` | Q-2 ya 0 filas en prod; mapa por idempotencia |
| `Archivar` | `Retirado` | huérfano bilateral → Retirado |
| `En proceso` | `En Proceso` | casing |
| `Sin respuesta` | `Sin Respuesta` | casing |
| `REVIEW_NEEDED` | `Por Revisar` | Status legacy SCREAMING → Title Case ES |
| *(resto enum Status)* | identity | ver `Status` en `tracker_flow.py` |

`Status=Archivar` (opción) vs checkbox `Archivar` vs `Next_Action=Archivar`: G7 deja **Next_Action=Archivar** como señal + checkbox ejecución manual (tidy); opción Status se poda vía mapa → Retirado. Prune de opción en schema = G8.

---

## 4. Holding (placeholders → vacío)

| actual | normalizado | notas |
|---|---|---|
| `Investigar` | *(vacío)* | placeholder ruido (Kernel 07.7); ≠ Next_Action.Investigar |
| `N/A` / `n/a` / `-` / `—` | *(vacío)* | |
| holdings reales (`Nike Inc.`, `LVMH`, …) | **no se tocan** | fuera de tabla = preserve |

---

## 5. Source_Type — rename de propiedad (plan G8)

| actual (nombre prop) | normalizado | notas |
|---|---|---|
| `Source_Type ` (trailing space) | `Source_Type` | Q-1; **G8 MCP rename** |
| valores `Vacante/Inbound/Referencia/Networking` | identity | |

Código dual-lee ambas claves (`SOURCE_TYPE_PROP_ALIASES`). El script G7 **no** renombra la propiedad en schema; reporta conteo de filas con key legacy vs clean.

---

## 6. Script — uso

```bash
cd Layer_1
# Fixture local (CI / sandbox — cero red):
python3 scripts/normalize_tracker_values.py --fixture ../tests/fixtures/g7_normalization_fixture.json

# Dry-run contra Notion (solo lectura vía proxy):
python3 scripts/normalize_tracker_values.py --dry-run

# Apply (gateado — NO en esta sesión de desarrollo):
python3 scripts/normalize_tracker_values.py --apply   # requiere NOTION_TOKEN

# Reanudable:
python3 scripts/normalize_tracker_values.py --fixture … --resume state/g7_normalize_state.json
```

**Idempotencia:** 2ª pasada sobre post-estado → `would_write=0`.  
**Pre/post:** el reporte imprime contadores por propiedad y valor.  
**class_b_guard:** todo payload de write pasa por guard; Class B de la allowlist de migración se re-admite explícitamente (integridad, no negocio arbitrario).

---

## 7. Dependencias de cutover (G8)

1. Export pre-migración (CSV/JSON) del Tracker.
2. Congelar ediciones manuales en ventana corta.
3. Correr script `--dry-run` → revisar pre/post.
4. Correr `--apply` (Claude/APROBAR_WRITE si MCP).
5. Rename schema `Source_Type␣` → `Source_Type` + prune opciones select legacy.
6. Quitar miembros legacy EN de `NextAction` enum (opcional post-prune).
7. Checklist radiografía §3.1.

Rollback: `DELETED_VALUE_MAPPINGS` + reverso de tabla (documentar en G8 plan); no auto-rollback en G7.
