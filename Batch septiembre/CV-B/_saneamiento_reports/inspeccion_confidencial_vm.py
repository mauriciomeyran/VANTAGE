import re

EN_STOPWORDS = re.compile(r"\b(the|and|with|for|managed|ensuring|leadership|team|of|in|across|store|through)\b", re.IGNORECASE)

f = "2026_Mauricio_Meyran_Confidencial_Gerente_de_Visual_Merchandising_CV-B.md"
with open(f, "r", encoding="utf-8") as fh:
    content = fh.read()

matches = list(EN_STOPWORDS.finditer(content))
print(f"Total matches: {len(matches)}\n")
for i, m in enumerate(matches):
    start = max(0, m.start() - 50)
    end = min(len(content), m.end() + 50)
    snippet = content[start:end].replace("\n", " ")
    print(f"[{i+1}] ...{snippet}...")
