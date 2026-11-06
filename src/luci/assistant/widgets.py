"""The assistant's interface: a robot at the bottom right with the CONTROL switch under it, and the chat panel."""

from __future__ import annotations

import html
import re

from PySide6.QtCore import QEvent, QObject, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QDesktopServices, QIcon, QPainter, QPainterPath, QPen, QPixmap, QTextCursor
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTextBrowser, QTextEdit, QVBoxLayout,
    QWidget,
)

from .audio import AudioRecorder
from .session import SUGGESTIONS

from ..gui import theme as _theme

# Same palette as the window (LUCI_visual.html). No glows or flashing lights.
ORANGE, YELLOW, PANEL, DEEP, TEXT, MUTED = (_theme.ORANGE, _theme.AMBER, _theme.BLACK, _theme.BLACK,
                                            _theme.CREAM, _theme.CREAM_3)
LINE, LINE_2, MONO = _theme.LINE, _theme.LINE_2, _theme.MONO_FONT


# ---------------------------------------------------------------------------
# Small painted icons (no image files)
# ---------------------------------------------------------------------------
def icon(name: str, colour: str = TEXT, size: int = 20) -> QIcon:
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(2, 2)
    pen = QPen(QColor(colour), 1.7)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    c = size / 2
    if name == "globe":
        p.drawEllipse(QPointF(c, c), 7, 7)
        p.drawEllipse(QPointF(c, c), 3, 7)
        p.drawLine(QPointF(c - 7, c), QPointF(c + 7, c))
    elif name == "reload":
        p.drawArc(QRectF(c - 6.5, c - 6.5, 13, 13), 40 * 16, 290 * 16)
        p.drawLine(QPointF(c + 6, c - 6), QPointF(c + 6, c - 1.5))
        p.drawLine(QPointF(c + 6, c - 6), QPointF(c + 1.5, c - 6))
    elif name == "close":
        p.drawLine(QPointF(c - 5, c - 5), QPointF(c + 5, c + 5))
        p.drawLine(QPointF(c + 5, c - 5), QPointF(c - 5, c + 5))
    elif name == "mic":
        p.drawRoundedRect(QRectF(c - 3, c - 8, 6, 10), 3, 3)
        p.drawArc(QRectF(c - 6, c - 5, 12, 10), 200 * 16, 140 * 16)
        p.drawLine(QPointF(c, c + 5), QPointF(c, c + 8))
    elif name == "stop":
        p.setBrush(QColor(colour))
        p.drawRoundedRect(QRectF(c - 4.5, c - 4.5, 9, 9), 2, 2)
    elif name == "send":
        path = QPainterPath()
        path.moveTo(c - 7, c - 6)
        path.lineTo(c + 7, c)
        path.lineTo(c - 7, c + 6)
        path.lineTo(c - 4, c)
        path.closeSubpath()
        p.setBrush(QColor(colour))
        p.drawPath(path)
    p.end()
    return QIcon(pixmap)


# ---------------------------------------------------------------------------
# Light Markdown -> Qt HTML
# ---------------------------------------------------------------------------
def _inline(text: str) -> str:
    text = html.escape(text, quote=False)
    links = []

    def keep(match):
        links.append(f"<a href='{match.group(2)}' style='color:#5cc8ff; text-decoration:none;'>{match.group(1)}</a>")
        return f"\x00{len(links) - 1}\x00"
    text = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", keep, text)
    text = re.sub(r"`([^`]+)`", r"<span style='font-family:JetBrains Mono,Consolas; color:#ff7b10;'>\1</span>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", text)
    text = re.sub(r"(?<!\w)_(?!\s)(.+?)(?<!\s)_(?!\w)", r"<i>\1</i>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: links[int(m.group(1))], text)


def markdown_html(text: str) -> str:
    lines = text.replace("\r", "").split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            block = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(html.escape(lines[i]))
                i += 1
            i += 1
            out.append("<span style='font-family:JetBrains Mono,Consolas; color:#ff7b10;'>" + "<br>".join(block) + "</span>")
            continue
        if line.strip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                    rows.append(cells)
                i += 1
            if rows:
                parts = ["<table cellspacing='0' cellpadding='4' style='margin:4px 0;'>"]
                for n, row in enumerate(rows):
                    style = f"color:{YELLOW}; font-weight:bold; border-bottom:1px solid {LINE_2};" if n == 0 else \
                        f"border-bottom:1px solid {LINE};"
                    parts.append("<tr>" + "".join(f"<td style='{style}'>{_inline(c)}</td>" for c in row) + "</tr>")
                parts.append("</table>")
                out.append("".join(parts))
            continue
        bullet = re.match(r"^(\s*)[-*•]\s+(.*)", line)
        number = re.match(r"^(\s*)(\d+)[.)]\s+(.*)", line)
        heading = re.match(r"^#{1,6}\s+(.*)", line)
        if re.fullmatch(r"\s*(-{3,}|\*{3,}|_{3,})\s*", line):
            out.append(f"<span style='color:{LINE_2};'>" + "─" * 28 + "</span>")
        elif heading:
            out.append(f"<b style='color:{YELLOW};'>{_inline(heading.group(1))}</b>")
        elif bullet:
            out.append("&nbsp;" * (2 + len(bullet.group(1)) * 2) + f"•&nbsp;{_inline(bullet.group(2))}")
        elif number:
            out.append("&nbsp;" * (1 + len(number.group(1)) * 2) + f"{number.group(2)}.&nbsp;{_inline(number.group(3))}")
        else:
            out.append(_inline(line))
        i += 1
    return re.sub(r"(<br>){3,}", "<br><br>", "<br>".join(out))


# ---------------------------------------------------------------------------
# Robot and switch
# ---------------------------------------------------------------------------
class RobotButton(QWidget):
    """The assistant's robot: a black disc with an orange ring. Busy = amber ring, steady (no flashing)."""

    clicked = Signal()
    SIZE = 74

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.SIZE, self.SIZE)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("LUCI Assistant")
        self.hover = False
        self.busy = False
        self.available = True

    def set_available(self, value: bool):
        """Grey (off) until there is an OpenAI key: Tools > Settings > OpenAI API key."""
        self.available = bool(value)
        self.setToolTip("LUCI Assistant" if self.available else
                        "LUCI Assistant is off. Add your OpenAI API key in Tools > Settings to turn it on.")
        self.update()

    def set_busy(self, value: bool):
        self.busy = value
        self.update()

    def enterEvent(self, event):
        self.hover = True
        self.update()

    def leaveEvent(self, event):
        self.hover = False
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        grey = QColor(_theme.LINE_2)
        ring = QColor(YELLOW) if self.busy else QColor(ORANGE)
        accent, accent_2, body_colour = QColor(ORANGE), QColor(YELLOW), QColor(TEXT)
        if not self.available:
            ring, accent, accent_2, body_colour = grey, grey, grey, QColor(_theme.CREAM_3)
        hover = self.hover and self.available
        p.setBrush(QBrush(QColor(_theme.ORANGE_TINT) if hover else QColor(_theme.BLACK)))
        p.setPen(QPen(ring, 2.5))
        p.drawEllipse(QRectF(self.rect()).adjusted(2, 2, -2, -2))
        # The drawing is designed on a 58 x 58 grid, scaled to the button.
        scale = self.width() * 0.82 / 58
        p.translate(self.width() * 0.09, self.height() * 0.09)
        p.scale(scale, scale)
        p.setPen(Qt.NoPen)
        p.setBrush(body_colour)
        p.drawRoundedRect(QRectF(17, 21, 24, 18), 4, 4)
        p.setBrush(accent)
        p.drawEllipse(QPointF(23, 27.5), 2.6, 2.6)
        p.drawEllipse(QPointF(35, 27.5), 2.6, 2.6)
        p.setPen(QPen(body_colour, 2))
        p.drawLine(QPointF(29, 21), QPointF(29, 13))
        p.setPen(Qt.NoPen)
        p.setBrush(accent_2)
        p.drawEllipse(QPointF(29, 13), 3, 3)
        body = QPainterPath()
        body.moveTo(13, 47)
        body.lineTo(19, 40)
        body.lineTo(39, 40)
        body.lineTo(45, 47)
        body.closeSubpath()
        p.setBrush(body_colour)
        p.drawPath(body)
        p.end()


class ControlSwitch(QWidget):
    """Small switch under the robot: on = the assistant can drive the window."""

    toggled = Signal(bool)
    W, H = 32, 18

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.W, self.H)
        self.setCursor(Qt.PointingHandCursor)
        self.on = False
        self._tooltip()

    def _tooltip(self):
        self.setToolTip("Control ON: the assistant can drive LUCI for you (open programs, fill the input and the "
                        "options...)." if self.on else
                        "Control OFF: the assistant only explains and checks. Turn it on so it can fill the forms "
                        "for you.")

    def set_on(self, value: bool):
        self.on = bool(value)
        self._tooltip()
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.set_on(not self.on)
            self.toggled.emit(self.on)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.H / 2
        p.setPen(QPen(QColor(ORANGE), 1))
        p.setBrush(QColor(ORANGE) if self.on else QColor(_theme.BLACK))
        p.drawRoundedRect(QRectF(0.5, 0.5, self.W - 1, self.H - 1), r - 0.5, r - 0.5)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(_theme.BLACK) if self.on else QColor(TEXT))
        side = self.H - 6
        p.drawEllipse(QRectF(self.W - side - 3 if self.on else 3, 3, side, side))


class InputBox(QTextEdit):
    """Enter sends, Shift+Enter breaks the line."""

    submit = Signal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            self.submit.emit()
            return
        super().keyPressEvent(event)


# ---------------------------------------------------------------------------
# Chat panel
# ---------------------------------------------------------------------------
STYLE = f"""
QFrame#assistantPanel {{ background-color: {PANEL}; border: 1px solid {ORANGE};
                         border-top-left-radius: 26px; border-bottom-right-radius: 26px;
                         border-top-right-radius: 4px; border-bottom-left-radius: 4px; }}
QLabel#assistantTitle {{ color: {TEXT}; font-family: '{_theme.DISPLAY_FONT}'; font-size: 14px; font-weight: 600;
                         background: transparent; border: none; }}
QLabel#assistantSub {{ color: {MUTED}; font-size: 11px; background: transparent; border: none; }}
QLabel#assistantStatus {{ color: {YELLOW}; font-size: 12px; font-style: italic; background: transparent; border: none; }}
QTextBrowser#assistantChat {{ background-color: {DEEP}; color: {TEXT}; border: none; border-top: 1px solid {LINE};
                              border-radius: 0px; padding: 8px 2px; font-size: 13px; }}
QTextEdit#assistantInput {{ background-color: {_theme.BLACK}; color: {TEXT}; border: 1px solid {LINE_2};
                            border-top-left-radius: 14px; border-bottom-right-radius: 14px;
                            border-top-right-radius: 3px; border-bottom-left-radius: 3px; padding: 6px 8px; font-size: 13px; }}
QTextEdit#assistantInput:focus {{ border-color: {ORANGE}; }}
QPushButton#assistantHead {{ background: transparent; border: 1px solid {LINE_2}; padding: 3px; min-height: 0px;
                             border-top-left-radius: 10px; border-bottom-right-radius: 10px;
                             border-top-right-radius: 2px; border-bottom-left-radius: 2px; }}
QPushButton#assistantHead:hover {{ border-color: {ORANGE}; }}
QPushButton#assistantHead:checked {{ background-color: {ORANGE}; border-color: {ORANGE}; }}
QPushButton#assistantSend {{ background-color: {ORANGE}; border: 1px solid {ORANGE}; min-height: 0px; padding: 0;
                             border-top-left-radius: 10px; border-bottom-right-radius: 10px;
                             border-top-right-radius: 2px; border-bottom-left-radius: 2px; }}
QPushButton#assistantSend:hover {{ background-color: {TEXT}; border-color: {TEXT}; }}
QPushButton#assistantSend:disabled {{ background-color: transparent; border-color: {LINE}; }}
QPushButton#assistantMic {{ background-color: transparent; border: 1px solid {LINE_2}; min-height: 0px; padding: 0;
                            border-top-left-radius: 10px; border-bottom-right-radius: 10px;
                            border-top-right-radius: 2px; border-bottom-left-radius: 2px; }}
QPushButton#assistantMic:hover {{ border-color: {ORANGE}; }}
QPushButton#assistantMic[recording="true"] {{ background-color: {_theme.RED}; border-color: {_theme.RED}; }}
"""


class ChatPanel(QFrame):
    close_requested = Signal()

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.setObjectName("assistantPanel")
        self.setFixedWidth(430)
        self.setStyleSheet(STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        head = QHBoxLayout()
        head.setSpacing(6)
        texts = QVBoxLayout()
        texts.setSpacing(0)
        title = QLabel("LUCI Assistant")
        title.setObjectName("assistantTitle")
        texts.addWidget(title)
        self.sub = QLabel("")
        self.sub.setObjectName("assistantSub")
        self.sub.setWordWrap(True)
        texts.addWidget(self.sub)
        head.addLayout(texts, 1)
        self.web_button = QPushButton()
        self.web_button.setObjectName("assistantHead")
        self.web_button.setCheckable(True)
        self.new_button = QPushButton()
        self.new_button.setObjectName("assistantHead")
        self.new_button.setIcon(icon("reload", MUTED))
        self.new_button.setToolTip("New conversation")
        self.new_button.clicked.connect(self.session.new_conversation)
        close = QPushButton()
        close.setObjectName("assistantHead")
        close.setIcon(icon("close", MUTED))
        close.setToolTip("Close")
        close.clicked.connect(self.close_requested.emit)
        for button in (self.web_button, self.new_button, close):
            button.setFixedSize(30, 30)
            button.setCursor(Qt.PointingHandCursor)
            head.addWidget(button)
        layout.addLayout(head)

        self.view = QTextBrowser()
        self.view.setObjectName("assistantChat")
        self.view.setOpenLinks(False)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.anchorClicked.connect(self._link)
        layout.addWidget(self.view, 1)
        self.status_label = QLabel("")
        self.status_label.setObjectName("assistantStatus")
        self.status_label.setWordWrap(True)
        self.status_label.hide()
        layout.addWidget(self.status_label)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.input = InputBox()
        self.input.setObjectName("assistantInput")
        self.input.setPlaceholderText("Ask or dictate...")
        self.input.setToolTip("Enter sends · Shift+Enter breaks the line")
        self.input.setFixedHeight(66)
        self.input.setAcceptRichText(False)
        self.input.submit.connect(self.send)
        self.mic_button = QPushButton()
        self.mic_button.setObjectName("assistantMic")
        self.mic_button.setIcon(icon("mic"))
        self.mic_button.setToolTip("Dictate: press to record and again to stop. The text stays in the box until "
                                   "you send it.")
        self.send_button = QPushButton()
        self.send_button.setObjectName("assistantSend")
        self.send_button.setIcon(icon("send", _theme.BLACK))
        self.send_button.setToolTip("Send")
        buttons = QVBoxLayout()
        buttons.setSpacing(6)
        for button in (self.mic_button, self.send_button):
            button.setFixedSize(40, 30)
            button.setCursor(Qt.PointingHandCursor)
            buttons.addWidget(button)
        self.mic_button.clicked.connect(self._mic)
        self.send_button.clicked.connect(self.send)
        self.web_button.toggled.connect(self.session.set_web)
        row.addWidget(self.input, 1)
        row.addLayout(buttons)
        layout.addLayout(row)

        self._dots = 0
        self._status_text = ""
        self._status_clock = QTimer(self)
        self._status_clock.setInterval(400)
        self._status_clock.timeout.connect(self._animate_status)
        self.recorder = AudioRecorder(self)
        self.recorder.seconds.connect(self._recording_seconds)
        self.recorder.finished.connect(self._audio_ready)
        self.recorder.error.connect(self._audio_error)
        self._transcribing = False

        session.changed.connect(self.paint)
        session.status.connect(self._on_status)
        session.control_changed.connect(lambda _on: self.subtitle())
        session.screen_changed.connect(self.subtitle)
        session.web_changed.connect(self._on_web)
        self._on_web(session.web)
        self.paint()

    # ---- painting -------------------------------------------------------------
    def _on_web(self, on: bool):
        self.web_button.blockSignals(True)
        self.web_button.setChecked(on)
        self.web_button.blockSignals(False)
        self.web_button.setIcon(icon("globe", _theme.BLACK if on else MUTED))
        self.web_button.setToolTip("Web search ON: when a question needs it, the assistant searches the web and "
                                   "cites the sources. Press to turn it off." if on else
                                   "Web search OFF. Press to let the assistant search the web when needed.")
        self.subtitle()

    def subtitle(self):
        self.sub.setText(f"On: {self.session.screen_name()}  ·  Control {'on' if self.session.control else 'off'}"
                         f"  ·  Web {'on' if self.session.web else 'off'}")

    @staticmethod
    def _user_bubble(text):
        return (f"<table width='100%' cellspacing='0' cellpadding='0' style='margin:6px 0;'><tr><td width='18%'></td>"
                f"<td style='background-color:{ORANGE}; color:#000000; font-weight:600; padding:9px 13px;'>{markdown_html(text)}</td>"
                f"</tr></table>")

    @staticmethod
    def _bot_bubble(text, border=LINE_2, title="", title_colour=ORANGE):
        head = f"<b style='color:{title_colour};'>{title}</b><br>" if title else ""
        return (f"<table width='100%' cellspacing='0' cellpadding='0' style='margin:6px 0;'><tr>"
                f"<td style='background-color:#000000; color:{TEXT}; padding:9px 13px; border:1px solid {border};'>"
                f"{head}{markdown_html(text)}</td><td width='8%'></td></tr></table>")

    def _suggestions(self):
        program, _layer = self.session.where()
        return SUGGESTIONS["program" if program else "landing"]

    def paint(self):
        parts = []
        if not self.session.messages:
            welcome = (f"Hi, I'm LUCI's assistant. You are in **{self.session.screen_name()}**.\n\n"
                       "I know LUCI and every program in it (and their documentation), I can see what is on your "
                       "screen and tell you if something does not fit, read your input files and logs, and, if you "
                       "turn on the switch under the robot, fill the forms for you.\n\n"
                       "With the globe button I can also search the web. You can dictate with the microphone.")
            parts.append(self._bot_bubble(welcome))
            cells = "".join(f"<td style='border:1px solid {LINE_2}; padding:5px 12px;'><a href='suggestion:{i}' "
                            f"style='color:{TEXT}; text-decoration:none; font-weight:600;'>{html.escape(text)}</a></td>"
                            f"<td width='6'></td>" for i, text in enumerate(self._suggestions()))
            parts.append(f"<table cellspacing='0' cellpadding='0' style='margin:2px 0 8px 0;'><tr>{cells}</tr></table>")
        for message in self.session.messages:
            if message["role"] == "user":
                parts.append(self._user_bubble(message["text"]))
            elif message["role"] == "system":
                parts.append(self._bot_bubble(message["text"], _theme.RED, "Notice", _theme.RED))
            else:
                parts.append(self._bot_bubble(message["text"]))
        self.view.setHtml("".join(parts))
        self.view.moveCursor(QTextCursor.End)
        bar = self.view.verticalScrollBar()
        bar.setValue(bar.maximum())
        self.send_button.setEnabled(not self.session.busy)
        self.new_button.setEnabled(not self.session.busy)

    def _link(self, url):
        target = url.toString()
        if url.scheme() in ("http", "https"):
            QDesktopServices.openUrl(url)
        elif target.startswith("suggestion:"):
            index = int(target.split(":")[1])
            options = self._suggestions()
            if index < len(options):
                self.session.send(options[index])

    # ---- status --------------------------------------------------------------------
    def _on_status(self, text):
        self._status_text = text
        if text:
            self.status_label.setText(text)
            self.status_label.show()
            self._status_clock.start()
        elif not self.recorder.recording and not self._transcribing:
            self._status_clock.stop()
            self.status_label.hide()
        self.send_button.setEnabled(not self.session.busy)
        self.new_button.setEnabled(not self.session.busy)

    def _animate_status(self):
        if self._status_text and not self.recorder.recording:
            self._dots = (self._dots + 1) % 4
            self.status_label.setText(self._status_text.rstrip(".") + "." * self._dots)

    def notice(self, text):
        self.status_label.setText(text)
        self.status_label.show()
        QTimer.singleShot(7000, lambda: (not self.session.busy and not self.recorder.recording
                                         and not self._transcribing) and self.status_label.hide())

    # ---- sending -------------------------------------------------------------------
    def send(self):
        if self.recorder.recording or self._transcribing:
            return
        text = self.input.toPlainText().strip()
        if text and not self.session.busy and self.session.send(text):
            self.input.clear()

    # ---- microphone ----------------------------------------------------------------
    def _set_recording(self, value):
        self.mic_button.setProperty("recording", "true" if value else "false")
        self.mic_button.setIcon(icon("stop" if value else "mic", "#ffffff"))
        self.mic_button.style().unpolish(self.mic_button)
        self.mic_button.style().polish(self.mic_button)

    def _mic(self):
        if self._transcribing:
            return
        if self.recorder.recording:
            self._set_recording(False)
            self.recorder.stop()
        else:
            self.recorder.start()
            if self.recorder.recording:
                self._set_recording(True)
                self.status_label.setText("Recording... 0:00  ·  press the microphone to stop")
                self.status_label.show()

    def _recording_seconds(self, seconds):
        self.status_label.setText(f"Recording... {seconds // 60}:{seconds % 60:02d}  ·  press the microphone to stop")

    def _audio_ready(self, path):
        self._set_recording(False)
        self._transcribing = True
        self.mic_button.setEnabled(False)
        self.status_label.setText("Transcribing...")
        self.status_label.show()
        self.session.transcribe(path, self._transcribed, self._audio_error)

    def _transcribed(self, text):
        self._transcribing = False
        self.mic_button.setEnabled(True)
        if not self.session.busy:
            self.status_label.hide()
        if not text:
            self.notice("Nothing was understood in the recording.")
            return
        current = self.input.toPlainText()
        cursor = self.input.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText((" " if current and not current.endswith((" ", "\n")) else "") + text)
        self.input.setTextCursor(cursor)
        self.input.setFocus()

    def _audio_error(self, message):
        self._transcribing = False
        self._set_recording(False)
        self.mic_button.setEnabled(True)
        self.notice(message)

    def stop_audio(self):
        if self.recorder.recording:
            self.recorder.cancel()
            self._set_recording(False)


# ---------------------------------------------------------------------------
# On the main window
# ---------------------------------------------------------------------------
class AssistantView(QObject):
    """Robot (with its switch) and chat panel over the LUCI window, at the bottom right."""

    MARGIN = 22

    def __init__(self, window, session):
        super().__init__(window)
        self.window = window
        self.session = session
        self.robot = RobotButton(window)
        self.switch = ControlSwitch(window)
        self.panel = ChatPanel(session, window)
        self.panel.hide()
        self.available = True
        self.robot.clicked.connect(self._robot_clicked)
        self.panel.close_requested.connect(lambda: session.set_panel_visible(False))
        self.switch.set_on(session.control)
        self.switch.toggled.connect(session.set_control)
        session.control_changed.connect(self.switch.set_on)
        session.panel_changed.connect(self._show_panel)
        session.status.connect(lambda text: self.robot.set_busy(bool(text)))
        window.installEventFilter(self)
        self.place()
        self.robot.show()
        self.refresh_availability()

    def _robot_clicked(self):
        if not self.available:
            box = QMessageBox(self.window)
            box.setWindowTitle("LUCI Assistant")
            box.setText("The assistant is off: it needs an OpenAI API key.")
            box.setInformativeText("Paste it in Tools > Settings > OpenAI API key. The robot turns on by itself.")
            settings = box.addButton("Open Settings", QMessageBox.AcceptRole)
            box.addButton("Close", QMessageBox.RejectRole)
            box.exec()
            if box.clickedButton() is settings:
                self.window.open_settings()
            return
        self.session.set_panel_visible(not self.panel.isVisible())

    def refresh_availability(self):
        """Robot grey and switch hidden while there is no OpenAI key; normal again once there is one."""
        from .config import read_key
        try:
            key, _error = read_key()
        except Exception:
            key = None
        self.available = bool(key)
        self.robot.set_available(self.available)
        self.switch.setVisible(self.available)
        if not self.available and self.panel.isVisible():
            self.session.set_panel_visible(False)

    def _show_panel(self, visible):
        self.panel.setVisible(visible)
        if visible:
            self.place()
            self.panel.raise_()
            self.panel.subtitle()
            self.panel.paint()
            self.panel.input.setFocus()
        else:
            self.panel.stop_audio()

    def place(self):
        w, h = self.window.width(), self.window.height()
        size = RobotButton.SIZE if h >= 700 else 58
        if self.robot.width() != size:
            self.robot.setFixedSize(size, size)
        bottom = self.window.statusBar().height() if self.window.statusBar() else 0
        x = w - self.robot.width() - self.MARGIN
        gap = 5
        y = h - bottom - self.robot.height() - gap - self.switch.height() - self.MARGIN
        self.robot.move(x, y)
        self.switch.move(x + (self.robot.width() - self.switch.width()) // 2, y + self.robot.height() + gap)
        # Below the page's top row (Back, Uninstall, Run, Stop stay visible).
        top = (self.window.menuBar().height() if self.window.menuBar() else 0) + 64
        height = max(260, min(680, y - top - 10))
        self.panel.setFixedHeight(height)
        self.panel.setFixedWidth(min(430, max(300, w - 2 * self.MARGIN - 220)))
        self.panel.move(w - self.panel.width() - self.MARGIN, max(top, y - height - 10))
        for widget in (self.switch, self.robot, self.panel):
            widget.raise_()

    def eventFilter(self, obj, event):
        if obj is self.window and event.type() in (QEvent.Resize, QEvent.Show):
            QTimer.singleShot(0, self.place)
        elif obj is self.window and event.type() == QEvent.WindowActivate:
            QTimer.singleShot(0, self.refresh_availability)
        return False
