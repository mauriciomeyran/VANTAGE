"""
reset_fetch_bug.py

Descongela las filas del VANTAGE Tracker que quedaron mal marcadas por el bug
de Fetch faltante (Bug Tracker: 3aa938be-fc42-818b-a4b9-f66c144ef50d).

Filtro estricto -- SOLO resetea filas donde las 4 condiciones se cumplen a la vez:
  - Fetch está vacío           (nunca se escribió -> huella del bug)
  - Gate_Decision == BLOCKED   (consecuencia directa del Fetch vacío)
  - Next_Action == Archivar    (lo que el bug terminó disparando)
  - Status == Target           (para no tocar Expirada/Contratado/Rechazado,
                                 que son estados legítimos y no deben reabrirse)

Si una fila ya tiene Fetch poblado (Accesible o Bloqueado), NO se toca --
esa pudo ser una decisión real del sistema o tuya, no un efecto del bug.

Uso:
  python3 reset_fetch_bug.py                 -> DRY RUN (solo lista, no escribe nada)
  python3 reset_fetch_bug.py --execute        -> ejecuta el reset real en Notion

Requiere layer_1.env con NOTION_TOKEN, igual que layer_1_run.py.
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from notion_utils import Client

DATA_SOURCE_ID = "442938be-fc42-828f-b72e-076818d65a5b"  # VANTAGE Tracker


def txt(prop):
    if not prop:
        return ""
    t = prop.get("type")
    if t == "rich_text" and prop.get("rich_text"):
        return prop["rich_text"][0]["plain_text"]
    if t == "select" and prop.get("select"):
        return prop["select"]["name"]
    if t == "title" and prop.get("title"):
        return prop["title"][0]["plain_text"]
    return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true",
                         help="Ejecuta el reset real. Sin esta bandera, solo hace dry run.")
    args = parser.parse_args()

    load_dotenv(dotenv_path=os.path.abspath("layer_1.env"), override=True)
    client = Client(auth=os.environ["NOTION_TOKEN"])

    print("Buscando filas corrompidas por el bug de Fetch faltante...")
    print("=" * 70)

    items = client.data_sources.query(data_source_id=DATA_SOURCE_ID)["results"]

    candidates = []
    for item in items:
        props = item["properties"]
        fetch = txt(props.get("Fetch"))
        gate = txt(props.get("Gate_Decision"))
        next_action = txt(props.get("Next_Action"))
        status = txt(props.get("Status"))

        if fetch == "" and gate == "BLOCKED" and next_action == "Archivar" and status == "Target":
            rol = txt(props.get("Rol")) or "Sin rol"
            marca = txt(props.get("Marca")) or "Sin marca"
            candidates.append((item["id"], marca, rol))

    print(f"Filas identificadas para reset: {len(candidates)}")
    print()
    for page_id, marca, rol in candidates:
        print(f"  [{page_id[:8]}] {marca} - {rol[:50]}")

    print()
    print("=" * 70)

    if not args.execute:
        print(f"[DRY-RUN] {len(candidates)} filas se resetearían (Next_Action y Gate_Decision -> vacío).")
        print("Corre de nuevo con --execute para aplicar el reset real.")
        return

    print(f"[EXECUTE] Reseteando {len(candidates)} filas...")
    ok, fail = 0, 0
    for page_id, marca, rol in candidates:
        try:
            client.pages.update(
                page_id=page_id,
                properties={
                    "Next_Action": {"rich_text": []},
                    "Gate_Decision": {"select": None},
                }
            )
            ok += 1
        except Exception as e:
            fail += 1
            print(f"WARNING: fallo en [{page_id[:8]}] {marca} - {rol[:40]}: {e}")

    print()
    print(f"OK: {ok} filas reseteadas, {fail} fallos.")
    print("Siguiente paso: correr layer_1_run.py (ya parcheado) para re-evaluarlas.")


if __name__ == "__main__":
    main()
