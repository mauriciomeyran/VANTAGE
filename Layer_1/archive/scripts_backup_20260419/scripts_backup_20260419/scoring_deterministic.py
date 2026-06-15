import os
import re
from dotenv import load_dotenv
from notion_client import Client

def txt(prop):
    if not prop: return ""
    t = prop.get("type")
    if t == "rich_text" and prop.get("rich_text"): 
        return prop["rich_text"][0]["plain_text"]
    if t == "select" and prop.get("select"): 
        return prop["select"]["name"]
    if t == "title" and prop.get("title"): 
        return prop["title"][0]["plain_text"]
    return ""

def get_vm_scope(role_title):
    """Determina VM_Scope basado en el título del rol"""
    if not role_title:
        return ""
    
    role_lower = role_title.lower()
    
    # Términos que indican VM alto
    vm_terms = ["visual merchandising", "visual", "vm", "brand environment", "estándares visuales"]
    
    for term in vm_terms:
        if term in role_lower:
            return "Alto"
    
    # Si no tiene términos VM directos, es bajo
    return "Bajo"

def get_role_class(role_title):
    """Determina Role_Class"""
    if not role_title:
        return ""
    
    role_lower = role_title.lower()
    
    # Roles VM puros
    vm_terms = ["visual merchandising", "visual", "vm", "brand environment"]
    for term in vm_terms:
        if term in role_lower:
            return "VM"
    
    # Roles pivote
    pivot_terms = ["training", "experience", "producer", "account", "project", "commercial"]
    for term in pivot_terms:
        if term in role_lower:
            return "Pivote"
    
    return "Otro"

def calculate_score(vm_scope, role_class):
    """Calcula score final (1-10)"""
    
    if vm_scope == "Alto" and role_class == "VM":
        return 8
    elif vm_scope == "Alto" and role_class == "Pivote":
        return 6
    elif vm_scope == "Bajo" and role_class == "VM":
        return 5
    elif vm_scope == "Bajo" and role_class == "Pivote":
        return 3
    else:
        return 2

def get_match_level(score):
    """Convierte score a Match level"""
    if score >= 8:
        return "Muy Alto"
    elif score >= 6:
        return "Alto"
    elif score >= 4:
        return "Medio"
    else:
        return "Bajo"

if __name__ == "__main__":
    load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
    client = Client(auth=os.environ["NOTION_TOKEN"])
    ds_id = "4e542b37-6e52-4418-89b7-a0eeb3138307"

    print("Aplicando scoring determinístico...")
    
    items = client.data_sources.query(data_source_id=ds_id)["results"]
    
    updates_count = 0
    
    for item in items:
        props = item["properties"]
        
        rol = txt(props.get("Rol"))
        current_vm_scope = txt(props.get("VM_Scope"))
        current_score = props.get("Score", {}).get("number")
        
        # Calcular nuevos valores
        new_vm_scope = get_vm_scope(rol)
        new_role_class = get_role_class(rol)
        new_score = calculate_score(new_vm_scope, new_role_class)
        new_match = get_match_level(new_score)
        
        # Solo actualizar si hay cambios
        needs_update = False
        update_props = {}
        
        if current_vm_scope != new_vm_scope:
            update_props["VM_Scope"] = {"select": {"name": new_vm_scope}}
            needs_update = True
        
        if current_score != new_score:
            update_props["Score"] = {"number": new_score}
            needs_update = True
        
        # Siempre actualizar Match y Role_Class para consistencia
        update_props["Match"] = {"select": {"name": new_match}}
        update_props["Role_Class"] = {"select": {"name": new_role_class}}
        needs_update = True
        
        if needs_update:
            try:
                client.pages.update(page_id=item["id"], properties=update_props)
                updates_count += 1
                print(f"✅ [{item['id'][:8]}] {rol} | VM_Scope: {new_vm_scope} | Score: {new_score} | Match: {new_match}")
            except Exception as e:
                print(f"❌ Error updating {item['id'][:8]}: {e}")
    
    print(f"\n✅ Scoring completado. {updates_count} entradas actualizadas.")