"""
vantage_id_rules.py

Módulo único de reglas de detección DEF/REF/heading/boundary para todo el
ecosistema de scripts VANTAGE L0 que operan sobre IDs del esquema
PREFIX:KEY (generate_census.py, generate_id_inventory.py,
apply_hyperlinks.py, normalize_heading_ids.py).

Por qué existe este módulo (Changelog, sesión 2026-07-25):
    Los 4 scripts reimplementaban cada uno su propia versión de la misma
    lógica (heading_looks_like_def, boundary checks, regex de sección),
    desactualizadas entre sí en momentos distintos. Resultado: cada
    script tenía una noción distinta de "¿es esto una definición
    válida?", lo que producía falsos huérfanos, falsos "sin resolver",
    y auditorías (normalize_heading_ids.py) que sugerían revertir un
    formato ya vigente. Este módulo es la única fuente de verdad; los
    4 scripts DEBEN importar de aquí, nunca reimplementar localmente.

Formato canónico VANTAGE (vigente desde esta sesión — SIN símbolo §):
    Heading de sección padre:
        ## NN PREFIX:KEY
        ## Título Normalizado
    Heading de subsección:
        ## NN.N PREFIX:KEY-NNN
        ## Título Normalizado
    TOC (tabla, SOLO secciones padre, nunca subsecciones):
        | # | PREFIX:KEY [clickable] | Heading Normalizado | Portion |
    Prosa / tablas de cuerpo:
        Cualquier mención de un ID -> [PREFIX:KEY](link)

    Padding: sección padre SIEMPRE 2 dígitos ("01".."21"). Subsección:
    SIN padding en el sufijo decimal ("08.1", nunca "08.01").

    El heading de definición NUNCA se auto-enlaza a sí mismo. Todo lo
    demás (TOC, prosa, tablas de referencia) SÍ debe ser clickeable.
"""

import re

# ─── Prefijos válidos del esquema (unificado — incluye BRIEF:, ausente en
#     generate_id_inventory.py y normalize_heading_ids.py antes de este fix) ──

VALID_PREFIXES = (
    "KERNEL:", "MANUAL:", "CANON:", "CAREER_CANON:", "SP:",
    "ALIASES:", "CHANGELOG:", "CHANGELOG_ARCHIVO:", "BRIEF:",
)

# ─── Patrón de ID genérico (idéntico en los 4 scripts previos, sin cambio) ───

ID_PATTERN = re.compile(r'\b([A-Z][A-Z0-9_]*:[A-Z0-9][A-Z0-9-]*)\b')

# ─── Heading de sección — NUEVO formato sin § ────────────────────────────────
# "NN PREFIX:KEY" (sección padre, 2 dígitos) o "NN.N PREFIX:KEY-NNN"
# (subsección, sufijo decimal SIN padding). El número puede o no ir
# seguido de un separador opcional (espacio simple es el canónico; se
# tolera además guion largo/corto residual de documentos aún no
# migrados, para no romper la detección durante la transición).
SECTION_HEADING_PREFIX_RE = re.compile(r"^\d{1,2}(?:\.\d+)?\s*(?:[—-]\s*)?")

# Igual que arriba pero con grupo de captura, para EXTRAER el número de
# sección real detectado en vivo (reemplaza el valor hardcodeado de
# CENSUS_SPEC cuando ambos están disponibles).
SECTION_HEADING_CAPTURE_RE = re.compile(r"^(\d{1,2}(?:\.\d+)?)\s*(?:[—-]\s*)?")

# Compatibilidad hacia atrás: documentos aún no migrados al formato sin §
# siguen usando "§N — ID" o "§N ID". Se reconoce para no romper la
# detección de documentos en transición, pero NUNCA se genera como
# sugerencia de fix — ver suggest_canonical_heading().
LEGACY_SECTION_HEADING_CAPTURE_RE = re.compile(r"^§([\w.]+)\s*(?:[—-]\s*)?")

# Segunda convención vigente, propia del Manual: heading sin "§" ni "NN",
# arranca directo con número/subnúmero plano seguido de punto y/o espacio
# — ej. "1. OBJETIVO DE VANTAGE · ID: MANUAL:OBJETIVO-001". Se mantiene
# como fallback de detección (no de generación) para no perder headings
# aún no migrados durante la transición de formato.
LEADING_NUMBER_SECTION_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+")

STANDALONE_ID_LINE_RE = re.compile(r'^\s*`?([A-Z][A-Z0-9_]*:[A-Z0-9][A-Z0-9-]*)`?\s*$')
HEADING_RE = re.compile(r'^(?:>\s*)*(#{1,6})\s*(.+?)\s*$')
FENCE_RE = re.compile(r'^\s*```')


# ─── Detección de línea standalone-ID (patrón "### CF01" + "CANON:FACT-001") ─

def line_is_standalone_id(line: str):
    """
    Devuelve el ID encontrado si la línea consiste ÚNICAMENTE en un ID
    (con o sin backticks), o None. Patrón observado en Career Canon:
    un heading corto (alias, ej. "### CF01") seguido de una línea suelta
    con el ID completo del esquema VANTAGE, actuando como anchor de facto.
    """
    m = STANDALONE_ID_LINE_RE.match(line)
    return m.group(1) if m else None


# ─── Boundary checks (fix v9.8.0 — evita que un ID largo cuente como DEF
#     de su ID padre por simple substring match) ─────────────────────────────

def starts_with_id_boundary(text: str, id_str: str) -> bool:
    """
    Como str.startswith(id_str), pero exige que lo que sigue al match no
    continúe el mismo token de ID (letra, dígito, '-', '_' o ':').

    Sin este boundary, "CANON:OUTPUT-CONTRACT-001".startswith("CANON:OUTPUT-CONTRACT")
    es True — un heading que menciona el ID hijo se cuenta erróneamente
    como definición del ID padre homónimo-por-prefijo.
    """
    if not text.startswith(id_str):
        return False
    rest = text[len(id_str):]
    return rest == "" or not (rest[0].isalnum() or rest[0] in "-_:")


def contains_id_boundary(haystack: str, needle: str) -> bool:
    """
    Como `needle in haystack`, pero exige que el carácter inmediatamente
    posterior a la coincidencia no continúe el mismo token de ID.

    Sin esto, "ID: CANON:OUTPUT-CONTRACT-001" contiene como substring
    literal "ID: CANON:OUTPUT-CONTRACT" — una mención de pasada al ID
    hijo se cuenta como definición del ID padre homónimo-por-prefijo.
    """
    idx = haystack.find(needle)
    if idx == -1:
        return False
    end = idx + len(needle)
    if end >= len(haystack):
        return True
    nxt = haystack[end]
    return not (nxt.isalnum() or nxt in "-_:")


# ─── heading_looks_like_def — versión consolidada, boundary-safe ────────────

def heading_looks_like_def(heading_text: str, id_found: str) -> bool:
    """
    Determina si, dentro de un heading, un ID capturado es su DEFINICIÓN.

    Cubre, en orden de prioridad:
      (a) Heading = ID puro: "CANON:ACHIEVEMENTS-001"
      (b) Heading = "NN ID" / "NN.N ID" (formato canónico sin §)
      (c) Heading = "§N — ID" / "§N ID" (formato legacy, transición)
      (d) ID precedido inmediatamente por "ID:" en cualquier posición
          ("... · ID: MANUAL:VANTAGE-RUNTIME-001")

    Todas las variantes usan boundary check — un ID largo (sufijo -001)
    NUNCA cuenta como DEF de su ID padre por simple substring match.
    """
    idx = heading_text.find(id_found)
    if idx == -1:
        return False

    prefix_immediate = heading_text[:idx]

    # (d) precedido inmediatamente por "ID:"
    if re.search(r'ID:?\s*$', prefix_immediate, flags=re.IGNORECASE):
        return True

    # (b)/(c) — quitar prefijo de sección (nuevo NN o legacy §N) y luego
    # exigir boundary-safe match contra lo que quede.
    prefix = SECTION_HEADING_PREFIX_RE.sub("", prefix_immediate)
    prefix = LEGACY_SECTION_HEADING_CAPTURE_RE.sub("", prefix)
    prefix = re.sub(r'^(ID:?)\s*', '', prefix, flags=re.IGNORECASE)
    prefix = prefix.strip('`\u2013\u2014-:. \t')

    if prefix != "":
        return False

    # (a)/(b)/(c) ya redujeron el prefijo a vacío -> confirmar boundary
    # en el resto del heading después del ID (evita que "-001" cuele
    # como DEF de su ID padre homónimo-por-prefijo).
    return starts_with_id_boundary(heading_text[idx:], id_found)


def extract_live_section(plain: str) -> str | None:
    """
    Extrae la sección real ("08", "08.1") del texto crudo de un heading
    de definición. Soporta el formato canónico NUEVO (sin §) y, para
    documentos en transición, el legacy con § y el plano del Manual.
    Devuelve None si ninguna convención aplica.
    """
    stripped = plain.strip("` \n")

    m = SECTION_HEADING_CAPTURE_RE.match(stripped)
    if m:
        return m.group(1)

    m2 = LEGACY_SECTION_HEADING_CAPTURE_RE.match(stripped)
    if m2:
        return f"§{m2.group(1)}"  # se marca explícitamente como legacy

    m3 = LEADING_NUMBER_SECTION_RE.match(stripped)
    if m3:
        return m3.group(1)

    return None


def is_definition_block(plain: str, id_str: str, btype: str) -> bool:
    """
    Determina si el bloque ES la definición del ID (heading o texto que
    arranca con el ID), vs. una mención de pasada. Consolidado desde
    generate_census.py (v9.8.0) + generate_id_inventory.py, con boundary
    check aplicado en TODAS las ramas (antes solo en (a)/(b) de census;
    inventory y apply_hyperlinks no lo tenían en absoluto).
    """
    stripped = plain.strip("` \n")
    heading_body_new = SECTION_HEADING_PREFIX_RE.sub("", stripped)
    heading_body_legacy = LEGACY_SECTION_HEADING_CAPTURE_RE.sub("", stripped)
    is_heading = btype in {"heading_1", "heading_2", "heading_3"}

    return (
        stripped == id_str
        or stripped == f"ID: {id_str}"
        or contains_id_boundary(plain, f"ID: {id_str}")
        or (is_heading and starts_with_id_boundary(plain.lstrip("` "), id_str))
        or (is_heading and starts_with_id_boundary(heading_body_new, id_str))
        or (is_heading and starts_with_id_boundary(heading_body_legacy, id_str))
    )


# ─── Clasificación de heading para normalize_heading_ids.py ─────────────────

def classify_heading(plain: str, id_str: str) -> str:
    """
    Devuelve 'ok_bare', 'ok_sectioned', 'ok_legacy_sectioned',
    'ok_id_label', o 'malformed'.

    'ok_legacy_sectioned' es una clasificación de TRANSICIÓN: el heading
    usa el formato viejo "§N — ID" — técnicamente reconocido (no rompe
    census), pero SIEMPRE se reporta como candidato a migrar al formato
    canónico nuevo ("NN ID"), nunca se acepta como destino final.
    """
    stripped = plain.strip("` \n")

    if f"ID: {id_str}" in plain or stripped == f"ID: {id_str}":
        return "ok_id_label"

    if stripped == id_str:
        return "ok_bare"

    heading_body_new = SECTION_HEADING_PREFIX_RE.sub("", stripped)
    if heading_body_new == id_str or starts_with_id_boundary(heading_body_new, id_str):
        return "ok_sectioned"

    heading_body_legacy = LEGACY_SECTION_HEADING_CAPTURE_RE.sub("", stripped)
    if heading_body_legacy == id_str or starts_with_id_boundary(heading_body_legacy, id_str):
        return "ok_legacy_sectioned"

    return "malformed"


def suggest_canonical_heading(plain: str, id_str: str) -> str:
    """
    Propone la reescritura canónica NUEVA (sin §, padding NN / NN.N sin
    padding en el sufijo decimal). Si no se detecta ningún número de
    sección (ni nuevo ni legacy), propone el ID puro sin prefijo numérico
    — el operador debe asignar manualmente el número de sección correcto
    en ese caso, ya que este script nunca inventa una posición en el TOC.
    """
    stripped = plain.strip("` \n")

    # Intentar extraer número ya presente (nuevo o legacy) para preservarlo
    m_new = SECTION_HEADING_CAPTURE_RE.match(stripped)
    m_legacy = LEGACY_SECTION_HEADING_CAPTURE_RE.match(stripped)

    section_num = None
    consumed_len = 0
    if m_new:
        section_num = m_new.group(1)
        consumed_len = m_new.end()
    elif m_legacy:
        raw = m_legacy.group(1)  # ej. "9.9" o "K.1" (legacy puede usar letras)
        section_num = raw
        consumed_len = m_legacy.end()

    remainder = stripped[consumed_len:]
    remainder = remainder.replace(id_str, "")
    remainder = re.sub(r"^\s*[—-]\s*", "", remainder).strip(" —-")

    if section_num:
        # Normalizar padding: parte entera a 2 dígitos, decimal sin padding.
        if "." in section_num:
            whole, dec = section_num.split(".", 1)
        else:
            whole, dec = section_num, None
        if whole.isdigit():
            whole = whole.zfill(2)
        section_fmt = f"{whole}.{dec}" if dec else whole
        base = f"{section_fmt} {id_str}"
    else:
        base = id_str

    return f"{base} — {remainder}".rstrip(" —") if remainder else base


# ─── Fence detection (para no procesar contenido dentro de ```code```) ──────

def is_fence_line(line: str) -> bool:
    return bool(FENCE_RE.match(line))
