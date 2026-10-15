"""Normalización de texto y categorías compartida por los módulos de VANTAGE.

Este módulo no tiene dependencias externas: es la base común que usan
``ai_agent``, ``resolver``, ``engines`` y ``main`` para que una categoría escrita
en español ("película", "series"), en inglés ("movie", "tv") o con acentos se
resuelva siempre al mismo identificador canónico.

Categorías canónicas: ``movies``, ``tv``, ``anime``, ``music``, ``games``,
``applications``, ``books`` y ``all``.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Final, Iterable, List, Optional, Sequence

CATEGORIA_POR_DEFECTO: Final[str] = "all"

#: Alias aceptados -> categoría canónica. Las claves ya están normalizadas.
ALIAS_CATEGORIAS: Final[dict[str, str]] = {
    # Películas
    "movie": "movies",
    "movies": "movies",
    "film": "movies",
    "films": "movies",
    "cine": "movies",
    "pelicula": "movies",
    "peliculas": "movies",
    "largometraje": "movies",
    # Series / TV
    "tv": "tv",
    "tvs": "tv",
    "show": "tv",
    "shows": "tv",
    "serie": "tv",
    "series": "tv",
    "temporada": "tv",
    "temporadas": "tv",
    "tvshow": "tv",
    "tvshows": "tv",
    # Anime
    "anime": "anime",
    "animes": "anime",
    "animacion": "anime",
    "animation": "anime",
    "manga": "anime",
    # Música
    "music": "music",
    "musica": "music",
    "album": "music",
    "albumes": "music",
    "discografia": "music",
    "mp3": "music",
    "flac": "music",
    "soundtrack": "music",
    "banda sonora": "music",
    # Juegos
    "game": "games",
    "games": "games",
    "juego": "games",
    "juegos": "games",
    "videogame": "games",
    "videogames": "games",
    "gaming": "games",
    # Aplicaciones / software
    "app": "applications",
    "apps": "applications",
    "application": "applications",
    "applications": "applications",
    "software": "applications",
    "programa": "applications",
    "programas": "applications",
    "aplicacion": "applications",
    "aplicaciones": "applications",
    # Libros / cómics
    "book": "books",
    "books": "books",
    "libro": "books",
    "libros": "books",
    "ebook": "books",
    "ebooks": "books",
    "literatura": "books",
    "comic": "books",
    "comics": "books",
    "audiolibro": "books",
    "audiolibros": "books",
    # Comodines
    "all": "all",
    "any": "all",
    "general": "all",
    "todo": "all",
    "todos": "all",
    "cualquiera": "all",
    "cualquier": "all",
    "none": "all",
    "null": "all",
    "ninguna": "all",
    "sin categoria": "all",
    "unknown": "all",
    "other": "all",
    "otros": "all",
}

#: Palabras que no aportan a la coincidencia de títulos.
PALABRAS_VACIAS: Final[frozenset[str]] = frozenset(
    """
    a an the la el los las un una unos unas de del al y e o u and or of in on for to
    movie movies film films pelicula peliculas serie series show shows tv temporada
    temporadas torrent torrents torrentz download descargar descarga ver online gratis
    free full completo completa hd hq mejor best top busca buscar encuentre encontrar
    find search quiero necesito please me mi my que cual como donde año ano year
    es en ingles subtitulado castellano latino espaol espanol
    """.split()
)

#: Patrón de identificador IMDb ("tt" + dígitos).
PATRON_IMDB: Final[re.Pattern[str]] = re.compile(r"^tt\d{6,9}$")

#: Patrón de año plausible dentro de una consulta.
PATRON_ANIO: Final[re.Pattern[str]] = re.compile(r"\b(19\d{2}|20\d{2})\b")


def normalizar(texto: Optional[str]) -> str:
    """Devuelve el texto en minúsculas, sin acentos, sin puntuación y con
    espacios simples.

    >>> normalizar("Película:  Oppenheimer (2023)")
    'pelicula oppenheimer 2023'
    """
    if not texto:
        return ""
    descompuesto = unicodedata.normalize("NFKD", str(texto))
    sin_acentos = "".join(c for c in descompuesto if not unicodedata.combining(c))
    solo_alfanumerico = re.sub(r"[^a-z0-9]+", " ", sin_acentos.lower())
    return re.sub(r"\s+", " ", solo_alfanumerico).strip()


def normalizar_categoria(valor: Optional[str], por_defecto: str = CATEGORIA_POR_DEFECTO) -> str:
    """Traduce cualquier etiqueta de categoría a una categoría canónica.

    Los valores desconocidos o vacíos caen a ``por_defecto`` (``"all"``), de modo
    que una alucinación del LLM nunca rompe la búsqueda.
    """
    clave = normalizar(valor)
    if not clave:
        return por_defecto
    if clave in ALIAS_CATEGORIAS:
        return ALIAS_CATEGORIAS[clave]
    for alias, canonica in ALIAS_CATEGORIAS.items():
        if " " not in alias and alias in clave.split():
            return canonica
    return por_defecto


def es_imdb_id(texto: Optional[str]) -> bool:
    """``True`` si el texto es un identificador IMDb con formato ``ttNNNNNNN``."""
    return bool(texto) and bool(PATRON_IMDB.match(str(texto).strip().lower()))


def imdb_numerico(texto: Optional[str]) -> Optional[str]:
    """Extrae la parte numérica del IMDb id (EZTV la requiere sin el prefijo ``tt``)."""
    if not texto:
        return None
    coincidencia = re.search(r"(?:tt)?(\d{6,9})", str(texto).strip().lower())
    return coincidencia.group(1) if coincidencia else None


def extraer_anio(texto: Optional[str]) -> Optional[int]:
    """Devuelve el primer año plausible (1900-2099) encontrado en el texto."""
    if not texto:
        return None
    coincidencia = PATRON_ANIO.search(str(texto))
    return int(coincidencia.group(1)) if coincidencia else None


def tokens_significativos(texto: Optional[str], *, minimo: int = 2) -> List[str]:
    """Tokens útiles para comprobar relevancia de un título.

    Descarta palabras vacías ("movie", "la", "busca"...), años y tokens de menos
    de ``minimo`` caracteres.

    >>> tokens_significativos("Busca la película Dune 2021")
    ['dune']
    """
    return [
        token
        for token in normalizar(texto).split()
        if token not in PALABRAS_VACIAS
        and len(token) >= minimo
        and not PATRON_ANIO.fullmatch(token)
    ]


def coincide_titulo(titulo: Optional[str], tokens: Sequence[str]) -> bool:
    """``True`` si todos los ``tokens`` aparecen en el título normalizado.

    La comparación es por palabra, no por subcadena: con subcadena, la consulta
    ``"Dune"`` casaría con "The Unfathomable Sand **Dunes**" (banda sonora de
    Genshin Impact), que es justo el falso positivo que se quiere evitar.

    Tolerancias admitidas por token:

    1. Coincidencia exacta con una palabra del título.
    2. Coincidencia con dos palabras contiguas concatenadas
       (``"spiderman"`` ~ ``"Spider Man"``).
    3. Token largo (>= 6) que sea prefijo de una palabra del título o viceversa.

    Sin tokens (consulta vacía o solo palabras vacías) siempre coincide.
    """
    if not tokens:
        return True

    palabras = normalizar(titulo).split()
    if not palabras:
        return False

    bigramas = {palabras[i] + palabras[i + 1] for i in range(len(palabras) - 1)}

    for token in tokens:
        if token in palabras or token in bigramas:
            continue
        if len(token) >= 6 and any(
            palabra.startswith(token) or token.startswith(palabra)
            for palabra in palabras
            if len(palabra) >= 4
        ):
            continue
        return False
    return True


def deduplicar_preservando_orden(valores: Iterable[str]) -> List[str]:
    """Elimina duplicados manteniendo el orden de aparición (case-insensitive)."""
    vistos: set[str] = set()
    resultado: List[str] = []
    for valor in valores:
        clave = valor.lower()
        if clave not in vistos:
            vistos.add(clave)
            resultado.append(valor)
    return resultado


#: Palabras que expresan la intención o la categoría de la petición, no el título.
#: El LLM las arrastra a veces a la consulta ("película Oppenheimer") y, enviadas
#: literalmente a los índices, la búsqueda devuelve cero resultados.
PALABRAS_INTENCION: Final[frozenset[str]] = frozenset(
    """
    pelicula peliculas movie movies film films cine
    serie series show shows tv tvshow tvshows temporada temporadas
    anime animes animacion animation manga
    musica music album albumes discografia mp3 flac soundtrack
    juego juegos game games videogame videogames gaming
    app apps aplicacion aplicaciones application applications software programa programas
    libro libros book books ebook ebooks literatura comic comics audiolibro audiolibros
    torrent torrents torrentz
    busca buscar buscame busco quiero necesito descargar descarga download find
    ver online gratis completo completa
    """.split()
)

#: Artículos que sólo se eliminan si encabezan la consulta.
ARTICULOS_INICIALES: Final[frozenset[str]] = frozenset(
    {"the", "a", "an", "la", "el", "los", "las", "un", "una", "unos", "unas", "le", "les", "der", "die", "das"}
)


def limpiar_consulta(consulta: Optional[str]) -> str:
    """Quita de la consulta las palabras de intención/categoría que arrastra el LLM.

    >>> limpiar_consulta("Busca la película Oppenheimer")
    'Oppenheimer'
    >>> limpiar_consulta("The Last of Us")
    'Last of Us'

    Si al limpiar no queda ningún token significativo se devuelve la consulta
    original intacta: "The Game" no debe quedar reducida a nada.
    """
    texto = (consulta or "").strip()
    if not texto:
        return ""

    tokens = [token for token in texto.split() if normalizar(token) not in PALABRAS_INTENCION]
    if tokens and normalizar(tokens[0]) in ARTICULOS_INICIALES:
        tokens = tokens[1:]

    limpio = " ".join(tokens).strip()
    if not limpio or not tokens_significativos(limpio):
        return texto
    return limpio
