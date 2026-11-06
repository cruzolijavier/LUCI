import sys

from luci.commands import (
    luci_command, luci_input_args, native_args, parse_advanced, preview_command, split_multi,
)
from luci.registry import FLAG_ONLY, layer, program


def _args(key, mode=None, value="", values=None, variant=None, advanced=""):
    spec = program(key)
    modes = {m.key: m for m in spec.input_modes}
    return native_args(spec, spec.variant(variant), input_mode=modes.get(mode),
                       input_value=value, values=values or {}, advanced=advanced)


def test_standard_inputs_are_luci_options_not_native_flags():
    # A typed SMILES travels as --molecule: LUCI checks it and adds --smi/--name itself.
    assert _args("aqme_csearch", "smiles", "CCO", {"program": "crest", "sample": "10"}) == [
        "--program", "crest", "--sample", "10"]
    modes = {m.key: m for m in program("aqme_csearch").input_modes}
    assert luci_input_args(modes["smiles"], " CCO ", "ethanol") == ["--molecule", "CCO", "--code-name", "ethanol"]
    assert luci_input_args(modes["smiles"], "CCO", "", skip_invalid=True) == ["--molecule", "CCO"]
    assert luci_input_args(modes["molecules"], "m.csv", skip_invalid=True) == [
        "--molecules", "m.csv", "--skip-invalid"]
    assert luci_input_args(modes["structures"], "/d") == ["--structures", "/d"]
    assert luci_input_args(modes["structures"], "  ") == []
    cmd = luci_command(layer("struct"), program("aqme_csearch"), ["--sample", "5"],
                       output_dir="/o", inputs=["--molecules", "m.csv"])
    assert cmd[3:] == ["struct", "--backend", "aqme_csearch", "--molecules", "m.csv",
                       "--output-dir", "/o", "--", "--sample", "5"]


def test_directory_input_gets_pattern(tmp_path):
    out = _args("goodvibes", "folder_log", str(tmp_path), {"q": True})
    assert out[0].endswith("*.log") and out[1:] == ["-q"]


def test_positional_input_and_switches():
    out = _args("dbstep", "pdb", "/data/prot.pdb", {"sterimol": True, "atom1": "2", "r": "4"})
    assert out == ["/data/prot.pdb", "--sterimol", "--atom1", "2", "-r", "4"]


def test_flag_only_choice():
    assert _args("goodvibes", "file", "a.log", {"boltz": FLAG_ONLY}) == ["a.log", "--boltz"]
    assert _args("goodvibes", "file", "a.log", {"boltz": "energy"}) == ["a.log", "--boltz", "energy"]


def test_value_is_flag_for_robert_steps():
    assert _args("robert", "csv_name", "t.csv", {"step": "curate"}) == ["--csv_name", "t.csv", "--curate"]


def test_multi_value_and_dash_flags():
    out = _args("ts_tools", "input_file", "r.txt", {"reactive_complex_factors_intra": "0, 1.2 1.3"})
    assert out == ["--input-file", "r.txt", "--reactive-complex-factors-intra", "0", "1.2", "1.3"]


def test_advanced_and_none_input():
    out = _args("edboplus", "new", "", {"components": "{'a': [1, 2]}"}, advanced='--seed 3')
    assert out == ["--components", "{'a': [1, 2]}", "--seed", "3"]


def test_luci_command_shape():
    cmd = luci_command(layer("react"), program("ts_tools"), ["--x"], variant="gxtb", output_dir="/o")
    assert cmd[:3] == [sys.executable, "-m", "luci"]
    assert cmd[3:] == ["react", "--backend", "ts_tools", "--variant", "gxtb", "--output-dir", "/o", "--", "--x"]
    single = luci_command(layer("feat"), program("dbstep"), [], variant="default")
    assert "--variant" not in single


def test_preview_quotes():
    text = preview_command([sys.executable, "-m", "luci", "feat", "--", "--smi", "C C", "a>>b"])
    assert text == 'luci feat -- --smi "C C" "a>>b"'


def test_helpers():
    assert split_multi("0, 1.2  1.3") == ["0", "1.2", "1.3"]
    assert parse_advanced('--crest_keywords "--nci --alpb h2o" --x') == ["--crest_keywords", "--nci --alpb h2o", "--x"]


def test_advanced_box_never_fails():
    assert parse_advanced('--name="a b" --csv "my res.csv') == ["--name=a b", "--csv", "my res.csv"]
    assert parse_advanced(r"--files C:\Data\x.sdf") == ["--files", r"C:\Data\x.sdf"]
