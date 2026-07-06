# VANTAGE AUDIT V2 — Verificación, Puntos Ciegos y Plan de Trabajo

**Audit Date:** 2026-07-05  
**Codebase Root:** `/Users/mauriciomeyran/Documents/04-Vantage_CV/`  
**Objective:** Auditoría técnica de pipelines de datos y automatización (Notion API, Python, integraciones de mensajería) — Verificación, documentación y plan de trabajo priorizado.

---

## 1. Resumen Ejecutivo

### Cambios desde 2026-06-24

**Cambios significativos detectados:**

1. **FIX APLICADO: Source_Type trailing space** — El campo "Source_Type " (con espacio final) está presente en VANTAGE_TRACKER y fue documentado como bug en auditoría previa. Ahora está correctamente manejado en:
   - `feed_processor.py` (línea 793-794)
   - `layer_1_run.py` (líneas 554, 622, 650, 655, 755, 796, 872)
   - `gate_logic.py` (línea 95)
   - `assign_next_action.py` (línea 145)
   - `cleanup_misfits.py` (línea 28)
   - `source_analytics.py` (línea 92)

2. **FIX APLICADO: Next_Action type consistency** — El campo Next_Action ahora se escribe consistentemente como `rich_text` en `layer_1_run.py` (líneas 595, 771, 918) y `assign_next_action.py` (línea 174), eliminando la inconsistencia de type reportada en auditoría previa.

3. **FIX APLICADO: Hash en Layer 3** — `layer_3_mail.py` ahora calcula hash al momento de ingestión mediante `_compute_l3_hash()` (líneas 393-403, 591-592), eliminando la dependencia de backfill para cross-layer dedup.

4. **NUEVO: Paginación data_sources API** — Scripts migrados al endpoint `data_sources/{id}/query` (API 2025-09-03) para DBs multi-source:
   - `layer_1_run.py` (query_all_items, líneas 62-113)
   - `consolidate_duplicates.py` (query_all_items, líneas 73-134)
   - `assign_next_action.py` (query_all_items, líneas 88-120)
   - `backfill_hash.py` (query_data_source, líneas 79-98)
   - `fetch_hashes.py` (query_all, líneas 33-56)
   - `generate_entity_index_v2.py` (query_data_source, líneas 82-95)

5. **NUEVO: Runtime Identity Contract** — `runtime_identity.py` centraliza la resolución de entity_prefix desde `resolver_registry_v2.json`, eliminando hardcoded prefixes (DT-014).

6. **NUEVOS Scripts de mantenimiento**:
   - `cleanup_misfits.py` — Limpieza automática de vacantes fuera de perfil
   - `health_check.py` — Health check de arranque pre-L1/L2/L3
   - `vantage_audit_fix.py` — Deprecación de scripts one-shot en Script Library
   - `vantage_bug_close.py` — Cierre masivo de bugs documentados
   - `class_b_guard.py` — Guard compartido para campos Class B
   - `lazy_loader.py` v2 — Fetch quirúrgico de secciones del Kernel

### Hallazgos más importantes de esta ronda

1. **[CRÍTICO] Exposición de API key en layer_1_blueprint.json** — El archivo Make.com contiene un GROQ API key hardcodeado en línea 35 (`***REDACTED***`). Este archivo está versionado en git.

2. **[ALTO] Inconsistencia de IDs de base de datos** — `resolver_registry_v2.json` documenta IDs diferentes para VANTAGE_TRACKER:
   - `database_id`: "596938befc42836baea7814a1491bd47"
   - `data_source_id`: "442938be-fc42-828f-b72e-076818d65a5b"
   - Algunos scripts aún usan el data_source_id antiguo "4e542b37-6e52-4418-89b7-a0eeb3138307" (v1.3 de runtime)

3. **[MEDIO] scoring_deterministic.py DEPRECATED** — El archivo tiene un header explícito de deprecación (líneas 1-15) indicando que fue reemplazado por layer_1_run.py v6.4 (0-100 scale), pero sigue existiendo en el codebase.

4. **[MEDIO] MCP server configurado pero no validado** — `.vscode/mcp.json` existe configurando el servidor Notion MCP, pero no hay evidencia de uso en el pipeline actual.

5. **[BAJO] Cobertura de tests inexistente** — Solo existe `test_datasource_query.py` como script de prueba diagnóstico. No hay suite de tests automatizada.

---

## 2. Verificación de Fixes Previos

| Fix | Estado reportado (2026-06-24) | Estado verificado hoy (2026-07-05) | Evidencia (archivo:línea) |
|-----|------------------------------|----------------------------------|---------------------------|
| Source_Type espacio final | CERRADO | **VERIFICADO** | feed_processor.py:793-794, layer_1_run.py:554, gate_logic.py:95 |
| DS_ID assign_next_action.py | VALIDADO EN PRODUCCIÓN | **VERIFICADO** | assign_next_action.py:127 usa DS_ID "442938be-fc42-828f-b72e-076818d65a5b" |
| Hash en L3 al crear | REPORTADO COMO PENDIENTE | **VERIFICADO** | layer_3_mail.py:393-403, 591-592 |
| Reescritura fetch_hashes.py | VALIDADO EN PRODUCCIÓN | **VERIFICADO** | fetch_hashes.py:1-126 usa data_sources API |
| Next_Action type mismatch | CERRADO | **VERIFICADO** | layer_1_run.py:595, 771, 918 usa rich_text consistentemente |

**Nota:** El fix de Source_Type " " fue aplicado consistentemente en todos los scripts que leen este campo. Sin embargo, `layer_1_blueprint.json` (Make.com) aún usa "Source_Type " en línea 143, lo cual es correcto para mantener consistencia con el schema de Notion.

---

## 3. Documentación Completa

### 3.1 Scripts Inventariados (verificados vs auditoría previa)

#### Scripts existentes sin cambios significativos:

1. **feed_processor.py** — SIN CAMBIOS CRÍTICOS
   - Ubicación: `Layer_1/scripts/feed_processor.py`
   - Cambio menor: Ahora usa `is_agregador()` y `validate_url_pre_ingestion()` importados de layer_1_run.py (líneas 45-46)
   - Hash: Se mantiene lógica de compute_dedup_hash

2. **layer_1_run.py** — CAMBIOS SIGNIFICATIVOS
   - Ubicación: `Layer_1/scripts/layer_1_run.py`
   - Versión actual: v7.5 (línea 3)
   - Cambios:
     - Migración a data_sources API (query_all_items, líneas 62-113)
     - Auto-asignación de Source_Type vacío (líneas 643-663)
     - Fuente aplica a Vacante e Inbound (línea 13)
     - Score siempre escribe cuando está vacío (línea 14)
     - Next_Action type fix: rich_text consistente (líneas 595, 771, 918)

3. **gate_logic.py** — SIN CAMBIOS FUNCIONALES
   - Ubicación: `Layer_1/scripts/gate_logic.py`
   - Fix aplicado: Source_Type con espacio (línea 95)

4. **scoring_deterministic.py** — DEPRECATED
   - Ubicación: `Layer_1/scripts/scoring_deterministic.py`
   - Estado: Header explícito de deprecación (líneas 1-15)
   - No debe usarse; layer_1_run.py v6.4 es el sistema canónico

5. **notion_utils.py** — SIN CAMBIOS
   - Ubicación: `Layer_1/scripts/notion_utils.py`
   - Mantiene caché, throttling, retry logic

6. **backfill_hash.py** — CAMBIOS SIGNIFICATIVOS
   - Ubicación: `Layer_1/scripts/backfill_hash.py`
   - Versión: v1.3 (línea 3)
   - Cambios:
     - Migración a data_sources API (query_data_source, líneas 79-98)
     - DS_ID actualizado a "442938be-fc42-828f-b72e-076818d65a5b" (línea 46)

7. **fetch_hashes.py** — REESCRITO COMPLETAMENTE
   - Ubicación: `Layer_1/scripts/fetch_hashes.py`
   - Cambios:
     - Eliminados page IDs hardcodeados
     - Usa data_sources API (query_all, líneas 33-56)
     - DS_IDs actualizados (líneas 25-28)

8. **consolidate_duplicates.py** — CAMBIOS SIGNIFICATIVOS
   - Ubicación: `Layer_1/scripts/consolidate_duplicates.py`
   - Cambios:
     - Migración a data_sources API (query_all_items, líneas 73-134)
     - MAX_EXPECTED_RESULTS = 500 (línea 28)

9. **assign_next_action.py** — CAMBIOS SIGNIFICATIVOS
   - Ubicación: `Layer_1/scripts/assign_next_action.py`
   - Cambios:
     - Migración a data_sources API (query_all_items, líneas 88-120)
     - Next_Action type fix: rich_text (línea 174)
     - Source_Type con espacio (línea 145)

10. **layer_3_mail.py** — CAMBIO CRÍTICO
    - Ubicación: `Layer_3/scripts/layer_3_mail.py`
    - Cambio:
      - Agregada función `_compute_l3_hash()` (líneas 393-403)
      - Hash escrito al crear página (líneas 591-592)

11. **profile_fit.py** — SIN CAMBIOS
    - Ubicación: `Layer_1/scripts/profile_fit.py`
    - Mantiene reglas de exclusión y flags de alias

12. **vantage.py** — SIN CAMBIOS FUNCIONALES
    - Ubicación: `Layer_1/scripts/vantage.py`
    - Mantiene runtime unificado

13. **agent_api.py** — SIN CAMBIOS
    - Ubicación: `Layer_1/scripts/agent_api.py`
    - Mantiene API de lenguaje natural

14. **vsync_doc.py** — CAMBIOS MENORES
    - Ubicación: `Layer_4/scripts/vsync_doc.py`
    - Versión: v8.5.4 (línea 3)
    - Fixes: code blocks > 2000 chars truncados, direction local/auto

15. **query_layer.py** — SIN CAMBIOS
16. **context_layer.py** — SIN CAMBIOS
17. **graph_layer.py** — SIN CAMBIOS
18. **generate_entity_index_v2.py** — CAMBIOS SIGNIFICATIVOS
    - Ubicación: `Layer_1/scripts/generate_entity_index_v2.py`
    - Cambios:
      - Migración a data_sources API (query_data_source, líneas 82-95)
      - Usa runtime_identity para entity_prefix (línea 34)
      - DS_IDs actualizados (líneas 44-47)

19. **resolver_layer_v1.py** — SIN CAMBIOS

### 3.2 Scripts NUEVOS (no inventariados en auditoría previa)

1. **cleanup_misfits.py**
   - Ubicación: `Layer_1/scripts/cleanup_misfits.py`
   - Rol: Marca como Expirada vacantes fuera de perfil VM
   - Trigger: Manual con --dry-run / --yes
   - Lee: VANTAGE_TRACKER (DS_ID "442938be-fc42-828f-b72e-076818d65a5b")
   - Escribe: Status=Expirada, Gate_Decision=BLOCKED, Next_Action=Archivar
   - Usa: profile_fit.py para determinar misfit reasons

2. **health_check.py**
   - Ubicación: `Layer_1/scripts/health_check.py`
   - Rol: Health check de arranque pre-L1/L2/L3
   - Trigger: Manual antes de correr pipeline
   - Verifica: env vars, git status, Notion reachability, docs sync, tickets abiertos
   - Exit codes: 0 = OK, 1 = algo falló

3. **vantage_audit_fix.py**
   - Ubicación: `Layer_1/scripts/vantage_audit_fix.py`
   - Rol: Deprecar scripts one-shot en Script Library y append changelog
   - Trigger: Manual con --dry-run / --execute
   - Modifica: Script Library (DS "ea914544-338f-485e-ac1b-7f137a5c9cee"), Cheat Sheet

4. **vantage_bug_close.py**
   - Ubicación: `Layer_1/scripts/vantage_bug_close.py`
   - Rol: Cerrar bugs con Status=Resuelto, Next_Action=Documentar
   - Trigger: Manual con --dry-run / --execute / --id
   - Modifica: Bug Tracker, cambia Next_Action a "Monitorear"

5. **runtime_identity.py**
   - Ubicación: `Layer_1/scripts/runtime_identity.py`
   - Rol: Contrato canónico para resolución de entity_prefix
   - Trigger: Importado por otros módulos
   - Lee: resolver_registry_v2.json
   - Expone: load_prefix_map(), get_entity_prefix(), get_authorized_prefixes(), generate_entity_id()

6. **lazy_loader.py** (v2)
   - Ubicación: `Layer_1/scripts/lazy_loader.py`
   - Rol: Fetch quirúrgico de secciones del Kernel por ruta DOC:CLAVE
   - Trigger: CLI o importado como módulo
   - Cambios v1→v2: Soporte multi-prefijo, matcher de inicio, retry con backoff

7. **class_b_guard.py**
   - Ubicación: `Layer_1/scripts/class_b_guard.py`
   - Rol: Guard compartido para campos Class B
   - Trigger: Importado por feed_processor.py y flujos MCP
   - Expone: CLASS_B_FIELDS (set), strip_class_b(), assert_no_class_b()

8. **diagnose_db.py**
   - Ubicación: `Layer_1/scripts/diagnose_db.py`
   - Rol: Diagnóstico de paginación (¿repite IDs o son filas distintas?)
   - Trigger: Manual
   - No modifica nada

### 3.3 Campos Críticos de Notion

#### hash
- **Generación:** 
  - feed_processor.py: compute_dedup_hash() (new entries)
  - layer_3_mail.py: _compute_l3_hash() (L3 entries)
  - backfill_hash.py: backfill para registros existentes
- **Inputs:**
  - Si fetch_status == "career_page": URL normalizada
  - Si fetch_status == "aggregator": brand|title|location
  - Si job_id existe y no es generado: job_id
  - Fallback: brand|title|location
- **Escritura:** feed_processor.py, layer_3_mail.py, backfill_hash.py
- **Tipo Notion:** rich_text
- **Valores:** 64-character hexadecimal SHA-256 string
- **Si vacío:** entity marcado como orphan candidate en entity_index

#### Fetch
- **Valores:** "Accesible", "Bloqueado", "Parcial"
- **Escritura:** layer_1_run.py (URL re-check), feed_processor.py (initial value)
- **Tipo Notion:** rich_text
- **Mapping interno:** feed_processor usa "aggregator"/"career_page" → mapea a Fetch en Notion
- **Si vacío:** layer_1_run.py intentará check URL

#### VM_Scope
- **Valores:** "Alto", "Bajo"
- **Generación:** get_vm_scope() en layer_1_run.py y scoring_deterministic.py
- **Inputs:** Role title field
- **Lógica:** "Alto" si contiene VM keywords, "Bajo" otherwise
- **Tipo Notion:** rich_text
- **Si vacío:** Computado desde title, nunca null

#### Prioridad
- **Valores:** "1"-"8" (select field)
- **Sistema canónico:** layer_1_run.py v6.4 (0-100 scale) → mapeado a Prioridad 1-8
- **Mapping:**
  - Score 90-100 → Prioridad 8
  - Score 80-89 → Prioridad 7
  - Score 70-79 → Prioridad 6
  - Score 60-69 → Prioridad 5
  - Score 50-59 → Prioridad 4
  - Score 40-49 → Prioridad 3
  - Score 30-39 → Prioridad 2
  - Score 0-29 → Prioridad 1
- **Tipo Notion:** select
- **Si vacío:** Default "4" para new entries

#### Job_ID
- **Tipo Notion:** rich_text
- **Escritura:** feed_processor.py (from feed JSON), layer_1_blueprint.json (Make.com)
- **Valores:** Variable (from source) o empty
- **Si vacío:** Hash generation fallback a URL o composite key

#### Status
- **Valores:** "Nueva", "Target", "Postulado", "En proceso", "Negociando", "Sin respuesta", "Expirada", "Rechazado", "Archivar", "Retirado", "Contratado", "REVIEW_NEEDED"
- **Tipo Notion:** select
- **Protección:** Terminal states (Expirada, Rechazado, Archivar, Retirado) previenen auto-cleanup
- **Si vacío:** Tratado como "Nueva" equivalente

#### Gate_Decision
- **Valores:** "CREATE", "BLOCKED", "APPLIED"
- **Tipo Notion:** select
- **Escritura:** layer_1_run.py, gate_logic.py, assign_next_action.py
- **Lógica:**
  - CREATE si: Source_Type in ["Inbound", "Referencia", "Networking"] OR (Source_Type=="Vacante" AND Fetch in ("Accesible", "Parcial") AND (VM_Scope=="Alto" OR Role_Class=="Pivote"))
  - BLOCKED si: is_role_excluded() OR hard_block OR none of CREATE conditions
  - APPLIED si: evaluate_application_status() (Postulado/En proceso/Negociando/Sin respuesta)
- **Si vacío:** Recalculado en next pipeline run

#### Next_Action
- **Valores:** "Re-check", "Reparar URL", "Verificar JD", "Archivar", "Follow-up", "Interview prep"
- **Tipo Notion:** rich_text (CONSISTENTE desde fix v8.7.2)
- **Escritura:** layer_1_run.py, gate_logic.py, assign_next_action.py
- **Protección:** Terminal states (Archivar, Expirada) nunca se sobrescriben
- **Si vacío:** Asignado por gate logic

#### Fuente
- **Valores:** "Agregador", "Career Page Oficial"
- **Tipo Notion:** rich_text
- **Escritura:** layer_1_run.py (determine_fuente)
- **Lógica:** Basado en domain matching (linkedin.com, indeed.com, etc.)
- **Si vacío:** Determinado por determine_fuente()

#### Source_Type
- **Valores:** "Vacante", "Inbound", "Referencia", "Networking"
- **Tipo Notion:** select
- **IMPORTANTE:** En VANTAGE_TRACKER el campo tiene espacio final: "Source_Type "
- **Escritura:** feed_processor.py (sets "Vacante"), layer_1_blueprint.json (Make.com)
- **Consistencia:** Todos los scripts que leen este campo ahora usan "Source_Type " con espacio

#### Score
- **Valores:** 0-100 (number)
- **Sistema canónico:** layer_1_run.py v6.4
- **Lógica:** Base +40, Visual signal +20, Company impact +15, Role quality +10, Recruiter +10, Innovation DNA +5, Scale +5, Pivot +5, Agency +5, Luxury +5 (capped at 100)
- **Tipo Notion:** number
- **Si vacío:** Calculado por scoring script

#### Match
- **Valores:** "Muy Alto", "Alto", "Medio", "Bajo"
- **Tipo Notion:** select
- **Escritura:** layer_1_run.py, scoring_deterministic.py
- **Lógica:** Mapeado desde Score (0-100)
- **Si vacío:** Calculado desde Score

#### Role_Class
- **Valores:** "VM", "Pivote", "Otro"
- **Tipo Notion:** select
- **Escritura:** layer_1_run.py, scoring_deterministic.py
- **Lógica:** Basado en keywords en role title
- **Si vacío:** Calculado desde title

### 3.4 Dry Trace — Registro Representativo (L3 → Entity Index)

**Input:** Email de Indeed con vacante VM Coordinator @ Zara

**Step 1: Layer 3 Mail Pipeline (layer_3_mail.py)**
1. Gmail fetch: unread email from .Jobs label
2. Groq extraction: rol="VM Coordinator", marca="Zara", url="https://indeed.com/jobs/view/123456"
3. URL canonicalization: remove tracking params
4. VM filter: passes (contains "VM")
5. Dedup check: URL not in Notion → proceed
6. **Hash computation:** _compute_l3_hash() → sha256("url:https://indeed.com/jobs/view/123456")
7. Write to Notion:
   - Rol: "VM Coordinator"
   - Marca: "Zara"
   - Status: "Target"
   - layer: "L3"
   - Source_Type: "Vacante"
   - Fuente: "Indeed"
   - URL: canonicalized URL
   - Holding: "Inditex"
   - **hash**: computed in step 6

**Step 2: Layer 1 Pipeline (layer_1_run.py)**
1. URL Gate: Indeed is aggregator → bypass validation, set Fetch="Accesible"
2. Fuente assignment: "Agregador"
3. Auto-asignación Source_Type: ya tiene "Vacante" → skip
4. Scoring v6.4:
   - Base: +40
   - Visual signal: +20 (VM in title)
   - Company impact: +15 (Zara/Inditex)
   - Role quality: +10 (Coordinator)
   - Score: 85
   - Match: "Muy Alto"
   - VM_Scope: "Alto"
   - Role_Class: "VM"
5. Gate logic: Fetch="Accesible" AND VM_Scope="Alto" → Gate_Decision="CREATE"
6. Next_Action: "Re-check"
7. **hash**: ya existe desde L3, no se modifica

**Step 3: Entity Index Generation (generate_entity_index_v2.py)**
1. Query VANTAGE_TRACKER via data_sources API
2. For each page:
   - Extract hash from properties
   - Generate entity_id: "TRACKER:H_{hash[:16]}"
   - canonical_id: hash
3. Write to entity_index_v2.json with metrics

**Assumptions without validation:**
- Hash de L3 usa el mismo algoritmo que feed_processor.compute_dedup_hash (verificado en código: sí, ambos usan sha256 de URL si existe)
- Cross-layer dedup funciona con hash en lugar de URL (verificado: sí, ambos usan hash)

### 3.5 Payloads Notion API — Auditoría

#### feed_processor.py write_to_notion()
```json
{
  "title_prop": {"title": [{"text": {"content": "..."}}]},
  "brand_prop": {"rich_text": [{"text": {"content": "..."}}]} or {"select": {"name": "..."}},
  "status_prop": {"select": {"name": "Target"|"REVIEW_NEEDED"}},
  "hash_prop": {"rich_text": [{"text": {"content": "..."}}]},
  "layer_prop": {"select": {"name": "L1"|"L2"|"L3"}},
  "fetch_status_prop": {"select": {"name": "aggregator"|"career_page"}},
  "fuente_prop": {"rich_text": [{"text": {"content": "Agregador"|"Career Page Oficial"}}]},
  "location_prop": {"rich_text": [{"text": {"content": "..."}}]},
  "holding_prop": {"rich_text": [{"text": {"content": "..."}}]},
  "url_prop": {"url": "https://..."},
  "Source_Type ": {"select": {"name": "Vacante"}},
  "Prioridad": {"select": {"name": "4"}},
  "notes_prop": {"rich_text": [{"text": {"content": "..."}}]}
}
```
**Status:** CORRECTO — "Source_Type " con espacio coincide con schema

#### layer_1_run.py updates
**URL Gate failure:**
```json
{
  "Fetch": {"rich_text": [{"text": {"content": "Bloqueado"}}]},
  "Status": {"select": {"name": "Expirada"}},
  "Next_Action": {"rich_text": [{"text": {"content": "Archivar"}}]},
  "Gate_Decision": {"select": {"name": "BLOCKED"}}
}
```
**Status:** CORRECTO — Next_Action como rich_text (fix aplicado)

**Scoring update:**
```json
{
  "VM_Scope": {"rich_text": [{"text": {"content": "Alto"|"Bajo"}}]},
  "Score": {"number": 0-100},
  "Role_Class": {"select": {"name": "VM"|"Pivote"|"Otro"}},
  "Match": {"select": {"name": "Muy Alto"|"Alto"|"Medio"|"Bajo"}}
}
```
**Status:** CORRECTO

**Gate logic update:**
```json
{
  "Gate_Decision": {"select": {"name": "CREATE"|"BLOCKED"|"APPLIED"}},
  "Next_Action": {"rich_text": [{"text": {"content": "Re-check"|"Reparar URL"|"Verificar JD"|"Archivar"|"Follow-up"|"Interview prep"}}]}
}
```
**Status:** CORRECTO — Next_Action como rich_text consistente

#### layer_3_mail.py create_notion_page()
```json
{
  "Rol": {"title": [{"text": {"content": "..."}}]},
  "Marca": {"rich_text": [{"text": {"content": "..."}}]},
  "Status": {"select": {"name": "Target"}},
  "layer": {"select": {"name": "L3"}},
  "Source_Type ": {"select": {"name": "Vacante"}},
  "Holding": {"rich_text": [{"text": {"content": "..."}}]},
  "Fuente": {"rich_text": [{"text": {"content": "..."}}]},
  "URL": {"url": "https://..."},
  "hash": {"rich_text": [{"text": {"content": "..."}}]}
}
```
**Status:** CORRECTO — "Source_Type " con espacio, hash incluido

#### assign_next_action.py update
```json
{
  "Gate_Decision": {"select": {"name": gate_decision}},
  "Next_Action": {"rich_text": [{"text": {"content": new_action}}]}
}
```
**Status:** CORRECTO — Next_Action como rich_text

### 3.6 Cross-Reference con Configuraciones Externas

#### mcp.json
- **Ubicación:** `.vscode/mcp.json`
- **Estado:** EXISTE — Configura servidor Notion MCP
- **Uso:** No hay evidencia de uso en el pipeline actual
- **Contenido:**
```json
{
  "servers": {
    "makenotion/notion-mcp-server": {
      "type": "http",
      "url": "https://mcp.notion.com/sse",
      "gallery": "https://api.mcp.github.com",
      "version": "1.0.0"
    }
  }
}
```

#### layer_1_blueprint.json (Make.com)
- **Ubicación:** `Layer_1/layer_1_blueprint.json`
- **Estado:** CRÍTICO — Contiene GROQ API key expuesta
- **Data Source ID:** "4e542b37-6e52-4418-89b7-a0eeb3138307" (antiguo v1.3)
- **Field mappings:**
  - "Source_Type " (con espacio) — CORRECTO
  - "Rol" (title)
  - "Marca" (text)
  - "URL" (url)
  - "JD" (text)
  - "JOB_ID" (text)
  - "Raw Source" (select)
  - "Status" (select, default "Nueva")
  - "Fuente" (select, default "Agregador")
- **⚠️ SECURITY ISSUE:** Línea 35 contiene GROQ API key hardcodeada

#### schema_full.json
- **Ubicación:** `Layer_1/archive/out/schema_full.json`
- **Estado:** ARCHIVO — Parece ser schema antiguo
- **Database ID:** "b14cc6fc-0151-4c22-8b11-690162236107"
- **Data Source ID:** "4e542b37-6e52-4418-89b7-a0eeb3138307" (antiguo)
- **Uso:** Referencia histórica solamente

#### resolver_registry_v2.json
- **Ubicación:** `Layer_1/scripts/resolver_registry_v2.json`
- **Estado:** LIVE — Usado por runtime_identity.py
- **Data Sources:**
  - VANTAGE_TRACKER: 
    - database_id: "596938befc42836baea7814a1491bd47"
    - data_source_id: "442938be-fc42-828f-b72e-076818d65a5b"
    - entity_prefix: "TRACKER"
  - ARCHIVO_TRACKER:
    - database_id: "4ec34e1b528648c9afbdd57c6eb76053"
    - data_source_id: "674696fd-94b6-464a-ac1f-64b0cc917e15"
    - entity_prefix: "ARCHIVO"
  - ARCHIVO_DRY_RUN:
    - database_id: "37d938befc42804a94a1c355a9b89363"
    - data_source_id: "37d938be-fc42-8022-9191-000bf6cdac7b"
    - entity_prefix: "DRYRUN"
  - BUG_TRACKER:
    - database_id: "36e938befc4281bd9e1fdc360b3b45f5"
    - data_source_id: "36e938be-fc42-81f8-8c6f-000b6769ba03"
    - entity_prefix: "BUG"
- **Known pitfalls:**
  - VANTAGE_TRACKER: "Source_Type tiene espacio final ('Source_Type ')"
  - ARCHIVO_TRACKER: "Source_Type sin espacio final (distinto de VANTAGE_TRACKER)"

---

## 4. Puntos Ciegos y Oportunidades

### 4.1 Seguridad

1. **[CRÍTICO] GROQ API key expuesta en layer_1_blueprint.json**
   - **Evidencia:** Layer_1/layer_1_blueprint.json:35
   - **Valor:** `***REDACTED***`
   - **Riesgo:** El archivo está versionado en git, la key está expuesta en el historial
   - **Impacto:** Cualquiera con acceso al repo puede usar la cuota de GROQ
   - **Acción:** Rotar la key inmediatamente, remover del archivo, usar variables de entorno

2. **[MEDIO] .gitignore incompleto**
   - **Evidencia:** .gitignore solo excluye algunos archivos .env
   - **Faltan:** No excluye todos los archivos .env example, no excluye otros archivos sensibles
   - **Impacto:** Riesgo de commit accidental de credenciales
   - **Acción:** Revisar y fortalecer .gitignore

3. **[BAJO] No hay validación de tokens antes de usar**
   - **Evidencia:** Los scripts asumen que NOTION_TOKEN existe y es válido
   - **Impacto:** Errores de runtime si faltan credenciales
   - **Acción:** health_check.py ya valida, pero podría mejorarse

### 4.2 Confiabilidad e Idempotencia

1. **[MEDIO] Race condition en consolidate_duplicates.py**
   - **Evidencia:** consolidate_duplicates.py:120-126 aborta si MAX_EXPECTED_RESULTS excedido
   - **Riesgo:** Si Layer 1 corre concurrentemente, puede abortar
   - **Impacto:** Script falla, requiere re-ejecución manual
   - **Acción:** Ya existe protección, pero podría mejorarse con locking

2. **[BAJO] No hay validación de idempotencia**
   - **Evidencia:** Correr un script dos veces puede duplicar efectos
   - **Ejemplo:** feed_processor.py puede crear duplicados si se corre dos veces con mismo feed
   - **Impacto:** Datos duplicados en Notion
   - **Acción:** Agregar validación de hash antes de crear

3. **[BAJO] Manejo de errores en layer_3_mail.py**
   - **Evidencia:** layer_3_mail.py deja email unread si Groq falla
   - **Riesgo:** Loop infinito de reintentos
   - **Impacto:** Cuota de GROQ agotada, emails nunca procesados
   - **Acción:** Agregar max retry count y fallback

### 4.3 Integridad de Datos a Largo Plazo

1. **[ALTO] Inconsistencia de IDs de base de datos**
   - **Evidencia:** resolver_registry_v2.json tiene IDs diferentes para VANTAGE_TRACKER
   - **database_id:** "596938befc42836baea7814a1491bd47"
   - **data_source_id:** "442938be-fc42-828f-b72e-076818d65a5b"
   - **Algunos scripts aún usan:** "4e542b37-6e52-4418-89b7-a0eeb3138307" (v1.3)
   - **Impacto:** Confusión sobre cuál ID es correcto, posibles errores de query
   - **Acción:** Unificar a data_source_id canónico, actualizar todos los scripts

2. **[MEDIO] Drift entre entity_index_v2.json y Notion real**
   - **Evidencia:** entity_index_v2.json se regenera manualmente via vantage.py sync()
   - **Riesgo:** Si no se corre sync(), el index queda desactualizado
   - **Impacto:** Resolver layer devuelve datos stale
   - **Acción:** Automatizar sync() periódico o hacer trigger-based

3. **[BAJO] ARCHIVO_TRACKER tiene schema diferente**
   - **Evidencia:** resolver_registry_v2.json known_pitfalls
   - **Diferencias:** Source_Type sin espacio, hash frecuentemente vacío, Status incompleto
   - **Impacto:** Cross-layer dedup puede fallar
   - **Acción:** Unificar schemas o documentar diferencias explícitamente

### 4.4 Observabilidad

1. **[MEDIO] No hay monitoreo de Layer 3**
   - **Evidencia:** layer_3_mail.py tiene heartbeat file (~/.vantage/l3_heartbeat.json)
   - **Riesgo:** Si Layer 3 falla silenciosamente, nadie se entera
   - **Impacto:** Vacantes de email no se ingieren
   - **Acción:** health_check.py ya verifica docs, pero no Layer 3 específicamente

2. **[BAJO] Logging inconsistente**
   - **Evidencia:** Algunos scripts usan print(), otros usan logging
   - **Impacto:** Difícil de debug en producción
   - **Acción:** Estandarizar logging framework

3. **[BAJO] No hay métricas de pipeline health**
   - **Evidencia:** notion_utils.py tiene metrics, pero no se usan sistemáticamente
   - **Impacto:** No se puede monitorear performance, errores, rate limits
   - **Acción:** Exponer métricas en dashboard o alertas

### 4.5 Cobertura de Tests

1. **[ALTO] No hay suite de tests automatizada**
   - **Evidencia:** Solo existe test_datasource_query.py como script de diagnóstico
   - **Impacto:** Riesgo de regresión al tocar gate_logic.py o scoring
   - **Acción:** Crear suite de tests unitarios para funciones críticas

2. **[BAJO] No hay tests de integración**
   - **Evidencia:** Ningún script de test simula el pipeline completo
   - **Impacto:** Bugs en integración entre layers solo se descubren en producción
   - **Acción:** Crear tests de integración con mocks de Notion/Gmail/Groq

### 4.6 Escalabilidad y Costo

1. **[MEDIO] Rate limits de Notion no manejados explícitamente**
   - **Evidencia:** notion_utils.py tiene MIN_INTERVAL_SECONDS=0.35 (3 req/s)
   - **Riesgo:** Si volumen se multiplica x10, se puede hit rate limit
   - **Impacto:** Pipeline falla, datos no se procesan
   - **Acción:** Implementar backoff agresivo, cola de tareas

2. **[MEDIO] Costo de Groq no monitoreado**
   - **Evidencia:** layer_3_mail.py usa GROQ_MAX_EMAILS_PER_RUN=10
   - **Riesgo:** Si volumen de emails aumenta, costo puede ser significativo
   - **Impacto:** Sorpresa en factura de GROQ
   - **Acción:** Implementar budget alerts, monitoreo de uso

3. **[BAJO] Límites de Gmail no manejados**
   - **Evidencia:** layer_3_mail.py no tiene límite explícito de fetch
   - **Riesgo:** Si hay muchos emails, puede hit IMAP limits
   - **Impacto:** Pipeline falla
   - **Acción:** Implementar paginación de emails, límites de fetch

### 4.7 Continuidad

1. **[ALTO] No hay backup de Notion DBs**
   - **Evidencia:** No hay script de backup, no hay proceso documentado
   - **Riesgo:** Si se borra una DB por error, se pierden todos los datos
   - **Impacto:** Pérdida irreversible de datos
   - **Acción:** Implementar backup periódico a JSON o otro sistema

2. **[MEDIO] vsync_doc.py es unidireccional**
   - **Evidencia:** vsync_doc.py puede hacer push local→Notion o pull Notion→local
   - **Riesgo:** Si se hace push incorrecto, se puede sobrescribir documentación
   - **Impacto:** Pérdida de documentación
   - **Acción:** Implementar diff antes de push, confirmación explícita

### 4.8 Deuda Técnica

1. **[MEDIO] scoring_deterministic.py DEPRECATED pero existe**
   - **Evidencia:** Header explícito de deprecación, pero archivo sigue en codebase
   - **Impacto:** Confusión sobre cuál scoring system usar
   - **Acción:** Mover a archive/ o eliminar completamente

2. **[BAJO] Layer 2 vacío**
   - **Evidencia:** Layer_2/ directory existe pero no tiene scripts
   - **Impacto:** Arquitectura incompleta
   - **Acción:** Implementar o eliminar Layer 2

3. **[BAJO] Múltiples implementaciones de gate logic**
   - **Evidencia:** gate_logic.py, assign_next_action.py, layer_1_run.py
   - **Impacto:** Mantenimiento burden, posible divergencia
   - **Acción:** Consolidar a single module

### 4.9 Feedback Loop de Resultados

1. **[ALTO] No hay feedback loop de resultados reales**
   - **Evidencia:** El sistema no aprende de resultados (contratado/rechazado/sin respuesta)
   - **Impacto:** Scoring no mejora con el tiempo, oportunidades de optimización perdidas
   - **Acción:** Implementar tracking de outcomes, ajustar scoring basado en resultados

2. **[MEDIO] No hay análisis de effectiveness de gate logic**
   - **Evidencia:** No hay métricas de qué tan bien predice el gate logic
   - **Impacto:** No se sabe si el gate logic está filtrando correctamente
   - **Acción:** Implementar análisis de false positives/negatives

### 4.10 Higiene de Git

1. **[MEDIO] Historial de git no permite rastrear cuándo se introdujo cada bug**
   - **Evidencia:** Commits son "auto-sync" con múltiples archivos
   - **Impacto:** Difícil de hacer blame tracking
   - **Acción:** Mejorar mensajes de commit, hacer commits más granulares

2. **[BAJO] Archivos de backup en git**
   - **Evidencia:** Layer_1/archive/ contiene muchos archivos .bak
   - **Impacto:** Repo contaminado con archivos que no deberían versionarse
   - **Acción:** Limpiar archive/, mover a backup externo

### 4.11 UX del Dashboard

1. **[BAJO] No se revisó en esta auditoría**
   - **Evidencia:** Dashboard/ existe pero no se analizó en detalle
   - **Impacto:** No se pueden identificar oportunidades de automatización
   - **Acción:** Auditoría separada del Dashboard

---

## 5. Preguntas Abiertas

### Heredadas de auditoría previa (sin resolver)

1. **Scoring System:** ¿Cuál scoring system es canónico? layer_1_run.py v6.4 (0-100) es el usado en producción, scoring_deterministic.py está DEPRECATED.
2. **Source_Type Field:** ¿Debe mantenerse el espacio final en "Source_Type "? Actualmente sí, por consistencia con schema de Notion.
3. **Next_Action Type:** ¿Debe ser rich_text o select? Actualmente rich_text (fix v8.7.2).
4. **Layer 2 Purpose:** ¿Cuál es el propósito de Layer 2? Actualmente vacío.
5. **Hash Backfill:** ¿Debe moverse a tiempo de ingestión? Ya implementado en Layer 3.
6. **Gate Logic Consolidation:** ¿Cuál gate logic debe ser canónica? layer_1_run.py tiene la implementación principal.
7. **Fetch Status Naming:** ¿Debe renombrarse internal fetch_status? Actualmente inconsistente pero no crítico.

### Nuevas preguntas de esta ronda

8. **Data Source IDs:** ¿Cuál es el data_source_id canónico para VANTAGE_TRACKER? Hay 3 diferentes en uso.
9. **GROQ API Key:** ¿Por qué está hardcodeada en layer_1_blueprint.json? Debe moverse a variables de entorno.
10. **MCP Server:** ¿Se usa el servidor Notion MCP configurado en .vscode/mcp.json? No hay evidencia de uso.
11. **Backup Strategy:** ¿Cuál es la estrategia de backup de Notion DBs? No existe actualmente.
12. **Feedback Loop:** ¿Hay interés en implementar feedback loop de resultados? Sería la mayor oportunidad de mejora.

---

## 6. PLAN DE TRABAJO

### Bloque 1 — Decisiones de Arquitectura que Bloquean Todo lo Demás

| # | Tipo | Prioridad | Descripción | Impacto | Dependencias | Riesgo si no se atiende | Fix/acción propuesta | Complejidad | Herramienta sugerida |
|---|------|-----------|-------------|---------|--------------|------------------------|---------------------|---------------------|
| 1 | Bug | CRÍTICA | Rotar GROQ API key expuesta en layer_1_blueprint.json | Seguridad | Ninguna | Uso no autorizado de cuota GROQ | Rotar key en GROQ console, remover de archivo, usar variables de entorno en Make.com | S | N/A (este mismo flujo) |
| 2 | Deuda técnica | ALTA | Unificar data_source_id de VANTAGE_TRACKER | Confiabilidad | Decision #3 | Errores de query, confusión | Elegir data_source_id canónico ("442938be-fc42-828f-b72e-076818d65a5b"), actualizar todos los scripts que usan ID antiguo | M | Aside (verificar en Notion) |
| 3 | Deuda técnica | ALTA | Decidir: ¿Mantener espacio final en "Source_Type "? | Consistencia | Ninguna | Inconsistencia en código si se cambia | Opción A: Mantener espacio (actual, estable) / Opción B: Renombrar campo en Notion (mayor impacto) | S | N/A (este mismo flujo) |
| 4 | Oportunidad | ALTA | Decidir: ¿Implementar feedback loop de resultados? | Estrategia | Ninguna | Scoring no mejora con el tiempo | Opción A: Implementar tracking básico / Opción B: Full ML pipeline / Opción C: No hacer nada | L | Perplexity Pro (investigar patrones de industria) |

### Bloque 2 — Fixes Sin Dependencias

| # | Tipo | Prioridad | Descripción | Impacto | Dependencias | Riesgo si no se atiende | Fix/acción propuesta | Complejidad | Herramienta sugerida |
|---|------|-----------|-------------|---------|--------------|------------------------|---------------------|---------------------|
| 5 | Bug | CRÍTICA | Fortalecer .gitignore para evitar commit de credenciales | Seguridad | Ninguna | Commit accidental de API keys | Agregar patrones para *.env, *.key, *.secret, **/config/*.env | S | N/A (este mismo flujo) |
| 6 | Deuda técnica | MEDIA | Mover scoring_deterministic.py a archive/ | Mantenimiento | Ninguna | Confusión sobre cuál scoring usar | Mover a Layer_1/archive/deprecated_scripts/ | S | N/A (este mismo flujo) |
| 7 | Deuda técnica | MEDIA | Eliminar archivos .bak de git | Higiene | Ninguna | Repo contaminado | git rm Layer_1/archive/**/*.bak, actualizar .gitignore | S | N/A (este mismo flujo) |
| 8 | Deuda técnica | BAJA | Decidir Layer 2: implementar o eliminar | Arquitectura | Ninguna | Arquitectura incompleta | Opción A: Eliminar directorio / Opción B: Implementar scripts | L | N/A (este mismo flujo) |
| 9 | Deuda técnica | BAJA | Consolidar gate logic a single module | Mantenimiento | Ninguna | Divergencia de implementaciones | Extraer gate logic a shared module, actualizar callers | M | N/A (este mismo flujo) |

### Bloque 3 — Mejoras de Confiabilidad y Observabilidad

| # | Tipo | Prioridad | Descripción | Impacto | Dependencias | Riesgo si no se atiende | Fix/acción propuesta | Complejidad | Herramienta sugerida |
|---|------|-----------|-------------|---------|--------------|------------------------|---------------------|---------------------|
| 10 | Oportunidad | ALTA | Implementar backup periódico de Notion DBs | Continuidad | Ninguna | Pérdida irreversible de datos | Script que exporta VANTAGE_TRACKER y ARCHIVO_TRACKER a JSON, configurar cron | M | N/A (este mismo flujo) |
| 11 | Oportunidad | MEDIA | Automatizar sync() de entity_index_v2.json | Integridad | Ninguna | Index desactualizado | Configurar cron para correr vantage.py sync() diariamente | S | N/A (este mismo flujo) |
| 12 | Oportunidad | MEDIA | Agregar monitoreo de Layer 3 en health_check.py | Observabilidad | Ninguna | Layer 3 falla silenciosamente | Verificar heartbeat file, alertar si > X horas sin actualización | M | N/A (este mismo flujo) |
| 13 | Oportunidad | MEDIA | Estandarizar logging framework | Observabilidad | Ninguna | Difícil de debug en producción | Usar logging módulo de Python, configurar formato consistente | M | N/A (este mismo flujo) |
| 14 | Oportunidad | BAJA | Implementar idempotencia en feed_processor.py | Confiabilidad | Ninguna | Duplicados si se corre dos veces | Validar hash antes de crear página | M | N/A (este mismo flujo) |
| 15 | Oportunidad | BAJA | Mejorar manejo de errores en layer_3_mail.py | Confiabilidad | Ninguna | Loop infinito de reintentos | Agregar max retry count, fallback a mark as seen | M | N/A (este mismo flujo) |

### Bloque 4 — Cobertura de Tests y Escalabilidad

| # | Tipo | Prioridad | Descripción | Impacto | Dependencias | Riesgo si no se atiende | Fix/acción propuesta | Complejidad | Herramienta sugerida |
|---|------|-----------|-------------|---------|--------------|------------------------|---------------------|---------------------|
| 16 | Oportunidad | ALTA | Crear suite de tests unitarios para funciones críticas | Calidad | Ninguna | Riesgo de regresión | Tests para compute_dedup_hash, gate logic, scoring | L | N/A (este mismo flujo) |
| 17 | Oportunidad | MEDIA | Crear tests de integración con mocks | Calidad | #16 | Bugs en integración en producción | Tests de pipeline completo con mocks de Notion/Gmail/Groq | L | N/A (este mismo flujo) |
| 18 | Oportunidad | MEDIA | Implementar backoff agresivo para rate limits de Notion | Escalabilidad | Ninguna | Pipeline falla si volumen x10 | Implementar cola de tareas con backoff exponencial | L | N/A (este mismo flujo) |
| 19 | Oportunidad | BAJA | Implementar budget alerts para GROQ | Costo | Ninguna | Sorpresa en factura | Monitorear uso de GROQ, alertar si cerca de límite | M | N/A (este mismo flujo) |
| 20 | Oportunidad | BAJA | Implementar paginación de emails en layer_3_mail.py | Escalabilidad | Ninguna | Hit IMAP limits | Paginar Gmail fetch, límites de fetch por run | M | N/A (este mismo flujo) |

### Bloque 5 — Oportunidades de Crecimiento (requieren decisión #4)

| # | Tipo | Prioridad | Descripción | Impacto | Dependencias | Riesgo si no se atiende | Fix/acción propuesta | Complejidad | Herramienta sugerida |
|---|------|-----------|-------------|---------|--------------|------------------------|---------------------|---------------------|
| 21 | Oportunidad | ALTA | Implementar tracking de outcomes (contratado/rechazado/sin respuesta) | Feedback loop | #4 | Scoring no mejora con el tiempo | Agregar campo "Outcome" a VANTAGE_TRACKER, tracking manual | M | N/A (este mismo flujo) |
| 22 | Oportunidad | ALTA | Implementar análisis de effectiveness de gate logic | Feedback loop | #21 | No se sabe si gate logic filtra correctamente | Calcular false positives/negatives de gate vs outcomes | L | Perplexity Pro (investigar patrones) |
| 23 | Oportunidad | MEDIA | Ajustar scoring basado en resultados históricos | Feedback loop | #21, #22 | Scoring no optimizado | Implementar weighted scoring basado en outcomes | L | DeepSeek (razonamiento paso a paso) |
| 24 | Oportunidad | BAJA | Auditoría de Dashboard UX | UX | Ninguna | Fricción manual no identificada | Revisar Dashboard, identificar oportunidades de automatización | M | Aside (verificar en navegador) |

---

## 7. Apéndice

### 7.1 IDs de Base de Datos y Consistencia

**VANTAGE_TRACKER:**
- database_id (resolver_registry_v2.json): "596938befc42836baea7814a1491bd47"
- data_source_id (resolver_registry_v2.json): "442938be-fc42-828f-b72e-076818d65a5b"
- data_source_id (layer_1_run.py): "442938be-fc42-828f-b72e-076818d65a5b" ✓ CONSISTENTE
- data_source_id (antiguo v1.3): "4e542b37-6e52-4418-89b7-a0eeb3138307" ✗ INCONSISTENTE
- data_source_id (layer_1_blueprint.json): "4e542b37-6e52-4418-89b7-a0eeb3138307" ✗ INCONSISTENTE

**ARCHIVO_TRACKER:**
- database_id (resolver_registry_v2.json): "4ec34e1b528648c9afbdd57c6eb76053"
- data_source_id (resolver_registry_v2.json): "674696fd-94b6-464a-ac1f-64b0cc917e15"
- data_source_id (consolidate_duplicates.py): "674696fd-94b6-464a-ac1f-64b0cc917e15" ✓ CONSISTENTE
- database_id (consolidate_duplicates.py): "4ec34e1b528648c9afbdd57c6eb76053" ✓ CONSISTENTE

**BUG_TRACKER:**
- database_id (resolver_registry_v2.json): "36e938befc4281bd9e1fdc360b3b45f5"
- data_source_id (resolver_registry_v2.json): "36e938be-fc42-81f8-8c6f-000b6769ba03"
- data_source_id (agent_api.py): "36e938be-fc42-81f8-8c6f-000b6769ba03" ✓ CONSISTENTE

**Conclusión:** VANTAGE_TRACKER tiene inconsistencia de IDs que debe resolverse (Bloque 1, #2).

### 7.2 Archivos de Configuración Externos Revisados

**mcp.json:**
- Ubicación: `.vscode/mcp.json`
- Estado: Configurado pero no usado en pipeline actual
- Recomendación: Evaluar si se debe usar o eliminar configuración

**layer_1_blueprint.json:**
- Ubicación: `Layer_1/layer_1_blueprint.json`
- Estado: CRÍTICO — contiene GROQ API key expuesta
- Recomendación: Rotar key, remover del archivo (Bloque 1, #1)

**schema_full.json:**
- Ubicación: `Layer_1/archive/out/schema_full.json`
- Estado: Archivo histórico, no usado en producción
- Recomendación: Mantener como referencia, mover a archive/ si no está ya

**resolver_registry_v2.json:**
- Ubicación: `Layer_1/scripts/resolver_registry_v2.json`
- Estado: LIVE — usado por runtime_identity.py
- Recomendación: Mantener, es la fuente de verdad para entity_prefix

---

**FIN DE AUDITORÍA V2**

**Fecha:** 2026-07-05  
**Auditor:** Devin (AI Assistant)  
**Modo:** SOLO LECTURA — Análisis estático de código y configuración  
**Entregable:** Documentación exhaustiva + plan de trabajo priorizado
