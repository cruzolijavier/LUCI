"""LUCI-STRUCT with real inputs: AQME CSEARCH, AQME CMIN, racerTS and MolSimplify."""

import math
from pathlib import Path

import pytest

from program_helpers import (  # noqa: F401 (luci and work are fixtures)
    luci, luci_data, require_env, sdf_atom_count, sdf_property, sdf_records, work, xyz_frames,
)

pytestmark = pytest.mark.programs

# Atoms (with hydrogens) and charge of every molecule in inputs/molecules.csv.
MOLECULES = {"pentane": (17, 0), "ethanol": (9, 0), "acetate": (7, -1)}
# Atoms of every structure in inputs/structures_mixed (SDF, MOL, XYZ, Gaussian .gjf and .log).
STRUCTURES = {"acetophenone": 17, "acetone": 10, "pentane": 17, "piperidine": 17, "methane": 5,
              "ammonium": 5}


def _conformers(folder: Path, name: str, suffix: str = "_rdkit.sdf") -> list[list[str]]:
    path = folder / f"{name}{suffix}"
    assert path.is_file(), f"{path.name} was not written; folder has {sorted(p.name for p in folder.iterdir())}"
    records = sdf_records(path)
    assert records, f"{path.name} is empty"
    return records


def _distance(a: list[float], b: list[float]) -> float:
    return math.dist(a, b)


def _sdf_coordinates(record: list[str]) -> list[list[float]]:
    count = sdf_atom_count(record)
    return [[float(line[0:10]), float(line[10:20]), float(line[20:30])] for line in record[4:4 + count]]


# --------------------------------------------------------------------------- AQME CSEARCH
def test_csearch_from_molecule_csv(work, luci):
    require_env("aqme")
    run = luci(work, "struct", "--backend", "aqme_csearch", "--molecules", "molecules.csv",
               "--", "--program", "rdkit", "--sample", "5").ok()
    folder = work / "LUCI_STRUCT" / "AQME_CSEARCH"
    assert run.output_folder() == folder
    for name, (atoms, charge) in MOLECULES.items():
        records = _conformers(folder, name)
        assert 1 <= len(records) <= 5, f"{name}: {len(records)} conformers with --sample 5"
        assert {sdf_atom_count(r) for r in records} == {atoms}, f"{name}: wrong number of atoms"
        assert int(float(sdf_property(records[0], "Real charge"))) == charge
    # Pentane is flexible (several conformers), ethanol is not worth more than a few.
    assert len(sdf_records(folder / "pentane_rdkit.sdf")) > 1
    assert (folder / "CSEARCH_data.dat").is_file()
    assert "No result for" not in run.output


def test_csearch_from_one_smiles(work, luci):
    require_env("aqme")
    luci(work, "struct", "--backend", "aqme_csearch", "--molecule", "CC(=O)c1ccccc1",
         "--code-name", "acetophenone", "--", "--program", "rdkit").ok()
    records = _conformers(work / "LUCI_STRUCT" / "AQME_CSEARCH", "acetophenone")
    assert {sdf_atom_count(r) for r in records} == {17}


def test_csearch_from_mixed_structure_files(work, luci):
    """SDF, MOL, XYZ, Gaussian input and Gaussian output in one folder: LUCI converts them."""
    require_env("aqme")
    run = luci(work, "struct", "--backend", "aqme_csearch", "--structures", "structures_mixed",
               "--output-dir", ".", "--", "--program", "rdkit", "--sample", "3").ok()
    folder = work / "LUCI_STRUCT" / "AQME_CSEARCH"
    for name, atoms in STRUCTURES.items():
        records = _conformers(folder, name)
        assert {sdf_atom_count(r) for r in records} == {atoms}, name
    ammonium = sdf_records(folder / "ammonium_rdkit.sdf")[0]
    assert int(float(sdf_property(ammonium, "Real charge"))) == 1
    # The converted SDF files stay inside the program folder, never in the user's folder.
    assert (folder / "input_sdf").is_dir()
    assert not (work / "structures_mixed" / "input_sdf").exists()
    assert "converted to SDF with Open Babel" in run.output


def test_csearch_molecules_with_errors(work, luci):
    require_env("aqme")
    refused = luci(work, "struct", "--backend", "aqme_csearch", "--molecules",
                   "molecules_with_errors.csv", "--", "--program", "rdkit")
    assert refused.code != 0
    assert "smiles cell is empty" in refused.output and "--skip-invalid" in refused.output
    assert not (work / "LUCI_STRUCT" / "AQME_CSEARCH" / "butane_rdkit.sdf").exists()
    luci(work, "struct", "--backend", "aqme_csearch", "--molecules", "molecules_with_errors.csv",
         "--skip-invalid", "--", "--program", "rdkit").ok()
    folder = work / "LUCI_STRUCT" / "AQME_CSEARCH"
    assert {sdf_atom_count(r) for r in _conformers(folder, "butane")} == {14}
    assert not list(folder.glob("no_smiles*"))


# --------------------------------------------------------------------------- AQME CMIN
def test_cmin_xtb_optimizes_csearch_conformers(work, luci):
    require_env("aqme")
    luci(work, "struct", "--backend", "aqme_csearch", "--molecules", "molecules.csv",
         "--", "--program", "rdkit", "--sample", "3").ok()
    run = luci(work, "struct", "--backend", "aqme_cmin", "--structures",
               "LUCI_STRUCT/AQME_CSEARCH", "--", "--program", "xtb").ok()
    folder = work / "LUCI_STRUCT" / "AQME_CMIN"
    assert run.output_folder() == folder
    assert "crashed" not in run.output
    # GFN2-xTB total energies of the lowest conformer (the SDF stores kcal/mol).
    hartree = 627.5095
    expected = {"ethanol": -11.392, "pentane": -16.830, "acetate": -14.166}
    for name, (atoms, charge) in MOLECULES.items():
        records = _conformers(folder, name, ".sdf") if (folder / f"{name}.sdf").exists() \
            else _conformers(folder, f"{name}_rdkit", ".sdf")
        assert {sdf_atom_count(r) for r in records} == {atoms}
        energy = float(sdf_property(records[0], "Energy")) / hartree
        assert energy == pytest.approx(expected[name], abs=0.01), f"{name}: E = {energy:.3f} Eh"
    # Both steps documented in one LUCI_data.dat, the second one pointing at the first.
    data = luci_data(work / "LUCI_STRUCT")
    assert data.count("AQME CSEARCH") >= 1 and data.count("AQME CMIN") >= 1
    assert "Input from   : LUCI_STRUCT/AQME_CSEARCH" in data


# --------------------------------------------------------------------------- racerTS
def test_racerts_ground_state_from_csv(work, luci):
    require_env("racerts")
    run = luci(work, "struct", "--backend", "racerts", "--molecules", "molecules.csv",
               "--", "--task", "gs", "--seed", "12").ok()
    folder = work / "LUCI_STRUCT" / "racerTS"
    for name, (atoms, _charge) in MOLECULES.items():
        frames = xyz_frames(folder / f"{name}_racerts.xyz")
        assert frames and {len(atoms_) for _, atoms_ in frames} == {atoms}, name
        # LUCI adds an SDF copy of every new XYZ ensemble.
        assert len(sdf_records(folder / f"{name}_racerts.sdf")) == len(frames)
    assert len(xyz_frames(folder / "pentane_racerts.xyz")) > 1
    assert "SDF copies written" in run.output


def test_racerts_constrained_keeps_fixed_atoms(work, luci):
    require_env("racerts")
    luci(work, "struct", "--backend", "racerts", "--structures", "substituents", "--output-dir", ".",
         "--", "--task", "constrained", "--hard", "0 1 2", "--seed", "12").ok()
    folder = work / "LUCI_STRUCT" / "racerTS"
    for name in ("methyl", "isopropyl", "tert_butyl"):
        reference = _sdf_coordinates(sdf_records(work / "substituents" / f"{name}.sdf")[0])
        frames = xyz_frames(folder / f"{name}_racerts.xyz")
        assert frames, name
        for _, atoms in frames:
            coords = [[float(v) for v in line.split()[1:4]] for line in atoms]
            # The fixed atoms keep their geometry (distances, so alignment does not matter).
            for i, j in ((0, 1), (1, 2), (0, 2)):
                assert _distance(coords[i], coords[j]) == pytest.approx(
                    _distance(reference[i], reference[j]), abs=0.02), (name, i, j)


# --------------------------------------------------------------------------- MolSimplify
def test_molsimplify_builds_octahedral_iron_complex(work, luci):
    require_env("molsimplify")
    luci(work, "struct", "--backend", "molsimplify", "--output-dir", ".", "--",
         "--metal", "fe", "--ligands", "water", "--counts", "[6]", "--oxstate", "2",
         "--coord", "6", "--geometry", "oct", "--spin", "5", "--jobname", "fe_aqua").ok()
    folder = work / "LUCI_STRUCT" / "MolSimplify"
    xyz = sorted(folder.rglob("fe_aqua*.xyz"))
    assert xyz, "MolSimplify wrote no structure"
    _, atoms = xyz_frames(xyz[0])[0]
    symbols = [line.split()[0] for line in atoms]
    assert len(atoms) == 19 and symbols.count("Fe") == 1 and symbols.count("O") == 6
    coords = [[float(v) for v in line.split()[1:4]] for line in atoms]
    iron = coords[symbols.index("Fe")]
    bonds = sorted(_distance(iron, c) for s, c in zip(symbols, coords) if s == "O")
    assert all(1.8 < d < 2.5 for d in bonds), bonds
    assert xyz[0].with_suffix(".sdf").is_file()
