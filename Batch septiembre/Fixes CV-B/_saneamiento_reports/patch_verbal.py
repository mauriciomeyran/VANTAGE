import shutil, csv, os

os.chdir("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Batch septiembre/CV-B")

# Patches quirúrgicos: tiempo verbal L'Oréal (rol cerrado 02/2025-03/2026) + "in-store" residual
PATCHES = {
    "2026_Mauricio_Meyran_Inditex_Imagen_y_Visual_Merchandiser_CDMX_CV-B.md": [
        ("Lidero la estrategia visual y el storytelling en punto de venta", "Lideré la estrategia visual y el storytelling en punto de venta"),
        ("Coordino proveedores locales para la producción e ins", "Coordiné proveedores locales para la producción e ins"),
    ],
    "2026_Mauricio_Meyran_Intimissimi_Visual_Merchandising_Coordinator_CV-B.md": [
        ("Lidero la estrategia visual y el desarrollo de conceptos de exhibición in-store", "Lideré la estrategia visual y el desarrollo de conceptos de exhibición en punto de venta"),
        ("Coordino proveedores locales para la producción e ins", "Coordiné proveedores locales para la producción e ins"),
        ("Colaboro con equipos de Marketing, Trade y Operacione", "Colaboré con equipos de Marketing, Trade y Operacione"),
    ],
    "2026_Mauricio_Meyran_ServiciosAndreiMoygo_Gerente_Visual_Merchandising_Desarrollo_Tienda_CV-B.md": [
        ("el desarrollo de conceptos de exhibición in-store para Valentino", "el desarrollo de conceptos de exhibición en punto de venta para Valentino"),
    ],
    "2026_Mauricio_Meyran_ZaraHome_VisualMerchandiser_CV-B.md": [
        ("Coordino proveedores locales para la producción e ins", "Coordiné proveedores locales para la producción e ins"),
    ],
}

log = []
for f, replacements in PATCHES.items():
    with open(f, "r", encoding="utf-8") as fh:
        content = fh.read()
    original = content
    changes = []
    for old, new in replacements:
        count = content.count(old)
        if count == 0:
            changes.append(f"NO ENCONTRADO: {old!r}")
        else:
            content = content.replace(old, new)
            changes.append(f"OK x{count}: {old[:40]!r}...")
    if content != original:
        shutil.copy(f, f + ".bak_verbal_patch")
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(content)
    log.append({"archivo": f, "cambios": " | ".join(changes)})

with open("_saneamiento_reports/patch_verbal_log.csv", "w", newline="", encoding="utf-8") as out:
    w = csv.DictWriter(out, fieldnames=["archivo", "cambios"])
    w.writeheader()
    w.writerows(log)

for r in log:
    print(f"{r['archivo'][:70]:<70}")
    print(f"   {r['cambios']}")
