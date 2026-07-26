#!/usr/bin/env python3
"""
vsum — VANTAGE Session Summarizer
=================================
Resume transcripts de sesiones de Claude / Gemini / ChatGPT / etc.
Orientado a continuidad entre chats e IAs: contexto, findings, acuerdos y action items.

Uso típico:
  vsum chat.md
  vsum https://claude.ai/share/79dbdbab-6d1b-4806-a69d-8edf61a23a1f
  vsum chat.md --notion
  vsum *.md --batch --notion
  vsum chat.md --model groq
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import re
from dateutil.parser import parse as date_parse
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

INBOX_PARENT_ID = "f30938be-fc42-824a-ad9b-01c5305c73f3"  # tu INBOX

MAX_CHARS_PER_CHUNK = 28000  # seguro para la mayoría de modelos
DEFAULT_MODEL = "groq"

SUMMARY_SYSTEM = """Eres un asistente especializado en resumir sesiones de trabajo técnico con IAs (Claude, Gemini, ChatGPT, etc.).

Tu objetivo es producir un resumen que permita **continuar el trabajo en otra sesión o con otra IA** sin pérdida de contexto, sin omisiones y sin alucinaciones.

Reglas estrictas:
- Solo usa información que esté explícitamente en el transcript. Nunca inventes ni completes huecos.
- Si algo no está claro o falta, dilo explícitamente ("no se menciona", "queda pendiente de confirmación").
- Prioriza: decisiones tomadas, hallazgos técnicos, action items, estado final y contexto necesario para el siguiente paso.
- Escribe en español claro y profesional.
- Usa IDs, nombres de archivos, tickets, versiones y URLs exactamente como aparecen.
"""

SUMMARY_PROMPT = """Analiza el siguiente transcript de sesión y genera un resumen estructurado en Markdown con estas secciones (omite las que no apliquen):

## Metadatos
- Fecha(s) aproximada(s)
- Participantes / IAs involucradas
- Tema principal (1 línea)

## Contexto de entrada
Qué se estaba trabajando y qué se le entregó al modelo al inicio (handoffs, archivos, estado previo).

## Hallazgos y diagnósticos
Lista clara de bugs, drifts, causas raíz, confirmaciones y descubrimientos técnicos. Incluye IDs, archivos y evidencia cuando aparezcan.

## Decisiones y acuerdos
Todo lo que se decidió o se acordó explícitamente (incluyendo "no tocar X hasta confirmar Y").

## Action items / Pendientes
- Formato de checklist.
- Indica quién/qué debe hacerlo si se menciona.
- Separa los que quedaron abiertos de los que se cerraron en la sesión.

## Estado final
Dónde quedó cada hilo al terminar la sesión (qué está resuelto, qué sigue abierto, qué se dejó a medias).

## Contexto para la siguiente sesión
Lo mínimo indispensable que la siguiente IA o la siguiente sesión necesita saber para no alucinar ni omitir nada. Incluye referencias a archivos, IDs, versiones y comandos clave.

## Notas adicionales
Cualquier otra información útil (warnings, tokens, limitaciones de herramientas, etc.).

Transcript:
---
{transcript}
---
"""


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def is_url(text: str) -> bool:
    try:
        result = urlparse(text)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def fetch_claude_share(url: str) -> str:
    """Best-effort scrape de claude.ai/share. Muchas veces solo trae texto parcial."""
    import requests
    from bs4 import BeautifulSoup

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Intentar extraer el contenido principal
        # Claude shares suelen tener el hilo en divs con clases variables
        candidates = soup.find_all(["div", "article", "main"])
        texts = []
        for c in candidates:
            t = c.get_text(separator="\n", strip=True)
            if len(t) > 500 and ("Dijiste" in t or "Claude" in t or "Human" in t):
                texts.append(t)

        if texts:
            # El más largo suele ser el hilo completo
            return max(texts, key=len)

        # Fallback: todo el body
        body = soup.body.get_text(separator="\n", strip=True) if soup.body else ""
        if len(body) > 300:
            return body

        raise ValueError("No se pudo extraer contenido útil de la URL de Claude share")
    except Exception as e:
        raise RuntimeError(
            f"No se pudo obtener el contenido de la URL.\n"
            f"Error: {e}\n\n"
            f"Recomendación: exporta el chat a .md desde Claude y pásame el archivo."
        ) from e


def parse_claude_md(content: str) -> list[tuple[Optional[dt.date], str]]:
    """
    Parsea el formato típico de export de Claude (los .md que compartes).
    Devuelve lista de (fecha_opcional, mensaje_limpio).
    """
    # Patrones comunes
    # ## Dijiste: ...   o   ## Claude respondió: ...
    # También soporta variantes en inglés

    messages = []
    # Dividir por encabezados de turno
    parts = re.split(
        r"(?m)^(##\s+(?:Dijiste|Claude respondió|Human|Assistant|User|Claude).*?)$",
        content,
    )

    current_date = None
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue

        # ¿Es un header de turno?
        if re.match(r"^##\s+(?:Dijiste|Claude respondió|Human|Assistant|User|Claude)", part):
            continue

        # Limpiar ruido típico de la UI de Claude
        cleaned = re.sub(r"Se usaron \d+ herramientas.*", "", part)
        cleaned = re.sub(r"Herramientas cargadas.*", "", cleaned)
        cleaned = re.sub(r"Archivo visualizado.*", "", cleaned)
        cleaned = re.sub(r"Ejecutó un comando.*", "", cleaned)
        cleaned = re.sub(r"Usó una herramienta.*", "", cleaned)
        cleaned = re.sub(r"Files hidden in shared chats", "", cleaned)
        cleaned = re.sub(r"Mostrar más", "", cleaned)
        cleaned = re.sub(r".*", "", cleaned)  # iconos raros
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

        if len(cleaned) < 20:
            continue

        # Intentar extraer fecha si aparece cerca
        date_match = re.search(r"(\d{1,2}:\d{2}\s*[ap]\.?m\.?|\d{4}-\d{2}-\d{2})", cleaned[:200], re.I)
        msg_date = None
        if date_match:
            try:
                msg_date = date_parse(date_match.group(1), fuzzy=True).date()
            except Exception:
                pass

        messages.append((msg_date or current_date, cleaned))

    return messages


def parse_generic(content: str) -> list[tuple[Optional[dt.date], str]]:
    """Fallback para otros formatos (WhatsApp-like, plain text, etc.)."""
    # Reutilizamos algo del script original + limpieza básica
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    return [(None, "\n".join(lines))]


def load_transcript(source: str) -> str:
    if is_url(source):
        print(f"→ Descargando URL: {source}")
        return fetch_claude_share(source)
    else:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"No existe el archivo: {source}")
        return path.read_text(encoding="utf-8")


def filter_by_date(
    messages: list[tuple[Optional[dt.date], str]],
    start: Optional[dt.date],
    end: Optional[dt.date],
) -> list[tuple[Optional[dt.date], str]]:
    if not start and not end:
        return messages
    filtered = []
    for d, msg in messages:
        if d is None:
            filtered.append((d, msg))  # conservamos los sin fecha
            continue
        if start and d < start:
            continue
        if end and d > end:
            continue
        filtered.append((d, msg))
    return filtered


def chunk_text(text: str, max_chars: int = MAX_CHARS_PER_CHUNK) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    chunks = []
    current = ""
    for paragraph in text.split("\n\n"):
        if len(current) + len(paragraph) + 2 > max_chars:
            if current:
                chunks.append(current.strip())
            current = paragraph
        else:
            current = current + "\n\n" + paragraph if current else paragraph
    if current.strip():
        chunks.append(current.strip())
    return chunks


# ---------------------------------------------------------------------------
# LLM calls
# ---------------------------------------------------------------------------

def call_gemini(prompt: str, model_name: str = "gemini-2.0-flash") -> str:
    import google.generativeai as genai

    if not GEMINI_API_KEY:
        raise RuntimeError("Falta GEMINI_API_KEY en el entorno o .env")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(
        [SUMMARY_SYSTEM, prompt],
        generation_config={"temperature": 0.2},
    )
    return response.text


def call_groq(prompt: str, model_name: str = "llama-3.3-70b-versatile") -> str:
    from groq import Groq

    if not GROQ_API_KEY:
        raise RuntimeError("Falta GROQ_API_KEY en el entorno o .env")
    client = Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SUMMARY_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return completion.choices[0].message.content


def summarize(text: str, model: str = DEFAULT_MODEL) -> str:
    chunks = chunk_text(text)
    summaries = []

    for i, chunk in enumerate(chunks, 1):
        print(f"  → Enviando chunk {i}/{len(chunks)} ({len(chunk)} chars) a {model}...")
        prompt = SUMMARY_PROMPT.format(transcript=chunk)
        try:
            if model == "gemini":
                part = call_gemini(prompt)
            else:
                part = call_groq(prompt)
            summaries.append(part)
        except Exception as e:
            if model == "gemini":
                print(f"  ⚠ Gemini falló ({e}). Intentando fallback a Groq...")
                part = call_groq(prompt)
                summaries.append(part)
            else:
                raise

    if len(summaries) == 1:
        return summaries[0]

    # Si hubo varios chunks, hacemos un meta-resumen
    print("  → Combinando resúmenes parciales...")
    combined = "\n\n---\n\n".join(summaries)
    meta_prompt = SUMMARY_PROMPT.format(
        transcript=f"Estos son resúmenes parciales de una misma sesión larga. Consolídalos en un único resumen coherente, sin duplicar información:\n\n{combined}"
    )
    if model == "gemini":
        try:
            return call_gemini(meta_prompt)
        except Exception as e:
            print(f"  ⚠ Gemini falló en meta-resumen ({e}). Fallback a Groq...")
            return call_groq(meta_prompt)
    return call_groq(meta_prompt)


# ---------------------------------------------------------------------------
# Notion
# ---------------------------------------------------------------------------

def push_to_notion(title: str, markdown_body: str) -> str:
    """Crea una página hija dentro del INBOX."""
    from notion_client import Client

    if not NOTION_TOKEN:
        raise RuntimeError("Falta NOTION_TOKEN en el entorno o .env")

    notion = Client(auth=NOTION_TOKEN)

    # Convertir markdown simple a blocks de Notion (versión mínima viable)
    # Para producción podrías usar un converter más completo
    children = []
    for block in markdown_body.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith("# "):
            children.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": block[2:]}}]},
            })
        elif block.startswith("## "):
            children.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": block[3:]}}]},
            })
        elif block.startswith("### "):
            children.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": block[4:]}}]},
            })
        elif block.startswith("- ") or block.startswith("* "):
            # lista simple
            for line in block.splitlines():
                line = line.lstrip("-* ").strip()
                if line:
                    children.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": line[:2000]}}]},
                    })
        else:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": block[:2000]}}]},
            })

    # Notion limita a 100 children por request; si es muy largo lo truncamos
    children = children[:90]

    page = notion.pages.create(
        parent={"page_id": INBOX_PARENT_ID},
        properties={
            "title": {
                "title": [{"type": "text", "text": {"content": title[:100]}}]
            }
        },
        children=children,
    )
    return page["url"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def process_one(
    source: str,
    output: Optional[str],
    start: Optional[dt.date],
    end: Optional[dt.date],
    model: str,
    to_notion: bool,
) -> Path:
    print(f"\n📄 Procesando: {source}")

    raw = load_transcript(source)

    # Detectar formato
    if "Dijiste:" in raw or "Claude respondió:" in raw or "Human:" in raw:
        messages = parse_claude_md(raw)
    else:
        messages = parse_generic(raw)

    messages = filter_by_date(messages, start, end)

    if not messages:
        raise RuntimeError("No quedaron mensajes después del filtrado por fechas.")

    full_text = "\n\n".join(msg for _, msg in messages)
    print(f"  → {len(messages)} mensajes / {len(full_text)} caracteres")

    summary = summarize(full_text, model=model)

    # Nombre de salida
    if output:
        out_path = Path(output)
    else:
        stem = Path(source).stem if not is_url(source) else "claude_share"
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
        out_path = Path(f"summary_{stem}_{stamp}.md")

    header = f"""# Resumen de sesión
**Fuente:** {source}
**Generado:** {dt.datetime.now().isoformat(timespec='minutes')}
**Modelo:** {model}

---

"""
    out_path.write_text(header + summary, encoding="utf-8")
    print(f"  ✅ Resumen guardado → {out_path}")

    if to_notion:
        title = f"Summary · {out_path.stem}"
        try:
            url = push_to_notion(title, summary)
            print(f"  ✅ Página creada en INBOX → {url}")
        except Exception as e:
            print(f"  ⚠ No se pudo subir a Notion: {e}")

    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="vsum — resume sesiones de Claude/Gemini/etc. orientado a continuidad entre chats."
    )
    parser.add_argument(
        "source",
        nargs="+",
        help="Archivo .md, URL de Claude share, o patrón (con --batch)",
    )
    parser.add_argument("-o", "--output", help="Archivo de salida (solo modo single)")
    parser.add_argument("--start", help="Fecha inicio (YYYY-MM-DD)")
    parser.add_argument("--end", help="Fecha fin (YYYY-MM-DD)")
    parser.add_argument(
        "--model",
        choices=["gemini", "groq"],
        default=DEFAULT_MODEL,
        help="Modelo a usar (default: groq, fallback automático a groq si gemini falla)",
    )
    parser.add_argument(
        "--notion",
        action="store_true",
        help="Crear página hija dentro del INBOX de Notion",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Procesar todos los archivos pasados (o un directorio)",
    )

    args = parser.parse_args()

    start = date_parse(args.start).date() if args.start else None
    end = date_parse(args.end).date() if args.end else None

    sources = args.source

    # Expandir si es un directorio o globs simples
    expanded = []
    for s in sources:
        p = Path(s)
        if p.is_dir():
            expanded.extend(sorted(p.glob("*.md")))
        else:
            expanded.append(s)

    if args.batch or len(expanded) > 1:
        print(f"Modo batch: {len(expanded)} archivos")
        results = []
        for src in expanded:
            try:
                out = process_one(str(src), None, start, end, args.model, args.notion)
                results.append(out)
            except Exception as e:
                print(f"  ❌ Error en {src}: {e}")
        print(f"\nListo. {len(results)} resúmenes generados.")
    else:
        process_one(expanded[0], args.output, start, end, args.model, args.notion)


if __name__ == "__main__":
    main()
