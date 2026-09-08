import re, glob, os, csv

os.chdir("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Batch septiembre/CV-B")

EXCLUIR = {
    "2026_Mauricio_Meyran_HM_Junior_Retail_Designer_CV-B.md",
    "2026_Mauricio_Meyran_HM_Retail_Designer_CV-B.md",
    "2026_Mauricio_Meyran_SARELLY_Global_Retail_Experience_VM_Manager_CV-B.md",
}

# Excepciones confirmadas 2026-09-05: nombres propios de campaña, términos técnicos
# de industria en inglés de uso estándar, títulos oficiales de certificación,
# y el footer de metadata (no es contenido del CV).
FRASES_EXENTAS = [
    "Born in Roma", "Stronger With You",
    "window installations", "store zoning",
    "Store Design", "Brand Environment",
    "Store Operations Leaders Orientation",
    "Field Leadership", "Flagship Store",
]

EN_STOPWORDS = re.compile(r"\b(the|and|with|for|managed|ensuring|leadership|team|of|in|across|store|through)\b", re.IGNORECASE)
# Desarrollo excluido cuando es sustantivo ("Desarrollo de X", "Desarrollo y X", "de Desarrollo de X")
PRESENTE_PROHIBIDO = re.compile(r"(?<!de\s)\b(Defino|Dirijo|Coordino|Colaboro|Gestiono|Lidero|Construyo|Contribuyo|Superviso)\b|(?<!de\s)\bDesarrollo\b(?!\s+(de|y)\b)")

def limpiar_exentas(content):
    """Elimina del texto las frases exentas antes de correr el chequeo de idioma,
    para que sus stopwords internas no cuenten como contaminación real.
    Case-insensitive: "flagship store" en minúsculas también debe quedar exento."""
    for frase in FRASES_EXENTAS:
        content = re.sub(re.escape(frase), "", content, flags=re.IGNORECASE)
    # También se descarta todo lo que esté después del separador de footer,
    # ya que el footer de metadata no es contenido del CV en sí.
    if "\n---\n" in content:
        content = content.split("\n---\n")[0]
    return content

files = sorted(glob.glob("2026_Mauricio_Meyran_*_CV-B.md"))
files = [f for f in files if f not in EXCLUIR]

report = []
for f in files:
    with open(f, "r", encoding="utf-8") as fh:
        raw = fh.read()

    cuerpo_limpio = limpiar_exentas(raw)
    en_hits = EN_STOPWORDS.findall(cuerpo_limpio)
    presente_matches = [m.group(0) for m in PRESENTE_PROHIBIDO.finditer(raw)]

    issues = []
    if en_hits:
        issues.append(f"IDIOMA_MIXTO_REAL({len(en_hits)})")
    if presente_matches:
        issues.append(f"TIEMPO_VERBAL({len(presente_matches)}:{','.join(set(presente_matches))})")

    severidad = "LIMPIO" if not issues else ("ALTA" if len(issues) >= 2 else "BAJA")
    report.append({"archivo": f, "severidad": severidad, "issues": " | ".join(issues) if issues else "—"})

with open("_saneamiento_reports/triaje_v3_sin_falsos_positivos.csv", "w", newline="", encoding="utf-8") as out:
    w = csv.DictWriter(out, fieldnames=["archivo", "severidad", "issues"])
    w.writeheader()
    w.writerows(report)

order = {"ALTA": 0, "BAJA": 1, "LIMPIO": 2}
for r in sorted(report, key=lambda x: order[x["severidad"]]):
    print(f"{r['archivo'][:70]:<70} {r['severidad']:<8} {r['issues']}")
