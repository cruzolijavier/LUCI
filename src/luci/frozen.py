"""LUCI packaged as an executable (PyInstaller): which program runs the LUCI CLI.

In a normal install the window runs ``python -m luci ...`` with its own interpreter.
In the executable there is no python: the folder holds ``LUCI.exe`` (the window) and
``luci-cli.exe`` (the command line), and the window calls ``luci-cli.exe -m luci ...``
(the CLI ignores the leading ``-m luci``, so commands look the same in both cases).
"""

from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def cli_interpreter() -> str:
    """What goes before ``-m luci`` in the commands the window runs."""
    if not is_frozen():
        return sys.executable
    name = "luci-cli.exe" if sys.platform == "win32" else "luci-cli"
    return str(Path(sys.executable).resolve().with_name(name))


def bundle_dir() -> Path | None:
    """Folder with the files packed in the executable (``_internal``), if frozen."""
    folder = getattr(sys, "_MEIPASS", None)
    return Path(folder) if is_frozen() and folder else None
