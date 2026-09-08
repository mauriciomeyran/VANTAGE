# LinkedIn Jobs — Protocolo de Búsqueda y Validación

## URL Base
`https://www.linkedin.com/jobs/search/`

## Parámetros Permitidos
- `keywords` — string codificado URI
- `location` — string codificado URI
- `geoId` — string (ej: `102/103632511/104`)
- `f_TPR` — string de recencia (ej: `r604800` = últimos 7 días; `r604800` = últimos 14 días)
- `f_E` — filtro de experiencia (opcional)

## URL de Búsqueda Completa
```
https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}&geoId={geoId}&f_TPR={f_TPR}
```

## Variantes de Búsqueda
Ver `search_queries.json` para las 3 variantes predefinidas.

## Extracción de Resultados — Paso 1: Página de Búsqueda

### Selectores
- Elementos de job: `a[href*="/jobs/view/"]`
- job_id: extraído del href con regex `/jobs/view/[^/]*?-(\d+)(?:\?|$)`
- title: `textContent` del `a`, truncado al primer `\n`, `|` o `—`
- company: contenido del `div[class*="company-name"]` o `h4 + div`
- location: contenido del `span[class*="location"]` o `div[class*="loc"]`
- posted date: elemento `time` o `span[class*="post-date"]`

### Deduplication
- Deduplicate por `job_id` (primera ocurrencia).
- Si dos jobs tienen el mismo `job_id`, conservar la primera.

### Limpieza de Title
- Title crudo de LinkedIn: "Título del Rol · Empresa · Ciudad"
- Extraer solo el título: split por `\n`, `|`, `—`, `·`, tomar primera parte.
- Remover `[LOCATION]` o `📍` al final.

## Validación de Detail Page — Paso 2: Visitar Cada Job

### URL de Detail Page
URL directa del `a[href*="/jobs/view/"]` sin modificar.

### Pasos de Validación
1. Navegar a la detail page.
2. Esperar carga (`wait_for_load()`).
3. Verificar que la página no sea:
   - Login wall (contenga "Únete a LinkedIn" o "Iniciar sesión" como formulario visible).
   - Error HTTP (429, 404, 500).
   - Cloudflare challenge ("Verificación de seguridad en curso").
4. Si la página es válida:
   - Extraer company (primera línea de texto que no sea el título).
   - Extraer location (línea después de company).
   - Extraer posted date ("Hace N ..." o fecha en `time`).
   - Extraer snippet de descripción (primer párrafo del JD).
5. Si la página es inválida:
   - Registrar en `audit_log` con `type: "Filled"` o `type: "HTTP"`.
   - Agregar a `not_evaluated.items`.

### Registro de Audit
```json
{
  "type": "Filled",  // o "HTTP", "Cloudflare"
  "platform": "LinkedIn",
  "job_id": "...",
  "detail": "Login wall / Cloudflare / 429",
  "timestamp": "2026-09-05T..."
}
```

## Reglas de Exclusión en LinkedIn

### Título Completo
Evaluar el título completo (no solo la primera palabra). Si contiene cualquier término excluido → rechazar.

Ejemplos:
- "Coordinator Jr." → rechazar (contiene "Jr.")
- "Visual Merchandising Jr. Coordinator" → rechazar (contiene "Jr.")
- "Sr. Visual Merchandiser" → aceptar
- "Assistant Visual Merchandising" → rechazar (contiene "Assistant")
- "Store Manager Regional" → rechazar (contiene "Store Manager")

### Compañía
Si la compañía está en la lista bloqueada → rechazar sin evaluar título.
Lista bloqueada: L'Oréal, Levi's, Dockers, El Palacio de Hierro.

### Location
- Aceptar: "Ciudad de México", "Área metropolitana de Ciudad de México", colonias específicas de CDMX.
- Rechazar: estados de México fuera de CDMX (EdoMex: Naucalpan, Ecatepec, Tlalnepantla, etc.)
- Si la location dice "Remoto", "Remote", "Working from home" → rechazar si no es en México.

## Estado de la Búsqueda

### KPIs para `search_summary`
- `candidates_count`: número de jobs que pasaron todas las exclusiones.
- `rejected_count`: número de jobs rechazados por título o compañía bloqueada.
- `not_evaluated_count`: número de jobs que no se pudieron validar.
- `total_results_count`: número total de resultados en la búsqueda.

### KPIs para `search_metadata`
- `searches_conducted`: lista de variantes ejecutadas.
- `page`: número de página (default 1).
- `recency_days`: rango de recencia (`f_TPR`).

## Notas de Implementación (2026-09-05)
- LinkedIn bloquea detrás de Cloudflare en ciertos patrones de búsqueda. Si la búsqueda falla con Cloudflare, registrar y detener la búsqueda en LinkedIn.
- LinkedIn puede devolver 429 tras varias visitas consecutivas de detail pages. Si se detecta 429, pausar y registrar; los jobs que no se pudieron visitar van a `not_evaluated`.
- LinkedIn puede requerir login para ver detalles de algunos jobs. Si hay login wall, registrar y pasar al siguiente job.
