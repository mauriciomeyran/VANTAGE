#!/usr/bin/env python3
"""
vsync_doc.py — VANTAGE v8.5.4 (LAYER 4)
- BASE_DIR = .../ACTIVE (version-agnostic)
- Usa .venv de Layer_1
- Fetch con httpx (fix NoneType)
- Incluye Cheat Sheet
- FIX: direction local/auto ahora funcional (push_local_to_notion conectado)
- FIX: auto_commit() movido dentro de main() y llamado al finalizar
- FIX: bloques code > 2000 chars truncados en chunks de párrafo (Notion API limit)
"""

import sys, os, argparse, time
from pathlib import Path
from datetime import datetime, timezone

# ── Paths L4 → L1 ────────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve()
_PROJECT = _SCRIPT_DIR.parents[2]  # VANTAGE
_L1 = _PROJECT / "Layer_1"

# usa venv de L1
for p in (_L1 / ".venv" / "lib").glob("python3*/site-packages"):
    sys.path.insert(0, str(p)); break

# carga env de L1
_ENV = _L1 / "config" / "layer_1.env"
if _ENV.exists():
    for line in _ENV.read_text().splitlines():
        line=line.strip()
        if line and not line.startswith("#") and "=" in line:
            k,_,v = line.partition("="); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

TOKEN = os.environ.get("NOTION_API_KEY") or os.environ.get("NOTION_TOKEN")
if not TOKEN: print("NOTION_TOKEN no encontrado"); sys.exit(1)

from notion_client import Client
import httpx

notion = Client(auth=TOKEN, timeout_ms=60000)
HTTP = httpx.Client(timeout=60.0)
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Notion-Version": "2025-09-03"}

BASE_DIR = _PROJECT / "Documentación" / "ACTIVE"

DOCS = {
    "kernel":        {"notion_id": "377938be-fc42-805e-a408-c9ae518d4fe7", "local_file": BASE_DIR / "Kernel.md", "label": "TECHNICAL KERNEL"},
    "system_prompt": {"notion_id": "37b938be-fc42-8001-9b9b-fcf81130d274", "local_file": BASE_DIR / "System Prompt.md", "label": "SYSTEM PROMPT"},
    "career_canon":  {"notion_id": "377938be-fc42-8089-93f2-f52dbd2dec6c", "local_file": BASE_DIR / "Career Canon.md", "label": "CAREER CANON"},
    "manual":        {"notion_id": "372938be-fc42-8050-9a67-e40857d7806e", "local_file": BASE_DIR / "Manual.md", "label": "MANUAL DE USUARIO"},
    "aliases":       {"notion_id": "37c938be-fc42-80d4-b9ae-f5969830331b", "local_file": BASE_DIR / "Aliases.md", "label": "ALIASES"},
    "change_log":    {"notion_id": "390938be-fc42-80e7-b429-d7d730339353", "local_file": BASE_DIR / "Change Log.md", "label": "CHANGE LOG"},
}

NOTION_TEXT_LIMIT = 1990  # margen de seguridad bajo el límite de 2000

def _rich_text(rt):
    if not rt: return ""
    return "".join(r.get("plain_text","") for r in rt)

def _block_to_md(block):
    bt = block.get("type",""); b = block.get(bt) or {}
    rt = _rich_text(b.get("rich_text") or [])
    if bt == "paragraph": return rt + "\n"
    if bt == "heading_1": return f"# {rt}\n"
    if bt == "heading_2": return f"## {rt}\n"
    if bt == "heading_3": return f"### {rt}\n"
    if bt == "bulleted_list_item": return f"- {rt}\n"
    if bt == "numbered_list_item": return f"1. {rt}\n"
    if bt == "to_do": return f"- [{'x' if b.get('checked') else ' '}] {rt}\n"
    if bt == "code": return f"```{b.get('language','')}\n{rt}\n```\n"
    if bt == "quote": return f"> {rt}\n"
    if bt == "divider": return "---\n"
    if bt == "callout":
        icon = b.get("icon") or {}
        emoji = icon.get("emoji","") if isinstance(icon, dict) else ""
        return f"> {emoji+' ' if emoji else ''}{rt}\n"

    if bt == "table":
        return ""

    if bt == "table_row":
        cells = ["".join(t.get("plain_text","") for t in c) for c in b.get("cells", [])]
        row = "| " + " | ".join(cells) + " |\n"

        parent = block.get("_parent_table", {})
        if (
            parent.get("has_column_header")
            and not parent.get("_header_written")
        ):
            parent["_header_written"] = True
            sep = "| " + " | ".join(["---"] * len(cells)) + " |\n"
            return row + sep

        return row
    if bt == "toggle": return f"**{rt}**\n"
    return ""

def safe_list(block_id, cursor=None):
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    params = {"page_size": 100}
    if cursor: params["start_cursor"] = cursor
    for i in range(3):
        try:
            r = HTTP.get(url, headers=HEADERS, params=params)
            if r.status_code == 200: return r.json()
        except Exception as e:
            print(f"       {e}")
        time.sleep(1.5*(i+1))
    return None

def _export_children(block_id, lines, parent_table=None, depth=0, seen=None):
    if seen is None:
        seen = set()
    if depth > 15 or block_id in seen:
        print(f"       ⚠️ skip depth={depth} block={block_id[:8]} (limit/loop guard)")
        return
    seen.add(block_id)

    cur = None
    while True:
        data = safe_list(block_id, cur)
        if data is None:
            return

        for b in data.get("results", []):

            current_parent = parent_table

            if b.get("type") == "table":
                current_parent = dict(b.get("table", {}))
                current_parent["_header_written"] = False

            if b.get("type") == "table_row" and current_parent is not None:
                b["_parent_table"] = current_parent

            lines.append(_block_to_md(b))

            if b.get("has_children"):
                _export_children(
                    b["id"],
                    lines,
                    current_parent,
                    depth + 1,
                    seen
                )

        if not data.get("has_more"):
            break

        cur = data.get("next_cursor")


def fetch_notion_as_md(pid):
    meta = notion.pages.retrieve(pid)
    ts = datetime.fromisoformat(meta["last_edited_time"].replace("Z","+00:00"))
    title = ""
    for p in meta.get("properties",{}).values():
        if p and p.get("type") == "title":
            title = _rich_text(p.get("title",[])); break
    lines = [f"# {title}\n\n"] if title else []
    cur=None; total=0
    while True:
        data = safe_list(pid, cur)
        if data is None: return None, ts
        for b in data.get("results",[]):
            current_parent = None
            if b.get("type") == "table":
                current_parent = dict(b.get("table", {}))
                current_parent["_header_written"] = False
            lines.append(_block_to_md(b)); total+=1
            if total % 20 == 0:
                print(f"       ...{total} bloques nivel-0", end="\r")
            if b.get("has_children"):
                _export_children(b["id"], lines, current_parent)
        if not data.get("has_more"): break
        cur = data.get("next_cursor")
    print(f"     {total} bloques")
    return "".join(lines), ts

def _make_code_blocks(lang, content):
    """Divide bloques code largos en chunks de párrafo si superan el límite."""
    if len(content) <= NOTION_TEXT_LIMIT:
        return [{"object":"block","type":"code","code":{
            "language": lang or "plain text",
            "rich_text": [{"type":"text","text":{"content": content}}]
        }}]
    # Contenido demasiado largo — dividir en párrafos con fence visual
    # FIX: reservar espacio para el prefijo antes de cortar (evita overflow del límite 2000)
    blocks = []
    n_chunks_estimate = (len(content) // NOTION_TEXT_LIMIT) + 2
    prefix_max_len = len(f"[code:{lang or 'plain'}:{n_chunks_estimate}/{n_chunks_estimate}]\n")
    safe_limit = NOTION_TEXT_LIMIT - prefix_max_len
    chunks = [content[i:i+safe_limit] for i in range(0, len(content), safe_limit)]
    for idx, chunk in enumerate(chunks):
        prefix = f"[code:{lang or 'plain'}:{idx+1}/{len(chunks)}]\n" if len(chunks) > 1 else ""
        blocks.append({"object":"block","type":"paragraph","paragraph":{
            "rich_text": [{"type":"text","text":{"content": prefix + chunk}}]
        }})
    return blocks

def _make_text_block(block_type, key, content):
    """Crea un bloque de texto truncando si supera el límite."""
    return {"object":"block","type":block_type, block_type:{
        "rich_text": [{"type":"text","text":{"content": content[:NOTION_TEXT_LIMIT]}}]
    }}

def _try_parse_table(lines, i):
    """
    Detecta un bloque de tabla Markdown a partir de la línea i.
    Retorna (table_block, next_i) o (None, i) si no es tabla.
    """
    if not (lines[i].strip().startswith("|") and lines[i].strip().endswith("|")):
        return None, i
    if i + 1 >= len(lines):
        return None, i
    sep = lines[i+1].strip()
    if not (sep.startswith("|") and set(sep.replace("|","").replace(" ","").replace(":","")) <= {"-"}):
        return None, i

    def _split_row(line):
        return [c.strip() for c in line.strip().strip("|").split("|")]

    header_cells = _split_row(lines[i])
    width = len(header_cells)
    rows = [header_cells]

    j = i + 2
    while j < len(lines):
        l = lines[j].strip()
        if not (l.startswith("|") and l.endswith("|")):
            break
        rows.append(_split_row(l))
        j += 1

    table_rows = []
    for row in rows:
        cells = row[:width] + [""] * max(0, width - len(row))
        table_rows.append({
            "object": "block", "type": "table_row",
            "table_row": {"cells": [[{"type":"text","text":{"content": c[:NOTION_TEXT_LIMIT]}}] for c in cells]}
        })

    table_block = {
        "object": "block", "type": "table",
        "table": {
            "table_width": width,
            "has_column_header": True,
            "has_row_header": False,
            "children": table_rows
        }
    }
    return table_block, j

def push_local_to_notion(pid, path):
    # Eliminar bloques existentes
    cur=None
    while True:
        d = safe_list(pid, cur)
        if not d: break
        for b in d.get("results",[]):
            if b.get("archived"):
                continue
            try:
                notion.blocks.delete(b["id"])
            except Exception as e:
                print(f"       ⚠️ no se pudo borrar bloque {b['id'][:8]}: {e}")
        if not d.get("has_more"): break
        cur = d.get("next_cursor")

    lines = path.read_text(encoding="utf-8").splitlines()
    blocks=[]; i=0
    while i < len(lines):
        l = lines[i]
        table_block, next_i = _try_parse_table(lines, i)
        if table_block is not None:
            blocks.append(table_block)
            i = next_i
            continue
        if l.startswith("```"):
            lang = l[3:].strip(); i+=1; code=[]
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i]); i+=1
            blocks.extend(_make_code_blocks(lang, "\n".join(code)))
        elif l.startswith("### "):
            blocks.append(_make_text_block("heading_3", "heading_3", l[4:]))
        elif l.startswith("## "):
            blocks.append(_make_text_block("heading_2", "heading_2", l[3:]))
        elif l.startswith("# "):
            blocks.append(_make_text_block("heading_1", "heading_1", l[2:]))
        elif l.startswith("- [x] ") or l.startswith("- [X] "):
            blocks.append({"object":"block","type":"to_do","to_do":{
                "checked":True,"rich_text":[{"type":"text","text":{"content":l[6:NOTION_TEXT_LIMIT+6]}}]}})
        elif l.startswith("- [ ] "):
            blocks.append({"object":"block","type":"to_do","to_do":{
                "checked":False,"rich_text":[{"type":"text","text":{"content":l[6:NOTION_TEXT_LIMIT+6]}}]}})
        elif l.startswith("- "):
            blocks.append(_make_text_block("bulleted_list_item", "bulleted_list_item", l[2:]))
        elif l.startswith("> "):
            blocks.append(_make_text_block("quote", "quote", l[2:]))
        elif l.startswith("---"):
            blocks.append({"object":"block","type":"divider","divider":{}})
        elif l.strip():
            blocks.append(_make_text_block("paragraph", "paragraph", l))
        else:
            blocks.append({"object":"block","type":"paragraph","paragraph":{"rich_text":[]}})
        i+=1
    for j in range(0, len(blocks), 100):
        notion.blocks.children.append(block_id=pid, children=blocks[j:j+100])

def auto_commit(dry_run=False):
    """Llama a git_sync.py si hay cambios en ACTIVE."""
    import subprocess
    gs = _PROJECT / "Layer_4" / "scripts" / "git_sync.py"
    if not gs.exists():
        return
    cmd = [sys.executable, str(gs)]
    if dry_run:
        cmd.append("--dry-run")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(_PROJECT))
        if result.returncode == 0:
            print(f"  📦 {result.stdout.strip()}")
        elif "No hay cambios" in result.stdout:
            pass
        else:
            print(f"  ⚠️ git: {result.stderr.strip() or result.stdout.strip()}")
    except Exception as e:
        print(f"  ⚠️ git_sync falló: {e}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--direction", choices=["notion","local","auto"], default="auto")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--doc", choices=list(DOCS.keys()))
    args = p.parse_args()
    targets = {args.doc: DOCS[args.doc]} if args.doc else DOCS

    print(f"\nvsync_doc v8.5.4 L4 → ACTIVE  [{args.direction.upper()}]{' DRY' if args.dry_run else ''}\n")

    for k, d in targets.items():
        local = d["local_file"]

        # ── DRY RUN: solo metadata (pages.retrieve), sin fetch recursivo de bloques ──
        if args.dry_run:
            try:
                meta = notion.pages.retrieve(d["notion_id"])
            except Exception as e:
                print(f"  ✗ {d['label']:<30} [DRY] ERROR — {e}")
                continue
            ts = datetime.fromisoformat(meta["last_edited_time"].replace("Z","+00:00"))
            local_ts = datetime.fromtimestamp(local.stat().st_mtime, tz=timezone.utc) if local.exists() else None

            if args.direction == "notion":
                print(f"  · {d['label']:<30} [DRY] notion→local (sin cambios aplicados)")
            elif args.direction == "local":
                print(f"  · {d['label']:<30} [DRY] local→notion (sin cambios aplicados)")
            else:
                winner = "local→notion" if (local_ts and local_ts > ts) else "notion→local"
                print(f"  · {d['label']:<30} [DRY] {winner} (auto, sin cambios aplicados)")
            continue

        # ── RUN REAL: aquí sí se justifica el fetch completo y recursivo ──
        md, ts = fetch_notion_as_md(d["notion_id"])
        if md is None:
            print(f"  ✗ {d['label']:<30} ERROR")
            continue

        if args.direction == "notion":
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text(md, encoding="utf-8")
            print(f"  ✓ {d['label']:<30} notion→local")

        elif args.direction == "local":
            if not local.exists():
                print(f"  ✗ {d['label']:<30} ERROR — local file no existe: {local}")
                continue
            push_local_to_notion(d["notion_id"], local)
            print(f"  ✓ {d['label']:<30} local→notion")

        else:  # auto — gana el más reciente
            local_ts = datetime.fromtimestamp(local.stat().st_mtime, tz=timezone.utc) if local.exists() else None
            if local_ts and local_ts > ts:
                if not local.exists():
                    print(f"  ✗ {d['label']:<30} ERROR — local file no existe: {local}")
                    continue
                push_local_to_notion(d["notion_id"], local)
                print(f"  ✓ {d['label']:<30} local→notion (auto)")
            else:
                local.parent.mkdir(parents=True, exist_ok=True)
                local.write_text(md, encoding="utf-8")
                print(f"  ✓ {d['label']:<30} notion→local (auto)")

    if not args.dry_run:
        auto_commit(dry_run=False)

if __name__ == "__main__":
    main()
