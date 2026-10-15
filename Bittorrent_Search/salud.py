#!/usr/bin/env python3
"""Comprobación del estado del backend, para la app y para diagnóstico rápido.

Responde a la pregunta "¿por qué no funciona?" **antes** de lanzar una búsqueda: si el
intérprete, el script, las dependencias, Ollama o el modelo faltan, lo dice con un JSON
claro en lugar de fallar a mitad de la búsqueda.

Uso::

    python3 salud.py            # informe legible
    python3 salud.py --json     # JSON para la app

Códigos de salida: 0 si todo está correcto, 65 si alguna comprobación falla.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from salud_motores import SaludMotores, formatear_resumen

RAIZ = Path(__file__).resolve().parent
HOST_OLLAMA_POR_DEFECTO = "http://localhost:11434"
MODELO_POR_DEFECTO = "qwen2.5:7b"
TIMEOUT_OLLAMA = 4.0
EXIT_OK = 0
EXIT_FALLO = 65


def comprobar_interprete(ruta: Optional[str] = None) -> Dict[str, Any]:
    """Verifica que exista un intérprete de Python utilizable."""
    candidato = Path(ruta) if ruta else Path(sys.executable)
    if not candidato.exists():
        return {"nombre": "intérprete", "ok": False, "detalle": f"no existe: {candidato}"}
    version = sys.version.split()[0] if candidato == Path(sys.executable) else "desconocida"
    return {"nombre": "intérprete", "ok": True, "detalle": f"{candidato} (Python {version})"}


def comprobar_entrada(raiz: Path = RAIZ) -> Dict[str, Any]:
    """Verifica que exista el script de entrada del backend."""
    entrada = raiz / "main.py"
    if not entrada.is_file():
        return {"nombre": "main.py", "ok": False, "detalle": f"no existe: {entrada}"}
    return {"nombre": "main.py", "ok": True, "detalle": str(entrada)}


def comprobar_dependencias(importador: Any = None) -> Dict[str, Any]:
    """Comprueba que estén instaladas las dependencias de ejecución."""
    import importlib

    modulo_import = importador or importlib.import_module
    faltantes: List[str] = []
    presentes: List[str] = []
    for nombre in ("requests", "bs4", "ollama"):
        try:
            modulo_import(nombre)
            presentes.append(nombre)
        except ImportError:
            faltantes.append(nombre)
    return {
        "nombre": "dependencias",
        "ok": not faltantes,
        "detalle": (
            f"instaladas: {', '.join(presentes)}"
            if not faltantes
            else f"faltan: {', '.join(faltantes)} (pip install -r requirements.txt)"
        ),
    }


def comprobar_ollama(
    host: str = HOST_OLLAMA_POR_DEFECTO,
    modelo: str = MODELO_POR_DEFECTO,
    *,
    timeout: float = TIMEOUT_OLLAMA,
    session: Any = None,
) -> List[Dict[str, Any]]:
    """Comprueba que Ollama responda y que el modelo esté descargado.

    Returns:
        Dos comprobaciones: ``ollama`` (servicio) y ``modelo`` (modelo concreto).
    """
    try:
        import requests
    except ImportError as error:  # pragma: no cover - dependencia obligatoria
        return [
            {"nombre": "ollama", "ok": False, "detalle": f"falta el paquete requests: {error}"},
            {"nombre": "modelo", "ok": False, "detalle": "no comprobable sin requests"},
        ]

    agente = session or requests
    try:
        respuesta = agente.get(f"{host.rstrip('/')}/api/tags", timeout=timeout)
        respuesta.raise_for_status()
        datos = respuesta.json()
    except Exception as error:  # requests.RequestException y JSON inválido
        return [
            {
                "nombre": "ollama",
                "ok": False,
                "detalle": f"no responde en {host}: {type(error).__name__}. Arráncalo con 'ollama serve'",
            },
            {"nombre": "modelo", "ok": False, "detalle": "no comprobable sin servicio"},
        ]

    disponibles = [str(m.get("name", "")) for m in (datos.get("models") or [])]
    servicio = {"nombre": "ollama", "ok": True, "detalle": f"{host} ({len(disponibles)} modelo(s))"}

    coincide = any(nombre == modelo or nombre.split(":")[0] == modelo.split(":")[0] for nombre in disponibles)
    if coincide:
        return [servicio, {"nombre": "modelo", "ok": True, "detalle": f"'{modelo}' disponible"}]

    return [
        servicio,
        {
            "nombre": "modelo",
            "ok": False,
            "detalle": f"'{modelo}' no está descargado. Instálalo con 'ollama pull {modelo}'. "
            f"Disponibles: {', '.join(disponibles) or 'ninguno'}",
        },
    ]


def informe(
    host: str = HOST_OLLAMA_POR_DEFECTO,
    modelo: str = MODELO_POR_DEFECTO,
    *,
    raiz: Path = RAIZ,
    interprete: Optional[str] = None,
    session: Any = None,
    salud: Optional[SaludMotores] = None,
) -> Dict[str, Any]:
    """Reúne todas las comprobaciones en un único informe."""
    comprobaciones = [
        comprobar_interprete(interprete),
        comprobar_entrada(raiz),
        comprobar_dependencias(),
        *comprobar_ollama(host, modelo, session=session),
    ]
    return {
        "ok": all(c["ok"] for c in comprobaciones),
        "raiz": str(raiz),
        "host": host,
        "modelo": modelo,
        "checks": comprobaciones,
        "motores": (salud or SaludMotores()).resumen(),
    }


def formatear(datos: Dict[str, Any]) -> str:
    """Informe legible para terminal."""
    lineas = [
        f"Backend: {datos['raiz']}",
        f"Ollama:  {datos['host']}   Modelo: {datos['modelo']}",
        "",
    ]
    for comprobacion in datos["checks"]:
        marca = "OK   " if comprobacion["ok"] else "FALLO"
        lineas.append(f"[{marca}] {comprobacion['nombre']:<14} {comprobacion['detalle']}")
    motores = datos.get("motores") or []
    lineas.append("")
    lineas.append("Salud de los motores (historial persistente):")
    lineas.append(formatear_resumen(motores))
    lineas.append("")
    lineas.append("Todo correcto." if datos["ok"] else "Hay comprobaciones fallidas: revisa las líneas [FALLO].")
    return "\n".join(lineas)


def main(argv: Optional[List[str]] = None) -> int:
    """Punto de entrada del verificador."""
    parser = argparse.ArgumentParser(description="Comprueba el estado del backend de VANTAGE.")
    parser.add_argument("--host", default=os.environ.get("OLLAMA_HOST", HOST_OLLAMA_POR_DEFECTO))
    parser.add_argument("--model", default=MODELO_POR_DEFECTO)
    parser.add_argument("--json", action="store_true", dest="salida_json")
    args = parser.parse_args(argv)

    datos = informe(host=args.host, modelo=args.model)
    print(json.dumps(datos, ensure_ascii=False, indent=2) if args.salida_json else formatear(datos))
    return EXIT_OK if datos["ok"] else EXIT_FALLO


if __name__ == "__main__":
    sys.exit(main())
