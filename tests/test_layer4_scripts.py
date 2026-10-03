"""Regresión de Layer_4/scripts.

Cubre los hallazgos B1–B11 de
handoffs/VALIDACION_GENERATE_CENSUS_Y_LAYER4_2026-10-02.md.
Git real en repos temporales; Notion/httpx siempre con dobles.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from conftest import L4_SCRIPTS, REPO_ROOT, load_module_from

GIT = shutil.which("git")
requires_git = pytest.mark.skipif(GIT is None, reason="git no disponible")


def run_py(script: Path, args=(), cwd=None, env=None, timeout=60):
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(cwd or script.parent),
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )


def git(args, cwd):
    return subprocess.run([GIT, *args], cwd=str(cwd), capture_output=True, text=True)


# ─────────────────────────────────────────────────────────────────────────────
# B1 — el sync en background ya no muere al escribir (PIPE sin lector)
# ─────────────────────────────────────────────────────────────────────────────

def _hook_tree(tmp_path: Path) -> Path:
    """Árbol Layer_4/scripts con el trigger real y un vsync_doc simulado."""
    root = tmp_path / "hook_repo"
    scripts = root / "Layer_4" / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy(L4_SCRIPTS / "trigger_sync_after_mcp_write.py", scripts / "trigger_sync_after_mcp_write.py")
    shutil.copy(L4_SCRIPTS / "foundational_docs.py", scripts / "foundational_docs.py")
    (scripts / "vsync_doc.py").write_text(
        "import pathlib, sys\n"
        "print('primer print del sync', flush=True)\n"
        "for i in range(3000):\n"
        "    print('linea de log %04d ' % i + 'x' * 90, flush=True)\n"
        f"pathlib.Path({str(root / 'sync_completado.txt')!r}).write_text('ok')\n",
        encoding="utf-8",
    )
    return root


KERNEL_ID = "377938be-fc42-805e-a408-c9ae518d4fe7"


def test_trigger_no_mata_el_sync_por_pipe_roto(tmp_path):
    root = _hook_tree(tmp_path)
    log = tmp_path / "mcp_sync.log"
    env = {**os.environ, "VANTAGE_MCP_SYNC_LOG": str(log)}

    result = run_py(root / "Layer_4/scripts/trigger_sync_after_mcp_write.py", [KERNEL_ID], cwd=root, env=env)
    assert result.returncode == 0

    marker = root / "sync_completado.txt"
    deadline = time.time() + 20
    while time.time() < deadline and not marker.exists():
        time.sleep(0.2)

    assert marker.exists(), (
        "el hijo debe poder escribir su salida completa sin morir con BrokenPipeError")
    assert log.exists(), "la salida del sync debe quedar en el log, no en un PIPE"


def test_trigger_ignora_page_id_no_fundacional(tmp_path):
    root = _hook_tree(tmp_path)
    result = run_py(root / "Layer_4/scripts/trigger_sync_after_mcp_write.py", ["pagina-cualquiera"], cwd=root)
    assert result.returncode == 0
    assert not (root / "sync_completado.txt").exists()


def test_trigger_sin_argumentos_falla(tmp_path):
    root = _hook_tree(tmp_path)
    result = run_py(root / "Layer_4/scripts/trigger_sync_after_mcp_write.py", [], cwd=root)
    assert result.returncode == 1


def test_wrapper_compila_y_falla_rapido():
    """B10: el stub ya no devuelve success=True sin escribir."""
    module = load_module_from(L4_SCRIPTS / "notion_write_wrapper.py", "nww_test")
    with pytest.raises(NotImplementedError):
        module.write_to_notion_page("pagina-x", {"children": []})


def test_foundational_docs_es_fuente_unica():
    """B11: el mapeo ya no está duplicado en dos archivos."""
    a = load_module_from(L4_SCRIPTS / "foundational_docs.py", "fd_a")
    b = load_module_from(L4_SCRIPTS / "notion_write_wrapper.py", "nww_b")
    c = load_module_from(L4_SCRIPTS / "trigger_sync_after_mcp_write.py", "trg_c")
    assert a.FOUNDATIONAL_DOCS == b.FOUNDATIONAL_DOCS == c.FOUNDATIONAL_DOCS
    assert len(a.FOUNDATIONAL_DOCS) == 9


# ─────────────────────────────────────────────────────────────────────────────
# B2 / B3 / B4 — git_sync
# ─────────────────────────────────────────────────────────────────────────────

def _git_repo(tmp_path: Path, branch: str = "main") -> Path:
    origin = tmp_path / "origin.git"
    subprocess.run([GIT, "init", "--bare", "-b", "main", str(origin)], check=True, capture_output=True)
    seed = tmp_path / "seed"
    seed.mkdir()
    git(["init", "-b", "main"], seed)
    git(["config", "user.name", "test"], seed)
    git(["config", "user.email", "test@test"], seed)
    (seed / "f.txt").write_text("1", encoding="utf-8")
    git(["add", "-A"], seed)
    git(["commit", "-m", "init"], seed)
    git(["remote", "add", "origin", str(origin)], seed)
    git(["push", "-u", "origin", "main"], seed)
    return seed


def _repo_with_script(tmp_path: Path, branch: str = "main") -> Path:
    seed = _git_repo(tmp_path, branch)
    work = tmp_path / f"work_{branch.replace('/', '_')}"
    shutil.copytree(seed, work)
    if branch != "main":
        git(["checkout", "-b", branch], work)
    scripts = work / "Layer_4" / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy(L4_SCRIPTS / "git_sync.py", scripts / "git_sync.py")
    (work / "skills").mkdir(exist_ok=True)
    # Baseline limpio: el script copiado queda commiteado antes de la prueba
    git(["add", "-A"], work)
    git(["commit", "-m", "script"], work)
    return work


@requires_git
def test_git_sync_dry_run_no_escribe_index(tmp_path):
    work = _repo_with_script(tmp_path)
    (work / "skills" / "demo.md").write_text("skill", encoding="utf-8")

    result = run_py(work / "Layer_4/scripts/git_sync.py", ["--dry-run"], cwd=work)

    assert result.returncode == 0
    assert not (work / "skills" / "index.json").exists(), "--dry-run no debe escribir index.json"
    assert "index.json" not in git(["status", "--porcelain"], work).stdout


@requires_git
def test_git_sync_pushea_la_rama_activa(tmp_path):
    work = _repo_with_script(tmp_path, branch="arena/sesion")
    (work / "cambio.txt").write_text("hola", encoding="utf-8")

    result = run_py(work / "Layer_4/scripts/git_sync.py", cwd=work)

    assert result.returncode == 0, result.stderr
    assert git(["rev-parse", "--abbrev-ref", "HEAD"], work).stdout.strip() == "arena/sesion"
    # El commit debe estar publicado en SU rama (antes se pusheaba 'main' fijo y
    # el commit de la rama de trabajo quedaba solo local).
    assert git(["log", "origin/arena/sesion..HEAD", "--oneline"], work).stdout.strip() == "", (
        "el commit de la rama activa quedó sin publicar")
    remote_branches = git(["branch", "--list", "--all"], work).stdout
    assert "remotes/origin/arena/sesion" in remote_branches
    # origin/main no debe recibir el commit de la rama de trabajo
    assert git(["log", "origin/main..HEAD", "--oneline"], work).stdout.strip() != ""


@requires_git
def test_git_sync_reporta_la_rama_en_el_resultado(tmp_path, monkeypatch):
    work = _repo_with_script(tmp_path, branch="feature/x")
    module = load_module_from(work / "Layer_4/scripts/git_sync.py", "gs_branch_test")
    monkeypatch.setattr(module, "REPO_ROOT", work)

    result = module.sync(dry_run=True)

    assert result.get("branch") == "feature/x"


@requires_git
def test_git_sync_genera_index_con_el_layout_real(tmp_path):
    """B4: skills/*.md deben entrar al índice (antes el glob *.skill no veía nada)."""
    work = _repo_with_script(tmp_path)
    (work / "skills" / "vantage-cv-b.md").write_text("skill", encoding="utf-8")
    (work / "skills" / "otra.md").write_text("skill", encoding="utf-8")

    result = run_py(work / "Layer_4/scripts/git_sync.py", cwd=work)

    assert result.returncode == 0, result.stderr
    index = json.loads((work / "skills" / "index.json").read_text(encoding="utf-8"))
    names = {r["name"] for r in index["resources"]}
    assert {"vantage-cv-b", "otra"} <= names


def test_get_skill_files_ve_el_layout_real_del_repo():
    module = load_module_from(L4_SCRIPTS / "git_sync.py", "gs_glob_test")
    module.SKILLS_DIR = REPO_ROOT / "skills"

    names = module.get_skill_files()

    assert names, "debe encontrar las skills del layout real (*.md)"
    assert "vantage-cv-b" in names


# ─────────────────────────────────────────────────────────────────────────────
# B5 / B6 / B7 — vdoc y vsync_doc (exit codes)
# ─────────────────────────────────────────────────────────────────────────────

def test_vdoc_comando_desconocido_falla():
    result = run_py(L4_SCRIPTS / "vdoc.py", ["comando_inexistente"])
    assert result.returncode != 0


def test_vdoc_rechaza_el_doc_vantage_que_no_existe():
    """B5: 'VANTAGE' se anunciaba pero vsync_doc no lo aceptaba (exit 2)."""
    result = run_py(L4_SCRIPTS / "vdoc.py", ["VANTAGE", "dry"])
    assert result.returncode != 0
    assert "no reconocido" in result.stdout.lower()


def test_vdoc_no_usa_home_hardcodeado():
    source = (L4_SCRIPTS / "vdoc.py").read_text(encoding="utf-8")
    assert "Path.home()/\"Documents" not in source.replace(" ", "")
    assert "Documents/03 Projects/VANTAGE" not in source


@pytest.fixture(scope="module")
def vsync_module(tmp_path_factory):
    """vsync_doc.py importado con token dummy y sin acceso a Notion."""
    pytest.importorskip("notion_client")
    pytest.importorskip("httpx")
    env_dir = tmp_path_factory.mktemp("vsync_env")
    scripts = env_dir / "Layer_4" / "scripts"
    scripts.mkdir(parents=True)
    (env_dir / "Layer_1" / "config").mkdir(parents=True)
    shutil.copy(L4_SCRIPTS / "vsync_doc.py", scripts / "vsync_doc.py")
    os.environ.setdefault("NOTION_TOKEN", "dummy-token-para-tests")
    return load_module_from(scripts / "vsync_doc.py", "vsync_under_test")


def test_vsync_decide_por_hash(vsync_module):
    h = vsync_module._hash
    local, notion = "local", "notion"
    manifest = {"kernel": h(notion)}

    assert vsync_module._decide("kernel", notion, notion, manifest) == "noop"
    assert vsync_module._decide("kernel", notion, "otro", manifest) == "notion->local"
    assert vsync_module._decide("kernel", "otro", notion, manifest) == "local->notion"
    assert vsync_module._decide("kernel", "a", "b", manifest) == "conflict"
    assert vsync_module._decide("kernel", local, notion, {}) == "conflict"


def test_vsync_exit_code_no_es_cero_si_falla_el_fetch(vsync_module, tmp_path, monkeypatch):
    """B7: un fetch fallido debe devolver exit != 0 (antes siempre 0)."""
    local = tmp_path / "Kernel.md"
    local.write_text("# Kernel\n", encoding="utf-8")
    monkeypatch.setitem(vsync_module.DOCS, "kernel", dict(vsync_module.DOCS["kernel"], local_file=local))
    monkeypatch.setattr(vsync_module, "fetch_notion_as_md", lambda pid: (None, None))
    monkeypatch.setattr(vsync_module, "auto_commit", lambda dry_run=False: None)
    monkeypatch.setattr(sys, "argv", ["vsync_doc.py", "--direction", "notion", "--doc", "kernel"])

    assert vsync_module.main() != 0


def test_vsync_rich_text_soporta_bloques_locales(vsync_module):
    """B11: los bloques construidos localmente no traen plain_text."""
    assert vsync_module._rich_text([{"type": "text", "text": {"content": "hola"}}]) == "hola"
    assert vsync_module._rich_text([{"plain_text": "notion"}]) == "notion"


def test_push_local_crea_antes_de_borrar(vsync_module, tmp_path, monkeypatch):
    """R-02: el tipo cambia → crear el reemplazo ANTES de borrar el viejo."""
    order = []

    class Children:
        @staticmethod
        def append(block_id=None, children=None, after=None):
            order.append("append")
            return {}

    class Blocks:
        children = Children()

        @staticmethod
        def delete(block_id=None):
            order.append("delete")
            return {}

    class FakeNotion:
        blocks = Blocks()

    monkeypatch.setattr(vsync_module, "notion", FakeNotion())
    monkeypatch.setattr(vsync_module, "safe_list", lambda pid, cur=None: {
        "results": [{"id": "old1", "type": "paragraph", "paragraph": {"rich_text": []}, "archived": False}],
        "has_more": False,
    })

    class Resp:
        status_code = 200
        text = ""

        def json(self):
            return {}

    class FakeHTTP:
        @staticmethod
        def patch(url, headers=None, json=None, timeout=None):
            order.append("patch")
            return Resp()

    monkeypatch.setattr(vsync_module, "HTTP", FakeHTTP)

    md = tmp_path / "doc.md"
    md.write_text("# Titulo\n\ncontenido\n", encoding="utf-8")
    result = vsync_module.push_local_to_notion("pid1", md)

    assert result["failed"] == 0
    assert order and order[0] == "append", f"crear antes de borrar, orden real: {order}"


def test_push_local_no_marca_tabla_identica_como_fallida(vsync_module, tmp_path, monkeypatch):
    """B11: una tabla sin cambios no debe forzar exit 1 / manifest sin actualizar."""
    monkeypatch.setattr(vsync_module, "safe_list", lambda pid, cur=None: {
        "results": [
            {"id": "t1", "type": "table", "table": {"table_width": 2}, "archived": False},
        ],
        "has_more": False,
    })
    # Filas existentes en Notion equivalentes a la tabla local
    existing_rows = [
        {"type": "table_row", "table_row": {"cells": [[{"plain_text": "ID"}], [{"plain_text": "Nombre"}]]}},
        {"type": "table_row", "table_row": {"cells": [[{"plain_text": "A"}], [{"plain_text": "Uno"}]]}},
    ]
    monkeypatch.setattr(vsync_module, "_existing_table_signature", lambda bid: [
        [vsync_module._rich_text(c) for c in r["table_row"]["cells"]] for r in existing_rows
    ])
    monkeypatch.setattr(vsync_module, "safe_list", lambda pid, cur=None: {
        "results": [{"id": "t1", "type": "table", "table": {"table_width": 2}, "archived": False}],
        "has_more": False,
    })
    # El archivo local contiene exactamente la misma tabla
    md = tmp_path / "doc.md"
    md.write_text("| ID | Nombre |\n|---|---|\n| A | Uno |\n", encoding="utf-8")

    result = vsync_module.push_local_to_notion("pid1", md)

    assert result["tables_skipped"] == 0
    assert result["failed"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# B8 / B9 — vdoc_nblm y vsum
# ─────────────────────────────────────────────────────────────────────────────

def test_vdoc_nblm_usa_documentacion_active():
    module = load_module_from(L4_SCRIPTS / "vdoc_nblm.py", "nblm_test")

    assert module.ACTIVE_DIR == REPO_ROOT / "Documentación" / "ACTIVE"
    assert module.PROJECT_ROOT == REPO_ROOT
    assert "/Users/mauriciomeyran" not in str(module.PROJECT_ROOT)


def test_vdoc_nblm_avisa_si_falta_active_dir(tmp_path, monkeypatch, capsys):
    module = load_module_from(L4_SCRIPTS / "vdoc_nblm.py", "nblm_warn_test")
    monkeypatch.setattr(module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(module, "DIGEST_PATH", tmp_path / "digest.txt")
    monkeypatch.setattr(module, "ACTIVE_DIR", tmp_path / "NO_EXISTE")

    class Notebooks:
        @staticmethod
        def list():
            class NB:
                id = "nb-1"

            return [NB()]

    class Client:
        notebooks = Notebooks()

    monkeypatch.setattr(module, "get_notebooklm_client", lambda: Client())
    monkeypatch.setattr(module, "generate_local_digest", lambda: None)

    module.main()

    assert "ACTIVE_DIR no existe" in capsys.readouterr().out


def test_vsum_no_manda_parrafos_gigantes_en_un_chunk():
    module = load_module_from(L4_SCRIPTS / "vsum.py", "vsum_test")

    chunks = module.chunk_text("x" * 25000, max_chars=10000)

    assert len(chunks) == 3
    assert all(len(c) <= 10000 for c in chunks)


def test_vsum_respeta_limite_con_parrafos_normales():
    module = load_module_from(L4_SCRIPTS / "vsum.py", "vsum_test2")

    text = "\n\n".join("p" * 3000 for _ in range(5))  # 5 párrafos de 3000
    chunks = module.chunk_text(text, max_chars=10000)

    assert all(len(c) <= 10000 for c in chunks)
    assert len(chunks) == 2


# ─────────────────────────────────────────────────────────────────────────────
# B11 — deuda técnica: sin rutas del usuario en Layer 4
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name", sorted(p.name for p in L4_SCRIPTS.glob("*.py")))
def test_layer4_sin_rutas_del_usuario(name):
    source = (L4_SCRIPTS / name).read_text(encoding="utf-8")
    assert "/Users/mauriciomeyran" not in source, f"{name} tiene rutas absolutas del operador"
