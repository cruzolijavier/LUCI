import json
import os
from pathlib import Path

import pytest

from conftest import fake_install
from luci.envs.manager import EnvError, EnvManager
from luci.execution import absolutize, parse_runner_kwargs, prepare, run_program
from luci.registry import program
from luci.settings import Settings


def test_prepare_cli_program(luci_home, tmp_path):
    manager = fake_install(luci_home, "dbstep")
    spec = program("dbstep")
    argv, outdir, run_dir, env, job, *_ = prepare(spec, spec.variant(), ["a.xyz", "--sterimol"],
                                                 str(tmp_path / "out"), manager, cwd=tmp_path)
    assert argv[1:7] == ["run", "--manifest-path", str(manager.manifest("dbstep")), "--frozen",
                         "--no-install", "--executable"]
    assert argv[7:] == ["dbstep", "a.xyz", "--sterimol"]
    assert run_dir == outdir == (tmp_path / "out").resolve()
    assert job is None


def test_default_args_and_placeholders(luci_home, tmp_path):
    manager = fake_install(luci_home, "thermognn")
    spec = program("thermognn")
    argv, outdir, *_ = prepare(spec, spec.variant(), ["--input", "m.csv"], str(tmp_path), manager)
    tail = argv[argv.index("--executable") + 1:]
    src = str(manager.source_dir("thermognn"))
    assert tail[:2] == ["python", f"{src}/predict.py"]
    assert tail[tail.index("--checkpoint") + 1] == f"{src}/ckpt/iter6"
    assert tail[tail.index("--output") + 1] == f"{outdir}/thermognn_predictions.csv"
    # A user choice wins over the default.
    argv, *_ = prepare(spec, spec.variant(), ["--checkpoint", "/my/ckpt"], str(tmp_path), manager)
    assert argv.count("--checkpoint") == 1


def test_aqme_runs_from_output_folder_with_relative_inputs(luci_home, tmp_path):
    manager = fake_install(luci_home, "aqme")
    data = tmp_path / "data"
    data.mkdir()
    spec = program("aqme_qdescp")
    argv, outdir, run_dir, *_ = prepare(spec, spec.variant(), ["--files", str(data / "*.sdf")],
                                        str(tmp_path / "res"), manager)
    assert run_dir == outdir == (tmp_path / "res").resolve()
    assert argv[argv.index("--files") + 1] == "../data/*.sdf"
    assert argv[argv.index("--destination") + 1] == str(outdir)


def test_aqme_never_writes_over_its_input(luci_home, tmp_path):
    manager = fake_install(luci_home, "aqme")
    sdf = tmp_path / "mol.sdf"
    sdf.write_text("")
    spec = program("aqme_cmin")
    # Output folder = the input's own folder (the GUI default): results go to CMIN/.
    argv, outdir, run_dir, *_ = prepare(spec, spec.variant(), ["--files", str(sdf), "--program", "xtb"],
                                        str(tmp_path), manager)
    assert outdir == tmp_path.resolve() / "CMIN"
    assert argv[argv.index("--files") + 1] == "../mol.sdf"


def test_aqme_list_and_equals_forms(luci_home, tmp_path):
    manager = fake_install(luci_home, "aqme")
    (tmp_path / "in").mkdir()
    spec = program("aqme_cmin")
    native = ["--files", f"[{tmp_path}/in/a.sdf,{tmp_path}/in/b.sdf]"]
    argv, *_ = prepare(spec, spec.variant(), native, str(tmp_path / "out"), manager)
    assert argv[argv.index("--files") + 1] == "[../in/a.sdf,../in/b.sdf]"
    argv, *_ = prepare(spec, spec.variant(), [f"--files={tmp_path}/in/a.sdf"], str(tmp_path / "out"), manager)
    assert "--files=../in/a.sdf" in argv


def test_robert_inputs_copied_to_output(luci_home, tmp_path):
    manager = fake_install(luci_home, "robert")
    folder = tmp_path / "my data"
    folder.mkdir()
    (folder / "train.csv").write_text("a,b\n")
    spec = program("robert")
    argv, outdir, *_ = prepare(spec, spec.variant(), ["--csv_name", str(folder / "train.csv")],
                               str(tmp_path / "out"), manager)
    assert argv[argv.index("--csv_name") + 1] == "train.csv"
    assert (outdir / "train.csv").is_file()


def test_user_equals_flag_beats_default_args(luci_home, tmp_path):
    manager = fake_install(luci_home, "thermognn")
    spec = program("thermognn")
    argv, *_ = prepare(spec, spec.variant(), ["--output=/x/p.csv"], str(tmp_path), manager)
    assert not any(t == "--output" for t in argv)


def test_positionals_after_switches_are_made_absolute(tmp_path):
    from luci.execution import value_flags_of
    (tmp_path / "a.xyz").write_text("")
    (tmp_path / "out.csv").write_text("")
    spec = program("dbstep")
    out = absolutize(["--sterimol", "a.xyz", "--csv", "out.csv", "--atom1", "2"], tmp_path,
                     {"--csv_dummy"}, value_flags_of(spec, spec.variant()))
    assert out[1] == str((tmp_path / "a.xyz").resolve())
    assert out[3] == "out.csv" and out[5] == "2"


def test_runner_job(luci_home, tmp_path):
    manager = fake_install(luci_home, "edboplus")
    spec = program("edboplus")
    argv, outdir, run_dir, env, job, job_file, _ = prepare(
        spec, spec.variant(), ["--filename", "scope.csv", "--objectives", "['yield']", "--batch", "4"],
        str(tmp_path), manager, cwd=tmp_path)
    assert argv[-2].endswith("edboplus_runner.py") and argv[-1] == str(job_file)
    assert job["kwargs"] == {"filename": "scope.csv", "objectives": ["yield"], "batch": 4}


def test_env_vars_and_path(luci_home, tmp_path, monkeypatch):
    settings = Settings(gaussian_dir="/opt/g16")
    settings.save()
    manager = fake_install(luci_home, "tstools")
    manager.settings = settings
    monkeypatch.setattr("luci.envs.manager.current_platform", lambda: "linux")
    monkeypatch.setattr("luci.envs.manager.EnvManager.supported", lambda self, spec: True)
    spec = program("ts_tools")
    _, _, _, env, *_ = prepare(spec, spec.variant("xtb"), [], str(tmp_path), manager)
    assert env["PATH"].startswith("/opt/g16" + os.pathsep)
    assert env["XTB_PATH"].endswith("/bin/xtb")


def test_unavailable_variant_is_refused(luci_home, tmp_path):
    manager = EnvManager(luci_home)
    spec = program("ts_tools")
    with pytest.raises(EnvError, match="not available"):
        prepare(spec, spec.variant("mlip"), [], str(tmp_path), manager)


def test_dry_run_prints_command(luci_home, tmp_path, capsys):
    manager = fake_install(luci_home, "goodvibes")
    spec = program("goodvibes")
    assert run_program(spec, spec.variant(), ["x.log"], output_dir=str(tmp_path), dry_run=True,
                       manager=manager) == 0
    assert "python -m goodvibes x.log" in capsys.readouterr().out


def test_absolutize_only_touches_files(tmp_path):
    (tmp_path / "a.xyz").write_text("")
    (tmp_path / "steric.csv").write_text("")
    (tmp_path / "sub").mkdir()
    flags = {"--files", "--csv_test"}
    values = {"--constraints_dist", "--csv", "--smiles"}
    out = absolutize(["a.xyz", "sub/*.log", "--files", "sub/*.sdf", "--constraints_dist",
                      "[[1,2,1.8]]", "--csv", "steric.csv", "--smiles", "[Na+].[Cl-]",
                      "--csv_test=a.xyz", "/abs/b.xyz"], tmp_path, flags, values)
    assert out[0] == str((tmp_path / "a.xyz").resolve())
    assert out[1] == str((tmp_path / "sub").resolve() / "*.log")
    assert out[3] == str((tmp_path / "sub").resolve() / "*.sdf")
    # Values that are not inputs stay exactly as typed, even if a file has that name.
    assert out[4:10] == ["--constraints_dist", "[[1,2,1.8]]", "--csv", "steric.csv",
                         "--smiles", "[Na+].[Cl-]"]
    assert out[10] == f"--csv_test={(tmp_path / 'a.xyz').resolve()}"
    assert out[11] == "/abs/b.xyz"


def test_aqme_logs_move_to_output(luci_home, tmp_path, monkeypatch):
    from luci.execution import _collect_logs, _snapshot
    run_dir, out = tmp_path / "in", tmp_path / "out"
    run_dir.mkdir(); out.mkdir()
    (run_dir / "OLD_data.dat").write_text("old")
    before = _snapshot(run_dir)
    (run_dir / "CSEARCH_data.dat").write_text("new")
    (run_dir / "AQME_run.csv").write_text("new")
    _collect_logs(run_dir, out, before)
    assert sorted(p.name for p in out.iterdir()) == ["AQME_run.csv", "CSEARCH_data.dat"]
    assert (run_dir / "OLD_data.dat").exists()


def test_dry_run_works_before_install(luci_home, tmp_path, capsys):
    spec = program("dbstep")
    assert run_program(spec, spec.variant(), ["x.xyz"], output_dir=str(tmp_path), dry_run=True,
                       manager=EnvManager(luci_home)) == 0
    assert "dbstep x.xyz" in capsys.readouterr().out


def test_runner_kwargs():
    assert parse_runner_kwargs(["--a", "1", "--b", "[1, 2]", "--c", "--d=x y", "--e-f", "{'k': 1}"]) == {
        "a": 1, "b": [1, 2], "c": True, "d": "x y", "e_f": {"k": 1}}
    with pytest.raises(ValueError):
        parse_runner_kwargs(["positional"])


def test_manager_outdated_detection(luci_home):
    manager = fake_install(luci_home, "dbstep")
    assert manager.is_installed("dbstep") and not manager.is_outdated("dbstep")
    marker = manager.workspace("dbstep") / ".luci-installed.json"
    marker.write_text(json.dumps({"manifest": "old"}))
    assert manager.is_outdated("dbstep")
    manager.remove("dbstep")
    assert not manager.is_installed("dbstep")


def test_failed_update_restores_previous_manifest(luci_home, tmp_path, monkeypatch):
    manager = fake_install(luci_home, "dbstep")
    manifest = manager.manifest("dbstep")
    manifest.write_text("# previous working manifest\n")
    (manager.workspace("dbstep") / "pixi.lock").write_text("old lock")
    failing = tmp_path / "failpixi"
    failing.write_text("#!/bin/sh\nexit 1\n")
    failing.chmod(0o755)
    monkeypatch.setenv("LUCI_PIXI", str(failing))
    with pytest.raises(EnvError):
        EnvManager(luci_home).install("dbstep")
    assert manifest.read_text() == "# previous working manifest\n"
    assert (manager.workspace("dbstep") / "pixi.lock").read_text() == "old lock"
    # The fake previous install cannot be restored by the failing pixi: not trusted.
    assert not EnvManager(luci_home).is_installed("dbstep")


def test_restricted_network_is_not_an_update(luci_home):
    manager = fake_install(luci_home, "dbstep")
    manager.settings.restricted_network = True
    assert not manager.is_outdated("dbstep")


def test_typed_smiles_are_never_paths(luci_home, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    manager = fake_install(luci_home, "autoqchem")
    spec = program("autoqchem")
    argv, *_ = prepare(spec, spec.variant(), ["--smiles", "[Na+].[Cl-]"], str(tmp_path), manager)
    assert argv[-1].endswith(".json")
    from luci.execution import path_flags
    assert "--smiles" not in path_flags(spec, spec.variant())
    assert "--logs" in path_flags(spec, spec.variant())


@pytest.mark.skipif(os.name == "nt", reason="POSIX signal forwarding")
def test_terminating_luci_stops_the_program(tmp_path):
    import signal, subprocess, sys, time
    marker = tmp_path / "child.pid"
    child = tmp_path / "child.py"
    child.write_text(f"import os, time\nopen({str(marker)!r}, 'w').write(str(os.getpid()))\ntime.sleep(60)\n")
    parent = tmp_path / "parent.py"
    parent.write_text(
        f"import sys\nsys.path.insert(0, {str(Path(__file__).resolve().parents[1] / 'src')!r})\n"
        f"from luci.proc import run_forwarding_signals\n"
        f"run_forwarding_signals([sys.executable, {str(child)!r}])\n")
    process = subprocess.Popen([sys.executable, str(parent)])
    for _ in range(200):
        if marker.exists() and marker.read_text():
            break
        time.sleep(0.05)
    child_pid = int(marker.read_text())
    process.send_signal(signal.SIGTERM)
    process.wait(timeout=10)
    time.sleep(0.3)
    with pytest.raises(ProcessLookupError):
        os.kill(child_pid, 0)


def test_download_size_and_monitor(tmp_path, capsys):
    import time
    from luci.envs.manager import DownloadMonitor, download_size, MANIFESTS
    assert download_size(MANIFESTS / "thermognn" / "pixi.lock") > 100e6
    prefix = tmp_path / "prefix"
    prefix.mkdir()
    (prefix / "f").write_bytes(b"x" * 2048)
    monitor = DownloadMonitor(Path("/nonexistent/pixi"), prefix, interval=0.05)
    monitor.start()
    time.sleep(0.3)
    monitor.stop()
    out = capsys.readouterr().out
    assert "Still working (" in out and "environment folder 2 KB" in out
