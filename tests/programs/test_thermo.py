"""LUCI-THERMO with real inputs: GoodVibes, universal_thermoGNN and ThermoMLIP."""

import math
import os

import pytest

from program_helpers import (  # noqa: F401 (luci and work are fixtures)
    luci, luci_data, read_csv, require_env, work,
)

pytestmark = pytest.mark.programs

# Reference thermochemistry of the frequency calculations in tests/data (Hartree, 298.15 K).
GAUSSIAN = {
    "methane_gaussian": {"scf_energy": -40.518383, "zpe": 0.044163, "gibbs_free_energy": -40.490912,
                         "multiplicity": "1", "level_of_theory": "B3LYP/6-31G(d)"},
    "hcn_triplet_gaussian": {"scf_energy": -93.153787, "zpe": 0.012567,
                             "gibbs_free_energy": -93.161850, "multiplicity": "3",
                             "level_of_theory": "B97D/6-31G(d)"},
}


def _check_row(row, reference):
    for key in ("scf_energy", "zpe", "gibbs_free_energy"):
        assert float(row[key]) == pytest.approx(reference[key], abs=2e-5), key
    assert row["multiplicity"] == reference["multiplicity"]
    assert row["level_of_theory"] == reference["level_of_theory"]


# --------------------------------------------------------------------------- GoodVibes
def test_goodvibes_folder_of_gaussian_outputs(work, luci):
    require_env("goodvibes")
    run = luci(work, "thermo", "--backend", "goodvibes", "--", "qm_outputs/*.log",
               "--csv", "thermo.csv").ok()
    # Results go next to the QM outputs, in LUCI_THERMO/GoodVibes.
    folder = work / "qm_outputs" / "LUCI_THERMO" / "GoodVibes"
    assert run.output_folder() == folder
    rows = {row["name"]: row for row in read_csv(folder / "thermo.csv")}
    assert set(rows) == {"methane_gaussian"}
    _check_row(rows["methane_gaussian"], GAUSSIAN["methane_gaussian"])
    assert (folder / "GoodVibes_output.dat").is_file()
    assert "GoodVibes" in luci_data(work / "qm_outputs" / "LUCI_THERMO")


def test_goodvibes_triplet_and_temperature(work, luci):
    require_env("goodvibes")
    luci(work, "thermo", "--backend", "goodvibes", "--output-dir", "res", "--",
         "qm_outputs/hcn_triplet_gaussian.out", "--csv", "t298.csv").ok()
    luci(work, "thermo", "--backend", "goodvibes", "--output-dir", "res", "--",
         "qm_outputs/hcn_triplet_gaussian.out", "--csv", "t500.csv", "--temp", "500").ok()
    folder = work / "res" / "LUCI_THERMO" / "GoodVibes"
    cold = read_csv(folder / "t298.csv")[0]
    hot = read_csv(folder / "t500.csv")[0]
    _check_row(cold, GAUSSIAN["hcn_triplet_gaussian"])
    # Same electronic energy; at higher T the -TS term makes G clearly lower.
    assert float(hot["scf_energy"]) == pytest.approx(float(cold["scf_energy"]), abs=1e-8)
    assert float(hot["gibbs_free_energy"]) < float(cold["gibbs_free_energy"]) - 0.01
    # The second run reused the folder and LUCI_data.dat has both runs.
    assert luci_data(work / "res" / "LUCI_THERMO").count("  GoodVibes\n") == 2


# --------------------------------------------------------------------------- thermoGNN
def test_thermognn_predicts_gibbs_formation_energies(work, luci):
    require_env("thermognn")
    run = luci(work, "thermo", "--backend", "thermognn", "--molecules", "molecules.csv").ok()
    folder = work / "LUCI_THERMO" / "universal_thermoGNN"
    assert run.output_folder() == folder
    rows = {row["code_name"]: row for row in read_csv(folder / "thermognn_predictions.csv")}
    assert set(rows) == {"pentane", "ethanol", "acetate"}
    for name, row in rows.items():
        value = float(row["formation_gibbs_pred"])
        assert math.isfinite(value), name
        assert float(row["edl_total_uncertainty"]) > 0, name
    # The anion is far more stable than the neutral molecules.
    assert float(rows["acetate"]["formation_gibbs_pred"]) < float(rows["ethanol"]["formation_gibbs_pred"])


# --------------------------------------------------------------------------- ThermoMLIP
@pytest.mark.skipif(not os.environ.get("HF_TOKEN"),
                    reason="ThermoMLIP needs Hugging Face access to the UMA weights (set HF_TOKEN)")
def test_thermomlip_single_molecule(work, luci):
    require_env("thermomlip")
    (work / "thermomlip.csv").write_text("")
    luci(work, "thermo", "--backend", "thermomlip", "--molecule", "CCO", "--code-name", "ethanol",
         "--", "--dataset-name", "luci_test", "--results-file", str(work / "thermomlip.csv"),
         "--num-conformers", "5", "--n-cores", "1").ok()
    text = (work / "thermomlip.csv").read_text()
    assert "ethanol" in text or "CCO" in text
