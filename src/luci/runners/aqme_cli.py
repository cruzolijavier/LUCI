"""AQME's command line, with honest exit codes.

AQME reports a malformed command (unknown or misspelled flag) by printing a
message and calling ``sys.exit()`` with no code, which shells and the LUCI
window would take as success. This wrapper runs AQME's own entry point with the
same arguments and turns that case into exit code 2. AQME also returns
normally when every molecule failed (no conformers optimised, no descriptors);
the wrapper then checks that the module wrote its results and returns 3 if it
did not. Everything else is AQME unchanged.
"""

import glob
import os
import sys
import time

# What each module must leave in its destination folder.
RESULTS = {"--csearch": ("*.sdf",), "--cmin": ("*.sdf",), "--qdescp": ("*.csv", "*/*.csv")}


def _destination(args):
    for index, token in enumerate(args):
        if token == "--destination" and index + 1 < len(args):
            return args[index + 1]
        if token.startswith("--destination="):
            return token.split("=", 1)[1]
    return os.getcwd()


def _produced(args, since):
    module = next((flag for flag in RESULTS if flag in args), None)
    if module is None:
        return True
    folder = _destination(args)
    for pattern in RESULTS[module]:
        for path in glob.glob(os.path.join(glob.escape(folder), pattern)):
            if os.path.getmtime(path) >= since - 1 and os.path.getsize(path) > 0:
                return True
    return False


def main():
    args = sys.argv[1:]
    try:
        from aqme.aqme import main as aqme_main
    except ImportError as exc:
        print("[LUCI runner] Error: AQME is not importable: {}".format(exc), file=sys.stderr)
        return 1
    sys.argv = ["aqme"] + args
    started = time.time()
    try:
        result = aqme_main()
    except SystemExit as exc:
        if "--help" in args or "-h" in args:
            return exc.code or 0
        return 2 if exc.code in (None, 0) else exc.code
    if result not in (None, 0):
        return int(result)
    if "--help" not in args and not _produced(args, started):
        print("\n[LUCI runner] AQME finished without writing any result; see the warnings above.",
              file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
