#!/usr/bin/env python3
"""
VANTAGE Feed Processor — L1 (Active Recon) + L2 (Strategic Search) + L3 (Mail)
Procesa JSON de discovery (you.com/Grok/LinkedIn) → Notion Opportunities DB.

Uso:
  python scripts/feed_processor.py --file feeds/2026-06-06_feed.json --layer 1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.parse
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# feed_processor necesita Client del SDK de PyPI (notion-client),
# no del wrapper local notion_client.py que vive en el mismo directorio.
# Mismo patrón que vantage.py sync() — excluimos scripts/ del path temporalmente.
import sys as _sys, importlib.util as _ilu
_scripts_dir = str(Path(__file__).resolve().parent)
_saved_path = _sys.path[:]
_saved_nc   = _sys.modules.pop("notion_client", None)
_sys.path   = [p for p in _sys.path if p not in (_scripts_dir, ".", "")]
try:
    from notion_client import Client
finally:
    _sys.path = _saved_path
    if _saved_nc is not None:
        _sys.modules["notion_client"] = _saved_nc

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# URL gate (HEAD+GET, agregadores sin CTA) — misma lógica que layer_1_run
from layer_1_run import is_agregador, validate_url_pre_ingestion
from profile_fit import is_role_excluded

_LAYER_1_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_LAYER_1_ROOT / ".env", override=True)

import os  # noqa: E402 — después de load_dotenv

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DB_ID = os.environ["NOTION_DB_OPPORTUNITIES"]
NOTION_ARCHIVE_PAGE_ID = os.environ["NOTION_ARCHIVE_PAGE_ID"]

MONTH_NAMES = [
    "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE",
    "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER",
]

# Jerarquía de dedup cross-layer (v8.0): L1 > L2 > L3
DEDUP_PRIORITY = {"L1": 1, "L2": 2, "L3": 3}

# Hard Blocks (SP §6) — backstop independiente de alias_map.json.
# El mecanismo de resolve_alias()/hard_block sigue activo; esto cubre los
# 3 casos críticos aunque alias_map.json no tenga el flag bien curado.
HARD_BLOCKED_BRANDS = {
    "l'oréal", "loreal", "l'oreal",
    "levi's", "levis", "dockers",
    "el palacio de hierro", "palacio de hierro",
}


def _normalize_brand_text(value: str) -> str:
    if not value:
        return ""
    return value.strip().lower().replace("’", "'").replace("‘", "'")


def is_hard_blocked_brand(value: str) -> str | None:
    """Devuelve el término bloqueado que hizo match, o None si no aplica."""
    normalized = _normalize_brand_text(value)
    for blocked in HARD_BLOCKED_BRANDS:
        if blocked in normalized:
            return blocked
    return None

GENERATED_JOB_ID_RE = re.compile(
    r"^(?:gen[_-]?|auto[_-]?|tmp[_-]?|unknown|n/?a|none|null|)$",
    re.IGNORECASE,
)


# ──────────────────────────────────────────
# Paso 0: sanitize_input
# ──────────────────────────────────────────
def sanitize_input(raw_text: str) -> str:
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = re.sub(r"(?m)^\s*//.*$", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r",\s*([}\]])", r"\1", text)
    text = text.strip()
    json.loads(text)  # validar parseable
    return text


# ──────────────────────────────────────────
# Paso 1: normalize_envelope
# ──────────────────────────────────────────
def normalize_envelope(json_data: dict, layer_cli: int) -> list[dict]:
    # ── GAP-01 · L0 Consolidation guard ────────────────────────────────────────
    # Perplexity (L0) debe consolidar y deduplicar los arrays de L1 y L2 antes de
    # llegar aquí, y setar el flag "consolidated_by_l0": true en el envelope.
    # Si el array mezcla layers sin ese flag, la jerarquía L1 > L2 puede no haberse
    # aplicado — las instancias de L2 podrían prevalecer sobre las de L1.
    #
    # Este warning es informativo: el pipeline continúa, pero el operador debe
    # verificar que el archivo venga del paso de Consolidation & Dedup (Prompt E).
    # Arrays de un solo origen (solo L1 ó solo L2 ó solo L3) son válidos sin flag.
    if isinstance(json_data, dict) and not json_data.get("consolidated_by_l0"):
        layers_in_payload: set[str] = set()
        items_to_check = json_data.get("listings") or []
        if not items_to_check and isinstance(json_data.get("results_by_source"), dict):
            for bucket in json_data["results_by_source"].values():
                if isinstance(bucket, list):
                    items_to_check.extend(bucket)
        for item in items_to_check:
            if isinstance(item, dict) and item.get("layer"):
                layers_to_add = item["layer"] if isinstance(item["layer"], list) else [item["layer"]]
                layers_in_payload.update(layers_to_add)
        mixed_l1_l2 = bool({"L1", "L2"}.issubset(layers_in_payload))
        if mixed_l1_l2:
            print(
                "\n⚠️  GAP-01 WARNING: El array contiene items de L1 y L2 pero no tiene el flag\n"
                "   'consolidated_by_l0: true'. La jerarquía de dedup L1 > L2 puede no haberse\n"
                "   aplicado — instancias de L2 podrían duplicar o prevalecer sobre las de L1.\n"
                "   ACCIÓN RECOMENDADA: Pasa el JSON por Perplexity (Prompt E) antes de\n"
                "   ingestarlo con feed_processor. Si el array es de un solo origen, ignora.\n"
            )
    # ── fin GAP-01 ──────────────────────────────────────────────────────────────

    layer_tag = f"L{layer_cli}"
    records: list[dict] = []

    if "results_by_source" in json_data and isinstance(json_data["results_by_source"], dict):
        for bucket in json_data["results_by_source"].values():
            if isinstance(bucket, list):
                records.extend(bucket)
            elif isinstance(bucket, dict):
                for value in bucket.values():
                    if isinstance(value, list):
                        records.extend(value)
                    elif isinstance(value, dict):
                        records.append(value)
    elif "listings" in json_data and isinstance(json_data["listings"], list):
        records = list(json_data["listings"])
    elif isinstance(json_data, list):
        records = list(json_data)
    else:
        raise ValueError(
            'Envelope no reconocido: se esperaba "results_by_source", "listings" o una lista.'
        )

    for record in records:
        record["layer"] = layer_tag
    return records


# ──────────────────────────────────────────
# Paso 2: coerce_types
# ──────────────────────────────────────────
def coerce_types(records: list[dict]) -> list[dict]:
    for record in records:
        dna = record.get("innovation_dna")
        if isinstance(dna, str):
            lowered = dna.strip().lower()
            if lowered == "true":
                record["innovation_dna"] = True
            elif lowered == "false":
                record["innovation_dna"] = False
    return records


# ──────────────────────────────────────────
# Normalización de campos feed → canónico
# ──────────────────────────────────────────
def _first_nonempty(record: dict, *keys: str) -> str:
    for key in keys:
        val = record.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return ""


def normalize_record_fields(record: dict) -> dict:
    title = _first_nonempty(record, "title", "rol", "role", "Rol")
    brand_raw = _first_nonempty(record, "brand", "marca", "company", "Marca")
    apply_url = _first_nonempty(record, "apply_url", "url", "URL")
    location = _first_nonempty(record, "location", "ubicacion", "city")
    job_id = _first_nonempty(record, "job_id", "JOB_ID")
    jd = _first_nonempty(record, "jd", "jd_snippet", "description", "JD")

    fetch_status = _first_nonempty(record, "fetch_status", "fetch")
    if not fetch_status:
        fetch_status = "aggregator" if is_agregador(apply_url) else "career_page"

    return {
        **record,
        "title": title,
        "brand_raw": brand_raw,
        "apply_url": apply_url,
        "location": location,
        "job_id": job_id,
        "jd": jd,
        "fetch_status": fetch_status,
    }


def normalize_url(url: str) -> str:
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url.strip())
    if not parsed.scheme:
        parsed = urllib.parse.urlparse("https://" + url.strip())
    query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    tracking_prefixes = ("utm_", "gclid", "fbclid", "ref", "source", "clk", "trk")
    filtered = [
        (k, v) for k, v in query_pairs
        if not any(k.lower().startswith(p) or k.lower() == p for p in tracking_prefixes)
    ]
    clean_query = urllib.parse.urlencode(filtered)
    path = parsed.path.rstrip("/") or "/"
    netloc = parsed.netloc.lower()
    return urllib.parse.urlunparse((parsed.scheme.lower(), netloc, path, "", clean_query, ""))


def is_generated_job_id(job_id: str) -> bool:
    if not job_id or not str(job_id).strip():
        return True
    return bool(GENERATED_JOB_ID_RE.match(str(job_id).strip()))


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def composite_key(record: dict) -> str:
    brand = (record.get("brand") or record.get("brand_raw") or "").strip().lower()
    title = (record.get("title") or "").strip().lower()
    location = (record.get("location") or "").strip().lower()
    return f"{brand}|{title}|{location}"


def compute_dedup_hash(record: dict) -> str:
    """Hash robusto cross-layer (SHA-256)."""
    fetch_status = record.get("fetch_status", "")

    if fetch_status == "career_page":
        url = normalize_url(record.get("apply_url") or "")
        if url:
            return sha256_hex(f"url:{url}")

    if fetch_status == "aggregator":
        return sha256_hex(f"agg:{composite_key(record)}")

    job_id = record.get("job_id") or ""
    if job_id and not is_generated_job_id(job_id):
        return sha256_hex(f"job_id:{job_id}")

    return sha256_hex(f"fallback:{composite_key(record)}")


# ──────────────────────────────────────────
# Notion schema (Class A v7.5 + fallback legacy)
# ──────────────────────────────────────────
@dataclass
class NotionSchema:
    """Resuelve nombres Class A → propiedades reales en la DB."""

    properties: dict[str, dict]

    @classmethod
    def load(cls, notion_client: Client) -> NotionSchema:
        ds = notion_client.databases.retrieve(database_id=NOTION_DB_ID)
        return cls(properties=ds.get("properties", {}))

    def _pick(self, *candidates: str) -> str | None:
        for name in candidates:
            if name in self.properties:
                return name
        return None

    @property
    def title_prop(self) -> str:
        return self._pick("title", "Rol") or "title"

    @property
    def brand_prop(self) -> str:
        return self._pick("brand", "Marca") or "brand"

    @property
    def brand_type(self) -> str:
        return self.properties.get(self.brand_prop, {}).get("type", "rich_text")

    @property
    def url_prop(self) -> str:
        return self._pick("apply_url", "URL") or "apply_url"

    @property
    def status_prop(self) -> str:
        return self._pick("status", "Status") or "status"

    @property
    def notes_prop(self) -> str:
        return self._pick("notes", "Notas") or "notes"

    @property
    def location_prop(self) -> str | None:
        return self._pick("location", "Texto")

    @property
    def hash_prop(self) -> str | None:
        return self._pick("hash")

    @property
    def layer_prop(self) -> str | None:
        return self._pick("layer")

    @property
    def fetch_status_prop(self) -> str | None:
        return self._pick("fetch_status")

    @property
    def fuente_prop(self) -> str | None:
        return self._pick("Fuente")

    @property
    def holding_prop(self) -> str | None:
        return self._pick("holding", "Holding")

    def text_filter(self, prop: str, value: str) -> dict:
        ptype = self.properties.get(prop, {}).get("type", "rich_text")
        if ptype == "select":
            return {"property": prop, "select": {"equals": value}}
        if ptype == "title":
            return {"property": prop, "title": {"equals": value}}
        return {"property": prop, "rich_text": {"equals": value}}

    def rich_text_value(self, text: str) -> dict:
        return {"rich_text": [{"text": {"content": text[:2000]}}]}

    def prop_text_value(self, prop: str, text: str) -> dict:
        ptype = self.properties.get(prop, {}).get("type", "rich_text")
        if ptype == "rich_text":
            return self.rich_text_value(text)
        if ptype == "title":
            return {"title": [{"text": {"content": text[:2000]}}]}
        return self.rich_text_value(text)

    def select_value(self, name: str) -> dict:
        return {"select": {"name": name}}

    def warn_missing_class_a(self) -> None:
        if not self.hash_prop:
            print("⚠️  WARNING: propiedad 'hash' no encontrada en schema — "
                  "hash irá a Notas (fallback silencioso evitado en log)")
        if not self.layer_prop:
            print("⚠️  WARNING: propiedad 'layer' no encontrada en schema — "
                  "layer irá a Notas")

    def brand_value(self, brand: str) -> dict:
        if self.brand_type == "select":
            return self.select_value(brand[:100])
        return self.rich_text_value(brand[:200])


# ──────────────────────────────────────────
# Notion query helper (notion-client 3.x)
# ──────────────────────────────────────────
def query_notion_db(
    notion_client: Client,
    *,
    filter_body: dict | None = None,
    schema: NotionSchema | None = None,
) -> list[dict]:
    # FIX v8.2 — multi-source DB (databases.query) puede devolver el mismo cursor
    # en loop infinito cuando la DB fue migrada a multi-source. Dos defensas:
    #   1. seen_cursors: detecta cursor repetido y aborta en la primera repetición.
    #   2. MAX_PAGES: freno de emergencia absoluto (dedup filtrado no necesita > 20 páginas).
    # Para queries filtradas (hash/URL/brand+title), 1–2 páginas son suficientes.
    # No se migra a data_sources/.../query porque esa API no soporta filtros arbitrarios.
    MAX_PAGES = 20
    seen_cursors: set[str] = set()
    page_num = 0

    all_results: list[dict] = []
    kwargs: dict[str, Any] = {}
    if filter_body:
        kwargs["filter"] = filter_body

    while True:
        page_num += 1
        if page_num > MAX_PAGES:
            print(f"  ⚠️  query_notion_db: MAX_PAGES ({MAX_PAGES}) alcanzado — abortando paginación")
            break
        try:
            response = notion_client.databases.query(database_id=NOTION_DB_ID, **kwargs)
        except Exception as exc:
            if schema and "property" in str(exc):
                return []
            raise
        all_results.extend(response.get("results", []))
        cursor = response.get("next_cursor")
        if response.get("has_more") and cursor:
            if cursor in seen_cursors:
                print(f"  ⚠️  query_notion_db: cursor repetido detectado — loop infinito abortado")
                break
            seen_cursors.add(cursor)
            kwargs["start_cursor"] = cursor
        else:
            break
    return all_results


# ──────────────────────────────────────────
# Paso 3: dedup_cross_layer
# ──────────────────────────────────────────
def _get_existing_layer(page: dict, schema: NotionSchema) -> str | None:
    """Extrae el valor del campo layer de una página Notion existente."""
    if not schema.layer_prop:
        return None
    props = page.get("properties", {})
    layer_field = props.get(schema.layer_prop, {})
    return layer_field.get("select", {}).get("name") if layer_field else None


def _upgrade_layer_if_needed(
    existing_page: dict,
    incoming_layer: str,
    notion_client: Client,
    schema: NotionSchema,
) -> None:
    """Si el registro entrante tiene mayor prioridad (menor número), actualiza el layer en Notion."""
    existing_layer = _get_existing_layer(existing_page, schema)
    if not existing_layer or not schema.layer_prop:
        return
    incoming_priority = DEDUP_PRIORITY.get(incoming_layer, 99)
    existing_priority = DEDUP_PRIORITY.get(existing_layer, 99)
    if incoming_priority < existing_priority:
        page_id = existing_page["id"]
        try:
            notion_client.pages.update(
                page_id=page_id,
                properties={schema.layer_prop: {"select": {"name": incoming_layer}}},
            )
            print(f"  🔄 Layer upgrade: {existing_layer} → {incoming_layer} ({page_id[:8]}...)")
        except Exception as exc:
            print(f"  ⚠️  Layer upgrade fallido para {page_id[:8]}: {exc}")


def dedup_cross_layer(
    record: dict,
    notion_client: Client,
    schema: NotionSchema,
    window_days: int = 30,
) -> bool:
    hash_key = compute_dedup_hash(record)
    incoming_layer = record.get("layer", "L3")

    if schema.hash_prop:
        hash_type = schema.properties[schema.hash_prop].get("type", "rich_text")
        if hash_type == "rich_text":
            filt = {"property": schema.hash_prop, "rich_text": {"equals": hash_key}}
        else:
            filt = schema.text_filter(schema.hash_prop, hash_key)
        existing = query_notion_db(notion_client, filter_body=filt, schema=schema)
        if existing:
            _upgrade_layer_if_needed(existing[0], incoming_layer, notion_client, schema)
            return True

    apply_url = record.get("apply_url") or ""
    if apply_url.startswith("http"):
        url_matches = query_notion_db(
            notion_client,
            filter_body={"property": schema.url_prop, "url": {"equals": apply_url}},
            schema=schema,
        )
        if url_matches:
            _upgrade_layer_if_needed(url_matches[0], incoming_layer, notion_client, schema)
            return True

    brand = record.get("brand") or record.get("brand_raw") or ""
    title = record.get("title") or ""
    if not brand or not title:
        return False

    time_filter = {"past_month": {}} if window_days >= 28 else {"past_week": {}}
    recent = query_notion_db(
        notion_client,
        filter_body={
            "and": [
                {"timestamp": "created_time", "created_time": time_filter},
                schema.text_filter(schema.brand_prop, brand),
                schema.text_filter(schema.title_prop, title),
            ]
        },
        schema=schema,
    )
    if recent:
        _upgrade_layer_if_needed(recent[0], incoming_layer, notion_client, schema)
        return True
    return False


# ──────────────────────────────────────────
# Paso 4: alias_map lookup
# ──────────────────────────────────────────
def load_alias_map() -> dict:
    path = _LAYER_1_ROOT / "config" / "alias_map.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def resolve_alias(brand_raw: str, alias_data: dict) -> tuple[str | None, str | None, bool | None]:
    """
    Retorna (marca_canónica, holding, hard_block).
    hard_block=None → alias no encontrado.
    """
    if not brand_raw:
        return None, None, None
    key = brand_raw.strip().lower()
    aliases = alias_data.get("aliases", {})
    entry = aliases.get(key)
    if not entry:
        for alias_key, alias_val in aliases.items():
            if alias_key in key or key in alias_key:
                entry = alias_val
                break
    if not entry:
        return None, None, None
    return entry.get("marca"), entry.get("holding"), entry.get("hard_block", False)


# ──────────────────────────────────────────
# Paso 5: URL_GATE
# ──────────────────────────────────────────
def run_url_gate(record: dict) -> tuple[bool, str]:
    apply_url = record.get("apply_url") or ""
    if not apply_url:
        return False, "MISSING_URL"

    if record.get("fetch_status") == "aggregator":
        is_valid, reason = validate_url_pre_ingestion(apply_url, record.get("jd", ""))
        if is_valid:
            return True, reason
        return False, reason

    is_valid, reason = validate_url_pre_ingestion(apply_url, record.get("jd", ""))
    return is_valid, reason


# ──────────────────────────────────────────
# Procesamiento por registro
# ──────────────────────────────────────────
@dataclass
class ProcessedRecord:
    record: dict
    hash_key: str
    disposition: str  # CLEAN | BLOCKED | REVIEW_NEEDED
    notes: str = ""
    brand: str = ""
    holding: str = ""


def process_record(
    raw: dict,
    notion_client: Client,
    schema: NotionSchema,
    alias_data: dict,
) -> ProcessedRecord:
    # ── GAP-03 · REVIEW_NEEDED resolution contract ──────────────────────────────
    # feed_processor.py asigna disposition="REVIEW_NEEDED" cuando una entrada
    # no puede procesarse completamente (alias sin resolver, URL parcial,
    # semi-duplicado cross-layer). Estas entradas SE ESCRIBEN en Notion con
    # Status="REVIEW_NEEDED" y sus campos Class B quedan BLOQUEADOS — Python no
    # los calcula hasta que el operador resuelva el problema.
    #
    # CONTRATO DE RESOLUCIÓN (Kernel §10):
    #   1. El operador abre la entrada en Notion y corrige el campo problemático
    #      (URL parcial → URL completa, alias ambiguo → marca canónica).
    #   2. El operador cambia Status → "Target".
    #   3. El operador corre: ~/vantage_pipeline.sh
    #   4. layer_1_run.py detecta Status="Target" en entradas que tenían
    #      Gate vacío o REVIEW_NEEDED y procesa sus campos Class B normalmente.
    #
    # "Target" es el ÚNICO valor de Status reconocido como señal de resolución.
    # Cualquier otro valor (ej. dejar "REVIEW_NEEDED") mantiene el bloqueo.
    # Ver también: layer_1_run.py — lógica de gate() y scoring sobre entradas
    # con Status="Target".
    # ── fin GAP-03 ──────────────────────────────────────────────────────────────
    record = normalize_record_fields(raw)
    hash_key = compute_dedup_hash(record)
    brand_raw = record.get("brand_raw", "")

    blocked_match = is_hard_blocked_brand(brand_raw)
    if blocked_match:
        print(f"  ⚠️  HARD_BLOCK: {brand_raw}")
        return ProcessedRecord(
            record=record,
            hash_key=hash_key,
            disposition="BLOCKED",
            notes=f"HARD_BLOCK: {brand_raw}",
            brand=brand_raw,
        )

    marca, holding, hard_block = resolve_alias(brand_raw, alias_data)
    if hard_block is True:
        return ProcessedRecord(
            record=record,
            hash_key=hash_key,
            disposition="BLOCKED",
            notes=f"hard_block alias: {brand_raw}",
            brand=marca or brand_raw,
        )

    excluded = is_role_excluded(record.get("title") or "")
    if excluded:
        return ProcessedRecord(
            record=record,
            hash_key=hash_key,
            disposition="BLOCKED",
            notes=f"exclude role: {excluded}",
            brand=marca or brand_raw,
        )

    if marca:
        record["brand"] = marca
        record["holding"] = holding or ""
    else:
        record["brand"] = brand_raw
        if brand_raw:
            return ProcessedRecord(
                record=record,
                hash_key=hash_key,
                disposition="REVIEW_NEEDED",
                notes=f"alias no resuelto: {brand_raw}",
                brand=brand_raw,
            )
        return ProcessedRecord(
            record=record,
            hash_key=hash_key,
            disposition="REVIEW_NEEDED",
            notes="marca vacía",
            brand="",
        )

    if dedup_cross_layer(record, notion_client, schema):
        return ProcessedRecord(
            record=record,
            hash_key=hash_key,
            disposition="REVIEW_NEEDED",
            notes="semi-duplicate (dedup cross-layer)",
            brand=record["brand"],
            holding=holding or "",
        )

    url_ok, url_reason = run_url_gate(record)
    if not url_ok:
        return ProcessedRecord(
            record=record,
            hash_key=hash_key,
            disposition="REVIEW_NEEDED",
            notes=f"URL_GATE: {url_reason}",
            brand=record["brand"],
            holding=holding or "",
        )

    if not record.get("title"):
        return ProcessedRecord(
            record=record,
            hash_key=hash_key,
            disposition="REVIEW_NEEDED",
            notes="título vacío",
            brand=record["brand"],
            holding=holding or "",
        )

    return ProcessedRecord(
        record=record,
        hash_key=hash_key,
        disposition="CLEAN",
        brand=record["brand"],
        holding=holding or "",
    )


# ──────────────────────────────────────────
# Paso 6: DRY RUN
# ──────────────────────────────────────────
def format_dryrun_table(processed: list[ProcessedRecord]) -> str:
    lines = [
        "| Disposition | Brand | Title | Location | Hash (8) | Notes |",
        "|---|---|---|---|---|---|",
    ]
    for p in processed:
        rec = p.record
        title = (rec.get("title") or "")[:40]
        loc = (rec.get("location") or "")[:20]
        lines.append(
            f"| {p.disposition} | {p.brand[:20]} | {title} | {loc} | {p.hash_key[:8]} | {p.notes[:40]} |"
        )
    return "\n".join(lines)


def write_dryrun_file(processed: list[ProcessedRecord], layer_cli: int) -> Path:
    today = date.today().isoformat()
    feeds_dir = _LAYER_1_ROOT / "feeds"
    feeds_dir.mkdir(exist_ok=True)
    path = feeds_dir / f"{today}_dryrun.md"

    clean = sum(1 for p in processed if p.disposition == "CLEAN")
    blocked = sum(1 for p in processed if p.disposition == "BLOCKED")
    review = sum(1 for p in processed if p.disposition == "REVIEW_NEEDED")

    body = f"""# DRY RUN · {today} · Layer L{layer_cli}

**Resumen:** {clean} limpio · {blocked} BLOCKED · {review} REVIEW_NEEDED

{format_dryrun_table(processed)}
"""
    path.write_text(body, encoding="utf-8")
    return path


def print_dryrun_summary(processed: list[ProcessedRecord], layer_cli: int) -> None:
    clean = sum(1 for p in processed if p.disposition == "CLEAN")
    blocked = sum(1 for p in processed if p.disposition == "BLOCKED")
    review = sum(1 for p in processed if p.disposition == "REVIEW_NEEDED")

    print(f"\n{'=' * 72}")
    print(f"DRY RUN · Layer L{layer_cli}")
    print(f"{'=' * 72}")
    print(format_dryrun_table(processed))
    print(f"\n{clean} limpio · {blocked} BLOCKED · {review} REVIEW_NEEDED")
    print(f"{'=' * 72}\n")


# ──────────────────────────────────────────
# Paso 8: Write to Notion
# ──────────────────────────────────────────
def build_notion_properties(p: ProcessedRecord, schema: NotionSchema) -> dict:
    rec = p.record
    status = "Target" if p.disposition == "CLEAN" else "REVIEW_NEEDED"
    layer = rec.get("layer", "L1")
    fetch = rec.get("fetch_status", "career_page")

    props: dict[str, Any] = {
        schema.title_prop: {
            "title": [{"text": {"content": (rec.get("title") or "Sin título")[:200]}}]
        },
        schema.brand_prop: schema.brand_value(p.brand),
        schema.status_prop: schema.select_value(status),
    }

    if schema.hash_prop:
        props[schema.hash_prop] = schema.prop_text_value(schema.hash_prop, p.hash_key)

    if schema.layer_prop:
        props[schema.layer_prop] = schema.select_value(layer)

    if schema.fetch_status_prop:
        props[schema.fetch_status_prop] = schema.select_value(fetch)
    elif schema.fuente_prop:
        fuente = "Agregador" if fetch == "aggregator" else "Career Page Oficial"
        props[schema.fuente_prop] = schema.rich_text_value(fuente)

    if schema.location_prop and rec.get("location"):
        props[schema.location_prop] = schema.rich_text_value(rec["location"])

    if schema.holding_prop and (p.holding or rec.get("holding")):
        props[schema.holding_prop] = schema.rich_text_value(p.holding or rec.get("holding", ""))

    apply_url = rec.get("apply_url") or ""
    if apply_url.startswith("http"):
        props[schema.url_prop] = {"url": apply_url}

    if "Source_Type " in schema.properties:
        props["Source_Type "] = schema.select_value("Vacante")

    # Prioridad default para entradas nuevas (Class A — §8 Kernel)
    # Default 4 alineado con FAST defaults §14. El operador ajusta manualmente en Notion.
    if "Prioridad" in schema.properties:
        props["Prioridad"] = schema.select_value("4")

    notes_parts = []
    if p.notes:
        notes_parts.append(p.notes)
    if not schema.layer_prop:
        notes_parts.append(f"layer: {layer}")
    if not schema.hash_prop:
        notes_parts.append(f"hash: {p.hash_key}")
    if rec.get("innovation_dna") is True:
        notes_parts.append("innovation_dna: true")
    if notes_parts:
        props[schema.notes_prop] = schema.rich_text_value(" · ".join(notes_parts))

    return props


def write_to_notion(
    notion_client: Client,
    processed: list[ProcessedRecord],
    schema: NotionSchema,
) -> tuple[int, int]:
    written = 0
    failed = 0
    for p in processed:
        if p.disposition == "BLOCKED":
            continue
        if p.disposition not in ("CLEAN", "REVIEW_NEEDED"):
            continue
        try:
            notion_client.pages.create(
                parent={"database_id": NOTION_DB_ID},
                properties=build_notion_properties(p, schema),
            )
            written += 1
            label = f"{p.record.get('title', '')[:40]} @ {p.brand}"
            print(f"  ✅ {label} → {p.disposition}")
        except Exception as exc:
            failed += 1
            print(f"  ❌ Error escribiendo {p.brand}: {exc}")
    return written, failed


# ──────────────────────────────────────────
# Paso 9: Archive DRY RUN en Notion
# ──────────────────────────────────────────
def _month_page_title(d: date) -> str:
    return f"{d.strftime('%Y-%m')} {MONTH_NAMES[d.month - 1]}"


def _find_child_page(notion_client: Client, parent_id: str, title: str) -> dict | None:
    cursor = None
    while True:
        kwargs: dict[str, Any] = {"page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        resp = notion_client.blocks.children.list(block_id=parent_id, **kwargs)
        for block in resp.get("results", []):
            if block.get("type") != "child_page":
                continue
            child_title = ""
            child_page = block.get("child_page", {})
            for t in child_page.get("title", []):
                # Resiliente: maneja string simple Y Notion Rich Text Object
                child_title += t if isinstance(t, str) else t.get("plain_text", "")
            if child_title.strip() == title:
                return {"id": block["id"], "title": child_title}
        if resp.get("has_more") and resp.get("next_cursor"):
            cursor = resp["next_cursor"]
        else:
            break
    return None


def _markdown_to_blocks(markdown: str) -> list[dict]:
    blocks: list[dict] = []
    for line in markdown.splitlines():
        if not line.strip():
            continue
        if line.startswith("# "):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": line[2:][:2000]}}]},
            })
        elif line.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": line[3:][:2000]}}]},
            })
        elif line.startswith("|"):
            blocks.append({
                "object": "block",
                "type": "code",
                "code": {"rich_text": [{"type": "text", "text": {"content": line[:2000]}}], "language": "plain text"},
            })
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": line[:2000]}}]},
            })
    return blocks[:100]


def archive_dryrun_notion(
    notion_client: Client,
    dryrun_path: Path,
    layer_cli: int,
) -> str | None:
    today = date.today()
    month_title = _month_page_title(today)
    dryrun_title = f"DRY RUN · {today.isoformat()} · Layer L{layer_cli}"

    month_page = _find_child_page(notion_client, NOTION_ARCHIVE_PAGE_ID, month_title)
    if not month_page:
        created = notion_client.pages.create(
            parent={"database_id": NOTION_ARCHIVE_PAGE_ID},
            properties={"title": {"title": [{"text": {"content": month_title}}]}},
        )
        month_page_id = created["id"]
        print(f"  📁 Creada página mensual: {month_title}")
    else:
        month_page_id = month_page["id"]

    markdown = dryrun_path.read_text(encoding="utf-8")
    blocks = _markdown_to_blocks(markdown)

    page = notion_client.pages.create(
        parent={"page_id": month_page_id},
        properties={"title": {"title": [{"text": {"content": dryrun_title}}]}},
        children=blocks[:100],
    )
    url = page.get("url", "")
    print(f"  📎 Archivado DRY RUN: {dryrun_title}")
    return url


# ──────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="VANTAGE Feed Processor")
    parser.add_argument("--file", required=True, help="Ruta al JSON de feed")
    parser.add_argument("--layer", type=int, default=1, choices=[1, 2, 3], help="Layer (1, 2 o 3)")
    parser.add_argument(
        "--fast",
        action="store_true",
        default=False,
        help=(
            "Modo FAST: procesa exactamente 1 vacante puntual fuera del ciclo semanal. "
            "El array debe contener un solo item. Para lotes, usa FEED sin --fast."
        ),
    )
    args = parser.parse_args()

    feed_path = Path(args.file)
    if not feed_path.is_absolute():
        feed_path = _LAYER_1_ROOT / feed_path
    if not feed_path.exists():
        print(f"❌ Archivo no encontrado: {feed_path}")
        sys.exit(1)

    print(f"🚀 VANTAGE Feed Processor — Layer L{args.layer}")
    print(f"   Archivo: {feed_path.name}")

    raw_text = feed_path.read_text(encoding="utf-8")
    try:
        clean_json = sanitize_input(raw_text)
        json_data = json.loads(clean_json)
    except json.JSONDecodeError as exc:
        print(f"❌ JSON inválido tras sanitize_input: {exc}")
        sys.exit(1)

    # ── GAP-02 · FAST length guard ──────────────────────────────────────────────
    # El trigger FAST acepta exactamente 1 vacante puntual fuera del ciclo semanal.
    # Si el array tiene más de 1 item y --fast está activo, se rechaza la operación.
    # Para procesar más de una vacante, usa FEED (sin --fast).
    if args.fast:
        raw_list = json_data if isinstance(json_data, list) else json_data.get("listings", [])
        if len(raw_list) != 1:
            print(
                f"\n❌ FAST ERROR: El modo --fast acepta exactamente 1 vacante.\n"
                f"   Array recibido: {len(raw_list)} item(s).\n"
                f"   Si necesitas procesar más de una vacante, usa FEED sin --fast:\n"
                f"   python scripts/feed_processor.py --file {args.file} --layer {args.layer}\n"
            )
            sys.exit(1)
        print("   Modo: FAST (vacante puntual · longitud 1 ✓)")
    # ── fin GAP-02 ──────────────────────────────────────────────────────────────

    records = normalize_envelope(json_data, args.layer)
    records = coerce_types(records)
    print(f"   Registros en envelope: {len(records)}")

    alias_data = load_alias_map()
    notion_client = Client(auth=NOTION_TOKEN)
    schema = NotionSchema.load(notion_client)
    print(f"   Notion schema: {len(schema.properties)} propiedades"
          f" (hash→{schema.hash_prop or 'Notas'}, layer→{schema.layer_prop or 'Notas'})")
    schema.warn_missing_class_a()

    processed = [process_record(r, notion_client, schema, alias_data) for r in records]

    print_dryrun_summary(processed, args.layer)
    dryrun_path = write_dryrun_file(processed, args.layer)
    print(f"📄 DRY RUN guardado: {dryrun_path}")

    to_write = [p for p in processed if p.disposition in ("CLEAN", "REVIEW_NEEDED")]
    n_write = len(to_write)

    confirm = input(f"¿Aprobar escritura de {n_write} vacantes en Notion? [s/N]: ").strip().lower()
    if confirm != "s":
        print("⏹️  Escritura abortada por el operador.")
        print("\n📦 Archivando DRY RUN en Notion...")
        archive_dryrun_notion(notion_client, dryrun_path, args.layer)
        sys.exit(0)

    print(f"\n📝 Escribiendo {n_write} registros en Notion...")
    written, failed = write_to_notion(notion_client, processed, schema)
    print(f"\n✅ Escritos: {written}  |  ❌ Fallidos: {failed}")

    print("\n📦 Archivando DRY RUN en Notion...")
    archive_dryrun_notion(notion_client, dryrun_path, args.layer)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Cancelado por usuario")
        sys.exit(1)