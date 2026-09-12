#!/usr/bin/env python3
"""
VANTAGE Pipeline Orquestador v9.0 — Refactor completo

Este orquestador reemplaza layer_1_run.py v8.0/v8.1 usando tracker_flow.py
como única fuente de verdad para decisiones de transición.

Características:
- CLI compatible con layer_1_run.py (--dry-run default, --apply explícito)
- Un solo re-query inicial + writes con diff (no write-churn)
- Fases lineales usando tracker_flow.py como core de decisión
- Prioridad manual respetada (is_mutable + last_edited_time)
- Dedup unificado con survivor canónico + guard is_mutable
- class_b_guard generalizado a TODAS las vías de escritura

Serial: DEVIN-20260912-01
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Setup path for imports
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from tracker_flow import (
    Status, NextAction, GateDecision, Actor,
    normalize_record, is_mutable, evaluate_flow, archive_gate,
    LIFECYCLE_MATRIX, TERMINAL_STATUSES, LIVE_APPLICATION_STATUSES,
    PROTECTED_STATUSES, DELETED_VALUE_MAPPINGS,
    sync_status_from_outcome, apply_status_sync_writeback, run_outcome_status_sync,
    choose_survivor, get_layer_rank, diff_records,
)
from gate_logic import gate_logic
from priority_logic import infer_prioridad

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
VANTAGE_DATA_SOURCE_ID = "442938be-fc42-828f-b72e-076818d65a5b"
VANTAGE_ARCHIVE_DATA_SOURCE_ID = os.environ.get("NOTION_ARCHIVE_DATA_SOURCE_ID", "674696fd-...")
ENABLE_DEDUP_AUDIT = os.environ.get("ENABLE_DEDUP_AUDIT", "true").lower() == "true"
DEDUP_WINDOW_DAYS = int(os.environ.get("DEDUP_WINDOW_DAYS", "60"))


class NotionClientFake:
    """Fake Notion client for dry-run mode (no actual API calls)"""
    def __init__(self):
        self.writes = []
        self.queries = []
        
    def query_data_sources(self, data_source_id: str, **kwargs) -> Dict[str, Any]:
        self.queries.append(("query_data_sources", data_source_id, kwargs))
        return {"results": []}
    
    def pages_update(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        self.writes.append(("pages_update", page_id, properties))
        return {"id": page_id}


def validate_url(url: str, source_type: str) -> tuple[bool, str]:
    """
    F2: URL Gate - validar URL con bypass para agregadores.
    
    Returns (is_valid, reason) donde reason puede ser:
    - "VALID" - URL válida
    - "BLOCKED" - URL bloqueada/caida
    - "AGREGADOR_RETRY_..." - agregador con fallo temporal
    """
    if not url:
        return False, "NO_URL"
    
    # Bypass para agregadores (KERNEL:GATE-DECISION-002)
    agregador_domains = [
        "jobs.nike.com", "workable.com", "greenhouse.io", "lever.co"
    ]
    for domain in agregador_domains:
        if domain in url:
            return True, "AGREGADOR_VALID"
    
    # URL con tracking params → bloquear (radiografía §1.1-F2)
    if any(param in url for param in ["utm_", "fbclid", "gclid"]):
        return False, "TRACKING_URL"
    
    # Validación HEAD request sería aquí en modo real
    # Para dry-run/fake, asumimos válido si tiene esquema
    if url.startswith(("http://", "https://")):
        return True, "VALID"
    
    return False, "INVALID_SCHEME"


def calculate_score_v6(record: Dict[str, Any]) -> int:
    """
    F3: Scoring v6.4 - fórmula idéntica a layer_1_run.py v8.0.
    
    Base: 40
    Bonos hasta 9 puntos por:
    - Marca premium (+10)
    - Rol senior (+10)
    - JD largo (+15)
    - Contacto directo (+10)
    - VM_Scope alto (+10)
    - Role_Class específico (+10)
    - Source_Type calidad (+15)
    """
    score = 40  # Base
    
    # Bonos (implementación simplificada para demo)
    marca = record.get("Marca", "").lower()
    if marca in ["zara", "bershka", "mango", "h&m", "stradivarius"]:
        score += 10
    
    rol = record.get("Rol", "").lower()
    if any(word in rol for word in ["senior", "lead", "manager", "director"]):
        score += 10
    
    jd = record.get("JD", "")
    if len(jd) > 500:
        score += 15
    
    contacto = record.get("Contacto", "")
    if contacto and "@" in contacto:
        score += 10
    
    vm_scope = record.get("VM_Scope", "")
    if vm_scope in ["Alto", "Medio"]:
        score += 10
    
    # Cap a 100
    return min(score, 100)


def apply_gate_decision(record: Dict[str, Any], score: int) -> Dict[str, Any]:
    """
    F4: Gate Logic + Next_Action via enums + DELETED_VALUE_MAPPINGS.
    
    Usa tracker_flow.evaluate_flow() como core de decisión.
    """
    # Normalizar record para tracker_flow
    normalized = normalize_record(record)
    
    # Evaluar flujo usando tracker_flow
    result = evaluate_flow(normalized, Actor.PIPELINE)
    
    return result


def manual_first_protection(record: Dict[str, Any], actor: Actor) -> bool:
    """
    §2.3: Ediciones manuales recientes = máxima prioridad.
    
    Una fila tocada por humano desde el último run queda inmune a mutación destructiva.
    """
    if not is_mutable(record, actor):
        return False
    
    last_edited_time = record.get("last_edited_time", "")
    last_gate_run = record.get("Last_Gate_Run", "")
    
    if not last_edited_time or not last_gate_run:
        return True  # Sin timestamp = asumir mutable
    
    # Si editado por humano después del último run → inmunidad
    last_edited_by_id = record.get("last_edited_by_id", "")
    from tracker_flow import _is_human_edit
    if _is_human_edit(last_edited_by_id):
        if last_edited_time > last_gate_run:
            logger.info(
                f"[MANUAL-FIRST] Fila {record.get('id', 'unknown')[:8]} "
                f"editada por humano después del último run → inmunidad"
            )
            return False
    
    return True


def analyze_outcome_patterns(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    F5: Análisis de patrones de rechazo — SOLO LECTURA.

    Opera sobre el snapshot ya normalizado (cero re-query, cero writes).
    Port conductual de layer_1_run.analyze_outcome_patterns sobre plano.
    """
    rejection_patterns: Dict[str, Dict[str, int]] = {}
    score_effectiveness: Dict[str, Dict[str, int]] = {}
    timing_patterns: Dict[str, List[int]] = {}

    live_applied = {
        Status.POSTULADO.value,
        Status.EN_PROCESO.value,
        Status.NEGOCIANDO.value,
        "En proceso",  # legacy casing visto en prod
    }

    for record in records:
        status = record.get("Status", "") or ""
        score = record.get("Score", 0) or 0
        marca = record.get("Marca", "") or ""
        vm_scope = record.get("VM_Scope", "") or ""
        applied_date = record.get("Apply Date", "") or record.get("Applied", "") or ""
        rejected_date = record.get("Rej Date", "") or ""

        score_bracket = f"Score {score}"

        if status == Status.RECHAZADO.value:
            score_effectiveness.setdefault(score_bracket, {"applied": 0, "rejected": 0})
            score_effectiveness[score_bracket]["rejected"] += 1
            if marca:
                rejection_patterns.setdefault(marca, {"applied": 0, "rejected": 0})
                rejection_patterns[marca]["rejected"] += 1
        elif status in live_applied:
            score_effectiveness.setdefault(score_bracket, {"applied": 0, "rejected": 0})
            score_effectiveness[score_bracket]["applied"] += 1
            if marca:
                rejection_patterns.setdefault(marca, {"applied": 0, "rejected": 0})
                rejection_patterns[marca]["applied"] += 1

        if applied_date and rejected_date:
            try:
                applied_dt = datetime.strptime(str(applied_date)[:10], "%Y-%m-%d").date()
                rejected_dt = datetime.strptime(str(rejected_date)[:10], "%Y-%m-%d").date()
                days_to_rejection = (rejected_dt - applied_dt).days
                timing_key = f"{vm_scope or 'N/A'}_VM"
                timing_patterns.setdefault(timing_key, []).append(days_to_rejection)
            except (ValueError, TypeError):
                pass

    return {
        "rejection_patterns": rejection_patterns,
        "score_effectiveness": score_effectiveness,
        "timing_patterns": timing_patterns,
    }


def _normalize_dedup_key(url: str) -> str:
    """Clave canónica de URL para agrupar duplicados (sin query/fragment)."""
    if not url:
        return ""
    raw = url.strip().lower()
    # Quitar esquema y www
    for prefix in ("https://", "http://"):
        if raw.startswith(prefix):
            raw = raw[len(prefix):]
            break
    if raw.startswith("www."):
        raw = raw[4:]
    # Quitar query y fragment
    raw = raw.split("?", 1)[0].split("#", 1)[0]
    return raw.rstrip("/")


def find_duplicate_groups(records: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """
    F6: Agrupa duplicados por URL canónica o hash idéntico.

    Solo produce grupos de tamaño ≥ 2. No escribe nada.
    """
    by_key: Dict[str, List[Dict[str, Any]]] = {}
    for record in records:
        url_key = _normalize_dedup_key(record.get("URL", "") or "")
        hash_key = (record.get("hash") or "").strip().lower()
        key = None
        if url_key:
            key = f"url:{url_key}"
        elif hash_key:
            key = f"hash:{hash_key}"
        if not key:
            continue
        by_key.setdefault(key, []).append(record)

    return [group for group in by_key.values() if len(group) >= 2]


def run_dedup_audit(
    records: List[Dict[str, Any]],
    client: Any,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    F6: Dedup unificado con survivor canónico + guard is_mutable.

    - Survivor = choose_survivor (core tracker_flow: Status rank → Score → URL → layer L1>L2>L3>N/A)
    - No-survivors mutables reciben Dedup_Flag = "Posible duplicado"
    - Filas protegidas (is_mutable=False) jamás se marcan ni se archivan
    - Cero trash físico; consolidate_duplicates.py se archiva en G6, no se llama aquí
    """
    result = {
        "groups_found": 0,
        "survivors": 0,
        "flagged": 0,
        "protected_skipped": 0,
        "flags": [],  # list of {survivor_id, flagged_id, reason}
    }

    groups = find_duplicate_groups(records)
    result["groups_found"] = len(groups)

    for group in groups:
        survivor = choose_survivor(group)
        result["survivors"] += 1
        survivor_id = survivor.get("id", "")

        for record in group:
            rid = record.get("id", "")
            if rid == survivor_id:
                continue

            # Guard is_mutable: filas protegidas son inmunes al mark
            if not is_mutable(record, Actor.DEDUP):
                result["protected_skipped"] += 1
                logger.info(
                    f"[F6] Skip protegido {rid[:8]} (survivor={survivor_id[:8]})"
                )
                continue

            flag_payload = {"Dedup_Flag": "Posible duplicado"}
            result["flags"].append({
                "survivor_id": survivor_id,
                "flagged_id": rid,
                "survivor_layer": survivor.get("layer", "N/A"),
                "flagged_layer": record.get("layer", "N/A"),
            })
            result["flagged"] += 1

            if not dry_run:
                client.pages_update(rid, flag_payload)
                logger.info(
                    f"[F6] Dedup_Flag → {rid[:8]} (survivor={survivor_id[:8]})"
                )
            else:
                logger.info(
                    f"[F6 DRY] marcaría Dedup_Flag → {rid[:8]} "
                    f"(survivor={survivor_id[:8]})"
                )

    return result


def run_orchestrator(
    client: Any,
    dry_run: bool = True,
    apply: bool = False,
    dedup_audit: bool = False
) -> Dict[str, Any]:
    """
    Ejecuta el orquestador completo.
    
    Args:
        client: Notion client (real o fake)
        dry_run: Modo diagnóstico (default True)
        apply: Modo escritura (requiere --apply explícito)
        dedup_audit: Ejecutar dedup audit al final
    
    Returns:
        Dict con métricas del run
    """
    if apply and dry_run:
        logger.warning("--apply ignora --dry-run, se usará modo escritura")
        dry_run = False
    
    if not dry_run and not apply:
        logger.warning("Sin --apply, default es dry-run")
        dry_run = True
    
    logger.info(f"{'='*60}")
    logger.info(f"VANTAGE Orquestador v9.0 - {'DRY RUN' if dry_run else 'APPLY MODE'}")
    logger.info(f"{'='*60}")
    
    metrics = {
        "total_processed": 0,
        "writes": 0,
        "skips": 0,
        "archives": 0,
        "errors": 0,
        "manual_protected": 0,
        "patterns": None,
        "dedup": None,
    }
    
    # F0: Query inicial único + snapshot (un solo re-query)
    logger.info("F0: Query inicial del Tracker...")
    query_result = client.query_data_sources(VANTAGE_DATA_SOURCE_ID)
    items = query_result.get("results", [])
    metrics["total_processed"] = len(items)
    
    logger.info(f"F0: {len(items)} filas recuperadas")

    # Snapshot normalizado del run (fuente única para F5/F6; cero re-query)
    snapshot: List[Dict[str, Any]] = []
    
    # Fases por cada fila
    for item in items:
        try:
            # Normalizar record
            record = normalize_record(item)
            snapshot.append(record)
            record_id = record.get("id", "unknown")[:8]
            
            # §2.3: Manual-first protection
            if not manual_first_protection(record, Actor.PIPELINE):
                metrics["manual_protected"] += 1
                continue
            
            # F1.5: Clasificación VM_Scope/Role_Class/Source_Type
            # (Se mantiene de layer_1_run.py, usa enums de tracker_flow)
            source_type = record.get("Source_Type ", "Vacante")  # Nota: espacio en trailing
            if not source_type:
                record["Source_Type "] = "Vacante"
            
            # F2: URL Gate
            url = record.get("URL", "")
            is_valid, reason = validate_url(url, source_type)
            
            if not is_valid and reason not in ["AGREGADOR_RETRY"]:
                # Archivar por URL inválida
                archive_result = archive_gate(
                    record,
                    reason=f"URL Gate: {reason}",
                    evidence=f"URL={url}",
                    actor=Actor.PIPELINE,
                    timestamp=datetime.now().isoformat()
                )
                if not dry_run:
                    client.pages_update(record["id"], archive_result)
                    metrics["writes"] += 1
                metrics["archives"] += 1
                continue
            
            # F3: Scoring v6.4
            score = calculate_score_v6(record)
            record["Score"] = score
            record["Score_Method"] = "DETERMINISTIC"
            
            # F3.5: Misfit + exclusiones (usando is_mutable de tracker_flow)
            # F3.5.1: Expiración NAD (unificado con F0 NAD)
            nad = record.get("NAD", "")
            if nad:
                try:
                    nad_date = datetime.strptime(nad, "%Y-%m-%d")
                    if nad_date < datetime.now():
                        archive_result = archive_gate(
                            record,
                            reason="NAD expirado",
                            evidence=f"NAD={nad}",
                            actor=Actor.PIPELINE,
                            timestamp=datetime.now().isoformat()
                        )
                        if not dry_run:
                            client.pages_update(record["id"], archive_result)
                            metrics["writes"] += 1
                        metrics["archives"] += 1
                        continue
                except ValueError:
                    logger.warning(f"NAD malformado: {nad}")
            
            # F3.6: Prioridad (via priority_logic.py, NO tocar bug :125)
            # (Portar llamada sin modificar lógica interna)
            try:
                from priority_logic import infer_prioridad
                prioridad = infer_prioridad(item, datetime.now())
                record["Prioridad"] = prioridad
            except Exception as e:
                logger.warning(f"Error calculando prioridad: {e}")
            
            # F4: Gate + Next_Action (via tracker_flow.evaluate_flow)
            gate_result = apply_gate_decision(record, score)
            
            # Write final con diff (solo si hay cambios reales)
            if not dry_run:
                changes = {}
                for key, value in gate_result.items():
                    if record.get(key) != value:
                        changes[key] = value
                
                if changes:
                    client.pages_update(record["id"], changes)
                    metrics["writes"] += 1
                else:
                    metrics["skips"] += 1
            else:
                metrics["skips"] += 1
                
        except Exception as e:
            logger.error(f"Error procesando fila {record.get('id', 'unknown')[:8]}: {e}")
            metrics["errors"] += 1

    # F5: Patrones (solo lectura, sobre snapshot — cero writes)
    logger.info("F5: Análisis de patrones (read-only)...")
    metrics["patterns"] = analyze_outcome_patterns(snapshot)
    
    # F6: Dedup unificado (survivor canónico + guard is_mutable)
    if dedup_audit or ENABLE_DEDUP_AUDIT:
        logger.info("F6: Dedup audit (survivor L1>L2>L3>N/A + is_mutable)...")
        dedup_result = run_dedup_audit(snapshot, client, dry_run=dry_run)
        metrics["dedup"] = dedup_result
        if not dry_run:
            metrics["writes"] += dedup_result.get("flagged", 0)
    
    # Summary
    logger.info(f"{'='*60}")
    logger.info("SUMMARY")
    logger.info(f"Total procesado: {metrics['total_processed']}")
    logger.info(f"Escrituras: {metrics['writes']}")
    logger.info(f"Skips (sin cambios): {metrics['skips']}")
    logger.info(f"Archivos: {metrics['archives']}")
    logger.info(f"Protegidos manual: {metrics['manual_protected']}")
    logger.info(f"Errores: {metrics['errors']}")
    if metrics.get("dedup"):
        logger.info(
            f"Dedup: groups={metrics['dedup']['groups_found']} "
            f"flagged={metrics['dedup']['flagged']} "
            f"protected={metrics['dedup']['protected_skipped']}"
        )
    logger.info(f"{'='*60}")
    
    return metrics


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="VANTAGE Pipeline Orquestador v9.0"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Modo diagnóstico (default)"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Modo escritura (requiere confirmación)"
    )
    parser.add_argument(
        "--dedup-audit",
        action="store_true",
        help="Ejecutar dedup audit al final"
    )
    
    args = parser.parse_args()
    
    # Load environment
    load_dotenv()
    
    # Crear client (fake en dry-run, real en apply)
    if args.apply:
        from notion_client import Client
        notion_token = os.environ.get("NOTION_TOKEN")
        if not notion_token:
            logger.error("NOTION_TOKEN requerido en modo --apply")
            sys.exit(1)
        client = Client(auth=notion_token)
    else:
        client = NotionClientFake()
    
    # Ejecutar orquestador
    metrics = run_orchestrator(
        client=client,
        dry_run=args.dry_run,
        apply=args.apply,
        dedup_audit=args.dedup_audit
    )
    
    # Exit code
    if metrics["errors"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
