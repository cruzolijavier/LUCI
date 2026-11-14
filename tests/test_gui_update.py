"""Update button and the grey assistant robot (offscreen)."""

import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from luci import updater


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app, tmp_path, monkeypatch):
    monkeypatch.setenv("LUCI_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("LUCI_UPDATER", "1")
    for name in ("LUCI_OPENAI_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    from luci.assistant import config
    monkeypatch.setattr(config, "key_files", lambda: [tmp_path / "none.txt"])
    # Never ask the real GitHub from a test: the automatic check after 4 s used to start a
    # real download thread that outlived the window (and crashed a later test on CircleCI).
    from luci.gui import updater_ui
    monkeypatch.setattr(updater_ui, "FIRST_CHECK_MS", 10 ** 9)
    monkeypatch.setattr(updater, "check", lambda *a, **k: None)
    from luci.gui.app import MainWindow
    win = MainWindow()
    win.resize(1100, 800)
    win.show()
    app.processEvents()
    yield win
    finder = win.update_button._finder if win.update_button is not None else None
    if finder is not None:
        finder.wait(5000)
    win.close()


def test_robot_grey_without_key_and_on_with_key(window, monkeypatch, app):
    view = window._assistant
    assert not view.available and not view.robot.available
    assert not view.switch.isVisibleTo(window)
    assert "Settings" in view.robot.toolTip()
    monkeypatch.setenv("LUCI_OPENAI_API_KEY", "sk-test")
    view.refresh_availability()
    assert view.available and view.robot.available and view.switch.isVisibleTo(window)
    monkeypatch.delenv("LUCI_OPENAI_API_KEY")
    view.refresh_availability()
    assert not view.available


def test_robot_pixels_differ_when_grey(window, monkeypatch):
    view = window._assistant
    grey = view.robot.grab().toImage()
    monkeypatch.setenv("LUCI_OPENAI_API_KEY", "sk-test")
    view.refresh_availability()
    colour = view.robot.grab().toImage()
    assert grey != colour


def test_update_button_badge(window, app, monkeypatch):
    button = window.update_button
    assert button is not None and not button.badge.isVisibleTo(button)
    new = updater.Update("9.0.0", "0" * 64, 5_000_000, "News", "http://x/y.zip")
    monkeypatch.setattr(updater, "check", lambda *a, **k: new)
    shown = []
    monkeypatch.setattr(type(button), "_ask_install", lambda self, announce=False: shown.append(announce))
    button.check(silent=True)
    button._finder.wait(5000)
    app.processEvents()
    assert button.pending is new and button.badge.isVisibleTo(button)
    assert shown == [True]
    button.check(silent=True)           # same version again: no second pop-up
    button._finder.wait(5000)
    app.processEvents()
    assert shown == [True]
    # the "!" does not cover the text
    text_width = button.fontMetrics().horizontalAdvance(button.text())
    assert button.badge.x() >= 10 + text_width - 2
    window.menuBar().grab().save(os.path.join(os.environ.get("SHOT_DIR", "/tmp"), "menu_badge.png"))


def test_up_to_date_and_error(window, app, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    button = window.update_button
    texts = []
    monkeypatch.setattr(QMessageBox, "information", lambda *a: texts.append(a[2]))
    monkeypatch.setattr(QMessageBox, "warning", lambda *a: texts.append(a[2]))
    monkeypatch.setattr(updater, "check", lambda *a, **k: None)
    button.check(silent=False)
    button._finder.wait(5000)
    app.processEvents()
    assert "up to date" in texts[-1]

    def boom(*a, **k):
        raise updater.UpdateError("Could not reach GitHub.")
    monkeypatch.setattr(updater, "check", boom)
    button.check(silent=False)
    button._finder.wait(5000)
    app.processEvents()
    assert "GitHub" in texts[-1]


def test_closing_during_a_check_never_kills_the_thread(window, app, monkeypatch):
    """A check still running when LUCI closes is left to finish, never terminate()d."""
    import threading
    from luci.gui import updater_ui
    release = threading.Event()
    monkeypatch.setattr(updater, "check", lambda *a, **k: release.wait(10) and None)
    button = window.update_button
    button.check(silent=True)
    finder = button._finder
    monkeypatch.setattr(finder, "terminate", lambda: pytest.fail("terminate() called"), raising=False)
    started = __import__("time").monotonic()
    button.shutdown()
    assert __import__("time").monotonic() - started < 5
    assert finder in updater_ui._LEFT_RUNNING and finder.parent() is None
    release.set()
    assert finder.wait(5000)
    app.processEvents()
    assert finder not in updater_ui._LEFT_RUNNING


def test_garbage_is_collected_in_the_gui_thread(app):
    import gc
    from luci.gui.app import MainGarbageCollector
    was_enabled = gc.isenabled()
    try:
        collector = MainGarbageCollector(app)
        assert not gc.isenabled()
        junk = [[] for _ in range(gc.get_threshold()[0] + 500)]   # new containers raise the generation-0 count
        assert gc.get_count()[0] > gc.get_threshold()[0]
        collector.check()
        assert gc.get_count()[0] < gc.get_threshold()[0]
        del junk
    finally:
        collector._timer.stop()
        if was_enabled:
            gc.enable()
