# Career Sites — Protocolo de Búsqueda

## Scope
Búsqueda en páginas oficiales de carrera y ATS de marcas objetivo en los sectores aceptados.

## Sectores Aceptados
- Luxury
- Premium
- Fashion
- Beauty
- Cosmetics
- Fragrances
- Jewelry
- Sportswear
- Experiential Retail

## Marcas Objetivo (semanal)

### Grupo A — Luxury / Premium / Fashion
- CHANEL
- Dior
- Gucci
- Louis Vuitton
- Hermès
- Burberry
- Valentino
- Versace
- Armani
- Prada
- Balenciaga
- Bottega Veneta
- Givenchy
- Fendi
- Celine
- Saint Laurent
- Tod's
- Brunello Cucinelli
- Armani Exchange

### Grupo B — Jewelry / Watches / Accessories
- Cartier
- Tiffany & Co.
- Bulgari
- Van Cleef & Arpels
- Chaumet
- Chopard
- Buccellati
- Tag Heuer
- Montblanc
- Swatch
- Tous
- Pandora
- Fossil
- Movado

### Grupo C — Beauty / Cosmetics / Fragrances
- Sephora
- Estée Lauder
- Coty
- Shiseido
- Revlon
- Kiehl's
- Clinique
- M·A·C
- Giorgio Armani Beauty
- Tom Ford Beauty
- Natura
- The Body Shop
- Yves Rocher
- Lancôme
- Hugo Boss Beauty

### Grupo D — Sportswear
- Nike
- Adidas
- Puma
- Reebok
- Under Armour
- New Balance
- Columbia
- The North Face
- Patagonia
- Skechers
- Fila

### Grupo E — Mexican Department Stores / Experiential Retail
- El Puerto de Liverpool
- Sears
- Coppel
- Aurrerá
- Soriana
- La Comer
- Liverpool (si tiene portal accesible)

## Marcas Bloqueadas (no buscar, no registrar)
- L'Oréal (todas las divisiones)
- Levi's
- Dockers
- El Palacio de Hierro

## Protocolo por Marca

### 1. Obtener URL de Career Page
- URL primaria: página oficial de carrera de la marca (ej: `marcaweb.com/careers`, `marcaweb.com/mx/careers`, `careers.marcaweb.com`).
- URL alternativa: si la marca usa ATS (Greenhouse, Lever, Workday, SmartRecruiters, Taleo, Ashby), la URL del ATS (ej: `marca.greenhouse.io`, `apply.marca.com`).
- URL de fallback: LinkedIn Jobs para la marca (si no hay career page accesible).

### 2. Validar Accesibilidad
- Navegar a la URL.
- Esperar carga.
- Verificar que no sea:
  - Cloudflare/WAF block ("Access Denied", "Verificación de seguridad").
  - DNS failure ("No se puede acceder a este sitio", "DNS_PROBE_FINISHED_NXDOMAIN").
  - HTTP 403, 404, 405, 500.
- Si la URL es inaccesible:
  - Registrar en `audit_log` (`type: "Cloudflare"`, `"DNS"`, `"HTTP"`).
  - Probar URL alternativa si existe.
  - Si todas las URLs son inaccesibles, dejar la marca como "no accesible" y continuar con la siguiente.

### 3. Extraer Listings
- Buscar en la página de carrera los listings disponibles.
- Si la página tiene search/filter: usar keywords "Visual Merchandising", "Brand Experience", "Retail Experience", "Store Design".
- Extraer para cada listing:
  - title (texto del listing)
  - location (si está disponible)
  - posted_date (si está disponible)
  - apply_url (URL de la detail page del listing)

### 4. Visitar Detail Page de Cada Listing
- Navegar a la apply_url del listing.
- Validar que la detail page carga sin errores (login wall, Cloudflare, HTTP error).
- Extraer:
  - title completo
  - company
  - location completa
  - posted_date
  - job_id (si está disponible, ej: ATS reference ID)
  - snippet de descripción (primer párrafo del JD)
  - industry signals (si el JD menciona los sectores aceptados)

### 5. Aplicar Exclusiones
- Título: verificar que no contiene términos excluidos (Store Manager, Director, VP, C-Level, Assistant, Asistente, Auxiliar, Jr., Internship, Intern, Entry Level, Pasantía, Sales Advisor, Vendedor, Asesor Comercial).
- Compañía: verificar que no está en la lista bloqueada.
- Location: verificar que es CDMX o área metropolitana (no EdoMex, no remoto fuera de México).

### 6. Registrar Resultado
- Si el listing pasa todas las exclusiones y la detail page es accesible → agregar a `jobs`.
- Si el listing falla alguna exclusión → agregar a `rejected_jobs` con `rejection_reason`.
- Si la detail page no se puede acceder → agregar a `not_evaluated.items`.

## Registro de Audit — Marcas No Accesibles

```json
{
  "type": "Cloudflare | DNS | HTTP",
  "platform": "Career Sites",
  "brand": "Nombre de la marca",
  "url_attempted": "URL de career page o ATS",
  "reason": "Access Denied / DNS_PROBE_FINISHED_NXDOMAIN / HTTP 403 / etc.",
  "timestamp": "2026-09-05T..."
}
```

## Observaciones (2026-09-05)
- La mayoría de las páginas de carrera de luxury/fashion beauty en México están detrás de Cloudflare/WAF cuando se accede desde IP mexicana (189.217.111.56). Esto afecta especialmente a CHANEL, Zara, Liverpool, Mango, Bershka, Oysho, Tiffany, Bulgari, Cartier, Celine, Givenchy, Versace, Bottega Veneta, Balenciaga, Clinique, The North Face, Gucci, Fendi, entre otras.
- Las URLs de ATS como `gucci.greenhouse.io`, `dior.greenhouse.io`, `louisvuitton.greenhouse.io`, `prada.greenhouse.io`, `careers.valentino.com` no resuelven DNS (NXDOMAIN).
- Marcas accesibles en la última búsqueda: Nike (careers.nike.com), M·A·C (maccosmetics.com/careers — pero es US-centric).
- El acceso a las career pages de marcas mexicanas (Liverpool, Sears, Coppel, Aurrerá, Soriana, El Palacio de Hierro) también está bloqueado por Cloudflare/WAF.

## Notas para Futuras Búsquedas
- Si el acceso a las career pages sigue bloqueado, considerar el uso de un proxy/residencial para acceder a las páginas bloqueadas.
- Alternativamente, monitorizar los LinkedIn Jobs de las marcas objetivo (LinkedIn permite ver los jobs publicados por las marcas incluso si el career page no es accesible).
