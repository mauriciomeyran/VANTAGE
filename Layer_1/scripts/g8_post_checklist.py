#!/usr/bin/env python3
"""
g8_post_checklist.py — G8 PASO 7: checklist radiografía §3.1

Modos:
  --offline   (default) valida código post G2–G7: is_mutable unificado,
              entry points, Archive, dual Source_Type, NORMALIZATION_TABLE.
  --export p  opcional: resume conteos del snapshot post-cutover.

Exit 0 = todo PASS/documented; exit 1 = algún FAIL.
Cero Notion.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

Check = Tuple[str, str, str]  # id, verdict, detail


def check_offline() -> List[Check]:
    from tracker_flow import (
        Status,
        PROTECTED_STATUSES,
        LIVE_APPLICATION_STATUSES,
        TERMINAL_STATUSES,
        is_mutable,
        Actor,
        NORMALIZATION_TABLE,
        SOURCE_TYPE_PROP_ALIASES,
        SOURCE_TYPE_PROP_LEGACY,
        SOURCE_TYPE_PROP_CANONICAL,
        NEXT_ACTION_CANONICAL,
        DELETED_VALUE_MAPPINGS,
    )

    out: List[Check] = []

    # 1. Entry points
    active_run = ROOT / "Layer_1" / "scripts" / "layer_1_run.py"
    orch = ROOT / "Layer_1" / "scripts" / "layer_1_orchestrator.py"
    arch_run = ROOT / "Archive" / "Legacy_Scripts" / "layer_1_run.py"
    out.append((
        "entry.layer_1_run_absent",
        "PASS" if not active_run.exists() else "FAIL",
        f"active exists={active_run.exists()}",
    ))
    out.append((
        "entry.orchestrator_present",
        "PASS" if orch.exists() else "FAIL",
        str(orch.relative_to(ROOT)),
    ))
    out.append((
        "entry.layer_1_run_archived",
        "PASS" if arch_run.exists() else "FAIL",
        str(arch_run.relative_to(ROOT)),
    ))

    pipe = (ROOT / "Layer_1" / "layer_1_pipeline.sh").read_text(encoding="utf-8")
    out.append((
        "entry.pipeline_points_orch",
        "PASS" if "layer_1_orchestrator.py" in pipe else "FAIL",
        "layer_1_pipeline.sh default",
    ))
    out.append((
        "entry.batch_retired",
        "PASS" if "RETIRADO" in pipe and "batch_operations" in pipe else "FAIL",
        "batch) case",
    ))

    # 2. PROTECTED = LIVE ∪ TERMINAL (única fuente)
    expected_prot = LIVE_APPLICATION_STATUSES | TERMINAL_STATUSES
    out.append((
        "mutable.protected_eq_live_union_terminal",
        "PASS" if PROTECTED_STATUSES == expected_prot else "FAIL",
        f"prot={sorted(s.value for s in PROTECTED_STATUSES)}",
    ))

    # 3. Matriz §3.1 — cada Status canónico
    bot = {
        "last_edited_by_id": "integration-id-feed-processor",
        "last_edited_time": "2020-01-01T00:00:00.000Z",
        "id": "checklist",
    }
    # LIVE + TERMINAL must be immutable for PIPELINE
    for st in sorted(PROTECTED_STATUSES, key=lambda s: s.value):
        m = is_mutable({**bot, "Status": st.value}, Actor.PIPELINE)
        out.append((
            f"matrix.{st.value}.pipeline_blocked",
            "PASS" if m is False else "FAIL",
            f"is_mutable={m}",
        ))
    # Operativos abiertos mutables
    for st in (Status.OBJETIVO, Status.EXPLORATORIO, Status.POR_REVISAR):
        m = is_mutable({**bot, "Status": st.value}, Actor.PIPELINE)
        out.append((
            f"matrix.{st.value}.pipeline_open",
            "PASS" if m is True else "FAIL",
            f"is_mutable={m}",
        ))

    # Contratado absolute
    m = is_mutable({**bot, "Status": Status.CONTRATADO.value}, Actor.PIPELINE)
    out.append((
        "matrix.Contratado.absolute",
        "PASS" if m is False else "FAIL",
        "PROTECTED_ABSOLUTE",
    ))

    # 4. G7 table essentials
    na = NORMALIZATION_TABLE.get("Next_Action", {})
    out.append((
        "g7.na.follow_up",
        "PASS" if na.get("Follow-up") == "Seguimiento" else "FAIL",
        str(na.get("Follow-up")),
    ))
    out.append((
        "g7.na.interview",
        "PASS" if na.get("Interview prep") == "Preparación Entrevista" else "FAIL",
        str(na.get("Interview prep")),
    ))
    out.append((
        "g7.na.recheck",
        "PASS" if na.get("Re-check") == "Revisión" else "FAIL",
        str(na.get("Re-check")),
    ))
    out.append((
        "g7.gate.expirada",
        "PASS" if NORMALIZATION_TABLE.get("Gate_Decision", {}).get("EXPIRADA") == "EXPIRED" else "FAIL",
        "",
    ))
    out.append((
        "g7.status.target",
        "PASS" if NORMALIZATION_TABLE.get("Status", {}).get("Target") == "Objetivo" else "FAIL",
        "",
    ))
    out.append((
        "g7.holding.investigar",
        "PASS" if NORMALIZATION_TABLE.get("Holding", {}).get("Investigar") == "" else "FAIL",
        "",
    ))

    out.append((
        "g7.na.canonical_count",
        "PASS" if len(NEXT_ACTION_CANONICAL) == 9 else "FAIL",
        f"n={len(NEXT_ACTION_CANONICAL)}",
    ))

    # 5. Source_Type dual
    out.append((
        "q1.source_type_dual",
        "PASS" if SOURCE_TYPE_PROP_LEGACY in SOURCE_TYPE_PROP_ALIASES
        and SOURCE_TYPE_PROP_CANONICAL in SOURCE_TYPE_PROP_ALIASES else "FAIL",
        str(SOURCE_TYPE_PROP_ALIASES),
    ))

    # 6. DELETED mappings
    st_del = DELETED_VALUE_MAPPINGS.get("Status", {})
    out.append((
        "deleted.status.archivar",
        "PASS" if st_del.get("Archivar") == "Retirado" else "FAIL",
        str(st_del),
    ))

    # 7. Writers emit ES
    from layer_1_orchestrator import get_application_next_action
    na_post = get_application_next_action(Status.POSTULADO.value)
    out.append((
        "writers.next_action_es",
        "PASS" if na_post == "Seguimiento" else "FAIL",
        na_post,
    ))

    # 8. Docs present
    for rel in (
        "Layer_1/docs/G7_NORMALIZATION_TABLE.md",
        "Layer_1/docs/G8_DEPLOYMENT_PLAN.md",
        "Layer_1/scripts/normalize_tracker_values.py",
        "Layer_1/scripts/export_tracker_snapshot.py",
        "Layer_1/scripts/rollback_schema_migration.py",
    ):
        p = ROOT / rel
        out.append((f"artifact.{rel}", "PASS" if p.exists() else "FAIL", rel))

    # 9. Archived writers
    for rel in (
        "Archive/Legacy_Scripts/batch_operations.py",
        "Archive/Legacy_Scripts/consolidate_duplicates.py",
        "Archive/Dashboard/layer_1_run_dash.py",
    ):
        p = ROOT / rel
        out.append((f"archive.{Path(rel).name}", "PASS" if p.exists() else "FAIL", rel))

    return out


def check_export(path: Path) -> List[Check]:
    out: List[Check] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data.get("records") if isinstance(data, dict) else data
    if not isinstance(records, list):
        return [("export.shape", "FAIL", "no records list")]
    out.append(("export.n", "PASS" if len(records) >= 1 else "FAIL", f"n={len(records)}"))

    # After cutover ideal: no legacy EN Next_Action
    legacy_na = {"Follow-up", "Interview prep", "Re-check", "Ninguna"}
    legacy_status = {"Target", "Archivar"}
    found_na = found_st = 0

    def _sel(rec, key):
        props = rec.get("properties") or {}
        prop = props.get(key)
        if not isinstance(prop, dict):
            return rec.get(key) or ""
        if prop.get("select"):
            return prop["select"].get("name") or ""
        return ""

    for r in records:
        na = _sel(r, "Next_Action")
        st = _sel(r, "Status")
        if na in legacy_na:
            found_na += 1
        if st in legacy_status:
            found_st += 1
    out.append((
        "export.legacy_next_action_zero",
        "PASS" if found_na == 0 else "FAIL",
        f"legacy_na_rows={found_na}",
    ))
    out.append((
        "export.legacy_status_zero",
        "PASS" if found_st == 0 else "FAIL",
        f"legacy_status_rows={found_st}",
    ))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="G8 post checklist §3.1")
    ap.add_argument("--offline", action="store_true", default=True)
    ap.add_argument("--export", default=None, help="snapshot JSON post-cutover")
    args = ap.parse_args(argv)

    checks = check_offline()
    if args.export:
        checks.extend(check_export(Path(args.export)))

    fails = [c for c in checks if c[1] == "FAIL"]
    print("=" * 60)
    print("G8 post checklist — radiografía §3.1 / cutover")
    print("=" * 60)
    for cid, verdict, detail in checks:
        mark = "✓" if verdict == "PASS" else "✗"
        print(f"  {mark} [{verdict}] {cid}" + (f" — {detail}" if detail else ""))
    print("=" * 60)
    print(f"total={len(checks)} pass={len(checks)-len(fails)} fail={len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
