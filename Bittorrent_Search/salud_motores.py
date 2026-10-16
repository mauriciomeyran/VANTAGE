#!/usr/bin/env python3
"""Salud persistente de los motores: no volver a esperar a un índice caído.

Contexto
--------
Un índice caído cuesta su timeout completo en **cada** búsqueda: medido el 2026-10-14,
MagnetDL (HTTP 522) aportaba ~12 s de los ~15 s de una búsqueda. El CLI lanza un proceso
por búsqueda, así que recordarlo en memoria no sirve de nada: hay que persistirlo.

Política
--------
- **Dos fallos consecutivos** marcan un motor como degradado. Cualquier éxito lo limpia.
- Degradado y con el último intento **dentro del TTL** (30 min): el motor no se consulta
  (coste cero) y el diagnóstico lo declara.
- Degradado y TTL vencido: se **vuelve a intentar** con un timeout reducido (3 s en vez de
  12). Ese intento *es* el sondeo: si el índice revivió, vuelve a aportar solo.
- Sólo cuentan los fallos de **fuente** (red, HTTP, estructura). Un fallo de resolución de
  IMDb no degrada EZTV: eso es un problema de la consulta, no del índice.

El estado vive en un JSON legible junto al proyecto (`.estado_motores.json`) y se escribe
de forma atómica, para que un corte a mitad no lo corrompa.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

RAIZ = Path(__file__).resolve().parent
ARCHIVO_POR_DEFECTO = RAIZ / ".estado_motores.json"

#: Fallos consecutivos necesarios para marcar un motor como degradado.
FALLOS_PARA_DEGRADAR = 2
#: Cuánto se recuerda un motor degradado antes de volver a sondearlo (segundos).
TTL_DEGRADADO = 30 * 60
#: Timeout aplicado a un motor degradado en su reintento de sondeo (segundos).
TIMEOUT_DEGRADADO = 3.0


@dataclass
class Decision:
    """Qué hacer con un motor en esta búsqueda."""

    #: ``True`` si no hay que consultarlo (degradado y dentro del TTL).
    saltar: bool = False
    #: Timeout a usar en la petición (``None`` = el del agregador).
    timeout: Optional[float] = None
    #: Explicación para el diagnóstico (``None`` si el motor está sano).
    motivo: Optional[str] = None

    @property
    def degradado(self) -> bool:
        return self.motivo is not None


@dataclass
class EstadoMotorSalud:
    """Historial de un motor."""

    nombre: str
    fallos_consecutivos: int = 0
    ultimo_fallo: Optional[float] = None
    ultimo_exito: Optional[float] = None
    ultimo_intento: Optional[float] = None
    ultimo_error: Optional[str] = None

    def como_dict(self) -> Dict[str, Any]:
        datos = asdict(self)
        for clave in ("ultimo_fallo", "ultimo_exito", "ultimo_intento"):
            valor = datos[clave]
            datos[clave] = _a_iso(valor) if valor else None
        return datos


def _a_iso(marca: Optional[float]) -> Optional[str]:
    """Convierte una marca de tiempo epoch a ISO local legible."""
    if not marca:
        return None
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(marca))


def _a_epoch(valor: Any) -> Optional[float]:
    """Acepta número o ISO y devuelve epoch; ``None`` si no se puede."""
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    for formato in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return time.mktime(time.strptime(str(valor), formato))
        except ValueError:
            continue
    return None


class SaludMotores:
    """Registro persistente de la salud de cada motor.

    Es inyectable (el agregador la recibe como dependencia), tiene reloj configurable
    para poder probarla sin esperar y se puede desactivar con ``activa=False``.
    """

    def __init__(
        self,
        ruta: Optional[Path] = None,
        *,
        activa: bool = True,
        fallos_para_degradar: int = FALLOS_PARA_DEGRADAR,
        ttl: float = TTL_DEGRADADO,
        timeout_degradado: float = TIMEOUT_DEGRADADO,
        reloj: Callable[[], float] = time.time,
    ) -> None:
        self.ruta = Path(ruta) if ruta else ARCHIVO_POR_DEFECTO
        self.activa = activa
        self.fallos_para_degradar = max(1, fallos_para_degradar)
        self.ttl = ttl
        self.timeout_degradado = timeout_degradado
        self.reloj = reloj
        self._estado: Optional[Dict[str, EstadoMotorSalud]] = None
        # Reentrante: ``guardar()`` llama a ``cargar()`` con el candado tomado. El
        # agregador usa esta clase desde varios hilos cuando busca en paralelo.
        self._candado = threading.RLock()

    # -- persistencia ------------------------------------------------------
    def cargar(self) -> Dict[str, EstadoMotorSalud]:
        """Lee el estado del disco; un archivo ausente o ilegible equivale a vacío."""
        with self._candado:
            return self._cargar_sin_candado()

    def _cargar_sin_candado(self) -> Dict[str, EstadoMotorSalud]:
        if self._estado is not None:
            return self._estado

        estado: Dict[str, EstadoMotorSalud] = {}
        if self.ruta.is_file():
            try:
                crudo = json.loads(self.ruta.read_text(encoding="utf-8"))
                for nombre, datos in (crudo.get("motores") or {}).items():
                    if not isinstance(datos, dict):
                        continue
                    estado[nombre] = EstadoMotorSalud(
                        nombre=nombre,
                        fallos_consecutivos=int(datos.get("fallos_consecutivos") or 0),
                        ultimo_fallo=_a_epoch(datos.get("ultimo_fallo")),
                        ultimo_exito=_a_epoch(datos.get("ultimo_exito")),
                        ultimo_intento=_a_epoch(datos.get("ultimo_intento")),
                        ultimo_error=datos.get("ultimo_error"),
                    )
            except (OSError, ValueError, TypeError) as error:
                logger.debug("estado de salud ilegible en %s (%s): se empieza de cero", self.ruta, error)

        self._estado = estado
        return estado

    def guardar(self) -> None:
        """Escribe el estado de forma atómica (temporal + rename).

        Itera sobre una **instantánea**: con búsquedas en paralelo, otro hilo puede
        insertar la clave de un motor mientras se recorre el diccionario, y eso lanzaba
        ``RuntimeError: dictionary changed size during iteration``.
        """
        if not self.activa:
            return
        with self._candado:
            datos = {
                "version": 1,
                "actualizado": _a_iso(self.reloj()),
                "motores": {
                    nombre: motor.como_dict() for nombre, motor in dict(self.cargar()).items()
                },
            }
            try:
                self.ruta.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(
                    "w", encoding="utf-8", dir=self.ruta.parent, prefix=self.ruta.name, suffix=".tmp", delete=False
                ) as temporal:
                    json.dump(datos, temporal, ensure_ascii=False, indent=2)
                    ruta_temporal = Path(temporal.name)
                os.replace(ruta_temporal, self.ruta)
            except Exception as error:  # persistir es una optimización, nunca un riesgo
                logger.warning("no se pudo guardar el estado de salud en %s: %s", self.ruta, error)

    def reiniciar(self) -> None:
        """Borra el estado en memoria y en disco."""
        with self._candado:
            self._estado = {}
        try:
            self.ruta.unlink(missing_ok=True)
        except OSError as error:
            logger.warning("no se pudo borrar %s: %s", self.ruta, error)

    # -- política ----------------------------------------------------------
    def decision(self, nombre: str, *, timeout_normal: Optional[float] = None) -> Decision:
        """Decide si consultar un motor y con qué timeout.

        Args:
            nombre: Nombre del motor.
            timeout_normal: Timeout del agregador (informativo).

        Returns:
            :class:`Decision` con ``saltar``, ``timeout`` y ``motivo``.
        """
        if not self.activa:
            return Decision()

        motor = self.cargar().get(nombre)
        if motor is None or motor.fallos_consecutivos < self.fallos_para_degradar:
            return Decision()

        desde = motor.ultimo_intento or motor.ultimo_fallo or 0
        antiguedad = self.reloj() - desde
        if antiguedad < self.ttl:
            minutos = int(antiguedad // 60)
            return Decision(
                saltar=True,
                motivo=(
                    f"degradado: {motor.fallos_consecutivos} fallos consecutivos, "
                    f"último intento hace {minutos} min (reintento en {int((self.ttl - antiguedad) // 60)} min)"
                ),
            )

        return Decision(
            timeout=self.timeout_degradado,
            motivo=(
                f"degradado: reintento de sondeo con timeout {self.timeout_degradado:g}s "
                f"tras {int(antiguedad // 60)} min sin intentarlo"
            ),
        )

    def registrar(self, nombre: str, *, exito: bool, error: Optional[str] = None) -> None:
        """Anota un intento y persiste el estado."""
        if not self.activa:
            return

        # Mutar y persistir dentro del candado: en paralelo, dos motores que terminan a
        # la vez insertaban claves mientras otro hilo iteraba el estado.
        with self._candado:
            ahora = self.reloj()
            motor = self._cargar_sin_candado().get(nombre) or EstadoMotorSalud(nombre=nombre)
            motor.ultimo_intento = ahora

            if exito:
                motor.fallos_consecutivos = 0
                motor.ultimo_exito = ahora
                motor.ultimo_error = None
            else:
                motor.fallos_consecutivos += 1
                motor.ultimo_fallo = ahora
                motor.ultimo_error = (error or "error desconocido")[:200]

            self._cargar_sin_candado()[nombre] = motor
            self.guardar()

    def resumen(self) -> List[Dict[str, Any]]:
        """Estado legible de todos los motores conocidos, para diagnóstico."""
        filas: List[Dict[str, Any]] = []
        for nombre, motor in sorted(self.cargar().items()):
            degradado = motor.fallos_consecutivos >= self.fallos_para_degradar
            filas.append(
                {
                    "nombre": nombre,
                    "degradado": degradado,
                    "fallos_consecutivos": motor.fallos_consecutivos,
                    "ultimo_exito": _a_iso(motor.ultimo_exito),
                    "ultimo_fallo": _a_iso(motor.ultimo_fallo),
                    "ultimo_error": motor.ultimo_error,
                }
            )
        return filas


def formatear_resumen(filas: List[Dict[str, Any]]) -> str:
    """Tabla de salud para terminal."""
    if not filas:
        return "Sin historial de motores todavía."
    lineas = [f"{'MOTOR':<14} {'ESTADO':<10} {'FALLOS':>6}  ÚLTIMO ERROR"]
    for fila in filas:
        estado = "degradado" if fila["degradado"] else "sano"
        lineas.append(
            f"{fila['nombre']:<14} {estado:<10} {fila['fallos_consecutivos']:>6}  {(fila['ultimo_error'] or '-')[:60]}"
        )
    return "\n".join(lineas)
