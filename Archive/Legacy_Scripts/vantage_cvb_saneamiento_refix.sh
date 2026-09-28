#!/usr/bin/env bash
set -euo pipefail

cd "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Plan Saneamiento/CV-B"

FILES=(
  "2026_Mauricio_Meyran_Confidencial_Gerente_de_Visual_Merchandising_CV-B.md"
  "2026_Mauricio_Meyran_Eurokor_VM_Skincare_CV-B.md"
  "2026_Mauricio_Meyran_HM_Junior_Retail_Designer_CV-B.md"
  "2026_Mauricio_Meyran_HM_Retail_Designer_CV-B.md"
  "2026_Mauricio_Meyran_Intimissimi_Visual_Merchandising_Coordinator_CV-B.md"
  "2026_Mauricio_Meyran_Multicont_Visual_Merchandiser_CV-B.md"
  "2026_Mauricio_Meyran_ServiciosAndreiMoygo_Gerente_Visual_Merchandising_Desarrollo_Tienda_CV-B.md"
)

echo "=== Diagnóstico: primera línea de tag rota en cada archivo ==="
for f in "${FILES[@]}"; do
  [ -f "$f" ] || { echo "SKIP (no existe): $f"; continue; }
  echo "--- $f ---"
  grep -nE '######[^a-zA-Z]*\[[0-9]+:[0-9]+\]' "$f" | head -1 | cat -A | cut -c1-120
done

echo ""
echo "=== Aplicando fix (sin anclar a whitespace) ==="
for f in "${FILES[@]}"; do
  [ -f "$f" ] || continue
  cp "$f" "$f.bak2"

  # Tag roto: matchea [N:N](N:N)
  sed -i '' -E 's/\[([0-9]+:[0-9]+)\]\(([0-9]+:[0-9]+)\)/[figma_text_id](\2)/g' "$f"

  # Pipe suelto en nodo 2:28
  sed -i '' -E 's/\[2:28\|\]/[figma_text_id]/g' "$f"

  # Fence remanente
  sed -i '' '/^```/d' "$f"

  echo "OK: $f"
done

echo ""
echo "=== Verificación post-fix ==="
for f in "${FILES[@]}"; do
  [ -f "$f" ] || continue
  good=$(grep -c '\[figma_text_id\]' "$f" || true)
  bad=$(grep -cE '######[^a-zA-Z]*\[[0-9]+:[0-9]+\]\([0-9]+:[0-9]+\)' "$f" || true)
  fence=$(grep -c '^```' "$f" || true)
  echo "$f -> figma_id=$good | bad=$bad | fences=$fence"
done

echo ""
echo "Si algo sale mal: for f in \"\${FILES[@]}\"; do mv \"\$f.bak2\" \"\$f\"; done"
