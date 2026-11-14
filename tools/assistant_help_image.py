"""Redraw the assistant's help picture (the robot's "?") for the dark and the light theme.

    QT_QPA_PLATFORM=offscreen python tools/assistant_help_image.py

Writes src/luci/gui/assets/assistant_help_dark.png and assistant_help_light.png, drawn
with the real buttons. Run it after changing a button or a text in
src/luci/assistant/help_image.py.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PySide6.QtWidgets import QApplication  # noqa: E402

from luci.assistant.help_image import write_assets  # noqa: E402


def main():
    app = QApplication.instance() or QApplication(sys.argv[:1])  # noqa: F841
    for path in write_assets():
        print(f"written {path}")


if __name__ == "__main__":
    main()
