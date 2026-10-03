"""Fixtures compartidas para los tests de scripts VANTAGE.

Los tests NO tocan Notion, ni el repo real, ni el home del operador: trabajan
sobre copias en tmp_path con clientes simulados.

Convención de import: los scripts de VANTAGE son ejecutables con efectos de
import (leen config, exigen token, resuelven rutas desde __file__), así que se
cargan desde una copia en un árbol temporal que imita el layout real del repo.
"""
from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CENSUS_SRC = REPO_ROOT / "Layer_1" / "scripts" / "generate_census.py"
L4_SCRIPTS = REPO_ROOT / "Layer_4" / "scripts"


def load_module_from(path: Path, name: str):
    """Importa un archivo .py por ruta sin depender de sys.path."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def census_tree(tmp_path_factory) -> Path:
    """Layout mínimo Layer_1/{scripts,config} para importar generate_census.py."""
    root = tmp_path_factory.mktemp("census_env")
    scripts = root / "Layer_1" / "scripts"
    config = root / "Layer_1" / "config"
    scripts.mkdir(parents=True)
    config.mkdir(parents=True)
    shutil.copy(CENSUS_SRC, scripts / "generate_census.py")
    (config / "layer_1.env").write_text(
        "NOTION_TOKEN=dummy-token-para-tests\nNOTION_VERSION=2025-09-03\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture(scope="session")
def census_module(census_tree):
    """generate_census.py importado con token dummy (sin red)."""
    pytest.importorskip("requests")
    pytest.importorskip("dotenv")
    return load_module_from(census_tree / "Layer_1" / "scripts" / "generate_census.py", "gc_under_test")


@pytest.fixture
def fake_responses(monkeypatch):
    """Doble configurable de `requests` para probar el flujo de publicación."""

    class FakeResponse:
        def __init__(self, status_code=200, payload=None, text="", headers=None):
            self.status_code = status_code
            self._payload = payload or {}
            self.text = text
            self.headers = headers or {}

        def json(self):
            return self._payload

    class FakeRequests:
        def __init__(self, get_payloads=None, patch_status=200, delete_status=200):
            self.get_payloads = list(get_payloads or [])
            self.patch_status = patch_status
            self.delete_status = delete_status
            self.get_calls = []
            self.patch_calls = []
            self.delete_calls = []

        def get(self, url, headers=None, params=None):
            self.get_calls.append(params or {})
            if self.get_payloads:
                payload = self.get_payloads.pop(0)
            else:
                payload = {"results": [], "has_more": False}
            if isinstance(payload, FakeResponse):
                return payload
            return FakeResponse(200, payload)

        def patch(self, url, headers=None, json=None):
            self.patch_calls.append(json or {})
            return FakeResponse(self.patch_status, {"results": [{"id": f"new{i}"} for i in range(len((json or {}).get("children", [])))]},
                                text="patch error")

        def delete(self, url, headers=None):
            self.delete_calls.append(url.rsplit("/", 1)[-1])
            return FakeResponse(self.delete_status, text="delete error")

    return FakeRequests
