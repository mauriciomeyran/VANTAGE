#!/usr/bin/env python3
import os
import re
import sys
import time
import argparse
from pathlib import Path
from dotenv import find_dotenv, load_dotenv

# Cargar variables de entorno desde .env usando find_dotenv para resolución dinámica
load_dotenv(find_dotenv())

# --- CONFIGURACIÓN Y CONSTANTES ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

DEFAULT_MODEL = "groq"
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.6-27b")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Reducido a 10000 para garantizar staying power bajo el límite de 12,000 TPM en Groq Tier Gratis
MAX_CHARS_PER_CHUNK = 10000

SUMMARY_SYSTEM = """Eres un sintetizador de información experto especializado en procesamiento de transcripciones y documentos técnicos.
Tu objetivo es generar resúmenes ejecutivos estructurados, precisos y de alto valor cognitivo."""

SUMMARY_PROMPT = """Procesa el siguiente texto y genera un resumen estructurado usando Markdown.
No omitas decisiones clave, elementos técnicos ni puntos de acción asignados.

FORMATO REQUERIDO:
## Resumen Ejecutivo
(Un párrafo conciso con el core de la sesión)

## Puntos Clave / Temas Discutidos
- (Bullet points claros y sin redundancia)

## Decisiones y Acuerdos
- (Decisiones tomadas o confirmaciones explícitas)

## Próximos Pasos / Acciones
- [ ] (Tareas explícitas identificadas con responsable si aplica)

---
TEXTO A PROCESAR:
{transcript}
"""

# --- LLM CLIENTS ---

def call_groq(prompt: str) -> str:
    from groq import Groq

    if not GROQ_API_KEY:
        raise RuntimeError("Falta GROQ_API_KEY en el entorno o .env")

    client = Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SUMMARY_SYSTEM},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )
    return completion.choices[0].message.content


def call_gemini(prompt: str) -> str:
    from google import genai
    from google.genai import types

    if not GEMINI_API_KEY:
        raise RuntimeError("Falta GEMINI_API_KEY en el entorno o .env")

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SUMMARY_SYSTEM,
            temperature=0.2,
        ),
    )
    return response.text

# --- HELPERS ---

def chunk_text(text: str, max_chars: int = MAX_CHARS_PER_CHUNK) -> list[str]:
    """Divide un texto largo en chunks respetando saltos de línea."""
    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_len = 0

    for para in paragraphs:
        if current_len + len(para) + 2 > max_chars:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
            current_chunk = [para]
            current_len = len(para)
        else:
            current_chunk.append(para)
            current_len += len(para) + 2

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def summarize(text: str, model: str = DEFAULT_MODEL) -> str:
    """Maneja el flujo de segmentación, llamadas a la API y consolidación."""
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

        # Pausa de seguridad para no chocar con rate limits por minuto (TPM/RPM)
        if i < len(chunks):
            time.sleep(2)

    if len(summaries) == 1:
        return summaries[0]

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

# --- CLI & EXECUTION ---

def process_one(filepath: str, output: str = None, start: int = None, end: int = None, model: str = DEFAULT_MODEL, notion: bool = False):
    path = Path(filepath)
    if not path.exists():
        print(f"Error: El archivo {filepath} no existe.", file=sys.stderr)
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        full_text = f.read()

    print(f"\n📄 Procesando: {path}")
    print(f"  → Total caracteres: {len(full_text)}")

    summary = summarize(full_text, model=model)

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"✓ Resumen guardado en: {out_path}")
    else:
        print("\n" + "=" * 40 + "\n")
        print(summary)
        print("\n" + "=" * 40)


def main():
    parser = argparse.ArgumentParser(description="vsum: Generador de resúmenes vía Groq/Gemini")
    parser.add_argument("file", help="Ruta al archivo Markdown o de texto a resumir")
    parser.add_argument("-o", "--output", help="Ruta de archivo de salida (opcional)")
    parser.add_argument("-m", "--model", choices=["groq", "gemini"], default=DEFAULT_MODEL, help="Modelo a utilizar (groq por defecto)")
    parser.add_argument("--notion", action="store_true", help="Bandera de integración con Notion")
    
    args = parser.parse_args()
    process_one(args.file, output=args.output, model=args.model, notion=args.notion)


if __name__ == "__main__":
    main()
