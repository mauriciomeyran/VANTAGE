from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

BASE_DIR = Path(__file__).resolve().parent
CACHE_PATH = BASE_DIR / "notion_cache.json"
METRICS_PATH = BASE_DIR / "notion_metrics.json"

NOTION_VERSION = os.environ.get("NOTION_VERSION", "2022-06-28")

# --- rate limiting ------------------------------------------------------------
# Notion API: ~3 req/s. Espaciamos llamadas reales (no cacheadas) a este ritmo.
MIN_INTERVAL_SECONDS = float(os.environ.get("NOTION_MIN_INTERVAL", "0.35"))

# --- cache ----------------------------------------------------------------------
CACHE_TTL_SECONDS = int(os.environ.get("NOTION_CACHE_TTL", str(60 * 60 * 6)))  # 6h default

# --- retry ----------------------------------------------------------------------
MAX_RETRIES = int(os.environ.get("NOTION_MAX_RETRIES", "3"))
RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


# --- logging ----------------------------------------------------------------------

logger = logging.getLogger("vantage.notion_client")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
    ))
    logger.addHandler(handler)
    logger.setLevel(os.environ.get("VANTAGE_LOG_LEVEL", "INFO"))


# --- error type (reusa el contrato de resolver_layer_v1) -------------------------

class ResolverError(Exception):
    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


# --- token --------------------------------------------------------------------------

def _get_token() -> str:
    token = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")
    if not token:
        raise ResolverError("notion_error", "missing notion api token")
    return token


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {_get_token()}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


# --- metrics ----------------------------------------------------------------------

_metrics: Dict[str, Any] = {
    "requests_total": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "retries": 0,
    "errors_by_status": {},
}


def _load_metrics() -> None:
    global _metrics
    if METRICS_PATH.exists():
        try:
            _metrics.update(json.loads(METRICS_PATH.read_text()))
        except (json.JSONDecodeError, OSError):
            pass


def _save_metrics() -> None:
    try:
        METRICS_PATH.write_text(json.dumps(_metrics, indent=2, ensure_ascii=False))
    except OSError as exc:
        logger.warning("no se pudo guardar metrics: %s", exc)


def get_metrics() -> Dict[str, Any]:
    return dict(_metrics)


def reset_metrics() -> None:
    global _metrics
    _metrics = {
        "requests_total": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "retries": 0,
        "errors_by_status": {},
    }
    _save_metrics()


_load_metrics()


# --- cache ----------------------------------------------------------------------

_cache: Dict[str, Dict[str, Any]] = {}


def _load_cache() -> None:
    global _cache
    if CACHE_PATH.exists():
        try:
            _cache = json.loads(CACHE_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            _cache = {}


def _save_cache() -> None:
    try:
        CACHE_PATH.write_text(json.dumps(_cache, ensure_ascii=False))
    except OSError as exc:
        logger.warning("no se pudo guardar cache: %s", exc)


def _cache_get(key: str) -> Optional[Any]:
    entry = _cache.get(key)
    if entry is None:
        return None
    if time.time() - entry["ts"] > CACHE_TTL_SECONDS:
        return None
    return entry["data"]


def _cache_set(key: str, data: Any) -> None:
    _cache[key] = {"ts": time.time(), "data": data}
    _save_cache()


def clear_cache() -> None:
    global _cache
    _cache = {}
    _save_cache()


_load_cache()


# --- throttle ----------------------------------------------------------------------

_last_request_ts = 0.0


def _throttle() -> None:
    global _last_request_ts
    now = time.time()
    wait = MIN_INTERVAL_SECONDS - (now - _last_request_ts)
    if wait > 0:
        time.sleep(wait)
    _last_request_ts = time.time()


# --- core request with retry + cache + logging + metrics --------------------------

def notion_get(path: str, use_cache: bool = True) -> Dict[str, Any]:
    """
    GET a un path de la API de Notion (ej. '/v1/pages/{id}').
    Aplica cache, throttle, retry con backoff exponencial, logging y metrics.
    401 NUNCA se reintenta -- es error de credenciales, no transitorio.
    """
    import requests

    url = f"https://api.notion.com{path}"
    cache_key = f"GET:{path}"

    if use_cache:
        cached = _cache_get(cache_key)
        if cached is not None:
            _metrics["cache_hits"] += 1
            _save_metrics()
            logger.debug("cache HIT  %s", path)
            return cached
        _metrics["cache_misses"] += 1

    last_exc: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        _throttle()
        start = time.time()
        try:
            resp = requests.get(url, headers=_headers(), timeout=30)
        except requests.RequestException as exc:
            last_exc = exc
            logger.warning("request error (attempt %d/%d) %s: %s", attempt, MAX_RETRIES, path, exc)
            _metrics["retries"] += 1
            _save_metrics()
            time.sleep(2 ** attempt)
            continue

        elapsed = time.time() - start
        _metrics["requests_total"] += 1

        if resp.status_code == 401:
            logger.error("401 unauthorized  %s  (%.2fs)", path, elapsed)
            _metrics["errors_by_status"]["401"] = _metrics["errors_by_status"].get("401", 0) + 1
            _save_metrics()
            raise ResolverError("notion_error", resp.text)

        if resp.status_code in RETRYABLE_STATUSES and attempt < MAX_RETRIES:
            logger.warning(
                "%d retryable  %s  (%.2fs)  attempt %d/%d",
                resp.status_code, path, elapsed, attempt, MAX_RETRIES,
            )
            _metrics["retries"] += 1
            _metrics["errors_by_status"][str(resp.status_code)] = (
                _metrics["errors_by_status"].get(str(resp.status_code), 0) + 1
            )
            _save_metrics()
            time.sleep(2 ** attempt)
            continue

        if resp.status_code >= 400:
            logger.error("%d error  %s  (%.2fs)", resp.status_code, path, elapsed)
            _metrics["errors_by_status"][str(resp.status_code)] = (
                _metrics["errors_by_status"].get(str(resp.status_code), 0) + 1
            )
            _save_metrics()
            raise ResolverError("notion_error", resp.text)

        logger.debug("200 OK  %s  (%.2fs)", path, elapsed)
        data = resp.json()
        if use_cache:
            _cache_set(cache_key, data)
        _save_metrics()
        return data

    _save_metrics()
    raise ResolverError("notion_error", f"max retries exceeded for {path}: {last_exc}")


def _notion_post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST a un path de la API de Notion con retry y metrics."""
    import requests

    url = f"https://api.notion.com{path}"
    last_exc: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        _throttle()
        start = time.time()
        try:
            resp = requests.post(url, headers=_headers(), json=payload, timeout=30)
        except requests.RequestException as exc:
            last_exc = exc
            logger.warning("request error (attempt %d/%d) %s: %s", attempt, MAX_RETRIES, path, exc)
            _metrics["retries"] += 1
            _save_metrics()
            time.sleep(2 ** attempt)
            continue

        elapsed = time.time() - start
        _metrics["requests_total"] += 1

        if resp.status_code == 401:
            logger.error("401 unauthorized  %s  (%.2fs)", path, elapsed)
            _metrics["errors_by_status"]["401"] = _metrics["errors_by_status"].get("401", 0) + 1
            _save_metrics()
            raise ResolverError("notion_error", resp.text)

        if resp.status_code in RETRYABLE_STATUSES and attempt < MAX_RETRIES:
            logger.warning(
                "%d retryable  %s  (%.2fs)  attempt %d/%d",
                resp.status_code, path, elapsed, attempt, MAX_RETRIES,
            )
            _metrics["retries"] += 1
            _metrics["errors_by_status"][str(resp.status_code)] = (
                _metrics["errors_by_status"].get(str(resp.status_code), 0) + 1
            )
            _save_metrics()
            time.sleep(2 ** attempt)
            continue

        if resp.status_code >= 400:
            logger.error("%d error  %s  (%.2fs)", resp.status_code, path, elapsed)
            _metrics["errors_by_status"][str(resp.status_code)] = (
                _metrics["errors_by_status"].get(str(resp.status_code), 0) + 1
            )
            _save_metrics()
            raise ResolverError("notion_error", resp.text)

        logger.debug("200 OK  %s  (%.2fs)", path, elapsed)
        _save_metrics()
        return resp.json()

    _save_metrics()
    raise ResolverError("notion_error", f"max retries exceeded for {path}: {last_exc}")


def _notion_patch(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """PATCH a un path de la API de Notion con retry y metrics."""
    import requests

    url = f"https://api.notion.com{path}"
    last_exc: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        _throttle()
        start = time.time()
        try:
            resp = requests.patch(url, headers=_headers(), json=payload, timeout=30)
        except requests.RequestException as exc:
            last_exc = exc
            logger.warning("request error (attempt %d/%d) %s: %s", attempt, MAX_RETRIES, path, exc)
            _metrics["retries"] += 1
            _save_metrics()
            time.sleep(2 ** attempt)
            continue

        elapsed = time.time() - start
        _metrics["requests_total"] += 1

        if resp.status_code == 401:
            logger.error("401 unauthorized  %s  (%.2fs)", path, elapsed)
            _metrics["errors_by_status"]["401"] = _metrics["errors_by_status"].get("401", 0) + 1
            _save_metrics()
            raise ResolverError("notion_error", resp.text)

        if resp.status_code in RETRYABLE_STATUSES and attempt < MAX_RETRIES:
            logger.warning(
                "%d retryable  %s  (%.2fs)  attempt %d/%d",
                resp.status_code, path, elapsed, attempt, MAX_RETRIES,
            )
            _metrics["retries"] += 1
            _metrics["errors_by_status"][str(resp.status_code)] = (
                _metrics["errors_by_status"].get(str(resp.status_code), 0) + 1
            )
            _save_metrics()
            time.sleep(2 ** attempt)
            continue

        if resp.status_code >= 400:
            logger.error("%d error  %s  (%.2fs)", resp.status_code, path, elapsed)
            _metrics["errors_by_status"][str(resp.status_code)] = (
                _metrics["errors_by_status"].get(str(resp.status_code), 0) + 1
            )
            _save_metrics()
            raise ResolverError("notion_error", resp.text)

        logger.debug("200 OK  %s  (%.2fs)", path, elapsed)
        _save_metrics()
        return resp.json()

    _save_metrics()
    raise ResolverError("notion_error", f"max retries exceeded for {path}: {last_exc}")


# --- Client namespaces -----------------------------------------------------------

class _DataSources:
    """
    Emula client.data_sources de notion-client 3.x.
    data_source_id es equivalente a database_id — Notion mantiene compatibilidad de IDs.
    """

    def query(
        self,
        data_source_id: str,
        start_cursor: Optional[str] = None,
        page_size: int = 100,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"page_size": page_size}
        if start_cursor:
            payload["start_cursor"] = start_cursor
        payload.update(kwargs)
        return _notion_post(f"/v1/databases/{data_source_id}/query", payload)


class _Pages:
    """Emula client.pages de notion-client."""

    def retrieve(self, page_id: str) -> Dict[str, Any]:
        return notion_get(f"/v1/pages/{page_id}", use_cache=False)

    def update(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        return _notion_patch(f"/v1/pages/{page_id}", {"properties": properties})

    def create(self, parent: Dict[str, Any], properties: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"parent": parent, "properties": properties}
        payload.update(kwargs)
        return _notion_post("/v1/pages", payload)


class _Databases:
    """Emula client.databases de notion-client."""

    def retrieve(self, database_id: str) -> Dict[str, Any]:
        return notion_get(f"/v1/databases/{database_id}", use_cache=True)

    def query(
        self,
        database_id: str,
        start_cursor: Optional[str] = None,
        page_size: int = 100,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"page_size": page_size}
        if start_cursor:
            payload["start_cursor"] = start_cursor
        payload.update(kwargs)
        return _notion_post(f"/v1/databases/{database_id}/query", payload)


# --- Client ----------------------------------------------------------------------

class Client:
    """
    Drop-in replacement para notion-client 3.x.
    Implementa los namespaces usados por los scripts de Vantage:
      - client.data_sources.query(data_source_id=..., **kwargs)
      - client.pages.update(page_id=..., properties=...)
      - client.pages.retrieve(page_id=...)
      - client.pages.create(parent=..., properties=...)
      - client.databases.retrieve(database_id=...)
      - client.databases.query(database_id=..., **kwargs)
    """

    def __init__(self, auth: Optional[str] = None, token: Optional[str] = None):
        resolved = auth or token
        if resolved:
            os.environ["NOTION_TOKEN"] = resolved

        self.data_sources = _DataSources()
        self.pages = _Pages()
        self.databases = _Databases()

    def get_metrics(self) -> Dict[str, Any]:
        return get_metrics()

    def clear_cache(self) -> None:
        clear_cache()

    def reset_metrics(self) -> None:
        reset_metrics()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "metrics":
        print(json.dumps(get_metrics(), indent=2, ensure_ascii=False))
    elif len(sys.argv) > 1 and sys.argv[1] == "clear-cache":
        clear_cache()
        print("cache limpiado")
    elif len(sys.argv) > 1 and sys.argv[1] == "reset-metrics":
        reset_metrics()
        print("metrics reiniciados")
    else:
        print("uso: python3 notion_utils.py [metrics|clear-cache|reset-metrics]")
