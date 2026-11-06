"""Entry point of LUCI.exe (the window)."""
import sys

from luci.cli import gui_main

if __name__ == "__main__":
    sys.exit(gui_main(sys.argv))
