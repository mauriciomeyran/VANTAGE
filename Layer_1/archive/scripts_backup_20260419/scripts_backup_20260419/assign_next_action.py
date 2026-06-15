import os
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

def evaluate_application_status(status):
    """Check if status indicates an active application"""
    return status in {"Postulado", "En proceso", "Negociando", "Sin respuesta"}

def gate_logic_complete(source_type, status, fetch, vm_scope, role_class):
    """
    Complete gate logic from kernel (8c)
    """
    # 1. Bypass for non-vacante
    if source_type in ["Inbound", "Referencia", "Networking"]:
        return "CREATE"  # Bypass automático
    
    # 2. Applied override for active applications
    elif evaluate_application_status(status):
        return "APPLIED"  # Override para aplicaciones activas
    
    # 3. Vacante logic
    elif source_type == "Vacante":
        if fetch == "Accesible" and (vm_scope == "Alto" or role_class == "Pivote"):
            return "CREATE"
    
    # Default
    return "BLOCKED"

def next_action_from_gate(gate_decision, status, fetch, current_action):
    """
    Next Action assignment from kernel (8c) with protection
    """
    # Protection: Manual actions and terminal states
    AUTO_ACTIONS = {"Re-check", "Reparar URL", "Verificar JD"}  # REMOVED "Archivar"
    TERMINAL_ACTIONS = {"Archivar", "Expirada"}
    
    # CRITICAL FIX: Protect terminal states FIRST
    if current_action and current_action in TERMINAL_ACTIONS:
        return current_action  # Respect manual terminal intent
    
    # Protection for manual actions (not auto-generated)
    if current_action and current_action not in AUTO_ACTIONS:
        return current_action  # Respect manual intent
    
    # Kernel logic (only runs if not protected above)
    if gate_decision == "APPLIED":
        if status == "Postulado": 
            return "Follow-up"
        elif status == "En proceso": 
            return "Interview prep"
        elif status == "Negociando": 
            return "Follow-up"
        elif status == "Sin respuesta": 
            return "Follow-up"
    
    elif gate_decision == "CREATE":
        return "Re-check"
    
    elif gate_decision == "BLOCKED":
        if fetch == "Bloqueado":
            return "Reparar URL"
        elif fetch == "Parcial":
            return "Verificar JD"
        else:
            return "Archivar"
    
    # Default
    return "Archivar"

if __name__ == "__main__":
    load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
    client = Client(auth=os.environ["NOTION_TOKEN"])
    ds_id = "4e542b37-6e52-4418-89b7-a0eeb3138307"

    items = client.data_sources.query(data_source_id=ds_id)["results"]
    
    manual_protected = 0
    terminal_protected = 0
    updated = 0
    skipped = 0
    
    for item in items:
        props = item["properties"]
        
        # Get current values
        current_action = txt(props.get("Next_Action"))
        status = txt(props.get("Status"))
        fetch = txt(props.get("Fetch"))
        vm_scope = txt(props.get("VM_Scope"))
        role_class = txt(props.get("Role_Class"))
        source_type = txt(props.get("Source_Type"))
        
        # TERMINAL STATE PROTECTION - CHECK FIRST
        if current_action in {"Archivar", "Expirada"}:
            terminal_protected += 1
            print(f"🛡️  [{item['id'][:8]}] PROTEGIDO (Terminal): '{current_action}' → NO SE MODIFICA")
            continue
        
        # Complete gate logic from kernel
        gate_decision = gate_logic_complete(source_type, status, fetch, vm_scope, role_class)
        
        # Calculate next action with protection
        new_action = next_action_from_gate(gate_decision, status, fetch, current_action)
        
        # Protection for manual actions (not auto-generated)
        AUTO_ACTIONS = {"Re-check", "Reparar URL", "Verificar JD"}  # REMOVED "Archivar"
        if current_action and current_action not in AUTO_ACTIONS:
            manual_protected += 1
            print(f"🛡️  [{item['id'][:8]}] PROTEGIDO (Manual): '{current_action}' → NO SE MODIFICA")
            continue
        
        # Only update if action changed
        if new_action == current_action:
            skipped += 1
            continue
        
        # Prepare update for Notion
        update = {
            "Gate_Decision": {"select": {"name": gate_decision}},
            "Next_Action": {"select": {"name": new_action}}
        }
        
        try:
            client.pages.update(page_id=item["id"], properties=update)
            updated += 1
            print(f"✅ [{item['id'][:8]}] {gate_decision}: '{current_action}' → '{new_action}'")
        except Exception as e:
            print(f"❌ [{item['id'][:8]}] Error: {e}")
    
    print(f"\n📊 RESUMEN:")
    print(f"  ✅ Actualizados: {updated}")
    print(f"  ⏭️  Saltados (sin cambios): {skipped}")
    print(f"  🛡️  Protegidos (manuales): {manual_protected}")
    print(f"  🛡️  Protegidos (terminales): {terminal_protected}")
    print(f"  📋 Total procesados: {len(items)}")
    print(f"\n💡 LÓGICA DEL KERNEL IMPLEMENTADA:")
    print(f"   • Source_Type bypass: Inbound/Referencia/Networking → CREATE")
    print(f"   • Status APPLIED: Postulado/En proceso/Negociando/Sin respuesta → APPLIED")
    print(f"   • Vacante: CREATE si Fetch=Accesible AND (VM_Scope=Alto OR Role_Class=Pivote)")
    print(f"   • PROTECCIÓN MEJORADA: 'Archivar' y 'Expirada' son estados terminales que NO se modifican")