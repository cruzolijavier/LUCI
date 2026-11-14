"""A whole workflow with real programs: SMILES -> conformers -> xTB optimization -> descriptors.

Checks the folder layout every run follows:

    <results>/LUCI_STRUCT/LUCI_data.dat
    <results>/LUCI_STRUCT/AQME_CSEARCH/...
    <results>/LUCI_STRUCT/AQME_CMIN/...
    <results>/LUCI_FEAT/LUCI_data.dat
    <results>/LUCI_FEAT/Morfeus/...
"""

import pytest

from program_helpers import (  # noqa: F401 (luci and work are fixtures)
    luci, luci_data, read_csv, require_env, sdf_records, work,
)

pytestmark = pytest.mark.programs


def test_struct_then_feat_workflow(work, luci):
    require_env("aqme")
    require_env("morfeus")
    luci(work, "struct", "--backend", "aqme_csearch", "--molecules", "molecules.csv",
         "--", "--program", "rdkit", "--sample", "3").ok()
    luci(work, "struct", "--backend", "aqme_cmin", "--structures", "LUCI_STRUCT/AQME_CSEARCH",
         "--", "--program", "xtb").ok()
    # The previous step's folder as input: results go to the same workflow folder, not inside it.
    run = luci(work, "feat", "--backend", "morfeus", "--structures", "LUCI_STRUCT/AQME_CMIN",
               "--", "--descriptors", "[sasa,dispersion]").ok()
    assert run.output_folder() == work / "LUCI_FEAT" / "Morfeus"
    assert sorted(p.name for p in work.glob("LUCI_*")) == ["LUCI_FEAT", "LUCI_STRUCT"]
    assert sorted(p.name for p in (work / "LUCI_STRUCT").iterdir()) == [
        "AQME_CMIN", "AQME_CSEARCH", "LUCI_data.dat"]
    assert not list((work / "LUCI_STRUCT" / "AQME_CMIN").glob("LUCI_*"))

    # One descriptor row per optimized conformer.
    conformers = sum(len(sdf_records(p)) for p in (work / "LUCI_STRUCT" / "AQME_CMIN").glob("*.sdf"))
    rows = read_csv(work / "LUCI_FEAT" / "Morfeus" / "morfeus_descriptors.csv")
    assert len(rows) == conformers
    assert all(float(r["sasa_area"]) > 0 and float(r["dispersion_p_int"]) > 0 for r in rows)

    struct = luci_data(work / "LUCI_STRUCT")
    feat = luci_data(work / "LUCI_FEAT")
    assert struct.index("AQME CSEARCH") < struct.index("AQME CMIN")
    assert struct.count("Result       : finished correctly (exit code 0)") == 2
    assert "Input from   : LUCI_STRUCT/AQME_CMIN (an earlier LUCI step)" in feat
    assert "Output folder: LUCI_FEAT/Morfeus" in feat
    assert "morfeus_descriptors.csv" in feat
    assert "luci feat --backend morfeus --structures LUCI_STRUCT/AQME_CMIN" in feat


def test_failed_run_is_recorded(work, luci):
    """A run that fails still leaves its block in LUCI_data.dat, with the exit code."""
    require_env("dbstep")
    run = luci(work, "feat", "--backend", "dbstep", "--structures", "substituents", "--output-dir", ".",
               "--", "--sterimol", "--atom1", "1", "--atom2", "99")
    assert run.code != 0
    data = luci_data(work / "LUCI_FEAT")
    assert "DBSTEP" in data and f"failed (exit code {run.code})" in data
