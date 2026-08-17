#!/bin/bash
# LAYER 3 mail script con notificaciones de sistema CON SONIDO
export PYTHONUNBUFFERED=1

notify() {
    osascript -e "display notification \"$2\" with title \"$1\""
}

notify_success() {
    osascript -e "display notification \"$2\" with title \"$1\" sound name \"Hero\""
}

notify_error() {
    osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\""
}

LAYER_1_DIR="$HOME/Documents/03 Projects/VANTAGE/Layer_1"
LAYER_3_DIR="$HOME/Documents/03 Projects/VANTAGE/Layer_3"

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

# Bucle de procesamiento: corre hasta que no queden correos
while true; do
    tmp=$(mktemp)
    "$VENV_PY" scripts/layer_3_mail.py 2>&1 | tee "$tmp"
    out=$(<"$tmp")
    rm -f "$tmp"
    if echo "$out" | grep -qE "No hay correos nuevos|Quedan ~0"; then
        echo "🏁 VL3 terminó — no quedan correos pendientes"
        notify_success "LAYER 3" "🏁 VL3 terminó — no quedan correos pendientes"
        break
    fi
    if echo "$out" | grep -qE "ABORT: Groq|Groq acceso denegado|Modelo Groq"; then
        echo "🛑 VL3 detenido — error de configuración Groq"
        notify_error "LAYER 3" "Groq error — revisa modelo/VPN/créditos"
        exit 1
    fi
    sleep 5
done
notify_success "LAYER 3" "✅ Procesamiento de mail exitoso"
exit 0
