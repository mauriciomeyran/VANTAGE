```markdown
# MANUAL DE USUARIO — VANTAGE v8.4
ID: 372938be-fc42-8050-9a67-e40857d7806e
Última actualización: 2026-06-17 · Post-Audit Documentation Renewal

---

## DECLARACIÓN DE AUDIENCIA Y ALCANCE
**Audiencia:** Operador humano.
**Alcance:** Configuración inicial, ciclo operativo semanal, comandos y flujos de uso.
**Regla de separación:** El Manual responde *cómo*. El Kernel responde *por qué*.

---

## ÍNDICE

| SECCIÓN | CONTENIDO | PORCIÓN |
|---|---|---|
| 1 | OBJETIVO DE VANTAGE | CONTEXTO |
| 2 | CÓMO FUNCIONA | CONTEXTO |
| 3 | SETUP | OPERACIÓN |
| 4 | FLUJO PUNTA A PUNTA | OPERACIÓN |
| 5 | VANTAGE RUNTIME | OPERACIÓN |
| 6 | TRACKER | OPERACIÓN |
| 7 | TROUBLESHOOTING | OPERACIÓN |
| 8 | PROMPTS & WRAPPERS | REFERENCIA |
| 9 | CHEAT SHEETS | REFERENCIA |
| 10 | HEALTH CHECK | REFERENCIA |
| 11 | CHANGELOG | REFERENCIA |
| 12 | REGLAS DE ORO | REFERENCIA |
| 13 | FILOSOFÍA DE FALLO | REFERENCIA |

---

## 5. VANTAGE RUNTIME
> ID: 372938be-fc42-8050-9a67-e40857d7806e:manual-runtime-001

VANTAGE Runtime es la capa de lectura/consulta del sistema. Vive en `Layer_1/scripts/`. Es solo lectura — nunca escribe en Notion.

### 5.1 Comandos disponibles

| Comando | Qué hace | Input | Output |
|---|---|---|---|
| `status` | Healthcheck: tamaño del index, métricas Notion, edad del index | ninguno | dict con `entity_index`, `notion_client_metrics`, `index_age_hours` |
| `ask "<prompt>"` | Lenguaje natural → intención → resultado | string libre | dict con `intent`, `count`, `results` |
| `resolve <entity_id>` | Resuelve un entity_id contra Notion en vivo | `PREFIX:H_xxxx` | `{entity_id, status, source_db, page_url, resolved}` |
| `context <entity_id>` | Propiedades + bloques de la página Notion | `PREFIX:H_xxxx` | `{entity, status, metadata, content}` |
| `query "<valor>"` | Busca por entity_id exacto, hash, o texto libre | string | `{query, match_type, count, results}` |
| `sync` | Regenera `entity_index_v2.json` desde Notion en vivo (atomic write) | ninguno | `{status, entities_before, entities_after, elapsed_seconds}` |

**CLI:**
```bash
cd ~/Documents/04-VANTAGE_CV/LAYER_1/scripts
source ../.venv/bin/activate
python3 vantage.py status
python3 vantage.py ask "show active roles"
python3 vantage.py resolve TRACKER:H_<id>
python3 vantage.py context TRACKER:H_<id>
python3 vantage.py query "<texto>"
python3 vantage.py sync
```

**Como módulo Python:**

```python
from vantage import ask, resolve, context, query, status, sync
```

### 5.2 Cuándo usar `sync`

Correr `sync` después de:

- Cualquier ciclo L1/L2 que haya escrito entradas nuevas en Notion
- Después de resolver entradas `REVIEW_NEEDED` en el Tracker
- Si `status` muestra `"warning": "entity_index_stale"` (index > 24h)
- Si `status` muestra `orphan_candidates > 0` de forma persistente

No es necesario para cambios de `Status`, `Score`, `Gate_Decision` en páginas individuales — esos se leen en vivo vía `resolve`/`context`.

### 5.3 Staleness indicator

`vantage.py status` incluye `index_age_hours`. Si el index tiene más de 24 horas, el output incluye:

```json
"warning": "entity_index_stale"
```

Acción: correr `python3 vantage.py sync`.

### 5.4 Errores comunes

| Error | Causa | Solución |
| --- | --- | --- |
| `{"status": "notion_error", "error": "missing notion api token"}` | `NOTION_TOKEN` no está en el entorno | Verificar `.env` en `LAYER_1/` y que `load_dotenv` lo cargue |
| `{"status": "unknown_entity"}` | entity_id no existe en el index | Correr `sync` primero; verificar que la entidad existe en Notion |
| `{"status": "not_found", "error": "no registry mapping"}` | `source_db` no en `resolver_registry_v2.json` | Revisar mapeo en el registry |
| 401 de Notion | Token inválido o revocado | Regenerar token en Notion, actualizar `.env` |
| `RuntimeError: query_layer no encontrado` | Ejecutando desde directorio incorrecto | Ejecutar siempre desde `Layer_1/scripts/` con venv activado |
| `{"status": "error", "error": "No se pudo cargar generate_entity_index_v2"}` | Módulo generador no encontrado | Verificar que `generate_entity_index_v2.py` existe en `Layer_1/scripts/` |

---

## 7. TROUBLESHOOTING

### 7.1 Diagnósticos Runtime

| Síntoma | Diagnóstico | Acción |
| --- | --- | --- |
| `status` devuelve `total_entities: 0` o error de archivo | `entity_index_v2.json` falta o corrupto | `python3 vantage.py sync` |
| `status` muestra `"warning": "entity_index_stale"` | Index > 24h | `python3 vantage.py sync` |
| `ask "show active roles"` devuelve `errors: [...]` no vacío | Entidades de VANTAGE_TRACKER fallan al resolver | Revisar cada `{entity_id, error}` en la lista |
| `ask "show archived history"` o `ask "show bugs"` devuelve `{"error": ...}` | Endpoint obsoleto en esos handlers | Ver `resolver_registry_v2.json["known_pitfalls"]["general"]`; evitar hasta refactor |
| `resolve`/`context` devuelven `notion_error` | Token ausente o rate limit | Verificar `.env` (`NOTION_TOKEN`) |
| `resolve` devuelve `not_found` para entidad que sí existe | Bug de paginación RID-02 en Archivo Tracker (>100 páginas) | Issue conocido. Abierto como RID-02. Workaround: usar `context` + revisar entity_index directamente |

### 7.2 Diagnósticos Pipeline

| Síntoma | Diagnóstico | Acción |
| --- | --- | --- |
| Vacante nueva no aparece en `find_candidates` | Entity index stale | `python3 vantage.py sync` |
| Entrada con `REVIEW_NEEDED` permanece sin procesar | Status no cambiado a `Target` | Corregir campo problemático en Notion → cambiar `Status` a `Target` → correr pipeline |
| `vantage_pipeline.sh` no procesa una entrada | Entrada no cumple criterios mínimos | Revisar campo `Notas` en la entrada; usar RT-1 si `Gate = BLOCKED` |
| L3 no parece ingestar correos recientes | `mail_pipeline.py` puede estar caído | Verificar credenciales IMAP/Groq en `layer_3.env`; correr `vl3` manualmente |

### 7.3 Cache

```bash
python3 notion_client.py metrics       # ver métricas de cache
python3 notion_client.py clear-cache   # limpiar cache (seguro, no destructivo)
python3 notion_client.py reset-metrics # resetear contadores
```

---

## 10. HEALTH CHECK

### 10.1 Verificación rápida del sistema

```bash
cd ~/Documents/04-VANTAGE_CV/LAYER_1/scripts
source ../.venv/bin/activate
python3 vantage.py status
```

Output esperado (sistema sano):

```json
{
  "runtime": "VANTAGE",
  "entity_index": {
    "total_entities": 465,
    "metrics": {
      "hash_coverage": 100.0,
      "orphan_candidates": 0
    }
  },
  "index_age_hours": <24
}
```

Si `index_age_hours > 24` o aparece `"warning": "entity_index_stale"`: correr `sync`.

### 10.2 Smoke tests

```bash
python3 vantage.py status                           # total_entities > 0, sin error
python3 vantage.py ask "show active roles"          # errors: [] o lista corta conocida
python3 vantage.py resolve TRACKER:H_<id_conocido>  # status: "resolved"
python3 vantage.py context TRACKER:H_<id_conocido>  # entity/status/metadata/content presentes
```

---

## ARRANQUE FRÍO — Checklist de Reactivación

> Basado en M-08 de la Auditoría Técnica v8.4
Usar cuando el sistema no ha sido operado por más de 5 días.
> 

**Checklist:**

```
□ 1. Verificar entorno
      cd ~/Documents/04-VANTAGE_CV/LAYER_1/scripts
      source ../.venv/bin/activate
      python3 --version  # debe ser 3.8+

□ 2. Verificar token Notion
      cat ../.env | grep NOTION_TOKEN  # debe estar presente y no expirado
      # Si expirado: regenerar en Notion → Settings → API → New token

□ 3. Status del Runtime
      python3 vantage.py status
      # Revisar: total_entities, hash_coverage, index_age_hours, warning

□ 4. Sincronizar Entity Index
      python3 vantage.py sync
      # Esperar confirmación: status: "ok", entities_after >= entities_before

□ 5. Verificar Tracker en Notion
      Abrir VANTAGE TRACKER → vista "All"
      Buscar entradas con Status = REVIEW_NEEDED
      Resolver cada una: corregir campo → Status: Target → correr pipeline

□ 6. Verificar L3 (mail pipeline)
      Correr vl3 manualmente una vez
      Si falla: verificar layer_3.env (IMAP credentials, GROQ_API_KEY)

□ 7. Verificar archivos pendientes
      ls Layer_1/scripts/*.bak 2>/dev/null   # mover o eliminar .bak acumulados
      ls Layer_1/scripts/_DEPRECATED_*        # eliminar si ya confirmado

□ 8. Smoke test final
      python3 vantage.py ask "show active roles"
      python3 vantage.py ask "find candidates"
      # Confirmar que la lista refleja el estado actual de Notion
```