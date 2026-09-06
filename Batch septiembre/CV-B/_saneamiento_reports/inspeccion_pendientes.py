import re, os

os.chdir("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Batch septiembre/CV-B")

FRASES_EXENTAS = [
    "Born in Roma", "Stronger With You",
    "window installations", "store zoning",
    "Store Design", "Brand Environment",
    "Store Operations Leaders Orientation",
    "Field Leadership",
]
EN_STOPWORDS = re.compile(r"\b(the|and|with|for|managed|ensuring|leadership|team|of|in|across|store|through)\b", re.IGNORECASE)
PRESENTE_PROHIBIDO = re.compile(r"\b(Defino|Dirijo|Coordino|Colaboro|Gestiono|Lidero|Desarrollo|Construyo|Contribuyo|Superviso)\b")

def limpiar_exentas(content):
    for frase in FRASES_EXENTAS:
        content = content.replace(frase, "")
    if "\n---\n" in content:
        content = content.split("\n---\n")[0]
    return content

targets = [
    "2026_Mauricio_Meyran_Multicont_Supervisor_de_Visual_Merchandiser_Cdmx_CV-B.md",
    "2026_Mauricio_Meyran_Beyond_Gerente_Marketing_Visual_Merchandising_PDV_Retail_BELLEZA_CV-B.md",
    "2026_Mauricio_Meyran_Confidencial_Gerente_Nacional_de_Visual_Merchandising_CV-B.md",
    "2026_Mauricio_Meyran_IKEA_Visual_Merchandiser_CV-B.md",
    "2026_Mauricio_Meyran_Juguetron_Visual_Merchandiser_CV-B.md",
    "2026_Mauricio_Meyran_Multicont_Visual_Merchandiser_CV-B.md",
    "2026_Mauricio_Meyran_Tendam_Responsable_de_Visual_Merchandiser_boutiques_CV-B.md",
    "2026_Mauricio_Meyran_Walmart_Analista_Diseno_Modular_Planogramas_CV-B.md",
]

for f in targets:
    print(f"\n{'='*90}\n=== {f} ===\n{'='*90}")
    with open(f, "r", encoding="utf-8") as fh:
        raw = fh.read()
    cuerpo = limpiar_exentas(raw)

    en_hits = list(EN_STOPWORDS.finditer(cuerpo))
    print(f"--- IDIOMA real ({len(en_hits)}) ---")
    for m in en_hits:
        start = max(0, m.start() - 45)
        end = min(len(cuerpo), m.end() + 45)
        print(f"  ...{cuerpo[start:end]!r}...")

    verbal_hits = list(PRESENTE_PROHIBIDO.finditer(raw))
    print(f"--- TIEMPO VERBAL ({len(verbal_hits)}) ---")
    for m in verbal_hits:
        start = max(0, m.start() - 45)
        end = min(len(raw), m.end() + 45)
        print(f"  ...{raw[start:end]!r}...")
