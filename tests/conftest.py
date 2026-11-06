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
