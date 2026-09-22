"""
test_vload.py — Tests para vload.py (HO-000062 P4)
Cubre resolución de UUID desde registry, modo --list, y casos edge.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Agregar Layer_1/scripts al path para importar vload
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Layer_1" / "scripts"))

import vload


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_registry():
    """Registry de ejemplo para tests."""
    return {
        "version": "2.0",
        "document_registry": {
            "KERNEL": "377938be-fc42-805e-a408-c9ae518d4fe7",
            "MANUAL": "372938be-fc42-8050-9a67-e40857d7806e",
            "CANON": "377938be-fc42-8089-93f2-f52dbd2dec6c",
            "_comment": "Este comentario debe ser ignorado"
        }
    }


@pytest.fixture
def temp_registry_file(sample_registry):
    """Crea un archivo registry temporal."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_registry, f)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def missing_registry_file():
    """Path a un archivo que no existe."""
    return Path("/tmp/nonexistent_registry_12345.json")


@pytest.fixture
def corrupt_registry_file():
    """Crea un archivo registry corrupto (JSON inválido)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        temp_path = Path(f.name)
    
    yield temp_path
    
    if temp_path.exists():
        temp_path.unlink()


# ---------------------------------------------------------------------------
# Tests: _load_document_registry
# ---------------------------------------------------------------------------

def test_load_document_registry_success(temp_registry_file):
    """Carga exitosa del document_registry."""
    registry = vload._load_document_registry(temp_registry_file)
    
    assert registry is not None
    assert isinstance(registry, dict)
    assert "KERNEL" in registry
    assert "MANUAL" in registry
    assert "CANON" in registry
    assert "_comment" not in registry  # Comentarios filtrados
    assert registry["KERNEL"] == "377938be-fc42-805e-a408-c9ae518d4fe7"


def test_load_document_registry_file_not_found(missing_registry_file):
    """Archivo no encontrado retorna dict vacío."""
    registry = vload._load_document_registry(missing_registry_file)
    
    assert registry == {}


def test_load_document_registry_corrupt_json(corrupt_registry_file):
    """JSON corrupto retorna dict vacío."""
    registry = vload._load_document_registry(corrupt_registry_file)
    
    assert registry == {}


def test_load_document_registry_missing_section():
    """Registry sin sección document_registry retorna dict vacío."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"version": "2.0", "other_section": {}}, f)
        temp_path = Path(f.name)
    
    try:
        registry = vload._load_document_registry(temp_path)
        assert registry == {}
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_load_document_registry_empty_section():
    """Document_registry vacío retorna dict vacío."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"version": "2.0", "document_registry": {}}, f)
        temp_path = Path(f.name)
    
    try:
        registry = vload._load_document_registry(temp_path)
        assert registry == {}
    finally:
        if temp_path.exists():
            temp_path.unlink()


# ---------------------------------------------------------------------------
# Tests: _resolve_uuid_from_prefix
# ---------------------------------------------------------------------------

def test_resolve_uuid_from_prefix_success(sample_registry):
    """Resolución exitosa de UUID desde prefix."""
    registry = {k: v for k, v in sample_registry["document_registry"].items() if not k.startswith("_")}
    
    uuid = vload._resolve_uuid_from_prefix("KERNEL", registry)
    assert uuid == "377938be-fc42-805e-a408-c9ae518d4fe7"
    
    uuid = vload._resolve_uuid_from_prefix("manual", registry)  # Case insensitive
    assert uuid == "372938be-fc42-8050-9a67-e40857d7806e"


def test_resolve_uuid_from_prefix_not_found(sample_registry):
    """Prefix no encontrado retorna None."""
    registry = {k: v for k, v in sample_registry["document_registry"].items() if not k.startswith("_")}
    
    uuid = vload._resolve_uuid_from_prefix("NONEXISTENT", registry)
    assert uuid is None


def test_resolve_uuid_from_prefix_empty_registry():
    """Registry vacío retorna None."""
    uuid = vload._resolve_uuid_from_prefix("KERNEL", {})
    assert uuid is None


# ---------------------------------------------------------------------------
# Tests: list_available_prefixes
# ---------------------------------------------------------------------------

@patch('builtins.print')
def test_list_available_prefixes_success(mock_print, temp_registry_file):
    """Lista de prefijos disponibles exitosa."""
    vload.list_available_prefixes(temp_registry_file)
    
    # Verificar que se llamó print varias veces (cabecera + entradas + pie)
    assert mock_print.call_count > 3
    
    # Verificar contenido de algunas llamadas
    print_calls = [str(call) for call in mock_print.call_args_list]
    call_text = " ".join(print_calls)
    
    assert "KERNEL" in call_text
    assert "MANUAL" in call_text
    assert "377938be-fc42-805e-a408-c9ae518d4fe7" in call_text


@patch('builtins.print')
def test_list_available_prefixes_empty_registry(mock_print):
    """Registry vacío muestra error."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"version": "2.0", "document_registry": {}}, f)
        temp_path = Path(f.name)
    
    try:
        vload.list_available_prefixes(temp_path)
        
        # Debería imprimir error
        print_calls = [str(call) for call in mock_print.call_args_list]
        call_text = " ".join(print_calls)
        assert "ERROR" in call_text
    finally:
        if temp_path.exists():
            temp_path.unlink()


# ---------------------------------------------------------------------------
# Tests: main() con mock de fetch_lazy_section
# ---------------------------------------------------------------------------

@patch('vload.fetch_lazy_section')
@patch('vload._load_document_registry')
def test_main_with_uuid_resolution(mock_load_registry, mock_fetch, temp_registry_file):
    """main() resuelve UUID automáticamente desde registry."""
    # Setup mocks
    sample_reg = {
        "KERNEL": "377938be-fc42-805e-a408-c9ae518d4fe7",
        "MANUAL": "372938be-fc42-8050-9a67-e40857d7806e"
    }
    mock_load_registry.return_value = sample_reg
    mock_fetch.return_value = "## KERNEL:SCHEMA\n\nContenido de prueba..."
    
    # Ejecutar con --route (sin --page)
    with patch('sys.argv', ['vload', '--route', 'KERNEL:SCHEMA']):
        vload.main()
    
    # Verificar que se llamó fetch_lazy_section con el UUID resuelto
    mock_fetch.assert_called_once()
    call_args = mock_fetch.call_args
    assert call_args[0][0] == "377938be-fc42-805e-a408-c9ae518d4fe7"  # UUID resuelto
    assert call_args[0][1] == "KERNEL:SCHEMA"


@patch('vload.fetch_lazy_section')
def test_main_with_explicit_uuid(mock_fetch):
    """main() usa UUID explícito cuando se proporciona --page."""
    mock_fetch.return_value = "## MANUAL:RUNTIME-002\n\nContenido..."
    
    with patch('sys.argv', ['vload', '--page', '12345678-1234-1234-1234-123456789012', '--route', 'MANUAL:RUNTIME-002']):
        vload.main()
    
    # Verificar que se usó el UUID explícito
    mock_fetch.assert_called_once()
    call_args = mock_fetch.call_args
    assert call_args[0][0] == "12345678-1234-1234-1234-123456789012"


@patch('vload.fetch_lazy_section')
@patch('vload._load_document_registry')
@patch('sys.exit')
def test_main_prefix_not_found(mock_exit, mock_load_registry, mock_fetch):
    """main() falla cuando el prefix no existe en registry."""
    mock_load_registry.return_value = {"KERNEL": "uuid-123"}
    mock_fetch.return_value = "Contenido"
    
    with patch('sys.argv', ['vload', '--route', 'NONEXISTENT:SECTION']):
        vload.main()
    
    # Debería llamar a sys.exit(1)
    mock_exit.assert_called_once_with(1)


@patch('vload.fetch_lazy_section')
@patch('vload._load_document_registry')
@patch('sys.exit')
def test_main_malformed_route(mock_exit, mock_load_registry, mock_fetch):
    """main() falla cuando la ruta no tiene formato PREFIX:CLAVE."""
    mock_load_registry.return_value = {"KERNEL": "uuid-123"}
    mock_fetch.return_value = "Contenido"
    
    with patch('sys.argv', ['vload', '--route', 'JUST_A_SECTION']):
        vload.main()
    
    # Debería llamar a sys.exit(1)
    mock_exit.assert_called_once_with(1)


@patch('vload.list_available_prefixes')
def test_main_list_mode(mock_list):
    """main() en modo --list llama a list_available_prefixes."""
    with patch('sys.argv', ['vload', '--list']):
        vload.main()
    
    mock_list.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: Integración con lazy_loader._parse_route
# ---------------------------------------------------------------------------

def test_parse_route_integration(temp_registry_file):
    """Integración con _parse_route de lazy_loader."""
    # _parse_route debe funcionar con el registry cargado
    prefix, clave = vload._parse_route("KERNEL:SCHEMA", temp_registry_file)
    
    assert prefix == "KERNEL"
    assert clave == "SCHEMA"


def test_parse_route_legacy_format(temp_registry_file):
    """Formato legacy (sin prefijo) debería funcionar."""
    prefix, clave = vload._parse_route("SCHEMA", temp_registry_file)
    
    assert prefix == ""  # Sin prefijo reconocido
    assert clave == "SCHEMA"


# ---------------------------------------------------------------------------
# Tests: Casos edge
# ---------------------------------------------------------------------------

def test_resolve_uuid_case_insensitive():
    """Resolución de UUID es case-insensitive para el prefix."""
    registry = {"KERNEL": "uuid-123", "MANUAL": "uuid-456"}
    
    assert vload._resolve_uuid_from_prefix("kernel", registry) == "uuid-123"
    assert vload._resolve_uuid_from_prefix("KERNEL", registry) == "uuid-123"
    assert vload._resolve_uuid_from_prefix("KeRnEl", registry) == "uuid-123"


def test_resolve_uuid_with_whitespace():
    """Resolución de UUID maneja whitespace en prefix."""
    registry = {"KERNEL": "uuid-123"}
    
    assert vload._resolve_uuid_from_prefix(" KERNEL ", registry) == "uuid-123"
    assert vload._resolve_uuid_from_prefix("\tKERNEL\n", registry) == "uuid-123"


def test_load_registry_with_custom_path():
    """Carga de registry con path personalizado."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"document_registry": {"CUSTOM": "custom-uuid"}}, f)
        temp_path = Path(f.name)
    
    try:
        registry = vload._load_document_registry(temp_path)
        assert registry == {"CUSTOM": "custom-uuid"}
    finally:
        if temp_path.exists():
            temp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])