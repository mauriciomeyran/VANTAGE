#!/usr/bin/env python3
import os, argparse
from dotenv import load_dotenv
from notion_utils import Client

TRACKER_DS_ID = "442938be-fc42-828f-b72e-076818d65a5b"
ARCHIVO_DB_ID = "4ec34e1b528648c9afbdd57c6eb76053"
ARCHIVE_STATUSES = {"Expirada", "Rechazado", "Retirado"}

def get_val(prop):
    if not prop: return None
    t = prop.get("type")
    if t == "title":
        b = prop.get("title", [])
        return b[0]["plain_text"] if b else ""
    if t == "rich_text":
        b = prop.get("rich_text", [])
        return b[0]["plain_text"] if b else ""
    if t == "select":
        s = prop.get("select")
        return s["name"] if s else None
    if t == "number": return prop.get("number")
    if t == "url": return prop.get("url")
    if t == "checkbox": return prop.get("checkbox", False)
    return None

def pt(v): return {"title": [{"text": {"content": str(v)[:2000]}}]}
def pr(v): return {"rich_text": [{"text": {"content": str(v)[:2000]}}]}
def ps(v): return {"select": {"name": str(v)}}
def pn(v): return {"number": float(v)}
def pu(v): return {"url": str(v)}

def build_props(src):
    p = {}
    p["Rol"] = pt(get_val(src.get("Rol", {})) or "Sin titulo")
    for f in ("Marca", "Holding", "Fuente", "JD", "hash", "Notas"):
        v = get_val(src.get(f, {}))
        if v: p[f] = pr(v)
    status = get_val(src.get("Status", {}))
    if status: p["Status"] = ps(status)
    gate = get_val(src.get("Gate_Decision", {}))
    if gate: p["Gate_Decision"] = ps({"EXPIRADA": "EXPIRED"}.get(gate.upper(), gate))
    for f in ("Role_Class", "Match", "layer"):
        v = get_val(src.get(f, {}))
        if v: p[f] = ps(v)
    st = get_val(src.get("Source_Type ", {})) or get_val(src.get("Source_Type", {}))
    if st: p["Source_Type"] = ps(st)
    score = get_val(src.get("Score", {}))
    if score is not None:
        try: p["Score"] = pn(score)
        except: pass
    url = get_val(src.get("URL", {})) or get_val(src.get("userDefined:URL", {}))
    if url: p["URL"] = pu(url)
    return p

def query_all(client, ds_id):
    results, kwargs = [], {"data_source_id": ds_id}
    while True:
        resp = client.data_sources.query(**kwargs)
        results.extend(resp.get("results", []))
        if resp.get("has_more") and resp.get("next_cursor"):
            kwargs["start_cursor"] = resp["next_cursor"]
        else: break
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    dry_run = not args.yes

    load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
    client = Client(auth=os.environ["NOTION_TOKEN"])

    print("Obteniendo entradas del Tracker...")
    all_items = query_all(client, TRACKER_DS_ID)
    print(f"  Total: {len(all_items)}\n")

    to_archive = [
        item for item in all_items
        if get_val(item["properties"].get("Status", {})) in ARCHIVE_STATUSES
        and not get_val(item["properties"].get("Interview", {}))
    ]

    label = "DRY RUN -- " if dry_run else ""
    print(f"{label}Entradas a archivar: {len(to_archive)}")
    print(f"{'STATUS':<16} {'SCORE':>5}  {'MARCA':<28} {'ROL'}")
    print("-" * 85)
    for item in sorted(to_archive, key=lambda x: (
        get_val(x["properties"].get("Status", {})) or "",
        get_val(x["properties"].get("Score", {})) or 0
    )):
        p = item["properties"]
        st = get_val(p.get("Status", {})) or ""
        sc = get_val(p.get("Score", {}))
        ma = get_val(p.get("Marca", {})) or ""
        ro = get_val(p.get("Rol", {})) or ""
        print(f"{st:<16} {f'{sc:.0f}' if sc else '-':>5}  {ma[:28]:<28} {ro[:35]}")

    if dry_run:
        print(f"\nDRY RUN -- nada modificado.")
        print(f"  Quedarian en Tracker: {len(all_items) - len(to_archive)}")
        print(f"  Ejecutar: python scripts/archive_vacantes.py --yes")
        return

    print(f"\n[1/2] Creando {len(to_archive)} registros en ARCHIVO DB...")
    created_ids, create_errors = {}, []
    for item in to_archive:
        props = item["properties"]
        ro = get_val(props.get("Rol", {})) or "Sin titulo"
        ma = get_val(props.get("Marca", {})) or ""
        try:
            new_page = client.pages.create(
                parent={"database_id": ARCHIVO_DB_ID},
                properties=build_props(props),
            )
            created_ids[item["id"]] = new_page["id"]
            print(f"  ok {ma[:22]:<22} | {ro[:35]}")
        except Exception as exc:
            print(f"  ERROR {ma[:20]} | {ro[:30]}: {exc}")
            create_errors.append((item, exc))

    print(f"\n  Creados: {len(created_ids)} | Errores: {len(create_errors)}")

    print(f"\n[2/2] Papelera del Tracker...")
    trashed_ok, trash_errors = 0, []
    for item in to_archive:
        if item["id"] not in created_ids: continue
        try:
            client.pages.update(page_id=item["id"], in_trash=True)
            trashed_ok += 1
        except Exception as exc:
            print(f"  ERROR papelera {item['id'][:8]}: {exc}")
            trash_errors.append((item, exc))

    print(f"\nResultado:")
    print(f"  Creados en ARCHIVO DB : {len(created_ids)}")
    print(f"  Eliminados del Tracker: {trashed_ok}")
    print(f"  Errores creacion      : {len(create_errors)}")
    print(f"  Errores papelera      : {len(trash_errors)}")
    print(f"  Tracker activo queda  : ~{len(all_items) - trashed_ok} entradas")

if __name__ == "__main__":
    main()
