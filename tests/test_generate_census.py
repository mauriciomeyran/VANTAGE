"""Regresión de Layer_1/scripts/generate_census.py.

Cubre los hallazgos A1–A8 de
handoffs/VALIDACION_GENERATE_CENSUS_Y_LAYER4_2026-10-02.md.
Sin red: `requests` siempre va con doble.
"""
from __future__ import annotations

import ast
import builtins
import shutil
from pathlib import Path

import pytest

from conftest import CENSUS_SRC, load_module_from


# ─────────────────────────────────────────────────────────────────────────────
# Extracción de IDs y secciones (comportamiento ya correcto — se protege)
# ─────────────────────────────────────────────────────────────────────────────

def test_extract_ids_quita_puntuacion_y_conserva_fronteras(census_module):
    rt = [{"plain_text": "Ver (KERNEL:PURPOSE), KERNEL:PURPOSE-001 y KERNEL:PURPOSE-001X."}]
    assert census_module.extract_ids_from_rich_text(rt) == [
        "KERNEL:PURPOSE",
        "KERNEL:PURPOSE-001",
        "KERNEL:PURPOSE-001X",
    ]


def test_is_definition_block_no_confunde_prefijos(census_module):
    assert census_module.is_definition_block(
        "01.4 SP:BOOTLOADER-004 — Agente Principal", "SP:BOOTLOADER-004", "heading_3")
    assert not census_module.is_definition_block(
        "01.4 SP:BOOTLOADER-004X — otro", "SP:BOOTLOADER-004", "heading_3")


def test_extract_live_section(census_module):
    assert census_module.extract_live_section("03.1 KERNEL:DOCUMENTATION-001 — Canonical") == "03.1"
    assert census_module.extract_live_section("03 KERNEL:DOCUMENTATION") == "03"


# ─────────────────────────────────────────────────────────────────────────────
# A4 — filas de tabla con '---' dentro de una celda
# ─────────────────────────────────────────────────────────────────────────────

def test_tabla_no_pierde_filas_con_guiones_en_una_celda(census_module):
    md_table = [
        "| ID | Sección | Nombre |",
        "|---|---|---|",
        "| `KERNEL:A` | 01 | Fila normal |",
        "| `KERNEL:B` | 02 | URL https://x.dev/a---b |",
    ]
    blocks = census_module.markdown_table_to_notion_blocks(md_table)
    rows = blocks[0]["table"]["children"]
    assert len(rows) == 3, "header + 2 filas de datos"

    textos = [
        "".join(s["text"]["content"] for s in r["table_row"]["cells"][0])
        for r in rows[1:]
    ]
    assert textos == ["KERNEL:A", "KERNEL:B"]


# ─────────────────────────────────────────────────────────────────────────────
# A3 — paginación al leer bloques de la página
# ─────────────────────────────────────────────────────────────────────────────

def test_fetch_all_children_pagina(census_module, fake_responses, monkeypatch):
    fake = fake_responses(get_payloads=[
        {"results": [{"id": f"b{i}"} for i in range(100)], "has_more": True, "next_cursor": "c2"},
        {"results": [{"id": f"c{i}"} for i in range(50)], "has_more": False},
    ])
    monkeypatch.setattr(census_module, "requests", fake)

    blocks = census_module.fetch_all_children("page1")

    assert len(blocks) == 150
    assert fake.get_calls[0] == {"page_size": 100}
    assert fake.get_calls[1] == {"page_size": 100, "start_cursor": "c2"}


def test_fetch_all_children_devuelve_none_si_falla(census_module, fake_responses, monkeypatch):
    fake = fake_responses()
    fake.get = lambda url, headers=None, params=None: fake_responses.FakeResponse(500, text="boom")
    monkeypatch.setattr(census_module, "requests", fake)

    assert census_module.fetch_all_children("page1") is None


# ─────────────────────────────────────────────────────────────────────────────
# A1 — orden seguro: APPEND antes de DELETE + rollback
# ─────────────────────────────────────────────────────────────────────────────

MD = "## T\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"


def test_update_notion_agrega_antes_de_borrar(census_module, fake_responses, monkeypatch):
    fake = fake_responses(get_payloads=[{"results": [{"id": "viejo1"}], "has_more": False}])
    monkeypatch.setattr(census_module, "requests", fake)

    assert census_module.update_notion_census_page("page1", MD) is True
    assert fake.patch_calls, "se agregó contenido nuevo"
    assert fake.delete_calls == ["viejo1"], "solo después se borró lo viejo"


def test_update_notion_no_borra_nada_si_falla_el_append(census_module, fake_responses, monkeypatch):
    fake = fake_responses(
        get_payloads=[{"results": [{"id": "viejo1"}, {"id": "viejo2"}], "has_more": False}],
        patch_status=500,
    )
    monkeypatch.setattr(census_module, "requests", fake)

    assert census_module.update_notion_census_page("page1", MD) is False
    assert fake.delete_calls == [], (
        "si el append falla NO se debe borrar nada: antes la página quedaba vacía")


def test_update_notion_aborta_con_payload_vacio(census_module, fake_responses, monkeypatch):
    fake = fake_responses(get_payloads=[{"results": [{"id": "viejo1"}], "has_more": False}])
    monkeypatch.setattr(census_module, "requests", fake)

    assert census_module.update_notion_census_page("page1", "") is False
    assert fake.delete_calls == []
    assert fake.patch_calls == []


def test_update_notion_reporta_fallo_si_un_delete_no_se_pudo(census_module, fake_responses, monkeypatch):
    fake = fake_responses(
        get_payloads=[{"results": [{"id": "viejo1"}], "has_more": False}],
        delete_status=400,
    )
    monkeypatch.setattr(census_module, "requests", fake)

    assert census_module.update_notion_census_page("page1", MD) is False


# ─────────────────────────────────────────────────────────────────────────────
# A2 — --auto-fix-orphans inserta DENTRO de CENSUS_SPEC y el id queda "conocido"
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def census_copy(tmp_path, census_tree):
    """Copia del script (con su layer_1.env) para poder reescribirla en el test."""
    root = tmp_path / "fix_env"
    (root / "Layer_1" / "scripts").mkdir(parents=True)
    (root / "Layer_1" / "config").mkdir(parents=True)
    script = root / "Layer_1" / "scripts" / "generate_census.py"
    shutil.copy(census_tree / "Layer_1" / "scripts" / "generate_census.py", script)
    shutil.copy(census_tree / "Layer_1" / "config" / "layer_1.env", root / "Layer_1" / "config" / "layer_1.env")
    return script


def _spec_of(source: Path):
    tree = ast.parse(source.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CENSUS_SPEC":
            return ast.literal_eval(node.value)
    raise AssertionError("CENSUS_SPEC no encontrado")


def _orphan_entry():
    return {
        "doc": "System Prompt",
        "link": "https://x",
        "is_def": True,
        "seccion": "01.9",
        "plain": "01.9 SP:BOOTLOADER-999 — X",
    }


def test_auto_fix_inserta_el_id_dentro_del_spec(census_copy, monkeypatch):
    module = load_module_from(census_copy, "gc_autofix")
    monkeypatch.setattr(builtins, "input", lambda *a, **k: "y")

    ok = module.auto_fix_orphans({"SP:BOOTLOADER-999": _orphan_entry()})

    assert ok is True
    spec = _spec_of(census_copy)
    assert "SP:BOOTLOADER-999" in module.known_ids_from_spec(spec), (
        "el ID debe quedar dentro del literal de CENSUS_SPEC, no después del ']'")

    reloaded = load_module_from(census_copy, "gc_autofix_reload")
    assert "SP:BOOTLOADER-999" in reloaded.known_ids_from_spec()

    # No debe acumular dicts sueltos fuera de la lista (residuo tipo B018)
    source = census_copy.read_text(encoding="utf-8")
    stray = [n for n in ast.parse(source).body
             if isinstance(n, ast.Expr) and isinstance(n.value, ast.Dict)]
    assert stray == [], f"quedaron {len(stray)} dict(s) sueltos fuera de CENSUS_SPEC"


def test_auto_fix_no_escribe_si_la_seccion_no_existe(census_copy, monkeypatch):
    module = load_module_from(census_copy, "gc_autofix_unknown")
    monkeypatch.setattr(builtins, "input", lambda *a, **k: "y")
    before = census_copy.read_text(encoding="utf-8")

    ok = module.auto_fix_orphans({"RARO:FOO-001": _orphan_entry()})

    assert ok is False
    assert census_copy.read_text(encoding="utf-8") == before


def test_auto_fix_es_idempotente_en_la_segunda_corrida(census_copy, monkeypatch):
    module = load_module_from(census_copy, "gc_autofix_idem")
    monkeypatch.setattr(builtins, "input", lambda *a, **k: "y")
    module.auto_fix_orphans({"SP:BOOTLOADER-999": _orphan_entry()})
    first = census_copy.read_text(encoding="utf-8")

    module2 = load_module_from(census_copy, "gc_autofix_idem2")
    module2.auto_fix_orphans({"SP:BOOTLOADER-999": _orphan_entry()})
    second = census_copy.read_text(encoding="utf-8")

    assert first == second, "repetir el auto-fix con el mismo ID no debe duplicar filas"
    spec = _spec_of(census_copy)
    ids = [r["id"] for s in spec for r in s["rows"]]
    assert ids.count("SP:BOOTLOADER-999") == 1


def test_known_ids_from_spec_acepta_spec_explicito(census_module):
    spec = [{"name": "X", "rows": [{"id": "X:UNO", "lookup_ids": ["X:ALIAS"]}]}]
    assert census_module.known_ids_from_spec(spec) == {"X:UNO", "X:ALIAS"}


# ─────────────────────────────────────────────────────────────────────────────
# A5 / A6 — portabilidad de la ruta de salida y exit codes
# ─────────────────────────────────────────────────────────────────────────────

def test_sin_rutas_del_usuario_hardcodeadas(census_module):
    source = CENSUS_SRC.read_text(encoding="utf-8")
    assert "/Users/mauriciomeyran" not in source


def test_sync_to_notion_distingue_cancelacion_de_error(census_module, monkeypatch):
    # Cancelación del usuario → None (no es fallo)
    monkeypatch.setattr(builtins, "input", lambda *a, **k: "n")
    assert census_module.sync_to_notion("page1", MD) is None

    # Error real en la publicación → False
    monkeypatch.setattr(census_module, "update_notion_census_page", lambda *a, **k: False)
    assert census_module.sync_to_notion("page1", MD, auto_confirm=True) is False

    # Publicación OK pero versión no sincronizada → False
    monotonic = {"n": 0}

    def fake_version(*a, **k):
        monotonic["n"] += 1
        return "v1"

    monkeypatch.setattr(census_module, "update_notion_census_page", lambda *a, **k: True)
    monkeypatch.setattr(census_module, "get_page_version", fake_version)
    monkeypatch.setattr(census_module, "update_page_version", lambda *a, **k: True)
    monkeypatch.setattr(census_module, "sync_page_version_from_changelog", lambda *a, **k: False)
    assert census_module.sync_to_notion("page1", MD, auto_confirm=True) is False


# ─────────────────────────────────────────────────────────────────────────────
# fetch_blocks — reintentos, 429 y error incompleto (comportamiento correcto)
# ─────────────────────────────────────────────────────────────────────────────

def test_fetch_blocks_reintenta_tras_429(census_module, monkeypatch):
    calls = {"n": 0}

    class Resp:
        def __init__(self, status, payload=None, headers=None):
            self.status_code = status
            self._payload = payload or {}
            self.headers = headers or {}
            self.text = ""

        def json(self):
            return self._payload

    def fake_get(url, headers=None, params=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return Resp(429, headers={"Retry-After": "1"})
        return Resp(200, {"results": [{"id": "a"}], "has_more": False})

    monkeypatch.setattr(census_module.requests, "get", fake_get)
    monkeypatch.setattr(census_module.time, "sleep", lambda s: None)

    assert len(census_module.fetch_blocks("page")) == 1
    assert calls["n"] == 2


def test_fetch_blocks_lanza_incompleto_tras_agotar_reintentos(census_module, monkeypatch):
    class Resp:
        status_code = 500
        text = "boom"

        def json(self):
            return {}

    monkeypatch.setattr(census_module.requests, "get", lambda *a, **k: Resp())
    monkeypatch.setattr(census_module.time, "sleep", lambda s: None)

    with pytest.raises(census_module.FetchIncompleteError):
        census_module.fetch_blocks("page")
