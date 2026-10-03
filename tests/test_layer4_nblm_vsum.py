"""Regresiones de seguridad y contexto; sin llamadas reales a servicios externos."""
import os
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from conftest import L4_SCRIPTS, load_module_from


@pytest.fixture
def nblm(tmp_path, monkeypatch):
    module = load_module_from(L4_SCRIPTS / "vdoc_nblm.py", "nblm_security")
    monkeypatch.setattr(module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(module, "DIGEST_PATH", tmp_path / "VANTAGE_digest.txt")
    monkeypatch.setattr(module, "ACTIVE_DIR", tmp_path / "Documentación/ACTIVE")
    module.ACTIVE_DIR.mkdir(parents=True)
    monkeypatch.setattr(module, "NOTEBOOK_ID", "vantage")
    return module


def test_digest_no_abre_secretos_archivos_excluidos_o_symlinks(nblm, tmp_path, monkeypatch):
    import builtins
    from pathlib import Path

    denied = [
        '.env', '.env.local', 'Layer_1/config/layer_1.env',
        'Layer_3/config/layer_3.env', 'Dashboard/config/dashboard.env',
        'config/PRODUCTION.ENV', 'config/test.env.example', 'config/key.pem',
        'config/key.key', 'config/key.key.bak', 'config/key.secret',
        'token_drive.json', 'client_secret_123.json', 'credentials.json',
        'Archive/deprecated.py', 'Layer_4/backups/old.md', 'data.bin',
    ]
    for name in denied:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('DO_NOT_UPLOAD', encoding='utf-8')
    (tmp_path / 'alias.txt').symlink_to(tmp_path / '.env')
    (tmp_path / 'alias-dir').symlink_to(tmp_path / 'Archive', target_is_directory=True)
    (nblm.ACTIVE_DIR / 'unsafe.md').symlink_to(tmp_path / '.env')
    (tmp_path / 'app.py').write_text('SAFE_CODE', encoding='utf-8')
    (nblm.ACTIVE_DIR / 'Kernel.md').write_text('SAFE_DOC', encoding='utf-8')
    real_read = Path.read_text

    def guarded_read(path, *args, **kwargs):
        assert nblm.is_safe_source(path), f'Lectura prohibida: {path}'
        return real_read(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'read_text', guarded_read)
    nblm.generate_local_digest()
    nblm.generate_local_digest()  # El digest no se incluye a sí mismo.
    with builtins.open(nblm.DIGEST_PATH, encoding='utf-8') as f:
        result = f.read()
    assert 'DO_NOT_UPLOAD' not in result
    assert 'SAFE_CODE' in result and 'SAFE_DOC' in result
    assert 'alias.txt' not in result
    assert nblm.DIGEST_PATH.stat().st_mode & 0o777 == 0o600


def test_digest_reemplaza_symlink_sin_modificar_destino(nblm, tmp_path):
    target = tmp_path / '.env'
    target.write_text('SECRET')
    nblm.DIGEST_PATH.symlink_to(target)
    nblm.generate_local_digest()
    assert target.read_text() == 'SECRET'
    assert not nblm.DIGEST_PATH.is_symlink()


def client_for(nblm, monkeypatch):
    notebooks = Mock()
    notebooks.list.return_value = [SimpleNamespace(id='vantage')]
    notebooks.list_sources.return_value = [SimpleNamespace(id='old', title='VANTAGE_digest.txt')]
    monkeypatch.setattr(nblm, 'get_notebooklm_client', lambda: SimpleNamespace(notebooks=notebooks))
    return notebooks


@pytest.mark.parametrize('notebook_id', ['', '  ', 'other'])
def test_notebook_obligatorio_y_validado(nblm, monkeypatch, notebook_id):
    client = client_for(nblm, monkeypatch)
    monkeypatch.setattr(nblm, 'NOTEBOOK_ID', notebook_id)
    assert nblm.main() == 1
    client.add_source.assert_not_called()
    client.delete_source.assert_not_called()
    assert not nblm.DIGEST_PATH.exists()


def test_sin_cuadernos_falla(nblm, monkeypatch):
    client = client_for(nblm, monkeypatch)
    client.list.return_value = []
    assert nblm.main() == 1
    client.add_source.assert_not_called()


@pytest.mark.parametrize('operation', ['list', 'list_sources', 'add_source', 'delete_source'])
def test_fallos_api_devuelven_error(nblm, monkeypatch, operation):
    client = client_for(nblm, monkeypatch)
    getattr(client, operation).side_effect = RuntimeError('API falló')
    assert nblm.main() == 1
    if operation != 'delete_source':
        client.delete_source.assert_not_called()


@pytest.mark.parametrize('operation', ['get_notebooklm_client', 'generate_local_digest'])
def test_fallos_auth_y_digest_devuelven_error(nblm, monkeypatch, operation):
    client = client_for(nblm, monkeypatch)
    monkeypatch.setattr(nblm, operation, Mock(side_effect=OSError('fallo')))
    assert nblm.main() == 1
    client.add_source.assert_not_called()


def test_sync_sube_antes_de_borrar_y_excluye_symlinks_active(nblm, tmp_path, monkeypatch):
    client = client_for(nblm, monkeypatch)
    (tmp_path / '.env').write_text('SECRET')
    (nblm.ACTIVE_DIR / 'unsafe.md').symlink_to(tmp_path / '.env')
    safe = nblm.ACTIVE_DIR / 'Kernel.md'
    safe.write_text('documento')
    assert nblm.main() == 0
    assert [c.args[1] for c in client.add_source.call_args_list] == [nblm.DIGEST_PATH, safe]
    names = [c[0] for c in client.mock_calls]
    assert names.index('add_source') < names.index('delete_source')


def test_cli_nblm_exit_no_cero_sin_id():
    result = subprocess.run([sys.executable, str(L4_SCRIPTS / 'vdoc_nblm.py')],
                            env={**os.environ, 'NOTEBOOK_ID': ''}, capture_output=True, text=True)
    assert result.returncode == 1
    assert 'NOTEBOOK_ID' in result.stdout


@pytest.fixture
def vsum(monkeypatch):
    module = load_module_from(L4_SCRIPTS / 'vsum.py', 'vsum_regression')
    monkeypatch.setattr(module.time, 'sleep', lambda _: None)
    monkeypatch.setattr(module, 'GROQ_API_KEY', None)
    return module


def test_ollama_usa_timeout_configurado(vsum, monkeypatch):
    response = Mock()
    response.read.return_value = b'{"choices":[{"message":{"content":"ok"}}]}'
    from unittest.mock import MagicMock
    opened = MagicMock()
    opened.__enter__.return_value = response
    urlopen = Mock(return_value=opened)
    monkeypatch.setattr(vsum.urllib.request, 'urlopen', urlopen)
    monkeypatch.setattr(vsum, 'OLLAMA_TIMEOUT_SEC', 17)
    assert vsum.call_ollama('test') == 'ok'
    assert urlopen.call_args.kwargs['timeout'] == 17


def test_chunks_no_desperdician_dos_caracteres(vsum):
    assert vsum.chunk_text('aaa\n\nbbbbb\n\nc', 10) == ['aaa\n\nbbbbb', 'c']
    for limit in (0, -1):
        with pytest.raises(ValueError):
            vsum.chunk_text('abc', limit)


@pytest.mark.parametrize('model', ['ollama', 'gemini'])
@pytest.mark.parametrize('has_key', [False, True])
def test_fallback_consistente_y_condicionado_a_clave(vsum, monkeypatch, model, has_key):
    gemini = Mock(side_effect=RuntimeError('gemini'))
    ollama = Mock(side_effect=RuntimeError('ollama'))
    groq = Mock(return_value='ok')
    monkeypatch.setattr(vsum, 'call_gemini', gemini)
    monkeypatch.setattr(vsum, 'call_ollama', ollama)
    monkeypatch.setattr(vsum, 'call_groq', groq)
    monkeypatch.setattr(vsum, 'GROQ_API_KEY', 'dummy' if has_key else None)
    if has_key:
        assert vsum.call_with_fallback('prompt', model) == 'ok'
        groq.assert_called_once_with('prompt')
    else:
        with pytest.raises(RuntimeError, match='ollama'):
            vsum.call_with_fallback('prompt', model)
        groq.assert_not_called()
    assert ollama.call_count == 2
    assert gemini.call_count == (model == 'gemini')


def test_reintento_ollama_recupera_sin_groq(vsum, monkeypatch):
    ollama = Mock(side_effect=[RuntimeError('transitorio'), 'ok'])
    groq = Mock()
    monkeypatch.setattr(vsum, 'call_ollama', ollama)
    monkeypatch.setattr(vsum, 'call_groq', groq)
    assert vsum.call_with_fallback('prompt', 'ollama') == 'ok'
    groq.assert_not_called()


def test_consolidacion_multinivel_acota_prompt_y_usa_mismo_fallback(vsum, monkeypatch):
    calls = []

    def fake(prompt, model):
        assert len(prompt) + len(vsum.SUMMARY_SYSTEM) <= vsum.MAX_CHARS_PER_CHUNK
        assert model == 'ollama'
        calls.append(prompt)
        return 'resumen ' * 200

    monkeypatch.setattr(vsum, 'call_with_fallback', fake)
    result = vsum.summarize('transcripcion ' * 15000)
    assert result == 'resumen ' * 200
    meta_calls = [p for p in calls if 'Estos son resúmenes parciales' in p]
    assert len(meta_calls) > 2  # más de una ronda de reducción


def test_consolidacion_aborta_si_no_reduce(vsum, monkeypatch):
    calls = []

    def fake(prompt, model):
        assert len(prompt) + len(vsum.SUMMARY_SYSTEM) <= vsum.MAX_CHARS_PER_CHUNK
        calls.append(prompt)
        return 'x' * 10000

    monkeypatch.setattr(vsum, 'call_with_fallback', fake)
    with pytest.raises(RuntimeError, match='no reduce'):
        vsum.summarize('x' * 20000)
    assert len(calls) < 20


def test_metadatos_excesivos_fallan_antes_de_api(vsum, monkeypatch):
    call = Mock()
    monkeypatch.setattr(vsum, 'call_with_fallback', call)
    with pytest.raises(ValueError, match='presupuesto'):
        vsum.summarize('texto', serial='x' * 10000)
    call.assert_not_called()


def test_digest_ilegible_aborta_sin_subir_version_anterior(nblm, tmp_path, monkeypatch):
    client = client_for(nblm, monkeypatch)
    nblm.DIGEST_PATH.write_text('DIGEST_ANTERIOR')
    (tmp_path / 'invalid.txt').write_bytes(b'\xff\xfe')
    assert nblm.main() == 1
    client.add_source.assert_not_called()
    assert nblm.DIGEST_PATH.read_text() == 'DIGEST_ANTERIOR'


@pytest.mark.parametrize('model,client_name', [('gemini', 'call_gemini'), ('groq', 'call_groq')])
def test_proveedor_explicito_exitoso_no_hace_fallback(vsum, monkeypatch, model, client_name):
    client = Mock(return_value='ok')
    ollama = Mock()
    monkeypatch.setattr(vsum, client_name, client)
    monkeypatch.setattr(vsum, 'call_ollama', ollama)
    assert vsum.call_with_fallback('prompt', model) == 'ok'
    client.assert_called_once_with('prompt')
    ollama.assert_not_called()


def test_groq_explicito_no_oculta_fallo(vsum, monkeypatch):
    monkeypatch.setattr(vsum, 'call_groq', Mock(side_effect=RuntimeError('groq')))
    with pytest.raises(RuntimeError, match='groq'):
        vsum.call_with_fallback('prompt', 'groq')


def test_resumen_vacio_falla(vsum, monkeypatch):
    monkeypatch.setattr(vsum, 'call_with_fallback', Mock(return_value='  '))
    with pytest.raises(RuntimeError, match='vacío'):
        vsum.summarize('texto')
