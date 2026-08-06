#!/usr/bin/env bash

TARGET_URL="https://gitingest.com/raw/mauriciomeyran/VANTAGE"
OUTPUT_FILE="${1:-VANTAGE_digest.txt}"

echo "Descargando ingest de VANTAGE desde $TARGET_URL..."

curl -s -L "$TARGET_URL" -o "$OUTPUT_FILE"

if [ -s "$OUTPUT_FILE" ]; then
    echo "Digest de VANTAGE guardado en: $OUTPUT_FILE"
    echo "Tamaño: $(du -h "$OUTPUT_FILE" | cut -f1)"
else
    echo "Error: El archivo descargado está vacío."
    rm -f "$OUTPUT_FILE"
    exit 1
fi
