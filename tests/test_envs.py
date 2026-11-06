"""Which pixi LUCI uses."""

import os
import sys

import pytest


@pytest.mark.skipif(sys.platform == "win32", reason="shell-script stand-in for pixi")
def test_old_pixi_on_path_is_not_used(tmp_path, monkeypatch, luci_home):
    """Avogadro 2 puts an old pixi on PATH; it cannot read lock format 7."""
    from luci.envs import manager as m
    fake = tmp_path / "pixi"
    fake.write_text("#!/bin/sh\necho pixi 0.40.3\n")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.delenv("LUCI_PIXI", raising=False)
    assert m.EnvManager().pixi_path() != fake
