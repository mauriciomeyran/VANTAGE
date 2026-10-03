# Validación de `generate_census.py` y scripts de Layer 4

**Fecha:** 2026-10-02 · **Alcance:** `Layer_1/scripts/generate_census.py`, `Layer_4/scripts/*.py`, `mcp_sync_wrapper.sh`, `wrappers/git_sync_wrapper.sh`, `scripts.zip`.
**Método:** análisis estático (`ruff 0.16.10`, `pyflakes 4.0.1`, `compileall`) + harness dinámico con dobles/mocks en `/tmp` (repos git simulados, `requests`/`notion`/`HTTP` simulados). **No se tocó Notion, ni el repo real, ni el Mac del operador.**
**Base:** commit local `c8ec5f6` (rama `arena/01a0fea2-vantage`), árbol limpio al iniciar.

---

## Veredicto

| Archivo | ¿Libre de bugs? | Hallazgos |
|---|---|---|
| `Layer_1/scripts/generate_census.py` | ❌ **No** | 5 funcionales (1 destructivo) + 3 menores |
| `Layer_4/scripts/git_sync.py` | ❌ **No** | 3 funcionales |
| `Layer_4/scripts/trigger_sync_after_mcp_write.py` | ❌ **No** | 1 crítico |
| `Layer_4/scripts/notion_write_wrapper.py` | ⚠️ **Stub** | 1 footgun (ya declarado experimental en README) |
| `Layer_4/scripts/vdoc.py` | ❌ **No** | 2 funcionales |
| `Layer_4/scripts/vsync_doc.py` | ⚠️ **Parcial** | 2 estructurales + 4 menores |
| `Layer_4/scripts/vdoc_nblm.py` | ❌ **No** | 1 crítico (rutas) |
| `Layer_4/scripts/vsum.py` | ⚠️ **Parcial** | 1 funcional |
| `Layer_4/scripts/mcp_sync_wrapper.sh` | ⚠️ | Hereda el bug crítico del trigger |

**Conclusión:** ninguno de los dos conjuntos estaba libre de bugs. Hay 2 hallazgos que pueden **perder estado** (census publicado vacío; sync post-MCP abortado) y 2 que producen **falsos positivos de éxito** (push a `main` desde otra rama; exit codes que siempre son 0).

Lo que sí quedó verificado como correcto: reintentos/429 en `fetch_blocks`, fronteras de IDs, `_decide()` de `vsync_doc`, el fix R-02 (crear-antes-de-borrar) y el fix V-06 (contar tablas no sincronizadas).

> **Estado (2026-10-02, misma rama):** los fixes A1–A6, A8, B1–B10, B11 (duplicación, `.zip`, rutas, versión de API, tabla idéntica) **ya están aplicados** en esta rama, con 48 tests de regresión en `tests/`. Quedan **pendientes de decisión** (no son bugs silenciosos): A7 (sección `CANON` dentro de `MANUAL` y si "Changelog Archivo" entra al censo) y el PATCH granular de tablas en `vsync_doc --direction local` (hoy: doc con tablas modificadas sigue bloqueando el manifest, por diseño V-06; si la tabla es idéntica ya no marca fallo). Ver sección 7.

---

## 1. `Layer_1/scripts/generate_census.py`

### 🔴 A1 — Borra toda la página antes de escribir: si falla el append, la página queda vacía

- **Dónde:** `update_notion_census_page()` L982-1017 (DELETE en L995-1000, append en L1004-1016).
- **Evidencia (harness):** página simulada con 3 bloques viejos y `PATCH` devolviendo 500 → se ejecutaron los 3 `DELETE` y la función devolvió `False` con la página **sin contenido**. No hay rollback ni backup.
- **Agravante:** los `DELETE` no verifican `status_code` ni reintentan; con un 429 se pierden silenciosamente y quedan bloques viejos duplicados junto a los nuevos.
- **Fix recomendado (mismo patrón R-02 que ya usan en `vsync_doc`):**
  1. Leer los bloques actuales **paginando** (`start_cursor`) y guardar sus IDs.
  2. Hacer `append` de **todos** los bloques nuevos por lotes.
  3. Solo si el paso 2 terminó OK, borrar los IDs viejos (con chequeo de status y reintento con backoff).
  4. Si el paso 2 falla, no borrar nada y salir con error (y `sys.exit(1)`, ver A6).
  - Si se quiere preservar el orden visual, guardar un backup local (`data/V_ID_CENSUS_BACKUP.json`) y re-insertarlo en el `except`.

### 🟠 A2 — `--auto-fix-orphans` no agrega los IDs al `CENSUS_SPEC` y ensucia el archivo

- **Dónde:** `auto_fix_orphans()` L743-799 (inserción en L790: `current_content[:census_spec_end] + ...`).
- **Evidencia:** tras aceptar el huérfano `SP:BOOTLOADER-999`, el parseo AST del archivo resultante muestra que el ID **no está dentro del literal de `CENSUS_SPEC`** y `known_ids_from_spec()` no lo incluye — las entradas quedan **después** del `]` de cierre, como expresiones muertas (ruff `B018` en L400/406). Ya hay **2 bloques residuales `# Auto-generated orphan IDs`** (L396 y L402): cada corrida suma basura.
- **Bug secundario:** el paso "Regenerando census con IDs actualizados" (L1305-1311) recalcula `known_ids` desde el `CENSUS_SPEC` **en memoria** (que no cambió) → es un **no-op** incluso si la inserción quedara bien.
- **Fix recomendado:**
  - Insertar dentro de la lista correcta: localizar la sección por `"name"` y el cierre de su `"rows"` con balanceo de corchetes, respetando la indentación; **o** (más robusto) mantener una lista separada `AUTO_ORPHANS_SPEC` y unirla en `known_ids_from_spec()`/`render_markdown()`.
  - Tras escribir, **recargar** el archivo (re-parse o `importlib.reload`) antes de recalcular los huérfanos.
  - Limpiar los 2 residuos actuales (L396-403).

### 🟠 A3 — Solo borra la primera página de bloques (duplicados si la página tiene >100)

- **Dónde:** L988-994 — `requests.get(url, headers=HEADERS)` sin cursor.
- **Evidencia:** T6 — página simulada de 150 bloques (API devuelve 100 + `has_more=True`) → solo **100 DELETE**; los otros 50 sobreviven y se duplican con el contenido nuevo.
- **Fix:** paginar el GET con `start_cursor` hasta `has_more == False`.

### 🟠 A4 — Filas de tabla con `---` en una celda se descartan

- **Dónde:** L882 — `if '---' not in line`.
- **Evidencia:** la fila `` | `KERNEL:B` | 02 | URL https://x.dev/a---b | `` desaparece de la tabla generada (queda header + 1 fila).
- **Fix:** detectar la fila separadora con regex (`^\s*\|[\s:\-|]+\|\s*$`) en vez de buscar `'---'` en toda la línea.

### 🟠 A5 — Ruta de salida hardcodeada

- **Dónde:** L1277 — `Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/data/V_ID_CENSUS_PRODUCTION.md")`.
- **Efecto:** el script no es portable; fuera de la Mac falla con `PermissionError`/`FileNotFoundError` (es la única ruta absoluta del script; el resto usa `script_dir`).
- **Fix:** `output = script_dir.parent / "data" / "V_ID_CENSUS_PRODUCTION.md"`.

### 🟡 A6 — El exit code nunca refleja fallos

- `sync_to_notion(...)` ignora su retorno (L1313); los docs incompletos solo se imprimen como advertencia (L1316). El proceso termina **0** aunque el sync o la versión hayan fallado.
- **Fix:** acumular `ok` y `sys.exit(0 if ok else 1)`. Importante si algún agente/cron decide "éxito" por exit code.

### 🟡 A7 — Estructura del census: `CANON` dentro de `MANUAL` y doc faltante

- Los **59 IDs `CANON:*` viven dentro de la sección `"MANUAL"`** de `CENSUS_SPEC` → `render_markdown()` los publica bajo el heading `## MANUAL`.
- `DOCUMENTS` tiene 8 docs; **falta "Changelog Archivo"** (que sí existe en `vsync_doc.DOCS`, en el hook MCP y como prefijo `CHANGELOG_ARCHIVO:` en `VALID_PREFIXES`) → ese documento nunca se indexa y sus IDs no se resuelven ni se detectan como huérfanos (invisibles).
- **Fix:** sección propia para `CANON` (o confirmar que es intencional) y agregar la página de Changelog Archivo a `DOCUMENTS` (o eliminar el prefijo).

### 🟡 A8 — Menores

- 4 f-strings sin placeholders (L1014, 1099, 1107, 1263) — pyflakes.
- `--debug-id` toma `sys.argv[idx+1:]` completo (L1242): cualquier flag posterior se interpreta como ID.
- `parse_markdown_table_cell()` no aplica formato de código al texto anterior al primer link (L803-868); hoy no afecta al census generado, pero es frágil si el output cambia.
- `update_page_version()` asume propiedad `rich_text` aunque `get_page_version()` soporta `select` (L1054-1080), y el nombre de propiedad está hardcodeado con espacio para la página `36e938be…` (L1104).

---

## 2. Layer 4

### 🔴 B1 — El hook de sync **mata** el sync que lanza (PIPE sin lector)

- **Dónde:** `trigger_sync_after_mcp_write.py` L58-64 y `notion_write_wrapper._trigger_sync()` L95-101 (`stdout=subprocess.PIPE`, `stderr=subprocess.PIPE`, y el padre termina sin leer).
- **Evidencia:** con un hijo que imprime **una sola línea** 1 s después de que el padre sale → `BrokenPipeError` y el hijo muere. Con un hijo que imprime 300 KB y marca final → el marcador **nunca** se escribió.
- **Impacto:** es el flujo oficial documentado en `MCP_SYNC_HOOK_README.md` (incluido `mcp_sync_wrapper.sh`): hoy el sync post-MCP que ese hook debería garantizar **no se completa**.
- **Fix:** `stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True`, o redirigir a log (`open("/tmp/vantage_mcp_sync.log", "a")`); alternativamente `subprocess.run([...], timeout=120)` si se acepta bloquear. Aplicar en los **dos** archivos.

### 🔴 B2 — `git_sync.py` commitea en la rama activa pero pushea `main`

- **Dónde:** `BRANCH = "main"` (L33) + `git push origin BRANCH` (L173).
- **Evidencia:** repo de prueba en rama `arena/sesion` con remote: el commit quedó en `arena/sesion`, `git log origin/main..HEAD` con 1 commit sin publicar, y el script imprimió **"✅ L4 Sync OK — 2 archivo(s) commiteados"**.
- **Impacto real:** el launchd `com.vantage.gitsync` corre `git_sync.py` cada 6 h; cualquier trabajo en una rama distinta de `main` se commitea localmente, **no se publica**, y reporta éxito.
- **Fix:**
  ```python
  branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])[1].strip() or "main"
  ...
  code, out, err = run(["git", "push", "origin", f"HEAD:refs/heads/{branch}"], timeout=30)
  ```

### 🟠 B3 — `git_sync.py --dry-run` escribe en disco

- **Dónde:** L142 — `regenerate_index_json()` se ejecuta **antes** del early-return de dry-run.
- **Evidencia:** repo de prueba → `--dry-run` creó `skills/index.json` y dejó `git status` con `?? skills/index.json`.
- **Fix:** en dry-run calcular el índice en memoria y reportarlo en el resultado (`index_updated: True`, "será actualizado") sin escribir el archivo.

### 🟠 B4 — `get_skill_files()` busca `*.skill` y el layout real es `*.md`

- **Dónde:** L69-73 (`SKILLS_DIR.glob("*.skill")`).
- **Evidencia:** sobre `skills/` real → `[]` (hay 29 `.md` y carpetas). `verify_versions.py` L716 documenta que `.skill` **es un sufijo virtual** (migración a carpeta/`SKILL.md`).
- **Efecto:** `regenerate_index_json()` nunca regenera `index.json` (feature muerta; el MCP server no recibe índice actualizado).
- **Fix:** alinear el glob con el layout real (`*.md` / `*/SKILL.md`) o retirar la feature y su mención en docstring/README.

### 🟠 B5 — `vdoc VANTAGE` está anunciado pero `vsync_doc` no lo acepta

- **Dónde:** `vdoc.py` L42 (`DOCS` incluye `"VANTAGE"`) y docstring L21; `vsync_doc.py` L691 (`--doc choices=list(DOCS.keys())`).
- **Evidencia:** `vsync_doc.py --direction notion --doc VANTAGE` → exit 2: `invalid choice: 'VANTAGE' (choose from kernel, system_prompt, …, project_charter)`.
- **Agravante:** `vdoc` no propaga el error (B6) → el operador ve que "corrió" sin saber que no hizo nada.
- **Fix:** mapear `VANTAGE` al doc/página que corresponda (¿root page?) o quitarlo del set y del docstring.

### 🟠 B6 — `vdoc.py` no propaga exit codes

- **Dónde:** L130-133 — `rc = run(...)`; `if rc != 0: print(...); return` → `main()` devuelve `None` → exit 0. Comando desconocido (L85-87) → exit 0. `if __name__ == "__main__": main()` sin `sys.exit`.
- **Evidencia:** `python3 vdoc.py comando_inexistente` → exit 0.
- **Fix:** `sys.exit(rc)` / `return rc` y `sys.exit(main())`.

### 🟠 B7 — `vsync_doc.py`: fallo de fetch no afecta el exit code (y `auto_commit` corre igual)

- **Dónde:** L742-753 — `if md is None: print("✗ ... ERROR"); continue` sin tocar `_exit_code[0]`; `auto_commit()` en L795.
- **Evidencia:** `main()` con `pages.retrieve` que lanza → imprime "✗ TECHNICAL KERNEL ERROR" y **retorna 0**. Con varios docs, un fallo de red parcial se reporta como éxito y además `auto_commit` podría commitear un estado parcial.
- **Fix:** `_exit_code[0] = 1` en ese `continue`, y omitir `auto_commit()` si hubo errores.

### 🟠 B8 — `vdoc_nblm.py`: `ACTIVE_DIR` incorrecto → no sube ningún doc, sin avisar

- **Dónde:** L8-9 — `PROJECT_ROOT = Path('/Users/mauriciomeyran/…')` y `ACTIVE_DIR = PROJECT_ROOT / 'ACTIVE'`; el real es `PROJECT_ROOT / 'Documentación' / 'ACTIVE'` (el que usa `vsync_doc`).
- **Evidencia:** import del módulo → `ACTIVE_DIR=/Users/mauriciomeyran/…/VANTAGE/ACTIVE` (no existe); simulando el flujo completo sube el digest, **0 de los 9 docs fundacionales** y no imprime advertencia; exit 0.
- **Fix:** derivar rutas de `__file__`, apuntar a `Documentación/ACTIVE` y avisar (y/o fallar) si el directorio no existe.

### 🟠 B9 — `vsum.py`: `chunk_text()` no parte párrafos gigantes

- **Dónde:** L204-226.
- **Evidencia:** un único párrafo de 25.000 chars → 1 chunk de 25.000 (límite declarado `MAX_CHARS_PER_CHUNK = 10000`).
- **Fix:** si `len(para) > max_chars`, subdividir por líneas o por ventana de caracteres.

### 🟠 B10 — `notion_write_wrapper.py` es un stub que devuelve `success=True` sin escribir

- **Dónde:** `write_to_notion_page()` L41-84 (`write_success = True` fijo; `TODO` en L66).
- **Evidencia:** `write_to_notion_page("pagina-x", {...})` → `{'success': True, …}` sin ninguna escritura; si el page_id es fundacional además **dispara un sync** del contenido viejo.
- **El README ya lo declara experimental** ("no usar en producción"), pero un import accidental es un footgun silencioso.
- **Fix:** lanzar `NotImplementedError` (fail-fast) mientras no esté implementado, o eliminarlo del repo.

### 🟡 B11 — Menores y deuda técnica

- **`FOUNDATIONAL_DOCS` duplicado** en `notion_write_wrapper.py` y `trigger_sync_after_mcp_write.py` (hoy idénticos, 9/9). Unificar en un módulo común.
- **`Layer_4/scripts.zip` versionado (46 KB)** con copias **anteriores** de 6 de 7 scripts (git_sync, notion_write_wrapper, trigger, vdoc, vdoc_nblm, vsync_doc; `vsum.py` es el único igual), un `vsync_doc.py.bak-*` y un `__pycache__` de Python 3.14 → riesgo de ejecutar la versión vieja. Actualizarlo o eliminarlo.
- **`vdoc.py PROJECT` hardcodeado** a `~/Documents/03 Projects/VANTAGE` (L35), no portable, mientras `git_sync`/`vsync_doc` derivan de `__file__`.
- **`vsync_doc` fija `Notion-Version: 2025-09-03`** en duro; `generate_census` usa `_notion_version()` → posible drift de versión entre capas.
- **`vsync_doc --direction local` con tablas:** `tables_skipped > 0` → exit 1 y manifest sin actualizar **siempre** (Kernel 10 tablas, Manual 47, Career Canon 5, System Prompt 4). El modo local nunca puede completar en esos docs (los `table_row` sí son patcheables individualmente: se puede implementar PATCH por celda, o bloquear la dirección local para docs con tablas).
- **Imports/variables sin uso:** `stat` (L20), `e` (L244/454), `local_ts` (L723) en `vsync_doc`; `sys` en `vdoc_nblm`; `re` en `vsum`; `Optional` en `notion_write_wrapper`; `process` en `trigger`.

---

## 3. Lo que sí quedó verificado como correcto

- **`fetch_blocks()`**: 429 → lee `Retry-After` y reintenta; 3 fallos → `FetchIncompleteError`; los docs incompletos no rompen el resto del census.
- **Extracción de IDs**: fronteras correctas (`KERNEL:PURPOSE` ≠ `-001` ≠ `-001X`), headings con numeración (`01.4 SP:BOOTLOADER-004 — …`) y `ID: …` en párrafos.
- **`_decide()`** de `vsync_doc`: los 5 casos correctos (noop, notion→local, local→notion, conflict, sin manifest).
- **Fix R-02** (`push_local_to_notion`): crea el reemplazo y solo entonces borra el viejo — verificado con mocks.
- **Fix V-06**: las tablas no sincronizadas se cuentan y evitan actualizar el manifest.
- **Mapeo de page_ids** consistente entre `generate_census`, `vsync_doc` y el hook MCP (9/9 en los dos últimos).
- `compileall` sin errores de sintaxis en los 8 archivos objetivo.

---

## 4. Plan de fixes sugerido (orden por riesgo)

| # | Fix | Impacto | Esfuerzo |
|---|-----|---------|----------|
| 1 | B1 — `DEVNULL`/log en el hook de sync (2 archivos) | El sync post-MCP vuelve a funcionar | 3 líneas |
| 2 | A1 + A3 — append-antes-de-borrar + paginación en el census | Evita dejar la página publicada vacía/duplicada | Medio |
| 3 | B2 — rama real en el push de `git_sync` | Evita commits sin publicar + falsos OK | Bajo |
| 4 | A2 — auto-fix de huérfanos + limpieza del residuo | La feature deja de ser un no-op | Medio |
| 5 | B6/B7/B8/A6 — propagación de errores y exit codes | Que ningún script reporte éxito cuando falló | Bajo |
| 6 | A4/A5/B3/B4/B5/B9/B10 | Corrección funcional y portabilidad | Bajo-Medio |
| 7 | A7/A8/B11 — estructura del census y deuda técnica | Precisión del artefacto publicado | Bajo |

---

## 5. Alcance no cubierto (no verificado en esta sesión)

- Comportamiento **en vivo** contra Notion (límites reales de la API, rate limits, propiedades `Versión`/`Versión `).
- Cliente `notebooklm` (`vdoc_nblm`) y credenciales: no está instalado aquí; solo se validaron rutas/flujo con dobles.
- `launchd`/cron del Mac, `.venv` de Layer_1, rutas reales `~/Documents/03 Projects/VANTAGE`.
- Semántica del negocio (qué debe contener el census, si `CANON` dentro de `MANUAL` es intencional).

---

## 6. Reproducción

Los harness usados quedaron en `/tmp/val/` (`validate_generate_census.py`, `validate_layer4.py`) y `/tmp/val2/` (repos y clientes simulados). Son **temporales**: si quieres, los convierto en `tests/` del repo (pytest, sin red) para que estos hallazgos queden como regresión.

**Evidencia rápida por hallazgo:**

| ID | Reproducción |
|----|--------------|
| A1 | `update_notion_census_page` con `PATCH`→500: 3 DELETE ejecutados, página vacía |
| A2 | `auto_fix_orphans({"SP:BOOTLOADER-999": …})` + AST: ID fuera de `CENSUS_SPEC`; 2 residuos en L396 y L402 |
| A3 | Página simulada de 150 bloques → 100 DELETE |
| A4 | Tabla con `a---b` en una celda → fila perdida |
| A5 | `grep -n "/Users/mauriciomeyran" generate_census.py` → L1277 |
| B1 | Hijo con 1 print tras la salida del padre → `BrokenPipeError` |
| B2 | Repo en `arena/sesion` + remote: commit en rama activa, `origin/main..HEAD` ≠ ∅, salida "✅ L4 Sync OK" |
| B3 | `git_sync.py --dry-run` → crea `skills/index.json` |
| B4 | `get_skill_files()` sobre `skills/` real → `[]` (29 `.md`) |
| B5 | `vsync_doc.py --doc VANTAGE` → exit 2 |
| B6 | `vdoc.py comando_inexistente` → exit 0 |
| B7 | `vsync_doc.main()` con fetch que lanza → exit 0 |
| B8 | Import de `vdoc_nblm` → `ACTIVE_DIR=…/VANTAGE/ACTIVE` (no existe); sube solo el digest |
| B9 | `vsum.chunk_text("x"*25000)` → 1 chunk de 25000 |
| B10 | `write_to_notion_page("pagina-x", {})` → `{'success': True}` sin escritura |

---

## 7. Fixes aplicados (2026-10-02)

Todos en esta rama, sin tocar Notion ni el Mac del operador. Cobertura: **48 tests** (`tests/test_generate_census.py`, `tests/test_layer4_scripts.py`) + `ruff`/`pyflakes` limpios.

### `Layer_1/scripts/generate_census.py`

| ID | Fix aplicado |
|----|--------------|
| A1 | `update_notion_census_page()` reescrita: **APPEND primero, DELETE después**, con verificación de status HTTP, rollback de lo agregado si un lote falla, y aborto sin escribir con payload vacío. Antes de este cambio la página podía quedar vacía. |
| A3 | Nuevo `fetch_all_children()`: pagina con `start_cursor` hasta `has_more == False` (antes solo borraba los primeros 100). |
| A2 | `auto_fix_orphans()` reescrita: inserta cada huérfano **dentro de la sección correcta** de `CENSUS_SPEC` (`_find_rows_bounds` balancea corchetes ignorando strings), valida por AST que el ID quede en el spec **antes** de escribir, es idempotente (no duplica IDs ya presentes) y reporta los IDs sin sección reconocida. `insert_orphan_rows()` separado y testeable. Se eliminaron los 2 residuos muertos (ex L396/L402). El entry point ahora **recarga el spec desde disco** tras el auto-fix (antes regeneraba con el spec en memoria = no-op). |
| A4 | La fila separadora se detecta con `TABLE_SEPARATOR_RE`; ya no se descartan filas con `---` en una celda. |
| A5 | Salida a `script_dir.parent / "data" / "V_ID_CENSUS_PRODUCTION.md"` (era ruta absoluta del operador). |
| A6 | El entry point acumula fallos y termina con `sys.exit(0/1)`; `sync_to_notion()` devuelve `None` en cancelación (no es fallo) y `False` en error real. `--debug-id` ignora flags posteriores. |
| A8 | f-strings sin placeholder corregidas; `known_ids_from_spec()`/`render_markdown()` aceptan un `spec` explícito. |
| A7 | **Pendiente de decisión**: se documentó en el código por qué `CANON` vive en la sección `MANUAL` y por qué "Changelog Archivo" no está en `DOCUMENTS` (agregarlo expondría cientos de IDs históricos). |

### Layer 4

| ID | Fix aplicado |
|----|--------------|
| B1 | `trigger_sync_after_mcp_write.py` y `notion_write_wrapper._trigger_sync()`: el hijo escribe a **log en disco** (`/tmp/vantage_mcp_sync.log`, configurable con `VANTAGE_MCP_SYNC_LOG`), con `start_new_session=True`. Ya no muere por `BrokenPipeError`. |
| B2 | `git_sync.py`: nuevo `current_branch()`; el push usa `HEAD:refs/heads/<rama activa>` (antes `main` hardcodeado) y el resultado reporta la rama. |
| B3 | `--dry-run` ya no escribe `index.json` (`regenerate_index_json(dry_run=True)` calcula en memoria). |
| B4 | `get_skill_files()` reconoce el layout real (`skills/*.md`, `*/SKILL.md` y legacy `*.skill`); verificado contra el repo: encuentra las 29 skills. |
| B5 | `vdoc.py`: `VANTAGE` eliminado de `DOCS` y del docstring (se anunciaba pero `vsync_doc --doc VANTAGE` daba exit 2). |
| B6 | `vdoc.py`: `main() -> int` + `sys.exit(main())`; comando desconocido, dirección/doc duplicados y fallo de `vsync_doc` ahora devuelven exit ≠ 0. |
| B7 | `vsync_doc.py`: los fallos de fetch (real y dry-run) marcan `_exit_code[0] = 1`, y **no** se llama `auto_commit()` si hubo errores. |
| B8 | `vdoc_nblm.py`: rutas derivadas de `__file__`; `ACTIVE_DIR = PROJECT_ROOT / 'Documentación' / 'ACTIVE'` y aviso explícito si no existe. |
| B9 | `vsum.py`: `_hard_split()` parte párrafos mayores a `max_chars`; los chunks ya no exceden el límite. |
| B10 | `notion_write_wrapper.write_to_notion_page()` lanza `NotImplementedError` en vez de simular éxito sin escritura. |
| B11 | `foundational_docs.py`: fuente única del mapeo `page_id → key` (antes duplicado en 2 archivos). `_rich_text()` acepta bloques locales (`text.content`). `vsync_doc` usa `notion_utils._notion_version()` (mismo criterio que L1) en vez de fijar `2025-09-03`. Una tabla **idéntica** ya no se cuenta como no sincronizada. `vdoc.py` deriva `PROJECT` de `__file__`. `scripts.zip` regenerado con las versiones actuales (sin `.bak`, `.DS_Store` ni `__pycache__`). Imports/variables sin uso eliminados. |

### Lo que NO se cambió (y por qué)

- **`CANON` dentro de la sección `MANUAL`** (A7): puede ser intencional (el Canon se publica pegado al Manual). Cambiarlo altera la estructura del documento publicado; requiere decisión del operador.
- **Tablas con contenido distinto en `--direction local`**: bloquean el manifest a propósito (fix V-06). Implementar PATCH por celda es una mejora pendiente, no un bug.
- **`vsync_doc --direction local` sobre `project_charter`**: sigue bloqueado (regla del Charter).
- **`tests/test_vload.py`**: se dejó intacto (solo tiene imports sin uso preexistentes).

### Verificación

```
$ python3 -m pytest tests/ -q
68 passed

$ ruff check --select F,E9,B018,B904,B006,B008,E722 Layer_1/scripts/generate_census.py Layer_4/scripts/ tests/
All checks passed!

$ python3 Layer_4/scripts/git_sync.py --dry-run   # sobre el repo real
📝 index.json se actualizaría (29 skills)
DRY RUN — auto-sync: auto-sync: 2026-10-03 02:37 (14 archivo(s)) (rama arena/01a0fea2-vantage)
   # y NO se creó skills/index.json (antes sí lo creaba)
```

**Trade-off asumido en A1:** durante la publicación el documento muestra transitoriamente el contenido viejo **y** el nuevo antes de borrar el viejo (duplica la longitud unos segundos). Es el mismo patrón del fix R-02 y evita el caso catastrófico de página vacía.
