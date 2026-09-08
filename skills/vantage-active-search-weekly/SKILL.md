# vantage-active-search-weekly

## Propósito
Ejecutar la búsqueda semanal (lunes) en los tres L1 para Mauricio Meyrán:
- LinkedIn Jobs
- Career Sites (oficiales + ATS)
- Aggregators (OCC, Indeed, Computrabajo, Bumeran)

Aplicar las reglas de inclusión/exclusión de Prompt A al emitir resultados.
Emitir un JSON por fuente, estructurado para el consolidador (L0).

## Trigger
- Semanal: lunes (active recon).
- Manual: cuando se quiere re-buscar una fuente específica sin esperar el ciclo.

## Pre-requisitos
- Browser-use CLI (o navegador con capacidades de navegación/automatización).
- Acceso a las fuentes (LinkedIn, career pages, aggregators) sin bloqueo de IP/Cloudflare.
- Las exclusiones de Prompt A cargadas en contexto (ver Kernel:PROMPT-A).

## Entrada
| Parámetro | Valor | Obligatorio |
|---|---|---|
| `candidate` | Mauricio Meyrán | Sí |
| `today_date` | YYYY-MM-DD | Sí |
| `search_variants` | queries de LinkedIn (ver search_queries.json) | Sí |
| `location` | Mexico City (CDMX) + Área metropolitana | Sí |

## Salida
Un JSON por fuente con schema común:
```json
{
  "prompt_variant": "A-weekly-unified-{source}",
  "prompt_version": "PromptA-v1.0+{source}",
  "generated_at": "YYYY-MM-DDTHH:MM:SSZ",
  "candidate": "Mauricio Meyrán",
  "search_summary": { ... },
  "audit_log": [ ... ],
  "jobs": [ ... ],
  "rejected_jobs": [ ... ],
  "not_evaluated": { ... },
  "search_metadata": { ... }
}
```

Los tres JSON se escriben en `Layer_1/feeds/{YYYY-MM-DD}_{source}.json` y luego se pasan al consolidador (Perplexity, L0).

## Exclusiones (Prompt A — no redefinir, solo referenciar)
- Títulos excluidos: Store Manager, Director, VP, C-Level, Assistant, Asistente, Auxiliar, Jr., Internship, Intern, Entry Level, Pasantía, Sales Advisor, Vendedor, Asesor Comercial.
- Empresas bloqueadas: L'Oréal (todas las divisiones), Levi's, Dockers, El Palacio de Hierro.
- Location: excluir remote fuera de México.
- Título evaluado con string completo (ej: "Visual Merchandising Jr. Coordinator" → reject por "Jr.").

## Sources

### 1. LinkedIn Jobs
- Búsqueda con keywords + location + geoId + f_TPR (recencia: ≤14 días preferido, ≤21 días aceptable si fit fuerte).
- URL base: `https://www.linkedin.com/jobs/search/`
- Parámetros: `keywords`, `location`, `geoId`, `f_TPR`, `f_E`.
- Página 1: extraer todos los `a[href*="/jobs/view/"]`, dedupe por job_id.
- Para cada vacante: visitar detail page → extraer company, location, posted date.
- Validar: la detail page carga sin login wall / Cloudflare block.
- Si hay 429 o login wall: registrar en `audit_log`, no fabricar.

#### Variantes de búsqueda (search_queries.json)
Ver `search_queries.json` para las 3 variantes de búsqueda de LinkedIn.

#### Reglas de validación de LinkedIn
- Truncar el title al texto antes del primer `|` o `\n` (LinkedIn suelta el título completo + ubicación + empresa en el mismo `textContent` del `a`).
- Dedupe por `job_id` extraído del href (`/jobs/view/[slug]-[ID]`).
- Location: confirmar que dice "Ciudad de México", "Área metropolitana de Ciudad de México", o colonias de CDMX. Estados cercanos (EdoMex) que no sean CDMX proper → rechazar o marcar como dudoso.

### 2. Career Sites
- Target: page oficial de carrera de cada marca relevante en los sectores aceptados.
- Sectores: Luxury, Premium, Fashion, Beauty, Cosmetics, Fragrances, Jewelry, Sportswear, Experiential Retail.
- Marcas relevantes: ver `sources/career_sites.md`.
- Protocolo por marca: navegar a URL de carrera → extraer listings → para cada listing, visitar detail page.
- Si career page está detrás de Cloudflare/WAF/DNS fail/403/404: registrar en `audit_log`, no fabricar resultados.
- ATS: Greenhouse, Lever, Workday, SmartRecruiters, Taleo, Ashby. Cada uno es infraestructura — no hay listings públicos en el homepage, solo las instances específicas de cada marca.
- Marcas bloqueadas (L'Oréal, Levi's, Dockers, El Palacio de Hierro): no buscar, no registrar resultados.

### 3. Aggregators
- Fuentes: OCC (occ.com.mx), Indeed (mx.indeed.com), Computrabajo (computrabajo.com.mx), Bumeran (bumeran.com.mx).
- Búsqueda con keywords + location.
- Para cada resultado: extraer title, company, location, apply_url, posted_date.
- Validar: que la URL de aplicación sea canónica (no sea query URL genérica de agregador sin job_id).
- Si agregador bloquea (403/Cloudflare): registrar en `audit_log`, no fabricar.

## Marcas objetivo (semanal — revisar si hay cambios)
- Ver `sources/career_sites.md` para la lista completa por sector (Luxury, Jewelry, Beauty, Sportswear, Mexican Retail).

## Errores comunes y cómo registrarlos

| Situación | Acción |
|---|---|
| Cloudflare / WAF block en career page | `audit_log.append({type: "Cloudflare", site: URL, ray_id: ...})`. No intentar bypass. |
| DNS falla en subdomain de ATS | `audit_log.append({type: "DNS", site: URL})`. No intentar con variants adivinadas infinitamente. |
| 403 Forbidden en agregador | `audit_log.append({type: "HTTP", platform: "OCC", code: 403})`. Registrar y pasar al siguiente. |
| LinkedIn 429 rate limiting | `audit_log.append({type: "HTTP", code: 429})`. Pausar, registrar, reintentar con pace o dejar como no verificado. |
| LinkedIn login wall | `audit_log.append({type: "Filled", platform: "LinkedIn"})`. Los jobs que no se pudieron validar van a `not_evaluated`. |
| Bumeran devuelve 404 en todas las URL de búsqueda | `audit_log.append({type: "Redirect", platform: "Bumeran", note: "sitio posiblemente migrado"})`. No fabricar. |

## Lo que NO hace este skill
- No consolida los resultados de los tres L1 (eso es L0/Perplexity).
- No calcula Score, Gate_Decision, Class B (eso es Python/layer_1_run.py).
- No hace fetch de JD completo más allá de lo necesario para validar (extraer company/location/date es suficiente para el JSON de fuente).
- No evalúa fit estratégico de cada vacante (eso es humano, KERNEL:OWNERSHIP-001).
- No toca el Tracker de Notion (eso es feed_processor.py + layer_1_run.py).
- No reescribe exclusiones de Prompt A (las hereda, no las modifica).

## Flujo de ejecución semanal
```
1. Bootstrap — cargar Prompt A (exclusiones, perfil, seniorities aceptados).
2. LinkedIn — ejecutar las 3 variantes de búsqueda, extraer listings, validar detail pages.
3. Career Sites — recorrer marcas objetivo, extraer listings, validar detail pages.
4. Aggregators — ejecutar búsqueda en OCC/Indeed/Computrabajo/Bumeran.
5. Para cada fuente:
   - Aplicar exclusiones Prompt A.
   - Emitir JSON con schema canónico.
   - Escribir en Layer_1/feeds/{YYYY-MM-DD}_{source}.json.
   - (Opcional) Normalizar con normalize_source_json.py.
6. Si alguna fuente falla completamente (todos los sites bloqueados):
   - No fabricar resultados.
   - Dejar el JSON con jobs=[], rejected_jobs=[], audit_log con la falla.
```

## Estado del skill
- [x] normalize_source_json.py — script de normalización de JSON de fuente.
- [x] SKILL.md completo con el contrato.
- [x] search_queries.json con las 3 variantes de LinkedIn.
- [x] sources/linkedin.md con protocolo de búsqueda + validación.
- [x] sources/career_sites.md con marcas objetivo + protocolo por marca.
- [x] sources/aggregators.md con protocolo de cada plataforma.
- [x] orchestrator_prompt.md — prompt ejecutable (separado del skill, versión simplificada para ejecución directa).
- [ ] triggers.json actualizado si existe el manifiesto.

## Prompt Ejecutable (separado del skill)

El skill define el protocolo documentado (este archivo). Para ejecutar la búsqueda, usar el **prompt ejecutable** independiente:

```
skills/vantage-active-search-weekly/orchestrator_prompt.md
```

**Cómo invocarlo:**

1. Leé el prompt: `read_file(path="skills/vantage-active-search-weekly/orchestrator_prompt.md")`
2. Ejecutá lo que dice el prompt en una sesión nueva (o la misma).
3. El prompt es auto-contenido y no requiere contexto externo — solo browser-use funcional.

**Por qué están separados:**

- El **skill** (SKILL.md) es la documentación del protocolo: qué buscar, qué excluir, qué registrar, qué NO hace.
- El **prompt ejecutable** (orchestrator_prompt.md) es la instrucción directa para el agente que ejecuta la búsqueda.
- Están separados para que el skill sirva como referencia documental y el prompt pueda mejorarse/ajustarse sin tocar el skill.

**Si el prompt no funciona como esperado:**

- Revisá que el agente que lo ejecuta tiene browser-use funcional.
- Chequeá que LinkedIn esté accesible en el momento (puede estar indisponible intermitentemente).
- Chequeá que las career pages no estén bloqueadas por Cloudflare desde la IP de la sesión.

## Related Skills
- `vantage-import-consolidated-feed` — ingesta del JSON consolidado en Notion (L1+L2 → Tracker).
