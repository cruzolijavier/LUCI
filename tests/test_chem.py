"""LUCI's checks of molecule CSVs and structure folders, and how they reach each program.

LUCI has no chemistry library: these checks are plain Python, and the
conversion to SDF is done by Open Babel inside a program's environment
(tested at the end when an environment with Open Babel is available).
"""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from conftest import fake_install
from luci.chem.molecules import name_issues, read_molecules, single_molecule, write_native
from luci.chem.structures import (
    StructureError, new_outputs, plan_folder, prepare_folder, read_gaussian_input, read_qm_output,
    sdf_dimension, snapshot,
)
from luci.chem.table import read_table
from luci.cli import parse, run
from luci.execution import absolutize, prepare
from luci.inputs import InputError, LuciInputs, missing_outputs
from luci.registry import program

DATA = Path(__file__).parent / "data"
RUNNER = Path(__file__).resolve().parents[1] / "src" / "luci" / "runners" / "to_sdf.py"
WATER = "3\ncharge=0 mult=1\nO 0.000 0.000 0.000\nH 0.957 0.000 0.000\nH -0.240 0.927 0.000\n"
SDF = """water
     RDKit          3D

  3  2  0  0  0  0  0  0  0  0999 V2000
    0.0000    0.0000    0.1000 O   0  0
    0.9570    0.0000    0.0000 H   0  0
   -0.2400    0.9270    0.0000 H   0  0
  1  2  1  0
  1  3  1  0
M  END
$$$$
"""


def fake_converter(jobs, work_dir):
    """Stands in for Open Babel: writes a one-record SDF per job."""
    for item in jobs:
        item.target.write_text(SDF.replace("water", item.source.stem))
        item.structures = 1


# --------------------------------------------------------------------- CSV and names
def test_no_chemistry_library_is_needed():
    import luci.chem.molecules  # noqa: F401
    import luci.chem.structures  # noqa: F401
    import luci.inputs  # noqa: F401
    assert "rdkit" not in sys.modules


def test_semicolon_cp1252_csv_with_problems(tmp_path):
    csv = tmp_path / "mols.csv"
    csv.write_bytes("code_name;smiles;charge\r\nétanol;CCO;0\r\nbad ring;C1CC;\r\n;CC;\r\n"
                    "dup;CCO;\r\nDUP;CCN;\r\nempty;;\r\n".encode("cp1252"))
    molset = read_molecules(csv)
    assert molset.file_ok
    assert [i.code for i in molset.issues] == ["encoding", "delimiter"]
    by_line = {r.line: r for r in molset.records}
    # The SMILES are not checked: C1CC is passed on as written.
    assert by_line[3].name == "bad_ring" and by_line[3].ok and by_line[3].smiles == "C1CC"
    assert not by_line[4].ok  # empty code_name
    assert any(i.code == "duplicate_name" for i in by_line[6].issues)  # Windows ignores case
    assert any(i.code == "smiles" for i in by_line[7].issues)
    assert any("accented" in i.message for i in by_line[2].issues)
    assert molset.counts()["error"] == 3


def test_missing_columns_suggest_the_rename(tmp_path):
    csv = tmp_path / "a.csv"
    csv.write_text("Name,Structure\nA,CCO\nB,c1ccccc1\n")
    hints = [i.hint for i in read_molecules(csv).issues]
    assert hints == ["Rename the column 'Structure' to smiles.", "Rename the column 'Name' to code_name."]


def test_csv_formats(tmp_path):
    fake = tmp_path / "book.csv"
    fake.write_bytes(b"PK\x03\x04rest")
    assert read_table(fake).issues[0].code == "excel"
    empty = tmp_path / "e.csv"
    empty.write_text("")
    assert read_table(empty).issues[0].code == "empty"
    assert read_table(tmp_path / "nope.csv").issues[0].code == "missing"
    sep = tmp_path / "sep.csv"
    sep.write_text("sep=;\ncode_name;smiles\na;CCO\n")
    assert read_molecules(sep).records[0].smiles == "CCO"
    utf16 = tmp_path / "u16.csv"
    utf16.write_bytes("code_name,smiles\na,CCO\n".encode("utf-16-le"))
    assert read_molecules(utf16).records[0].name == "a"
    quote = tmp_path / "q.csv"
    quote.write_text('code_name,smiles\n"a,CCO\nb,CC\n')
    assert read_table(quote).issues[-1].code == "quote"


def test_names():
    assert name_issues("my mol")[0] == "my_mol"
    assert name_issues("a/b")[1][0].level == "error"
    assert name_issues("CON")[1][0].level == "error"
    assert name_issues("x.")[1][0].level == "error"
    assert name_issues("ok_name-1")[1] == []


def test_native_layouts(tmp_path):
    csv = tmp_path / "m.csv"
    csv.write_text("smiles,code_name,charge,smiles_original\nCCO,eth anol,0,OCC\nCC,,,\n")
    molset = read_molecules(csv)
    aqme, rows = write_native(molset, tmp_path / "aqme.csv",
                              (("smiles", "SMILES"), ("code_name", "code_name")), skip_invalid=True)
    # smiles_* columns would be read as more molecules by AQME: left out.
    assert rows == 1 and aqme.read_text() == "SMILES,code_name,charge\nCCO,eth_anol,0\n"
    mlip, _ = write_native(molset, tmp_path / "mlip.csv", (("code_name", "id"), ("smiles", "smiles")),
                           keep_extra=False, skip_invalid=True)
    assert mlip.read_text() == "id,smiles\neth_anol,CCO\n"


def test_single_molecule_default_name():
    assert single_molecule("CCO").records[0].name == "molecule"
    assert single_molecule("CCO", "ethanol").records[0].name == "ethanol"
    assert not single_molecule("", "x").ok


# --------------------------------------------------------------------- structures (plain text)
def test_gaussian_and_orca_geometries():
    geometry, issues = read_qm_output((DATA / "methane_gaussian.log").read_text())
    assert geometry.symbols.count("H") == 4 and (geometry.charge, geometry.mult) == (0, 1)
    geometry, _ = read_qm_output((DATA / "hcn_triplet_gaussian.out").read_text())
    assert (geometry.charge, geometry.mult) == (0, 3)
    geometry, _ = read_qm_output((DATA / "da_endo_orca.out").read_text())
    assert (geometry.charge, geometry.mult) == (0, 1) and len(geometry.symbols) > 10
    with pytest.raises(StructureError):
        read_qm_output("nothing useful")


def test_gaussian_input_details():
    text = ("%chk=a\n# hf\n\ntitle\n\n0,1\nO 0 0.0 0.0 0.0\nH 0 0.957D+00 0 0\nBq 1 1 1\n"
            "H-Bq 2 2 2\nH 0 -0.24 0.927 0\n\n")
    geometry = read_gaussian_input(text)
    assert geometry.symbols == ["O", "H", "H"] and geometry.coords[1][0] == pytest.approx(0.957)
    with pytest.raises(StructureError, match="Z-matrix"):
        read_gaussian_input("# hf\n\nz\n\n0 1\nC\nH 1 1.09\n\n")


def test_link1_charge_belongs_to_the_last_geometry():
    log = (DATA / "methane_gaussian.log").read_text()
    second = log.replace("Charge =  0 Multiplicity = 1", "Charge =  1 Multiplicity = 2")
    geometry, _ = read_qm_output(log + "\n" + second)
    assert (geometry.charge, geometry.mult) == (1, 2)


def test_plan_folder(tmp_path):
    (tmp_path / "methane.gjf").write_text("# hf\n\nt\n\n0 1\nC 0 0 0\n\n")
    (tmp_path / "methane.log").write_text((DATA / "methane_gaussian.log").read_text())
    (tmp_path / "w.sdf").write_text(SDF)
    (tmp_path / "w.xyz").write_text(WATER)
    flat = SDF.replace("     RDKit          3D", "     RDKit          2D").replace("0.1000", "0.0000")
    (tmp_path / "flat.mol").write_text(flat.replace("3  2", "4  2").replace(
        "   -0.2400", "    1.0000    1.0000    0.0000 C   0  0\n   -0.2400"))
    (tmp_path / "empty.xyz").write_text("")
    (tmp_path / "notes.txt").write_text("x")
    result = plan_folder(tmp_path)
    by_name = {item.source.name: item for item in result.files}
    # The finished calculation wins over its input; the SDF over the XYZ.
    assert "methane.log" in by_name and "methane.gjf" not in by_name
    assert "w.sdf" in by_name and "w.xyz" not in by_name
    assert by_name["methane.log"].action == "convert" and by_name["methane.log"].charge == 0
    assert by_name["w.sdf"].action == "use"
    assert not by_name["flat.mol"].ok and not by_name["empty.xyz"].ok
    assert len(result.issues) == 2  # two "same name" warnings


def test_sdf_dimension():
    path = DATA / "methane_gaussian.log"
    assert sdf_dimension(path) == (0, False)


def test_prepare_folder_converts_caches_and_never_touches_user_files(tmp_path):
    src = tmp_path / "in"
    src.mkdir()
    (src / "water.xyz").write_text(WATER)
    (src / "w2.sdf").write_text(SDF)
    work = tmp_path / "out" / "input_sdf"
    calls = []

    def converter(jobs, work_dir):
        calls.append([j.source.name for j in jobs])
        fake_converter(jobs, work_dir)
    first = prepare_folder(src, work, converter)
    assert first.ok and first.folder == work and calls == [["water.xyz"]]
    assert sorted(p.name for p in work.glob("*.sdf")) == ["w2.sdf", "water.sdf"]
    prepare_folder(src, work, converter)
    assert calls == [["water.xyz"]]  # unchanged: reused
    (src / "water.xyz").rename(src / "h2o.xyz")
    prepare_folder(src, work, converter)
    assert sorted(p.name for p in work.glob("*.sdf")) == ["h2o.sdf", "w2.sdf"]
    # A file LUCI did not make is never overwritten or deleted.
    (work / "mine.sdf").write_text("keep")
    (src / "mine.xyz").write_text(WATER)
    result = prepare_folder(src, work, converter, skip_invalid=True)
    assert (work / "mine.sdf").read_text() == "keep"
    assert any(i.code == "exists" for item in result.files for i in item.issues)


def test_prepare_folder_never_converts_into_the_users_folder(tmp_path):
    (tmp_path / "water.xyz").write_text(WATER)
    result = prepare_folder(tmp_path, tmp_path, fake_converter)
    assert result.folder == tmp_path / "input_sdf"


def test_sdf_only_folder_is_used_as_it_is(tmp_path):
    (tmp_path / "w.sdf").write_text(SDF)
    result = prepare_folder(tmp_path, tmp_path / "work", None)
    assert result.folder == tmp_path and not (tmp_path / "work").exists()


def test_dry_run_writes_nothing(tmp_path):
    (tmp_path / "water.xyz").write_text(WATER)
    result = prepare_folder(tmp_path, tmp_path / "work", None, dry_run=True)
    assert result.ok and not (tmp_path / "work").exists()


def test_new_outputs(tmp_path):
    (tmp_path / "old.sdf").write_text(SDF)
    (tmp_path / "old.xyz").write_text(WATER)
    before = snapshot(tmp_path, ("**/*.xyz", "**/*.sdf"))
    (tmp_path / "run").mkdir()
    (tmp_path / "run" / "complex.xyz").write_text(WATER)
    (tmp_path / "old.xyz").write_text(WATER + "\n")
    os.utime(tmp_path / "old.xyz", (1e9 + 5, 2e9))
    items = new_outputs(tmp_path, ("**/*.xyz",), before)
    # old.sdf existed before the run: never replaced.
    assert [item.target.name for item in items] == ["complex.sdf"]


# --------------------------------------------------------------------- reaching the program
def _prepare(luci_home, key, inputs, tmp_path, env="aqme", native=(), **kwargs):
    manager = fake_install(luci_home, env)
    spec = program(key)
    variant = kwargs.pop("variant", None)
    return prepare(spec, spec.variant(variant), list(native), str(tmp_path / "out"), manager,
                   inputs=inputs, cwd=tmp_path, **kwargs)


def test_aqme_gets_its_csv_layout(luci_home, tmp_path):
    csv = tmp_path / "m, v2.csv"
    csv.write_text("code_name;smiles\nethanol;CCO\n")
    prepared = _prepare(luci_home, "aqme_csearch", LuciInputs(molecules=str(csv)), tmp_path)
    value = prepared.argv[prepared.argv.index("--input") + 1]
    assert value == ".luci/inputs/m_v2.csv"  # relative, and no ',' that AQME would split on
    assert (prepared.outdir / value).read_text() == "SMILES,code_name\nCCO,ethanol\n"
    assert prepared.inputs.names == ["ethanol"]


def test_errors_stop_the_run_unless_skipped(luci_home, tmp_path):
    csv = tmp_path / "m.csv"
    csv.write_text("code_name,smiles\nok,CCO\na/b,CC\n")
    with pytest.raises(InputError, match="cannot be used in file names"):
        _prepare(luci_home, "aqme_csearch", LuciInputs(molecules=str(csv)), tmp_path)
    prepared = _prepare(luci_home, "aqme_csearch", LuciInputs(molecules=str(csv), skip_invalid=True),
                        tmp_path)
    assert prepared.inputs.names == ["ok"]


def test_typed_smiles_flags_and_one_row_csv(luci_home, tmp_path):
    prepared = _prepare(luci_home, "aqme_csearch", LuciInputs(molecule="CCO", code_name="eth"), tmp_path)
    argv = prepared.argv
    assert argv[argv.index("--smi") + 1] == "CCO" and argv[argv.index("--name") + 1] == "eth"
    prepared = _prepare(luci_home, "thermognn", LuciInputs(molecule="CCO", code_name="eth"), tmp_path,
                        env="thermognn")
    path = Path(prepared.argv[prepared.argv.index("--input") + 1])
    assert path.read_text() == "smiles,code_name\nCCO,eth\n"


def test_thermomlip_columns(luci_home, tmp_path):
    csv = tmp_path / "m.csv"
    csv.write_text("smiles,code_name,charge\nCCO,eth,0\n")
    prepared = _prepare(luci_home, "thermomlip", LuciInputs(molecules=str(csv)), tmp_path,
                        env="thermomlip", variant="batch")
    path = Path(prepared.argv[prepared.argv.index("--csv") + 1])
    assert path.read_text() == "id,smiles\neth,CCO\n"


def test_relative_structures_folder(luci_home, tmp_path):
    folder = tmp_path / "ligands"
    folder.mkdir()
    (folder / "w.sdf").write_text(SDF)
    manager = fake_install(luci_home, "dbstep")
    spec = program("dbstep")
    prepared = prepare(spec, spec.variant(), ["--sterimol"], "", manager, cwd=tmp_path,
                       inputs=LuciInputs(structures="ligands"))
    assert str(folder.resolve() / "*.sdf") in prepared.argv


def test_native_input_flag_with_standard_input_is_refused(luci_home, tmp_path):
    csv = tmp_path / "m.csv"
    csv.write_text("code_name,smiles\na,CCO\n")
    with pytest.raises(InputError, match="--input"):
        _prepare(luci_home, "aqme_csearch", LuciInputs(molecules=str(csv)), tmp_path,
                 native=["--input", "other.csv"])


def test_wrong_kind_of_input_is_explained(luci_home, tmp_path):
    with pytest.raises(InputError, match="folder of 3D structures"):
        _prepare(luci_home, "aqme_cmin", LuciInputs(molecule="CCO"), tmp_path)


def test_default_output_is_next_to_the_input(luci_home, tmp_path):
    folder = tmp_path / "project"
    folder.mkdir()
    csv = folder / "m.csv"
    csv.write_text("code_name,smiles\nethanol,CCO\n")
    manager = fake_install(luci_home, "aqme")
    spec = program("aqme_csearch")
    prepared = prepare(spec, spec.variant(), [], "", manager, cwd=tmp_path,
                       inputs=LuciInputs(molecules=str(csv)))
    assert prepared.outdir == folder.resolve() / "CSEARCH"


def test_aqme_list_syntax_is_absolutized(tmp_path):
    (tmp_path / "a.sdf").write_text("x")
    tokens = absolutize(["--files", "[a.sdf,b.sdf]"], tmp_path, {"--files"})
    assert tokens[1] == f"[{(tmp_path / 'a.sdf').resolve()},b.sdf]"


def test_missing_outputs(tmp_path):
    (tmp_path / "ethanol_rdkit.sdf").write_text("x")
    (tmp_path / "phenol.sdf").write_text("x")       # AQME 2.1 CMIN naming
    (tmp_path / "lib_1_rdkit.sdf").write_text("x")  # several molecules in lib.sdf
    (tmp_path / "empty_rdkit.sdf").write_text("")
    assert missing_outputs(["ethanol", "phenol", "lib", "empty", "acetate"], tmp_path,
                           "{name}_*.sdf") == ["empty", "acetate"]


# --------------------------------------------------------------------- command line
def test_cli_options_and_check(tmp_path, capsys):
    parsed = parse(["struct", "--backend", "aqme_csearch", "--molecules", "m.csv", "--skip-invalid",
                    "--", "--sample", "3"])
    assert parsed["molecules"] == "m.csv" and parsed["skip_invalid"] and parsed["native"] == ["--sample", "3"]
    trailing = parse(["struct", "--backend", "aqme_csearch", "--sample", "3", "--molecule", "CCO",
                      "--code-name", "e"])
    assert trailing["molecule"] == "CCO" and trailing["code_name"] == "e"
    csv = tmp_path / "m.csv"
    csv.write_text("code_name,smiles\na,CCO\nb b,CC\n")
    assert run(["check", str(csv)]) == 0
    assert "LUCI uses 'b_b'" in capsys.readouterr().out
    assert run(["check", "--molecules", str(csv)]) == 0
    csv.write_text("code_name,smiles\na/b,CCO\n")
    assert run(["check", str(csv)]) == 1
    assert run(["struct", "--backend", "aqme_csearch", "--molecules", "a", "--molecule", "C"]) == 2
    assert run(["struct", "--backend", "aqme_csearch", "--molecule", ""]) == 2
    assert run(["thermo", "--backend", "thermomlip", "--variant", "single", "--molecules", "x.csv"]) == 2


# --------------------------------------------------------------------- Open Babel (real)
def _python_with_openbabel():
    candidates = [os.environ.get("LUCI_OPENBABEL_PYTHON", "")]
    home = os.environ.get("LUCI_HOME", "")
    for root in (home, "/tmp/lucihome2"):
        if root:
            candidates.append(str(Path(root) / "envs" / "aqme" / ".pixi" / "envs" / "default" / "bin" / "python"))
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            probe = subprocess.run([candidate, "-c", "from openbabel import pybel"], capture_output=True)
            if probe.returncode == 0:
                return candidate
    return None


@pytest.mark.skipif(_python_with_openbabel() is None, reason="no environment with Open Babel here")
def test_to_sdf_runner_with_open_babel(tmp_path):
    python = _python_with_openbabel()
    (tmp_path / "w.xyz").write_text(WATER + WATER)
    geometry, _ = read_qm_output((DATA / "hcn_triplet_gaussian.out").read_text())
    job = tmp_path / "job.json"
    results = tmp_path / "results.json"
    job.write_text(json.dumps({"results": str(results), "files": [
        {"source": str(tmp_path / "w.xyz"), "text": "", "fmt": "xyz", "target": str(tmp_path / "w.sdf"),
         "name": "w", "charge": 0, "mult": 1},
        {"source": "", "text": geometry.xyz("hcn"), "fmt": "xyz", "target": str(tmp_path / "hcn.sdf"),
         "name": "hcn", "charge": 0, "mult": 3},
        {"source": str(tmp_path / "nope.xyz"), "text": "", "fmt": "xyz",
         "target": str(tmp_path / "nope.sdf"), "name": "nope", "charge": None, "mult": None},
    ]}))
    subprocess.run([python, str(RUNNER), str(job)], check=True)
    outcome = json.loads(results.read_text())
    assert outcome[str(tmp_path / "w.sdf")]["ok"] and outcome[str(tmp_path / "w.sdf")]["structures"] == 2
    assert not outcome[str(tmp_path / "nope.sdf")]["ok"]
    text = (tmp_path / "hcn.sdf").read_text()
    assert text.startswith("hcn\n") and ">  <Mult>\n3\n" in text and ">  <Real charge>\n0\n" in text
    assert sdf_dimension(tmp_path / "w.sdf")[0] == 2


@pytest.mark.skipif(_python_with_openbabel() is None, reason="no environment with Open Babel here")
def test_charges_are_placed_on_atoms_and_sdf_properties_kept(tmp_path):
    python = _python_with_openbabel()
    (tmp_path / "nh4.xyz").write_text("5\ncharge=1\nN 0 0 0\nH 0.59 0.59 0.59\nH -0.59 -0.59 0.59\n"
                                      "H -0.59 0.59 -0.59\nH 0.59 -0.59 -0.59\n")
    record = SDF.replace("$$$$", ">  <Real charge>\n0\n\n>  <energy>\n-39.8\n\n$$$$")
    (tmp_path / "two.sd").write_text(record + SDF.replace("water", "water2"))
    job = tmp_path / "job.json"
    results = tmp_path / "r.json"
    job.write_text(json.dumps({"results": str(results), "files": [
        {"source": str(tmp_path / "nh4.xyz"), "text": "", "fmt": "xyz", "target": str(tmp_path / "nh4.sdf"),
         "name": "nh4", "charge": 1, "mult": None},
        {"source": str(tmp_path / "two.sd"), "text": "", "fmt": "sdf", "target": str(tmp_path / "two.sdf"),
         "name": "two", "charge": None, "mult": None}]}))
    subprocess.run([python, str(RUNNER), str(job)], check=True)
    check = (
        "from rdkit import Chem\n"
        "import sys\n"
        "nh4 = [m for m in Chem.SDMolSupplier(sys.argv[1], removeHs=False)]\n"
        "two = [m for m in Chem.SDMolSupplier(sys.argv[2], removeHs=False)]\n"
        "print(Chem.GetFormalCharge(nh4[0]), len(two), two[0].GetProp('energy'), two[0].GetProp('Real charge'))\n")
    out = subprocess.run([python, "-c", check, str(tmp_path / "nh4.sdf"), str(tmp_path / "two.sdf")],
                         capture_output=True, text=True, check=True).stdout.split()
    assert out == ["1", "2", "-39.8", "0"]


def test_counterpoise_job_charge_is_the_whole_system():
    log = (DATA / "methane_gaussian.log").read_text()
    fragments = log.replace("Charge =  0 Multiplicity = 1",
                            "Charge =  1 Multiplicity = 1 in supermolecule\n"
                            " Charge =  0 Multiplicity = 1 in fragment      1.", 1)
    geometry, _ = read_qm_output(fragments)
    assert geometry.charge == 1


def test_xyz_with_unknown_element(tmp_path):
    (tmp_path / "q.xyz").write_text("1\n\nQq 0 0 0\n")
    item = plan_folder(tmp_path).files[0]
    assert not item.ok and "not an element" in item.issues[0].message


def test_wildcards_in_the_structures_path_are_refused(luci_home, tmp_path):
    folder = tmp_path / "run [3]"
    folder.mkdir()
    (folder / "w.sdf").write_text(SDF)
    with pytest.raises(InputError, match="wildcards"):
        _prepare(luci_home, "dbstep", LuciInputs(structures=str(folder)), tmp_path, env="dbstep")


def test_copied_inputs_never_overwrite_a_different_file(luci_home, tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "data.csv").write_text("x,y\n1,2\n")
    (tmp_path / "b" / "data.csv").write_text("mine\n")
    manager = fake_install(luci_home, "robert")
    spec = program("robert")
    with pytest.raises(InputError, match="already exists"):
        prepare(spec, spec.variant(), ["--csv_name", str(tmp_path / "a" / "data.csv")],
                str(tmp_path / "b"), manager, dry_run=True)
    assert (tmp_path / "b" / "data.csv").read_text() == "mine\n"
