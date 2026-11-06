# PyInstaller recipe for LUCI: run packaging\build_exe.bat on Windows, packaging/build_unix.sh on
# macOS / Linux (or: pyinstaller packaging/luci.spec). The same file serves the three systems.
# Result, Windows: dist/LUCI/ with LUCI.exe (window), luci-cli.exe (command line) and _internal/.
#         Linux:   dist/LUCI/ with LUCI, luci-cli and _internal/.
#         macOS:   dist/LUCI.app (LUCI and luci-cli inside Contents/MacOS).
# The program environments are NOT inside: LUCI installs them with pixi on first use.
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH).parent
SRC = ROOT / "src"

datas = collect_data_files("luci", excludes=["**/non_used/**", "**/__pycache__/**", "**/logo - copia.png"])
# The runners are run by each program's own Python, so they must be real .py files on disk.
datas += [(str(p), "luci/runners") for p in (SRC / "luci" / "runners").glob("*.py")]
datas += [(str(ROOT / "README.md"), ".")]
bundled = SRC / "luci" / "assistant" / "bundled_key.txt"
if bundled.is_file():
    datas += [(str(bundled), "luci/assistant")]

hidden = collect_submodules("luci") + ["PySide6.QtMultimedia"]
excludes = ["PyQt5", "PyQt6", "PySide2", "tkinter", "matplotlib", "numpy", "pandas", "scipy", "IPython", "pytest",
            "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.Qt3DCore", "PySide6.QtQuick3D",
            "PySide6.QtCharts", "PySide6.QtDataVisualization", "PySide6.QtPdf"]
ICON = str(ROOT / "packaging" / "luci.ico") if sys.platform == "win32" else None   # .ico is Windows only


def analysis(script):
    return Analysis([str(ROOT / "packaging" / script)], pathex=[str(SRC)], datas=datas,
                    hiddenimports=hidden, excludes=excludes, noarchive=False)


gui = analysis("luci_gui.py")
cli = analysis("luci_cli.py")

gui_exe = EXE(PYZ(gui.pure), gui.scripts, [], exclude_binaries=True, name="LUCI",
              console=False, icon=ICON, upx=False)
cli_exe = EXE(PYZ(cli.pure), cli.scripts, [], exclude_binaries=True, name="luci-cli",
              console=True, icon=ICON, upx=False)

collected = COLLECT(gui_exe, gui.binaries, gui.datas, cli_exe, cli.binaries, cli.datas,
                    name="LUCI", upx=False)

if sys.platform == "darwin":
    # A double-clickable LUCI.app; luci-cli sits next to LUCI inside it, where the window looks for it.
    app = BUNDLE(collected, name="LUCI.app", icon=None, bundle_identifier="es.uv.luci",
                 info_plist={"CFBundleName": "LUCI", "CFBundleDisplayName": "LUCI",
                             "NSHighResolutionCapable": True, "LSMinimumSystemVersion": "11.0"})
