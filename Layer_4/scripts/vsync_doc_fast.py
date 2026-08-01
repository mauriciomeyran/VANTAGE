#!/usr/bin/env python3
"""
vsync_doc_fast.py — Versión optimizada para sync local→notion
Solo procesa documentos con hipervínculos nuevos
"""

import sys, os, time, re
from pathlib import Path

# Configuración de paths
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

NOTION_TEXT_LIMIT = 1990

# Copiar funciones necesarias de vsync_doc.py
def _rich_text(rt):
    if not rt: return ""
    return "".join(r.get("plain_text","") for r in rt)

def safe_list(pid, cur):
    try:
        if cur:
            return notion.blocks.children.list(block_id=pid, start_cursor=cur)
        return notion.blocks.children.list(block_id=pid)
    except Exception as e:
        print(f"        ⚠️ safe_list error: {e}")
        return None

def _text_to_rich_text(content: str) -> list:
    content = content[:NOTION_TEXT_LIMIT]
    segments = []
    pos = 0
    # Patrón de link markdown "[texto](url)"
    _MD_LINK_RE = re.compile(r"\[([^\[\]]+)\]\((https?://[^\s()]+)\)")
    for m in _MD_LINK_RE.finditer(content):
        if m.start() > pos:
            segments.append({"type": "text", "text": {"content": content[pos:m.start()]}})
        label, url = m.group(1), m.group(2)
        segments.append({"type": "text", "text": {"content": label, "link": {"url": url}}})
        pos = m.end()
    if pos < len(content):
        segments.append({"type": "text", "text": {"content": content[pos:]}})
    if not segments:
        segments = [{"type": "text", "text": {"content": ""}}]
    return segments

def _make_text_block(block_type, key, content):
    return {"object":"block","type":block_type, block_type:{
        "rich_text": _text_to_rich_text(content)
    }}

def _try_parse_table(lines, i):
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
            "table_row": {"cells": [_text_to_rich_text(c) for c in cells]}
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

def _make_code_blocks(lang, content):
    if len(content) <= NOTION_TEXT_LIMIT:
        return [{"object":"block","type":"code","code":{
            "language": lang or "plain text",
            "rich_text": [{"type":"text","text":{"content": content}}]
        }}]
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

def push_local_to_notion(pid, path):
    # Eliminar bloques existentes
    cur=None
    deleted_count = 0
    while True:
        d = safe_list(pid, cur)
        if not d: break
        for b in d.get("results",[]):
            if b.get("archived"):
                continue
            try:
                notion.blocks.delete(b["id"])
                deleted_count += 1
                if deleted_count % 50 == 0:
                    print(f"       ...{deleted_count} bloques eliminados", end="\r")
            except Exception as e:
                print(f"       ⚠️ no se pudo borrar bloque {b['id'][:8]}: {e}")
        if not d.get("has_more"): break
        cur = d.get("next_cursor")
    print(f"       {deleted_count} bloques eliminados")

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
        elif l.strip() == "---":
            blocks.append({"object":"block","type":"divider","divider":{}})
        elif l.strip():
            blocks.append(_make_text_block("paragraph", "paragraph", l))
        i+=1

    # Crear bloques en lotes
    print(f"       Creando {len(blocks)} bloques...")
    for idx, block in enumerate(blocks):
        try:
            notion.blocks.children.append(block_id=pid, children=[block])
            if (idx + 1) % 50 == 0:
                print(f"       ...{idx + 1}/{len(blocks)} bloques creados", end="\r")
        except Exception as e:
            print(f"       ⚠️ error creando bloque {idx}: {e}")
    print(f"       {len(blocks)} bloques creados")

DOCS = {
    "kernel":        {"notion_id": "377938be-fc42-805e-a408-c9ae518d4fe7", "local_file": BASE_DIR / "Kernel.md", "label": "TECHNICAL KERNEL"},
    "system_prompt": {"notion_id": "37b938be-fc42-8001-9b9b-fcf81130d274", "local_file": BASE_DIR / "System Prompt.md", "label": "SYSTEM PROMPT"},
    "career_canon":  {"notion_id": "377938be-fc42-8089-93f2-f52dbd2dec6c", "local_file": BASE_DIR / "Career Canon.md", "label": "CAREER CANON"},
    "manual":        {"notion_id": "372938be-fc42-8050-9a67-e40857d7806e", "local_file": BASE_DIR / "Manual.md", "label": "MANUAL DE USUARIO"},
    "aliases":       {"notion_id": "37c938be-fc42-80d4-b9ae-f5969830331b", "local_file": BASE_DIR / "Aliases.md", "label": "ALIASES"},
    "change_log":    {"notion_id": "390938be-fc42-80e7-b429-d7d730339353", "local_file": BASE_DIR / "Change Log.md", "label": "CHANGE LOG"},
    "brief":         {"notion_id": "3a3938be-fc42-8008-9e90-ec435c01f50d", "local_file": BASE_DIR / "Brief.md", "label": "DOCUMENT NAVIGATION BRIEF"},
}

# Procesar solo documentos con hipervínculos nuevos (orden por cantidad de cambios)
# Basado en diff de apply_hyperlinks.py
DOCS_ORDERED = [
    "career_canon",    # 2 hipervínculos nuevos
    "aliases",         # 8 hipervínculos nuevos
    "system_prompt",   # 12 hipervínculos nuevos
    "kernel",          # 26 hipervínculos nuevos
    "manual",          # 40 hipervínculos nuevos
    # Brief: 0 cambios (omitido)
    # change_log: sin cambios de hipervínculos (omitido)
]

def main():
    print("vsync_doc_fast - Sync optimizado local→notion")
    print("Procesando documentos por tamaño (menor a mayor)")
    print("=" * 50)
    
    for doc_key in DOCS_ORDERED:
        if doc_key not in DOCS:
            print(f"⚠️  {doc_key} no encontrado en DOCS, saltando...")
            continue
            
        doc_info = DOCS[doc_key]
        notion_id = doc_info["notion_id"]
        local_file = doc_info["local_file"]
        label = doc_info["label"]
        
        print(f"\n📄 {label} ({doc_key})")
        
        if not local_file.exists():
            print(f"   ⚠️  Archivo local no existe: {local_file}")
            continue
            
        # Leer contenido local
        local_text = local_file.read_text(encoding="utf-8")
        
        # Push a Notion
        print(f"   ↗️  Pushing to Notion...")
        start_time = time.time()
        
        try:
            vsync.push_local_to_notion(notion_id, local_file)
            elapsed = time.time() - start_time
            print(f"   ✅ Completado en {elapsed:.1f}s")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
            
        # Pausa breve entre documentos para evitar rate limiting
        time.sleep(1)
    
    print("\n" + "=" * 50)
    print("Sync optimizado completado")

if __name__ == "__main__":
    main()