"""Visual identity for the LUCI GUI: palette, fonts, the stylesheet and the bundled art.

Everything a future visual refresh needs to touch lives here, so package
screens never carry colors of their own. The look follows ``LUCI_visual.html``
(black, cream and orange; Unbounded / Figtree / JetBrains Mono; "leaf" corners),
on purpose without glows: no shadows, halos or moving lights.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication

# ---------------------------------------------------------------------------
# Palette (same names as in LUCI_visual.html)
# ---------------------------------------------------------------------------
BLACK = "#000000"
CREAM = "#fff3e7"          # text
CREAM_2 = "#bcb4ab"        # cream at 68% on black: secondary text
CREAM_3 = "#867f78"        # cream at 45% on black: captions
LINE = "#29271f"           # cream at 16% on black: hairlines
LINE_2 = "#4d4945"         # cream at 30% on black: borders
ORANGE = "#ff7b10"
ORANGE_TINT = "#211002"      # orange at 13% on black
AMBER = "#ffb02e"
GREEN = "#3ddc84"
RED = "#ff5c5c"
BLUE = "#5cc8ff"
PURPLE = "#b48cff"
PANEL = "#0b0a09"          # cream at 4% on black: console, chat
ON_ACCENT = "#000000"      # text on orange / amber / green / red fills
HOVER_FILL = CREAM         # hover colour of the orange buttons
FILTER_BG, FILTER_LINE, FILTER_BORDER, FILTER_HOVER = "#0f0b05", "#66461a", "#a0742a", "#2e2108"
PURPLE_BG, BLUE_BG, RED_BG, RED_TEXT = "#120e19", "#09141a", "#1a0909", "#ffc9c9"

# The light theme keeps the names: BLACK is "the background" and CREAM "the text ink", whatever
# the mode. Colours used as text on a light background are a little deeper to keep the contrast.
_DARK = {k: v for k, v in dict(
    BLACK=BLACK, CREAM=CREAM, CREAM_2=CREAM_2, CREAM_3=CREAM_3, LINE=LINE, LINE_2=LINE_2, ORANGE=ORANGE,
    ORANGE_TINT=ORANGE_TINT, AMBER=AMBER, GREEN=GREEN, RED=RED, BLUE=BLUE, PURPLE=PURPLE, PANEL=PANEL,
    ON_ACCENT=ON_ACCENT, HOVER_FILL=HOVER_FILL, FILTER_BG=FILTER_BG, FILTER_LINE=FILTER_LINE,
    FILTER_BORDER=FILTER_BORDER, FILTER_HOVER=FILTER_HOVER, PURPLE_BG=PURPLE_BG, BLUE_BG=BLUE_BG,
    RED_BG=RED_BG, RED_TEXT=RED_TEXT).items()}
_LIGHT = dict(
    BLACK="#fffaf4", CREAM="#1b140c", CREAM_2="#5b5249", CREAM_3="#80776d", LINE="#e6dccf", LINE_2="#c9bcad",
    ORANGE="#d4570a", ORANGE_TINT="#ffeadb", AMBER="#a86300", GREEN="#14803a", RED="#c92a2a", BLUE="#1f6fa8",
    PURPLE="#7041c4", PANEL="#f6efe6", ON_ACCENT="#ffffff", HOVER_FILL="#a84506", FILTER_BG="#fff1e0",
    FILTER_LINE="#e9c79c", FILTER_BORDER="#c98a2e", FILTER_HOVER="#ffe2bd", PURPLE_BG="#f1ebfc",
    BLUE_BG="#e7f3fb", RED_BG="#fdeaea", RED_TEXT="#8a1f1f")
PALETTES = {"dark": _DARK, "light": _LIGHT}

DISPLAY_FONT = "Unbounded"
BODY_FONT = "Figtree"
MONO_FONT = "JetBrains Mono"


def _gui_file(relative: str) -> Path:
    try:
        return Path(resources.files("luci.gui").joinpath(relative))
    except Exception:
        return Path(__file__).resolve().parent / relative


def asset_url(name: str) -> str:
    """Return a bundled asset as a stylesheet-safe url(), independent of the CWD."""
    # Qt stylesheets need forward slashes even on Windows.
    return _gui_file(f"assets/{name}").as_posix()


_FONTS_LOADED = False


def load_fonts() -> None:
    """Register the bundled fonts (SIL OFL, see assets/fonts/OFL.txt) once per process."""
    global _FONTS_LOADED
    if _FONTS_LOADED or QApplication.instance() is None:
        return
    _FONTS_LOADED = True
    folder = _gui_file("assets/fonts")
    if folder.is_dir():
        for font in sorted(folder.glob("*.ttf")):
            QFontDatabase.addApplicationFont(str(font))


# Corners: the "leaf" shape of the design, big radius on two opposite corners.
def _leaf(big: int, small: int, mirror: bool = False) -> str:
    a, b = (small, big) if mirror else (big, small)
    return (f"border-top-left-radius: {a}px; border-top-right-radius: {b}px; "
            f"border-bottom-right-radius: {a}px; border-bottom-left-radius: {b}px;")


LEAF = _leaf(22, 4)
LEAF_MIRROR = _leaf(22, 4, mirror=True)
LEAF_FIELD = _leaf(14, 3)
LEAF_BUTTON = _leaf(12, 3)

_TEMPLATE = """
/* LUCI theme, from LUCI_visual.html. No glows: flat colors only. */
QWidget { background: @BLACK; color: @CREAM; font-family: '@BODY'; font-size: 13px; }
QMainWindow, QDialog { background: @BLACK; }
QToolTip { background: @BLACK; color: @CREAM; border: 1px solid @LINE_2; padding: 5px 8px; font-size: 12px; }
QMenuBar { background: @BLACK; color: @CREAM_3; border-bottom: 1px solid @LINE; padding: 2px 6px; font-size: 12px; }
QMenuBar::item { background: transparent; padding: 4px 10px; border-radius: 6px; }
QMenuBar::item:selected { background: @ORANGE_TINT; color: @CREAM; }
QMenu { background: @BLACK; border: 1px solid @LINE_2; padding: 4px; @LEAF_BUTTON }
QMenu::item { padding: 6px 18px 6px 12px; border-radius: 6px; color: @CREAM; }
QMenu::item:selected { background: @ORANGE; color: @ON_ACCENT; }
QMenu::separator { height: 1px; background: @LINE; margin: 4px 2px; }

/* ---- Sidebar -------------------------------------------------------------- */
QFrame#sidebar { background: @BLACK; border: none; border-right: 1px solid @LINE; }
QFrame#logoFrame { background: transparent; border: none; }
QLabel#logo { background: transparent; }
QLabel#brand { color: @CREAM; font-family: '@DISPLAY'; font-size: 22px; font-weight: 800; }
QLabel#brandSub { color: @CREAM_3; font-size: 11px; }
QListWidget { background: transparent; border: none; outline: none; padding: 4px 0; }
QListWidget::item { color: @CREAM; padding: 10px; }
QListWidget#layerList { border: none; background: transparent; padding: 0; }
QListWidget#layerList::item, QListWidget#layerList::item:selected, QListWidget#layerList::item:hover {
    background: transparent; border: none; padding: 0; margin: 0; }
QWidget#navItem { background: transparent; }
QLabel#navTitle { background: transparent; color: @CREAM; font-family: '@DISPLAY'; font-size: 12px; font-weight: 600; }
QLabel#navCaption { background: transparent; color: @CREAM_3; font-size: 11px; }
QLabel#navTitle[selected="true"], QLabel#navCaption[selected="true"] { color: @ON_ACCENT; }
QLabel#navTitle[dimmed="true"], QLabel#navCaption[dimmed="true"] { color: @LINE_2; }

/* ---- Titles and text ------------------------------------------------------- */
QLabel#pageTitle { color: @CREAM; font-family: '@DISPLAY'; font-size: 24px; font-weight: 800; }
QLabel#heroTitle { color: @CREAM; font-family: '@DISPLAY'; font-size: 32px; font-weight: 800; }
QLabel#pageSubtitle { color: @CREAM_2; font-size: 14px; }
QLabel#pageCaption { color: @CREAM_2; font-size: 13px; }
QLabel#hint { color: @CREAM_3; font-size: 11px; }
QLabel#backendBadge { color: @ORANGE; font-weight: 800; padding: 6px 10px; background: @BLACK; border: 1px solid @ORANGE; border-radius: 14px; }
QLabel#backendInfo { color: @CREAM_2; background: @BLACK; border: 1px solid @LINE_2; padding: 12px 14px; @LEAF }

/* ---- "What do you have?" filter ----------------------------------------- */
QFrame#filterBar { background: @FILTER_BG; border: none; border-bottom: 1px solid @FILTER_LINE; }
QLabel#filterLabel { background: transparent; color: @AMBER; font-family: '@DISPLAY'; font-size: 13px; font-weight: 600; min-height: 18px; }
QLabel#filterSub { background: transparent; color: @CREAM_2; font-size: 12px; }
QToolButton#filterChip { background: @FILTER_BG; color: @AMBER; border: 1px solid @FILTER_BORDER; border-radius: 16px;
                         padding: 6px 16px; min-height: 20px; font-size: 13px; font-weight: 800; }
QToolButton#filterChip[compact="true"] { padding: 3px 12px; font-size: 12px; border-radius: 13px; }
QToolButton#filterChip:hover { background: @FILTER_HOVER; }
QToolButton#filterChip:checked { background: @AMBER; color: @ON_ACCENT; border-color: @AMBER; }
QToolButton#clearFilter { background: transparent; color: @AMBER; border: none; font-size: 12px;
                          font-weight: 800; padding: 4px 6px; min-height: 22px; }
QToolButton#clearFilter:hover { color: @CREAM; }

/* ---- Home: layer cards ------------------------------------------------------ */
QFrame#layerCard { background: @BLACK; border: 1px solid @LINE; @LEAF }
QFrame#layerCard[alt="true"] { @LEAF_MIRROR }
QFrame#layerCard:hover { border-color: @LINE_2; }
QFrame#layerCard QLabel, QFrame#layerCard QWidget#formPanel { background: transparent; }
QPushButton#programChip { background: transparent; border: 1px solid @LINE_2; color: @CREAM; padding: 3px 12px;
                          min-height: 20px; font-size: 12px; font-weight: 600; @LEAF_BUTTON }
QPushButton#programChip:hover { border-color: @ORANGE; color: @ORANGE; }
QPushButton#programChip[state="ok"] { border-color: @GREEN; color: @GREEN; }
QPushButton#programChip[state="update"] { border-color: @BLUE; color: @BLUE; }
QPushButton#programChip[state="blocked"] { border-color: @RED; color: @RED; }
QPushButton#programChip[state="pending"] { border-style: dashed; color: @CREAM_3; }

/* ---- Program cards -------------------------------------------------------- */
QFrame#programCard { background: @BLACK; border: 1px solid @LINE; @LEAF }
QFrame#programCard[alt="true"] { @LEAF_MIRROR }
QFrame#programCard:hover { border-color: @LINE_2; }
QFrame#programCard QLabel, QFrame#programCard QWidget#formPanel { background: transparent; }
QLabel#cardTitle { color: @CREAM; font-family: '@DISPLAY'; font-size: 16px; font-weight: 600; }
QLabel#cardBody { color: @CREAM_2; font-size: 13px; font-weight: 400; }
QLabel#cardNote { color: @CREAM_3; font-size: 12px; font-weight: 400; }
QLabel#hiddenNote { color: @CREAM_3; font-size: 12px; }
QLabel#chip { border-radius: 9px; padding: 1px 9px; font-size: 11px; font-weight: 600; }
QLabel#chip[kind="input"] { background: transparent; color: @CREAM_2; border: 1px solid @LINE_2; }
QLabel#chip[kind="cost"] { background: transparent; color: @CREAM_3; border: 1px solid @LINE_2; }
QLabel#chip[kind="loop"] { background: @PURPLE_BG; color: @PURPLE; border: 1px solid @PURPLE; }
QLabel#chip[kind="platform"] { background: transparent; color: @AMBER; border: 1px solid @AMBER; }
QLabel#statusPill { border-radius: 10px; padding: 2px 10px; font-size: 11px; font-weight: 800; }
QLabel#statusPill[state="ok"] { background: @GREEN; color: @ON_ACCENT; border: 1px solid @GREEN; }
QLabel#statusPill[state="missing"] { background: transparent; color: @CREAM_2; border: 1px solid @LINE_2; }
QLabel#statusPill[state="update"] { background: @BLUE_BG; color: @BLUE; border: 1px solid @BLUE; }
QLabel#statusPill[state="blocked"] { background: @RED_BG; color: @RED; border: 1px solid @RED; }
QLabel#statusPill[state="pending"] { background: transparent; color: @CREAM_3; border: 1px dashed @LINE_2; }

/* ---- Buttons ------------------------------------------------------------------- */
QPushButton { background: transparent; border: 1px solid @LINE_2; padding: 5px 16px; min-height: 30px; color: @CREAM;
              font-size: 12px; font-weight: 800; text-align: center; @LEAF_BUTTON }
QPushButton:hover { border-color: @ORANGE; color: @ORANGE; }
QPushButton#primaryButton, QPushButton#runButton, QPushButton#launchButton {
    background: @ORANGE; color: @ON_ACCENT; border: 1px solid @ORANGE; }
QPushButton#primaryButton:hover, QPushButton#runButton:hover, QPushButton#launchButton:hover {
    background: @HOVER_FILL; border-color: @HOVER_FILL; color: @ON_ACCENT; }
QPushButton#primaryButton { padding: 4px 16px; min-height: 28px; font-size: 12px; }
QPushButton#launchButton { padding: 14px 18px; min-height: 58px; font-size: 15px; }
QPushButton#secondaryButton { padding: 4px 14px; min-height: 28px; font-size: 12px; }
QPushButton#runButton, QPushButton#stopButton, QPushButton#packageBackButton {
    padding: 4px 16px; min-height: 26px; max-height: 30px; font-size: 12px; }
QPushButton#stopButton { background: transparent; color: @RED; border: 1px solid @RED; }
QPushButton#stopButton:hover { background: @RED; color: @ON_ACCENT; }
QPushButton#browseButton { min-height: 30px; max-height: 32px; }
QPushButton#smallButton { padding: 2px 12px; min-height: 24px; max-height: 28px; font-size: 11px; }
QPushButton:disabled, QPushButton#runButton:disabled, QPushButton#stopButton:disabled, QPushButton#primaryButton:disabled {
    background: transparent; color: @LINE_2; border-color: @LINE; }
QToolButton#helpButton { background: transparent; color: @CREAM_2; border: 1px solid @LINE_2; border-radius: 13px;
                         min-width: 26px; max-width: 26px; min-height: 26px; max-height: 26px;
                         font-size: 12px; font-weight: 800; padding: 0; }
QToolButton#helpButton:hover { background: @ORANGE; color: @ON_ACCENT; border-color: @ORANGE; }
QToolButton#helpButton[docs="true"] { color: @CREAM; }
QToolButton#pill { background: transparent; color: @CREAM; border: 1px solid @LINE_2; border-radius: 17px;
                   padding: 7px 16px; min-height: 22px; font-size: 12px; font-weight: 600; }
QToolButton#pill:hover { border-color: @ORANGE; }
QToolButton#pill:checked { background: @ORANGE; color: @ON_ACCENT; border-color: @ORANGE; }
QToolButton#section { color: @ORANGE; font-family: '@DISPLAY'; font-weight: 600; border: 1px solid @LINE; padding: 8px 12px;
                      min-height: 38px; background: @BLACK; text-align: left; @LEAF_FIELD }
QToolButton#section:hover { border-color: @LINE_2; }

/* ---- Forms ------------------------------------------------------------------- */
QGroupBox { border: 1px solid @LINE; margin-top: 14px; padding: 20px 14px 10px; font-family: '@DISPLAY';
            font-size: 12px; font-weight: 600; color: @ORANGE; background: @BLACK; @LEAF }
QGroupBox::title { subcontrol-origin: margin; left: 18px; padding: 0 8px; color: @ORANGE; background: @BLACK; }
QGroupBox QLabel { background: transparent; color: @CREAM_2; font-family: '@BODY'; font-size: 13px; font-weight: 800; }
/* Layout-only containers never paint: a rounded widget then shows the panel
   color behind its corners instead of the window background. */
QWidget#formPanel { background: transparent; border: none; }
QLabel#fieldLabel { background: transparent; color: @CREAM_2; font-weight: 800; }
QLabel#inlineLabel { background: transparent; color: @CREAM_3; font-weight: 800; }
QLineEdit, QComboBox, QPlainTextEdit, QSpinBox, QDoubleSpinBox {
    background: @BLACK; border: 1px solid @LINE_2; padding: 7px 12px; min-height: 22px; color: @CREAM;
    font-family: '@BODY'; font-size: 13px; font-weight: 400; selection-background-color: @ORANGE; selection-color: @ON_ACCENT;
    @LEAF_FIELD }
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid @ORANGE; }
QLineEdit:disabled, QComboBox:disabled { color: @CREAM_3; border-color: @LINE; }
QComboBox { font-weight: 600; padding-right: 36px; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: center right; width: 26px; height: 26px;
                       margin-right: 6px; border: none; background: transparent; }
QComboBox::down-arrow { image: url({{CHEVRON}}); width: 14px; height: 14px; }
QComboBox::down-arrow:on { top: 1px; }
QComboBox QAbstractItemView { background: @BLACK; border: 1px solid @LINE_2; padding: 4px; outline: none;
                              selection-background-color: @ORANGE; selection-color: @ON_ACCENT; }
QComboBox QAbstractItemView::item { min-height: 26px; padding: 2px 6px; }
QComboBox QAbstractItemView::indicator { width: 15px; height: 15px; border: 1px solid @LINE_2; border-radius: 4px;
                                         background: @BLACK; margin-right: 4px; }
QComboBox QAbstractItemView::indicator:checked { background: @ORANGE; border-color: @ORANGE; image: url({{CHECK}}); }
QComboBox[placeholder="true"] { color: @CREAM_3; font-weight: 400; }
QCheckBox { spacing: 8px; min-height: 40px; background: transparent; color: @CREAM_2; }
QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid @LINE_2; border-radius: 5px; background: @BLACK; }
QCheckBox::indicator:hover { border-color: @ORANGE; }
QCheckBox::indicator:checked { background: @ORANGE; border: 1px solid @ORANGE; image: url({{CHECK}}); }
QCheckBox#compactCheck { min-height: 22px; font-size: 12px; }
QToolButton#themeButton { background: transparent; border: none; border-radius: 6px; padding: 2px; }
QToolButton#themeButton:hover { background: @ORANGE_TINT; }
QLabel#sidebarFooter { color: @CREAM_3; font-size: 11px; }
QToolButton#mailButton { background: transparent; border: none; padding: 2px; }
QToolButton#mailButton:hover { background: @ORANGE_TINT; }
QLineEdit#homeSearch { font-size: 14px; padding: 6px 14px; }
QLineEdit#smilesEdit { font-family: '@MONO'; font-size: 12px; }

/* ---- Console, splitter, status bar ----------------------------------------- */
QPlainTextEdit#console { background: @PANEL; color: @CREAM; border: none; border-left: 2px solid @ORANGE;
                         font-family: '@MONO'; font-size: 12px; padding: 8px 12px; @_LEAF_CONSOLE }
QPlainTextEdit#preview { font-family: '@MONO'; font-size: 12px; color: @CREAM; }
QLabel#consoleLabel { background: transparent; color: @CREAM; font-family: '@DISPLAY'; font-size: 12px; font-weight: 600; }
QSplitter::handle:vertical { background: @LINE; height: 1px; margin: 4px 22px; }
QSplitter::handle:vertical:hover { background: @ORANGE; }
QStatusBar { background: @BLACK; color: @CREAM_3; border-top: 1px solid @LINE; font-family: '@MONO'; font-size: 11px; }
QStatusBar::item { border: none; }
QStatusBar QLabel { background: transparent; color: @CREAM_3; }
QToolBar { background: @BLACK; border: none; spacing: 6px; padding: 6px; }
QScrollBar:vertical, QScrollBar:horizontal { background: transparent; width: 10px; height: 10px; margin: 0; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background: @LINE_2; border-radius: 4px; min-height: 28px; min-width: 28px; margin: 2px; }
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background: @CREAM_3; }
QScrollBar::add-line, QScrollBar::sub-line { background: none; border: none; width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: none; }
QScrollArea { background: transparent; border: none; }

/* ---- Banners on program pages ---------------------------------------------- */
QFrame#banner { @LEAF }
QFrame#banner QLabel { background: transparent; font-size: 12px; }
QFrame#banner[kind="info"] { background: transparent; border: 1px solid @LINE_2; }
QFrame#banner[kind="info"] QLabel { color: @CREAM_2; }
QFrame#banner[kind="warn"] { background: @ORANGE_TINT; border: 1px solid @ORANGE; }
QFrame#banner[kind="warn"] QLabel { color: @CREAM; }
QFrame#banner[kind="error"] { background: @RED_BG; border: 1px solid @RED; }
QFrame#banner[kind="error"] QLabel { color: @RED_TEXT; }

/* ---- Dialogs, tables, progress ------------------------------------------------ */
QLabel#resultLabel { font-size: 13px; font-weight: 800; padding: 4px 0; }
QLabel#resultLabel[kind="ok"] { color: @GREEN; }
QLabel#resultLabel[kind="warn"] { color: @AMBER; }
QLabel#resultLabel[kind="error"] { color: @RED; }
QProgressBar { background: @LINE; border: none; border-radius: 2px; max-height: 6px; text-align: center; color: transparent; }
QProgressBar::chunk { background: @ORANGE; border-radius: 2px; }
QTableWidget, QTableView, QTreeWidget, QListView { background: @BLACK; border: 1px solid @LINE; gridline-color: @LINE;
                                                   selection-background-color: @ORANGE; selection-color: @ON_ACCENT; }
QHeaderView::section { background: @BLACK; color: @ORANGE; border: none; border-bottom: 1px solid @LINE_2; padding: 6px;
                       font-family: '@DISPLAY'; font-size: 11px; font-weight: 600; }
QTableCornerButton::section { background: @BLACK; border: none; }

/* ---- Input checks (molecules, SMILES, structures) ------------------------ */
QFrame#checkPanel { background: @BLACK; border: 1px dashed @LINE_2; @LEAF_FIELD }
QFrame#checkPanel QLabel, QFrame#checkPanel QCheckBox { background: transparent; }
QLabel#checkSummary { font-size: 13px; font-weight: 800; color: @CREAM; }
QLabel#checkSummary[kind="ok"] { color: @GREEN; }
QLabel#checkSummary[kind="warn"] { color: @AMBER; }
QLabel#checkSummary[kind="error"] { color: @RED; }
QLabel#checkSummary[kind="busy"] { color: @BLUE; }
QLabel#checkDetail { color: @CREAM_2; font-size: 12px; font-weight: 400; }
QLabel#moleculeCard { background: #ffffff; border: 1px solid @LINE_2; border-radius: 10px; color: #4b555b; font-size: 12px; padding: 4px; }
QLabel#moleculeCard[empty="true"] { background: @BLACK; color: @CREAM_3; }
QTreeWidget#issueList { background: @BLACK; border: none; border-top: 1px solid @LINE; font-size: 12px; alternate-background-color: @PANEL; }
QTreeWidget#issueList::item { padding: 3px 2px; border-bottom: 1px solid @LINE; }
QTreeWidget#issueList::item:selected { background: @ORANGE_TINT; color: @CREAM; }
"""

_PALETTE_KEYS = tuple(_DARK)
_mode = "dark"
ORANGE_STYLE = LUCI_STYLE = ""


def _build_style() -> str:
    tokens = {"@" + key: globals()[key] for key in _PALETTE_KEYS}
    tokens.update({
        "@LEAF_MIRROR": LEAF_MIRROR, "@LEAF_FIELD": LEAF_FIELD, "@LEAF_BUTTON": LEAF_BUTTON,
        "@_LEAF_CONSOLE": _leaf(14, 3, mirror=True), "@LEAF": LEAF,
        "@DISPLAY": DISPLAY_FONT, "@BODY": BODY_FONT, "@MONO": MONO_FONT,
    })
    text = _TEMPLATE
    # Longest names first, so "@CREAM_2" is never read as "@CREAM" + "_2".
    for token in sorted(tokens, key=len, reverse=True):
        text = text.replace(token, tokens[token])
    return (text.replace("{{CHEVRON}}", asset_url("chevron_down.png"))
            .replace("{{CHECK}}", asset_url("check.png")))


def set_mode(mode: str) -> None:
    """Switch the palette ("dark" or "light"). Everything that reads ``theme.X`` afterwards sees the
    new colours; the window re-applies the stylesheet and repaints its own widgets."""
    global _mode, ORANGE_STYLE, LUCI_STYLE
    if mode not in PALETTES:
        mode = "dark"
    _mode = mode
    globals().update(PALETTES[mode])
    ORANGE_STYLE = LUCI_STYLE = _build_style()


def mode() -> str:
    return _mode


def style() -> str:
    return ORANGE_STYLE


set_mode("dark")


def logo_path() -> Path:
    """Return the bundled main logo path, independent of the working directory."""
    if _mode == "light":
        light = _gui_file("logos/logo_light.png")  # transparent, white parts turned into ink
        if light.is_file():
            return light
    return _gui_file("logos/logo.png")


def symbol_path() -> Path:
    """The square logo used by the window and taskbar icon."""
    icon = _gui_file("logos/icon.png")
    return icon if icon.is_file() else logo_path()


def application_icon() -> QIcon:
    """Build a proportional square icon for the window and Windows taskbar."""
    icon = QIcon()
    icon_file = symbol_path()
    if icon_file.is_file():
        pixmap = QPixmap(str(icon_file))
        if not pixmap.isNull():
            # KeepAspectRatio prevents distortion; a square canvas centres the art.
            pixmap = pixmap.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            canvas = QPixmap(256, 256)
            canvas.fill(Qt.transparent)
            painter = QPainter(canvas)
            painter.drawPixmap((256 - pixmap.width()) // 2, (256 - pixmap.height()) // 2, pixmap)
            painter.end()
            icon.addPixmap(canvas)
    return icon
