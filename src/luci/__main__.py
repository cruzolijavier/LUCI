"""Run LUCI CLI or GUI with ``python -m luci`` (``python -m luci --gui`` for the window)."""

from .cli import main

raise SystemExit(main())
