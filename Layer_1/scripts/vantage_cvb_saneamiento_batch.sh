#!/usr/bin/env bash
set -euo pipefail

cd "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Plan Saneamiento/CV-B"

FILES=(
  "2026_Mauricio_Meyran_Confidencial_Gerente_de_Visual_Merchandising_CV-B.md"
  "2026_Mauricio_Meyran_Multicont_Visual_Merchandiser_CV-B.md"
  "2026_Mauricio_Meyran_Eurokor_VM_Skincare_CV-B.md"
  "2026_Mauricio_Meyran_HM_Junior_Retail_Designer_CV-B.md"
  "2026_Mauricio_Meyran_HM_Retail_Designer_CV-B.md"
  "2026_Mauricio_Meyran_Intimissimi_Visual_Merchandising_Coordinator_CV-B.md"
  "2026_Mauricio_Meyran_ServiciosAndreiMoygo_Gerente_Visual_Merchandising_Desarrollo_Tienda_CV-B.md"
  "2026_Mauricio_Meyran_Inditex_Imagen_y_Visual_Merchandiser_CDMX_CV-B.md"
  "2026_Mauricio_Meyran_SARELLY_Global_Retail_Experience_VM_Manager_CV-B.md"
  "2026_Mauricio_Meyran_ZaraHome_VisualMerchandiser_CV-B.md"
)

for f in "${FILES[@]}"; do
  [ -f "$f" ] || { echo "SKIP (no existe): $f"; continue; }
  cp "$f" "$f.bak"

  # 1. Tag roto [N:N](N:N) -> [figma_text_id](N:N)
  sed -i '' -E 's/^(######[[:space:]]+)\[([0-9]+:[0-9]+)\]\(\2\)/\1[figma_text_id](\2)/' "$f"

  # 2. Pipe suelto en nodo 2:28 -> [2:28|](2:28) -> [figma_text_id](2:28)
  sed -i '' -E 's/\[2:28\|\]\(2:28\)/[figma_text_id](2:28)/' "$f"

  # 3. Code fence de apertura ```markdown (o ```json) en línea 1 -> eliminar
  sed -i '' '1{/^```/d;}' "$f"

  # 4. Code fence de cierre ``` (última línea de fence remanente) -> eliminar
  sed -i '' '/^```$/d' "$f"

  echo "OK: $f"
done

echo ""
echo "=== Verificación post-fix ==="
for f in "${FILES[@]}"; do
  [ -f "$f" ] || continue
  good=$(grep -cE '^######[[:space:]]+\[figma_text_id\]\([0-9]+:[0-9]+\)' "$f")
  bad=$(grep -cE '^######[[:space:]]+\[[0-9]+:[0-9]+\]\([0-9]+:[0-9]+\)' "$f")
  fence=$(grep -c '^```' "$f")
  echo "$f -> good=$good bad=$bad fences_restantes=$fence"
done

echo ""
echo "Backups guardados como *.bak junto a cada archivo."
echo "Si algo sale mal: for f in \"\${FILES[@]}\"; do mv \"\$f.bak\" \"\$f\"; done"
