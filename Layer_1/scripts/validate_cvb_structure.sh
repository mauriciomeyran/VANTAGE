#!/bin/bash
# Validate CV-B files structure for VANTAGE CV Sync
# This script checks that all markdown files comply with the required format

set -e

CVB_DIR="/Users/karlameyran/Library/CloudStorage/GoogleDrive-mauricio.meyran@gmail.com/Mi unidad/Plan Saneamiento/CV-B"

echo "=== VANTAGE CV Sync Structure Validation ==="
echo "Directory: $CVB_DIR"
echo "=============================================="
echo ""

cd "$CVB_DIR"

# Expected format regex (Figma parser regex: /######\s+\[figma_text_id\]\(([^)]+)\)/)
# Expected: ###### [figma_text_id](N:N)

total_files=0
pass_files=0
fail_files=0

for file in *.md; do
    if [ ! -f "$file" ]; then
        continue
    fi
    
    total_files=$((total_files + 1))
    file_passed=true
    
    echo "FILE: $file"
    
    # Check 1: File starts with correct tag format
    first_line=$(head -1 "$file")
    if [[ ! "$first_line" =~ ^######\ \[figma_text_id\]\([0-9]+:[0-9]+\) ]]; then
        echo "  ❌ FAIL: First line doesn't match expected format: ###### [figma_text_id](N:N)"
        echo "     Found: $first_line"
        file_passed=false
    else
        echo "  ✅ PASS: First line format correct"
    fi
    
    # Check 2: Count figma_text_id tags
    figma_count=$(grep -c '\[figma_text_id\]' "$file" 2>/dev/null || true)
    if [ -z "$figma_count" ]; then
        figma_count=0
    fi
    echo "  📊 figma_text_id tags: $figma_count"
    
    # Check 3: Check for broken tags (wrong format)
    broken=$(grep -c '\[[0-9]*:[0-9]*\](\[0-9]*:[0-9]*)' "$file" 2>/dev/null || true)
    if [ -z "$broken" ]; then
        broken=0
    fi
    if [ "$broken" -gt 0 ]; then
        echo "  ❌ FAIL: Found $broken broken tags (format [N:N](N:N) instead of [figma_text_id](N:N))"
        file_passed=false
    else
        echo "  ✅ PASS: No broken tags found"
    fi
    
    # Check 4: Check for stray pipe characters in tags
    pipe_count=$(grep -c '\[figma_text_id|\]' "$file" 2>/dev/null || true)
    if [ -z "$pipe_count" ]; then
        pipe_count=0
    fi
    if [ "$pipe_count" -gt 0 ]; then
        echo "  ❌ FAIL: Found $pipe_count tags with stray pipe character"
        file_passed=false
    else
        echo "  ✅ PASS: No stray pipe characters in tags"
    fi
    
    # Check 5: Check for code fences at start (should not have)
    first_line_fence=$(head -1 "$file" | grep -c '```' || true)
    if [ -z "$first_line_fence" ]; then
        first_line_fence=0
    fi
    if [ "$first_line_fence" -gt 0 ]; then
        echo "  ❌ FAIL: File starts with code fence (should not have)"
        file_passed=false
    else
        echo "  ✅ PASS: No code fence at start"
    fi
    
    # Check 6: Sample tag validation
    sample_tag=$(grep -m1 '\[figma_text_id\]' "$file" || echo "")
    if [[ "$sample_tag" =~ ^######\ \[figma_text_id\]\([0-9]+:[0-9]+\) ]]; then
        echo "  ✅ PASS: Sample tag format correct: $sample_tag"
    else
        echo "  ❌ FAIL: Sample tag format incorrect: $sample_tag"
        file_passed=false
    fi
    
    # Check 7: Check for unclosed code fences
    open_fence=$(grep -c '```' "$file" 2>/dev/null || true)
    if [ -z "$open_fence" ]; then
        open_fence=0
    fi
    if [ "$((open_fence % 2))" -ne 0 ]; then
        echo "  ❌ FAIL: Unclosed code fence detected (odd number of fence markers: $open_fence)"
        file_passed=false
    else
        echo "  ✅ PASS: Code fences properly closed"
    fi
    
    if [ "$file_passed" = true ]; then
        pass_files=$((pass_files + 1))
        echo "  🎯 RESULT: PASS"
    else
        fail_files=$((fail_files + 1))
        echo "  🎯 RESULT: FAIL"
    fi
    
    echo ""
done

echo "=============================================="
echo "VALIDATION SUMMARY"
echo "=============================================="
echo "Total files checked: $total_files"
echo "Passed: $pass_files"
echo "Failed: $fail_files"
echo ""

if [ $fail_files -eq 0 ]; then
    echo "✅ ALL FILES PASSED VALIDATION"
    exit 0
else
    echo "❌ SOME FILES FAILED VALIDATION"
    exit 1
fi