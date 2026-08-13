# HANDOFF TERMINAL — Gap Report vivo + Saneamiento de disco (post-auditoría 2026-08-13)

**Para:** operador, en la Mac (`~/Documents/03 Projects/VANTAGE`)
**Fuente de verdad:** `AUDIT_SANEAMIENTO_ESTRUCTURAL.md` (repo root, commit e385253)
**Objetivo:** cerrar el "Límite declarado" del auditor: ejecutar la mitad Notion del gap report que el sandbox no pudo correr (sin token), y ejecutar los movimientos de disco del Tier A/Tier C con su verificación post-movimiento.

> ⚠️ **Nunca** pegues `NOTION_TOKEN` en un chat ni lo subas al repo. El token ya debe vivir en `Layer_1/config/layer_1.env` (gitignored, verificado en `.gitignore`). Este handoff no necesita exponerlo en ningún momento.

---

## PASO 0 — Preflight (30 segundos)

```bash
cd "$HOME/Documents/03 Projects/VANTAGE/Layer_1"
test -f config/layer_1.env && echo "ENV OK" || echo "FALTA config/layer_1.env"
grep -c "NOTION_TOKEN" config/layer_1.env   # debe imprimir ≥1 (sin mostrar el valor)
test -d .venv && echo "VENV OK"
```

Si `FALTA config/layer_1.env`, cópialo desde tu gestor de secretos o recréalo con las claves que ya usa el pipeline (mismo archivo que lee `feed_processor.py`). Sin token real, detente aquí.

## PASO 1 — Línea base del gap report (READ-ONLY, no escribe nada en Notion)

```bash
cd "$HOME/Documents/03 Projects/VANTAGE/Layer_1/scripts"
source ../.venv/bin/activate

# Gap report SCRIPT LIBRARY (86 assets esperados en disco)
python3 verify_versions.py --scripts | tee "$HOME/vantage_scripts_gap_$(date +%Y%m%d).txt"

# Gap report SKILL LIBRARY (25 .skill esperados en disco)
python3 verify_versions.py --skills | tee "$HOME/vantage_skills_gap_$(date +%Y%m%d).txt"
```

**Cómo leer el output contra las predicciones de la auditoría (Directiva 2):**

| Sección del reporte | Predicción a validar |
| --- | --- |
| `SIN REGISTRAR EN NOTION` | Scripts reales nuevos nunca registrados. Si aparecen los zombies Tier A, es porque su fila Notion nunca se dio de alta — Claude los manejará como "deprecado, no registrar" |
| `REGISTRADOS Y VIGENTES` | La mayoría; incluye los 6 zombies Tier A (aún en disco) |
| `EN NOTION COMO 'Activo' PERO NO EN DISCO` | Huérfanos esperados si sus filas siguen Activas: `auto_archive.py`, `vsync_doc_fast.py`, `apply_hyperlinks.py` (legacy), `vantage-assign.sh`. **Advertencia de corrupción**: títulos con `http://` incrustado no matchean contra disco y pueden aparecer aquí como falsos huérfanos |

Guarda los dos `.txt` — son la **evidencia de entrada** para el handoff de Claude (HANDOFF_CLAUDE_NOTION_SIDE.md). Pégalos en el chat con Claude cuando abras esa sesión.

## PASO 2 — Movimientos Tier A (solo tras confirmar que quieres ejecutar el Entregable 2)

Los 6 movimientos son `git mv` reversibles; la auditoría verificó **cero aristas de entrada** hacia estos archivos (nadie los importa ni ejecuta).

```bash
cd "$HOME/Documents/03 Projects/VANTAGE"

git mv Layer_1/scripts/backfill_next_action_select.py Archive/Legacy_Scripts/
git mv Layer_1/scripts/toggle_changelog_archive.py  Archive/Legacy_Scripts/
git mv Layer_1/scripts/backfill_archive_fingerprint.py Archive/Legacy_Scripts/
git mv Layer_4/scripts/patch_vsync_doc.py Archive/Legacy_Scripts/
git mv Layer_4/scripts/patch_vsync_doc.STATUS.md Archive/Legacy_Scripts/
git mv Layer_1/tools/patch_new_scripts.py Archive/Legacy_Scripts/
git mv Layer_1/scripts/extract_score_distribution.py Archive/Legacy_Scripts/
```

Opcional (Tier B2 — renombrado de naming mixto, requiere tu OK explícito):

```bash
git mv "Archive/Legacy_Scripts/DEPRECADO apply_hyperlinks.py" Archive/Legacy_Scripts/DEPRECATED_apply_hyperlinks.py
git mv "Archive/Legacy_Scripts/DEPRECADO vsync_doc_fast.py" Archive/Legacy_Scripts/DEPRECATED_vsync_doc_fast.py
```

## PASO 3 — Verificación post-movimiento (obligatoria)

```bash
cd "$HOME/Documents/03 Projects/VANTAGE/Layer_1/scripts"
source ../.venv/bin/activate

# Debe reportar 80 assets (86 − 6 movidos). Si no: hay un archivo fuera de lugar.
python3 verify_versions.py --scripts

# Glosario local: debe seguir 0 gaps (el Glosario §22 los documenta como "movidos" en el batch de Claude).
python3 verify_versions.py --new-scripts

git status --short
```

## PASO 4 — Tier C (artefactos de proceso) — GATEADO: ejecuta solo con confirmación

La auditoría prescribe tabla de decisión previa. Ejecuta este bloque **únicamente** después de que Claude haya presentado el DRY RUN de Tier C y tú hayas respondido `APROBAR_WRITE`:

```bash
cd "$HOME/Documents/03 Projects/VANTAGE"

# C1 — backups que esquivan *.bak del .gitignore
git rm Layer_1/scripts/feed_processor.py.bak2 \
       Layer_1/scripts/feed_processor.py.bak_prioridad \
       Layer_1/scripts/generate_census.py.bak_census010

# C2 — parches ya aplicados
git rm Layer_1/scripts/dedup_fix_verified.patch \
       Layer_1/scripts/fix_terminal_protection_layer_1_run.patch

# C3 — dumps de depuración
git rm Layer_1/scripts/bug_tracker_full.json \
       Layer_1/scripts/task_tracker_full.json \
       Layer_1/scripts/out/schema_full.json \
       Layer_1/scripts/out/schema_properties.json

# C6 — backup byte-idéntico del manifest
git rm "Documentación/ACTIVE/.vsync_manifest.json.backup"

# B5 — copia accidental duplicada
git rm Archive/Legacy_Scripts/dump_trackers.py.save
```

**C4 (stubs graph_v2/backlinks_v2 en `Layer_1/scripts/`) NO se retira aquí**: requiere primero el fix de `graph_layer.py` para leer de `Layer_1/data/` (Hallazgo F2 de la auditoría). Ese fix es de código + tests → ticket propio con Claude. Hasta entonces los stubs se quedan.

Opcional, mismo gate: ampliar `.gitignore` con `*.bak*` (patrón coherente con `EXCLUDED_DIR_SUBSTRINGS` de `verify_versions.py`).

## PASO 5 — Commit y push

```bash
cd "$HOME/Documents/03 Projects/VANTAGE"
git add -A
git commit -m "housekeeping: Tier A movimientos a Archive/Legacy_Scripts + retiro de artefactos Tier C (auditoría 2026-08-13)"
git push
```

Si prefieres el flujo canónico de VANTAGE, usa en su lugar `vgit` (wrapper `Layer_4/wrappers/git_sync_wrapper.sh`) — ten en cuenta que `git_sync.py` regenerará `skills/index.json` en la misma corrida (deseable, está en sync 25/25).

## PASO 6 — Cierre y entrega de evidencia

1. Pega el contenido de los dos `.txt` del PASO 1 (y el del PASO 3) en la sesión de Claude — son su input formal.
2. Confirma en chat: "Tier A ejecutado" / "Tier C ejecutado" (o lo que hayas corrido).
3. Si ejecutaste movimientos, el batch de Claude debe incluir la remediación documental acoplada (Script Library `Deprecado`/`Archivar` + Glosario §22) — **no cerrar la sesión sin eso** (regla de acoplamiento, Directiva 2 de la auditoría).

**Salida esperada de todo el flujo:** gap report vivo (PASO 1) → movimientos (PASO 2) → 80 assets (PASO 3) → retiro de artefactos (PASO 4) → commit (PASO 5) → remediación Notion (handoff de Claude) → entrada `[AUDIT]` en Change Log cerrando el pendiente v9.17.1.
