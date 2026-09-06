import re, glob, os, shutil, csv

os.chdir("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Batch septiembre/CV-B")

# Excluidos: EN legítimo por HANDOFF.idioma=EN (confirmado 2026-09-05)
EXCLUIR = {
    "2026_Mauricio_Meyran_HM_Junior_Retail_Designer_CV-B.md",
    "2026_Mauricio_Meyran_HM_Retail_Designer_CV-B.md",
    "2026_Mauricio_Meyran_SARELLY_Global_Retail_Experience_VM_Manager_CV-B.md",
}

files = sorted(glob.glob("2026_Mauricio_Meyran_*_CV-B.md"))
files = [f for f in files if f not in EXCLUIR]

# Reemplazos globales confirmados por inspección de muestra (2026-09-05)
# Frases plantilla contaminadas, idénticas entre archivos del mismo batch/skeleton.
# NO se tocan nombres propios de campaña ("Born in Roma", "Stronger With You").
REPLACEMENTS = [
    ("storytelling in-store", "storytelling en punto de venta"),
    ("Store Design** |", "Diseño de Tienda** |"),  # rol "Coordinador de Brand Environment y Store Design" -> mantiene Store Design como parte de rol si es título oficial; ajustar solo si aplica
]

# Nota: "Store Design" como parte de nombres de rol/departamento reales puede ser
# terminología oficial de marca (Store Design es un departamento formal en varias
# organizaciones de retail) — se deja fuera del reemplazo automático por defecto.
# Solo se reemplaza el patrón de bullet "storytelling in-store", que es prosa,
# no nombre propio ni término oficial.
REPLACEMENTS = [
    ("storytelling in-store", "storytelling en punto de venta"),
]

log = []

for f in files:
    with open(f, "r", encoding="utf-8") as fh:
        content = fh.read()

    original = content
    changes_this_file = []

    for old, new in REPLACEMENTS:
        count = content.count(old)
        if count > 0:
            content = content.replace(old, new)
            changes_this_file.append(f"{old!r} -> {new!r} x{count}")

    if content != original:
        shutil.copy(f, f + ".bak_global_replace")
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(content)
        log.append({"archivo": f, "cambios": " | ".join(changes_this_file)})
    else:
        log.append({"archivo": f, "cambios": "sin coincidencias"})

with open("_saneamiento_reports/reemplazo_global_log.csv", "w", newline="", encoding="utf-8") as out:
    w = csv.DictWriter(out, fieldnames=["archivo", "cambios"])
    w.writeheader()
    w.writerows(log)

print(f"Procesados: {len(files)} archivos (excluidos {len(EXCLUIR)} EN-legítimos)")
print()
for r in log:
    print(f"{r['archivo'][:70]:<70} {r['cambios']}")
