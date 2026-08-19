#!/usr/bin/env python3
"""VANTAGE Scout Layer 1 - Web UI"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

PACKAGE_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PACKAGE_ROOT / "output"

app = Flask(__name__, template_folder=str(PACKAGE_ROOT))


@app.route("/")
def index():
    """Main dashboard page."""
    return render_template("index.html")


@app.route("/api/wrappers")
def get_wrappers():
    """Get available wrappers."""
    wrappers = [
        {"id": "Prompt_Career_Sites", "name": "Career Sites", "description": "Official career pages and ATS platforms"},
        {"id": "Prompt_LinkedIn", "name": "LinkedIn", "description": "LinkedIn Jobs only"},
        {"id": "Prompt_Aggregators", "name": "Aggregators", "description": "OCC, Indeed, Computrabajo, etc."},
    ]
    return jsonify(wrappers)


@app.route("/api/run", methods=["POST"])
def run_scout():
    """Execute a scout wrapper."""
    data = request.json
    wrapper = data.get("wrapper")
    dry_run = data.get("dry_run", False)
    
    if not wrapper:
        return jsonify({"error": "Wrapper is required"}), 400
    
    try:
        # Build command
        cmd = [sys.executable, str(PACKAGE_ROOT / "main.py"), "--wrapper", wrapper]
        if dry_run:
            cmd.append("--dry-run")
        
        # Run the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes timeout
            cwd=str(PACKAGE_ROOT.parent)
        )
        
        if result.returncode != 0:
            return jsonify({
                "error": "Execution failed",
                "stderr": result.stderr,
                "stdout": result.stdout
            }), 500
        
        # Parse JSON output
        try:
            output_data = json.loads(result.stdout)
            return jsonify({"success": True, "data": output_data})
        except json.JSONDecodeError:
            return jsonify({
                "error": "Invalid JSON output",
                "raw_output": result.stdout
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Execution timeout"}), 408
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/results")
def get_results():
    """Get latest results from output directory."""
    if not OUTPUT_DIR.exists():
        return jsonify({"results": []})
    
    results = []
    for file_path in sorted(OUTPUT_DIR.glob("*.json"), reverse=True)[:10]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                results.append({
                    "filename": file_path.name,
                    "date": file_path.stat().st_mtime,
                    "items_count": len(data.get("items", [])),
                    "wrapper": file_path.stem.replace("vantage_scout_", "").rsplit("_", 1)[0],
                    "data": data
                })
        except Exception:
            continue
    
    return jsonify({"results": results})


@app.route("/api/config")
def get_config():
    """Get current configuration status."""
    from dotenv import load_dotenv
    import os
    
    env_file = PACKAGE_ROOT / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    config = {
        "llm_provider": os.getenv("LLM_PROVIDER", "Not configured"),
        "browser_headless": os.getenv("BROWSER_HEADLESS", "false"),
        "cost_limit": os.getenv("LLM_COST_LIMIT", "5.0"),
        "env_exists": env_file.exists()
    }
    
    return jsonify(config)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
