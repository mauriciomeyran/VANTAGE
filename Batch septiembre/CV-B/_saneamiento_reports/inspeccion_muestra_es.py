import re

EN_STOPWORDS = re.compile(r"\b(the|and|with|for|managed|ensuring|leadership|team|of|in|across|store|through)\b", re.IGNORECASE)

targets = [
    "2026_Mauricio_Meyran_Confidencial_Gerente_de_Visual_Merchandising_CV-B.md",
    "2026_Mauricio_Meyran_Eurokor_VM_Skincare_CV-B.md",
    "2026_Mauricio_Meyran_Tendam_Responsable_de_Visual_Merchandiser_boutiques_CV-B.md",
]

for f in targets:
    print(f"\n=== {f} ===")
    with open(f, "r", encoding="utf-8") as fh:
        content = fh.read()
    matches = list(EN_STOPWORDS.finditer(content))
    print(f"Total matches: {len(matches)}")
    for m in matches[:6]:
        start = max(0, m.start() - 40)
        end = min(len(content), m.end() + 40)
        snippet = content[start:end].replace("\n", " ")
        print(f"  ...{snippet}...")
