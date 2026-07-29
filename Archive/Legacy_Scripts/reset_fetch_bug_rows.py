#!/usr/bin/env python3
"""
reset_fetch_bug_rows.py — VANTAGE

Libera de PROTECCIÓN TOTAL únicamente las filas del Tracker cuyo
Next_Action="Archivar" fue causado por el bug de Fetch vacío
(Bug Tracker: 3aa938be-fc42-818b-a4b9-f66c144ef50d), NO archivados reales.

Firma exacta del bug (las 4 condiciones deben cumplirse TODAS):
  - Status            == "Target"      (nunca se movió, no es un archivado real)
  - Next_Action       == "Archivar"    (valor puesto por el bug, no por decisión humana)
  - Gate_Decision     == "BLOCKED"     (consecuencia directa del Fetch vacío)
  - Fetch             == ""            (la causa raíz: nunca se escribió)

Cualquier fila que no calce las 4 condiciones exactas se deja intacta —
incluye explícitamente los duplicados ya confirmados (Multicont, Confidencial)
si por algún motivo compartieran esta firma, ya que esos requieren su propio
Dry Run vía la skill vantage-tidy-opportunities-tracker, no este script.

Uso:
  python3 reset_fetch_bug_rows.py                # DRY RUN — solo lista candidatos
  python3 reset_fetch_bug_rows.py --execute       # escribe de verdad, pide confirmación interactiva
"""

import os
import sys
import httpx
from dotenv import load_dotenv

VANTAGE_DATA_SOURCE_ID = "442938be-fc42-828f-b72e-076818d65a5b"
VANTAGE_NOTION_VERSION = "2025-09-03"
VANTAGE_NOTION_API_BASE = "https://api.notion.com/v1"

EXECUTE = "--execute" in sys.argv


def txt(prop):
    if not prop:
        return ""
    t = prop.get("type")
    if t == "select" and prop.get("select"):
        return prop["select"]["name"]
    if t == "rich_text" and prop.get("rich_text"):
        return prop["rich_text"][0]["plain_text"]
    if t == "title" and prop.get("title"):
        return prop["title"][0]["plain_text"]
    return ""


def query_all_items(http_client, headers):
    url = f"{VANTAGE_NOTION_API_BASE}/data_sources/{VANTAGE_DATA_SOURCE_ID}/query"
    all_results = []
    cursor = None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        resp = http_client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
        all_results.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return all_results


def matches_bug_signature(props):
    status = txt(props.get("Status"))
    next_action = txt(props.get("Next_Action"))
    gate = txt(props.get("Gate_Decision"))
    fetch = txt(props.get("Fetch"))
    return (
        status == "Target"
        and next_action == "Archivar"
        and gate == "BLOCKED"
        and fetch == ""
    )


def main():
    load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
    token = os.environ["NOTION_TOKEN"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": VANTAGE_NOTION_VERSION,
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=30) as http_client:
        items = query_all_items(http_client, headers)

        candidates = []
        for item in items:
            props = item["properties"]
            if matches_bug_signature(props):
                candidates.append({
                    "id": item["id"],
                    "rol": txt(props.get("Rol")),
                    "marca": txt(props.get("Marca")),
                })

        print("=" * 70)
        print(f"CANDIDATOS que calzan EXACTO con la firma del bug: {len(candidates)}")
        print("=" * 70)
        for c in candidates:
            print(f"  [{c['id'][:8]}] {c['marca']} | {c['rol'][:55]}")

        if not candidates:
            print("\nNada que resetear — sin candidatos en esta corrida.")
            return

        if not EXECUTE:
            print(f"\n[DRY RUN] {len(candidates)} filas quedarían con Next_Action y "
                  "Gate_Decision vacíos (sin escribir nada). Corre con --execute para aplicar.")
            return

        confirm = input(
            f"\nEscribir el reset en {len(candidates)} filas reales de Notion. "
            "Escribe APROBAR_WRITE para continuar: "
        )
        if confirm != "APROBAR_WRITE":
            print("Cancelado — no se escribió nada.")
            return

        ok, fail = 0, 0
        for c in candidates:
            try:
                resp = http_client.patch(
                    f"{VANTAGE_NOTION_API_BASE}/pages/{c['id']}",
                    headers=headers,
                    json={
                        "properties": {
                            "Next_Action": {"rich_text": []},
                            "Gate_Decision": {"select": None},
                        }
                    },
                )
                resp.raise_for_status()
                ok += 1
                print(f"  OK  [{c['id'][:8]}] {c['marca']}")
            except Exception as e:
                fail += 1
                print(f"  FAIL [{c['id'][:8]}] {c['marca']} — {e}")

        print(f"\n{'=' * 70}\nResultado: {ok} reseteadas, {fail} fallidas de {len(candidates)} totales.")
        print("Siguiente paso: correr layer_1_run.py (ya parcheado) para que FASE 2 "
              "escriba Fetch=Accesible y FASE 4 las reevalúe de verdad.")


if __name__ == "__main__":
    main()
