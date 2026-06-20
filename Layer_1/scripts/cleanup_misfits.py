#!/usr/bin/env python3
"""Marca como Expirada las vacantes fuera de perfil (exclusiones + fit VM)."""

import argparse
import os
import sys

from dotenv import load_dotenv
from notion_utils import Client

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from layer_1_run import get_role_class, get_vm_scope, query_all_items, txt
from profile_fit import profile_misfit_reasons, should_auto_cleanup

DS_ID = "442938befc42828fb72e076818d65a5b"


def collect_misfits(items):
    misfits = []
    for item in items:
        props = item["properties"]
        rol = txt(props.get("Rol"))
        marca = txt(props.get("Marca"))
        status = txt(props.get("Status"))
        source_type = txt(props.get("Source_Type ")) or "Vacante"
        vm_scope = txt(props.get("VM_Scope")) or get_vm_scope(rol)
        role_class = txt(props.get("Role_Class")) or get_role_class(rol)
        score = props.get("Score", {}).get("number")
        reasons = profile_misfit_reasons(
            rol=rol,
            marca=marca,
            vm_scope=vm_scope,
            role_class=role_class,
            source_type=source_type,
            score=score,
        )
        if should_auto_cleanup(status, reasons):
            misfits.append({
                "id": item["id"],
                "marca": marca,
                "rol": rol,
                "status": status,
                "score": score,
                "reasons": reasons,
            })
    return misfits


def run_cleanup(client, misfits, dry_run=False):
    updated = 0
    for row in misfits:
        print(
            f"[{row['id'][:8]}] {row['status']:10} sc={row['score']} | "
            f"{row['marca'][:25]} | {row['rol'][:45]}"
        )
        print(f"   -> {', '.join(row['reasons'])}")
        if dry_run:
            continue
        try:
            client.pages.update(
                page_id=row["id"],
                properties={
                    "Status": {"select": {"name": "Expirada"}},
                    "Gate_Decision": {"select": {"name": "BLOCKED"}},
                    "Next_Action": {"rich_text": [{"text": {"content": "Archivar"}}]},
                },
            )
            updated += 1
        except Exception as exc:
            print(f"   ERROR: {exc}")
    return updated


def main():
    parser = argparse.ArgumentParser(description="Limpia vacantes fuera de perfil VM")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()

    load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
    client = Client(auth=os.environ["NOTION_TOKEN"])

    items = query_all_items(client, DS_ID)
    misfits = collect_misfits(items)
    print(f"Encontradas {len(misfits)} vacantes fuera de perfil (de {len(items)} total)\n")

    if not misfits:
        print("Nada que limpiar.")
        return

    if args.dry_run:
        run_cleanup(client, misfits, dry_run=True)
        return

    if not args.yes:
        confirm = input("Marcar como Expirada? (y/N): ").lower().strip()
        if confirm != "y":
            print("Cancelado.")
            return

    updated = run_cleanup(client, misfits, dry_run=False)
    print(f"\nOK {updated} vacantes marcadas Expirada / BLOCKED / Archivar")


if __name__ == "__main__":
    main()
