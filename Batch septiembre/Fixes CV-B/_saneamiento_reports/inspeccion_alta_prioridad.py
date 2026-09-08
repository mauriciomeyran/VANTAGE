import re

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
    "2026_Mauricio_Meyran_GDC_Inmobiliaria_Auxiliar_Experiencia_VM_CV-B.md",
    "2026_Mauricio_Meyran_Inditex_Imagen_y_Visual_Merchandiser_CDMX_CV-B.md",
    "2026_Mauricio_Meyran_Intimissimi_Visual_Merchandising_Coordinator_CV-B.md",
    "2026_Mauricio_Meyran_ServiciosAndreiMoygo_Gerente_Visual_Merchandising_Desarrollo_Tienda_CV-B.md",
    "2026_Mauricio_Meyran_ZaraHome_VisualMerchandiser_CV-B.md",
]

for f in targets:
    print(f"\n{'='*90}\n=== {f} ===\n{'='*90}")
    with open(f, "r", encoding="utf-8") as fh:
        raw = fh.read()
    cuerpo = limpiar_exentas(raw)

    print("--- IDIOMA (real) ---")
    for m in EN_STOPWORDS.finditer(cuerpo):
        start = max(0, m.start() - 45)
        end = min(len(cuerpo), m.end() + 45)
        print(f"  ...{cuerpo[start:end]!r}...")

    print("--- TIEMPO VERBAL ---")
    for m in PRESENTE_PROHIBIDO.finditer(raw):
        start = max(0, m.start() - 45)
        end = min(len(raw), m.end() + 45)
        print(f"  ...{raw[start:end]!r}...")
