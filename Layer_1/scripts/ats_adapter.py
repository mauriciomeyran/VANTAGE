#!/usr/bin/env python3
"""
VANTAGE — ATS Adapter (Fase 3 Opción A)

Thin adapter between structured ATS clients (starting with Workday) and the
Layer 1 ingestion path (feed_processor / run_ingestion).

Target path in repo: Layer_1/scripts/ats_adapter.py

Responsibilities:
  - Call ats_workday.workday_structured_search / _2level
  - Translate jobPostings + audit into a feed envelope that normalize_envelope
    and process_record already understand.
  - Enforce the non-negotiable state contract: only verified_empty may produce
    an empty listings list that is treated as genuine zero; blocked / dns /
    timeout / unknown never invent vacancies and never claim verified_empty.

Does NOT write to Notion. Writing remains gated by APROBAR_WRITE + --apply
in the orchestrator.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Allow import from same scripts/ directory or from attachments during dev.
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

try:
    import ats_workday as wd
except ImportError:  # fallback for sandbox layout
    _ATTACH = Path("/home/workdir/attachments")
    if str(_ATTACH) not in sys.path:
        sys.path.insert(0, str(_ATTACH))
    import ats_workday as wd  # type: ignore


# ---------------------------------------------------------------- constants

VERIFIED_OK = {wd.QueryState.VERIFIED_RESULTS, wd.QueryState.VERIFIED_EMPTY}
TERMINAL_BAD = {
    wd.QueryState.BLOCKED,
    wd.QueryState.DNS_FAILURE,
    wd.QueryState.TIMEOUT,
    wd.QueryState.UNKNOWN,
}

# Chanel defaults (priority tenant for first live dry-run)
DEFAULT_CHANEL = {
    "tenant": "cc",
    "site": "ChanelCareers",
    "host": "cc.wd3.myworkdayjobs.com",
}


# ---------------------------------------------------------------- helpers

def _build_apply_url(host: str, external_path: str) -> str:
    """Construct canonical apply URL from Workday host + externalPath."""
    host = host.rstrip("/")
    if not host.startswith("http"):
        host = f"https://{host}"
    path = external_path if external_path.startswith("/") else f"/{external_path}"
    return f"{host}{path}"


def _job_to_feed_record(job: Dict[str, Any], host: str, brand: str,
                        layer: str = "L1") -> Dict[str, Any]:
    """Map one Workday jobPosting to the canonical feed record shape."""
    title = (job.get("title") or "").strip()
    external_path = (job.get("externalPath") or "").strip()
    locations_text = (job.get("locationsText") or job.get("location") or "").strip()
    posted = (job.get("postedOn") or "").strip()
    bullet = job.get("bulletFields") or []
    job_id = ""
    if bullet and isinstance(bullet, list) and bullet:
        job_id = str(bullet[0]).strip()
    elif job.get("jobReqId"):
        job_id = str(job["jobReqId"]).strip()

    apply_url = _build_apply_url(host, external_path) if external_path else ""

    return {
        "title": title,
        "brand": brand,
        "company": brand,
        "apply_url": apply_url,
        "url": apply_url,
        "location": locations_text,
        "job_id": job_id,
        "jd": "",  # structured search does not fetch full JD; left empty on purpose
        "fetch_status": "career_page",
        "source_type": "career_page",
        "layer": layer,
        "posted_on": posted,
        "external_path": external_path,
        "ats": "workday",
    }


def _make_envelope(
    records: List[Dict[str, Any]],
    *,
    tenant: str,
    site: str,
    host: str,
    state: str,
    audit: Dict[str, Any],
    scope_degradation: Optional[Dict[str, Any]],
    brand: str,
) -> Dict[str, Any]:
    """Build a feed envelope compatible with normalize_envelope / run_ingestion."""
    return {
        "schema_version": "vantage-feed-1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "ats_adapter.workday",
        "ats": "workday",
        "tenant": tenant,
        "site": site,
        "host": host,
        "brand": brand,
        "final_state": state,
        "audit": audit,
        "scope_degradation": scope_degradation,
        "consolidated_by_l0": False,  # single-source; GAP-01 does not apply
        "listings": records,
        "results_by_source": {
            f"workday:{tenant}/{site}": records,
        },
        "meta": {
            "raw_count": len(records),
            "state": state,
            "resolved_scope": (audit or {}).get("resolved_scope"),
            "applied_facets": (audit or {}).get("applied_facets"),
        },
    }


# ---------------------------------------------------------------- public API

def run_workday_discovery(
    tenant: str,
    site: str,
    host: str,
    *,
    require_city: bool = False,
    search_text: Optional[str] = None,
    use_two_level: bool = True,
    brand: Optional[str] = None,
    dry_run: bool = True,
    limit: int = 20,
    safety_cap: int = 2000,
) -> Dict[str, Any]:
    """
    Execute structured Workday search and return a feed-ready envelope.

    Returns dict with keys:
      - state          : QueryState string
      - detail         : human-readable detail
      - envelope       : feed JSON ready for normalize_envelope / run_ingestion
      - jobs           : raw job list (for inspection)
      - audit          : full audit trail from ats_workday
      - scope_degradation : explicit degradation info or None
      - dry_run        : echo of the flag
    """
    brand = brand or tenant.upper()

    if use_two_level:
        out = wd.workday_structured_search_2level(
            tenant=tenant,
            site=site,
            host=host,
            dry_run=dry_run,
            limit=limit,
            safety_cap=safety_cap,
            require_city=require_city,
        )
    else:
        out = wd.workday_structured_search(
            tenant=tenant,
            site=site,
            host=host,
            target_city=True,
            require_city=require_city,
            dry_run=dry_run,
            limit=limit,
            safety_cap=safety_cap,
            search_text=search_text,
        )

    state = out.get("state") or wd.QueryState.UNKNOWN
    detail = out.get("detail") or ""
    jobs = out.get("jobs") or []
    audit = out.get("audit") or {}
    scope_deg = out.get("scope_degradation")

    # Non-negotiable: only verified_* states may produce listings that the
    # downstream pipeline treats as real discovery results.
    if state not in VERIFIED_OK:
        records: List[Dict[str, Any]] = []
        # Still emit envelope so the caller sees the technical state.
    else:
        records = [
            _job_to_feed_record(j, host=host, brand=brand)
            for j in jobs
            if isinstance(j, dict) and (j.get("title") or j.get("externalPath"))
        ]

    envelope = _make_envelope(
        records,
        tenant=tenant,
        site=site,
        host=host,
        state=state,
        audit=audit,
        scope_degradation=scope_deg,
        brand=brand,
    )

    return {
        "state": state,
        "detail": detail,
        "envelope": envelope,
        "jobs": jobs,
        "audit": audit,
        "scope_degradation": scope_deg,
        "dry_run": dry_run,
        "record_count": len(records),
    }


def write_feed_file(envelope: Dict[str, Any], path: Path) -> Path:
    """Write envelope to disk as UTF-8 JSON. Returns the path written."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(envelope, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def format_discovery_report(result: Dict[str, Any]) -> str:
    """Human-readable summary for dry-run / CLI output."""
    a = result.get("audit") or {}
    lines = [
        "=== VANTAGE ATS Adapter — Workday Discovery ===",
        f"state:            {result.get('state')}",
        f"detail:           {result.get('detail') or '—'}",
        f"dry_run:          {result.get('dry_run')}",
        f"records (feed):   {result.get('record_count')}",
        f"raw jobs:         {len(result.get('jobs') or [])}",
        f"resolved_scope:   {a.get('resolved_scope')}",
        f"applied_facets:   {a.get('applied_facets')}",
    ]
    deg = result.get("scope_degradation")
    if deg:
        lines += [
            f"SCOPE DEGRADED:   requested={deg.get('requested_scope')} "
            f"resolved={deg.get('resolved_scope')}",
            f"  reason:         {deg.get('reason')}",
        ]
    env = result.get("envelope") or {}
    listings = env.get("listings") or []
    lines.append(f"listings preview ({min(10, len(listings))} of {len(listings)}):")
    for rec in listings[:10]:
        lines.append(
            f"  - {rec.get('title', '?')} | {rec.get('location', '?')} | {rec.get('apply_url', '')[:70]}"
        )
    if len(listings) > 10:
        lines.append(f"  … +{len(listings) - 10} more")
    return "\n".join(lines)


# ---------------------------------------------------------------- CLI (standalone)

if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="VANTAGE ATS Adapter — Workday discovery")
    p.add_argument("--tenant", default=DEFAULT_CHANEL["tenant"])
    p.add_argument("--site", default=DEFAULT_CHANEL["site"])
    p.add_argument("--host", default=DEFAULT_CHANEL["host"])
    p.add_argument("--brand", default="Chanel")
    p.add_argument("--require-city", action="store_true")
    p.add_argument("--search-text", default=None)
    p.add_argument("--no-two-level", action="store_true",
                   help="Use single-level search instead of country→city")
    p.add_argument("--out", default=None,
                   help="Write feed JSON to this path")
    p.add_argument("--no-dry-run", action="store_true",
                   help="Pass dry_run=False to the client (still no Notion write)")
    args = p.parse_args()

    result = run_workday_discovery(
        tenant=args.tenant,
        site=args.site,
        host=args.host,
        require_city=args.require_city,
        search_text=args.search_text,
        use_two_level=not args.no_two_level,
        brand=args.brand,
        dry_run=not args.no_dry_run,
    )
    print(format_discovery_report(result))

    if args.out:
        written = write_feed_file(result["envelope"], Path(args.out))
        print(f"\nFeed written → {written}")
