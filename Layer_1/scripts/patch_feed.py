import os

target_path = '/Users/mauriciomeyran/Documents/03 Projects/VANTAGE/Layer_1/scripts/feed_processor.py'

# Bloque nuevo de funciones
patch = """
def normalize_url(url: str) -> str:
    if not url: return ""
    parsed = urllib.parse.urlparse(url.strip())
    if not parsed.scheme: parsed = urllib.parse.urlparse("https://" + url.strip())
    query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    tracking_prefixes = ("utm_", "gclid", "fbclid", "ref", "source", "clk", "trk")
    filtered = [(k, v) for k, v in query_pairs if not any(k.lower().startswith(p) or k.lower() == p for p in tracking_prefixes)]
    clean_query = urllib.parse.urlencode(filtered)
    path = (parsed.path.rstrip("/") or "/").lower()
    netloc = parsed.netloc.lower()
    return urllib.parse.urlunparse((parsed.scheme.lower(), netloc, path, "", clean_query, ""))

def _extract_text_prop(page: dict, schema: NotionSchema, prop_name: str) -> str:
    field = page.get("properties", {}).get(prop_name, {})
    ftype = field.get("type")
    if ftype == "rich_text": return "".join(t.get("plain_text", "") for t in field.get("rich_text", []))
    if ftype == "title": return "".join(t.get("plain_text", "") for t in field.get("title", []))
    if ftype == "select": return (field.get("select") or {}).get("name", "")
    if ftype == "url": return field.get("url") or ""
    return ""

def dedup_cross_layer(record: dict, notion_utils: Client, schema: NotionSchema, window_days: int = 30) -> bool:
    hash_key = compute_dedup_hash(record)
    incoming_layer = record.get("layer", "L3")
    time_filter = {"past_month": {}} if window_days >= 28 else {"past_week": {}}
    
    if schema.hash_prop:
        hash_type = schema.properties[schema.hash_prop].get("type", "rich_text")
        filt = ({"property": schema.hash_prop, "rich_text": {"equals": hash_key}} if hash_type == "rich_text" else schema.text_filter(schema.hash_prop, hash_key))
        existing = query_notion_db(notion_utils, filter_body=filt, schema=schema)
        if existing:
            _upgrade_layer_if_needed(existing[0], incoming_layer, notion_utils, schema)
            return True
            
    apply_url_norm = normalize_url(record.get("apply_url") or "")
    if apply_url_norm:
        url_candidates = query_notion_db(notion_utils, filter_body={"and": [{"timestamp": "created_time", "created_time": time_filter}, {"property": schema.url_prop, "url": {"is_not_empty": True}}]}, schema=schema)
        for page in url_candidates:
            existing_url = _extract_text_prop(page, schema, schema.url_prop)
            if normalize_url(existing_url) == apply_url_norm:
                _upgrade_layer_if_needed(page, incoming_layer, notion_utils, schema)
                return True
                
    brand = (record.get("brand") or record.get("brand_raw") or "").strip().lower()
    title = (record.get("title") or "").strip().lower()
    if not brand or not title: return False
    recent = query_notion_db(notion_utils, filter_body={"timestamp": "created_time", "created_time": time_filter}, schema=schema)
    for page in recent:
        existing_brand = _extract_text_prop(page, schema, schema.brand_prop).strip().lower()
        existing_title = _extract_text_prop(page, schema, schema.title_prop).strip().lower()
        if existing_brand == brand and existing_title == title:
            _upgrade_layer_if_needed(page, incoming_layer, notion_utils, schema)
            return True
    return False
"""

with open(target_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if "def normalize_url" in line: skip = True
    if "def dedup_cross_layer" in line: skip = True
    if "return False # end of dedup" in line: # Marcador de seguridad si existiera
        skip = False
        continue
    if not skip: new_lines.append(line)
    if "return False" in line and "def dedup_cross_layer" in "".join(lines[lines.index(line)-10:lines.index(line)+5]):
        skip = False

with open(target_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
    f.write(patch)

print("Patch aplicado con éxito.")