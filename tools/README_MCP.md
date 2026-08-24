# VANTAGE Serial Allocation MCP Server

## Overview

This MCP server exposes the VANTAGE handoff serial allocation functionality as an MCP tool, allowing agents without terminal or filesystem access to allocate serial numbers from the GLOBAL_VANTAGE_COUNTER.

## Installation

### 1. Install Dependencies

```bash
cd /Users/mauriciomeyran/Documents/03 Projects/VANTAGE/tools
pip install -r requirements_mcp.txt
```

### 2. Verify Configuration

The MCP server is already configured in `~/.config/devin/mcp_config.json`:

```json
{
  "vantage-serial": {
    "command": "python3",
    "args": [
      "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/tools/mcp_vantage_serial_server.py"
    ],
    "env": {
      "VANTAGE_SERIAL_DB": "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/state/vantage_handoff_counter.sqlite3"
    }
  }
}
```

### 3. Restart MCP Client

Restart your MCP client (Devin CLI) to load the new server configuration.

## Usage

### MCP Tool: `allocate_vantage_serial`

**Input:** `{}` (empty object)

**Output (Success):**
```json
{
  "serial": "HO-000004",
  "authority": "GLOBAL_VANTAGE_COUNTER",
  "status": "ALLOCATED"
}
```

**Output (Error):**
```json
{
  "error": "HANDOFF_SERIAL_UNAVAILABLE",
  "status": "UNAVAILABLE",
  "detail": "Error details here"
}
```

### Example MCP Call

```python
# From any agent with MCP access
result = mcp_call_tool("vantage-serial", "allocate_vantage_serial", {})
if result["status"] == "ALLOCATED":
    serial = result["serial"]
    # Use the serial for handoff
```

## Fallback Logic for Skills

Skills that need serial allocation should implement fallback logic:

```python
def get_handoff_serial():
    try:
        # 1. Try MCP first
        result = mcp_call_tool("vantage-serial", "allocate_vantage_serial", {})
        if result["status"] == "ALLOCATED":
            return result["serial"]
    except:
        pass
    
    # 2. Fallback: Terminal available
    if has_terminal():
        result = subprocess.run([
            "python3", 
            "/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/scripts/allocate_vantage_serial.py",
            "next"
        ], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    
    # 3. No MCP or Terminal available
    return {"error": "HANDOFF_SERIAL_UNAVAILABLE", "status": "UNAVAILABLE"}
```

## Architecture

- **Reuses existing logic:** Imports functions from `Layer_1/scripts/allocate_vantage_serial.py`
- **SQLite transactional:** Uses the same database and counter mechanism
- **Authority:** GLOBAL_VANTAGE_COUNTER (consistent with existing implementation)
- **Format:** HO-XXXXXX (6-digit zero-padded serial numbers)

## Files

- **Server:** `tools/mcp_vantage_serial_server.py` - MCP server implementation
- **Dependencies:** `tools/requirements_mcp.txt` - Python package requirements
- **Database:** `state/vantage_handoff_counter.sqlite3` - SQLite counter database
- **Config:** `~/.config/devin/mcp_config.json` - MCP server configuration
- **Original logic:** `Layer_1/scripts/allocate_vantage_serial.py` - NOT MODIFIED

## Testing

### Dry Run (with temporary database)

```bash
# Create temporary database for testing
export VANTAGE_SERIAL_DB=/tmp/test_vantage_serials.sqlite3
python3 tools/mcp_vantage_serial_server.py
```

### Production (with real database)

Uses the configured database path: `state/vantage_handoff_counter.sqlite3`

## Troubleshooting

### MCP Server Not Starting

- Verify MCP SDK is installed: `pip show mcp`
- Check Python path in `mcp_config.json`
- Verify database path is accessible

### Serial Allocation Failing

- Check database file permissions
- Verify SQLite database is not corrupted
- Check GLOBAL_VANTAGE_COUNTER exists in database

### Configuration Issues

- Verify `~/.config/devin/mcp_config.json` syntax
- Restart MCP client after configuration changes
- Check environment variables are set correctly

## Integration Notes

- **Health Check:** The existing health check remains unchanged
- **HTTP Service:** The Flask HTTP service in `allocate_vantage_serial.py` is not affected
- **Counter:** GLOBAL_VANTAGE_COUNTER is not reinitialized
- **Database:** The existing SQLite database is used without modification
