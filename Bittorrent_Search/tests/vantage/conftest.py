"""Fixtures offline para la suite de VANTAGE.

Todas las pruebas de este directorio corren **sin red**: las respuestas reales de
cada índice se guardaron en ``fixtures/`` y se sirven mediante :class:`SesionFalsa`,
que implementa el subconjunto de ``requests.Session`` que usan los motores.

Cobertura de fixtures (capturadas el 2026-10-14):

=================================  ==========================================
archivo                            origen
=================================  ==========================================
``yts_response.json``              ``https://yts.gg/api/v2/list_movies.json``
``limetorrents_search.html``       ``https://www.limetorrents.fun/search/...``
``nyaa_search.html``               ``https://nyaa.si/?q=dune``
``eztv_response.json``             ``https://eztv.re/api/get-torrents``
``imdb_suggestion.json``           ``https://v2.sg.media-imdb.com/suggestion``
=================================  ==========================================
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest
import requests

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

FIXTURES = Path(__file__).resolve().parent / "fixtures"

#: ``(fragmento de URL, archivo de fixture)`` evaluado en orden.
REGLAS_POR_DEFECTO: List[Tuple[str, str]] = [
    ("yts", "yts_response.json"),
    ("limetorrents", "limetorrents_search.html"),
    ("nyaa.si", "nyaa_search.html"),
    ("eztv", "eztv_response.json"),
    ("media-imdb.com", "imdb_suggestion.json"),
]


def cargar_texto(nombre: str) -> str:
    """Lee un fixture como texto."""
    return (FIXTURES / nombre).read_text(encoding="utf-8")


def cargar_json(nombre: str) -> Any:
    """Lee un fixture JSON."""
    return json.loads(cargar_texto(nombre))


class RespuestaFalsa:
    """Subconjunto de ``requests.Response`` que consumen los motores."""

    def __init__(
        self,
        texto: str,
        url: str,
        status_code: int = 200,
        content_type: Optional[str] = None,
    ) -> None:
        if content_type is None:
            content_type = "application/json" if texto.lstrip()[:1] in "{[" else "text/html"
        self.text = texto
        self.content = texto.encode("utf-8")
        self.url = url
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}

    def json(self) -> Any:
        return json.loads(self.text)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Client Error for url: {self.url}")


class SesionFalsa:
    """Sesión ``requests`` simulada que enruta por fragmento de URL.

    Cualquier URL sin regla lanza ``requests.ConnectionError``, que es como se
    simula un índice caído (MagnetDL con HTTP 522) o un mirror que no resuelve
    (``yts.mx``).
    """

    def __init__(
        self,
        reglas: Optional[List[Tuple[str, str]]] = None,
        *,
        fallos: Optional[List[str]] = None,
    ) -> None:
        self.reglas = list(reglas) if reglas is not None else list(REGLAS_POR_DEFECTO)
        self.fallos = list(fallos or [])
        self.llamadas: List[Dict[str, Any]] = []

    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> RespuestaFalsa:
        self.llamadas.append({"url": url, "params": dict(params or {}), "timeout": timeout})
        if any(fragmento in url for fragmento in self.fallos):
            raise requests.ConnectionError(f"host simulado como caído: {url}")
        for fragmento, archivo in self.reglas:
            if fragmento in url:
                return RespuestaFalsa(cargar_texto(archivo), url)
        raise requests.ConnectionError(f"sin ruta simulada para {url}")

    def close(self) -> None:  # compatibilidad con requests.Session
        return None


class ClienteLLMFalso:
    """Doble del cliente de Ollama."""

    def __init__(
        self,
        contenido: Optional[str] = None,
        *,
        error: Optional[Exception] = None,
        soporta_format: bool = True,
    ) -> None:
        self.contenido = contenido
        self.error = error
        self.soporta_format = soporta_format
        self.llamadas: List[Dict[str, Any]] = []

    def chat(
        self,
        model: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        stream: bool = False,
        format: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.llamadas.append({"model": model, "messages": messages, "format": format})
        if self.error is not None:
            raise self.error
        if format is not None and not self.soporta_format:
            raise TypeError("chat() got an unexpected keyword argument 'format'")
        return {"message": {"content": self.contenido or ""}}




@pytest.fixture(autouse=True)
def salud_aislada(tmp_path, monkeypatch):
    """Redirige el estado de salud a un temporal: las pruebas no deben ensuciar el real.

    Sin esto, cada motor que falle en una prueba (por ejemplo, por no tener ruta simulada)
    quedaría anotado en `.estado_motores.json` y podría degradar un índice de verdad.
    """
    import salud_motores

    monkeypatch.setattr(salud_motores, "ARCHIVO_POR_DEFECTO", tmp_path / ".estado_motores.json")
    return tmp_path / ".estado_motores.json"


@pytest.fixture
def sesion_falsa() -> SesionFalsa:
    """Sesión simulada con todas las rutas de fixture."""
    return SesionFalsa()


@pytest.fixture
def agregador_offline(sesion_falsa: SesionFalsa):
    """Agregador secuencial con la red sustituida por fixtures."""
    from engines import AgregadorTorrents

    agregador = AgregadorTorrents(paralelo=False)
    agregador.session = sesion_falsa
    return agregador


@pytest.fixture
def cliente_llm() -> ClienteLLMFalso:
    """Cliente LLM por defecto que devuelve JSON crudo válido."""
    return ClienteLLMFalso('{"query": "Oppenheimer 2023", "categoria": "movie"}')
