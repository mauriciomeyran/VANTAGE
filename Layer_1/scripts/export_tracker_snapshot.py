#!/usr/bin/env python3
"""
export_tracker_snapshot.py — G8 PASO 1: export pre/post migración

Dry-read del Tracker (data_sources.query) → JSON + sha256.
También acepta --fixture para CI/sandbox (cero red).

Uso:
  python3 export_tracker_snapshot.py --out data/exports/pre.json
  python3 export_tracker_snapshot.py --fixture ../../tests/fixtures/g7_normalization_fixture.json --out /tmp/x.json

Cero writes a Notion siempre (solo query).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

DATA_SOURCE_ID_DEFAULT = "442938be-fc42-828f-b72e-076818d65a5b"


def find_env_file(explicit: Optional[str]) -> Optional[Path]:
    if explicit:
        p = Path(explicit).expanduser()
        return p if p.is_file() else None
    cur = Path.cwd()
    for c in [cur, *cur.parents]:
        for name in ("config/layer_1.env", ".env"):
            ep = c / name
            if ep.is_file():
                return ep
    return None


def load_env_file(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def get_token(env_file: Optional[str]) -> str:
    key = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")
    if key:
        return key
    ep = find_env_file(env_file)
    if ep:
        vals = load_env_file(ep)
        key = vals.get("NOTION_TOKEN") or vals.get("NOTION_API_KEY")
        if key:
            print(f"token from {ep}")
            return key
    print("ERROR: NOTION_TOKEN required unless --fixture", file=sys.stderr)
    sys.exit(2)


def fetch_all(client: Any, data_source_id: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    cursor: Optional[str] = None
    while True:
        kw: Dict[str, Any] = {"data_source_id": data_source_id, "page_size": 100}
        if cursor:
            kw["start_cursor"] = cursor
        resp = client.data_sources.query(**kw)
        records.extend(resp.get("results") or [])
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return records


def load_fixture(path: Path) -> List[Dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return list(raw.get("records") or raw.get("results") or raw.get("rows") or [])
    raise SystemExit(f"fixture shape unsupported: {type(raw)}")


def summarize(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Conteos ligeros por Status/Next_Action/Gate (preflight acta)."""
    from collections import Counter

    def extract(rec: Dict[str, Any], key: str) -> str:
        props = rec.get("properties") or {}
        # try exact + Source_Type dual
        keys = [key]
        if key == "Source_Type":
            keys = ["Source_Type ", "Source_Type"]
        for k in keys:
            prop = props.get(k)
            if not prop:
                if k in rec and not isinstance(rec.get(k), dict):
                    return str(rec.get(k) or "")
                continue
            t = prop.get("type") if isinstance(prop, dict) else None
            if t == "select" and prop.get("select"):
                return prop["select"].get("name") or ""
            if t == "rich_text":
                return "".join(c.get("plain_text", "") for c in prop.get("rich_text") or [])
            if isinstance(prop, dict) and "select" in prop and prop["select"]:
                return prop["select"].get("name") or ""
        return ""

    status_c: Counter = Counter()
    na_c: Counter = Counter()
    gate_c: Counter = Counter()
    st_legacy = st_clean = 0
    for r in records:
        status_c[extract(r, "Status") or "(vacío)"] += 1
        na_c[extract(r, "Next_Action") or "(vacío)"] += 1
        gate_c[extract(r, "Gate_Decision") or "(vacío)"] += 1
        props = r.get("properties") or {}
        if "Source_Type " in props:
            st_legacy += 1
        if "Source_Type" in props:
            st_clean += 1
    return {
        "n": len(records),
        "Status": dict(status_c),
        "Next_Action": dict(na_c),
        "Gate_Decision": dict(gate_c),
        "Source_Type_prop_legacy_rows": st_legacy,
        "Source_Type_prop_clean_rows": st_clean,
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="G8 export Tracker snapshot (read-only)")
    ap.add_argument("--out", required=True, help="path JSON de salida")
    ap.add_argument("--fixture", default=None, help="JSON local — cero red")
    ap.add_argument("--data-source-id", default=DATA_SOURCE_ID_DEFAULT)
    ap.add_argument("--env-file", default=None)
    args = ap.parse_args(argv)

    if args.fixture:
        records = load_fixture(Path(args.fixture))
        source = f"fixture:{args.fixture}"
    else:
        token = get_token(args.env_file)
        try:
            from notion_client import Client
            client = Client(auth=token)
        except Exception as exc:
            print(f"ERROR client: {exc}", file=sys.stderr)
            return 2
        records = fetch_all(client, args.data_source_id)
        source = f"notion:data_source:{args.data_source_id}"

    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "data_source_id": args.data_source_id,
        "n_records": len(records),
        "records": records,
        "summary": summarize(records),
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    out.write_text(text, encoding="utf-8")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    # sidecar sha
    sha_path = out.with_suffix(out.suffix + ".sha256")
    sha_path.write_text(f"{digest}  {out.name}\n", encoding="utf-8")

    print("=" * 60)
    print("G8 export_tracker_snapshot — READ ONLY")
    print("=" * 60)
    print(f"out:      {out}")
    print(f"sha256:   {digest}")
    print(f"records:  {len(records)}")
    print(f"source:   {source}")
    print(f"summary:  {json.dumps(payload['summary'], ensure_ascii=False)}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
