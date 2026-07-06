#!/bin/bash
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BASE="/Users/mauriciomeyran/Documents/04-VANTAGE_CV/DOCUMENTACIÓN"
SRC="$BASE/VANTAGE 8.0"
DST="$BASE/VANTAGE 8.2"
BACKUP="$SRC/parachutes_pre_live_$TIMESTAMP"

echo "▶ VANTAGE Deploy v8.0 → v8.2 — $TIMESTAMP"

[ -d "$SRC" ] || { echo "ERROR: Carpeta origen no encontrada: $SRC"; exit 1; }
[ -d "$DST" ] || { echo "ERROR: Carpeta destino no encontrada: $DST"; exit 1; }

for f in "CAREER CANON V8.2.md" "KERNEL V8.2.md" "SYSTEM PROMPT V8.2.md"; do
  [ -f "$DST/$f" ] || { echo "ERROR: '$f' no encontrado. Abortar."; exit 1; }
done
echo "✓ Archivos v8.2 validados"

mkdir -p "$BACKUP"
cp "$SRC/CAREER_v8.0.md" "$BACKUP/CAREER_v8.0_pre_live_$TIMESTAMP.md"
cp "$SRC/KERNEL_v8.0.md" "$BACKUP/KERNEL_v8.0_pre_live_$TIMESTAMP.md"
cp "$SRC/SYSTEM_v8.0.md" "$BACKUP/SYSTEM_v8.0_pre_live_$TIMESTAMP.md"
echo "✓ Parachutes creados en: VANTAGE 8.0/parachutes_pre_live_$TIMESTAMP/"

echo ""
echo "════════════════════════════════════════"
echo "PASO MANUAL OBLIGATORIO:"
echo "  → Abrir Claude Projects"
echo "  → Pegar contenido de 'SYSTEM PROMPT V8.2.md' en System Instructions"
echo "  → Attachments: 'KERNEL V8.2.md' + 'CAREER CANON V8.2.md'"
echo "  → Sesión NUEVA → SYNC como smoke test"
echo "════════════════════════════════════════"
