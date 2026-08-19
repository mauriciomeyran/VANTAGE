from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import requests as _requests

try:
    from query_layer import find_entity, list_entities, search_entities, resolve_entity
except ImportError:
    raise RuntimeError("query_layer.py no encontrado en la misma carpeta.")

try:
    from context_layer import assemble_context
    from notion_utils import ResolverError, _get_token, _notion_version
except ImportError:
    raise RuntimeError("context_layer.py / notion_utils.py no encontrados en la misma carpeta.")

try:
    from graph_layer import get_archived_from, get_backlinks, graph_stats
    _GRAPH_AVAILABLE = True
except ImportError:
    _GRAPH_AVAILABLE = False

_BUG_TRACKER_DS_ID = "36e938be-fc42-81f8-8c6f-000b6769ba03"
_ARCHIVO_TRACKER_DS_ID = "674696fd-94b6-464a-ac1f-64b0cc917e15"

ARCHIVED_STATUSES = {"Expirada"}
ALREADY_ACTIONED_STATUSES = {"Postulado", "En proceso"}


def _is_active(status_value: Optional[str]) -> bool:
    if status_value is None:
        return True
    return status_value not in ARCHIVED_STATUSES


def _iterate_contexts(entities: List[Dict[str, Any]]):
    for entry in entities:
        entity_id = entry.get("entity_id")
        try:
            ctx = assemble_context(entity_id)
            yield entity_id, ctx, None
        except ResolverError as exc:
            yield entity_id, None, f"{exc.status}: {exc.message}"
        except Exception as exc:
            yield entity_id, None, str(exc)


def _notion_db_query(data_source_id: str, body: Optional[Dict] = None) -> List[Dict]:
    url = f"https://api.notion.com/v1/data_sources/{data_source_id}/query"
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Notion-Version": _notion_version(),
        "Content-Type": "application/json",
    }

    results = []
    payload = body or {}
    while True:
        resp = _requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        results.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        payload = {**payload, "start_cursor": data["next_cursor"]}
    return results


def _extract_title(page: Dict[str, Any]) -> str:
    props = page.get("properties", {})
    for _, val in props.items():
        if val.get("type") == "title":
            rich = val.get("title", [])
            return "".join(r.get("plain_text", "") for r in rich)
    return page.get("id", "sin título")


def _extract_prop(page: Dict[str, Any], prop_name: str) -> Any:
    props = page.get("properties", {})
    if prop_name not in props:
        return None

    val = props[prop_name]
    t = val.get("type")

    if t == "title":
        rich = val.get("title", [])
        return "".join(r.get("plain_text", "") for r in rich)
    if t == "rich_text":
        rich = val.get("rich_text", [])
        return "".join(r.get("plain_text", "") for r in rich)
    if t == "select":
        s = val.get("select")
        return s["name"] if s else None
    if t == "multi_select":
        return [s["name"] for s in val.get("multi_select", [])]
    if t == "date":
        d = val.get("date")
        return d["start"] if d else None
    if t == "number":
        return val.get("number")
    if t == "checkbox":
        return val.get("checkbox")
    if t == "url":
        return val.get("url")
    return None


def _handle_show_roles(active: bool) -> Dict[str, Any]:
    trackers = list_entities(source_db="VANTAGE_TRACKER")
    matched, errors = [], []

    for entity_id, ctx, err in _iterate_contexts(trackers):
        if err:
            errors.append({"entity_id": entity_id, "error": err})
            continue

        if _is_active(ctx["status"]) == active:
            matched.append({
                "entity_id": entity_id,
                "status": ctx["status"],
                "score": ctx["metadata"].get("Score"),
                "gate_decision": ctx["metadata"].get("Gate_Decision"),
                "page_url": ctx["entity"].get("page_url"),
            })

    return {
        "intent": "show_active_roles" if active else "show_archived_roles",
        "count": len(matched),
        "results": matched,
        "errors": errors,
    }


def _handle_find_candidates() -> Dict[str, Any]:
    trackers = list_entities(source_db="VANTAGE_TRACKER")
    matched, errors = [], []

    for entity_id, ctx, err in _iterate_contexts(trackers):
        if err:
            errors.append({"entity_id": entity_id, "error": err})
            continue

        status = ctx["status"]
        gate = ctx["metadata"].get("Gate_Decision")
        match = ctx["metadata"].get("Match")

        score = ctx["metadata"].get("Score") or 0

        if (
            _is_active(status)
            and status not in ALREADY_ACTIONED_STATUSES
            and gate != "BLOCKED"
            and match in ("Alto", "Medio")
            and score >= 60
        ):
            matched.append({
                "entity_id": entity_id,
                "status": status,
                "score": ctx["metadata"].get("Score"),
                "match": match,
                "gate_decision": gate,
                "page_url": ctx["entity"].get("page_url"),
            })

    matched.sort(key=lambda r: (r["score"] or 0), reverse=True)
    return {"intent": "find_candidates", "count": len(matched), "results": matched, "errors": errors}


def _handle_compare(entity_id_a: str, entity_id_b: str) -> Dict[str, Any]:
    ctx_a = assemble_context(entity_id_a)
    ctx_b = assemble_context(entity_id_b)

    keys = sorted(set(ctx_a["metadata"]) | set(ctx_b["metadata"]) | {"status"})
    diff = {}

    for key in keys:
        val_a = ctx_a["status"] if key == "status" else ctx_a["metadata"].get(key)
        val_b = ctx_b["status"] if key == "status" else ctx_b["metadata"].get(key)
        if val_a != val_b:
            diff[key] = {"a": val_a, "b": val_b}

    return {
        "intent": "compare_entities",
        "entity_a": {"entity_id": entity_id_a, "page_url": ctx_a["entity"].get("page_url")},
        "entity_b": {"entity_id": entity_id_b, "page_url": ctx_b["entity"].get("page_url")},
        "diff": diff,
        "diff_count": len(diff),
    }


def _handle_show_archived_history() -> Dict[str, Any]:
    try:
        pages = _notion_db_query(_ARCHIVO_TRACKER_DS_ID)
    except Exception as exc:
        return {"intent": "show_archived_history", "error": str(exc)}

    records = []
    for page in pages:
        records.append({
            "page_id": page.get("id"),
            "title": _extract_title(page),
            "status": _extract_prop(page, "Status"),
            "marca": _extract_prop(page, "Marca"),
            "page_url": page.get("url"),
        })

    by_status: Dict[str, int] = {}
    by_marca: Dict[str, int] = {}
    for r in records:
        s = r["status"] or "sin status"
        m = r["marca"] or "sin marca"
        by_status[s] = by_status.get(s, 0) + 1
        by_marca[m] = by_marca.get(m, 0) + 1

    return {
        "intent": "show_archived_history",
        "total": len(records),
        "by_status": by_status,
        "top_marcas": dict(sorted(by_marca.items(), key=lambda x: -x[1])[:10]),
        "records": records,
    }


def _handle_show_bugs() -> Dict[str, Any]:
    try:
        pages = _notion_db_query(_BUG_TRACKER_DS_ID)
    except Exception as exc:
        return {"intent": "show_bugs", "error": str(exc)}

    bugs = []
    for page in pages:
        severity = _extract_prop(page, "Prioridad")
        if severity is None:
            severity = _extract_prop(page, "Severity") or _extract_prop(page, "Priority")

        component = _extract_prop(page, "Componente")
        if component is None:
            component = _extract_prop(page, "Component") or _extract_prop(page, "Area")

        bugs.append({
            "page_id": page.get("id"),
            "title": _extract_title(page),
            "status": _extract_prop(page, "Status"),
            "severity": severity,
            "component": component,
            "next_action": _extract_prop(page, "Next_Action"),
            "fecha_deteccion": _extract_prop(page, "Fecha_Detección"),
            "fecha_resolucion": _extract_prop(page, "Fecha_Resolución"),
            "page_url": page.get("url"),
        })

    by_status: Dict[str, int] = {}
    for b in bugs:
        s = b["status"] or "sin status"
        by_status[s] = by_status.get(s, 0) + 1

    return {
        "intent": "show_bugs",
        "total": len(bugs),
        "by_status": by_status,
        "bugs": bugs,
    }


def _handle_graph_relations(entity_id: str) -> Dict[str, Any]:
    archived_from = get_archived_from(entity_id)
    backlinks = get_backlinks(entity_id)

    return {
        "intent": "graph_relations",
        "entity_id": entity_id,
        "archived_from": archived_from,
        "archived_to": backlinks,
        "backlinks": backlinks,
        "stats": graph_stats(),
    }


def _handle_search(text: str) -> Dict[str, Any]:
    results = search_entities(text)
    return {"intent": "search", "query": text, "count": len(results), "results": results}


def ask(prompt: str, **kwargs) -> Dict[str, Any]:
    p = prompt.lower().strip()

    if "active role" in p or "roles activos" in p:
        return _handle_show_roles(active=True)

    if any(kw in p for kw in ("archived history", "archivo histórico", "historial")):
        return _handle_show_archived_history()

    if "show archived" in p:
        if "role" in p or "roles" in p or "job" in p:
            return _handle_show_roles(active=False)
        return _handle_show_archived_history()

    if "archived role" in p or "roles archivados" in p or "archived job" in p:
        return _handle_show_roles(active=False)

    if "bug" in p:
        return _handle_show_bugs()

    if "find candidate" in p or "candidatos" in p:
        return _handle_find_candidates()

    if "relation" in p or "graph" in p:
        parts = prompt.split()
        ids = [tok for tok in parts if ":" in tok and not tok.startswith("http")]
        if ids:
            return _handle_graph_relations(ids[0])
        if _GRAPH_AVAILABLE:
            return {"intent": "graph_stats", "stats": graph_stats()}

    if "compare" in p:
        a = kwargs.get("a")
        b = kwargs.get("b")
        if not a or not b:
            parts = prompt.split()
            ids = [tok for tok in parts if ":" in tok]
            if len(ids) == 2:
                a, b = ids
        if not a or not b:
            return {
                "intent": "compare_entities",
                "error": "se necesitan dos entity_ids, ej: ask('compare TRACKER:H_x TRACKER:H_y')",
            }
        return _handle_compare(a, b)

    return _handle_search(prompt)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("uso: python3 agent_api.py ''")
        print("ejemplos:")
        print("  python3 agent_api.py 'show active roles'")
        print("  python3 agent_api.py 'show archived history'")
        print("  python3 agent_api.py 'show bugs'")
        print("  python3 agent_api.py 'find candidates'")
        print("  python3 agent_api.py 'compare TRACKER:H_xxx TRACKER:H_yyy'")
        raise SystemExit(1)

    print(json.dumps(ask(sys.argv[1]), indent=2, ensure_ascii=False))
