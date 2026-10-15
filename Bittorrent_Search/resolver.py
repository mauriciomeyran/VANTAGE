"""Resolución de títulos a identificadores IMDb.

EZTV (series) y otras fuentes de solo API exigen un ``imdb_id``; el pipeline solo
recibe lenguaje natural. Este módulo cierra ese hueco usando el endpoint público
de sugerencias de IMDb (``v2.sg.media-imdb.com``), que devuelve JSON sin login ni
clave.

La selección de candidato está separada en :func:`seleccionar_candidato` para
poder probarla sin red.
"""

from __future__ import annotations

import logging
import urllib.parse
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import requests

from texto import PATRON_IMDB, es_imdb_id, extraer_anio, imdb_numerico, normalizar

logger = logging.getLogger(__name__)

URL_SUGERENCIAS_IMDB = "https://v2.sg.media-imdb.com/suggestion/{inicial}/{consulta}.json"
AGENTE_SUGERENCIAS = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
TIMEOUT_POR_DEFECTO = 10.0

#: Tipos de IMDb preferidos, en orden de prioridad, para una búsqueda audiovisual.
TIPOS_PREFERIDOS: Tuple[str, ...] = (
    "movie",
    "tvSeries",
    "tvMiniSeries",
    "tvMovie",
    "tvSpecial",
    "video",
    "short",
)

#: Preferencia para fuentes de series (EZTV): evita resolver al film homónimo.
#: Ejemplo real: "Severance" tiene un film de 2006 (tt0464196) y la serie de 2022
#: (tt11280740); sin esta preferencia se elegía el film, que no tiene torrents.
TIPOS_TV: Tuple[str, ...] = (
    "tvSeries",
    "tvMiniSeries",
    "tvMovie",
    "tvSpecial",
    "movie",
    "video",
    "short",
)

#: Preferencia para fuentes de películas.
TIPOS_PELICULA: Tuple[str, ...] = (
    "movie",
    "tvMovie",
    "video",
    "short",
    "tvSeries",
    "tvMiniSeries",
)


class ErrorResolucion(RuntimeError):
    """No fue posible resolver un identificador IMDb para el texto dado."""


def resolver_imdb_id(
    texto: str,
    anio: Optional[int] = None,
    *,
    tipos_preferidos: Sequence[str] = TIPOS_PREFERIDOS,
    timeout: float = TIMEOUT_POR_DEFECTO,
    session: Optional[requests.Session] = None,
) -> Optional[str]:
    """Resuelve ``texto`` a un IMDb id con formato ``ttNNNNNNN``.

    Args:
        texto: Título en lenguaje natural (o ya un IMDb id, que se devuelve tal cual).
        anio: Año de estreno para desambiguar remakes.
        tipos_preferidos: Prioridad de tipos IMDb.
        timeout: Timeout de la petición en segundos.
        session: Sesión ``requests`` reutilizable.

    Returns:
        El IMDb id (``"tt15398776"``) o ``None`` si no hay candidatos.

    Raises:
        ErrorResolucion: Si el endpoint no responde o devuelve JSON inválido.
    """
    if es_imdb_id(texto):
        return str(texto).strip().lower()

    consulta = normalizar(texto)
    if not consulta:
        return None

    if anio is None:
        anio = extraer_anio(texto)

    inicial = consulta[0]
    url = URL_SUGERENCIAS_IMDB.format(
        inicial=urllib.parse.quote(inicial, safe=""),
        consulta=urllib.parse.quote(consulta.replace(" ", "_"), safe=""),
    )

    try:
        respuesta = (session or requests).get(
            url, headers={"User-Agent": AGENTE_SUGERENCIAS}, timeout=timeout
        )
        respuesta.raise_for_status()
        datos = respuesta.json()
    except requests.RequestException as error:
        raise ErrorResolucion(f"fallo consultando sugerencias de IMDb: {error}") from error
    except ValueError as error:
        raise ErrorResolucion(f"respuesta de IMDb no es JSON válido: {error}") from error

    candidatos = datos.get("d") if isinstance(datos, dict) else None
    if not isinstance(candidatos, list):
        return None

    return seleccionar_candidato(candidatos, consulta, anio, tipos_preferidos)


def seleccionar_candidato(
    candidatos: Iterable[Dict[str, Any]],
    consulta: str,
    anio: Optional[int] = None,
    tipos_preferidos: Sequence[str] = TIPOS_PREFERIDOS,
) -> Optional[str]:
    """Elige el mejor candidato de la lista de sugerencias de IMDb.

    Criterios, en orden: título exacto, año coincidente, tipo preferido y
    finalmente el ``rank`` de popularidad de IMDb.

    Args:
        candidatos: Lista ``d`` de la respuesta de sugerencias.
        consulta: Título ya normalizado.
        anio: Año buscado.
        tipos_preferidos: Prioridad de tipos.

    Returns:
        IMDb id del mejor candidato o ``None``.
    """
    consulta_normalizada = normalizar(consulta)
    orden_tipos = {tipo: indice for indice, tipo in enumerate(tipos_preferidos)}
    puntuados: List[Tuple[Tuple[int, int, int, int], str]] = []

    for candidato in candidatos:
        if not isinstance(candidato, dict):
            continue
        imdb_id = str(candidato.get("id", "")).strip().lower()
        if not PATRON_IMDB.match(imdb_id):
            continue

        titulo = normalizar(candidato.get("l"))
        if not titulo:
            continue

        qid = str(candidato.get("qid") or candidato.get("q") or "").strip()
        anio_candidato = candidato.get("y")
        anio_candidato = int(anio_candidato) if isinstance(anio_candidato, (int, float)) else None

        # Menor es mejor en cada componente.
        penalizacion_titulo = 0 if titulo == consulta_normalizada else 1
        penalizacion_anio = 0 if (anio is None or anio_candidato == anio) else 1
        penalizacion_tipo = orden_tipos.get(qid, len(tipos_preferidos))
        rank = candidato.get("rank")
        rank = int(rank) if isinstance(rank, (int, float)) else 10**9

        puntuados.append(((penalizacion_titulo, penalizacion_anio, penalizacion_tipo, rank), imdb_id))

    if not puntuados:
        return None

    puntuados.sort(key=lambda par: par[0])
    mejor_puntaje, mejor_id = puntuados[0]
    logger.debug("IMDb resuelto: %s con puntaje %s", mejor_id, mejor_puntaje)
    return mejor_id


def describir_candidatos(candidatos: Iterable[Dict[str, Any]], limite: int = 5) -> List[str]:
    """Resumen legible de candidatos, útil para diagnósticos en terminal."""
    resumen: List[str] = []
    for candidato in list(candidatos)[:limite]:
        if not isinstance(candidato, dict) or not PATRON_IMDB.match(str(candidato.get("id", ""))):
            continue
        resumen.append(f"{candidato.get('l')} ({candidato.get('y') or 's/f'}) {candidato.get('id')}")
    return resumen
