# VANTAGE - Búsqueda de metadatos BitTorrent en lenguaje natural

Sistema modular en Python 3.11+ que convierte una petición en lenguaje natural en
una búsqueda agregada sobre varios índices públicos de BitTorrent y devuelve el
resultado más estable (más sembradores) o los N mejores.

```
lenguaje natural -> [ai_agent + Ollama] -> query + categoria
                                              |
                              [engines: 5 motores en paralelo]
                                              |
                        dedup por info-hash + filtro de relevancia
                                              |
                                  resultado óptimo + diagnóstico
```

## Ubicación

Este directorio (`~/Documents/03 Projects/VANTAGE/Bittorrent_Search`) es
autocontenido: módulos, documentación, pruebas, scripts de verificación y su
propio `venv`.

```bash
cd ~/Documents/03\ Projects/VANTAGE/Bittorrent_Search
source venv/bin/activate
```

Vive en su propia carpeta **dentro** del repo VANTAGE (no en la raíz), para no mezclarlo con el
resto del sistema (Layer_1, Dashboard, handoffs generales). El `handoffs/` de esta
carpeta guarda solo los handoffs de este subsistema.

## Estado verificado (2026-10-14, red residencial MX)

| Motor | Endpoint verificado | Resultado real |
| --- | --- | --- |
| YTS (películas) | `https://yts.gg/api/v2/list_movies.json` | 200 OK — 11 items para "Oppenheimer 2023". `yts.mx` **no resuelve DNS** |
| LimeTorrents (general) | `https://www.limetorrents.lol` → `.fun` | 200 OK — 38 items |
| Nyaa (anime/asiático) | `https://nyaa.si` | 200 OK — 0 items para "Oppenheimer" (no es su catálogo) |
| EZTV (series) | `https://eztv.re` → `eztvx.to` | 200 OK — 79 items para "Severance" (con IMDb `tt11280740`) |
| MagnetDL (general) | `https://www.magnetdl.com` | **Sin respuesta**: read timeout en `.com`, DNS sin resolver en `.mx` (un HTTP 522 apareció en una comprobación previa). El motor sigue activo y se degrada de forma visible |

Resultados de la verificación en vivo (`scripts/verificar_engines.py`):

- **Películas** — "Oppenheimer 2023" / `movies` → 49 items brutos, **47 únicos**,
  mejor resultado *Oppenheimer (2023) NEW ENG 1080p HQ-CAM x264 AAC - HushRips*
  con 1276 sembradores.
- **Series** — "Severance" / `tv` → 119 items brutos, **98 únicos**, mejor resultado
  *Severance S02E10 1080p WEB H264-SuccessfulCrab* con 3845 sembradores.

El informe `VERIFICACION_ENGINES.md` contiene la corrida de películas con la salud de
cada mirror; para la de series: `python3 scripts/verificar_engines.py -q Severance -c tv`.

## Arquitectura

| Archivo | Responsabilidad |
| --- | --- |
| `ai_agent.py` | Extracción de `{"query", "categoria"}` vía Ollama con contrato JSON estricto y recuperación por capas |
| `texto.py` | Normalización de texto/categorías, saneado de la consulta, detección de IMDb id y años, coincidencia por palabra |
| `resolver.py` | Título → IMDb id (`v2.sg.media-imdb.com`), con preferencia de tipo (serie vs película) |
| `engines.py` | Los 5 motores + `AgregadorTorrents` (paralelo, dedup, relevancia, diagnóstico) |
| `scraper.py` | Shim de compatibilidad con la firma histórica `buscar_torrents` (delega en Nyaa) |
| `main.py` | CLI: extracción → búsqueda → salida + códigos de salida |
| `salud.py` | Verificación del backend (intérprete, dependencias, Ollama, modelo) |
| `salud_motores.py` | Historial persistente de fallos por motor y política de reintentos |
| `scripts/vantage-search` | Punto de entrada estable para clientes externos |
| `scripts/verificar_engines.py` | Verificación en vivo de mirrors y motores, informe markdown |
| `tests/vantage/` | 185 pruebas offline con fixtures HTML/JSON reales |

## Instalación

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt        # ejecución
pip install -r requirements-dev.txt    # pruebas (pytest)
```

Requisitos: Ollama en `http://localhost:11434` y un modelo local
(`ollama pull qwen2.5:7b`).

## Uso

```bash
source venv/bin/activate
python3 main.py "Busca la serie Severance" --verbose -n 2
```

Salida real:

```
Extracción LLM: query='Severance' categoria='tv'
consulta='Severance' categoria=tv min_seeders=5
imdb_id=tt11280740
items: 119 brutos, 98 únicos, 0 descartados por relevancia
[OMITIDO] YTS            no soporta categoria='tv'
[OK]      LimeTorrents   40 resultado(s) (659 ms)
[FALLO]   MagnetDL       ErrorFuenteNoDisponible: ningún mirror respondió: ...
[OK]      EZTV           79 resultado(s), imdb=tt11280740 (1129 ms)
[OK]      Nyaa           0 resultado(s) (426 ms)

Resultado #1:
  Title:    Severance S02E10 1080p WEB H264-SuccessfulCrab
  Magnet:   magnet:?xt=urn:btih:f66008699dbee820082b4de1ce59c560d9d6dd85&dn=...
  Seeders:  3845
  Leechers: 1321
  Size:     5.69 GB
  Source:   LimeTorrents
```

### Opciones

| Opción | Efecto |
| --- | --- |
| `-n, --all N` | Muestra los N mejores resultados (por defecto 1) |
| `-s, --min-seeders N` | Sembradores mínimos (por defecto 5) |
| `-m, --model NAME` | Modelo de Ollama (por defecto `qwen2.5:7b`) |
| `--host URL` | Host de Ollama (por defecto `http://localhost:11434`) |
| `-v, --verbose` | Imprime el diagnóstico por motor |
| `--json` | Salida JSON estable: `consulta`, `resultados`, `mejor` y `diagnostico` (con `consulta_efectiva`, `consulta_original`, `motores`) |
| `--sin-relevancia` | No filtra por coincidencia de título con la consulta |
| `--no-imdb` | No resuelve IMDb por red (desactiva EZTV si no hay id) |
| `--secuencial` | Consulta los motores en serie con pausas |
| `--motores LISTA` | Consulta solo esos motores: `YTS`, `LimeTorrents`, `MagnetDL`, `EZTV`, `Nyaa` (o sus dominios) |
| `--sin-motores LISTA` | No consulta esos motores (override manual de la salud automática) |
| `--salud {auto,off,reset}` | `auto` (por defecto) no vuelve a esperar a un índice degradado; `off` ignora el historial; `reset` lo borra |
| `--debug` | Registro de depuración en stderr |

### Códigos de salida

| Código | Significado |
| --- | --- |
| 0 | Resultado encontrado |
| 2 | Ningún item superó los filtros |
| 3 | Fallo del LLM (conexión o parseo) |
| 4 | Todos los motores fallaron |
| 64 | Argumentos inválidos (uso incorrecto). Antes argparse usaba 2, que aquí significa "sin resultados" |
| 65 | Solo `vantage-search`: backend ausente o intérprete no encontrado (devuelve `{"error": ...}`) |
| 130 | Interrupción por teclado |

## Cliente externo: `scripts/vantage-search`

Para que otros programas (la app de escritorio, Raycast, scripts propios) no dependan de
las rutas internas del `venv`, el proyecto expone un punto de entrada estable:

```bash
scripts/vantage-search "Busca la serie Severance" --json
scripts/vantage-search --doctor          # estado del backend, en JSON
```

- Pasa cualquier opción de `main.py` tal cual (`-n`, `-s`, `--motores`, `--sin-motores`...).
- `--doctor` comprueba intérprete, `main.py`, dependencias, Ollama y modelo descargado, y
  devuelve `{"ok": true|false, "checks": [...]}`. Es lo que usa el botón "Comprobar
  conexión" de la app.
- Si el backend no está (`venv` ausente), imprime en stdout
  `{"error": {"tipo": "interprete_ausente", ...}}` y sale con **65**, para que el cliente
  muestre el motivo sin interpretar texto libre.
- Se puede apuntar a otro intérprete con `VANTAGE_PYTHON=/ruta/python scripts/vantage-search ...`.

La interfaz estable es ese script: cambiar el backend por dentro no obliga a tocar la app.

---

## Salud de los motores: no volver a esperar a un índice caído

Un índice caído cuesta su timeout en **cada** búsqueda. Como el CLI lanza un proceso por
búsqueda, `salud_motores.py` guarda el historial en disco (`.estado_motores.json`) y aplica
esta política:

- **Dos fallos consecutivos** marcan un motor como degradado; cualquier éxito lo limpia.
- Degradado y con el último intento **dentro del TTL** (30 min): no se consulta (coste cero)
  y el diagnóstico lo declara como `[SALTADO]`.
- Degradado y TTL vencido: se reintenta con **timeout reducido** (3 s en vez de 12). Ese
  intento *es* el sondeo: si el índice revivió, vuelve a aportar solo.
- Solo cuentan los fallos **de fuente** (red, HTTP, estructura). Un fallo de resolución de
  IMDb no degrada EZTV: eso es un problema de la consulta, no del índice.

Medido con MagnetDL caído (2026-10-15), siempre con los mismos 47 resultados:

| Búsqueda | Comportamiento | Tiempo |
| --- | --- | --- |
| 1.ª | primer fallo | 33 911 ms |
| 2.ª | segundo fallo → degradado | 13 840 ms |
| 3.ª | **lo salta** | 2 140 ms |
| 4.ª (TTL vencido) | re-sondeo con timeout de 3 s | 4 800 ms |
| 5.ª | el sondeo falló → vuelve a saltarlo | 2 046 ms |
| cualquiera con `--salud off` | ignora el historial | 13 693 ms |

Control desde la CLI:

```bash
python3 main.py "Severance"                  # 'auto' por defecto
python3 main.py "Severance" --salud off      # ignora el historial (útil para comparar)
python3 main.py "Severance" --salud reset    # borra el historial y continúa
python3 scripts/vantage-search --doctor      # muestra la tabla de salud
```

El archivo `.estado_motores.json` es un JSON legible y se escribe de forma atómica; se puede
borrar a mano en cualquier momento. La salud **no** altera los resultados: solo decide
cuánto se espera a un índice que ya falló.

---

## Diagnóstico: por qué una búsqueda queda vacía

El fallo más caro de la versión anterior era invisible: el agregador capturaba
todas las excepciones con `except Exception: pass`, así que un 403, un dominio que
no resuelve o un selector roto se mostraban igual que "no hay resultados".

Ahora cada motor devuelve un estado (`ok`, `omitido`, `resultados`, `error`,
`milisegundos`) y, cuando la búsqueda queda vacía, el reporte se imprime en
`stderr` sin que haya que pedirlo:

```
$ python3 main.py "Zxqwvbn 1999 pelicula inexistente"
No results found matching criteria.
consulta='Zxqwvbn 1999 pelicula inexistente' categoria=movies min_seeders=5
imdb_id=no resuelto
items: 0 brutos, 0 únicos, 0 descartados por relevancia
[OK]      YTS            0 resultado(s) (1203 ms)
[OK]      LimeTorrents   0 resultado(s) (643 ms)
[FALLO]   MagnetDL       ErrorFuenteNoDisponible: ningún mirror respondió: ...
[OMITIDO] EZTV           no soporta categoria='movies'
[OK]      Nyaa           0 resultado(s) (456 ms)
```

Contrato de errores de los motores: `requests.RequestException` para red/HTTP,
`ErrorEstructura` cuando la página responde 200 pero cambió de forma,
`ErrorFuenteNoDisponible` cuando fallan todos los mirrors. Devolver `[]` significa
exactamente "la fuente respondió bien y nada pasó los filtros".

Cuando el LLM arrastra la categoría dentro de la consulta (`"película Oppenheimer"`),
el reporte muestra la consulta efectiva y la original:

```
consulta='Oppenheimer' categoria=movies min_seeders=5 (peticion original='película Oppenheimer')
```

## Motores

### YTS — películas (API JSON)
- Rota mirrors en orden: `yts.gg`, `yts.mx`, `yts.lt`, `yts.am`.
  Un mirror que devuelve HTML con HTTP 200 se descarta mediante un validador de
  JSON, no se confunde con resultados.
- El magnet se construye desde el info-hash que ya entrega la API.
- Categoría: solo `movies`; `all`/`movies` no envían filtro de género.
- Los géneros (`action`, `sci-fi`, ...) se mapean al parámetro `genre`, pero **solo sirven
  para llamadas directas**: el agregador pasa siempre la categoría canónica, que no lleva
  género, así que desde la CLI ese parámetro nunca se envía. Las claves del mapa se
  normalizan (`Sci-Fi` -> `sci fi`), que era el motivo de que ni siquiera en llamada
  directa funcionaran.

### LimeTorrents — generalista (HTML)
- Mirrors: `limetorrents.fun` (verificado) y `limetorrents.lol` (redirige al anterior).
- **La página de búsqueda no publica magnets.** Cada fila trae un enlace
  `itorrents.net/torrent/<hash>.torrent`; de ahí se extrae el info-hash de 40 hex y
  se construye el magnet con trackers. Evita una petición extra por resultado.
- **El mirror ignora la categoría de la URL** (`/search/music/...` devuelve lo
  mismo que `/search/all/...`). Por eso la categoría se filtra en cliente leyendo la
  etiqueta `in <Categoría>` de cada fila. Las filas "in Other" se marcan como
  `otros` y no se cuelan en un filtro concreto; si la etiqueta es ilegible la fila
  se conserva (fallar abierto, nunca ocultar resultados).

### Nyaa — anime/asiático (HTML)
- Índice centrado en anime. Códigos de categoría corregidos: `1_0` es **Anime**;
  el contenido de imagen real es `4_0` (Live Action), `2_0` audio, `3_0` literatura,
  `6_0` software. La versión anterior mapeaba `movies` a `1_0`, que es anime.
- Una página de Nyaa sin resultados no incluye la tabla: se detecta y se trata como
  lista vacía, no como error de estructura.

### EZTV — series (API JSON)
- No acepta búsquedas por texto: exige un `imdb_id` numérico.
- El título se resuelve con `resolver.py` (sugerencias públicas de IMDb) usando
  **preferencia de tipo TV**: sin ella, "Severance" resolvía al film de 2006
  (`tt0464196`) en lugar de a la serie de 2022 (`tt11280740`, la que tiene torrents).
- Si ya escribes `tt11280740` o `11280740`, se usa tal cual sin tocar la red.

### MagnetDL — generalista (HTML)
- Ruta `/<inicial>/<slug>/`, selectores `table.download`, `td.m a`, `td.n a`, `td.s`, `td.l`.
- Verificado sin respuesta (read timeout en `.com`, DNS en `.mx`). No se desactiva: si
  vuelve, funciona;
  mientras tanto aparece como `[FALLO]` en el diagnóstico en lugar de romper la búsqueda.

## Decisiones de diseño

1. **Relevancia por palabra, no por subcadena.** El log original mostraba que
   "Dune" devolvía *"Genshin Impact - The Unfathomable Sand Dunes"*. Una comparación
   por subcadena no lo detecta (`"dune"` está dentro de `"dunes"`). Ahora cada token
   significativo debe coincidir con una palabra del título, con tolerancia para
   compuestos (`"spiderman"` ~ *Spider Man*). Palabras vacías ("movie", "la", "busca")
   y años se descartan de la consulta.
2. **Deduplicación por info-hash conservando la mejor copia.** Cuando dos fuentes
   exponen el mismo release se conserva la de más sembradores, así el magnet
   reportado es el más sano.
3. **Motores en paralelo.** Son hosts distintos, así que no compiten por rate limit;
   en serie la latencia se sumaba (hasta ~15 s solo esperando a MagnetDL). El reporte
   conserva igualmente el orden declarado de motores (`as_completed` no lo garantiza).
4. **Una sola resolución de IMDb.** Se resuelve una vez y sólo si algún motor
   aplicable la exige: una búsqueda de música o juegos no gasta esa petición.
5. **`format="json"` en Ollama** más recuperación por capas (markdown, JSON embebido
   en prosa, comas finales, comillas simples) y normalización de categorías: el LLM
   puede responder "película" y el motor recibe `movies`.
6. **Categorías canónicas.** `movies`, `tv`, `anime`, `music`, `games`,
   `applications`, `books`, `all`. Cualquier valor desconocido cae a `all` en lugar
   de romper la búsqueda.
7. **Consulta saneada antes de buscar.** El LLM devuelve a veces la categoría dentro
   de la consulta (`"película Oppenheimer"`), y enviada literalmente a los índices da
   cero resultados. `texto.limpiar_consulta` quita las palabras de intención/categoría
   y los artículos iniciales; si al limpiar no queda nada significativo devuelve la
   consulta original (para no romper títulos como *The Game*). El reporte muestra
   `consulta=` (la efectiva) y `peticion original=` cuando difieren.
8. **Reintentos acotados por coste.** Cada petición se reintenta **solo** cuando el fallo
   es barato: 429/5xx y errores de conexión (DNS, conexión rechazada). Un **timeout no se
   reintenta** ni un 4xx no reintentable: un índice muerto cuesta su timeout completo en
   cada intento, así que insistir duplicaría el peor caso (12 s -> 24 s) justo lo que
   evita la salud de motores. La pausa del backoff es `PAUSA_REINTENTO`.
9. **No esperar a un índice caído, y no depender de que el cliente lo recuerde.**
   Medido: una búsqueda con todos los motores tardaba **15 s**, y **~12 s de esos eran
   el timeout de MagnetDL** (caído desde el 2026-10-14). Resolverlo solo en el cliente
   tenía dos problemas: los resultados por defecto seguían siendo lentos y, el día que
   el índice reviviera, alguien tendría que acordarse de volver a habilitarlo (y
   reconstruir la app). Por eso la política vive en el backend (`salud_motores.py`):
   degrada tras dos fallos, salta el motor dentro del TTL y lo re-sondea con timeout
   reducido cuando vence. La búsqueda baja a **~2,1 s** con los mismos resultados y se
   auto-cura sin intervención. `--motores`/`--sin-motores` y `--salud` quedan como
   overrides explícitos del usuario.

## Pruebas

185 pruebas offline (sin red): sirven respuestas reales guardadas en
`tests/vantage/fixtures/`.

```bash
source venv/bin/activate
pytest tests/vantage -v
```

Cubren: normalización y relevancia, saneado de la consulta, recuperación de JSON del
LLM, parseo de cada motor, rotación de mirrors, detección de estructura rota, magnet
desde info-hash, deduplicación, filtro de categoría en cliente, resolución de IMDb,
selección de motores (`--motores`/`--sin-motores`), verificación de salud, el wrapper
`vantage-search`, diagnóstico por motor, paridad paralelo/secuencial y los códigos de
salida de la CLI.

## Verificación en vivo

```bash
python3 scripts/verificar_engines.py                                  # informe en pantalla
python3 scripts/verificar_engines.py --query "Severance" -c tv
python3 scripts/verificar_engines.py --salida VERIFICACION_ENGINES.md # informe markdown
```

Comprueba la salud de cada mirror (HTTP, latencia, causa del fallo) y cuántos items
devuelve cada motor. Devuelve 0 si al menos un motor respondió con resultados.

## Limitaciones conocidas

- **MagnetDL** no responde (timeout en `.com`, DNS en `.mx`); su timeout es el peor caso del
  pipeline en paralelo.
- **LimeTorrents** no filtra por categoría en servidor: el filtro es local sobre la
  primera página de resultados.
- **Nyaa** solo sirve bien anime/asiático; para películas occidentales devolverá
  vacío con frecuencia.
- **YTS** es solo películas y **EZTV** solo series; con `--no-imdb` EZTV se degrada
  visiblemente salvo que la consulta incluya un IMDb id.
- El pipeline depende de HTML de terceros: si un índice cambia su marcado, el motor
  afectado responde `ErrorEstructura` (visible en el diagnóstico) en lugar de
  devolver basura.
- **Verificado en vivo (2026-10-15)**: cuando el mirror de LimeTorrents no encuentra
  coincidencias reales para una consulta, devuelve una lista genérica de ~40 filas de
  categorías mezcladas (mayoría «Other»). El filtro de relevancia descarta casi todo,
  pero puede colarse algún título que contenga el término por casualidad. Ejemplo real:
  "Amélie" devolvió como primer resultado *X Art 2013 11 15 Undress Me Amelie*. Mitigación
  disponible hoy: `--sin-motores LimeTorrents` o `--motores` explícito. Una solución fina
  (puntuación de relevancia o lista de categorías) es una decisión de producto pendiente.

## Nota legal

Proyecto con fines educativos y de investigación sobre agregación de metadatos
públicos. Respeta los términos de servicio y los límites de cada índice; el scraper
usa timeouts y no implementa reintentos agresivos.
