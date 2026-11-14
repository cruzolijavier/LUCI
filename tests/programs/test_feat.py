"""LUCI-FEAT with real inputs: AQME QDESCP, DBSTEP, Morfeus and Auto-QChem."""

import math
from pathlib import Path

import pytest

from program_helpers import (  # noqa: F401 (luci and work are fixtures)
    INPUTS, luci, read_csv, require_env, work,
)

pytestmark = pytest.mark.programs

SUBSTITUENTS = ("methyl", "isopropyl", "tert_butyl")


def _floats(row, *keys):
    return [float(row[key]) for key in keys]


# --------------------------------------------------------------------------- AQME QDESCP
def test_qdescp_from_molecule_csv(work, luci):
    """SMILES -> conformers -> GFN2-xTB descriptors, Boltzmann-averaged."""
    require_env("aqme")
    run = luci(work, "feat", "--backend", "aqme_qdescp", "--molecules", "molecules.csv",
               "--", "--program", "xtb").ok()
    folder = work / "LUCI_FEAT" / "AQME_QDESCP"
    assert run.output_folder() == folder
    tables = sorted(folder.glob("AQME-ROBERT_interpret_*.csv"))
    assert tables, f"no descriptor table in {sorted(p.name for p in folder.iterdir())}"
    rows = {row["code_name"]: row for row in read_csv(tables[0])}
    assert set(rows) == {"pentane", "ethanol", "acetate"}
    for name, row in rows.items():
        homo, lumo, gap = _floats(row, "HOMO", "LUMO", "HOMO-LUMO gap")
        assert homo < lumo and gap == pytest.approx(lumo - homo, abs=0.05), name
        assert float(row["SASA"]) > 50, name
    # GFN2-xTB orbital energies (eV): an alkane binds its electrons harder than the anion.
    assert float(rows["pentane"]["HOMO"]) == pytest.approx(-11.3, abs=0.4)
    assert float(rows["acetate"]["HOMO"]) > float(rows["pentane"]["HOMO"])
    assert float(rows["pentane"]["SASA"]) > float(rows["ethanol"]["SASA"])


def test_qdescp_from_structures(work, luci):
    require_env("aqme")
    luci(work, "feat", "--backend", "aqme_qdescp", "--structures", "substituents",
         "--output-dir", ".", "--", "--program", "xtb").ok()
    folder = work / "LUCI_FEAT" / "AQME_QDESCP"
    tables = sorted(folder.glob("AQME-ROBERT_full_*.csv"))
    assert tables
    rows = {row["code_name"]: row for row in read_csv(tables[0])}
    assert set(rows) == set(SUBSTITUENTS)
    assert float(rows["tert_butyl"]["SASA"]) > float(rows["isopropyl"]["SASA"]) > float(rows["methyl"]["SASA"])


# --------------------------------------------------------------------------- DBSTEP
def test_dbstep_sterimol_series(work, luci):
    """Sterimol of Me, iPr and tBu (atom 1 = H at the attachment point, atom 2 = first C)."""
    require_env("dbstep")
    run = luci(work, "feat", "--backend", "dbstep", "--structures", "substituents", "--output-dir", ".",
               "--", "--sterimol", "--atom1", "1", "--atom2", "2", "--csv", "sterimol.csv").ok()
    folder = work / "LUCI_FEAT" / "DBSTEP"
    assert run.output_folder() == folder
    rows = {Path(row["file"]).stem: row for row in read_csv(folder / "sterimol.csv")}
    assert set(rows) == set(SUBSTITUENTS)
    b1 = {name: float(rows[name]["bmin"]) for name in SUBSTITUENTS}
    b5 = {name: float(rows[name]["bmax"]) for name in SUBSTITUENTS}
    # Literature (Verloop, H as the dummy atom): Me B1 1.52-1.70, tBu B1 2.60-2.90, B5 3.17-3.30.
    assert b1["methyl"] == pytest.approx(1.70, abs=0.15)
    assert b1["tert_butyl"] == pytest.approx(2.85, abs=0.25)
    assert b5["tert_butyl"] == pytest.approx(3.25, abs=0.2)
    assert b1["methyl"] < b1["isopropyl"] < b1["tert_butyl"]
    assert b5["methyl"] < b5["isopropyl"]


def test_dbstep_buried_volume(work, luci):
    require_env("dbstep")
    luci(work, "feat", "--backend", "dbstep", "--structures", "substituents", "--output-dir", ".",
         "--", "--vbur", "--atom1", "2", "-r", "3.5", "--csv", "vbur.csv").ok()
    rows = {Path(r["file"]).stem: r for r in read_csv(work / "LUCI_FEAT" / "DBSTEP" / "vbur.csv")}
    vbur = {name: float(rows[name]["percent_vbur"]) for name in SUBSTITUENTS}
    assert all(0 < value < 100 for value in vbur.values())
    assert vbur["methyl"] < vbur["isopropyl"] < vbur["tert_butyl"]


# --------------------------------------------------------------------------- Morfeus
def test_morfeus_sterimol_and_buried_volume(work, luci):
    require_env("morfeus")
    run = luci(work, "feat", "--backend", "morfeus", "--structures", "substituents", "--output-dir", ".",
               "--", "--descriptors", "[sterimol,buried_volume]", "--atom_1", "1", "--atom_2", "2").ok()
    folder = work / "LUCI_FEAT" / "Morfeus"
    assert run.output_folder() == folder
    rows = {row["code_name"]: row for row in read_csv(folder / "morfeus_descriptors.csv")}
    assert set(rows) == set(SUBSTITUENTS)
    b1 = {n: float(rows[n]["sterimol_B1"]) for n in SUBSTITUENTS}
    vbur = {n: float(rows[n]["buried_volume_percent"]) for n in SUBSTITUENTS}
    assert b1["methyl"] == pytest.approx(1.70, abs=0.15)
    assert b1["methyl"] < b1["isopropyl"] < b1["tert_butyl"]
    assert vbur["methyl"] < vbur["isopropyl"] < vbur["tert_butyl"]


def test_morfeus_and_dbstep_agree(work, luci):
    """Two independent implementations of Sterimol must give the same B1/B5 on the same files."""
    require_env("morfeus")
    require_env("dbstep")
    luci(work, "feat", "--backend", "morfeus", "--structures", "substituents", "--output-dir", ".",
         "--", "--descriptors", "[sterimol]", "--atom_1", "1", "--atom_2", "2").ok()
    luci(work, "feat", "--backend", "dbstep", "--structures", "substituents", "--output-dir", ".",
         "--", "--sterimol", "--atom1", "1", "--atom2", "2", "--csv", "sterimol.csv").ok()
    morfeus = {r["code_name"]: r for r in read_csv(work / "LUCI_FEAT" / "Morfeus" / "morfeus_descriptors.csv")}
    dbstep = {Path(r["file"]).stem: r for r in read_csv(work / "LUCI_FEAT" / "DBSTEP" / "sterimol.csv")}
    for name in SUBSTITUENTS:
        assert float(morfeus[name]["sterimol_B1"]) == pytest.approx(float(dbstep[name]["bmin"]), abs=0.05)
        assert float(morfeus[name]["sterimol_B5"]) == pytest.approx(float(dbstep[name]["bmax"]), abs=0.05)


def test_morfeus_sasa_on_mixed_files(work, luci):
    """SDF, MOL, XYZ, Gaussian .gjf and .log in one folder: one row each, larger molecules more area."""
    require_env("morfeus")
    luci(work, "feat", "--backend", "morfeus", "--structures", "structures_mixed", "--output-dir", ".",
         "--", "--descriptors", "[sasa]").ok()
    rows = {r["code_name"]: r for r in read_csv(work / "LUCI_FEAT" / "Morfeus" / "morfeus_descriptors.csv")}
    assert set(rows) == {"acetophenone", "acetone", "pentane", "piperidine", "methane", "ammonium"}
    area = {name: float(row["sasa_area"]) for name, row in rows.items()}
    assert area["methane"] < area["acetone"] < area["pentane"] < area["acetophenone"]


def test_morfeus_xtb_and_pyramidalization(work, luci):
    require_env("morfeus")
    one = work / "acetone_only"
    one.mkdir()
    (one / "acetone.gjf").write_text((work / "structures_mixed" / "acetone.gjf").read_text())
    luci(work, "feat", "--backend", "morfeus", "--structures", "acetone_only", "--output-dir", ".",
         "--", "--descriptors", "[xtb,pyramidalization]", "--atom_1", "2").ok()
    row = read_csv(work / "LUCI_FEAT" / "Morfeus" / "morfeus_descriptors.csv")[0]
    # GFN2-xTB energy of acetone (Eh) and a planar carbonyl carbon (P close to 0... or to 1 by Morfeus' scale).
    assert float(row["xtb_energy"]) == pytest.approx(-13.53, abs=0.05)
    assert float(row["xtb_homo"]) < float(row["xtb_lumo"])
    assert float(row["xtb_ip"]) > 0 and math.isfinite(float(row["xtb_dipole"]))
    assert float(row["pyramidalization_P_angle"]) < 1.0


# --------------------------------------------------------------------------- Auto-QChem
def test_autoqchem_rejects_outputs_from_other_workflows(work, luci):
    """Auto-QChem only reads the jobs its own workflow writes; LUCI must say so, not write an empty table."""
    require_env("autoqchem")
    run = luci(work, "feat", "--backend", "autoqchem", "--", "--logs", "qm_outputs")
    assert run.code != 0
    assert "not any Gaussian output" in run.output
    assert "circular import" not in run.output


AUTOQCHEM_LOGS = INPUTS / "autoqchem_logs"


@pytest.mark.skipif(not list(AUTOQCHEM_LOGS.glob("*.log")),
                    reason="put Gaussian outputs from Auto-QChem's workflow in "
                           "tests/programs/inputs/autoqchem_logs to test parsing")
def test_autoqchem_parses_its_workflow_outputs(work, luci):
    require_env("autoqchem")
    luci(work, "feat", "--backend", "autoqchem", "--", "--logs", "autoqchem_logs").ok()
    rows = read_csv(work / "autoqchem_logs" / "LUCI_FEAT" / "Auto-QChem" / "autoqchem_descriptors.csv")
    assert len(rows) == len(list(AUTOQCHEM_LOGS.glob("*.log")))
    for row in rows:
        assert float(row["homo_energy"]) < float(row["lumo_energy"])
