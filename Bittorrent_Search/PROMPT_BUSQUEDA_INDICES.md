# Prompt para Búsqueda y Conexión con Índices Públicos de Torrents

> **Estado (2026-10-14): esta investigación ya se ejecutó.** Índices que responden
> hoy: YTS (`yts.gg`), LimeTorrents (`limetorrents.fun`), Nyaa (`nyaa.si`) y EZTV
> (`eztv.re`). MagnetDL está caído (HTTP 522). 1337x devolvía 403 y TorrentGalaxy ya
> no resuelve, así que quedaron descartados. El detalle con latencias y motivos está
> en `VERIFICACION_ENGINES.md`, y la implementación final en `engines.py`. Este
> documento se conserva como el prompt de investigación original.

## Objetivo
Encontrar e implementar integración con índices públicos de torrents accesibles en occidente que permitan scraping sin bloqueos excesivos.

## Prompt de Investigación

```
Tu tarea es encontrar índices públicos de torrents accesibles desde occidente que permitan scraping. Sigue este proceso sistemático:

### Paso 1: Identificación de Índices
Busca y documenta índices públicos de torrents que cumplan con:
- Accesibles sin VPN desde Europa/América
- Permiten peticiones HTTP/HTTPS estándar
- No requieren login para búsquedas básicas
- Tienen contenido variado (películas, series, música, software)
- Indexan enlaces magnet (no solo .torrent)

Índices conocidos a investigar:
- LimeTorrents (y sus mirrors)
- TorrentGalaxy
- YTS (YIFY)
- EZTV
- Zooqle
- Demonoid (si está activo)
- BTDB
- MagnetDL

### Paso 2: Evaluación de Accesibilidad
Para cada índice identificado, verifica:
1. **Resolución DNS:** ¿El dominio resuelve correctamente?
2. **Estado HTTP:** ¿Responde con 200 OK?
3. **Bloqueo de User-Agent:** ¿Bloquea requests con User-Agent genérico?
4. **Bloqueo de Cloudflare:** ¿Tiene protecciones anti-bot?
5. **Rate limiting:** ¿Permite múltiples requests sin bloqueo?

### Paso 3: Análisis de Estructura HTML
Para índices accesibles, analiza:
1. **URL de búsqueda:** Patrón de URL para búsquedas (query params, path structure)
2. **Tabla de resultados:** Selector CSS para contenedor de resultados
3. **Campos por item:**
   - Título (selector CSS)
   - Enlace magnet (selector CSS)
   - Seeders (selector CSS)
   - Leechers (selector CSS)
   - Tamaño (opcional)
4. **Paginación:** ¿Cómo navegar a página siguiente?
5. **Filtros de categoría:** ¿Soporta filtrado por categoría en URL?

### Paso 4: Implementación de Scraper
Basado en el análisis, proporciona:
1. **URL base y parámetros de búsqueda**
2. **Headers necesarios** (User-Agent, cookies, etc.)
3. **Selectores CSS/BeautifulSoup** para cada campo
4. **Lógica de extracción** completa
5. **Manejo de errores** específico para este índice

### Paso 5: Validación
Proporciona código de prueba que:
1. Realice una búsqueda de ejemplo
2. Extraiga al menos 5 resultados
3. Verifique que los enlaces magnet son válidos
4. Confirme que seeders/leechers son números correctos

## Entregable Esperado

Para cada índice exitoso, proporciona:

```python
# 1. Configuración
BASE_URL = "..."
USER_AGENT = "..."
HEADERS = {...}

# 2. Función de búsqueda
def buscar_torrents(query: str, categoria: Optional[str] = None, min_seeders: int = 5) -> List[Dict]:
    # Implementación completa con selectores específicos
    pass

# 3. Mapeo de categorías
CATEGORY_MAPPING = {
    "movies": "...",
    "tv": "...",
    # etc.
}

# 4. Notas específicas
NOTES = """
- Protecciones anti-bot: Sí/No
- Rate limit: X requests/min
- Bloqueo geográfico: Sí/No
- Estabilidad: Alta/Media/Baja
"""
```

## Estrategias de Fallback

Propón alternativas para cuando un índice falla:
1. Lista de mirrors/dominios alternativos
2. Índices secundarios como backup
3. Lógica de rotación entre índices
4. Detección automática de bloqueos

## Consideraciones Éticas y Legales

- Solo indexar contenido público
- No violar términos de servicio del índice
- Respetar rate limits
- No implementar scraping agresivo
- Considerar el impacto en los servidores del índice
```

## Prompt Simplificado para Ejecución Inmediata

```
Busca índices públicos de torrents accesibles desde occidente. Para cada uno encontrado:

1. Verifica si responde a requests HTTP con headers estándar
2. Analiza la estructura HTML de resultados de búsqueda
3. Proporciona selectores CSS para: título, magnet, seeders, leechers
4. Escribe un scraper en Python usando requests + BeautifulSoup
5. Prueba con una búsqueda real y muestra los resultados

Prioriza índices con:
- Sin protección Cloudflare
- Sin CAPTCHA
- Sin login obligatorio
- Disponibilidad de enlaces magnet
```

## Checklist de Validación

Para cada índice candidato:
- [ ] DNS resuelve
- [ ] HTTP 200 OK
- [ ] No requiere login
- [ ] Tiene enlaces magnet
- [ ] Estructura HTML parseable
- [ ] Seeders/leechers visibles
- [ ] Permite búsqueda por query
- [ ] No bloquea después de 10 requests
- [ ] Tiene contenido occidental (películas/series en inglés/español)

## Herramientas Sugeridas

Para investigación:
- `curl -I <url>` - Verificar headers HTTP
- `curl -A "Mozilla/5.0..." <url>` - Test con User-Agent
- Chrome DevTools - Inspect element para selectores
- Postman - Test requests con diferentes headers
- BeautifulSoup - Parsing HTML en Python

## Ejemplo de Output Esperado

```python
# Índice: EjemploTorrent
BASE_URL = "https://exampletorrent.com"

def buscar_torrents(query: str, categoria: Optional[str] = None, min_seeders: int = 5) -> List[Dict]:
    headers = {"User-Agent": "Mozilla/5.0..."}
    params = {"q": query, "sort": "seeders"}
    response = requests.get(f"{BASE_URL}/search", params=params, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    for row in soup.select("table.torrent-list tr:not(:first-child)"):
        title = row.select_one("td.name a").text.strip()
        magnet = row.select_one("td.magnet a")["href"]
        seeders = int(row.select_one("td.seeders").text)
        leechers = int(row.select_one("td.leechers").text)

        if seeders >= min_seeders:
            results.append({"title": title, "magnet": magnet, "seeders": seeders, "leechers": leechers})

    return results
```
