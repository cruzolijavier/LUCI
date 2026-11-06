"""Reusable form building blocks shared by every LUCI package screen.

These widgets carry the behaviour that used to be copied into each package
form: fields that look alike, row titles that line up, the round help
affordance, and the collapsible sections. A package screen should be able to
describe what it needs and get all of this for free.
"""

from __future__ import annotations

import html
from pathlib import Path

from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt, QUrl, Signal
from PySide6.QtGui import QCursor, QDesktopServices, QPalette, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLayout, QLineEdit, QListView, QListWidget, QPlainTextEdit,
    QPushButton, QSizePolicy, QStyle, QStyleOptionComboBox, QStylePainter,
    QToolButton, QToolTip, QVBoxLayout, QWidget,
)


GLOB = set("*?[]")

# Height of a styled QLineEdit/QComboBox: 28px content + 14px padding + 2px border.
# Row titles use it so a label is centered against the cell it names.
FIELD_HEIGHT = 44
# Row titles share one width per form; longer ones wrap onto two lines.
LABEL_MAX_WIDTH = 180


def align_labels(container: QWidget, max_width: int = LABEL_MAX_WIDTH):
    """Give every row title in ``container`` the same width, so fields line up."""
    labels = container.findChildren(QLabel, "fieldLabel")
    if not labels:
        return
    natural = [label.fontMetrics().horizontalAdvance(label.text()) + 6 for label in labels]
    width = min(max(natural), max_width)
    for label, wanted in zip(labels, natural):
        label.setWordWrap(wanted > width)
        label.setFixedWidth(width)

DOCS_HELP = ("Opens the {name} documentation website in your browser, where every native flag "
             "this box accepts is described in full.")


def transparent(widget: QWidget) -> QWidget:
    """Mark a layout-only container so it shows the panel color, not the window."""
    widget.setObjectName("formPanel")
    return widget


class PageStack(QWidget):
    """Shows one of several pages, and takes only the height of that page.

    QStackedWidget reserves the height of its tallest page whenever a page
    wraps text (its height-for-width ignores hidden pages' size policies), so
    a short input would sit in a box sized for the tallest one.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        transparent(self)
        self._pages: list[QWidget] = []
        self._current = -1
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

    def addWidget(self, page: QWidget) -> int:
        self._pages.append(page)
        self._layout.addWidget(page)
        if self._current < 0:
            self._current = 0
        page.setVisible(len(self._pages) - 1 == self._current)
        return len(self._pages) - 1

    def count(self) -> int:
        return len(self._pages)

    def widget(self, index: int) -> QWidget:
        return self._pages[index]

    def currentIndex(self) -> int:
        return self._current

    def currentWidget(self) -> QWidget | None:
        return self._pages[self._current] if 0 <= self._current < len(self._pages) else None

    def setCurrentIndex(self, index: int) -> None:
        if not 0 <= index < len(self._pages):
            return
        self._current = index
        for position, page in enumerate(self._pages):
            page.setVisible(position == index)
        self.updateGeometry()


def row_label(text: str) -> QLabel:
    """Return a form-row title vertically centered against its field widget."""
    label = QLabel(text)
    label.setObjectName("fieldLabel")
    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    label.setMinimumHeight(FIELD_HEIGHT)
    label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    return label


class HelpButton(QToolButton):
    """Round '?' next to a field that explains it on hover, and on click."""

    def __init__(self, text: str, url: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("helpButton")
        self.setText("?")
        # The button explains a field; it should never steal tab focus from it.
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.PointingHandCursor)
        self._url = url
        # Styled apart so a link out of the app reads differently from an in-place hint.
        self.setProperty("docs", "true" if url else "false")
        self.set_help(text)
        self.clicked.connect(self._activated)

    def set_help(self, text: str):
        """Set the explanation, as rich text so QToolTip wraps it over lines."""
        self._help = text
        self.setToolTip(f"<p>{html.escape(text)}</p>")

    def _activated(self):
        """Open the documentation, or repeat the explanation for click users."""
        if self._url:
            QDesktopServices.openUrl(QUrl(self._url))
            return
        QToolTip.showText(QCursor.pos(), self.toolTip(), self)


def with_help(field, text: str, *, url: str = "") -> QHBoxLayout:
    """Return a field row carrying its help affordance, centered on the right."""
    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(10)
    if isinstance(field, QWidget):
        row.addWidget(field, 1)
    else:
        row.addLayout(field, 1)
    if text or url:
        row.addWidget(HelpButton(text, url), 0, Qt.AlignVCenter)
    else:
        # Keep the field's right edge aligned with the rows that have a "?"
        # (box layouts add no spacing next to a spacer, so include it here).
        row.addSpacing(HELP_BUTTON_SIZE + row.spacing())
    return row


HELP_BUTTON_SIZE = 26


def advanced_hint() -> QLabel:
    """Grey caption shown under the advanced flags cell."""
    hint = QLabel("Other options that the program accepts.")
    hint.setObjectName("hint")
    hint.setWordWrap(True)
    return hint


def form_layout(parent: QWidget) -> QFormLayout:
    """Return a form layout with LUCI's shared row metrics and label alignment."""
    form = QFormLayout(parent)
    form.setLabelAlignment(Qt.AlignCenter | Qt.AlignVCenter)
    form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
    form.setHorizontalSpacing(18)
    form.setVerticalSpacing(12)
    return form


class NoScrollComboBox(QComboBox):
    """Dropdown whose value the mouse wheel cannot change.

    Qt lets a wheel event over a closed combo box step through its values, so
    scrolling past a form silently rewrites settings the user never touched.
    Ignoring the event hands the wheel to the scroll area instead, and the
    value only changes by opening the popup and picking an entry. The open
    popup is a separate widget, so its own scrolling still works.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # Long entries ("Database tags (retrieve / export)") must not set the
        # width of the whole form on a small laptop screen.
        self.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.setMinimumContentsLength(8)

    def wheelEvent(self, event):
        event.ignore()

    def mark_placeholder(self, is_placeholder: bool):
        """Grey, regular text while the box shows a hint rather than a value."""
        if self.property("placeholder") != is_placeholder:
            self.setProperty("placeholder", is_placeholder)
            repolish(self)


class CollapsibleGroupBox(QGroupBox):
    """Clickable section for package forms, expanded by default.

    Every section used to start collapsed unless a call site remembered to
    call .expand() right after building it — most did not, so fields like
    Method or Constraints were invisible (and their dropdowns unreachable)
    until a user discovered the unmarked click-to-expand header. Expanding
    by default removes that trap; the caret still lets sections be tucked
    away on purpose.
    """

    # Emitted after the section's rows were made visible (first show, expand).
    content_shown = Signal()

    def __init__(self, title: str, parent=None, *, expanded: bool = True):
        super().__init__(parent)
        self._base_title = title
        self._expanded = expanded
        self._initialized = False
        self.setCursor(Qt.PointingHandCursor)
        self._apply_title()
        if not expanded:
            self.setMaximumHeight(48)

    def _apply_title(self):
        self.setTitle(f"{'▾' if self._expanded else '▸'}  {self._base_title}")

    def _set_content_visible(self, visible: bool):
        # Direct children only. A recursive walk reaches inside the widgets
        # themselves and force-shows a QComboBox's private popup window, after
        # which Qt sees the dropdown as already open and a click never opens
        # it. Hiding a direct child hides its descendants anyway, and leaving
        # them alone also keeps a QStackedWidget showing just its current page.
        for child in self.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
            child.setVisible(visible)

    def expand(self):
        self._expanded = True
        self.setMaximumHeight(16777215)
        self._set_content_visible(True)
        self._apply_title()
        self.content_shown.emit()

    def collapse(self):
        self._expanded = False
        self._set_content_visible(False)
        self.setMaximumHeight(48)
        self._apply_title()

    def showEvent(self, event):
        if not self._initialized:
            self._initialized = True
            self._set_content_visible(self._expanded)
            if self._expanded:
                self.content_shown.emit()
        super().showEvent(event)

    def mousePressEvent(self, event):
        if event.position().y() <= 38:
            if self._expanded:
                self.collapse()
            else:
                self.expand()
            event.accept()
            return
        super().mousePressEvent(event)


class FileDropLineEdit(QLineEdit):
    file_dropped = Signal(str)
    open_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def mousePressEvent(self, event):
        if not self.text().strip():
            self.open_requested.emit()
            event.accept()
            return
        super().mousePressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self.file_dropped.emit(url.toLocalFile())
                event.acceptProposedAction()
                return
        event.ignore()


class LabeledPath(QWidget):
    changed = Signal(str)

    def __init__(self, label: str, file_filter: str, directory: bool = False, parent=None,
                 save: bool = False):
        super().__init__(parent)
        self.file_filter = file_filter
        self.directory = directory
        self.save = save
        transparent(self)
        self.edit = FileDropLineEdit()
        self.edit.setPlaceholderText(f"{label} - drop here or click to browse")
        self.edit.textChanged.connect(self.changed)
        self.edit.open_requested.connect(self.browse)
        self.edit.file_dropped.connect(self.setText)
        self.setAcceptDrops(True)
        browse_button = QPushButton("Browse")
        browse_button.setObjectName("browseButton")
        browse_button.clicked.connect(self.browse)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.edit, 1)
        layout.addWidget(browse_button)

    def browse(self):
        if self.directory:
            value = QFileDialog.getExistingDirectory(self, "Select folder")
        elif self.save:
            value, _ = QFileDialog.getSaveFileName(self, "Choose where to save", "", self.file_filter)
        else:
            value, _ = QFileDialog.getOpenFileName(self, "Select input file", "", self.file_filter)
        if value:
            self.setText(value)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self.setText(url.toLocalFile())
                event.acceptProposedAction()
                return
        event.ignore()

    def text(self) -> str:
        return self.edit.text().strip()

    def setText(self, text: str):
        self.edit.setText(text)


class MultiColumnSelector(NoScrollComboBox):
    """Dropdown that takes several columns at once.

    It reads as one more cell in the form, with the same height and chevron as
    the single-value dropdowns beside it. The popup holds a checkbox per column
    and stays open while entries are ticked, and the closed box summarises the
    current selection.
    """

    selection_changed = Signal()
    EMPTY_HINT = "Load a CSV to pick columns"
    PLACEHOLDER = "Select columns"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = QStandardItemModel(self)
        self.setModel(self._model)
        self.setView(QListView())
        self.view().viewport().installEventFilter(self)
        self._model.itemChanged.connect(self._item_changed)
        self.set_columns([])

    def _item_changed(self, _item):
        self.update()
        self.selection_changed.emit()

    def eventFilter(self, watched, event):
        # Toggle the row under the cursor and swallow the release, so ticking
        # several columns does not close the popup after the first one.
        if watched is self.view().viewport() and event.type() == QEvent.MouseButtonRelease:
            index = self.view().indexAt(event.position().toPoint())
            item = self._model.itemFromIndex(index) if index.isValid() else None
            if item is not None and item.isEnabled() and item.isCheckable():
                item.setCheckState(Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked)
            return True
        return super().eventFilter(watched, event)

    def set_columns(self, columns: list[str]):
        """Replace the offered columns, keeping whatever is still selected."""
        previous = set(self.selected_values())
        self._model.blockSignals(True)
        self._model.clear()
        for column in columns:
            item = QStandardItem(column)
            item.setCheckable(True)
            item.setEditable(False)
            item.setCheckState(Qt.Checked if column in previous else Qt.Unchecked)
            self._model.appendRow(item)
        if not columns:
            # Disabled, so it can never be ticked or read back as a column.
            hint = QStandardItem(self.EMPTY_HINT)
            hint.setEnabled(False)
            hint.setEditable(False)
            self._model.appendRow(hint)
        self._model.blockSignals(False)
        self.update()

    def selected_values(self) -> list[str]:
        items = (self._model.item(row) for row in range(self._model.rowCount()))
        return [item.text() for item in items
                if item is not None and item.isCheckable() and item.checkState() == Qt.Checked]

    def set_values(self, values: str | list[str] | None):
        if isinstance(values, str):
            values = [part.strip().strip("'\"") for part in values.strip("[]").split(",") if part.strip()]
        wanted = set(values or [])
        self._model.blockSignals(True)
        for row in range(self._model.rowCount()):
            item = self._model.item(row)
            if item is not None and item.isCheckable():
                item.setCheckState(Qt.Checked if item.text() in wanted else Qt.Unchecked)
        self._model.blockSignals(False)
        self.update()
        self.selection_changed.emit()

    def _display_text(self) -> str:
        selected = self.selected_values()
        if selected:
            return ", ".join(selected)
        first = self._model.item(0)
        return self.EMPTY_HINT if first is not None and not first.isCheckable() else self.PLACEHOLDER

    def paintEvent(self, _event):
        # Painted by hand because a combo box otherwise shows only the current
        # row, and this one has to report every ticked column.
        self.mark_placeholder(not self.selected_values())
        painter = QStylePainter(self)
        painter.setPen(self.palette().color(QPalette.Text))
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        option.currentText = self._display_text()
        painter.drawComplexControl(QStyle.CC_ComboBox, option)
        painter.drawControl(QStyle.CE_ComboBoxLabel, option)


def input_value_from_widget(widget: QWidget) -> str | None:
    if isinstance(widget, QCheckBox):
        return "True" if widget.isChecked() else None
    if isinstance(widget, MultiColumnSelector):
        selected = widget.selected_values()
        return "[" + ",".join(selected) + "]" if selected else None
    if isinstance(widget, QComboBox):
        value = widget.currentData()
        return value if value not in ("", None) else None
    if isinstance(widget, LabeledPath):
        value = widget.text()
        return value or None
    if isinstance(widget, QLineEdit):
        value = widget.text().strip()
        return value or None
    if isinstance(widget, QPlainTextEdit):
        value = widget.toPlainText().strip()
        return value or None
    return None


def directory_destination(value: str) -> str:
    if not value.strip():
        return ""
    path = Path(value.strip())
    if path.exists() and path.is_dir():
        return str(path.resolve())
    return str(path.parent.resolve()) if path.parent else ""


class FlowLayout(QLayout):
    """Lays widgets out left to right and wraps them onto new lines.

    Used for tag chips and filter toggles, which must never force a
    horizontal scrollbar on a narrow window.
    """

    def __init__(self, parent=None, spacing: int = 8):
        super().__init__(parent)
        self._items = []
        self._spacing = spacing
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._arrange(QRect(0, 0, width, 0), apply=False)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._arrange(rect, apply=True)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        return size + QSize(margins.left() + margins.right(), margins.top() + margins.bottom())

    def _arrange(self, rect, apply):
        margins = self.contentsMargins()
        area = rect.adjusted(margins.left(), margins.top(), -margins.right(), -margins.bottom())
        x, y, line_height = area.x(), area.y(), 0
        for item in self._items:
            if item.widget() is not None and not item.widget().isVisibleTo(item.widget().parentWidget()):
                continue
            hint = item.sizeHint()
            if x + hint.width() > area.right() + 1 and line_height > 0:
                x = area.x()
                y += line_height + self._spacing
                line_height = 0
            if apply:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x += hint.width() + self._spacing
            line_height = max(line_height, hint.height())
        return y + line_height - rect.y() + margins.bottom()


def chip(text: str, kind: str = "input", tooltip: str = "") -> QLabel:
    """A small rounded tag; ``kind`` picks its colour in the theme."""
    label = QLabel(text)
    label.setObjectName("chip")
    label.setProperty("kind", kind)
    if tooltip:
        label.setToolTip(tooltip)
    return label


def status_pill(text: str, state: str) -> QLabel:
    """Installation state: ok, missing, blocked or pending."""
    label = QLabel(text)
    label.setObjectName("statusPill")
    label.setProperty("state", state)
    return label


def repolish(widget: QWidget):
    """Re-apply the stylesheet after a dynamic property changed."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()
