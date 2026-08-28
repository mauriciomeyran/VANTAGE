#!/usr/bin/env python3
"""
VANTAGE - Orphan Script Audit
Cruza cada script en Layer_1/scripts/ contra el corpus de referencias conocidas
(Raycast, wrappers, triggers.json, config de MCP/Devin, Figma Sync, Manual/Kernel)
y emite un veredicto REFERENCIADO / HUERFANO por archivo.

No mueve ni borra nada — solo genera el reporte. La decision de archivar a
Archive/Legacy_Scripts/DEPRECATED_* sigue siendo del operador (ver skill
vantage-housekeeping-archive).

Uso:
    python3 orphan_audit.py                  # imprime tabla en consola
    python3 orphan_audit.py --out audit.md    # tambien escribe SCRIPT_AUDIT.md
"""
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # raiz del repo
SCRIPTS_DIR = BASE_DIR / "Layer_1" / "scripts"

# Fuentes que se consideran corpus de referencia valido.
# Se leen como texto crudo y se busca el nombre del script (basename) dentro.
REFERENCE_SOURCES = [
    BASE_DIR / "Raycast",
    BASE_DIR / "Layer_1" / "wrappers",
    BASE_DIR / "Layer_4" / "wrappers",
    BASE_DIR / "Layer_3" / "wrappers",
    BASE_DIR / "skills" / "triggers.json",
    BASE_DIR / ".vscode" / "mcp.json",
    BASE_DIR / "Layer_1" / ".devin" / "config.json",
    BASE_DIR / "Figma Sync" / "code.js",
    BASE_DIR / "Figma Sync" / "package.json",
    BASE_DIR / "Layer_1" / "package.json",
    BASE_DIR / "Layer_4" / "com.vantage.gitsync.plist",
    BASE_DIR / "main.py",
    BASE_DIR / "web_ui.py",
    BASE_DIR / "Layer_1" / "layer_1_pipeline.sh",
    BASE_DIR / "MANUAL.md",
    BASE_DIR / "Documentación" / "ACTIVE" / "Manual.md",
    BASE_DIR / "Documentación" / "ACTIVE" / "Kernel.md",
]


def build_corpus() -> str:
    """Concatena el contenido de todas las fuentes de referencia (recursivo en dirs)."""
    chunks = []
    for src in REFERENCE_SOURCES:
        if not src.exists():
            continue
        if src.is_dir():
            for f in src.rglob("*"):
                if f.is_file():
                    try:
                        chunks.append(f.read_text(encoding="utf-8", errors="ignore"))
                    except Exception:
                        pass
        else:
            try:
                chunks.append(src.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                pass
    # Tambien cruzar cada script contra los DEMAS scripts (llamadas internas)
    for f in SCRIPTS_DIR.glob("*.py"):
        try:
            chunks.append(f.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            pass
    return "\n".join(chunks)


def audit() -> list[tuple[str, int, str]]:
    corpus = build_corpus()
    results = []
    scripts = sorted(SCRIPTS_DIR.glob("*.py")) + sorted(SCRIPTS_DIR.glob("*.sh"))
    for script in scripts:
        name = script.name
        # Contar ocurrencias del nombre en el corpus, excluyendo el propio archivo
        own_content = script.read_text(encoding="utf-8", errors="ignore")
        count = corpus.count(name) - own_content.count(name)
        status = "REFERENCIADO" if count > 0 else "HUERFANO"
        results.append((name, max(count, 0), status))
    return results


def render_markdown(results: list[tuple[str, int, str]]) -> str:
    lines = [
        "# SCRIPT_AUDIT.md — Auditoría de Scripts Huérfanos",
        "",
        "Generado por `orphan_audit.py`. No mueve archivos — solo reporta.",
        "El movimiento a `Archive/Legacy_Scripts/DEPRECATED_*` sigue siendo decisión del operador.",
        "",
        "| Script | Referencias | Veredicto |",
        "|---|---|---|",
    ]
    for name, count, status in results:
        lines.append(f"| {name} | {count} | {status} |")
    huerfanos = [r for r in results if r[2] == "HUERFANO"]
    lines.append("")
    lines.append(f"**Total huérfanos detectados: {len(huerfanos)}**")
    if huerfanos:
        lines.append("")
        for name, _, _ in huerfanos:
            lines.append(f"- {name}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", help="Ruta de salida para SCRIPT_AUDIT.md (opcional)")
    args = parser.parse_args()

    results = audit()
    md = render_markdown(results)
    print(md)

    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"\n[+] Reporte escrito en {args.out}")


if __name__ == "__main__":
    main()
