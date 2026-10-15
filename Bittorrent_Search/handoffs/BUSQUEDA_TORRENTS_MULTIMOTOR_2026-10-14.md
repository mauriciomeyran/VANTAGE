# Handoff — VANTAGE: búsqueda BitTorrent multi-motor (reparación, verificación y pruebas)

**Fecha:** 2026-10-14
**Ámbito:** pipeline de búsqueda en lenguaje natural (`ai_agent`, `engines`, `main`)
**Estado:** completo y verificado contra los índices reales

---

## 1. Punto de partida

La sesión anterior cerró con el scraper funcionando **solo contra Nyaa.si**, un índice
de anime, y con esta nota en `MANUAL_USUARIO.md`: *"para películas occidentales puede
que no encuentre resultados"*. El síntoma que quedó abierto era que cualquier fallo
de red o de selectores se mostraba como `No results found matching criteria.` sin
ninguna explicación, porque el agregador atrapaba todo con `except Exception: pass`.

Diagnóstico verificado contra la red (no supuesto):

| Motor | Estado al retomar | Causa real |
| --- | --- | --- |
| YTS | caído | `yts.mx` no resuelve DNS (mirror vivo: `yts.gg`) |
| LimeTorrents | 200 OK pero 0 items | la página de búsqueda **no publica magnets**: el selector `a[href^='magnet:?']` nunca encontraba nada |
| MagnetDL | caído | HTTP 522, origen Cloudflare sin respuesta |
| EZTV | 200 OK pero inutilizable | exige `imdb_id`; el pipeline solo enviaba texto libre |
| Nyaa | 200 OK | correcto, pero es catálogo de anime |

Además, `engines.py` ya existía pero `README.md` documentaba un `agregador.py` que no
existe, y la búsqueda no filtraba relevancia: `"Dune"` devolvía *"Genshin Impact - The
Unfathomable Sand Dunes"*.

## 2. Cambios

### Módulos nuevos
- **`texto.py`** — normalización (acentos, puntuación), categorías canónicas con alias
  en español/inglés, detección de IMDb id y año, y `coincide_titulo` **por palabra**
  (con tolerancia para compuestos `spiderman` ~ *Spider Man*). La comparación por
  subcadena no detectaba el falso positivo de "Dune"/"Dunes".
- **`resolver.py`** — título → IMDb id vía `v2.sg.media-imdb.com`, con **preferencia de
  tipo**. Sin ella, "Severance" resolvía al film de 2006 (`tt0464196`, sin torrents) en
  vez de a la serie de 2022 (`tt11280740`, 79 items en EZTV).

### `engines.py`
- **YTS**: rotación de mirrors `yts.gg → yts.mx → yts.lt → yts.am` con validador de
  JSON (un 200 con página HTML de error se descarta, no se confunde con resultados).
- **LimeTorrents**: el magnet se construye desde el info-hash del enlace
  `itorrents.net/torrent/<hash>.torrent` de cada fila (sin petición extra). El mirror
  **ignora la categoría de la URL**, así que el filtro de categoría se aplica en
  cliente leyendo la etiqueta `in <Categoría>`; "in Other" ya no es comodín.
- **Nyaa**: códigos de categoría corregidos (`1_0` es Anime; Live Action es `4_0`).
  Página sin resultados ≠ error de estructura.
- **EZTV**: resuelve el IMDb id con preferencia TV; acepta `ttNNNNNNN` o el número.
- **MagnetDL**: se mantiene activo; si el origen vuelve, funciona sin cambios.
- **Saneado de la consulta**: `texto.limpiar_consulta` quita las palabras de
  intención/categoría que el LLM arrastra ("película Oppenheimer" → "Oppenheimer").
  Sin esto la búsqueda literal devolvía cero resultados de forma intermitente según
  la muestra del modelo.
- **Agregador**: ejecución en paralelo (hosts distintos, sin competir por rate limit),
  dedup por info-hash **conservando la copia con más sembradores**, filtro de
  relevancia, y `EstadoMotor`/`ResumenBusqueda` con ok/omitido/resultados/error/ms.
  El reporte conserva el orden declarado de motores aunque la ejecución sea concurrente.
  La resolución de IMDb solo ocurre si un motor **aplicable** la necesita.

### `ai_agent.py`
- `format="json"` en Ollama (con repliegue si el cliente no lo acepta), recuperación por
  capas (markdown, JSON embebido en prosa, comas finales, comillas simples) y
  normalización de la categoría devuelta por el modelo.

### `main.py`
- CLI con `-n/--all`, `-s/--min-seeders`, `-m/--model`, `--host`, `-v/--verbose`,
  `--json`, `--sin-relevancia`, `--no-imdb`, `--secuencial`, `--debug`.
- Códigos de salida: 0 ok, 2 sin resultados, 3 fallo LLM, 4 todos los motores caídos.
- Cuando no hay resultados, el diagnóstico por motor se imprime en `stderr`.

### `scraper.py`
- Reducido a shim de compatibilidad de `buscar_torrents(...)`: delega en el motor Nyaa y
  rechaza explícitamente otros `base_url`.

### Pruebas y verificación
- `tests/vantage/` — **99 pruebas offline** sobre fixtures HTML/JSON reales capturadas
  el 2026-10-14 (sin red en la suite).
- `scripts/verificar_engines.py` — sondeo en vivo de mirrors (HTTP, latencia, causa) y
  de motores; genera informe markdown. Salida real en `VERIFICACION_ENGINES.md`.
- `requirements-dev.txt` — pytest.

## 3. Evidencia de funcionamiento

```
$ python3 main.py "Busca la serie Severance" --verbose -n 2
Extracción LLM: query='Severance' categoria='tv'
imdb_id=tt11280740
items: 119 brutos, 98 únicos, 0 descartados por relevancia
[OMITIDO] YTS            no soporta categoria='tv'
[OK]      LimeTorrents   40 resultado(s) (659 ms)
[FALLO]   MagnetDL       ErrorFuenteNoDisponible: ningún mirror respondió: ...
[OK]      EZTV           79 resultado(s), imdb=tt11280740 (1129 ms)
[OK]      Nyaa           0 resultado(s) (426 ms)

Resultado #1: Severance S02E10 1080p WEB H264-SuccessfulCrab — 3845 sembradores / 1321 — 5.69 GB
```

Y el caso que antes era mudo:

```
$ python3 main.py "Zxqwvbn 1999 pelicula inexistente"
No results found matching criteria.
consulta='Zxqwvbn 1999 pelicula inexistente' categoria=movies min_seeders=5
items: 0 brutos, 0 únicos, 0 descartados por relevancia
[OK]      YTS            0 resultado(s) (1203 ms)
[OK]      LimeTorrents   0 resultado(s) (643 ms)
[FALLO]   MagnetDL       ErrorFuenteNoDisponible: ...
[OMITIDO] EZTV           no soporta categoria='movies'
[OK]      Nyaa           0 resultado(s) (456 ms)
```

`pytest tests/vantage -q` → **99 passed**.

## 4. Rendimiento: no esperar a un índice caído (añadido después)

Medido con el backend real: una búsqueda con todos los motores tarda **15 025 ms** y
**~12 s de esos son el timeout de MagnetDL** (caído desde el 2026-10-14). Se añadió:

- `--motores LISTA` / `--sin-motores LISTA` (`engines.seleccionar_motores()`, acepta
  nombres o dominios, sin distinguir acentos ni mayúsculas).
- `salud.py`: comprobación de intérprete, dependencias, Ollama y modelo, con salida JSON
  (`--doctor`). Es lo que usará el botón "Comprobar conexión" de la futura app.
- `scripts/vantage-search`: punto de entrada estable para clientes externos; encapsula la
  ruta del `venv` y devuelve `{"error": ...}` con código **65** si falta el backend.
- Los errores de uso de la CLI ahora salen con **64** en vez de 2 (que significa "sin
  resultados" y confundiría a un cliente).

Resultado medido: **15 025 ms → 2 265 ms** con los mismos 47 resultados.

### Salud persistente (segunda iteración)

Excluir el índice a mano resolvía la latencia pero no la **caducidad**: el día que
MagnetDL vuelva, alguien tendría que acordarse de rehabilitarlo (y reconstruir la app de
Glaze). Se añadió `salud_motores.py`, que persiste el historial en `.estado_motores.json`:

- Dos fallos consecutivos degradan el motor; un éxito lo limpia.
- Dentro del TTL (30 min) no se consulta: `[SALTADO]` en el diagnóstico, coste cero.
- TTL vencido: re-sondeo con timeout de 3 s (no 12). Si revive, se recupera solo.
- Solo cuentan los fallos de fuente: `ErrorResolucion` (IMDb) no degrada EZTV.
- Overrides: `--salud auto|off|reset`, más `--motores`/`--sin-motores`.

Medido en vivo, siempre con los mismos 47 resultados: 1.º fallo 33 911 ms → 2.º fallo
13 840 ms → **3.º saltado 2 140 ms** → TTL vencido 4 800 ms (sondeo) → saltado otra vez
2 046 ms → `--salud off` 13 693 ms.

**Trampa encontrada y corregida:** los tests usaban el `.estado_motores.json` real y lo
ensuciaban con fallos simulados (habrían degradado YTS/Nyaa sin motivo). Ahora hay una
fixture autouse que redirige el estado a un temporal, y se comprueba que la suite no
recrea el archivo real. Suite: **134 pruebas**.

Suite de pruebas: **122** (antes 99).

## 5. Cómo reproducirlo

```bash
cd ~/Documents/03\ Projects/VANTAGE/Bittorrent_Search
source venv/bin/activate
pytest tests/vantage -q                      # 99 pruebas, sin red
python3 scripts/verificar_engines.py         # salud real de los índices
python3 main.py "Busca la serie Severance" -v
```

## 5. Pendientes / siguientes pasos

1. **MagnetDL** (HTTP 522) sigue caído: cuando vuelva, verificar los selectores
   `table.download` con `scripts/verificar_engines.py` (no se pudo validar contra HTML real).
   Mientras tanto, el cliente puede saltarlo con `--sin-motores MagnetDL` (15 s → 2,3 s).
2. **LimeTorrents**: el filtro de categoría es local y solo mira la primera página; una
   paginación real requeriría seguir `/search/.../seeds/2/`.
3. **Sin paginación** en YTS (50 items) ni EZTV (100); añadir `--paginas` si hace falta.
4. **Relevancia**: si un título legítimo se descarta por el filtro por palabra, la
   válvula de escape es `--sin-relevancia`; convendría registrar en el diagnóstico los
   títulos descartados (hoy solo se cuenta cuántos).
5. **Índices**: los dominios cambian; el verificador es el punto de entrada para
   actualizar las constantes `BASE_URLS_*` de `engines.py`.
6. **Calidad del release vs. semillas**: el orden es estrictamente por sembradores
   (requisito del contrato original), y en la verificación real el primer puesto de
   "Oppenheimer 2023" fue un **HQ-CAM** con 1276 sembradores, por encima de un BluRay
   1080p con 571. No es un bug, es el criterio acordado, pero conviene decidir si se
   añade un desempate por calidad (descartar CAM/TS/HDCAM o priorizar BluRay/WEB-DL)
   como opción, sin tocar el orden por defecto.
