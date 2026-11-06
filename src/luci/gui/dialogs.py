"""Windows that manage LUCI itself: installing environments and settings."""

from __future__ import annotations

import codecs
import subprocess
import sys

from PySide6.QtCore import QProcess, QProcessEnvironment, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..envs.manager import EnvManager
from ..registry import ENV_BY_KEY, PROGRAMS
from ..settings import Settings, current_platform
from .widgets import LabeledPath, repolish, row_label, status_pill


def luci_cli(*args: str) -> list[str]:
    """argv that runs the LUCI CLI with the interpreter running the GUI."""
    from ..frozen import cli_interpreter
    return [cli_interpreter(), "-m", "luci", *args]


def fit_to_screen(dialog: QDialog, width: int, height: int):
    """Open at the wanted size, but never larger than the screen (150% scaling)."""
    screen = dialog.screen() or QApplication.primaryScreen()
    if screen is not None:
        area = screen.availableGeometry()
        width, height = min(width, area.width() - 40), min(height, area.height() - 60)
    dialog.resize(width, height)


def child_environment() -> QProcessEnvironment:
    """UTF-8 output from LUCI and the programs, whatever the Windows code page."""
    environment = QProcessEnvironment.systemEnvironment()
    # Console text only; files keep each program's own default encoding.
    environment.insert("PYTHONIOENCODING", "utf-8")
    return environment


def start_process(process: QProcess, argv: list[str], cwd: str = ""):
    """Start the LUCI CLI; it forwards a terminate request to the program it runs."""
    if cwd:
        process.setWorkingDirectory(cwd)
    # Runs are not interactive: a program asking a question must fail, not wait forever.
    process.setStandardInputFile(QProcess.nullDevice())
    process.start(argv[0], argv[1:])


def stop_process(process: QProcess | None, wait: bool = False):
    """Stop a process and every program it started (pixi, the backend...).

    Never blocks the window: the stop request is sent and the process's own
    ``finished`` signal reports the end. If it is still running 8 s later it is
    killed. ``wait=True`` (only when LUCI itself is closing) waits up to 8 s.

    Windows: ``taskkill /T /F`` ends the whole tree, started without waiting.
    Elsewhere the LUCI CLI receives SIGTERM and passes it to the process group
    of the program it launched (see ``luci.proc``).
    """
    try:
        if process is None or process.state() == QProcess.NotRunning:
            return
        pid = int(process.processId())
    except RuntimeError:  # the Qt object is already gone
        return
    if current_platform() == "windows":
        if pid > 0:
            try:
                subprocess.Popen(["taskkill", "/PID", str(pid), "/T", "/F"],
                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            except OSError:
                process.kill()
        else:
            process.kill()
    else:
        process.terminate()
    if wait:
        if not process.waitForFinished(8000):
            process.kill()
            process.waitForFinished(2000)
        return
    QTimer.singleShot(8000, lambda: _kill_if_running(process))


def _kill_if_running(process: QProcess):
    try:
        if process.state() != QProcess.NotRunning:
            process.kill()
    except RuntimeError:
        pass


def env_state(manager: EnvManager, env_key: str) -> tuple[str, str]:
    """(pill text, pill state) describing one environment."""
    spec = ENV_BY_KEY[env_key]
    if not spec.available:
        return "Coming soon", "pending"
    if not manager.supported(spec):
        return "Linux / WSL only" if spec.platforms == ("linux",) else "Not for this system", "blocked"
    if manager.is_installed(env_key):
        if manager.is_outdated(env_key):
            return "Update available", "update"
        return "Installed", "ok"
    return "Not installed", "missing"


class ProcessDialog(QDialog):
    """Runs one LUCI CLI command (install / remove) and shows its output."""

    # Not called "finished": that name belongs to QDialog's own signal.
    completed = Signal(int)

    def __init__(self, title: str, argv: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        fit_to_screen(self, 760, 460)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        heading.setWordWrap(True)
        layout.addWidget(heading)
        self.state = QLabel("Working... downloading and installing can take several minutes. "
                            "The log below shows what is happening.")
        self.state.setObjectName("pageCaption")
        self.state.setWordWrap(True)
        layout.addWidget(self.state)
        progress_row = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # busy indicator: pixi does not report a percentage
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(10)
        progress_row.addWidget(self.progress, 1)
        self.elapsed = QLabel("0:00")
        self.elapsed.setObjectName("pageCaption")
        progress_row.addWidget(self.elapsed)
        layout.addLayout(progress_row)
        self._seconds = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)
        self._title = title
        self.log = QPlainTextEdit()
        self.log.setObjectName("console")
        self.log.setReadOnly(True)
        layout.addWidget(self.log, 1)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.clicked.connect(self.stop)
        self.close_button = QPushButton("Close")
        self.close_button.setObjectName("secondaryButton")
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.accept)
        buttons.addWidget(self.stop_button)
        buttons.addWidget(self.close_button)
        layout.addLayout(buttons)

        self.exit_code: int | None = None
        self._stopped = False
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self.process = QProcess(self)
        self.process.setProcessEnvironment(child_environment())
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read)
        self.process.finished.connect(self._done)
        self.process.errorOccurred.connect(self._error)
        self.log.appendPlainText("$ " + " ".join(argv) + "\n")
        start_process(self.process, argv)

    def _read(self):
        data = self._decoder.decode(bytes(self.process.readAllStandardOutput()))
        progress = [line for line in data.splitlines() if "[LUCI] Still working (" in line]
        if progress:
            self.state.setText(progress[-1].replace("[LUCI] ", "") + ". Not frozen: big "
                               "environments (PyTorch) take several minutes, more on slow networks.")
        if data:
            self.log.moveCursor(QTextCursor.End)
            self.log.insertPlainText(data)
            self.log.ensureCursorVisible()

    def _tick(self):
        self._seconds += 1
        self.elapsed.setText(f"{self._seconds // 60}:{self._seconds % 60:02d}")

    def _done(self, code: int, _status=None):
        if self.exit_code is not None:
            return  # errorOccurred and finished can both report the same end
        self._read()
        self.exit_code = code
        self._timer.stop()
        self.progress.setRange(0, 1)
        self.progress.setValue(1 if code == 0 else 0)
        if self._stopped:
            text, kind = "Stopped. Nothing was changed for programs already installed.", "warn"
        elif code == 0:
            text, kind = "Finished successfully.", "ok"
        else:
            text, kind = "Failed. The last lines of the log below explain why.", "error"
        self.state.setText(text)
        self.state.setObjectName("resultLabel")
        self.state.setProperty("kind", kind)
        repolish(self.state)
        self.setWindowTitle(f"{self._title} - {text.split('.')[0]}")
        self.stop_button.setEnabled(False)
        self.close_button.setEnabled(True)
        self.completed.emit(code)

    def _error(self, error):
        # Only a failure to start is reported here; a stopped or crashed process
        # also emits finished, which _done handles.
        if error == QProcess.FailedToStart and self.exit_code is None:
            self.log.appendPlainText(f"\n[LUCI] Could not start: {self.process.errorString()}")
            self._done(1)

    def stop(self):
        if self._stopped or self.exit_code is not None:
            return
        self._stopped = True
        self.stop_button.setEnabled(False)
        self.state.setText("Stopping...")
        stop_process(self.process)

    def reject(self):
        if self.process.state() != QProcess.NotRunning:
            return  # Use Stop first; closing must not orphan an install.
        super().reject()


class EnvironmentsDialog(QDialog):
    """Every environment, its state, and install / remove buttons."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LUCI environments")
        fit_to_screen(self, 900, 540)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        title = QLabel("Environments")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        self.caption = QLabel()
        self.caption.setObjectName("pageCaption")
        self.caption.setWordWrap(True)
        self.caption.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.caption)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Environment", "Programs", "State", ""])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout.addWidget(self.table, 1)
        buttons = QHBoxLayout()
        open_home = QPushButton("Open LUCI folder")
        open_home.setObjectName("secondaryButton")
        open_home.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(EnvManager().home))))
        buttons.addWidget(open_home)
        buttons.addStretch(1)
        close = QPushButton("Close")
        close.setObjectName("secondaryButton")
        close.clicked.connect(self.accept)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.refresh()

    def refresh(self):
        manager = EnvManager()
        pixi = manager.pixi_path()
        self.caption.setText(
            f"Stored in {manager.home}. pixi: {pixi or 'downloaded automatically on the first install'}.")
        users: dict[str, list[str]] = {}
        for spec in PROGRAMS:
            for variant in spec.variants:
                names = users.setdefault(variant.env, [])
                label = spec.name if len(spec.variants) == 1 else f"{spec.name} ({variant.label})"
                if label not in names:
                    names.append(label)
        envs = list(ENV_BY_KEY.values())
        self.table.setRowCount(len(envs))
        for row, spec in enumerate(envs):
            name = QTableWidgetItem(f"{spec.title}  {spec.size_hint}".strip())
            name.setToolTip(spec.note)
            self.table.setItem(row, 0, name)
            programs = QTableWidgetItem(", ".join(users.get(spec.key, [])))
            programs.setToolTip(spec.note)
            self.table.setItem(row, 1, programs)
            text, state = env_state(manager, spec.key)
            pill_cell = QWidget()
            pill_cell.setObjectName("formPanel")
            pill_layout = QHBoxLayout(pill_cell)
            pill_layout.setContentsMargins(6, 2, 6, 2)
            pill = status_pill(text, state)
            pill.setToolTip(spec.note)
            pill_layout.addWidget(pill)
            self.table.setCellWidget(row, 2, pill_cell)
            action_cell = QWidget()
            action_cell.setObjectName("formPanel")
            action_layout = QHBoxLayout(action_cell)
            action_layout.setContentsMargins(6, 2, 6, 2)
            if state in ("missing", "update"):
                button = QPushButton("Install" if state == "missing" else "Update")
                button.setObjectName("primaryButton")
                button.clicked.connect(lambda _=False, k=spec.key: self._run("install", k))
                action_layout.addWidget(button)
            if state in ("ok", "update"):
                button = QPushButton("Uninstall")
                button.setObjectName("secondaryButton")
                button.clicked.connect(lambda _=False, k=spec.key: self._run("remove", k))
                action_layout.addWidget(button)
            self.table.setCellWidget(row, 3, action_cell)
            self.table.setRowHeight(row, 46)

    def _run(self, action: str, env_key: str):
        if action == "remove":
            if uninstall_environment(self, env_key):
                self.refresh()
                self.changed.emit()
            return
        dialog = ProcessDialog(f"Installing {ENV_BY_KEY[env_key].title}",
                               luci_cli("env", "install", env_key), self)
        dialog.completed.connect(lambda _code: (self.refresh(), self.changed.emit()))
        dialog.exec()


def uninstall_environment(parent, env_key: str, busy: bool = False) -> bool:
    """Ask, then uninstall one environment. Returns True if it was removed."""
    spec = ENV_BY_KEY[env_key]
    users = [p.name for p in PROGRAMS if any(v.env == env_key for v in p.variants)]
    if busy:
        QMessageBox.warning(parent, "Program running",
                            f"{', '.join(users)} is running. Stop it before uninstalling.")
        return False
    size = spec.size_hint or "several GB"
    answer = QMessageBox.question(
        parent, "Uninstall",
        f"Uninstall {', '.join(users)}?\n\nThis deletes its environment ({size}) and frees "
        "that disk space. Your input files and results are not touched. You can install it "
        "again at any time.",
        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    if answer != QMessageBox.Yes:
        return False
    dialog = ProcessDialog(f"Uninstalling {', '.join(users)}", luci_cli("env", "remove", env_key),
                           parent)
    dialog.exec()
    return dialog.exit_code == 0


class SettingsDialog(QDialog):
    """External programs, tokens and paths LUCI cannot install itself."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LUCI settings")
        self.settings = Settings.load()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        title = QLabel("Settings")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        caption = QLabel("Programs LUCI cannot install for you (licensed or not packaged; Gaussian, "
                         "ORCA, g-xTB and the Hugging Face token are only used by Linux programs), "
                         "and where results go.")
        caption.setObjectName("pageCaption")
        caption.setWordWrap(True)
        layout.addWidget(caption)
        where = QLabel(f"Saved in {Settings.path()}")
        where.setObjectName("hint")
        where.setWordWrap(True)
        where.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(where)
        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        self.gaussian = LabeledPath("Folder containing g16", "", directory=True)
        self.gaussian.setText(self.settings.gaussian_dir)
        self.orca = LabeledPath("Folder containing orca", "", directory=True)
        self.orca.setText(self.settings.orca_dir)
        self.gxtb = LabeledPath("g-xTB executable", "All files (*)")
        self.gxtb.setText(self.settings.gxtb_path)
        self.hf_token = QLineEdit(self.settings.hf_token)
        self.hf_token.setEchoMode(QLineEdit.Password)
        self.hf_token.setPlaceholderText("hf_... (only for UMA models: ThermoMLIP, TS-tools MLIP)")
        self.results = LabeledPath("Default results folder", "", directory=True)
        self.results.setText(self.settings.results_dir)
        self.results.edit.setPlaceholderText(str(Settings().default_results_dir()))
        self.pixi = LabeledPath("pixi executable", "All files (*)")
        self.pixi.setText(self.settings.pixi_path)
        self.pixi.edit.setPlaceholderText("Automatic (PATH, or downloaded by LUCI)")
        self.openai_key = QLineEdit(self.settings.openai_api_key)
        self.openai_key.setEchoMode(QLineEdit.Password)
        self.openai_key.setPlaceholderText("sk-... (the LUCI assistant; or put it in openai_key.txt)")
        self.restricted = QCheckBox("Restricted network (firewall blocks the conda/PyPI name mapping)")
        self.restricted.setChecked(self.settings.restricted_network)
        form.addRow(row_label("Gaussian 16"), self.gaussian)
        form.addRow(row_label("ORCA"), self.orca)
        form.addRow(row_label("g-xTB"), self.gxtb)
        form.addRow(row_label("Hugging Face token"), self.hf_token)
        form.addRow(row_label("OpenAI API key"), self.openai_key)
        form.addRow(row_label("Results folder"), self.results)
        form.addRow(row_label("pixi"), self.pixi)
        form.addRow("", self.restricted)
        layout.addLayout(form)
        layout.addStretch(1)
        fit_to_screen(self, 760, 560)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        self.settings.gaussian_dir = self.gaussian.text()
        self.settings.orca_dir = self.orca.text()
        self.settings.gxtb_path = self.gxtb.text()
        self.settings.hf_token = self.hf_token.text().strip()
        self.settings.openai_api_key = self.openai_key.text().strip()
        self.settings.results_dir = self.results.text()
        self.settings.pixi_path = self.pixi.text()
        self.settings.restricted_network = self.restricted.isChecked()
        self.settings.save()
        self.accept()


__all__ = ["EnvironmentsDialog", "ProcessDialog", "SettingsDialog", "env_state", "luci_cli",
           "start_process", "stop_process", "uninstall_environment"]
