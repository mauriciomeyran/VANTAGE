#!/bin/bash
# Entrada pública LAYER_1 v7.5 — delega al core (seguro vía symlink ~/vantage_pipeline.sh)
# Con notificaciones de sistema: En progreso / Completado (sonido) / Error (sonido)

notify() {
    osascript -e "display notification \"$2\" with title \"$1\""
}

notify_success() {
    osascript -e "display notification \"$2\" with title \"$1\" sound name \"Hero\""
}

notify_error() {
    osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\""
}

VANTAGE_ROOT="$HOME/Documents/04-Vantage_CV"
ROOT="${LAYER_1_DIR:-$VANTAGE_ROOT/Layer_1}"
FEEDS_DIR="$VANTAGE_ROOT/Layer_1/feeds"

# Si no se pasan argumentos, detectar el feed más reciente
if [ $# -eq 0 ]; then
    LATEST_FEED=$(ls -t "$FEEDS_DIR"/*.json 2>/dev/null | head -1 | xargs basename)
    if [ -n "$LATEST_FEED" ]; then
        set -- feed "$LATEST_FEED"
    fi
fi


# Notificar: En progreso
notify "VANTAGE" "Iniciando pipeline..."

# Ejecutar pipeline
if "$ROOT/layer_1_pipeline.sh" "$@"; then
    # Notificar: Completado CON SONIDO (Hero)
    notify_success "VANTAGE" "✅ Pipeline completado exitosamente"
    exit 0
else
    # Notificar: Error CON SONIDO (Basso)
    notify_error "VANTAGE" "❌ Error: Pipeline falló ($?)"
    exit $?
fi
