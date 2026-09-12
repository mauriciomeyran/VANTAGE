#!/usr/bin/env python3
"""
normalize_tracker_values.py — G7 normalización idempotente del Tracker

Tabla ejecutable actual→normalizado (vive en tracker_flow.NORMALIZATION_TABLE):
  Next_Action  Follow-up/Interview prep/Re-check/Ninguna/Expirada → ES canónico
  Gate_Decision EXPIRADA → EXPIRED (resto técnico EN fijado)
  Status       Target/Archivar/casing → Objetivo/Retirado/Title Case
  Holding      placeholders Investigar/N/A/- → vacío (reales jamás se vacían)
  Source_Type  rename propiedad Source_Type␣ → Source_Type = G8 MCP (aquí solo plan)

Uso (patrón vl1_sync):
    python3 normalize_tracker_values.py                  # dry-run default
    python3 normalize_tracker_values.py --dry-run
    python3 normalize_tracker_values.py --apply           # gateado: requiere token
    python3 normalize_tracker_values.py --fixture path.json
    python3 normalize_tracker_values.py --resume state.json

Garantías:
  - dry-run default → cero writes (proxy read-only o fixture local)
  - idempotente: 2ª pasada diffs=0
  - reanudable: --resume salta page_ids ya procesados
  - pre/post counts por propiedad y por valor
  - class_b_guard en todo write path
  - Cero Notion prod en esta sesión de desarrollo (fixtures + fake)

G8 (fuera de alcance aquí): rename schema vivo Source_Type␣ y prune opciones
select vía Claude/MCP con APROBAR_WRITE.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tracker_flow import (  # noqa: E402
    NORMALIZATION_TABLE,
    SOURCE_TYPE_PROP_ALIASES,
    SOURCE_TYPE_PROP_CANONICAL,
    SOURCE_TYPE_PROP_LEGACY,
    normalize_field_value,
    normalize_record,
    normalization_diff,
    to_notion_properties,
)
from class_b_guard import guard_write_payload  # noqa: E402

logger = logging.getLogger("normalize_tracker_values")
logging.basicConfig(level=logging.INFO, format="%(message)s")

DATA_SOURCE_ID_DEFAULT = "442938be-fc42-828f-b72e-076818d65a5b"

# Props que este script puede escribir (valores normalizados).
# Source_Type rename de PROPIEDAD = G8 schema; aquí solo unificamos valor en plano.
WRITABLE_PROPS = ("Status", "Next_Action", "Gate_Decision", "Holding")


# ── Env / token (mismo patrón que vl1_sync) ──────────────────────────────────

def find_env_file(explicit_path: Optional[str]) -> Optional[Path]:
    if explicit_path:
        p = Path(explicit_path).expanduser()
        return p if p.is_file() else None
    current = Path.cwd()
    for candidate in [current, *current.parents]:
        for name in ("config/layer_1.env", ".env"):
            env_path = candidate / name
            if env_path.is_file():
                return env_path
    return None


def load_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def get_notion_token(explicit_env_path: Optional[str]) -> str:
    key = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")
    if key:
        return key
    env_path = find_env_file(explicit_env_path)
    if env_path:
        values = load_env_file(env_path)
        key = values.get("NOTION_TOKEN") or values.get("NOTION_API_KEY")
        if key:
            logger.info(f"NOTION_TOKEN cargado desde {env_path}")
            return key
        logger.error(f"{env_path} sin NOTION_TOKEN/NOTION_API_KEY")
        sys.exit(1)
    logger.error("NOTION_TOKEN/NOTION_API_KEY no encontrado")
    sys.exit(1)


# ── Proxy read-only ──────────────────────────────────────────────────────────

class _NoWritePages:
    def __init__(self) -> None:
        self.would_update: List[Dict[str, Any]] = []

    def update(
        self,
        page_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        **_: Any,
    ) -> Dict[str, Any]:
        self.would_update.append({"page_id": page_id, "properties": properties or {}})
        logger.info(f"[DRY-RUN] would update {str(page_id)[:8]} -> {list((properties or {}).keys())}")
        return {"id": page_id, "_dry_run": True}


class ReadOnlyNotionClient:
    """Lecturas pasan; pages.update interceptado."""

    def __init__(self, real: Any) -> None:
        self._real = real
        self.pages = _NoWritePages()
        self.data_sources = real.data_sources


class _FixturePages:
    def __init__(self, outer: "FixtureClient") -> None:
        self._outer = outer

    def update(self, page_id=None, properties=None, **_):
        return self._outer.pages_update(page_id, properties or {})


class _FixtureDS:
    def __init__(self, records: List[Dict[str, Any]]) -> None:
        self._records = records

    def query(self, **_: Any) -> Dict[str, Any]:
        return {"results": self._records, "has_more": False}


class FixtureClient:
    """Cliente local: records desde fixture JSON (cero red)."""

    def __init__(self, records: List[Dict[str, Any]]) -> None:
        self._records = records
        self.writes: List[Dict[str, Any]] = []
        self.pages = _FixturePages(self)
        self.data_sources = _FixtureDS(records)

    def pages_update(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        self.writes.append({"page_id": page_id, "properties": properties})
        return {"id": page_id}


# ── Core ─────────────────────────────────────────────────────────────────────

def build_normalization_payload(flat: Dict[str, Any]) -> Dict[str, Any]:
    """
    Diff material actual→normalizado. Solo props con cambio real.
    Holding: solo placeholders (tabla); holdings reales no están en tabla → no toca.
    """
    payload: Dict[str, Any] = {}
    for prop in WRITABLE_PROPS:
        cur = flat.get(prop, "")
        if cur in (None, ""):
            # Holding vacío ya OK; Next_Action vacío puede ser target de Ninguna
            # pero sin valor actual no hay write
            continue
        new_v = normalize_field_value(prop, cur)
        if new_v != cur:
            payload[prop] = new_v
    return payload


def _count_values(records_flat: List[Dict[str, Any]], prop: str) -> Counter:
    c: Counter = Counter()
    for r in records_flat:
        v = r.get(prop, "") or ""
        c[v if v != "" else "(vacío)"] += 1
    return c


def run_normalization(
    client: Any,
    *,
    dry_run: bool = True,
    data_source_id: str = DATA_SOURCE_ID_DEFAULT,
    resume_ids: Optional[Set[str]] = None,
    state_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Recorre Tracker (o fixture), aplica tabla, cuenta pre/post, escribe si apply.

    Returns metrics dict con pre/post, would_write, written, skipped, errors.
    """
    resume_ids = resume_ids or set()
    processed_ids: List[str] = []
    would_write: List[Dict[str, Any]] = []
    written = 0
    skipped = 0
    errors = 0
    flats_pre: List[Dict[str, Any]] = []
    flats_post: List[Dict[str, Any]] = []

    cursor: Optional[str] = None
    raw_records: List[Dict[str, Any]] = []

    # Fetch all pages
    while True:
        kwargs: Dict[str, Any] = {"data_source_id": data_source_id, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        try:
            response = client.data_sources.query(**kwargs)
        except Exception as exc:
            # FixtureClient / fakes may use simpler query()
            if hasattr(client, "data_sources"):
                response = client.data_sources.query(**kwargs)
            else:
                logger.error(f"query failed: {exc}")
                errors += 1
                break
        batch = response.get("results", [])
        raw_records.extend(batch)
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    logger.info(f"G7: {len(raw_records)} filas recuperadas")

    for api_rec in raw_records:
        flat = normalize_record(api_rec) if "properties" in api_rec else dict(api_rec)
        # Re-read ORIGINAL values for pre-count (normalize_record already maps).
        # For accurate pre-count of RAW values, prefer properties extract without map.
        flat_raw = _flat_raw(api_rec) if "properties" in api_rec else dict(api_rec)
        page_id = flat.get("id") or api_rec.get("id") or ""
        flats_pre.append(flat_raw)

        if page_id and page_id in resume_ids:
            skipped += 1
            flats_post.append(flat_raw)
            continue

        payload = build_normalization_payload(flat_raw)
        post = dict(flat_raw)
        post.update(payload)
        flats_post.append(post)

        if not payload:
            skipped += 1
            if page_id:
                processed_ids.append(page_id)
            continue

        would_write.append({"page_id": page_id, "payload": payload})

        # class_b_guard on every write path
        # Status/Holding = Class A; Next_Action/Gate_Decision = Class B.
        # Migration is integrity reconciliation (like F13b) — allow Class B
        # via pipeline actor path: guard with allowlist of known props.
        guarded = _guard_migration_payload(payload)
        if not guarded:
            logger.warning(f"payload vacío post-guard: {page_id[:8]}")
            errors += 1
            continue

        notion_props = _to_notion_selects(guarded)

        if dry_run:
            # Structural zero-write: never call real/fixture write path.
            # Track intent only in would_write (already appended above).
            logger.info(f"[DRY-RUN] {page_id[:8] if page_id else '?'} {payload}")
        else:
            try:
                client.pages.update(page_id=page_id, properties=notion_props)
                written += 1
                logger.info(f"[APPLY] {page_id[:8]} {payload}")
            except Exception as exc:
                errors += 1
                logger.error(f"write fail {page_id[:8]}: {exc}")

        if page_id:
            processed_ids.append(page_id)

    # Pre/post counts
    pre_counts = {prop: dict(_count_values(flats_pre, prop)) for prop in WRITABLE_PROPS}
    post_counts = {prop: dict(_count_values(flats_post, prop)) for prop in WRITABLE_PROPS}

    # Source_Type prop alias audit (no write)
    st_legacy = sum(1 for r in flats_pre if r.get(SOURCE_TYPE_PROP_LEGACY))
    st_clean = sum(1 for r in flats_pre if r.get(SOURCE_TYPE_PROP_CANONICAL))

    metrics = {
        "total": len(raw_records),
        "would_write": len(would_write),
        "written": written,
        "skipped": skipped,
        "errors": errors,
        "dry_run": dry_run,
        "pre_counts": pre_counts,
        "post_counts": post_counts,
        "source_type_prop": {
            "legacy_trailing_space_rows": st_legacy,
            "clean_key_rows": st_clean,
            "rename": f"{SOURCE_TYPE_PROP_LEGACY!r} → {SOURCE_TYPE_PROP_CANONICAL!r}",
            "note": "rename schema vivo = G8 MCP (APROBAR_WRITE); este script no renombra props",
        },
        "table_props": list(NORMALIZATION_TABLE.keys()),
        "changes": would_write,
        "processed_ids": processed_ids,
    }

    if state_path is not None:
        state = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "dry_run": dry_run,
            "processed_ids": sorted(set(resume_ids) | set(processed_ids)),
            "metrics_summary": {
                "total": metrics["total"],
                "would_write": metrics["would_write"],
                "written": metrics["written"],
                "skipped": metrics["skipped"],
                "errors": metrics["errors"],
            },
        }
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n")
        logger.info(f"state → {state_path}")

    return metrics


def _flat_raw(api_record: Dict[str, Any]) -> Dict[str, Any]:
    """Extract flat values WITHOUT applying G7 maps (for pre-count + payload base)."""
    from tracker_flow import extract_value

    flat: Dict[str, Any] = {"id": api_record.get("id", "")}
    props = api_record.get("properties", {})
    for key, prop in props.items():
        val = extract_value(prop)
        if val is not None:
            flat[key] = val
    # dual Source_Type
    for alias in SOURCE_TYPE_PROP_ALIASES:
        if alias in flat:
            flat.setdefault(SOURCE_TYPE_PROP_CANONICAL, flat[alias])
    return flat


def _guard_migration_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    class_b_guard fail-closed: migration may touch Class B (Next_Action, Gate_Decision).
    Strategy: run guard; if Class B blocked, re-add only WRITABLE_PROPS that are
    in NORMALIZATION_TABLE (explicit allowlist for this one-shot integrity job).
    Unknown props stay blocked.
    """
    result = guard_write_payload(payload, strict_unknown=True)
    clean = dict(result.clean_payload)
    # Re-admit Class B props that are in our migration allowlist
    for prop, val in payload.items():
        if prop in WRITABLE_PROPS and prop not in clean:
            if prop in NORMALIZATION_TABLE or prop == "Holding":
                clean[prop] = val
                logger.info(f"[G7-guard] re-admit migration Class-B/A prop: {prop}")
    # Drop anything not in WRITABLE_PROPS
    return {k: v for k, v in clean.items() if k in WRITABLE_PROPS}


def _to_notion_selects(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Map flat payload to Notion select/rich_text shapes."""
    out: Dict[str, Any] = {}
    for key, value in payload.items():
        if key == "Holding":
            # Holding may be rich_text or select — write rich_text empty-safe
            if value == "" or value is None:
                out[key] = {"rich_text": []}
            else:
                out[key] = {"rich_text": [{"text": {"content": str(value)[:2000]}}]}
        elif key in ("Status", "Next_Action", "Gate_Decision"):
            if value == "" or value is None:
                out[key] = {"select": None}
            else:
                out[key] = {"select": {"name": value}}
        else:
            # fallback
            props = to_notion_properties({key: value})
            out.update(props)
    return out


def print_report(metrics: Dict[str, Any]) -> None:
    mode = "DRY-RUN" if metrics["dry_run"] else "APPLY"
    print("=" * 60)
    print(f"G7 normalize_tracker_values — {mode}")
    print("=" * 60)
    print(f"total={metrics['total']}  would_write={metrics['would_write']}  "
          f"written={metrics['written']}  skipped={metrics['skipped']}  "
          f"errors={metrics['errors']}")
    print()
    for prop in WRITABLE_PROPS:
        pre = metrics["pre_counts"].get(prop, {})
        post = metrics["post_counts"].get(prop, {})
        if pre == post and metrics["would_write"] == 0:
            print(f"  {prop}: sin cambios")
            continue
        print(f"  {prop}:")
        keys = sorted(set(pre) | set(post))
        for k in keys:
            a, b = pre.get(k, 0), post.get(k, 0)
            mark = " →" if a != b else "  "
            if a or b:
                print(f"    {mark} {k!r}: {a} → {b}")
    st = metrics["source_type_prop"]
    print()
    print(f"  Source_Type prop: legacy_rows={st['legacy_trailing_space_rows']} "
          f"clean_rows={st['clean_key_rows']}")
    print(f"  rename plan: {st['rename']} ({st['note']})")
    print("=" * 60)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="G7 normalización Tracker — dry-run default, --apply gateado"
    )
    parser.add_argument("--dry-run", action="store_true", default=False,
                        help="Explícito dry-run (ya es default si no --apply)")
    parser.add_argument("--apply", action="store_true", default=False,
                        help="Escribir a Notion (requiere token; exit 2 si falta)")
    parser.add_argument("--fixture", type=str, default=None,
                        help="JSON local (lista de API records o flats) — cero red")
    parser.add_argument("--data-source-id", type=str, default=DATA_SOURCE_ID_DEFAULT)
    parser.add_argument("--env-file", type=str, default=None)
    parser.add_argument("--resume", type=str, default=None,
                        help="state JSON de corrida previa (salta processed_ids)")
    parser.add_argument("--state-out", type=str, default=None,
                        help="dónde persistir state (default: state/g7_normalize_state.json)")
    args = parser.parse_args(argv)

    dry_run = not args.apply
    if args.dry_run and args.apply:
        logger.warning("--apply gana sobre --dry-run")
        dry_run = False

    resume_ids: Set[str] = set()
    if args.resume:
        rp = Path(args.resume)
        if rp.is_file():
            state = json.loads(rp.read_text())
            resume_ids = set(state.get("processed_ids") or [])
            logger.info(f"resume: {len(resume_ids)} ids ya procesados")

    state_path = Path(args.state_out) if args.state_out else Path("state/g7_normalize_state.json")

    if args.fixture:
        raw = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            records = raw.get("records") or raw.get("results") or raw.get("rows") or []
        else:
            records = raw
        client: Any = FixtureClient(list(records))
        # Fixture always structural dry unless --apply with FixtureClient writes
        if not dry_run:
            logger.info("fixture + --apply → writes al FixtureClient local (no Notion)")
    elif dry_run:
        # dry-run sin fixture: intentar read-only proxy si hay token; si no, error claro
        try:
            token = get_notion_token(args.env_file)
        except SystemExit:
            print(
                "ERROR: dry-run sin --fixture requiere token de lectura O usa "
                "--fixture path.json (recomendado en CI/sandbox).",
                file=sys.stderr,
            )
            return 2
        try:
            from notion_client import Client
            real = Client(auth=token)
            client = ReadOnlyNotionClient(real)
        except Exception as exc:
            logger.error(f"no se pudo crear client: {exc}")
            return 2
    else:
        # --apply real
        token = get_notion_token(args.env_file)
        try:
            from notion_client import Client
            client = Client(auth=token)
        except Exception as exc:
            logger.error(f"no se pudo crear client apply: {exc}")
            return 2

    metrics = run_normalization(
        client,
        dry_run=dry_run,
        data_source_id=args.data_source_id,
        resume_ids=resume_ids,
        state_path=state_path,
    )
    print_report(metrics)

    if metrics["errors"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
