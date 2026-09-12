## Sanitización del repo (plan + hallazgo piloto real)

**Lo que encontré (no lo que supuse):**
- Escaneo menciones de todo `Layer_1/scripts/*.py` + `*.sh` fuera de Archive: **1 solo sin-mención: `vantage_reorder_palacio.py`** → candidato #1 a archivar (verificar + Evaluación de Impacto per `KERNEL:DOCUMENTATION-011`, luego mover).
- Tu "mapa de dependencias en Kernel": lo que existe en repo es el **contrato DOC-011** (toda baja/modificación con dependencias → Evaluación de Impacto con 6 preguntas + registro en Change Log) + Census de IDs. No hay un grafo archivo→archivo único en `Kernel.md`. Si tu mapa vive en Notion, pégamelo y lo cruzo; si no, el plan lo construye.
- El problema real no es código huérfano: es **duplicidad generacional** (`layer_1_run.py` vs `tracker_flow.py`, `Dashboard/layer_1_run_dash.py` duplicado) + **transitorios** (patches, `__pycache__`, backups en máquinas muertas) + **docs sin índice**.

**Plan (3 niveles de evidencia: entry-traced / referenced-only / unreferenced):**
1. **Declarar roots** (lo que sí ejecuta): dispatch `layer_1_pipeline.sh` + `Raycast/*.sh` + aliases (`vl1`, futuro `vl1s`) + skills. Trazar imports desde ahí = grafo vivo real. (Yo hago el piloto si quieres.)
2. **Bajas inmediatas:** `vantage_reorder_palacio.py` → Archive (con DOC-011); `__pycache__/` + `*.pyc` → gitignore si no están; patches T4 → `/tmp`, jamás al repo; backups → 1 path canónico local + gitignore.
3. **Duplicados (mapear, NO borrar aún):** `layer_1_run_dash.py` vs `layer_1_run.py`, `tracker_flow.py` vs monolito — documentar quién corre hoy (vl1=v7.5) y marcar el resto `SUPERSEDED|DUPLICATE|PENDING-T6` en un índice.
4. **Docs:** `handoffs/README.md` (serial→estado→vigente/obsoleto, 10 líneas); cerrar seriales T0–T5 como históricos; regla same-day vgit + transitorios con fecha de muerte.
5. **Gate:** cada baja con Evaluación de Impacto DOC-011 (6 preguntas) + entrada Change Log. Sin excepción: es lo que evita la próxima doble verificación.