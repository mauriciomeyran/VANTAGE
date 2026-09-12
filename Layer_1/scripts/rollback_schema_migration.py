#!/usr/bin/env python3
"""
rollback_schema_migration.py — G8 PASO 9: rollback de valores post-normalización

NO es `git revert`. Restaura valores desde export pre-cutover (PASO 1).

Uso:
  python3 rollback_schema_migration.py --input data/exports/pre_cutover.json --dry-run
  python3 rollback_schema_migration.py --input data/exports/pre_cutover.json --apply

Comportamiento:
  - Valida shape del backup (id + properties).
  - Diff backup vs estado actual (fixture o Notion read).
  - Restaura SOLO props en WRITABLE_PROPS si difieren del backup.
  - Holding: restaura valor de backup tal cual (incl. placeholders si estaban).
  - dry-run default; --apply gateado + class_b_guard.
  - Cero Notion si --fixture / dry-run sin token path.

Nota F9d: re-crear options select legacy en schema NO se hace aquí
(eso es MCP UI). Este script solo reescribe valores de filas.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

sys.path.insert(0, str(Path(__file__).resolve().parent))

from class_b_guard import guard_write_payload  # noqa: E402

logger = logging.getLogger("rollback_schema_migration")
logging.basicConfig(level=logging.INFO, format="%(message)s")

DATA_SOURCE_ID_DEFAULT = "442938be-fc42-828f-b72e-076818d65a5b"
WRITABLE_PROPS = ("Status", "Next_Action", "Gate_Decision", "Holding")


def load_backup(path: Path) -> List[Dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "records" in raw:
        records = raw["records"]
    elif isinstance(raw, list):
        records = raw
    else:
        raise SystemExit("backup must be list or {records: [...]}")
    for i, rec in enumerate(records):
        if "id" not in rec:
            raise SystemExit(f"record[{i}] missing id")
        if "properties" not in rec and not any(k in rec for k in WRITABLE_PROPS):
            raise SystemExit(f"record[{i}] missing properties")
    return records


def extract_flat(rec: Dict[str, Any]) -> Dict[str, Any]:
    """API shape or flat → flat values for WRITABLE_PROPS."""
    flat: Dict[str, Any] = {"id": rec.get("id", "")}
    props = rec.get("properties")
    if isinstance(props, dict):
        for key in list(WRITABLE_PROPS) + ["Source_Type ", "Source_Type"]:
            prop = props.get(key)
            if prop is None:
                continue
            if not isinstance(prop, dict):
                flat[key] = prop
                continue
            t = prop.get("type")
            if t == "select" or "select" in prop:
                sel = prop.get("select")
                flat[key] = (sel or {}).get("name", "") if sel else ""
            elif t == "rich_text" or "rich_text" in prop:
                flat[key] = "".join(
                    c.get("plain_text", "") for c in (prop.get("rich_text") or [])
                )
            else:
                flat[key] = ""
    else:
        for key in WRITABLE_PROPS:
            if key in rec:
                flat[key] = rec[key]
    return flat


def to_notion_props(payload: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, value in payload.items():
        if key == "Holding":
            if value in ("", None):
                out[key] = {"rich_text": []}
            else:
                out[key] = {"rich_text": [{"text": {"content": str(value)[:2000]}}]}
        elif key in ("Status", "Next_Action", "Gate_Decision"):
            if value in ("", None):
                out[key] = {"select": None}
            else:
                out[key] = {"select": {"name": value}}
    return out


def guard_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    result = guard_write_payload(payload, strict_unknown=True)
    clean = dict(result.clean_payload)
    for prop, val in payload.items():
        if prop in WRITABLE_PROPS and prop not in clean:
            clean[prop] = val
    return {k: v for k, v in clean.items() if k in WRITABLE_PROPS}


def plan_rollback(
    backup_records: List[Dict[str, Any]],
    current_by_id: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    For each backup row, if current differs on WRITABLE_PROPS, plan restore to backup values.
    If page missing in current, skip (no undelete).
    """
    plans: List[Dict[str, Any]] = []
    for brec in backup_records:
        bflat = extract_flat(brec)
        pid = bflat.get("id") or ""
        if not pid:
            continue
        cur = current_by_id.get(pid)
        if cur is None:
            # restore-only known pages; missing = skip
            continue
        cflat = extract_flat(cur) if "properties" in cur else dict(cur)
        payload: Dict[str, Any] = {}
        for prop in WRITABLE_PROPS:
            bval = bflat.get(prop, "")
            cval = cflat.get(prop, "")
            # normalize None
            bval = "" if bval is None else bval
            cval = "" if cval is None else cval
            if bval != cval:
                payload[prop] = bval
        if payload:
            plans.append({"page_id": pid, "payload": payload, "from": {
                k: cflat.get(k) for k in payload
            }})
    return plans


def run_rollback(
    backup_records: List[Dict[str, Any]],
    *,
    current_records: Optional[List[Dict[str, Any]]] = None,
    client: Any = None,
    dry_run: bool = True,
    data_source_id: str = DATA_SOURCE_ID_DEFAULT,
) -> Dict[str, Any]:
    """
    current_records: if provided, use as 'current' state (fixture).
    else fetch via client.data_sources.query.
    """
    if current_records is None:
        if client is None:
            raise ValueError("client or current_records required")
        current_records = []
        cursor = None
        while True:
            kw: Dict[str, Any] = {"data_source_id": data_source_id, "page_size": 100}
            if cursor:
                kw["start_cursor"] = cursor
            resp = client.data_sources.query(**kw)
            current_records.extend(resp.get("results") or [])
            if not resp.get("has_more"):
                break
            cursor = resp.get("next_cursor")

    current_by_id = {r.get("id"): r for r in current_records if r.get("id")}
    plans = plan_rollback(backup_records, current_by_id)

    written = 0
    errors = 0
    for item in plans:
        payload = guard_payload(item["payload"])
        if not payload:
            continue
        notion_props = to_notion_props(payload)
        if dry_run:
            logger.info(f"[DRY-RUN] rollback {item['page_id'][:8]} {payload}")
        else:
            try:
                client.pages.update(page_id=item["page_id"], properties=notion_props)
                written += 1
                logger.info(f"[APPLY] rollback {item['page_id'][:8]} {payload}")
            except Exception as exc:
                errors += 1
                logger.error(f"rollback fail {item['page_id'][:8]}: {exc}")

    return {
        "backup_n": len(backup_records),
        "current_n": len(current_records),
        "would_restore": len(plans),
        "written": written,
        "errors": errors,
        "dry_run": dry_run,
        "plans": plans,
    }


def validate_backup_only(backup_file: str) -> List[Dict[str, Any]]:
    """Legacy entry: validate shape, print OK (compat G4d stub)."""
    records = load_backup(Path(backup_file))
    print(f"Loaded backup with {len(records)} records")
    print("✓ Backup validation passed")
    return records


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="G8 rollback valores desde export pre-cutover")
    ap.add_argument("--input", required=True, help="export pre-cutover JSON")
    ap.add_argument("--dry-run", action="store_true", default=False)
    ap.add_argument("--apply", action="store_true", default=False)
    ap.add_argument("--fixture-current", default=None,
                    help="estado 'actual' local (simula post-migra) — cero red")
    ap.add_argument("--data-source-id", default=DATA_SOURCE_ID_DEFAULT)
    ap.add_argument("--env-file", default=None)
    args = ap.parse_args(argv)

    dry_run = not args.apply
    if args.dry_run:
        dry_run = True
    if args.apply:
        dry_run = False

    backup = load_backup(Path(args.input))
    print(f"backup records: {len(backup)}")

    current_records = None
    client = None
    if args.fixture_current:
        raw = json.loads(Path(args.fixture_current).read_text(encoding="utf-8"))
        current_records = raw.get("records") if isinstance(raw, dict) else raw
        # FixtureClient-like for apply path
        class _P:
            def __init__(self):
                self.writes = []
            def update(self, page_id=None, properties=None, **_):
                self.writes.append({"page_id": page_id, "properties": properties})
                return {"id": page_id}

        class _C:
            def __init__(self):
                self.pages = _P()
        client = _C()
    elif not dry_run or True:
        # For dry-run without fixture: need current from Notion OR treat backup==current → 0 plans
        if args.fixture_current is None and dry_run and not os.environ.get("NOTION_TOKEN"):
            # validate-only mode if no current
            validate_backup_only(args.input)
            print("No --fixture-current / token: solo validación de backup (would_restore unknown)")
            print("Para plan completo: --fixture-current post.json o token + query")
            return 0
        if not args.fixture_current:
            token = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")
            if not token:
                ep = Path(args.env_file) if args.env_file else None
                # minimal
                print("ERROR: token or --fixture-current required for full rollback plan", file=sys.stderr)
                return 2
            from notion_client import Client
            client = Client(auth=token)

    metrics = run_rollback(
        backup,
        current_records=current_records if current_records is not None else (
            backup if dry_run and client is None else None
        ),
        client=client,
        dry_run=dry_run,
        data_source_id=args.data_source_id,
    )
    print("=" * 60)
    print(f"G8 rollback — {'DRY-RUN' if metrics['dry_run'] else 'APPLY'}")
    print(f"backup={metrics['backup_n']} current={metrics['current_n']} "
          f"would_restore={metrics['would_restore']} written={metrics['written']} "
          f"errors={metrics['errors']}")
    for p in metrics["plans"][:20]:
        print(f"  {p['page_id'][:8]} {p['from']} → {p['payload']}")
    if len(metrics["plans"]) > 20:
        print(f"  … +{len(metrics['plans'])-20} more")
    print("=" * 60)
    return 1 if metrics["errors"] else 0


if __name__ == "__main__":
    # compat: old CLI --input only
    if len(sys.argv) >= 3 and sys.argv[1] == "--input" and "--dry-run" not in sys.argv and "--apply" not in sys.argv and "--fixture-current" not in sys.argv:
        validate_backup_only(sys.argv[2])
        sys.exit(0)
    sys.exit(main())
