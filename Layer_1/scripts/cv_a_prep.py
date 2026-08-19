#!/usr/bin/env python3
"""
cv_a_prep.py — Preparacion mecanica para CV-A (KERNEL:CV-PIPELINE-001)

Responsabilidad: hacer todo lo determinista ANTES de que Claude entre a
razonar. No reemplaza el analisis semantico de CV-A (Positioning Mode,
Gap Analysis) — solo reduce el trabajo de Claude a esa parte.

Uso:
python3 cv_a_prep.py --url "https://..." [--out HANDOFF_scaffold.md]
python3 cv_a_prep.py --jd-file jd.txt --empresa "Acme" --rol "VM Manager"
python3 cv_a_prep.py --url "https://..." --jd-file jd_pegado.txt

Salida: un archivo Markdown scaffold con:
- Metadata pre-llenada (URL, fecha, JD crudo adjunto)
- Resultado del Hard Block check (determinista)
- Estructura de 8 campos del HANDOFF, vacia, lista para que Claude
complete Positioning Mode + Gap Analysis + Observaciones.

Si el Hard Block dispara, el script NO genera scaffold de analisis —
solo un reporte de bloqueo (consistente con CV-A: "detener el analisis
y reportarlo, no generar HANDOFF").
"""

import argparse
import datetime
import hashlib
import json
import logging
import os
import re
import sys
import urllib.request
from pathlib import Path

# Directorio de salida centralizado
DEFAULT_OUTPUT_DIR = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/output")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)

# --- KERNEL:CV-PIPELINE-001 / MANUAL:DATA-MANAGEMENT §10 — Hard Blocks ---
HARD_BLOCK_CONFIG_PATH = Path(__file__).parent.parent / "config" / "hard_blocks.json"


def load_hard_blocks() -> list[str]:
    """Carga la lista de empleadores con hard block desde config."""
    try:
        if HARD_BLOCK_CONFIG_PATH.exists():
            with open(HARD_BLOCK_CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config.get("hard_block_employers", [])
        else:
            logger.warning(f"Config de hard blocks no encontrado en {HARD_BLOCK_CONFIG_PATH}, usando fallback")
            return ["l'oreal", "loreal", "l'oré¡±", "levi's", "levis", "dockers", "palacio de hierro", "el palacio de hierro"]
    except Exception as e:
        logger.error(f"Error cargando config de hard blocks: {e}, usando fallback")
        return ["l'oreal", "loreal", "l'oré¡±", "levi's", "levis", "dockers", "palacio de hierro", "el palacio de hierro"]


HARD_BLOCK_EMPLOYERS = load_hard_blocks()

# Nota: Aereopostale NO es Hard Block (confirmado con el operador 2026-08-07).

# --- Cache Configuration ---
CACHE_DIR = Path.home() / ".vantage_cache" / "jd_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_EXPIRY_HOURS = 24


def get_cache_key(url: str) -> str:
    """Genera un hash unico para la URL como clave de cache."""
    return hashlib.md5(url.encode()).hexdigest()


def is_cache_valid(cache_path: Path) -> bool:
    """Verifica si el cache aun es valido basado en la edad del archivo."""
    if not cache_path.exists():
        return False
    try:
        age_hours = (datetime.datetime.now() - datetime.datetime.fromtimestamp(cache_path.stat().st_mtime)).total_seconds() / 3600
        return age_hours < CACHE_EXPIRY_HOURS
    except Exception as e:
        logger.warning(f"Error verificando validez de cache {cache_path}: {e}")
        return False


def detect_language(text: str) -> str:
    """Detecta el idioma del texto basado en heuristicas simples."""
    if not text:
        return "UNKNOWN"

    spanish_keywords = ['y', 'en', 'de', 'para', 'con', 'por', 'una', 'el', 'la', 'los', 'las', 'un', 'una', 'es', 'son', 'se', 'su', 'sus', 'que', 'quien', 'cual', 'donde', 'cuando', 'como', 'hasta', 'hacia', 'desde', 'entre', 'sobre', 'tras', 'durante', 'mediante', 'segun', 'contra', 'sin', 'excepto', 'salvo', 'incluso', 'aunque', 'mientras', 'porque', 'para', 'que']

    english_keywords = ['and', 'in', 'of', 'for', 'with', 'by', 'from', 'at', 'on', 'to', 'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought', 'used', 'to', 'about', 'above', 'across', 'after', 'against', 'along', 'among', 'around', 'before', 'behind', 'below', 'beneath', 'beside', 'between', 'beyond', 'during', 'except', 'inside', 'into', 'near', 'outside', 'over', 'past', 'since', 'through', 'throughout', 'till', 'toward', 'under', 'underneath', 'until', 'upon', 'within', 'without']

    words = text.lower().split()
    spanish_count = sum(1 for word in words if word in spanish_keywords)
    english_count = sum(1 for word in words if word in english_keywords)

    if spanish_count > english_count:
        return "ES"
    elif english_count > spanish_count:
        return "EN"
    else:
        return "UNKNOWN"


def fetch_jd(url: str) -> str:
    """Descarga el HTML de la vacante y extrae texto plano basico con cache."""
    cache_key = get_cache_key(url)
    cache_path = CACHE_DIR / f"{cache_key}.txt"

    if is_cache_valid(cache_path):
        logger.info(f"Usando cache para {url}")
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()

    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (VANTAGE cv_a_prep.py)"}
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
            logger.info(f"JD descargado exitosamente para {url}")
    except urllib.error.HTTPError as e:
        logger.error(f"Error HTTP descargando URL {url}: {e.code}")
        if cache_path.exists():
            logger.info("Usando cache existente como fallback")
            with open(cache_path, "r", encoding="utf-8") as f:
                return f.read()
        raise
    except urllib.error.URLError as e:
        logger.error(f"Error de URL descargando {url}: {e}")
        if cache_path.exists():
            logger.info("Usando cache existente como fallback")
            with open(cache_path, "r", encoding="utf-8") as f:
                return f.read()
        raise
    except Exception as e:
        logger.error(f"Error inesperado descargando {url}: {e}")
        if cache_path.exists():
            logger.info("Usando cache existente como fallback")
            with open(cache_path, "r", encoding="utf-8") as f:
                return f.read()
        raise

    raw = re.sub(r"<(script|style)[^>]*>.*?\1>", "", raw, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\s+", " ", text).strip()

    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(text)
        logger.debug(f"Cache guardado para {url}")
    except Exception as e:
        logger.warning(f"Error guardando cache para {url}: {e}")

    return text


def check_hard_block(text: str) -> list[str]:
    """Retorna la lista de empleadores bloqueados detectados en el texto."""
    lowered = text.lower()
    hits = []
    for employer in HARD_BLOCK_EMPLOYERS:
        if employer in lowered:
            hits.append(employer)
    return hits


def build_block_report(url: str, empresa: str, hits: list[str]) -> str:
    fecha = datetime.date.today().isoformat()
    return f"""# CV-A — BLOQUEADO (Hard Block)

- URL vacante: {url or '(no provista)'}
- Empresa (si se indico): {empresa or '(no indicada)'}
- Fecha de check: {fecha}
- Empleadores bloqueados detectados en el texto: {', '.join(hits)}

Referencia: KERNEL:CV-PIPELINE-001 / MANUAL:DATA-MANAGEMENT §10 — Hard Blocks
(L'Oreal todas las divisiones, Levi's/Dockers, El Palacio de Hierro).

Este empleador no recontrata. No se genero HANDOFF ni scaffold de analisis.
Si el hit es un falso positivo (ej. mencion incidental de la marca en el
JD, no el empleador contratante), revisar manualmente antes de descartar.
"""


def build_scaffold(url: str, empresa: str, rol: str, jd_text: str) -> str:
    fecha = datetime.date.today().isoformat()
    jd_block = jd_text if jd_text else "[JD no provisto — pegar aqui antes de correr el analisis]"

    detected_lang = detect_language(jd_text) if jd_text else "UNKNOWN"

    return f"""# HANDOFF CV-A — {empresa or '[Nombre de la empresa / vacante]'}

## Metadata
- URL vacante: {url or '[pendiente]'}
- Fecha de analisis: {fecha}
- Idioma detectado (ES/EN): {detected_lang}
- Positioning Mode seleccionado: [pendiente — Claude, N1-N4 o EMPATE]

## Hard Block Check (determinista — cv_a_prep.py)
- Empleador: {empresa or '[pendiente]'} — PASA (sin coincidencias en lista Hard Block)
- Nota: este check es un primer filtro por string-match contra nombres de
empleador. No sustituye la verificacion de alcance store-level (soft,
requiere juicio) que hace Claude en el paso de Validacion de exclusiones.

## JD crudo (input para Claude)
{jd_block}

## Positioning Mode — Justificacion
[PENDIENTE — Claude: mapear JD_keywords_top6 contra CANON:POSITIONING]

## Gap Analysis
### Matches directos
- [PENDIENTE — Claude]

### Matches parciales
- [PENDIENTE — Claude]

### Gaps (fit_gaps)
- [PENDIENTE — Claude]

## Validacion de exclusiones
- Empleador: {empresa or '[pendiente]'} — PASA (Hard Block determinista, ver arriba)
- Alcance del rol: [PENDIENTE — Claude, requiere juicio store-level vs estrategico]

## Observaciones
[PENDIENTE — Claude, opcional]

## Proximo paso
[PENDIENTE — Claude: Listo para CV-B, o BLOQUEADO — razon]
"""


def auto_clean_cache() -> int:
    """Limpia automaticamente cache expirado. Retorna cantidad de archivos eliminados."""
    cleaned = 0
    try:
        for cache_file in CACHE_DIR.glob("*.txt"):
            if not is_cache_valid(cache_file):
                cache_file.unlink()
                cleaned += 1
        if cleaned > 0:
            logger.info(f"Auto-limpieza de cache: {cleaned} archivos expirados eliminados")
    except Exception as e:
        logger.warning(f"Error en auto-limpieza de cache: {e}")
    return cleaned


def main():
    parser = argparse.ArgumentParser(description="Preparacion mecanica para CV-A")
    parser.add_argument("--url", help="URL de la vacante")
    parser.add_argument("--jd-file", help="Ruta a archivo de texto con el JD ya pegado")
    parser.add_argument("--empresa", default="", help="Nombre de la empresa (opcional)")
    parser.add_argument("--rol", default="", help="Nombre del rol (opcional)")
    parser.add_argument(
        "--out",
        default=None,
        help="Ruta de salida (default: HANDOFF_scaffold_<YYYY-MM-DD>.md en {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Limpiar cache de JDs expirados antes de procesar"
    )
    parser.add_argument(
        "--no-auto-clean",
        action="store_true",
        help="Desactivar limpieza automatica de cache expirado"
    )
    args = parser.parse_args()

    if not args.no_auto_clean:
        auto_clean_cache()

    if args.clear_cache:
        logger.info("Limpiando cache de JDs expirados manualmente...")
        cleaned = 0
        for cache_file in CACHE_DIR.glob("*.txt"):
            if not is_cache_valid(cache_file):
                cache_file.unlink()
                cleaned += 1
        logger.info(f"Cache limpiado manualmente: {cleaned} archivos expirados eliminados.")

    if not args.url and not args.jd_file:
        print("ERROR: provee --url y/o --jd-file", file=sys.stderr)
        sys.exit(1)

    jd_text = ""
    if args.jd_file:
        with open(args.jd_file, "r", encoding="utf-8") as f:
            jd_text = f.read().strip()
    elif args.url:
        try:
            jd_text = fetch_jd(args.url)
        except Exception as e:
            print(f"AVISO: no se pudo hacer fetch automatico de la URL ({e}).", file=sys.stderr)
            print("Generando scaffold sin JD — pegar manualmente.", file=sys.stderr)
            jd_text = ""

    check_text = " ".join(filter(None, [args.empresa, jd_text]))
    hits = check_hard_block(check_text)

    fecha = datetime.date.today().isoformat()

    if args.out:
        out_path = args.out
    else:
        out_path = str(DEFAULT_OUTPUT_DIR / f"HANDOFF_scaffold_{fecha}.md")

    if hits:
        if not args.out:
            out_path = str(DEFAULT_OUTPUT_DIR / f"BLOCKED_{fecha}.md")
        content = build_block_report(args.url or "", args.empresa, hits)
    else:
        content = build_scaffold(args.url or "", args.empresa, args.rol, jd_text)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"OK — generado: {out_path}")
    if hits:
        print(f"HARD BLOCK detectado: {', '.join(hits)} — no se genero scaffold de analisis.")
    else:
        print("Sin Hard Block. Scaffold listo — pasar a Claude para completar Positioning Mode + Gap Analysis.")


if __name__ == "__main__":
    main()