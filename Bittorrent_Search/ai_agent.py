"""Extracción de parámetros de búsqueda a partir de lenguaje natural (Ollama).

Contrato
--------
``procesar_peticion_usuario(texto_usuario, cliente_llm, model) -> dict`` devuelve
siempre::

    {"query": str, "categoria": str}

``categoria`` se normaliza a las categorías canónicas de :mod:`texto`
(``movies``, ``tv``, ``anime``, ``music``, ``games``, ``applications``, ``books``,
``all``), de modo que "película", "movie", "Peliculas" y "cine" produzcan el mismo
valor y ningún motor reciba una categoría inventada por el modelo.

El cliente LLM se inyecta (dependencia), así que este módulo no importa
``ollama`` y se puede probar con un doble de prueba.
"""

from __future__ import annotations

import ast
import json
import logging
import re
from typing import Any, Dict, Optional

from texto import normalizar_categoria

logger = logging.getLogger(__name__)

MODELO_POR_DEFECTO = "qwen2.5:7b"

SYSTEM_PROMPT = """You are a query extraction system. Extract the search query and category from the user's input.
Output ONLY raw JSON in this exact format: {"query": string, "categoria": string}
No markdown code blocks, no explanation, no conversational text. Raw JSON only."""

#: Claves aceptadas como "query" y como "categoría" en la respuesta del modelo.
CLAVES_QUERY = ("query", "consulta", "busqueda", "búsqueda", "titulo", "título", "term")
CLAVES_CATEGORIA = ("categoria", "categoría", "category", "tipo", "type", "genero", "género")


def procesar_peticion_usuario(
    texto_usuario: str,
    cliente_llm: Any,
    model: str = MODELO_POR_DEFECTO,
) -> Dict[str, str]:
    """Extrae ``query`` y ``categoria`` de la petición en lenguaje natural.

    Args:
        texto_usuario: Petición del usuario ("Busca la película Oppenheimer").
        cliente_llm: Cliente ``ollama.Client`` ya construido (inyección de dependencia).
        model: Nombre del modelo local en Ollama.

    Returns:
        ``{"query": str, "categoria": str}`` con la categoría ya normalizada.

    Raises:
        ValueError: Si el modelo no devuelve un JSON con una ``query`` utilizable.
        ConnectionError: Si la llamada al LLM falla.
    """
    if not texto_usuario or not texto_usuario.strip():
        raise ValueError("texto_usuario vacío")

    mensajes = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": texto_usuario},
    ]

    try:
        respuesta = _llamar_chat(cliente_llm, model, mensajes)
    except Exception as error:  # la causa raíz puede ser httpx, ConnectionError, etc.
        raise ConnectionError(f"LLM request failed: {error}") from error

    salida = _contenido_respuesta(respuesta)
    if not salida:
        raise ValueError("el LLM devolvió una respuesta vacía")

    datos = extraer_json(salida)
    if not isinstance(datos, dict) or not datos:
        raise ValueError(f"Failed to parse JSON from LLM output: {salida!r}")

    query = _primera_clave(datos, CLAVES_QUERY)
    if not query or not str(query).strip():
        raise ValueError(f"Missing required key 'query' in parsed JSON: {datos}")

    categoria_cruda = _primera_clave(datos, CLAVES_CATEGORIA)

    return {
        "query": str(query).strip(),
        "categoria": normalizar_categoria(str(categoria_cruda) if categoria_cruda is not None else None),
    }


def _llamar_chat(cliente_llm: Any, model: str, mensajes: list[dict[str, str]]) -> Any:
    """Llama a ``chat`` pidiendo JSON nativo de Ollama, con repliegue si no se soporta.

    ``format="json"`` restringe la decodificación del modelo a JSON válido; algunos
    clientes/modelos antiguos no aceptan el parámetro, así que se reintenta sin él.
    """
    try:
        return cliente_llm.chat(model=model, messages=mensajes, stream=False, format="json")
    except TypeError:
        logger.debug("el cliente LLM no acepta format='json'; se reintenta sin restricción")
        return cliente_llm.chat(model=model, messages=mensajes, stream=False)


def _contenido_respuesta(respuesta: Any) -> str:
    """Extrae el texto del mensaje soportando respuesta tipo dict o tipo objeto."""
    if respuesta is None:
        return ""
    if isinstance(respuesta, dict):
        mensaje = respuesta.get("message") or {}
        if isinstance(mensaje, dict):
            return str(mensaje.get("content") or "").strip()
        return str(getattr(mensaje, "content", "") or "").strip()
    mensaje = getattr(respuesta, "message", None)
    if mensaje is not None:
        contenido = mensaje.get("content") if isinstance(mensaje, dict) else getattr(mensaje, "content", None)
        if contenido:
            return str(contenido).strip()
    return str(getattr(respuesta, "content", "") or "").strip()


def _primera_clave(datos: Dict[str, Any], claves: tuple[str, ...]) -> Optional[Any]:
    """Primera clave presente entre ``claves``, comparando sin acentos ni mayúsculas."""
    plano = {str(clave).strip().lower(): valor for clave, valor in datos.items()}
    for clave in claves:
        if clave in plano:
            return plano[clave]
    normalizado_plano = {re.sub(r"[^a-z]", "", clave): valor for clave, valor in plano.items()}
    for clave in claves:
        candidato = re.sub(r"[^a-z]", "", clave)
        if candidato in normalizado_plano:
            return normalizado_plano[candidato]
    return None


def extraer_json(salida: str) -> Optional[Dict[str, Any]]:
    """Extrae un objeto JSON de la salida del modelo con recuperación por capas.

    Orden de intentos:

    1. ``json.loads`` directo.
    2. Eliminando bloques markdown ```` ```json ````.
    3. El primer objeto ``{...}`` embebido en texto conversacional.
    4. Ese objeto reparado (comas finales) y, si es un dict de Python con comillas
       simples, ``ast.literal_eval``.

    Returns:
        El dict parseado o ``None`` si ninguna estrategia funciona.
    """
    if not salida:
        return None

    texto = salida.strip()
    candidatos = [texto]

    sin_markdown = re.sub(r"```(?:json)?", "", texto).strip()
    candidatos.append(sin_markdown)

    for candidato in list(candidatos):
        coincidencia = re.search(r"\{.*\}", candidato, re.DOTALL)
        if coincidencia:
            candidatos.append(coincidencia.group(0))

    for candidato in candidatos:
        limpio = candidato.strip()
        if not limpio:
            continue
        try:
            datos = json.loads(limpio)
            if isinstance(datos, dict):
                return datos
        except json.JSONDecodeError:
            pass

        reparado = re.sub(r",\s*([}\]])", r"\1", limpio)
        try:
            datos = json.loads(reparado)
            if isinstance(datos, dict):
                return datos
        except json.JSONDecodeError:
            pass

        if "'" in reparado:
            try:
                datos = ast.literal_eval(reparado)
                if isinstance(datos, dict):
                    return datos
            except (ValueError, SyntaxError):
                pass

    return None


#: Alias retrocompatible con la versión anterior del módulo.
_extract_json_from_output = extraer_json
