#!/usr/bin/env bash
# Genera paquete_arena_extractos.txt (solo lectura; no modifica el repo).
# Ejecutar con: bash build_paquete_arena.sh   (desde cualquier carpeta dentro del repo VANTAGE)
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1

M="Documentación/ACTIVE/Manual.md"
K="Documentación/ACTIVE/Kernel.md"
OUT="paquete_arena_extractos.txt"

ex() { # etiqueta archivo desde hasta
  echo; echo "=== $1 | $2 L$3-$4 ==="
  awk -v a="$3" -v b="$4" 'NR>=a && NR<=b {printf "L%d| %s\n", NR, $0}' "$2"
}
gr() { # etiqueta patrón contexto archivos...
  local lbl="$1" pat="$2" ctx="$3"; shift 3
  echo; echo "=== $lbl | grep -nE -C$ctx \"$pat\" ==="
  grep -nE -C"$ctx" "$pat" "$@" || echo "(sin coincidencias)"
}

{
  # Kernel
  ex "N2/#1/#5/#10/B-09 (Kernel 07.1)" "$K" 436 450
  ex "#9 (Kernel)"                     "$K" 336 340
  ex "#11 (Kernel)"                    "$K" 452 456
  ex "#10 (Kernel Entry Template)"     "$K" 478 484
  ex "N2 (Kernel Campos protegidos)"   "$K" 688 694
  # Manual
  ex "#1/#10/#11/N2 (Manual §21)"      "$M" 884 894
  ex "#9 (Manual)"                     "$M" 360 364
  ex "#9 (Manual)"                     "$M" 1140 1152
  ex "#9/N3 (Manual)"                  "$M" 1306 1311
  ex "#13/N3 (Manual vsum)"            "$M" 564 574
  ex "#13 (Manual §22.3)"              "$M" 1229 1236
  ex "#12 (Manual, 1a ocurrencia)"     "$M" 922 926
  ex "#12 (Manual, 2a ocurrencia)"     "$M" 954 958
  # Búsquedas
  gr "#3" "consolidate_duplicates" 1 "$M" "$K"
  gr "#4" "vsync_doc|(seis|6) documentos" 1 "$M"
  gr "#5" "GATE-DECISION-012|DEDUP-LAYER-UPGRADE" 1 "$M" "$K"
  # Código (hecho de #4)
  ex "#4 (código)" "Layer_4/scripts/vsync_doc.py" 51 60
} > "$OUT"

echo "Generado: $(pwd)/$OUT ($(wc -l < "$OUT") líneas)"
echo
echo "--- Verificación (NO va a Arena): otros escritores de Fuente en *.py ---"
grep -rnE "[\"']Fuente[\"']" --include="*.py" . | grep -v "Layer_1/scripts/feed_processor.py" | head -30 || true
echo "--- fin ---"
