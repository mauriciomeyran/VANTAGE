#!/usr/bin/env python3
"""
vsync_doc.py — VANTAGE v9.13.0 (LAYER 4)
- BASE_DIR = .../ACTIVE (version-agnostic)
- Usa .venv de Layer_1
- Fetch con httpx (fix NoneType)
- FIX: direction local/auto ahora funcional (push_local_to_notion conectado)
- FIX: auto_commit() movido dentro de main() y llamado al finalizar
- FIX: bloques code > 2000 chars truncados en chunks de párrafo (Notion API limit)
- v8.5.5: REMOVED --direction local (ACTIVE LOCAL es read-only, Notion es única fuente de verdad)
- v8.5.5: Auto mode ahora solo permite notion→local, local→notion deshabilitado
- v8.5.6: FIX Permission handling — _make_writable() y _restore_permissions() para manejar archivos read-only
- v9.13.0: REFACTORED push_local_to_notion() para usar PATCH puntual en lugar de delete-all + create-all
          Esto preserva los block_ids de Notion, manteniendo la integridad de los anchors de hipervínculos
          según KERNEL:DOCUMENTATION-011. Eliminados comentarios temporales de v8.5.7.
"""

import sys, os, argparse, time, hashlib, json, stat
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
    "brief":           {"notion_id": "3a3938be-fc42-8008-9e90-ec435c01f50d", "local_file": BASE_DIR / "Brief.md", "label": "DOCUMENT NAVIGATION BRIEF"},
    "change_log_archivo": {"notion_id": "3ba938be-fc42-8011-8947-fb4fa5d1f63f", "local_file": BASE_DIR / "Changelog Archivo.md", "label": "CHANGELOG ARCHIVO"},
}

NOTION_TEXT_LIMIT = 1990  # margen de seguridad bajo el límite de 2000

MANIFEST_PATH = BASE_DIR / ".vsync_manifest.json"

def _hash(text: str) -> str:
    return hashlib.sha256((text or "").strip().encode("utf-8")).hexdigest()

def _load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        try:
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_manifest(manifest: dict):
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

def _make_writable(file_path: Path) -> int:
    """Hace el archivo temporalmente writable y retorna los permisos originales."""
    if not file_path.exists():
        return 0o644  # Default permissions for new files
    original_mode = file_path.stat().st_mode
    try:
        file_path.chmod(0o644)  # rw-r--r--
        return original_mode
    except Exception as e:
        print(f"  ⚠️  No se pudo hacer writable {file_path.name}: {e}")
        return original_mode

def _restore_permissions(file_path: Path, original_mode: int):
    """Restaura los permisos originales del archivo."""
    if not file_path.exists():
        return
    try:
        file_path.chmod(original_mode)
    except Exception as e:
        print(f"  ⚠️  No se pudo restaurar permisos de {file_path.name}: {e}")

def _decide(key, local_text, notion_text, manifest):
    """Decide direccion via hash, no mtime. Retorna: 'local->notion' | 'notion->local' | 'noop' | 'conflict'"""
    last = manifest.get(key)
    lh, nh = _hash(local_text), _hash(notion_text)
    if lh == nh:
        return "noop"
    if last is None:
        # sin historial: no hay forma segura de decidir -> tratar como conflicto
        return "conflict"
    if lh == last and nh != last:
        return "notion->local"
    if nh == last and lh != last:
        return "local->notion"
    return "conflict"  # ambos lados cambiaron desde el ultimo sync


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

import re as _re

# Patrón de link markdown "[texto](url)". No captura links dentro de un
# fence de código (los bloques 'code' nunca pasan por esta función — ver
# _make_code_blocks, que sigue escribiendo contenido crudo a propósito).
_MD_LINK_RE = _re.compile(r"\[([^\[\]]+)\]\((https?://[^\s()]+)\)")

def _text_to_rich_text(content: str) -> list:
    """
    Convierte una línea de markdown a una lista de segmentos rich_text de
    Notion, resolviendo "[texto](url)" a un link real (rich_text con
    campo "link"), en vez de dejar la sintaxis markdown como texto plano.

    FIX (Cross-Reference Hyperlinks — bug de tabla): antes de este parche,
    todo el contenido (incluyendo celdas de tabla vía _try_parse_table)
    se empujaba a Notion como texto literal sin interpretar la sintaxis
    de link, así que "[KERNEL:CV-GOLDEN-RULES-001](url)" llegaba a Notion
    como el string completo con corchetes y URL pegados al ID — rompiendo
    la coincidencia exacta que generate_census.py necesita para reconocer
    el bloque como definición del ID. Ver DT — Census Sync / Cross-Reference
    Hyperlinks Pt 3.

    Trunca el contenido combinado a NOTION_TEXT_LIMIT igual que antes.
    """
    content = content[:NOTION_TEXT_LIMIT]
    segments = []
    pos = 0
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
    """Crea un bloque de texto truncando si supera el límite, resolviendo
    cualquier link markdown embebido a un link real de Notion."""
    return {"object":"block","type":block_type, block_type:{
        "rich_text": _text_to_rich_text(content)
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

def _patch_block_rich_text(block_id: str, btype: str, new_rich_text: list) -> bool:
    """
    PATCH /v1/blocks/{id} sobre el campo rich_text del tipo correspondiente.
    No cambia el tipo del bloque, no cambia su posición, no cambia su ID.
    Reutiliza la lógica validada de apply_hyperlinks_notion.py.
    """
    payload = {btype: {"rich_text": new_rich_text}}
    for attempt in range(3):
        try:
            r = HTTP.patch(
                f"https://api.notion.com/v1/blocks/{block_id}",
                headers=HEADERS, json=payload, timeout=30,
            )
            if r.status_code == 200:
                return True
            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", 2))
                time.sleep(wait)
                continue
            print(f"       ⚠️ [ERROR {r.status_code}] PATCH {block_id[:8]}: {r.text[:150]}")
            return False
        except Exception as e:
            print(f"       ⚠️ Exception PATCH {block_id[:8]}: {e}")
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
            continue
    return False

def _patch_table_row(block_id: str, cells: list) -> bool:
    """PATCH de una table_row completa (todas sus celdas) — mismo bloque, mismo ID."""
    payload = {"table_row": {"cells": cells}}
    for attempt in range(3):
        try:
            r = HTTP.patch(
                f"https://api.notion.com/v1/blocks/{block_id}",
                headers=HEADERS, json=payload, timeout=30,
            )
            if r.status_code == 200:
                return True
            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", 2))
                time.sleep(wait)
                continue
            print(f"       ⚠️ [ERROR {r.status_code}] PATCH table_row {block_id[:8]}: {r.text[:150]}")
            return False
        except Exception as e:
            print(f"       ⚠️ Exception PATCH table_row {block_id[:8]}: {e}")
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
            continue
    return False

def push_local_to_notion(pid, path):
    """
    Sincroniza archivo local a Notion usando PATCH puntual para preservar block_ids.
    Reemplaza el patrón destroy/rebuild (delete-all + create-all) que rompía anchors.
    
    ESTRATEGIA:
    1. Fetch bloques existentes de Notion con sus block_ids
    2. Parsear archivo local a bloques
    3. Hacer matching por posición y tipo (estrategia determinista)
    4. PATCH bloques existentes que coinciden por posición
    5. DELETE bloques sobrantes al final
    6. APPEND bloques nuevos al final
    
    Esta estrategia preserva los block_ids de bloques existentes manteniendo
    la integridad de los anchors de hipervínculos según KERNEL:DOCUMENTATION-011.
    """
    # Fetch bloques existentes
    existing_blocks = []
    cur = None
    while True:
        d = safe_list(pid, cur)
        if not d:
            break
        for b in d.get("results", []):
            if b.get("archived"):
                continue
            existing_blocks.append(b)
        if not d.get("has_more"):
            break
        cur = d.get("next_cursor")
    
    # Parsear archivo local a bloques
    lines = path.read_text(encoding="utf-8").splitlines()
    local_blocks = []
    i = 0
    while i < len(lines):
        l = lines[i]
        table_block, next_i = _try_parse_table(lines, i)
        if table_block is not None:
            local_blocks.append(table_block)
            i = next_i
            continue
        if l.startswith("```"):
            lang = l[3:].strip(); i+=1; code=[]
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i]); i+=1
            local_blocks.extend(_make_code_blocks(lang, "\n".join(code)))
        elif l.startswith("### "):
            local_blocks.append(_make_text_block("heading_3", "heading_3", l[4:]))
        elif l.startswith("## "):
            local_blocks.append(_make_text_block("heading_2", "heading_2", l[3:]))
        elif l.startswith("# "):
            local_blocks.append(_make_text_block("heading_1", "heading_1", l[2:]))
        elif l.startswith("- [x] ") or l.startswith("- [X] "):
            local_blocks.append({"object":"block","type":"to_do","to_do":{
                "checked":True,"rich_text":[{"type":"text","text":{"content":l[6:NOTION_TEXT_LIMIT+6]}}]}})
        elif l.startswith("- [ ] "):
            local_blocks.append({"object":"block","type":"to_do","to_do":{
                "checked":False,"rich_text":[{"type":"text","text":{"content":l[6:NOTION_TEXT_LIMIT+6]}}]}})
        elif l.startswith("- "):
            local_blocks.append(_make_text_block("bulleted_list_item", "bulleted_list_item", l[2:]))
        elif l.startswith("> "):
            local_blocks.append(_make_text_block("quote", "quote", l[2:]))
        elif l.startswith("---"):
            local_blocks.append({"object":"block","type":"divider","divider":{}})
        elif l.strip():
            local_blocks.append(_make_text_block("paragraph", "paragraph", l))
        else:
            local_blocks.append({"object":"block","type":"paragraph","paragraph":{"rich_text":[]}})
        i+=1
    
    # PATCH por posición: para cada bloque local, intentar hacer PATCH al bloque existente en la misma posición
    patches_applied = 0
    blocks_created = 0
    blocks_deleted = 0
    
    max_blocks = max(len(existing_blocks), len(local_blocks))
    
    for idx in range(max_blocks):
        if idx < len(local_blocks) and idx < len(existing_blocks):
            # Ambos existen: intentar PATCH
            local_block = local_blocks[idx]
            existing_block = existing_blocks[idx]
            block_type = local_block.get("type")
            existing_type = existing_block.get("type")
            
            # Si tipos coinciden, hacer PATCH
            if block_type == existing_type:
                if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", 
                                "bulleted_list_item", "quote", "to_do"]:
                    # Bloques de texto: PATCH rich_text
                    new_rich_text = local_block[block_type].get("rich_text", [])
                    if _patch_block_rich_text(existing_block["id"], block_type, new_rich_text):
                        patches_applied += 1
                elif block_type == "divider":
                    # Divider no tiene contenido que actualizar
                    pass
                elif block_type == "table":
                    # Tabla: estructura completa (más complejo, simplificado por ahora)
                    # TODO: Implementar PATCH granular de tablas
                    # Por ahora, si la tabla cambia, no la tocamos
                    pass
                elif block_type == "table_row":
                    # Table row: PATCH cells
                    new_cells = local_block["table_row"].get("cells", [])
                    if _patch_table_row(existing_block["id"], new_cells):
                        patches_applied += 1
                else:
                    # Otros tipos: intentar PATCH genérico
                    payload = {block_type: local_block[block_type]}
                    if _patch_block_rich_text(existing_block["id"], block_type, 
                                             local_block[block_type].get("rich_text", [])):
                        patches_applied += 1
            else:
                # Tipos no coinciden: recrear (DELETE + CREATE)
                try:
                    notion.blocks.delete(existing_block["id"])
                    blocks_deleted += 1
                except Exception as e:
                    print(f"       ⚠️ no se pudo borrar bloque {existing_block['id'][:8]}: {e}")
                blocks_created += 1
                
        elif idx < len(local_blocks):
            # Solo existe local: crear nuevo
            blocks_created += 1
            
        elif idx < len(existing_blocks):
            # Solo existe en Notion: borrar
            try:
                notion.blocks.delete(existing_blocks[idx]["id"])
                blocks_deleted += 1
            except Exception as e:
                print(f"       ⚠️ no se pudo borrar bloque {existing_blocks[idx]['id'][:8]}: {e}")
    
    # Crear bloques nuevos al final (para casos donde len(local) > len(existing))
    if len(local_blocks) > len(existing_blocks):
        new_blocks = local_blocks[len(existing_blocks):]
        for j in range(0, len(new_blocks), 100):
            notion.blocks.children.append(block_id=pid, children=new_blocks[j:j+100])
    
    print(f"       ✓ PATCH stats: {patches_applied} actualizados, {blocks_created} nuevos, {blocks_deleted} eliminados")

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
    p.add_argument("--direction", choices=["notion","auto","local"], default="auto", help="notion→local (read-only), auto (decide por hash), o local→notion (PATCH puntual, preserva anchors)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--doc", choices=list(DOCS.keys()))
    args = p.parse_args()
    targets = {args.doc: DOCS[args.doc]} if args.doc else DOCS

    print(f"\nvsync_doc v9.13.0 L4 → ACTIVE  [{args.direction.upper()}]{' DRY' if args.dry_run else ''}")
    print("⚠️  DOCUMENTACIÓN ACTIVE LOCAL ES READ-ONLY — NOTION ES ÚNICA FUENTE DE VERDAD")
    if args.direction == "local":
        print("ℹ️  --direction local ahora usa PATCH puntual para preservar anchors (KERNEL:DOCUMENTATION-011)\n")
    else:
        print()

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
            else:
                manifest = _load_manifest()
                local_text = local.read_text(encoding="utf-8") if local.exists() else ""
                notion_text, _ts_unused = fetch_notion_as_md(d["notion_id"])
                decision = _decide(k, local_text, notion_text or "", manifest)
                label_map = {
                    "local->notion": "local→notion (PATCH puntual)",
                    "notion->local": "notion→local",
                    "noop": "sin cambios (hash igual)",
                    "conflict": "⚠️ CONFLICT — ambos lados cambiaron, resolver manual",
                }
                print(f"  · {d['label']:<30} [DRY] {label_map[decision]} (auto, sin cambios aplicados)")
            continue

        # ── RUN REAL: aquí sí se justifica el fetch completo y recursivo ──
        md, ts = fetch_notion_as_md(d["notion_id"])
        if md is None:
            print(f"  ✗ {d['label']:<30} ERROR")
            continue

        if args.direction == "notion":
            local.parent.mkdir(parents=True, exist_ok=True)
            original_mode = _make_writable(local)
            local.write_text(md, encoding="utf-8")
            _restore_permissions(local, original_mode)
            print(f"  ✓ {d['label']:<30} notion→local")

        elif args.direction == "local":
            print(f"  → {d['label']:<30} local→notion (PATCH puntual, preserva anchors)")
            original_mode = _make_writable(local)
            push_local_to_notion(d["notion_id"], local)
            _restore_permissions(local, original_mode)
            manifest = _load_manifest()
            manifest[k] = _hash(local.read_text(encoding="utf-8"))
            _save_manifest(manifest)

        else:  # auto — decide por hash de contenido vs manifest, no por mtime
            manifest = _load_manifest()
            local_text = local.read_text(encoding="utf-8") if local.exists() else ""
            decision = _decide(k, local_text, md, manifest)

            if decision == "noop":
                print(f"  · {d['label']:<30} sin cambios (hash igual, auto)")
            elif decision == "conflict":
                print(f"  ⚠️ {d['label']:<30} CONFLICT — ambos lados cambiaron desde el último sync. SIN APLICAR. Resolver manual con --direction.")
            elif decision == "local->notion":
                print(f"  ⚠️  {d['label']:<30} SKIP — local→notion deshabilitado (ACTIVE LOCAL es read-only)")
                print(f"    Cambios locales detectados pero no se pueden subir a Notion.")
                print(f"    Use --direction notion para sobrescribir local con la versión de Notion.")
                continue
            else:  # notion->local
                local.parent.mkdir(parents=True, exist_ok=True)
                original_mode = _make_writable(local)
                local.write_text(md, encoding="utf-8")
                _restore_permissions(local, original_mode)
                manifest[k] = _hash(md)
                _save_manifest(manifest)
                print(f"  ✓ {d['label']:<30} notion→local (auto)")

    if not args.dry_run:
        auto_commit(dry_run=False)

if __name__ == "__main__":
    main()
