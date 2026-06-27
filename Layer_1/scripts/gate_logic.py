import os
from dotenv import load_dotenv
from notion_utils import Client

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

def gate_logic(entry):
    """
    Determine the next action based on entry status and current action.
    Implements terminal state protection where manual human intent overrides automation.
    """
    # Terminal states that should never be overwritten
    TERMINAL_ACTIONS = {"Archivar", "Expirada"}
    
    # Check if current action is already a terminal state
    current_action = entry.get("Next_Action", "")
    if current_action in TERMINAL_ACTIONS:
        # Terminal state protection: respect manual human intent
        return current_action
    
    # Original gate logic (only runs if not in terminal state)
    status = entry.get("Status", "")
    gate_decision = entry.get("Gate_Decision", "")
    
    # APPLIED override
    if gate_decision == "APPLIED":
        if status == "Postulado": 
            return "Follow-up"
        elif status == "En proceso": 
            return "Interview prep"
        elif status == "Negociando": 
            return "Follow-up"
        elif status == "Sin respuesta": 
            return "Follow-up"
    
    # CREATE logic
    elif gate_decision == "CREATE":
        if status == "Postulado":
            return "Follow-up"
        return "Re-check"
    
    # BLOCKED logic with terminal state protection
    elif gate_decision == "BLOCKED":
        fetch = entry.get("Fetch", "")
        if fetch == "Bloqueado":
            return "Reparar URL"
        elif fetch == "Parcial":
            return "Verificar JD"
        else:
            # This is where the conflict was - now respects terminal states
            return "Archivar"
    
    # Default fallback
    return "Archivar"

def evaluate_gate(fetch, vm_scope, role_class):
    """Evalúa la regla del gate"""
    if fetch == "Accesible" and (vm_scope == "Alto" or role_class == "Pivote"):
        return "CREATE"
    return "BLOCKED"

if __name__ == "__main__":
    load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
    client = Client(auth=os.environ["NOTION_TOKEN"])
    ds_id = "4e542b37-6e52-4418-89b7-a0eeb3138307"

    print("Evaluando Gate Logic con Protección de Estados Terminales...")
    print("=" * 60)
    
    items = client.data_sources.query(data_source_id=ds_id)["results"]
    
    create_count = 0
    blocked_count = 0
    terminal_protected = 0
    
    for item in items:
        props = item["properties"]
        
        # Extraer propiedades
        rol = txt(props.get("Rol"))
        marca = txt(props.get("Marca"))
        fetch = txt(props.get("Fetch"))
        vm_scope = txt(props.get("VM_Scope"))
        role_class = txt(props.get("Role_Class"))
        status = txt(props.get("Status"))
        source_type = txt(props.get("Source_Type "))
        current_action = txt(props.get("Next_Action"))
        
        # Crear entry para gate_logic
        entry = {
            "Next_Action": current_action,
            "Status": status,
            "Gate_Decision": "",
            "Fetch": fetch
        }
        
        # Evaluar gate decision (solo para Vacante)
        if source_type == "Vacante":
            gate_decision = evaluate_gate(fetch, vm_scope, role_class)
        else:
            gate_decision = "CREATE"  # Bypass para otros tipos
        
        entry["Gate_Decision"] = gate_decision
        
        # Aplicar gate logic con protección terminal
        new_action = gate_logic(entry)
        
        # Contar resultados
        # Warning: Status=Postulado pero Gate_Decision no es APPLIED
        if status == "Postulado" and gate_decision != "APPLIED":
            print(f"⚠️  DESAJUSTE | {rol} @ {marca}")
            print(f"   Status=Postulado pero Gate_Decision={gate_decision} — actualizar manualmente en Notion")
            print()

        if current_action in {"Archivar", "Expirada"}:
            terminal_protected += 1
            print(f"🛡️  PROTEGIDO | {rol} @ {marca}")
            print(f"   Estado terminal: {current_action} → NO SE MODIFICA")
        elif gate_decision == "CREATE":
            create_count += 1
            print(f"✅ CREATE | {rol} @ {marca}")
            print(f"   Acción: {current_action} → {new_action}")
        else:
            blocked_count += 1
            print(f"❌ BLOCKED | {rol} @ {marca}")
            print(f"   Acción: {current_action} → {new_action}")
        
        print(f"   Fetch={fetch}, VM_Scope={vm_scope}, Role_Class={role_class}")
        print()
    
    print("=" * 60)
    print(f"📊 RESULTADOS:")
    print(f"  ✅ CREATE:           {create_count}")
    print(f"  ❌ BLOCKED:          {blocked_count}")
    print(f"  🛡️  PROTEGIDOS:       {terminal_protected}")
    print(f"  📋 TOTAL:            {len(items)}")
    print()
    print("💡 Estados terminales 'Archivar' y 'Expirada' NO se modifican.")