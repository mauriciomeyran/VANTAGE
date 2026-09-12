#!/usr/bin/env python3
"""
VANTAGE URL Gate helpers — compartidos entre orquestador e ingesta.

Extraído de layer_1_run.py para que feed_processor.py no dependa del
orquestador viejo (vocab §3 / G2c-3). layer_1_run.py puede seguir
reexportando si hace falta hasta G6.
"""

from __future__ import annotations

import urllib.parse
from typing import Tuple

# Agregadores conocidos (KERNEL:GATE-DECISION-002)
AGREGADOR_DOMAINS = [
    "linkedin.com",
    "indeed.com",
    "occ.com.mx",
    "glassdoor.com",
    "bumeran.com",
    "computrabajo.com",
    "computrabajo.com.mx",
    "jobs.nike.com",
    "workable.com",
    "greenhouse.io",
    "lever.co",
]


def is_agregador(url: str) -> bool:
    """Determina si la URL pertenece a un agregador de empleo."""
    if not url:
        return False
    try:
        parsed = urllib.parse.urlparse(url)
        domain = (parsed.netloc or "").lower()
    except Exception:
        return False
    for pattern in AGREGADOR_DOMAINS:
        if domain.endswith(pattern) or pattern in domain:
            return True
    return False


def normalize_url(url: str) -> str:
    """Agrega https:// si falta esquema."""
    if not url or not isinstance(url, str):
        return url
    url = url.strip()
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return f"https://{url}"


def validate_url_offline(url: str, jd_text: str = "") -> Tuple[bool, str]:
    """
    Validación offline (sin red) — usable en tests y dry-run.

    Reglas alineadas con el gate del orquestador + pre-ingesta:
    - JD > 100 chars → válido
    - agregador → AGREGADOR_VALID
    - tracking params → bloqueado
    - esquema http(s) → VALID
    """
    if jd_text and isinstance(jd_text, str) and len(jd_text.strip()) > 100:
        return True, "JD_ALREADY_EXISTS"

    if not url:
        return False, "MISSING_URL"

    url = normalize_url(url)

    if is_agregador(url):
        return True, "AGREGADOR_VALID"

    lower = url.lower()
    if any(param in lower for param in ("utm_", "gclid", "fbclid", "ref=", "source=")):
        return False, "TRACKING_URL"

    if url.startswith(("http://", "https://")):
        return True, "VALID"

    return False, "INVALID_SCHEME"


def validate_url_pre_ingestion(url: str, jd_text: str = "") -> Tuple[bool, str]:
    """
    GATE pre-ingesta. Intenta HEAD real si `requests` está disponible;
    si no (tests/offline), cae a validate_url_offline.
    """
    # Prioridad JD
    if jd_text and isinstance(jd_text, str) and len(jd_text.strip()) > 100:
        return True, "JD_ALREADY_EXISTS"

    if not url:
        return False, "MISSING_URL"

    url = normalize_url(url)

    try:
        import requests  # type: ignore
    except ImportError:
        return validate_url_offline(url, jd_text)

    if is_agregador(url):
        try:
            agg_response = requests.head(
                url,
                allow_redirects=True,
                timeout=6,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                },
            )
            if agg_response.status_code == 200:
                return True, "AGREGADOR_VERIFIED"
            return True, f"AGREGADOR_RETRY_STATUS_{agg_response.status_code}"
        except requests.exceptions.RequestException:
            return True, "AGREGADOR_RETRY_TIMEOUT"

    # Whitelist career pages problemáticas
    try:
        parsed = urllib.parse.urlparse(url)
        domain = (parsed.netloc or "").lower()
        for problematic in ("jobs.nike.com", "workable.com", "greenhouse.io", "lever.co"):
            if problematic in domain:
                return True, f"WHITELISTED_DOMAIN_{problematic}"
    except Exception:
        pass

    # Offline-safe fallback para el resto (evita colgar tests/CI sin red)
    # El HEAD completo vive en layer_1_run hasta G6; aquí no re-implementamos
    # el scrape de CTA para no duplicar surface de red en ingesta.
    return validate_url_offline(url, jd_text)
