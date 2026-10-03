#!/usr/bin/env python3
"""
vdoc_local_contingency.py — Contingencia aislada local → Notion (fuera del CLI vdoc)
====================================================================================
Herramienta de emergencia para empujar UN SOLO documento desde
`Documentación/ACTIVE/` hacia Notion cuando sea estrictamente necesario.
Queda fuera de `vdoc` y `vsync_doc --direction` para impedir escrituras
accidentales local→Notion durante la operación normal (Notion es SSOT y
`ACTIVE/` es read-only).

Salvaguardas obligatorias:
  1. Un solo documento por corrida (`--doc <doc>` o `<doc>` posicional; nunca
     opera en lote sobre todos los documentos).
  2. Guarda del Charter: `project_charter` / `charter` está bloqueado siempre
     (requiere ticket Task Tracker tipo CHARTER evaluado por CLAUDE/MAIN).
  3. Confirmación explícita: exige escribir exactamente `FORZAR` en terminal
     interactiva antes de tocar Notion.
  4. Backup previo obligatorio: descarga el estado vivo de Notion en
     `Layer_4/backups/<doc>_<YYYYMMDD_HHMMSS>.md` antes de aplicar PATCH. Si el
     backup falla, aborta sin escribir nada.

Uso:
    python3 Layer_4/scripts/vdoc_local_contingency.py --doc kernel --dry-run
    python3 Layer_4/scripts/vdoc_local_contingency.py --doc kernel
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT = SCRIPT_DIR.parents[1]
BACKUP_DIR = PROJECT / "Layer_4" / "backups"

sys.path.insert(0, str(SCRIPT_DIR))
import vsync_doc  # noqa: E402

DOC_ALIASES = {
    "charter": "project_charter",
    "Navigation_Brief": "brief",
}
VALID_DOC_KEYS = set(vsync_doc.DOCS.keys()) | set(DOC_ALIASES.keys())


def _parse_args(argv: list[str]) -> tuple[str | None, bool, str | None]:
    """Devuelve `(doc_key_canonico, dry_run, error_msg)`."""
    if any(a in ("-h", "--help") for a in argv):
        return None, False, "HELP"

    dry_run = False
    docs_found: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--dry-run", "dry"):
            dry_run = True
            i += 1
        elif arg == "--doc":
            if i + 1 >= len(argv):
                return None, dry_run, "Falta el nombre del documento después de --doc."
            docs_found.append(argv[i + 1])
            i += 2
        elif arg.startswith("--doc="):
            docs_found.append(arg.split("=", 1)[1])
            i += 1
        elif arg.startswith("-"):
            return None, dry_run, f"Flag no reconocido: '{arg}'"
        else:
            docs_found.append(arg)
            i += 1

    if len(docs_found) == 0:
        return (
            None,
            dry_run,
            "Debes especificar exactamente UN documento (--doc <doc>). "
            "Esta herramienta no permite sincronización masiva.",
        )
    if len(docs_found) > 1:
        return (
            None,
            dry_run,
            f"Solo se permite UN documento por corrida; recibidos: {docs_found}",
        )

    raw_doc = docs_found[0]
    if raw_doc not in VALID_DOC_KEYS:
        return (
            None,
            dry_run,
            f"Documento no reconocido: '{raw_doc}'. Opciones válidas: {sorted(vsync_doc.DOCS.keys())}",
        )

    canonical_doc = DOC_ALIASES.get(raw_doc, raw_doc)
    return canonical_doc, dry_run, None


def create_pre_write_backup(doc_key: str, notion_id: str, backup_dir: Path | None = None) -> Path | None:
    """Descarga el contenido actual de Notion y lo guarda en `Layer_4/backups/`."""
    target_dir = backup_dir if backup_dir is not None else BACKUP_DIR
    try:
        notion_md, _ = vsync_doc.fetch_notion_as_md(notion_id)
    except Exception as e:
        print(f"  ✗ Error al obtener snapshot de Notion para backup previo: {e}")
        return None

    if notion_md is None:
        print("  ✗ No se pudo descargar el estado actual de Notion; se aborta sin escribir.")
        return None

    target_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = target_dir / f"{doc_key}_{ts}.md"
    backup_path.write_text(notion_md, encoding="utf-8")
    return backup_path


def main(argv: list[str] | None = None) -> int:
    raw_args = sys.argv[1:] if argv is None else list(argv)
    doc_key, dry_run, err = _parse_args(raw_args)

    if err == "HELP":
        print(__doc__)
        return 0
    if err is not None:
        print(f"✗ {err}")
        return 1

    assert doc_key is not None
    if doc_key == "project_charter":
        print(
            "BLOCKED: el Charter no acepta escritura directa vía "
            "vdoc_local_contingency. Todo cambio al Charter requiere "
            "ticket Task Tracker tipo CHARTER, evaluado por CLAUDE/MAIN "
            "(ver SP:BOOTLOADER-002/004)."
        )
        return 1

    doc_info = vsync_doc.DOCS[doc_key]
    local_file: Path = doc_info["local_file"]
    notion_id: str = doc_info["notion_id"]
    label: str = doc_info["label"]

    if not local_file.exists():
        print(f"✗ No existe el archivo local: {local_file}")
        return 1

    if dry_run:
        print(f"  · {label:<30} [DRY] contingencia local→notion (sin cambios aplicados)")
        return 0

    print(f"\n⚠️  CONTINGENCIA LOCAL → NOTION para un solo documento: {label} ({doc_key})")
    print("   Notion es la única fuente de verdad; esta operación sobrescribe bloques en Notion.")
    print("   Se creará primero un backup en Layer_4/backups/ antes de aplicar PATCH.")
    try:
        confirm = input("   Escribe exactamente FORZAR para continuar: ").strip()
    except EOFError:
        print("\n   Sin entrada interactiva disponible — cancelado por seguridad.")
        return 0

    if confirm != "FORZAR":
        print("   Cancelado. No se escribió nada.")
        return 0

    backup_path = create_pre_write_backup(doc_key, notion_id)
    if backup_path is None:
        return 1
    print(f"  ✓ Backup previo guardado en: {backup_path}")

    original_mode = vsync_doc._make_writable(local_file)
    try:
        result = vsync_doc.push_local_to_notion(notion_id, local_file)
    finally:
        vsync_doc._restore_permissions(local_file, original_mode)

    if result["failed"] > 0 or result["tables_skipped"] > 0:
        print(
            f"  ✗ {label:<30} {result['failed']} bloque(s) fallaron, "
            f"{result['tables_skipped']} tabla(s) sin sincronizar — manifest NO actualizado"
        )
        return 1

    manifest = vsync_doc._load_manifest()
    manifest[doc_key] = vsync_doc._hash(local_file.read_text(encoding="utf-8"))
    vsync_doc._save_manifest(manifest)
    print(f"  ✓ {label:<30} local→notion completado (contingencia)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
