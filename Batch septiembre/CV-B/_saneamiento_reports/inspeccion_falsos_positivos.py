import re

EN_STOPWORDS = re.compile(r"\b(the|and|with|for|managed|ensuring|leadership|team|of|in|across|store|through)\b", re.IGNORECASE)

targets = [
    "2026_Mauricio_Meyran_HM_Junior_Retail_Designer_CV-B.md",
    "2026_Mauricio_Meyran_HM_Retail_Designer_CV-B.md",
    "2026_Mauricio_Meyran_SARELLY_Global_Retail_Experience_VM_Manager_CV-B.md",
]

for f in targets:
    print(f"\n=== {f} ===")
    with open(f, "r", encoding="utf-8") as fh:
        content = fh.read()
    matches = list(EN_STOPWORDS.finditer(content))
    print(f"Total matches: {len(matches)}")
    for m in matches[:6]:
        start = max(0, m.start() - 30)
        end = min(len(content), m.end() + 30)
        snippet = content[start:end].replace("\n", " ")
        print(f"  ...{snippet}...")
