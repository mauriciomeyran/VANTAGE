"""Orquestador de línea de comandos de VANTAGE.

Flujo: lenguaje natural -> extracción con LLM local -> búsqueda agregada en los
motores -> impresión del resultado más estable (o de los N mejores).

Cuando una búsqueda no devuelve nada, el diagnóstico por motor se imprime en
``stderr``: el usuario ve *qué* motor falló y por qué, en lugar de un genérico
"no hay resultados".

Códigos de salida
-----------------
====  ============================================
0     resultado encontrado (o ayuda mostrada)
2     ningún item superó los filtros
3     fallo del LLM (conexión o parseo)
4     todos los motores fallaron
130   interrupción por teclado
====  ============================================
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Sequence

from ai_agent import MODELO_POR_DEFECTO, procesar_peticion_usuario
from engines import AgregadorTorrents, ResumenBusqueda

HOST_OLLAMA_POR_DEFECTO = "http://localhost:11434"
SEEDERS_MINIMOS_POR_DEFECTO = 5

EXIT_OK = 0
EXIT_SIN_RESULTADOS = 2
EXIT_ERROR_LLM = 3
EXIT_MOTORES_CAIDOS = 4
EXIT_INTERRUMPIDO = 130


def construir_parser() -> argparse.ArgumentParser:
    """Define la interfaz de línea de comandos."""
    parser = argparse.ArgumentParser(
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
        cliente_llm = conectar_llm(args.host)
    except ConnectionError as error:
        print(f"Error de conexión con Ollama: {error}", file=sys.stderr)
        return EXIT_ERROR_LLM

    try:
        extraido = extraer_parametros(consulta, cliente_llm, args.model)
    except (ValueError, ConnectionError) as error:
        print(f"Fallo en el procesamiento del LLM: {error}", file=sys.stderr)
        return EXIT_ERROR_LLM

    agregador = AgregadorTorrents(paralelo=not args.secuencial, pausa=(0.2, 0.6))
    items, resumen = agregador.buscar_con_diagnostico(
        extraido["query"],
        extraido["categoria"],
        args.min_seeders,
        exigir_coincidencia=not args.sin_relevancia,
        resolver_imdb=not args.no_imdb,
    )

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
    try:
        return ejecutar(args)
    except KeyboardInterrupt:
        print("Interrumpido por el usuario.", file=sys.stderr)
        return EXIT_INTERRUMPIDO


if __name__ == "__main__":
    sys.exit(main())
