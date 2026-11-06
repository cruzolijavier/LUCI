"""Render every LUCI screen offscreen at several window sizes (for visual review).

    QT_QPA_PLATFORM=offscreen python tools/gui_screenshots.py OUTDIR [WxH ...]
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from luci.gui.app import MainWindow
from luci.registry import LAYERS, programs_in

SIZES = ["1920x1080", "1366x768", "1024x700", "760x520"]


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "screenshots")
    sizes = sys.argv[2:] or SIZES
    out.mkdir(parents=True, exist_ok=True)
    app = QApplication(sys.argv[:1])
    window = MainWindow()
    window.show()
    for size in sizes:
        width, height = (int(v) for v in size.split("x"))
        window.resize(width, height)
        app.processEvents()
        for row, layer in enumerate(LAYERS):
            window.layer_list.setCurrentRow(row)
            workspace = window.current_workspace()
            workspace.go_home()
            app.processEvents()
            window.grab().save(str(out / f"{size}_{row}_{layer.key}_landing.png"))
            for program in programs_in(layer.key):
                workspace.select_package(program.key)
                app.processEvents()
                window.grab().save(str(out / f"{size}_{row}_{layer.key}_{program.key}.png"))
            workspace.go_home()
        # The input filter, with SMILES selected, seen from the first layer.
        window.layer_list.setCurrentRow(0)
        window.filter_bar.buttons["smiles"].setChecked(True)
        app.processEvents()
        window.grab().save(str(out / f"{size}_filter_smiles.png"))
        window.filter_bar.buttons["reaction"].setChecked(True)
        window.filter_bar.buttons["smiles"].setChecked(False)
        app.processEvents()
        window.grab().save(str(out / f"{size}_filter_reaction.png"))
        window.filter_bar.clear()
    print(f"saved {len(list(out.glob('*.png')))} screenshots in {out}")


if __name__ == "__main__":
    main()
