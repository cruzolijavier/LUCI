"""The three standard inputs, with LUCI's check of them shown under the field.

* :class:`MoleculesInput`  a CSV with smiles and code_name columns
* :class:`SmilesInput`     one SMILES and its code_name
* :class:`StructuresInput` a folder of 3D structures (converted to SDF at run time)

The CSV and folder panels show a one-line verdict ("40 molecules, 38 OK, 2
with errors"), the list of problems with how to fix them, and a box to leave
the bad entries out. LUCI does not check the SMILES themselves: the
programs do. Reading a CSV runs in a background thread, so a big file never
freezes the window.
"""

from __future__ import annotations

import html
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from ..chem.issues import LEVEL_ORDER, Issue, worst
from ..chem.molecules import MoleculeRecord, MoleculeSet, name_issues, read_molecules
from ..chem.structures import FolderResult, plan_folder
from ..registry import InputMode
from . import theme
from .widgets import LabeledPath, repolish, transparent

def level_colour(level: str, default: str | None = None) -> str:
    """Colour of a check level in the current theme."""
    return {"error": theme.RED, "warning": theme.AMBER, "info": theme.BLUE,
            "ok": theme.GREEN}.get(level, default or theme.CREAM_2)
LEVEL_WORDS = {"error": "Error", "warning": "Warning", "info": "Note", "ok": "OK"}
SUMMARY_KIND = {"error": "error", "warning": "warn", "info": "ok", "ok": "ok"}
MAX_ROWS = 2000
# Long SMILES or names wrap at any character instead of widening the form.
BREAK = "​"


class _Relay(QObject):
    """Brings a background result back to the GUI thread."""

    done = Signal(int, object)


def run_in_background(token: int, work, relay: _Relay) -> None:
    def target():
        try:
            result = work()
        except Exception as exc:  # reported in the panel, never raised in a thread
            result = exc
        try:
            relay.done.emit(token, result)
        except RuntimeError:
            pass  # the page was closed while the check ran

    threading.Thread(target=target, daemon=True).start()


def breakable(text: str, every: int = 12) -> str:
    """HTML-escaped text that may wrap inside long words (SMILES, file names)."""
    chunks = [text[i:i + every] for i in range(0, len(text), every)]
    return BREAK.join(html.escape(chunk) for chunk in chunks)


def issues_html(issues: list[Issue]) -> str:
    parts = []
    for issue in sorted(issues, key=lambda i: LEVEL_ORDER[i.level]):
        colour = level_colour(issue.level)
        hint = f"<br><span style='color:{theme.CREAM_2}'>{html.escape(issue.hint)}</span>" if issue.hint else ""
        parts.append(f"<p style='margin:0 0 6px 0'><b style='color:{colour}'>"
                     f"{LEVEL_WORDS[issue.level]}:</b> {html.escape(issue.message)}{hint}</p>")
    return "".join(parts) or f"<p style='color:{theme.GREEN}'>No problems found.</p>"


def fatal_html(issues: list[Issue]) -> str:
    """File-level errors: the message in bold, the fix in normal weight."""
    return "<br>".join(f"<b>{html.escape(i.message)}</b> <span style='font-weight:400;color:{theme.CREAM_2}'>"
                       f"{html.escape(i.hint)}</span>" for i in issues if i.level == "error")


class CheckPanel(QFrame):
    """Verdict line, problem list and the explanation of the selected entry."""

    recheck_requested = Signal()
    skip_changed = Signal(bool)

    def __init__(self, noun: str, columns: list[str], parent=None):
        super().__init__(parent)
        self.setObjectName("checkPanel")
        self.noun = noun
        self._entries: list = []
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(8)
        self.summary = QLabel()
        self.summary.setObjectName("checkSummary")
        self.summary.setWordWrap(True)
        self.summary.setTextFormat(Qt.RichText)
        top.addWidget(self.summary, 1)
        self.recheck = QPushButton("Check again")
        self.recheck.setObjectName("smallButton")
        self.recheck.setToolTip("Read the input again (after editing it in Excel, for example).")
        self.recheck.clicked.connect(self.recheck_requested.emit)
        top.addWidget(self.recheck, 0, Qt.AlignTop)
        root.addLayout(top)

        self.only_problems = QCheckBox("Problems only")
        self.only_problems.setObjectName("compactCheck")
        self.only_problems.setChecked(True)
        self.only_problems.toggled.connect(self._fill)
        root.addWidget(self.only_problems)

        self.list = QTreeWidget()
        self.list.setObjectName("issueList")
        self.list.setColumnCount(len(columns))
        self.list.setHeaderLabels(columns)
        self.list.setRootIsDecorated(False)
        self.list.setUniformRowHeights(True)
        self.list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list.setMinimumHeight(110)
        self.list.setMaximumHeight(220)
        self.list.header().setStretchLastSection(True)
        self.list.header().setSectionResizeMode(QHeaderView.Interactive)
        self.list.currentItemChanged.connect(self._selected)
        root.addWidget(self.list)
        self.more = QLabel()
        self.more.setObjectName("hint")
        self.more.hide()
        root.addWidget(self.more)

        self.detail = QLabel()
        self.detail.setObjectName("checkDetail")
        self.detail.setWordWrap(True)
        self.detail.setTextFormat(Qt.RichText)
        self.detail.setTextInteractionFlags(Qt.TextSelectableByMouse)
        root.addWidget(self.detail)

        self.skip = QCheckBox()
        self.skip.setObjectName("compactCheck")
        self.skip.toggled.connect(self.skip_changed.emit)
        self.skip.hide()
        root.addWidget(self.skip)
        self.hide()

    # ------------------------------------------------------------- layout
    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self.fit_text)

    def fit_text(self) -> None:
        """Reserve the height wrapped text needs at its current width.

        Form rows do not ask a word-wrapped label for its height at the real
        width; the minimum is reset first so it can also shrink.
        """
        for label in (self.detail, self.summary):
            label.setMinimumHeight(0)
            width = label.width()
            height = label.heightForWidth(width) if width > 50 else -1
            label.setMinimumHeight(max(0, height))

    # ------------------------------------------------------------- states
    def set_summary(self, kind: str, text: str) -> None:
        self.summary.setProperty("kind", kind)
        repolish(self.summary)
        self.summary.setText(text)
        self.show()
        QTimer.singleShot(0, self.fit_text)

    def busy(self, text: str) -> None:
        self.set_summary("busy", html.escape(text))
        self._entries = []
        self.list.clear()
        self.list.hide()
        self.only_problems.hide()
        self.more.hide()
        self.detail.clear()
        self.skip.hide()

    def set_entries(self, entries: list, *, summary_kind: str, summary: str, bad: int) -> None:
        """``entries``: objects with ``status``, ``issues``, ``cells()`` and ``detail_html()``."""
        self._entries = entries
        self.set_summary(summary_kind, summary)
        has_problems = any(e.status in ("error", "warning") for e in entries)
        self.only_problems.blockSignals(True)
        self.only_problems.setChecked(has_problems)
        self.only_problems.blockSignals(False)
        self.only_problems.setVisible(bool(entries))
        self._fill()
        self.skip.blockSignals(True)
        if bad:
            self.skip.setText(f"Leave out the {bad} with errors")
            self.skip.setToolTip(f"Run the other {self.noun}s and skip the {bad} "
                                 f"{self.noun}{'s' if bad != 1 else ''} with errors.")
            self.skip.show()
        else:
            self.skip.hide()
        # A new input never inherits the choice made for the previous one.
        self.skip.setChecked(False)
        self.skip.blockSignals(False)
        self.skip_changed.emit(False)

    def _fill(self, *_args) -> None:
        self.list.clear()
        only = self.only_problems.isChecked()
        shown = [e for e in self._entries if not only or e.status in ("error", "warning")]
        if only:
            shown.sort(key=lambda e: LEVEL_ORDER.get(e.status, 3))
        for entry in shown[:MAX_ROWS]:
            cells = [str(c) for c in entry.cells()]
            item = QTreeWidgetItem(cells)
            colour = QColor(level_colour(entry.status))
            item.setForeground(0, QBrush(colour))
            item.setData(0, Qt.UserRole, entry)
            item.setToolTip(len(cells) - 1, "\n".join(i.text() for i in entry.issues))
            self.list.addTopLevelItem(item)
        for column in range(self.list.columnCount() - 1):
            self.list.resizeColumnToContents(column)
            self.list.setColumnWidth(column, min(self.list.columnWidth(column), 160))
        hidden = len(shown) - MAX_ROWS
        self.more.setText(f"{hidden} more not listed; the run report lists all of them."
                          if hidden > 0 else "")
        self.more.setVisible(hidden > 0)
        self.list.setVisible(bool(shown))
        if shown:
            self.list.setCurrentItem(self.list.topLevelItem(0))
        else:
            self.detail.setText("")

    def _selected(self, current, _previous=None) -> None:
        if current is None:
            return
        entry = current.data(0, Qt.UserRole)
        if entry is not None:
            self.detail.setText(entry.detail_html())
            QTimer.singleShot(0, self.fit_text)


# ----------------------------------------------------------------- entries
class _MoleculeEntry:
    def __init__(self, record: MoleculeRecord):
        self.record = record
        self.issues = record.issues
        self.status = record.status

    def cells(self):
        first = next((i.message for i in self.issues if i.level in ("error", "warning")), "")
        return [LEVEL_WORDS[self.status] if self.status != "info" else "OK",
                self.record.code_name or "(empty)", first or "OK", self.record.line or "",
                self.record.smiles]

    def detail_html(self) -> str:
        name = html.escape(self.record.code_name or "(no code_name)")
        where = f" &middot; line {self.record.line}" if self.record.line else ""
        smiles = (f"<br><span style='font-family:Consolas,monospace'>{breakable(self.record.smiles)}"
                  "</span>" if self.record.smiles else "")
        return f"<b>{name}</b>{where}{smiles}<div style='margin-top:6px'>{issues_html(self.issues)}</div>"


class _FileEntry:
    def __init__(self, item):
        self.item = item
        self.issues = item.issues
        self.status = "error" if not item.ok else worst(item.issues)

    def cells(self):
        first = next((i.message for i in self.issues if i.level in ("error", "warning")), "")
        return [LEVEL_WORDS[self.status] if self.status != "info" else "OK", self.item.source.name,
                first or self.item.label()]

    def detail_html(self) -> str:
        what = {"use": "Used as it is (SDF).",
                "convert": "Converted to SDF with Open Babel when the run starts."}.get(self.item.action, "")
        return (f"<b>{breakable(self.item.source.name)}</b><br>{html.escape(what) if self.item.ok else ''}"
                f"<div style='margin-top:6px'>{issues_html(self.issues)}</div>")


# ----------------------------------------------------------------- inputs
class _CheckedInput(QWidget):
    """Shared plumbing: a field, a check panel and a background check."""

    changed = Signal(str)
    checked = Signal()

    def __init__(self, mode: InputMode, parent=None):
        super().__init__(parent)
        transparent(self)
        self.mode = mode
        self.result = None
        self.error = ""
        self._token = 0
        self._busy = False
        self._relay = _Relay(self)
        self._relay.done.connect(self._finished)
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(8)
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(250)
        self._debounce.timeout.connect(self.check)

    def _changed(self, value: str) -> None:
        self.result = None
        self.error = ""
        self.changed.emit(value)
        self._debounce.start()

    def _start(self, text: str, work) -> None:
        self._token += 1
        self.result = None
        self.error = ""
        self._busy = True
        self.panel.busy(text)
        run_in_background(self._token, work, self._relay)

    def _set_error(self, message: str) -> None:
        """An input that cannot be used at all (missing file, unreadable...)."""
        self._token += 1
        self._busy = False
        self.result = None
        self.error = message
        self.panel.set_entries([], summary_kind="error", summary=html.escape(message), bad=0)
        self.checked.emit()

    def _finished(self, token: int, result) -> None:
        if token != self._token:
            return  # an older check finished after the input changed
        self._busy = False
        if isinstance(result, Exception):
            self.result = None
            self.error = f"LUCI could not read this input ({result.__class__.__name__}: {result})."
            self.panel.set_entries([], summary_kind="error", summary=html.escape(self.error), bad=0)
        else:
            self.result = result
            self.show_result(result)
        self.checked.emit()

    def is_checking(self) -> bool:
        return self._busy or self._debounce.isActive()

    def skip_invalid(self) -> bool:
        # isHidden, not isVisible: a collapsed section must not change the command.
        return not self.panel.skip.isHidden() and self.panel.skip.isChecked()

    def set_skip_invalid(self, value: bool) -> None:
        self.panel.skip.setChecked(bool(value))

    def text(self) -> str:
        return self.edit.text()

    def setText(self, text: str) -> None:
        self.edit.setText(text)

    def problems(self) -> tuple[int, int, str]:
        """(entries with errors, entries in total, a sentence if the input is unusable)."""
        return 0, 0, self.error

    def wait(self, timeout_ms: int = 30000) -> None:
        """Finish a pending or running check (before Run, and in tests)."""
        from PySide6.QtCore import QCoreApplication, QElapsedTimer
        if self._debounce.isActive():
            self._debounce.stop()
            self.check()
        timer = QElapsedTimer()
        timer.start()
        while self._busy and timer.elapsed() < timeout_ms:
            QCoreApplication.processEvents()
            threading.Event().wait(0.01)


class MoleculesInput(_CheckedInput):
    """A molecule CSV (smiles, code_name), read and checked in the background."""

    def __init__(self, mode: InputMode, parent=None):
        super().__init__(mode, parent)
        self.edit = LabeledPath(mode.label, mode.file_filter)
        self.layout_.addWidget(self.edit)
        self.panel = CheckPanel("molecule", ["", "code_name", "Problem", "Line", "SMILES"])
        self.panel.recheck_requested.connect(self.check)
        self.layout_.addWidget(self.panel)
        self.edit.changed.connect(self._changed)

    def check(self) -> None:
        self._debounce.stop()
        path = self.edit.text()
        if not path:
            self._token += 1
            self._busy = False
            self.result = None
            self.error = ""
            self.panel.hide()
            return
        target = Path(path).expanduser()
        if target.is_dir():
            self._set_error(f"{target.name} is a folder; choose the CSV file inside it.")
            return
        if not target.is_file():
            self._set_error(f"{path} does not exist.")
            return
        self._start("Reading the molecules...", lambda: read_molecules(path))

    def show_result(self, molset: MoleculeSet) -> None:
        if not molset.file_ok:
            self.error = molset.summary()
            self.panel.set_entries([], summary_kind="error", summary=fatal_html(molset.issues), bad=0)
            return
        entries = [_MoleculeEntry(r) for r in molset.records]
        counts = molset.counts()
        notes = [i for i in molset.issues if i.level != "error"]
        summary = html.escape(molset.summary())
        if notes:
            summary += f"<br><span style='color:{theme.CREAM_3};font-weight:400'>" + "<br>".join(
                html.escape(i.text()) for i in notes) + "</span>"
        statuses = {r.status for r in molset.records} | {i.level for i in notes}
        kind = "error" if "error" in statuses else "warn" if "warning" in statuses else "ok"
        self.panel.set_entries(entries, summary_kind=kind, summary=summary, bad=counts["error"])

    def problems(self) -> tuple[int, int, str]:
        if self.error:
            return 0, 0, self.error
        molset = self.result
        if not isinstance(molset, MoleculeSet):
            return 0, 0, ""
        counts = molset.counts()
        if counts["total"] == 0:
            return 0, 0, "The CSV has no molecules."
        return counts["error"], counts["total"], ""


class SmilesInput(_CheckedInput):
    """One SMILES and its code_name. Only the name is checked (it names the files)."""

    def __init__(self, mode: InputMode, parent=None, *, with_name: bool = True):
        super().__init__(mode, parent)
        row = QHBoxLayout()
        row.setSpacing(10)
        self.edit = QLineEdit()
        self.edit.setObjectName("smilesEdit")
        self.edit.setPlaceholderText("SMILES, e.g. CC(=O)Oc1ccccc1C(=O)O")
        row.addWidget(self.edit, 3)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("code_name")
        self.name_edit.setToolTip("Name of the output files. Empty: 'molecule'.")
        self.name_edit.setMinimumWidth(120)
        self.name_edit.setMaximumWidth(240)
        self.name_edit.setVisible(with_name)
        row.addWidget(self.name_edit, 1)
        self.layout_.addLayout(row)
        self.note = QLabel()
        self.note.setObjectName("checkDetail")
        self.note.setWordWrap(True)
        self.note.setTextFormat(Qt.RichText)
        self.note.hide()
        self.layout_.addWidget(self.note)
        self.panel = CheckPanel("molecule", [""])  # unused; keeps the shared interface
        self.edit.textChanged.connect(self._typed)
        self.name_edit.textChanged.connect(self._typed)

    def _typed(self, _text: str = "") -> None:
        self.changed.emit(self.edit.text())
        self.check()

    def code_name(self) -> str:
        return "" if self.name_edit.isHidden() else self.name_edit.text().strip()

    def check(self) -> None:
        issues = []
        if self.code_name():
            _, issues = name_issues(self.code_name())
        self.note.setText(issues_html(issues) if issues else "")
        self.note.setVisible(bool(issues))
        self.error = next((i.message for i in issues if i.level == "error"), "")
        self.checked.emit()

    def is_checking(self) -> bool:
        return False

    def wait(self, timeout_ms: int = 30000) -> None:
        self.check()

    def skip_invalid(self) -> bool:
        return False


class StructuresInput(_CheckedInput):
    """A folder of 3D structures: LUCI lists what it will use and what it will convert."""

    def __init__(self, mode: InputMode, parent=None):
        super().__init__(mode, parent)
        self.edit = LabeledPath(mode.label, "", directory=True)
        self.layout_.addWidget(self.edit)
        self.panel = CheckPanel("file", ["", "File", "What LUCI does"])
        self.panel.recheck_requested.connect(self.check)
        self.layout_.addWidget(self.panel)
        self.edit.changed.connect(self._changed)

    def check(self) -> None:
        self._debounce.stop()
        folder = self.edit.text()
        if not folder:
            self._token += 1
            self._busy = False
            self.result = None
            self.error = ""
            self.panel.hide()
            return
        if not Path(folder).expanduser().is_dir():
            self._set_error(f"{folder} is not a folder.")
            return
        self._start("Reading the folder...", lambda: plan_folder(folder))

    def show_result(self, result: FolderResult) -> None:
        if not result.files:
            self.error = result.summary()
            self.panel.set_entries([], summary_kind="error", summary=fatal_html(result.issues), bad=0)
            return
        entries = [_FileEntry(item) for item in result.files]
        notes = [i for i in result.issues if i.level != "info"]
        summary = html.escape(result.summary())
        if result.to_convert():
            summary += (f"<br><span style='color:{theme.CREAM_3};font-weight:400'>Files that are not SDF are "
                        "converted with Open Babel, in the program's environment, when the run "
                        "starts.</span>")
        if notes:
            summary += f"<br><span style='color:{theme.CREAM_3};font-weight:400'>" + "<br>".join(
                html.escape(i.text()) for i in notes) + "</span>"
        statuses = [e.status for e in entries]
        kind = "error" if "error" in statuses else "warn" if "warning" in statuses or notes else "ok"
        self.panel.set_entries(entries, summary_kind=kind, summary=summary, bad=result.counts()["failed"])

    def problems(self) -> tuple[int, int, str]:
        if self.error:
            return 0, 0, self.error
        result = self.result
        if not isinstance(result, FolderResult):
            return 0, 0, ""
        counts = result.counts()
        return counts["failed"], counts["files"], ""


def make_input(mode: InputMode, parent=None) -> _CheckedInput | None:
    """The checked widget for a standard input, or None for a program-specific one."""
    if mode.kind == "molecules":
        return MoleculesInput(mode, parent)
    if mode.kind == "smiles":
        return SmilesInput(mode, parent, with_name=bool(mode.name_flag) or not mode.flag)
    if mode.kind == "structures":
        return StructuresInput(mode, parent)
    return None
