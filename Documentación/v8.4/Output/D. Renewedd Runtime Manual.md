```markdown
# RUNTIME OPERATIONS GUIDE — VANTAGE v8.4
ID: 380938be-fc42-8019-85bf-ccd4cc3bd14b
Última actualización: 2026-06-17 · Post-Audit Documentation Renewal

> Estado verificado: 465 entidades, 100% hash coverage, 0 orphans (2026-06-15/16).
> Esta documentación describe únicamente lo que existe y corre hoy.

---

## DOCUMENTO 1 — MANUAL DE USUARIO (Runtime)

### 1.3 Qué NO hace — CORRECCIÓN v8.4

~~"No regenera el Entity Index automáticamente — eso es un paso manual."~~

**Estado actual:** `vantage.py sync` (implementado 2026-06-16) regenera
`entity_index_v2.json` desde Notion en vivo con atomic write.
La regeneración ya no es exclusivamente manual.

Sigue siendo manual:
- La actualización de `graph_v2.json` y `backlinks_v2.json` (sync no los toca)
- La decisión de cuándo correr `sync` (no hay auto-trigger)

### 1.5 Comandos — TABLA CANÓNICA v8.4

| Comando | Qué hace | Input | Output |
|---|---|---|---|
| `status` | Healthcheck: index size, Notion metrics, index age | ninguno | dict con `entity_index`, `notion_client_metrics`, `index_age_hours`, `warning` (si stale) |
| `ask "<prompt>"` | Lenguaje natural → intención → resultado | string libre | dict con `intent`, `count`, `results` |
| `resolve <entity_id>` | Resuelve entity_id contra Notion en vivo | `PREFIX:H_xxxx` | `{entity_id, status, source_db, page_url, resolved}` |
| `context <entity_id>` | Propiedades + bloques de página Notion | `PREFIX:H_xxxx` | `{entity, status, metadata, content}` |
| `query "<valor>"` | Busca por entity_id, hash o texto libre | string | `{query, match_type, count, results}` |
| `sync` | Regenera entity_index_v2.json desde Notion (atomic write) | ninguno | `{status, entities_before, entities_after, elapsed_seconds, index_path}` |

### 1.11 FAQ — CORRECCIONES v8.4

**¿`resolver_registry_v2.json` dice "DESIGN_ONLY"?**
No. Este campo fue corregido el 2026-06-16. El registry refleja estado operativo real.
Cualquier referencia previa a esta advertencia es documentación obsoleta.

**¿Puedo regenerar el Entity Index automáticamente?**
Sí, usando `python3 vantage.py sync`. El comando hace atomic write (.tmp → os.replace),
preserva el index anterior si falla, e invalida el cache interno con `force_reload=True`.
Resultado verificado en producción: 465 entidades, 4.3s, 0 errores.

---

## DOCUMENTO 5 — REGISTRY GOVERNANCE

### 5.7 Estado del Registry — CERRADO v8.4

El pendiente documentado en versiones anteriores ("resolver_registry_v2.json
autodescripto como DESIGN_ONLY") fue resuelto el 2026-06-16. Los campos
`status` y `resolution_contract.live_resolution` fueron actualizados al
estado operativo real. Este pendiente está **cerrado**.

---

## DOCUMENTO NUEVO — HEALTH MONITORING & DIAGNOSTICS

### HM-1 Runtime Status

```bash
python3 vantage.py status
```

Campos a revisar:

| Campo | Valor sano | Acción si no sano |
| --- | --- | --- |
| `total_entities` | > 0 (esperado ~465) | Correr `sync` |
| `hash_coverage` | 100.0 | Investigar orphan_candidates |
| `orphan_candidates` | 0 | Correr `backfill_hash.py` y luego `sync` |
| `index_age_hours` | < 24 | Correr `sync` |
| `warning` | ausente | Si `entity_index_stale`: correr `sync` |

### HM-2 Index Freshness

El index se considera stale si `index_age_hours > 24`.

Trigger automático de staleness: ninguno (por diseño — decisión humana).
Indicador visible: `"warning": "entity_index_stale"` en output de `status`.

Cuándo es crítico el sync:

- Post ciclo L1/L2 semanal (entradas nuevas escritas por `feed_processor.py`)
- Post resolución de entradas `REVIEW_NEEDED`
- Antes de correr `find_candidates` si el index tiene >24h

### HM-3 Resolver Validation

Verificar que el Resolver funciona contra Notion:

```bash
# Tomar un entity_id conocido de status output
python3 vantage.py resolve TRACKER:H_<id_conocido>
# Esperado: {"status": "resolved", "resolved": true}
```

**Pitfall activo — RID-02:** El Resolver no pagina `data_sources/query`.
En Archivo Tracker (384+ entidades), entidades en páginas > 1 pueden devolver
`not_found` incorrectamente. Estado: **Abierto**.

Workaround hasta resolución: para entidades de ARCHIVO, usar `context` directamente
o verificar manualmente en Notion si el resolve retorna `not_found` inesperado.

### HM-4 L3 Heartbeat

**Estado actual:** No existe heartbeat automático de L3 (issue abierto M-05).

Verificación manual:

```bash
vl3  # correr mail_pipeline.py manualmente
# Si falla: revisar layer_3.env
#   - GMAIL_APP_PASSWORD: expirar y regenerar si falla IMAP
#   - GROQ_API_KEY: verificar vigencia en console.groq.com
#   - NOTION_TOKEN: mismo que LAYER_1/.env
```

Señal de fallo L3: no hay vacantes nuevas vía email en >3 días
(bajo condiciones normales de mercado).

---

## DOCUMENTO NUEVO — RECOVERY PROCEDURES

### REC-1 Cold Start (Arranque Frío)

Ver Manual §ARRANQUE FRÍO — Checklist completo de reactivación.
Usar cuando el sistema no ha sido operado por >5 días.

Resumen de pasos: status → sync → revisar REVIEW_NEEDED → verificar L3 → smoke test.

### REC-2 Runtime Recovery

Si `vantage.py` falla con import errors:

```bash
# 1. Verificar directorio
pwd  # debe ser .../LAYER_1/scripts

# 2. Verificar venv
which python3  # debe apuntar al .venv

# 3. Verificar archivos
ls query_layer.py context_layer.py agent_api.py notion_client.py resolver_layer_v1.py

# 4. Verificar .env
cat ../.env | grep NOTION_TOKEN

# 5. Reinstalar dependencias si necesario
pip install -r ../requirements.txt
```

### REC-3 Entity Index Recovery

Si `sync` falla y el index está corrupto:

```bash
# sync hace atomic write — el index anterior se preserva si sync falla
# Verificar:
python3 vantage.py status  # si responde, el index previo está intacto

# Si el index está completamente ausente:
python3 generate_entity_index_v2.py
# Esto regenera entity_index_v2.json sin pasar por vantage.py
```

### REC-4 Notion Token Recovery

Si todas las operaciones que tocan Notion retornan 401:

1. Ir a Notion → Settings → Connections → Internal integrations
2. Regenerar token de la integración VANTAGE
3. Actualizar `LAYER_1/.env`: `NOTION_TOKEN=secret_nuevo_token`
4. Limpiar cache: `python3 notion_client.py clear-cache`
5. Verificar: `python3 vantage.py resolve TRACKER:H_<id_conocido>`

### REC-5 L3 Recovery

Si `mail_pipeline.py` (vl3) falla:

1. Verificar `LAYER_3/config/layer_3.env` — todos los campos presentes
2. Probar IMAP: `python3 -c "import imaplib; c = imaplib.IMAP4_SSL('imap.gmail.com'); c.login('tu@gmail.com', 'app_password')"`
3. Probar Groq: verificar API key en console.groq.com → correr `vl3` de nuevo
4. Si persiste: revisar logs de ejecución anterior del launchd job

```

***

## ENTREGABLE 6 — ROADMAP OPERATIVO ACTUALIZADO

```markdown
# ROADMAP OPERATIVO — VANTAGE v8.4
ID: 380938be-fc42-8099-93b0-e910060d68ee
Última actualización: 2026-06-17 · Post-Audit Documentation Renewal

> Este roadmap reemplaza el roadmap histórico de integración (Fases 0–4).
> Las fases históricas están archivadas — no son estado operativo vigente.

---

## ESTADO ACTUAL — Sistema Operativo (verificado 2026-06-16)

| Componente | Estado | Notas |
|---|---|---|
| Registry V2 | ✅ Operativo | `entity_index_v2.json`, `graph_v2.json`, `backlinks_v2.json`, `resolver_registry_v2.json` |
| Resolver Layer V1 | ✅ Operativo | Bug RID-02 abierto (paginación) |
| Query Layer | ✅ Operativo | In-memory, `entity_index_v2.json` |
| Context Layer | ✅ Operativo | |
| Agent API | ✅ Operativo | 8 intents. Handlers `show_archived_history`/`show_bugs` pendientes de verificación end-to-end |
| Runtime CLI | ✅ Operativo | `status`, `ask`, `resolve`, `context`, `query`, `sync` |
| Auditoría Técnica | ✅ Completada | v8.4 · 2026-06-17 |
| Remediaciones Iniciales | ✅ Ejecutadas | `sync` implementado, registry corregido, `vacante_purge_trash_only.py` deprecado |
| Documentation Renewal | ✅ Completado | Post-Audit · 2026-06-17 |

---

## RIESGOS ABIERTOS

### Prioridad Inmediata

**RID-02 — Resolver Pagination** · Integridad · Alto
El Resolver no pagina `data_sources/query`. Con Archivo Tracker en 384+ entidades,
`resolve` y `context` pueden devolver `not_found` para entidades válidas no en la
primera página de resultados.
Acción requerida: Añadir loop `while has_more` con `start_cursor` en
`resolver_layer_v1.py::_query_notion`, siguiendo el patrón de `agent_api.py::_notion_db_query`.

**ROP-03 — Hard Blocks Python Enforcement** · Operativo · Alto
Los Hard Blocks (L'Oréal, Levi's, El Palacio de Hierro) están declarados en el SP
para Claude pero no están implementados en `feed_processor.py` ni `mail_pipeline.py`.
L3 (automático, sin Claude) puede ingestar vacantes de empresas bloqueadas.
Acción requerida: Añadir `HARD_BLOCKED_BRANDS` set y guard en `process_record()`
de `feed_processor.py`.

### Prioridad Esta Semana

**Manual sync update** · Documental · Crítico
Manual §5 no incluye `sync` en la tabla de comandos. Sección §5 dice "no regenera
automáticamente". Correcciones documentadas en Documentation Renewal — aplicar en Notion.

**Runtime Doc sync update** · Documental · Crítico
Runtime Doc §1.3, §1.5, §1.11 contienen información obsoleta sobre `sync` y sobre
el registry "DESIGN_ONLY". Correcciones documentadas en Documentation Renewal — aplicar en Notion.

**M-01 — Staleness indicator** · Monitoreo
`vantage.py status()` ya incluye `index_age_hours` e `"warning": "entity_index_stale"`
implementados en el código productivo. Verificar que la documentación refleja
este comportamiento (incluido en Documentation Renewal).

### Próximo Ciclo

**M-05 — L3 Heartbeat** · Monitoreo · Operativo
`mail_pipeline.py` escribe `l3_heartbeat.json` con timestamp de último run exitoso.
`vantage.py status` lo lee y reporta `l3_last_success` y `l3_status`.
Resuelve ROP-01 (fallo silencioso de L3).

**M-06 — Runtime optimization path** · Performance · Operativo
`_handle_find_candidates` aplica pre-filtro in-memory sobre el entity_index antes
de llamar a Notion, reduciendo de O(n) a O(k) llamadas donde k << n.
Requiere añadir campos `status`, `gate_decision`, `match` al entity_index en `sync`.

**M-08 — Cold Start procedure** · Documentación
Procedimiento de arranque frío añadido al Manual en Documentation Renewal.
Verificar inserción efectiva en Notion.

---

## RIESGOS MONITOREADOS (no requieren acción inmediata)

**RID-01** — Entity index stale sin advertencia → parcialmente resuelto por M-01 (implementado). Disciplina operativa requerida.
**RAI-03** — Tokens de aprobación ambiguos (`Ok`/`Go`) → corrección documental en SP. Disciplina operativa requerida hasta que todos los sistemas que leen el SP tengan la versión corregida.
**ROP-04** — Latencia O(n) en `find_candidates` → abierto como M-06 (próximo ciclo).
**RID-03** — Dedup cross-layer L3 vs L1/L2 → riesgo medio, sin acción inmediata. Monitorear duplicados en el Tracker.

---

## PRÓXIMAS ACCIONES

### Inmediata (esta sesión / próxima sesión)
- [ ] Implementar paginación en `resolver_layer_v1.py` (RID-02)
- [ ] Implementar Hard Blocks en `feed_processor.py` (ROP-03)

### Esta Semana
- [ ] Aplicar correcciones de Manual en Notion (sync command, cold start)
- [ ] Aplicar correcciones de Runtime Doc en Notion (sync, registry stale warning)
- [ ] Verificar M-01 (staleness) activo en producción con `python3 vantage.py status`

### Próximo Ciclo
- [ ] M-05: L3 heartbeat en `mail_pipeline.py` + lectura en `status()`
- [ ] M-06: Pre-filter in-memory en `_handle_find_candidates`
- [ ] M-08: Confirmar inserción de cold start procedure en Notion
- [ ] Verificar handlers `show_archived_history`/`show_bugs` end-to-end contra Notion
- [ ] Eliminar archivos `.bak` o mover a `Layer_1/backups/`
- [ ] Eliminar `_DEPRECATED_vacante_purge_trash_only.py` tras confirmación
```

---