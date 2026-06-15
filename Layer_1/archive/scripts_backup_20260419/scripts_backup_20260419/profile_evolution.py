#!/usr/bin/env python3
"""
JHS Profile Evolution - Manejo de cambios en perfil y configuración del sistema
"""

import os
import json
import yaml
from datetime import datetime
from dotenv import load_dotenv

def load_current_config():
    """Load current system configuration"""
    config_file = "config/profile_config.yaml"
    
    if not os.path.exists(config_file):
        # Create default config
        default_config = {
            "profile": {
                "current_role": "VM & Brand Execution Coordinator",
                "current_company": "L'Oréal Luxe México", 
                "experience_level": "Mid-level",
                "target_seniority": "Senior Coordinator / Manager",
                "last_updated": datetime.now().isoformat()
            },
            "scoring": {
                "vm_keywords": ["visual merchandising", "visual", "vm", "brand environment", "estándares visuales"],
                "pivot_keywords": ["training", "experience", "producer", "account", "project", "commercial", "manager"],
                "score_weights": {
                    "Alto_VM": 8,
                    "Alto_Pivote": 6,
                    "Bajo_VM": 5,
                    "Bajo_Pivote": 3,
                    "default": 2
                }
            },
            "target_companies": {
                "tier_1_luxury": ["LVMH", "Richemont", "Kering", "Hermès", "Chanel"],
                "tier_2_premium": ["Estée Lauder", "Swarovski", "Hugo Boss", "Pandora"],
                "tier_3_scale": ["Nike", "Adidas", "Apple", "Zara", "Liverpool"]
            },
            "search_focus": {
                "weekly_priority": "VM_roles_core",
                "executive_priority": "Regional_LATAM",
                "geographic_scope": "CDMX_LATAM_Remote"
            }
        }
        
        os.makedirs("config", exist_ok=True)
        with open(config_file, "w") as f:
            yaml.dump(default_config, f, indent=2)
        
        return default_config
    
    with open(config_file, "r") as f:
        return yaml.safe_load(f)

def save_config(config):
    """Save updated configuration"""
    config["profile"]["last_updated"] = datetime.now().isoformat()
    
    with open("config/profile_config.yaml", "w") as f:
        yaml.dump(config, f, indent=2)

def update_profile_progression():
    """Update profile based on career progression"""
    config = load_current_config()
    
    print("📊 PERFIL ACTUAL:")
    print(f"  Rol: {config['profile']['current_role']}")
    print(f"  Empresa: {config['profile']['current_company']}")  
    print(f"  Nivel: {config['profile']['experience_level']}")
    print(f"  Target: {config['profile']['target_seniority']}")
    
    print(f"\n🔧 CONFIGURACIÓN ACTUAL:")
    print(f"  Keywords VM: {len(config['scoring']['vm_keywords'])} términos")
    print(f"  Empresas Tier 1: {len(config['target_companies']['tier_1_luxury'])}")
    print(f"  Scope: {config['search_focus']['geographic_scope']}")
    
    print(f"\n🚀 OPCIONES DE EVOLUCIÓN:")
    print("1. Actualizar experiencia actual")
    print("2. Cambiar target seniority") 
    print("3. Agregar nuevos keywords VM")
    print("4. Modificar empresas target")
    print("5. Ajustar scoring weights")
    print("6. Ver configuración completa")
    print("7. Salir sin cambios")
    
    choice = input("\nSelecciona opción (1-7): ").strip()
    
    if choice == "1":
        new_role = input("Nuevo rol actual: ").strip()
        new_company = input("Nueva empresa actual: ").strip()
        if new_role:
            config["profile"]["current_role"] = new_role
        if new_company:
            config["profile"]["current_company"] = new_company
        print("✅ Experiencia actualizada")
        
    elif choice == "2":
        print("Opciones de target seniority:")
        print("  a) Senior Coordinator")
        print("  b) Manager")  
        print("  c) Senior Manager")
        print("  d) Director")
        target_choice = input("Selecciona (a-d): ").strip().lower()
        
        targets = {
            "a": "Senior Coordinator",
            "b": "Manager", 
            "c": "Senior Manager",
            "d": "Director"
        }
        
        if target_choice in targets:
            config["profile"]["target_seniority"] = targets[target_choice]
            print(f"✅ Target actualizado a: {targets[target_choice]}")
            
    elif choice == "3":
        print("Keywords actuales:", config["scoring"]["vm_keywords"])
        new_keyword = input("Agregar keyword (o ENTER para cancelar): ").strip()
        if new_keyword and new_keyword not in config["scoring"]["vm_keywords"]:
            config["scoring"]["vm_keywords"].append(new_keyword)
            print(f"✅ Agregado: {new_keyword}")
            
    elif choice == "4":
        print("Empresas Tier 1 actuales:", config["target_companies"]["tier_1_luxury"])
        new_company = input("Agregar empresa Tier 1 (o ENTER para cancelar): ").strip()
        if new_company and new_company not in config["target_companies"]["tier_1_luxury"]:
            config["target_companies"]["tier_1_luxury"].append(new_company)
            print(f"✅ Agregada: {new_company}")
            
    elif choice == "5":
        print("Scoring weights actuales:")
        for key, value in config["scoring"]["score_weights"].items():
            print(f"  {key}: {value}")
        
        weight_key = input("¿Qué weight modificar? (Alto_VM/Alto_Pivote/etc): ").strip()
        if weight_key in config["scoring"]["score_weights"]:
            new_value = input(f"Nuevo valor para {weight_key} (actual: {config['scoring']['score_weights'][weight_key]}): ")
            try:
                config["scoring"]["score_weights"][weight_key] = int(new_value)
                print(f"✅ {weight_key} actualizado a {new_value}")
            except ValueError:
                print("❌ Valor inválido")
                
    elif choice == "6":
        print("\n📄 CONFIGURACIÓN COMPLETA:")
        print(yaml.dump(config, indent=2))
        input("Presiona ENTER para continuar...")
        
    elif choice == "7":
        print("👋 Sin cambios")
        return
        
    else:
        print("❌ Opción inválida")
        return
    
    save_config(config)
    print("\n✅ Configuración guardada")
    print("💡 Para aplicar cambios: edita manualmente scripts/run_pipeline.py con los nuevos valores")

def generate_config_summary():
    """Generate summary of current configuration for system sync"""
    config = load_current_config()
    
    print("\n📋 RESUMEN PARA SINCRONIZACIÓN:")
    print("=" * 50)
    print("# Actualizar en scripts/run_pipeline.py:")
    print()
    print("vm_terms = [")
    for keyword in config["scoring"]["vm_keywords"]:
        print(f'    "{keyword}",')
    print("]")
    print()
    print("pivot_terms = [")
    for keyword in config["scoring"]["pivot_keywords"]:
        print(f'    "{keyword}",')
    print("]")
    print()
    print("# Score weights:")
    for key, value in config["scoring"]["score_weights"].items():
        print(f"# {key}: {value}")

def main():
    print("🔄 JHS PROFILE EVOLUTION")
    print("=" * 50)
    
    # Check if pyyaml is installed
    try:
        import yaml
    except ImportError:
        print("❌ Error: PyYAML no está instalado")
        print("💡 Instalar: pip install pyyaml")
        return
    
    try:
        update_profile_progression()
        generate_config_summary()
    except KeyboardInterrupt:
        print("\n👋 Saliendo...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()