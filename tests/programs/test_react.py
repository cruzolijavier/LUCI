"""LUCI-REACT with real inputs: TS-tools (needs Gaussian 16, so it runs only where g16 is)."""

import shutil

import pytest

from program_helpers import (  # noqa: F401 (luci and work are fixtures)
    luci, require_env, work,
)

pytestmark = pytest.mark.programs


@pytest.mark.skipif(shutil.which("g16") is None,
                    reason="TS-tools drives xTB through Gaussian 16: g16 is not on PATH")
def test_tstools_sn2_transition_state(work, luci):
    require_env("tstools")
    luci(work, "react", "--backend", "ts_tools", "--variant", "xtb", "--",
         "--input-file", "reactions.txt", "--proc", "2").ok()
    folder = work / "LUCI_REACT" / "TS-tools"
    assert list(folder.rglob("*.xyz")), "TS-tools wrote no transition state"
