#!/usr/bin/env python3
"""Verificación en vivo de los motores de VANTAGE.

Comprueba, contra la red real, dos cosas:

1. **Salud de mirrors**: qué dominio de cada motor responde, con qué código HTTP y
   cuánta latencia (los mirrors de estos índices cambian de dominio con frecuencia:
   ``yts.mx`` dejó de resolver y ``yts.gg`` funciona; ``eztv.re`` redirige a
   ``eztvx.to``; ``limetorrents.lol`` redirige a ``limetorrents.fun``).
2. **Funcionalidad**: cuántos items devuelve cada motor para una consulta real, con
   los motivos de fallo explícitos.

Uso::

    source venv/bin/activate
    python3 scripts/verificar_engines.py
    python3 scripts/verificar_engines.py --query "Severance" --categoria tv
    python3 scripts/verificar_engines.py --salida VERIFICACION_ENGINES.md

Códigos de salida: 0 si al menos un motor devolvió resultados, 1 si ninguno.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import requests  # noqa: E402

import engines  # noqa: E402
from engines import AgregadorTorrents, EstadoMotor, Motor  # noqa: E402

TIMEOUT_SONDEO = 15.0


@dataclass
class Sonda:
    """Configuración para comprobar la salud de los mirrors de un motor."""

    motor: str
    bases: Sequence[str]
    ruta: str
    params: Dict[str, Any] = field(default_factory=dict)
    validador: Optional[Any] = None
    cabeceras: Optional[Dict[str, str]] = None


@dataclass
class ResultadoSonda:
    """Resultado de comprobar un mirror concreto."""

    motor: str
    base: str
    ok: bool
    latencia_ms: int
    detalle: str


SONDAS: Tuple[Sonda, ...] = (
    Sonda("YTS", engines.BASE_URLS_YTS, engines.RUTA_YTS,
          {"query_term": "Oppenheimer", "limit": 2}, engines._validar_yts,
          {"User-Agent": engines.AGENTE_NAVEGADOR}),
    Sonda("LimeTorrents", engines.BASE_URLS_LIME, "/search/all/oppenheimer/seeds/1/",
          {}, None, engines.CABECERAS_NAVEGADOR),
    Sonda("MagnetDL", engines.BASE_URLS_MAGNETDL, "/o/oppenheimer/",
          {}, None, engines.CABECERAS_NAVEGADOR),
    Sonda("EZTV", engines.BASE_URLS_EZTV, engines.RUTA_EZTV,
          {"imdb_id": "11280740", "limit": 2}, engines._validar_eztv,
          {"User-Agent": engines.AGENTE_NAVEGADOR}),
    Sonda("Nyaa", engines.BASE_URLS_NYAA, "/",
          {"q": "dune", "s": "seeders", "o": "desc"}, None, engines.CABECERAS_NAVEGADOR),
)


def sondear_mirror(sonda: Sonda, base: str) -> ResultadoSonda:
    """Comprueba un mirror concreto y describe el resultado en una línea."""
    url = base.rstrip("/") + sonda.ruta
    inicio = time.monotonic()
    try:
        respuesta = requests.get(url, params=sonda.params, headers=sonda.cabeceras, timeout=TIMEOUT_SONDEO)
        latencia = int((time.monotonic() - inicio) * 1000)
        respuesta.raise_for_status()
        if sonda.validador is not None:
            sonda.validador(respuesta)
        return ResultadoSonda(sonda.motor, base, True, latencia, f"HTTP {respuesta.status_code}, contenido válido")
    except requests.RequestException as error:
        latencia = int((time.monotonic() - inicio) * 1000)
        return ResultadoSonda(sonda.motor, base, False, latencia, _resumir(error))
    except engines.ErrorEstructura as error:
        latencia = int((time.monotonic() - inicio) * 1000)
        return ResultadoSonda(sonda.motor, base, False, latencia, _resumir(error))


def _resumir(error: Exception) -> str:
    """Mensaje corto y legible de una excepción."""
    texto = str(error).replace("\n", " ")
    if isinstance(error, requests.ConnectionError) and "NameResolutionError" in texto:
        return "DNS no resuelve"
    if isinstance(error, requests.ConnectionError) and "Max retries" in texto:
        return "timeout / conexión rechazada"
    return texto[:110]


def sondear_todo() -> List[ResultadoSonda]:
    """Comprueba todos los mirrors de todos los motores."""
    resultados: List[ResultadoSonda] = []
    for sonda in SONDAS:
        for base in sonda.bases:
            resultados.append(sondear_mirror(sonda, base))
    return resultados


def probar_motores(
    query: str,
    categoria: str,
    min_seeders: int,
    *,
    paralelo: bool = True,
) -> Tuple[List[Dict[str, Any]], Any]:
    """Ejecuta la búsqueda agregada real y devuelve items + resumen."""
    agregador = AgregadorTorrents(paralelo=paralelo, timeout=TIMEOUT_SONDEO)
    try:
        return agregador.buscar_con_diagnostico(
            query, categoria, min_seeders, exigir_coincidencia=True, resolver_imdb=True
        )
    finally:
        agregador.session.close()


def formatear_informe(
    query: str,
    categoria: str,
    min_seeders: int,
    sondas: Sequence[ResultadoSonda],
    items: Sequence[Dict[str, Any]],
    resumen: Any,
    *,
    top: int = 3,
) -> str:
    """Construye el informe en markdown."""
    momento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lineas: List[str] = [
        f"# VANTAGE - verificación de motores ({momento})",
        "",
        f"- Consulta: `{query}`",
        f"- Categoría: `{categoria}`",
        f"- Sembradores mínimos: `{min_seeders}`",
        "",
        "## Salud de mirrors",
        "",
        "| Motor | Mirror | Estado | Latencia | Detalle |",
        "| --- | --- | --- | --- | --- |",
    ]
    for sonda in sondas:
        estado = "OK" if sonda.ok else "FALLO"
        lineas.append(f"| {sonda.motor} | `{sonda.base}` | {estado} | {sonda.latencia_ms} ms | {sonda.detalle} |")

    lineas += ["", "## Resultados por motor", "", "| Motor | Estado | Items | Tiempo | Detalle |", "| --- | --- | --- | --- | --- |"]
    for estado in resumen.estados:
        situacion = "omitido" if estado.omitido else ("OK" if estado.ok else "FALLO")
        detalle = estado.error or "-"
        lineas.append(
            f"| {estado.nombre} | {situacion} | {estado.resultados} | {estado.milisegundos} ms | {detalle[:120]} |"
        )

    lineas += [
        "",
        f"**Totales:** {resumen.brutos} items brutos, {resumen.unicos} únicos, "
        f"{resumen.descartados_relevancia} descartados por relevancia, "
        f"{len(items)} tras filtros. IMDb id: `{resumen.imdb_id or 'no resuelto'}`.",
        "",
    ]

    if items:
        lineas += [f"## Top {min(top, len(items))} por estabilidad", ""]
        for posicion, item in enumerate(items[:top], start=1):
            lineas.append(
                f"{posicion}. **{item['title']}** — {item['seeders']} sembradores / "
                f"{item['leechers']} descargadores — {item['size']} — `{item['source']}`"
            )
        lineas.append("")

    motores_con_datos = [estado.nombre for estado in resumen.motores_ok if estado.resultados]
    lineas.append(
        f"**Veredicto:** {len(motores_con_datos)}/{len(resumen.motores_ok)} motores activos devolvieron "
        f"resultados ({', '.join(motores_con_datos) or 'ninguno'})."
    )
    return "\n".join(lineas)


def _escribir_informe(destino: Path, informe: str, *, forzar: bool = False) -> None:
    """Escribe el informe, negándose a pisar archivos que no sean informes.

    ``--salida engines.py`` destruía el motor sin avisar: la herramienta se documenta
    como sondeo, no como escritor destructivo.
    """
    if destino.suffix.lower() not in (".md", ".txt") and not forzar:
        raise SystemExit(
            f"«{destino}» no parece un informe (.md o .txt). Usa --forzar si es intencional."
        )
    destino.write_text(informe + "\n", encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Punto de entrada del verificador."""
    parser = argparse.ArgumentParser(description="Verifica en vivo los motores de VANTAGE.")
    parser.add_argument("-q", "--query", default="Oppenheimer 2023", help="Consulta de prueba")
    parser.add_argument("-c", "--categoria", default="movies", help="Categoría canónica")
    parser.add_argument("-s", "--min-seeders", type=int, default=5, help="Sembradores mínimos")
    parser.add_argument("--salida", help="Ruta donde guardar el informe en markdown (.md o .txt)")
    parser.add_argument("--forzar", action="store_true",
                        help="Permite escribir el informe en un archivo con otra extensión")
    parser.add_argument("--json", action="store_true", dest="salida_json", help="Imprime JSON en lugar del informe")
    parser.add_argument("--sin-sondeo", action="store_true", help="Omite el sondeo de mirrors")
    args = parser.parse_args(argv)

    sondas = [] if args.sin_sondeo else sondear_todo()
    items, resumen = probar_motores(args.query, args.categoria, args.min_seeders)

    if args.salida_json:
        print(json.dumps(
            {
                "consulta": args.query,
                "categoria": args.categoria,
                "mirrors": [vars(sonda) for sonda in sondas],
                "motores": [vars(estado) for estado in resumen.estados],
                "items": list(items),
            },
            ensure_ascii=False,
            indent=2,
        ))
    else:
        informe = formatear_informe(args.query, args.categoria, args.min_seeders, sondas, items, resumen)
        print(informe)
        if args.salida:
            _escribir_informe(Path(args.salida), informe, forzar=args.forzar)
            print(f"\nInforme guardado en {Path(args.salida).resolve()}", file=sys.stderr)

    # Criterio documentado: 0 si algún motor devolvió resultados. ``items`` ya pasó el
    # filtro de relevancia, así que puede quedar vacío con motores que sí respondieron.
    return 0 if resumen.brutos else 1


if __name__ == "__main__":
    sys.exit(main())
