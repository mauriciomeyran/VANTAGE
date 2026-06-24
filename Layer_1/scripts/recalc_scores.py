#!/usr/bin/env python3
"""
VANTAGE Score Recalculation (v6.4)
Recalculates all scores using v6.4 (0-100 scale) and writes to Notion.
This replaces the deprecated scoring_deterministic.py (2-8 scale).

Usage: python3 scripts/recalc_scores.py [--dry-run]
"""

import os
import sys
import pathlib
import argparse

# Set up venv path first
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / ".venv" / "lib" / "python3.14" / "site-packages"))

from dotenv import load_dotenv
from notion_client import Client

# Import v6.4 scoring functions from layer_1_run.py
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from layer_1_run import calculate_score_v6, get_match_level_v6, score_to_prioridad, get_vm_scope, get_role_class

VANTAGE_DATA_SOURCE_ID = "442938be-fc42-828f-b72e-076818d65a5b"

def txt(prop):
    """Extract plain text from Notion property"""
    if not prop: return ""
    t = prop.get("type")
    if t == "url": return prop.get("url") or ""
    if t == "rich_text" and prop.get("rich_text"):
        return prop["rich_text"][0]["plain_text"]
    if t == "select" and prop.get("select"):
        return prop["select"]["name"]
    if t == "title" and prop.get("title"):
        return prop["title"][0]["plain_text"]
    if t == "number": return prop.get("number")
    if t == "date" and prop.get("date"):
        return prop["date"]["start"]
    return ""

def is_active_status(status):
    """Returns True if status is not terminal/archived"""
    terminal_statuses = {"Expirada", "Rechazado", "Archivar", "Retirado"}
    return status not in terminal_statuses

def main():
    parser = argparse.ArgumentParser(description="VANTAGE Score Recalculation (v6.4)")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing to Notion")
    args = parser.parse_args()

    # Find .env file in project root (Layer_1/../.env)
    script_dir = pathlib.Path(__file__).resolve().parent
    project_root = script_dir.parent
    env_file = project_root / ".env"
    
    if not env_file.exists():
        # Try alternate location
        env_file = project_root.parent / ".env"
    
    load_dotenv(dotenv_path=env_file, override=True)
    
    if "NOTION_TOKEN" not in os.environ:
        print(f"❌ ERROR: NOTION_TOKEN not found in environment")
        print(f"   Looking for .env at: {env_file}")
        print(f"   .env exists: {env_file.exists()}")
        sys.exit(1)
    
    client = Client(auth=os.environ["NOTION_TOKEN"])

    print("🔄 VANTAGE Score Recalculation (v6.4)")
    print("=" * 70)
    print(f"Data Source ID: {VANTAGE_DATA_SOURCE_ID}")
    print(f"Mode: {'DRY-RUN (no writes)' if args.dry_run else 'LIVE (will write to Notion)'}")
    print()

    # Query all entries
    print("Fetching entries from VANTAGE_TRACKER...")
    all_items = []
    payload = {}
    
    # Use data_sources.query if available, otherwise use direct request
    if hasattr(client, "data_sources"):
        while True:
            response = client.data_sources.query(data_source_id=VANTAGE_DATA_SOURCE_ID, **payload)
            all_items.extend(response.get("results", []))
            if not response.get("has_more"):
                break
            payload["start_cursor"] = response["next_cursor"]
    else:
        # Fallback to direct request
        url = f"https://api.notion.com/v1/data_sources/{VANTAGE_DATA_SOURCE_ID}/query"
        headers = {
            "Authorization": f"Bearer {os.environ['NOTION_TOKEN']}",
            "Notion-Version": "2025-09-03",
            "Content-Type": "application/json"
        }
        import requests
        while True:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            all_items.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            payload["start_cursor"] = data["next_cursor"]

    print(f"Total entries: {len(all_items)}")
    print()

    # Filter active entries
    active_items = [item for item in all_items if is_active_status(txt(item["properties"].get("Status")))]
    print(f"Active entries (non-terminal): {len(active_items)}")
    print()

    # Analyze and apply changes
    changes = []
    unchanged = []
    errors = []

    for item in active_items:
        props = item["properties"]
        page_id = item["id"]
        
        try:
            # Current values
            current_score = props.get("Score", {}).get("number")
            current_match = txt(props.get("Match"))
            current_vm_scope = txt(props.get("VM_Scope"))
            current_role_class = txt(props.get("Role_Class"))
            current_prioridad = txt(props.get("Prioridad"))
            
            # Input fields
            rol = txt(props.get("Rol"))
            marca = txt(props.get("Marca"))
            jd = txt(props.get("JD"))
            company = marca  # Use marca as company
            title = rol  # Use rol as title
            contact = txt(props.get("Contacto"))
            
            # Calculate new values using v6.4
            entry = {
                "jd": jd,
                "company": company,
                "title": title,
                "contact": contact
            }
            
            new_score = calculate_score_v6(entry)
            new_match = get_match_level_v6(new_score)
            new_vm_scope = get_vm_scope(rol)
            new_role_class = get_role_class(rol)
            new_prioridad = score_to_prioridad(new_score)
            
            # Check if anything changed
            has_change = (
                current_score != new_score or
                current_match != new_match or
                current_vm_scope != new_vm_scope or
                current_role_class != new_role_class or
                current_prioridad != new_prioridad
            )
            
            if has_change:
                changes.append({
                    "page_id": page_id,
                    "rol": rol,
                    "marca": marca,
                    "current": {
                        "score": current_score,
                        "match": current_match,
                        "vm_scope": current_vm_scope,
                        "role_class": current_role_class,
                        "prioridad": current_prioridad
                    },
                    "new": {
                        "score": new_score,
                        "match": new_match,
                        "vm_scope": new_vm_scope,
                        "role_class": new_role_class,
                        "prioridad": new_prioridad
                    }
                })
                
                # Apply changes if not dry-run
                if not args.dry_run:
                    update_props = {}
                    
                    if current_score != new_score:
                        update_props["Score"] = {"number": new_score}
                    
                    if current_match != new_match:
                        update_props["Match"] = {"select": {"name": new_match}}
                    
                    if current_vm_scope != new_vm_scope:
                        update_props["VM_Scope"] = {"select": {"name": new_vm_scope}}
                    
                    if current_role_class != new_role_class:
                        update_props["Role_Class"] = {"select": {"name": new_role_class}}
                    
                    if current_prioridad != new_prioridad:
                        update_props["Prioridad"] = {"select": {"name": new_prioridad}}
                    
                    if update_props:
                        try:
                            client.pages.update(page_id=page_id, properties=update_props)
                            print(f"✅ Updated: {rol} @ {marca}")
                        except Exception as e:
                            errors.append({
                                "page_id": page_id,
                                "rol": rol,
                                "error": str(e)
                            })
                            print(f"❌ Error updating {rol}: {e}")
            else:
                unchanged.append({
                    "page_id": page_id,
                    "rol": rol
                })
                
        except Exception as e:
            errors.append({
                "page_id": page_id,
                "rol": txt(props.get("Rol")),
                "error": str(e)
            })

    # Print results
    print(f"📊 RESULTS")
    print("=" * 70)
    print(f"Entries with changes: {len(changes)}")
    print(f"Entries unchanged: {len(unchanged)}")
    print(f"Errors: {len(errors)}")
    print()

    if args.dry_run and changes:
        print(f"📝 CHANGES (showing first 20)")
        print("-" * 70)
        for i, change in enumerate(changes[:20]):
            print(f"\n[{i+1}] {change['rol']} @ {change['marca']}")
            print(f"    ID: {change['page_id'][:8]}...")
            print(f"    Score: {change['current']['score']} → {change['new']['score']}")
            print(f"    Match: {change['current']['match']} → {change['new']['match']}")
            print(f"    VM_Scope: {change['current']['vm_scope']} → {change['new']['vm_scope']}")
            print(f"    Role_Class: {change['current']['role_class']} → {change['new']['role_class']}")
            print(f"    Prioridad: {change['current']['prioridad']} → {change['new']['prioridad']}")
        
        if len(changes) > 20:
            print(f"\n... and {len(changes) - 20} more changes")
    
    if errors:
        print(f"\n❌ ERRORS")
        print("-" * 70)
        for error in errors[:10]:
            print(f"    {error['rol']} ({error['page_id'][:8]}...): {error['error']}")
        if len(errors) > 10:
            print(f"    ... and {len(errors) - 10} more errors")

    print()
    print("=" * 70)
    if args.dry_run:
        print("✅ Dry-run complete. No changes were written to Notion.")
        print("   Run without --dry-run to apply these changes.")
    else:
        print(f"✅ Recalculation complete. {len(changes)} entries updated.")
        print(f"   {len(errors)} errors encountered.")

if __name__ == "__main__":
    main()
