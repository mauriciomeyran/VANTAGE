# graph_layer.py
import json
from collections import defaultdict

def _load_graph_data():
    with open('graph_v2.json', 'r', encoding='utf-8') as f:
        graph_data = json.load(f)
    with open('backlinks_v2.json', 'r', encoding='utf-8') as f:
        backlinks_data = json.load(f)
    return graph_data, backlinks_data

graph_v2, backlinks_v2 = _load_graph_data()

def get_archived_from(entity_id: str) -> list:
    edges = graph_v2.get("edges", [])
    return [edge for edge in edges if edge["from"] == entity_id and edge["type"] == "archived_from"]

def get_backlinks(entity_id: str) -> list:
    return backlinks_v2.get("backlinks", {}).get(entity_id, [])

def graph_stats() -> dict:
    edges = graph_v2.get("edges", [])
    total_edges = len(edges)
    edges_by_type = defaultdict(int)
    for edge in edges:
        edges_by_type[edge["type"]] += 1
    all_nodes = set()
    for edge in edges:
        all_nodes.add(edge["from"])
        all_nodes.add(edge["to"])
    return {
        "total_edges": total_edges,
        "total_nodes": len(all_nodes),
        "edges_by_type": dict(edges_by_type)
    }