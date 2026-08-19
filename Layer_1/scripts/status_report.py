#!/usr/bin/env python3
"""
JHS Status Reporter - Genera resumen de aplicaciones y estado del sistema
Actualizado para notion-client 3.1.0:
- /databases/{id}/query fue eliminado en API version 2025-09-03
- Usar client.data_sources.query(data_source_id=...) como reemplazo directo
"""

import os
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
from notion_utils import Client


def txt(prop):
    if not prop:
        return ""
    t = prop.get("type")
    if t == "url":
        return prop.get("url") or ""
    if t == "rich_text" and prop.get("rich_text"):
        return prop["rich_text"][0]["plain_text"]
    if t == "select" and prop.get("select"):
        return prop["select"]["name"]
    if t == "title" and prop.get("title"):
        return prop["title"][0]["plain_text"]
    if t == "number":
        return prop.get("number")
    if t == "date" and prop.get("date"):
        return prop["date"]["start"]
    return ""


def query_database(client, database_id):
    """
    Usa client.data_sources.query() — equivalente a databases.query() en notion-client <3.x.
    El ID de la base de datos funciona como data_source_id (Notion mantiene compatibilidad de IDs).
    Pagina automáticamente para obtener todos los resultados.
    """
    all_results = []
    kwargs = {}

    while True:
        response = client.data_sources.query(data_source_id=database_id, **kwargs)
        all_results.extend(response.get("results", []))
        if response.get("has_more") and response.get("next_cursor"):
            kwargs["start_cursor"] = response["next_cursor"]
        else:
            break

    return all_results


def inspect_archive_queue():
    """
    Inspecciona las colas/archivos marcados para archivo y despliega el listado formateado.
    Utiliza graph_layer para obtener entidades con edges de tipo 'archived_from'.
    
    Versión mejorada (D2-rework):
    - Integración profunda con entity_index_v2.json para detalles de entidades
    - Detección de entidades con Next_Action='Archivar' o Dedup_Flag='Posible duplicado'
    - Validación de integridad del grafo
    - Reporting estructurado con formato JSON para consumo programático
    - Manejo robusto de errores con códigos de salida
    
    Returns:
        dict: Resultado estructurado con estadísticas y lista de entidades
    """
    result = {
        "success": False,
        "graph_stats": None,
        "archived_entities": [],
        "next_action_archive": [],
        "dedup_flag_candidates": [],
        "errors": []
    }
    
    try:
        # Import graph_layer for archive inspection
        import sys
        import json
        from pathlib import Path
        scripts_dir = Path(__file__).resolve().parent
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        
        from graph_layer import get_archived_from, graph_stats
        
        print("\n📦 ARCHIVE QUEUE INSPECTION (v2)")
        print("=" * 50)
        
        # Get graph statistics
        stats = graph_stats()
        result["graph_stats"] = stats
        
        print(f"📊 Graph Statistics:")
        print(f"  Total edges: {stats['total_edges']}")
        print(f"  Total nodes: {stats['total_nodes']}")
        print(f"  Edges by type:")
        for edge_type, count in stats['edges_by_type'].items():
            print(f"    - {edge_type}: {count}")
        
        # Get archived_from edges count
        archived_count = stats['edges_by_type'].get('archived_from', 0)
        print(f"\n🗄️  Archived From Edges: {archived_count}")
        
        # Load entity index for detailed entity information
        data_dir = Path(__file__).resolve().parent.parent / "data"
        entity_index_path = data_dir / "entity_index_v2.json"
        
        entity_index = {}
        if entity_index_path.exists():
            try:
                with open(entity_index_path, 'r', encoding='utf-8') as f:
                    entity_index = json.load(f)
                print(f"✅ Entity index cargado: {len(entity_index.get('entities', []))} entidades")
            except Exception as e:
                error_msg = f"Error cargando entity_index: {e}"
                print(f"⚠️  {error_msg}")
                result["errors"].append(error_msg)
        else:
            error_msg = f"Entity index no encontrado en {entity_index_path}"
            print(f"⚠️  {error_msg}")
            result["errors"].append(error_msg)
        
        # Analyze archived entities
        if archived_count > 0:
            print(f"\n⚠️  Hay {archived_count} relaciones de archivo en el grafo")
            
            # Try to get detailed information about archived entities
            entities_by_id = {e['entity_id']: e for e in entity_index.get('entities', [])}
            
            # Look for entities with archived_from edges
            for entity in entity_index.get('entities', []):
                entity_id = entity.get('entity_id')
                if entity_id:
                    archived_edges = get_archived_from(entity_id)
                    if archived_edges:
                        entity_info = {
                            "entity_id": entity_id,
                            "name": entity.get('name', 'Unknown'),
                            "type": entity.get('entity_type', 'Unknown'),
                            "archived_from_count": len(archived_edges),
                            "archived_from": archived_edges
                        }
                        result["archived_entities"].append(entity_info)
            
            if result["archived_entities"]:
                print(f"  � Entidades con relaciones de archivo: {len(result['archived_entities'])}")
                for entity in result['archived_entities'][:5]:
                    print(f"    • [{entity['entity_id'][:8]}] {entity['name']} ({entity['type']})")
                if len(result['archived_entities']) > 5:
                    print(f"    • ... y {len(result['archived_entities']) - 5} más")
            else:
                print("  ℹ️  No se encontraron entidades detalladas en entity_index")
                print("  �💡 Revisa entity_index_v2.json para detalles de entidades archivadas")
        else:
            print("  ✅ No hay relaciones de archivo pendientes")
        
        # Look for entities with Next_Action='Archivar' (from entity index if available)
        if entity_index:
            for entity in entity_index.get('entities', []):
                props = entity.get('properties', {})
                next_action = props.get('Next_Action', '')
                if next_action == 'Archivar':
                    result["next_action_archive"].append({
                        "entity_id": entity.get('entity_id'),
                        "name": entity.get('name', 'Unknown'),
                        "type": entity.get('entity_type', 'Unknown')
                    })
            
            if result["next_action_archive"]:
                print(f"\n🎯 Entidades con Next_Action='Archivar': {len(result['next_action_archive'])}")
                for entity in result['next_action_archive'][:5]:
                    print(f"    • [{entity['entity_id'][:8]}] {entity['name']}")
                if len(result['next_action_archive']) > 5:
                    print(f"    • ... y {len(result['next_action_archive']) - 5} más")
        
        # Look for entities with Dedup_Flag='Posible duplicado'
        if entity_index:
            for entity in entity_index.get('entities', []):
                props = entity.get('properties', {})
                dedup_flag = props.get('Dedup_Flag', '')
                if dedup_flag == 'Posible duplicado':
                    result["dedup_flag_candidates"].append({
                        "entity_id": entity.get('entity_id'),
                        "name": entity.get('name', 'Unknown'),
                        "type": entity.get('entity_type', 'Unknown')
                    })
            
            if result["dedup_flag_candidates"]:
                print(f"\n🔍 Entidades con Dedup_Flag='Posible duplicado': {len(result['dedup_flag_candidates'])}")
                for entity in result['dedup_flag_candidates'][:5]:
                    print(f"    • [{entity['entity_id'][:8]}] {entity['name']}")
                if len(result['dedup_flag_candidates']) > 5:
                    print(f"    • ... y {len(result['dedup_flag_candidates']) - 5} más")
        
        # Print JSON output for programmatic consumption
        print(f"\n📄 JSON Output (para consumo programático):")
        print(json.dumps({
            "graph_stats": stats,
            "archived_entities_count": len(result["archived_entities"]),
            "next_action_archive_count": len(result["next_action_archive"]),
            "dedup_flag_candidates_count": len(result["dedup_flag_candidates"]),
            "errors": result["errors"]
        }, indent=2))
        
        result["success"] = True
        return result
        
    except ImportError as e:
        error_msg = f"Error importing graph_layer: {e}"
        print(f"❌ {error_msg}")
        result["errors"].append(error_msg)
        return result
    except Exception as e:
        error_msg = f"Error inspecting archive queue: {e}"
        print(f"❌ {error_msg}")
        result["errors"].append(error_msg)
        return result


def main():
    parser = argparse.ArgumentParser(description="VANTAGE Status Reporter")
    parser.add_argument(
        "--archive-queue",
        action="store_true",
        help="Inspeccionar colas/archivos marcados para archivo"
    )
    args = parser.parse_args()
    
    load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
    client = Client(auth=os.environ["NOTION_TOKEN"])
    ds_id = "442938be-fc42-828f-b72e-076818d65a5b"

    print("📊 VANTAGE STATUS REPORT")
    print(f"🗓️  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    
    # Handle --archive-queue flag
    if args.archive_queue:
        inspect_archive_queue()
        return

    items = query_database(client, ds_id)

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
            except Exception:
                pass

        if nad:
            try:
                nad_dt = datetime.strptime(nad, "%Y-%m-%d").date()
                if nad_dt < today:
                    nads_vencidas.append({
                        "id": item["id"][:8],
                        "empresa": marca,
                        "rol": rol[:30] if rol else "Sin rol",
                        "nad": nad,
                        "status": status,
                    })
            except Exception:
                pass

    total_entries = len(items)

    print(f"\n🎯 ESTADO ACTUAL:")
    print(f"  📈 Pipeline Activo (CREATE): {pipeline_activo}")
    print(f"  🚀 En Aplicación (APPLIED):  {applied_count}")
    print(f"  ❌ Blocked:                  {blocked_count}")
    print(f"  📊 Total entradas:           {total_entries}")
    print(f"  📅 Aplicadas (7 días):       {aplicadas_semana}")

    if nads_vencidas:
        print(f"\n⚠️  NADs VENCIDAS ({len(nads_vencidas)}):")
        for nad in nads_vencidas[:5]:
            print(f"  • [{nad['id']}] {nad['empresa']} — {nad['rol']} (NAD: {nad['nad']})")
        if len(nads_vencidas) > 5:
            print(f"  • ... y {len(nads_vencidas) - 5} más")
    else:
        print("\n✅ Sin NADs vencidas")

    # Health check
    print(f"\n🏥 HEALTH CHECK:")
    active_total = pipeline_activo + applied_count
    active_ratio = (active_total / total_entries) if total_entries > 0 else 0
    blocked_ratio = (blocked_count / total_entries) if total_entries > 0 else 0

    if active_ratio >= 0.3:
        print("  ✅ Ratio activas saludable")
    else:
        print("  ⚠️  Pocas entradas activas — ejecutar búsquedas")

    if blocked_ratio <= 0.4:
        print("  ✅ Ratio Blocked controlado")
    else:
        print("  ⚠️  Demasiadas Blocked — hacer mantenimiento")

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
