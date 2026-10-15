"""Pruebas offline de VANTAGE: normalización, LLM, motores, agregador y CLI.

Ejecutar con::

    source venv/bin/activate
    pytest tests/vantage -v
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import pytest
import requests

import engines
import main as modulo_main
import scraper
from ai_agent import extraer_json, procesar_peticion_usuario
from conftest import ClienteLLMFalso, RespuestaFalsa, SesionFalsa, cargar_json
from ai_agent import MODELO_POR_DEFECTO
from engines import (
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
from resolver import (
    TIPOS_PELICULA,
    TIPOS_TV,
    ErrorResolucion,
    resolver_imdb_id,
    seleccionar_candidato,
)
from texto import (
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
