"""Motores de búsqueda de metadatos BitTorrent y agregador de VANTAGE.

Contrato de resultados
----------------------
Cada motor devuelve ``list[dict]`` con estas claves:

=============  =====  ==================================
clave          tipo   descripción
=============  =====  ==================================
``title``      str    nombre del release
``magnet``     str    URI magnet completo
``seeders``    int    sembradores
``leechers``   int    descargadores
``size``       str    tamaño legible o ``"N/A"``
``source``     str    motor que produjo el item
=============  =====  ==================================

Contrato de errores
-------------------
Ningún motor silencia fallos:

* ``requests.RequestException`` ante errores de red o HTTP.
* :class:`ErrorEstructura` cuando la página responde 200 pero su estructura ya
  no es la esperada (selectores roscados).
* :class:`ErrorFuenteNoDisponible` cuando todos los mirrors de un motor fallan.

Devolver ``[]`` significa exactamente "la fuente respondió bien y ningún item
pasó los filtros". Gracias a esto el agregador puede reportar *por qué* una
búsqueda quedó vacía en lugar de imprimir un genérico "no hay resultados".

Estado verificado (2026-10-14, red residencial MX)
--------------------------------------------------
=============  ==========================================  ===================
motor          endpoint verificado                         resultado
=============  ==========================================  ===================
YTS            ``https://yts.gg/api/v2/list_movies.json``  200 OK (``yts.mx`` no resuelve DNS)
LimeTorrents   ``https://www.limetorrents.lol`` -> ``.fun`` 200 OK (40 filas)
naa            ``https://nyaa.si``                          200 OK
EZTV           ``https://eztv.re`` -> ``eztvx.to``          200 OK (exige IMDb id)
MagnetDL       ``https://www.magnetdl.com``                 HTTP 522 (origen caído)
=============  ==========================================  ===================
"""

from __future__ import annotations

import inspect
import logging
import random
import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import requests
from bs4 import BeautifulSoup

from resolver import ErrorResolucion, TIPOS_PELICULA, TIPOS_PREFERIDOS, TIPOS_TV, resolver_imdb_id
from salud_motores import Decision, SaludMotores
from texto import (
    deduplicar_preservando_orden,
    es_imdb_id,
    extraer_anio,
    imdb_numerico,
    limpiar_consulta,
    coincide_titulo,
    normalizar,
    normalizar_categoria,
    tokens_significativos,
)

logger = logging.getLogger(__name__)

TIMEOUT_POR_DEFECTO = 12.0
REINTENTOS_POR_DEFECTO = 2
#: Pausa base del backoff entre reintentos, en segundos. Las pruebas la ponen a 0
#: para no dormir 0.5 s por cada motor simulado como caído.
PAUSA_REINTENTO = 0.5
MAX_WORKERS_POR_DEFECTO = 5

AGENTE_NAVEGADOR = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
CABECERAS_NAVEGADOR: Dict[str, str] = {
    "User-Agent": AGENTE_NAVEGADOR,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
    "Connection": "keep-alive",
}

#: Trackers añadidos a los magnets que construimos nosotros (LimeTorrents/YTS).
TRACKERS_POR_DEFECTO: Tuple[str, ...] = (
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://open.stealth.si:80/announce",
    "udp://tracker.torrent.eu.org:451/announce",
    "udp://exodus.desync.com:6969/announce",
)

#: Captura el info-hash desde un magnet o desde un enlace de descarga .torrent.
PATRON_HASH = re.compile(
    r"(?:xt=urn:btih:|itorrents\.net/torrent/)([A-Fa-f0-9]{40}|[A-Za-z2-7]{32})"
)
PATRON_MAGNET = re.compile(r"magnet:\?xt=urn:btih:[^\s\"'<>]+", re.IGNORECASE)
PATRON_SIN_RESULTADOS = re.compile(
    r"no results|nothing found|no torrents|sin resultados|0 results", re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Excepciones
# ---------------------------------------------------------------------------
class ErrorMotor(RuntimeError):
    """Fallo genérico de un motor de búsqueda."""


class ErrorEstructura(ErrorMotor):
    """La fuente respondió pero su HTML/JSON ya no tiene la forma esperada."""


class ErrorFuenteNoDisponible(ErrorMotor):
    """Ninguno de los mirrors configurados respondió correctamente."""


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------
def construir_magnet(
    info_hash: str,
    display_name: Optional[str] = None,
    trackers: Sequence[str] = TRACKERS_POR_DEFECTO,
) -> str:
    """Construye un URI magnet a partir de un info-hash.

    >>> construir_magnet("D6E78B95225B76E200A9DB223EEDB7E1C8AD6E45", "Oppenheimer")
    'magnet:?xt=urn:btih:d6e78b95225b76e200a9db223eedb7e1c8ad6e45&dn=Oppenheimer&tr=...'

    Raises:
        ValueError: Si el hash está vacío.
    """
    hash_limpio = re.sub(r"[^A-Za-z0-9]", "", info_hash or "")
    if not hash_limpio:
        raise ValueError("info-hash vacío: imposible construir el magnet")

    partes = [f"xt=urn:btih:{hash_limpio.lower()}"]
    if display_name:
        partes.append(f"dn={urllib.parse.quote(display_name.strip(), safe='')}")
    for tracker in trackers:
        partes.append(f"tr={urllib.parse.quote(tracker, safe='')}")
    return "magnet:?" + "&".join(partes)


def a_entero(texto: Optional[str]) -> int:
    """Convierte "1,276" o " 12 " en ``int``; devuelve 0 si no hay dígitos."""
    if not texto:
        return 0
    solo_digitos = re.sub(r"[^\d]", "", str(texto))
    return int(solo_digitos) if solo_digitos else 0


def formatear_bytes(valor: Any) -> str:
    """Convierte bytes a una cadena legible (``1536`` -> ``"1.5 KB"``)."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return "N/A"
    if numero <= 0:
        return "N/A"
    for unidad in ("B", "KB", "MB", "GB", "TB"):
        if numero < 1024 or unidad == "TB":
            return f"{numero:.1f} {unidad}".replace(".0 ", " ")
        numero /= 1024
    return "N/A"


def limpiar_titulo(texto: Optional[str]) -> str:
    """Colapsa espacios y saltos de línea del título extraído."""
    return re.sub(r"\s+", " ", (texto or "")).strip()


def _pedir(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: float = TIMEOUT_POR_DEFECTO,
    reintentos: int = REINTENTOS_POR_DEFECTO,
    session: Optional[requests.Session] = None,
) -> requests.Response:
    """GET con reintentos y backoff lineal.

    Raises:
        requests.RequestException: si se agotan los reintentos.
    """
    agente = session or requests
    ultimo_error: Optional[Exception] = None

    for intento in range(1, max(1, reintentos) + 1):
        try:
            respuesta = agente.get(url, headers=headers, params=params, timeout=timeout)
            if respuesta.status_code in (429, 500, 502, 503, 504) and intento < reintentos:
                time.sleep(PAUSA_REINTENTO * intento)
                continue
            respuesta.raise_for_status()
            return respuesta
        except requests.RequestException as error:
            ultimo_error = error
            # No se reintenta un timeout ni un error HTTP: un índice muerto cuesta su
            # timeout completo en cada intento, así que insistir duplicaría el peor caso
            # (12 s -> 24 s). Los fallos baratos (DNS, conexión rechazada) y los códigos
            # 429/5xx, que se gestionan arriba, sí se reintentan.
            # ``ConnectTimeout`` hereda de ``ConnectionError`` **y** de ``Timeout``: es un
            # fallo de conexión barato (acotado por el timeout de conexión), así que se
            # reintenta, a diferencia de un ``ReadTimeout`` que cuesta el timeout completo.
            no_reintentable = isinstance(error, (requests.Timeout, requests.HTTPError)) and not isinstance(
                error, requests.ConnectTimeout
            )
            if no_reintentable:
                break
            if intento < reintentos:
                time.sleep(PAUSA_REINTENTO * intento)

    raise requests.RequestException(
        f"GET {url} falló tras {max(1, reintentos)} intento(s): {ultimo_error}"
    ) from ultimo_error


def _pedir_con_mirrors(
    bases: Sequence[str],
    ruta: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: float = TIMEOUT_POR_DEFECTO,
    session: Optional[requests.Session] = None,
    validador: Optional[Callable[[requests.Response], None]] = None,
    reintentos: int = REINTENTOS_POR_DEFECTO,
) -> Tuple[requests.Response, str]:
    """Prueba cada mirror hasta que uno responda y pase ``validador``.

    Returns:
        ``(respuesta, base_url)`` del primer mirror válido.

    Raises:
        ErrorFuenteNoDisponible: si todos los mirrors fallan.
    """
    fallos: List[str] = []
    for base in bases:
        url = base.rstrip("/") + ruta
        try:
            respuesta = _pedir(
                url,
                headers=headers,
                params=params,
                timeout=timeout,
                session=session,
                reintentos=reintentos,
            )
            if validador is not None:
                validador(respuesta)
            return respuesta, base
        except (requests.RequestException, ErrorEstructura, ValueError) as error:
            resumen = str(error).replace("\n", " ")[:140]
            fallos.append(f"{base} -> {type(error).__name__}: {resumen}")
            logger.debug("mirror descartado: %s", fallos[-1])

    raise ErrorFuenteNoDisponible("ningún mirror respondió: " + " | ".join(fallos))


def _pagina_vacia(html: str, sopa: BeautifulSoup) -> bool:
    """Detecta páginas de "sin resultados" para no confundirlas con un fallo."""
    if PATRON_SIN_RESULTADOS.search(html):
        return True
    return sopa.find(string=PATRON_SIN_RESULTADOS) is not None


def _item(
    titulo: str,
    magnet: Optional[str],
    seeders: int,
    leechers: int,
    size: str,
    fuente: str,
) -> Optional[Dict[str, Any]]:
    """Normaliza un item y descarta los que no tienen magnet válido."""
    if not magnet or not magnet.lower().startswith("magnet:"):
        return None
    return {
        "title": limpiar_titulo(titulo),
        "magnet": magnet,
        "seeders": int(seeders),
        "leechers": int(leechers),
        "size": size or "N/A",
        "source": fuente,
    }


# ---------------------------------------------------------------------------
# Motor 1: YTS (API JSON, películas)
# ---------------------------------------------------------------------------
BASE_URLS_YTS: Tuple[str, ...] = (
    "https://yts.gg",
    "https://yts.mx",
    "https://yts.lt",
    "https://yts.am",
)
RUTA_YTS = "/api/v2/list_movies.json"

#: Categoría canónica -> género de la API de YTS (``None`` = sin filtro de género).
#: Categoría canónica -> género de la API de YTS (``None`` = sin filtro de género).
#:
#: Alcance real: solo sirve para llamadas directas a :func:`buscar_torrents_yts`. El
#: agregador pasa siempre la categoría canónica (``movies``/``all``), que no lleva género,
#: así que desde la CLI el parámetro ``genre`` nunca se envía. Se conserva porque la API de
#: YTS lo admite y una llamada directa puede aprovecharlo.
GENEROS_YTS: Dict[str, Optional[str]] = {
    "all": None,
    "movies": None,
    "action": "Action",
    "adventure": "Adventure",
    "animation": "Animation",
    "biography": "Biography",
    "comedy": "Comedy",
    "crime": "Crime",
    "documentary": "Documentary",
    "drama": "Drama",
    "family": "Family",
    "fantasy": "Fantasy",
    "history": "History",
    "horror": "Horror",
    "music": "Music",
    "mystery": "Mystery",
    "romance": "Romance",
    "sci-fi": "Sci-Fi",
    "sport": "Sport",
    "thriller": "Thriller",
    "war": "War",
    "western": "Western",
}

#: Índice de búsqueda de :data:`GENEROS_YTS` con las claves normalizadas. Sin esto, la
#: consulta normalizaba la entrada ("Sci-Fi" -> "sci fi") pero no las claves, así que los
#: géneros con guion o acento no coincidían nunca.
GENEROS_YTS_NORMALIZADO: Dict[str, Optional[str]] = {
    normalizar(clave): valor for clave, valor in GENEROS_YTS.items()
}


def _validar_yts(respuesta: requests.Response) -> None:
    """Comprueba que el mirror devuelva JSON de la API de YTS y no su página 404."""
    tipo = respuesta.headers.get("Content-Type", "")
    if "json" not in tipo.lower() and respuesta.text.lstrip()[:1] != "{":
        raise ErrorEstructura(f"{respuesta.url} no devolvió JSON (Content-Type: {tipo or 'desconocido'})")
    try:
        respuesta.json()
    except ValueError as error:
        raise ErrorEstructura(f"{respuesta.url} devolvió JSON inválido: {error}") from error


def buscar_torrents_yts(
    query: str,
    categoria: Optional[str] = None,
    min_seeders: int = 5,
    *,
    timeout: float = TIMEOUT_POR_DEFECTO,
    session: Optional[requests.Session] = None,
) -> List[Dict[str, Any]]:
    """Busca películas en la API pública de YTS probando mirrors en orden.

    Args:
        query: Título o IMDb id (``tt15398776``).
        categoria: Categoría canónica o género YTS.
        min_seeders: Umbral mínimo de sembradores.
        timeout: Timeout por petición.
        session: Sesión ``requests`` reutilizable.

    Returns:
        Items ordenados por sembradores descendente.

    Raises:
        ErrorFuenteNoDisponible: si ningún mirror entrega JSON válido.
        requests.RequestException: si la petición falla.
    """
    genero = GENEROS_YTS_NORMALIZADO.get(normalizar(categoria) if categoria else "all")
    parametros: Dict[str, Any] = {
        "query_term": query,
        "limit": 50,
        "sort_by": "seeds",
        "order_by": "desc",
    }
    if genero:
        parametros["genre"] = genero

    respuesta, _ = _pedir_con_mirrors(
        BASE_URLS_YTS,
        RUTA_YTS,
        headers={"User-Agent": AGENTE_NAVEGADOR},
        params=parametros,
        timeout=timeout,
        session=session,
        validador=_validar_yts,
    )
    datos = respuesta.json()

    if datos.get("status") != "ok":
        raise ErrorEstructura(f"YTS respondió status={datos.get('status')!r}: {datos.get('status_message')}")

    peliculas = (datos.get("data") or {}).get("movies") or []
    resultados: List[Dict[str, Any]] = []

    for pelicula in peliculas:
        titulo_base = pelicula.get("title_long") or pelicula.get("title") or ""
        for torrent in pelicula.get("torrents") or []:
            seeders = a_entero(torrent.get("seeds"))
            if seeders < min_seeders:
                continue
            calidad = torrent.get("quality") or "HD"
            tipo = torrent.get("type") or ""
            titulo = f"{titulo_base} [{calidad}]" + (f" [{tipo}]" if tipo else "") + " [YTS]"
            try:
                magnet = construir_magnet(torrent.get("hash", ""), titulo)
            except ValueError:
                continue
            item = _item(
                titulo,
                magnet,
                seeders,
                a_entero(torrent.get("peers")),
                torrent.get("size") or "N/A",
                "YTS",
            )
            if item:
                resultados.append(item)

    return _ordenar_por_estabilidad(resultados)


# ---------------------------------------------------------------------------
# Motor 2: LimeTorrents (HTML, generalista)
# ---------------------------------------------------------------------------
BASE_URLS_LIME: Tuple[str, ...] = (
    "https://www.limetorrents.fun",
    "https://www.limetorrents.lol",
)

#: Categoría canónica -> segmento de URL de LimeTorrents.
CATEGORIAS_LIME: Dict[str, str] = {
    "all": "all",
    "movies": "movies",
    "tv": "tv-shows",
    "anime": "anime",
    "music": "music",
    "games": "games",
    "applications": "applications",
    "books": "books",
}

#: Etiqueta "in X" de cada fila -> categoría canónica (filtrado en cliente).
#: "other"/"xxx" no son comodines: se mapean a "otros" para que una búsqueda de
#: música no devuelva filas sin categoría útil.
ETIQUETAS_LIME: Dict[str, str] = {
    "movies": "movies",
    "tv shows": "tv",
    "tv": "tv",
    "music": "music",
    "games": "games",
    "applications": "applications",
    "software": "applications",
    "anime": "anime",
    "books": "books",
    "other": "otros",
    "xxx": "otros",
}

#: Etiqueta ilegible: la fila se conserva en cualquier filtro (fallar abierto,
#: nunca ocultar resultados por un cambio de formato del sitio).
CATEGORIA_DESCONOCIDA = "desconocida"


def extraer_categoria_lime(texto_fila: str) -> str:
    """Extrae la categoría canónica de una celda tipo ``"1 Year+ - in Movies"``."""
    coincidencia = re.search(r"in\s+([A-Za-z ]+?)\s*$", limpiar_titulo(texto_fila), re.IGNORECASE)
    if not coincidencia:
        return CATEGORIA_DESCONOCIDA
    return ETIQUETAS_LIME.get(normalizar(coincidencia.group(1)), CATEGORIA_DESCONOCIDA)


def _parsear_pagina_limetorrents(
    respuesta: requests.Response,
    categoria_canonica: str,
    min_seeders: int,
) -> List[Dict[str, Any]]:
    """Parsea una página de resultados de LimeTorrents y devuelve los items válidos.

    Args:
        respuesta: Respuesta HTTP de LimeTorrents.
        categoria_canonica: Categoría canónica para filtrar en cliente.
        min_seeders: Umbral mínimo de sembradores.

    Returns:
        Lista de items válidos de esta página.

    Raises:
        ErrorEstructura: Si la página no tiene la estructura esperada.
    """
    sopa = BeautifulSoup(respuesta.text, "html.parser")

    tabla = sopa.find("table", class_="table2")
    if tabla is None:
        if _pagina_vacia(respuesta.text, sopa):
            return []
        raise ErrorEstructura(
            f"{respuesta.url}: no se encontró 'table.table2' (¿cambió el HTML o hay bloqueo anti-bot?)"
        )

    filas = [fila for fila in tabla.find_all("tr") if fila.find("th") is None]
    resultados: List[Dict[str, Any]] = []
    sin_hash = 0
    fuera_de_categoria = 0

    for fila in filas:
        celdas = fila.find_all("td")
        contenedor = fila.select_one("td.tdleft div.tt-name")
        if contenedor is None or len(celdas) < 6:
            continue

        enlaces = contenedor.find_all("a", href=True)
        if not enlaces:
            continue

        enlace_titulo = next((a for a in enlaces if "-torrent-" in a["href"]), enlaces[-1])
        titulo = limpiar_titulo(enlace_titulo.get_text(" ", strip=True))
        if not titulo:
            continue

        if categoria_canonica != "all":
            categoria_fila = extraer_categoria_lime(celdas[1].get_text(" ", strip=True))
            if categoria_fila not in (categoria_canonica, CATEGORIA_DESCONOCIDA):
                fuera_de_categoria += 1
                continue

        magnet = None
        directo = fila.find("a", href=PATRON_MAGNET)
        if directo is not None:
            magnet = directo["href"]
        else:
            coincidencia = PATRON_HASH.search(" ".join(a["href"] for a in enlaces))
            if coincidencia:
                try:
                    magnet = construir_magnet(coincidencia.group(1), titulo)
                except ValueError:
                    magnet = None

        if not magnet:
            sin_hash += 1
            continue

        seeders = a_entero(fila.select_one("td.tdseed").get_text() if fila.select_one("td.tdseed") else None)
        leechers = a_entero(fila.select_one("td.tdleech").get_text() if fila.select_one("td.tdleech") else None)
        if seeders < min_seeders:
            continue

        item = _item(
            titulo,
            magnet,
            seeders,
            leechers,
            limpiar_titulo(celdas[2].get_text()),
            "LimeTorrents",
        )
        if item:
            resultados.append(item)

    if sin_hash:
        logger.debug("LimeTorrents: %s fila(s) sin info-hash derivable", sin_hash)
    if fuera_de_categoria:
        logger.debug("LimeTorrents: %s fila(s) descartadas por categoría", fuera_de_categoria)

    return resultados


def buscar_torrents_limetorrents(
    query: str,
    categoria: Optional[str] = None,
    min_seeders: int = 5,
    *,
    paginas: int = 1,
    timeout: float = TIMEOUT_POR_DEFECTO,
    session: Optional[requests.Session] = None,
) -> List[Dict[str, Any]]:
    """Busca en LimeTorrents construyendo el magnet desde el info-hash de la fila.

    La página de búsqueda **no** publica enlaces magnet: cada fila trae un enlace
    ``itorrents.net/torrent/<hash>.torrent`` del que se deriva el info-hash. Ese
    hash se convierte en magnet con :func:`construir_magnet`, evitando una
    petición extra por resultado.

    El mirror verificado ignora el segmento de categoría de la URL, por lo que el
    filtro de categoría se aplica en cliente usando la etiqueta ``in <categoría>``
    de cada fila.

    Args:
        query: Término de búsqueda.
        categoria: Categoría canónica para filtrar en cliente.
        min_seeders: Umbral mínimo de sembradores.
        paginas: Número de páginas a consultar (por defecto 1).
        timeout: Timeout por petición.
        session: Sesión ``requests`` reutilizable.

    Returns:
        Items ordenados por sembradores descendente, deduplicados por magnet.

    Raises:
        ValueError: Si ``paginas`` no es un entero positivo.
        ErrorFuenteNoDisponible: Si ningún mirror responde.
        ErrorEstructura: Si la página no trae la tabla de resultados esperada.
    """
    if not isinstance(paginas, int) or isinstance(paginas, bool) or paginas < 1:
        raise ValueError("paginas debe ser un entero positivo")

    categoria_canonica = normalizar_categoria(categoria) if categoria else "all"
    segmento = CATEGORIAS_LIME.get(categoria_canonica, "all")
    slug = urllib.parse.quote(query.strip().lower().replace(" ", "-"), safe="")

    resultados_completos: List[Dict[str, Any]] = []
    magnets_vistos: set[str] = set()

    for numero_pagina in range(1, paginas + 1):
        ruta = f"/search/{segmento}/{slug}/seeds/{numero_pagina}/"

        respuesta, _ = _pedir_con_mirrors(
            BASE_URLS_LIME,
            ruta,
            headers=CABECERAS_NAVEGADOR,
            timeout=timeout,
            session=session,
        )

        items_pagina = _parsear_pagina_limetorrents(respuesta, categoria_canonica, min_seeders)

        if not items_pagina:
            if numero_pagina == 1:
                return []
            break

        for item in items_pagina:
            magnet = item["magnet"]
            if magnet not in magnets_vistos:
                magnets_vistos.add(magnet)
                resultados_completos.append(item)

    return _ordenar_por_estabilidad(resultados_completos)


# ---------------------------------------------------------------------------
# Motor 3: MagnetDL (HTML, generalista)
# ---------------------------------------------------------------------------
BASE_URLS_MAGNETDL: Tuple[str, ...] = (
    "https://www.magnetdl.com",
    "https://www.magnetdl.com.mx",
)
NOTAS_MAGNETDL = (
    "Sin respuesta verificado el 2026-10-14/15: read timeout en .com y DNS sin resolver en "
    ".mx (el HTTP 522 apareció en una comprobación previa). El motor queda activo y, si "
    "vuelve, funciona sin cambios."
)


def buscar_torrents_magnetdl(
    query: str,
    categoria: Optional[str] = None,
    min_seeders: int = 5,
    *,
    timeout: float = TIMEOUT_POR_DEFECTO,
    session: Optional[requests.Session] = None,
) -> List[Dict[str, Any]]:
    """Busca en MagnetDL (HTML, ruta ``/<inicial>/<slug>/``).

    Raises:
        ErrorFuenteNoDisponible: si ningún mirror responde (hoy lo habitual: read timeout en
            ``.com`` y DNS sin resolver en ``.mx``).
    """
    slug = query.strip().lower().replace(" ", "-")
    inicial = slug[0] if slug and slug[0].isalnum() else "a"
    ruta = f"/{inicial}/{urllib.parse.quote(slug, safe='')}/"

    respuesta, _ = _pedir_con_mirrors(
        BASE_URLS_MAGNETDL,
        ruta,
        headers={**CABECERAS_NAVEGADOR, "Referer": "https://www.magnetdl.com/"},
        timeout=timeout,
        session=session,
    )

    sopa = BeautifulSoup(respuesta.text, "html.parser")

    # Mismo orden que en LimeTorrents: primero la tabla, después el aviso de "sin resultados".
    tabla = sopa.find("table", class_="download")
    if tabla is None:
        if _pagina_vacia(respuesta.text, sopa):
            return []
        raise ErrorEstructura(f"{respuesta.url}: no se encontró 'table.download'")

    resultados: List[Dict[str, Any]] = []
    for fila in tabla.find_all("tr"):
        magnet_nodo = fila.select_one("td.m a[href^='magnet:?']")
        titulo_nodo = fila.select_one("td.n a")
        if magnet_nodo is None or titulo_nodo is None:
            continue

        seeders = a_entero(fila.select_one("td.s").get_text() if fila.select_one("td.s") else None)
        leechers = a_entero(fila.select_one("td.l").get_text() if fila.select_one("td.l") else None)
        if seeders < min_seeders:
            continue

        celdas = fila.find_all("td")
        item = _item(
            titulo_nodo.get_text(" ", strip=True),
            magnet_nodo.get("href"),
            seeders,
            leechers,
            limpiar_titulo(celdas[5].get_text()) if len(celdas) > 5 else "N/A",
            "MagnetDL",
        )
        if item:
            resultados.append(item)

    return _ordenar_por_estabilidad(resultados)


# ---------------------------------------------------------------------------
# Motor 4: EZTV (API JSON, series; exige IMDb id)
# ---------------------------------------------------------------------------
BASE_URLS_EZTV: Tuple[str, ...] = (
    "https://eztv.re",
    "https://eztvx.to",
    "https://eztv.wf",
)
RUTA_EZTV = "/api/get-torrents"


def _validar_eztv(respuesta: requests.Response) -> None:
    if "torrents" not in respuesta.text and "torrents_count" not in respuesta.text:
        raise ErrorEstructura(f"{respuesta.url} no devolvió el JSON de EZTV")


def buscar_torrents_eztv(
    query: str,
    categoria: Optional[str] = None,
    min_seeders: int = 5,
    *,
    imdb_id: Optional[str] = None,
    resolver: bool = True,
    timeout: float = TIMEOUT_POR_DEFECTO,
    session: Optional[requests.Session] = None,
) -> List[Dict[str, Any]]:
    """Busca series en la API de EZTV.

    EZTV no acepta búsquedas por texto: requiere un ``imdb_id`` numérico. Si no se
    recibe uno, se resuelve con :mod:`resolver` a partir del título.

    Args:
        query: Título en lenguaje natural o IMDb id.
        categoria: Se ignora (EZTV es solo series) pero se acepta por simetría.
        min_seeders: Umbral mínimo de sembradores.
        imdb_id: IMDb id ya resuelto (``tt11280740`` o ``11280740``).
        resolver: Si es ``False``, no se intenta resolver el id por red.
        timeout: Timeout por petición.
        session: Sesión ``requests`` reutilizable.

    Raises:
        ErrorResolucion: si no hay IMDb id y no se pudo resolver.
        ErrorFuenteNoDisponible: si ningún mirror responde.
    """
    identificador = imdb_numerico(imdb_id) if imdb_id else imdb_numerico(query)

    if not identificador:
        if not resolver:
            raise ErrorResolucion(
                f"EZTV exige un IMDb id y no se pudo resolver '{query}' (resolución desactivada)"
            )
        resuelto = resolver_imdb_id(
            query, extraer_anio(query), tipos_preferidos=TIPOS_TV, session=session, timeout=timeout
        )
        if not resuelto:
            raise ErrorResolucion(f"EZTV exige un IMDb id y no se encontró candidato para '{query}'")
        identificador = imdb_numerico(resuelto)

    respuesta, _ = _pedir_con_mirrors(
        BASE_URLS_EZTV,
        RUTA_EZTV,
        headers={"User-Agent": AGENTE_NAVEGADOR},
        params={"imdb_id": identificador, "limit": 100, "page": 1},
        timeout=timeout,
        session=session,
        validador=_validar_eztv,
    )
    datos = respuesta.json()

    if a_entero(datos.get("torrents_count")) == 0:
        return []

    resultados: List[Dict[str, Any]] = []
    for torrent in datos.get("torrents") or []:
        seeders = a_entero(torrent.get("seeds"))
        if seeders < min_seeders:
            continue
        titulo = torrent.get("title") or torrent.get("filename") or "TV Release"
        item = _item(
            titulo,
            torrent.get("magnet_url"),
            seeders,
            a_entero(torrent.get("peers")),
            formatear_bytes(torrent.get("size_bytes")),
            "EZTV",
        )
        if item:
            resultados.append(item)

    return _ordenar_por_estabilidad(resultados)


# ---------------------------------------------------------------------------
# Motor 5: Nyaa (HTML, anime y contenido asiático)
# ---------------------------------------------------------------------------
BASE_URLS_NYAA: Tuple[str, ...] = ("https://nyaa.si",)

#: Categoría canónica -> código de categoría de Nyaa.
#: Ojo: ``1_0`` es *Anime*; el contenido de imagen real es ``4_0`` (Live Action).
CATEGORIAS_NYAA: Dict[str, Optional[str]] = {
    "all": None,
    "anime": "1_0",
    "movies": "4_0",
    "tv": "4_0",
    "music": "2_0",
    "applications": "6_0",
    "games": "6_0",
    "books": "3_0",
}


def buscar_torrents_nyaa(
    query: str,
    categoria: Optional[str] = None,
    min_seeders: int = 5,
    *,
    pagina: int = 1,
    timeout: float = TIMEOUT_POR_DEFECTO,
    session: Optional[requests.Session] = None,
) -> List[Dict[str, Any]]:
    """Busca en Nyaa (HTML, ``table.torrent-list``).

    Índice centrado en anime: para películas occidentales suele devolver vacío, y
    una página sin resultados de Nyaa no incluye la tabla, por lo que se detecta
    como lista vacía y no como error de estructura.

    Raises:
        ErrorFuenteNoDisponible: si Nyaa no responde.
        ErrorEstructura: si hay tabla pero las columnas cambiaron.
    """
    codigo = CATEGORIAS_NYAA.get(normalizar_categoria(categoria) if categoria else "all")
    parametros: Dict[str, Any] = {"q": query, "s": "seeders", "o": "desc", "p": pagina}
    if codigo:
        parametros["c"] = codigo

    respuesta, _ = _pedir_con_mirrors(
        BASE_URLS_NYAA,
        "/",
        headers=CABECERAS_NAVEGADOR,
        params=parametros,
        timeout=timeout,
        session=session,
    )

    sopa = BeautifulSoup(respuesta.text, "html.parser")
    tabla = sopa.find("table", class_="torrent-list")
    if tabla is None:
        if _pagina_vacia(respuesta.text, sopa):
            return []
        raise ErrorEstructura(f"{respuesta.url}: no se encontró 'table.torrent-list'")

    resultados: List[Dict[str, Any]] = []
    for fila in tabla.find_all("tr"):
        celdas = fila.find_all("td")
        if len(celdas) < 7:
            continue

        enlaces_titulo = celdas[1].find_all("a")
        if not enlaces_titulo:
            continue
        titulo = limpiar_titulo(enlaces_titulo[-1].get_text(" ", strip=True))

        magnet = None
        for enlace in celdas[2].find_all("a", href=True):
            if enlace["href"].lower().startswith("magnet:"):
                magnet = enlace["href"]
                break

        seeders = a_entero(celdas[5].get_text())
        if seeders < min_seeders:
            continue

        item = _item(
            titulo,
            magnet,
            seeders,
            a_entero(celdas[6].get_text()),
            limpiar_titulo(celdas[3].get_text()),
            "Nyaa",
        )
        if item:
            resultados.append(item)

    return _ordenar_por_estabilidad(resultados)


# ---------------------------------------------------------------------------
# Orden, deduplicación y relevancia
# ---------------------------------------------------------------------------
def _ordenar_por_estabilidad(resultados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ordena por sembradores descendente y, como desempate, por descargadores.

    Ordenar por sembradores es el criterio de "estabilidad" del enrutado torrent:
    más sembradores implica mayor disponibilidad de las piezas.
    """
    return sorted(resultados, key=lambda item: (item["seeders"], item["leechers"]), reverse=True)


@dataclass
class EstadoMotor:
    """Resultado de un motor dentro de una búsqueda agregada."""

    nombre: str
    ok: bool
    resultados: int = 0
    error: Optional[str] = None
    omitido: bool = False
    milisegundos: int = 0
    imdb_id: Optional[str] = None
    #: ``True`` si no se consultó por estar degradado (salud persistente).
    saltado_por_salud: bool = False
    #: Motivo de la salud (degradado, sondeo, TTL...).
    motivo_salud: Optional[str] = None
    #: Timeout efectivamente aplicado a este motor, en segundos.
    timeout_segundos: Optional[float] = None

    def linea(self) -> str:
        """Línea de reporte para terminal."""
        if self.omitido:
            return f"[OMITIDO] {self.nombre:<14} {self.error or 'no aplica a la categoría'}"
        if self.saltado_por_salud:
            return f"[SALTADO] {self.nombre:<14} {self.motivo_salud}"
        if not self.ok:
            return f"[FALLO]   {self.nombre:<14} {self.error}"
        detalle = f"{self.resultados} resultado(s)"
        if self.imdb_id:
            detalle += f", imdb={self.imdb_id}"
        if self.motivo_salud:
            detalle += f" [{self.motivo_salud}]"
        return f"[OK]      {self.nombre:<14} {detalle} ({self.milisegundos} ms)"


@dataclass
class ResumenBusqueda:
    """Diagnóstico completo de una búsqueda agregada."""

    consulta: str
    categoria: str
    min_seeders: int
    #: Petición tal como la devolvió el LLM, cuando difiere de ``consulta``.
    consulta_original: Optional[str] = None
    imdb_id: Optional[str] = None
    error_imdb: Optional[str] = None
    estados: List[EstadoMotor] = field(default_factory=list)
    brutos: int = 0
    unicos: int = 0
    descartados_relevancia: int = 0

    @property
    def motores_ok(self) -> List[EstadoMotor]:
        return [estado for estado in self.estados if estado.ok and not estado.omitido]

    @property
    def motores_fallidos(self) -> List[EstadoMotor]:
        return [estado for estado in self.estados if not estado.ok and not estado.omitido]

    def formatear(self) -> str:
        """Reporte multilínea listo para imprimir en stderr."""
        cabecera = f"consulta='{self.consulta}' categoria={self.categoria} min_seeders={self.min_seeders}"
        if self.consulta_original and self.consulta_original != self.consulta:
            cabecera += f" (peticion original='{self.consulta_original}')"
        lineas = [
            cabecera,
            f"imdb_id={self.imdb_id or 'no resuelto'}"
            + (f" ({self.error_imdb})" if self.error_imdb else ""),
            f"items: {self.brutos} brutos, {self.unicos} únicos, "
            f"{self.descartados_relevancia} descartados por relevancia",
        ]
        lineas.extend(estado.linea() for estado in self.estados)
        return "\n".join(lineas)


@dataclass
class Motor:
    """Descriptor de un motor conectable al agregador."""

    nombre: str
    funcion: Callable[..., List[Dict[str, Any]]]
    #: Categorías canónicas que el motor puede atender (``"all"`` incluye todo).
    categorias_soportadas: Tuple[str, ...] = ("all",)
    requiere_imdb: bool = False
    #: Preferencia de tipo al resolver el IMDb id (series vs películas).
    tipos_imdb: Tuple[str, ...] = TIPOS_PREFERIDOS
    nota: str = ""

    def soporta(self, categoria: str) -> bool:
        return categoria == "all" or categoria in self.categorias_soportadas


CATEGORIAS_GENERALISTAS: Tuple[str, ...] = (
    "all",
    "movies",
    "tv",
    "anime",
    "music",
    "games",
    "applications",
    "books",
)

MOTORES_POR_DEFECTO: Tuple[Motor, ...] = (
    Motor("YTS", buscar_torrents_yts, ("movies",), tipos_imdb=TIPOS_PELICULA, nota="API JSON, películas"),
    Motor("LimeTorrents", buscar_torrents_limetorrents, CATEGORIAS_GENERALISTAS, nota="HTML, generalista"),
    Motor("MagnetDL", buscar_torrents_magnetdl, CATEGORIAS_GENERALISTAS, nota=NOTAS_MAGNETDL),
    Motor(
        "EZTV",
        buscar_torrents_eztv,
        ("tv",),
        requiere_imdb=True,
        tipos_imdb=TIPOS_TV,
        nota="API JSON, series",
    ),
    Motor("Nyaa", buscar_torrents_nyaa, CATEGORIAS_GENERALISTAS, nota="HTML, anime/asiático"),
)


class AgregadorTorrents:
    """Consulta varios motores, deduplica por info-hash y elige el mejor item.

    Ejemplo:
        >>> agregador = AgregadorTorrents()
        >>> items, resumen = agregador.buscar_con_diagnostico("Oppenheimer 2023", "movies")
        >>> print(resumen.formatear())          # doctest: +SKIP
        >>> items[0]["source"]                  # doctest: +SKIP
        'YTS'
    """

    def __init__(
        self,
        motores: Optional[Sequence[Motor]] = None,
        *,
        paralelo: bool = True,
        timeout: float = TIMEOUT_POR_DEFECTO,
        max_workers: int = MAX_WORKERS_POR_DEFECTO,
        pausa: Tuple[float, float] = (0.0, 0.0),
        salud: Optional[SaludMotores] = None,
        limetorrents_paginas: int = 1,
    ) -> None:
        """
        Args:
            motores: Motores a usar (por defecto :data:`MOTORES_POR_DEFECTO`).
            paralelo: Consulta los motores en paralelo (hosts distintos: no hay
                competencia por rate limit). ``False`` los consulta en secuencia.
            timeout: Timeout por petición.
            max_workers: Hilos máximos en modo paralelo.
            pausa: Rango de espera aleatoria entre motores en modo secuencial.
            salud: Registro persistente de salud de los motores. Si es ``None`` se usa el
                archivo por defecto (``.estado_motores.json``); pasar
                ``SaludMotores(activa=False)`` lo desactiva.
            limetorrents_paginas: Páginas a consultar en LimeTorrents (por defecto 1).
        """
        if motores is not None and not tuple(motores):
            raise ValueError(
                "la lista de motores está vacía: usa MOTORES_POR_DEFECTO u omite el parámetro"
            )
        self.motores: Tuple[Motor, ...] = (
            tuple(motores) if motores is not None else MOTORES_POR_DEFECTO
        )
        nombres = [motor.nombre for motor in self.motores]
        duplicados = sorted({nombre for nombre in nombres if nombres.count(nombre) > 1})
        if duplicados:
            raise ValueError(
                f"nombres de motor duplicados: {', '.join(duplicados)}. El diagnóstico indexa "
                "por nombre y colapsaría las filas."
            )
        self.paralelo = paralelo
        self.timeout = timeout
        self.max_workers = max_workers
        self.pausa = pausa
        self.salud = salud if salud is not None else SaludMotores()
        self.limetorrents_paginas = limetorrents_paginas
        self.session = requests.Session()
        self.ultimo_resumen: Optional[ResumenBusqueda] = None

    def cerrar(self) -> None:
        """Cierra la sesión HTTP compartida. Idempotente."""
        try:
            self.session.close()
        except Exception:  # nunca debe tumbar el cierre por un fallo de red
            logger.debug("fallo al cerrar la sesión HTTP", exc_info=True)

    def __enter__(self) -> "AgregadorTorrents":
        return self

    def __exit__(self, *_: Any) -> None:
        self.cerrar()

    # -- infraestructura ---------------------------------------------------
    def _kwargs_motor(
        self,
        motor: Motor,
        *,
        imdb_id: Optional[str],
        resolver: bool,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Pasa sólo los argumentos opcionales que la firma del motor acepta."""
        parametros = inspect.signature(motor.funcion).parameters
        kwargs: Dict[str, Any] = {}
        if "timeout" in parametros:
            kwargs["timeout"] = self.timeout if timeout is None else timeout
        if "session" in parametros:
            kwargs["session"] = self.session
        if "imdb_id" in parametros:
            kwargs["imdb_id"] = imdb_id
        if "resolver" in parametros:
            kwargs["resolver"] = resolver
        if "paginas" in parametros:
            kwargs["paginas"] = self.limetorrents_paginas
        return kwargs

    @staticmethod
    def _cuenta_como_fallo(error: BaseException) -> bool:
        """``True`` si el error indica que la fuente falla (y no la consulta).

        Un fallo de resolución de IMDb (``ErrorResolucion``) es un problema de la
        búsqueda, no del índice: si contara, dos consultas sin resultados en IMDb
        dejarían EZTV degradado media hora sin motivo.
        """
        if isinstance(error, ErrorResolucion):
            return False
        return isinstance(error, (requests.RequestException, ErrorMotor, ValueError))

    def _anotar_salud(self, nombre: str, *, exito: bool, error: Optional[str] = None) -> None:
        """Anota salud sin poder tumbar la búsqueda.

        El registro es una optimización: si falla (por ejemplo por una carrera interna),
        no debe descartar resultados ya obtenidos ni propagarse. Convertir un problema de
        contabilidad en pérdida de datos es justo lo que pasaba antes de BH2-001.
        """
        try:
            self.salud.registrar(nombre, exito=exito, error=error)
        except Exception:
            logger.warning("no se pudo anotar la salud de %s; la búsqueda continúa", nombre, exc_info=True)

    def _resolver_imdb(
        self, query: str, motores: Sequence[Motor], activo: bool
    ) -> Tuple[Optional[str], Optional[str]]:
        """Resuelve el IMDb id una sola vez si algún motor lo necesita.

        Con ``categoria="all"`` se usa la preferencia del único motor que exige IMDb (EZTV,
        solo series): una serie se resuelve bien y una película da 0 resultados en EZTV de
        cualquier forma, así que la preferencia TV no pierde nada y gana el caso de series.
        """
        exigentes = [motor for motor in motores if motor.requiere_imdb]
        if not activo or not exigentes:
            return None, None
        if es_imdb_id(query):
            return query.lower(), None
        try:
            return (
                resolver_imdb_id(
                    query,
                    extraer_anio(query),
                    tipos_preferidos=exigentes[0].tipos_imdb,
                    session=self.session,
                    timeout=self.timeout,
                ),
                None,
            )
        except ErrorResolucion as error:
            return None, str(error)

    # -- API pública -------------------------------------------------------
    def buscar_con_diagnostico(
        self,
        query: str,
        categoria: Optional[str] = None,
        min_seeders: int = 5,
        *,
        exigir_coincidencia: bool = True,
        resolver_imdb: bool = True,
    ) -> Tuple[List[Dict[str, Any]], ResumenBusqueda]:
        """Busca en todos los motores aplicables y devuelve items + diagnóstico.

        Args:
            query: Consulta ya extraída por el LLM.
            categoria: Categoría canónica o alias en español.
            min_seeders: Umbral mínimo de sembradores.
            exigir_coincidencia: Descarta items cuyo título no contenga todos los
                tokens significativos de la consulta (evita el clásico falso
                positivo "Dune" -> "Sand Dunes" de la banda sonora de Genshin).
            resolver_imdb: Permite resolver IMDb por red cuando el motor lo exige.

        Returns:
            ``(items, resumen)``; ``items`` va ordenado por sembradores descendente.
        """
        categoria_canonica = normalizar_categoria(categoria)
        consulta_original = query
        # El LLM arrastra a veces la categoría dentro de la consulta
        # ("película Oppenheimer"): enviada literalmente a los índices da
        # cero resultados, así que se sanea antes de buscar.
        query = limpiar_consulta(query)
        tokens = [] if es_imdb_id(query) else tokens_significativos(query)

        aplicables: List[Motor] = []
        omitidos_por_nombre: Dict[str, EstadoMotor] = {}
        for motor in self.motores:
            if motor.soporta(categoria_canonica):
                aplicables.append(motor)
            else:
                omitidos_por_nombre[motor.nombre] = EstadoMotor(
                    nombre=motor.nombre,
                    ok=True,
                    omitido=True,
                    error=f"no soporta categoria='{categoria_canonica}'",
                )

        # Resolver el IMDb id sólo si algún motor aplicable lo exige: una búsqueda
        # de música o juegos no debe gastar una petición de red en IMDb.
        imdb_id, error_imdb = self._resolver_imdb(query, aplicables, resolver_imdb)

        estados_por_nombre: Dict[str, EstadoMotor] = {}
        resultados: List[Dict[str, Any]] = []

        def ejecutar(
            motor: Motor,
        ) -> Tuple[Motor, List[Dict[str, Any]], Optional[str], int, Decision]:
            decision = self.salud.decision(motor.nombre, timeout_normal=self.timeout)
            if decision.saltar:
                logger.debug("motor %s saltado por salud: %s", motor.nombre, decision.motivo)
                return motor, [], None, 0, decision

            inicio = time.monotonic()
            try:
                items = motor.funcion(
                    query,
                    categoria_canonica,
                    min_seeders,
                    **self._kwargs_motor(
                        motor,
                        imdb_id=imdb_id,
                        # Si el agregador ya intentó resolver y falló, el motor no repite la
                        # petición: el motivo real queda en ``resumen.error_imdb``.
                        resolver=False if (imdb_id or error_imdb) else resolver_imdb,
                        timeout=decision.timeout,
                    ),
                )
                self._anotar_salud(motor.nombre, exito=True)
                return motor, list(items or []), None, int((time.monotonic() - inicio) * 1000), decision
            except Exception as error:  # se reporta, nunca se silencia
                mensaje = f"{type(error).__name__}: {str(error).replace(chr(10), ' ')[:200]}"
                if self._cuenta_como_fallo(error):
                    self._anotar_salud(motor.nombre, exito=False, error=mensaje)
                return motor, [], mensaje, int((time.monotonic() - inicio) * 1000), decision

        if self.paralelo and len(aplicables) > 1:
            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(aplicables))) as pool:
                futuros = [pool.submit(ejecutar, motor) for motor in aplicables]
                for futuro in as_completed(futuros):
                    motor, items, error, ms, decision = futuro.result()
                    estados_por_nombre[motor.nombre] = self._estado(
                        motor, items, error, ms, imdb_id, decision
                    )
                    resultados.extend(items)
        else:
            for indice, motor in enumerate(aplicables):
                if indice and self.pausa[1] > 0:
                    time.sleep(random.uniform(*self.pausa))
                _, items, error, ms, decision = ejecutar(motor)
                estados_por_nombre[motor.nombre] = self._estado(motor, items, error, ms, imdb_id, decision)
                resultados.extend(items)

        # El reporte conserva el orden declarado en self.motores (paralelo incluido).
        estados: List[EstadoMotor] = [
            omitidos_por_nombre[motor.nombre]
            if motor.nombre in omitidos_por_nombre
            else estados_por_nombre[motor.nombre]
            for motor in self.motores
        ]

        brutos = len(resultados)
        unicos = self.deduplicar(resultados)
        if exigir_coincidencia and tokens:
            filtrados = [item for item in unicos if coincide_titulo(item.get("title"), tokens)]
            descartados = len(unicos) - len(filtrados)
        else:
            filtrados, descartados = unicos, 0

        resumen = ResumenBusqueda(
            consulta=query,
            consulta_original=consulta_original,
            categoria=categoria_canonica,
            min_seeders=min_seeders,
            imdb_id=imdb_id,
            error_imdb=error_imdb,
            estados=estados,
            brutos=brutos,
            unicos=len(unicos),
            descartados_relevancia=descartados,
        )
        self.ultimo_resumen = resumen
        logger.debug("búsqueda agregada: %s", resumen.formatear().replace("\n", " | "))
        return filtrados, resumen

    @staticmethod
    def _estado(
        motor: Motor,
        items: List[Dict[str, Any]],
        error: Optional[str],
        milisegundos: int,
        imdb_id: Optional[str],
        decision: Optional[Decision] = None,
    ) -> EstadoMotor:
        decision = decision or Decision()
        return EstadoMotor(
            nombre=motor.nombre,
            ok=error is None,
            resultados=len(items),
            error=error,
            milisegundos=milisegundos,
            imdb_id=imdb_id if motor.requiere_imdb else None,
            saltado_por_salud=decision.saltar,
            motivo_salud=decision.motivo,
            timeout_segundos=decision.timeout,
        )

    def buscar_en_cascada(
        self,
        query: str,
        categoria: Optional[str] = None,
        min_seeders: int = 5,
        *,
        exigir_coincidencia: bool = True,
        resolver_imdb: bool = True,
    ) -> List[Dict[str, Any]]:
        """Igual que :meth:`buscar_con_diagnostico` pero devuelve solo los items."""
        items, _ = self.buscar_con_diagnostico(
            query,
            categoria,
            min_seeders,
            exigir_coincidencia=exigir_coincidencia,
            resolver_imdb=resolver_imdb,
        )
        return items

    @staticmethod
    def deduplicar(lista_torrents: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplica por info-hash conservando el item con más sembradores.

        Cuando varias fuentes exponen el mismo release, se queda la copia con
        mejor métrica de estabilidad para no perder el magnet más sano.

        Returns:
            Lista deduplicada y ordenada por sembradores descendente.
        """
        por_hash: Dict[str, Dict[str, Any]] = {}
        sin_hash: List[Dict[str, Any]] = []

        for item in lista_torrents:
            coincidencia = PATRON_HASH.search(str(item.get("magnet", "")))
            if not coincidencia:
                sin_hash.append(item)
                continue
            clave = coincidencia.group(1).lower()
            actual = por_hash.get(clave)
            if actual is None or (item.get("seeders", 0), item.get("leechers", 0)) > (
                actual.get("seeders", 0),
                actual.get("leechers", 0),
            ):
                por_hash[clave] = item

        return _ordenar_por_estabilidad([*por_hash.values(), *sin_hash])

    def buscar_optimo(
        self,
        query: str,
        categoria: Optional[str] = None,
        min_seeders: int = 5,
        *,
        exigir_coincidencia: bool = True,
        resolver_imdb: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Devuelve el item más estable (más sembradores) o ``None``."""
        items = self.buscar_en_cascada(
            query,
            categoria,
            min_seeders,
            exigir_coincidencia=exigir_coincidencia,
            resolver_imdb=resolver_imdb,
        )
        return items[0] if items else None


#: Alias retrocompatible con el nombre usado por versiones anteriores del proyecto.
Agregador = AgregadorTorrents


#: Alias aceptados en ``--motores``/``--sin-motores`` (nombres de dominio incluidos).
ALIAS_MOTORES: Dict[str, str] = {
    "yts.gg": "yts",
    "yts.mx": "yts",
    "yts.lt": "yts",
    "yts.am": "yts",
    "limetorrents.fun": "limetorrents",
    "limetorrents.lol": "limetorrents",
    "magnetdl.com": "magnetdl",
    "eztv.re": "eztv",
    "eztvx.to": "eztv",
    "nyaa.si": "nyaa",
}


def _clave_motor(nombre: str) -> str:
    """Normaliza un nombre de motor para compararlo (sin acentos, espacios ni puntos)."""
    return normalizar(nombre).replace(" ", "")


def nombres_disponibles(motores: Sequence[Motor] = MOTORES_POR_DEFECTO) -> List[str]:
    """Nombres de motor aceptados, para mensajes de ayuda y validaciones."""
    return [motor.nombre for motor in motores]


def seleccionar_motores(
    incluidos: Optional[Sequence[str]] = None,
    excluidos: Optional[Sequence[str]] = None,
    disponibles: Sequence[Motor] = MOTORES_POR_DEFECTO,
) -> Tuple[Motor, ...]:
    """Filtra la lista de motores por nombre, para no consultar índices que no interesan.

    Acepta los nombres canónicos o los dominios (``YTS``, ``yts.gg``, ``nyaa.si``) y no
    distingue mayúsculas ni acentos. Excluir un motor caído evita esperar su timeout: es
    la diferencia entre una búsqueda de ~15 s y una de ~2-3 s.

    Args:
        incluidos: Si se indica, solo se usan estos motores.
        excluidos: Motores que no deben consultarse.
        disponibles: Catálogo de motores sobre el que filtrar.

    Returns:
        Tupla de motores en el orden original del catálogo.

    Raises:
        ValueError: Si un nombre no corresponde a ningún motor o si no queda ninguno.

    Ejemplo:
        >>> [m.nombre for m in seleccionar_motores(["yts.gg", "nyaa"])]
        ['YTS', 'Nyaa']
        >>> [m.nombre for m in seleccionar_motores(None, ["magnetdl"])]
        ['YTS', 'LimeTorrents', 'EZTV', 'Nyaa']
    """
    indice: Dict[str, Motor] = {_clave_motor(motor.nombre): motor for motor in disponibles}
    for alias, clave in ALIAS_MOTORES.items():
        if clave in indice:
            indice[_clave_motor(alias)] = indice[clave]

    def resolver(nombre: str) -> Motor:
        motor = indice.get(_clave_motor(nombre))
        if motor is None:
            raise ValueError(
                f"motor desconocido: '{nombre}'. Válidos: {', '.join(nombres_disponibles(disponibles))}"
            )
        return motor

    seleccionados: List[Motor] = list(disponibles)

    if incluidos:
        # Se compara por nombre: Motor es un dataclass con eq y por tanto no es hashable.
        resueltos = {resolver(nombre).nombre for nombre in incluidos}
        # Se respeta el orden del catálogo, no el orden en que se escribieron.
        seleccionados = [motor for motor in disponibles if motor.nombre in resueltos]

    if excluidos:
        fuera = {resolver(nombre).nombre for nombre in excluidos}
        seleccionados = [motor for motor in seleccionados if motor.nombre not in fuera]

    if not seleccionados:
        raise ValueError("la selección de motores quedó vacía: revisa --motores/--sin-motores")

    return tuple(seleccionados)


def motores_desde_texto(texto: Optional[str]) -> Optional[List[str]]:
    """Convierte ``"yts, nyaa.si"`` en ``["yts", "nyaa.si"]``; ``None`` si está vacío."""
    if not texto:
        return None
    return [parte.strip() for parte in texto.split(",") if parte.strip()] or None
