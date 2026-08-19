#!/usr/bin/env python3
"""
VANTAGE — Bulk Upload de lógica completa de skills a Notion (body)

Lee /skills/, empareja cada SKILL.md con su fila en Skill Library y
escribe el contenido completo como body de la página.

Uso:
  python bulk_upload_skill_bodies.py              # Dry Run (default)
  python bulk_upload_skill_bodies.py --write      # Escritura real
  python bulk_upload_skill_bodies.py --only vantage-cv-a --write
  python bulk_upload_skill_bodies.py --force --write

Requiere: NOTION_TOKEN en Layer_1/config/layer_1.env (o env)
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

# ─── Rutas ───────────────────────────────────────────────────
PROJECT_ROOT = Path("/Users/mauriciomeyran/Documents/03 Projects/VANTAGE")
SKILLS_PATH = PROJECT_ROOT / "skills"
ENV_PATH = PROJECT_ROOT / "Layer_1" / "config" / "layer_1.env"

NOTION_SKILL_LIBRARY_DS = "2f1938be-fc42-83c8-8972-07300201136d"
NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2025-09-03"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)


def load_token() -> str:
    token = os.environ.get("NOTION_TOKEN")
    if token:
        return token
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == "NOTION_TOKEN":
                    return v.strip().strip('"').strip("'")
    logger.error("NOTION_TOKEN no encontrado")
    sys.exit(1)


def discover_skill_dirs(skills_path: Path) -> dict:
    """Hasta 2 niveles. {skill_name: Path}"""
    discovered = {}
    for entry in skills_path.iterdir():
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        if (entry / "SKILL.md").exists():
            discovered[entry.name] = entry
            continue
        for sub in entry.iterdir():
            if not sub.is_dir() or sub.name.startswith("."):
                continue
            if (sub / "SKILL.md").exists():
                if sub.name in discovered:
                    logger.warning(f"Duplicado de nombre '{sub.name}' — se conserva la primera")
                    continue
                discovered[sub.name] = sub
    return discovered


def normalize_skill_name(raw: str) -> str:
    name = raw.strip()
    if name.endswith(".skill"):
        name = name[: -len(".skill")]
    return name


def fetch_notion_skill_library(token: str) -> dict:
    """{normalized_name: page_id} — ignora Deprecado, resuelve conflictos."""
    url = f"{NOTION_API_BASE}/data_sources/{NOTION_SKILL_LIBRARY_DS}/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    rows = []
    payload = {"page_size": 100}
    while True:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        rows.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data.get("next_cursor")

    candidates = {}
    for row in rows:
        props = row.get("properties", {})
        page_id = row.get("id", "")
        title_parts = props.get("Skill", {}).get("title", [])
        raw_name = "".join(t.get("plain_text", "") for t in title_parts).strip()
        if not raw_name:
            continue
        estado = (props.get("Estado", {}).get("select") or {}).get("name", "")
        if estado == "Deprecado":
            continue
        ruta_parts = props.get("Ruta", {}).get("rich_text", [])
        ruta = "".join(t.get("plain_text", "") for t in ruta_parts)
        created = row.get("created_time", "")
        normalized = normalize_skill_name(raw_name)
        candidates.setdefault(normalized, []).append({
            "page_id": page_id, "ruta": ruta, "created_time": created
        })

    resolved = {}
    for name, entries in candidates.items():
        if len(entries) == 1:
            resolved[name] = entries[0]["page_id"]
            continue
        new_fmt = [e for e in entries if "SKILL.md" in e["ruta"]]
        if len(new_fmt) == 1:
            resolved[name] = new_fmt[0]["page_id"]
        else:
            newest = max(entries, key=lambda e: e["created_time"])
            resolved[name] = newest["page_id"]
            logger.warning(f"Conflicto '{name}' → se eligió la más reciente")
    return resolved


def markdown_to_blocks(md: str) -> list:
    """Conversor mínimo pero suficiente: headings, párrafos, code fences, listas."""
    blocks = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Code fence
        if stripped.startswith("```"):
            lang = stripped[3:].strip() or "plain text"
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            blocks.append({
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"type": "text", "text": {"content": "\n".join(code_lines)[:2000]}}],
                    "language": lang if lang in (
                        "python", "javascript", "typescript", "bash", "json", "yaml",
                        "markdown", "plain text", "shell", "html", "css"
                    ) else "plain text"
                }
            })
            i += 1
            continue

        # Headings
        if stripped.startswith("### "):
            blocks.append({
                "object": "block", "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": stripped[4:][:2000]}}]}
            })
        elif stripped.startswith("## "):
            blocks.append({
                "object": "block", "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": stripped[3:][:2000]}}]}
            })
        elif stripped.startswith("# "):
            blocks.append({
                "object": "block", "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": stripped[2:][:2000]}}]}
            })
        # Listas
        elif stripped.startswith("- ") or stripped.startswith("* "):
            blocks.append({
                "object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": stripped[2:][:2000]}}]}
            })
        elif stripped and stripped[0].isdigit() and ". " in stripped[:4]:
            text = stripped.split(". ", 1)[-1]
            blocks.append({
                "object": "block", "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]}
            })
        # Párrafo
        elif stripped:
            # Notion limita rich_text a ~2000 chars por bloque
            for chunk_start in range(0, len(stripped), 1900):
                chunk = stripped[chunk_start:chunk_start + 1900]
                blocks.append({
                    "object": "block", "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]}
                })
        # línea vacía → separador suave (omitimos)
        i += 1

    return blocks


def clear_page_children(page_id: str, token: str) -> None:
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
    }
    url = f"{NOTION_API_BASE}/blocks/{page_id}/children"
    while True:
        resp = requests.get(url, headers=headers, params={"page_size": 100}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        children = data.get("results", [])
        if not children:
            break
        for child in children:
            del_url = f"{NOTION_API_BASE}/blocks/{child['id']}"
            requests.delete(del_url, headers=headers, timeout=15)
        if not data.get("has_more"):
            break


def append_blocks(page_id: str, blocks: list, token: str) -> None:
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    url = f"{NOTION_API_BASE}/blocks/{page_id}/children"
    # Notion acepta máximo 100 bloques por request
    for i in range(0, len(blocks), 100):
        chunk = blocks[i:i + 100]
        payload = {"children": chunk}
        resp = requests.patch(url, headers=headers, json=payload, timeout=60)
        if resp.status_code != 200:
            logger.error(f"Error append blocks: {resp.status_code} {resp.text[:300]}")
            resp.raise_for_status()


def main():
    parser = argparse.ArgumentParser(description="Bulk upload de bodies de skills a Notion")
    parser.add_argument("--write", action="store_true", help="Ejecutar escritura real")
    parser.add_argument("--force", action="store_true", help="Sobrescribir aunque ya tenga contenido")
    parser.add_argument("--only", type=str, help="Solo esta skill (nombre de carpeta)")
    args = parser.parse_args()

    token = load_token()
    discovered = discover_skill_dirs(SKILLS_PATH)
    if args.only:
        if args.only not in discovered:
            logger.error(f"Skill '{args.only}' no encontrada en disco")
            sys.exit(1)
        discovered = {args.only: discovered[args.only]}

    notion_map = fetch_notion_skill_library(token)

    matched = []
    no_match = []
    for name, path in sorted(discovered.items()):
        page_id = notion_map.get(name)
        if page_id:
            matched.append((name, path, page_id))
        else:
            no_match.append(name)

    print("=" * 60)
    print(f"[DRY RUN]" if not args.write else "[WRITE MODE]")
    print(f"Skills en disco      : {len(discovered)}")
    print(f"Match en Skill Library: {len(matched)}")
    print(f"Sin match (skip)      : {len(no_match)}")
    print("-" * 60)

    if no_match:
        print("Sin fila en Skill Library (no se tocan):")
        for n in no_match:
            print(f"  ✗ {n}")
        print("-" * 60)

    for name, path, page_id in matched:
        md_path = path / "SKILL.md"
        content = md_path.read_text(encoding="utf-8")
        print(f"  ✓ {name:<40} → {page_id}  ({len(content)} chars)")

    if not args.write:
        print("-" * 60)
        print("Ninguna escritura realizada. Usa --write para ejecutar.")
        return

    print("-" * 60)
    print("Escribiendo bodies...")
    ok, fail = 0, 0
    for name, path, page_id in matched:
        try:
            content = (path / "SKILL.md").read_text(encoding="utf-8")
            blocks = markdown_to_blocks(content)
            if not blocks:
                logger.warning(f"{name}: sin bloques generados, se salta")
                fail += 1
                continue
            clear_page_children(page_id, token)
            append_blocks(page_id, blocks, token)
            logger.info(f"OK  {name} ({len(blocks)} bloques)")
            ok += 1
        except Exception as e:
            logger.error(f"FAIL {name}: {e}")
            fail += 1

    print("-" * 60)
    print(f"Resultado: {ok} escritos, {fail} fallidos")
    print("[FIN]")


if __name__ == "__main__":
    main()
