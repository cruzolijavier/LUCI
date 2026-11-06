"""Entry point of luci-cli.exe (the command line; the window runs it for every job).

The window calls ``luci-cli.exe -m luci <layer> ...``, the same words as
``python -m luci ...`` in a normal install, so the leading ``-m luci`` is dropped.
"""
import sys

from luci.cli import main

if __name__ == "__main__":
    if sys.argv[1:3] == ["-m", "luci"]:
        del sys.argv[1:3]
    sys.exit(main())
