#!/usr/bin/env python3
"""
cv_a_prep.py — Preparación mecánica para CV-A (KERNEL:CV-PIPELINE-001)

Responsabilidad: hacer todo lo determinista ANTES de que Claude entre a
razonar. No reemplaza el análisis semántico de CV-A (Positioning Mode,
Gap Analysis) — solo reduce el trabajo de Claude a esa parte.

Uso:
    python3 cv_a_prep.py --url "https://..." [--out HANDOFF_scaffold.md]
    python3 cv_a_prep.py --jd-file jd.txt --empresa "Acme" --rol "VM Manager"
    python3 cv_a_prep.py --url "https://..." --jd-file jd_pegado.txt

Salida: un archivo Markdown scaffold con:
  - Metadata pre-llenada (URL, fecha, JD crudo adjunto)
  - Resultado del Hard Block check (determinista)
  - Estructura de 8 campos del HANDOFF, vacía, lista para que Claude
    complete Positioning Mode + Gap Analysis + Observaciones.

Si el Hard Block dispara, el script NO genera scaffold de análisis —
solo un reporte de bloqueo (consistente con CV-A: "detener el análisis
y reportarlo, no generar HANDOFF").
"""

import argparse
import datetime
import re
import sys
import urllib.request

# --- KERNEL:CV-PIPELINE-001 / MANUAL:DATA-MANAGEMENT §10 — Hard Blocks ---
# Empleadores con bloqueo total de recontratación. Mantener sincronizado
# manualmente con la fuente canónica (Career Canon / Manual §10). Este
# script NO es la fuente de verdad — solo aplica la regla ya documentada.
HARD_BLOCK_EMPLOYERS = [
    "l'oreal", "loreal", "l'oréal",
    "levi's", "levis", "dockers",
    "palacio de hierro", "el palacio de hierro",
]

# Nota: Aéropostale NO es Hard Block (confirmado con el operador 2026-08-07).


def fetch_jd(url: str) -> str:
    """Descarga el HTML de la vacante y extrae texto plano básico.

    Extracción cruda: quita tags, scripts y estilos. No es un parser de
    JD estructurado — Claude sigue siendo responsable de interpretar el
    texto resultante durante el análisis real.
    """
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (VANTAGE cv_a_prep.py)"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")

    # Strip script/style blocks
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw, flags=re.DOTALL | re.IGNORECASE)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", " ", raw)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
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
- Empresa (si se indicó): {empresa or '(no indicada)'}
- Fecha de check: {fecha}
- Empleadores bloqueados detectados en el texto: {', '.join(hits)}

Referencia: KERNEL:CV-PIPELINE-001 / MANUAL:DATA-MANAGEMENT §10 — Hard Blocks
(L'Oréal todas las divisiones, Levi's/Dockers, El Palacio de Hierro).

Este empleador no recontrata. No se generó HANDOFF ni scaffold de análisis.
Si el hit es un falso positivo (ej. mención incidental de la marca en el
JD, no el empleador contratante), revisar manualmente antes de descartar.
"""


def build_scaffold(url: str, empresa: str, rol: str, jd_text: str) -> str:
    fecha = datetime.date.today().isoformat()
    jd_block = jd_text if jd_text else "[JD no provisto — pegar aquí antes de correr el análisis]"

    return f"""# HANDOFF CV-A — {empresa or '[Nombre de la empresa / vacante]'}

## Metadata
- URL vacante: {url or '[pendiente]'}
- Fecha de análisis: {fecha}
- Idioma detectado (ES/EN): [pendiente — Claude]
- Positioning Mode seleccionado: [pendiente — Claude, N1-N4 o EMPATE]

## Hard Block Check (determinista — cv_a_prep.py)
- Empleador: {empresa or '[pendiente]'} — PASA (sin coincidencias en lista Hard Block)
- Nota: este check es un primer filtro por string-match contra nombres de
  empleador. No sustituye la verificación de alcance store-level (soft,
  requiere juicio) que hace Claude en el paso de Validación de exclusiones.

## JD crudo (input para Claude)
{jd_block}

## Positioning Mode — Justificación
[PENDIENTE — Claude: mapear JD_keywords_top6 contra CANON:POSITIONING]

## Gap Analysis
### Matches directos
- [PENDIENTE — Claude]

### Matches parciales
- [PENDIENTE — Claude]

### Gaps (fit_gaps)
- [PENDIENTE — Claude]

## Validación de exclusiones
- Empleador: {empresa or '[pendiente]'} — PASA (Hard Block determinista, ver arriba)
- Alcance del rol: [PENDIENTE — Claude, requiere juicio store-level vs estratégico]

## Observaciones
[PENDIENTE — Claude, opcional]

## Próximo paso
[PENDIENTE — Claude: Listo para CV-B, o BLOQUEADO — razón]
"""


def main():
    parser = argparse.ArgumentParser(description="Preparación mecánica para CV-A")
    parser.add_argument("--url", help="URL de la vacante")
    parser.add_argument("--jd-file", help="Ruta a archivo de texto con el JD ya pegado")
    parser.add_argument("--empresa", default="", help="Nombre de la empresa (opcional)")
    parser.add_argument("--rol", default="", help="Nombre del rol (opcional)")
    parser.add_argument(
        "--out",
        default=None,
        help="Ruta de salida (default: HANDOFF_scaffold_<fecha>.md)",
    )
    args = parser.parse_args()

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
            print(f"AVISO: no se pudo hacer fetch automático de la URL ({e}).", file=sys.stderr)
            print("Generando scaffold sin JD — pegar manualmente.", file=sys.stderr)
            jd_text = ""

    check_text = " ".join(filter(None, [args.empresa, jd_text]))
    hits = check_hard_block(check_text)

    fecha = datetime.date.today().isoformat()
    out_path = args.out or f"HANDOFF_scaffold_{fecha}.md"

    if hits:
        content = build_block_report(args.url or "", args.empresa, hits)
        out_path = args.out or f"BLOCKED_{fecha}.md"
    else:
        content = build_scaffold(args.url or "", args.empresa, args.rol, jd_text)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"OK — generado: {out_path}")
    if hits:
        print(f"HARD BLOCK detectado: {', '.join(hits)} — no se generó scaffold de análisis.")
    else:
        print("Sin Hard Block. Scaffold listo — pasar a Claude para completar Positioning Mode + Gap Analysis.")


if __name__ == "__main__":
    main()
