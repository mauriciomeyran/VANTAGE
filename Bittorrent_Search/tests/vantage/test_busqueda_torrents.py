"""Pruebas offline de VANTAGE: normalización, LLM, motores, agregador y CLI.

Ejecutar con::

    source venv/bin/activate
    pytest tests/vantage -v
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
import re
import subprocess
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import requests

import engines
import main as modulo_main
import salud
import salud_motores
import scraper
from ai_agent import extraer_json, procesar_peticion_usuario
from conftest import RAIZ, ClienteLLMFalso, RespuestaFalsa, SesionFalsa, cargar_json, cargar_texto
from ai_agent import MODELO_POR_DEFECTO
from engines import (
    MOTORES_POR_DEFECTO,
    AgregadorTorrents,
    ErrorEstructura,
    ErrorFuenteNoDisponible,
    EstadoMotor,
    Motor,
    ResumenBusqueda,
    buscar_torrents_eztv,
    buscar_torrents_limetorrents,
    buscar_torrents_magnetdl,
    buscar_torrents_nyaa,
    buscar_torrents_yts,
    construir_magnet,
    extraer_categoria_lime,
    formatear_bytes,
)
from engines import motores_desde_texto, nombres_disponibles, seleccionar_motores
from resolver import (
    TIPOS_PELICULA,
    TIPOS_TV,
    ErrorResolucion,
    resolver_imdb_id,
    seleccionar_candidato,
)
from texto import (
    _prefijo_con_diferencia_corta,
    coincide_titulo,
    es_imdb_id,
    imdb_numerico,
    limpiar_consulta,
    normalizar,
    normalizar_categoria,
    tokens_significativos,
)

HASH_LIME = "d6e78b95225b76e200a9db223eedb7e1c8ad6e45"
RESPUESTA_LLM = '{"query": "Oppenheimer 2023", "categoria": "movies"}'


class SesionTexto(SesionFalsa):
    """Sesión simulada que devuelve siempre el mismo cuerpo."""

    def __init__(self, texto: str, status_code: int = 200) -> None:
        super().__init__(reglas=[])
        self._texto = texto
        self._status = status_code

    def get(self, url, headers=None, params=None, timeout=None) -> RespuestaFalsa:
        self.llamadas.append({"url": url, "params": dict(params or {}), "timeout": timeout})
        return RespuestaFalsa(self._texto, url, status_code=self._status)


# ---------------------------------------------------------------------------
# texto.py
# ---------------------------------------------------------------------------
class TestNormalizacion:
    def test_normalizar_quita_acentos_y_puntuacion(self) -> None:
        assert normalizar("Película:  Oppenheimer (2023)") == "pelicula oppenheimer 2023"

    def test_normalizar_vacio(self) -> None:
        assert normalizar(None) == ""
        assert normalizar("   ") == ""

    @pytest.mark.parametrize(
        ("entrada", "esperado"),
        [
            ("movie", "movies"),
            ("Movies", "movies"),
            ("película", "movies"),
            ("Peliculas", "movies"),
            ("cine", "movies"),
            ("serie", "tv"),
            ("TV Shows", "tv"),
            ("temporadas", "tv"),
            ("música", "music"),
            ("FLAC", "music"),
            ("juegos", "games"),
            ("software", "applications"),
            ("libros", "books"),
            ("anime", "anime"),
            ("", "all"),
            (None, "all"),
            ("banana", "all"),
        ],
    )
    def test_normalizar_categoria(self, entrada: Optional[str], esperado: str) -> None:
        assert normalizar_categoria(entrada) == esperado

    def test_deteccion_imdb(self) -> None:
        assert es_imdb_id("tt15398776")
        assert es_imdb_id("TT15398776")
        assert not es_imdb_id("15398776")
        assert not es_imdb_id("nm0649178")

    def test_imdb_numerico(self) -> None:
        assert imdb_numerico("tt15398776") == "15398776"
        assert imdb_numerico("11280740") == "11280740"
        assert imdb_numerico("abc") is None

    def test_tokens_significativos(self) -> None:
        assert tokens_significativos("Busca la película Dune 2021") == ["dune"]
        assert tokens_significativos("Oppenheimer 2023 torrent") == ["oppenheimer"]
        assert tokens_significativos("") == []

    def test_relevancia_por_palabra_no_por_subcadena(self) -> None:
        """El falso positivo del log original: "Dune" no debe casar con "Sand Dunes"."""
        titulo_genshin = (
            "HOYO-MiX - Genshin Impact - The Unfathomable Sand Dunes "
            "(Original Game Soundtrack) (FLAC) [24-Bit 48-kHz]"
        )
        assert not coincide_titulo(titulo_genshin, tokens_significativos("Dune"))
        assert coincide_titulo("Dune (2021) 1080p", tokens_significativos("Dune"))
        assert coincide_titulo("Hachi feat. Miku Hatsune - Duna no Wakusei - Dune (720p)", ["dune"])

    def test_relevancia_tolera_compuestos(self) -> None:
        assert coincide_titulo("Spider Man No Way Home 2021", ["spiderman"])
        assert coincide_titulo("Oppenheimer 2023 1080p", ["oppenheimer"])
        assert not coincide_titulo("Barbie 2023", ["oppenheimer"])

    def test_relevancia_sin_tokens(self) -> None:
        assert coincide_titulo("cualquier cosa", [])


# ---------------------------------------------------------------------------
# ai_agent.py
# ---------------------------------------------------------------------------
class TestExtraccionLLM:
    def test_json_crudo(self, cliente_llm: ClienteLLMFalso) -> None:
        resultado = procesar_peticion_usuario("Busca la película Oppenheimer", cliente_llm)
        assert resultado == {"query": "Oppenheimer 2023", "categoria": "movies"}

    def test_usa_format_json(self, cliente_llm: ClienteLLMFalso) -> None:
        procesar_peticion_usuario("algo", cliente_llm)
        assert cliente_llm.llamadas[0]["format"] == "json"

    def test_markdown_fence(self) -> None:
        cliente = ClienteLLMFalso('```json\n{"query": "Dune", "categoria": "movies"}\n```')
        assert procesar_peticion_usuario("Dune", cliente) == {"query": "Dune", "categoria": "movies"}

    def test_json_embebido_en_prosa(self) -> None:
        cliente = ClienteLLMFalso('Claro, aquí está:\n{"query": "Severance", "categoria": "tv"}\nEspero que ayude.')
        assert procesar_peticion_usuario("Severance", cliente) == {"query": "Severance", "categoria": "tv"}

    def test_comillas_simples(self) -> None:
        cliente = ClienteLLMFalso("{'query': 'Dune', 'categoria': 'movie'}")
        assert procesar_peticion_usuario("Dune", cliente)["categoria"] == "movies"

    def test_comas_finales(self) -> None:
        cliente = ClienteLLMFalso('{"query": "Dune", "categoria": "movies",}')
        assert procesar_peticion_usuario("Dune", cliente) == {"query": "Dune", "categoria": "movies"}

    def test_clave_con_acento(self) -> None:
        cliente = ClienteLLMFalso('{"query": "Dune", "categoría": "película"}')
        assert procesar_peticion_usuario("Dune", cliente) == {"query": "Dune", "categoria": "movies"}

    def test_categoria_ausente_cae_a_all(self) -> None:
        cliente = ClienteLLMFalso('{"query": "Dune"}')
        assert procesar_peticion_usuario("Dune", cliente) == {"query": "Dune", "categoria": "all"}

    def test_categoria_inventada_cae_a_all(self) -> None:
        cliente = ClienteLLMFalso('{"query": "Dune", "categoria": "documental espacial"}')
        assert procesar_peticion_usuario("Dune", cliente)["categoria"] == "all"

    def test_cliente_sin_soporte_de_format(self) -> None:
        cliente = ClienteLLMFalso('{"query": "Dune", "categoria": "movies"}', soporta_format=False)
        assert procesar_peticion_usuario("Dune", cliente)["query"] == "Dune"
        assert len(cliente.llamadas) == 2  # primer intento con format, repliegue sin él

    def test_salida_basura(self) -> None:
        with pytest.raises(ValueError):
            procesar_peticion_usuario("Dune", ClienteLLMFalso("no tengo idea de qué responder"))

    def test_sin_query(self) -> None:
        with pytest.raises(ValueError):
            procesar_peticion_usuario("Dune", ClienteLLMFalso('{"categoria": "movies"}'))

    def test_texto_vacio(self, cliente_llm: ClienteLLMFalso) -> None:
        with pytest.raises(ValueError):
            procesar_peticion_usuario("   ", cliente_llm)

    def test_error_del_cliente_es_connectionerror(self) -> None:
        cliente = ClienteLLMFalso(error=RuntimeError("ollama no responde"))
        with pytest.raises(ConnectionError):
            procesar_peticion_usuario("Dune", cliente)

    def test_extraer_json_sin_json(self) -> None:
        assert extraer_json("nada") is None
        assert extraer_json("") is None


# ---------------------------------------------------------------------------
# Motores
# ---------------------------------------------------------------------------
class TestMotorNyaa:
    def test_parseo_de_fixture(self, sesion_falsa: SesionFalsa) -> None:
        items = buscar_torrents_nyaa("dune", min_seeders=5, session=sesion_falsa)
        assert items, "la fixture de Nyaa debe producir resultados"
        assert all(item["seeders"] >= 5 for item in items)
        assert all(item["magnet"].startswith("magnet:?xt=urn:btih:") for item in items)
        assert all(item["title"] for item in items)
        assert all(item["source"] == "Nyaa" for item in items)
        sembradores = [item["seeders"] for item in items]
        assert sembradores == sorted(sembradores, reverse=True)

    def test_pagina_sin_resultados_no_es_error(self) -> None:
        sesion = SesionTexto("<html><body><div>No results found</div></body></html>")
        assert buscar_torrents_nyaa("oppenheimer", session=sesion) == []

    def test_estructura_inesperada_es_error(self) -> None:
        sesion = SesionFalsa(reglas=[("nyaa.si", "yts_response.json")])
        with pytest.raises(ErrorEstructura):
            buscar_torrents_nyaa("dune", session=sesion)


class TestMotorLimeTorrents:
    def test_magnet_construido_desde_hash(self, sesion_falsa: SesionFalsa) -> None:
        items = buscar_torrents_limetorrents("oppenheimer", min_seeders=5, session=sesion_falsa)
        assert len(items) >= 30
        mejor = items[0]
        assert mejor["seeders"] == 1276
        assert mejor["leechers"] == 97
        assert HASH_LIME in mejor["magnet"]
        assert mejor["title"].startswith("Oppenheimer (2023)")
        assert mejor["source"] == "LimeTorrents"
        assert "GB" in mejor["size"]
        assert all(item["seeders"] >= 5 for item in items)

    def test_filtro_de_categoria_en_cliente(self, sesion_falsa: SesionFalsa) -> None:
        """El mirror ignora la categoría de la URL: el filtro real es client-side.

        La fixture de "oppenheimer" mezcla filas de Movies, Music, TV shows y Other,
        así que filtrar por movies o music debe reducir el conjunto y separarlo.
        """
        todas = buscar_torrents_limetorrents("oppenheimer", min_seeders=5, session=sesion_falsa)
        peliculas = buscar_torrents_limetorrents("oppenheimer", "movies", session=sesion_falsa)
        musica = buscar_torrents_limetorrents("oppenheimer", "music", session=sesion_falsa)

        assert len(peliculas) < len(todas)
        assert len(musica) < len(todas)
        assert peliculas and musica
        magnets_peliculas = {item["magnet"] for item in peliculas}
        magnets_musica = {item["magnet"] for item in musica}
        assert not (magnets_peliculas & magnets_musica)

    def test_categoria_other_no_es_comodin(self, sesion_falsa: SesionFalsa) -> None:
        """Las filas "in Other" no deben colarse en un filtro de categoría concreto."""
        peliculas = buscar_torrents_limetorrents("oppenheimer", "movies", session=sesion_falsa)
        todas = buscar_torrents_limetorrents("oppenheimer", min_seeders=5, session=sesion_falsa)
        assert len(peliculas) < len(todas)

    def test_categoria_de_fila(self) -> None:
        assert extraer_categoria_lime("1 Year+ - in Movies") == "movies"
        assert extraer_categoria_lime("3 Years+ - in TV shows") == "tv"
        assert extraer_categoria_lime("2 Years+ - in Music") == "music"
        assert extraer_categoria_lime("5 Years+ - in Other") == "otros"
        assert extraer_categoria_lime("texto sin categoria") == "desconocida"

    def test_estructura_inesperada(self) -> None:
        sesion = SesionFalsa(reglas=[("limetorrents", "yts_response.json")])
        with pytest.raises(ErrorEstructura):
            buscar_torrents_limetorrents("oppenheimer", session=sesion)

    def test_paginacion_por_defecto_compatible(self, sesion_falsa: SesionFalsa) -> None:
        """paginas=1 (por defecto) debe conservar el comportamiento actual."""
        items = buscar_torrents_limetorrents("oppenheimer", min_seeders=5, session=sesion_falsa)
        assert len(items) >= 30
        assert all(item["seeders"] >= 5 for item in items)

    def test_paginacion_varias_paginas(self) -> None:
        """paginas=3 debe consultar páginas 1, 2 y 3, combinar resultados con hashes distintos y deduplicar."""
        fixture_base = cargar_texto("limetorrents_search.html")
        # Cambiar hashes para simular resultados distintos en cada página
        fixture_pag2 = fixture_base.replace("D6E78B95225B76E200A9DB223EEDB7E1C8AD6E45", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        fixture_pag3 = fixture_base.replace("D6E78B95225B76E200A9DB223EEDB7E1C8AD6E45", "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB")

        rutas_consultadas = []

        def mock_paginas(url, headers=None, params=None, timeout=None):
            rutas_consultadas.append(url)
            if "/seeds/1/" in url:
                return RespuestaFalsa(fixture_base, url)
            elif "/seeds/2/" in url:
                return RespuestaFalsa(fixture_pag2, url)
            elif "/seeds/3/" in url:
                return RespuestaFalsa(fixture_pag3, url)
            return RespuestaFalsa("<html><body>No results</body></html>", url)

        sesion = SesionFalsa(reglas=[])
        sesion.get = mock_paginas

        items = buscar_torrents_limetorrents("oppenheimer", paginas=3, session=sesion)

        # Verificar que se consultaron las 3 rutas correctas
        assert len(rutas_consultadas) == 3
        assert any("/seeds/1/" in r for r in rutas_consultadas)
        assert any("/seeds/2/" in r for r in rutas_consultadas)
        assert any("/seeds/3/" in r for r in rutas_consultadas)

        # Verificar que los resultados incluyen magnets de las 3 páginas
        magnets = [item["magnet"] for item in items]
        assert any("d6e78b95225b76e200a9db223eedb7e1c8ad6e45" in m for m in magnets), "debe incluir hash de página 1"
        assert any("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" in m for m in magnets), "debe incluir hash de página 2"
        assert any("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" in m for m in magnets), "debe incluir hash de página 3"

        # Verificar que no hay duplicados
        assert len(magnets) == len(set(magnets)), "los magnets deben ser únicos"

    def test_paginacion_deduplica_magnets(self) -> None:
        """Los magnets repetidos entre páginas deben deduplicarse."""
        fixture = cargar_texto("limetorrents_search.html")

        def pagina_repetida(url, headers=None, params=None, timeout=None):
            return RespuestaFalsa(fixture, url)

        sesion = SesionFalsa(reglas=[])
        sesion.get = pagina_repetida

        items = buscar_torrents_limetorrents("oppenheimer", paginas=2, session=sesion)
        magnets = [item["magnet"] for item in items]
        assert len(magnets) == len(set(magnets)), "los magnets deben ser únicos"

    def test_paginacion_termina_en_pagina_vacia(self) -> None:
        """Si una página posterior está vacía, debe terminar y devolver resultados acumulados."""
        contador = {"paginas": 0}

        def paginas_con_vacia(url, headers=None, params=None, timeout=None):
            contador["paginas"] += 1
            if "/seeds/1/" in url:
                return RespuestaFalsa(cargar_texto("limetorrents_search.html"), url)
            elif "/seeds/2/" in url:
                return RespuestaFalsa("<html><body>No results found</body></html>", url)
            return RespuestaFalsa("<html><body>No results</body></html>", url)

        sesion = SesionFalsa(reglas=[])
        sesion.get = paginas_con_vacia

        items = buscar_torrents_limetorrents("oppenheimer", paginas=5, session=sesion)
        assert contador["paginas"] == 2, "debe detenerse en la página 2 (vacía)"
        assert len(items) >= 30, "debe devolver resultados de la página 1"

    def test_paginacion_primera_pagina_vacia(self) -> None:
        """Si la primera página está vacía, debe devolver lista vacía."""
        sesion = SesionTexto("<html><body>No results found</body></html>")
        items = buscar_torrents_limetorrents("oppenheimer", paginas=3, session=sesion)
        assert items == []

    def test_paginacion_rechaza_cero(self) -> None:
        with pytest.raises(ValueError, match="entero positivo"):
            buscar_torrents_limetorrents("oppenheimer", paginas=0)

    def test_paginacion_rechaza_negativo(self) -> None:
        with pytest.raises(ValueError, match="entero positivo"):
            buscar_torrents_limetorrents("oppenheimer", paginas=-1)

    def test_paginacion_rechaza_booleano(self) -> None:
        with pytest.raises(ValueError, match="entero positivo"):
            buscar_torrents_limetorrents("oppenheimer", paginas=True)
        with pytest.raises(ValueError, match="entero positivo"):
            buscar_torrents_limetorrents("oppenheimer", paginas=False)

    def test_paginacion_rechaza_no_entero(self) -> None:
        with pytest.raises(ValueError, match="entero positivo"):
            buscar_torrents_limetorrents("oppenheimer", paginas="3")
        with pytest.raises(ValueError, match="entero positivo"):
            buscar_torrents_limetorrents("oppenheimer", paginas=3.5)

    def test_paginacion_propaga_error_estructura(self) -> None:
        """Los errores de estructura deben propagarse, no ocultarse."""
        sesion = SesionFalsa(reglas=[("limetorrents", "yts_response.json")])
        with pytest.raises(ErrorEstructura):
            buscar_torrents_limetorrents("oppenheimer", paginas=2, session=sesion)

    def test_paginacion_propaga_error_fuente(self) -> None:
        """Los errores de fuente no disponible deben propagarse."""
        sesion = SesionFalsa(fallos=["limetorrents"])
        with pytest.raises(ErrorFuenteNoDisponible):
            buscar_torrents_limetorrents("oppenheimer", paginas=2, session=sesion)


class TestMotorYTS:
    def test_items_y_orden(self, sesion_falsa: SesionFalsa) -> None:
        items = buscar_torrents_yts("Oppenheimer", min_seeders=5, session=sesion_falsa)
        assert items
        mejor = items[0]
        assert mejor["seeders"] == 100
        assert mejor["leechers"] == 74
        assert "[1080p]" in mejor["title"]
        assert mejor["title"].endswith("[YTS]")
        assert mejor["source"] == "YTS"
        assert all(item["seeders"] >= 5 for item in items)
        sembradores = [item["seeders"] for item in items]
        assert sembradores == sorted(sembradores, reverse=True)

    def test_rotacion_de_mirrors(self) -> None:
        """Si yts.gg y yts.mx fallan, el motor sigue con yts.lt."""
        sesion = SesionFalsa(reglas=[("yts", "yts_response.json")], fallos=["yts.gg", "yts.mx"])
        items = buscar_torrents_yts("Oppenheimer", session=sesion)
        assert items
        urls = [llamada["url"] for llamada in sesion.llamadas]
        assert any("yts.gg" in url for url in urls)
        assert any("yts.lt" in url for url in urls)

    def test_todos_los_mirrors_caidos(self) -> None:
        sesion = SesionFalsa(fallos=["yts"])
        with pytest.raises(ErrorFuenteNoDisponible) as error:
            buscar_torrents_yts("Oppenheimer", session=sesion)
        assert "yts.gg" in str(error.value)

    def test_mirror_que_devuelve_html_es_descartado(self) -> None:
        """Un 200 con página de error no debe pasar el validador de JSON."""
        sesion = SesionFalsa(reglas=[("yts", "nyaa_search.html")])
        with pytest.raises(ErrorFuenteNoDisponible):
            buscar_torrents_yts("Oppenheimer", session=sesion)


class TestMotorEZTV:
    def test_con_imdb_id(self, sesion_falsa: SesionFalsa) -> None:
        items = buscar_torrents_eztv("Severance", imdb_id="tt11280740", session=sesion_falsa)
        assert len(items) == 5
        assert items[0]["seeders"] == 100
        assert items[0]["leechers"] == 38
        assert items[0]["size"] == "6.4 GB"
        assert items[0]["source"] == "EZTV"

    def test_umbral_de_sembradores(self, sesion_falsa: SesionFalsa) -> None:
        # La fixture tiene seeds 100, 54, 31, 16 y 9: con min_seeders=50 quedan dos.
        items = buscar_torrents_eztv("Severance", min_seeders=50, imdb_id="11280740", session=sesion_falsa)
        assert len(items) == 2
        assert [item["seeders"] for item in items] == [100, 54]

    def test_sin_imdb_y_sin_resolucion(self, sesion_falsa: SesionFalsa) -> None:
        with pytest.raises(ErrorResolucion):
            buscar_torrents_eztv("Severance", resolver=False, session=sesion_falsa)

    def test_cero_torrents_no_es_error(self) -> None:
        sesion = SesionTexto('{"imdb_id":"1","torrents_count":0,"limit":5,"page":1,"torrents":[]}')
        assert buscar_torrents_eztv("Oppenheimer", imdb_id="tt15398776", session=sesion) == []

    def test_usa_preferencia_tv_al_resolver(self, monkeypatch: pytest.MonkeyPatch, sesion_falsa: SesionFalsa) -> None:
        capturado: Dict[str, Any] = {}

        def resolver_falso(texto: str, anio=None, **kwargs: Any) -> str:
            capturado.update(kwargs)
            capturado["texto"] = texto
            return "tt11280740"

        monkeypatch.setattr(engines, "resolver_imdb_id", resolver_falso)
        items = buscar_torrents_eztv("Severance", session=sesion_falsa)
        assert capturado["tipos_preferidos"] == TIPOS_TV
        assert items


class TestMotorMagnetDL:
    def test_origen_caido_reporta_el_motivo(self, sesion_falsa: SesionFalsa) -> None:
        with pytest.raises(ErrorFuenteNoDisponible) as error:
            buscar_torrents_magnetdl("oppenheimer", session=sesion_falsa)
        assert "magnetdl.com" in str(error.value)


# ---------------------------------------------------------------------------
# Agregador
# ---------------------------------------------------------------------------
class TestAgregador:
    @staticmethod
    def _item(titulo: str, hash_: str, seeders: int, leechers: int = 1, fuente: str = "X") -> Dict[str, Any]:
        return {
            "title": titulo,
            "magnet": construir_magnet(hash_, titulo),
            "seeders": seeders,
            "leechers": leechers,
            "size": "1 GB",
            "source": fuente,
        }

    def test_deduplicacion_por_hash_conserva_el_mejor(self) -> None:
        hash_ = "a" * 40
        items = [self._item("Release", hash_, 10), self._item("Release", hash_, 90)]
        unicos = AgregadorTorrents.deduplicar(items)
        assert len(unicos) == 1
        assert unicos[0]["seeders"] == 90

    def test_deduplicacion_sin_hash_conserva_todo(self) -> None:
        items = [
            {"title": "A", "magnet": "magnet:?xt=urn:btih:invalido", "seeders": 5, "leechers": 1},
            {"title": "B", "magnet": "", "seeders": 4, "leechers": 1},
        ]
        assert len(AgregadorTorrents.deduplicar(items)) == 2

    def test_busqueda_movies_con_diagnostico(self) -> None:
        sesion = SesionFalsa(reglas=[("yts", "yts_response.json"), ("limetorrents", "limetorrents_search.html")])
        agregador = AgregadorTorrents(paralelo=False)
        agregador.session = sesion

        items, resumen = agregador.buscar_con_diagnostico("Oppenheimer 2023", "movies", min_seeders=5)

        assert items
        assert all(item["seeders"] >= 5 for item in items)
        assert all("oppenheimer" in normalizar(item["title"]) for item in items)
        sembradores = [item["seeders"] for item in items]
        assert sembradores == sorted(sembradores, reverse=True)

        # El reporte conserva el orden declarado de motores.
        assert [estado.nombre for estado in resumen.estados] == [
            "YTS",
            "LimeTorrents",
            "MagnetDL",
            "EZTV",
            "Nyaa",
        ]
        por_nombre = {estado.nombre: estado for estado in resumen.estados}
        assert por_nombre["YTS"].ok and por_nombre["YTS"].resultados > 0
        assert por_nombre["LimeTorrents"].ok and por_nombre["LimeTorrents"].resultados > 0
        assert not por_nombre["MagnetDL"].ok and "ErrorFuenteNoDisponible" in (por_nombre["MagnetDL"].error or "")
        assert not por_nombre["Nyaa"].ok
        assert por_nombre["EZTV"].omitido and "movies" in (por_nombre["EZTV"].error or "")
        assert resumen.brutos == resumen.unicos + 0 or resumen.unicos <= resumen.brutos
        assert resumen.motores_fallidos and resumen.motores_ok

    def test_no_gasta_peticion_imdb_si_ningun_motor_aplicable_la_exige(self) -> None:
        sesion = SesionFalsa(reglas=[("limetorrents", "limetorrents_search.html")])
        agregador = AgregadorTorrents(paralelo=False)
        agregador.session = sesion
        _, resumen = agregador.buscar_con_diagnostico("oppenheimer", "music", min_seeders=1)
        assert resumen.imdb_id is None
        assert all("media-imdb" not in llamada["url"] for llamada in sesion.llamadas)

    def test_filtro_de_relevancia_descarta_falsos_positivos(self) -> None:
        titulo = "HOYO-MiX - Genshin Impact - The Unfathomable Sand Dunes (Original Game Soundtrack) (FLAC)"
        items = [self._item(titulo, "b" * 40, 17, fuente="Nyaa")]
        agregador = AgregadorTorrents(
            motores=[Motor("Falso", lambda query, categoria=None, min_seeders=5, **_: items)],
            paralelo=False,
        )

        filtrados, resumen = agregador.buscar_con_diagnostico("Dune", "all", 5)
        assert filtrados == []
        assert resumen.descartados_relevancia == 1

        sin_filtro, _ = agregador.buscar_con_diagnostico("Dune", "all", 5, exigir_coincidencia=False)
        assert len(sin_filtro) == 1

    def test_buscar_optimo_elige_el_de_mas_sembradores(self) -> None:
        items = [self._item("Uno", "c" * 40, 3), self._item("Dos", "d" * 40, 80)]
        agregador = AgregadorTorrents(
            motores=[Motor("Falso", lambda query, categoria=None, min_seeders=5, **_: items)],
            paralelo=False,
        )
        optimo = agregador.buscar_optimo("Dos", "all", 1)
        assert optimo is not None and optimo["seeders"] == 80

    def test_paralelo_y_secuencial_dan_lo_mismo(self) -> None:
        reglas = [("yts", "yts_response.json"), ("limetorrents", "limetorrents_search.html")]
        secuencial = AgregadorTorrents(paralelo=False)
        secuencial.session = SesionFalsa(reglas=reglas)
        paralelo = AgregadorTorrents(paralelo=True, max_workers=3)
        paralelo.session = SesionFalsa(reglas=reglas)

        items_sec, _ = secuencial.buscar_con_diagnostico("Oppenheimer 2023", "movies", 5)
        items_par, resumen_par = paralelo.buscar_con_diagnostico("Oppenheimer 2023", "movies", 5)

        assert [item["magnet"] for item in items_sec] == [item["magnet"] for item in items_par]
        # El orden del reporte es estable aunque la ejecución sea concurrente.
        assert [estado.nombre for estado in resumen_par.estados] == [
            "YTS",
            "LimeTorrents",
            "MagnetDL",
            "EZTV",
            "Nyaa",
        ]

    def test_reporte_legible(self) -> None:
        resumen = ResumenBusqueda(
            consulta="dune",
            categoria="all",
            min_seeders=5,
            estados=[EstadoMotor(nombre="YTS", ok=False, error="ErrorFuenteNoDisponible: caído")],
        )
        texto = resumen.formatear()
        assert "consulta='dune'" in texto
        assert "[FALLO]" in texto and "YTS" in texto


# ---------------------------------------------------------------------------
# resolver.py
# ---------------------------------------------------------------------------
class TestResolver:
    def test_selecciona_el_titulo_exacto_con_anio(self) -> None:
        candidatos = cargar_json("imdb_suggestion.json")["d"]
        assert seleccionar_candidato(candidatos, "oppenheimer", 2023) == "tt15398776"

    def test_preferencia_tv_evita_el_film_homonimo(self) -> None:
        candidatos = [
            {"id": "tt0464196", "l": "Severance", "y": 2006, "qid": "movie", "rank": 5000},
            {"id": "tt11280740", "l": "Severance", "y": 2022, "qid": "tvSeries", "rank": 900},
        ]
        assert seleccionar_candidato(candidatos, "severance", None, TIPOS_TV) == "tt11280740"
        assert seleccionar_candidato(candidatos, "severance", 2022, TIPOS_TV) == "tt11280740"
        assert seleccionar_candidato(candidatos, "severance", None, TIPOS_PELICULA) == "tt0464196"
        assert seleccionar_candidato(candidatos, "severance", 2006, TIPOS_TV) == "tt0464196"

    def test_ignora_ids_que_no_son_de_titulo(self) -> None:
        candidatos = [{"id": "nm0649178", "l": "Alan Oppenheimer", "rank": 1}]
        assert seleccionar_candidato(candidatos, "oppenheimer") is None

    def test_imdb_id_se_devuelve_sin_red(self) -> None:
        sesion = SesionFalsa(fallos=["media-imdb"])
        assert resolver_imdb_id("tt15398776", session=sesion) == "tt15398776"
        assert sesion.llamadas == []

    def test_fallo_del_endpoint(self) -> None:
        with pytest.raises(ErrorResolucion):
            resolver_imdb_id("oppenheimer", session=SesionFalsa(fallos=["media-imdb"]))

    def test_json_invalido(self) -> None:
        with pytest.raises(ErrorResolucion):
            resolver_imdb_id("oppenheimer", session=SesionTexto("<html>error</html>"))

    def test_resolucion_real_contra_fixture(self) -> None:
        sesion = SesionFalsa(reglas=[("media-imdb", "imdb_suggestion.json")])
        assert resolver_imdb_id("Oppenheimer", session=sesion) == "tt15398776"


# ---------------------------------------------------------------------------
# scraper.py (shim de compatibilidad)
# ---------------------------------------------------------------------------
class TestShimScraper:
    def test_rechaza_indices_no_soportados(self) -> None:
        with pytest.raises(NotImplementedError):
            scraper.buscar_torrents("dune", base_url="https://1337x.to")

    def test_delega_en_el_motor_nyaa(self, monkeypatch: pytest.MonkeyPatch) -> None:
        capturado: Dict[str, Any] = {}

        def falso(query: str, categoria=None, min_seeders: int = 5, **kwargs: Any) -> List[Dict[str, Any]]:
            capturado.update({"query": query, "categoria": categoria, "min_seeders": min_seeders})
            return [{"title": "x", "magnet": "magnet:?xt=urn:btih:" + "e" * 40, "seeders": 9, "leechers": 1}]

        monkeypatch.setattr(scraper, "buscar_torrents_nyaa", falso)
        items = scraper.buscar_torrents("dune", "movies", 3)
        assert capturado == {"query": "dune", "categoria": "movies", "min_seeders": 3}
        assert items[0]["seeders"] == 9


# ---------------------------------------------------------------------------
# main.py (CLI)
# ---------------------------------------------------------------------------
class AgregadorFalso:
    """Agregador inyectable que devuelve items y resumen prefijados."""

    items: List[Dict[str, Any]] = []
    resumen: Optional[ResumenBusqueda] = None
    llamadas: List[Dict[str, Any]] = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.__class__.llamadas.append({"args": args, "kwargs": kwargs})

    def cerrar(self) -> None:
        """El orquestador cierra el agregador al terminar (BH-017); aquí no hay nada que cerrar."""
        return None

    def buscar_con_diagnostico(self, query: str, categoria=None, min_seeders: int = 5, **kwargs: Any):
        self.__class__.llamadas.append({"query": query, "categoria": categoria, "min_seeders": min_seeders, **kwargs})
        return list(self.__class__.items), self.__class__.resumen


ITEM_EJEMPLO = {
    "title": "Oppenheimer (2023) [1080p] [bluray] [YTS]",
    "magnet": "magnet:?xt=urn:btih:" + "f" * 40,
    "seeders": 100,
    "leechers": 74,
    "size": "3.33 GB",
    "source": "YTS",
}


def _resumen(items: int = 1, fallos: bool = False) -> ResumenBusqueda:
    estados = [EstadoMotor(nombre="YTS", ok=True, resultados=items, milisegundos=120)]
    if fallos:
        estados = [EstadoMotor(nombre="YTS", ok=False, error="ErrorFuenteNoDisponible: caído")]
    return ResumenBusqueda(consulta="Oppenheimer 2023", categoria="movies", min_seeders=5, estados=estados)


class TestMainCLI:
    def test_formatear_item(self) -> None:
        texto = modulo_main.formatear_item(ITEM_EJEMPLO)
        assert "Title:" in texto and "Magnet:" in texto and "Source:" in texto
        assert "Oppenheimer" in texto

    def test_parser_por_defecto(self) -> None:
        args = modulo_main.construir_parser().parse_args(["Oppenheimer"])
        assert args.all == 1
        assert args.min_seeders == 5
        assert args.model == MODELO_POR_DEFECTO
        assert args.consulta == ["Oppenheimer"]
        assert args.limetorrents_paginas == 1

    def test_limetorrents_paginas_valor_explicito(self) -> None:
        args = modulo_main.construir_parser().parse_args(["Oppenheimer", "--limetorrents-paginas", "3"])
        assert args.limetorrents_paginas == 3

    def test_limetorrents_paginas_valor_invalido(self) -> None:
        with pytest.raises(SystemExit) as salida:
            modulo_main.main(["Oppenheimer", "--limetorrents-paginas", "0"])
        assert salida.value.code == modulo_main.EXIT_USO

    def test_limetorrents_paginas_llega_al_agregador(self, monkeypatch: pytest.MonkeyPatch) -> None:
        capturado: Dict[str, Any] = {}

        class Capturador(AgregadorFalso):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                capturado.update(kwargs)
                super().__init__(*args, **kwargs)

        AgregadorFalso.items = [ITEM_EJEMPLO]
        AgregadorFalso.resumen = _resumen()
        monkeypatch.setattr(modulo_main, "conectar_llm", lambda host: ClienteLLMFalso(RESPUESTA_LLM))
        monkeypatch.setattr(modulo_main, "AgregadorTorrents", Capturador)

        modulo_main.main(["Oppenheimer 2023", "--limetorrents-paginas", "5"])

        assert capturado["limetorrents_paginas"] == 5

    def test_limetorrents_paginas_llega_al_motor(self, sesion_falsa: SesionFalsa, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verifica que el valor de paginas llega al motor LimeTorrents."""
        kwargs_capturados = []

        def mock_buscar(query, categoria=None, min_seeders=5, paginas=1, **kwargs):
            kwargs_capturados.append({"paginas": paginas, "other_kwargs": kwargs})
            return []

        # Crear un motor falso que use el mock, soportando todas las categorías
        motor_falso = Motor("LimeTorrents", mock_buscar, ("all", "movies", "tv", "anime", "music", "games", "applications", "books"))

        agregador = AgregadorTorrents(motores=[motor_falso], limetorrents_paginas=3)
        agregador.session = sesion_falsa
        agregador.buscar_con_diagnostico("oppenheimer", "movies", 5)

        assert len(kwargs_capturados) > 0
        assert kwargs_capturados[0]["paginas"] == 3

    def test_limetorrents_paginas_no_afecta_otros_motores(self, sesion_falsa: SesionFalsa) -> None:
        """Verifica que los demás motores no reciben el parámetro paginas."""
        llamadas_yts = []

        def mock_yts(query, categoria=None, min_seeders=5, **kwargs):
            llamadas_yts.append(kwargs)
            return []

        # Crear un motor YTS falso
        motor_yts = Motor("YTS", mock_yts, ("movies",))

        agregador = AgregadorTorrents(motores=[motor_yts], limetorrents_paginas=5)
        agregador.session = sesion_falsa
        agregador.buscar_con_diagnostico("oppenheimer", "movies", 5)

        assert len(llamadas_yts) > 0
        assert "paginas" not in llamadas_yts[0], "YTS no debe recibir el parámetro paginas"

    def test_flujo_completo_offline(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
        AgregadorFalso.items = [ITEM_EJEMPLO]
        AgregadorFalso.resumen = _resumen()
        monkeypatch.setattr(modulo_main, "conectar_llm", lambda host: ClienteLLMFalso(RESPUESTA_LLM))
        monkeypatch.setattr(modulo_main, "AgregadorTorrents", AgregadorFalso)

        codigo = modulo_main.main(["Oppenheimer 2023"])

        assert codigo == modulo_main.EXIT_OK
        salida = capsys.readouterr().out
        assert "Title:" in salida and "magnet:" in salida

    def test_salida_json(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
        AgregadorFalso.items = [ITEM_EJEMPLO]
        AgregadorFalso.resumen = _resumen()
        monkeypatch.setattr(modulo_main, "conectar_llm", lambda host: ClienteLLMFalso(RESPUESTA_LLM))
        monkeypatch.setattr(modulo_main, "AgregadorTorrents", AgregadorFalso)

        codigo = modulo_main.main(["Oppenheimer 2023", "--json"])
        datos = json.loads(capsys.readouterr().out)

        assert codigo == modulo_main.EXIT_OK
        assert datos["mejor"]["source"] == "YTS"
        assert datos["consulta"]["categoria"] == "movies"
        assert datos["diagnostico"]["motores"][0]["nombre"] == "YTS"

    def test_sin_resultados_devuelve_2_y_explica(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        AgregadorFalso.items = []
        AgregadorFalso.resumen = _resumen(items=0)
        monkeypatch.setattr(modulo_main, "conectar_llm", lambda host: ClienteLLMFalso(RESPUESTA_LLM))
        monkeypatch.setattr(modulo_main, "AgregadorTorrents", AgregadorFalso)

        codigo = modulo_main.main(["Oppenheimer 2023"])

        assert codigo == modulo_main.EXIT_SIN_RESULTADOS
        error = capsys.readouterr().err
        assert "No results found" in error
        assert "consulta='Oppenheimer 2023'" in error  # el diagnóstico se imprime

    def test_todos_los_motores_caidos_devuelve_4(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        AgregadorFalso.items = []
        AgregadorFalso.resumen = _resumen(items=0, fallos=True)
        monkeypatch.setattr(modulo_main, "conectar_llm", lambda host: ClienteLLMFalso(RESPUESTA_LLM))
        monkeypatch.setattr(modulo_main, "AgregadorTorrents", AgregadorFalso)

        codigo = modulo_main.main(["Oppenheimer 2023"])

        assert codigo == modulo_main.EXIT_MOTORES_CAIDOS
        assert "[FALLO]" in capsys.readouterr().err

    def test_fallo_de_ollama(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
        def falla(host: str) -> Any:
            raise ConnectionError("no hay servicio")

        monkeypatch.setattr(modulo_main, "conectar_llm", falla)
        codigo = modulo_main.main(["Oppenheimer"])
        assert codigo == modulo_main.EXIT_ERROR_LLM
        assert "Ollama" in capsys.readouterr().err

    def test_all_muestra_varios(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
        segundo = dict(ITEM_EJEMPLO, seeders=50, title="Oppenheimer (2023) [720p] [YTS]")
        AgregadorFalso.items = [ITEM_EJEMPLO, segundo]
        AgregadorFalso.resumen = _resumen(items=2)
        monkeypatch.setattr(modulo_main, "conectar_llm", lambda host: ClienteLLMFalso(RESPUESTA_LLM))
        monkeypatch.setattr(modulo_main, "AgregadorTorrents", AgregadorFalso)

        codigo = modulo_main.main(["Oppenheimer 2023", "-n", "2", "--verbose"])
        salida = capsys.readouterr().out

        assert codigo == modulo_main.EXIT_OK
        assert "Resultado #1" in salida and "Resultado #2" in salida
        assert "[OK]" in salida


# ---------------------------------------------------------------------------
# Utilidades varias
# ---------------------------------------------------------------------------
class TestUtilidades:
    def test_formatear_bytes(self) -> None:
        assert formatear_bytes(6871947674) == "6.4 GB"
        assert formatear_bytes(1536) == "1.5 KB"
        assert formatear_bytes(None) == "N/A"
        assert formatear_bytes("basura") == "N/A"
        assert formatear_bytes(0) == "N/A"

    def test_construir_magnet_incluye_trackers_y_dn(self) -> None:
        magnet = construir_magnet("D6E78B95225B76E200A9DB223EEDB7E1C8AD6E45", "Oppenheimer (2023)")
        assert magnet.startswith("magnet:?xt=urn:btih:d6e78b95225b76e200a9db223eedb7e1c8ad6e45")
        assert "dn=Oppenheimer%20%282023%29" in magnet
        assert "&tr=" in magnet

    def test_construir_magnet_sin_hash(self) -> None:
        with pytest.raises(ValueError):
            construir_magnet("")


class TestSeleccionMotores:
    def test_por_nombre_y_por_dominio(self) -> None:
        assert [m.nombre for m in seleccionar_motores(["yts.gg", "nyaa"])] == ["YTS", "Nyaa"]
        assert [m.nombre for m in seleccionar_motores(["LIMETORRENTS.FUN"])] == ["LimeTorrents"]
        assert [m.nombre for m in seleccionar_motores(["eztv.re"])] == ["EZTV"]

    def test_respeta_el_orden_del_catalogo(self) -> None:
        """Se piden al revés y deben devolverse en el orden del catálogo."""
        assert [m.nombre for m in seleccionar_motores(["nyaa", "yts"])] == ["YTS", "Nyaa"]

    def test_excluir_motores(self) -> None:
        sin_magnetdl = [m.nombre for m in seleccionar_motores(None, ["magnetdl"])]
        assert "MagnetDL" not in sin_magnetdl and len(sin_magnetdl) == len(MOTORES_POR_DEFECTO) - 1
        assert [m.nombre for m in seleccionar_motores(["yts", "nyaa"], ["nyaa"])] == ["YTS"]

    def test_motor_desconocido_da_la_lista_de_validos(self) -> None:
        with pytest.raises(ValueError) as error:
            seleccionar_motores(["noexiste"])
        mensaje = str(error.value)
        assert "noexiste" in mensaje
        assert "YTS" in mensaje and "Nyaa" in mensaje

    def test_seleccion_vacia_es_error(self) -> None:
        with pytest.raises(ValueError):
            seleccionar_motores(["yts"], ["yts"])

    def test_nombres_disponibles(self) -> None:
        assert nombres_disponibles() == ["YTS", "LimeTorrents", "MagnetDL", "EZTV", "Nyaa"]

    @pytest.mark.parametrize(
        ("entrada", "esperado"),
        [
            ("yts, nyaa.si", ["yts", "nyaa.si"]),
            ("  yts  ", ["yts"]),
            ("yts,,nyaa", ["yts", "nyaa"]),
            ("", None),
            (None, None),
            (" , ", None),
        ],
    )
    def test_motores_desde_texto(self, entrada: Optional[str], esperado: Optional[List[str]]) -> None:
        assert motores_desde_texto(entrada) == esperado


class TestSalud:
    def test_ollama_y_modelo_disponibles(self) -> None:
        sesion = SesionTexto('{"models": [{"name": "qwen2.5:7b"}, {"name": "nomic-embed-text:latest"}]}')
        comprobaciones = salud.comprobar_ollama("http://localhost:11434", "qwen2.5:7b", session=sesion)
        assert [c["ok"] for c in comprobaciones] == [True, True]

    def test_modelo_sin_descargar(self) -> None:
        sesion = SesionTexto('{"models": [{"name": "otro:1b"}]}')
        comprobaciones = salud.comprobar_ollama(modelo="qwen2.5:7b", session=sesion)
        assert comprobaciones[0]["ok"] is True
        assert comprobaciones[1]["ok"] is False
        assert "ollama pull" in comprobaciones[1]["detalle"]

    def test_servicio_caido(self) -> None:
        comprobaciones = salud.comprobar_ollama(session=SesionFalsa(fallos=["11434"]))
        assert comprobaciones[0]["ok"] is False
        assert "ollama serve" in comprobaciones[0]["detalle"]
        assert comprobaciones[1]["ok"] is False

    def test_dependencias_faltantes(self) -> None:
        def importador(nombre: str) -> Any:
            if nombre == "bs4":
                raise ImportError("simulado")
            return importlib.import_module(nombre)

        comprobacion = salud.comprobar_dependencias(importador)
        assert comprobacion["ok"] is False
        assert "bs4" in comprobacion["detalle"]

    def test_informe_completo_y_formato(self) -> None:
        sesion = SesionTexto('{"models": [{"name": "qwen2.5:7b"}]}')
        datos = salud.informe(session=sesion)
        assert datos["ok"] is True
        assert len(datos["checks"]) == 5
        assert "OK" in salud.formatear(datos)

    def test_main_sale_con_65_si_algo_falla(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
        monkeypatch.setattr(
            salud, "informe",
            lambda **_: {"ok": False, "raiz": ".", "host": "h", "modelo": "m",
                         "checks": [{"nombre": "ollama", "ok": False, "detalle": "caído"}]},
        )
        assert salud.main(["--json"]) == salud.EXIT_FALLO
        assert json.loads(capsys.readouterr().out)["ok"] is False


class TestWrapperVantageSearch:
    """El wrapper es el punto de entrada que usará la app de escritorio."""

    @staticmethod
    def _ruta() -> Path:
        ruta = RAIZ / "scripts" / "vantage-search"
        if not ruta.exists():
            pytest.skip("wrapper no desplegado")
        return ruta

    def test_ayuda(self) -> None:
        proceso = subprocess.run([str(self._ruta()), "--help"], capture_output=True, text=True, timeout=30)
        assert proceso.returncode == 0
        assert "vantage-search" in proceso.stdout

    def test_interprete_ausente_devuelve_65_con_json(self) -> None:
        entorno = {**os.environ, "VANTAGE_PYTHON": "/ruta/que/no/existe/python"}
        proceso = subprocess.run(
            [str(self._ruta()), "Dune", "--json"],
            capture_output=True, text=True, env=entorno, timeout=60,
        )
        assert proceso.returncode == 65
        datos = json.loads(proceso.stdout)
        assert datos["error"]["tipo"] == "interprete_ausente"
        assert "venv" in datos["error"]["mensaje"]

    def test_wrapper_transmite_limetorrents_paginas(self) -> None:
        """Verifica que el wrapper transmite --limetorrents-paginas al backend."""
        proceso = subprocess.run(
            [str(self._ruta()), "--help-backend"],
            capture_output=True, text=True, timeout=30,
        )
        assert proceso.returncode == 0
        assert "--limetorrents-paginas" in proceso.stdout


class TestMotoresEnLaCLI:
    def test_motores_llegan_al_agregador(self, monkeypatch: pytest.MonkeyPatch) -> None:
        capturado: Dict[str, Any] = {}

        class Capturador(AgregadorFalso):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                capturado.update(kwargs)
                super().__init__(*args, **kwargs)

        AgregadorFalso.items = [ITEM_EJEMPLO]
        AgregadorFalso.resumen = _resumen()
        monkeypatch.setattr(modulo_main, "conectar_llm", lambda host: ClienteLLMFalso(RESPUESTA_LLM))
        monkeypatch.setattr(modulo_main, "AgregadorTorrents", Capturador)

        codigo = modulo_main.main(["Oppenheimer 2023", "--sin-motores", "MagnetDL, eztv.re"])

        assert codigo == modulo_main.EXIT_OK
        assert [motor.nombre for motor in capturado["motores"]] == ["YTS", "LimeTorrents", "Nyaa"]

    def test_motor_invalido_falla_antes_de_llamar_al_llm(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        llamado = {"llm": False}

        def conectar(host: str) -> Any:
            llamado["llm"] = True
            return ClienteLLMFalso(RESPUESTA_LLM)

        monkeypatch.setattr(modulo_main, "conectar_llm", conectar)

        codigo = modulo_main.main(["Dune", "--motores", "noexiste"])

        assert codigo == modulo_main.EXIT_USO
        assert llamado["llm"] is False, "no debe gastar una llamada al LLM si los motores son inválidos"
        assert "noexiste" in capsys.readouterr().err

    def test_error_de_uso_no_usa_el_codigo_2(self) -> None:
        """El código 2 significa 'sin resultados': un flag mal escrito no puede confundirse."""
        with pytest.raises(SystemExit) as salida:
            modulo_main.main(["Dune", "--all", "0"])
        assert salida.value.code == modulo_main.EXIT_USO


class TestSaludMotores:
    """Política de la salud persistente, con reloj controlado."""

    @staticmethod
    def _salud(tmp_path: Path, reloj, **kwargs: Any) -> Any:
        parametros = {"fallos_para_degradar": 2, "ttl": 1800.0, "timeout_degradado": 3.0}
        parametros.update(kwargs)
        return salud_motores.SaludMotores(tmp_path / "estado.json", reloj=reloj, **parametros)

    def test_archivo_ausente_es_estado_vacio(self, tmp_path: Path) -> None:
        salud = self._salud(tmp_path, lambda: 1000.0)
        assert salud.resumen() == []
        assert salud.decision("YTS").saltar is False

    def test_dos_fallos_degradan_y_el_exito_limpia(self, tmp_path: Path) -> None:
        momento = [1000.0]
        salud = self._salud(tmp_path, lambda: momento[0])

        salud.registrar("MagnetDL", exito=False, error="HTTP 522")
        assert salud.decision("MagnetDL").saltar is False, "un fallo aislado no debe bastar"

        salud.registrar("MagnetDL", exito=False, error="HTTP 522")
        decision = salud.decision("MagnetDL")
        assert decision.saltar is True
        assert "degradado" in (decision.motivo or "")

        salud.registrar("MagnetDL", exito=True)
        assert salud.decision("MagnetDL").saltar is False
        assert salud.decision("MagnetDL").motivo is None

    def test_ttl_vencido_reintenta_con_timeout_reducido(self, tmp_path: Path) -> None:
        momento = [1000.0]
        salud = self._salud(tmp_path, lambda: momento[0])
        salud.registrar("MagnetDL", exito=False)
        salud.registrar("MagnetDL", exito=False)
        assert salud.decision("MagnetDL").saltar is True

        momento[0] += 1801  # pasado el TTL
        decision = salud.decision("MagnetDL")
        assert decision.saltar is False
        assert decision.timeout == 3.0
        assert "sondeo" in (decision.motivo or "")

    def test_archivo_corrupto_no_rompe(self, tmp_path: Path) -> None:
        ruta = tmp_path / "estado.json"
        ruta.write_text("{esto no es json", encoding="utf-8")
        salud = salud_motores.SaludMotores(ruta)
        assert salud.resumen() == []
        assert salud.decision("YTS").saltar is False

    def test_escritura_atomica_genera_json_valido(self, tmp_path: Path) -> None:
        ruta = tmp_path / "estado.json"
        salud = salud_motores.SaludMotores(ruta)
        salud.registrar("Nyaa", exito=False, error="timeout")
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        assert datos["motores"]["Nyaa"]["fallos_consecutivos"] == 1
        assert list(tmp_path.glob("*.tmp")) == [], "no deben quedar temporales"

    def test_desactivada_no_escribe(self, tmp_path: Path) -> None:
        ruta = tmp_path / "estado.json"
        salud = salud_motores.SaludMotores(ruta, activa=False)
        salud.registrar("Nyaa", exito=False)
        assert not ruta.exists()
        assert salud.decision("Nyaa").saltar is False

    def test_reiniciar_borra_el_historial(self, tmp_path: Path) -> None:
        ruta = tmp_path / "estado.json"
        salud = salud_motores.SaludMotores(ruta)
        salud.registrar("Nyaa", exito=False)
        salud.registrar("Nyaa", exito=False)
        assert salud.decision("Nyaa").saltar is True

        salud.reiniciar()
        assert not ruta.exists()
        assert salud.decision("Nyaa").saltar is False


class TestSaludEnElAgregador:
    """Integración: un motor caído deja de costar su timeout."""

    @staticmethod
    def _agregador(tmp_path: Path, sesion: SesionFalsa, reloj):
        """Agregador con solo Nyaa y LimeTorrents: únicamente Nyaa puede fallar."""
        motores = seleccionar_motores(["nyaa", "limetorrents"])
        agregador = AgregadorTorrents(motores=motores, paralelo=False)
        agregador.session = sesion
        agregador.salud = salud_motores.SaludMotores(
            tmp_path / "estado.json", reloj=reloj, fallos_para_degradar=2, ttl=1800.0, timeout_degradado=3.0
        )
        return agregador

    @staticmethod
    def _llamadas_a(sesion: SesionFalsa, fragmento: str) -> int:
        return sum(1 for llamada in sesion.llamadas if fragmento in llamada["url"])

    def test_motor_caido_se_salta_tras_dos_busquedas(self, tmp_path: Path) -> None:
        momento = [1000.0]
        sesion = SesionFalsa(reglas=[("limetorrents", "limetorrents_search.html")])
        agregador = self._agregador(tmp_path, sesion, lambda: momento[0])

        # Las dos primeras búsquedas lo intentan y fallan (aún no está degradado).
        for intento in (1, 2):
            agregador.buscar_con_diagnostico("oppenheimer", "movies", 5)
            estado = next(e for e in agregador.ultimo_resumen.estados if e.nombre == "Nyaa")
            assert estado.saltado_por_salud is False, f"no debe saltarse en el intento {intento}"
            assert estado.ok is False

        llamadas_nyaa = self._llamadas_a(sesion, "nyaa.si")
        agregador.buscar_con_diagnostico("oppenheimer", "movies", 5)
        estado = next(e for e in agregador.ultimo_resumen.estados if e.nombre == "Nyaa")

        assert estado.saltado_por_salud is True
        assert "degradado" in (estado.motivo_salud or "")
        assert estado.milisegundos == 0
        assert self._llamadas_a(sesion, "nyaa.si") == llamadas_nyaa, "no debe pedirse nada al motor saltado"
        # El motor sano sigue consultándose en la misma búsqueda.
        assert self._llamadas_a(sesion, "limetorrents") > 0

    def test_ttl_vencido_sondea_con_timeout_reducido_y_se_recupera(self, tmp_path: Path) -> None:
        momento = [1000.0]
        sesion = SesionFalsa(reglas=[("limetorrents", "limetorrents_search.html")])
        agregador = self._agregador(tmp_path, sesion, lambda: momento[0])

        for _ in range(3):
            agregador.buscar_con_diagnostico("oppenheimer", "movies", 5)
        assert next(e for e in agregador.ultimo_resumen.estados if e.nombre == "Nyaa").saltado_por_salud

        # Pasado el TTL, se reintenta con timeout reducido; el índice ya responde.
        momento[0] += 1801
        sesion.reglas.append(("nyaa.si", "nyaa_search.html"))
        agregador.buscar_con_diagnostico("dune", "movies", 5)
        estado = next(e for e in agregador.ultimo_resumen.estados if e.nombre == "Nyaa")

        assert estado.saltado_por_salud is False
        assert estado.timeout_segundos == 3.0, "el sondeo debe usar el timeout reducido"
        assert estado.ok is True and estado.resultados > 0

        # Tras el éxito vuelve a la normalidad: sin salto y con el timeout habitual.
        agregador.buscar_con_diagnostico("dune", "movies", 5)
        estado = next(e for e in agregador.ultimo_resumen.estados if e.nombre == "Nyaa")
        assert estado.saltado_por_salud is False
        assert estado.timeout_segundos is None
        assert estado.ok is True

    def test_un_fallo_de_imdb_no_degrada_eztv(self, tmp_path: Path) -> None:
        """Sin IMDb no hay resultados, pero el índice no tiene la culpa."""
        momento = [1000.0]
        sesion = SesionFalsa(reglas=[("limetorrents", "limetorrents_search.html")])
        motores = seleccionar_motores(["eztv", "limetorrents"])
        agregador = AgregadorTorrents(motores=motores, paralelo=False)
        agregador.session = sesion
        agregador.salud = salud_motores.SaludMotores(
            tmp_path / "estado.json", reloj=lambda: momento[0], fallos_para_degradar=2
        )

        for _ in range(3):
            agregador.buscar_con_diagnostico("severance", "tv", 5, resolver_imdb=False)
            estado = next(e for e in agregador.ultimo_resumen.estados if e.nombre == "EZTV")
            assert estado.saltado_por_salud is False
            assert "ErrorResolucion" in (estado.error or "")

        assert all(fila["nombre"] != "EZTV" for fila in agregador.salud.resumen())


class TestSaludEnLaCLI:
    def test_reset_borra_el_historial(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        ruta = tmp_path / "estado.json"
        monkeypatch.setattr(salud_motores, "ARCHIVO_POR_DEFECTO", ruta)
        salud_motores.SaludMotores(ruta).registrar("Nyaa", exito=False)

        AgregadorFalso.items = [ITEM_EJEMPLO]
        AgregadorFalso.resumen = _resumen()
        monkeypatch.setattr(modulo_main, "conectar_llm", lambda host: ClienteLLMFalso(RESPUESTA_LLM))
        monkeypatch.setattr(modulo_main, "AgregadorTorrents", AgregadorFalso)

        assert modulo_main.main(["Oppenheimer 2023", "--salud", "reset"]) == modulo_main.EXIT_OK
        assert not ruta.exists()

    def test_off_no_escribe_estado(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        ruta = tmp_path / "estado.json"
        monkeypatch.setattr(salud_motores, "ARCHIVO_POR_DEFECTO", ruta)
        AgregadorFalso.items = [ITEM_EJEMPLO]
        AgregadorFalso.resumen = _resumen()
        monkeypatch.setattr(modulo_main, "conectar_llm", lambda host: ClienteLLMFalso(RESPUESTA_LLM))
        monkeypatch.setattr(modulo_main, "AgregadorTorrents", AgregadorFalso)

        assert modulo_main.main(["Oppenheimer 2023", "--salud", "off"]) == modulo_main.EXIT_OK
        assert not ruta.exists()


class TestLimpiarConsulta:
    @pytest.mark.parametrize(
        ("entrada", "esperado"),
        [
            ("película Oppenheimer", "Oppenheimer"),
            ("Busca la película Oppenheimer", "Oppenheimer"),
            ("Busca la serie Severance", "Severance"),
            ("quiero descargar Dune 2021", "Dune 2021"),
            ("ver online gratis Frieren", "Frieren"),
            ("anime Frieren", "Frieren"),
            ("The Last of Us", "Last of Us"),
            ("tt11280740", "tt11280740"),
            ("Dune", "Dune"),
            ("", ""),
            (None, ""),
        ],
    )
    def test_limpiar_consulta(self, entrada: Optional[str], esperado: str) -> None:
        assert limpiar_consulta(entrada) == esperado

    def test_no_destruye_un_titulo_que_es_palabra_de_categoria(self) -> None:
        """'The Game' no debe quedar vacío al quitar 'game'."""
        assert limpiar_consulta("The Game") == "The Game"

    def test_agregador_busca_la_consulta_limpia(self) -> None:
        sesion = SesionFalsa(reglas=[("limetorrents", "limetorrents_search.html")])
        agregador = AgregadorTorrents(paralelo=False)
        agregador.session = sesion

        items, resumen = agregador.buscar_con_diagnostico("película Oppenheimer", "movies", 5)

        assert resumen.consulta == "Oppenheimer"
        assert resumen.consulta_original == "película Oppenheimer"
        assert items
        assert all("oppenheimer" in normalizar(item["title"]) for item in items)
        assert "peticion original='película Oppenheimer'" in resumen.formatear()


class SesionConEstados(SesionFalsa):
    """Devuelve respuestas prefijadas en orden (para probar reintentos)."""

    def __init__(self, respuestas: List[Any], **kwargs: Any) -> None:
        super().__init__(reglas=[], **kwargs)
        self.pendientes = list(respuestas)

    def get(self, url, headers=None, params=None, timeout=None) -> RespuestaFalsa:
        self.llamadas.append({"url": url, "params": dict(params or {}), "timeout": timeout})
        if self.pendientes:
            item = self.pendientes.pop(0)
            if isinstance(item, Exception):
                raise item
            estado, cuerpo = item
            return RespuestaFalsa(cuerpo, url, status_code=estado)
        return RespuestaFalsa(cargar_texto("yts_response.json"), url)


class SesionQueFalla(SesionFalsa):
    """Falla siempre con la excepción indicada."""

    def __init__(self, error: Exception) -> None:
        super().__init__(reglas=[])
        self.error = error

    def get(self, url, headers=None, params=None, timeout=None) -> RespuestaFalsa:
        self.llamadas.append({"url": url, "params": dict(params or {}), "timeout": timeout})
        raise self.error


HTML_LIME_CON_AVISO = (
    '<html><body><div class="aviso">No results found for your search</div>'
    '<table class="table2"><tr><th>Name</th></tr><tr>'
    '<td class="tdleft"><div class="tt-name">'
    '<a href="http://itorrents.net/torrent/' + "a" * 40 + '.torrent" class="csprite_dl14"></a>'
    '<a href="/Oppenheimer-torrent-1.html">Oppenheimer 2023 1080p BluRay</a></div></td>'
    '<td class="tdnormal">1 Year+ - in Movies</td><td class="tdnormal">2.0 GB</td>'
    '<td class="tdseed">900</td><td class="tdleech">12</td><td class="tdright"></td>'
    "</tr></table></body></html>"
)


def _cargar_verificador() -> Any:
    """Carga scripts/verificar_engines.py, que no es un paquete importable."""
    ruta = RAIZ / "scripts" / "verificar_engines.py"
    especificacion = importlib.util.spec_from_file_location("verificar_engines_bh", ruta)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


class TestReintentosAlcanzables:
    """BH-001: el presupuesto de reintentos debe usarse de verdad, sin castigar timeouts."""

    def test_reintenta_un_503_y_acaba_bien(self) -> None:
        sesion = SesionConEstados([(503, "sin servicio"), (200, cargar_texto("yts_response.json"))])
        items = buscar_torrents_yts("Oppenheimer", min_seeders=5, session=sesion)
        assert items, "el segundo intento debía devolver resultados"
        assert len(sesion.llamadas) == 2

    def test_no_reintenta_un_timeout(self) -> None:
        """Un índice muerto cuesta su timeout: insistir duplicaría el peor caso."""
        sesion = SesionQueFalla(requests.Timeout("read timeout"))
        with pytest.raises(ErrorFuenteNoDisponible):
            buscar_torrents_nyaa("dune", session=sesion)
        assert len(sesion.llamadas) == 1, "un timeout no debe reintentarse"

    def test_no_reintenta_un_404(self) -> None:
        sesion = SesionConEstados([(404, "no existe")])
        with pytest.raises(ErrorFuenteNoDisponible):
            buscar_torrents_nyaa("dune", session=sesion)
        assert len(sesion.llamadas) == 1, "un 4xx no reintentable debe fallar de inmediato"

    def test_si_reintenta_un_connect_timeout(self) -> None:
        """BH2-006: `ConnectTimeout` también hereda de `ConnectionError`: es barato."""
        sesion = SesionQueFalla(requests.ConnectTimeout("no se pudo conectar"))
        with pytest.raises(ErrorFuenteNoDisponible):
            buscar_torrents_nyaa("dune", session=sesion)
        assert len(sesion.llamadas) == 2, "un fallo de conexión sí debe reintentarse"

    def test_read_timeout_no_se_reintenta(self) -> None:
        """El `ReadTimeout` cuesta el timeout completo: no se insiste."""
        sesion = SesionQueFalla(requests.ReadTimeout("el servidor no responde"))
        with pytest.raises(ErrorFuenteNoDisponible):
            buscar_torrents_nyaa("dune", session=sesion)
        assert len(sesion.llamadas) == 1


class TestRelevanciaSinFalsosPositivos:
    """BH-002: los prefijos de 4 letras ya no cuelan títulos ajenos."""

    @pytest.mark.parametrize(
        ("titulo", "token", "esperado"),
        [
            ("Barb Wire 1996 1080p", "barbie", False),
            ("Severance S02E10 1080p", "severe", False),
            ("Oppenheimer 2023 1080p", "oppenheimer", True),
            ("Spider Man No Way Home 2021", "spiderman", True),
            ("Dune 2021 1080p", "dune", True),
            ("The Unfathomable Sand Dunes FLAC", "dune", False),
        ],
    )
    def test_coincide_titulo(self, titulo: str, token: str, esperado: bool) -> None:
        assert coincide_titulo(titulo, [token]) is esperado

    @pytest.mark.parametrize(
        ("a", "b", "esperado"),
        [
            ("oppenheimer", "oppenheimers", True),
            ("avengers", "avenger", True),
            ("barbie", "barb", False),
            ("severance", "severe", False),
            # "dune"/"dunes" sí entra aquí; el caso de Dune lo protege el guardia
            # len(token) >= 6 de coincide_titulo, no este helper.
            ("dune", "dunes", True),
        ],
    )
    def test_prefijo_con_diferencia_corta(self, a: str, b: str, esperado: bool) -> None:
        assert _prefijo_con_diferencia_corta(a, b) is esperado


class TestPaginaVaciaNoPisaResultados:
    """BH-003: con tabla presente, un aviso de "no results" no debe vaciar la búsqueda."""

    def test_limetorrents_con_tabla_y_aviso(self) -> None:
        sesion = SesionTexto(HTML_LIME_CON_AVISO)
        items = buscar_torrents_limetorrents("oppenheimer", min_seeders=5, session=sesion)
        assert len(items) == 1
        assert items[0]["seeders"] == 900
        assert "a" * 40 in items[0]["magnet"]

    def test_limetorrents_sin_tabla_y_con_aviso_sigue_devolviendo_vacio(self) -> None:
        sesion = SesionTexto("<html><body><div>No results found</div></body></html>")
        assert buscar_torrents_limetorrents("oppenheimer", session=sesion) == []

    def test_limetorrents_sin_tabla_ni_aviso_es_error_de_estructura(self) -> None:
        sesion = SesionTexto("<html><body><p>otra cosa</p></body></html>")
        with pytest.raises(ErrorEstructura):
            buscar_torrents_limetorrents("oppenheimer", session=sesion)


class TestGenerosYTS:
    """BH-004: las claves del mapa de géneros deben normalizarse como la consulta."""

    def test_genero_con_guion_llega_al_parametro(self, sesion_falsa: SesionFalsa) -> None:
        buscar_torrents_yts("Dune", "sci-fi", session=sesion_falsa)
        assert sesion_falsa.llamadas[-1]["params"].get("genre") == "Sci-Fi"

    def test_genero_en_espanol_no_se_traduce(self, sesion_falsa: SesionFalsa) -> None:
        """La tabla usa los nombres de género de la API (en inglés); otro valor no rompe."""
        buscar_torrents_yts("Amelie", "Animación", session=sesion_falsa)
        assert "genre" not in sesion_falsa.llamadas[-1]["params"]

    def test_movies_no_envia_genero(self, sesion_falsa: SesionFalsa) -> None:
        buscar_torrents_yts("Dune", "movies", session=sesion_falsa)
        assert "genre" not in sesion_falsa.llamadas[-1]["params"]


class TestContratoDeInterfaz:
    """BH-007, BH-008, BH-009: guardas de escritura, validación de host y códigos de salida."""

    def test_salida_rechaza_extension_de_codigo(self, tmp_path: Path) -> None:
        modulo = _cargar_verificador()
        with pytest.raises(SystemExit):
            modulo._escribir_informe(tmp_path / "engines.py", "informe")
        assert not (tmp_path / "engines.py").exists()

    def test_salida_acepta_markdown(self, tmp_path: Path) -> None:
        modulo = _cargar_verificador()
        destino = tmp_path / "informe.md"
        modulo._escribir_informe(destino, "informe")
        assert destino.read_text(encoding="utf-8").startswith("informe")

    def test_salida_forzada_permite_otra_extension(self, tmp_path: Path) -> None:
        modulo = _cargar_verificador()
        destino = tmp_path / "informe.rst"
        modulo._escribir_informe(destino, "informe", forzar=True)
        assert destino.exists()

    def test_verificador_sale_0_si_los_motores_dieron_algo(self, monkeypatch: pytest.MonkeyPatch) -> None:
        modulo = _cargar_verificador()
        monkeypatch.setattr(modulo, "sondear_todo", lambda: [])
        resumen = ResumenBusqueda(
            consulta="dune", categoria="all", min_seeders=5, brutos=3, unicos=0, descartados_relevancia=3
        )
        monkeypatch.setattr(modulo, "probar_motores", lambda *a, **k: ([], resumen))
        assert modulo.main(["--sin-sondeo", "-q", "dune"]) == 0

    def test_verificador_sale_1_si_ningun_motor_respondio(self, monkeypatch: pytest.MonkeyPatch) -> None:
        modulo = _cargar_verificador()
        monkeypatch.setattr(modulo, "sondear_todo", lambda: [])
        resumen = ResumenBusqueda(consulta="dune", categoria="all", min_seeders=5, brutos=0)
        monkeypatch.setattr(modulo, "probar_motores", lambda *a, **k: ([], resumen))
        assert modulo.main(["--sin-sondeo", "-q", "dune"]) == 1

    def test_shim_rechaza_host_que_solo_contiene_nyaa(self) -> None:
        with pytest.raises(NotImplementedError):
            scraper.buscar_torrents("dune", base_url="https://not-nyaa.example")

    def test_shim_acepta_el_host_de_nyaa(self) -> None:
        assert scraper._es_host_de_nyaa("https://nyaa.si") is True
        assert scraper._es_host_de_nyaa("nyaa.si") is True
        assert scraper._es_host_de_nyaa("https://nyaa.si.example.com") is False
        assert scraper._es_host_de_nyaa("https://1337x.to") is False


class TestHigieneDelAgregador:
    """BH-012, BH-013, BH-014, BH-017."""

    @staticmethod
    def _agregador(tmp_path: Path, sesion: SesionFalsa) -> Any:
        agregador = AgregadorTorrents(paralelo=False)
        agregador.session = sesion
        agregador.salud = salud_motores.SaludMotores(tmp_path / "estado.json")
        return agregador

    def test_no_repite_la_resolucion_imdb(self, tmp_path: Path) -> None:
        """BH-012: si el agregador ya falló resolviendo, el motor no reintenta."""
        sesion = SesionFalsa(reglas=[("limetorrents", "limetorrents_search.html")])
        agregador = self._agregador(tmp_path, sesion)

        _, resumen = agregador.buscar_con_diagnostico("severance", "tv", 5)

        llamadas_imdb = [llamada for llamada in sesion.llamadas if "media-imdb" in llamada["url"]]
        assert len(llamadas_imdb) == 1, "no debe intentarse la resolución dos veces"
        assert resumen.error_imdb

    def test_motores_vacios_es_error(self) -> None:
        with pytest.raises(ValueError):
            AgregadorTorrents(motores=[])

    def test_nombres_duplicados_es_error(self) -> None:
        duplicado = [Motor("X", buscar_torrents_nyaa), Motor("X", buscar_torrents_nyaa)]
        with pytest.raises(ValueError) as error:
            AgregadorTorrents(motores=duplicado)
        assert "duplicados" in str(error.value)

    def test_cerrar_cierra_la_sesion(self, tmp_path: Path) -> None:
        sesion = SesionFalsa(reglas=[("limetorrents", "limetorrents_search.html")])
        agregador = self._agregador(tmp_path, sesion)
        assert sesion.cerrada is False
        agregador.cerrar()
        assert sesion.cerrada is True

    def test_es_gestor_de_contexto(self, tmp_path: Path) -> None:
        sesion = SesionFalsa(reglas=[])
        with AgregadorTorrents(paralelo=False) as agregador:
            agregador.session = sesion
        assert sesion.cerrada is True


class TestNotaDelCatalogoYTypeError:
    """BH-015 y BH-018."""

    def test_el_informe_de_salud_incluye_la_nota(self, tmp_path: Path) -> None:
        ruta = tmp_path / "estado.json"
        salud_motores.SaludMotores(ruta).registrar("MagnetDL", exito=False, error="timeout")
        sesion = SesionTexto('{"models": [{"name": "qwen2.5:7b"}]}')

        datos = salud.informe(salud=salud_motores.SaludMotores(ruta), session=sesion)

        fila = next(m for m in datos["motores"] if m["nombre"] == "MagnetDL")
        assert fila["nota"], "Motor.nota debe llegar al informe"
        assert "MagnetDL" in fila["nombre"]

    def test_typeerror_interno_no_se_silencia(self) -> None:
        class ClienteRoto:
            def __init__(self) -> None:
                self.llamadas = 0

            def chat(self, **kwargs: Any) -> Any:
                self.llamadas += 1
                raise TypeError("un fallo interno del cliente")

        cliente = ClienteRoto()
        with pytest.raises(ConnectionError):
            procesar_peticion_usuario("Dune", cliente)
        assert cliente.llamadas == 1, "no debe reintentarse un TypeError ajeno"

    def test_typeerror_por_format_si_se_repliega(self) -> None:
        cliente = ClienteLLMFalso('{"query": "Dune", "categoria": "movies"}', soporta_format=False)
        assert procesar_peticion_usuario("Dune", cliente)["query"] == "Dune"
        assert len(cliente.llamadas) == 2


class TestSaludThreadSafe:
    """BH2-001: la salud se usa desde varios hilos y no puede perder resultados.

    Reproducido antes del arreglo: se descartaban los 40 resultados de un índice que sí
    había respondido (reportado como `ok=False` con un `RuntimeError`) y, si fallaba también
    el registro del `except`, la búsqueda completa se caía.
    """

    class _DiccionarioQueCambia(dict):
        """Inserta una clave mientras se itera, como haría otro hilo."""

        def items(self):
            for indice, (clave, valor) in enumerate(super().items()):
                if indice == 1:
                    super().__setitem__(
                        "intruso", salud_motores.EstadoMotorSalud(nombre="intruso")
                    )
                yield clave, valor

    def test_guardar_itera_una_instantanea(self, tmp_path: Path) -> None:
        salud = salud_motores.SaludMotores(tmp_path / "estado.json")
        salud._estado = self._DiccionarioQueCambia(
            A=salud_motores.EstadoMotorSalud(nombre="A"),
            B=salud_motores.EstadoMotorSalud(nombre="B"),
        )
        salud.guardar()  # antes: RuntimeError: dictionary changed size during iteration
        datos = json.loads((tmp_path / "estado.json").read_text(encoding="utf-8"))
        assert datos["motores"]["A"]["nombre"] == "A"

    def test_registros_concurrentes_no_pierden_motores(self, tmp_path: Path) -> None:
        salud = salud_motores.SaludMotores(tmp_path / "estado.json")
        errores: List[BaseException] = []

        def anotar(nombre: str) -> None:
            try:
                for _ in range(5):
                    salud.registrar(nombre, exito=False, error="simulado")
            except BaseException as error:  # noqa: BLE001 - se reporta en la aserción
                errores.append(error)

        hilos = [threading.Thread(target=anotar, args=(f"M{indice}",)) for indice in range(6)]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join()

        assert not errores, f"fallos concurrentes: {errores[:2]}"
        assert len(salud.resumen()) == 6

    @staticmethod
    def _agregador_con_salud_rota(tmp_path: Path, sesion: SesionFalsa, *, falla_el_exito: bool):
        agregador = AgregadorTorrents(motores=seleccionar_motores(["limetorrents"]), paralelo=False)
        agregador.session = sesion
        salud = salud_motores.SaludMotores(tmp_path / "estado.json")

        def registrar_roto(nombre, *, exito, error=None):
            if exito == falla_el_exito:
                raise RuntimeError("dictionary changed size during iteration")

        salud.registrar = registrar_roto
        agregador.salud = salud
        return agregador

    def test_un_fallo_al_anotar_exito_no_pierde_resultados(self, tmp_path: Path) -> None:
        sesion = SesionFalsa(reglas=[("limetorrents", "limetorrents_search.html")])
        agregador = self._agregador_con_salud_rota(tmp_path, sesion, falla_el_exito=True)

        items, resumen = agregador.buscar_con_diagnostico("oppenheimer", "movies", 5)

        estado = resumen.estados[0]
        assert items, "los resultados ya obtenidos no pueden descartarse por contabilidad"
        assert estado.ok is True and estado.resultados > 0

    def test_un_fallo_al_anotar_error_no_aborta_la_busqueda(self, tmp_path: Path) -> None:
        sesion = SesionFalsa(reglas=[("limetorrents", "limetorrents_search.html")])
        agregador = self._agregador_con_salud_rota(tmp_path, sesion, falla_el_exito=False)
        sesion.fallos = ["nyaa"]  # fuerza un fallo de motor para pasar por el except

        items, _ = agregador.buscar_con_diagnostico("oppenheimer", "movies", 5)

        assert items, "un fallo de salud no debe propagarse y tumbar la búsqueda"

    def test_paralelo_con_salud(self, tmp_path: Path) -> None:
        """Combinación que ninguna prueba cubría: la ruta por defecto es paralela.

        Los motores sin ruta simulada fallan legítimamente; lo que se comprueba es que
        ninguno falle por una carrera interna de la salud y que los resultados lleguen.
        """
        reglas = [("limetorrents", "limetorrents_search.html"), ("nyaa.si", "nyaa_search.html")]
        agregador = AgregadorTorrents(paralelo=True, max_workers=4)
        agregador.session = SesionFalsa(reglas=reglas)
        agregador.salud = salud_motores.SaludMotores(tmp_path / "estado.json")

        items, resumen = agregador.buscar_con_diagnostico("oppenheimer", "all", 5)

        assert items, "la búsqueda en paralelo debe devolver los resultados del motor que respondió"
        assert all(
            "RuntimeError" not in (estado.error or "") for estado in resumen.estados
        ), "una carrera de la salud no debe aparecer como fallo de motor"
        assert any(estado.nombre == "LimeTorrents" and estado.ok for estado in resumen.estados)


class TestMotoresConsultados:
    """BH2-002: el campo solo debe listar los índices que se consultaron de verdad."""

    def test_excluye_omitidos_y_saltados(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
        resumen = ResumenBusqueda(
            consulta="severance",
            categoria="tv",
            min_seeders=5,
            estados=[
                EstadoMotor(nombre="YTS", ok=True, omitido=True, error="no soporta categoria='tv'"),
                EstadoMotor(nombre="LimeTorrents", ok=True, resultados=40),
                EstadoMotor(nombre="MagnetDL", ok=True, saltado_por_salud=True, motivo_salud="degradado"),
                EstadoMotor(nombre="EZTV", ok=True, resultados=75),
            ],
        )
        AgregadorFalso.items = [ITEM_EJEMPLO]
        AgregadorFalso.resumen = resumen
        monkeypatch.setattr(modulo_main, "conectar_llm", lambda host: ClienteLLMFalso(RESPUESTA_LLM))
        monkeypatch.setattr(modulo_main, "AgregadorTorrents", AgregadorFalso)

        modulo_main.main(["Severance", "--json"])
        datos = json.loads(capsys.readouterr().out)

        assert datos["diagnostico"]["motores_consultados"] == ["LimeTorrents", "EZTV"]


class TestCifraDocumentada:
    """La cifra de pruebas del README es un dato verificado, no una promesa.

    Se quedó obsoleta tres veces durante el desarrollo (86 -> 99 -> 134 -> 169 -> 177), así
    que ahora hay una prueba que la compara con la colección real de pytest.
    """

    def test_el_readme_dice_la_cifra_real(self, request: pytest.FixtureRequest) -> None:
        # ``session.items`` solo trae lo seleccionado: en una ejecución filtrada (-k/-m) el
        # total no es comparable, así que ahí se salta en vez de dar un falso positivo.
        if request.config.option.keyword or getattr(request.config.option, "markexpr", None):
            pytest.skip("ejecución filtrada: el total de la suite no es comparable")
        total = len(request.session.items)
        texto = (RAIZ / "README.md").read_text(encoding="utf-8")
        cifras = {int(cifra) for cifra in re.findall(r"(\d+) pruebas offline", texto)}
        assert cifras, "el README debe declarar el número de pruebas"
        assert cifras == {total}, (
            f"el README dice {sorted(cifras)} pruebas y la suite tiene {total}: actualiza las cifras"
        )


class TestBriefIntegradoConElManual:
    """El Anexo A del brief cita el manual de uso y no puede quedarse atrás.

    Comprueba dos cosas: que los casos de «Solución de Problemas» del manual estén todos en el
    anexo (estructura, robusto ante reescrituras) y que las citas literales coincidan en los
    dos documentos (si alguien reescribe el manual sin tocar el brief, falla aquí).
    """

    @staticmethod
    def _casos_de_problemas() -> List[str]:
        manual = (RAIZ / "MANUAL_USUARIO.md").read_text(encoding="utf-8")
        bloque = manual.split("## Solución de Problemas", 1)[1].split("\n## ", 1)[0]
        return re.findall(r"^### (.+)$", bloque, re.M)

    def test_los_casos_del_manual_estan_todos_en_el_anexo(self) -> None:
        brief = (RAIZ / "BRIEF_UI_GLAZE.md").read_text(encoding="utf-8")
        casos = self._casos_de_problemas()

        assert len(casos) >= 7, f"se esperaban al menos 7 casos en el manual, hay {len(casos)}"
        faltan = [caso for caso in casos if caso not in brief]
        assert not faltan, (
            f"el Anexo A del brief no cubre estos casos del manual: {faltan}. "
            "Añádelos a la tabla A.4 y al orden de A.8."
        )

    @pytest.mark.parametrize(
        "cita",
        [
            "El nombre del torrent (incluye calidad y fuente)",
            "El enlace magnético que puedes copiar y pegar en tu cliente de torrents (Transmission, qBittorrent, etc.)",
            "Índice de origen (YTS, LimeTorrents, Nyaa, EZTV o MagnetDL)",
            '**Sé específico:** "Película Oppenheimer 2023" funciona mejor que solo "Oppenheimer"',
            "**Anime:** para anime, Nyaa suele dar mejores resultados que los índices generalistas",
            "No responde (timeout en `.com`, DNS en `.mx`)",
        ],
    )
    def test_las_citas_literales_coinciden(self, cita: str) -> None:
        manual = (RAIZ / "MANUAL_USUARIO.md").read_text(encoding="utf-8")
        brief = (RAIZ / "BRIEF_UI_GLAZE.md").read_text(encoding="utf-8")

        assert cita in manual or cita in brief, f"la cita ya no está en ninguno: {cita!r}"
        assert cita in manual, f"el manual ya no dice {cita!r}: actualiza el Anexo A"
        assert cita in brief, f"el Anexo A no dice {cita!r}: resincronízalo con el manual"
