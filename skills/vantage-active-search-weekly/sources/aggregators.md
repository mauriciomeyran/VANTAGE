# Aggregators — Protocolo de Búsqueda

## Fuentes Aprobadas
- OCC (occ.com.mx)
- Indeed (mx.indeed.com)
- Computrabajo (computrabajo.com.mx)
- Bumeran (bumeran.com.mx)

## Fuentes No Aprovadas (prohibidas)
- LinkedIn (pertenece al L1 separado)
- Career Pages / ATS (pertenecen al L1 separado)
- Cualquier agregador no listado arriba

## URL de Búsqueda por Plataforma

### OCC
- URL template: `https://www.occ.com.mx/empleos/?q={keywords}&l={location}`
- Parámetros:
  - `q`: keywords codificadas (ej: "Visual+Merchandising+OR+Brand+Experience")
  - `l`: location codificada (ej: "Mexico+City%2C+Mexico")
- Observaciones 2026-09-05:
  - Regresa HTTP 403 Forbidden en búsqueda.
  - Verificar si hay URLs alternativas (ej: `/empleos/empresas/`, `/empleos/categoria/...`).
  - Si todas las URLs fallan con 403, registrar en audit_log y detener búsqueda en OCC.

### Indeed
- URL template: `https://mx.indeed.com/jobs?q={keywords}&l={location}`
- Parámetros:
  - `q`: keywords codificadas
  - `l`: location codificada
- Observaciones 2026-09-05:
  - Regresa Cloudflare block con "Solicitud bloqueada" + Ray ID.
  - IP 189.217.111.56 aparece bloqueada explícitamente.
  - Si hay Cloudflare block, registrar y detener búsqueda en Indeed (no intentar bypass).

### Computrabajo
- URL template: `https://www.computrabajo.com.mx/empleos/?q={keywords}&l={location}`
- Parámetros:
  - `q`: keywords codificadas
  - `l`: location codificada
- URLs alternativas para probar si la búsqueda falla:
  - `https://www.computrabajo.com.mx/empleos-licencias-y-registros/`
  - `https://www.computrabajo.com.mx/empleos-marketing-y-ventas/`
- Observaciones 2026-09-05:
  - Regresa HTTP 403 Forbidden en búsqueda y en URLs alternativas.
  - Si todas fallan con 403, registrar y detener búsqueda en Computrabajo.

### Bumeran
- URL template: `https://www.bumeran.com.mx/empleos?q={keywords}&l={location}`
- URL alternativas para probar:
  - `https://www.bumeran.com.mx/empleos-en-mexico-ciudad`
  - `https://www.bumeran.com.mx/buscador-empleos?q={keywords}`
  - `https://www.bumeran.com.mx/empleos-en-mexico/?q={keywords}`
  - `https://www.bumeran.com.mx/empleos-en-mexico-ciudad-de-mexico`
- Observaciones 2026-09-05:
  - Todas las URL de búsqueda devuelven "No encontramos la página que buscas" (404 equiv.).
  - Posiblemente el sitio migró o sufrío cambio de estructura.
  - Si todas las URL devuelven 404, registrar en audit_log como `"type": "Redirect"` con note "sitio posiblemente migrado" y detener búsqueda en Bumeran.

## Keywords para Búsqueda en Aggregators

### Keywords Base (siempre incluir)
- Visual Merchandising
- VM Coordinator
- VM Manager
- Visual Merchandiser

### Keywords Adicionales (siempre incluir)
- Brand Experience
- Retail Experience
- Store Design
- Exhibición Visual
- Coordinador de Experiencias

### Keywords de Nivel/Seniority (opcional)
- "Líder" + "Visual Merchandising"
- "Supervisor" + "Visual Merchandising"
- "Coordinador" + "Visual Merchandising"

### Location
- "Mexico City" o "Ciudad de México" o "CDMX"
- "Área metropolitana de Ciudad de México"
- No usar "México" sin más contexto (demasiado amplio, incluye todo el país).

### Recencia
- Preferente: últimos 14 días (Indeed: `fromage=14`, OCC/Computrabajo/Bumeran: parámetro de recencia si existe).
- Aceptable: últimos 21 días si el fit es fuerte.
- No usar recencia mayor a 21 días.

## Extracción de Resultados

### Campos a Extraer por Resultado
- title (texto del listing)
- company
- location
- apply_url (URL de la detail page del listing)
- posted_date (fecha de publicación)
- job_id (si está disponible, ej: ID del job en la plataforma)

### Limpieza de Title
- Remover tags HTML, emojis, y caracteres especiales.
- Title debe ser el texto limpio del puesto (ej: "Visual Merchandiser", no "Visual Merchandiser · Empresa XYZ").

### Validar Apply URL
- La apply_url debe ser una URL canónica del job (no una query URL genérica del agregador).
- Si la apply_url es una query URL sin job_id identificable → marcar como "apply_url genérica" y registrar en notas.

## Exclusiones a Aplicar

### Título
Evaluar el título completo. Si contiene cualquier término excluido → rechazar.
- Términos excluidos: Store Manager, Director, VP, C-Level, Assistant, Asistente, Auxiliar, Jr., Internship, Intern, Entry Level, Pasantía, Sales Advisor, Vendedor, Asesor Comercial.

### Compañía
Si la compañía está en la lista bloqueada → rechazar sin evaluar título.
Lista bloqueada: L'Oréal, Levi's, Dockers, El Palacio de Hierro.

### Location
- Aceptar: resultados en Ciudad de México / Área Metropolitana.
- Rechazar: resultados fuera de CDMX, remoto fuera de México, EdoMex que no sea CDMX proper.

## Registro de Audit

### Plataforma Bloqueada
```json
{
  "type": "Cloudflare | DNS | HTTP",
  "platform": "OCC | Indeed | Computrabajo | Bumeran",
  "url_attempted": "URL de búsqueda",
  "reason": "403 Forbidden / Cloudflare block / DNS failure / 404",
  "timestamp": "2026-09-05T..."
}
```

### Resultado No Evaluado
```json
{
  "type": "not_evaluated",
  "platform": "OCC | Indeed | Computrabajo | Bumeran",
  "job_id": "...",
  "title": "...",
  "reason": "No se pudo extraer apply_url canónica / URL bloqueada / etc.",
  "timestamp": "2026-09-05T..."
}
```

## KPIs para search_summary

| Campo | Descripción |
|---|---|
| `candidates_count` | Número de jobs que pasaron todas las exclusiones. |
| `rejected_count` | Número de jobs rechazados por título o compañía bloqueada. |
| `not_evaluated_count` | Número de jobs que no se pudieron validar. |
| `total_results_count` | Número total de resultados en la búsqueda. |
| `platform_accessible` | `true` si se pudo acceder al menos a una plataforma. |
| `platforms_blocked` | Lista de plataformas que devolvieron error. |

## KPIs para search_metadata

| Campo | Descripción |
|---|---|
| `searches_conducted` | Lista de plataformas en las que se ejecutó búsqueda. |
| `recency_days` | Rango de recencia usado (14 o 21). |
| `keywords_used` | Lista de keywords usadas en la búsqueda. |

## Notas de Implementación (2026-09-05)

- Todas las cuatro plataformas (OCC, Indeed, Computrabajo, Bumeran) devolvieron errores en la última búsqueda (2026-09-05).
- Esto puede ser un problema de IP (189.217.111.56 aparece bloqueada en Indeed) o de plataforma (OCC/Computrabajo 403, Bumeran 404).
- Si los errores persisten, considerar usar un proxy residencial o diferentes shells para cada plataforma.
- Si solo una plataforma funciona, registrar las otras como "platforms_blocked" y continuar con la que funciona.
