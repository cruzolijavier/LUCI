"""LUCI-DESIGN with real inputs: EDBO+ and ScopeBO, two rounds of the lab loop each."""

import csv
from pathlib import Path

import pytest

from program_helpers import (  # noqa: F401 (luci and work are fixtures)
    luci, luci_data, read_csv, require_env, work,
)

pytestmark = pytest.mark.programs


def _write(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _measure(row: dict) -> str:
    """A made-up but smooth 'experiment': hotter, more base and DMSO give more yield."""
    value = 0.8 * float(row["temperature"]) + 10 * float(row["base_equiv"])
    return str(round(value + (15 if row["solvent"] == "DMSO" else 0), 1))


def test_edboplus_campaign(work, luci):
    require_env("edboplus")
    # Round 0: build the scope (3 solvents x 3 temperatures x 2 base loadings).
    luci(work, "design", "--backend", "edboplus", "--output-dir", ".", "--", "--components",
         "{'solvent': ['THF', 'DMSO', 'MeCN'], 'temperature': [30, 50, 70], 'base_equiv': [1.0, 2.0]}").ok()
    folder = work / "LUCI_DESIGN" / "EDBOplus"
    scope = folder / "reaction.csv"
    rows = read_csv(scope)
    assert len(rows) == 18 and set(rows[0]) == {"solvent", "temperature", "base_equiv"}

    # Round 1: no data yet, EDBO+ picks a diverse first batch.
    suggest = ["design", "--backend", "edboplus", "--", "--filename", "LUCI_DESIGN/EDBOplus/reaction.csv",
               "--objectives", "['yield']", "--objective_mode", "['max']", "--batch", "3", "--seed", "1"]
    luci(work, *suggest).ok()
    rows = read_csv(scope)
    first = [r for r in rows if float(r["priority"]) == 1]
    assert len(first) == 3 and all(r["yield"] == "PENDING" for r in rows)

    # The chemist measures them; round 2 trains the model and suggests new experiments.
    for row in first:
        row["yield"] = _measure(row)
    _write(scope, rows)
    luci(work, *suggest).ok()
    rows = read_csv(scope)
    measured = [r for r in rows if r["yield"] != "PENDING"]
    second = [r for r in rows if float(r["priority"]) == 1]
    assert len(measured) == 3 and len(second) == 3
    assert all(r["yield"] == "PENDING" for r in second), "EDBO+ suggested an experiment already done"
    assert (folder / "pred_reaction.csv").is_file()
    # Three runs, one folder, three blocks in LUCI_data.dat.
    assert luci_data(work / "LUCI_DESIGN").count("  EDBO+\n") == 3


def test_scopebo_featurize_build_and_suggest(work, luci):
    require_env("scopebo")
    # 1. GFN2-xTB / Morfeus descriptors for each starting material.
    for csv_name, out in (("scopebo_alkyl_iodides.csv", "alkyl.csv"), ("scopebo_phosphines.csv", "phos.csv")):
        luci(work, "design", "--backend", "scopebo", "--molecules", csv_name,
             "--", "--features_name", out).ok()
    folder = work / "LUCI_DESIGN" / "ScopeBO"
    alkyl = read_csv(folder / "alkyl.csv")
    assert len(alkyl) == 4 and "HOMO" in alkyl[0] and "SASA" in alkyl[0]
    sasa = {row[""]: float(row["SASA"]) for row in alkyl}
    assert sasa["CI"] < sasa["CCI"] < sasa["CC(C)I"]

    # 2. Reaction space: every iodide with every phosphine (relative paths from where LUCI runs).
    luci(work, "design", "--backend", "scopebo", "--output-dir", ".", "--", "--reactants",
         "{'LUCI_DESIGN/ScopeBO/alkyl.csv': 'AlkI', 'LUCI_DESIGN/ScopeBO/phos.csv': 'Phos'}").ok()
    space = folder / "reaction_space.csv"
    rows = read_csv(space)
    assert len(rows) == 12

    # 3. Three results measured, ScopeBO suggests the next two substrates.
    with open(space, newline="", encoding="utf-8") as handle:
        table = list(csv.reader(handle))
    header = table[0]
    for line in table[1:4]:
        line[header.index("yield")] = str(40 + len(line[0]))
    with open(space, "w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(table)
    luci(work, "design", "--backend", "scopebo", "--", "--filename", "LUCI_DESIGN/ScopeBO/reaction_space.csv",
         "--objectives", "['yield']", "--batch", "2", "--seed", "1").ok()
    rows = read_csv(space)
    suggested = [r for r in rows if float(r["priority"]) == 1]
    assert len(suggested) == 2 and all(r["yield"] == "PENDING" for r in suggested)
