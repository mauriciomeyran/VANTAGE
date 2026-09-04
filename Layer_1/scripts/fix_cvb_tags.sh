#!/bin/bash
# Fix broken Figma node tags in CV-B files
# Compatible with BSD/macOS sed (uses -i '' syntax)

set -e

# Directory containing CV-B files
CVB_DIR="/Users/karlameyran/Library/CloudStorage/GoogleDrive-mauricio.meyran@gmail.com/Mi unidad/Plan Saneamiento/CV-B"

# Files to fix (all .md files in directory)
FILES=(*.md)

echo "Starting CV-B tag fix..."
echo "=========================="

# Change to CV-B directory
cd "$CVB_DIR"

for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "WARNING: File not found: $file"
        continue
    fi
    
    echo "Processing: $file"
    
    # Fix 1: Replace [N:N](N:N) → [figma_text_id](N:N)
    sed -i '' 's/\[[0-9]*:[0-9]*\]/[figma_text_id]/g' "$file"
    
    # Fix 2: Fix stray pipe character in node 2:28 (Eurokor, HM_Junior, HM_Retail_Designer)
    sed -i '' 's/\[2:28|\]/[figma_text_id]/g' "$file"
    
    # Fix 3: Remove stray code fence markers
    sed -i '' '/^```$/d' "$file"
    
    echo "  ✓ Fixed tags in $file"
done

echo "=========================="
echo "Tag fix complete!"
echo ""
echo "Verification:"
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        count=$(grep -c "\[figma_text_id\]" "$file" || echo "0")
        broken=$(grep -c "\[[0-9]*:[0-9]*\]\([0-9]*:[0-9]*\)" "$file" || echo "0")
        echo "  $file: $count figma_text_id tags, $broken broken tags"
    fi
done