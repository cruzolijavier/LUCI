"""ROBERT's command line, with honest exit codes.

ROBERT stops on an error (missing column, missing model folder, input file
not found...) by printing a message and calling ``sys.exit()`` with no code,
which shells and the LUCI window would take as success. This wrapper runs
ROBERT's own entry point with the same arguments and turns that case into
exit code 2.
"""

import sys


def main():
    args = sys.argv[1:]
    try:
        from robert.robert import main as robert_main
    except ImportError as exc:
        print("[LUCI runner] Error: ROBERT is not importable: {}".format(exc), file=sys.stderr)
        return 1
    sys.argv = ["robert"] + args
    try:
        result = robert_main()
    except SystemExit as exc:
        if "--help" in args or "-h" in args:
            return exc.code or 0
        if exc.code in (None, 0):
            print("[LUCI runner] ROBERT stopped early; see the message above.", file=sys.stderr)
            return 2
        return exc.code
    except EOFError:
        print("[LUCI runner] ROBERT asked for missing information; fill in the target and name "
              "columns.", file=sys.stderr)
        return 2
    return 0 if result is None else int(result)


if __name__ == "__main__":
    sys.exit(main())
