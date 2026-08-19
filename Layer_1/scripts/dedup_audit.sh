#!/bin/bash
# VANTAGE Dedup Audit Shortcut
# Ejecuta dedup_opportunities.py para detectar y marcar duplicados vía fuzzy matching

cd "$(dirname "$0")/.."
python3 scripts/dedup_opportunities.py
