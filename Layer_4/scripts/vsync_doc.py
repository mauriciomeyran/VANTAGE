#!/usr/bin/env python3
"""
vsync_doc.py — VANTAGE v8.5.2 (LAYER 4)
- BASE_DIR = .../ACTIVE (version-agnostic)
- Usa .venv de Layer_1
- Fetch con httpx (fix NoneType)
- Incluye Cheat Sheet
"""

import sys, os, argparse, time
from pathlib import Path
from datetime import datetime, timezone

# ── Paths L4 → L1 ────────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve()
_PROJECT = _SCRIPT_DIR.parents[2]  # 04-Vantage_CV
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
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Notion-Version": "2022-06-28"}

BASE_DIR = _PROJECT / "- Documentación" / "ACTIVE"

DOCS = {
    "kernel":        {"notion_id": "377938be-fc42-805e-a408-c9ae518d4fe7", "local_file": BASE_DIR / "Kernel.md", "label": "TECHNICAL KERNEL"},
    "system_prompt": {"notion_id": "37b938be-fc42-8001-9b9b-fcf81130d274", "local_file": BASE_DIR / "System Prompt.md", "label": "SYSTEM PROMPT"},
    "career_canon":  {"notion_id": "377938be-fc42-8089-93f2-f52dbd2dec6c", "local_file": BASE_DIR / "Career Canon.md", "label": "CAREER CANON"},
    "manual":        {"notion_id": "372938be-fc42-8050-9a67-e40857d7806e", "local_file": BASE_DIR / "Manual.md", "label": "MANUAL DE USUARIO"},
    "cheat_sheet":   {"notion_id": "37c938be-fc42-80d4-b9ae-f5969830331b", "local_file": BASE_DIR / "Cheat Sheet & Change Log.md", "label": "CHEAT SHEET"},
}

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
            lines.append(_block_to_md(b)); total+=1
        if not data.get("has_more"): break
        cur = data.get("next_cursor")
    print(f"     {total} bloques")
    return "".join(lines), ts

def push_local_to_notion(pid, path):
    cur=None
    while True:
        d = safe_list(pid, cur)
        if not d: break
        for b in d.get("results",[]):
            try: notion.blocks.delete(b["id"])
            except: pass
        if not d.get("has_more"): break
        cur = d.get("next_cursor")
    
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks=[]; i=0
    while i < len(lines):
        l = lines[i]
        if l.startswith("```"):
            lang = l[3:].strip(); i+=1; code=[]
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i]); i+=1
            blocks.append({"object":"block","type":"code","code":{"language":lang or "plain text","rich_text":[{"type":"text","text":{"content":"\n".join(code)}}]}})
        elif l.startswith("### "):
            blocks.append({"object":"block","type":"heading_3","heading_3":{"rich_text":[{"type":"text","text":{"content":l[4:]}}]}})
        elif l.startswith("## "):
            blocks.append({"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":l[3:]}}]}})
        elif l.startswith("# "):
            blocks.append({"object":"block","type":"heading_1","heading_1":{"rich_text":[{"type":"text","text":{"content":l[2:]}}]}})
        elif l.startswith("- [x] ") or l.startswith("- [X] "):
            blocks.append({"object":"block","type":"to_do","to_do":{"checked":True,"rich_text":[{"type":"text","text":{"content":l[6:]}}]}})
        elif l.startswith("- [ ] "):
            blocks.append({"object":"block","type":"to_do","to_do":{"checked":False,"rich_text":[{"type":"text","text":{"content":l[6:]}}]}})
        elif l.startswith("- "):
            blocks.append({"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":[{"type":"text","text":{"content":l[2:]}}]}})
        elif l.startswith("> "):
            blocks.append({"object":"block","type":"quote","quote":{"rich_text":[{"type":"text","text":{"content":l[2:]}}]}})
        elif l.startswith("---"):
            blocks.append({"object":"block","type":"divider","divider":{}})
        elif l.strip():
            blocks.append({"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":l}}]}})
        else:
            blocks.append({"object":"block","type":"paragraph","paragraph":{"rich_text":[]}})
        i+=1
    for j in range(0, len(blocks), 100):
        notion.blocks.children.append(block_id=pid, children=blocks[j:j+100])

def main():
    p = argparse.ArgumentParser(); p.add_argument("--direction", choices=["notion","local","auto"], default="auto")
    p.add_argument("--dry-run", action="store_true"); p.add_argument("--doc", choices=list(DOCS.keys()))
    args = p.parse_args()
    targets = {args.doc: DOCS[args.doc]} if args.doc else DOCS
    print(f"\nvsync_doc v8.5.2 L4 → ACTIVE  [{args.direction.upper()}]{' DRY' if args.dry_run else ''}\n")
    for k,d in targets.items():
        md, ts = fetch_notion_as_md(d["notion_id"])
        if md is None: print(f"  ✗ {d['label']:<30} ERROR"); continue
        local = d["local_file"]
        if args.direction == "notion" and not args.dry_run:
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text(md, encoding="utf-8")
        print(f"  ✓ {d['label']:<30} notion→local")

if __name__ == "__main__": main()

# ── Auto-commit integrado ────────────────────────────────────────────────────
def auto_commit(dry_run=False):
    """Llama a git_sync.py si hay cambios en ACTIVE."""
    import subprocess
    gs = _PROJECT / "Layer_4/scripts/git_sync.py"
    if not gs.exists():
        return
    args = [sys.executable, str(gs)]
    if dry_run:
        args.append("--dry-run")
    try:
        result = subprocess.run(args, capture_output=True, text=True, cwd=str(_PROJECT))
        if result.returncode == 0:
            print(f"  📦 {result.stdout.strip()}")
        elif "No hay cambios" in result.stdout:
            pass  # silencio limpio
        else:
            print(f"  ⚠️ git: {result.stderr.strip() or result.stdout.strip()}")
    except Exception as e:
        print(f"  ⚠️ git_sync falló: {e}")
