#!/usr/bin/env python3
"""
verify_versions.py — VANTAGE Manifest Reader / Sync Orchestrator (v3.0)
"""
import os, sys, argparse, requests
from datetime import datetime

NOTION_VERSION = "2022-06-28"
API_BASE = "https://api.notion.com/v1"
MANIFEST_DB_ID = "290e849f-92e3-4f0f-b025-94769f40dfeb"
CHANGELOG_PAGE_ID = "390938be-fc42-80e7-b429-d7d730339353"
VERSION_EXEMPT = {"LEDGER"}

def load_token():
    env_path = os.path.expanduser("~/Documents/03 Projects/VANTAGE/Layer_1/.env")
    if os.path.isfile(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("NOTION_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"\'')
    return os.environ.get("NOTION_TOKEN", "").strip()

def _h(token, write=False):
    h = {"Authorization": f"Bearer {token}", "Notion-Version": NOTION_VERSION}
    if write: h["Content-Type"] = "application/json"
    return h

def get_manifest(token):
    r = requests.post(f"{API_BASE}/databases/{MANIFEST_DB_ID}/query", headers=_h(token, True), json={})
    r.raise_for_status()
    return r.json()["results"]

def parse_manifest(rows):
    out = {}
    for row in rows:
        p = row["properties"]
        name = (p.get("Componente", {}).get("title") or [{}])[0].get("plain_text", "(unnamed)")
        version = "".join(t["plain_text"] for t in p.get("Versión", {}).get("rich_text", []))
        status = (p.get("Status", {}).get("select") or {}).get("name", "UNKNOWN")
        out[name] = {"version": version, "status": status, "page_id": row["id"]}
    return out

def get_changelog_version(token):
    r = requests.get(f"{API_BASE}/pages/{CHANGELOG_PAGE_ID}", headers=_h(token))
    r.raise_for_status()
    return "".join(t["plain_text"] for t in r.json().get("properties", {}).get("Versión", {}).get("rich_text", [])) or "v0.0.0"

def patch_row(page_id, version, status, token):
    r = requests.patch(f"{API_BASE}/pages/{page_id}", headers=_h(token, True),
        json={"properties": {
            "Versión": {"rich_text": [{"text": {"content": version}}]},
            "Status": {"select": {"name": status}},
            "Last Sync": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}}
        }})
    if not r.ok: print(f"  WARNING: {page_id} — {r.status_code}: {r.text[:100]}")

def mode_check(token):
    print("=" * 55)
    print("VANTAGE — MANIFEST CHECK (read-only)")
    print("=" * 55)
    manifest = parse_manifest(get_manifest(token))
    if not manifest: sys.exit("FAIL — 0 rows.")
    for name, d in manifest.items():
        tag = " [exempt]" if name in VERSION_EXEMPT else ""
        flag = "v" if d["status"] == "OK" else "x"
        print(f"  [{flag}] {name:<15} {d['version'] or '(empty)':<12} [{d['status']}]{tag}")
    print("-" * 55)
    versioned = {k: v for k, v in manifest.items() if k not in VERSION_EXEMPT}
    outdated = {k: v for k, v in versioned.items() if v["status"] != "OK"}
    versions = set(v["version"] for v in versioned.values())
    if outdated or len(versions) > 1:
        print("FAIL — Version drift:")
        for k, v in outdated.items(): print(f"  OUTDATED: {k} -> {v['version']}")
        if len(versions) > 1: print(f"  VERSION SET: {versions}")
        sys.exit(1)
    print(f"PASS — all components at {next(iter(versions))}")

def mode_sync(token):
    print("=" * 55)
    print("VANTAGE — MANIFEST SYNC (write)")
    print("=" * 55)
    new_v = get_changelog_version(token)
    print(f"Target: {new_v}")
    print("-" * 55)
    for name, d in parse_manifest(get_manifest(token)).items():
        patch_row(d["page_id"], new_v, "OK", token)
        print(f"  Updated: {name:<15} -> {new_v}")
    print(f"SYNC COMPLETE — Baseline: {new_v}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sync", action="store_true")
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    token = load_token()
    if not token: sys.exit("ERROR: Token no encontrado.")
    mode_sync(token) if args.sync else mode_check(token)

if __name__ == "__main__":
    main()
