## 22 MANUAL:SCRIPT-GLOSSARY
Glosario de Scripts — Referencia Operativa en Humano

> Propósito: traducir cada script/wrapper del árbol activo (Layer_1, Layer_3, Layer_4, Dashboard, Raycast) a lenguaje operativo — qué hace, por qué existe, y un caso de uso concreto por cada flag disponible. Este documento es el "manual de instrucciones" legible; la Script Library (Notion DB) es su índice corto y estructurado. Se referencian entre sí — ver [MANUAL:SCRIPT-GLOSSARY-XREF](#) al final.

> Nodo padre de [KERNEL:DOMAIN-ARCHITECTURE] — organizado por capa, no alfabéticamente, para que la lectura secuencial siga el flujo real del sistema (L1 → L3 → L4 → Dashboard → Raycast).

---

### 22.1 MANUAL:SCRIPT-GLOSSARY-L1
Layer 1 — Active Recon & Core Pipeline

#### `layer_1_run.py`
**Qué hace:** Motor principal del pipeline L1 — ejecuta las fases de scoring, gating y deduplicación sobre el Tracker.
**Flags:**
| Flag | Caso de uso |
|---|---|
| `--dry-run` | Antes de correr el pipeline completo en un día con muchos feeds nuevos, corre con `--dry-run` para ver qué escribiría sin comprometer el Tracker — útil si sospechas que un feed trae datos sucios. |
| `--dedup-audit` | Al cerrar el ciclo semanal de L1, agrégalo para que el mismo comando dispare `dedup_opportunities.py` como subproceso y te dé el reporte fuzzy sin correr dos comandos separados. |

#### `feed_processor.py`
**Qué hace:** Ingiere un JSON de feed (L1/L2/L3) y crea/actualiza registros en el Tracker.
**Flags:**
| Flag | Caso de uso |
|---|---|
| `--file` (requerido) | Siempre necesario — apunta al JSON del feed a procesar. Rutas relativas se resuelven desde `Layer_1/`. |
| `--layer {1,2,3}` | Si estás cargando un feed que viene de investigación manual en Perplexity (no de L1 automatizado), usa `--layer 2` para que el Tracker lo etiquete correctamente como fuente estratégica. |
| `--fast` | Encontraste UNA vacante urgente fuera de tu ciclo semanal (ej. alguien te la compartió por WhatsApp) — usa `--fast` para meterla sola sin esperar al batch de los lunes. Rechaza feeds con más de un item. |
| `--interactive` | Cuando el feed trae vacantes de calidad mixta y quieres decidir una por una (`[S]í/[O]mitir/[Q]uit`) en vez de que todo se escriba automáticamente. Ojo: si eliges Quit a medio camino, lo ya escrito no se revierte. |

#### `generate_census.py`
**Qué hace:** Genera el ID Census — barrido completo de IDs canónicos en los 9 documentos fundacionales, detecta huérfanos.
**Flags:**
| Flag | Caso de uso |
|---|---|
| `--debug-id <id1> <id2> …` | Ya sabes que `KERNEL:SCHEMA-008` está fallando en el census y no quieres esperar el barrido completo — pásalo directo y te da diagnóstico quirúrgico de esos IDs específicos. |

#### `generate_entity_index_v2.py`
**Qué hace:** Reconstruye el índice de entidades (`entity_index_v2.json`), el grafo de relaciones y los backlinks — la base de datos interna que usa `vantage.py ask/query`.
**Flags:**
| Flag | Caso de uso |
|---|---|
| `--limit <N>` | Estás probando un cambio en la lógica de indexado y no quieres esperar a que procese todas las fuentes — límita a N entidades por fuente para iterar rápido. |
| `--out <ruta>` | Quieres generar un índice de prueba sin pisar el archivo real que usa producción — apunta a una ruta temporal. |
| `--skip-graph` | Solo necesitas refrescar el índice de entidades (para `vantage.py query`) y no te importa el grafo/backlinks en este momento — ahorra tiempo de corrida. |

#### `generate_id_inventory.py`
**Qué hace:** Escanea un árbol de archivos y genera un inventario CSV/Markdown de todas las definiciones y referencias de IDs canónicos encontradas.
**Flags:**
| Flag | Caso de uso |
|---|---|
| `--root <ruta>` (requerido) | Quieres auditar solo una subcarpeta (ej. solo `Layer_1/`) en vez de todo VANTAGE — acota el escaneo. |
| `--out <ruta>` | ⚠️ Nota real: el default NO es `./out` como dice el help — es una ruta absoluta fija a tu carpeta `Layer_1/data`. Si corres esto desde otra máquina o usuario, especifica `--out` explícitamente o el inventario se va a una ruta que no existe. |

#### `apply_hyperlinks_notion.py`
**Qué hace:** Aplica el sistema de cross-reference hyperlinks entre documentos fundacionales (PATCH de bloques en Notion).
**Flags:**
| Flag | Caso de uso |
|---|---|
| `--doc {kernel,system_prompt,manual,career_canon,aliases,change_log,brief}` | Acabas de editar solo el Manual y no quieres re-procesar los 7 documentos — corre el ciclo de hyperlinks en uno solo. |
| `--all` | Ciclo completo de housekeeping documental — mutuamente excluyente con `--doc`. |
| `--apply` | El modo real de escritura — sin este flag, cualquier corrida (incluso sin `--dry-run`) es preview únicamente. |
| `--dry-run` | ⚠️ No tiene efecto propio — el script ya es dry-run por default sin `--apply`. Es no-op explícito, no un modo adicional. |

#### `normalize_heading_ids.py`
**Qué hace:** Audita y corrige headings legacy o mal formados en los documentos fundacionales.
**Flags:**
| Flag | Caso de uso |
|---|---|
| `--csv <ruta>` | Quieres revisar en Excel/Numbers qué headings están mal antes de decidir si vale la pena corregirlos — exporta el reporte sin tocar Notion. |
| `--apply` | Ya revisaste el CSV y confirmaste que los fixes son correctos — aplica los reemplazos vía API. |
| `--yes` | Vas a correr `--apply` en un batch grande ya pre-aprobado y no quieres que te pregunte confirmación por cada heading. |

#### `consolidate_duplicates.py`
**Qué hace:** Detecta y fusiona registros duplicados en el Tracker, archivando el sobrante.
**Flags:**
| Flag | Caso de uso |
|---|---|
| `--dry-run` | Antes de fusionar nada, corre esto para ver qué grupos detectaría como duplicados. |
| `--yes` | Ya revisaste el dry-run y confías en el resultado — salta la confirmación interactiva. |
| `--aggressive` | El matching normal (por URL) no está agrupando vacantes que sabes que son la misma posición republicada con URL distinta — usa matching por marca+rol. No fusiona URLs de vacantes genuinamente distintas. |

#### `cross_tracker_match.py`
**Qué hace:** Busca coincidencias entre el Tracker activo y el Archivo Tracker por regla marca+rol.
**Flags:**
| Flag | Caso de uso |
|---|---|
| `--dry-run` | ⚠️ Importante: default es `True` vía `store_true`, y no existe forma de desactivarlo — este script **siempre** es solo-reporte, nunca ejecuta acciones. Si tu intención es que alguna vez actúe, hoy no puede — es candidato para el punto B (documentación transversal) si quieres dejarlo explícito en Kernel. |

#### `dedup_opportunities.py`
**Qué hace:** Auditoría fuzzy de duplicados y limpieza puntual del flag `Dedup_Flag`.
**Uso:**
| Modo | Caso de uso |
|---|---|
| Sin argumentos | Auditoría general — lo que corre `dedup_audit.sh`/Raycast. |
| `--clear <page_id>` | Un registro quedó marcado erróneamente como "Posible duplicado" y quieres limpiar solo ese flag sin re-correr toda la auditoría. ⚠️ Solo accesible desde Terminal directo — el wrapper de Raycast (`dedup_audit.sh`) no lo expone. |

#### `backfill_class_a.py`
**Qué hace:** Backfill de campos Class A (`layer`, `hash`, `Prioridad`) en registros existentes del Tracker.
**Flags:**
| Flag | Caso de uso |
|---|---|
| `--dry-run` | Antes de correr un backfill masivo tras un cambio de schema, revisa qué se llenaría. |

#### `backfill_next_action_select.py`
**Qué hace:** Migra el campo `Next_Action` de texto libre a `select` tipado.
**Flags:**
| Flag | Caso de uso |
|---|---|
| `--execute` | Ya validaste el dry-run (default) y quieres aplicar la conversión real. |

#### `verify_versions.py` (alias `vversions`)
**Qué hace:** Herramienta central de verificación — versión de los 9 fundacionales, gap-report de scripts/skills, e integridad de longitud documental.
**Flags:**
| Flag | Caso de uso |
|---|---|
| `--sync` | Acabas de subir la versión en Change Log y necesitas propagarla a los otros 8 documentos con verificación de escritura. |
| `--bootstrap` | Al abrir sesión, genera el dump read-only de Ledger + Changelog + tickets prioritarios — más barato que pedirle a Claude que haga fetch manual de cada uno. |
| `--scripts` | Sospechas que hay scripts nuevos sin registrar en Script Library — corre esto para el gap-report. (Ver también punto D — `--new-scripts` propuesto). |
| `--skills` | Igual que arriba pero para archivos `.skill`. |
| `--length` | Antes de una sincronización crítica, si sospechas que algún documento se truncó silenciosamente (edición accidental, corte de API), corre esto como sanity check. |
| `--update-baseline` | Solo después de confirmar manualmente que un cambio de longitud fue una edición legítima (no truncamiento) — actualiza el baseline. Requiere `--length`. |

#### `clean_script_library_links.py`
**Qué hace:** Limpia valores de URL corruptos (`http://` mal formados) en Script Library.
**Flags:**
| Flag | Caso de uso |
|---|---|
| `--apply` | Detectaste links rotos en Script Library tras una migración — aplica la limpieza real. Sin el flag, solo lista candidatos. |

#### `backfill_archive_fingerprint.py`
**Qué hace:** Calcula y completa fingerprints de deduplicación en el Archivo Tracker.
**Uso:** Sin flags CLI propios — se corre directo, solo requiere `NOTION_TOKEN`/`NOTION_API_KEY` en el entorno.

#### `notion_utils.py`
**Qué hace:** Cliente HTTP compartido para todas las llamadas a Notion — caché, rate limiting, reintentos. No se invoca directo salvo para diagnóstico.
**Uso (comando posicional):**
| Comando | Caso de uso |
|---|---|
| `metrics` | Quieres ver cuántas llamadas a Notion se han cacheado vs. hecho en vivo en la sesión actual. |
| `clear-cache` | Sospechas que estás viendo datos obsoletos de Notion pese a un cambio reciente — vacía la caché local. |
| `reset-metrics` | Reinicia los contadores de métricas para medir una corrida específica desde cero. |

**Variables de entorno (tuning silencioso — hoy corren con default sin que lo notes):**
| Variable | Default | Caso de uso |
|---|---|---|
| `NOTION_MIN_INTERVAL` | `0.35` (segundos) | Si notas que tus corridas de L1 son lentas y no te importa el riesgo de rate-limit, puedes bajar este intervalo. |
| `NOTION_CACHE_TTL` | `21600` (6h) | Si estás iterando rápido sobre un documento y la caché te da versiones viejas, baja el TTL temporalmente. |
| `NOTION_MAX_RETRIES` | `3` | Súbelo si tu conexión es inestable y ves fallos por timeout en vez de reintentos agotados. |
| `VANTAGE_LOG_LEVEL` | `INFO` | Cambia a `DEBUG` cuando estés troubleshooting un bug de integración con Notion y quieras ver el detalle de cada request. |
| `NOTION_VERSION` | `2022-06-28` (la mayoría) / `2025-09-03` (`resolver_layer_v1.py`) | ⚠️ Nota real: hay inconsistencia entre scripts — mezclar versiones de API en el mismo flujo puede producir HTTP 400 (ya documentado en KERNEL). |

#### `health_check.py`
**Qué hace:** Chequeo de salud del sistema — conectividad, versión, tickets pendientes, estado de git.
**Uso:** Sin flags — se corre directo (via `vantage-health.sh` en Raycast). Exit code 0 = sano, 1 = issues encontrados (no fallo fatal).

#### `vantage.py`
**Qué hace:** CLI unificado de consulta en lenguaje natural sobre el índice de entidades.
**Comandos:**
| Comando | Caso de uso |
|---|---|
| `ask <texto>` | Pregunta abierta en lenguaje natural — une todos los tokens del argumento. |
| `resolve <id>` | Resuelve un ID canónico puntual a su contenido — solo usa el primer token. |
| `context <id>` | Similar a resolve pero trae contexto extendido alrededor del ID. |
| `query <texto>` | Búsqueda estructurada — une todos los tokens. |
| `status` | Estado general del sistema, sin argumentos. |
| `sync` | Reconstruye índice/grafo/backlinks desde Notion — requiere `NOTION_TOKEN`. Costoso, úsalo solo cuando sepas que el índice está desactualizado. |

#### `feedback_loop.py`
**Qué hace:** Calcula métricas de efectividad y conversión sobre el Tracker.
**Flags:**
| Flag | Caso de uso |
|---|---|
| `--json` | Quieres pasar el output a otro script o graficarlo — output máquina-legible en vez del reporte de texto. |

#### `toggle_changelog_archive.py`
**Qué hace:** Convierte el formato del Archivo Changelog exportado (toggle blocks Markdown).
**Flags:**
| Flag | Caso de uso |
|---|---|
| `--file <ruta>` (requerido) | El Markdown exportado desde Notion que quieres convertir. |
| `--out <ruta>` | Default es `/tmp/archivo_changelog_toggled.md` — especifica otra ruta si quieres conservarlo fuera de `/tmp`. |
| `--dry-run` | Ver las primeras 80 líneas convertidas sin escribir el archivo completo. |
| `--apply` | ⚠️ No tiene efecto real — el archivo se escribe siempre que `--dry-run` esté ausente; este flag es vestigial. |

#### `lazy_loader.py`
**Qué hace:** Fetch quirúrgico de una sección específica de un documento de Notion (economía de contexto — evita traer el documento completo).
**Flags:**
| Flag | Caso de uso |
|---|---|
| `--page <uuid>` (requerido) | La página de Notion sobre la que quieres resolver una ruta. |
| `--route <PREFIX:CLAVE>` (requerido) | Ej. `KERNEL:SCHEMA-008` — trae solo esa sección, no el documento entero. Ideal cuando Claude necesita un solo nodo y no quieres gastar tokens en el resto. |

#### `context_layer.py` / `query_layer.py`
**Qué hace:** Resolución de entidades individuales (`context_layer.py entity_id`) y búsqueda libre (`query_layer.py texto`) sobre el índice — motor interno detrás de `vantage.py resolve/query`.
**Uso:** Un argumento posicional cada uno; normalmente no se invocan directo, sino a través de `vantage.py`.

---

### 22.2 MANUAL:SCRIPT-GLOSSARY-L3
Layer 3 — Passive Intake (Gmail)

#### `layer_3_mail.py`
**Qué hace:** Lee correos no leídos de una etiqueta Gmail vía IMAP, extrae vacantes con Groq, las escribe en el Tracker.
**Variables de entorno (todas ajustables sin tocar código):**
| Variable | Default | Caso de uso |
|---|---|---|
| `GMAIL_LABEL` | `.Jobs` | Si organizas tus alertas de LinkedIn en una etiqueta distinta, apunta L3 ahí sin modificar el script. |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | Si notas que la extracción está fallando en vacantes complejas, prueba con un modelo más grande de Groq. |
| `GROQ_MIN_DELAY_SEC` | `12` | Súbelo si estás pegando contra rate limits de Groq en corridas con muchos correos. |
| `GROQ_MAX_RETRIES` | `8` | Ajusta si tu conexión es inestable. |
| `GROQ_BODY_MAX_CHARS` | `3500` | Si tus alertas de correo traen JDs muy largos y se están truncando antes de lo útil, súbelo (cuidado con costo de tokens de Groq). |
| `GROQ_MAX_EMAILS_PER_RUN` | `10` | Si tuviste una semana sin correr L3 y hay backlog, súbelo temporalmente para procesar todo de un jalón. ⚠️ Nota de discrepancia: Manual y Aliases citan valores distintos (10 vs 5) — el código real usa 10 como default; candidato prioritario para el punto B. |

---

### 22.3 MANUAL:SCRIPT-GLOSSARY-L4
Layer 4 — Version Control & Sync Documental

#### `vdoc.py`
**Qué hace:** Wrapper de orquestación — decide dirección de sync (Notion↔local) y dispara `vsync_doc.py` + `git_sync.py`.
**Uso (tokens posicionales, no flags tradicionales):**
| Token | Caso de uso |
|---|---|
| `dry` | Preview de lo que haría en modo auto, sin escribir nada. Úsalo antes de cualquier sync si no estás seguro de qué documento cambió más recientemente. |
| `notion` | Fuerzas Notion→local (pide confirmación). Úsalo si sabes que editaste en Notion y el local está desactualizado. |
| `local` | Fuerzas local→Notion (PATCH puntual). ⚠️ Nota real: pese a que el resto del sistema pide confirmación para direcciones forzadas, `local` tiene una excepción temporal en el código y NO pide confirmación — ejecuta directo. |
| `auto` | Deja que el script decida por hash cuál lado está más reciente. |
| `<documento>` (ej. `kernel`, `brief`) | Restringe el sync a un solo documento en vez de los 7. |

#### `vsync_doc.py`
**Qué hace:** Motor real de sincronización documento-por-documento (invocado por `vdoc.py`, no directo normalmente).
**Flags:**
| Flag | Caso de uso |
|---|---|
| `--direction {notion,auto,local}` | Igual lógica que los tokens de `vdoc.py`, pero si necesitas invocar el motor directo (debugging). |
| `--dry-run` | Preview sin aplicar ni auto-commit. |
| `--doc {kernel,system_prompt,career_canon,manual,aliases,change_log,brief}` | Nota real: maneja 7 documentos, incluyendo `brief` — aunque la documentación textual del Manual describe un catálogo de 6. |

#### `git_sync.py`
**Qué hace:** Genera commit y push del árbol VANTAGE hacia GitHub.
**Flags:**
| Flag | Caso de uso |
|---|---|
| `--dry` | Antes de un push automático, revisa qué archivos entrarían al commit sin ejecutar nada. |

#### `vsum.py`
**Qué hace:** Genera resúmenes de archivos Markdown/texto vía Groq o Gemini.
**Flags:**
| Flag | Caso de uso |
|---|---|
| `file` (posicional, requerido) | Ruta al archivo local a resumir. ⚠️ Nota real: pese a lo que sugiere cualquier doc sobre "Claude Share URLs", el código solo acepta rutas de archivo local — una URL fallará. |
| `-o/--output <ruta>` | Si quieres guardar el resumen en vez de verlo en pantalla — útil para encadenar con otro proceso. |
| `-m/--model {groq,gemini}` | Si Groq está teniendo rate limits, cambia manualmente a Gemini con este flag en vez de esperar el fallback automático. |
| `--notion` | ⚠️ Flag vestigial — se parsea pero no tiene ningún efecto en el código actual. No lo uses esperando que cree una página en Notion. |

---

### 22.4 MANUAL:SCRIPT-GLOSSARY-DASHBOARD
Dashboard — Servidor Local de Visualización

#### `dashboard_start.sh` → `dashboard_server.py`
**Qué hace:** Levanta el servidor local del Dashboard, corre smoke test, abre el navegador.
**Uso:** Sin flags — un solo comando hace todo el ciclo (start → healthcheck → smoke test → abrir browser). Si el smoke test falla, no abre el navegador y te avisa por notificación de sistema.

#### `layer_1_run_dash.py`
**Qué hace:** Variante de `layer_1_run.py` adaptada para ser invocada desde el Dashboard web en vez de Terminal.
**Uso:** Sin flags CLI propios — se invoca vía las rutas HTTP del Dashboard, no directo.

---

### 22.5 MANUAL:SCRIPT-GLOSSARY-RAYCAST
Raycast — Atajos de Un Click

> Estos scripts son wrappers delgados — su único trabajo es invocar el script real de la capa correspondiente con notificaciones de sistema (sonido de éxito/error). No tienen flags propios más allá de lo que reenvían.

| Wrapper Raycast | Invoca | Nota operativa |
|---|---|---|
| `vantage-health.sh` | `health_check.py` | Sin flags. |
| `vantage-vl1.sh` → `layer_1_wrapper.sh` | `layer_1_pipeline.sh` | Si no le pasas argumentos, auto-detecta el feed JSON más reciente en `Layer_1/feeds/`. |
| `vantage-vl3.sh` → `layer_3_mail.sh` | `layer_3_mail.py` | Sin flags — valida que exista `.venv` y `config/layer_3.env` antes de correr. |
| `vantage-dedup.sh` / `vantage-opport-dedup.sh` | `dedup_opportunities.py` (sin args) | ⚠️ No expone `--clear` — para limpiar un flag puntual necesitas Terminal directo. |
| `vantage-vgit.sh` → `git_sync_wrapper.sh` | `git_sync.py` | Reenvía `"$@"` — sí puedes pasarle `--dry` vía Raycast si tu atajo lo permite. Loguea cada corrida en `/tmp/vantage_l4_gitsync.log`. |
| `vantage-vdoc-dry.sh` | `vdoc.py dry` | Atajo directo al modo preview. |
| `vantage-vdoc-notion.sh` | `vdoc.py notion` | Atajo directo al modo forzado Notion→local (pide confirmación). |
| `vantage-vd.sh` | `vdoc.py` (modo según config del atajo) | Revisa el contenido del script si necesitas saber qué dirección dispara por default. |
| `vantage-census.sh` | `generate_census.py` | Sin `--debug-id` expuesto — census completo únicamente. |
| `vantage-versions-bootstrap.sh` | `verify_versions.py --bootstrap` | |
| `vantage-versions-sync.sh` | `verify_versions.py --sync` | |
| `vantage-versions-scripts-gap.sh` | `verify_versions.py --scripts` | |
| `vantage-hyperlinks-dry.sh` | `apply_hyperlinks_notion.py --all` (sin `--apply`) | |
| `vantage-hyperlinks-apply.sh` | `apply_hyperlinks_notion.py --all --apply` | ⚠️ Escritura real de un solo click — sin gate de confirmación adicional del lado Raycast. |
| `vantage-status.sh` | `status_report.py` | Sin flags. |
| `vantage-sync.sh` | (revisar contenido — probablemente alias de `vdoc.py auto` o `vsync_doc.py`) | Pendiente de confirmación directa si se usa activamente. |
| `clean-caches-raycast.sh` | `clean_caches.sh` | Limpieza de cachés de apps (Chrome, Figma, Notion, etc.) — no toca sesión/login, solo caché regenerable. |

---

### 22.6 MANUAL:SCRIPT-GLOSSARY-XREF
Matriz de Transición de Estados — Ciclo de Vida del Script

Vista tabular consolidada, mismo patrón que [KERNEL:GATE-DECISION-011] (Matriz de Transición de vacantes) — aplicada aquí al ciclo de vida de un script dentro del sistema de documentación (disco → Glosario → Script Library). Referencia canónica para el skill `vantage-sync-script-glossary` (punto E) y para `verify_versions.py --new-scripts` (punto D) — no reemplaza la descripción en prosa de cada script, la complementa con indexación de estados.

| Estado Origen | Evento / Trigger | Guard / Regla | Estado Destino | Componente | Efecto |
|---|---|---|---|---|---|
| [ENTRY] | Commit de archivo .py/.sh nuevo en árbol activo (Layer_1/3/4, Dashboard, Raycast) | No excluido por EXCLUDED_DIR_NAMES/EXCLUDED_FILE_PREFIXES | NO_DOCUMENTADO | Filesystem (git) | Ninguno — script existe, cero registro |
| NO_DOCUMENTADO | Operador corre `vversions --new-scripts` | Nombre de archivo ausente en SCRIPT_GLOSSARY_PATH (local, sin Notion) | DETECTADO | Python (local, read-only) | Exit code 1 — reporte en stdout, sin escritura |
| DETECTADO | Claude invoca `vantage-sync-script-glossary` | Lectura del script fuente (grep de flags/env vars) + DRY RUN de ambas entradas propuestas | PROPUESTO | Claude (AI Component) | Ninguno aún — solo preview, sin escritura |
| PROPUESTO | Operador confirma APROBAR_WRITE | Escritura dual atómica: entrada en Glosario (Notion, página Manual) + fila en Script Library (Notion DB) | DOCUMENTADO | Claude + Notion MCP | Página Manual actualizada; fila Script Library creada; write-back verification en ambos |
| PROPUESTO | Operador rechaza o no confirma | Sin APROBAR_WRITE | DETECTADO | Humano | Sin cambio — permanece pendiente para próxima corrida |
| DOCUMENTADO | Edición posterior del script (nuevo flag agregado) | Diff entre flags reales (grep) y flags documentados en Glosario | DESACTUALIZADO | Python + Claude (detección manual o futura extensión de `--new-scripts`) | Marcado ⚠️ en Glosario — no auto-corregido, requiere revisión igual que hallazgos de auditoría (ver lista al final de esta sección) |
| DOCUMENTADO | Script renombrado con prefijo `DEPRECATED_` o movido a carpeta excluida | EXCLUDED_FILE_PREFIXES / EXCLUDED_DIR_NAMES aplica en el próximo `scan_committed_assets()` | HUÉRFANO_GLOSARIO | Filesystem (git) + Python (detección pasiva) | Ninguno automático — entrada en Glosario/Script Library queda obsoleta, sin flag de alerta hasta auditoría manual |
| DOCUMENTADO (Script Library) | Fila marcada "Activo" en Notion sin archivo correspondiente en disco | `vversions --scripts` (ya existente, vía Notion) | HUÉRFANO_NOTION | Python (read-only) + Notion | Reportado en gap report — remediación manual, mismo patrón que hoy |

**Reglas de mantenimiento derivadas de la matriz:**

- Todo script nuevo agregado al árbol activo transita `[ENTRY] → NO_DOCUMENTADO → DETECTADO → PROPUESTO → DOCUMENTADO` — nunca salta directo a `DOCUMENTADO` sin pasar por DRY RUN + APROBAR_WRITE (mismo invariante que [KERNEL:DATA-FLOW]).
- El estado `DOCUMENTADO` es doble — requiere presencia simultánea en Glosario **y** Script Library. Un script en solo uno de los dos no es `DOCUMENTADO`, es un estado intermedio no listado arriba porque hoy no debería poder ocurrir (la escritura de `vantage-sync-script-glossary` es atómica en ambos destinos).
- `DESACTUALIZADO` y `HUÉRFANO_*` no tienen remediación automática por diseño — son señales para auditoría del operador, igual que los hallazgos ⚠️ ya documentados en este Glosario. Documentar la discrepancia, no "arreglarla" sin instrucción explícita.
- Esta matriz es la fuente de verdad para el diseño del skill `vantage-sync-script-glossary` — cualquier cambio a su lógica de transición pasa por `vantage-documentacion-transversal-propuesta` sobre este nodo (`MANUAL:SCRIPT-GLOSSARY-XREF`), no por edición directa del skill.

**Hallazgos de discrepancia activos (heredados de auditoría arena.ia, verificados contra código fuente):**
1. `layer_1_pipeline.sh batch` no reenvía `--execute` a `batch_operations.py` — siempre corre en modo definido por el propio script.
2. `vdoc.py local` no pide confirmación pese a que el resto de direcciones forzadas sí (excepción temporal marcada en el propio código).
3. `vsync_doc.py --doc` maneja 7 documentos (incluye `brief`), no 6.
4. `dedup_opportunities.py --clear` requiere posición fija en `sys.argv`, no es un flag argparse real.
5. `vsum.py --notion` se parsea pero no tiene efecto — vestigial.
6. `cross_tracker_match.py --dry-run` no puede desactivarse — default `True` sin opuesto.
7. `GROQ_MAX_EMAILS_PER_RUN`: Manual/Aliases citan valores distintos entre sí; código usa 10.
