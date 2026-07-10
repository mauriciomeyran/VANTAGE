import os
import sys
import time
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────

script_dir = Path(__file__).resolve().parent
dotenv_path = script_dir.parent / "config" / "layer_1.env"

if not dotenv_path.exists():
    print(f"[ERROR] No se encontró layer_1.env en {dotenv_path}")
    sys.exit(1)

load_dotenv(dotenv_path=dotenv_path)
NOTION_TOKEN = os.getenv("NOTION_TOKEN") or os.getenv("NOTION_API_KEY")

if not NOTION_TOKEN:
    print("[ERROR] Ni NOTION_TOKEN ni NOTION_API_KEY definidos en layer_1.env")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

VALID_PREFIXES = ("KERNEL:", "MANUAL:", "CANON:", "CAREER_CANON:", "SP:", "ALIASES:", "CHANGELOG:")

DOCUMENTS = {
    "System Prompt": "37b938be-fc42-8001-9b9b-fcf81130d274",
    "Manual":        "372938be-fc42-8050-9a67-e40857d7806e",
    "Kernel":        "377938be-fc42-805e-a408-c9ae518d4fe7",
    "Career Canon":  "377938be-fc42-8089-93f2-f52dbd2dec6c",
    "Aliases":       "37c938be-fc42-80d4-b9ae-f5969830331b",
    "Change Log":    "390938be-fc42-80e7-b429-d7d730339353",
}

# Prioridad de documento al resolver el "mejor" bloque para un ID
# (menor número = mayor prioridad)
DOC_PRIORITY = {
    "Kernel":        1,
    "System Prompt": 2,
    "Manual":        3,
    "Career Canon":  4,
    "Aliases":       5,
    "Change Log":    6,
}

# ─── LISTADO CANÓNICO DE IDs (fuente: generate_census.py) ─────────────────────

CENSUS_SPEC = [
    {
        "name": "KERNEL",
        "rows": [
            {"id": "KERNEL:BOOTSTRAP-001"},
            {"id": "KERNEL:PURPOSE"},
            {"id": "KERNEL:ARCHITECTURE"},
            {"id": "KERNEL:ARCHITECTURE-L0"},
            {"id": "KERNEL:ARCHITECTURE-L1"},
            {"id": "KERNEL:ARCHITECTURE-L2"},
            {"id": "KERNEL:ARCHITECTURE-L3"},
            # typo histórico + forma correcta como lookup_ids para máxima cobertura
            {"id": "KERNEL:ARHITECTURE-L4", "lookup_ids": ["KERNEL:ARHITECTURE-L4", "KERNEL:ARCHITECTURE-L4"]},
            {"id": "KERNEL:SCHEMA"},
            {"id": "KERNEL:SCHEMA-001"},
            {"id": "KERNEL:SCHEMA-002"},
            {"id": "KERNEL:SCHEMA-003"},
            {"id": "KERNEL:SCHEMA-004"},
            {"id": "KERNEL:SCHEMA-005"},
            {"id": "KERNEL:SCHEMA-006"},
            {"id": "KERNEL:SCHEMA-007"},
            {"id": "KERNEL:TRACKER-SCHEMA"},
            {"id": "KERNEL:TRACKER-SCHEMA-001"},
            {"id": "KERNEL:TRACKER-SCHEMA-002"},
            {"id": "KERNEL:HEALTH-CHECK"},
            {"id": "KERNEL:HEALTH-CHECK-001"},
            {"id": "KERNEL:HEALTH-CHECK-002"},
            {"id": "KERNEL:OWNERSHIP"},
            {"id": "KERNEL:OWNERSHIP-001"},
            {"id": "KERNEL:OWNERSHIP-002"},
            {"id": "KERNEL:TRIGGERS"},
            {"id": "KERNEL:TRIGGER-001"},
            {"id": "KERNEL:TRIGGER-002"},
            {"id": "KERNEL:TRIGGER-003"},
            {"id": "KERNEL:TRIGGER-004"},
            {"id": "KERNEL:TRIGGER-005"},
            {"id": "KERNEL:TRIGGER-006"},
            {"id": "KERNEL:TRIGGER-007"},
            {"id": "KERNEL:TRIGGER-008"},
            {"id": "KERNEL:TRIGGER-009"},
            {"id": "KERNEL:GATE-DECISION"},
            {"id": "KERNEL:GATE-DECISION-001"},
            {"id": "KERNEL:GATE-DECISION-002"},
            {"id": "KERNEL:GATE-DECISION-003"},
            {"id": "KERNEL:GATE-DECISION-004"},
            {"id": "KERNEL:GATE-DECISION-005"},
            {"id": "KERNEL:CV-GOLDEN-RULES"},
            {"id": "KERNEL:CV-GOLDEN-RULES-001"},
            {"id": "KERNEL:CV-GOLDEN-RULES-002"},
            {"id": "KERNEL:CV-GOLDEN-RULES-003"},
            {"id": "KERNEL:CV-GOLDEN-RULES-004"},
            {"id": "KERNEL:CV-GOLDEN-RULES-005"},
            {"id": "KERNEL:CV-PIPELINE"},
            {"id": "KERNEL:CANON-UPDATE"},
            {"id": "KERNEL:FAIL-PHILOSOPHY"},
            {"id": "KERNEL:SCOPE"},
            {"id": "KERNEL:DATA-FLOW"},
            {"id": "KERNEL:ROUTING"},
            {"id": "KERNEL:EVOLUTION"},
            {"id": "KERNEL:DOC-CONTRACT"},
            {"id": "KERNEL:NORM"},
            # KERNEL:NAMING-CONVENTION pendiente de alta formal en el spec —
            # ver nota de sesión 2026-07-08: sección escrita en el Kernel pero
            # aún no agregada aquí. Hasta que se agregue, generate_census.py
            # la reportará como huérfana (comportamiento correcto e intencional).
        ],
    },
    {
        "name": "SYSTEM PROMPT",
        "rows": [
            {"id": "SP:CEDULA-DIGITAL"},
            {"id": "KERNEL:SCOPE"},
            {"id": "KERNEL:DATA-FLOW"},
            {"id": "SP:TRIGGERS"},
            {"id": "KERNEL:CV-GOLDEN-RULES"},
            {"id": "SP:SCHEMA"},
            {"id": "KERNEL:ROUTING"},
            {"id": "SP:ID-CONNECTORS-001"},
            {"id": "SP:BOOTSTRAP-001"},
            {"id": "SP:SYNC-RULE"},
            {"id": "SP:CONSISTENCY"},
        ],
    },
    {
        "name": "MANUAL",
        "rows": [
            {"id": "MANUAL:OBJETIVO-001"},
            {"id": "MANUAL:FUNCIONAMIENTO-001"},
            {"id": "MANUAL:SETUP-001"},
            {"id": "MANUAL:FLUJO-001"},
            {"id": "MANUAL:VCHECKLIST-001"},
            {"id": "MANUAL:VANTAGE-RUNTIME-001"},
            {"id": "MANUAL:GESTION-DATOS-001"},
            {"id": "MANUAL:TROUBLESHOOTING-001"},
            {"id": "MANUAL:PROMPTS-WRAPPERS-001"},
            {"id": "MANUAL:CHEATSHEETS-001"},
            {"id": "MANUAL:HEALTHCHECK-001"},
            {"id": "MANUAL:CHANGELOG-001"},
            {"id": "MANUAL:REGLAS-DE-ORO-001"},
            {"id": "MANUAL:FALLO-001"},
            {"id": "MANUAL:SLA-001"},
        ],
    },
    {
        "name": "CAREER CANON",
        "rows": [
            {"id": "CAREER_CANON:AUDIENCE-SCOPE"},
            {"id": "CANON:PROFILE-001"},
            {"id": "CANON:SKILLS-001"},
            {"id": "CANON:EXPERIENCE-001"},
            {
                "id": "CANON:EXPERIENCE-C01 … C05",
                "lookup_ids": [
                    "CANON:EXPERIENCE-C01",
                    "CANON:EXPERIENCE-C02",
                    "CANON:EXPERIENCE-C03",
                    "CANON:EXPERIENCE-C04",
                    "CANON:EXPERIENCE-C05",
                ],
            },
            {"id": "CANON:ACHIEVEMENTS-001"},
            {"id": "CANON:KPIS-001"},
            {
                "id": "CANON:KPI-001 … KPI-008",
                "lookup_ids": [
                    "CANON:KPI-001", "CANON:KPI-002", "CANON:KPI-003", "CANON:KPI-004",
                    "CANON:KPI-005", "CANON:KPI-006", "CANON:KPI-007", "CANON:KPI-008",
                ],
            },
            {"id": "CANON:FACTS-001"},
            {
                "id": "CANON:FACT-001 … FACT-008",
                "lookup_ids": [
                    "CANON:FACT-001", "CANON:FACT-002", "CANON:FACT-003", "CANON:FACT-004",
                    "CANON:FACT-005", "CANON:FACT-006", "CANON:FACT-007", "CANON:FACT-008",
                ],
            },
            {
                "id": "CANON:UF-001 … UF-003",
                "lookup_ids": ["CANON:UF-001", "CANON:UF-002", "CANON:UF-003"],
            },
            {"id": "CANON:POSITIONING-001"},
            {
                "id": "CANON:POSITIONING-N1 … N4",
                "lookup_ids": [
                    "CANON:POSITIONING-N1", "CANON:POSITIONING-N2",
                    "CANON:POSITIONING-N3", "CANON:POSITIONING-N4",
                ],
            },
            {"id": "CANON:OUTPUT-CONTRACT-001"},
            {"id": "CANON:OUTPUT-CONTRACT-SKELETON-001"},
            {"id": "CANON:OUTPUT-CONTRACT-TAGREGISTRY-001"},
        ],
    },
]

# ─── CAPA DE RED (engine de generator.py con rate-limit de generate_census.py) ─

def fetch_blocks(block_id: str) -> list:
    """Obtiene todos los bloques de un nivel con paginación y manejo de rate-limit."""
    blocks = []
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    cursor = None

    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor

        r = requests.get(url, headers=HEADERS, params=params)

        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 2))
            print(f"  [429] Rate limit. Esperando {wait}s...")
            time.sleep(wait)
            continue

        if r.status_code != 200:
            print(f"  [ERROR {r.status_code}] bloque {block_id}: {r.text[:120]}")
            break

        data = r.json()
        blocks.extend(data.get("results", []))

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    return blocks


def fetch_blocks_recursive(block_id: str) -> list:
    """Barre recursivamente todos los bloques hijos (engine de generator.py)."""
    result = []
    for block in fetch_blocks(block_id):
        result.append(block)
        if block.get("has_children") and block["type"] not in ("child_page", "child_database"):
            result.extend(fetch_blocks_recursive(block["id"]))
    return result

# ─── EXTRACCIÓN DE IDs (engine de generator.py, expandido a más block types) ──

def extract_ids_from_rich_text(rich_text: list) -> list:
    """Extrae todos los tokens que empiecen con un prefijo válido."""
    ids = []
    for segment in rich_text:
        text = segment.get("plain_text", "").strip()
        for token in text.split():
            clean = token.strip(".,;:()[]{}<>`'\"""''")
            if clean.startswith(VALID_PREFIXES):
                ids.append(clean)
    return ids


def is_definition_block(plain: str, id_str: str, btype: str) -> bool:
    """
    Determina si el bloque ES la definición del ID (heading o texto que arranca
    con el ID), vs. una mención de pasada.
    """
    stripped = plain.strip("` \n")
    return (
        stripped == id_str
        or stripped == f"ID: {id_str}"
        or f"ID: {id_str}" in plain
        or (btype in {"heading_1", "heading_2", "heading_3"}
            and plain.lstrip("` ").startswith(id_str))
    )


def extract_ids_from_block(block: dict) -> list:
    """
    Devuelve lista de (id_str, is_definition) para cada ID encontrado en el bloque.
    Cubre: headings, párrafos, listas, callouts, quotes, toggles, code, table_row.
    """
    btype = block["type"]
    found = []

    text_types = {
        "paragraph", "bulleted_list_item", "numbered_list_item",
        "callout", "quote", "toggle",
        "heading_1", "heading_2", "heading_3",
    }

    if btype in text_types:
        rich_text = block[btype].get("rich_text", [])
        plain = "".join(s.get("plain_text", "") for s in rich_text).strip()
        for id_str in extract_ids_from_rich_text(rich_text):
            found.append((id_str, is_definition_block(plain, id_str, btype)))

    elif btype == "code":
        rich_text = block["code"].get("rich_text", [])
        plain = "".join(s.get("plain_text", "") for s in rich_text).strip()
        for line in plain.splitlines():
            for id_str in extract_ids_from_rich_text([{"plain_text": line}]):
                is_def = line.strip().strip("`") == id_str
                found.append((id_str, is_def))

    elif btype == "table_row":
        cells = block["table_row"].get("cells", [])
        for cell in cells:
            cell_plain = "".join(s.get("plain_text", "") for s in cell).strip()
            for id_str in extract_ids_from_rich_text(cell):
                is_def = cell_plain.strip("` \n") == id_str or f"ID: {id_str}" in cell_plain
                found.append((id_str, is_def))

    return found

# ─── CONSTRUCCIÓN DEL ÍNDICE ───────────────────────────────────────────────────

def build_link_index() -> dict:
    """
    Barre todos los documentos y construye un índice:
      id_str -> list of { doc, link, is_def }
    """
    link_index = {}

    for doc_name, page_id in DOCUMENTS.items():
        print(f"Indexando: {doc_name}...")
        blocks = fetch_blocks_recursive(page_id)
        page_id_clean = page_id.replace("-", "")

        for block in blocks:
            block_id_clean = block["id"].replace("-", "")
            link = f"https://app.notion.com/p/{page_id_clean}#{block_id_clean}"

            for id_str, is_def in extract_ids_from_block(block):
                link_index.setdefault(id_str, []).append({
                    "doc":    doc_name,
                    "link":   link,
                    "is_def": is_def,
                })

    return link_index


def pick_best_link(entries: list) -> dict | None:
    """
    Selecciona el mejor candidato priorizando:
      1. Bloques de definición (is_def=True) sobre menciones
      2. Documento de mayor prioridad (menor número en DOC_PRIORITY)
    """
    if not entries:
        return None

    defs = [e for e in entries if e["is_def"]]
    pool = defs if defs else entries

    return min(pool, key=lambda e: (DOC_PRIORITY.get(e["doc"], 999), e["link"]))


def resolve_link(row: dict, link_index: dict) -> str | None:
    """Resuelve el mejor link para una fila del CENSUS_SPEC."""
    lookup_ids = row.get("lookup_ids") or [row["id"]]
    candidates = []
    for lid in lookup_ids:
        candidates.extend(link_index.get(lid, []))
    best = pick_best_link(candidates)
    return best["link"] if best else None

# ─── DETECCIÓN DE HUÉRFANOS (KERNEL:CENSUS-SYNC, Regla 2) ─────────────────────

def known_ids_from_spec() -> set:
    """
    Aplana CENSUS_SPEC a un set de todos los IDs "conocidos" (tanto el
    id declarado como cualquier lookup_id asociado), para poder comparar
    contra lo que realmente se encontró en los documentos.
    """
    known = set()
    for section in CENSUS_SPEC:
        for row in section["rows"]:
            known.add(row["id"])
            for lid in row.get("lookup_ids", []):
                known.add(lid)
    return known


def find_orphan_ids(link_index: dict, known_ids: set) -> dict:
    """
    Detecta IDs encontrados en los documentos (con al menos un bloque de
    definición, is_def=True) que NO están declarados en CENSUS_SPEC.

    Solo se consideran definiciones, no menciones sueltas, para evitar
    falsos positivos de cross-references (ej. "ver KERNEL:X en el Kernel").

    Devuelve: id_str -> mejor entry (doc, link) para reportarlo, ordenado
    por prefijo y nombre para lectura consistente.
    """
    orphans = {}
    for id_str, entries in link_index.items():
        if id_str in known_ids:
            continue
        def_entries = [e for e in entries if e["is_def"]]
        if not def_entries:
            continue  # solo mención de pasada, no es una definición nueva
        orphans[id_str] = pick_best_link(def_entries)

    return dict(sorted(orphans.items()))

# ─── RENDER ────────────────────────────────────────────────────────────────────

def render_markdown(link_index: dict, orphans: dict) -> tuple:
    lines = []
    unresolved = []

    for section in CENSUS_SPEC:
        lines += [f"### {section['name']}", "", "| ID |", "|---|"]
        for row in section["rows"]:
            link = resolve_link(row, link_index)
            display_id = row["id"]
            if link:
                cell = f"[`{display_id}`]( {link} )"
            else:
                cell = f"`{display_id}`"
                unresolved.append(display_id)
            lines.append(f"| {cell} |")
        lines.append("")

    # Sección de huérfanos — siempre se imprime, incluso vacía, para que
    # quede explícito en el artefacto que la detección corrió (Regla 2:
    # "no ignorar silenciosamente IDs nuevos").
    lines += ["### IDs Huérfanos (fuera de CENSUS_SPEC)", ""]
    if orphans:
        lines += ["| ID | Documento | Link |", "|---|---|---|"]
        for id_str, entry in orphans.items():
            lines.append(f"| `{id_str}` | {entry['doc']} | [link]( {entry['link']} ) |")
    else:
        lines.append("_Ninguno detectado en esta corrida._")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n", unresolved

# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\nV-ID-CENSUS Generator v3.0")
    print(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 52)

    link_index = build_link_index()
    known_ids = known_ids_from_spec()
    orphans = find_orphan_ids(link_index, known_ids)
    md, unresolved = render_markdown(link_index, orphans)

    output = Path("V_ID_CENSUS_PRODUCTION.md")
    output.write_text(md, encoding="utf-8")

    total = sum(len(s["rows"]) for s in CENSUS_SPEC)
    print("\n" + "=" * 52)
    print(f"  IDs en spec:          {total}")
    print(f"  IDs resueltos:        {total - len(unresolved)}")
    print(f"  IDs SIN link:         {len(unresolved)}")
    if unresolved:
        print("  Sin resolver:")
        for uid in unresolved:
            print(f"    - {uid}")
    print("-" * 52)
    print(f"  IDs huérfanos (en docs, fuera de spec): {len(orphans)}")
    if orphans:
        print("  ⚠ Huérfanos detectados — agregar a CENSUS_SPEC o confirmar que son ruido:")
        for uid, entry in orphans.items():
            print(f"    - {uid}  ({entry['doc']})")
    print("=" * 52)
    print(f"\nExportado a: {output.resolve()}")
