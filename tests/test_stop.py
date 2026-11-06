"""The Stop buttons, driven like a user, with real child processes."""

import os
from pathlib import Path
import sys
import time

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QtWidgets = pytest.importorskip("PySide6.QtWidgets")

SRC = Path(__file__).resolve().parents[1] / "src"
pytestmark = pytest.mark.skipif(os.name == "nt", reason="uses POSIX process checks")


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def errors(monkeypatch):
    """Exceptions raised inside Qt slots end up here instead of passing silently."""
    seen = []
    monkeypatch.setattr(sys, "excepthook", lambda *exc: seen.append(exc))
    return seen


def _long_job(tmp_path):
    """A 'LUCI CLI' that starts a long program through luci.proc, like a real run."""
    marker = tmp_path / "child.pid"
    child = tmp_path / "child.py"
    child.write_text(f"import os, time\nopen({str(marker)!r}, 'w').write(str(os.getpid()))\n"
                     "print('working', flush=True)\ntime.sleep(120)\n")
    cli = tmp_path / "cli.py"
    cli.write_text(f"import sys\nsys.path.insert(0, {str(SRC)!r})\n"
                   "from luci.proc import run_forwarding_signals\n"
                   f"sys.exit(run_forwarding_signals([sys.executable, {str(child)!r}]))\n")
    return [sys.executable, str(cli)], marker


def _wait(app, condition, seconds=15):
    end = time.time() + seconds
    while time.time() < end:
        app.processEvents()
        if condition():
            return True
        time.sleep(0.05)
    return False


def _alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    # A zombie still answers kill(0); check its state.
    try:
        return Path(f"/proc/{pid}/stat").read_text().split()[2] != "Z"
    except OSError:
        return False


def test_install_dialog_stop(app, tmp_path, errors):
    from luci.gui.dialogs import ProcessDialog
    argv, marker = _long_job(tmp_path)
    dialog = ProcessDialog("Installing test", argv)
    dialog.show()
    assert _wait(app, lambda: marker.exists() and marker.read_text())
    child = int(marker.read_text())
    started = time.time()
    dialog.stop_button.click()
    assert time.time() - started < 1.0, "Stop must not freeze the window"
    dialog.stop_button.click()  # a second click is harmless
    assert _wait(app, lambda: dialog.exit_code is not None)
    assert _wait(app, lambda: not _alive(child), 5), "the program kept running"
    assert "Stopped" in dialog.state.text()
    assert dialog.close_button.isEnabled()
    dialog.close_button.click()
    assert errors == []


def test_program_page_stop(app, tmp_path, errors, luci_home):
    from conftest import fake_install
    from luci.gui.app import MainWindow
    fake_install(luci_home, "dbstep")
    window = MainWindow()
    window.show()
    workspace = window.workspaces["feat"]
    workspace.select_package("dbstep")
    page = workspace.pages["dbstep"]
    argv, marker = _long_job(tmp_path)
    page.command = lambda: argv
    page.form.missing_required = lambda: []
    page.run_button.click()
    assert _wait(app, lambda: marker.exists() and marker.read_text())
    child = int(marker.read_text())
    assert not page.run_button.isEnabled() and page.stop_button.isEnabled()
    started = time.time()
    page.stop_button.click()
    assert time.time() - started < 1.0
    assert _wait(app, lambda: not page.is_running())
    assert _wait(app, lambda: not _alive(child), 5)
    assert "Stopped by the user" in page.console.toPlainText()
    assert page.run_button.isEnabled() and not page.stop_button.isEnabled()
    page.stop()  # stopping again when nothing runs does nothing
    # It can run again after a stop.
    marker.unlink()
    page.run_button.click()
    assert _wait(app, lambda: marker.exists() and marker.read_text())
    page.stop_button.click()
    assert _wait(app, lambda: not page.is_running())
    window.close()
    assert errors == []


def test_closing_luci_stops_running_programs(app, tmp_path, errors, luci_home, monkeypatch):
    from conftest import fake_install
    from luci.gui.app import MainWindow
    fake_install(luci_home, "dbstep")
    window = MainWindow()
    window.show()
    page = window.workspaces["feat"].pages["dbstep"]
    window.workspaces["feat"].select_package("dbstep")
    argv, marker = _long_job(tmp_path)
    page.command = lambda: argv
    page.form.missing_required = lambda: []
    page.run_button.click()
    assert _wait(app, lambda: marker.exists() and marker.read_text())
    child = int(marker.read_text())
    monkeypatch.setattr(QtWidgets.QMessageBox, "question", lambda *a, **k: QtWidgets.QMessageBox.Yes)
    window.close()
    assert _wait(app, lambda: not _alive(child), 10)
    assert errors == []


def test_windows_stop_path_does_not_block(app, tmp_path, errors, monkeypatch):
    """On Windows Stop launches taskkill without waiting for it."""
    from luci.gui import dialogs
    argv, marker = _long_job(tmp_path)
    dialog = dialogs.ProcessDialog("Installing test", argv)
    assert _wait(app, lambda: marker.exists() and marker.read_text())
    calls = []

    class FakePopen:
        def __init__(self, cmd, **kwargs):
            calls.append(cmd)
            dialog.process.kill()  # what taskkill would do

    monkeypatch.setattr(dialogs, "current_platform", lambda: "windows")
    monkeypatch.setattr(dialogs.subprocess, "Popen", FakePopen)
    started = time.time()
    dialog.stop()
    assert time.time() - started < 1.0
    assert calls and calls[0][:2] == ["taskkill", "/PID"] and calls[0][-2:] == ["/T", "/F"]
    assert _wait(app, lambda: dialog.exit_code is not None)
    os.kill(int(marker.read_text()), 9)
    assert errors == []
