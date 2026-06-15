#!/usr/bin/env python3
"""
JHS Status Reporter - Genera resumen de aplicaciones y estado del sistema
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from notion_client import Client

def txt(prop):
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

def main():
    load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
    client = Client(auth=os.environ["NOTION_TOKEN"])
    ds_id = "4e542b37-6e52-4418-89b7-a0eeb3138307"

    print("📊 JHS STATUS REPORT")
    print(f"🗓️  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    items = client.data_sources.query(data_source_id=ds_id)["results"]
    
    pipeline_activo = 0
    aplicadas_semana = 0
    nads_vencidas = []
    blocked_count = 0
    applied_count = 0
    
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    for item in items:
        props = item["properties"]
        gate_decision = txt(props.get("Gate_Decision"))
        status = txt(props.get("Status"))
        applied_date = txt(props.get("Applied"))
        nad = txt(props.get("NAD"))
        rol = txt(props.get("Rol"))
        marca = txt(props.get("Marca"))
        
        if gate_decision == "CREATE":
            pipeline_activo += 1
        elif gate_decision == "APPLIED":
            applied_count += 1
        elif gate_decision == "BLOCKED":
            blocked_count += 1
            
        if applied_date:
            try:
                applied_dt = datetime.strptime(applied_date, "%Y-%m-%d").date()
                if applied_dt >= week_ago:
                    aplicadas_semana += 1
            except:
                pass
        
        if nad:
            try:
                nad_dt = datetime.strptime(nad, "%Y-%m-%d").date()
                if nad_dt < today:
                    nads_vencidas.append({
                        'id': item['id'][:8],
                        'empresa': marca,
                        'rol': rol[:30] if rol else "Sin rol",
                        'nad': nad,
                        'status': status
                    })
            except:
                pass
    
    total_entries = len(items)
    
    print(f"\n🎯 ESTADO ACTUAL:")
    print(f"  📈 Pipeline Activo: {pipeline_activo} entradas")
    print(f"  🚀 En Aplicación: {applied_count} entradas")
    print(f"  ❌ Blocked: {blocked_count}")
    print(f"  📊 Total: {total_entries}")
    print(f"  📅 Aplicadas (7 días): {aplicadas_semana}")
    
    if nads_vencidas:
        print(f"\n⚠️  NADs VENCIDAS ({len(nads_vencidas)}):")
        for nad in nads_vencidas[:5]:
            print(f"  • [{nad['id']}] {nad['empresa']} - {nad['rol']} (NAD: {nad['nad']})")
        if len(nads_vencidas) > 5:
            print(f"  • ... y {len(nads_vencidas)-5} más")
    else:
        print("\n✅ Sin NADs vencidas")
    
    # Health check
    print(f"\n🏥 HEALTH CHECK:")
    active_total = pipeline_activo + applied_count
    active_ratio = (active_total / total_entries) if total_entries > 0 else 0
    blocked_ratio = (blocked_count / total_entries) if total_entries > 0 else 0
    
    if active_ratio >= 0.3:
        print("  ✅ Ratio entradas activas saludable")
    else:
        print("  ⚠️  Pocas entradas activas - ejecutar búsquedas")
    
    if blocked_ratio <= 0.4:
        print("  ✅ Ratio Blocked controlado")  
    else:
        print("  ⚠️  Demasiadas Blocked - hacer mantenimiento")
    
    print(f"\n💡 PRÓXIMAS ACCIONES:")
    if aplicadas_semana == 0 and pipeline_activo > 0:
        print("  🎯 Aplicar a entradas de Pipeline Activo")
    if nads_vencidas:
        print("  📞 Follow-up en NADs vencidas")
    if blocked_ratio > 0.4:
        print("  🔧 Revisar Vista Blocked → reparar URLs")
    if active_ratio < 0.2:
        print("  🔍 Ejecutar búsquedas para más oportunidades")

if __name__ == "__main__":
    main()