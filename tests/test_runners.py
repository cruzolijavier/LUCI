"""Run each runner the way LUCI does (a separate Python, a JSON job) against fakes."""

import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

RUNNERS = Path(__file__).resolve().parents[1] / "src" / "luci" / "runners"


@pytest.mark.parametrize("script", sorted(RUNNERS.glob("*.py")), ids=lambda p: p.name)
def test_runners_parse_as_python38(script):
    # Auto-QChem's environment is Python 3.8; runners must stay compatible.
    ast.parse(script.read_text(), feature_version=(3, 8))


def _run(runner, kwargs, tmp_path, fake_modules=None, source_dir="", extra_path=None):
    fakes = tmp_path / "fakes"
    for relative, code in (fake_modules or {}).items():
        target = fakes / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(textwrap.dedent(code))
    out = tmp_path / "out"
    job = tmp_path / "job.json"
    job.write_text(json.dumps({"program": runner, "output_dir": str(out),
                               "source_dir": source_dir, "kwargs": kwargs}))
    env = dict(os.environ, PYTHONPATH=str(fakes))
    if extra_path:
        env["PATH"] = str(extra_path) + os.pathsep + env["PATH"]
    return subprocess.run([sys.executable, str(RUNNERS / f"{runner}.py"), str(job)],
                          capture_output=True, text=True, env=env), out


RECORDER = """
import json, os
def record(name, **kwargs):
    with open(os.environ.get("CALLS", "calls.jsonl"), "a") as handle:
        handle.write(json.dumps([name, {k: v for k, v in kwargs.items()}], default=str) + "\\n")
"""


def _calls(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def test_edboplus_create_and_run(tmp_path, monkeypatch):
    calls = tmp_path / "calls.jsonl"
    monkeypatch.setenv("CALLS", str(calls))
    fake = {
        "recorder.py": RECORDER,
        "edbo/__init__.py": "", "edbo/plus/__init__.py": "",
        "edbo/plus/optimizer_botorch.py": """
            from recorder import record
            class EDBOplus:
                @staticmethod
                def generate_reaction_scope(**kw): record("scope", **kw)
                def run(self, **kw): record("run", **kw)
        """,
    }
    result, out = _run("edboplus_runner", {"components": {"solvent": ["THF"]}}, tmp_path, fake)
    assert result.returncode == 0, result.stderr
    scope = tmp_path / "scope.csv"
    scope.write_text("a\n")
    result, _ = _run("edboplus_runner", {"filename": str(scope), "objectives": ["yield", "ee"],
                                         "objective_mode": "['MAX', 'min']", "batch": "3",
                                         "objective_thresholds": "[0.0, None]"}, tmp_path, fake)
    assert result.returncode == 0, result.stderr
    (name1, kw1), (name2, kw2) = _calls(calls)
    assert name1 == "scope" and kw1["check_overwrite"] is False and kw1["filename"] == "reaction.csv"
    assert name2 == "run" and kw2["objective_mode"] == ["max", "min"] and kw2["batch"] == 3
    assert kw2["directory"] == str(tmp_path) and kw2["objective_thresholds"] == [0.0, None]


def test_edboplus_validation(tmp_path):
    scope = tmp_path / "s.csv"
    scope.write_text("a\n")
    fake = {"edbo/__init__.py": "", "edbo/plus/__init__.py": "",
            "edbo/plus/optimizer_botorch.py": "class EDBOplus: pass"}
    result, _ = _run("edboplus_runner", {"filename": str(scope), "objectives": ["y"],
                                         "objective_mode": []}, tmp_path, fake)
    assert result.returncode == 1 and "objective_mode" in result.stderr


def test_scopebo_three_steps(tmp_path, monkeypatch):
    calls = tmp_path / "calls.jsonl"
    monkeypatch.setenv("CALLS", str(calls))
    source = tmp_path / "repo"
    (source / "Code").mkdir(parents=True)
    (source / "Code" / "__init__.py").write_text("")
    (source / "Code" / "predictor.py").write_text(textwrap.dedent("""
        from recorder import record
        class ScopeBO:
            @staticmethod
            def generate_features(smiles, **kw): record("features", smiles=smiles, **kw)
            @staticmethod
            def create_reaction_space(**kw): record("space", **kw)
            def run(self, **kw): record("run", **kw)
    """))
    fakes = {"recorder.py": RECORDER}
    smiles = tmp_path / "s.csv"
    smiles.write_text("smiles\nCI\nCCI\n")
    space = tmp_path / "space.csv"
    space.write_text("x\n")
    for kwargs in ({"smiles_csv": str(smiles), "common_core": "CI"},
                   {"reactants": {"r1.csv": "A"}, "objectives": "['yield']"},
                   {"filename": str(space), "batch": "2"}):
        result, out = _run("scopebo_runner", kwargs, tmp_path, fakes, source_dir=str(source))
        assert result.returncode == 0, result.stderr
    features, space_call, run = _calls(calls)
    assert features[1]["smiles"] == ["CI", "CCI"]
    assert list(space_call[1]["reactants"]) == [str(out / "r1.csv")]
    assert run[1]["batch"] == 2 and run[1]["show_suggestions"] is False


def test_autoqchem_parse(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "a.log").write_text("x")
    (logs / "b.log").write_text("x")
    fake = {"autoqchem/__init__.py": "",
            "autoqchem/gaussian_log_extractor.py": """
                class gaussian_log_extractor:
                    def __init__(self, path): self.path = path
                    def get_descriptors(self):
                        if self.path.endswith("b.log"): raise ValueError("broken")
                        return {"descriptors": {"homo": -0.2, "lumo": 0.1}, "atom_descriptors": object()}
            """}
    result, out = _run("autoqchem_runner", {"logs": str(logs / "*.log")}, tmp_path, fake)
    assert result.returncode == 0, result.stderr
    table = (out / "autoqchem_descriptors.csv").read_text().splitlines()
    assert table[0] == "file,homo,lumo" and table[1].startswith("a.log")
    assert "skipped b.log" in result.stdout


def test_autoqchem_submit_requires_key(tmp_path):
    fake = {"autoqchem/__init__.py": "", "autoqchem/molecule.py": "def molecule(*a, **k): pass",
            "autoqchem/sge_manager.py": "class sge_manager:\n    def __init__(self, **k): pass"}
    result, _ = _run("autoqchem_runner", {"action": "submit", "smiles": "C", "user": "u",
                                          "host": "h"}, tmp_path, fake)
    assert result.returncode == 1 and "SSH key" in result.stderr


@pytest.mark.skipif(os.name == "nt", reason="uses a shell script as fake executable")
def test_molsimplify_input_file(tmp_path):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    fake = bindir / "molsimplify"
    fake.write_text("#!/bin/sh\ncat \"$2\" > \"$(dirname \"$2\")/seen.inp\"\n")
    fake.chmod(0o755)
    result, out = _run("molsimplify_runner", {"metal": "Fe", "ligands": "water, cl", "counts": "[4, 2]",
                                              "oxstate": 2, "spin": 5}, tmp_path, extra_path=bindir)
    assert result.returncode == 0, result.stderr
    seen = (out / "LUCI-MolSimplify" / "seen.inp").read_text().splitlines()
    assert seen[:3] == ["-core fe", "-lig water,cl", "-ligocc 4,2"]
    assert "-oxstate 2" in seen and "-spin 5" in seen


def test_molsimplify_mismatched_counts(tmp_path):
    result, _ = _run("molsimplify_runner", {"metal": "fe", "ligands": "a,b", "counts": "1"}, tmp_path)
    assert result.returncode == 1 and "same length" in result.stderr


def test_autoqchem_action_follows_input(tmp_path):
    fake = {"autoqchem/__init__.py": "", "autoqchem/molecule.py": "def molecule(*a, **k): pass",
            "autoqchem/sge_manager.py": "class sge_manager:\n    def __init__(self, **k): pass"}
    # A SMILES input means "submit", even if the action field says something else.
    result, _ = _run("autoqchem_runner", {"smiles": "C", "action": "export"}, tmp_path, fake)
    assert result.returncode == 1 and "cluster user and host" in result.stderr


def test_edboplus_refuses_to_overwrite_a_campaign(tmp_path):
    fake = {"edbo/__init__.py": "", "edbo/plus/__init__.py": "",
            "edbo/plus/optimizer_botorch.py": "class EDBOplus:\n    @staticmethod\n    def generate_reaction_scope(**k): open(k['directory'] + '/' + k['filename'], 'w').write('x')"}
    out = tmp_path / "out"
    out.mkdir()
    (out / "reaction.csv").write_text("yield,priority\n80,-1\n")
    result, _ = _run("edboplus_runner", {"components": {"a": [1]}}, tmp_path, fake)
    assert result.returncode == 1 and "already exists" in result.stderr
    assert (out / "reaction.csv").read_text().startswith("yield")


def test_edboplus_objective_mode_validation(tmp_path):
    scope = tmp_path / "s.csv"
    scope.write_text("yield\n")
    fake = {"edbo/__init__.py": "", "edbo/plus/__init__.py": "",
            "edbo/plus/optimizer_botorch.py": "class EDBOplus:\n    def run(self, **k): pass"}
    result, _ = _run("edboplus_runner", {"filename": str(scope), "objectives": ["yield"],
                                         "objective_mode": ["highest"]}, tmp_path, fake)
    assert result.returncode == 1 and "max or min" in result.stderr
    result, _ = _run("edboplus_runner", {"filename": str(scope), "objectives": ["yield"],
                                         "objective_mode": ["Minimize"]}, tmp_path, fake)
    assert result.returncode == 0, result.stderr


def test_autoqchem_parse_with_nothing_parsed_fails(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "a.out").write_text("x")
    fake = {"autoqchem/__init__.py": "",
            "autoqchem/gaussian_log_extractor.py": "class gaussian_log_extractor:\n    def __init__(self, p): raise ValueError('bad')"}
    result, _ = _run("autoqchem_runner", {"logs": str(logs)}, tmp_path, fake)
    assert result.returncode == 1 and "none of the 1 file" in result.stderr


FAKE_RACERTS = """
import json, os, sys
def main():
    args = sys.argv[1:]
    out = args[args.index("-o") + 1]
    with open(os.path.join(os.path.dirname(out), "calls.jsonl"), "a") as handle:
        handle.write(json.dumps(args) + "\\n")
    if "fail" in args[1]:
        return 2
    with open(out, "w") as handle:
        handle.write("1\\nE=0\\nH 0 0 0\\n1\\nE=1\\nH 0 0 1\\n")
    return 0
"""

SDF = """mol
  LUCI

  2  1  0  0  0  0  0  0  0  0999 V2000
    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.0900    0.0000    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0
M  END
>  <Real charge>
1

>  <Mult>
2

$$$$
"""


def test_racerts_one_call_per_molecule(tmp_path):
    csv_file = tmp_path / "mols.csv"
    csv_file.write_text("smiles,code_name,charge\nCCO,ethanol,\nfail,bad,\nCC[O-],ethoxide,-1\n")
    fake = {"racerts/__init__.py": "", "racerts/cli.py": FAKE_RACERTS}
    result, out = _run("racerts_runner", {"molecules": str(csv_file), "n_conformers": 30}, tmp_path, fake)
    assert result.returncode == 0, result.stderr
    calls = [json.loads(line) for line in (out / "calls.jsonl").read_text().splitlines()]
    assert [c[0] for c in calls] == ["gs", "gs", "gs"]
    assert calls[0][1] == "CCO" and "--n-conformers" in calls[0] and "30" in calls[0]
    assert calls[2][calls[2].index("--charge") + 1] == "-1"
    assert (out / "ethanol_racerts.xyz").is_file() and not (out / "bad_racerts.xyz").exists()
    assert "2 of 3" in result.stdout and "bad" in result.stdout


def test_racerts_ts_needs_atoms_and_structures(tmp_path):
    folder = tmp_path / "st"
    folder.mkdir()
    (folder / "ts1.sdf").write_text(SDF + SDF)
    fake = {"racerts/__init__.py": "", "racerts/cli.py": FAKE_RACERTS}
    result, _ = _run("racerts_runner", {"structures": str(folder / "*.sdf"), "task": "ts"}, tmp_path, fake)
    assert result.returncode != 0 and "reacting atoms" in result.stderr
    result, out = _run("racerts_runner", {"structures": str(folder / "*.sdf"), "task": "ts",
                                          "reacting_atoms": "0 1"}, tmp_path, fake)
    assert result.returncode == 0, result.stderr
    call = json.loads((out / "calls.jsonl").read_text().splitlines()[0])
    assert call[1].endswith("ts1_first.sdf")  # several structures: the first one
    assert call[call.index("--reacting-atoms") + 1:call.index("--reacting-atoms") + 3] == ["0", "1"]
    assert call[call.index("--charge") + 1] == "1" and call[call.index("--multiplicity") + 1] == "2"
    csv_file = tmp_path / "m.csv"
    csv_file.write_text("smiles,code_name\nCCO,x\n")
    result, _ = _run("racerts_runner", {"molecules": str(csv_file), "task": "ts"}, tmp_path, fake)
    assert result.returncode != 0 and "3D structure" in result.stderr


FAKE_MORFEUS = """
class _D:
    def __init__(self, elements, coordinates, *args, **kwargs):
        self.n = len(elements)
        self.kwargs = kwargs
        self.L_value, self.B_1_value, self.B_5_value = 3.0, 1.5, 2.5
        self.L_value_uncorrected, self.bond_length = 2.6, 1.09
        self.area, self.volume = 10.0 * self.n, 5.0
        self.atom_areas = {i + 1: float(i) for i in range(self.n)}
Sterimol = SASA = _D
"""


def test_morfeus_table(tmp_path):
    folder = tmp_path / "st"
    folder.mkdir()
    (folder / "a.sdf").write_text(SDF + SDF)
    (folder / "b.sdf").write_text(SDF)
    fake = {"morfeus/__init__.py": FAKE_MORFEUS, "numpy/__init__.py": "def array(x, dtype=None):\n    return x\n"}
    result, out = _run("morfeus_runner", {"structures": str(folder / "*.sdf"),
                                          "descriptors": "[sterimol,sasa]", "atom_1": 1, "atom_2": 2},
                       tmp_path, fake)
    assert result.returncode == 0, result.stderr
    import csv
    rows = list(csv.DictReader((out / "morfeus_descriptors.csv").open()))
    assert [(r["code_name"], r["structure"]) for r in rows] == [("a", "1"), ("a", "2"), ("b", "1")]
    assert rows[0]["sterimol_B5"] == "2.5" and rows[0]["sasa_area"] == "20.0" and rows[0]["sasa_atom_area"] == "0.0"


def test_morfeus_sterimol_needs_atoms(tmp_path):
    folder = tmp_path / "st"
    folder.mkdir()
    (folder / "a.sdf").write_text(SDF)
    fake = {"morfeus/__init__.py": FAKE_MORFEUS, "numpy/__init__.py": "def array(x, dtype=None):\n    return x\n"}
    result, _ = _run("morfeus_runner", {"structures": str(folder / "*.sdf")}, tmp_path, fake)
    assert result.returncode != 0 and "Atom 1" in result.stdout
