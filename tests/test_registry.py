import tomllib

import pytest

from luci.envs.manager import MANIFESTS
from luci.registry import (
    ENVIRONMENTS, LAYERS, PROGRAMS, layer, matches_inputs, program, program_platforms, programs_in,
    validate,
)

CONDA_PLATFORM = {"win-64": "windows", "linux-64": "linux", "osx-64": "macos", "osx-arm64": "macos"}


def test_registry_is_consistent():
    assert validate() == []


def test_six_layers_named_after_results():
    assert [l.key for l in LAYERS] == ["struct", "thermo", "react", "feat", "pred", "design"]
    for spec in LAYERS:
        assert programs_in(spec.key), spec.key


def test_every_program_in_exactly_one_layer():
    keys = [p.key for p in PROGRAMS]
    assert len(keys) == len(set(keys))
    assert {p.layer for p in PROGRAMS} == {l.key for l in LAYERS}


@pytest.mark.parametrize("name,expected", [
    ("conf", "struct"), ("gopt", "struct"), ("c", "struct"), ("go", "struct"),
    ("feat", "feat"), ("f", "feat"), ("pred", "pred"), ("LUCI-THERMO", "thermo"),
])
def test_legacy_layer_names(name, expected):
    assert layer(name).key == expected


def test_legacy_program_names():
    assert program("molsimp").key == "molsimplify"
    assert program("cmin").key == "aqme_cmin"
    assert program("ts-tools").key == "ts_tools"


def test_thermognn_and_ts_tools_placement():
    assert program("thermognn").layer == "thermo"
    ts = program("ts_tools")
    assert ts.layer == "react"
    assert [v.key for v in ts.variants] == ["xtb", "gxtb", "mlip"]


@pytest.mark.parametrize("env", [e for e in ENVIRONMENTS if e.available], ids=lambda e: e.key)
def test_manifest_matches_environment(env):
    path = MANIFESTS / env.key / "pixi.toml"
    assert path.is_file(), f"missing manifest for {env.key}"
    data = tomllib.loads(path.read_text())
    platforms = {CONDA_PLATFORM[p] for p in data["workspace"]["platforms"]}
    assert set(env.platforms) <= platforms, f"{env.key}: registry promises {env.platforms}"
    assert ("postinstall" in data.get("tasks", {})) == env.postinstall
    if env.source is None:
        assert "src" not in data.get("tasks", {}).get("postinstall", "")


def test_filter_by_inputs():
    smiles = {p.key for p in PROGRAMS if matches_inputs(p, {"smiles"})}
    assert {"aqme_csearch", "thermognn", "molsimplify"} <= smiles
    assert "goodvibes" not in smiles
    assert {p.key for p in PROGRAMS if matches_inputs(p, {"reaction"})} == {"ts_tools", "molsimplify"}


def test_linux_only_programs():
    for key in ("thermomlip", "ts_tools"):
        assert program_platforms(program(key)) == ("linux",)
    assert "windows" in program_platforms(program("dbstep"))
