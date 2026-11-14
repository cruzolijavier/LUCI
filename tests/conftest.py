import json
import os
from pathlib import Path
import stat
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture
def luci_home(tmp_path, monkeypatch):
    """An isolated LUCI home with a fake pixi on PATH."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("LUCI_HOME", str(home))
    bindir = tmp_path / "bin"
    bindir.mkdir()
    pixi = bindir / ("pixi.exe" if os.name == "nt" else "pixi")
    pixi.write_text("#!/bin/sh\necho fake pixi \"$@\"\n")
    pixi.chmod(pixi.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("LUCI_PIXI", str(pixi))
    return home


def fake_install(home: Path, env_key: str):
    """Mark an environment as installed without running pixi."""
    from luci.envs.manager import EnvManager, MARKER
    manager = EnvManager(home)
    (manager.prefix(env_key)).mkdir(parents=True, exist_ok=True)
    manager.workspace(env_key).mkdir(parents=True, exist_ok=True)
    manager.manifest(env_key).write_text(manager.packaged_manifest(env_key).read_text())
    (manager.workspace(env_key) / MARKER).write_text(json.dumps({"manifest": manager._manifest_hash(env_key)}))
    return manager



# Test modules that build windows: their leftovers are collected after every test.
QT_MODULES = {"test_gui", "test_gui_update", "test_stop", "test_assistant"}


@pytest.fixture(autouse=True)
def _collect_qt_garbage_in_the_main_thread(request):
    """Free the windows a test leaves behind here, in the main thread.

    Python's cyclic garbage collector runs in whichever thread happens to allocate:
    if a closed window is collected by a worker thread (the HTTP server of
    test_updater, a check thread...), PySide 6.12 defers its deletion to the main
    thread and crashes there (Shiboken::BindingManager::runDeletionInMainThread);
    CircleCI saw it as a segfault in test_updater. The window applies the same rule
    with gui.app.MainGarbageCollector.
    """
    yield
    if request.module.__name__.rsplit(".", 1)[-1] in QT_MODULES:
        import gc
        gc.collect()
