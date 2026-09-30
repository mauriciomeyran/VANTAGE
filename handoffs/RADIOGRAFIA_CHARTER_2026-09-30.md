# RADIOGRAFÍA DE CABLEADO CHARTER — VANTAGE
Destinatario: CLAUDE/MAIN (gatekeeper del Charter) · Auditor: Arena.ai Agent Mode · Fecha: 2026-09-30
Rol: solo lectura / inventario. No se modificó ningún archivo del repo (`git status` limpio al cierre).

## 0. Declaraciones de método (obligatorias por §2–§3 del contrato)

| Ítem | Declaración |
|---|---|
| HEAD auditado | `7483169edba264191ab19c364c5c2726cdb9283f` — "auto-sync: 2026-09-30 14:56 (3 archivo(s))". `git fetch origin main` → `origin/main` = mismo hash. Rama de trabajo `arena/01a0f420-vantage` sin cambios sobre ese commit. |
| Historia git | `git log --oneline \| wc -l` = **1** (historia aplanada). Los hashes que citan los changelogs (`b2c5b42`, `94873d6`, `6cc6a54`, `d34cd48`, etc.) **no son verificables** desde este checkout. |
| Acceso a Notion | **No tengo** MCP/API de Notion ni token (`env \| grep -ci notion` = 0). Sí tuve `fetch_page` sobre las URLs públicas renderizadas `https://app.notion.com/p/f87938befc428263a305819877d2245f` (Charter) y `.../394938befc4281e6a381e3869e60d89d` (Census). Es un render web: puede estar cacheado, no expone tipos de bloque ni `plain_text` crudo. Leí Charter chunks 0, 1 y 5 de 6 (TOC completo + §7); Census chunks 0 y 5 de 6 (sección PROJECT CHARTER completa + cola "IDs Huérfanos"). **No leí** Charter chunks 2–4 ni Census chunks 1–4. Las comparaciones contra Notion son **visuales, fila por fila**, no por API. |
| Ejecución | Todo es lectura estática, salvo cómputos locales puros (sin red, sin escritura) marcados [EJEC-LOCAL]: AST de `CENSUS_SPEC`, `vantage_id_rules.classify_heading`/`suggest_canonical_heading` sobre los 38 headings del espejo local, `sha256` de archivos, lectura de `document_registry`, `grep -c`. Nada que requiera Notion/credenciales se ejecutó. |
| Repo vs. `charter_integration.patch` | El patch en la raíz es un artefacto previo; el código actual ya contiene sus cambios. Se reporta en H. |

Convención de estado: **[LEÍDO]** = confirmado por lectura estática · **[EJEC-LOCAL]** = confirmado ejecutando función pura en sandbox · **[REQUIERE EJECUCIÓN — NO VERIFICABLE POR LECTURA]** · **[⚠ CONTRADICCIÓN]**.

---

## A. Sincronización documental

| Archivo:línea | Cita literal | Qué hace respecto al Charter |
|---|---|---|
| `Layer_4/scripts/vsync_doc.py:107-111` (bloque completo, dentro de `DOCS` L66-112) | `"project_charter": {` / `"notion_id": "f87938be-fc42-8263-a305-819877d2245f",` / `"local_file": BASE_DIR / "PROJECT_CHARTER.md",` / `"label": "PROJECT CHARTER",` / `},` | Registra el Charter como 9.ª clave de `DOCS`. UUID + espejo local + etiqueta. `vsync_doc.DOCS` tiene 9 claves: `kernel, system_prompt, career_canon, manual, aliases, change_log, brief, change_log_archivo, project_charter` [LEÍDO]. No hay alias en este archivo (la clave canónica es `project_charter`). |
| `vsync_doc.py:64` | `BASE_DIR = _PROJECT / "Documentación" / "ACTIVE"` | Ruta efectiva del espejo: `Documentación/ACTIVE/PROJECT_CHARTER.md` (existe, 397 líneas, 32 245 B). |
| `vsync_doc.py:691` | `p.add_argument("--doc", choices=list(DOCS.keys()))` | `--doc project_charter` es opción válida del CLI. |
| `vsync_doc.py:693` | `targets = {args.doc: DOCS[args.doc]} if args.doc else DOCS` | Sin `--doc`, el Charter entra **implícitamente** en toda corrida (incluye las de los wrappers Raycast, ver fila abajo). |
| `vsync_doc.py:737-745` | `if args.direction == "notion":` … `local.write_text(md, encoding="utf-8")` … `manifest[k] = _hash(md)` | `notion→local`: sobrescribe `PROJECT_CHARTER.md` desde Notion y actualiza el manifest. Lectura sobre Notion (no escribe en Notion). |
| `vsync_doc.py:747-751` | `elif args.direction == "local":` … `result = push_local_to_notion(d["notion_id"], local)` | **Ruta de escritura hacia la página Notion del Charter** (PATCH puntual) cuando `--direction local` apunta al Charter (explícito o por ausencia de `--doc`). Ejecución real [REQUIERE EJECUCIÓN — NO VERIFICABLE POR LECTURA]. |
| `vsync_doc.py:770-774` | `elif decision == "local->notion":` … `SKIP — local→notion deshabilitado (ACTIVE LOCAL es read-only)` | En modo `auto` el Charter nunca sube a Notion; solo `--direction local` lo hace. |
| `vsync_doc.py:115` | `MANIFEST_PATH = BASE_DIR / ".vsync_manifest.json"` | Manifest de hashes por clave; incluye `project_charter` (fila siguiente). |
| `Documentación/ACTIVE/.vsync_manifest.json:11` | `"project_charter": "5272fd09ff780143a46d01a5a45bcacb270047353e39d7aa94c02689007785e2"` | [EJEC-LOCAL] `sha256(PROJECT_CHARTER.md.strip())` == ese valor → el espejo local en HEAD coincide con el último sync registrado. |
| `Layer_4/scripts/vdoc.py:44-47` (bloque `DOC_ALIASES` completo) | `DOC_ALIASES = {` / `    "charter": "project_charter",` / `    "Navigation_Brief": "brief",  # histórico: vdoc acepta Navigation_Brief; vsync usa "brief"` / `}` | Alias `charter` → clave canónica `project_charter`. |
| `vdoc.py:42` | `DOCS = {"kernel", "system_prompt", "career_canon", "manual", "aliases", "change_log", "Navigation_Brief", "VANTAGE", "change_log_archivo", "project_charter", "charter"}` | Whitelist de argumentos CLI: acepta tanto `project_charter` como `charter`. |
| `vdoc.py:94-95` | `doc_key = DOC_ALIASES.get(doc, doc)` / `vsync_args += ["--doc", doc_key]` | Resolución del alias antes de invocar `vsync_doc.py`. |
| `vdoc.py:22` | `vdoc project_charter  \|  vdoc charter` | Docstring de uso. |
| `vdoc.py:111-125, 128-135` | `forced = direction in ("notion", "local")` … `confirm != "s"` … `run(vsync_args, "vsync_doc (Notion ↔ ACTIVE)")` / `run(vgit_args, "git_sync (ACTIVE → GitHub)")` | `vdoc local charter` (y `vdoc local` sin doc) llega a `push_local_to_notion` tras confirmación interactiva `s/N`; después ejecuta `git_sync.py`. |
| Otros scripts en `Layer_4/` con string `charter` / UUID | — | `grep -rIni 'charter' Layer_4` → únicamente `vdoc.py`, `vsync_doc.py`, `trigger_sync_after_mcp_write.py`, `notion_write_wrapper.py`, `MCP_SYNC_HOOK_README.md`. `git_sync.py`, `vsum.py`, `vdoc_nblm.py`, `mcp_sync_wrapper.sh`, `com.vantage.gitsync.plist`: 0 menciones. |
| `Layer_4/scripts/git_sync.py:5` (implícito) | `Detecta cambios en el repo y hace add+commit+push automáticamente.` | Sin mención del Charter; por su docstring opera sobre el repo completo (comportamiento real no verificado: [REQUIERE EJECUCIÓN — NO VERIFICABLE POR LECTURA]). |
| `Raycast/vantage-vdoc-dry.sh:15` · `Raycast/vantage-vdoc-notion.sh:15` | `python3 vsync_doc.py --direction auto --dry-run` · `python3 vsync_doc.py --direction notion` | Sin `--doc` → incluyen el Charter (vía `vsync_doc.py:693`). |
| `Layer_4/scripts.zip` | (27 entradas; contiene `vsync_doc.py`, `trigger_sync_after_mcp_write.py`, `notion_write_wrapper.py`, `MCP_SYNC_HOOK_README.md`) | Escaneo binario de todas las entradas: **0 ocurrencias** de `harter`/`HARTER`. Copia anterior al cableado. |

---

## B. Hooks de sincronización asíncrona

| Archivo:línea | Cita literal | Qué hace respecto al Charter |
|---|---|---|
| `Layer_4/scripts/trigger_sync_after_mcp_write.py:31-43` (lista completa) | `# ── Documentos fundacionales (9) ──…` / `FOUNDATIONAL_DOCS = {` / `"377938be-fc42-805e-a408-c9ae518d4fe7": "kernel",` / `"37b938be-fc42-8001-9b9b-fcf81130d274": "system_prompt",` / `"377938be-fc42-8089-93f2-f52dbd2dec6c": "career_canon",` / `"372938be-fc42-8050-9a67-e40857d7806e": "manual",` / `"37c938be-fc42-80d4-b9ae-f5969830331b": "aliases",` / `"390938be-fc42-80e7-b429-d7d730339353": "change_log",` / `"3a3938be-fc42-8008-9e90-ec435c01f50d": "brief",` / `"3ba938be-fc42-8011-8947-fb4fa5d1f63f": "change_log_archivo",` / `"f87938be-fc42-8263-a305-819877d2245f": "project_charter",` / `}` | Charter = 9.º y último elemento (L42). 9 entradas en total [LEÍDO]. |
| `trigger_sync_after_mcp_write.py:53-57` | `if page_id not in FOUNDATIONAL_DOCS:` … `sys.exit(0)` … `doc_key = FOUNDATIONAL_DOCS[page_id]` | Comparación por **string exacto** con UUID con guiones (`sys.argv[1].strip()`, L51). Un page_id sin guiones no coincide. |
| `trigger_sync_after_mcp_write.py:64-70` | `subprocess.Popen([sys.executable, str(_VSYNC_DOC), "--direction", "notion", "--doc", doc_key], …)` | Para el Charter dispara `vsync_doc.py --direction notion --doc project_charter` en background (lectura Notion → local). Disparo real [REQUIERE EJECUCIÓN — NO VERIFICABLE POR LECTURA]. |
| `trigger_sync_after_mcp_write.py:7-13` | `por el operador después de un write MCP a cualquiera de los 8 documentos fundacionales:` / `- Kernel` / `- System Prompt` / `- Career Canon` / `- Manual` / `- Aliases` / `- Change Log` | **[⚠ CONTRADICCIÓN interna]** docstring dice "8" y lista 6; el Charter no figura; el encabezado L31 dice "(9)" y el dict tiene 9. |
| `Layer_4/scripts/notion_write_wrapper.py:27-38` (lista completa) | `# ── Documentos fundacionales (9) ──…` / `FOUNDATIONAL_DOCS = {` … (mismas 8 claves que arriba) … `"3ba938be-fc42-8011-8947-fb4fa5d1f63f": "change_log_archivo",` / `"f87938be-fc42-8263-a305-819877d2245f": "project_charter",` / `}` | Charter presente (L37), 9 entradas idénticas al trigger. |
| `notion_write_wrapper.py:41-83` | `# TODO: Implementar la lógica real de escritura según el stack del proyecto` … `# Simular escritura exitosa` / `write_success = True` | La función es un **stub**: no escribe en Notion; solo imprime y llama `_trigger_sync` si `page_id in FOUNDATIONAL_DOCS` (L77-79). |
| `notion_write_wrapper.py:95-96` | `subprocess.Popen([sys.executable, str(_TRIGGER_SCRIPT), page_id], …)` | Encadena al trigger anterior. |
| Consumidores de `notion_write_wrapper` | `grep -rIl 'notion_write_wrapper' . --exclude-dir=Archive` → `Change Log.md` (×2 copias + `Changelog Archivo.md`), `script_hash_baseline.json`, `MCP_SYNC_HOOK_README.md`, `charter_integration.patch`, el propio archivo | Ningún script ejecutable lo importa. Consistente con README L33 (fila siguiente). |
| `Layer_4/scripts/MCP_SYNC_HOOK_README.md:7` | `## Documentos Fundacionales (9)` | Catálogo declara 9. |
| `MCP_SYNC_HOOK_README.md:19` | `\| Project Charter        \| f87938be-fc42-8263-a305-819877d2245f \| project_charter       \|` | Fila del Charter en la tabla `page_id → key en vsync_doc.py` (última de 9 filas, L11-19). |
| `MCP_SYNC_HOOK_README.md:31-33` | `3. **notion_write_wrapper.py**` / `**Estado: Experimental / Stub.**` / `No está terminado ni es usado por ningún script del repo. Contiene la lista de los 8 documentos y la llamada al trigger…` | **[⚠ CONTRADICCIÓN interna]** "los 8 documentos" vs "(9)" en L7 y 9 filas en la tabla. Declara explícitamente "No usar en producción". |
| `MCP_SYNC_HOOK_README.md:37-38` | `El servidor MCP de Notion está configurado a nivel de sistema (~/.config/devin/mcp_config.json), **fuera del repo**.` / `Por tanto, **no es posible interceptar automáticamente** los writes…` | El propio README declara que el hook **no dispara solo**: requiere invocación manual (L42-45: `./Layer_4/scripts/mcp_sync_wrapper.sh <page_id>`). Que un write MCP real al Charter dispare algo: **[REQUIERE EJECUCIÓN — NO VERIFICABLE POR LECTURA]** (y según el README, no ocurre de forma automática). |
| `Layer_4/scripts/mcp_sync_wrapper.sh:6` y `:26` | `# Si el write fue a uno de los 6 documentos fundacionales, dispara automáticamente` · `python3 "$SCRIPT_DIR/trigger_sync_after_mcp_write.py" "$PAGE_ID"` | Sin lista propia; delega en el trigger (por lo tanto hereda el Charter). Comentario dice "6" (conteo desactualizado). |

---

## C. Census — indexación de IDs canónicos

### C.1 Conteo verificado (AST de `CENSUS_SPEC`, [EJEC-LOCAL])

| Archivo:línea | Cita / dato | Qué hace respecto al Charter |
|---|---|---|
| `Layer_1/scripts/generate_census.py:64-395` | `CENSUS_SPEC = [` … cierra en L395 | Bloque completo evaluado con `ast.literal_eval`: 6 secciones → `PROJECT CHARTER` 38 · `KERNEL` 90 · `MANUAL` 113 · `NAVIGATION BRIEF` 29 · `SYSTEM PROMPT` 16 · `ALIASES` 8 = **294 IDs, 294 únicos, 0 duplicados**. |
| `generate_census.py:65-108` | `"name": "PROJECT CHARTER",` … `{"id": "CHARTER:MILESTONES-005", "seccion": "5.5", …},` | **Entradas con prefijo `CHARTER:` = 38** (7 nodos raíz + 31 sub-nodos), 38 únicas, **0 duplicados**. Todas viven en la sección `PROJECT CHARTER`; ninguna `CHARTER:` fuera de ella; ninguna fila de esa sección carece del prefijo. |
| Desglose | `PURPOSE`, `STATUS`, `CONTINUITY` (sin sub-nodos) · `NON-NEGOTIABLES` + `-001..010` · `MILESTONES` + `-001..005` · `DECISIONS` + `-001..011` · `FAILURES` + `-001..005` | 7 + 10 + 5 + 11 + 5 = 38 ✔. |
| `generate_census.py:40-49` | `"Project Charter": "f87938be-fc42-8263-a305-819877d2245f",` (L48) dentro de `DOCUMENTS` | El Charter es **indexado por el generador** (se fetch-ea su árbol de bloques en `build_link_index`, L585-588). |
| `generate_census.py:51-60` | `"Project Charter": 8,` (L59, `DOC_PRIORITY`) | Prioridad más baja (8) para desempate en `pick_best_link` (L622). |
| `generate_census.py:362` | `{"id": "SP:BOOTLOADER-004", "seccion": "01.4", "nombre": "Agente Principal y Gatekeeper del Charter"},` | Fila del SP que nombra al Charter (referencia por nombre; ID no es `CHARTER:`). Aparece en el MD en L306. |
| `generate_census.py:674` | `"CHARTER": "PROJECT CHARTER",` (`infer_section_from_id`) | Mapea huérfanos `CHARTER:*` a la sección `PROJECT CHARTER` al autocorregir el spec. |
| `generate_census.py:1182-1190` | `live_seccion = best.get("seccion") if best else None` … `if live_seccion: seccion = live_seccion else: seccion = row.get("seccion", "")` | La columna Sección del MD sale **del heading vivo**; `seccion` del spec es solo fallback (explica la diferencia spec↔MD en C.2). `nombre` **siempre** sale del spec (L1183). |
| `generate_census.py:1238` | `notion_page_id = "394938befc4281e6a381e3869e60d89d"` | Página destino de `--sync-to-notion` (Census Notion). |
| `generate_census.py:1277` | `output = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/data/V_ID_CENSUS_PRODUCTION.md")` | Ruta absoluta del MD generado. |
| `generate_census.py:1313-1314` | `if sync_to_notion_flag:` / `sync_to_notion(notion_page_id, md, auto_confirm_flag, sync_version_flag)` | Ruta de publicación a Notion. Ejecución [REQUIERE EJECUCIÓN — NO VERIFICABLE POR LECTURA]. |
| `Layer_1/data/V_ID_CENSUS_PRODUCTION.md:1-4` | `## PROJECT CHARTER` / `\| ID \| Sección \| Nombre \|` | Sección del Charter: **primera** del MD, filas L5-L42 = **38 filas** `CHARTER:` (conteo por `grep -c 'CHARTER:'` = 38; 38 parseadas con regex; 0 sin parsear). Mismo conjunto y **mismo orden** que `CENSUS_SPEC`; 0 IDs duplicados; 0 anchors duplicados; todos con base `https://app.notion.com/p/f87938befc428263a305819877d2245f`. Ninguna fila con "⚠︎sin verificar en vivo". |
| `V_ID_CENSUS_PRODUCTION.md:337-339` | `## IDs Huérfanos (fuera de CENSUS_SPEC)` / `_Ninguno detectado en esta corrida._` | 0 huérfanos (incluye 0 `CHARTER:`). El MD **no trae timestamp de generación**: no se puede fechar desde el archivo. |
| `Layer_1/data/V_ID_CENSUS_PRODUCTION.pdf` | (PDF 1.9 MB) | **No inspeccionable** en este sandbox (sin `pdftotext`/`pypdf`/`fitz`). Sin afirmación sobre su contenido. |

### C.2 Las 38 entradas `CHARTER:` — spec vs. MD vs. Notion Census

Notion Census: sección `### PROJECT CHARTER` con 38 filas en el fetch público (chunk 0). Comparé visualmente ID, Sección y anchor fila por fila contra el `.md`: **las 38 coinciden**. Además, los anchors del TOC del Charter vivo (Notion, chunk 0/1) coinciden con los del Census para los 38 IDs.

| # | ID | generate_census.py (línea · seccion spec) | V_ID_CENSUS_PRODUCTION.md (línea · Sección) | anchor block-id en el .md | Census Notion (fetch público) |
|---|---|---|---|---|---|
| 1 | `CHARTER:PURPOSE` | L68 · "01" | L5 · "1." | `3eb938befc4280cfa758eec00c6b4bd3` | fila presente; Sección y anchor idénticos (comparación visual) |
| 2 | `CHARTER:NON-NEGOTIABLES` | L69 · "02" | L6 · "4." | `3eb938befc4280d0b67de66fad8199c8` | fila presente; Sección y anchor idénticos (comparación visual) |
| 3 | `CHARTER:STATUS` | L70 · "03" | L7 · "7." | `3eb938befc4280ebb77fef32858e73c4` | fila presente; Sección y anchor idénticos (comparación visual) |
| 4 | `CHARTER:MILESTONES` | L71 · "04" | L8 · "5." | `3eb938befc4280dc8598dadd5e8c050f` | fila presente; Sección y anchor idénticos (comparación visual) |
| 5 | `CHARTER:DECISIONS` | L72 · "05" | L9 · "2." | `3eb938befc42809ba6ffc94a0d10b714` | fila presente; Sección y anchor idénticos (comparación visual) |
| 6 | `CHARTER:FAILURES` | L73 · "06" | L10 · "3." | `3eb938befc428075b83ec234ef46eed3` | fila presente; Sección y anchor idénticos (comparación visual) |
| 7 | `CHARTER:CONTINUITY` | L74 · "07" | L11 · "6." | `3eb938befc42803e9c24f2d6e9bced1e` | fila presente; Sección y anchor idénticos (comparación visual) |
| 8 | `CHARTER:DECISIONS-001` | L76 · "2.1" | L12 · "2.1" | `3eb938befc4280229697f961aefc5ceb` | fila presente; Sección y anchor idénticos (comparación visual) |
| 9 | `CHARTER:DECISIONS-002` | L77 · "2.2" | L13 · "2.2" | `3eb938befc4280edbfdef81c9d544217` | fila presente; Sección y anchor idénticos (comparación visual) |
| 10 | `CHARTER:DECISIONS-003` | L78 · "2.3" | L14 · "2.3" | `3eb938befc4280a5b8b2ea05b3b675f0` | fila presente; Sección y anchor idénticos (comparación visual) |
| 11 | `CHARTER:DECISIONS-004` | L79 · "2.4" | L15 · "2.4" | `3eb938befc428027a260f02f48639a3c` | fila presente; Sección y anchor idénticos (comparación visual) |
| 12 | `CHARTER:DECISIONS-005` | L80 · "2.5" | L16 · "2.5" | `3eb938befc428050882de943cdab7c31` | fila presente; Sección y anchor idénticos (comparación visual) |
| 13 | `CHARTER:DECISIONS-006` | L81 · "2.6" | L17 · "2.6" | `3eb938befc4280f78858f4ff46434c05` | fila presente; Sección y anchor idénticos (comparación visual) |
| 14 | `CHARTER:DECISIONS-007` | L82 · "2.7" | L18 · "2.7" | `9107d5660b9f4417b9e10b35e17f89f8` | fila presente; Sección y anchor idénticos (comparación visual) |
| 15 | `CHARTER:DECISIONS-008` | L83 · "2.8" | L19 · "2.8" | `e71d4525c5e74c73aa77d7db4033b28d` | fila presente; Sección y anchor idénticos (comparación visual) |
| 16 | `CHARTER:DECISIONS-009` | L84 · "2.9" | L20 · "2.9" | `a2a688b0c9874f05990238b0c72b7a9b` | fila presente; Sección y anchor idénticos (comparación visual) |
| 17 | `CHARTER:DECISIONS-010` | L85 · "2.10" | L21 · "2.10" | `60edda41d7ac4601b824838882d8d02e` | fila presente; Sección y anchor idénticos (comparación visual) |
| 18 | `CHARTER:DECISIONS-011` | L86 · "2.11" | L22 · "2.11" | `55b26526efbb46b38e8666abf8877599` | fila presente; Sección y anchor idénticos (comparación visual) |
| 19 | `CHARTER:FAILURES-001` | L87 · "3.1" | L23 · "3.1" | `3eb938befc42805f9285f417aa359826` | fila presente; Sección y anchor idénticos (comparación visual) |
| 20 | `CHARTER:FAILURES-002` | L88 · "3.2" | L24 · "3.2" | `3eb938befc4280f29959f58b132ac9cb` | fila presente; Sección y anchor idénticos (comparación visual) |
| 21 | `CHARTER:FAILURES-003` | L89 · "3.3" | L25 · "3.3" | `3eb938befc4280998c78cf5f4df4689d` | fila presente; Sección y anchor idénticos (comparación visual) |
| 22 | `CHARTER:FAILURES-004` | L90 · "3.4" | L26 · "3.4" | `119fab7b2a2340ab86a346cbd20b5a54` | fila presente; Sección y anchor idénticos (comparación visual) |
| 23 | `CHARTER:FAILURES-005` | L91 · "3.5" | L27 · "3.5" | `78ae3afe77e949b3a25941edc42e0d86` | fila presente; Sección y anchor idénticos (comparación visual) |
| 24 | `CHARTER:NON-NEGOTIABLES-001` | L92 · "4.1" | L28 · "4.1" | `3eb938befc4280499cb9f08227656612` | fila presente; Sección y anchor idénticos (comparación visual) |
| 25 | `CHARTER:NON-NEGOTIABLES-002` | L93 · "4.2" | L29 · "4.2" | `3eb938befc428061a047e730d71fe71c` | fila presente; Sección y anchor idénticos (comparación visual) |
| 26 | `CHARTER:NON-NEGOTIABLES-003` | L94 · "4.3" | L30 · "4.3" | `3eb938befc4280519ae1d3aac599e87f` | fila presente; Sección y anchor idénticos (comparación visual) |
| 27 | `CHARTER:NON-NEGOTIABLES-004` | L95 · "4.4" | L31 · "4.4" | `3eb938befc4280e69881deea2667da7c` | fila presente; Sección y anchor idénticos (comparación visual) |
| 28 | `CHARTER:NON-NEGOTIABLES-005` | L96 · "4.5" | L32 · "4.5" | `3eb938befc42808b90e5f40c88c56fcd` | fila presente; Sección y anchor idénticos (comparación visual) |
| 29 | `CHARTER:NON-NEGOTIABLES-006` | L97 · "4.6" | L33 · "4.6" | `179d400507a140efbdf0f2ee95bea187` | fila presente; Sección y anchor idénticos (comparación visual) |
| 30 | `CHARTER:NON-NEGOTIABLES-007` | L98 · "4.7" | L34 · "4.7" | `bb64e1aef10d4cdb94a23241d2c343e6` | fila presente; Sección y anchor idénticos (comparación visual) |
| 31 | `CHARTER:NON-NEGOTIABLES-008` | L99 · "4.8" | L35 · "4.8" | `b9ca36b00b124df9be3db39c0a629e3d` | fila presente; Sección y anchor idénticos (comparación visual) |
| 32 | `CHARTER:NON-NEGOTIABLES-009` | L100 · "4.9" | L36 · "4.9" | `d756328198ed4ea4bb7f39f7bb6027b7` | fila presente; Sección y anchor idénticos (comparación visual) |
| 33 | `CHARTER:NON-NEGOTIABLES-010` | L101 · "4.10" | L37 · "4.10" | `6cd49fcd84bd4a0eba084b1b0ab10ca1` | fila presente; Sección y anchor idénticos (comparación visual) |
| 34 | `CHARTER:MILESTONES-001` | L102 · "5.1" | L38 · "5.1" | `3eb938befc4280eb9ad8ce382d23dd35` | fila presente; Sección y anchor idénticos (comparación visual) |
| 35 | `CHARTER:MILESTONES-002` | L103 · "5.2" | L39 · "5.2" | `3eb938befc4280c0bf5dc992ed50be72` | fila presente; Sección y anchor idénticos (comparación visual) |
| 36 | `CHARTER:MILESTONES-003` | L104 · "5.3" | L40 · "5.3" | `3eb938befc4280658fd9d6c19954a7ea` | fila presente; Sección y anchor idénticos (comparación visual) |
| 37 | `CHARTER:MILESTONES-004` | L105 · "5.4" | L41 · "5.4" | `01cf0330464a4dbc97d1584d4176dd41` | fila presente; Sección y anchor idénticos (comparación visual) |
| 38 | `CHARTER:MILESTONES-005` | L106 · "5.5" | L42 · "5.5" | `301a87b2a0f841ce8917c35189fbb99a` | fila presente; Sección y anchor idénticos (comparación visual) |

| Observación spec↔MD | Cita | Hecho |
|---|---|---|
| **[⚠ divergencia spec↔MD]** nodos raíz | spec: `{"id": "CHARTER:PURPOSE", "seccion": "01"…}` … `CHARTER:CONTINUITY … "07"` (L68-74); MD: `CHARTER:PURPOSE … \| 1. \|`, `NON-NEGOTIABLES \| 4. \|`, `STATUS \| 7. \|`, `MILESTONES \| 5. \|`, `DECISIONS \| 2. \|`, `FAILURES \| 3. \|`, `CONTINUITY \| 6. \|` | Los 7 valores `seccion` hardcodeados (01–07, orden PURPOSE/NON-NEG/STATUS/MILESTONES/DECISIONS/FAILURES/CONTINUITY) **no coinciden** con la numeración viva (1,4,7,5,2,3,6). El MD muestra la viva (con punto final, que es lo que captura `SECTION_HEADING_CAPTURE_RE = ^([\w.]+)` de `generate_census.py:493`). Los 31 sub-nodos sí coinciden (spec alineado por PR #18 según Change Log). |
| **[⚠ divergencia nombre spec↔título vivo]** | `nombre` del spec (L68-74) vs. headings en `PROJECT_CHARTER.md` L15, 56, 157, 206, 237, 283, 344 y TOC Notion | [EJEC-LOCAL] `nombre` del spec == título del heading vivo solo en **12 de 38**. Los 7 raíz difieren: `Propósito del Proyecto`↔`Génesis y propósito` · `Principios No Negociables`↔`Reglas no negociables (consolidadas)` · `Estatus del Proyecto`↔`Estado de este documento` · `Hitos y Milestones`↔`Trayectoria esperada — hitos de fase, no lista de tareas` · `Registro de Decisiones`↔`Cronología de decisiones estructurales mayores` · `Registro de Fallos`↔`Fracasos conocidos (para no repetir)` · `Continuidad Operativa`↔`Protocolo de continuidad entre agentes y sesiones`. Otros 19 sub-nodos son títulos abreviados (p. ej. `DECISIONS-011`: spec `…gatekeeper exclusivo del Charter` vs. vivo `…gatekeeper exclusivo de cambios al Charter`). Census Notion muestra los nombres del spec (no los vivos). |
| Censo Notion: propiedades | Notion Census (fetch público): `Versión v9.22.26` · `Status Active` · `Fecha de actualización Sep 30` · `Page ID 394938befc4281e6a381e3869e60d89` | La propiedad `Page ID` se renderiza con 31 caracteres (la página real tiene 32: `394938befc4281e6a381e3869e60d89d`). Dato crudo del render; no se interpreta. |
| Estado del sync a Notion | Change Log ACTIVE L6: `MD en main desde v9.22.24; sync a Notion pendiente` · L17: `Pendientes en orden: vcensus --sync-to-notion --yes` | **[⚠ CONTRADICCIÓN changelog↔estado vivo]** El Census Notion (render público, hoy) **ya contiene** las 38 filas `CHARTER:` con anchors idénticos al `.md`. No es posible saber desde aquí quién/cuándo lo hizo; `vcensus --sync-to-notion` específicamente: [REQUIERE EJECUCIÓN — NO VERIFICABLE POR LECTURA]. |

---

## D. Reglas de detección y prefijos válidos

| Archivo:línea | Cita literal | Qué hace respecto al Charter |
|---|---|---|
| `Layer_1/scripts/generate_census.py:38` | `VALID_PREFIXES = ("KERNEL:", "MANUAL:", "CANON:", "CAREER_CANON:", "SP:", "ALIASES:", "CHANGELOG:", "CHANGELOG_ARCHIVO:", "BRIEF:", "CHARTER:")` | `"CHARTER:"` presente (10.º de 10). Usado en `extract_ids_from_rich_text` (L487) → sin este prefijo el generador no extrae ningún ID `CHARTER:`. |
| `Layer_1/scripts/normalize_heading_ids.py:76` | `VALID_PREFIXES = ("KERNEL:", "MANUAL:", "CANON:", "CAREER_CANON:", "SP:", "ALIASES:", "CHANGELOG:", "CHANGELOG_ARCHIVO:", "CHARTER:")` | `"CHARTER:"` presente (9.º de 9). **No incluye `"BRIEF:"`** (difiere de las otras dos tuplas). |
| `normalize_heading_ids.py:78-86` (`DOCUMENTS` completo) | `"System Prompt": "37b938be-…",` `"Manual": "372938be-…",` `"Kernel": "377938be-…",` `"Career Canon": "377938be-…",` `"Aliases": "37c938be-…",` `"Change Log": "390938be-…",` `"Project Charter": "f87938be-fc42-8263-a305-819877d2245f",` | Charter presente (L85, 7.º y último de 7). `DOCUMENTS` de este módulo **no** contiene Navigation Brief. |
| `normalize_heading_ids.py:94` y `:165-167` | `SKIP_DOCS_FOR_HEADING_AUDIT = {"Change Log"}` / `for doc_name, page_id in DOCUMENTS.items(): if doc_name in SKIP_DOCS_FOR_HEADING_AUDIT: continue` | El Charter **no** está en la lista de exclusión: su árbol de bloques entra a la auditoría de headings. |
| `normalize_heading_ids.py:50, 184, 192-200` | `from vantage_id_rules import classify_heading, suggest_canonical_heading` · `status = classify_heading(plain, id_str)` · `if status in ("malformed", "ok_legacy_sectioned"):` … `"suggested_fix": suggest_canonical_heading(plain, id_str),` | Flujo de auditoría aplicado a headings del Charter. |
| `normalize_heading_ids.py:209-236, 251` | `def apply_fix(finding)` … `requests.patch(f"https://api.notion.com/v1/blocks/{block_id}", …)` · `parser.add_argument("--apply", …)` | Con `--apply`, el script **puede sobrescribir headings** de cualquier doc de `DOCUMENTS`, Charter incluido. Ejecución real [REQUIERE EJECUCIÓN — NO VERIFICABLE POR LECTURA]. |
| `Layer_1/scripts/vantage_id_rules.py:43-46` | `VALID_PREFIXES = (` / `"KERNEL:", "MANUAL:", "CANON:", "CAREER_CANON:", "SP:",` / `"ALIASES:", "CHANGELOG:", "CHANGELOG_ARCHIVO:", "BRIEF:", "CHARTER:",` / `)` | `"CHARTER:"` presente (10.º de 10). Nota: el módulo **declara** la tupla, pero `normalize_heading_ids.py` define la suya propia (L76) y `ID_PATTERN` (L50 de `vantage_id_rules.py`) es genérico `\b([A-Z][A-Z0-9_]*:[A-Z0-9][A-Z0-9-]*)\b`. |
| `vantage_id_rules.py:31` y `:58,63` | `Padding: sección padre SIEMPRE 2 dígitos ("01".."21").` · `SECTION_HEADING_PREFIX_RE = re.compile(r"^\d{1,2}(?:\.\d+)?\s*(?:[—-]\s*)?")` | Formato canónico declarado por el módulo vs. headings del Charter (`PROJECT_CHARTER.md:15` `## 1. CHARTER:PURPOSE — Génesis y propósito`). |
| `vantage_id_rules.py:224-250` — resultado [EJEC-LOCAL] sobre strings literales del Charter | `classify_heading("1. CHARTER:PURPOSE — Génesis y propósito","CHARTER:PURPOSE")` → `malformed` · `classify_heading("7. CHARTER:STATUS — Estado de este documento",…)` → `malformed` · `classify_heading("2.1 CHARTER:DECISIONS-001 — Separación Class A / Class B",…)` → `ok_sectioned` · `classify_heading("2.10 CHARTER:DECISIONS-010 — Creación de este Charter",…)` → `ok_sectioned` | [EJEC-LOCAL] Corrida sobre los 38 headings `CHARTER:` de `PROJECT_CHARTER.md` (espejo de Notion): **7 `malformed`** (los 7 nodos raíz: `PURPOSE, DECISIONS, FAILURES, NON-NEGOTIABLES, MILESTONES, CONTINUITY, STATUS`, forma `N.` con punto final) y **31 `ok_sectioned`** (los sub-nodos `N.n`). `suggest_canonical_heading("1. CHARTER:PURPOSE — Génesis y propósito","CHARTER:PURPOSE")` devuelve `01 CHARTER:PURPOSE — .  — Génesis y propósito`. Comportamiento del script completo contra Notion vivo: [REQUIERE EJECUCIÓN — NO VERIFICABLE POR LECTURA]. |
| Otros módulos con lista propia de prefijos o de docs fundacionales (rastreo `CHARTER`/`CHANGELOG_ARCHIVO:`/`"BRIEF:"` en `Layer_1/scripts/` y `Layer_4/scripts/`) | `grep -rIn 'CHANGELOG_ARCHIVO:\|"ALIASES:"\|"BRIEF:"\|"CAREER_CANON:"\|"CANON:"' --include=*.py --include=*.sh --include=*.json --include=*.js` (sin `Archive/`) → solo las 3 tuplas anteriores | No hay una 4.ª lista de prefijos. `generate_id_inventory.py` no declara `VALID_PREFIXES` (solo placeholders `PREFIX:*`, L84-90). `apply_hyperlinks_notion.py` **no** declara su tupla: la cita en docstring L24 (`VALID_PREFIXES, DOCUMENTS  ← de generate_census.py`) pero en código solo usa `census.DOCUMENTS` (L89). |
| `Layer_1/scripts/orphan_audit.py:40-41` | `BASE_DIR / "Documentación" / "ACTIVE" / "Manual.md",` / `… "Kernel.md",` | Lista propia de 2 documentos; el Charter no figura (0 menciones). |

---

## E. Health check, verificación de versiones y registry

| Archivo:línea | Cita literal | Qué hace respecto al Charter |
|---|---|---|
| `Layer_1/scripts/health_check.py:29-39` (estructura `DOCS_FUNDACIONALES` completa) | `"V-ALIASES": ("37c938be-fc42-80d4-b9ae-f5969830331b", "Aliases.md"),` `"V-CHANGELOG": ("390938be-…", "Change Log.md"),` `"V-SYSTEM-PROMPT": ("37b938be-…", "System Prompt.md"),` `"V-KERNEL": ("377938be-fc42-805e-…", "Kernel.md"),` `"V-MANUAL": ("372938be-…", "Manual.md"),` `"V-CAREER-CANON":  ("377938be-fc42-8089-…", "Career Canon.md"),` `"V-BRIEF":         ("3a3938be-…", "Brief.md"),` `"V-CHANGELOG-ARCHIVO": ("3ba938be-…", "Changelog Archivo.md"),` **`"V-CHARTER":       ("f87938be-fc42-8263-a305-819877d2245f", "Project Charter.md"),`** | Clave exacta: **`"V-CHARTER"`** (L38), 9.ª de 9 entradas. Nombre de archivo esperado: `"Project Charter.md"`. |
| `health_check.py:168-177` | `for name, (_, filename) in DOCS_FUNDACIONALES.items(): expected_file = ACTIVE_DIR / filename` / `if not expected_file.exists(): missing.append(name)` / `ok(f"{len(DOCS_FUNDACIONALES)} docs fundacionales presentes en ACTIVE/")` | `check_docs_sync` busca `Documentación/ACTIVE/Project Charter.md`. |
| **[⚠ CONTRADICCIÓN código↔código]** `health_check.py:38` vs `vsync_doc.py:109` | `"Project Charter.md"` vs `BASE_DIR / "PROJECT_CHARTER.md"` | El archivo real en `ACTIVE/` es `PROJECT_CHARTER.md`. `ls "Documentación/ACTIVE/Project Charter.md"` → *No such file or directory* (vale en FS sensible o insensible a mayúsculas: difiere también espacio/guion bajo). Lectura estática: `V-CHARTER` cae en `missing` (L171). La corrida de `health_check.py` en sí: [REQUIERE EJECUCIÓN — NO VERIFICABLE POR LECTURA]. El Change Log (ACTIVE L86) declara la entrada con ese mismo literal `"Project Charter.md"`: no contradice el código, pero no detecta el desajuste. |
| `health_check.py:462-463` | `for _, filename in DOCS_FUNDACIONALES.values(): path = ACTIVE_DIR / filename` | `check_vdoc_last` itera también el Charter; con el nombre `"Project Charter.md"` el `path.exists()` (L464) es falso y se omite. |
| `Layer_1/scripts/verify_versions.py:27` | `# Nombres canónicos de los 12 puntos de supervisión (9 fundacionales + VANTAGE hub + ARCHIVEROS + CHARTER).` | Comentario de conteo: 12. |
| `verify_versions.py:33` (lista `DOC_KEYS` completa) | `DOC_KEYS = ["CHANGELOG", "KERNEL", "MANUAL", "CANON", "SP", "ALIASES", "CENSUS", "BRIEF", "VANTAGE", "CHANGELOG_ARCHIVO", "ARCHIVEROS", "CHARTER"]` | `"CHARTER"` es el 12.º y último (12 claves). |
| `verify_versions.py:32, 38-47` | `# CHARTER (Project Charter) también participa en --sync del mismo modo.` … `# BRIEF, VANTAGE, CHANGELOG_ARCHIVO, ARCHIVEROS y CHARTER SÍ viven ya en document_registry` … `CHARTER_FALLBACK_ID = "f87938be-fc42-8263-a305-819877d2245f"` | Declara `CHARTER_FALLBACK_ID` (L47), red de seguridad si el registry pierde la clave. |
| `verify_versions.py:133-172` (`load_document_uuids`, bloque relevante L162-165) | `if key == "CHARTER":` / `val = doc_registry.get(key)` / `uuids[key] = val.replace("-", "") if val else CHARTER_FALLBACK_ID.replace("-", "")` / `continue` | Resolución: primero `document_registry["CHARTER"]`, si falta → `CHARTER_FALLBACK_ID`; ambos sin guiones. Con el JSON actual resuelve vía registry (`resolver_registry_v2.json:54`). |
| `verify_versions.py:550, 952-960, 1003-1009` | `for doc in DOC_KEYS:` (length check, sync, check mode) | El Charter participa en: (a) `--length` (L550), (b) `--sync` comparando su propiedad Versión contra la del CHANGELOG (L952-960), (c) modo lectura (L1003). Ejecución real [REQUIERE EJECUCIÓN — NO VERIFICABLE POR LECTURA]. Render público actual: Charter `Versión v9.22.26`, Census `Versión v9.22.26`. |
| `Layer_1/data/length_baseline.json` (claves) | `['CHANGELOG','KERNEL','MANUAL','CANON','SP','ALIASES','CENSUS','BRIEF','VANTAGE','CHANGELOG_ARCHIVO','ARCHIVEROS']` | **Sin clave `CHARTER`** (11 claves, capturas 2026-08-09). `verify_versions.py:562-570` lo trataría como `[BASELINE INICIAL]` en la primera corrida `--length`. |
| `Layer_1/data/resolver_registry_v2.json:54` (entrada literal) | `"CHARTER":   "f87938be-fc42-8263-a305-819877d2245f"` | Entrada `"CHARTER"` en `document_registry` (L41-55). Claves no-comentario: `KERNEL, MANUAL, CANON, TRACKER, SP, ALIASES, CHANGELOG, CHANGELOG_ARCHIVO, BRIEF, VANTAGE, ARCHIVEROS, CHARTER` = **12**, `CHARTER` última. |
| `resolver_registry_v2.json:42` (fragmento) | `Actualizado (CHARTER): conteo de fundamentales pasa de 10→11 — se incorpora CHARTER al document_registry.` | Comentario dice 11; el dict tiene 12 claves (incluye `TRACKER`). Dato crudo. |
| `Layer_1/scripts/lazy_loader.py:77-83` (consumidor implícito) | `doc_registry = registry.get("document_registry")` … `prefixes = {k for k in doc_registry.keys() if not k.startswith("_")}` / `_authorized_prefixes_cache = frozenset(prefixes)` | **Dependencia indirecta**: `CHARTER` entra en los prefijos autorizados del Lazy Loader por ser clave del registry (0 ocurrencias del string `CHARTER` en `lazy_loader.py`). [EJEC-LOCAL] las claves del registry incluyen `CHARTER`. Ruteo real `CHARTER:<clave>`: [REQUIERE EJECUCIÓN — NO VERIFICABLE POR LECTURA]. |
| `Layer_1/scripts/vload.py:30-45, 54-66` (consumidor implícito) | `doc_registry = registry.get("document_registry")` … `return registry.get(prefix_upper)` | `vload --route CHARTER:…` resolvería el UUID por la clave `CHARTER` (0 ocurrencias del string `CHARTER` en `vload.py`). Ejecución: [REQUIERE EJECUCIÓN — NO VERIFICABLE POR LECTURA]. |
| `registry_seed.json` equivalente | `find . -name '*registry_seed*'` → único: `Figma Sync/registry_seed.json` | Es un seed de campos de CV (`HEADER_NAME`, `SEC_PERFIL_PROFESIONAL_TITLE`, …), **sin** `document_registry` y 0 menciones de `charter`. **No existe** un `registry_seed.json` equivalente de documentos en el repo. |
| `Layer_1/scripts/runtime_identity.py` | — | 0 menciones de `charter`; el Change Log (ACTIVE L89) declara que "usa registry dinámicamente". No verifiqué más allá del grep. |
| `Layer_1/scripts/script_hash_baseline.json` | claves de los scripts del cableado (p. ej. L346, L366, L374, L426) | [EJEC-LOCAL] `sha256(bytes)` (mismo método que `verify_versions.py:651`) vs baseline: **no coinciden** para 11 de los 12 archivos del cableado (solo `mcp_sync_wrapper.sh` coincide; `trigger_sync_after_mcp_write.py` capturado 2026-09-22, `notion_write_wrapper.py` 2026-09-28, el resto 2026-08-27). Global: 118 entradas → 60 coinciden, 48 difieren, 10 archivos ausentes (deriva general preexistente, no específica del Charter). |

---

## F. Hipervínculos

| Archivo:línea | Cita literal | Qué hace respecto al Charter |
|---|---|---|
| `Layer_1/scripts/apply_hyperlinks_notion.py:100-109` (`DOC_KEY_TO_NAME` completo) | `DOC_KEY_TO_NAME = {` `"kernel": "Kernel",` `"system_prompt": "System Prompt",` `"manual": "Manual",` `"career_canon": "Career Canon",` `"aliases": "Aliases",` `"change_log": "Change Log",` `"brief": "Navigation Brief",` **`"project_charter": "Project Charter",`** `}` | El Charter está en el mapa estático de documentos cableables (8 claves). Es la que determina qué docs se procesan. |
| `apply_hyperlinks_notion.py:305-306, 326` | `group.add_argument("--doc", choices=list(DOC_KEY_TO_NAME.keys()))` / `group.add_argument("--all", action="store_true")` / `targets = list(DOC_KEY_TO_NAME.keys()) if args.all else [args.doc]` | `--doc project_charter` válido; `--all` incluye el Charter. |
| `apply_hyperlinks_notion.py:82, 88-89, 241` | `import generate_census as census` / `HEADERS = census.HEADERS` / `DOCUMENTS = census.DOCUMENTS` / `page_id = DOCUMENTS[doc_name]` | El UUID del Charter se toma de `generate_census.DOCUMENTS` (L48), no de un literal propio. |
| `apply_hyperlinks_notion.py:161-178` | `def build_dynamic_mapping(link_index)` … `mapping[id_str] = best["link"]` | El mapping `ID → URL` se arma del `link_index` de `generate_census` (que incluye Charter) → los IDs `CHARTER:*` con DEF resuelto se convierten en hipervínculo **en todos los documentos** procesados cuando aparecen como REF, no solo en el Charter. |
| `apply_hyperlinks_notion.py:65, 96` | `python3 apply_hyperlinks_notion.py --doc project_charter --dry-run` · `EXCLUDE_IDS = set()` | Ejemplo de uso documentado con el Charter; sin exclusiones. Los 31 sub-nodos no tienen tratamiento especial ni lista propia en este script (0 ocurrencias de `CHARTER:`); participan solo como entradas del `link_index` de `generate_census`. |
| `Raycast/vantage-hyperlinks-dry.sh:17` · `Raycast/vantage-hyperlinks-apply.sh:18` | `python3 apply_hyperlinks_notion.py --all` · `python3 apply_hyperlinks_notion.py --all --apply` | Ambos wrappers usan `--all` (Charter incluido). Hacen `cd ~/Documents/03\ Projects/VANTAGE/Layer_4/scripts` y llaman `apply_hyperlinks_notion.py` por ruta relativa; ese archivo **no está en `Layer_4/scripts/`** (vive en `Layer_1/scripts/`). Resolución real: [REQUIERE EJECUCIÓN — NO VERIFICABLE POR LECTURA]. |
| `Layer_1/data/dry_run_hyperlinks.diff` (389 líneas; `--- a/` de L1, L27, L48, L148, L317) | Archivos: `Aliases.md`, `Career Canon.md`, `Kernel.md`, `Manual.md`, `System Prompt.md` | `grep -c -i charter` = **0**. El diff cubre 5 documentos; no incluye Charter, Brief ni Change Log. **No hay anchors `CHARTER:` que contrastar**; por lo tanto no hay discrepancia de anchors Charter en este archivo. (Dato lateral no-Charter: `KERNEL:*` en L56-80 usa prefijo de block-id `39e938befc42…`, mientras el Census usa `3af938befc42…`; el Change Log ACTIVE L15 ya lo registra como pendiente.) |
| Anchors del Charter: Census `.md` ↔ TOC Notion vivo | 38 anchors (tabla C.2) | Coinciden con los del TOC del Charter renderizado por Notion (comparación visual). Ninguna discrepancia de anchor observada. |

---

## G. Tests

| Archivo:línea | Cita literal | Qué hace respecto al Charter |
|---|---|---|
| `tests/`, `Layer_1/tests/`, `Layer_3/tests/`, `Layer_1/scripts/conftest.py` | `grep -rIn -i -e charter -e project_charter -e V-CHARTER` → **0 coincidencias** (exit 2/sin salida) | **Ningún archivo de test menciona el Charter.** |
| Conteos de documentos fundacionales en tests | `grep` de `DOCS_FUNDACIONALES`, `FOUNDATIONAL`, `fundacional`, `len(…DOC…)`, `== 8/9/11` en tests | **0 coincidencias.** El único test con `document_registry` es `tests/test_vload.py:30-35`, fixture de 3 claves (`KERNEL`, `MANUAL`, `CANON`) + `_comment`; sin asserts sobre el Charter ni sobre un conteo de docs fundacionales. |
| Archivos de test existentes | `tests/test_vload.py`; `Layer_1/tests/test_{authorized_fixes,class_b_origin_invariant,dedup,gate_logic,graph_layer,health_check,profile_fit,scoring,status_report}.py`; `Layer_3/tests/test_layer_3_mail.py`; `Archive/test_vload.py` | No existe ningún `test_vdoc*.py` ni `test_vsync*.py` (`find`), ni en el árbol actual ni en el historial visible (`git log --all -- '*test_vdoc*' '*test_vsync*'` vacío; historia aplanada). `test_health_check.py` solo cubre `check_auto_link_corruption` (docstring L1-7); no toca `DOCS_FUNDACIONALES`. |
| **[⚠ CONTRADICCIÓN]** `Documentación/ACTIVE/Change Log.md:58, 66, 71` (entrada Layer_4/GROK) | L58: `- tests/test_vdoc.py (o suit de tests equivalente en tests/)` · L66: `Ajustes en la suite de pruebas unitarias (test_vdoc.py / test_vsync.py) para validar dinámicamente la presencia de los 9 documentos y verificar la resolución correcta del alias charter desde CLI.` · L71: `Suite de pruebas unitarias: Ejecución de pytest en el directorio de pruebas validando assertions de 9 fundacionales sin regresiones.` | El changelog declara tests modificados/ejecutados para el Charter; **el repo no contiene esos tests ni cualquier assert sobre Charter**. Además `charter_integration.patch` (A/B) no toca ningún archivo de `tests/`. La entrada los redacta con "o suit de tests equivalente" (sin ruta exacta). |

---

## H. Menciones sueltas (texto libre `CHARTER`, sin `Archive/` ni `PROJECT_CHARTER.md`)

Búsqueda: `git ls-files -z | grep -zv '^Archive/' | xargs -0 grep -l -a -i charter` → 21 archivos (más `PROJECT_CHARTER.md` excluido). Los de A–G ya están citados arriba; aquí los no cubiertos y los negativos relevantes.

| Archivo:línea | Cita literal | Qué hace respecto al Charter |
|---|---|---|
| `Documentación/ACTIVE/System Prompt.md:68` | `### 01.4 SP:BOOTLOADER-004 — Agente Principal y Gatekeeper del Charter` | Sección del SP que declara el rol de gatekeeper. |
| `System Prompt.md:69-71` | `CLAUDE/MAIN es el agente principal de continuidad de contexto de VANTAGE y el único evaluador autorizado de solicitudes de cambio al V \| PROJECT CHARTER.` | Fuente normativa del rol de CLAUDE/MAIN. |
| `System Prompt.md:81-84` | `Ningún agente escribe directamente sobre el Charter, bajo ninguna vía.` / `Toda propuesta de cambio … entra exclusivamente como ticket Task Tracker, tipo CHARTER.` | Regla de no-escritura directa. (Contraste técnico: ver `vsync_doc.py:747-751` y `normalize_heading_ids.py:209-236`, rutas de código que escriben a Notion si se ejecutan sobre el Charter.) |
| `System Prompt.md:94-95` | `CLAUDE/MAIN no evalúa un ticket CHARTER sin haber fetcheado el documento completo en esa misma sesión — ver Bootstrap Universal…` | Precondición de lectura; "Bootstrap Universal" no está en el SP del repo (0 coincidencias de esa cadena aparte de esta línea). |
| `System Prompt.md:98-110` (`SP:SYNC-RULE`) | `Toda sesión opera bajo la regla de validación cruzada de los siguientes diez documentos fundacionales:` … `- NAVIGATION BRIEF` / `- VANTAGE CENTRAL HUB` | **[⚠ contraste]** La lista de 10 del SP **no incluye** el Charter, mientras `verify_versions.py:33` sí lo incluye en `DOC_KEYS` (12) y `SP:SYNC-RULE` L112 fija la Regla de Versión Única contra el CHANGELOG. |
| `hermes.md:23` | `2. Recupera SYSTEM PROMPT,  ID CENSUS y PROJECT CHARTER` | Bootstrap de Hermes: fetch del Charter al iniciar sesión. |
| `hermes.md:27` | `* PROJECT CHARTER → f87938be-fc42-8263-a305-819877d2245f (nuevo — contexto de génesis, decisiones estructurales, fracasos conocidos, reglas no negociables; ver SP:BOOTLOADER-004 para conocer del rol de gatekeeping, exclusivo de CLAUDE/MAIN)` | UUID del Charter como fuente de bootstrap (MCP-Notion, `notion-fetch`). |
| `handoffs/CONTRATO_MISTRAL_CHARTER_NODES.md:4, 12, 22` | `Gatekeeper del Charter: CLAUDE/MAIN (CHARTER:DECISIONS-011)` · `grep -c '"id": "CHARTER:' Layer_1/scripts/generate_census.py` → debe devolver **38** · `Convertir los 31 sub-nodos del V \| PROJECT CHARTER (Notion page f87938be-fc42-8263-a305-819877d2245f)…` | Contrato de la migración de 31 sub-nodos a `heading_3`. [EJEC-LOCAL] `grep -c '"id": "CHARTER:'` sobre `generate_census.py` = **38** ✔ (coincide con P1 del contrato). Regex del contrato L115: `^\d+\.\d+ CHARTER:(DECISIONS\|FAILURES\|NON-NEGOTIABLES\|MILESTONES)-\d{3} — .+`. |
| `charter_integration.patch` (83 líneas) | `+    "project_charter": {"notion_id": "f87938be-fc42-8263-a305-819877d2245f", "local_file": BASE_DIR / "PROJECT_CHARTER.md", "label": "PROJECT CHARTER"},` (L7) · `+    "f87938be-fc42-8263-a305-819877d2245f": "project_charter",` (L63, L83) | Patch sobre 4 archivos de `Layer_4/scripts/` (`vsync_doc.py`, `vdoc.py`, `trigger_sync_after_mcp_write.py`, `notion_write_wrapper.py`). Ya aplicado en HEAD. **No toca** `MCP_SYNC_HOOK_README.md` ni `tests/`. Su hunk de `trigger_sync…` cambia `(8)`→`(9)` en el comentario L31 pero no el docstring L7. |
| `Documentación/ACTIVE/Change Log.md` y `Documentación/Change Log.md` | ACTIVE: L5-6, 9-19 (PR #17/#18 census+contrato), 21-35 (mapeo granular), 36-51 (migración Notion), 52-75 (Layer_4), 76-93 (Layer_1), 96-111 (Littlebird §7) · `Documentación/Change Log.md`: L6-14, 20-30, 41-50, 62-72, 80-82 | Dos copias distintas (183 y 685 líneas, `diff` las diferencia). Contienen las narrativas contrastadas en la tabla de contradicciones. |
| `Layer_1/data/inventario_ids.csv` · `inventario_ids_por_id.md` · `inventario_huerfanos.md` | `grep -c CHARTER` = 0 en los tres | Artefactos de `generate_id_inventory.py` **sin ningún ID `CHARTER:`**. El generador recorre `*.md` bajo la raíz dada (`generate_id_inventory.py:170` `root.rglob("*.md")`, uso L19 `--root ../Documentación/ACTIVE`), por lo que una corrida nueva alcanzaría `PROJECT_CHARTER.md`; los datos en HEAD no lo reflejan. |
| Negativos (0 menciones de `charter`, sin cambios) | `Documentación/ACTIVE/{Kernel,Manual,Brief,Aliases,Career Canon,Changelog Archivo}.md`; `README.md`; `MANUAL.md`; `Layer_1/VANTAGE_ARCHITECTURE.md`; `Layer_1/layer_1_routine.md`; `skills/*`; `Raycast/*`; `Dashboard/*`; `Layer_3/*`; `Layer_4/com.vantage.gitsync.plist`; `Layer_4/scripts/{git_sync,vsum,vdoc_nblm}.py`, `mcp_sync_wrapper.sh` | Ninguna referencia directa. (Kernel/Manual/Brief/Aliases/Career Canon locales no describen al Charter.) |
| `Documentación/ACTIVE/PROJECT_CHARTER.md:326-335, 361-365, 380-384, 392-394` (fuera de H por contrato; se cita solo como fuente de contradicción) | `A la fecha de creación de este documento, el Charter no tiene un prefijo canónico dado de alta en document_registry/registry_seed.json — por lo tanto, el fallback de vload --route CHARTER:... no funciona todavía` · `Numeración de nodos e IDs … aplicada en este documento, alta en Census pendiente.` · `Si entra o no a la vigilancia de vversions/Regla de Versión Única…` | Ver tabla de contradicciones. El Notion vivo (render público, chunk 5) contiene el mismo texto de §7. |

---

## I. Contradicciones changelog ↔ código ↔ estado (reportadas, no resueltas)

| # | Declaración (cita) | Código / estado real (cita) |
|---|---|---|
| 1 | `Change Log ACTIVE:58,66,71` — tests `test_vdoc.py / test_vsync.py` ajustados; "pytest … assertions de 9 fundacionales" | No existen tales archivos ni asserts sobre Charter (G). `charter_integration.patch` no incluye tests. |
| 2 | `Change Log ACTIVE:65` — README "(8 → 9)" actualizado | `MCP_SYNC_HOOK_README.md:7` dice 9 pero `:33` aún dice `lista de los 8 documentos`. |
| 3 | `Change Log ACTIVE:64` — "incremento del inventario fundacional de 8 a 9" en trigger y wrapper | Encabezado `(9)` y 9 entradas ✔ (`trigger…:31-43`, `notion_write_wrapper.py:27-38`), pero el docstring `trigger_sync_after_mcp_write.py:7` sigue con `8 documentos fundacionales` y lista 6; `mcp_sync_wrapper.sh:6` dice 6. |
| 4 | `Change Log ACTIVE:86` — `(H-01) agregado de "V-CHARTER": (…, "Project Charter.md")` | El archivo local se llama `PROJECT_CHARTER.md` (`vsync_doc.py:109`); `health_check.py:38` busca `Project Charter.md`, que no existe en `ACTIVE/` (`ls` verificado). |
| 5 | `Change Log ACTIVE:87` — `conteo de fundamentales pasa de 10→11` | `resolver_registry_v2.json:43-54` tiene 12 claves no-comentario; `verify_versions.py:27` habla de "12 puntos de supervisión". |
| 6 | `Change Log ACTIVE:6, 17` — `sync a Notion pendiente` / `Pendientes … vcensus --sync-to-notion --yes` | Census Notion (render público hoy) ya muestra las 38 filas `CHARTER:` con anchors idénticos al `.md` (C.2). Quién/cuándo: no determinable. |
| 7 | `PROJECT_CHARTER.md:327-329` — `el Charter no tiene un prefijo canónico dado de alta en document_registry/registry_seed.json` | `resolver_registry_v2.json:54` tiene `"CHARTER"`; `registry_seed.json` (Figma Sync) no es un registry documental y no existe equivalente. |
| 8 | `PROJECT_CHARTER.md:365` — `alta en Census pendiente` · `:380-382` `el alta formal del prefijo CHARTER: … y su incorporación al ID Census` pendiente | `generate_census.py:38, 65-108` y `V_ID_CENSUS_PRODUCTION.md:5-42` ya tienen `CHARTER:` y 38 filas. |
| 9 | `PROJECT_CHARTER.md:392-394` — `Si entra o no a la vigilancia de vversions…` pendiente de decisión | `verify_versions.py:33` incluye `"CHARTER"` en `DOC_KEYS` y `:162-165` lo resuelve; `SP:SYNC-RULE` (`System Prompt.md:100-110`) sigue listando 10 docs sin Charter. |
| 10 | `PROJECT_CHARTER.md:329` — `vload --route CHARTER:... no funciona todavía` | `vload.py:45, 66` resolvería por clave del `document_registry`, que hoy contiene `CHARTER`. Comportamiento real: [REQUIERE EJECUCIÓN — NO VERIFICABLE POR LECTURA]. |
| 11 | `Change Log ACTIVE:14(c), 19(T-03)` — ruta absoluta "en L1256" y `vdoc.py L34` | `generate_census.py:1277` y `vdoc.py:35` (desfase de líneas; hechos equivalentes). |
| 12 | `Change Log ACTIVE:89` — `apply_hyperlinks_notion.py (reusa VALID_PREFIXES y DOCUMENTS de generate_census.py, ya cubierto indirectamente)` | Reusa `DOCUMENTS` (`:89`); **no** reusa `VALID_PREFIXES` en código (solo docstring `:24`); además tiene su propia entrada estática `"project_charter"` (`:108`). |
| 13 | `Change Log ACTIVE:34, 50` — `IDs afectados: Ninguno nuevo` (v9.22.23/24) | Ya corregido por el propio changelog (`:14(a)`, `:18`): 31 IDs nuevos vía PR #17. Verificado en código: 38 entradas `CHARTER:` (7+31), 294 totales. La corrección es consistente con el código. |
| 14 | `Change Log ACTIVE:10` (G-08) — eliminada copia espuria del bloque Charter en `find_census_spec_end()` | `generate_census.py`: ocurrencias de `CHARTER` solo en L38, 48, 59, 66-106, 674 (+ `Charter` en nombre L362); ninguna dentro de `find_census_spec_end` (L724+). Consistente. |
| 15 | `MCP_SYNC_HOOK_README.md:33` — `notion_write_wrapper.py … no es usado por ningún script del repo` | Verificado: ningún módulo lo importa (B). Consistente. |
| 16 | `Change Log ACTIVE:9` — `vdoc.py no invoca generate_census.py; flags … --debug-id, --sync-to-notion, --yes, --no-sync-version` | `vdoc.py` no contiene `generate_census`; `generate_census.py:1240-1261` parsea esos 4 flags más `--auto-fix-orphans`. Consistente. |

---

## J. Mapa resumen

| Componente | Toca al Charter cómo | Estado |
|---|---|---|
| `vsync_doc.py` `DOCS["project_charter"]` (L107-111) | Clave canónica + UUID + espejo `PROJECT_CHARTER.md`; target por defecto de toda corrida sin `--doc`; `--direction local` = ruta de escritura a Notion | Registro: **confirmado por lectura**. Ejecución/escritura: **REQUIERE EJECUCIÓN** |
| `.vsync_manifest.json:11` | Hash del último sync del Charter | **Confirmado por lectura** ([EJEC-LOCAL] sha256 coincide con `PROJECT_CHARTER.md` en HEAD) |
| `vdoc.py` (`DOCS` L42, `DOC_ALIASES` L44-47) | Alias `charter` → `project_charter`; whitelist CLI | **Confirmado por lectura** |
| `trigger_sync_after_mcp_write.py` `FOUNDATIONAL_DOCS` (L42) | UUID Charter → lanza `vsync_doc --direction notion --doc project_charter` en background | Lista: **confirmado por lectura** · Disparo real: **REQUIERE EJECUCIÓN** · Docstring desactualizado (L7) |
| `notion_write_wrapper.py` `FOUNDATIONAL_DOCS` (L37) | UUID Charter; stub sin escritura real, sin consumidores | **Confirmado por lectura** (stub) |
| `MCP_SYNC_HOOK_README.md` (L7, L19, L33, L37-38) | Documenta Charter en tabla de 9; declara que el hook no intercepta writes MCP automáticamente | **Confirmado por lectura**; conteo interno inconsistente (L33) |
| `mcp_sync_wrapper.sh` | Delega al trigger; sin lista propia | **Confirmado por lectura** |
| `generate_census.py` `CENSUS_SPEC` (L65-108) | 38 entradas `CHARTER:` únicas (7 raíz + 31 sub-nodos) | **Confirmado por lectura** ([EJEC-LOCAL] AST: 294 / 0 dup) |
| `generate_census.py` `VALID_PREFIXES` (L38), `DOCUMENTS` (L48), `DOC_PRIORITY` (L59), `infer_section_from_id` (L674) | Detección/indexación del Charter en el link_index | **Confirmado por lectura** |
| `V_ID_CENSUS_PRODUCTION.md` (L1-42, 306) | 38 filas `CHARTER:` con Sección y anchor; 0 huérfanos | **Confirmado por lectura** (coincide con `CENSUS_SPEC`, salvo Sección raíz que viene del heading vivo) |
| Census Notion (`394938be…`) | Sección PROJECT CHARTER de 38 filas | Coincide con `.md` por **fetch público + comparación visual**; `--sync-to-notion` en sí: **REQUIERE EJECUCIÓN** |
| `normalize_heading_ids.py` (L76, L85, L165, L209-236) | Prefijo + documento auditable + ruta `--apply` (PATCH) sobre headings del Charter; headings raíz `malformed` por la función pura | Config: **confirmado por lectura** · Comportamiento: **REQUIERE EJECUCIÓN** |
| `vantage_id_rules.py` `VALID_PREFIXES` (L43-46), `classify_heading` (L224) | Reglas únicas de detección; headings `N.` clasifican `malformed`, `N.n` `ok_sectioned` | **Confirmado por lectura / EJEC-LOCAL** |
| `apply_hyperlinks_notion.py` (L100-109, L89, L305-326) | Charter en `DOC_KEY_TO_NAME`; UUID vía `census.DOCUMENTS`; IDs `CHARTER:*` se hipervinculan como REF en otros docs; `--all` lo incluye | **Confirmado por lectura** · Corrida: **REQUIERE EJECUCIÓN** |
| `dry_run_hyperlinks.diff` | 0 menciones de Charter (cubre 5 docs) | **Confirmado por lectura** |
| `health_check.py` `DOCS_FUNDACIONALES["V-CHARTER"]` (L38) | Chequeo de existencia de espejo local; archivo esperado `Project Charter.md` ≠ `PROJECT_CHARTER.md` | Config: **confirmado por lectura** · Resultado de la corrida: **REQUIERE EJECUCIÓN** (archivo esperado inexistente verificado por `ls`) |
| `verify_versions.py` `DOC_KEYS` (L33), `CHARTER_FALLBACK_ID` (L47), `load_document_uuids` (L162-165) | Supervisión de versión/longitud/sync del Charter | Config: **confirmado por lectura** · Corrida: **REQUIERE EJECUCIÓN** |
| `length_baseline.json` | Sin clave `CHARTER` | **Confirmado por lectura** |
| `resolver_registry_v2.json:54` | `document_registry["CHARTER"]` (12 claves) | **Confirmado por lectura** |
| `lazy_loader.py` (L77-83) / `vload.py` (L45, L66) | Consumo indirecto: `CHARTER` como prefijo autorizado / ruteable por ser clave del registry | Mecanismo: **confirmado por lectura** · Ruteo real: **REQUIERE EJECUCIÓN** |
| `Figma Sync/registry_seed.json` | No es equivalente (seed de CV, sin `document_registry`) | **Confirmado por lectura** |
| `script_hash_baseline.json` | 11/12 scripts del cableado difieren del baseline (deriva general 48/118) | **Confirmado por lectura / EJEC-LOCAL**; veredicto oficial: **REQUIERE EJECUCIÓN** (`--scripts-drift`) |
| `tests/`, `Layer_1/tests/`, `Layer_3/tests/` | 0 referencias al Charter | **Confirmado por lectura** |
| `System Prompt.md` L68-96 (`SP:BOOTLOADER-004`) y L98-110 (`SP:SYNC-RULE`) | Rol de gatekeeper; lista de 10 docs sin Charter | **Confirmado por lectura** (espejo ACTIVE; no se verificó el SP vivo) |
| `hermes.md:23-27` | Bootstrap fetch del Charter por UUID | **Confirmado por lectura** |
| `handoffs/CONTRATO_MISTRAL_CHARTER_NODES.md`, `charter_integration.patch`, Change Logs | Documentación/historia del cableado | **Confirmado por lectura** |
| `Raycast/vantage-vdoc-*.sh`, `vantage-hyperlinks-*.sh` | Incluyen el Charter implícitamente (sin `--doc` / `--all`) | **Confirmado por lectura** · Ejecución: **REQUIERE EJECUCIÓN** |
| `inventario_ids*.csv/md`, `inventario_huerfanos.md` | 0 IDs `CHARTER:`; el generador sí alcanzaría `PROJECT_CHARTER.md` | **Confirmado por lectura** |
| `V_ID_CENSUS_PRODUCTION.pdf` | — | **No verificable** en esta sesión (sin herramienta de PDF) |
