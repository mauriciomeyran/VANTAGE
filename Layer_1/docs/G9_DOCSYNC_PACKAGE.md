# G9 — Paquete docsync (diffs listos; Notion aplica Claude)

**Gate:** G9 · **Fecha:** 2026-09-12 · **Versión documental:** v9.22.0  
**Quién aplica a Notion:** Claude + `APROBAR_WRITE` nodo a nodo  
**Quién NO escribe Notion en la sesión de código:** Arena/Devin (solo mirror repo)

## Condición Q-4

| Antes | Después G9 |
|---|---|
| NO implementar Class-B-block-en-REVIEW **si** G9 deroga GATE-DECISION-010 | **Derogado** en `KERNEL:GATE-DECISION-010` v9.22.0 |
| Sin derogación = gate rojo | Condición **satisfecha** · `handoffs/PREGUNTAS_ABIERTAS.md` Q-4 CERRADA |

## Archivos tocados (repo mirror)

| Path | Cambio |
|---|---|
| `Documentación/ACTIVE/Kernel.md` | §§05.2, 04 dedup, 07.1, 07.7–07.8, 09.2–09.3, **09.10 derogación**, 09.13 |
| `Documentación/ACTIVE/Manual.md` | §22.1 orchestrator, 22.1a tracker_flow/gate_logic, batch retired, NA ES |
| `Documentación/ACTIVE/Aliases.md` | vl1→orch; vl1batch retired; vl1s; dedup |
| `Documentación/ACTIVE/Change Log.md` | entrada **v9.22.0** formato vigente (tope) |
| `skills/- Tidy/vantage-tidy-opportunities-tracker/SKILL.md` | SSOT is_mutable; nota G9 |
| `handoffs/PREGUNTAS_ABIERTAS.md` | Q-4 cerrada |

## Nodos Kernel a inyectar (Claude)

Orden sugerido de APROBAR_WRITE:

1. `KERNEL:SCHEMA-001` (Status 12 + Source_Type note)
2. `KERNEL:SCHEMA-007` (Holding placeholder)
3. `KERNEL:SCHEMA-008` (Next_Action 9 ES)
4. `KERNEL:GATE-DECISION-002` / `003`
5. **`KERNEL:GATE-DECISION-010`** (bloque completo A/B/C + derogación Q-4) — crítico
6. `KERNEL:GATE-DECISION-013`
7. `KERNEL:OWNERSHIP-002`
8. Manual glosario L1 + Aliases vl1
9. tidy skill body
10. Changelog v9.22.0 + bump propiedad Versión si aplica

## Verificación offline (esta sesión)

```bash
rg -n "DEROGACIÓN PARCIAL|is_mutable|layer_1_orchestrator" Documentación/ACTIVE/Kernel.md | head
rg -n "v9.22.0|Q-4" Documentación/ACTIVE/Change\ Log.md handoffs/PREGUNTAS_ABIERTAS.md | head
.venv/bin/python Layer_1/scripts/g8_post_checklist.py --offline   # sigue 37 PASS
.venv/bin/python Layer_1/scripts/g9_docsync_verify.py             # exit 0
```

## Fuera de alcance G9

- Ejecutar cutover G8 en prod (sesión Mau/Claude con token).
- Census alta de IDs nuevos (no hay IDs nuevos — reescritura).
- G10 handoff serial + frase cierre.
