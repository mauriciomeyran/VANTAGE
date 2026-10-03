#!/usr/bin/env python3
"""
foundational_docs.py — VANTAGE L4
Fuente única del mapeo page_id → key de vsync_doc.DOCS.

Antes esta lista estaba duplicada (idéntica) en notion_write_wrapper.py y en
trigger_sync_after_mcp_write.py: cualquier alta/baja de documento fundacional
debía editarse dos veces o los dos scripts quedaban en drift (ver hallazgo B11
en handoffs/VALIDACION_GENERATE_CENSUS_Y_LAYER4_2026-10-02.md).

Los page_id deben coincidir con las claves de vsync_doc.DOCS.
"""

from __future__ import annotations

import os
from pathlib import Path

FOUNDATIONAL_DOCS = {
    "377938be-fc42-805e-a408-c9ae518d4fe7": "kernel",
    "37b938be-fc42-8001-9b9b-fcf81130d274": "system_prompt",
    "377938be-fc42-8089-93f2-f52dbd2dec6c": "career_canon",
    "372938be-fc42-8050-9a67-e40857d7806e": "manual",
    "37c938be-fc42-80d4-b9ae-f5969830331b": "aliases",
    "390938be-fc42-80e7-b429-d7d730339353": "change_log",
    "3a3938be-fc42-8008-9e90-ec435c01f50d": "brief",
    "3ba938be-fc42-8011-8947-fb4fa5d1f63f": "change_log_archivo",
    "f87938be-fc42-8263-a305-819877d2245f": "project_charter",
}

DEFAULT_MCP_SYNC_LOG = "/tmp/vantage_mcp_sync.log"


def mcp_sync_log_path() -> Path:
    """Ruta del log del sync post-MCP (configurable con VANTAGE_MCP_SYNC_LOG)."""
    return Path(os.environ.get("VANTAGE_MCP_SYNC_LOG", DEFAULT_MCP_SYNC_LOG))
