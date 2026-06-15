#!/bin/bash
# Dashboard start script con notificaciones de sistema CON SONIDO

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
DASHBOARD_DIR="$HOME/Documents/04-VANTAGE_CV/DASHBOARD"

# Notificar: En progreso
notify "Dashboard" "Iniciando servidor..."

# Cargar variables de entorno
set -a
[ -f "$LAYER_1_DIR/.env" ] && source "$LAYER_1_DIR/.env"
set +a

cd "$DASHBOARD_DIR" || exit 1
source "$LAYER_1_DIR/.venv/bin/activate"

export PYTHONPATH="$DASHBOARD_DIR/scripts:$LAYER_1_DIR/scripts${PYTHONPATH:+:$PYTHONPATH}"

pkill -f dashboard_server.py 2>/dev/null

python3 scripts/dashboard_server.py &
SERVER_PID=$!
echo "✅ Servidor iniciado (PID $SERVER_PID)"

for i in {1..10}; do
    sleep 1
    python3 -c "import requests; requests.get('http://127.0.0.1:8000/health')" 2>/dev/null && break
done

sleep 2
python3 scripts/smoke_dashboard.py
SMOKE=$?

if [ $SMOKE -eq 0 ]; then
    notify_success "Dashboard" "Servidor listo, abriendo dashboard..."
    echo "✅ Smoke test OK — abriendo dashboard..."
    open "$DASHBOARD_DIR/dashboard.html"
else
    notify_error "Dashboard" "Smoke test falló"
    echo "❌ Smoke test falló — revisa el servidor"
    exit 1
fi
