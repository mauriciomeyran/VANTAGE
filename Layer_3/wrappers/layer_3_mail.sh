#!/bin/bash
# LAYER 3 mail script con notificaciones de sistema CON SONIDO

notify() {
    osascript -e "display notification \"$2\" with title \"$1\""
}

notify_success() {
    osascript -e "display notification \"$2\" with title \"$1\" sound name \"Hero\""
}

notify_error() {
    osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\""
}

LAYER_1_DIR="$HOME/Documents/04-VANTAGE_CV/LAYER_1"
LAYER_3_DIR="$HOME/Documents/04-VANTAGE_CV/LAYER_3"

# Notificar: En progreso
notify "LAYER 3" "Iniciando procesamiento de mail..."

if [ ! -d "$LAYER_1_DIR/.venv" ]; then
    notify_error "LAYER 3" ".venv no encontrado"
    echo "❌ Error: .venv no encontrado en $LAYER_1_DIR"
    exit 1
fi

VENV_PY="$LAYER_1_DIR/.venv/bin/python3"
if [ ! -x "$VENV_PY" ]; then
    notify_error "LAYER 3" "Python del venv no encontrado"
    echo "❌ Error: Python del venv no encontrado en $VENV_PY"
    echo "💡 Ejecuta: cd \"$LAYER_1_DIR\" && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

cd "$LAYER_3_DIR" || exit 1

if [ ! -f "config/layer_3.env" ]; then
    notify_error "LAYER 3" "config/layer_3.env no encontrado"
    echo "❌ Error: config/layer_3.env no encontrado"
    echo "💡 Copia config/layer_3.env.example → config/layer_3.env y completa las credenciales"
    exit 1
fi

# Ejecutar script Python
if "$VENV_PY" scripts/layer_3_mail.py; then
    notify_success "LAYER 3" "✅ Procesamiento de mail exitoso"
    exit 0
else
    notify_error "LAYER 3" "Falló procesamiento de mail ($?)"
    exit $?
fi
