"""Orquestador de línea de comandos de VANTAGE.

Flujo: lenguaje natural -> extracción con LLM local -> búsqueda agregada en los
motores -> impresión del resultado más estable (o de los N mejores).

Cuando una búsqueda no devuelve nada, el diagnóstico por motor se imprime en
``stderr``: el usuario ve *qué* motor falló y por qué, en lugar de un genérico
"no hay resultados".

Códigos de salida
-----------------
=====  ============================================
0      resultado encontrado (o ayuda mostrada)
2      ningún item superó los filtros
3      fallo del LLM (conexión o parseo)
4      todos los motores fallaron
64     argumentos inválidos (uso incorrecto)
130    interrupción por teclado
=====  ============================================
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Sequence

from ai_agent import MODELO_POR_DEFECTO, procesar_peticion_usuario
from salud_motores import SaludMotores
from engines import (
    AgregadorTorrents,
    ResumenBusqueda,
    motores_desde_texto,
    nombres_disponibles,
    seleccionar_motores,
)

HOST_OLLAMA_POR_DEFECTO = "http://localhost:11434"
SEEDERS_MINIMOS_POR_DEFECTO = 5

EXIT_OK = 0
EXIT_SIN_RESULTADOS = 2
EXIT_ERROR_LLM = 3
EXIT_MOTORES_CAIDOS = 4
EXIT_USO = 64
EXIT_INTERRUMPIDO = 130


class ParserVantage(argparse.ArgumentParser):
    """ArgumentParser que sale con el código 64 en vez de 2.

    argparse usa 2 para los errores de uso y en esta CLI 2 significa "sin
    resultados": un cliente (por ejemplo la app de escritorio) no podría
    distinguir un flag mal escrito de una búsqueda vacía.
    """

    def error(self, message: str) -> None:  # pragma: no cover - termina el proceso
        self.print_usage(sys.stderr)
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        raise SystemExit(EXIT_USO)


def construir_parser() -> argparse.ArgumentParser:
    """Define la interfaz de línea de comandos."""
    parser = ParserVantage(
        prog="main.py",
        description="Búsqueda de metadatos BitTorrent en lenguaje natural (VANTAGE).",
        epilog='Ejemplo: python3 main.py "Busca la película Oppenheimer 2023" --verbose',
    )
    parser.add_argument("consulta", nargs="+", help="Petición en lenguaje natural")
    parser.add_argument("-n", "--all", type=int, default=1, metavar="N",
                        help="Muestra los N mejores resultados (por defecto 1)")
    parser.add_argument("-s", "--min-seeders", type=int, default=SEEDERS_MINIMOS_POR_DEFECTO,
                        help=f"Sembradores mínimos (por defecto {SEEDERS_MINIMOS_POR_DEFECTO})")
    parser.add_argument("-m", "--model", default=MODELO_POR_DEFECTO,
                        help=f"Modelo de Ollama (por defecto {MODELO_POR_DEFECTO})")
    parser.add_argument("--host", default=HOST_OLLAMA_POR_DEFECTO,
                        help=f"Host de Ollama (por defecto {HOST_OLLAMA_POR_DEFECTO})")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Muestra el diagnóstico por motor")
    parser.add_argument("--json", action="store_true", dest="salida_json",
                        help="Salida JSON legible por máquina")
    parser.add_argument("--sin-relevancia", action="store_true",
                        help="No filtra por coincidencia de título con la consulta")
    parser.add_argument("--no-imdb", action="store_true",
                        help="No resuelve IMDb por red (desactiva EZTV si no hay id)")
    parser.add_argument("--secuencial", action="store_true",
                        help="Consulta los motores en serie con pausas (más lento, más conservador)")
    parser.add_argument("--motores", metavar="LISTA", default=None,
                        help="Consulta solo estos motores, separados por comas "
                             f"({', '.join(nombres_disponibles())})")
    parser.add_argument("--sin-motores", metavar="LISTA", default=None,
                        help="No consulta estos motores, separados por comas "
                             "(util para saltar indices caidos que solo anaden espera)")
    parser.add_argument("--salud", choices=("auto", "off", "reset"), default="auto",
                        help="Salud persistente de los motores: 'auto' no vuelve a esperar a un "
                             "índice caído, 'off' la desactiva, 'reset' borra el historial")
    parser.add_argument("--limetorrents-paginas", type=int, default=1, metavar="N",
                        help="Páginas a consultar en LimeTorrents (por defecto 1)")
    parser.add_argument("--debug", action="store_true", help="Registro de depuración en stderr")
    return parser


def conectar_llm(host: str) -> Any:
    """Construye y valida el cliente de Ollama.

    Raises:
        ConnectionError: Si Ollama no responde o no está disponible el paquete.
    """
    try:
        import ollama  # importación diferida: la CLI funciona sin Ollama para --help
    except ImportError as error:
        raise ConnectionError(f"paquete 'ollama' no instalado: {error}") from error

    try:
        cliente = ollama.Client(host=host)
        cliente.list()
        return cliente
    except Exception as error:
        raise ConnectionError(
            f"no se pudo conectar a Ollama en {host}: {error}. Arranca el servicio con 'ollama serve'"
        ) from error


def extraer_parametros(consulta: str, cliente_llm: Any, modelo: str) -> Dict[str, str]:
    """Envuelve la extracción del LLM para reutilizarla desde otros módulos."""
    return procesar_peticion_usuario(consulta, cliente_llm, model=modelo)


def formatear_item(item: Dict[str, Any], indice: Optional[int] = None) -> str:
    """Formatea un resultado para terminal."""
    encabezado = "Resultado óptimo" if indice is None else f"Resultado #{indice}"
    return "\n".join(
        [
            f"{encabezado}:",
            f"  Title:    {item.get('title', 'N/A')}",
            f"  Magnet:   {item.get('magnet', 'N/A')}",
            f"  Seeders:  {item.get('seeders', 0)}",
            f"  Leechers: {item.get('leechers', 0)}",
            f"  Size:     {item.get('size', 'N/A')}",
            f"  Source:   {item.get('source', 'N/A')}",
        ]
    )


def _payload_json(
    extraido: Dict[str, str],
    items: List[Dict[str, Any]],
    resumen: ResumenBusqueda,
) -> Dict[str, Any]:
    """Estructura JSON estable para consumo por otros programas."""
    return {
        "consulta": extraido,
        "resultados": items,
        "mejor": items[0] if items else None,
        "diagnostico": {
            "consulta_efectiva": resumen.consulta,
            # Solo los que se consultaron de verdad: ni los omitidos por categoría ni los
            # saltados por salud (que cuestan cero y no se tocaron).
            "motores_consultados": [
                estado.nombre
                for estado in resumen.estados
                if not estado.omitido and not estado.saltado_por_salud
            ],
            "consulta_original": resumen.consulta_original,
            "categoria": resumen.categoria,
            "imdb_id": resumen.imdb_id,
            "error_imdb": resumen.error_imdb,
            "min_seeders": resumen.min_seeders,
            "items_brutos": resumen.brutos,
            "items_unicos": resumen.unicos,
            "descartados_por_relevancia": resumen.descartados_relevancia,
            "motores": [
                {
                    "nombre": estado.nombre,
                    "ok": estado.ok,
                    "omitido": estado.omitido,
                    "resultados": estado.resultados,
                    "error": estado.error,
                    "ms": estado.milisegundos,
                    "imdb_id": estado.imdb_id,
                    "saltado_por_salud": estado.saltado_por_salud,
                    "motivo_salud": estado.motivo_salud,
                    "timeout_segundos": estado.timeout_segundos,
                }
                for estado in resumen.estados
            ],
        },
    }


def ejecutar(args: argparse.Namespace) -> int:
    """Ejecuta el flujo completo y devuelve el código de salida."""
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s")

    consulta = " ".join(args.consulta).strip()

    try:
        motores = seleccionar_motores(
            motores_desde_texto(args.motores), motores_desde_texto(args.sin_motores)
        )
    except ValueError as error:
        print(f"Selección de motores inválida: {error}", file=sys.stderr)
        return EXIT_USO

    try:
        cliente_llm = conectar_llm(args.host)
    except ConnectionError as error:
        print(f"Error de conexión con Ollama: {error}", file=sys.stderr)
        return EXIT_ERROR_LLM

    try:
        extraido = extraer_parametros(consulta, cliente_llm, args.model)
    except (ValueError, ConnectionError) as error:
        print(f"Fallo en el procesamiento del LLM: {error}", file=sys.stderr)
        return EXIT_ERROR_LLM

    salud = SaludMotores(activa=args.salud != "off")
    if args.salud == "reset":
        salud.reiniciar()
        if args.verbose:
            print("Historial de salud de motores borrado.")

    agregador = AgregadorTorrents(
        motores=motores,
        paralelo=not args.secuencial,
        pausa=(0.2, 0.6),
        salud=salud,
        limetorrents_paginas=args.limetorrents_paginas,
    )
    try:
        items, resumen = agregador.buscar_con_diagnostico(
            extraido["query"],
            extraido["categoria"],
            args.min_seeders,
            exigir_coincidencia=not args.sin_relevancia,
            resolver_imdb=not args.no_imdb,
        )
    finally:
        agregador.cerrar()

    if args.salida_json:
        print(json.dumps(_payload_json(extraido, items, resumen), ensure_ascii=False, indent=2))
    elif items:
        if args.verbose:
            print(f"Extracción LLM: query='{extraido['query']}' categoria='{extraido['categoria']}'")
            print(resumen.formatear())
            print()
        limite = max(1, args.all)
        for posicion, item in enumerate(items[:limite], start=1):
            print(formatear_item(item, None if limite == 1 else posicion))
            if posicion < min(limite, len(items)):
                print()
        if len(items) > limite:
            print(f"\n({len(items)} resultados disponibles; usa -n {len(items)} para verlos todos)")
    else:
        print("No results found matching criteria.", file=sys.stderr)
        print(resumen.formatear(), file=sys.stderr)

    if items:
        return EXIT_OK
    if not resumen.motores_ok and resumen.motores_fallidos:
        return EXIT_MOTORES_CAIDOS
    return EXIT_SIN_RESULTADOS


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Punto de entrada. Devuelve el código de salida."""
    parser = construir_parser()
    args = parser.parse_args(argv)
    if args.all < 1:
        parser.error("--all debe ser >= 1")
    if args.min_seeders < 0:
        parser.error("--min-seeders debe ser >= 0")
    if args.limetorrents_paginas < 1:
        parser.error("--limetorrents-paginas debe ser >= 1")
    try:
        return ejecutar(args)
    except KeyboardInterrupt:
        print("Interrumpido por el usuario.", file=sys.stderr)
        return EXIT_INTERRUMPIDO


if __name__ == "__main__":
    sys.exit(main())
