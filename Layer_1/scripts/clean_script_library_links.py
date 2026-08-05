#!/usr/bin/env python3
"""
VANTAGE — Script Library Link-Corruption Cleaner
Path: Layer_1/scripts/clean_script_library_links.py

Limpia la corrupción de auto-link de Notion (`http://` insertado en medio de
nombres de archivo tipo `word.py` -> `word_http://py`) en las propiedades
`Ruta` y `Script` de la base SCRIPT LIBRARY. Dry-run por default; --apply
para escribir de verdad. Verificación por relectura tras cada escritura.
"""

import os
import sys
import argparse
from pathlib import Path
import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR.parent / "config" / "layer_1.env"
SCRIPT_LIBRARY_DATA_SOURCE_ID = "ea914544-338f-485e-ac1b-7f137a5c9cee"


def load_env(env_path: Path) -> dict:
    env_vars = {}
    if not env_path.exists():
        print(f"[-] Error: no se encontró {env_path}", file=sys.stderr)
        sys.exit(1)
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars


def headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2025-09-03",
        "Content-Type": "application/json",
    }


def query_all_rows(client: httpx.Client, hdrs: dict) -> list:
    """Pagina sobre el data source completo."""
    rows = []
    payload = {"page_size": 100}
    url = f"https://api.notion.com/v1/data_sources/{SCRIPT_LIBRARY_DATA_SOURCE_ID}/query"
    while True:
        resp = client.post(url, headers=hdrs, json=payload)
        if resp.status_code != 200:
            print(f"[-] Error query: HTTP {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
            sys.exit(1)
        data = resp.json()
        rows.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data.get("next_cursor")
    return rows


def extract_plain_text(prop: dict) -> str:
    """Extrae texto plano de una propiedad title o rich_text."""
    kind = prop.get("type")
    parts = prop.get(kind, [])
    return "".join(p.get("plain_text", "") for p in parts)


def has_link_corruption(prop: dict) -> bool:
    """Detecta si algún fragmento del rich_text trae un link Markdown
    auto-insertado por Notion (ej. 'word.py' -> 'word_[py](http://py)').

    El auto-link de Notion no deja la substring "http://" en el plain_text
    del fragmento -- la URL vive en la anotación de link del propio
    fragmento (text.link.url) y/o en el campo href a nivel de fragmento.
    Por eso la detección basada solo en plain_text nunca la encuentra.
    """
    kind = prop.get("type")
    parts = prop.get(kind, [])
    for p in parts:
        link = p.get("text", {}).get("link")
        if link and link.get("url", "").startswith("http"):
            return True
        # algunos payloads exponen el link también en el nivel del fragmento
        if p.get("href"):
            return True
    return False


def build_clean_rich_text(clean_value: str) -> list:
    return [{"type": "text", "text": {"content": clean_value}}]


def main():
    parser = argparse.ArgumentParser(description="Limpia corrupción http:// en SCRIPT LIBRARY.")
    parser.add_argument("--apply", action="store_true", help="Escribe de verdad. Sin esto, es dry-run.")
    args = parser.parse_args()

    env = load_env(ENV_PATH)
    token = env.get("NOTION_TOKEN")
    if not token:
        print("[-] NOTION_TOKEN no definido", file=sys.stderr)
        sys.exit(1)

    hdrs = headers(token)

    with httpx.Client(timeout=20.0) as client:
        rows = query_all_rows(client, hdrs)
        print(f"[*] {len(rows)} filas encontradas en SCRIPT LIBRARY")
        print("-" * 70)

        candidates = []
        for row in rows:
            page_id = row["id"]
            props = row.get("properties", {})

            script_prop = props.get("Script")
            ruta_prop = props.get("Ruta")

            script_val = extract_plain_text(script_prop) if script_prop else ""
            ruta_val = extract_plain_text(ruta_prop) if ruta_prop else ""

            needs_fix = (
                "http://" in script_val
                or "http://" in ruta_val
                or (has_link_corruption(script_prop) if script_prop else False)
                or (has_link_corruption(ruta_prop) if ruta_prop else False)
            )
            if not needs_fix:
                continue

            clean_script = script_val.replace("http://", "")
            clean_ruta = ruta_val.replace("http://", "")
            candidates.append((page_id, script_val, clean_script, ruta_val, clean_ruta,
                                script_prop["type"], ruta_prop["type"] if ruta_prop else None))

        print(f"[*] {len(candidates)} filas con corrupción detectada")
        print("-" * 70)
        for page_id, s_old, s_new, r_old, r_new, s_type, r_type in candidates:
            if s_old != s_new:
                print(f"  {s_old!r} -> {s_new!r}")
            else:
                print(f"  {s_old!r} (link-annotation corrupta, texto visible sin cambio)")
            if r_old:
                if r_old != r_new:
                    print(f"    Ruta: {r_old!r} -> {r_new!r}")
                else:
                    print(f"    Ruta: {r_old!r} (link-annotation corrupta, texto visible sin cambio)")

        if not candidates:
            print("[+] Nada que limpiar.")
            return

        if not args.apply:
            print("-" * 70)
            print("[DRY RUN] Ninguna escritura realizada. Correr con --apply para escribir de verdad.")
            return

        print("-" * 70)
        print("[*] Escribiendo correcciones...")
        fail_count = 0
        for page_id, s_old, s_new, r_old, r_new, s_type, r_type in candidates:
            props_payload = {}
            if s_type == "title":
                props_payload["Script"] = {"title": build_clean_rich_text(s_new)}
            else:
                props_payload["Script"] = {"rich_text": build_clean_rich_text(s_new)}
            if r_old:
                if r_type == "title":
                    props_payload["Ruta"] = {"title": build_clean_rich_text(r_new)}
                else:
                    props_payload["Ruta"] = {"rich_text": build_clean_rich_text(r_new)}

            patch_url = f"https://api.notion.com/v1/pages/{page_id}"
            patch_headers = dict(hdrs)
            patch_headers["Notion-Version"] = "2022-06-28"  # /v1/pages usa esta versión
            resp = client.patch(patch_url, headers=patch_headers, json={"properties": props_payload})
            if resp.status_code != 200:
                print(f"  [-] FAIL {s_old!r}: HTTP {resp.status_code}: {resp.text[:150]}")
                fail_count += 1
                continue

            # Verificación por relectura: texto correcto Y sin link-annotation residual
            verify = client.get(patch_url, headers=patch_headers)
            if verify.status_code == 200:
                vprops = verify.json().get("properties", {})
                vscript_prop = vprops.get("Script", {})
                vscript = extract_plain_text(vscript_prop)
                still_linked = has_link_corruption(vscript_prop)
                if vscript == s_new and not still_linked:
                    print(f"  [+] PASS {s_new!r}")
                elif still_linked:
                    print(f"  [-] FAIL relectura {s_new!r} (link-annotation persiste tras el patch)")
                    fail_count += 1
                else:
                    print(f"  [-] FAIL relectura {s_new!r} (leído: {vscript!r})")
                    fail_count += 1
            else:
                print(f"  [-] FAIL verificación {s_new!r}: HTTP {verify.status_code}")
                fail_count += 1

        print("-" * 70)
        print(f"[VEREDICTO] {len(candidates) - fail_count}/{len(candidates)} corregidos correctamente.")
        if fail_count:
            sys.exit(1)


if __name__ == "__main__":
    main()
