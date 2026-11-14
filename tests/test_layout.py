"""Results folders (LUCI_<LAYER>/<Program>) and LUCI_data.dat, without running a real program."""

from pathlib import Path

from conftest import fake_install
from luci.inputs import LuciInputs
from luci.layout import (
    earlier_step, layer_folder_name, program_dir, program_folder_name, results_root,
)
from luci.registry import PROGRAMS, program
from luci.execution import run_program


def test_folder_names_are_unique_and_safe():
    names = {(p.layer, program_folder_name(p)) for p in PROGRAMS}
    assert len(names) == len(PROGRAMS)
    assert program_folder_name(program("aqme_csearch")) == "AQME_CSEARCH"
    assert program_folder_name(program("edboplus")) == "EDBOplus"
    assert all(set(name) <= set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
               for _layer, name in names)
    assert layer_folder_name("struct") == "LUCI_STRUCT"


def test_results_root_flattens_earlier_steps(tmp_path):
    root = tmp_path / "project"
    step = root / "LUCI_STRUCT" / "AQME_CSEARCH"
    assert results_root(step) == root
    assert results_root(root / "LUCI_STRUCT") == root
    assert results_root(root) == root
    assert results_root(root / "data") == root / "data"
    assert program_dir(root, program("morfeus")) == root / "LUCI_FEAT" / "Morfeus"
    assert earlier_step(step / "input_sdf") == "LUCI_STRUCT/AQME_CSEARCH"
    assert earlier_step(root / "data") == ""


def test_run_writes_luci_data(luci_home, tmp_path, capsys):
    manager = fake_install(luci_home, "aqme")
    csv = tmp_path / "mols.csv"
    csv.write_text("code_name,smiles\nethanol,CCO\n")
    spec = program("aqme_csearch")
    code = run_program(spec, spec.variant(), ["--program", "rdkit"], manager=manager,
                       inputs=LuciInputs(molecules=str(csv)),
                       luci_argv=["struct", "--backend", "aqme_csearch", "--molecules", "mols.csv"])
    assert code == 0
    folder = tmp_path / "LUCI_STRUCT" / "AQME_CSEARCH"
    assert f"[LUCI] Output folder: {folder}" in capsys.readouterr().out
    data = (tmp_path / "LUCI_STRUCT" / "LUCI_data.dat").read_text()
    assert data.startswith("=" * 78 + "\nLUCI_data.dat - LUCI-STRUCT (3D structures)")
    for text in ("AQME CSEARCH", "Result       : finished correctly (exit code 0)",
                 "Output folder: LUCI_STRUCT/AQME_CSEARCH", "Options      : --program rdkit",
                 "LUCI command : luci struct --backend aqme_csearch --molecules mols.csv",
                 "1 handed over: ethanol", "No result for: 1 input(s): ethanol"):
        assert text in data, text
    # A second run appends a block; the header is written once.
    run_program(spec, spec.variant(), [], manager=manager, inputs=LuciInputs(molecules=str(csv)))
    data = (tmp_path / "LUCI_STRUCT" / "LUCI_data.dat").read_text()
    assert data.count("LUCI_data.dat - ") == 1 and data.count("  AQME CSEARCH\n") == 2


def test_dry_run_writes_nothing(luci_home, tmp_path):
    manager = fake_install(luci_home, "dbstep")
    spec = program("dbstep")
    (tmp_path / "a.xyz").write_text("1\n\nH 0 0 0\n")
    assert run_program(spec, spec.variant(), [str(tmp_path / "a.xyz")], dry_run=True, manager=manager) == 0
    assert not (tmp_path / "LUCI_FEAT").exists()
