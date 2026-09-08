# VANTAGE — Active Search Orchestrator Prompt

> **Nota:** Este prompt es el ejecutor manual del skill `vantage-active-search-weekly`. No requiere cronjob. Se invoca en sesión cuando el operador necesita ejecutar la búsqueda.

---

## Contexto inicial (se resuelve al inicio)

Antes de ejecutar cualquier búsqueda, resolvé:

```bash
date +%Y-%m-%d
```

Esa fecha (`{HOY}`) se usará en todos los nombres de archivo y en los registros.

---

## 0. Firmar el inicio (KERNEL:DOCUMENTATION-005)

Antes de empezar a navegar, anuncia:

```
SEARCHING...
```

Al terminar, anuncia:

```
SEARCH COMPLETE
```

---

## 1. Firmas del perfil (Prompt A)

El candidato es **Mauricio Meyrán**. Aplicá estrictamente:

### Seniorities aceptadas
Coordinator, Senior Coordinator, Lead, Supervisor, Líder, Subgerente, Assistant Manager, Manager, Sr., Jefe, Head (solo IC — verificar en JD que es individual contributor, no reporting a c-level).

### Location
Mexico City (CDMX) + Área Metropolitana de CDMX. Rechazar:
- Remote fuera de México
- EdoMex que no sea el Área Metropolitana (Naucalpan, Ecatepec, Tlalnepantla, Nezahualcóyotl, Atizapán, etc.)

### Work modes aceptados
On-site, Hybrid. Rechazar Remote puro fuera de México.

### Industrias aceptadas
Luxury, Premium, Fashion, Beauty, Cosmetics, Fragrances, Jewelry, Sportswear, Experiential Retail.

### Títulos excluidos (rechazar inmediatamente si el título COMPLETO contiene cualquiera de estos)
Store Manager, Director, VP, C-Level, Assistant, Asistente, Auxiliar, Jr., Internship, Intern, Entry Level, Pasantía, Sales Advisor, Vendedor, Asesor Comercial.

**Regla:** el título completo se evalúa como string. Ejemplos:
- `Coordinator Jr.` → Rechazar (contiene "Jr.")
- `Visual Merchandising Jr. Coordinator` → Rechazar (contiene "Jr.")
- `Sr. Visual Merchandiser` → Aceptar
- `Assistant Visual Merchandising` → Rechazar (contiene "Assistant")
- `Store Manager Regional` → Rechazar (contiene "Store Manager")

### Empresas bloqueadas (no buscar, no registrar bajo ningún circumstance)
L'Oréal (todas las divisiones), Levi's, Dockers, El Palacio de Hierro.

---

## 2. Fuentes (ejecutar en orden)

### 2.1 LinkedIn Jobs

**Pre-requisitos:** Lee `skills/vantage-active-search-weekly/search_queries.json` para obtener las 3 variantes de búsqueda.

Cada variante tiene: `name`, `keywords`, `location`, `geoId`, `f_TPR`.

**Protocolo por variante:**

Para cada una de las 3 variantes:

1. Construí la URL de búsqueda:
   ```
   https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}&geoId={geoId}&f_TPR={f_TPR}
   ```
2. Navegá con `new_tab(url)`.
3. Esperá carga con `wait_for_load()`.
4. Extraé todos los `a[href*="/jobs/view/"]` de la página.
5. Dedupé por `job_id` (primera ocurrencia).
6. Para cada job, visitá la detail page y extraé:
   - `title` (truncar al primer `\n`, `|`, `—`)
   - `company`
   - `location`
   - `posted_date` (time o "Hace N ...")
   - `jd_snippet` (primer párrafo del JD)
7. Aplicá exclusiones de Prompt A.
8. Si pasa → agregar a `jobs`.
9. Si falla → agregar a `rejected_jobs` con `rejection_reason`.

**Errores de LinkedIn:**

- **429 Rate Limiting:** registrar en `audit_log`, dejar los jobs restantes en `not_evaluated`, continuar con la siguiente variante.
- **Login Wall:** registrar en `audit_log`, dejar los jobs sin poder validar en `not_evaluated`, continuar.
- **Cloudflare block:** registrar en `audit_log`, detener la variante actual, continuar con la siguiente.

**Dedup:** por `job_id`. Si dos variantes devuelven el mismo `job_id`, conservar la primera.

**Output:** escribir `Layer_1/feeds/{HOY}_linkedin_raw.json` con el siguiente formato:

```json
{
  "source": "linkedin",
  "searched_at": "{HOY}",
  "variants_executed": ["VM_BRAND_RETAIL", "VM_SPECIFIC", "BRAND_STORE"],
  "jobs": [
    {
      "title": "...",
      "company": "...",
      "location": "...",
      "apply_url": "https://mx.linkedin.com/jobs/view/...",
      "posted_date": "2026-09-01",
      "job_id": "4457550792",
      "platform_signals": "Hace 1 semana, 99 solicitudes",
      "jd": "...",
      "seniority": "",
      "work_mode": "",
      "industry": "Sportswear",
      "source_type": "linkedin"
    }
  ],
  "rejected_jobs": [
    {
      "title": "...",
      "company": "...",
      "location": "...",
      "rejection_reason": "excluded_title:Jr."
    }
  ],
  "not_evaluated": {
    "reason": "...",
    "items": [
      {
        "title": "...",
        "job_id": "...",
        "reason": "URL bloqueada / login wall / 429"
      }
    ]
  },
  "audit_log": [
    {
      "type": "HTTP",
      "platform": "LinkedIn",
      "detail": "429 Rate Limiting tras 15 visitas consecutivas",
      "timestamp": "{HOY}T..."
    }
  ],
  "search_metadata": {
    "variants_executed": 3,
    "total_jobs_extracted": 49,
    "total_jobs_after_dedup": 45
  }
}
```

### 2.2 Career Sites

**Pre-requisitos:** Lee `skills/vantage-active-search-weekly/sources/career_sites.md` para la lista de marcas objetivo por sector.

**Protocolo por marca:**

Para cada marca en los grupos A-E (salvo las bloqueadas):

1. Intentá acceder a la URL de career page (ver marca en el archivo).
2. Si la página está accesible:
   - Buscá listings con keywords "Visual Merchandising", "Brand Experience", "Retail Experience", "Store Design".
   - Extraé cada listing: title, location, posted_date, apply_url.
   - Para cada listing, visitá la detail page.
   - Extraé: title completo, company, location, posted_date, job_id (si está en URL), jd_snippet.
   - Aplicá exclusiones de Prompt A.
   - Si pasa → agregar a `jobs`.
   - Si falla → agregar a `rejected_jobs`.
3. Si la página NO está accesible (Cloudflare, DNS, 403, 404, SSL):
   - Registrar en `audit_log`.
   - Intentá URL alternativa si existe (ATS o LinkedIn Jobs para la marca).
   - Si ninguna funciona → dejar la marca como "no accesible", continuar con la siguiente.

**Marcas bloqueadas:** no buscar. Si aparece una vacante de marca bloqueada, rechazar inmediatamente.

**Output:** escribir `Layer_1/feeds/{HOY}_career_sites_raw.json` con formato similar al de LinkedIn.

```json
{
  "source": "career_sites",
  "searched_at": "{HOY}",
  "brands_attempted": ["CHANEL", "Dior", "Gucci", ...],
  "brands_accessible": ["Nike", "M·A·C"],
  "brands_blocked": ["CHANEL", "Gucci", ...],
  "jobs": [...],
  "rejected_jobs": [...],
  "not_evaluated": {...},
  "audit_log": [
    {
      "type": "Cloudflare",
      "brand": "CHANEL",
      "url_attempted": "https://www.chanel.com/mx/musion/careers/",
      "detail": "Access Denied",
      "timestamp": "{HOY}T..."
    }
  ],
  "search_metadata": {
    "brands_attempted": 28,
    "brands_accessible": 2,
    "brands_blocked": 26
  }
}
```

### 2.3 Aggregators

**Pre-requisitos:** Lee `skills/vantage-active-search-weekly/sources/aggregators.md` para los URL templates.

**Protocolo por plataforma:**

Para cada plataforma (OCC, Indeed, Computrabajo, Bumeran):

1. Construí la URL de búsqueda con keywords + location.
2. Intentá acceder.
3. Si accesible:
   - Extraé resultados: title, company, location, apply_url, posted_date.
   - Para cada resultado, validá que apply_url sea canónica.
   - Aplicá exclusiones de Prompt A.
   - Si pasa → agregar a `jobs`.
   - Si falla → agregar a `rejected_jobs`.
4. Si NO accesible (403, Cloudflare, DNS, 404):
   - Registrar en `audit_log`.
   - Intentá URL alternativa si existe.
   - Si ninguna funciona → registrar plataforma como "bloqueada", continuar.

**Output:** escribir `Layer_1/feeds/{HOY}_aggregators_raw.json`.

```json
{
  "source": "aggregators",
  "searched_at": "{HOY}",
  "platforms_attempted": ["OCC", "Indeed", "Computrabajo", "Bumeran"],
  "platforms_accessible": ["Indeed"],
  "platforms_blocked": ["OCC", "Computrabajo", "Bumeran"],
  "jobs": [...],
  "rejected_jobs": [...],
  "not_evaluated": {...},
  "audit_log": [
    {
      "type": "HTTP",
      "platform": "OCC",
      "detail": "403 Forbidden",
      "url_attempted": "https://www.occ.com.mx/empleos/?q=...",
      "timestamp": "{HOY}T..."
    }
  ],
  "search_metadata": {
    "platforms_attempted": 4,
    "platforms_accessible": 1,
    "platforms_blocked": 3
  }
}
```

---

## 3. Normalización (después de todas las búsquedas)

Una vez que los 3 JSONs crudos están escritos, ejecutá:

```bash
python skills/vantage-active-search-weekly/normalize_source_json.py \
  --source linkedin \
  --input Layer_1/feeds/{HOY}_linkedin_raw.json \
  --output Layer_1/feeds/{HOY}_linkedin.json
```

```bash
python skills/vantage-active-search-weekly/normalize_source_json.py \
  --source career_sites \
  --input Layer_1/feeds/{HOY}_career_sites_raw.json \
  --output Layer_1/feeds/{HOY}_career_sites.json
```

```bash
python skills/vantage-active-search-weekly/normalize_source_json.py \
  --source aggregators \
  --input Layer_1/feeds/{HOY}_aggregators_raw.json \
  --output Layer_1/feeds/{HOY}_aggregators.json
```

Estos son los JSONs normalizados que se pasan al consolidador (L0).

---

## 4. Reporte final

Al finalizar, reportá:

```
## Búsqueda Activa Semanal — {HOY}

### LinkedIn
- Candidatos: X
- Rechazados: Y
- No evaluados: Z
- Archivo: Layer_1/feeds/{HOY}_linkedin.json

### Career Sites
- Candidatos: X
- Rechazados: Y
- No evaluados: Z
- Archivo: Layer_1/feeds/{HOY}_career_sites.json

### Aggregators
- Candidatos: X
- Rechazados: Y
- No evaluados: Z
- Archivo: Layer_1/feeds/{HOY}_aggregators.json

### Errores encontrados
- [lista de errores con tipo, plataforma, detail]

### Notas
- [observaciones relevantes — ej: "OC M y Computrabajo seguían con 403", "Bumeran devolvió 404 en todas las URL"]
```

---

## 5. Reglas de pragmatismo (no violar)

- **No reintentes infinitamente.** Si una fuente falla, registra y continuá.
- **No inventes resultados.** Si no podés acceder a una página, no crees vacancies.
- **No skips.** No saltés fuentes sin intentarlas primero.
- **No paralelices sin necesidad.** Ejecutá en secuencia: LinkedIn → Career Sites → Aggregators.
- **No ignores exclusiones.** Aplicá Prompt A estrictamente sobre cada vacancy.
- **No sobre-escribas.** Si un job ya existe en la búsqueda actual, dedupé por job_id.
