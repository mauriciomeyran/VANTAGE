#!/bin/bash
# Start VANTAGE Serial Allocation HTTP Server

# Configuration
VANTAGE_ROOT="/Users/mauriciomeyran/Documents/03 Projects/VANTAGE"
SCRIPT_DIR="$VANTAGE_ROOT/Layer_1/scripts"
HTTP_SERVER="$SCRIPT_DIR/vantage_serial_http_server.py"
LOG_FILE="$VANTAGE_ROOT/state/vantage_serial_server.log"
PID_FILE="$VANTAGE_ROOT/state/vantage_serial_server.pid"

# Environment
export VANTAGE_SERIAL_DB="$VANTAGE_ROOT/state/vantage_handoff_counter.sqlite3"
export VANTAGE_SERIAL_HOST="localhost"
export VANTAGE_SERIAL_PORT="8787"

echo "Starting VANTAGE Serial Allocation HTTP Server..."
echo "Database: $VANTAGE_SERIAL_DB"
echo "Host: $VANTAGE_SERIAL_HOST:$VANTAGE_SERIAL_PORT"
echo "Log: $LOG_FILE"

# Start server in background
cd "$SCRIPT_DIR"
nohup python3 "$HTTP_SERVER" > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

echo "Server started with PID: $(cat $PID_FILE)"
echo "HTTP API available at: http://$VANTAGE_SERIAL_HOST:$VANTAGE_SERIAL_PORT"
echo ""
echo "Endpoints:"
echo "  POST http://$VANTAGE_SERIAL_HOST:$VANTAGE_SERIAL_PORT/allocate - Allocate serial"
echo "  GET  http://$VANTAGE_SERIAL_HOST:$VANTAGE_SERIAL_PORT/health - Get status"
echo ""
echo "To stop the server: kill $(cat $PID_FILE)"
