#!/usr/bin/env python3
"""
JHS Pipeline Recovery - Manejo de fallos y resume operations
"""

import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client

def save_checkpoint(step, data):
    """Save pipeline checkpoint"""
    checkpoint = {
        "timestamp": datetime.now().isoformat(),
        "step": step,
        "data": data
    }
    
    os.makedirs("out", exist_ok=True)
    with open("out/pipeline_checkpoint.json", "w") as f:
        json.dump(checkpoint, f, indent=2)

def load_checkpoint():
    """Load last pipeline checkpoint"""
    try:
        with open("out/pipeline_checkpoint.json", "r") as f:
            return json.load(f)
    except:
        return None

def clear_checkpoint():
    """Clear checkpoint after successful completion"""
    try:
        os.remove("out/pipeline_checkpoint.json")
    except:
        pass

def safe_execute_step(step_name, step_function, *args, **kwargs):
    """Execute a step with error handling and checkpointing"""
    print(f"🔄 Ejecutando: {step_name}...")
    
    try:
        result = step_function(*args, **kwargs)
        save_checkpoint(step_name, {"status": "completed", "result": result})
        print(f"✅ {step_name} completado")
        return result
    except Exception as e:
        error_data = {"status": "failed", "error": str(e), "timestamp": datetime.now().isoformat()}
        save_checkpoint(step_name, error_data)
        print(f"❌ {step_name} falló: {e}")
        raise

def resume_pipeline():
    """Resume pipeline from last checkpoint"""
    checkpoint = load_checkpoint()
    
    if not checkpoint:
        print("ℹ️  No hay checkpoint previo. Ejecutando pipeline completo.")
        return False
    
    print(f"🔍 Checkpoint encontrado: {checkpoint['step']}")
    print(f"🗓️  Timestamp: {checkpoint['timestamp']}")
    
    if checkpoint['data'].get('status') == 'completed':
        print(f"✅ Último paso completado exitosamente")
        return False  # Continue normal execution
    elif checkpoint['data'].get('status') == 'failed':
        print(f"❌ Pipeline falló en: {checkpoint['step']}")
        print(f"Error: {checkpoint['data'].get('error', 'Unknown')}")
        
        retry = input("¿Reintentar desde el paso fallido? (y/N): ").lower().strip()
        if retry == 'y':
            return checkpoint['step']  # Return step to retry
        else:
            clear_checkpoint()
            return False
    
    return False

def verify_data_consistency():
    """Verify data consistency after pipeline operations"""
    try:
        load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
        client = Client(auth=os.environ["NOTION_TOKEN"])
        ds_id = "4e542b37-6e52-4418-89b7-a0eeb3138307"
        
        print("🔍 Verificando consistencia de datos...")
        
        items = client.data_sources.query(data_source_id=ds_id)["results"]
        
        issues = []
        
        for item in items:
            props = item["properties"]
            
            # Check for missing critical fields
            if not props.get("Score", {}).get("number"):
                issues.append(f"[{item['id'][:8]}] Sin Score")
            
            if not props.get("VM_Scope", {}).get("select", {}).get("name"):
                issues.append(f"[{item['id'][:8]}] Sin VM_Scope")
                
            if not props.get("Gate_Decision", {}).get("select", {}).get("name"):
                issues.append(f"[{item['id'][:8]}] Sin Gate_Decision")
        
        if issues:
            print(f"⚠️  {len(issues)} problemas de consistencia detectados:")
            for issue in issues[:5]:  # Show first 5
                print(f"  {issue}")
            if len(issues) > 5:
                print(f"  ... y {len(issues)-5} más")
            return False
        else:
            print("✅ Datos consistentes")
            return True
            
    except Exception as e:
        print(f"❌ Error verificando consistencia: {e}")
        return False

def main():
    print("🔧 JHS PIPELINE RECOVERY")
    print("=" * 50)
    
    # Check for resume
    resume_step = resume_pipeline()
    
    if resume_step:
        print(f"🔄 Resumiendo desde: {resume_step}")
        # Here you could implement step-specific resume logic
        # For now, we'll just clear and restart
        clear_checkpoint()
        print("🔄 Reiniciando pipeline completo...")
    
    # Verify current data state
    if verify_data_consistency():
        print("✅ Sistema en estado consistente")
    else:
        print("⚠️  Inconsistencias detectadas - ejecutar pipeline recomendado")
    
    # Clear checkpoint on manual verification
    clear_checkpoint()
    print("\n💡 Para pipeline con recovery automático:")
    print("  ~/vantage_pipeline.sh  → LAYER_1/wrappers/layer_1_wrapper.sh")

if __name__ == "__main__":
    main()