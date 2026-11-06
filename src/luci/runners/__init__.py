"""Scripts that LUCI executes *inside* a program's environment.

They are run by file path with the environment's own Python (which may be as
old as 3.8 and never has LUCI installed), so they only use the standard
library, the program itself and the sibling helper ``_luci_job``. Each one
reads the JSON job written by :mod:`luci.execution` and calls the program's
Python API, for programs that have no command line of their own.
"""
