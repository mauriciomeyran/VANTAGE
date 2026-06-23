#!/usr/bin/env python3
"""
vsync_doc.py — VANTAGE v8.5
Sincronización bidireccional Notion ↔ .md locales para páginas de documentación.

Uso:
    python3 vsync_doc.py                        # auto: gana el más reciente
    python3 vsync_doc.py --direction notion     # Notion → local (default pre-sesión)
    python3 vsync_doc.py --direction local      # local → Notion
    python3 vsync_doc.py --direction auto       # compara timestamps, gana más reciente
    python3 vsync_doc.py --dry-run              # muestra diferencias sin escribir
    python3 vsync_doc.py --doc kernel           # sincroniza solo un documento

Requiere:
    NOTION_API_KEY en layer_1.env
    notion-client instalado en .venv
"""

import sys
import os
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

# ── Path injection (local notion_client.py shadow fix) ──────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent
_VENV_SITE  = _SCRIPT_DIR.parent / ".venv" / "lib"
for _p in _VENV_SITE.glob("python3*/site-packages"):
    sys.path.insert(0, str(_p))
    break

# ── Cargar env ───────────────────────────────────────────────────────────────
_ENV_PATH = _SCRIPT_DIR.parent / "config" / "layer_1.env"
if _ENV_PATH.exists():
    with open(_ENV_PATH) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

NOTION_TOKEN = os.environ.get("NOTION_API_KEY") or os.environ.get("NOTION_TOKEN")
if not NOTION_TOKEN:
    print("❌  NOTION_API_KEY no encontrado. Corre: set -a && source ../config/layer_1.env && set +a")
    sys.exit(1)

from notion_client import Client  # noqa: E402

notion = Client(auth=NOTION_TOKEN)

# ── Mapa de documentos ───────────────────────────────────────────────────────
BASE_DIR = Path.home() / "Documents" / "04-Vantage_CV" / "- Documentación" / "v8.5"

DOCS = {
    "kernel": {
        "notion_id": "377938be-fc42-805e-a408-c9ae518d4fe7",
        "local_file": BASE_DIR / "Kernel v8.5.md",
        "label": "TECHNICAL KERNEL",
    },
    "system_prompt": {
        "notion_id": "37b938be-fc42-8001-9b9b-fcf81130d274",
        "local_file": BASE_DIR / "System Prompt v8.5.md",
        "label": "SYSTEM PROMPT",
    },
    "career_canon": {
        "notion_id": "377938be-fc42-8089-93f2-f52dbd2dec6c",
        "local_file": BASE_DIR / "Career Canon v8.5.md",
        "label": "CAREER CANON",
    },
    "manual": {
        "notion_id": "372938be-fc42-8050-9a67-e40857d7806e",
        "local_file": BASE_DIR / "Manual v8.5.md",
        "label": "MANUAL DE USUARIO",
    },
    "cheat_sheet": {
        "notion_id": "37c938be-fc42-80d4-b9ae-f5969830331b",
        "local_file": BASE_DIR / "Cheat Sheet & Change Log.md",
        "label": "ALIASES & CHANGE LOG",
    },
}

# ── Helpers Notion → Markdown ────────────────────────────────────────────────

def _rich_text(rt_list: list) -> str:
    return "".join(r.get("plain_text", "") for r in rt_list)


def _block_to_md(block: dict) -> str:
    bt = block.get("type", "")
    b  = block.get(bt, {})

    if bt == "paragraph":
        return _rich_text(b.get("rich_text", [])) + "\n"
    if bt in ("heading_1", "heading_2", "heading_3"):
        level = {"heading_1": "#", "heading_2": "##", "heading_3": "###"}[bt]
        return f"{level} {_rich_text(b.get('rich_text', []))}\n"
    if bt == "bulleted_list_item":
        return f"- {_rich_text(b.get('rich_text', []))}\n"
    if bt == "numbered_list_item":
        return f"1. {_rich_text(b.get('rich_text', []))}\n"
    if bt == "to_do":
        check = "x" if b.get("checked") else " "
        return f"- [{check}] {_rich_text(b.get('rich_text', []))}\n"
    if bt == "code":
        lang = b.get("language", "")
        code = _rich_text(b.get("rich_text", []))
        return f"```{lang}\n{code}\n```\n"
    if bt == "quote":
        return f"> {_rich_text(b.get('rich_text', []))}\n"
    if bt == "divider":
        return "---\n"
    if bt == "callout":
        icon = b.get("icon", {}).get("emoji", "")
        return f"> {icon} {_rich_text(b.get('rich_text', []))}\n"
    if bt == "toggle":
        return f"**{_rich_text(b.get('rich_text', []))}**\n"
    if bt == "child_page":
        return f"[{b.get('title','')}]\n"
    return ""  # tipos no soportados: silencio


def fetch_notion_as_md(page_id: str) -> tuple[str, datetime]:
    """Descarga página Notion y retorna (markdown, last_edited_time)."""
    # Metadata para timestamp
    meta = notion.pages.retrieve(page_id)
    last_edited = datetime.fromisoformat(
        meta["last_edited_time"].replace("Z", "+00:00")
    )

    # Título
    title = ""
    props = meta.get("properties", {})
    for prop in props.values():
        if prop.get("type") == "title":
            title = _rich_text(prop["title"])
            break

    # Bloques
    lines = [f"# {title}\n\n"] if title else []
    cursor = None
    while True:
        kwargs = {"block_id": page_id, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        resp = notion.blocks.children.list(**kwargs)
        for block in resp.get("results", []):
            md = _block_to_md(block)
            if md:
                lines.append(md)
        if resp.get("has_more"):
            cursor = resp["next_cursor"]
        else:
            break

    return "".join(lines), last_edited


def push_local_to_notion(page_id: str, md_path: Path) -> None:
    """Sube .md local a Notion (append sobre página limpia)."""
    content = md_path.read_text(encoding="utf-8")
    lines   = content.splitlines()

    # Limpiar bloques existentes
    cursor = None
    while True:
        kwargs = {"block_id": page_id, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        resp = notion.blocks.children.list(**kwargs)
        for block in resp.get("results", []):
            notion.blocks.delete(block["id"])
        if resp.get("has_more"):
            cursor = resp["next_cursor"]
        else:
            break

    # Convertir líneas a bloques Notion
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Code block
        if line.startswith("```"):
            lang = line[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            blocks.append({
                "object": "block", "type": "code",
                "code": {
                    "language": lang or "plain text",
                    "rich_text": [{"type": "text", "text": {"content": "\n".join(code_lines)}}]
                }
            })
        elif line.startswith("### "):
            blocks.append({"object": "block", "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": line[4:]}}]}})
        elif line.startswith("## "):
            blocks.append({"object": "block", "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": line[3:]}}]}})
        elif line.startswith("# "):
            blocks.append({"object": "block", "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}})
        elif line.startswith("- [x] ") or line.startswith("- [X] "):
            blocks.append({"object": "block", "type": "to_do",
                "to_do": {"checked": True,
                    "rich_text": [{"type": "text", "text": {"content": line[6:]}}]}})
        elif line.startswith("- [ ] "):
            blocks.append({"object": "block", "type": "to_do",
                "to_do": {"checked": False,
                    "rich_text": [{"type": "text", "text": {"content": line[6:]}}]}})
        elif line.startswith("- "):
            blocks.append({"object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}})
        elif line.startswith("> "):
            blocks.append({"object": "block", "type": "quote",
                "quote": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}})
        elif line.startswith("---"):
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        elif line.strip():
            blocks.append({"object": "block", "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": line}}]}})
        else:
            blocks.append({"object": "block", "type": "paragraph",
                "paragraph": {"rich_text": []}})
        i += 1

    # Notion acepta máx 100 bloques por request
    for chunk_start in range(0, len(blocks), 100):
        notion.blocks.children.append(
            block_id=page_id,
            children=blocks[chunk_start:chunk_start + 100]
        )


# ── Core sync ────────────────────────────────────────────────────────────────

def sync_doc(key: str, doc: dict, direction: str, dry_run: bool) -> dict:
    label     = doc["label"]
    local_path = doc["local_file"]
    notion_id  = doc["notion_id"]

    result = {"key": key, "label": label, "action": None, "status": "ok", "detail": ""}

    # Timestamps
    notion_md, notion_ts = fetch_notion_as_md(notion_id)

    if local_path.exists():
        local_mtime = datetime.fromtimestamp(local_path.stat().st_mtime, tz=timezone.utc)
        local_md    = local_path.read_text(encoding="utf-8")
    else:
        local_mtime = datetime.min.replace(tzinfo=timezone.utc)
        local_md    = ""

    # Determinar dirección
    if direction == "notion":
        winner = "notion"
    elif direction == "local":
        winner = "local"
    else:  # auto
        if not local_path.exists():
            winner = "notion"
        elif notion_md.strip() == local_md.strip():
            result["action"] = "in_sync"
            result["detail"] = "Sin diferencias"
            return result
        else:
            winner = "notion" if notion_ts >= local_mtime else "local"
            result["detail"] = (
                f"Notion: {notion_ts.strftime('%Y-%m-%d %H:%M')} UTC  |  "
                f"Local: {local_mtime.strftime('%Y-%m-%d %H:%M')} UTC  →  gana {winner}"
            )

    if winner == "notion":
        result["action"] = "notion→local"
        if not dry_run:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_text(notion_md, encoding="utf-8")
    else:
        result["action"] = "local→notion"
        if not dry_run:
            push_local_to_notion(notion_id, local_path)

    return result


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="vsync_doc — Sync bidireccional Notion ↔ .md (VANTAGE v8.5)"
    )
    parser.add_argument(
        "--direction", choices=["notion", "local", "auto"], default="auto",
        help="notion=Notion gana | local=local gana | auto=gana el más reciente (default)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Muestra qué haría sin escribir nada"
    )
    parser.add_argument(
        "--doc", choices=list(DOCS.keys()), default=None,
        help="Sincroniza solo un documento específico"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output en JSON (para integración con vstatus)"
    )
    args = parser.parse_args()

    targets = {args.doc: DOCS[args.doc]} if args.doc else DOCS

    prefix = "[DRY RUN] " if args.dry_run else ""
    if not args.json:
        print(f"\n{'='*58}")
        print(f"  vsync_doc — VANTAGE v8.5  {prefix}")
        print(f"  Dirección: {args.direction.upper()}  |  Docs: {len(targets)}")
        print(f"{'='*58}\n")

    results = []
    for key, doc in targets.items():
        try:
            r = sync_doc(key, doc, args.direction, args.dry_run)
        except Exception as e:
            r = {"key": key, "label": doc["label"], "action": "error",
                 "status": "error", "detail": str(e)}
        results.append(r)

        if not args.json:
            icons = {"notion→local": "⬇", "local→notion": "⬆",
                     "in_sync": "✓", "error": "✗"}
            icon = icons.get(r["action"], "?")
            detail = f"  {r['detail']}" if r["detail"] else ""
            print(f"  {icon}  {r['label']:<30} [{r['action']}]{detail}")

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        in_sync = sum(1 for r in results if r["action"] == "in_sync")
        errors  = sum(1 for r in results if r["status"] == "error")
        written = len(results) - in_sync - errors
        print(f"\n  Resultado: {written} sincronizados · {in_sync} en sync · {errors} errores")
        print(f"{'='*58}\n")


if __name__ == "__main__":
    main()
