"""The picture behind the robot's "?": what every button of the assistant does.

The picture is drawn with the real buttons (the robot, the CONTROL switch and the
chat buttons paint themselves), so it always looks like the window. It ships as
``gui/assets/assistant_help_dark.png`` and ``assistant_help_light.png``; to redraw
both after changing a button or a text:

    QT_QPA_PLATFORM=offscreen python tools/assistant_help_image.py

If a PNG is missing, the window draws the picture on the spot.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QImage, QPainter, QPainterPath, QPen, QPixmap, QRegion
from PySide6.QtWidgets import QPushButton, QWidget

from ..gui import theme

WIDTH = 760            # logical pixels; the PNG is drawn at twice this size
SCALE = 2
MARGIN = 34
ICON_COLUMN = 96

# (section, [(what to draw, name, explanation)])
SECTIONS = (
    ("Next to the robot", (
        ("robot", "Assistant",
         "Opens and closes the chat. The ring turns amber while the assistant works. A grey robot "
         "has no OpenAI key yet: add it in Tools > Settings."),
        ("switch", "CONTROL",
         "Off: the assistant explains and checks your inputs, nothing else. On: it can drive LUCI for "
         "you: open programs, fill the input and the options, save and load workflows. It presses Run "
         "only when you ask."),
        ("help", "Help", "Shows this guide."),
    )),
    ("In the chat", (
        ("globe", "Web search",
         "Orange = on: when a question needs it, the assistant searches the web and cites the sources."),
        ("reload", "New conversation", "Starts a fresh chat; the assistant forgets the previous one."),
        ("close", "Close", "Hides the chat. Nothing is lost: the robot opens it again."),
        ("mic", "Dictate",
         "Press to record and again to stop (red while recording). The text stays in the box until "
         "you send it."),
        ("send", "Send", "Sends the message. Enter sends, Shift+Enter starts a new line."),
    )),
)


def asset_path(mode: str) -> Path:
    return theme._gui_file(f"assets/assistant_help_{'light' if mode == 'light' else 'dark'}.png")


def help_pixmap(mode: str | None = None) -> QPixmap:
    """The guide for the current theme: the bundled PNG, or drawn now if it is missing."""
    mode = mode or theme.mode()
    path = asset_path(mode)
    if path.is_file():
        pixmap = QPixmap(str(path))
        if not pixmap.isNull():
            pixmap.setDevicePixelRatio(SCALE)
            return pixmap
    pixmap = QPixmap.fromImage(render())
    pixmap.setDevicePixelRatio(SCALE)
    return pixmap


# ---------------------------------------------------------------------------- drawing
def _font(family: str, size: float, bold: bool = False) -> QFont:
    font = QFont(family)
    font.setPixelSize(round(size))
    font.setBold(bold)
    return font


def _text_height(font: QFont, text: str, width: float) -> float:
    return QFontMetricsF(font).boundingRect(QRectF(0, 0, width, 10_000), Qt.TextWordWrap, text).height()


def _button(name: str) -> QPixmap:
    """A chat button exactly as the panel shows it (style and icon of widgets.py)."""
    from . import widgets
    button = QPushButton()
    button.setStyleSheet(widgets.style())
    if name in ("mic", "send"):
        button.setObjectName("assistantMic" if name == "mic" else "assistantSend")
        button.setFixedSize(40, 30)
        button.setIcon(widgets.icon(name, theme.ON_ACCENT if name == "send" else None))
    else:
        button.setObjectName("assistantHead")
        button.setFixedSize(30, 30)
        if name == "globe":
            button.setCheckable(True)
            button.setChecked(True)
        button.setIcon(widgets.icon(name, theme.ON_ACCENT if name == "globe" else widgets.MUTED))
    button.style().unpolish(button)
    button.style().polish(button)
    return _grab(button)


def _grab(widget) -> QPixmap:
    image = QImage(widget.size() * SCALE, QImage.Format_ARGB32_Premultiplied)
    image.setDevicePixelRatio(SCALE)
    image.fill(Qt.transparent)
    widget.render(image, QPoint(), QRegion(), QWidget.RenderFlag.DrawChildren)
    pixmap = QPixmap.fromImage(image)
    pixmap.setDevicePixelRatio(SCALE)
    return pixmap


def _pictures() -> dict[str, list[QPixmap]]:
    from . import widgets
    robot = widgets.RobotButton()
    off, on = widgets.ControlSwitch(), widgets.ControlSwitch()
    on.set_on(True)
    help_button = widgets.HelpButton()
    pictures = {"robot": [_grab(robot)], "switch": [_grab(off), _grab(on)], "help": [_grab(help_button)]}
    for name in ("globe", "reload", "close", "mic", "send"):
        pictures[name] = [_button(name)]
    return pictures


def render() -> QImage:
    """The guide for the current theme, at ``SCALE`` x the logical size."""
    from . import widgets
    widgets.sync_theme()
    theme.load_fonts()
    title_font = _font(theme.DISPLAY_FONT, 22, True)
    lead_font = _font(theme.BODY_FONT, 13.5)
    section_font = _font(theme.BODY_FONT, 11.5, True)
    section_font.setLetterSpacing(QFont.AbsoluteSpacing, 1.4)
    name_font = _font(theme.BODY_FONT, 15, True)
    text_font = _font(theme.BODY_FONT, 13.5)
    text_width = WIDTH - 2 * MARGIN - ICON_COLUMN
    pictures = _pictures()

    rows = []
    for section, items in SECTIONS:
        rows.append(("section", section, 34))
        for key, name, text in items:
            height = max(56, 22 + _text_height(text_font, text, text_width) + 10)
            rows.append(("item", (key, name, text), height))
    height = MARGIN + 34 + 26 + 8 + sum(h for _, _, h in rows) + MARGIN

    image = QImage(round(WIDTH * SCALE), round(height * SCALE), QImage.Format_ARGB32_Premultiplied)
    image.setDevicePixelRatio(SCALE)
    image.fill(Qt.transparent)
    p = QPainter(image)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)
    # The panel's own shape: "leaf" corners and an orange line.
    frame = QRectF(1, 1, WIDTH - 2, height - 2)
    path = QPainterPath()
    big, small = 30, 5
    path.moveTo(frame.left() + big, frame.top())
    path.lineTo(frame.right() - small, frame.top())
    path.quadTo(frame.right(), frame.top(), frame.right(), frame.top() + small)
    path.lineTo(frame.right(), frame.bottom() - big)
    path.quadTo(frame.right(), frame.bottom(), frame.right() - big, frame.bottom())
    path.lineTo(frame.left() + small, frame.bottom())
    path.quadTo(frame.left(), frame.bottom(), frame.left(), frame.bottom() - small)
    path.lineTo(frame.left(), frame.top() + big)
    path.quadTo(frame.left(), frame.top(), frame.left() + big, frame.top())
    p.setPen(QPen(QColor(theme.ORANGE), 1.5))
    p.setBrush(QColor(theme.PANEL))
    p.drawPath(path)

    y = MARGIN
    p.setPen(QColor(theme.CREAM))
    p.setFont(title_font)
    p.drawText(QRectF(MARGIN, y, WIDTH - 2 * MARGIN, 34), Qt.AlignLeft | Qt.AlignVCenter, "LUCI Assistant")
    y += 34
    p.setPen(QColor(theme.CREAM_2))
    p.setFont(lead_font)
    p.drawText(QRectF(MARGIN, y, WIDTH - 2 * MARGIN, 26), Qt.AlignLeft | Qt.AlignVCenter,
               "What each button does")
    y += 26 + 8

    for kind, value, row_height in rows:
        if kind == "section":
            p.setPen(QPen(QColor(theme.LINE), 1))
            p.drawLine(QRectF(MARGIN, y + 10, WIDTH - 2 * MARGIN, 0).topLeft(),
                       QRectF(MARGIN, y + 10, WIDTH - 2 * MARGIN, 0).topRight())
            p.setPen(QColor(theme.ORANGE))
            p.setFont(section_font)
            p.drawText(QRectF(MARGIN, y + 14, WIDTH - 2 * MARGIN, 18), Qt.AlignLeft | Qt.AlignVCenter,
                       value.upper())
            y += row_height
            continue
        key, name, text = value
        shots = pictures[key]
        widths = [shot.width() / SCALE for shot in shots]
        total = sum(widths) + 8 * (len(shots) - 1)
        if key == "robot":       # the robot is big: shown smaller in the guide
            scale = 52 / widths[0]
        else:
            scale = 1.0
        x = MARGIN + (ICON_COLUMN - 12 - total * scale) / 2
        for shot, width in zip(shots, widths):
            h = shot.height() / SCALE * scale
            target = QRectF(x, y + (min(row_height, 56) - h) / 2, width * scale, h)
            p.drawPixmap(target, shot, QRectF(0, 0, shot.width(), shot.height()))
            x += width * scale + 8
        left = MARGIN + ICON_COLUMN
        p.setPen(QColor(theme.CREAM))
        p.setFont(name_font)
        p.drawText(QRectF(left, y + 2, text_width, 22), Qt.AlignLeft | Qt.AlignVCenter, name)
        p.setPen(QColor(theme.CREAM_2))
        p.setFont(text_font)
        p.drawText(QRectF(left, y + 24, text_width, row_height - 24), Qt.TextWordWrap, text)
        y += row_height
    p.end()
    return image


def write_assets() -> list[Path]:
    """Draw both PNGs (dark and light) into gui/assets. Needs a QApplication."""
    previous = theme.mode()
    written = []
    try:
        for mode in ("dark", "light"):
            theme.set_mode(mode)
            path = asset_path(mode)
            render().save(str(path))
            written.append(path)
    finally:
        theme.set_mode(previous)
        from . import widgets
        widgets.sync_theme()
    return written
