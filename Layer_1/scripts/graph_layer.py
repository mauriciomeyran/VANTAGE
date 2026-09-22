# graph_layer.py
import json
import os
from collections import defaultdict

_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

def _load_graph_data():
    with open(os.path.join(_DIR, 'graph_v2.json'), 'r', encoding='utf-8') as f:
        graph_data = json.load(f)
    with open(os.path.join(_DIR, 'backlinks_v2.json'), 'r', encoding='utf-8') as f:
        backlinks_data = json.load(f)
    return graph_data, backlinks_data

graph_v2, backlinks_v2 = _load_graph_data()

def _check_suspended():
    """Check if graph subsystem is suspended and log warning."""
    if graph_v2.get("status") == "SUSPENDED":
        import logging
        logger = logging.getLogger("vantage.graph_layer")
        logger.warning(
            "Graph subsystem SUSPENDED: %s",
            graph_v2.get("reason", "Product decision")
        )
        return True
    return False

def get_archived_from(entity_id: str) -> list:
    if _check_suspended():
        return []
    edges = graph_v2.get("edges", [])
    return [edge for edge in edges if edge["from"] == entity_id and edge["type"] == "archived_from"]

def get_backlinks(entity_id: str) -> list:
    if _check_suspended():
        return []
    return backlinks_v2.get("backlinks", {}).get(entity_id, [])

def graph_stats() -> dict:
    if _check_suspended():
        return {
            "total_edges": 0,
            "total_nodes": 0,
            "edges_by_type": {},
            "status": "SUSPENDED",
            "reason": graph_v2.get("reason", "Product decision")
        }
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