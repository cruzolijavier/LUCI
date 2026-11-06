"""The shell around every program form: header, status banners, run controls, console.

The form (``luci.gui.form``) describes *what* to run; this page knows *how*:
it checks the environment is installed, offers to install it, starts the LUCI
CLI in a QProcess and streams its output.
"""

from __future__ import annotations

import codecs
import re

from PySide6.QtCore import QProcess, Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit, QPushButton, QScrollArea,
    QSplitter, QVBoxLayout, QWidget,
)

from ..envs.manager import EnvManager
from ..registry import ENV_BY_KEY, LAYER_BY_KEY
from .dialogs import (
    ProcessDialog, child_environment, env_state, luci_cli, start_process, stop_process,
    uninstall_environment,
)
from .widgets import repolish, status_pill

# Forms stop growing past this width on large screens, like the landing cards.
FORM_MAX_WIDTH = 1120
ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


class Banner(QFrame):
    """A coloured strip with one message (info, warn or error)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("banner")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 10, 8)
        layout.setSpacing(12)
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.RichText)
        self.label.setOpenExternalLinks(True)
        layout.addWidget(self.label, 1)
        self.button = QPushButton()
        self.button.setObjectName("primaryButton")
        self.button.hide()
        layout.addWidget(self.button, 0, Qt.AlignVCenter)
        self.hide()

    def show_message(self, kind: str, html: str, button: str = ""):
        self.setProperty("kind", kind)
        repolish(self)
        self.label.setText(html)
        self.button.setText(button)
        self.button.setVisible(bool(button))
        self.show()


class PackagePage(QWidget):
    """Common shell that gives every program the same workflow controls."""

    back_requested = Signal()
    environments_changed = Signal()

    def __init__(self, form: QWidget, parent=None):
        super().__init__(parent)
        self.form = form
        self.process: QProcess | None = None
        self._stopping = False
        program = form.package

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QWidget()
        header.setObjectName("formPanel")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(22, 10, 22, 4)
        header_layout.setSpacing(6)
        actions = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.setObjectName("packageBackButton")
        self.back_button.clicked.connect(self.back_requested.emit)
        actions.addWidget(self.back_button)
        actions.addStretch(1)
        self.uninstall_button = QPushButton("Uninstall")
        self.uninstall_button.setObjectName("packageBackButton")
        self.uninstall_button.setToolTip("Delete this program's environment to free disk space. "
                                         "Your files and results are kept.")
        self.uninstall_button.clicked.connect(self.uninstall)
        actions.addWidget(self.uninstall_button)
        actions.addSpacing(12)
        self.run_button = QPushButton("Run")
        self.run_button.setObjectName("runButton")
        self.run_button.clicked.connect(self.run)
        actions.addWidget(self.run_button)
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop)
        actions.addWidget(self.stop_button)
        header_layout.addLayout(actions)
        root.addWidget(header)

        # Title, caption and banners scroll with the form, so a short window
        # still leaves room for the fields themselves.
        body = QWidget()
        body.setObjectName("formPanel")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        intro = QWidget()
        intro.setObjectName("formPanel")
        intro_layout = QVBoxLayout(intro)
        intro_layout.setContentsMargins(26, 4, 26, 0)
        intro_layout.setSpacing(6)

        title_row = QHBoxLayout()
        title_row.setSpacing(14)
        title = QLabel(program.name)
        title.setObjectName("pageTitle")
        title_row.addWidget(title)
        self.pill = status_pill("", "missing")
        title_row.addWidget(self.pill, 0, Qt.AlignVCenter)
        title_row.addStretch(1)
        intro_layout.addLayout(title_row)
        layer = LAYER_BY_KEY[program.layer]
        caption = QLabel(f"{layer.title} · {program.description}")
        caption.setObjectName("pageCaption")
        caption.setWordWrap(True)
        intro_layout.addWidget(caption)
        self.banner = Banner()
        self.banner.button.clicked.connect(self.install)
        intro_layout.addWidget(self.banner)
        self.requirements = Banner()
        intro_layout.addWidget(self.requirements)
        body_layout.addWidget(intro)
        body_layout.addWidget(form)

        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_scroll.setFrameShape(QFrame.NoFrame)
        centered = QWidget()
        centered.setObjectName("formPanel")
        self._centering = QHBoxLayout(centered)
        self._centering.setContentsMargins(0, 0, 0, 0)
        self._centering.addWidget(body, 1)
        form_scroll.setWidget(centered)
        self._form_scroll = form_scroll
        splitter.addWidget(form_scroll)

        console_panel = QWidget()
        console_layout = QVBoxLayout(console_panel)
        console_layout.setContentsMargins(22, 8, 22, 16)
        console_label = QLabel("Execution console")
        console_label.setObjectName("consoleLabel")
        console_layout.addWidget(console_label)
        self.console = QPlainTextEdit()
        self.console.setObjectName("console")
        self.console.setReadOnly(True)
        self.console.setMinimumHeight(60)
        console_layout.addWidget(self.console)
        splitter.addWidget(console_panel)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([640, 120])
        self.console.setPlaceholderText("Output of the run appears here.")
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        root.addWidget(splitter, 1)

        form.variant_changed.connect(lambda _key: self.refresh_status())
        self.refresh_status()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._centre_form()

    def showEvent(self, event):
        super().showEvent(event)
        # The window may have been resized while another page was shown.
        self._centre_form()

    def _centre_form(self):
        """Centre the form with side margins once the window is wider than it needs."""
        spare = max(0, self._form_scroll.viewport().width() - FORM_MAX_WIDTH)
        self._centering.setContentsMargins(spare // 2, 0, spare - spare // 2, 0)

    # ---------------------------------------------------------------- status
    def env_key(self) -> str:
        return self.form.current_variant().env

    def refresh_status(self):
        """Update the pill, the banners and the Run button for the chosen variant."""
        manager = EnvManager()
        variant = self.form.current_variant()
        env = ENV_BY_KEY[variant.env]
        text, state = env_state(manager, variant.env)
        self.pill.setText(text)
        self.pill.setProperty("state", state)
        repolish(self.pill)
        if state == "pending":
            self.banner.show_message("info", f"<b>Not available yet.</b> {env.note}")
        elif state == "blocked":
            self.banner.show_message(
                "error", f"<b>Cannot run on this computer.</b> {env.note or 'Unsupported system.'}")
        elif state == "missing":
            size = f" ({env.size_hint})" if env.size_hint else ""
            self.banner.show_message(
                "warn", f"<b>{env.title}</b> is not installed yet{size}. LUCI installs it in its "
                        "own environment, without touching anything else.", "Install")
        elif state == "update":
            self.banner.show_message(
                "warn", f"A newer definition of <b>{env.title}</b> ships with this LUCI version.",
                "Update")
        else:
            self.banner.hide()
        notes = [*(f"Needs {item}." for item in variant.requires)]
        if self.form.package.notes:
            notes.append(self.form.package.notes)
        if notes:
            self.requirements.show_message("info", " ".join(notes))
        else:
            self.requirements.hide()
        running = self.process is not None and self.process.state() != QProcess.NotRunning
        self.uninstall_button.setVisible(state in ("ok", "update"))
        self.uninstall_button.setEnabled(not running)
        self.run_button.setEnabled(state in ("ok", "update") and not running)
        self.run_button.setToolTip("" if state in ("ok", "update") else self.banner.label.text())

    # ------------------------------------------------------------- execution
    def command(self) -> list[str]:
        return self.form.command()

    def install(self):
        env = ENV_BY_KEY[self.env_key()]
        dialog = ProcessDialog(f"Installing {env.title}", luci_cli("env", "install", env.key), self)
        dialog.exec()
        self.refresh_status()
        self.environments_changed.emit()

    def uninstall(self):
        if uninstall_environment(self, self.env_key(), busy=self.is_running()):
            self.refresh_status()
            self.environments_changed.emit()

    def run(self):
        if self.process is not None and self.process.state() != QProcess.NotRunning:
            return
        missing = self.form.missing_required()
        if missing:
            QMessageBox.warning(self, "Missing information",
                                "Fill in before running:\n\n• " + "\n• ".join(missing))
            return
        if not self._input_ready():
            return
        try:
            command = self.command()
        except ValueError as exc:
            QMessageBox.warning(self, "Cannot build the command", str(exc))
            return
        self.form.remember_output()
        self._decoder.reset()
        self.console.clear()
        self.console.appendPlainText("$ " + " ".join(command) + "\n")
        self.process = QProcess(self)
        self.process.setProcessEnvironment(child_environment())
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._error)
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        start_process(self.process, command)

    def _input_ready(self) -> bool:
        """Stop a run LUCI's check already knows would fail, or offer to leave bad entries out."""
        checked = self.form.standard_input()
        if checked is None:
            return True
        checked.check()  # the file may have changed since it was last read
        checked.wait(10000)
        bad, total, fatal = checked.problems()
        if fatal:
            QMessageBox.warning(self, "The input cannot be used",
                                f"{fatal}\n\nThe details and how to fix it are shown under the input.")
            return False
        if not bad or checked.skip_invalid():
            return True
        mode = self.form.current_mode()
        noun = "molecule" if mode.kind == "molecules" else "file"
        if bad >= total:
            QMessageBox.warning(self, "Nothing can be run",
                                f"All {total} {noun}s have errors. The list under the input says what "
                                "is wrong with each one and how to fix it.")
            return False
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Some entries have errors")
        box.setText(f"{bad} of {total} {noun}s have errors and would make the program fail.")
        box.setInformativeText("They are listed under the input with how to fix them. You can fix "
                               "them first, or leave them out and run the rest.")
        leave_out = box.addButton(f"Leave them out and run {total - bad}", QMessageBox.AcceptRole)
        box.addButton(QMessageBox.Cancel)
        box.exec()
        if box.clickedButton() is not leave_out:
            return False
        checked.set_skip_invalid(True)
        return True

    def _read_output(self):
        if self.process:
            data = self._decoder.decode(bytes(self.process.readAllStandardOutput()))
            data = ANSI.sub("", data)
            if data:
                self.console.moveCursor(QTextCursor.End)
                self.console.insertPlainText(data)
                self.console.ensureCursorVisible()

    def _finished(self, exit_code: int, _exit_status=None):
        self._read_output()
        self.stop_button.setEnabled(False)
        if self._stopping:
            self.console.appendPlainText("\n[LUCI] Stopped by the user.\n")
        else:
            self.console.appendPlainText(f"\n[LUCI] Workflow finished with exit code {exit_code}.\n")
        self._stopping = False
        self.refresh_status()

    def _error(self, error):
        # A stopped or crashed run also emits finished; only a failed start is reported here.
        if error == QProcess.FailedToStart:
            self.console.appendPlainText(f"\n[LUCI] Could not start: {self.process.errorString()}\n")
            self.stop_button.setEnabled(False)
            self._stopping = False
            self.refresh_status()

    def stop(self, wait: bool = False):
        if not self.is_running():
            return
        self._stopping = True
        self.stop_button.setEnabled(False)
        self.console.appendPlainText("\n[LUCI] Stopping...\n")
        stop_process(self.process, wait=wait)

    def is_running(self) -> bool:
        return self.process is not None and self.process.state() != QProcess.NotRunning

    def save_state(self) -> dict:
        return self.form.save_state()

    def load_state(self, state: dict):
        self.form.load_state(state)
        self.refresh_status()

    def reset(self):
        self.form.reset()
        self.refresh_status()
