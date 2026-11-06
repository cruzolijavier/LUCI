"""The LUCI main window.

This file owns navigation only: the layer list, the "what do you have?"
filter, the program cards and the window chrome. Program screens are built
from the registry by ``luci.gui.form``, wrapped by ``luci.gui.package_base``;
the look lives in ``luci.gui.theme`` and the shared fields in
``luci.gui.widgets``.
"""

from __future__ import annotations

import ctypes
import json
from pathlib import Path
import re
import sys

from PySide6.QtCore import QPointF, QRectF, QSettings, QSize, Qt, QUrl, Signal
from PySide6.QtGui import (
    QAction, QCloseEvent, QColor, QDesktopServices, QFont, QIcon, QPainter, QPainterPath, QPalette, QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPushButton, QScrollArea, QSizePolicy, QStackedWidget, QStatusBar,
    QToolButton, QVBoxLayout, QWidget,
)

from .. import __version__, updater
from ..envs.manager import EnvManager
from ..settings import luci_home
from ..registry import (
    ENV_BY_KEY, INPUT_HELP, LEGACY_LAYER_DEFAULT, INPUT_LABELS, LAYERS, MODE_LABELS, LayerSpec,
    ProgramSpec, layer as find_layer, matches_inputs, program as find_program,
    programs_in,
)
from .dialogs import (
    EnvironmentsDialog, ProcessDialog, SettingsDialog, env_state, luci_cli, uninstall_environment,
)
from .form import PackageForm
from .package_base import PackagePage
from . import theme, updater_ui
from .theme import ORANGE_STYLE, application_icon, load_fonts, logo_path, symbol_path
from .widgets import FlowLayout, chip, repolish, status_pill

WIDE = 1180
STATE_ORDER = {"ok": 0, "update": 1, "missing": 2, "blocked": 3, "pending": 4}
STATE_TEXT = {"ok": "Installed", "missing": "Not installed", "update": "Update available",
              "blocked": "Not for this system", "pending": "Coming soon"}  # legend of the home page


def program_state(spec: ProgramSpec, manager: EnvManager) -> tuple[str, str]:
    """(text, state) of a program: as installable as its best variant."""
    states = [env_state(manager, v.env) for v in spec.variants]
    return min(states, key=lambda item: STATE_ORDER[item[1]])


# ---------------------------------------------------------------------------
# Landing page of a layer
# ---------------------------------------------------------------------------
class ProgramCard(QFrame):
    """One program on a layer page: what it does, its tags and its state."""

    open_requested = Signal(str)
    install_requested = Signal(str)
    uninstall_requested = Signal(str)

    def __init__(self, spec: ProgramSpec, parent=None):
        super().__init__(parent)
        self.spec = spec
        self.setObjectName("programCard")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(10)
        title = QLabel(spec.name)
        title.setObjectName("cardTitle")
        top.addWidget(title)
        self.pill = status_pill("", "missing")
        top.addWidget(self.pill, 0, Qt.AlignVCenter)
        top.addStretch(1)
        layout.addLayout(top)

        body = QLabel(spec.description)
        body.setObjectName("cardBody")
        body.setWordWrap(True)
        layout.addWidget(body)

        tags = QWidget()
        tags.setObjectName("formPanel")
        flow = FlowLayout(tags, spacing=6)
        if spec.tags.inputs:
            for kind in spec.tags.inputs:
                flow.addWidget(chip(INPUT_LABELS[kind], "input", INPUT_HELP[kind]))
        else:
            flow.addWidget(chip("No input file", "input", "Builds from names and options only."))
        # Cost and systems are not shown: a program that cannot run on this
        # computer says so in red in its status pill, and that is enough.
        if spec.tags.mode == "loop":
            flow.addWidget(chip(MODE_LABELS["loop"], "loop",
                                "Run, measure in the lab, add the results, run again."))
        layout.addWidget(tags)

        self.note = QLabel()
        self.note.setObjectName("cardNote")
        self.note.setWordWrap(True)
        layout.addWidget(self.note)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        self.open_button = QPushButton("Open")
        self.open_button.setObjectName("primaryButton")
        self.open_button.setCursor(Qt.PointingHandCursor)
        self.open_button.clicked.connect(lambda: self.open_requested.emit(spec.key))
        buttons.addWidget(self.open_button)
        self.install_button = QPushButton("Install")
        self.install_button.setObjectName("secondaryButton")
        self.install_button.setCursor(Qt.PointingHandCursor)
        self.install_button.clicked.connect(lambda: self.install_requested.emit(spec.key))
        buttons.addWidget(self.install_button)
        self.uninstall_button = QPushButton("Uninstall")
        self.uninstall_button.setObjectName("secondaryButton")
        self.uninstall_button.setCursor(Qt.PointingHandCursor)
        self.uninstall_button.setToolTip("Delete this program's environment to free disk space.")
        self.uninstall_button.clicked.connect(lambda: self.uninstall_requested.emit(spec.key))
        buttons.addWidget(self.uninstall_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        self.refresh()

    def refresh(self, manager: EnvManager | None = None):
        manager = manager or EnvManager()
        # A program is as installable as its best variant.
        text, state = program_state(self.spec, manager)
        self.pill.setText(text)
        self.pill.setProperty("state", state)
        repolish(self.pill)
        self.install_button.setVisible(state in ("missing", "update"))
        self.uninstall_button.setVisible(any(manager.is_installed(v.env) for v in self.spec.variants))
        self.install_button.setText("Update" if state == "update" else "Install")
        # Only "coming soon" needs a sentence on the card; a program for another
        # system is already marked by its red pill (its page explains why).
        env_notes = []
        for variant in self.spec.variants:
            note = ENV_BY_KEY[variant.env].note
            if note and note not in env_notes and state == "pending":
                env_notes.append(note)
        self.note.setText(" ".join(env_notes))
        self.note.setVisible(bool(env_notes))


class LayerLandingPage(QWidget):
    """Program cards of one layer, filtered by what the user has."""

    package_selected = Signal(str)
    install_requested = Signal(str)
    uninstall_requested = Signal(str)
    show_all_requested = Signal()

    def __init__(self, spec: LayerSpec, parent=None):
        super().__init__(parent)
        self.spec = spec
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 18, 28, 22)
        root.setSpacing(14)
        title = QLabel(spec.title)
        title.setObjectName("pageTitle")
        subtitle = QLabel(spec.description)
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)
        self.cards: list[ProgramCard] = []
        for index, program_spec in enumerate(programs_in(spec.key)):
            card = ProgramCard(program_spec)
            card.setProperty("alt", "true" if index % 2 else "false")
            card.open_requested.connect(self.package_selected.emit)
            card.install_requested.connect(self.install_requested.emit)
            card.uninstall_requested.connect(self.uninstall_requested.emit)
            card.setMaximumWidth(980)
            self.cards.append(card)
            root.addWidget(card)
        hidden_row = QHBoxLayout()
        self.hidden_note = QLabel()
        self.hidden_note.setObjectName("hiddenNote")
        hidden_row.addWidget(self.hidden_note)
        self.show_all = QToolButton()
        self.show_all.setObjectName("clearFilter")
        self.show_all.setText("Show all")
        self.show_all.setCursor(Qt.PointingHandCursor)
        self.show_all.clicked.connect(self.show_all_requested.emit)
        hidden_row.addWidget(self.show_all)
        hidden_row.addStretch(1)
        root.addLayout(hidden_row)
        root.addStretch(1)
        self.apply_filter(set())

    def apply_filter(self, have: set[str]) -> int:
        shown = 0
        for card in self.cards:
            visible = matches_inputs(card.spec, have)
            card.setVisible(visible)
            shown += visible
        hidden = len(self.cards) - shown
        self.hidden_note.setText(
            f"{hidden} program{'s' if hidden != 1 else ''} hidden: "
            f"{'they need' if hidden != 1 else 'it needs'} other inputs." if hidden else "")
        self.hidden_note.setVisible(bool(hidden))
        self.show_all.setVisible(bool(hidden))
        return shown

    def refresh(self):
        manager = EnvManager()
        for card in self.cards:
            card.refresh(manager)


# ---------------------------------------------------------------------------
# Home: "Choose a layer"
# ---------------------------------------------------------------------------
class LogoButton(QLabel):
    """The LUCI logo; a click goes back to the home page."""

    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Home")

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)


def scaled_logo(width: int) -> QPixmap:
    """The logo at ``width`` logical pixels, sharp on high-DPI screens."""
    source = QPixmap(str(logo_path())) if logo_path().is_file() else QPixmap()
    if source.isNull():
        return source
    screen = QApplication.primaryScreen()
    ratio = screen.devicePixelRatio() if screen else 1.0
    pixmap = source.scaledToWidth(int(width * max(1.0, ratio)), Qt.SmoothTransformation)
    pixmap.setDevicePixelRatio(max(1.0, ratio))
    return pixmap


def _norm(text: str) -> str:
    """Lower case with only letters and digits: 'AQME-CSEARCH' and 'AQME CSEARCH' compare equal."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def search_programs(query: str) -> list[ProgramSpec]:
    """Programs matching ``query`` (name, key, old names, layer or description), best matches first."""
    flat = _norm(query)
    tokens = [t for t in re.split(r"[^a-z0-9]+", query.lower()) if t]
    if not flat:
        return []
    found: list[tuple[int, int, ProgramSpec]] = []
    for order, spec in enumerate(p for layer in LAYERS for p in programs_in(layer.key)):
        layer_title = find_layer(spec.layer).title
        names = [_norm(spec.name), _norm(spec.key)] + [_norm(k) for k in spec.legacy_keys]
        haystack = _norm(" ".join([spec.name, spec.key, layer_title, spec.description, *spec.legacy_keys]))
        if flat in names:
            rank = 0
        elif any(name.startswith(flat) for name in names):
            rank = 1
        elif any(flat in name for name in names):
            rank = 2
        elif tokens and all(t in haystack for t in tokens):
            rank = 3
        else:
            continue
        found.append((rank, order, spec))
    return [spec for _, _, spec in sorted(found, key=lambda item: item[:2])]


class LayerCard(QFrame):
    """One layer on the home page: what it gives, its programs and a button to open it."""

    open_layer = Signal(str)
    open_program = Signal(str)

    def __init__(self, spec: LayerSpec, alt: bool, parent=None):
        super().__init__(parent)
        self.spec = spec
        self.setObjectName("layerCard")
        self.setProperty("alt", "true" if alt else "false")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)
        top = QHBoxLayout()
        top.setSpacing(12)
        title = QLabel(spec.title)
        title.setObjectName("cardTitle")
        top.addWidget(title)
        programs = programs_in(spec.key)
        count = QLabel(f"{len(programs)} program{'s' if len(programs) != 1 else ''}")
        count.setObjectName("cardNote")
        top.addWidget(count, 0, Qt.AlignVCenter)
        top.addStretch(1)
        layout.addLayout(top)
        body = QLabel(spec.description)
        body.setObjectName("cardBody")
        body.setWordWrap(True)
        layout.addWidget(body)
        holder = QWidget()
        holder.setObjectName("formPanel")
        flow = FlowLayout(holder, spacing=8)
        self.chips: dict[str, QPushButton] = {}
        for program_spec in programs:
            button = QPushButton(program_spec.name)
            button.setObjectName("programChip")
            button.setCursor(Qt.PointingHandCursor)
            button.setToolTip(program_spec.description)
            button.clicked.connect(lambda _=False, key=program_spec.key: self.open_program.emit(key))
            flow.addWidget(button)
            self.chips[program_spec.key] = button
        layout.addWidget(holder)
        layout.addStretch(1)
        # The whole card opens the layer (the program chips keep opening their program).
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(f"Open {spec.title}")

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.position().toPoint()):
            self.open_layer.emit(self.spec.key)
        super().mouseReleaseEvent(event)

    def refresh(self, manager: EnvManager):
        for key, button in self.chips.items():
            text, state = program_state(find_program(key), manager)
            button.setProperty("state", state)
            button.setToolTip(f"{text} - {find_program(key).description}")
            repolish(button)


class HomePage(QWidget):
    """First screen: the logo and the six layers, each with its programs."""

    layer_requested = Signal(str)
    program_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 30, 36, 30)
        root.setSpacing(18)
        hero = QHBoxLayout()
        hero.setSpacing(30)
        self.logo = QLabel()
        self.logo.setObjectName("logo")
        pixmap = scaled_logo(200)
        if not pixmap.isNull():
            self.logo.setPixmap(pixmap)
        hero.addWidget(self.logo, 0, Qt.AlignVCenter)
        texts = QVBoxLayout()
        texts.setSpacing(8)
        texts.addStretch(1)
        title = QLabel("Choose a layer")
        title.setObjectName("heroTitle")
        texts.addWidget(title)
        sub = QLabel("Each layer is one step of the workflow. Open a layer to see its programs, "
                     "or go straight to one.")
        sub.setObjectName("pageSubtitle")
        sub.setWordWrap(True)
        texts.addWidget(sub)
        self.search = QLineEdit()
        self.search.setObjectName("homeSearch")
        self.search.setPlaceholderText("Search a program, e.g. AQME-CSEARCH")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumHeight(38)
        self.search.setMaximumWidth(520)
        self.search.textChanged.connect(self._search_changed)
        self.search.returnPressed.connect(self._open_first_match)
        texts.addWidget(self.search)
        texts.addStretch(1)
        hero.addLayout(texts, 1)
        root.addLayout(hero)
        # Search results (replace the layer cards while there is a query).
        self.results = QWidget()
        self.results.setObjectName("formPanel")
        results_layout = QVBoxLayout(self.results)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.setSpacing(10)
        self.results_note = QLabel("")
        self.results_note.setObjectName("pageSubtitle")
        results_layout.addWidget(self.results_note)
        results_holder = QWidget()
        results_holder.setObjectName("formPanel")
        self.results_flow = FlowLayout(results_holder, spacing=8)
        results_layout.addWidget(results_holder)
        self.results.hide()
        self._matches: list[ProgramSpec] = []
        root.addWidget(self.results)
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(18)
        self.grid.setVerticalSpacing(18)
        self.cards: list[LayerCard] = []
        for index, spec in enumerate(LAYERS):
            card = LayerCard(spec, alt=bool(index % 2))
            card.open_layer.connect(self.layer_requested.emit)
            card.open_program.connect(self.program_requested.emit)
            self.cards.append(card)
        self._columns = 0
        self._arrange(2)
        self.grid_holder = QWidget()
        self.grid_holder.setObjectName("formPanel")
        self.grid_holder.setLayout(self.grid)
        root.addWidget(self.grid_holder)
        legend_holder = QWidget()
        legend_holder.setObjectName("formPanel")
        legend = FlowLayout(legend_holder, spacing=6)
        for state, text in STATE_TEXT.items():
            legend.addWidget(status_pill(text, state))
        root.addWidget(legend_holder)
        root.addStretch(1)

    def _arrange(self, columns: int):
        if columns == self._columns:
            return
        self._columns = columns
        for card in self.cards:
            self.grid.removeWidget(card)
        for index, card in enumerate(self.cards):
            self.grid.addWidget(card, index // columns, index % columns)
        for column in range(2):
            self.grid.setColumnStretch(column, 1 if column < columns else 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._arrange(2 if self.width() >= 900 else 1)

    # ---------------------------------------------------------------- search
    def _search_changed(self, text: str):
        self._matches = search_programs(text)
        searching = bool(_norm(text))
        self.grid_holder.setVisible(not searching)
        self.results.setVisible(searching)
        while self.results_flow.count():
            item = self.results_flow.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        if not searching:
            return
        manager = EnvManager()
        for spec in self._matches:
            button = QPushButton(f"{spec.name}  \u00b7  {find_layer(spec.layer).title}")
            button.setObjectName("programChip")
            button.setCursor(Qt.PointingHandCursor)
            status, state = program_state(spec, manager)
            button.setProperty("state", state)
            button.setToolTip(f"{status} - {spec.description}")
            button.clicked.connect(lambda _=False, key=spec.key: self.program_requested.emit(key))
            self.results_flow.addWidget(button)
        count = len(self._matches)
        self.results_note.setText(
            f"{count} program{'s' if count != 1 else ''} found. Press Enter to open the first one."
            if count else "No program matches your search.")

    def _open_first_match(self):
        if self._matches:
            self.program_requested.emit(self._matches[0].key)

    def clear_search(self):
        self.search.clear()

    def refresh(self):
        manager = EnvManager()
        for card in self.cards:
            card.refresh(manager)
        if self.search.text():
            self._search_changed(self.search.text())


class LayerWorkspace(QWidget):
    """One layer: its landing page plus a screen per program."""

    page_changed = Signal(bool)

    def __init__(self, spec: LayerSpec, settings: QSettings, parent=None):
        super().__init__(parent)
        self.spec = spec
        self.settings = settings
        self.pages: dict[str, PackagePage] = {}
        self.package_key: str | None = None
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        self.landing = LayerLandingPage(spec)
        self.landing.package_selected.connect(self.select_package)
        landing_scroll = QScrollArea()
        landing_scroll.setWidgetResizable(True)
        landing_scroll.setFrameShape(QFrame.NoFrame)
        landing_scroll.setWidget(self.landing)
        self.stack.addWidget(landing_scroll)
        for program_spec in programs_in(spec.key):
            page = PackagePage(PackageForm(spec, program_spec, settings))
            page.back_requested.connect(self.go_home)
            page.environments_changed.connect(self.refresh)
            self.pages[program_spec.key] = page
            self.stack.addWidget(page)
        root.addWidget(self.stack)

    def select_package(self, key: str):
        """Open a program, accepting the names used by LUCI 0.1 workflows."""
        if key not in self.pages:
            try:
                key = find_program(key).key
            except KeyError:
                return
        if key in self.pages:
            self.package_key = key
            self.pages[key].refresh_status()
            self.stack.setCurrentIndex(1 + list(self.pages).index(key))
            self.page_changed.emit(True)

    def go_home(self):
        self.package_key = None
        self.landing.refresh()
        self.stack.setCurrentIndex(0)
        self.page_changed.emit(False)

    def refresh(self):
        self.landing.refresh()
        for page in self.pages.values():
            page.refresh_status()

    def has_package(self) -> bool:
        return self.stack.currentIndex() != 0 and self.package_key is not None

    def current_package(self) -> PackagePage | None:
        return self.pages[self.package_key] if self.has_package() else None

    def current_form(self) -> PackageForm | None:
        page = self.current_package()
        return page.form if page is not None else None

    def command(self) -> list[str]:
        page = self.current_package()
        return page.command() if page is not None else []

    def running_pages(self) -> list[PackagePage]:
        return [page for page in self.pages.values() if page.is_running()]

    def reset(self):
        self.go_home()
        for page in self.pages.values():
            page.reset()

    def save_state(self) -> dict:
        page = self.current_package()
        return {"program": self.package_key, "form": page.save_state() if page else {}}

    def load_state(self, state: dict):
        key = state.get("program") or state.get("backend")
        if not key:
            self.go_home()
            return
        self.select_package(key)
        page = self.current_package()
        if page is not None:
            page.load_state(state.get("form", {}))
        else:
            self.go_home()


# ---------------------------------------------------------------------------
# Window chrome
# ---------------------------------------------------------------------------
class FilterBar(QFrame):
    """"What do you have?" toggles shared by every layer."""

    changed = Signal(set)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("filterBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(32, 14, 32, 14)
        layout.setSpacing(16)
        texts = QWidget()
        texts.setObjectName("formPanel")
        text_layout = QVBoxLayout(texts)
        text_layout.setContentsMargins(0, 0, 8, 0)
        text_layout.setSpacing(1)
        label = QLabel("What do you have?")
        label.setObjectName("filterLabel")
        text_layout.addWidget(label)
        sub = QLabel("Select your data; programs that don't fit are hidden")
        sub.setObjectName("filterSub")
        self.sub = sub
        text_layout.addWidget(sub)
        layout.addWidget(texts, 0, Qt.AlignVCenter)
        holder = QWidget()
        holder.setObjectName("formPanel")
        flow = FlowLayout(holder, spacing=8)
        self.buttons: dict[str, QToolButton] = {}
        for key, text in INPUT_LABELS.items():
            button = QToolButton()
            button.setObjectName("filterChip")
            button.setText(text)
            button.setToolTip(INPUT_HELP[key])
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.toggled.connect(self._emit)
            flow.addWidget(button)
            self.buttons[key] = button
        self.clear_button = QToolButton()
        self.clear_button.setObjectName("clearFilter")
        self.clear_button.setText("Clear")
        self.clear_button.setCursor(Qt.PointingHandCursor)
        self.clear_button.clicked.connect(self.clear)
        flow.addWidget(self.clear_button)
        holder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(holder, 1)
        self._emit()

    def set_compact(self, compact: bool):
        """On narrow windows the chips need the room more than the explanation."""
        if self.sub.isVisibleTo(self) == compact:
            self.sub.setVisible(not compact)
            for button in self.buttons.values():
                button.setProperty("compact", "true" if compact else "false")
                repolish(button)
            self.layout().setContentsMargins(28 if compact else 32, 8 if compact else 14,
                                             28 if compact else 32, 8 if compact else 14)
            self.layout().invalidate()
            self.updateGeometry()

    def selected(self) -> set[str]:
        return {key for key, button in self.buttons.items() if button.isChecked()}

    def clear(self):
        for button in self.buttons.values():
            button.blockSignals(True)
            button.setChecked(False)
            button.blockSignals(False)
        self._emit()

    def _emit(self, *_):
        self.clear_button.setVisible(bool(self.selected()))
        self.changed.emit(self.selected())


class NavItem(QWidget):
    """Sidebar entry: layer title and what it delivers, drawn as a hexagonal tab on a timeline.

    Flat colours only (no glow): the selected layer is filled orange and shifted
    to the right, the others are outlined and move a little on hover.
    """

    GUTTER = 22      # room for the timeline and its dot
    SLANT = 12       # width of the pointed ends
    SHIFT_SELECTED = 14
    SHIFT_HOVER = 7

    def __init__(self, spec: LayerSpec, parent=None):
        super().__init__(parent)
        self.setObjectName("navItem")
        self.setAttribute(Qt.WA_Hover, True)
        self._selected = False
        self._hover = False
        self._compact = False
        self.first = False
        self.last = False
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        self.title = QLabel(spec.title)
        self.title.setObjectName("navTitle")
        self.caption = QLabel(spec.delivers)
        self.caption.setObjectName("navCaption")
        layout.addWidget(self.title)
        layout.addWidget(self.caption)
        self.setToolTip(spec.description)
        self._apply_margins()

    def _shift(self) -> int:
        return self.SHIFT_SELECTED if self._selected else (self.SHIFT_HOVER if self._hover else 0)

    def _apply_margins(self):
        vertical = 9 if self._compact else 15
        left = self.GUTTER + self._shift() + self.SLANT + 10
        self.layout().setContentsMargins(left, vertical, self.SLANT + 12, vertical)
        self.layout().setSpacing(0 if self._compact else 2)

    def set_compact(self, compact: bool):
        self._compact = compact
        self._apply_margins()

    def set_state(self, selected: bool, dimmed: bool, caption: str):
        self.caption.setText(caption)
        self._selected = selected
        for label in (self.title, self.caption):
            label.setProperty("selected", "true" if selected else "false")
            label.setProperty("dimmed", "true" if dimmed and not selected else "false")
            repolish(label)
        self._apply_margins()
        self.update()

    def enterEvent(self, event):
        self._hover = True
        self._apply_margins()
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._apply_margins()
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        mid = h / 2
        line_x = 6.5
        # Timeline: continuous from the first dot to the last one.
        p.setPen(QPen(QColor(theme.ORANGE), 1))
        p.drawLine(QPointF(line_x, mid if self.first else 0), QPointF(line_x, mid if self.last else h))
        # Hexagonal tab.
        inset = 3 if self._compact else 5
        x0 = self.GUTTER + self._shift() + 0.5
        x1 = w - 8 - (self.SHIFT_SELECTED - self._shift()) - 0.5
        top, bottom = inset + 0.5, h - inset - 0.5
        path = QPainterPath()
        path.moveTo(x0, mid)
        path.lineTo(x0 + self.SLANT, top)
        path.lineTo(x1 - self.SLANT, top)
        path.lineTo(x1, mid)
        path.lineTo(x1 - self.SLANT, bottom)
        path.lineTo(x0 + self.SLANT, bottom)
        path.closeSubpath()
        if self._selected:
            p.setPen(QPen(QColor(theme.ORANGE), 1))
            p.setBrush(QColor(theme.ORANGE))
        else:
            p.setPen(QPen(QColor(theme.ORANGE if self._hover else theme.LINE_2), 1))
            p.setBrush(QColor(theme.BLACK))
        p.drawPath(path)
        # Dot on the timeline.
        p.setPen(QPen(QColor(theme.ORANGE), 1.5))
        p.setBrush(QColor(theme.ORANGE if self._selected else theme.BLACK))
        p.drawEllipse(QPointF(line_x, mid), 4.5, 4.5)
        p.end()


CONTACT_EMAIL = "javier.cruz.oliver@gmail.com"


def envelope_icon(colour: str, size: int = 20) -> QIcon:
    """A small envelope drawn with the painter (no font or image file needed)."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor(colour), 2.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)
    w = size * 2
    box = QRectF(w * 0.08, w * 0.22, w * 0.84, w * 0.56)
    p.drawRoundedRect(box, 3, 3)
    flap = QPainterPath()
    flap.moveTo(box.left() + 1, box.top() + 1)
    flap.lineTo(box.center().x(), box.center().y() + w * 0.04)
    flap.lineTo(box.right() - 1, box.top() + 1)
    p.drawPath(flap)
    p.end()
    pixmap.setDevicePixelRatio(2.0)
    return QIcon(pixmap)


class MainWindow(QMainWindow):
    # True on the home page ("Choose a layer"), False on a layer or a program.
    home_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        load_fonts()
        self.setWindowTitle("LUCI - Layered Unified Computational Interfaces")
        self.resize(1280, 820)
        self.setMinimumSize(760, 440)
        # Window state lives next to the rest of LUCI's data (and follows LUCI_HOME).
        self.settings = QSettings(str(luci_home() / "gui.ini"), QSettings.IniFormat)
        if symbol_path().is_file():
            self.setWindowIcon(application_icon())
        self.workspaces: dict[str, LayerWorkspace] = {}
        self.nav_items: list[NavItem] = []
        self._logo_size = 0
        self._home = False
        self._build_menu()
        self._build_ui()
        self.setStyleSheet(ORANGE_STYLE)
        app = QApplication.instance()
        if app is not None:
            app.setFont(QFont(theme.BODY_FONT, 10))
        # The assistant (robot at the bottom right); LUCI works the same without it.
        from ..assistant import install_assistant
        install_assistant(self)

    # ----------------------------------------------------------------- build
    def _build_menu(self):
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(QAction("Save workflow...", self, triggered=self.save_workflow))
        file_menu.addAction(QAction("Load workflow...", self, triggered=self.load_workflow))
        file_menu.addSeparator()
        file_menu.addAction(QAction("Exit", self, triggered=self.close))
        tools = self.menuBar().addMenu("Tools")
        tools.addAction(QAction("Environments...", self, triggered=self.open_environments))
        tools.addAction(QAction("Settings...", self, triggered=self.open_settings))
        help_menu = self.menuBar().addMenu("Help")
        # "Update LUCI" at the right of the menu bar (a red "!" when a new version is waiting).
        self.update_button = None
        if updater_ui.enabled():
            self.update_button = updater_ui.UpdateButton(self)
            self.menuBar().setCornerWidget(self.update_button, Qt.TopRightCorner)
            help_menu.addAction(QAction("Check for updates...", self,
                                        triggered=lambda: self.update_button.check(silent=False)))
        help_menu.addAction(QAction("About LUCI", self, triggered=self.about))

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        side = QVBoxLayout(self.sidebar)
        side.setContentsMargins(14, 18, 10, 14)
        side.setSpacing(6)
        self.logo = LogoButton()
        self.logo.setObjectName("logo")
        self.logo.setAlignment(Qt.AlignCenter)
        self.logo.clicked.connect(self.show_home)
        self._logo_pixmap = QPixmap(str(logo_path())) if logo_path().is_file() else QPixmap()
        side.addWidget(self.logo, 0, Qt.AlignHCenter)
        self.home_button = QPushButton("\u2190  Home")
        self.home_button.setObjectName("secondaryButton")
        self.home_button.setCursor(Qt.PointingHandCursor)
        self.home_button.setToolTip("Back to the main hub (Choose a layer)")
        self.home_button.clicked.connect(self.show_home)
        side.addWidget(self.home_button)
        side.addSpacing(8)

        self.layer_list = QListWidget()
        self.layer_list.setObjectName("layerList")
        self.layer_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.layer_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        for index, spec in enumerate(LAYERS):
            item = QListWidgetItem()
            item.setData(Qt.UserRole, spec.key)
            nav = NavItem(spec)
            nav.first, nav.last = index == 0, index == len(LAYERS) - 1
            nav.setStyleSheet(ORANGE_STYLE)
            nav.ensurePolished()
            item.setSizeHint(QSize(10, nav.sizeHint().height()))
            self.layer_list.addItem(item)
            self.layer_list.setItemWidget(item, nav)
            self.nav_items.append(nav)
        self.layer_list.currentRowChanged.connect(self.select_layer)
        self.layer_list.setSpacing(0)
        self.layer_list.setFrameShape(QFrame.NoFrame)
        side.addWidget(self.layer_list, 1)
        # Footer: documentation link (not published yet), contact and the running version.
        footer = QHBoxLayout()
        footer.setContentsMargins(4, 4, 0, 0)
        footer.setSpacing(8)
        docs = QLabel("Documentation link (coming soon)")
        docs.setObjectName("sidebarFooter")
        docs.setWordWrap(True)
        docs.setToolTip("The documentation does not exist yet")
        footer.addWidget(docs, 1)
        mail = QToolButton()
        mail.setObjectName("mailButton")
        mail.setIcon(envelope_icon(theme.CREAM))
        mail.setIconSize(QSize(20, 20))
        mail.setCursor(Qt.PointingHandCursor)
        mail.setToolTip(f"Contact: {CONTACT_EMAIL}")
        mail.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(f"mailto:{CONTACT_EMAIL}")))
        footer.addWidget(mail, 0, Qt.AlignVCenter)
        version = QLabel(f"v{__version__}")
        version.setObjectName("sidebarFooter")
        footer.addWidget(version, 0, Qt.AlignVCenter)
        side.addLayout(footer)
        outer.addWidget(self.sidebar)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        self.filter_bar = FilterBar()
        self.filter_bar.changed.connect(self.apply_filter)
        right_layout.addWidget(self.filter_bar)
        self.stack = QStackedWidget()
        for spec in LAYERS:
            workspace = LayerWorkspace(spec, self.settings)
            workspace.page_changed.connect(self._page_changed)
            workspace.landing.install_requested.connect(self.install_program)
            workspace.landing.uninstall_requested.connect(self.uninstall_program)
            workspace.landing.show_all_requested.connect(self.filter_bar.clear)
            self.workspaces[spec.key] = workspace
            self.stack.addWidget(workspace)
        right_layout.addWidget(self.stack, 1)
        self.home = HomePage()
        self.home.layer_requested.connect(self.open_layer)
        self.home.program_requested.connect(self.open_program)
        self.home_scroll = QScrollArea()
        self.home_scroll.setWidgetResizable(True)
        self.home_scroll.setFrameShape(QFrame.NoFrame)
        self.home_scroll.setWidget(self.home)
        self.home_scroll.hide()
        right_layout.addWidget(self.home_scroll, 1)
        outer.addWidget(right, 1)

        self.setStatusBar(QStatusBar())
        self._fit_sidebar()
        self.layer_list.setCurrentRow(0)
        self.apply_filter(set())

    # ------------------------------------------------------------- behaviour
    def _fit_sidebar(self):
        """A narrower sidebar and logo on small windows, so forms keep their room."""
        wide = self.width() >= WIDE
        narrow = self.width() < 900
        if hasattr(self, "filter_bar"):
            self.filter_bar.set_compact(self.width() < 1240)
        self.sidebar.setFixedWidth(290 if wide else (212 if narrow else 236))
        compact = self.height() < 620
        if compact != getattr(self, "_compact", None):
            self._compact = compact
            for row, nav in enumerate(self.nav_items):
                nav.set_compact(compact)
                self.layer_list.item(row).setSizeHint(QSize(10, nav.sizeHint().height()))
        if self.height() < 620:
            size = 110
        elif self.height() < 760:
            size = 160
        else:
            size = 236 if wide else (170 if narrow else 196)
        if size != self._logo_size and not self._logo_pixmap.isNull():
            self._logo_size = size
            pixmap = scaled_logo(size)
            self.logo.setPixmap(pixmap)
            ratio = pixmap.devicePixelRatio() or 1.0
            self.logo.setFixedSize(int(pixmap.width() / ratio), int(pixmap.height() / ratio))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_sidebar()

    def apply_filter(self, have: set):
        for index, spec in enumerate(LAYERS):
            shown = self.workspaces[spec.key].landing.apply_filter(have)
            total = len(programs_in(spec.key))
            caption = spec.delivers if not have else f"{shown} of {total} match"
            self.nav_items[index].set_state(index == self.layer_list.currentRow(), bool(have) and shown == 0,
                                            caption)
        self._have = have

    def _page_changed(self, on_program: bool):
        self.filter_bar.setVisible(not on_program and not self._home)

    # ------------------------------------------------------------------ home
    def is_home(self) -> bool:
        return self._home

    def show_home(self):
        """The "Choose a layer" page; the sidebar comes back with the first layer opened."""
        self._home = True
        self.sidebar.hide()
        self.filter_bar.hide()
        self.stack.hide()
        self.home.clear_search()
        self.home.refresh()
        self.home_scroll.show()
        self.statusBar().showMessage("Home")
        self.home_changed.emit(True)

    def leave_home(self):
        if not self._home:
            return
        self._home = False
        self.home_scroll.hide()
        self.sidebar.show()
        self.stack.show()
        workspace = self.current_workspace()
        self.filter_bar.setVisible(not workspace.has_package())
        self.statusBar().showMessage(f"Ready - {LAYERS[self.stack.currentIndex()].title}")
        self.home_changed.emit(False)

    def open_layer(self, key: str):
        row = next(i for i, spec in enumerate(LAYERS) if spec.key == find_layer(key).key)
        self.leave_home()
        if self.layer_list.currentRow() != row:
            self.layer_list.setCurrentRow(row)
        else:
            self.select_layer(row)

    def open_program(self, key: str):
        spec = find_program(key)
        self.open_layer(spec.layer)
        self.current_workspace().select_package(spec.key)

    def select_layer(self, row: int):
        if row < 0:
            return
        self.leave_home()
        spec = LAYERS[row]
        previous = self.current_workspace() if self.stack.count() else None
        if previous is not None and previous is not self.workspaces[spec.key]:
            if not previous.running_pages():
                previous.go_home()
        self.stack.setCurrentIndex(row)
        workspace = self.workspaces[spec.key]
        workspace.landing.refresh()
        self.filter_bar.setVisible(not workspace.has_package())
        self.apply_filter(getattr(self, "_have", set()))
        self.statusBar().showMessage(f"Ready - {spec.title}")

    def current_workspace(self) -> LayerWorkspace:
        return self.workspaces[LAYERS[self.stack.currentIndex()].key]

    def refresh_all(self):
        for workspace in self.workspaces.values():
            workspace.refresh()
            for page in workspace.pages.values():
                page.form.refresh_destination_hint()

    def install_program(self, program_key: str):
        spec = find_program(program_key)
        manager = EnvManager()
        envs = []
        for variant in spec.variants:
            state = env_state(manager, variant.env)[1]
            if state in ("missing", "update") and variant.env not in envs:
                envs.append(variant.env)
        for env_key in envs[:1]:
            dialog = ProcessDialog(f"Installing {spec.name}", luci_cli("env", "install", env_key), self)
            dialog.exec()
        self.refresh_all()

    def uninstall_program(self, program_key: str):
        spec = find_program(program_key)
        manager = EnvManager()
        installed = [v.env for v in spec.variants if manager.is_installed(v.env)]
        running = any(page.is_running() for ws in self.workspaces.values()
                      for key, page in ws.pages.items() if key == spec.key)
        for env_key in dict.fromkeys(installed):
            if not uninstall_environment(self, env_key, busy=running):
                break
        self.refresh_all()

    def open_environments(self):
        dialog = EnvironmentsDialog(self)
        dialog.changed.connect(self.refresh_all)
        dialog.exec()
        self.refresh_all()

    def open_settings(self):
        if SettingsDialog(self).exec():
            self.refresh_all()
        # A new OpenAI key (or its removal) turns the assistant on (or off).
        assistant = getattr(self, "_assistant", None)
        if assistant is not None:
            assistant.refresh_availability()

    # ------------------------------------------------------------- workflows
    def save_workflow(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save LUCI workflow", "luci-workflow.json",
                                              "LUCI workflow (*.json)")
        if path:
            spec = LAYERS[self.stack.currentIndex()]
            Path(path).write_text(json.dumps({
                "luci": __version__, "layer": spec.key,
                "state": self.current_workspace().save_state(),
            }, indent=2), encoding="utf-8")

    def load_workflow(self, path: str | None = None):
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "Load LUCI workflow", "", "LUCI workflow (*.json)")
        if not path:
            return
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            state = dict(payload.get("state") or {})
            legacy_module = payload.get("module")
            program_key = state.get("program") or state.get("backend")
            if legacy_module and program_key in (None, "", "aqme", "robert"):
                # LUCI 0.1 files store "module": conf/gopt/feat/pred and a backend
                # that may just name the package.
                program_key = LEGACY_LAYER_DEFAULT.get(legacy_module, program_key)
                state["program"] = program_key
            if program_key:
                layer_key = find_program(program_key).layer
                state["program"] = find_program(program_key).key
            else:
                layer_key = find_layer(payload.get("layer") or legacy_module).key
            index = next(i for i, spec in enumerate(LAYERS) if spec.key == layer_key)
            self.leave_home()
            self.layer_list.setCurrentRow(index)
            self.current_workspace().load_state(state)
        except (OSError, ValueError, KeyError, StopIteration, TypeError, AttributeError) as exc:
            QMessageBox.critical(self, "Could not load workflow", str(exc))

    def about(self):
        QMessageBox.about(
            self, "About LUCI",
            f"LUCI {__version__}\nLayered Unified Computational Interfaces\n\n"
            "Layers are named after what you get back. Every program runs in its own "
            "environment, installed on demand.")

    def closeEvent(self, event: QCloseEvent):
        running = [page for ws in self.workspaces.values() for page in ws.running_pages()]
        if running:
            answer = QMessageBox.question(self, "Workflow running",
                                          "Stop the running workflow(s) and exit?")
            if answer != QMessageBox.Yes:
                event.ignore()
                return
            for page in running:
                page.stop(wait=True)  # LUCI is closing: make sure nothing is left behind
        if self.update_button is not None:
            self.update_button.shutdown()
        event.accept()


def _install_excepthook():
    """An error inside the window is logged and shown; it never closes LUCI."""
    import traceback
    log_file = luci_home() / "gui-errors.log"

    def hook(kind, value, tb):
        text = "".join(traceback.format_exception(kind, value, tb))
        try:
            with log_file.open("a", encoding="utf-8") as handle:
                handle.write(text + "\n")
        except OSError:
            pass
        sys.__stderr__ and sys.__stderr__.write(text)
        if QApplication.instance() is not None:
            QMessageBox.warning(None, "LUCI error",
                                f"Something went wrong:\n\n{value}\n\nDetails were saved to {log_file}.")

    sys.excepthook = hook


def main(argv: list[str] | None = None) -> int:
    # Give Windows a stable identity so the taskbar uses LUCI's icon.
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("luci.gui.app")
    except Exception:
        pass
    app = QApplication(argv or sys.argv)
    # Selected text and highlighted list items: dark text on orange, readable.
    palette = app.palette()
    palette.setColor(QPalette.Highlight, QColor(theme.ORANGE))
    palette.setColor(QPalette.HighlightedText, QColor(theme.BLACK))
    for role, colour in ((QPalette.Window, theme.BLACK), (QPalette.Base, theme.BLACK),
                         (QPalette.WindowText, theme.CREAM), (QPalette.Text, theme.CREAM),
                         (QPalette.ButtonText, theme.CREAM), (QPalette.PlaceholderText, theme.CREAM_3),
                         (QPalette.ToolTipBase, theme.BLACK), (QPalette.ToolTipText, theme.CREAM)):
        palette.setColor(role, QColor(colour))
    app.setPalette(palette)
    app.setApplicationName("LUCI")
    app.setOrganizationName("LUCI")
    if symbol_path().is_file():
        app.setWindowIcon(application_icon())
    _install_excepthook()
    updater.clean_leftovers()
    window = MainWindow()
    window.show_home()
    window.showMaximized()
    return app.exec()


__all__ = ["MainWindow", "main"]
