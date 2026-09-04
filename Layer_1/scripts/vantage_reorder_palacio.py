from pathlib import Path
#!/usr/bin/env python3
"""
VANTAGE — Reordenamiento de bloques CV-B contra registry_seed.json
Uso: python3 vantage_reorder_palacio.py
Correr desde la raíz del repo (VANTAGE/).

Qué hace: reordena los bloques (tag + contenido) de cada archivo para
que coincidan posición-por-posición con el orden de
'Figma Sync/registry_seed.json'. NO modifica el texto de ningún bloque
— solo su ubicación en el archivo. Header (antes del primer tag) y
footer (después del último tag) se preservan intactos.

Seguridad: hace backup .bak3 de cada archivo antes de tocarlo, y aborta
(sin escribir nada) si el set de IDs del archivo no coincide 1:1 con el
registry — nunca inventa ni descarta bloques.
"""
import re, json, sys, os

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY = str(REPO_ROOT / "Figma Sync" / "registry_seed.json")
BASE = str(REPO_ROOT / "Plan Saneamiento" / "CV-B")

FILES = [
    "2026_Mauricio_Meyran_Beyond_Gerente_Marketing_Visual_Merchandising_PDV_Retail_BELLEZA_CV-B.md",
    "2026_Mauricio_Meyran_Confidencial_Gerente_de_Visual_Merchandising_CV-B.md",
    "2026_Mauricio_Meyran_Multicont_Supervisor_de_Visual_Merchandiser_Cdmx_CV-B.md",
    "2026_Mauricio_Meyran_Multicont_Visual_Merchandiser_CV-B.md",
    "2026_Mauricio_Meyran_Tendam_Responsable_de_Visual_Merchandiser_boutiques_CV-B.md",
]

TAG_RE = re.compile(r'^######\s\[figma_text_id\]\((\d+:\d+)\)\s*$', re.MULTILINE)

def main():
    if not os.path.isfile(REGISTRY):
        sys.exit(f"ABORT: no encuentro {REGISTRY} — correr desde la raíz del repo VANTAGE/")

    reg_order = list(json.load(open(REGISTRY, encoding="utf-8")).values())

    for fname in FILES:
        path = os.path.join(BASE, fname)
        if not os.path.isfile(path):
            print(f"SKIP (no existe): {fname}")
            continue

        text = open(path, encoding="utf-8").read()
        matches = list(TAG_RE.finditer(text))
        if not matches:
            print(f"SKIP (sin tags detectados): {fname}")
            continue

        header = text[:matches[0].start()]
        footer_start = matches[-1].end()

        blocks = {}
        for i, m in enumerate(matches):
            node_id = m.group(1)
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else footer_start
            blocks[node_id] = text[start:end]

        footer = text[footer_start:]

        missing = [i for i in reg_order if i not in blocks]
        extra = [i for i in blocks if i not in reg_order]
        if missing or extra:
            print(f"ABORT {fname}: missing={missing} extra={extra} — no se escribe nada")
            continue

        new_text = header + "".join(blocks[i] for i in reg_order) + footer

        if new_text == text:
            print(f"SIN CAMBIOS (ya en orden): {fname}")
            continue

        with open(path + ".bak3", "w", encoding="utf-8") as f:
            f.write(text)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)
        print(f"REORDENADO: {fname}")

    print("\n=== Verificación post-fix ===")
    for fname in FILES:
        path = os.path.join(BASE, fname)
        if not os.path.isfile(path):
            continue
        text = open(path, encoding="utf-8").read()
        ids = TAG_RE.findall(text)
        seq_ok = ids == reg_order
        print(f"{fname} -> n={len(ids)} secuencia_ok={seq_ok}")

    print("\nBackups: *.bak3 junto a cada archivo.")
    print("Rollback: for f in <archivos>; do mv \"$f.bak3\" \"$f\"; done")

if __name__ == "__main__":
    main()
