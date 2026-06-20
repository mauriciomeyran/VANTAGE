#!/usr/bin/env python3
"""
JHS Source Analytics - Analiza efectividad de fuentes de discovery
Uso: python3 scripts/source_analytics.py
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from notion_utils import Client
from collections import defaultdict

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

def classify_source(fuente, url):
    """Classify source type from Fuente field and URL"""
    if not fuente:
        return "Unknown"
    
    fuente_lower = fuente.lower()
    
    # Direct career pages
    career_domains = ["careers.", "jobs.", "empleos.", "bolsa", "trabajo"]
    if url and any(domain in url.lower() for domain in career_domains):
        if any(brand in url.lower() for brand in ["lvmh", "richemont", "kering", "nike", "adidas"]):
            return "Career_Page_Premium"
        else:
            return "Career_Page_Standard"
    
    # Aggregators
    if any(site in fuente_lower for site in ["linkedin", "indeed", "occ", "glassdoor", "computrabajo"]):
        return fuente.title()
    
    # Manual/Direct
    if any(source in fuente_lower for source in ["referido", "directo", "networking"]):
        return "Direct_Contact"
    
    return "Other"

def main():
    load_dotenv(dotenv_path=os.path.abspath(".env"), override=True)
    client = Client(auth=os.environ["NOTION_TOKEN"])
    ds_id = "4e542b37-6e52-4418-89b7-a0eeb3138307"

    print("📊 JHS SOURCE EFFECTIVENESS ANALYTICS")
    print(f"🗓️  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    items = client.data_sources.query(data_source_id=ds_id)["results"]
    
    # Analytics containers
    source_stats = defaultdict(lambda: {
        "total": 0,
        "create": 0, 
        "applied": 0,
        "blocked": 0,
        "fetch_success": 0,
        "scores": []
    })
    
    weekly_discovery = defaultdict(lambda: defaultdict(int))
    search_type_effectiveness = {"SEARCH-WEEK": [], "SEARCH-EXEC": [], "Manual": []}
    
    # Date calculations
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    print("🔍 Analizando fuentes...")
    
    for item in items:
        props = item["properties"]
        fuente = txt(props.get("Fuente"))
        url = txt(props.get("URL"))
        gate_decision = txt(props.get("Gate_Decision"))
        fetch = txt(props.get("Fetch"))
        score = props.get("Score", {}).get("number") or 0
        status = txt(props.get("Status"))
        source_type = txt(props.get("Source_Type"))
        notas = txt(props.get("Notas"))
        
        # Classify source
        source_class = classify_source(fuente, url)
        
        # Basic stats
        source_stats[source_class]["total"] += 1
        source_stats[source_class]["scores"].append(score)
        
        if gate_decision == "CREATE":
            source_stats[source_class]["create"] += 1
        elif gate_decision == "APPLIED":
            source_stats[source_class]["applied"] += 1
        elif gate_decision == "BLOCKED":
            source_stats[source_class]["blocked"] += 1
            
        if fetch == "Accesible":
            source_stats[source_class]["fetch_success"] += 1
        
        # Try to detect search type from notes
        search_type = "Manual"
        if notas:
            if "feed semanal" in notas.lower() or "search-week" in notas.lower():
                search_type = "SEARCH-WEEK"
            elif "search-exec" in notas.lower() or "ejecutiv" in notas.lower():
                search_type = "SEARCH-EXEC"
        
        search_type_effectiveness[search_type].append({
            "gate": gate_decision,
            "score": score,
            "source": source_class
        })
    
    # Display results
    print(f"\n📈 EFECTIVIDAD POR FUENTE:")
    print(f"{'Fuente':<20} {'Total':<8} {'CREATE':<8} {'APPLIED':<9} {'BLOCKED':<9} {'Fetch%':<8} {'Score Avg'}")
    print("-" * 80)
    
    for source, stats in sorted(source_stats.items(), key=lambda x: x[1]["total"], reverse=True):
        if stats["total"] == 0:
            continue
            
        create_rate = (stats["create"] / stats["total"]) * 100
        applied_rate = (stats["applied"] / stats["total"]) * 100  
        blocked_rate = (stats["blocked"] / stats["total"]) * 100
        fetch_rate = (stats["fetch_success"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        avg_score = sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else 0
        
        print(f"{source:<20} {stats['total']:<8} {stats['create']:<8} {stats['applied']:<9} {stats['blocked']:<9} {fetch_rate:<7.0f}% {avg_score:<4.1f}")
    
    # Search method effectiveness
    print(f"\n🔍 EFECTIVIDAD POR MÉTODO DE BÚSQUEDA:")
    for method, entries in search_type_effectiveness.items():
        if not entries:
            continue
            
        total = len(entries)
        create_count = sum(1 for e in entries if e["gate"] == "CREATE")
        applied_count = sum(1 for e in entries if e["gate"] == "APPLIED")
        avg_score = sum(e["score"] for e in entries) / total if total > 0 else 0
        
        success_rate = ((create_count + applied_count) / total) * 100 if total > 0 else 0
        
        print(f"  {method:<12}: {total:>3} entries, {success_rate:>5.1f}% éxito, Score promedio: {avg_score:.1f}")
    
    # Quality insights
    print(f"\n💡 INSIGHTS DE CALIDAD:")
    
    # Best performing sources
    best_sources = []
    for source, stats in source_stats.items():
        if stats["total"] >= 3:  # At least 3 entries for relevance
            success_rate = ((stats["create"] + stats["applied"]) / stats["total"]) * 100
            fetch_rate = (stats["fetch_success"] / stats["total"]) * 100
            overall_quality = (success_rate * 0.7) + (fetch_rate * 0.3)  # Weighted quality score
            best_sources.append((source, overall_quality, stats["total"]))
    
    if best_sources:
        best_sources.sort(key=lambda x: x[1], reverse=True)
        print(f"  🏆 Mejores fuentes (calidad ponderada):")
        for source, quality, total in best_sources[:3]:
            print(f"     {source}: {quality:.1f}% calidad ({total} entradas)")
    
    # URL reliability insights
    reliable_sources = []
    for source, stats in source_stats.items():
        if stats["total"] >= 2:
            fetch_rate = (stats["fetch_success"] / stats["total"]) * 100
            reliable_sources.append((source, fetch_rate, stats["total"]))
    
    if reliable_sources:
        reliable_sources.sort(key=lambda x: x[1], reverse=True)
        print(f"  🔗 Fuentes más confiables (URLs funcionales):")
        for source, rate, total in reliable_sources[:3]:
            print(f"     {source}: {rate:.0f}% URLs funcionales ({total} entradas)")
    
    # Recommendations
    print(f"\n🎯 RECOMENDACIONES:")
    
    # Check if any source has consistently low performance
    poor_sources = []
    for source, stats in source_stats.items():
        if stats["total"] >= 3:
            success_rate = ((stats["create"] + stats["applied"]) / stats["total"]) * 100
            if success_rate < 30:  # Less than 30% success
                poor_sources.append((source, success_rate))
    
    if poor_sources:
        print(f"  ⚠️  Considerar reducir tiempo en:")
        for source, rate in poor_sources:
            print(f"     {source} ({rate:.0f}% éxito)")
    
    # Check which search method is most effective
    best_method = None
    best_rate = 0
    for method, entries in search_type_effectiveness.items():
        if len(entries) >= 3:
            success_rate = sum(1 for e in entries if e["gate"] in ["CREATE", "APPLIED"]) / len(entries) * 100
            if success_rate > best_rate:
                best_rate = success_rate
                best_method = method
    
    if best_method:
        print(f"  🚀 Enfocar más tiempo en: {best_method} ({best_rate:.0f}% efectivo)")
    
    print("=" * 60)

if __name__ == "__main__":
    main()