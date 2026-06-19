```

***

## ENTREGABLE 3 — KERNEL ACTUALIZADO

Cambios quirúrgicos — solo secciones que requieren corrección post-auditoría:

```markdown
## CAMBIOS KERNEL v8.4 — Post-Audit

### §2 ARQUITECTURA — Corrección nomenclatura (Auditoría FASE 0)

El sistema opera a través de cuatro capas no intercambiables:
L0 (Runtime/Observabilidad) + L1 (Active Recon) + L2 (Strategic Search) + L3 (Passive Intake).

> NOTA DE ABSTRACCIÓN: El Kernel describe 4 capas arquitectónicas (L0–L3).
> La Runtime Documentation describe los 5 componentes internos de L0
> (Entity Index, Resolver, Query, Context, Agent API).
> Ambos conteos son correctos en su nivel de abstracción — no son contradictorios.

### §2 ARQUITECTURA — Corrección dedup hierarchy

Jerarquía de dedup: **L1 > L2 > L3**

L0 (Runtime) **no es una capa de dedup**. Es una capa de observabilidad/lectura.
No aparece en la jerarquía de dedup. Cualquier referencia a "L1 > L2 > L3 > Runtime"
en documentos anteriores es incorrecta y debe ignorarse.

### §6 VANTAGE RUNTIME — Estado verificado (2026-06-16)

| Componente | Estado | Función |
|---|---|---|
| Entity Index v2 | **VERIFIED** | 465 entidades, 100% hash coverage, 0 orphans |
| Resolver Layer v1 | **VERIFIED** | Resolución determinista vía Registry. **NOTA: bug de paginación abierto (RID-02)** |
| Query Layer | **VERIFIED** | Operaciones in-memory sobre entity_index_v2.json |
| Context Layer | **VERIFIED** | Extracción propiedades + bloques desde Notion |
| Agent API | **VERIFIED** | 8 intents implementados. Handlers `show_archived_history`/`show_bugs` con endpoint pendiente de verificación |

**Pitfall operativo activo:**
- RID-02: Resolver no pagina `data_sources/query`. En Archivo Tracker (384+ entidades),
  entidades fuera de la primera página pueden devolver `not_found` incorrectamente.
  Estado: **Abierto**. Prioridad: Inmediata.

**Comando `sync` (implementado v8.4):**
`vantage.py sync` regenera `entity_index_v2.json` desde Notion en vivo.
Atomic write (`.tmp` → `os.replace`). Preserva index anterior si falla.
Invalidación de cache con `force_reload=True` post-sync.

### §6.2 Gobernanza del Registry

`resolver_registry_v2.json` estado actual: **OPERATIVO** (corregido 2026-06-16).
Los campos `status` y `resolution_contract.live_resolution` reflejan
implementación real. No existe advertencia "DESIGN_ONLY" válida.

### ELIMINACIÓN — Línea huérfana en header del Kernel

La línea "Runtime Length: Generado desde KERNEL (DEPRECATED)" en la
declaración de audiencia no tiene significado operativo. Debe ser eliminada.
```