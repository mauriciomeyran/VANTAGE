#!/bin/bash
# vantage-mcp-tunnel.sh - Orchestrator for VANTAGE MCP SSE Bridge + cloudflared tunnel
# Usage: ./vantage-mcp-tunnel.sh {start|stop|restart|status|url}
#
# Constraints (SESSION CONTRACT HERMES-MCP-REMOTE-TUNNEL-002):
#   - No modification to remote Notion databases or production records.
#   - All configuration stays local to the M2 host filesystem.
#   - Tunnel requires Bearer Token on all requests (auto-generated).
#   - Independent verification required before reporting operational.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SSE_BRIDGE_DIR="$PROJECT_ROOT/.devin/mcp-sse-bridge"
SECRET_FILE="$HOME/.vantage/mcp-secret.txt"
SSE_PID_FILE="$HOME/.vantage/mcp-sse-bridge.pid"
TUNNEL_PID_FILE="$HOME/.vantage/mcp-tunnel-cloudflared.pid"
TUNNEL_URL_FILE="$HOME/.vantage/mcp-tunnel-url.txt"
LOG_DIR="$HOME/.vantage/logs"

SSE_PORT="${VANTAGE_MCP_SSE_PORT:-8080}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

ensure_dirs() {
  mkdir -p "$HOME/.vantage" "$LOG_DIR"
}

# ── Secret management ────────────────────────────────────────────────────────
get_secret() {
  if [ ! -f "$SECRET_FILE" ]; then
    log_error "Secret file not found at $SECRET_FILE"
    log_info "The SSE bridge generates this on first start. Run 'start' first."
    exit 1
  fi
  cat "$SECRET_FILE"
}

# ── SSE Bridge ───────────────────────────────────────────────────────────────
start_sse_bridge() {
  if [ -f "$SSE_PID_FILE" ]; then
    local PID
    PID=$(cat "$SSE_PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
      log_warn "SSE bridge already running (PID: $PID)"
      return 0
    fi
    rm -f "$SSE_PID_FILE"
  fi

  if [ ! -d "$SSE_BRIDGE_DIR" ]; then
    log_error "SSE bridge directory not found: $SSE_BRIDGE_DIR"
    exit 1
  fi

  if [ ! -f "$SSE_BRIDGE_DIR/package.json" ]; then
    log_error "SSE bridge package.json not found. Install deps first:"
    log_info "  cd $SSE_BRIDGE_DIR && npm install"
    exit 1
  fi

  log_info "Starting SSE bridge on port $SSE_PORT..."
  cd "$SSE_BRIDGE_DIR"
  PORT="$SSE_PORT" node server.js >> "$LOG_DIR/mcp-sse-bridge.log" 2>&1 &
  local SSE_PID=$!
  echo "$SSE_PID" > "$SSE_PID_FILE"

  # Wait for SSE bridge to become healthy
  local tries=0
  while [ $tries -lt 15 ]; do
    if ! ps -p "$SSE_PID" > /dev/null 2>&1; then
      log_error "SSE bridge process exited prematurely"
      cat "$LOG_DIR/mcp-sse-bridge.log"
      rm -f "$SSE_PID_FILE"
      exit 1
    fi
    if curl -sf "http://127.0.0.1:$SSE_PORT/health" > /dev/null 2>&1; then
      log_info "SSE bridge started (PID: $SSE_PID)"
      return 0
    fi
    sleep 1
    tries=$((tries + 1))
  done

  log_error "SSE bridge did not become healthy within 15 seconds"
  cat "$LOG_DIR/mcp-sse-bridge.log"
  kill "$SSE_PID" 2>/dev/null || true
  rm -f "$SSE_PID_FILE"
  exit 1
}

stop_sse_bridge() {
  if [ -f "$SSE_PID_FILE" ]; then
    local PID
    PID=$(cat "$SSE_PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
      log_info "Stopping SSE bridge (PID: $PID)..."
      kill "$PID" 2>/dev/null || true
      sleep 2
      if ps -p "$PID" > /dev/null 2>&1; then
        kill -9 "$PID" 2>/dev/null || true
      fi
      log_info "SSE bridge stopped"
    fi
    rm -f "$SSE_PID_FILE"
  else
    log_warn "SSE bridge not running"
  fi
}

# ── Cloudflare Tunnel ────────────────────────────────────────────────────────
start_tunnel() {
  if [ -f "$TUNNEL_PID_FILE" ]; then
    local PID
    PID=$(cat "$TUNNEL_PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
      log_warn "Cloudflared tunnel already running (PID: $PID)"
      return 0
    fi
    rm -f "$TUNNEL_PID_FILE"
  fi

  log_info "Starting cloudflared tunnel to localhost:$SSE_PORT..."
  cloudflared tunnel --url "http://localhost:$SSE_PORT" \
    > "$LOG_DIR/cloudflared.log" 2>&1 &
  local TUNNEL_PID=$!
  echo "$TUNNEL_PID" > "$TUNNEL_PID_FILE"

  # Extract the public URL from cloudflared output
  local tries=0
  while [ $tries -lt 30 ]; do
    if ! ps -p "$TUNNEL_PID" > /dev/null 2>&1; then
      log_error "Cloudflared tunnel exited unexpectedly"
      cat "$LOG_DIR/cloudflared.log"
      rm -f "$TUNNEL_PID_FILE"
      exit 1
    fi
    local TUNNEL_URL
    TUNNEL_URL=$(grep -oE 'https://[a-z0-9.-]+\.trycloudflare\.com' "$LOG_DIR/cloudflared.log" 2>/dev/null | head -1 || true)
    if [ -n "$TUNNEL_URL" ]; then
      echo "$TUNNEL_URL" > "$TUNNEL_URL_FILE"
      log_info "Cloudflared tunnel started (PID: $TUNNEL_PID)"
      log_info "Public URL: $TUNNEL_URL"
      return 0
    fi
    sleep 2
    tries=$((tries + 1))
  done

  log_error "Cloudflared tunnel URL not found within 60 seconds"
  cat "$LOG_DIR/cloudflared.log"
  exit 1
}

stop_tunnel() {
  if [ -f "$TUNNEL_PID_FILE" ]; then
    local PID
    PID=$(cat "$TUNNEL_PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
      log_info "Stopping cloudflared tunnel (PID: $PID)..."
      kill "$PID" 2>/dev/null || true
      sleep 2
      if ps -p "$PID" > /dev/null 2>&1; then
        kill -9 "$PID" 2>/dev/null || true
      fi
      log_info "Cloudflared tunnel stopped"
    fi
    rm -f "$TUNNEL_PID_FILE" "$TUNNEL_URL_FILE"
  else
    log_warn "Cloudflared tunnel not running"
  fi
}

# ── Service management ───────────────────────────────────────────────────────
start() {
  ensure_dirs
  log_info "Starting VANTAGE MCP tunnel services..."
  start_sse_bridge
  start_tunnel

  local SECRET
  SECRET=$(get_secret)

  local TUNNEL_URL=""
  if [ -f "$TUNNEL_URL_FILE" ]; then
    TUNNEL_URL=$(cat "$TUNNEL_URL_FILE")
  fi

  echo ""
  log_info "=== VANTAGE MCP Tunnel Services Started ==="
  echo ""
  echo "SSE Bridge:   http://127.0.0.1:$SSE_PORT"
  echo "Public URL:   $TUNNEL_URL"
  echo "Secret file:  $SECRET_FILE"
  echo ""
  echo "Endpoints:"
  echo "  SSE:    GET  $TUNNEL_URL/sse?server=<mem0|context-sync>"
  echo "  RPC:    POST $TUNNEL_URL/message?server=<mem0|context-sync>"
  echo "  Health: GET  $TUNNEL_URL/health"
  echo ""
  echo "Web Client Configuration String:"
  echo "  URL:     $TUNNEL_URL"
  echo "  Auth:    Bearer $SECRET"
  echo ""
  echo "Copy-paste URL for Claude.ai / remote MCP clients:"
  echo "  SSE: $TUNNEL_URL/sse?server=mem0"
  echo "  Token: Bearer $SECRET"
  echo ""
  echo "Logs: $LOG_DIR/mcp-sse-bridge.log, $LOG_DIR/cloudflared.log"
  echo ""
}

stop() {
  log_info "Stopping VANTAGE MCP tunnel services..."
  stop_tunnel
  stop_sse_bridge
  log_info "All services stopped"
}

status() {
  echo "=== VANTAGE MCP Tunnel Status ==="
  echo ""

  # SSE Bridge
  if [ -f "$SSE_PID_FILE" ]; then
    local PID
    PID=$(cat "$SSE_PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
      echo -e "${GREEN}✓${NC} SSE Bridge: Running (PID: $PID, port $SSE_PORT)"
    else
      echo -e "${RED}✗${NC} SSE Bridge: Stale PID file"
    fi
  else
    echo -e "${RED}✗${NC} SSE Bridge: Not running"
  fi

  # Tunnel
  if [ -f "$TUNNEL_PID_FILE" ]; then
    local PID
    PID=$(cat "$TUNNEL_PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
      echo -e "${GREEN}✓${NC} Cloudflared Tunnel: Running (PID: $PID)"
    else
      echo -e "${RED}✗${NC} Cloudflared Tunnel: Stale PID file"
    fi
  else
    echo -e "${RED}✗${NC} Cloudflared Tunnel: Not running"
  fi

  # Secret
  if [ -f "$SECRET_FILE" ]; then
    local SECRET
    SECRET=$(cat "$SECRET_FILE")
    echo -e "${GREEN}✓${NC} Secret: ${SECRET:0:8}... (truncated)"
  else
    echo -e "${RED}✗${NC} Secret: Not generated"
  fi

  # Tunnel URL
  if [ -f "$TUNNEL_URL_FILE" ]; then
    local TUNNEL_URL
    TUNNEL_URL=$(cat "$TUNNEL_URL_FILE")
    echo -e "${GREEN}✓${NC} Tunnel URL: $TUNNEL_URL"
  else
    echo -e "${YELLOW}-${NC} Tunnel URL: Not available"
  fi

  echo ""
}

show_url() {
  if [ ! -f "$TUNNEL_URL_FILE" ]; then
    log_error "Tunnel not running or URL file not found"
    exit 1
  fi

  local TUNNEL_URL
  TUNNEL_URL=$(cat "$TUNNEL_URL_FILE")
  local SECRET
  SECRET=$(get_secret)

  echo "=== VANTAGE MCP Tunnel URL ==="
  echo ""
  echo "Local:   http://127.0.0.1:$SSE_PORT"
  echo "Public:  $TUNNEL_URL"
  echo ""
  echo "Web Client Configuration:"
  echo "  SSE URL: $TUNNEL_URL/sse?server=mem0"
  echo "  Auth:    Bearer $SECRET"
  echo ""
}

# ── Graceful shutdown on SIGINT/SIGTERM ──────────────────────────────────────
trap 'log_info "Received interrupt signal, shutting down..."; stop; exit 0' INT TERM

# ── Main ─────────────────────────────────────────────────────────────────────
case "${1:-start}" in
  start)   start   ;;
  stop)    stop    ;;
  restart) stop; sleep 2; start ;;
  status)  status  ;;
  url)     show_url ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|url}"
    exit 1
    ;;
esac