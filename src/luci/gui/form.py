"""The one screen every LUCI program uses.

There is deliberately no per-program form class. A program describes its flags
in :mod:`luci.registry` and this module turns that description into the
version selector, the input section, the option sections, the help
affordances, the command preview and the saved-workflow state. Adding a
program should never mean writing a widget.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFormLayout, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from ..commands import luci_command, luci_input_args, native_args, preview_command
from ..registry import ENV_BY_KEY, InputMode, LayerSpec, OptionSpec, ProgramSpec, Variant
from ..settings import Settings
from .inputs import make_input
from .widgets import (
    DOCS_HELP, GLOB, CollapsibleGroupBox, LabeledPath, PageStack, MultiColumnSelector, NoScrollComboBox,
    advanced_hint, align_labels, directory_destination, form_layout, row_label, transparent,
    with_help,
)

COLUMN_PLACEHOLDER = "Select a column"

# Option names used by earlier LUCI versions, so their saved workflows still load.
LEGACY_OPTIONS = {"aqme_cmin": {"method": "program"}}
# Input types of earlier versions -> (standard input, how the old value maps).
# "parent": the old value was one file and the new input is its folder.
LEGACY_INPUTS = {
    "aqme_csearch": {"smi": ("smiles", ""), "input": ("molecules", ""), "files": ("structures", "parent")},
    "aqme_cmin": {"files": ("structures", "parent"), "folder_sdf": ("structures", "")},
    "aqme_qdescp": {"input": ("molecules", ""), "files": ("structures", ""),
                    "files_xyz": ("structures", ""), "file": ("structures", "parent")},
    "thermomlip": {"csv": ("molecules", "")},
    "thermognn": {"input": ("molecules", "")},
    "dbstep": {"file": ("structures", "parent"), "folder_xyz": ("structures", ""),
               "folder_sdf": ("structures", ""), "folder_log": ("structures", "")},
    "autoqchem": {"smiles_csv": ("molecules", "")},
    "scopebo": {"smiles_csv": ("molecules", "")},
}
# Options of earlier versions that became the code_name of a typed SMILES.
LEGACY_CODE_NAME = {"aqme_csearch": "name", "thermomlip": "mol_id"}


def choice_values(choices: tuple[Any, ...]) -> list[tuple[str, str]]:
    """Normalise ``choices`` into (label, value) pairs."""
    return [c if isinstance(c, tuple) else (c, c) for c in choices]


class PackageForm(QWidget):
    """A program screen built entirely from its :class:`ProgramSpec`."""

    # Emitted when the selected variant changes (the page refreshes its banner).
    variant_changed = Signal(str)

    def __init__(self, module: LayerSpec, package: ProgramSpec, settings: QSettings, parent=None):
        super().__init__(parent)
        self.module = module
        self.package = package
        self.settings = settings
        self.variant_combo = None
        self.widgets: dict[str, QWidget] = {}
        self.rows: dict[str, tuple] = {}
        self.sections: dict[str, CollapsibleGroupBox] = {}
        self.input_widgets: dict[str, QWidget] = {}
        self.destination: LabeledPath | None = None
        self._auto_destination = True
        self._setting_destination = False

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 20, 26, 18)
        root.setSpacing(12)

        self._build_variant(root)
        self._build_input(root)
        self._build_options(root)
        self._build_advanced(root)
        self._build_preview(root)
        root.addStretch(1)

        self._refresh_columns()
        self.update_preview()
        self._label_width = 0
        self._fit_labels()
        for section in self.sections.values():
            # Showing or expanding a section re-shows its rows: re-apply the rules.
            section.content_shown.connect(self._apply_visibility)

    def _fit_labels(self):
        """Row titles take up to 28% of the form, between 110 and 210 px.

        In a narrow window the input section puts its titles above the fields,
        so the input and its check get the full width.
        """
        input_form = getattr(self, "_input_form", None)
        if input_form is not None:
            policy = QFormLayout.WrapAllRows if 0 < self.width() < 700 else QFormLayout.DontWrapRows
            if input_form.rowWrapPolicy() != policy:
                input_form.setRowWrapPolicy(policy)
        width = max(90, min(180, int(self.width() * 0.25))) if self.width() > 200 else 180
        if width != self._label_width:
            self._label_width = width
            align_labels(self, width)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_labels()

    # ------------------------------------------------------------------ build
    def _variants_follow_input(self) -> bool:
        return any(mode.variant for mode in self.package.input_modes)

    def _build_variant(self, root: QVBoxLayout):
        """A version selector, for programs offered in several variants."""
        variants = self.package.variants
        if len(variants) < 2 or self._variants_follow_input():
            return
        box = CollapsibleGroupBox("Method")
        form = form_layout(box)
        self.variant_combo = NoScrollComboBox()
        for variant in variants:
            env = ENV_BY_KEY[variant.env]
            label = variant.label if env.available else f"{variant.label}  (not available yet)"
            self.variant_combo.addItem(label, variant.key)
        help_text = " ".join(f"{v.label}: {v.description}" for v in variants if v.description)
        form.addRow(row_label("Level"), with_help(self.variant_combo, help_text))
        self.variant_combo.currentIndexChanged.connect(self._variant_changed)
        root.addWidget(box)
        self.sections["@variant"] = box

    def current_variant(self) -> Variant:
        if self.variant_combo is not None:
            return self.package.variant(self.variant_combo.currentData())
        mode = self.current_mode()
        if mode is not None and mode.variant:
            return self.package.variant(mode.variant)
        return self.package.variants[0]

    def _variant_changed(self, _index=0):
        self.update_preview()
        self.variant_changed.emit(self.current_variant().key)

    def _build_input(self, root: QVBoxLayout):
        modes = self.package.input_modes
        if not modes and self.package.output != "field":
            self.input_stack = None
            return
        title = "Input" if modes else "Output"
        if modes and self.package.output == "field":
            title = "Input and output"
        box = CollapsibleGroupBox(title)
        form = form_layout(box)
        self._input_form = form
        self.input_combo = None
        self.input_stack = None
        if len(modes) > 1:
            self.input_combo = NoScrollComboBox()
            for mode in modes:
                self.input_combo.addItem(mode.label, mode.key)
            self.input_combo.currentIndexChanged.connect(self._input_mode_changed)
            form.addRow(row_label("Input type"), with_help(self.input_combo, self.package.input_help))
        if modes:
            self.input_stack = PageStack()
            for mode in modes:
                widget = self._input_widget(mode)
                self.input_widgets[mode.key] = widget
                self.input_stack.addWidget(widget)
            # The label stays next to the field, not centred on the check panel below it.
            if len(modes) > 1:
                # The type row already explains the choices; a second button here
                # would only repeat it.
                form.addRow(top_label("Input"), with_help(self.input_stack, ""))
            else:
                form.addRow(top_label("Input"), _top_help(self.input_stack, modes[0].help))
        index = 0
        input_options = self.package.input_options()
        while index < len(input_options):
            run = [input_options[index]]
            index += 1
            while index < len(input_options) and input_options[index].same_row:
                run.append(input_options[index])
                index += 1
            self._add_row(form, run)
        if self.package.output == "field":
            self.destination = LabeledPath("Output directory", "", directory=True)
            self.destination.edit.setPlaceholderText(self._auto_destination_hint())
            self.destination.changed.connect(self._destination_changed)
            form.addRow(row_label("Output directory"), with_help(
                self.destination,
                "Folder where results are written. Defaults to the input's own folder."))
        root.addWidget(box)
        self.sections["@input"] = box

    def _auto_destination_hint(self) -> str:
        return f"Automatic: next to the input, or {self._fallback_destination()}"

    def _fallback_destination(self) -> str:
        """Where results go when the input gives no folder: the last folder used
        with this program (so the rounds of a loop stay together), else the
        default results folder."""
        if self.package.tags.mode == "loop":
            # Rounds of a design campaign stay in the same folder.
            last = self.settings.value(f"last_output/{self.package.key}", "", type=str)
            if last:
                return last
        return str(Settings.load().default_results_dir() / self.package.key)

    def remember_output(self):
        """Called when a run starts: the next run without an input reuses this folder."""
        folder = self.output_dir()
        if folder:
            self.settings.setValue(f"last_output/{self.package.key}", folder)

    def _input_widget(self, mode: InputMode) -> QWidget:
        checked = make_input(mode)
        if checked is not None:
            # LUCI's standard inputs: the field plus a live check of what it holds.
            checked.changed.connect(self._input_changed)
            checked.panel.skip_changed.connect(lambda _on: self.update_preview())
            # A finished check can change the command (--skip-invalid): refresh the preview.
            checked.checked.connect(self.update_preview)
            return _StandardPanel(checked)
        if mode.dialog == "none":
            panel = transparent(QWidget())
            layout = QHBoxLayout(panel)
            layout.setContentsMargins(0, 0, 0, 0)
            note = QLabel("No input file: fill in the options below.")
            note.setObjectName("hint")
            layout.addWidget(note, 1)
            panel.edit = _NoInput()
            return panel
        if mode.dialog == "text":
            panel = transparent(QWidget())
            layout = QHBoxLayout(panel)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(18)
            edit = QLineEdit()
            edit.textChanged.connect(self._input_changed)
            inline = QLabel(mode.label)
            inline.setObjectName("inlineLabel")  # not a row title: keeps its own width
            layout.addWidget(inline)
            layout.addWidget(edit, 1)
            panel.edit = edit
            return panel
        panel = transparent(QWidget())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        picker = LabeledPath(mode.label, mode.file_filter, directory=mode.dialog == "directory")
        picker.changed.connect(self._input_changed)
        layout.addWidget(picker)
        panel.edit = picker
        return panel

    def _build_options(self, root: QVBoxLayout):
        options = list(self.package.options)
        for group in self.package.groups():
            box = CollapsibleGroupBox(group)
            form = form_layout(box)
            index = 0
            members = [o for o in options if o.group == group]
            while index < len(members):
                run = [members[index]]
                index += 1
                while index < len(members) and members[index].same_row:
                    run.append(members[index])
                    index += 1
                self._add_row(form, run)
            root.addWidget(box)
            self.sections[group] = box

    def _add_row(self, form, run: list[OptionSpec]):
        lead = run[0]
        built = [self._make_widget(o) for o in run]
        for option, widget in zip(run, built):
            self.widgets[option.key] = widget
        title = lead.row_label or lead.label
        if any(o.required for o in run):
            title += " *"
        if lead.kind == "multi_choice":
            form.addRow(with_help(built[0], lead.tooltip))
        elif len(run) == 1:
            form.addRow(row_label(title), with_help(built[0], lead.tooltip))
        else:
            paired = QHBoxLayout()
            paired.setSpacing(10)
            for widget in built:
                paired.addWidget(widget, 1)
            form.addRow(row_label(title), with_help(paired, lead.tooltip))
        # The whole row (title, field and "?") is shown or hidden together.
        row = form.rowCount() - 1
        for option in run:
            self.rows[option.key] = (form, row, run)

    def _make_widget(self, option: OptionSpec) -> QWidget:
        if option.kind == "bool":
            widget = QCheckBox()
            widget.setChecked(bool(option.default))
            widget.stateChanged.connect(self.update_preview)
            return widget
        if option.kind == "choice":
            widget = NoScrollComboBox()
            for label, value in choice_values(option.choices):
                widget.addItem(label, value)
            index = widget.findData(option.default)
            widget.setCurrentIndex(index if index >= 0 else 0)
            widget.currentIndexChanged.connect(self.update_preview)
            return widget
        if option.kind == "columns":
            widget = NoScrollComboBox()
            widget.addItem(COLUMN_PLACEHOLDER, "")
            widget.currentIndexChanged.connect(self.update_preview)
            return widget
        if option.kind == "multi_columns":
            widget = MultiColumnSelector()
            widget.selection_changed.connect(self.update_preview)
            return widget
        if option.kind == "multi_choice":
            widget = transparent(QWidget())
            grid = QGridLayout(widget)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setHorizontalSpacing(28)
            grid.setVerticalSpacing(2)
            widget.boxes = {}
            for position, (label, value) in enumerate(choice_values(option.choices)):
                box = QCheckBox(label)
                box.setChecked(value in (option.default or ()))
                box.stateChanged.connect(self.update_preview)
                widget.boxes[value] = box
                grid.addWidget(box, position // 2, position % 2)
            grid.setColumnStretch(1, 1)
            return widget
        if option.kind == "path":
            widget = LabeledPath(option.label, option.file_filter or "All files (*)",
                                 directory=option.directory, save=option.save)
            widget.changed.connect(self.update_preview)
            return widget
        widget = QLineEdit()
        placeholder = option.placeholder
        if option.required and placeholder and not placeholder.startswith("e.g."):
            placeholder = "e.g. " + placeholder  # an example, not a value already filled in
        widget.setPlaceholderText(placeholder)
        widget.textChanged.connect(self.update_preview)
        return widget

    def _build_advanced(self, root: QVBoxLayout):
        box = CollapsibleGroupBox("Advanced flags")
        layout = QVBoxLayout(box)
        self.advanced = QPlainTextEdit()
        self.advanced.setMaximumHeight(90)
        self.advanced.textChanged.connect(self.update_preview)
        layout.addLayout(with_help(self.advanced,
                                   DOCS_HELP.format(name=self.package.name),
                                   url=self.package.docs_url))
        layout.addWidget(advanced_hint())
        root.addWidget(box)

    def _build_preview(self, root: QVBoxLayout):
        box = CollapsibleGroupBox("Command preview")
        layout = QVBoxLayout(box)
        self.preview = QPlainTextEdit()
        self.preview.setObjectName("preview")
        self.preview.setReadOnly(True)
        self.preview.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.preview.setFixedHeight(76)
        layout.addWidget(self.preview)
        copy_row = QHBoxLayout()
        copy_row.addStretch(1)
        copy = QPushButton("Copy command")
        copy.setObjectName("secondaryButton")
        copy.clicked.connect(lambda: QApplication.clipboard().setText(self.preview.toPlainText()))
        copy_row.addWidget(copy)
        layout.addLayout(copy_row)
        root.addWidget(box)

    # ------------------------------------------------------------------ input
    def current_mode(self) -> InputMode | None:
        modes = self.package.input_modes
        if not modes:
            return None
        if self.input_combo is None:
            return modes[0]
        return modes[self.input_combo.currentIndex()]

    def mode_key(self) -> str:
        mode = self.current_mode()
        return mode.key if mode is not None else ""

    def input_value(self) -> str:
        mode = self.current_mode()
        if mode is None:
            return ""
        panel = self.input_widgets[mode.key]
        edit = panel.edit
        return edit.text().strip() if isinstance(edit, QLineEdit) else edit.text()

    def standard_input(self):
        """The checked widget of the selected input, if it is one of LUCI's standard inputs."""
        mode = self.current_mode()
        if mode is None or not mode.kind:
            return None
        return self.input_widgets[mode.key].checked

    def code_name(self) -> str:
        checked = self.standard_input()
        return checked.code_name() if checked is not None and hasattr(checked, "code_name") else ""

    def skip_invalid(self) -> bool:
        checked = self.standard_input()
        return checked.skip_invalid() if checked is not None else False

    def input_args(self) -> list[str]:
        """LUCI options for the selected standard input (--molecules, --molecule...)."""
        return luci_input_args(self.current_mode(), self.input_value(), self.code_name(),
                               self.skip_invalid())

    def _input_mode_changed(self):
        self.input_stack.setCurrentIndex(self.input_combo.currentIndex())
        self._input_changed("")
        if self._variants_follow_input():
            self.variant_changed.emit(self.current_variant().key)

    def _input_changed(self, _value=""):
        self._refresh_columns()
        if self.destination is not None and self._auto_destination:
            mode = self.current_mode()
            value = self.input_value()
            if mode is None or not value or mode.dialog in ("text", "none"):
                target = ""
            elif mode.dialog == "directory":
                folder = Path(value).expanduser()
                if GLOB.intersection(value):
                    folder = folder.parent
                target = str(folder.resolve())
            else:
                target = directory_destination(value)
            self._setting_destination = True
            self.destination.setText(target)
            self._setting_destination = False
        self.update_preview()

    def _destination_changed(self, value: str):
        if not self._setting_destination:
            self._auto_destination = not bool(value.strip())
            if self._auto_destination:
                # Cleared by the user: go back to "next to the input".
                self._input_changed("")
                return
        self.update_preview()

    def refresh_destination_hint(self):
        """Called when Settings change the default results folder."""
        if self.destination is not None:
            self.destination.edit.setPlaceholderText(self._auto_destination_hint())
        self.update_preview()

    def _refresh_columns(self):
        """Offer the input CSV's header to the column pickers, if any exist."""
        column_options = [o for o in self.package.options
                          if o.kind in ("columns", "multi_columns")]
        if not column_options:
            return
        headers: list[str] = []
        path = self.input_value()
        if path:
            try:
                with Path(path).open(newline="", encoding="utf-8-sig") as handle:
                    first = handle.readline()
                try:  # Excel in Spanish/European locales writes ';'
                    dialect = csv.Sniffer().sniff(first, delimiters=",;\t")
                except csv.Error:
                    dialect = csv.excel
                headers = [h.strip() for h in next(csv.reader([first], dialect)) if h.strip()]
            except (OSError, StopIteration, csv.Error, UnicodeDecodeError):
                headers = []
        for option in column_options:
            widget = self.widgets[option.key]
            if option.kind == "multi_columns":
                widget.set_columns(headers)
                continue
            widget.mark_placeholder(True)
            previous = widget.currentData()
            widget.blockSignals(True)
            widget.clear()
            widget.addItem(COLUMN_PLACEHOLDER, "")
            for header in headers:
                widget.addItem(header, header)
            index = widget.findData(previous)
            widget.setCurrentIndex(index if index >= 0 else 0)
            widget.blockSignals(False)
            widget.mark_placeholder(not widget.currentData())

    # ------------------------------------------------------------- visibility
    def _visible(self, option: OptionSpec) -> bool:
        if option.visible_if is None:
            return True
        source, expected = option.visible_if
        if source == "@input":
            current = self.mode_key()
        elif source == "@variant":
            current = self.current_variant().key
        else:
            parent = self.package.option(source)
            if parent is not None and not self._visible(parent):
                return False
            current = self._raw_value(source)
            if current in (None, "") and parent is not None:
                current = parent.default
        wanted = {part.strip() for part in expected.split(",")}
        if isinstance(current, (list, tuple, set)):
            # A multi_choice parent: shown when any of the ticked values matches.
            return bool(wanted & {str(item) for item in current})
        return str(current) in wanted

    def _apply_visibility(self):
        for option in self.package.options:
            if option.key not in self.rows:
                continue
            form, row, run = self.rows[option.key]
            if option is run[0]:
                form.setRowVisible(row, any(self._visible(o) for o in run))
            if len(run) > 1:
                self.widgets[option.key].setVisible(self._visible(option))
        for group in self.package.groups():
            members = [o for o in self.package.options if o.group == group]
            self.sections[group].setVisible(any(self._visible(o) for o in members))

    # ----------------------------------------------------------------- values
    def _raw_value(self, key: str) -> Any:
        widget = self.widgets.get(key)
        option = next((o for o in self.package.options if o.key == key), None)
        if widget is None or option is None:
            return ""
        if option.kind == "bool":
            return widget.isChecked()
        if option.kind in ("choice", "columns"):
            return widget.currentData()
        if option.kind == "multi_columns":
            return widget.selected_values()
        if option.kind == "multi_choice":
            return [value for value, box in widget.boxes.items() if box.isChecked()]
        if option.kind == "path":
            return widget.text()
        return widget.text().strip()

    def values(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for option in self.package.options:
            if not self._visible(option):
                continue
            value = self._raw_value(option.key)
            if option.kind == "bool":
                if bool(value) != bool(option.default):
                    result[option.key] = True if option.flag_only else str(bool(value))
            elif option.kind == "multi_choice":
                if set(value) != set(option.default or ()):
                    result[option.key] = "[" + ",".join(value) + "]"
            elif option.kind == "multi_columns":
                if value:
                    result[option.key] = "[" + ",".join(value) + "]"
            elif value != (option.default or ""):
                if value not in (None, ""):
                    result[option.key] = value
        return result

    def output_dir(self) -> str:
        """The folder results go to: the field, the input's folder, or the fallback."""
        if self.destination is None:
            return ""
        chosen = self.destination.text()
        if chosen:
            return chosen
        return self._fallback_destination()

    def missing_required(self) -> list[str]:
        """Labels of required fields left empty (the run is refused until filled)."""
        missing = []
        mode = self.current_mode()
        if mode is not None and mode.dialog != "none" and not self.input_value():
            missing.append(mode.label)
        for option in self.package.options:
            if option.required and self._visible(option) and self._raw_value(option.key) in ("", None, []):
                missing.append(option.label)
        return missing

    def command(self) -> list[str]:
        variant = self.current_variant()
        native = native_args(
            self.package, variant,
            input_mode=self.current_mode(),
            input_value=self.input_value(),
            values=self.values(),
            advanced=self.advanced.toPlainText(),
        )
        return luci_command(self.module, self.package, native,
                            variant=variant.key, output_dir=self.output_dir(),
                            inputs=self.input_args())

    def update_preview(self):
        self._apply_visibility()
        for option in self.package.options:
            if option.kind == "columns":
                self.widgets[option.key].mark_placeholder(not self.widgets[option.key].currentData())
        text = preview_command(self.command())
        if self.preview.toPlainText() != text:
            self.preview.setPlainText(text)

    # ------------------------------------------------------------------ state
    def reset(self):
        if self.variant_combo is not None:
            self.variant_combo.setCurrentIndex(0)
        if self.input_combo is not None:
            self.input_combo.setCurrentIndex(0)
        for panel in self.input_widgets.values():
            panel.edit.setText("")
            checked = getattr(panel, "checked", None)
            if checked is not None and hasattr(checked, "name_edit"):
                checked.name_edit.setText("")
            if checked is not None:
                checked.set_skip_invalid(False)
        if self.destination is not None:
            self.destination.setText("")
            self._auto_destination = True
        for option in self.package.options:
            widget = self.widgets[option.key]
            if option.kind == "bool":
                widget.setChecked(bool(option.default))
            elif option.kind in ("choice", "columns"):
                index = widget.findData(option.default)
                widget.setCurrentIndex(index if index >= 0 else 0)
            elif option.kind == "multi_columns":
                widget.set_values([])
            elif option.kind == "multi_choice":
                for value, box in widget.boxes.items():
                    box.setChecked(value in (option.default or ()))
            else:
                widget.setText("")
        self.advanced.clear()
        self._refresh_columns()
        self.update_preview()

    def save_state(self) -> dict:
        return {
            "variant": self.current_variant().key,
            "input_mode": self.mode_key(),
            "inputs": {key: panel.edit.text() for key, panel in self.input_widgets.items()},
            "code_name": self.code_name(),
            "skip_invalid": self.skip_invalid(),
            # An automatic folder is not saved: it follows the input when reloaded.
            "destination": (self.destination.text()
                            if self.destination is not None and not self._auto_destination else ""),
            "values": {o.key: self._raw_value(o.key) for o in self.package.options},
            "advanced": self.advanced.toPlainText(),
        }

    def load_state(self, state: dict):
        """Restore a saved form; unknown keys and odd values are ignored, not fatal."""
        state = state if isinstance(state, dict) else {}
        if self.variant_combo is not None:
            index = self.variant_combo.findData(state.get("variant"))
            if index >= 0:
                self.variant_combo.setCurrentIndex(index)
        legacy = LEGACY_INPUTS.get(self.package.key, {})
        mode_key = state.get("input_mode")
        if mode_key in legacy and mode_key not in self.input_widgets:
            mode_key = legacy[mode_key][0]
        if self.input_combo is not None:
            index = self.input_combo.findData(mode_key)
            if index >= 0:
                self.input_combo.setCurrentIndex(index)
        inputs = state.get("inputs") or {}
        modes = {mode.key: mode for mode in self.package.input_modes}
        filled: set[str] = set()
        for key, value in (inputs.items() if isinstance(inputs, dict) else []):
            text = "" if value is None else str(value)
            if key not in self.input_widgets and key in legacy:
                key, how = legacy[key]
                if how == "parent" and text and not Path(text).is_dir():
                    text = str(Path(text).parent)
                if not text or key in filled:
                    continue  # several old inputs map here: keep the first one that was filled
            if text:
                filled.add(key)
            if key in self.input_widgets:
                if modes[key].dialog == "file" and text and Path(text).is_dir():
                    text = ""  # an older LUCI stored a folder where a file is now expected
                self.input_widgets[key].edit.setText(text)
        saved_values = state.get("values") if isinstance(state.get("values"), dict) else {}
        code_name = state.get("code_name") or saved_values.get(LEGACY_CODE_NAME.get(self.package.key, ""), "")
        for panel in self.input_widgets.values():
            checked = getattr(panel, "checked", None)
            if checked is not None and hasattr(checked, "name_edit"):
                checked.name_edit.setText("" if code_name is None else str(code_name))
            if checked is not None:
                checked.set_skip_invalid(state.get("skip_invalid") is True)
        if self.destination is not None:
            destination = state.get("destination") or ""
            destination = destination if isinstance(destination, str) else str(destination)
            self._auto_destination = not destination.strip()
            self.destination.setText(destination)
        self._refresh_columns()
        saved = state.get("values") or {}
        saved = dict(saved) if isinstance(saved, dict) else {}
        for old_key, new_key in LEGACY_OPTIONS.get(self.package.key, {}).items():
            if old_key in saved and new_key not in saved:
                saved[new_key] = saved.pop(old_key)
        for option in self.package.options:
            if option.key not in saved:
                continue
            widget = self.widgets[option.key]
            value = saved[option.key]
            if option.kind == "bool":
                widget.setChecked(bool(value) and value not in ("False", "false", "0"))
            elif option.kind in ("choice", "columns"):
                index = widget.findData(value)
                widget.setCurrentIndex(index if index >= 0 else 0)
            elif option.kind == "multi_columns":
                widget.set_values(value if isinstance(value, (list, str)) else [])
            elif option.kind == "multi_choice":
                chosen = value if isinstance(value, (list, tuple)) else ()
                for name, box in widget.boxes.items():
                    box.setChecked(name in chosen)
            else:
                widget.setText("" if value is None else str(value))
        advanced = state.get("advanced") or ""
        self.advanced.setPlainText(advanced if isinstance(advanced, str) else str(advanced))
        self.update_preview()


def top_label(text: str) -> QWidget:
    """A row title that stays level with the first line of a tall field."""
    holder = transparent(QWidget())
    layout = QVBoxLayout(holder)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    label = row_label(text)
    label.setSizePolicy(label.sizePolicy().horizontalPolicy(), QSizePolicy.Fixed)
    layout.addWidget(label)
    layout.addStretch(1)
    holder.label = label
    return holder


def _top_help(field: QWidget, text: str):
    """with_help, with the '?' level with the first line instead of centred."""
    row = with_help(field, text)
    for index in range(row.count()):
        item = row.itemAt(index)
        if item.widget() is not None and item.widget() is not field:
            row.setAlignment(item.widget(), Qt.AlignTop)
    return row


class _StandardPanel(QWidget):
    """Stack page holding a checked standard input; ``edit`` is its main field."""

    def __init__(self, checked):
        super().__init__()
        transparent(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(checked)
        self.checked = checked
        self.edit = checked


class _NoInput:
    """Stands in for an input field when the selected input needs no file."""

    def text(self) -> str:
        return ""

    def setText(self, _text: str):
        pass
