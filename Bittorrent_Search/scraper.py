"""Capa de compatibilidad con la interfaz histórica ``buscar_torrents``.

La implementación vive en :mod:`engines`, que añade multi-motor, rotación de
mirrors, construcción de magnets a partir del info-hash y diagnóstico por motor.
Este módulo conserva la firma original (``query``, ``categoria``, ``min_seeders``,
``base_url``) para que scripts o pruebas antiguas sigan funcionando, y delega en
el motor de Nyaa.

Para búsquedas generalistas usa directamente::

    from engines import AgregadorTorrents
    items = AgregadorTorrents().buscar_en_cascada("Oppenheimer 2023", "movies")
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from engines import BASE_URLS_NYAA, buscar_torrents_nyaa

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = BASE_URLS_NYAA[0]
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

#: Categoría -> código de categoría de Nyaa (compatibilidad con versiones previas).
CATEGORY_MAPPING: Dict[str, str] = {
    "anime": "1_0",
    "movies": "4_0",
    "music": "2_0",
    "applications": "6_0",
    "tv": "4_0",
}


def buscar_torrents(
    query: str,
    categoria: Optional[str] = None,
    min_seeders: int = 5,
    base_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Busca en Nyaa con la firma original del proyecto.

    Args:
        query: Texto de búsqueda.
        categoria: Categoría canónica o alias ("película", "movie", "anime"...).
        min_seeders: Sembradores mínimos.
        base_url: Solo se acepta el host de Nyaa (``https://nyaa.si``); cualquier
            otro valor lanza ``NotImplementedError`` porque este shim ya no
            implementa otros índices — usa :mod:`engines` para eso.

    Returns:
        Items ordenados por sembradores descendente.

    Raises:
        NotImplementedError: Si ``base_url`` apunta a un índice no soportado.
        requests.RequestException: Si la petición falla.
    """
    if base_url and "nyaa" not in base_url.lower():
        raise NotImplementedError(
            f"el shim scraper.py solo sirve Nyaa; para '{base_url}' usa engines.py "
            "(AgregadorTorrents o el motor específico)"
        )
    if base_url:
        logger.debug("base_url=%s aceptado (host de Nyaa)", base_url)

    return buscar_torrents_nyaa(query, categoria, min_seeders)
