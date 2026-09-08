import re, csv, glob, os

os.chdir("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Batch septiembre/CV-B")
files = sorted(glob.glob("2026_Mauricio_Meyran_*_CV-B.md"))

EN_STOPWORDS = re.compile(r"\b(the|and|with|for|managed|ensuring|leadership|team|of|in|across|store|through)\b", re.IGNORECASE)
PRESENTE_PROHIBIDO = re.compile(r"\b(Defino|Dirijo|Coordino|Colaboro|Gestiono|Lidero|Desarrollo|Construyo|Contribuyo|Superviso)\b")
PUNCHLINE = re.compile(r"^\*\*[A-ZÁÉÍÓÚÑ][^*]{3,40}:\*\*")
METRICA_SIN_BOLD = re.compile(r"(?<!\*)\b(\d+%|\+\d+|\d+\+ (?:tiendas|puntos de venta|corners|reportes|subgerentes|supervisores|países))\b(?!\*)")
SECCION_O_EMPRESA_SIN_BOLD = re.compile(r"^\n?([A-ZÁÉÍÓÚÑ&\.\s]{6,60})\n", re.MULTILINE)

report = []
for f in files:
    with open(f, "r", encoding="utf-8") as fh:
        content = fh.read()
    issues = []
    en_hits = EN_STOPWORDS.findall(content)
    if en_hits:
        issues.append(f"IDIOMA_MIXTO({len(en_hits)})")
    presente_hits = PRESENTE_PROHIBIDO.findall(content)
    if presente_hits:
        issues.append(f"TIEMPO_VERBAL({len(presente_hits)}:{','.join(set(presente_hits))})")
    bullets = content.split("###### [figma_text_id]")
    punchline_count = sum(1 for b in bullets if PUNCHLINE.search(b))
    total_bullets = len(bullets) - 1
    if total_bullets > 0 and (punchline_count / total_bullets) > 0.4:
        issues.append(f"PUNCHLINE_EXCESIVO({punchline_count}/{total_bullets})")
    metricas_sin_bold = METRICA_SIN_BOLD.findall(content)
    if metricas_sin_bold:
        issues.append(f"METRICA_SIN_BOLD({len(metricas_sin_bold)})")
    secciones_candidatas = SECCION_O_EMPRESA_SIN_BOLD.findall(content)
    secciones_sin_bold = [s for s in secciones_candidatas if not s.strip().startswith("**")]
    if secciones_sin_bold:
        issues.append(f"SECCION_SIN_BOLD({len(secciones_sin_bold)})")
    severidad = "LIMPIO" if not issues else ("ALTA" if len(issues) >= 3 else "MEDIA" if len(issues) >= 2 else "BAJA")
    report.append({"archivo": f, "severidad": severidad, "issues": " | ".join(issues) if issues else "—"})

with open("_saneamiento_reports/triaje_v2_post_correccion.csv", "w", newline="", encoding="utf-8") as out:
    w = csv.DictWriter(out, fieldnames=["archivo", "severidad", "issues"])
    w.writeheader()
    w.writerows(report)

order = {"ALTA": 0, "MEDIA": 1, "BAJA": 2, "LIMPIO": 3}
for r in sorted(report, key=lambda x: order[x["severidad"]]):
    print(f"{r['archivo'][:70]:<70} {r['severidad']:<8} {r['issues']}")
