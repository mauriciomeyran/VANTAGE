import re

METRICA_SIN_BOLD = re.compile(r"(?<!\*)\b(\d+%|\+\d+|\d+\+ (?:tiendas|puntos de venta|corners|reportes|subgerentes|supervisores|países))\b(?!\*)")
SECCION_O_EMPRESA_SIN_BOLD = re.compile(r"^\n?([A-ZÁÉÍÓÚÑ&\.\s]{6,60})\n", re.MULTILINE)

f = "2026_Mauricio_Meyran_Confidencial_Gerente_de_Visual_Merchandising_CV-B.md"
with open(f, "r", encoding="utf-8") as fh:
    content = fh.read()

print("--- METRICA_SIN_BOLD ---")
for m in METRICA_SIN_BOLD.finditer(content):
    start = max(0, m.start() - 40)
    end = min(len(content), m.end() + 40)
    print(f"...{content[start:end]!r}...")

print("\n--- SECCION_SIN_BOLD ---")
for m in SECCION_O_EMPRESA_SIN_BOLD.finditer(content):
    s = m.group(1).strip()
    if not s.startswith("**"):
        print(repr(s))
