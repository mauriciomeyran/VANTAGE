# VANTAGE ARCHITECTURE — v7.5

## 1. Script Inventory

| Script | Rol | Status |
|---|---|---|
| `layer_1_run.py` | PIPELINE PRINCIPAL v7.5 — tracker Notion (URL Gate, Fuente, Scoring, Gates) | Active |
| `layer_2_mail.py` | Mail processor — PATRÓN DE REFERENCIA para .env y Notion write | Active |
| `feed_processor.py` | FEED Layer 1 + Layer 3 — pipeline unificado | Pending (P1) |
| `dedup_opportunities.py` | Dedup existente (intra-layer) | Active |
| `gate_logic.py` | URL_GATE existente | Active |
| `layer_1_pipeline.sh` | Shell dispatcher | Active |

---

## 2. Envelope Types por Layer

| Layer | Fuente | Envelope key | Estructura |
|---|---|---|---|
| L1 | you.com / Grok | `results_by_source` | Dict de buckets → flatten a lista plana |
| L2 | Mail | N/A | Procesado por `layer_2_mail.py` |
| L3 | LinkedIn | `listings` | Lista plana directa |

**Regla:** `normalize_envelope()` detecta el envelope y entrega siempre `list[dict]` con campo `layer` inyectado.

---

## 3. Class A Schema — Campos Notion

### Campos existentes (referencia)
- `title` (title)
- `brand` (select)
- `status` (select)
- `apply_url` (url)
- `location` (rich_text)
- `fetch_status` (select: `career_page` | `aggregator`)
- `notes` (rich_text)

### Campos nuevos v7.5 — Class A

| Campo | Tipo Notion | Valores | Descripción |
|---|---|---|---|
| `layer` | select | `L1` / `L2` / `L3` | Origen del registro |
| `hash` | rich_text | string SHA-256 | Clave de dedup cross-layer |

---

## 4. Status Values

| Status | Quién escribe | Descripción |
|---|---|---|
| `Target` | Python | Registro limpio, Class A completo |
| `REVIEW_NEEDED` | Python | Alias no resuelto, URL falla, semi-duplicate |
| `BLOCKED` | Python | Hard block — NO se escribe en Notion |
| `Applied` | Operador | Postulación enviada |
| `Discarded` | Operador | Descartado manualmente |

---

## 5. Dedup Strategy

- **Hash primario:** `apply_url` normalizada — solo si `fetch_status = career_page`
- **Hash secundario:** `brand|title|location` — para aggregators
- **Hash terciario:** `job_id` — si existe y no es generado
- **Ventana:** 30 días
- **Scope:** Toda la DB Notion (cross-layer)
- **Campo:** `hash` escrito Y consultado desde Notion

---

## 6. BOUNDARY v7.5

- **Claude-territory:** CV Pipeline · CANON-UPDATE · `FAST [URL]`
- **Python-territory:** FEED Layer 1 · FEED Layer 3
- **Excepción FAST:** array longitud 1 + trigger explícito = Claude procesa normal

---

## 7. `layer_1_run.py` — Pipeline v7.5

Territorio Claude sobre el **tracker legacy** (campos: `Rol`, `Marca`, `URL`, `Fuente`, `Score`, `Source_Type`, `Gate_Decision`, `Status`, etc.).

| Paso | Nombre | Descripción |
|---|---|---|
| 0 | URL Gate pre-scoring | Valida URLs; agregadores aceptados; JD >100 chars bypass; Inbound/Referencia/Networking → CREATE |
| 0.5 | Asignación Fuente | `Career Page Oficial` / `Agregador` — **Vacante e Inbound** con URL |
| 1 | Scoring v6.4 | `Score`, `Match`, `VM_Scope`, `Role_Class` — escribe Score si está vacío (`None`) |
| 2 | URL re-check | Re-validación solo para registros válidos post-scoring |
| 3 | Gate logic | `Gate_Decision` con protecciones (whitelist, SPA, BYPASS types) |
| 4 | Análisis patrones | Tasas de rechazo por empresa |

**Cambios v7.5:**
- Paso 0.5: eliminado filtro `Source_Type == Vacante` — Inbound con URL recibe `Fuente`
- Paso 1: condición explícita `current_score is None` para backfill de Score vacío
- Paginación: `query_all_items()` — Notion devuelve máx. 100 registros por página (DB actual: 125+)
- Class A (`layer`, `hash`, dedup cross-layer): responsabilidad de `feed_processor.py`, no de este script

**Ejecución:** `python3 scripts/layer_1_run.py` · alias `vantagep`

---

## 8. Paths de referencia

| Recurso | Path |
|---|---|
| LAYER_1 root | `~/Documents/04-VANTAGE_CV/LAYER_1` |
| Pipeline runner | `LAYER_1/scripts/layer_1_run.py` |
| Feed processor | `LAYER_1/scripts/feed_processor.py` |
| Shell dispatcher | `LAYER_1/layer_1_pipeline.sh` |
| Alias público | `~/vantage_pipeline.sh` → `wrappers/layer_1_wrapper.sh` |
| Feeds JSON | `~/Documents/04-VANTAGE_CV/Feeds/` |

