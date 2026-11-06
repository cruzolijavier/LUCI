from luci.cli import parse, run


def test_new_syntax():
    p = parse(["feat", "--backend", "dbstep", "--output-dir", "o", "--", "a.xyz", "--sterimol"])
    assert (p["layer"], p["backend"], p["output_dir"], p["native"]) == ("feat", "dbstep", "o", ["a.xyz", "--sterimol"])


def test_native_starts_at_first_unknown_option():
    assert parse(["feat", "-b", "dbstep", "a.xyz", "--vbur"])["native"] == ["a.xyz", "--vbur"]


def test_legacy_flags():
    p = parse(["--conf", "--aqme", "--files", "*.sdf"])
    assert p["backend"] == "aqme_csearch" and p["native"] == ["--files", "*.sdf"]
    assert parse(["gopt", "--files", "x.sdf"])["backend"] == "aqme_cmin"
    assert parse(["feat", "--files", "x.sdf"])["backend"] == "aqme_qdescp"
    assert parse(["conf", "--molsimplify", "--metal", "fe"])["backend"] == "molsimplify"
    robert = parse(["--pred", "--robert", "--csv_name", "t.csv"])
    assert robert["backend"] == "robert" and robert["native"][0] == "--predict"


def test_help_does_not_run(capsys):
    assert run(["struct", "--help"]) == 0
    assert "aqme_csearch" in capsys.readouterr().out
    assert run(["feat", "--help"]) == 0


def test_programs_listing(capsys):
    assert run(["programs", "--have", "reaction"]) == 0
    out = capsys.readouterr().out
    assert "ts_tools" in out and "goodvibes" not in out


def test_layer_mismatch_and_unknown(capsys):
    assert run(["thermo", "--backend", "dbstep"]) == 2
    assert run(["nolayer"]) == 2
    assert run(["feat", "--backend", "nothing"]) == 2


def test_not_installed_is_a_clear_error(luci_home, capsys):
    assert run(["feat", "--backend", "dbstep", "--", "a.xyz"]) == 1
    assert "luci env install dbstep" in capsys.readouterr().err


def test_env_list(luci_home, capsys):
    assert run(["env", "list"]) == 0
    out = capsys.readouterr().out
    assert "dbstep" in out and "not available yet" in out


def test_unavailable_env_refuses_install(luci_home, capsys):
    assert run(["env", "install", "boreact"]) == 1
    assert "not available" in capsys.readouterr().err


def test_legacy_dry_run_and_destination_anywhere(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    p = parse(["conf", "--molsimplify", "--metal", "fe", "--dry-run"])
    assert p["dry_run"] and p["native"] == ["--metal", "fe"]
    p = parse(["--conf", "--aqme", "--input", "a.csv", "--destination", "res", "--program", "rdkit"])
    assert p["output_dir"] == str(tmp_path / "res")
    assert p["native"] == ["--input", "a.csv", "--program", "rdkit"]


def test_program_flags_named_like_legacy_ones_survive():
    p = parse(["pred", "--backend", "robert", "--aqme", "--csv_name", "x.csv"])
    assert p["backend"] == "robert" and p["native"] == ["--aqme", "--csv_name", "x.csv"]
    assert p["legacy"] is None


def test_legacy_default_is_announced(capsys, luci_home):
    run(["feat", "--files", "x.sdf"])
    assert "No --backend given: using aqme_qdescp" in capsys.readouterr().err


def test_programs_bad_arguments(capsys):
    assert run(["programs", "--layer", "nope"]) == 2
    assert run(["programs", "--have", "nonsense"]) == 2
    assert run(["programs", "--have", "SMILES"]) == 0


def test_legacy_multiple_files_become_one_value():
    p = parse(["--conf", "--aqme", "--files", "a.sdf", "b.sdf", "--program", "rdkit"])
    assert p["native"] == ["--files", "[a.sdf,b.sdf]", "--program", "rdkit"]


def test_env_uninstall_command(luci_home, capsys):
    from conftest import fake_install
    from luci.envs.manager import EnvManager
    fake_install(luci_home, "dbstep")
    assert run(["env", "uninstall", "dbstep"]) == 0
    assert not EnvManager(luci_home).is_installed("dbstep")
