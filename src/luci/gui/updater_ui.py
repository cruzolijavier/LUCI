"""The "Update LUCI" button of the menu bar (with a red "!" when a new version is waiting)
and the pop-up that tells about it when LUCI opens. The work itself is in ``luci.updater``."""

from __future__ import annotations

import os

from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QProgressDialog, QPushButton

from .. import updater
from . import theme

BADGE = 16
BADGE_GAP = BADGE + 14          # room kept on the right of the text while an update is waiting
RECHECK_MS = 60 * 60 * 1000     # look again every hour
FIRST_CHECK_MS = 4000           # shortly after opening, so the window appears first


def enabled() -> bool:
    """The button is for the executable. LUCI_UPDATER=1 shows it when running from source."""
    return updater.can_update()[0] or os.environ.get("LUCI_UPDATER") == "1"


class _Finder(QThread):
    found = Signal(object, str)           # (Update or None, error)

    def run(self):
        try:
            self.found.emit(updater.check(), "")
        except updater.UpdateError as exc:
            self.found.emit(None, str(exc))
        except Exception as exc:          # never let a thread kill LUCI
            self.found.emit(None, str(exc))


class _Installer(QThread):
    progress = Signal(int, int, str)
    done = Signal(object, str)            # (folder with the new files, error)

    def __init__(self, update, parent=None):
        super().__init__(parent)
        self.update = update

    def run(self):
        try:
            folder = updater.download(self.update, lambda a, b, t: self.progress.emit(a, b, t))
            self.done.emit(folder, "")
        except updater.UpdateError as exc:
            self.done.emit(None, str(exc))
        except Exception as exc:
            self.done.emit(None, f"{type(exc).__name__}: {exc}")


class UpdateButton(QPushButton):
    """Flat button for the menu bar's corner. Click = check, or install if one is waiting."""

    def __init__(self, window):
        super().__init__("Update LUCI", window)
        self.window_ = window
        self.pending = None                 # updater.Update waiting to be installed
        self.announced = set()              # versions already shown in a pop-up
        self._finder = None
        self._installer = None
        self._silent = True
        self.setCursor(Qt.PointingHandCursor)
        self.setFlat(True)
        self.badge = QLabel("!", self)
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setFixedSize(BADGE, BADGE)
        self.badge.setStyleSheet(f"background:{theme.RED}; color:#ffffff; border-radius:{BADGE // 2}px;"
                                 "font-weight:bold; font-size:11px;")
        self.badge.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.badge.hide()
        self._refresh()
        self.clicked.connect(self._clicked)
        self._timer = QTimer(self)
        self._timer.timeout.connect(lambda: self.check(silent=True))
        self._timer.start(RECHECK_MS)
        QTimer.singleShot(FIRST_CHECK_MS, lambda: self.check(silent=True))

    # ---------------------------------------------------------------- looks
    def _style(self) -> str:
        right = 10 + (BADGE_GAP if self.pending else 0)
        colour = theme.ORANGE if self.pending else theme.CREAM_3
        return (f"QPushButton {{ color:{colour}; background:transparent; border:none; font-size:12px;"
                f" padding:4px {right}px 4px 10px; border-radius:6px; }}"
                f"QPushButton:hover {{ background:{theme.ORANGE_TINT}; color:{theme.CREAM}; }}")

    def _refresh(self):
        self.setStyleSheet(self._style())
        if self.pending:
            self.setText("Update LUCI")
            self.setToolTip(f"LUCI {self.pending.version} is available. Click to install it.")
        else:
            self.setText("Update LUCI")
            self.setToolTip("Check for a new version of LUCI.")
        self.badge.setVisible(bool(self.pending))
        # Fixed width = text + padding (+ room for the "!"), and tell the menu bar to lay it out again.
        right = 10 + (BADGE_GAP if self.pending else 0)
        self.setFixedWidth(self.fontMetrics().horizontalAdvance(self.text()) + 10 + right + 6)
        bar = self.window_.menuBar()
        bar.setCornerWidget(self, Qt.TopRightCorner)
        self.show()
        self._place_badge()

    def _place_badge(self):
        self.badge.move(self.width() - BADGE - 10, (self.height() - BADGE) // 2)
        self.badge.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place_badge()

    # ---------------------------------------------------------------- check
    def check(self, silent: bool = False):
        """Look on GitHub. silent=True is the background check: it says nothing unless there is news."""
        if self._finder is not None and self._finder.isRunning():
            return
        if self._installer is not None and self._installer.isRunning():
            return
        self._silent = silent
        self._finder = _Finder(self)
        self._finder.found.connect(self._checked)
        self._finder.start()

    def _checked(self, update, error):
        if update is not None:
            self.pending = update
            self._refresh()
            if update.version not in self.announced and self._silent:
                self.announced.add(update.version)
                self._ask_install(announce=True)
            elif not self._silent:
                self._ask_install()
            return
        if error:
            if not self._silent:
                QMessageBox.warning(self.window_, "Update LUCI", error)
            return
        self.pending = None
        self._refresh()
        if not self._silent:
            QMessageBox.information(self.window_, "Update LUCI",
                                    f"LUCI {updater.current_version()} is up to date.")

    def _clicked(self):
        if self.pending is not None:
            self._ask_install()
        else:
            self.check(silent=False)

    # -------------------------------------------------------------- install
    def _ask_install(self, announce: bool = False):
        update = self.pending
        if update is None:
            return
        ok, reason = updater.can_update()
        if not ok and os.environ.get("LUCI_UPDATER") != "1":
            QMessageBox.information(self.window_, "Update LUCI", reason)
            return
        box = QMessageBox(self.window_)
        box.setWindowTitle("Update LUCI")
        box.setIcon(QMessageBox.Information)
        box.setText(f"LUCI {update.version} is available (you have {updater.current_version()}).")
        details = update.notes.strip()
        mb = update.size / 1e6
        box.setInformativeText((details + "\n\n" if details else "") +
                               f"The download is about {mb:.0f} MB. LUCI will close and open again by itself. "
                               "Your environments and settings are kept.")
        install = box.addButton("Update now", QMessageBox.AcceptRole)
        box.addButton("Later", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is install:
            self._install()

    def _install(self):
        running = [page for ws in self.window_.workspaces.values() for page in ws.running_pages()]
        if running:
            QMessageBox.warning(self.window_, "Update LUCI",
                                "A workflow is running. Wait until it finishes (or stop it) and update then.")
            return
        self.dialog = QProgressDialog("Downloading...", None, 0, 100, self.window_)
        self.dialog.setWindowTitle("Update LUCI")
        self.dialog.setWindowModality(Qt.WindowModal)
        self.dialog.setMinimumDuration(0)
        self.dialog.setAutoClose(False)
        self.dialog.setAutoReset(False)
        self.dialog.setValue(0)
        self.dialog.show()
        self._installer = _Installer(self.pending, self)
        self._installer.progress.connect(self._progress)
        self._installer.done.connect(self._installed)
        self._installer.start()

    def _progress(self, done, total, text):
        if total:
            self.dialog.setMaximum(100)
            self.dialog.setValue(min(99, int(done * 100 / total)))
            self.dialog.setLabelText(f"{text} {done / 1e6:.0f} / {total / 1e6:.0f} MB")
        else:
            self.dialog.setMaximum(0)       # busy bar while unpacking
            self.dialog.setLabelText(text)

    def _installed(self, folder, error):
        self.dialog.close()
        if error or folder is None:
            QMessageBox.critical(self.window_, "Update LUCI", f"{error}\n\nLUCI was not changed.")
            return
        try:
            updater.apply_and_restart(folder)
        except Exception as exc:
            QMessageBox.critical(self.window_, "Update LUCI",
                                 f"The update could not be started: {exc}\n\nLUCI was not changed.")
            return
        QApplication.quit()

    def shutdown(self):
        """Called when the window closes: do not leave threads running."""
        for thread in (self._finder, self._installer):
            if thread is not None and thread.isRunning():
                if not thread.wait(3000):
                    thread.terminate()
                    thread.wait(1000)


__all__ = ["UpdateButton", "enabled"]
